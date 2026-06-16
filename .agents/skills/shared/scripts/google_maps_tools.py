#!/usr/bin/env python3
"""Minimal Google Maps helper for route and place queries.

Commands:
  route  --origin "place or lat,lng" --destination "place or lat,lng" --mode WALK
  place  --query "restaurant name near Shinjuku" [--lat 35.69 --lng 139.70]

Environment:
  GOOGLE_MAPS_API_KEY optional.

If no key is set, this script returns Google Maps URLs instead of API details.
In URL-only mode it cannot retrieve Google real-time routes, opening hours,
ratings, business status, or price levels.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from typing import Any

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
NO_KEY_WARNING_ZH = "未配置 GOOGLE_MAPS_API_KEY，将使用 Google Maps URL 链接模式；无法自动获取 Google 的实时路线、营业时间、评分和价格等级，只能提供搜索链接或标注为需要人工确认。"

MODE_TO_URL = {
    "WALK": "walking",
    "DRIVE": "driving",
    "BICYCLE": "bicycling",
    "TRANSIT": "transit",
    "TWO_WHEELER": "driving",
}


def maps_url(
    origin: str | None = None,
    destination: str | None = None,
    query: str | None = None,
    mode: str | None = None,
    waypoints: list[str] | None = None,
) -> str:
    if query:
        # For exact Anitabi point links, pass only "lat,lng" as query.
        # Do not append names like "lat,lng (scene name)", because Google Maps
        # may treat it as a text search and report that the place cannot be found.
        return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)
    if origin and destination:
        params = {
            "api": "1",
            "origin": origin,
            "destination": destination,
        }
        if mode:
            params["travelmode"] = MODE_TO_URL.get(mode.upper(), mode.lower())
        if waypoints:
            params["waypoints"] = "|".join(waypoints)
        return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params)
    return "https://www.google.com/maps"


def _coord_text(point: dict[str, Any]) -> str | None:
    """Return a Google Maps friendly coordinate string from a point dict."""
    lat = point.get("lat") if point.get("lat") is not None else point.get("latitude")
    lng = point.get("lng") if point.get("lng") is not None else point.get("lon") or point.get("longitude")
    if lat is None or lng is None:
        return None
    return f"{lat},{lng}"


def build_route_urls_from_points(points: list[dict[str, Any]], mode: str = "WALK", max_points_per_url: int = 11) -> dict[str, Any]:
    """Build Google Maps route URL(s) from ordered points.

    Google Maps URL-only mode cannot reliably accept unlimited waypoints. This helper
    therefore creates one full URL when the route is short enough, and chunked URLs
    when the itinerary has many stops. Each chunk keeps the last stop as the start of
    the next chunk so users can follow the whole route in order.
    """
    coords: list[str] = []
    names: list[str] = []
    for p in points:
        c = _coord_text(p)
        if c:
            coords.append(c)
            names.append(str(p.get("name") or p.get("title") or c))
    if len(coords) < 2:
        return {
            "overall_map_url": None,
            "overall_map_url_parts": [],
            "stop_count": len(coords),
            "warning": "少于两个有效坐标，无法生成整条路线链接。",
        }

    max_points_per_url = max(2, int(max_points_per_url or 10))

    def one_url(chunk: list[str]) -> str:
        return maps_url(
            origin=chunk[0],
            destination=chunk[-1],
            mode=mode,
            waypoints=chunk[1:-1] if len(chunk) > 2 else None,
        )

    if len(coords) <= max_points_per_url:
        url = one_url(coords)
        return {
            "overall_map_url": url,
            "overall_map_url_parts": [{"part": 1, "from": names[0], "to": names[-1], "stop_count": len(coords), "map_url": url}],
            "stop_count": len(coords),
            "warning": None,
        }

    parts = []
    start = 0
    part_no = 1
    # Keep overlap: the final point of each chunk becomes the first point of the next.
    while start < len(coords) - 1:
        end = min(start + max_points_per_url, len(coords))
        chunk = coords[start:end]
        parts.append({
            "part": part_no,
            "from": names[start],
            "to": names[end - 1],
            "stop_count": len(chunk),
            "map_url": one_url(chunk),
        })
        if end >= len(coords):
            break
        start = end - 1
        part_no += 1

    return {
        "overall_map_url": parts[0]["map_url"] if parts else None,
        "overall_map_url_parts": parts,
        "stop_count": len(coords),
        "warning": "点位较多，Google Maps URL 无法稳定承载无限途经点，已按顺序拆分为多个路线链接。",
    }


def request_json(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def compute_route(args: argparse.Namespace) -> dict:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        return {
            "api_available": False,
            "map_mode": "google_maps_url_only",
            "map_url": maps_url(args.origin, args.destination, mode=args.mode),
            "travel_mode": args.mode.upper(),
            "duration_text": None,
            "distance_text": None,
            "requires_manual_confirmation": True,
            "warning": NO_KEY_WARNING_ZH,
        }
    payload = {
        "origin": {"address": args.origin},
        "destination": {"address": args.destination},
        "travelMode": args.mode.upper(),
        "routingPreference": "TRAFFIC_AWARE" if args.mode.upper() == "DRIVE" else None,
        "languageCode": args.language,
        "units": "METRIC",
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps.localizedValues,routes.legs.steps.navigationInstruction",
    }
    return {
        "api_available": True,
        "map_mode": "google_api",
        "raw": request_json(ROUTES_URL, payload, headers),
        "map_url": maps_url(args.origin, args.destination, mode=args.mode),
    }


def search_place(args: argparse.Namespace) -> dict:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        return {
            "api_available": False,
            "map_mode": "google_maps_url_only",
            "google_maps_url": maps_url(query=args.query),
            "opening_hours": None,
            "rating": None,
            "price_level": None,
            "business_status": None,
            "requires_manual_confirmation": True,
            "warning": NO_KEY_WARNING_ZH,
        }
    payload: dict[str, Any] = {"textQuery": args.query, "languageCode": args.language}
    if args.lat is not None and args.lng is not None:
        payload["locationBias"] = {
            "circle": {
                "center": {"latitude": args.lat, "longitude": args.lng},
                "radius": float(args.radius),
            }
        }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.googleMapsUri,places.websiteUri,places.regularOpeningHours,places.priceLevel,places.rating,places.businessStatus",
    }
    return {
        "api_available": True,
        "map_mode": "google_api",
        "raw": request_json(PLACES_SEARCH_URL, payload, headers),
        "google_maps_url": maps_url(query=args.query),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("route")
    r.add_argument("--origin", required=True)
    r.add_argument("--destination", required=True)
    r.add_argument("--mode", default="WALK", choices=["WALK", "DRIVE", "BICYCLE", "TRANSIT", "TWO_WHEELER"])
    r.add_argument("--language", default="zh-CN")
    m = sub.add_parser("multi-route-url")
    m.add_argument("--points-json", required=True, help="JSON array of ordered points, or path to a JSON file containing points/stops/routes[0].stops")
    m.add_argument("--mode", default="WALK", choices=["WALK", "DRIVE", "BICYCLE", "TRANSIT", "TWO_WHEELER"])
    m.add_argument("--max-points-per-url", type=int, default=11)
    p = sub.add_parser("place")
    p.add_argument("--query", required=True)
    p.add_argument("--lat", type=float)
    p.add_argument("--lng", type=float)
    p.add_argument("--radius", type=float, default=500)
    p.add_argument("--language", default="zh-CN")
    args = parser.parse_args()
    if args.cmd == "route":
        result = compute_route(args)
    elif args.cmd == "place":
        result = search_place(args)
    else:
        raw = args.points_json
        path = raw if len(raw) < 260 else None
        try:
            if path and os.path.exists(path):
                data = json.load(open(path, "r", encoding="utf-8"))
            else:
                data = json.loads(raw)
            if isinstance(data, dict):
                points = data.get("points") or data.get("stops") or ((data.get("routes") or [{}])[0].get("stops")) or []
            else:
                points = data
            result = build_route_urls_from_points(points, mode=args.mode, max_points_per_url=args.max_points_per_url)
        except Exception as exc:
            result = {"overall_map_url": None, "overall_map_url_parts": [], "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
