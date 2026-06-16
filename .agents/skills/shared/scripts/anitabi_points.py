#!/usr/bin/env python3
"""Fetch and normalize Anitabi pilgrimage points for a Bangumi subject ID.

Usage:
  python anitabi_points.py 403020 --have-image
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from typing import Any


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "anime-pilgrimage-skill/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def first_value(obj: dict, names: list[str]) -> Any:
    for name in names:
        if name in obj and obj[name] not in (None, ""):
            return obj[name]
    return None


def as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_geo(obj: dict) -> tuple[float | None, float | None]:
    """Return latitude and longitude. Anitabi detail API commonly uses geo=[lat,lng]."""
    geo = obj.get("geo")
    if isinstance(geo, list) and len(geo) >= 2:
        return as_float(geo[0]), as_float(geo[1])
    if isinstance(geo, dict):
        lat = first_value(geo, ["lat", "latitude", "y"])
        lng = first_value(geo, ["lng", "lon", "longitude", "x"])
        return as_float(lat), as_float(lng)
    lat = first_value(obj, ["lat", "latitude", "y", "gpsLat"])
    lng = first_value(obj, ["lng", "lon", "longitude", "x", "gpsLng"])
    return as_float(lat), as_float(lng)


def flatten_points(data: Any) -> list[dict]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["points", "data", "items", "result"]:
            val = data.get(key)
            if isinstance(val, list):
                return val
        # Some APIs return nested city/episode groups. Collect dicts that look like points.
        found: list[dict] = []
        def walk(x: Any) -> None:
            if isinstance(x, dict):
                lat, lng = extract_geo(x)
                if lat is not None and lng is not None:
                    found.append(x)
                else:
                    for v in x.values():
                        walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(data)
        return found
    return []


def tag_point(name: str, address: str | None) -> list[str]:
    text = f"{name} {address or ''}"
    tags = []
    rules = {
        "restaurant": ["餐", "食堂", "拉面", "咖啡", "cafe", "café", "居酒屋", "饭", "店"],
        "attraction": ["公园", "神社", "寺", "博物馆", "美术馆", "展望", "塔", "城"],
        "station": ["駅", "站", "station"],
        "school": ["学校", "高校", "大学", "中学"],
        "bridge": ["桥", "橋", "bridge"],
        "street": ["通", "街", "路", "坂"],
        "shop": ["商店", "店", "便利店", "书店", "ショップ", "shop"],
    }
    lower = text.lower()
    for tag, words in rules.items():
        if any(w.lower() in lower for w in words):
            tags.append(tag)
    return tags or ["unknown"]


def normalize_point(p: dict) -> dict | None:
    lat, lng = extract_geo(p)
    if lat is None or lng is None:
        return None
    name = str(first_value(p, ["cn", "name", "title", "label", "address"]) or f"Point {p.get('id', '')}").strip()
    address = first_value(p, ["address", "addr", "location"])
    image_url = first_value(p, ["image", "imageURL", "imageUrl", "cover", "screenshot", "photo"])
    origin = first_value(p, ["origin", "imageOrigin", "source"])
    origin_url = first_value(p, ["originURL", "originUrl", "sourceUrl", "sourceURL"])
    episode = first_value(p, ["ep", "episode", "epName", "chapter"])
    scene_time = first_value(p, ["s", "time", "sceneTime", "timestamp"])
    pid = str(first_value(p, ["id", "pointId", "uuid"]) or f"{lat},{lng}")
    return {
        "id": pid,
        "name": name,
        "lat": lat,
        "lng": lng,
        "address": address,
        "episode": str(episode) if episode is not None else None,
        "scene_time": str(scene_time) if scene_time is not None else None,
        "image_url": image_url,
        "origin": origin,
        "origin_url": origin_url,
        "tags": tag_point(name, address),
        "source_urls": [origin_url] if origin_url else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bangumi_id", type=int)
    parser.add_argument("--have-image", action="store_true")
    args = parser.parse_args()
    qs = "?" + urllib.parse.urlencode({"haveImage": "true"}) if args.have_image else ""
    url = f"https://api.anitabi.cn/bangumi/{args.bangumi_id}/points/detail{qs}"
    data = fetch_json(url)
    raw_points = flatten_points(data)
    points = [x for x in (normalize_point(p) for p in raw_points if isinstance(p, dict)) if x]
    output = {
        "stage": "pilgrimage_points",
        "work": {"bangumi_id": args.bangumi_id, "title": ""},
        "points": points,
        "point_count": len(points),
        "filter_notes": [f"source={url}", "Preserve origin/origin_url attribution when showing reference images."],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
