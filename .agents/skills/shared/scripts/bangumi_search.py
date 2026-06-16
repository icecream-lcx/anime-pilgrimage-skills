#!/usr/bin/env python3
"""Search Bangumi subjects and emit normalized anime candidates.

Usage:
  python bangumi_search.py "孤独摇滚"

Environment:
  BANGUMI_ACCESS_TOKEN optional
  BANGUMI_USER_AGENT recommended
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.bgm.tv/v0/search/subjects"


def request_json(url: str, payload: dict | None = None) -> dict:
    data = None
    method = "GET"
    headers = {
        "Accept": "application/json",
        "User-Agent": os.getenv("BANGUMI_USER_AGENT", "anime-pilgrimage-skill/0.1"),
    }
    token = os.getenv("BANGUMI_ACCESS_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        method = "POST"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body[:500]}") from exc


def normalize_subject(item: dict, rank: int) -> dict:
    tags = item.get("tags") or []
    aliases = []
    infobox = item.get("infobox") or []
    for row in infobox:
        key = str(row.get("key", ""))
        value = row.get("value")
        if key in {"别名", "别称", "英文名", "中文名"}:
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, dict) and v.get("v"):
                        aliases.append(str(v["v"]))
                    elif v:
                        aliases.append(str(v))
            elif value:
                aliases.append(str(value))
    return {
        "rank": rank,
        "bangumi_id": item.get("id"),
        "title": item.get("name_cn") or item.get("name") or "",
        "original_title": item.get("name") or None,
        "aliases": sorted(set(a for a in aliases if a)),
        "type": "anime" if item.get("type") == 2 else str(item.get("type") or "unknown"),
        "date": item.get("date"),
        "summary": item.get("summary"),
        "score": (item.get("rating") or {}).get("score"),
        "source_urls": [f"https://bgm.tv/subject/{item.get('id')}"] if item.get("id") else [],
        "tags": [t.get("name") for t in tags if isinstance(t, dict) and t.get("name")],
    }


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: bangumi_search.py <keyword> [limit]")
    keyword = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    payload = {
        "keyword": keyword,
        "sort": "match",
        "filter": {"type": [2]},
    }
    data = request_json(API_URL, payload)
    items = data.get("data") or []
    candidates = [normalize_subject(item, i + 1) for i, item in enumerate(items[:limit])]
    output = {
        "stage": "anime_candidates",
        "query": keyword,
        "candidates": candidates,
        "needs_user_confirmation": True,
        "confirmation_question": "请确认以上哪个 Bangumi 条目是你要规划圣地巡礼的作品。",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
