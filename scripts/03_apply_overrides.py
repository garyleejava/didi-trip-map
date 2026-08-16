#!/usr/bin/env python3
"""Apply optional manual coordinate overrides before building the map."""

import argparse
import csv
import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_overrides(path):
    if not path or not path.exists():
        return {}
    spec = importlib.util.spec_from_file_location("user_overrides", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "OVERRIDES", {})


def main():
    parser = argparse.ArgumentParser(
        description="Apply optional manual coordinate overrides to geocoded locations."
    )
    parser.add_argument("--input", type=pathlib.Path, default=ROOT / "outputs" / "locations_raw.csv")
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "outputs" / "locations.csv")
    parser.add_argument("--overrides", type=pathlib.Path, default=ROOT / "overrides" / "user_overrides.py")
    args = parser.parse_args()

    overrides = load_overrides(args.overrides)
    with open(args.input, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    stats = {"total": 0, "overridden": 0, "located": 0, "skipped": 0}
    for row in rows:
        stats["total"] += 1
        key = (row["city"], row["role"], row["name"])
        override = overrides.get(key)
        out = {
            "city": row["city"],
            "role": row["role"],
            "name": row["name"],
            "count": row["count"],
            "lat": "",
            "lng": "",
            "matched_name": "",
            "address": "",
            "source": "amap",
            "note": "",
        }
        if row.get("status") == "skipped_current_location":
            out["note"] = "起点为当前位置，未定位"
            stats["skipped"] += 1
            out_rows.append(out)
            continue
        if override:
            out["lat"] = str(override["lat"])
            out["lng"] = str(override["lng"])
            out["matched_name"] = override.get("matched_name", "")
            out["address"] = override.get("address", "")
            out["note"] = override.get("note", "")
            out["source"] = "manual"
            stats["overridden"] += 1
            stats["located"] += 1
            out_rows.append(out)
            continue
        out["lat"] = row.get("lat", "")
        out["lng"] = row.get("lng", "")
        out["matched_name"] = row.get("matched_name", "")
        out["address"] = row.get("address", "")
        if out["lat"] and out["lng"]:
            stats["located"] += 1
        out_rows.append(out)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "city",
                "role",
                "name",
                "count",
                "lat",
                "lng",
                "matched_name",
                "address",
                "source",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)
    print(stats)


if __name__ == "__main__":
    main()
