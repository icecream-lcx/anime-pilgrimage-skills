#!/usr/bin/env python3
"""Build editable HTML anime-pilgrimage itinerary pages.

v8 features:
- Preserves Route A as the all-Anitabi-points route, including multi-day trips.
- Preserves Route B as one or more time-fit daily routes.
- Supports output_language for Chinese / English / Japanese UI labels.
- Keeps coordinate-only Google Maps point links.
- Route B pages support omitted-point add-back, drag reorder, link rebuild, and time recalculation.
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


def js(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False)


def lang_code(doc: dict) -> str:
    for src in [doc.get("output_language"), (doc.get("trip_profile") or {}).get("output_language")]:
        if isinstance(src, dict):
            primary = str(src.get("primary") or "").strip()
            if primary:
                return primary
        elif isinstance(src, str) and src.strip():
            return src.strip()
    return "zh-CN"


def lang_family(code: str) -> str:
    c = (code or "zh-CN").lower()
    if c.startswith("zh"):
        return "zh"
    if c.startswith("ja"):
        return "ja"
    if c.startswith("ko"):
        return "ko"
    if c.startswith("fr"):
        return "fr"
    if c.startswith("es"):
        return "es"
    return "en"


UI = {
    "zh": {
        "route_a_name": "Route A：全量点位路线",
        "route_b_name": "Route B：时间适配路线",
        "route_b_day": "Route B：第 {day} 天时间适配路线",
        "title_suffix": "圣地巡礼计划",
        "work": "作品", "bangumi_id": "Bangumi 编号", "date": "日期", "time": "时间",
        "route_strategy": "路线策略", "estimated": "预计", "map_mode": "地图模式", "max_walk": "单段最长步行距离",
        "print": "打印 / 另存为 PDF", "export": "导出当前表格文本",
        "overall_link": "当前路线 Google Maps 总链接", "open_current": "打开当前路线", "open_part": "打开第 {n} 段路线（{count} 个点位）",
        "not_enough_coords": "当前路线少于两个有效坐标，无法生成路线链接。",
        "rebuild": "按当前表格重新生成路线链接", "recalc": "按当前路线重新适配时间",
        "weather": "天气参考", "limits": "模式与限制说明", "timeline": "巡礼时间表（可直接编辑）",
        "timeline_drag": "巡礼时间表（可直接编辑，支持拖动排序）", "segments": "交通路线", "omitted": "未纳入当前路线的 Anitabi 点位",
        "manual_check": "人工确认清单", "sources": "来源链接", "order": "顺序", "arrival": "到达", "departure": "离开", "stay": "停留(分)",
        "place": "地点", "photo": "拍照参考", "hours": "营业时间", "price": "价格", "map": "地图", "action": "操作",
        "from": "出发", "to": "到达", "mode": "方式", "distance": "距离", "duration": "时间", "link": "链接",
        "delete": "删除", "add_b": "加入路线 B", "reference_image": "参考图", "route": "路线", "status": "状态",
        "unknown": "未知", "manual_confirm": "需人工确认", "ticket": "门票", "average": "人均", "scheduled": "已安排", "unscheduled": "灵活安排", "manual_added": "手动加入",
        "walking": "步行", "transit": "公共交通", "driving": "驾车", "url_only": "仅使用 Google Maps 链接模式",
        "route_a_note": "Route A 为全量点位路线，默认覆盖所有有效 Anitabi 坐标点；时间不够的点位可在表格中自行删除或调整。",
        "route_b_note": "Route B 为时间适配路线。下方未纳入点位可以点击加入，也可以拖入上方表格；修改后可重新生成路线链接并重新适配时间。",
        "warning": "营业时间、交通时间、天气、评分和价格均为规划参考，出发前建议再次自行确认。未配置 Google Maps API 时，只能提供 URL 链接和人工确认项。",
        "omitted_empty": "没有未纳入点位。", "omitted_help_b": "这些点位属于 Anitabi 原始点位，但没有放入时间适配路线。可以点击“加入路线 B”，也可以把行拖到上方时间表中指定位置。",
        "omitted_help": "这些点位属于 Anitabi 原始点位，但没有放入当前路线。",
        "maps_reference": "Google Maps URL 仅用于打开路线参考；如果点位较多或交通方式复杂，请在地图中再次确认。删除、加入或拖动点位后，可重新生成路线链接并重新适配时间。",
        "manual_1": "确认当天交通时刻和换乘，尤其是 URL-only 模式下的公共交通段。",
        "manual_2": "确认餐厅/景点当天是否营业。", "manual_3": "确认门票价格、预约要求、评分参考和最后入场时间。", "manual_4": "确认参考图版权/来源标注。",
        "weather_none": "暂无可用天气摘要，出发前请再次确认当地天气。",
        "coord_warning": "少于两个有效坐标，无法生成路线链接。", "chunk_warning": "点位较多，Google Maps URL 已按顺序拆分为多个链接。",
    },
    "en": {
        "route_a_name": "Route A: Full landmark route",
        "route_b_name": "Route B: Time-fit route",
        "route_b_day": "Route B: Day {day} time-fit route",
        "title_suffix": "Anime Pilgrimage Plan",
        "work": "Work", "bangumi_id": "Bangumi ID", "date": "Date", "time": "Time",
        "route_strategy": "Route strategy", "estimated": "Estimated", "map_mode": "Map mode", "max_walk": "Max walking distance per segment",
        "print": "Print / Save as PDF", "export": "Export current table text",
        "overall_link": "Overall Google Maps route link", "open_current": "Open current route", "open_part": "Open part {n} route ({count} stops)",
        "not_enough_coords": "Fewer than two valid coordinates; a route link cannot be generated.",
        "rebuild": "Rebuild route links from current table", "recalc": "Recalculate times from current route",
        "weather": "Weather reference", "limits": "Mode and limitation notes", "timeline": "Pilgrimage timeline (editable)",
        "timeline_drag": "Pilgrimage timeline (editable, drag to reorder)", "segments": "Transport segments", "omitted": "Anitabi points not included in this route",
        "manual_check": "Manual confirmation checklist", "sources": "Source links", "order": "Order", "arrival": "Arrival", "departure": "Departure", "stay": "Stay (min)",
        "place": "Place", "photo": "Photo reference", "hours": "Opening hours", "price": "Price", "map": "Map", "action": "Action",
        "from": "From", "to": "To", "mode": "Mode", "distance": "Distance", "duration": "Duration", "link": "Link",
        "delete": "Delete", "add_b": "Add to Route B", "reference_image": "Reference image", "route": "Route", "status": "Status",
        "unknown": "Unknown", "manual_confirm": "Manual confirmation required", "ticket": "Ticket", "average": "Average", "scheduled": "Scheduled", "unscheduled": "Flexible", "manual_added": "Manually added",
        "walking": "Walking", "transit": "Public transit", "driving": "Driving", "url_only": "Google Maps URL-only mode",
        "route_a_note": "Route A is the full landmark route and covers every valid Anitabi coordinate point by default. Remove or adjust rows manually if needed.",
        "route_b_note": "Route B is the time-fit route. Omitted points below can be added by button or dragged into the main table; after editing, rebuild links and recalculate times.",
        "warning": "Opening hours, route durations, weather, ratings, and prices are planning references only. Verify again before departure. Without Google Maps API, only URL links and manual-confirmation items can be provided.",
        "omitted_empty": "No omitted points.", "omitted_help_b": "These points are from the original Anitabi list but were not included in the time-fit route. Click Add to Route B or drag a row into the main table.",
        "omitted_help": "These points are from the original Anitabi list but were not included in the current route.",
        "maps_reference": "Google Maps URLs are route references only. If there are many stops or complex transport segments, verify them again in the map. After deleting, adding, or reordering points, rebuild route links and recalculate times.",
        "manual_1": "Confirm same-day transit schedules and transfers, especially public-transit segments in URL-only mode.",
        "manual_2": "Confirm whether restaurants or attractions are open on the trip date.", "manual_3": "Confirm ticket prices, reservation requirements, ratings, and last-entry times.", "manual_4": "Confirm reference image copyright/source attribution.",
        "weather_none": "No weather summary is available. Please check the local weather again before departure.",
        "coord_warning": "Fewer than two valid coordinates; a route link cannot be generated.", "chunk_warning": "There are many stops, so the Google Maps route has been split into sequential links.",
    },
    "ja": {
        "route_a_name": "Route A：全ランドマークルート",
        "route_b_name": "Route B：時間適応ルート",
        "route_b_day": "Route B：{day}日目 時間適応ルート",
        "title_suffix": "聖地巡礼計画",
        "work": "作品", "bangumi_id": "Bangumi ID", "date": "日付", "time": "時間",
        "route_strategy": "ルート方針", "estimated": "予定", "map_mode": "地図モード", "max_walk": "1区間の最大徒歩距離",
        "print": "印刷 / PDF保存", "export": "現在の表をテキスト出力",
        "overall_link": "現在の Google Maps 全体ルート", "open_current": "現在のルートを開く", "open_part": "第 {n} 区間を開く（{count} 地点）",
        "not_enough_coords": "有効な座標が2つ未満のため、ルートリンクを生成できません。",
        "rebuild": "現在の表からルートリンクを再生成", "recalc": "現在のルートで時刻を再計算",
        "weather": "天気参考", "limits": "モードと制限", "timeline": "巡礼タイムライン（編集可）",
        "timeline_drag": "巡礼タイムライン（編集可・ドラッグ並べ替え可）", "segments": "交通区間", "omitted": "現在のルートに含まれない Anitabi 地点",
        "manual_check": "手動確認リスト", "sources": "出典リンク", "order": "順番", "arrival": "到着", "departure": "出発", "stay": "滞在(分)",
        "place": "場所", "photo": "写真参考", "hours": "営業時間", "price": "料金", "map": "地図", "action": "操作",
        "from": "出発", "to": "到着", "mode": "手段", "distance": "距離", "duration": "時間", "link": "リンク",
        "delete": "削除", "add_b": "Route B に追加", "reference_image": "参考画像", "route": "ルート", "status": "状態",
        "unknown": "不明", "manual_confirm": "手動確認が必要", "ticket": "チケット", "average": "平均", "scheduled": "予定済み", "unscheduled": "柔軟に調整", "manual_added": "手動追加",
        "walking": "徒歩", "transit": "公共交通", "driving": "車", "url_only": "Google Maps URL のみモード",
        "route_a_note": "Route A は全ランドマークルートで、有効な Anitabi 座標地点をすべて含みます。不要な行は手動で削除または調整できます。",
        "route_b_note": "Route B は時間適応ルートです。下の未採用地点はボタンまたはドラッグで追加できます。編集後、リンク再生成と時刻再計算を行ってください。",
        "warning": "営業時間、移動時間、天気、評価、料金は参考情報です。出発前に再確認してください。Google Maps API がない場合は URL リンクと手動確認項目のみ提供します。",
        "omitted_empty": "未採用地点はありません。", "omitted_help_b": "これらは Anitabi の元地点ですが時間適応ルートには含まれていません。ボタンまたはドラッグで Route B に追加できます。",
        "omitted_help": "これらは Anitabi の元地点ですが現在のルートには含まれていません。",
        "maps_reference": "Google Maps URL は参考ルートです。地点が多い場合や交通が複雑な場合は地図で再確認してください。編集後はリンクと時刻を再計算できます。",
        "manual_1": "当日の交通時刻と乗換を確認してください。", "manual_2": "店舗や観光施設の営業日を確認してください。", "manual_3": "料金、予約、評価、最終入場時刻を確認してください。", "manual_4": "参考画像の著作権・出典を確認してください。",
        "weather_none": "利用可能な天気概要がありません。出発前に現地の天気を再確認してください。",
        "coord_warning": "有効な座標が2つ未満のため、ルートリンクを生成できません。", "chunk_warning": "地点が多いため、Google Maps ルートを複数の連続リンクに分割しました。",
    },
}


def tr(doc: dict, key: str, **kwargs: Any) -> str:
    fam = lang_family(lang_code(doc))
    d = UI.get(fam) or UI["en"]
    val = d.get(key) or UI["en"].get(key) or UI["zh"].get(key) or key
    try:
        return val.format(**kwargs)
    except Exception:
        return val


def local_value(doc: dict, x: Any, default_key: str = "unknown") -> str:
    if x is None or str(x).strip() == "":
        return tr(doc, default_key)
    text = str(x).strip()
    low = text.lower()
    fam = lang_family(lang_code(doc))
    maps = {
        "unknown": {"zh":"未知","en":"Unknown","ja":"不明"},
        "none": {"zh":"无","en":"None","ja":"なし"},
        "google_maps_url_only": {"zh":"仅使用 Google Maps 链接模式","en":"Google Maps URL-only mode","ja":"Google Maps URL のみモード"},
        "time_fit": {"zh":"时间适配路线","en":"Time-fit route","ja":"時間適応ルート"},
        "balanced_time_fit": {"zh":"均衡时间适配","en":"Balanced time-fit","ja":"バランス型時間適応"},
        "all_points": {"zh":"全量点位路线","en":"Full landmark route","ja":"全ランドマークルート"},
        "scheduled": {"zh":"已安排","en":"Scheduled","ja":"予定済み"},
        "unscheduled": {"zh":"灵活安排","en":"Flexible","ja":"柔軟に調整"},
        "manual-added": {"zh":"手动加入","en":"Manually added","ja":"手動追加"},
        "manual_added": {"zh":"手动加入","en":"Manually added","ja":"手動追加"},
        "walking": {"zh":"步行","en":"Walking","ja":"徒歩"},
        "walk": {"zh":"步行","en":"Walking","ja":"徒歩"},
        "transit": {"zh":"公共交通","en":"Public transit","ja":"公共交通"},
        "public_transit": {"zh":"公共交通","en":"Public transit","ja":"公共交通"},
        "driving": {"zh":"驾车","en":"Driving","ja":"車"},
        "return_to_start": {"zh":"返回出发地","en":"Return to start","ja":"出発地に戻る"},
        "user_specified": {"zh":"用户指定终点","en":"User-specified endpoint","ja":"ユーザー指定の終点"},
    }
    if low in maps:
        return maps[low].get(fam) or maps[low].get("en") or text
    return text.replace("Route A", "Route A").replace("Route B", "Route B")


def weather_summary(doc: dict, weather: dict | None) -> str:
    weather = weather or {}
    summary = str(weather.get("summary") or "").strip()
    if summary:
        return summary if lang_family(lang_code(doc)) != "zh" or not re.search(r"[A-Za-z]{8,}", summary) else "天气摘要请以出发前最新预报为准。"
    return tr(doc, "weather_none")


def map_link(lat: Any, lng: Any) -> str:
    if lat is None or lng is None or str(lat) == "" or str(lng) == "":
        return ""
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{lat},{lng}")


def maps_dir_url(coords: list[str], mode: str = "walking") -> str:
    if len(coords) < 2:
        return ""
    mode = mode if mode in {"walking", "driving", "bicycling", "transit"} else "walking"
    params = {"api": "1", "origin": coords[0], "destination": coords[-1], "travelmode": mode}
    if len(coords) > 2:
        params["waypoints"] = "|".join(coords[1:-1])
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params)


def build_overall_route_links(doc: dict, stops: list[dict], mode: str = "walking", max_points_per_url: int = 11) -> dict:
    coords, names = [], []
    for s in stops:
        lat, lng = s.get("lat"), s.get("lng")
        if lat is None or lng is None or str(lat) == "" or str(lng) == "":
            continue
        coords.append(f"{lat},{lng}")
        names.append(str(s.get("name") or f"Stop {len(coords)}"))
    if len(coords) < 2:
        return {"overall_map_url": None, "overall_map_url_parts": [], "warning": tr(doc, "coord_warning")}
    max_points_per_url = max(2, int(max_points_per_url or 11))
    if len(coords) <= max_points_per_url:
        url = maps_dir_url(coords, mode)
        return {"overall_map_url": url, "overall_map_url_parts": [{"part": 1, "from": names[0], "to": names[-1], "map_url": url, "stop_count": len(coords)}], "warning": None}
    parts, start, part_no = [], 0, 1
    while start < len(coords) - 1:
        end = min(start + max_points_per_url, len(coords))
        chunk = coords[start:end]
        url = maps_dir_url(chunk, mode)
        parts.append({"part": part_no, "from": names[start], "to": names[end - 1], "map_url": url, "stop_count": len(chunk)})
        if end >= len(coords):
            break
        start = end - 1
        part_no += 1
    return {"overall_map_url": parts[0]["map_url"] if parts else None, "overall_map_url_parts": parts, "warning": tr(doc, "chunk_warning")}


def point_id(p: dict) -> str:
    return str(p.get("point_id") or p.get("id") or "")


def all_points(doc: dict) -> list[dict]:
    return doc.get("points") or ((doc.get("pilgrimage_points") or {}).get("points")) or []


def point_to_stop(point: dict, order: int, doc: dict, unscheduled: bool = False) -> dict:
    lat = point.get("lat") if point.get("lat") is not None else point.get("latitude")
    lng = point.get("lng") if point.get("lng") is not None else point.get("lon") or point.get("longitude")
    return {
        "order": order,
        "point_id": point.get("point_id") or point.get("id") or f"point-{order}",
        "name": point.get("name") or point.get("title") or f"Point {order}",
        "lat": lat, "lng": lng,
        "planned_arrival": point.get("planned_arrival") or (tr(doc, "unscheduled") if unscheduled else ""),
        "planned_departure": point.get("planned_departure") or (tr(doc, "unscheduled") if unscheduled else ""),
        "stay_minutes": point.get("stay_minutes") or 20,
        "photo_reference": point.get("photo_reference") or point.get("image_url") or point.get("image"),
        "photo_notes": point.get("photo_notes") or point.get("episode") or point.get("scene_time") or "",
        "schedule_status": "unscheduled" if unscheduled else point.get("schedule_status", "scheduled"),
    }


def is_route_a(route: dict, idx: int) -> bool:
    rid = str(route.get("route_id") or "").lower()
    rtype = str(route.get("route_type") or route.get("selection_policy") or route.get("point_policy") or "").lower()
    if "route_a" in rid or rid == "a":
        return True
    if "all" in rtype and "point" in rtype:
        return True
    if rtype in {"all_points", "complete_all_points", "all_valid_anitabi_points"}:
        return True
    if "time" in rtype or "subset" in rtype:
        return False
    return idx == 0


def normalize_routes(doc: dict) -> list[dict]:
    routes = doc.get("routes") or []
    out: list[dict] = []
    if isinstance(routes, list):
        out = list(routes)
    elif isinstance(routes, dict):
        a = routes.get("route_a_full_all_points") or routes.get("route_a") or routes.get("A")
        if isinstance(a, dict):
            a.setdefault("route_id", "A")
            a.setdefault("route_type", "all_points")
            out.append(a)
        bs = routes.get("route_b_time_fit_by_day") or routes.get("route_b") or routes.get("B") or []
        if isinstance(bs, dict):
            bs = [bs]
        if isinstance(bs, list):
            for i,b in enumerate(bs,1):
                if isinstance(b, dict):
                    b.setdefault("route_id", f"B_day_{b.get('day_index') or i}")
                    b.setdefault("route_type", "time_fit")
                    out.append(b)
    # Ensure Route A exists when points exist.
    if all_points(doc) and not any(is_route_a(r, i) for i, r in enumerate(out)):
        out.insert(0, {"route_id": "A", "route_type": "all_points", "route_name": tr(doc, "route_a_name"), "stops": []})
    return out


def route_stops(doc: dict, route: dict, idx: int) -> tuple[list[dict], list[dict], bool, str]:
    pts = all_points(doc)
    raw_stops = list(route.get("stops") or route.get("points") or [])
    stops = [point_to_stop(s, i+1, doc, False) if ("lat" in s or "latitude" in s) else s for i,s in enumerate(raw_stops)]
    if is_route_a(route, idx):
        seen = {point_id(s) for s in stops if point_id(s)}
        for p in pts:
            if point_id(p) not in seen:
                stops.append(point_to_stop(p, len(stops)+1, doc, True))
        return stops, [], False, tr(doc, "route_a_note")
    selected = {point_id(s) for s in stops if point_id(s)}
    omitted: list[dict] = list(route.get("omitted_points") or [])
    seen_omit = {point_id(p) for p in omitted if point_id(p)}
    for p in pts:
        pid = point_id(p)
        if pid and pid not in selected and pid not in seen_omit:
            omitted.append(p)
    return stops, omitted, True, tr(doc, "route_b_note")


def html_omitted(doc: dict, omitted: list[dict], is_b: bool) -> str:
    if not omitted:
        return f"<p class='small'>{esc(tr(doc,'omitted_empty'))}</p>"
    rows = []
    for i,p in enumerate(omitted,1):
        lat = p.get("lat") if p.get("lat") is not None else p.get("latitude")
        lng = p.get("lng") if p.get("lng") is not None else p.get("lon") or p.get("longitude")
        name = p.get("name") or p.get("title") or f"Point {i}"
        photo = p.get("image_url") or p.get("image") or p.get("photo_reference") or ""
        notes = " ".join(str(x) for x in [p.get("episode") or "", p.get("scene_time") or ""] if str(x))
        action = f'<button onclick="addOmittedRow(this.closest(\'tr\'))">{esc(tr(doc,"add_b"))}</button>' if is_b else ""
        rows.append(f"""
<tr draggable="true" class="omitted-row" data-point-id="{esc(point_id(p))}" data-name="{esc(name)}" data-lat="{esc(lat)}" data-lng="{esc(lng)}" data-photo="{esc(photo)}" data-notes="{esc(notes)}" data-stay-min="20">
<td>{esc(i)}</td><td><strong>{esc(name)}</strong><br><small>{esc(lat)}, {esc(lng)}</small></td>
<td>{f'<a href="{esc(photo)}" target="_blank">{esc(tr(doc,"reference_image"))}</a>' if photo else ''}</td>
<td>{esc(notes)}</td><td>{f'<a href="{esc(map_link(lat,lng))}" target="_blank">{esc(tr(doc,"map"))}</a>' if lat and lng else ''}</td><td>{action}</td>
</tr>""")
    help_text = tr(doc, "omitted_help_b") if is_b else tr(doc, "omitted_help")
    return f"""<p class="small">{esc(help_text)}</p>
<table id="omitted"><thead><tr><th>{esc(tr(doc,'order'))}</th><th>{esc(tr(doc,'place'))}</th><th>{esc(tr(doc,'photo'))}</th><th>{esc(tr(doc,'time'))}</th><th>{esc(tr(doc,'map'))}</th><th>{esc(tr(doc,'action'))}</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"""


def render_route(doc: dict, route: dict, idx: int) -> str:
    work = doc.get("work") or route.get("work") or {}
    trip = doc.get("trip_profile") or {}
    weather = doc.get("weather") or {}
    places = doc.get("places") or []
    stops, omitted, is_b, note = route_stops(doc, route, idx)
    rid = str(route.get("route_id") or ("A" if not is_b else f"B_day_{route.get('day_index') or idx}"))
    day = route.get("day_index")
    if is_route_a(route, idx):
        route_title = route.get("display_name") or route.get("route_name") or tr(doc, "route_a_name")
    elif day:
        route_title = route.get("display_name") or route.get("route_name") or tr(doc, "route_b_day", day=day)
    else:
        route_title = route.get("display_name") or route.get("route_name") or tr(doc, "route_b_name")
    title = f"{esc(work.get('title') or '')} {esc(tr(doc,'title_suffix'))} - {esc(route_title)}"
    start_time = route.get("estimated_start") or trip.get("local_start_time") or "09:00"
    end_time = route.get("estimated_end") or trip.get("local_end_time") or "18:00"
    max_walk = ((trip.get("mobility") or {}).get("max_walking_distance_km")) or doc.get("max_walking_distance_km") or 1.5
    try: max_walk_f = float(max_walk)
    except Exception: max_walk_f = 1.5
    map_mode = doc.get("map_mode") or ((trip.get("map_access") or {}).get("map_mode")) or "unknown"
    overall = build_overall_route_links(doc, stops, "walking", int(route.get("max_points_per_url") or 11))
    part_items = "".join(f'<li>{esc(tr(doc,"open_part", n=p.get("part"), count=p.get("stop_count")))}：{esc(p.get("from"))} → {esc(p.get("to"))} <a href="{esc(p.get("map_url"))}" target="_blank">Google Maps</a></li>' for p in overall.get("overall_map_url_parts") or [])
    warnings = []
    for x in (doc.get("warnings") or []) + (doc.get("assumptions") or []): warnings.append(str(x))
    warnings.append(tr(doc, "warning"))
    rows = []
    for n,s in enumerate(stops,1):
        lat,lng = s.get("lat"),s.get("lng")
        murl = map_link(lat,lng)
        photo = s.get("photo_reference") or s.get("image_url") or ""
        stay = s.get("stay_minutes") or 20
        status = local_value(doc, s.get("schedule_status") or "scheduled")
        rows.append(f"""
<tr draggable="true" class="stop-row" data-point-id="{esc(point_id(s))}" data-lat="{esc(lat)}" data-lng="{esc(lng)}" data-name="{esc(s.get('name'))}" data-photo="{esc(photo)}" data-notes="{esc(s.get('photo_notes'))}" data-stay-min="{esc(stay)}">
<td class="order" contenteditable="true">{n}</td>
<td class="arrival" contenteditable="true">{esc(s.get('planned_arrival'))}</td>
<td class="departure" contenteditable="true">{esc(s.get('planned_departure'))}</td>
<td class="stay" contenteditable="true">{esc(stay)}</td>
<td class="place" contenteditable="true"><strong>{esc(s.get('name'))}</strong><br><small>{esc(lat)}, {esc(lng)}</small><br><small>{esc(tr(doc,'status'))}：{esc(status)}</small></td>
<td class="notes" contenteditable="true">{esc(s.get('photo_notes'))}<br>{f'<a href="{esc(photo)}" target="_blank">{esc(tr(doc,"reference_image"))}</a>' if photo else ''}</td>
<td contenteditable="true">{esc(tr(doc,'unknown'))}<br>{esc(tr(doc,'manual_confirm'))}</td>
<td contenteditable="true">{esc(tr(doc,'ticket'))}：{esc(tr(doc,'unknown'))}<br>{esc(tr(doc,'average'))}：{esc(tr(doc,'unknown'))}</td>
<td>{f'<a href="{esc(murl)}" target="_blank">{esc(tr(doc,"map"))}</a>' if murl else ''}</td>
<td><button onclick="deleteStopRow(this)">{esc(tr(doc,'delete'))}</button></td>
</tr>""")
    omitted_block = html_omitted(doc, omitted, is_b)
    warning_items = "".join(f"<li>{esc(w)}</li>" for w in warnings)
    html_lang = {"zh":"zh-CN","en":"en","ja":"ja"}.get(lang_family(lang_code(doc)), "en")
    labels = {k: tr(doc,k) for k in ["delete","add_b","map","reference_image","manual_confirm","walking","transit","route","open_current","not_enough_coords"]}
    return f"""<!doctype html><html lang="{html_lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;margin:24px;line-height:1.55;color:#222}}.card{{border:1px solid #ddd;border-radius:14px;padding:16px;margin:16px 0;box-shadow:0 1px 6px rgba(0,0,0,.06)}}table{{width:100%;border-collapse:collapse;margin:12px 0}}th,td{{border:1px solid #ddd;padding:8px;vertical-align:top}}th{{background:#f6f6f6}}td[contenteditable=true]{{background:#fffdf2}}button{{padding:8px 12px;border:1px solid #aaa;border-radius:8px;background:#fff;cursor:pointer;margin:4px 8px 4px 0}}.small{{color:#666;font-size:.9em}}.warn{{background:#fff7e6;border-left:4px solid #f0ad4e;padding:10px}}.drag-over{{outline:3px dashed #4f8cff}}.stop-row,.omitted-row{{cursor:grab}}.over-time{{background:#fff1f0!important}}@media print{{button{{display:none}}body{{margin:12mm}}}}
</style></head><body>
<h1>{title}</h1><div class="card"><p><strong>{esc(tr(doc,'work'))}：</strong>{esc(work.get('title'))}　<strong>{esc(tr(doc,'bangumi_id'))}：</strong>{esc(work.get('bangumi_id'))}</p><p><strong>{esc(tr(doc,'date'))}：</strong>{esc(route.get('date') or trip.get('date'))}　<strong>{esc(tr(doc,'time'))}：</strong>{esc(trip.get('local_start_time'))} - {esc(trip.get('local_end_time'))}</p><p><strong>{esc(tr(doc,'route_strategy'))}：</strong>{esc(local_value(doc, route.get('strategy') or route.get('selection_policy') or route.get('route_type')))}　<strong>{esc(tr(doc,'estimated'))}：</strong>{esc(start_time)} - {esc(end_time)}</p><p><strong>{esc(tr(doc,'map_mode'))}：</strong>{esc(local_value(doc,map_mode))}　<strong>{esc(tr(doc,'max_walk'))}：</strong>{esc(max_walk_f)} km</p><p class="warn">{esc(note)}<br>{esc(tr(doc,'warning'))}</p><button onclick="window.print()">{esc(tr(doc,'print'))}</button><button onclick="exportText()">{esc(tr(doc,'export'))}</button></div>
<div class="card"><h2>{esc(tr(doc,'overall_link'))}</h2><p>{f'<a id="overallRouteMain" href="{esc(overall.get("overall_map_url"))}" target="_blank"><strong>{esc(tr(doc,"open_current"))}</strong></a>' if overall.get('overall_map_url') else f'<span id="overallRouteMain">{esc(tr(doc,"not_enough_coords"))}</span>'}</p><ul id="overallRouteParts">{part_items}</ul><button onclick="rebuildOverallRouteLinks()">{esc(tr(doc,'rebuild'))}</button><button onclick="recalculateSchedule()">{esc(tr(doc,'recalc'))}</button><p id="scheduleStatus" class="small" contenteditable="true">{esc(overall.get('warning') or tr(doc,'maps_reference'))}</p></div>
<div class="card"><h2>{esc(tr(doc,'weather'))}</h2><p contenteditable="true">{esc(weather_summary(doc, weather))}</p></div>
<div class="card"><h2>{esc(tr(doc,'limits'))}</h2><ul contenteditable="true">{warning_items}</ul></div>
<div class="card"><h2>{esc(tr(doc,'timeline_drag') if is_b else tr(doc,'timeline'))}</h2><table id="stops"><thead><tr><th>{esc(tr(doc,'order'))}</th><th>{esc(tr(doc,'arrival'))}</th><th>{esc(tr(doc,'departure'))}</th><th>{esc(tr(doc,'stay'))}</th><th>{esc(tr(doc,'place'))}</th><th>{esc(tr(doc,'photo'))}</th><th>{esc(tr(doc,'hours'))}</th><th>{esc(tr(doc,'price'))}</th><th>{esc(tr(doc,'map'))}</th><th>{esc(tr(doc,'action'))}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="card"><h2>{esc(tr(doc,'segments'))}</h2><table id="segments"><thead><tr><th>{esc(tr(doc,'order'))}</th><th>{esc(tr(doc,'from'))}</th><th>{esc(tr(doc,'to'))}</th><th>{esc(tr(doc,'mode'))}</th><th>{esc(tr(doc,'distance'))}</th><th>{esc(tr(doc,'duration'))}</th><th>{esc(tr(doc,'link'))}</th></tr></thead><tbody></tbody></table></div>
<div class="card"><h2>{esc(tr(doc,'omitted'))}</h2>{omitted_block}</div>
<div class="card"><h2>{esc(tr(doc,'manual_check'))}</h2><ul contenteditable="true"><li>{esc(tr(doc,'manual_1'))}</li><li>{esc(tr(doc,'manual_2'))}</li><li>{esc(tr(doc,'manual_3'))}</li><li>{esc(tr(doc,'manual_4'))}</li></ul></div>
<div class="card"><h2>{esc(tr(doc,'sources'))}</h2><ul></ul></div>
<script>
const LABELS = {js(labels)}; const MAX_POINTS_PER_GOOGLE_MAPS_URL=11; const TRIP_START_TIME={js(str(start_time))}; const TRIP_END_TIME={js(str(end_time))}; const MAX_WALKING_KM={max_walk_f}; let draggedRow=null;
function mapsDirUrl(coords,mode='walking'){{if(coords.length<2)return'';const p=new URLSearchParams();p.set('api','1');p.set('origin',coords[0]);p.set('destination',coords[coords.length-1]);p.set('travelmode',mode);if(coords.length>2)p.set('waypoints',coords.slice(1,-1).join('|'));return 'https://www.google.com/maps/dir/?'+p.toString();}}
function singleSegmentUrl(a,b,mode='walking'){{const p=new URLSearchParams();p.set('api','1');p.set('origin',a.lat+','+a.lng);p.set('destination',b.lat+','+b.lng);p.set('travelmode',mode==='transit'?'transit':'walking');return 'https://www.google.com/maps/dir/?'+p.toString();}}
function rows(){{return Array.from(document.querySelectorAll('#stops tbody tr'));}} function data(row){{return {{pointId:row.dataset.pointId||'',name:row.dataset.name||'',lat:row.dataset.lat||'',lng:row.dataset.lng||'',photo:row.dataset.photo||'',notes:row.dataset.notes||'',stayMin:parseInt((row.querySelector('.stay')?.textContent||row.dataset.stayMin||'20').trim(),10)||20}};}}
function coords(){{return rows().map(r=>[r.dataset.lat,r.dataset.lng]).filter(x=>x[0]&&x[1]).map(x=>x[0]+','+x[1]);}}
function rebuildOverallRouteLinks(){{const c=coords(),main=document.getElementById('overallRouteMain'),list=document.getElementById('overallRouteParts');list.innerHTML='';if(c.length<2){{main.removeAttribute('href');main.textContent=LABELS.not_enough_coords;return;}}let chunks=[];for(let s=0;s<c.length-1;){{let e=Math.min(s+MAX_POINTS_PER_GOOGLE_MAPS_URL,c.length);chunks.push(c.slice(s,e));if(e>=c.length)break;s=e-1;}}main.href=mapsDirUrl(chunks[0]);main.textContent=LABELS.open_current;chunks.forEach((ch,i)=>{{let li=document.createElement('li'),a=document.createElement('a');a.href=mapsDirUrl(ch);a.target='_blank';a.textContent=(i+1)+'. Google Maps ('+ch.length+')';li.appendChild(a);list.appendChild(li);}});}}
function parseHHMM(t,f){{const m=String(t||'').match(/(\d{{1,2}}):(\d{{2}})/);return m?parseInt(m[1])*60+parseInt(m[2]):f;}} function fmt(x){{x=Math.round(x);return String(Math.floor(x/60)%24).padStart(2,'0')+':'+String(x%60).padStart(2,'0');}}
function km(a,b){{const R=6371,la1=Number(a.lat)*Math.PI/180,la2=Number(b.lat)*Math.PI/180,dla=la2-la1,dlo=(Number(b.lng)-Number(a.lng))*Math.PI/180,h=Math.sin(dla/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dlo/2)**2;return 2*R*Math.atan2(Math.sqrt(h),Math.sqrt(1-h));}}
async function leg(a,b){{const d=km(a,b); if(d>MAX_WALKING_KM)return {{distanceKm:d,minutes:Math.max(12,Math.round(d*8+12)),mode:'transit',source:LABELS.manual_confirm,manual:true}}; return {{distanceKm:d*1.25,minutes:Math.max(3,Math.round(d*1.25/4.2*60)),mode:'walking',source:'OSRM / OpenStreetMap or distance estimate',manual:true}};}}
function updateOrders(){{rows().forEach((r,i)=>{{const o=r.querySelector('.order');if(o)o.textContent=String(i+1);}});}}
function deleteStopRow(btn){{btn.closest('tr')?.remove();updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}}
function createStopRow(d){{const tr=document.createElement('tr');tr.draggable=true;tr.className='stop-row';Object.assign(tr.dataset,{{pointId:d.pointId||'',lat:d.lat||'',lng:d.lng||'',name:d.name||'',photo:d.photo||'',notes:d.notes||'',stayMin:d.stayMin||'20'}});const m=d.lat&&d.lng?'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(d.lat+','+d.lng):'';tr.innerHTML=`<td class="order" contenteditable="true"></td><td class="arrival" contenteditable="true"></td><td class="departure" contenteditable="true"></td><td class="stay" contenteditable="true">${{d.stayMin||20}}</td><td class="place" contenteditable="true"><strong>${{d.name||''}}</strong><br><small>${{d.lat||''}}, ${{d.lng||''}}</small><br><small>${{LABELS.status||'Status'}}：${{LABELS.manual_added||'Manually added'}}</small></td><td class="notes" contenteditable="true">${{d.notes||''}}<br>${{d.photo?`<a href="${{d.photo}}" target="_blank">${{LABELS.reference_image}}</a>`:''}}</td><td contenteditable="true">${{LABELS.unknown||'Unknown'}}<br>${{LABELS.manual_confirm}}</td><td contenteditable="true">${{LABELS.unknown||'Unknown'}}</td><td>${{m?`<a href="${{m}}" target="_blank">${{LABELS.map}}</a>`:''}}</td><td><button onclick="deleteStopRow(this)">${{LABELS.delete}}</button></td>`;bindStopRowDrag(tr);return tr;}}
function addOmittedRow(row,before=null){{if(!row)return;const d={{pointId:row.dataset.pointId,name:row.dataset.name,lat:row.dataset.lat,lng:row.dataset.lng,photo:row.dataset.photo,notes:row.dataset.notes,stayMin:row.dataset.stayMin}};const tr=createStopRow(d),tb=document.querySelector('#stops tbody');before?tb.insertBefore(tr,before):tb.appendChild(tr);row.remove();updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}}
function bindStopRowDrag(r){{r.addEventListener('dragstart',e=>{{draggedRow=r;e.dataTransfer.effectAllowed='move';}});r.addEventListener('dragover',e=>{{e.preventDefault();r.classList.add('drag-over');}});r.addEventListener('dragleave',()=>r.classList.remove('drag-over'));r.addEventListener('drop',e=>{{e.preventDefault();r.classList.remove('drag-over');if(!draggedRow||draggedRow===r)return;if(draggedRow.classList.contains('omitted-row'))addOmittedRow(draggedRow,r);else document.querySelector('#stops tbody').insertBefore(draggedRow,r);updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}});}}
function bindOmittedDrag(r){{r.addEventListener('dragstart',e=>{{draggedRow=r;e.dataTransfer.effectAllowed='move';}});}}
function setupDragDrop(){{document.querySelectorAll('#stops tbody tr').forEach(bindStopRowDrag);document.querySelectorAll('#omitted tbody tr').forEach(bindOmittedDrag);const tb=document.querySelector('#stops tbody');tb.addEventListener('dragover',e=>e.preventDefault());tb.addEventListener('drop',e=>{{e.preventDefault();if(!draggedRow)return;if(draggedRow.classList.contains('omitted-row'))addOmittedRow(draggedRow);else tb.appendChild(draggedRow);updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}});}}
async function recalculateSchedule(){{const rs=rows();let cur=parseHHMM(TRIP_START_TIME,540),limit=parseHHMM(TRIP_END_TIME,1080);const seg=document.querySelector('#segments tbody');seg.innerHTML='';for(let i=0;i<rs.length;i++){{rs[i].classList.remove('over-time');if(i>0){{const a=data(rs[i-1]),b=data(rs[i]),l=await leg(a,b);cur+=l.minutes;const tr=document.createElement('tr');tr.innerHTML=`<td>${{i}}</td><td>${{a.name}}</td><td>${{b.name}}</td><td>${{l.mode==='transit'?LABELS.transit:LABELS.walking}}</td><td>${{l.distanceKm.toFixed(2)}} km</td><td>${{l.minutes}} min<br><small>${{l.source}}</small></td><td><a href="${{singleSegmentUrl(a,b,l.mode)}}" target="_blank">${{LABELS.route}}</a></td>`;seg.appendChild(tr);}}const stay=parseInt(rs[i].querySelector('.stay')?.textContent||'20',10)||20;rs[i].querySelector('.arrival').textContent=fmt(cur);cur+=stay;rs[i].querySelector('.departure').textContent=fmt(cur);if(limit&&cur>limit)rs[i].classList.add('over-time');}}updateOrders();document.getElementById('scheduleStatus').textContent=LABELS.manual_confirm+'; '+fmt(cur);}}
function exportText(){{const blob=new Blob([document.body.innerText],{{type:'text/plain;charset=utf-8'}});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='pilgrimage-itinerary.txt';a.click();URL.revokeObjectURL(url);}}
setupDragDrop();updateOrders();
</script></body></html>"""


def safe_filename(route: dict, idx: int) -> str:
    rid = str(route.get("route_id") or "").lower()
    if "route_a" in rid or rid == "a" or (idx == 0 and not "b" in rid):
        return "pilgrimage_route_A.html"
    day = route.get("day_index")
    if day:
        return f"pilgrimage_route_B_day_{day}.html"
    m = re.search(r"day[_-]?(\d+)", rid)
    if m:
        return f"pilgrimage_route_B_day_{m.group(1)}.html"
    if rid in {"b", "route_b"}:
        return "pilgrimage_route_B.html"
    clean = re.sub(r"[^A-Za-z0-9_-]+", "_", rid or f"route_{idx+1}").strip("_")
    return f"pilgrimage_route_{clean}.html"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    doc = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    out_dir = Path(args.output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    routes = normalize_routes(doc)
    files = []
    for i, route in enumerate(routes):
        html_text = render_route(doc, route, i)
        name = safe_filename(route, i)
        path = out_dir / name
        path.write_text(html_text, encoding="utf-8")
        files.append({"route_id": route.get("route_id") or name, "path": str(path), "editable": True, "supports_drag_drop_reorder": True, "supports_route_b_add_omitted_points": True, "supports_time_recalculation": True})
    print(json.dumps({"stage": "html_itinerary", "output_language": doc.get("output_language"), "html_files": files, "summary": f"Generated {len(files)} HTML itinerary file(s)."}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
