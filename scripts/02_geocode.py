#!/usr/bin/env python3
"""Batch geocode Didi start/end places with AMap Web Service API."""

import csv
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import argparse


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "outputs" / "trips.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "locations_raw.csv"
DEFAULT_SUMMARY = ROOT / "outputs" / "geocode_summary.json"

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

SUFFIXES = sorted(
    [
        "网约车上车点",
        "停车楼负二层",
        "地上东停车场",
        "地下停车场",
        "东门售票处",
        "北进站口",
        "南进站口",
        "东南门",
        "东北门",
        "西南门",
        "西北门",
        "南2门",
        "北2门",
        "南1门",
        "北1门",
        "南3门",
        "西2门",
        "西1门",
        "东4门",
        "东2门",
        "西3门",
        "西南2门",
        "进站口",
        "出站口",
        "售票处",
        "检票处",
        "检票口",
        "公交站",
        "上车点",
        "下车点",
        "停车位",
        "停车场",
        "出入口",
        "安检口",
        "游客中心",
        "接送点",
        "站前广场",
        "中心区",
        "北广场",
        "西北侧",
        "东北侧",
        "西南侧",
        "东南侧",
        "南侧",
        "北侧",
        "西侧",
        "东侧",
        "附近",
        "人行门",
        "主路",
        "辅路",
        "南门",
        "北门",
        "东门",
        "西门",
    ],
    key=len,
    reverse=True,
)


def norm_city(raw):
    raw = (raw or "").strip()
    return CITY_NORM.get(raw, raw.replace("市", ""))


def normalize(text):
    return re.sub(r"[\s|·•,，;；()（）\-—_/\\、]+", "", text or "").lower()


def lcs_len(a, b):
    m, n = len(a), len(b)
    if not m or not n:
        return 0
    prev = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        cur = [0] * (n + 1)
        ai = a[i - 1]
        for j in range(1, n + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def strip_suffix(name):
    name = re.sub(r"[（(][^()（）]*[)）]", "", name).strip()
    changed = True
    while changed:
        changed = False
        for suf in SUFFIXES:
            if name.endswith(suf) and len(name) > len(suf) + 1:
                name = name[: -len(suf)].rstrip("-—–").strip()
                changed = True
                break
        m = re.search(r"[A-Z]\d*口$", name)
        if m and len(name) > len(m.group(0)) + 1:
            name = name[: m.start()].rstrip("-—–").strip()
            changed = True
    return name or name


def base_name(orig):
    parts = [p.strip() for p in orig.split("|") if p.strip()]
    cand = parts[-1] if parts else orig
    return strip_suffix(cand)


def query_candidates(orig):
    parts = [p.strip() for p in orig.split("|") if p.strip()]
    base = base_name(orig)
    last = parts[-1] if parts else orig
    out = [base]
    if last != base:
        out.append(last)
    if orig != base and orig != last:
        out.append(orig)
    # De-duplicate while preserving order.
    seen = set()
    deduped = []
    for q in out:
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped


def api_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_place(key, city, keyword):
    params = {
        "key": key,
        "keywords": keyword,
        "city": city,
        "citylimit": "true",
        "offset": "8",
        "page": "1",
        "extensions": "base",
        "output": "json",
    }
    url = "https://restapi.amap.com/v3/place/text?" + urllib.parse.urlencode(params)
    return api_get(url)


def geocode_address(key, city, address):
    params = {
        "key": key,
        "address": address,
        "city": city,
        "output": "json",
    }
    url = "https://restapi.amap.com/v3/geocode/geo?" + urllib.parse.urlencode(params)
    return api_get(url)


def score_poi(poi, orig, base):
    name_n = normalize(poi.get("name") or "")
    addr_n = normalize(poi.get("address") or "")
    orig_n = normalize(orig)
    base_n = normalize(base)
    if not base_n:
        return 0
    score = min(lcs_len(name_n, base_n), 30) * 2
    score += min(lcs_len(addr_n, base_n), 30)
    if base_n in name_n or name_n in base_n:
        score += 12
    if base_n in addr_n or addr_n in base_n:
        score += 8
    if base_n in orig_n or orig_n in base_n:
        score += 6
    ptype = normalize(poi.get("type") or "")
    if "地铁站" in base and "地铁" not in name_n:
        score -= 4
    if "公交站" in base and "公交" not in name_n:
        score -= 3
    if "道路" in ptype or "道路附属" in ptype:
        score -= 2
    return score


def best_poi(key, city, orig):
    base = base_name(orig)
    best = None
    best_score = 0
    tried = []
    for q in query_candidates(orig):
        tried.append(q)
        data = search_place(key, city, q)
        if data.get("status") != "1":
            continue
        pois = data.get("pois") or []
        for poi in pois:
            s = score_poi(poi, orig, q if q != orig else base)
            if s > best_score:
                best_score = s
                best = poi
    if best:
        best["_score"] = best_score
        best["_query"] = tried
        return best
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Batch geocode Didi trip places with the AMap Web Service API."
    )
    parser.add_argument("--key", default="")
    parser.add_argument("--input", type=pathlib.Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=pathlib.Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    key = (args.key or os.environ.get("AMAP_KEY") or "").strip()
    if not key:
        print("AMAP_KEY env var is required", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with open(args.input, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    seen = {}
    for row in rows:
        city = norm_city(row.get("城市"))
        for role in ("起点", "终点"):
            name = (row.get(role) or "").strip()
            if not name:
                continue
            seen.setdefault((city, role, name), []).append(row)

    results = []
    failures = []
    start = time.time()
    for i, ((city, role, name), records) in enumerate(
        sorted(seen.items(), key=lambda x: (x[0][0], x[0][1], x[0][2]))
    ):
        count = len(records)
        if name in ("当前位置", "当前位置 ") or "当前位置" in name:
            results.append(
                {
                    "city": city,
                    "role": role,
                    "name": name,
                    "count": count,
                    "query": "",
                    "matched_name": "",
                    "address": "",
                    "lat": "",
                    "lng": "",
                    "score": "",
                    "status": "skipped_current_location",
                }
            )
            print(f"{i+1}/{len(seen)} skip 当前位置 {city} {role} x{count}", flush=True)
            continue

        poi = None
        try:
            poi = best_poi(key, city, name)
        except Exception as exc:
            failures.append(
                {
                    "city": city,
                    "role": role,
                    "name": name,
                    "count": count,
                    "error": repr(exc),
                }
            )
            print(
                f"{i+1}/{len(seen)} ERROR {city} {role} x{count} {name}: {exc!r}",
                flush=True,
            )
            time.sleep(0.8)
            continue

        if poi:
            loc = (poi.get("location") or "").split(",")
            results.append(
                {
                    "city": city,
                    "role": role,
                    "name": name,
                    "count": count,
                    "query": ",".join(poi.get("_query", [])),
                    "matched_name": poi.get("name") or "",
                    "address": poi.get("address") or "",
                    "lat": loc[1] if len(loc) == 2 else "",
                    "lng": loc[0] if len(loc) == 2 else "",
                    "score": poi.get("_score", ""),
                    "status": "ok",
                }
            )
            print(
                f"{i+1}/{len(seen)} OK {city} {role} x{count} {name} -> "
                f"{poi.get('name')} {poi.get('location')}",
                flush=True,
            )
        else:
            # Fallback: raw geocoder.
            try:
                data = geocode_address(key, city, name)
                geos = data.get("geocodes") or []
                if geos:
                    loc = (geos[0].get("location") or "").split(",")
                    results.append(
                        {
                            "city": city,
                            "role": role,
                            "name": name,
                            "count": count,
                            "query": "geocode",
                            "matched_name": geos[0].get("formatted_address") or "",
                            "address": geos[0].get("formatted_address") or "",
                            "lat": loc[1] if len(loc) == 2 else "",
                            "lng": loc[0] if len(loc) == 2 else "",
                            "score": "",
                            "status": "geocode",
                        }
                    )
                    print(
                        f"{i+1}/{len(seen)} GEO {city} {role} x{count} {name} -> "
                        f"{geos[0].get('formatted_address')} {geos[0].get('location')}",
                        flush=True,
                    )
                    continue
            except Exception as exc:
                print(f"geocode fallback error {name}: {exc!r}", flush=True)
            results.append(
                {
                    "city": city,
                    "role": role,
                    "name": name,
                    "count": count,
                    "query": ",".join(query_candidates(name)),
                    "matched_name": "",
                    "address": "",
                    "lat": "",
                    "lng": "",
                    "score": "",
                    "status": "not_found",
                }
            )
            failures.append(
                {
                    "city": city,
                    "role": role,
                    "name": name,
                    "count": count,
                }
            )
            print(
                f"{i+1}/{len(seen)} MISS {city} {role} x{count} {name}",
                flush=True,
            )
        time.sleep(0.18)

    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "city",
                "role",
                "name",
                "count",
                "query",
                "matched_name",
                "address",
                "lat",
                "lng",
                "score",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    summary = {
        "total_unique": len(seen),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "geocode": sum(1 for r in results if r["status"] == "geocode"),
        "skipped": sum(1 for r in results if r["status"] == "skipped_current_location"),
        "not_found": sum(1 for r in results if r["status"] == "not_found"),
        "failures": failures,
        "seconds": round(time.time() - start, 1),
    }
    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
