#!/usr/bin/env python3
"""Fetch Open-Meteo hourly forecast for a coordinate and date.

Usage:
  python open_meteo_forecast.py 35.6586 139.7454 2026-07-10 Asia/Tokyo
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("Usage: open_meteo_forecast.py <lat> <lng> <YYYY-MM-DD> [timezone]")
    lat, lng, date = sys.argv[1], sys.argv[2], sys.argv[3]
    timezone = sys.argv[4] if len(sys.argv) > 4 else "auto"
    params = {
        "latitude": lat,
        "longitude": lng,
        "timezone": timezone,
        "start_date": date,
        "end_date": date,
        "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "anime-pilgrimage-skill/0.1"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    output = {
        "source_url": url,
        "raw": data,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
