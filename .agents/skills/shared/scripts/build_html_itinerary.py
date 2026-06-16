#!/usr/bin/env python3
"""Build editable HTML itinerary from a route_weather_plan/enriched_places JSON file.

Usage:
  python build_html_itinerary.py plan.json --output-dir output

v6 route policy:
- Route A / all_points routes include every valid Anitabi coordinate point.
- Route B / time_fit routes keep the time-selected stops in the main table,
  but omitted Anitabi points are shown below and can be added into the Route B
  table by button or drag-and-drop.
- The generated HTML can rebuild Google Maps route links after manual edits.
- Route B can recalculate arrival/departure times after manual edits. Without a
  Google Maps API key, the HTML uses OSRM if available and otherwise falls back
  to a distance-based estimate; public-transit times must still be confirmed in
  Google Maps.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import urllib.parse
from pathlib import Path
from typing import Any


def esc(x: Any) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def js_str(x: Any) -> str:
    return json.dumps("" if x is None else str(x), ensure_ascii=False)


def zh_value(x: Any, default: str = "未知") -> str:
    """Localize common English/internal enum values for the generated Chinese HTML."""
    if x is None:
        return default
    text = str(x).strip()
    if text == "":
        return default
    low = text.lower()
    mapping = {
        "unknown": "未知",
        "none": "无",
        "null": "未知",
        "google_maps_url_only": "仅使用 Google Maps 链接模式",
        "google_api": "Google Maps API 模式",
        "google_maps_api": "Google Maps API 模式",
        "all_points": "全量点位路线",
        "complete_all_points": "全量点位路线",
        "time_fit": "时间适配路线",
        "time_selected": "时间适配路线",
        "selected_subset": "时间适配路线",
        "balanced_time_fit": "均衡时间适配",
        "shortest": "最短路线优先",
        "photo_priority": "拍照优先",
        "meal_priority": "餐饮优先",
        "weather_safe": "天气安全优先",
        "balanced": "均衡规划",
        "all_valid_anitabi_points_included": "已纳入所有有效 Anitabi 点位",
        "time_fit_selected_subset": "按时间筛选的点位子集",
        "scheduled": "已安排",
        "unscheduled": "灵活安排",
        "manual-added": "手动加入",
        "manual_added": "手动加入",
        "walking": "步行",
        "walk": "步行",
        "transit": "公共交通",
        "public_transit": "公共交通",
        "drive": "驾车",
        "driving": "驾车",
        "taxi": "出租车",
        "yes": "是",
        "no": "否",
        "free to visit": "免费参观",
        "free": "免费",
    }
    if low in mapping:
        return mapping[low]
    # Light phrase-level cleanup for internal English identifiers.
    text = text.replace("Route A", "路线 A").replace("Route B", "路线 B")
    text = text.replace("time_fit", "时间适配").replace("balanced_time_fit", "均衡时间适配")
    text = text.replace("all_points", "全量点位")
    text = text.replace("google_maps_url_only", "仅使用 Google Maps 链接模式")
    text = text.replace("unknown", "未知")
    return text


def is_probably_english(text: str) -> bool:
    letters = re.findall(r"[A-Za-z]", text or "")
    return len(letters) >= 8


def translate_weather_summary(text: Any, weather: dict | None = None) -> str:
    """Return a Chinese weather summary for display.

    The upstream route JSON may contain an English natural-language summary.
    This function keeps the HTML Chinese-first without depending on an online
    translation service. It first tries to synthesize a Chinese summary from
    structured hourly/daily data; otherwise it applies conservative phrase
    replacements to common weather wording.
    """
    weather = weather or {}
    # Prefer structured hourly weather if available.
    hourly = weather.get("hourly") or weather.get("hourly_forecast") or []
    if isinstance(hourly, list) and hourly:
        temps = []
        pops = []
        high_rain_time = None
        for h in hourly:
            try:
                temp = h.get("temperature_c") if isinstance(h, dict) else None
                if temp is None:
                    temp = h.get("temperature_2m") if isinstance(h, dict) else None
                if temp is not None:
                    temps.append(float(temp))
            except Exception:
                pass
            try:
                pop = h.get("precipitation_probability") if isinstance(h, dict) else None
                if pop is not None:
                    pop = float(pop)
                    pops.append(pop)
                    if high_rain_time is None and pop >= 60:
                        high_rain_time = str(h.get("time") or "")[11:16] or str(h.get("time") or "")
            except Exception:
                pass
        parts = []
        if temps:
            parts.append(f"气温约 {min(temps):.1f}–{max(temps):.1f}℃")
        if pops:
            max_pop = max(pops)
            if max_pop < 30:
                parts.append("降雨概率较低")
            elif max_pop < 60:
                parts.append(f"最高降雨概率约 {max_pop:.0f}%")
            else:
                if high_rain_time:
                    parts.append(f"{high_rain_time} 前后起降雨概率较高，最高约 {max_pop:.0f}%")
                else:
                    parts.append(f"降雨概率较高，最高约 {max_pop:.0f}%")
        if parts:
            parts.append("户外拍摄建议优先安排在天气较稳定的时段，并在出发前再次确认最新预报。")
            return "；".join(parts)

    text = str(text or "").strip()
    if not text:
        daily = weather.get("daily") or {}
        if isinstance(daily, dict):
            vals = []
            if daily.get("temperature_2m_min") is not None and daily.get("temperature_2m_max") is not None:
                vals.append(f"气温约 {daily.get('temperature_2m_min')}–{daily.get('temperature_2m_max')}℃")
            if daily.get("precipitation_probability_max") is not None:
                vals.append(f"最高降雨概率约 {daily.get('precipitation_probability_max')}%")
            if vals:
                vals.append("天气信息仅供参考，出发前建议再次确认。")
                return "；".join(vals)
        return "暂无可用天气摘要，出发前请再次确认当地天气。"

    if not is_probably_english(text):
        return zh_value(text)

    # Conservative phrase replacements for common generated weather prose.
    repl = [
        (r"\bMorning\b", "上午"),
        (r"\bAfternoon\b", "下午"),
        (r"\bEvening\b", "傍晚"),
        (r"\bNight\b", "夜间"),
        (r"\bis mild\b", "较为温和"),
        (r"\bmild\b", "温和"),
        (r"\bmostly dry\b", "整体较少降雨"),
        (r"\bdry\b", "少雨"),
        (r"\baround\b", "约"),
        (r"\brain probability\b", "降雨概率"),
        (r"\brises after\b", "在……之后上升："),
        (r"\bbecomes high from about\b", "从约"),
        (r"\bonward\b", "之后较高"),
        (r"\bso outdoor photos are best done before the afternoon\b", "因此户外拍摄建议尽量安排在下午前完成"),
        (r"\boutdoor photos\b", "户外拍摄"),
        (r"\bbest done\b", "建议完成"),
        (r"\bbefore the afternoon\b", "在下午前"),
        (r"\brain\b", "降雨"),
        (r"\bhigh\b", "较高"),
        (r"\blow\b", "较低"),
        (r"\bwind\b", "风力"),
        (r"\bcloudy\b", "多云"),
        (r"\bsunny\b", "晴"),
        (r"\bovercast\b", "阴"),
        (r"\bshowers\b", "阵雨"),
        (r"\bthunderstorm\b", "雷雨"),
        (r"C\b", "℃"),
    ]
    out = text
    for pat, rep in repl:
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)
    out = out.replace(";", "；").replace(",", "，")
    out = zh_value(out)
    if is_probably_english(out):
        # Fallback: do not leave a full English paragraph in the visible HTML.
        return "天气摘要已转换为中文显示失败，请根据下方温度、降雨概率或出发前天气预报再次确认。原始摘要可在 JSON 文件中查看。"
    return out


def map_link(lat: Any, lng: Any, name: str = "") -> str:
    """Return an exact coordinate search link.

    Do not append the point name to the query. Google Maps often treats
    "lat,lng (name)" as a text search and may fail even when the coordinates
    are valid. The HTML table shows the name separately; the link uses only
    "lat,lng".
    """
    if lat is None or lng is None or str(lat) == "" or str(lng) == "":
        return ""
    q = f"{lat},{lng}"
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)


def maps_dir_url(coords: list[str], mode: str = "walking") -> str:
    if len(coords) < 2:
        return ""
    mode = mode if mode in {"walking", "driving", "bicycling", "transit"} else "walking"
    params = {"api": "1", "origin": coords[0], "destination": coords[-1], "travelmode": mode}
    if len(coords) > 2:
        params["waypoints"] = "|".join(coords[1:-1])
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params)


def build_overall_route_links(stops: list[dict], mode: str = "walking", max_points_per_url: int = 11) -> dict:
    coords: list[str] = []
    names: list[str] = []
    for s in stops:
        lat, lng = s.get("lat"), s.get("lng")
        if lat is None or lng is None or str(lat) == "" or str(lng) == "":
            continue
        coords.append(f"{lat},{lng}")
        names.append(str(s.get("name") or f"Stop {len(coords)}"))
    if len(coords) < 2:
        return {"overall_map_url": None, "overall_map_url_parts": [], "warning": "少于两个有效坐标，无法生成路线链接。"}
    max_points_per_url = max(2, int(max_points_per_url or 10))
    if len(coords) <= max_points_per_url:
        url = maps_dir_url(coords, mode)
        return {"overall_map_url": url, "overall_map_url_parts": [{"part": 1, "from": names[0], "to": names[-1], "map_url": url, "stop_count": len(coords)}], "warning": None}
    parts = []
    start = 0
    part_no = 1
    while start < len(coords) - 1:
        end = min(start + max_points_per_url, len(coords))
        chunk = coords[start:end]
        url = maps_dir_url(chunk, mode)
        parts.append({"part": part_no, "from": names[start], "to": names[end - 1], "map_url": url, "stop_count": len(chunk)})
        if end >= len(coords):
            break
        start = end - 1
        part_no += 1
    return {"overall_map_url": parts[0]["map_url"] if parts else None, "overall_map_url_parts": parts, "warning": "点位较多，Google Maps URL 已按顺序拆分为多个链接。"}


def find_place(places: list[dict], point_id: str) -> dict:
    for p in places:
        if str(p.get("point_id")) == str(point_id):
            return p
    return {}


def parse_minutes(t: Any) -> int | None:
    if not t:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})", str(t))
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return h * 60 + mi


def infer_stay_minutes(stop: dict, default: int = 20) -> int:
    a = parse_minutes(stop.get("planned_arrival"))
    d = parse_minutes(stop.get("planned_departure"))
    if a is not None and d is not None and d > a:
        return max(5, min(240, d - a))
    raw = stop.get("stay_minutes") or stop.get("planned_stay_minutes") or stop.get("stay_min")
    try:
        value = int(float(raw))
        return max(5, min(240, value))
    except Exception:
        return default


def _point_to_stop(point: dict, order: int, unscheduled: bool = False) -> dict:
    arrival = point.get("planned_arrival") or ("灵活安排" if unscheduled else "")
    departure = point.get("planned_departure") or ("灵活安排" if unscheduled else "")
    return {
        "order": order,
        "point_id": point.get("id") or point.get("point_id") or f"point-{order}",
        "name": point.get("name") or point.get("title") or f"Point {order}",
        "lat": point.get("lat") if point.get("lat") is not None else point.get("latitude"),
        "lng": point.get("lng") if point.get("lng") is not None else point.get("lon") or point.get("longitude"),
        "planned_arrival": arrival,
        "planned_departure": departure,
        "stay_minutes": point.get("stay_minutes") or 20,
        "photo_reference": point.get("photo_reference") or point.get("image_url") or point.get("image"),
        "photo_notes": point.get("photo_notes") or point.get("episode") or point.get("scene_time") or "",
        "weather_note": point.get("weather_note") or "",
        "schedule_status": "unscheduled" if unscheduled else point.get("schedule_status", "scheduled"),
    }


def all_anitabi_points(doc: dict) -> list[dict]:
    return doc.get("points") or ((doc.get("pilgrimage_points") or {}).get("points")) or []


def route_requires_all_points(route: dict, idx: int) -> bool:
    rid = str(route.get("route_id") or "").upper()
    strategy = str(route.get("strategy") or "").lower()
    point_policy = str(route.get("point_policy") or "").lower()
    route_type = str(route.get("route_type") or "").lower()
    if route_type in {"all_points", "complete_all_points"}:
        return True
    if route_type in {"time_fit", "time_selected", "selected_subset"}:
        return False
    if "time_fit" in point_policy or "selected" in point_policy or "subset" in point_policy:
        return False
    if "all" in point_policy or strategy == "all_points":
        return True
    return rid == "A" or idx == 0


def collect_route_stops(doc: dict, route: dict, idx: int) -> tuple[list[dict], list[dict], str, bool]:
    """Return (display_stops, omitted_points, policy_note, is_time_fit_route)."""
    route_stops = list(route.get("stops") or [])
    points = all_anitabi_points(doc)
    if not points:
        return route_stops, [], "未检测到独立 Anitabi 点位列表，按 route.stops 显示。", False

    if route_requires_all_points(route, idx):
        existing_ids = {str(s.get("point_id") or s.get("id")) for s in route_stops}
        merged = list(route_stops)
        next_order = len(merged) + 1
        for point in points:
            pid = str(point.get("id") or point.get("point_id"))
            if pid and pid in existing_ids:
                continue
            merged.append(_point_to_stop(point, next_order, unscheduled=True))
            next_order += 1
        for i, stop in enumerate(merged, 1):
            stop["order"] = stop.get("order") or i
            stop["stay_minutes"] = infer_stay_minutes(stop, 20)
        return merged, [], "路线 A：全量点位路线，默认覆盖所有有效 Anitabi 坐标点；时间不够的点位标记为灵活安排。", False

    selected_ids = {str(s.get("point_id") or s.get("id")) for s in route_stops}
    omitted: list[dict] = []
    seen_omitted = set()
    for point in route.get("omitted_points") or []:
        pid = str(point.get("id") or point.get("point_id"))
        if pid:
            seen_omitted.add(pid)
        omitted.append(point)
    for point in points:
        pid = str(point.get("id") or point.get("point_id"))
        if pid and pid not in selected_ids and pid not in seen_omitted:
            omitted.append(point)
            seen_omitted.add(pid)
    for i, stop in enumerate(route_stops, 1):
        stop["order"] = stop.get("order") or i
        stop["stay_minutes"] = infer_stay_minutes(stop, 20)
    return route_stops, omitted, "路线 B：时间适配路线。下方未纳入点位可以点击加入，也可以拖入上方表格；修改后可重新生成路线链接并重新适配时间。", True


def render_omitted_points(omitted_points: list[dict], is_time_fit_route: bool) -> str:
    if not omitted_points:
        return "<p class='small'>没有未纳入点位。</p>"
    rows = []
    for i, p in enumerate(omitted_points, 1):
        lat = p.get("lat") if p.get("lat") is not None else p.get("latitude")
        lng = p.get("lng") if p.get("lng") is not None else p.get("lon") or p.get("longitude")
        name = p.get("name") or p.get("title") or f"Point {i}"
        murl = map_link(lat, lng, name)
        photo = p.get("image_url") or p.get("image") or p.get("photo_reference") or ""
        notes = " ".join(str(x) for x in [p.get("episode") or "", p.get("scene_time") or ""] if str(x))
        action = '<button onclick="addOmittedRow(this.closest(\'tr\'))">加入路线 B</button>' if is_time_fit_route else ''
        rows.append(f"""
        <tr draggable="true" class="omitted-row" data-point-id="{esc(p.get('id') or p.get('point_id') or '')}" data-name="{esc(name)}" data-lat="{esc(lat)}" data-lng="{esc(lng)}" data-photo="{esc(photo)}" data-notes="{esc(notes)}" data-stay-min="20">
          <td>{esc(i)}</td>
          <td><strong>{esc(name)}</strong><br><small>{esc(lat)}, {esc(lng)}</small></td>
          <td>{f'<a href="{esc(photo)}" target="_blank">参考图</a>' if photo else ''}</td>
          <td>{esc(notes)}</td>
          <td>{f'<a href="{esc(murl)}" target="_blank">地图</a>' if murl else ''}</td>
          <td>{action}</td>
        </tr>
        """)
    help_text = "这些点位属于 Anitabi 原始点位，但没有放入时间适配路线。路线 B 中可以点击“加入路线 B”，也可以把行拖到上方时间表中指定位置。" if is_time_fit_route else "这些点位属于 Anitabi 原始点位，但没有放入当前路线。"
    return f"""
    <p class="small">{esc(help_text)}</p>
    <table id="omitted">
      <thead><tr><th>序号</th><th>地点</th><th>参考图</th><th>集数/时间</th><th>地图</th><th>操作</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def render_route(doc: dict, route: dict, places: list[dict], idx: int) -> str:
    work = doc.get("work") or route.get("work") or {}
    trip = doc.get("trip_profile") or {}
    weather = doc.get("weather") or {}
    stops, omitted_points, route_policy_note, is_time_fit_route = collect_route_stops(doc, route, idx)
    segments = route.get("segments") or []
    rid = route.get('route_id') or chr(ord('A') + idx)
    title = f"{esc(work.get('title', '作品'))} 圣地巡礼计划 - 路线 {esc(rid)}"
    map_mode = doc.get('map_mode') or (trip.get('map_access') or {}).get('map_mode') or 'unknown'
    max_walk = doc.get('max_walking_distance_km') or ((trip.get('mobility') or {}).get('max_walking_distance_km')) or 1.5
    try:
        max_walk_float = float(max_walk)
    except Exception:
        max_walk_float = 1.5
    start_time = route.get('estimated_start') or trip.get('local_start_time') or '09:00'
    end_time = route.get('estimated_end') or trip.get('local_end_time') or '18:00'

    overall_links = build_overall_route_links(stops, mode="walking", max_points_per_url=int(route.get("max_points_per_url") or 11))
    overall_url = overall_links.get("overall_map_url")
    overall_part_items = "".join(
        f'<li>第 {esc(part.get("part"))} 段：{esc(part.get("from"))} → {esc(part.get("to"))}，共 {esc(part.get("stop_count"))} 个点位，<a href="{esc(part.get("map_url"))}" target="_blank">打开 Google Maps 路线</a></li>'
        for part in (overall_links.get("overall_map_url_parts") or [])
    )
    overall_warning = overall_links.get("warning")
    warnings = []
    warnings.extend(doc.get('warnings') or [])
    warnings.extend(doc.get('assumptions') or [])
    if is_time_fit_route:
        warnings.append("路线 B 在浏览器中新增或拖动点位后，可按当前顺序重新生成 Google Maps 路线链接，并重新估算时间。无 Google Maps API 时，浏览器无法读取 Google 实时路线时间，会优先尝试 OSRM / OpenStreetMap，失败后使用距离估算；公共交通时间仍需在 Google Maps 中人工确认。")
    warning_items = ''.join(f'<li>{esc(w)}</li>' for w in warnings)

    stop_rows = []
    for s in stops:
        place = find_place(places, str(s.get("point_id")))
        murl = map_link(s.get("lat"), s.get("lng"), s.get("name", ""))
        photo = s.get("photo_reference") or ""
        photo_html = f'<a href="{esc(photo)}" target="_blank">参考图</a>' if photo else ""
        status = zh_value(s.get("schedule_status") or "scheduled")
        stay_min = infer_stay_minutes(s, 20)
        stop_rows.append(f"""
        <tr draggable="true" class="stop-row" data-point-id="{esc(s.get('point_id') or s.get('id') or '')}" data-lat="{esc(s.get('lat'))}" data-lng="{esc(s.get('lng'))}" data-name="{esc(s.get('name'))}" data-photo="{esc(photo)}" data-notes="{esc(s.get('photo_notes'))}" data-stay-min="{esc(stay_min)}">
          <td class="order" contenteditable="true">{esc(s.get('order'))}</td>
          <td class="arrival" contenteditable="true">{esc(s.get('planned_arrival'))}</td>
          <td class="departure" contenteditable="true">{esc(s.get('planned_departure'))}</td>
          <td class="stay" contenteditable="true">{esc(stay_min)}</td>
          <td class="place" contenteditable="true"><strong>{esc(s.get('name'))}</strong><br><small>{esc(s.get('lat'))}, {esc(s.get('lng'))}</small><br><small>状态：{esc(status)}</small></td>
          <td class="notes" contenteditable="true">{esc(s.get('photo_notes'))}<br>{photo_html}</td>
          <td contenteditable="true">{esc(zh_value(place.get('opening_hours')))}<br>{esc(zh_value(place.get('verification_note'), '需人工确认'))}</td>
          <td contenteditable="true">门票：{esc(zh_value(place.get('ticket_price')))}<br>人均：{esc(zh_value(place.get('average_price')))}</td>
          <td>{f'<a href="{murl}" target="_blank">地图</a>' if murl else ''}</td>
          <td><button onclick="deleteStopRow(this)">删除</button></td>
        </tr>
        """)

    seg_rows = []
    for seg in segments:
        url = seg.get("map_url") or ""
        seg_rows.append(f"""
        <tr>
          <td contenteditable="true">{esc(seg.get('order'))}</td>
          <td contenteditable="true">{esc(seg.get('from'))}</td>
          <td contenteditable="true">{esc(seg.get('to'))}</td>
          <td contenteditable="true">{esc(zh_value(seg.get('transport_mode')))}</td>
          <td contenteditable="true">{esc(seg.get('distance_text'))}<br><small>{'超过步行上限，建议公共交通' if seg.get('walking_limit_exceeded') else ''}</small></td>
          <td contenteditable="true">{esc(seg.get('duration_text'))}<br><small>{'需人工确认交通时刻' if seg.get('requires_manual_transit_confirmation') else ''}</small></td>
          <td>{f'<a href="{esc(url)}" target="_blank">路线</a>' if url else ''}</td>
        </tr>
        """)

    sources = []
    for key in ["source_urls"]:
        for u in route.get(key, []) or []:
            sources.append(u)
    for p in places:
        for u in p.get("source_urls", []) or []:
            sources.append(u)
        for u in [p.get("official_url"), p.get("google_maps_url")]:
            if u:
                sources.append(u)
    source_items = "\n".join(f'<li><a href="{esc(u)}" target="_blank">{esc(u)}</a></li>' for u in sorted(set(sources)))
    omitted_block = render_omitted_points(omitted_points, is_time_fit_route)
    time_fit_js = "true" if is_time_fit_route else "false"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 24px; line-height: 1.55; color: #222; }}
h1, h2 {{ margin-bottom: 0.4rem; }}
.card {{ border: 1px solid #ddd; border-radius: 14px; padding: 16px; margin: 16px 0; box-shadow: 0 1px 6px rgba(0,0,0,.06); }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
th {{ background: #f6f6f6; }}
td[contenteditable="true"] {{ background: #fffdf2; }}
button {{ padding: 8px 12px; border: 1px solid #aaa; border-radius: 8px; background: #fff; cursor: pointer; margin: 4px 8px 4px 0; }}
.small {{ color: #666; font-size: 0.9em; }}
.warn {{ background: #fff7e6; border-left: 4px solid #f0ad4e; padding: 10px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #eef; margin-left: 6px; font-size: 0.9em; }}
.drag-over {{ outline: 3px dashed #4f8cff; }}
.stop-row, .omitted-row {{ cursor: grab; }}
.over-time {{ background: #fff1f0 !important; }}
#scheduleStatus {{ margin-top: 8px; }}
@media print {{ button {{ display: none; }} body {{ margin: 12mm; }} }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="card">
  <p><strong>作品：</strong>{esc(work.get('title'))}　<strong>Bangumi 编号：</strong>{esc(work.get('bangumi_id'))}</p>
  <p><strong>日期：</strong>{esc(trip.get('date'))}　<strong>时间：</strong>{esc(trip.get('local_start_time'))} - {esc(trip.get('local_end_time'))}</p>
  <p><strong>路线策略：</strong>{esc(zh_value(route.get('strategy')))}<span class="badge">{esc(zh_value(route.get('route_type') or route.get('point_policy')))}</span>　<strong>预计：</strong>{esc(start_time)} - {esc(end_time)}</p>
  <p><strong>地图模式：</strong>{esc(zh_value(map_mode))}　<strong>单段最长步行距离：</strong>{esc(max_walk_float)} km</p>
  <p class="warn">{esc(route_policy_note)}<br>营业时间、交通时间、天气、评分和价格均为规划参考，出发前建议再次自行确认。未配置 Google Maps API 时，只能提供 URL 链接和人工确认项。</p>
  <button onclick="window.print()">打印 / 另存为 PDF</button>
  <button onclick="exportText()">导出当前表格文本</button>
</div>

<div class="card">
  <h2>当前路线 Google Maps 总链接</h2>
  <p>{f'<a id="overallRouteMain" href="{esc(overall_url)}" target="_blank"><strong>打开当前路线</strong></a>' if overall_url else '<span id="overallRouteMain">当前路线少于两个有效坐标，无法生成路线链接。</span>'}</p>
  <ul id="overallRouteParts">{overall_part_items}</ul>
  <button onclick="rebuildOverallRouteLinks()">按当前表格重新生成路线链接</button>
  <button onclick="recalculateSchedule()">按当前路线重新适配时间</button>
  <p id="scheduleStatus" class="small" contenteditable="true">{esc(overall_warning or 'Google Maps URL 仅用于打开路线参考；如果点位较多或交通方式复杂，请在地图中再次确认。删除、加入或拖动点位后，可重新生成路线链接并重新适配时间。')}</p>
</div>

<div class="card">
  <h2>天气参考</h2>
  <p contenteditable="true">{esc(translate_weather_summary(weather.get('summary'), weather))}</p>
</div>

<div class="card">
  <h2>模式与限制说明</h2>
  <ul contenteditable="true">{warning_items}</ul>
</div>

<div class="card">
  <h2>巡礼时间表（可直接编辑{ '，支持拖动排序' if is_time_fit_route else ''}）</h2>
  <table id="stops">
    <thead><tr><th>顺序</th><th>到达</th><th>离开</th><th>停留(分)</th><th>地点</th><th>拍照参考</th><th>营业时间</th><th>价格</th><th>地图</th><th>操作</th></tr></thead>
    <tbody>{''.join(stop_rows)}</tbody>
  </table>
</div>

<div class="card">
  <h2>交通路线</h2>
  <table id="segments">
    <thead><tr><th>顺序</th><th>出发</th><th>到达</th><th>方式</th><th>距离</th><th>时间</th><th>链接</th></tr></thead>
    <tbody>{''.join(seg_rows)}</tbody>
  </table>
</div>

<div class="card">
  <h2>未纳入当前路线的 Anitabi 点位</h2>
  {omitted_block}
</div>

<div class="card">
  <h2>人工确认清单</h2>
  <ul contenteditable="true">
    <li>确认当天交通时刻和换乘，尤其是 URL-only 模式下的公共交通段。</li>
    <li>确认餐厅/景点当天是否营业。</li>
    <li>确认门票价格、预约要求、评分参考和最后入场时间。</li>
    <li>确认参考图版权/来源标注。</li>
  </ul>
</div>

<div class="card">
  <h2>来源链接</h2>
  <ul>{source_items}</ul>
</div>

<script>
const MAX_POINTS_PER_GOOGLE_MAPS_URL = 11;
const IS_TIME_FIT_ROUTE = {time_fit_js};
const TRIP_START_TIME = {js_str(start_time)};
const TRIP_END_TIME = {js_str(end_time)};
const MAX_WALKING_KM = {max_walk_float};
let draggedRow = null;

function mapsDirUrl(coords, mode = 'walking') {{
  if (coords.length < 2) return '';
  const params = new URLSearchParams();
  params.set('api', '1');
  params.set('origin', coords[0]);
  params.set('destination', coords[coords.length - 1]);
  params.set('travelmode', mode);
  if (coords.length > 2) params.set('waypoints', coords.slice(1, -1).join('|'));
  return 'https://www.google.com/maps/dir/?' + params.toString();
}}
function singleSegmentUrl(a, b, mode = 'walking') {{
  const params = new URLSearchParams();
  params.set('api', '1');
  params.set('origin', a.lat + ',' + a.lng);
  params.set('destination', b.lat + ',' + b.lng);
  params.set('travelmode', mode === 'transit' ? 'transit' : 'walking');
  return 'https://www.google.com/maps/dir/?' + params.toString();
}}
function collectStopRows() {{ return Array.from(document.querySelectorAll('#stops tbody tr')); }}
function rowData(row) {{
  return {{
    pointId: row.dataset.pointId || '',
    name: row.dataset.name || (row.querySelector('.place strong') ? row.querySelector('.place strong').textContent.trim() : ''),
    lat: row.dataset.lat || '',
    lng: row.dataset.lng || '',
    photo: row.dataset.photo || '',
    notes: row.dataset.notes || '',
    stayMin: parseInt((row.querySelector('.stay') ? row.querySelector('.stay').textContent : row.dataset.stayMin || '20').trim(), 10) || 20,
  }};
}}
function collectCoordsFromTable() {{
  return collectStopRows()
    .map(row => [row.dataset.lat, row.dataset.lng])
    .filter(pair => pair[0] && pair[1])
    .map(pair => pair[0] + ',' + pair[1]);
}}
function rebuildOverallRouteLinks() {{
  const coords = collectCoordsFromTable();
  const main = document.getElementById('overallRouteMain');
  const list = document.getElementById('overallRouteParts');
  list.innerHTML = '';
  if (coords.length < 2) {{
    main.removeAttribute('href');
    main.textContent = '当前路线少于两个有效坐标，无法生成路线链接。';
    return;
  }}
  let chunks = [];
  for (let start = 0; start < coords.length - 1;) {{
    const end = Math.min(start + MAX_POINTS_PER_GOOGLE_MAPS_URL, coords.length);
    chunks.push(coords.slice(start, end));
    if (end >= coords.length) break;
    start = end - 1;
  }}
  const firstUrl = mapsDirUrl(chunks[0], 'walking');
  main.href = firstUrl;
  main.textContent = '打开当前路线';
  chunks.forEach((chunk, i) => {{
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = mapsDirUrl(chunk, 'walking');
    a.target = '_blank';
    a.textContent = `打开第 ${{i + 1}} 段路线（${{chunk.length}} 个点位）`;
    li.appendChild(a);
    list.appendChild(li);
  }});
}}
function formatMin(total) {{
  total = Math.round(total);
  const h = Math.floor(total / 60) % 24;
  const m = total % 60;
  return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
}}
function parseHHMM(text, fallback) {{
  const m = String(text || '').match(/(\\d{{1,2}}):(\\d{{2}})/);
  if (!m) return fallback;
  return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
}}
function haversineKm(a, b) {{
  const R = 6371;
  const lat1 = Number(a.lat), lon1 = Number(a.lng), lat2 = Number(b.lat), lon2 = Number(b.lng);
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const p1 = lat1 * Math.PI / 180;
  const p2 = lat2 * Math.PI / 180;
  const x = Math.sin(dLat/2)**2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dLon/2)**2;
  return 2 * R * Math.atan2(Math.sqrt(x), Math.sqrt(1-x));
}}
async function tryOsrmWalking(a, b) {{
  const url = `https://router.project-osrm.org/route/v1/foot/${{a.lng}},${{a.lat}};${{b.lng}},${{b.lat}}?overview=false`;
  try {{
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    const r = data.routes && data.routes[0];
    if (!r) return null;
    return {{ minutes: Math.max(1, Math.round(r.duration / 60)), distanceKm: r.distance / 1000, source: 'OSRM / OpenStreetMap 步行估算' }};
  }} catch (e) {{ return null; }}
}}
async function estimateLeg(a, b) {{
  const straight = haversineKm(a, b);
  if (straight <= MAX_WALKING_KM) {{
    const osrm = await tryOsrmWalking(a, b);
    if (osrm) return {{...osrm, mode: 'walking', manual: false}};
    return {{distanceKm: straight * 1.25, minutes: Math.max(3, Math.round(straight * 1.25 / 4.2 * 60)), mode: 'walking', source: '直线距离放大估算，需地图确认', manual: true}};
  }}
  return {{distanceKm: straight, minutes: Math.max(12, Math.round(straight * 8 + 12)), mode: 'transit', source: '超过步行上限，已改为公共交通；时间需在 Google Maps 确认', manual: true}};
}}
function updateOrders() {{
  collectStopRows().forEach((row, i) => {{
    const order = row.querySelector('.order');
    if (order) order.textContent = String(i + 1);
  }});
}}
function deleteStopRow(btn) {{
  const row = btn.closest('tr');
  if (row) row.remove();
  updateOrders();
  rebuildOverallRouteLinks();
  recalculateSchedule();
}}
function createStopRowFromData(d) {{
  const tr = document.createElement('tr');
  tr.draggable = true;
  tr.className = 'stop-row';
  tr.dataset.pointId = d.pointId || '';
  tr.dataset.lat = d.lat || '';
  tr.dataset.lng = d.lng || '';
  tr.dataset.name = d.name || '';
  tr.dataset.photo = d.photo || '';
  tr.dataset.notes = d.notes || '';
  tr.dataset.stayMin = d.stayMin || '20';
  const photoHtml = d.photo ? `<a href="${{d.photo}}" target="_blank">参考图</a>` : '';
  const murl = d.lat && d.lng ? 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(d.lat + ',' + d.lng) : '';
  tr.innerHTML = `
    <td class="order" contenteditable="true"></td>
    <td class="arrival" contenteditable="true"></td>
    <td class="departure" contenteditable="true"></td>
    <td class="stay" contenteditable="true">${{d.stayMin || 20}}</td>
    <td class="place" contenteditable="true"><strong>${{d.name || ''}}</strong><br><small>${{d.lat || ''}}, ${{d.lng || ''}}</small><br><small>状态：手动加入</small></td>
    <td class="notes" contenteditable="true">${{d.notes || ''}}<br>${{photoHtml}}</td>
    <td contenteditable="true">未知<br>需人工确认</td>
    <td contenteditable="true">门票：未知<br>人均：未知</td>
    <td>${{murl ? `<a href="${{murl}}" target="_blank">地图</a>` : ''}}</td>
    <td><button onclick="deleteStopRow(this)">删除</button></td>`;
  bindStopRowDrag(tr);
  return tr;
}}
function addOmittedRow(row, beforeRow = null) {{
  if (!row) return;
  const d = {{
    pointId: row.dataset.pointId || '', name: row.dataset.name || '', lat: row.dataset.lat || '', lng: row.dataset.lng || '',
    photo: row.dataset.photo || '', notes: row.dataset.notes || '', stayMin: row.dataset.stayMin || '20'
  }};
  const tr = createStopRowFromData(d);
  const tbody = document.querySelector('#stops tbody');
  if (beforeRow) tbody.insertBefore(tr, beforeRow); else tbody.appendChild(tr);
  row.remove();
  updateOrders();
  rebuildOverallRouteLinks();
  recalculateSchedule();
}}
function bindStopRowDrag(row) {{
  row.addEventListener('dragstart', e => {{ draggedRow = row; e.dataTransfer.effectAllowed = 'move'; }});
  row.addEventListener('dragover', e => {{ e.preventDefault(); row.classList.add('drag-over'); }});
  row.addEventListener('dragleave', () => row.classList.remove('drag-over'));
  row.addEventListener('drop', e => {{
    e.preventDefault(); row.classList.remove('drag-over');
    if (!draggedRow || draggedRow === row) return;
    if (draggedRow.classList.contains('omitted-row')) addOmittedRow(draggedRow, row);
    else document.querySelector('#stops tbody').insertBefore(draggedRow, row);
    updateOrders(); rebuildOverallRouteLinks(); recalculateSchedule();
  }});
}}
function bindOmittedDrag(row) {{
  row.addEventListener('dragstart', e => {{ draggedRow = row; e.dataTransfer.effectAllowed = 'move'; }});
}}
function setupDragDrop() {{
  document.querySelectorAll('#stops tbody tr').forEach(bindStopRowDrag);
  document.querySelectorAll('#omitted tbody tr').forEach(bindOmittedDrag);
  const tbody = document.querySelector('#stops tbody');
  tbody.addEventListener('dragover', e => e.preventDefault());
  tbody.addEventListener('drop', e => {{
    e.preventDefault();
    if (!draggedRow) return;
    if (draggedRow.classList.contains('omitted-row')) addOmittedRow(draggedRow);
    else tbody.appendChild(draggedRow);
    updateOrders(); rebuildOverallRouteLinks(); recalculateSchedule();
  }});
}}
async function recalculateSchedule() {{
  const rows = collectStopRows();
  const start = parseHHMM(TRIP_START_TIME, 9 * 60);
  const endLimit = parseHHMM(TRIP_END_TIME, 18 * 60);
  let current = start;
  const segBody = document.querySelector('#segments tbody');
  segBody.innerHTML = '';
  let manualCount = 0;
  for (let i = 0; i < rows.length; i++) {{
    const row = rows[i];
    row.classList.remove('over-time');
    if (i > 0) {{
      const prev = rowData(rows[i - 1]);
      const cur = rowData(row);
      const leg = await estimateLeg(prev, cur);
      current += leg.minutes;
      if (leg.manual) manualCount += 1;
      const tr = document.createElement('tr');
      const modeText = leg.mode === 'transit' ? '公共交通' : '步行';
      tr.innerHTML = `<td>${{i}}</td><td>${{prev.name}}</td><td>${{cur.name}}</td><td>${{modeText}}</td><td>${{leg.distanceKm.toFixed(2)}} km</td><td>${{leg.minutes}} 分钟<br><small>${{leg.source}}</small></td><td><a href="${{singleSegmentUrl(prev, cur, leg.mode)}}" target="_blank">路线</a></td>`;
      segBody.appendChild(tr);
    }}
    const stayCell = row.querySelector('.stay');
    const stay = parseInt((stayCell ? stayCell.textContent : '20').trim(), 10) || 20;
    row.dataset.stayMin = String(stay);
    const arrivalCell = row.querySelector('.arrival');
    const depCell = row.querySelector('.departure');
    if (arrivalCell) arrivalCell.textContent = formatMin(current);
    current += stay;
    if (depCell) depCell.textContent = formatMin(current);
    if (endLimit && current > endLimit) row.classList.add('over-time');
  }}
  updateOrders();
  const status = document.getElementById('scheduleStatus');
  const overText = endLimit && current > endLimit ? `；已超过用户结束时间约 ${{Math.round(current - endLimit)}} 分钟` : '';
  status.textContent = `已按当前表格顺序重新适配时间，预计结束：${{formatMin(current)}}${{overText}}。${{manualCount ? '其中 ' + manualCount + ' 段为估算或公共交通人工确认段。' : '步行段已尽量使用 OSRM / OpenStreetMap 估算。'}}`;
}}
function exportText() {{
  const text = document.body.innerText;
  const blob = new Blob([text], {{type: 'text/plain;charset=utf-8'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'pilgrimage-itinerary.txt';
  a.click();
  URL.revokeObjectURL(url);
}}
setupDragDrop();
updateOrders();
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    doc = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    routes = doc.get("routes") or []
    places = doc.get("places") or []
    files = []
    for i, route in enumerate(routes[:2]):
        rid = route.get("route_id") or chr(ord('A') + i)
        html_text = render_route(doc, route, places, i)
        path = out_dir / f"pilgrimage_route_{rid}.html"
        path.write_text(html_text, encoding="utf-8")
        files.append({"route_id": rid, "title": route.get("route_name"), "path": str(path), "editable": True, "contains_source_links": True, "supports_drag_drop_reorder": True, "supports_route_b_add_omitted_points": True, "supports_time_recalculation": True})
    print(json.dumps({"stage": "html_itinerary", "html_files": files, "summary": f"已生成 {len(files)} 个 HTML 计划表文件。", "remaining_manual_checks": ["出发前请再次确认营业时间、评分、价格等级、门票/人均价格、公共交通和天气。", "在浏览器中编辑路线 B 后，请使用 Google Maps 链接确认公共交通耗时和营业时间。"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
