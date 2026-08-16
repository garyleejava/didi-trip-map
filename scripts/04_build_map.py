#!/usr/bin/env python3
"""Build the standalone Didi trip map HTML from CSV data."""

import csv
import json
import argparse
import os
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_TRIP_CSV = ROOT / "outputs" / "trips.csv"
DEFAULT_LOC_CSV = ROOT / "outputs" / "locations.csv"
DEFAULT_TEMPLATE = ROOT / "template" / "map_template.html"
DEFAULT_OUTPUT = ROOT / "outputs" / "trip-map.html"

CITY_NORM = {
    "北京": "北京",
    "北京市": "北京",
    "上海": "上海",
    "上海市": "上海",
    "重庆": "重庆",
    "重庆市": "重庆",
    "秦皇岛": "秦皇岛",
    "秦皇岛市": "秦皇岛",
    "大连": "大连",
    "大连市": "大连",
    "洛阳": "洛阳",
    "洛阳市": "洛阳",
    "保定": "保定",
    "保定市": "保定",
    "青岛": "青岛",
    "青岛市": "青岛",
    "西安": "西安",
    "西安市": "西安",
    "唐山": "唐山",
    "唐山市": "唐山",
    "石家庄": "石家庄",
    "石家庄市": "石家庄",
    "渭南": "渭南",
    "渭南市": "渭南",
    "南京": "南京",
    "南京市": "南京",
    "杭州": "杭州",
    "杭州市": "杭州",
    "大同": "大同",
    "大同市": "大同",
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


def parse_datetime(value):
    """Return year, month, day, and ISO date from a common CSV datetime string."""
    text = (value or "").strip()
    if not text:
        return "", "", "", ""
    try:
        dt = __import__("datetime").datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            dt = __import__("datetime").datetime.strptime(text[:16], "%Y-%m-%d %H:%M")
        except ValueError:
            return "", "", "", ""
    return (
        str(dt.year),
        f"{dt.month:02d}",
        f"{dt.day:02d}",
        f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Build a standalone Didi trip map HTML file."
    )
    parser.add_argument("--trips", type=pathlib.Path, default=DEFAULT_TRIP_CSV)
    parser.add_argument("--locations", type=pathlib.Path, default=DEFAULT_LOC_CSV)
    parser.add_argument("--template", type=pathlib.Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--key", default="")
    parser.add_argument("--security-code", default="")
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

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
        year, month, day, date = parse_datetime(row.get("上车时间"))
        od_key = (
            f"{city_norm}|{o['name'] if o else origin}|{d['name'] if d else dest}"
            if o and d
            else ""
        )
        quality = (
            "ok"
            if o and d
            else "missing_origin"
            if not o and d
            else "missing_dest"
            if o and not d
            else "missing_both"
        )
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
                "pickupYear": year,
                "pickupMonth": f"{year}-{month}" if year else "",
                "pickupDate": date,
                "city": city,
                "cityNorm": city_norm,
                "origin": origin,
                "dest": dest,
                "distance": as_number(row.get("里程_公里")),
                "distanceNum": as_number(row.get("里程_公里")),
                "amount": as_number(row.get("金额_元")),
                "amountNum": as_number(row.get("金额_元")),
                "note": (row.get("备注") or "").strip(),
                "o": o,
                "d": d,
                "odKey": od_key,
                "dataQuality": quality,
            }
        )

    payload = json.dumps(trips, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    js_string = json.dumps(payload, ensure_ascii=False)

    api_key = (args.key or os.environ.get("AMAP_KEY") or "").strip()
    security_code = (
        args.security_code or os.environ.get("AMAP_SECURITY_JS_CODE") or ""
    ).strip()
    with open(args.template, encoding="utf-8") as f:
        template = f.read()
    html = template.replace(
        "window.__TRIPS__ = null;",
        "window.__TRIPS__ = JSON.parse(" + js_string + ");",
    )
    js_key = json.dumps(api_key, ensure_ascii=False)
    html = html.replace(
        'window.__AMAP_KEY__ = "";',
        "window.__AMAP_KEY__ = " + js_key + ";",
    )
    js_security_code = json.dumps(security_code, ensure_ascii=False)
    html = html.replace(
        'window.__AMAP_SECURITY_JS_CODE__ = "";',
        "window.__AMAP_SECURITY_JS_CODE__ = " + js_security_code + ";",
    )
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
