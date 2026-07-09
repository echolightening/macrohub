#!/usr/bin/env python3
"""
ingest_off.py — Open Food Facts bulk-dump ETL for MacroHub Track-2.

AGENDA item 28, milestone M8. Governed by LOCKED.md invariants 5/6 and the
item28 nutrition-research brief. $0 model spend — deterministic ETL only.

Source: Open Food Facts official static English-tagged export
(https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz,
mirrored via S3), ~4.5M rows. The full multilingual Parquet dump
(huggingface.co/datasets/openfoodfacts/product-database) is ~7.6GB and out of
scope for this bounded seed run; the "en" CSV export is OFF's own smaller
official artifact and is what this script consumes. Growth path: point
--gz-path at the full parquet-derived CSV (or raise --cap / set --cap 0) once
disk/time budget allows a larger ingest — same script, no redesign.

REQUIRED per Fable verdict modification 2 (ODbL flag-and-segregate, not
exclude): every record in this shard carries source: openfoodfacts and
license: ODbL-1.0. These records are NEVER merged into a mixed-source shard —
they live only under data/fooddb/openfoodfacts/, physically separate from the
usda/ and menustat/ shard directories. See LOCKED.md's ODbL attribution note.

Usage: ingest_off.py --gz-path <off_en.csv.gz> --out-dir <data/fooddb/openfoodfacts> [--cap N]
"""
import argparse
import csv
import gzip
import json
import os
import sys

csv.field_size_limit(sys.maxsize)

REQUIRED_FIELDS = ["energy-kcal_100g", "proteins_100g", "carbohydrates_100g", "fat_100g"]


def log(msg):
    print(f"[ingest_off] {msg}", flush=True)


def to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gz-path", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cap", type=int, default=30000,
                     help="cap on OFF records admitted this run (personal-seed scope, "
                          "per M10 gate mod 4 — pass 0 for unlimited)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    kept = []
    scanned = 0
    dropped_missing_core = 0

    with gzip.open(args.gz_path, mode="rt", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            scanned += 1
            if scanned % 500_000 == 0:
                log(f"  scanned {scanned:,} rows, kept {len(kept)}...")
            if args.cap and len(kept) >= args.cap:
                break
            code = (row.get("code") or "").strip()
            name = (row.get("product_name") or "").strip()
            if not code or not name:
                continue
            cal = to_float(row.get("energy-kcal_100g"))
            pro = to_float(row.get("proteins_100g"))
            carb = to_float(row.get("carbohydrates_100g"))
            fat = to_float(row.get("fat_100g"))
            if cal is None or pro is None or carb is None or fat is None:
                dropped_missing_core += 1
                continue
            satfat = to_float(row.get("saturated-fat_100g")) or 0.0
            fiber = to_float(row.get("fiber_100g")) or 0.0
            brand = (row.get("brands") or "").split(",")[0].strip()
            serving_size_text = (row.get("serving_size") or "").strip()
            serving_qty = to_float(row.get("serving_quantity"))
            aliases = []
            generic = (row.get("generic_name") or "").strip()
            if generic and generic != name:
                aliases.append(generic)

            rec = {
                "fooddb_id": f"off:{code}",
                "name": f"{brand} {name}".strip() if brand else name,
                "aliases": aliases,
                "per_100g": {
                    "cal": round(cal, 2),
                    "pro": round(pro, 2),
                    "carb": round(carb, 2),
                    "fat": round(fat, 2),
                    "satfat": round(satfat, 2),
                    "fiber": round(fiber, 2),
                },
                "serving": {
                    "amount": serving_qty if serving_qty else 100,
                    "unit": "g",
                    "household": serving_size_text or None,
                },
                "source": "openfoodfacts",
                "provenance": "label",
                "confidence": 1.0,
                "license": "ODbL-1.0",
            }
            if brand:
                rec["brand"] = brand
            categories = (row.get("categories_en") or "").strip()
            if categories:
                rec["category"] = categories.split(",")[0].strip()
            countries = (row.get("countries_en") or "").strip()
            if countries:
                rec["countries"] = countries
            kept.append(rec)

    log(f"scan complete: {scanned:,} rows scanned, {len(kept)} kept, "
        f"{dropped_missing_core} dropped for missing core macro fields")

    out_path = os.path.join(args.out_dir, "openfoodfacts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "shard": "openfoodfacts",
            "source": "openfoodfacts",
            "license": "ODbL-1.0",
            "attribution": "Data sourced from Open Food Facts (https://world.openfoodfacts.org), "
                            "licensed under the Open Database License (ODbL) v1.0. "
                            "See https://opendatacommons.org/licenses/odbl/1-0/ . "
                            "Share-alike obligations attach only if this shard is redistributed "
                            "as part of a derivative database — see LOCKED.md ODbL note.",
            "count": len(kept),
            "records": kept,
        }, f, indent=2)
    log(f"wrote {out_path}: {len(kept)} records (physically segregated shard, source=openfoodfacts on every record)")


if __name__ == "__main__":
    main()
