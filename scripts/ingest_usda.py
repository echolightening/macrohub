#!/usr/bin/env python3
"""
ingest_usda.py — USDA FoodData Central bulk-download ETL for MacroHub Track-2.

AGENDA item 28, milestone M8. Governed by LOCKED.md invariants 5/6 (Track-2
caps, provenance labeling) and the item28 nutrition-research brief
(~/local-ai/specs/plans/item28-nutrition-research-brief.md). $0 model spend —
this is deterministic ETL, no Haiku/Claude call anywhere in this file.

Source: USDA FoodData Central Full Download (public domain, no license
restriction), downloaded from https://fdc.nal.usda.gov/fdc-datasets/ .
Covers SR Legacy (raw/authoritative foods), Foundation (high-quality
analytical), FNDDS/Survey (foods-as-eaten, incl. mixed/ethnic dishes), and
Branded (manufacturer label panels).

Emits records matching MacroHub's M2 schema field-for-field (STATE.md
"Stored-meal schema"): canonical_id (== fooddb_id), name, aliases[], per-100g
macros using MacroHub's exact field names (cal, pro, carb, fat, satfat,
fiber), serving, source, provenance, confidence.

Branded Foods is capped (CAP_BRANDED below) for this seed run — USDA ships
~2M+ branded label records; per M10's close-out gate text ("useful personal
seed with documented growth path, not largest practical dataset" — Fable
verdict fable-bench:item28-nutrition-research-2026-07-09, required
modification 4), this run takes a bounded, quality-filtered sample rather
than all of them. Growth path: re-run with a higher --cap-branded (or 0 for
unlimited) once the pipeline shape is validated — same script, no redesign.

Usage: ingest_usda.py --raw-dir <dir with extracted USDA CSVs> --out-dir <data/fooddb/usda> [--cap-branded N]
"""
import argparse
import csv
import json
import os
import sys

csv.field_size_limit(sys.maxsize)

# USDA nutrient_id -> MacroHub field name (verified against nutrient.csv this run)
NUTRIENT_MAP = {
    "1008": "cal",     # Energy, KCAL
    "1003": "pro",     # Protein, G
    "1004": "fat",     # Total lipid (fat), G
    "1005": "carb",    # Carbohydrate, by difference, G
    "1258": "satfat",  # Fatty acids, total saturated, G
    "1079": "fiber",   # Fiber, total dietary, G
}
REQUIRED_FIELDS = {"cal", "pro", "carb", "fat"}  # satfat/fiber optional, default 0.0

SOURCE_BY_DATATYPE = {
    "sr_legacy_food": "usda_sr_legacy",
    "foundation_food": "usda_foundation",
    "survey_fndds_food": "usda_fndds",
    "branded_food": "usda_branded",
}


def log(msg):
    print(f"[ingest_usda] {msg}", flush=True)


def load_target_foods(raw_dir, cap_branded):
    """Pass 1: read food.csv + branded_food.csv, decide which fdc_ids to keep,
    and stash the metadata needed to build the final record (name, brand,
    serving info) without re-reading food.csv later."""
    food_path = os.path.join(raw_dir, "food.csv")
    branded_path = os.path.join(raw_dir, "branded_food.csv")

    targets = {}  # fdc_id -> dict of partial record fields
    counts = {"sr_legacy_food": 0, "foundation_food": 0, "survey_fndds_food": 0, "branded_food": 0}

    with open(food_path, encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        for row in r:
            dtype = row["data_type"]
            if dtype == "branded_food":
                # Branded gets its extra fields (serving/brand) from branded_food.csv
                # in the second pass; cap applied there so we only keep the ones we
                # actually admit.
                continue
            if dtype not in SOURCE_BY_DATATYPE:
                continue
            fdc_id = row["fdc_id"]
            targets[fdc_id] = {
                "fdc_id": fdc_id,
                "name": row["description"].strip(),
                "data_type": dtype,
                "serving": {"amount": 100, "unit": "g"},
                "aliases": [],
            }
            counts[dtype] += 1
    log(f"food.csv pass: sr_legacy={counts['sr_legacy_food']} foundation={counts['foundation_food']} "
        f"fndds={counts['survey_fndds_food']}")

    # Second pass: branded_food.csv carries name via... actually branded names live in
    # food.csv too (description), so re-scan food.csv filtered to branded_food, joined
    # with branded_food.csv for serving/brand. We stream both by fdc_id using branded_food.csv
    # as the driver (smaller row shape) and look up description lazily via a dict built here.
    branded_names = {}
    with open(food_path, encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["data_type"] == "branded_food":
                branded_names[row["fdc_id"]] = row["description"].strip()

    kept_branded = 0
    with open(branded_path, encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        for row in r:
            if cap_branded and kept_branded >= cap_branded:
                break
            fdc_id = row["fdc_id"]
            name = branded_names.get(fdc_id)
            if not name:
                continue
            serving_size = row.get("serving_size") or ""
            serving_unit = row.get("serving_size_unit") or "g"
            try:
                serving_amount = float(serving_size) if serving_size else 100
            except ValueError:
                serving_amount = 100
            brand = row.get("brand_owner") or row.get("brand_name") or ""
            targets[fdc_id] = {
                "fdc_id": fdc_id,
                "name": f"{brand} {name}".strip() if brand else name,
                "data_type": "branded_food",
                "serving": {"amount": serving_amount, "unit": serving_unit or "g",
                             "household": row.get("household_serving_fulltext") or None},
                "aliases": [name] if brand else [],
                "brand": brand or None,
                "gtin_upc": row.get("gtin_upc") or None,
                "category": row.get("branded_food_category") or None,
            }
            kept_branded += 1
    counts["branded_food"] = kept_branded
    log(f"branded_food.csv pass: kept {kept_branded} of cap={cap_branded or 'unlimited'}")
    return targets, counts


def attach_nutrients(raw_dir, targets):
    """Pass 2: single streaming pass over food_nutrient.csv (the 1.7GB file),
    filling in macro amounts only for fdc_ids already selected in `targets`."""
    fn_path = os.path.join(raw_dir, "food_nutrient.csv")
    wanted_ids = set(targets.keys())
    filled = 0
    with open(fn_path, encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            if i % 5_000_000 == 0 and i:
                log(f"  food_nutrient.csv: {i:,} rows scanned...")
            fdc_id = row["fdc_id"]
            if fdc_id not in wanted_ids:
                continue
            nutrient_id = row["nutrient_id"]
            field = NUTRIENT_MAP.get(nutrient_id)
            if not field:
                continue
            amount = row.get("amount")
            if not amount:
                continue
            try:
                amount = float(amount)
            except ValueError:
                continue
            rec = targets[fdc_id]
            if "macros" not in rec:
                rec["macros"] = {}
                filled += 1
            rec["macros"][field] = amount
    log(f"food_nutrient.csv pass complete: {filled} target foods got at least one macro value")
    return targets


def finalize_records(targets, counts):
    """Drop records missing required core fields (per brief's OFF policy,
    applied uniformly to any source: 'ingest must drop records missing the
    core macro fields'). Emit final MacroHub-schema records."""
    out_by_source = {"usda_sr_legacy": [], "usda_foundation": [], "usda_fndds": [], "usda_branded": []}
    dropped = 0
    for fdc_id, rec in targets.items():
        macros = rec.get("macros", {})
        if not REQUIRED_FIELDS.issubset(macros.keys()):
            dropped += 1
            continue
        source_key = SOURCE_BY_DATATYPE[rec["data_type"]]
        out = {
            "fooddb_id": f"usda:{fdc_id}",
            "name": rec["name"],
            "aliases": rec.get("aliases", []),
            "per_100g": {
                "cal": round(macros.get("cal", 0.0), 2),
                "pro": round(macros.get("pro", 0.0), 2),
                "carb": round(macros.get("carb", 0.0), 2),
                "fat": round(macros.get("fat", 0.0), 2),
                "satfat": round(macros.get("satfat", 0.0), 2),
                "fiber": round(macros.get("fiber", 0.0), 2),
            },
            "serving": rec.get("serving", {"amount": 100, "unit": "g"}),
            "source": "usda",
            "source_detail": source_key,
            "provenance": "usda",
            "confidence": 1.0,
        }
        if rec.get("brand"):
            out["brand"] = rec["brand"]
        if rec.get("gtin_upc"):
            out["gtin_upc"] = rec["gtin_upc"]
        if rec.get("category"):
            out["category"] = rec["category"]
        out_by_source[source_key].append(out)
    log(f"finalize: dropped {dropped} records missing required core fields "
        f"({', '.join(sorted(REQUIRED_FIELDS))})")
    return out_by_source


def write_shards(out_by_source, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    for source_key, records in out_by_source.items():
        path = os.path.join(out_dir, f"{source_key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "shard": source_key,
                "source": "usda",
                "license": "public_domain",
                "count": len(records),
                "records": records,
            }, f, indent=2)
        log(f"wrote {path}: {len(records)} records")
        total += len(records)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True, help="dir with extracted USDA CSVs (food.csv, branded_food.csv, food_nutrient.csv, ...)")
    ap.add_argument("--out-dir", required=True, help="output dir for MacroHub-schema JSON shards")
    ap.add_argument("--cap-branded", type=int, default=20000,
                     help="cap on branded_food records ingested this run (personal-seed scope, "
                          "per M10 gate mod 4 — pass 0 for unlimited/full ingest)")
    args = ap.parse_args()

    log(f"pass 1: selecting target foods from food.csv + branded_food.csv (cap_branded={args.cap_branded or 'unlimited'})")
    targets, counts = load_target_foods(args.raw_dir, args.cap_branded)
    log(f"pass 2: streaming food_nutrient.csv to fill macros for {len(targets)} target foods")
    targets = attach_nutrients(args.raw_dir, targets)
    log("pass 3: finalize + drop incomplete records")
    out_by_source = finalize_records(targets, counts)
    total = write_shards(out_by_source, args.out_dir)
    log(f"DONE: {total} USDA records written across {len(out_by_source)} shards to {args.out_dir}")


if __name__ == "__main__":
    main()
