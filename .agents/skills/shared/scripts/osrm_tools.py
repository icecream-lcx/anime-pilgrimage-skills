#!/usr/bin/env python3
"""OSRM/OpenStreetMap rough routing helper.

Commands:
  route --origin-lat 35.66 --origin-lng 139.66 --destination-lat 35.67 --destination-lng 139.67 --profile foot

Environment:
  OSRM_BASE_URL optional. Default: https://router.project-osrm.org

Notes:
  - Coordinates are passed to OSRM as longitude,latitude in the URL.
  - Use this only for rough walk/drive/cycle estimates.
  - Public OSRM demo servers may be rate-limited and do not provide Google real-time traffic,
    Google business data, ratings, price levels, or reliable public transit schedules.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "https://router.project-osrm.org"
PROFILE_MAP = {
    "foot": "foot",
    "walk": "foot",
    "walking": "foot",
    "car": "car",
    "drive": "car",
    "driving": "car",
    "bike": "bike",
    "bicycle": "bike",
    "cycling": "bike",
}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def google_maps_url(origin: str, destination: str, travelmode: str = "walking") -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        + "&origin=" + urllib.parse.quote(origin)
        + "&destination=" + urllib.parse.quote(destination)
        + "&travelmode=" + urllib.parse.quote(travelmode)
    )


def osrm_route(args: argparse.Namespace) -> dict[str, Any]:
    base_url = os.getenv("OSRM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    profile = PROFILE_MAP.get(args.profile.lower(), args.profile.lower())
    origin = f"{args.origin_lat},{args.origin_lng}"
    destination = f"{args.destination_lat},{args.destination_lng}"
    straight_km = haversine_km(args.origin_lat, args.origin_lng, args.destination_lat, args.destination_lng)
    gmaps_walk = google_maps_url(origin, destination, "walking")
    gmaps_transit = google_maps_url(origin, destination, "transit")

    result: dict[str, Any] = {
        "provider": "osrm_openstreetmap",
        "api_available": False,
        "profile": profile,
        "straight_line_distance_km": round(straight_km, 3),
        "google_maps_walking_url": gmaps_walk,
        "google_maps_transit_url": gmaps_transit,
        "warning": "OSRM/OpenStreetMap estimates are rough and do not include Google real-time routes, business opening hours, ratings, price levels, or public transit schedules.",
    }

    coords = f"{args.origin_lng},{args.origin_lat};{args.destination_lng},{args.destination_lat}"
    url = f"{base_url}/route/v1/{profile}/{coords}?overview=false&steps=false&alternatives=false"
    try:
        with urllib.request.urlopen(url, timeout=args.timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        route = (raw.get("routes") or [{}])[0]
        distance_m = route.get("distance")
        duration_s = route.get("duration")
        result.update({
            "api_available": True,
            "osrm_url": url,
            "distance_meters": distance_m,
            "distance_km": round(float(distance_m) / 1000, 3) if distance_m is not None else None,
            "duration_seconds": duration_s,
            "duration_minutes": round(float(duration_s) / 60, 1) if duration_s is not None else None,
            "raw_code": raw.get("code"),
        })
    except Exception as exc:  # noqa: BLE001
        result.update({
            "api_available": False,
            "error": str(exc),
            "distance_km": round(straight_km, 3),
            "duration_minutes": None,
            "fallback": "Used straight-line distance only. Manually confirm route in Google Maps or another map app.",
        })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("route")
    r.add_argument("--origin-lat", type=float, required=True)
    r.add_argument("--origin-lng", type=float, required=True)
    r.add_argument("--destination-lat", type=float, required=True)
    r.add_argument("--destination-lng", type=float, required=True)
    r.add_argument("--profile", default="foot", choices=["foot", "walk", "walking", "car", "drive", "driving", "bike", "bicycle", "cycling"])
    r.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()
    if args.cmd == "route":
        print(json.dumps(osrm_route(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
