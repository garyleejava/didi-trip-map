#!/usr/bin/env python3
"""Build the static Leaflet demo page from sample data."""

import argparse
import csv
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent

CITY_NORM = {
    "北京": "北京",
    "北京市": "北京",
    "上海": "上海",
    "上海市": "上海",
    "重庆": "重庆",
    "重庆市": "重庆",
    "成都": "成都",
    "成都市": "成都",
}


def norm_city(raw):
    raw = (raw or "").strip()
    return CITY_NORM.get(raw, raw.replace("市", ""))


def as_number(value):
    try:
        n = float(value)
        if n != n or n in (float("inf"), float("-inf")):
            return None
        return round(n, 2)
    except (TypeError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Build the static Leaflet demo page from sample data."
    )
    parser.add_argument("--trips", type=pathlib.Path, default=ROOT / "sample" / "trips.csv")
    parser.add_argument("--locations", type=pathlib.Path, default=ROOT / "sample" / "locations.csv")
    parser.add_argument("--template", type=pathlib.Path, default=ROOT / "docs" / "demo_template.html")
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "docs" / "index.html")
    args = parser.parse_args()

    with open(args.trips, encoding="utf-8-sig") as f:
        trips_raw = list(csv.DictReader(f))
    with open(args.locations, encoding="utf-8-sig") as f:
        locs = list(csv.DictReader(f))

    lookup = {}
    for loc in locs:
        lookup[(loc["city"], loc["role"], loc["name"])] = loc

    trips = []
    located = 0
    missing = 0
    for index, row in enumerate(trips_raw):
        city = (row.get("城市") or "").strip()
        city_norm = norm_city(city)
        origin = (row.get("起点") or "").strip()
        dest = (row.get("终点") or "").strip()

        def place(city_key, role, name):
            loc = lookup.get((city_key, role, name))
            if not loc or not loc.get("lat") or not loc.get("lng"):
                return None
            return {
                "name": name,
                "lat": float(loc["lat"]),
                "lng": float(loc["lng"]),
                "matched_name": loc.get("matched_name") or "",
                "address": loc.get("address") or "",
            }

        o = place(city_norm, "起点", origin)
        d = place(city_norm, "终点", dest)
        if o:
            located += 1
        if not o and origin:
            missing += 1
        if d:
            located += 1
        if not d and dest:
            missing += 1

        trips.append(
            {
                "id": index,
                "source": (row.get("来源") or "").strip(),
                "file": (row.get("来源文件") or "").strip(),
                "sourceIndex": (row.get("来源序号") or "").strip(),
                "car": (row.get("车型") or "").strip(),
                "carCat": (row.get("车型类别") or "").strip(),
                "pickup": (row.get("上车时间") or "").strip(),
                "arrival": (row.get("到达时间") or "").strip(),
                "city": city,
                "cityNorm": city_norm,
                "origin": origin,
                "dest": dest,
                "distance": as_number(row.get("里程_公里")),
                "amount": as_number(row.get("金额_元")),
                "note": (row.get("备注") or "").strip(),
                "o": o,
                "d": d,
            }
        )

    payload = json.dumps(trips, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    js_string = json.dumps(payload, ensure_ascii=False)

    with open(args.template, encoding="utf-8") as f:
        template = f.read()
    html = template.replace(
        "window.__TRIPS__ = null;",
        "window.__TRIPS__ = JSON.parse(" + js_string + ");",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(
        {
            "trips": len(trips),
            "located_place_refs": located,
            "missing_place_refs": missing,
            "bytes": len(html.encode("utf-8")),
        }
    )


if __name__ == "__main__":
    main()
