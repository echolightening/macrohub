#!/usr/bin/env python3
"""
ingest_menustat.py — MenuStat chain-restaurant panel ETL for MacroHub Track-2.

AGENDA item 28, milestone M8. Governed by LOCKED.md invariants 5/6 and the
item28 nutrition-research brief. $0 model spend — deterministic ETL only.

SOURCE DEVIATION FROM THE BRIEF (documented, not silent — mirrors item-15's
loud-enumeration-failure discipline): the brief cited menustat.org as the
direct download source. As of this build (2026-07-09), menustat.org
redirects to an unrelated third-party site (spiritofpeoria.com) — the
original NYC-DOH-affiliated domain has lapsed/been repurposed. The real
current home of the MenuStat dataset is the Harvard Dataverse deposit
"MenuStat Annual Data" (Cleveland, Lauren, 2022), DOI 10.7910/DVN/K4NYTR,
https://doi.org/10.7910/DVN/K4NYTR — this is the same NYU/NYC-DOH-produced
panel, just rehosted. This script consumes the most recent year available
there (2018, file id 6191167, ~71k menu items). Free, no auth required.

Emits MacroHub-schema records; drops rows missing core macro fields (many
MenuStat rows are "customizable build" placeholders with a text range like
"340-1175" instead of a numeric value — those are dropped, not estimated).

Usage: ingest_menustat.py --tab-path <menustat_2018.tab> --out-dir <data/fooddb/menustat>
"""
import argparse
import csv
import json
import os
import sys

csv.field_size_limit(sys.maxsize)


def log(msg):
    print(f"[ingest_menustat] {msg}", flush=True)


def to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tab-path", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    kept = []
    scanned = 0
    dropped = 0

    with open(args.tab_path, encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            scanned += 1
            cal = to_float(row.get("Calories_100g"))
            pro = to_float(row.get("Protein_100g"))
            carb = to_float(row.get("Carbohydrates_100g"))
            fat = to_float(row.get("Total_Fat_100g"))
            if cal is None or pro is None or carb is None or fat is None:
                dropped += 1
                continue
            satfat = to_float(row.get("Saturated_Fat_100g")) or 0.0
            fiber = to_float(row.get("Dietary_Fiber_100g")) or 0.0
            restaurant = (row.get("Restaurant") or "").strip()
            item_name = (row.get("Item_Name") or "").strip()
            menu_item_id = (row.get("Menu_Item_ID") or "").strip()
            serving_amount = to_float(row.get("Serving_Size"))
            serving_unit = (row.get("Serving_Size_Unit") or "g").strip() or "g"
            serving_household = (row.get("Serving_Size_household") or "").strip() or None

            rec = {
                "fooddb_id": f"menustat:{menu_item_id}",
                "name": f"{restaurant} {item_name}".strip() if restaurant else item_name,
                "aliases": [item_name] if restaurant and item_name != restaurant else [],
                "per_100g": {
                    "cal": round(cal, 2),
                    "pro": round(pro, 2),
                    "carb": round(carb, 2),
                    "fat": round(fat, 2),
                    "satfat": round(satfat, 2),
                    "fiber": round(fiber, 2),
                },
                "serving": {
                    "amount": serving_amount if serving_amount else 100,
                    "unit": serving_unit,
                    "household": serving_household,
                },
                "source": "menustat",
                "provenance": "label",
                "confidence": 1.0,
                "brand": restaurant or None,
                "category": (row.get("Food_Category") or "").strip() or None,
                "year": row.get("Year"),
            }
            kept.append(rec)

    log(f"scan complete: {scanned} rows scanned, {len(kept)} kept, {dropped} dropped "
        f"(missing core macro fields — mostly 'customizable build' placeholder rows)")

    out_path = os.path.join(args.out_dir, "menustat.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "shard": "menustat",
            "source": "menustat",
            "license": "public_free_no_restriction_noted",
            "note": "Sourced from Harvard Dataverse doi:10.7910/DVN/K4NYTR (2018 panel), NOT "
                    "menustat.org directly — that domain has lapsed/redirects elsewhere as of "
                    "this build. See this script's module docstring.",
            "count": len(kept),
            "records": kept,
        }, f, indent=2)
    log(f"wrote {out_path}: {len(kept)} records")


if __name__ == "__main__":
    main()
