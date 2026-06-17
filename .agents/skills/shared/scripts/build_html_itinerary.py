#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any


def esc(x: Any) -> str:
    return html.escape('' if x is None else str(x), quote=True)


def js(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False)


def normalize_link_url(url: Any) -> str:
    if url is None:
        return ''
    u = str(url).strip().strip('"\'“”‘’')
    if not u:
        return ''
    if u.startswith('//'):
        u = 'https:' + u
    if u.startswith('http://') or u.startswith('https://'):
        return u
    return ''


def link_html(url: Any, label: Any) -> str:
    u = normalize_link_url(url)
    if not u:
        return ''
    return f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def lang_code(doc: dict) -> str:
    for src in [doc.get('output_language'), (doc.get('trip_profile') or {}).get('output_language')]:
        if isinstance(src, dict) and src.get('primary'):
            return str(src.get('primary'))
        if isinstance(src, str) and src.strip():
            return src.strip()
    return 'zh-CN'


def lang_family(code: str) -> str:
    c = (code or 'zh-CN').lower()
    if c.startswith('zh'):
        return 'zh'
    if c.startswith('ja'):
        return 'ja'
    return 'en'


UI = {
    'zh': {
        'route_a_name': 'Route A：全量点位路线', 'route_b_name': 'Route B：时间适配路线', 'route_b_day': 'Route B：第 {day} 天时间适配路线',
        'title_suffix': '圣地巡礼计划', 'work': '作品', 'bangumi_id': 'Bangumi 编号', 'date': '日期', 'time': '时间', 'start_end': '起终点',
        'route_strategy': '路线策略', 'estimated': '预计', 'map_mode': '地图模式', 'max_walk': '单段最长步行距离',
        'print': '打印 / 另存为 PDF', 'export': '导出当前表格文本', 'overall_link': '当前路线 Google Maps 总链接',
        'open_current': '打开当前路线', 'open_part': '打开第 {n} 段路线（{count} 个点位）', 'not_enough_coords': '当前路线少于两个有效坐标，无法生成路线链接。',
        'rebuild': '按当前表格重新生成路线链接', 'recalc': '按当前路线重新适配时间', 'weather': '天气参考', 'limits': '模式与限制说明',
        'timeline': '巡礼时间表（可直接编辑）', 'timeline_drag': '巡礼时间表（可直接编辑，支持拖动排序）', 'segments': '交通路线',
        'omitted': '未纳入当前路线的 Anitabi 点位', 'manual_check': '人工确认清单', 'sources': '来源链接', 'order': '顺序',
        'arrival': '到达', 'departure': '离开', 'stay': '停留(分)', 'place': '地点', 'photo': '拍照参考', 'hours': '营业时间',
        'price': '价格', 'map': '地图', 'action': '操作', 'from': '出发', 'to': '到达', 'mode': '方式', 'distance': '距离',
        'duration': '时间', 'link': '链接', 'delete': '删除', 'add_b': '加入路线 B', 'reference_image': '参考图', 'route': '路线',
        'status': '状态', 'unknown': '未知', 'manual_confirm': '需人工确认', 'ticket': '门票', 'average': '人均', 'scheduled': '已安排',
        'unscheduled': '灵活安排', 'manual_added': '手动加入', 'walking': '步行', 'transit': '公共交通', 'url_only': '仅使用 Google Maps 链接模式',
        'route_a_note': 'Route A 为全量点位路线，默认覆盖所有有效 Anitabi 坐标点；时间不够的点位可在表格中自行删除或调整。',
        'route_b_note': 'Route B 为时间适配路线。下方未纳入点位可以点击加入，也可以拖入上方表格；修改后可重新生成路线链接并重新适配时间。',
        'warning': '营业时间、交通时间、天气、评分和价格均为规划参考，出发前建议再次自行确认。未配置 Google Maps API 时，只能提供 URL 链接和人工确认项。',
        'maps_reference': 'Google Maps URL 仅用于打开路线参考；删除、加入或拖动点位后，可重新生成路线链接并重新适配时间。',
        'omitted_help_b': '这些点位属于 Anitabi 原始点位，但没有放入时间适配路线。可以点击“加入路线 B”，也可以把行拖到上方时间表中指定位置。',
        'omitted_help': '这些点位属于 Anitabi 原始点位，但没有放入当前路线。', 'omitted_empty': '没有未纳入点位。',
        'manual_1': '确认当天交通时刻和换乘，尤其是 URL-only 模式下的公共交通段。', 'manual_2': '确认餐厅/景点当天是否营业。',
        'manual_3': '确认门票价格、预约要求、评分参考和最后入场时间。', 'manual_4': '确认参考图版权/来源标注。',
        'weather_none': '暂无可用天气摘要，出发前请再次确认当地天气。', 'coord_warning': '少于两个有效坐标，无法生成路线链接。',
        'chunk_warning': '点位较多，Google Maps URL 已按顺序拆分为多个链接。', 'endpoint_return': '未指定终点，默认最终返回出发地。'
    },
    'en': {
        'route_a_name': 'Route A: Full landmark route', 'route_b_name': 'Route B: Time-fit route', 'route_b_day': 'Route B: Day {day} time-fit route',
        'title_suffix': 'Anime Pilgrimage Plan', 'work': 'Work', 'bangumi_id': 'Bangumi ID', 'date': 'Date', 'time': 'Time', 'start_end': 'Start / End',
        'route_strategy': 'Route strategy', 'estimated': 'Estimated', 'map_mode': 'Map mode', 'max_walk': 'Max walking distance per segment',
        'print': 'Print / Save as PDF', 'export': 'Export current table text', 'overall_link': 'Overall Google Maps route link',
        'open_current': 'Open current route', 'open_part': 'Open part {n} route ({count} stops)', 'not_enough_coords': 'Fewer than two valid coordinates; a route link cannot be generated.',
        'rebuild': 'Rebuild route links from current table', 'recalc': 'Recalculate times from current route', 'weather': 'Weather reference', 'limits': 'Mode and limitation notes',
        'timeline': 'Pilgrimage timeline (editable)', 'timeline_drag': 'Pilgrimage timeline (editable, drag to reorder)', 'segments': 'Transport segments',
        'omitted': 'Anitabi points not included in this route', 'manual_check': 'Manual confirmation checklist', 'sources': 'Source links', 'order': 'Order',
        'arrival': 'Arrival', 'departure': 'Departure', 'stay': 'Stay (min)', 'place': 'Place', 'photo': 'Photo reference', 'hours': 'Opening hours',
        'price': 'Price', 'map': 'Map', 'action': 'Action', 'from': 'From', 'to': 'To', 'mode': 'Mode', 'distance': 'Distance',
        'duration': 'Duration', 'link': 'Link', 'delete': 'Delete', 'add_b': 'Add to Route B', 'reference_image': 'Reference image', 'route': 'Route',
        'status': 'Status', 'unknown': 'Unknown', 'manual_confirm': 'Manual confirmation required', 'ticket': 'Ticket', 'average': 'Average', 'scheduled': 'Scheduled',
        'unscheduled': 'Flexible', 'manual_added': 'Manually added', 'walking': 'Walking', 'transit': 'Public transit', 'url_only': 'Google Maps URL-only mode',
        'route_a_note': 'Route A is the full landmark route and covers every valid Anitabi coordinate point by default. Remove or adjust rows manually if needed.',
        'route_b_note': 'Route B is the time-fit route. Omitted points below can be added by button or dragged into the main table; after editing, rebuild links and recalculate times.',
        'warning': 'Opening hours, route durations, weather, ratings, and prices are planning references only. Verify again before departure. Without Google Maps API, only URL links and manual-confirmation items can be provided.',
        'maps_reference': 'Google Maps URLs are route references only. After deleting, adding, or reordering points, rebuild route links and recalculate times.',
        'omitted_help_b': 'These points are from the original Anitabi list but were not included in the time-fit route. Click Add to Route B or drag a row into the main table.',
        'omitted_help': 'These points are from the original Anitabi list but were not included in the current route.', 'omitted_empty': 'No omitted points.',
        'manual_1': 'Confirm same-day transit schedules and transfers, especially public-transit segments in URL-only mode.', 'manual_2': 'Confirm whether restaurants or attractions are open on the trip date.',
        'manual_3': 'Confirm ticket prices, reservation requirements, ratings, and last-entry times.', 'manual_4': 'Confirm reference image copyright/source attribution.',
        'weather_none': 'No weather summary is available. Please check the local weather again before departure.', 'coord_warning': 'Fewer than two valid coordinates; a route link cannot be generated.',
        'chunk_warning': 'There are many stops, so the Google Maps route has been split into sequential links.', 'endpoint_return': 'No ending location was specified, so the route returns to the starting point by default.'
    },
    'ja': {
        'route_a_name': 'Route A：全ランドマークルート', 'route_b_name': 'Route B：時間適応ルート', 'route_b_day': 'Route B：{day}日目 時間適応ルート',
        'title_suffix': '聖地巡礼計画', 'work': '作品', 'bangumi_id': 'Bangumi ID', 'date': '日付', 'time': '時間', 'start_end': '出発 / 到着',
        'endpoint_return': '到着地点が指定されていないため、出発地点に戻るルートとして扱います。'
    }
}

ENUM_LABELS = {
    'google_maps_url_only': {'zh': '仅使用 Google Maps 链接模式', 'en': 'Google Maps URL-only mode', 'ja': 'Google Maps URL のみモード'},
    'balanced_time_fit': {'zh': '均衡时间适配', 'en': 'Balanced time-fit', 'ja': 'バランス型時間適応'},
    'time_fit': {'zh': '时间适配路线', 'en': 'Time-fit route', 'ja': '時間適応ルート'},
    'unknown': {'zh': '未知', 'en': 'Unknown', 'ja': '不明'},
    'scheduled': {'zh': '已安排', 'en': 'Scheduled', 'ja': '予定済み'},
    'unscheduled': {'zh': '灵活安排', 'en': 'Flexible', 'ja': '自由調整'},
    'manual-added': {'zh': '手动加入', 'en': 'Manually added', 'ja': '手動追加'},
    'walking': {'zh': '步行', 'en': 'Walking', 'ja': '徒歩'},
    'transit': {'zh': '公共交通', 'en': 'Public transit', 'ja': '公共交通'},
    'return_to_start': {'zh': '返回出发地', 'en': 'Return to start', 'ja': '出発地点に戻る'},
    'user_specified': {'zh': '用户指定终点', 'en': 'User-specified endpoint', 'ja': 'ユーザー指定の到着地点'},
}


def tr(doc: dict, key: str, **kwargs: Any) -> str:
    fam = lang_family(lang_code(doc))
    table = UI.get(fam, UI['en'])
    s = table.get(key) or UI['en'].get(key) or UI['zh'].get(key) or key
    try:
        return s.format(**kwargs)
    except Exception:
        return s


def enum_label(doc: dict, value: Any) -> str:
    v = str(value or '').strip()
    if not v:
        return tr(doc, 'unknown')
    fam = lang_family(lang_code(doc))
    if v in ENUM_LABELS:
        return ENUM_LABELS[v].get(fam) or ENUM_LABELS[v].get('en') or v
    return v


def num(x: Any) -> float | None:
    try:
        if x is None or x == '':
            return None
        return float(x)
    except Exception:
        return None


def point_lat_lng(p: dict) -> tuple[float | None, float | None]:
    lat = p.get('lat') if p.get('lat') is not None else p.get('latitude')
    lng = p.get('lng') if p.get('lng') is not None else p.get('lon') if p.get('lon') is not None else p.get('longitude')
    if (lat is None or lng is None) and isinstance(p.get('geo'), list) and len(p['geo']) >= 2:
        lat, lng = p['geo'][0], p['geo'][1]
    return num(lat), num(lng)


def point_id(p: dict) -> str:
    return str(p.get('point_id') or p.get('id') or p.get('name') or p.get('title') or '')


def point_name(p: dict, idx: int = 0) -> str:
    return str(p.get('name') or p.get('title') or p.get('label') or p.get('place_name') or f'Point {idx + 1}')


def point_photo_url(p: dict) -> str:
    candidates = [p.get('image_url'), p.get('image'), p.get('photo_url'), p.get('photo_reference'), p.get('reference_image_url'), p.get('cover')]
    images = p.get('images')
    if isinstance(images, list) and images:
        candidates.append(images[0])
    return normalize_link_url(next((c for c in candidates if c), ''))


def point_notes(p: dict) -> str:
    parts = []
    ep = p.get('episode') if p.get('episode') is not None else p.get('ep')
    scene = p.get('scene') or p.get('scene_time') or p.get('s')
    if ep not in [None, '']:
        parts.append(f'EP{ep}')
    if scene not in [None, '']:
        parts.append(f'scene {scene}')
    if p.get('notes'):
        parts.append(str(p.get('notes')))
    return ' / '.join(parts)


def maps_search_url(lat: Any, lng: Any) -> str:
    if lat in [None, ''] or lng in [None, '']:
        return ''
    return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(f'{lat},{lng}', safe='')


def maps_dir_url(nodes: list[str], mode: str = 'walking') -> str:
    clean = [str(c).strip() for c in nodes if str(c).strip()]
    if len(clean) < 2:
        return ''
    mode = mode if mode in {'walking', 'driving', 'bicycling', 'transit'} else 'walking'
    params = {'api': '1', 'origin': clean[0], 'destination': clean[-1], 'travelmode': mode}
    if len(clean) > 2:
        params['waypoints'] = '|'.join(clean[1:-1])
    return 'https://www.google.com/maps/dir/?' + urllib.parse.urlencode(params, safe='|,')


def location_label(loc: Any) -> str:
    if not loc:
        return ''
    if isinstance(loc, str):
        return loc.strip()
    if isinstance(loc, dict):
        return str(loc.get('name') or loc.get('address') or loc.get('label') or loc.get('query') or '').strip()
    return ''


def location_lat_lng(loc: Any) -> tuple[float | None, float | None]:
    if not isinstance(loc, dict):
        return None, None
    lat = loc.get('lat') if loc.get('lat') is not None else loc.get('latitude')
    lng = loc.get('lng') if loc.get('lng') is not None else loc.get('lon') if loc.get('lon') is not None else loc.get('longitude')
    if (lat is None or lng is None) and isinstance(loc.get('geo'), list) and len(loc['geo']) >= 2:
        lat, lng = loc['geo'][0], loc['geo'][1]
    return num(lat), num(lng)


def location_query(loc: Any) -> str:
    if not loc:
        return ''
    if isinstance(loc, str):
        return loc.strip()
    if isinstance(loc, dict):
        lat, lng = location_lat_lng(loc)
        if lat is not None and lng is not None:
            return f'{lat},{lng}'
        return str(loc.get('address') or loc.get('name') or loc.get('label') or loc.get('query') or '').strip()
    return ''


def route_endpoint_locations(doc: dict, route: dict) -> tuple[Any, Any]:
    trip = doc.get('trip_profile') or doc.get('profile') or {}
    start = route.get('start_location') or route.get('origin_location') or trip.get('start_location') or trip.get('origin_location') or doc.get('start_location') or route.get('origin') or trip.get('origin')
    end = route.get('end_location') or route.get('destination_location') or trip.get('end_location') or trip.get('destination_location') or doc.get('end_location') or route.get('destination') or trip.get('destination')
    if not location_query(end) and location_query(start):
        end = start
    return start, end


def route_endpoint_nodes(doc: dict, route: dict) -> tuple[dict, dict]:
    start_loc, end_loc = route_endpoint_locations(doc, route)
    start_q = location_query(start_loc)
    end_q = location_query(end_loc) or start_q
    start_label = location_label(start_loc) or start_q or tr(doc, 'unknown')
    end_label = location_label(end_loc) or start_label or end_q or tr(doc, 'unknown')
    start_lat, start_lng = location_lat_lng(start_loc)
    end_lat, end_lng = location_lat_lng(end_loc)
    return {'query': start_q, 'label': start_label, 'lat': start_lat, 'lng': start_lng}, {'query': end_q, 'label': end_label, 'lat': end_lat, 'lng': end_lng}


def route_nodes_with_endpoints(doc: dict, route: dict, stops: list[dict]) -> list[dict]:
    start_node, end_node = route_endpoint_nodes(doc, route)
    nodes = []
    if start_node.get('query'):
        nodes.append(start_node)
    for i, s in enumerate(stops):
        lat, lng = point_lat_lng(s)
        if lat is None or lng is None:
            continue
        nodes.append({'query': f'{lat},{lng}', 'label': point_name(s, i), 'lat': lat, 'lng': lng})
    if end_node.get('query'):
        nodes.append(end_node)
    return nodes


def build_overall_route_links(doc: dict, stops: list[dict], mode: str = 'walking', max_points_per_url: int = 11, route: dict | None = None) -> dict:
    nodes = route_nodes_with_endpoints(doc, route or {}, stops)
    if len(nodes) < 2:
        return {'overall_map_url': '', 'overall_map_url_parts': [], 'warning': tr(doc, 'coord_warning')}
    max_points_per_url = max(2, int(max_points_per_url or 11))
    queries = [n['query'] for n in nodes]
    labels = [n['label'] for n in nodes]
    if len(queries) <= max_points_per_url:
        url = maps_dir_url(queries, mode)
        return {'overall_map_url': url, 'overall_map_url_parts': [{'part': 1, 'from': labels[0], 'to': labels[-1], 'map_url': url, 'stop_count': len(queries)}], 'warning': None}
    parts = []
    start = 0
    part_no = 1
    while start < len(queries) - 1:
        end = min(start + max_points_per_url, len(queries))
        chunk = queries[start:end]
        url = maps_dir_url(chunk, mode)
        parts.append({'part': part_no, 'from': labels[start], 'to': labels[end - 1], 'map_url': url, 'stop_count': len(chunk)})
        if end >= len(queries):
            break
        start = end - 1
        part_no += 1
    return {'overall_map_url': parts[0]['map_url'] if parts else '', 'overall_map_url_parts': parts, 'warning': tr(doc, 'chunk_warning')}


def extract_work(doc: dict) -> dict:
    return doc.get('work') or doc.get('anime') or doc.get('subject') or {}


def extract_all_points(doc: dict) -> list[dict]:
    for key in ['points', 'anitabi_points', 'landmarks', 'all_points']:
        if isinstance(doc.get(key), list):
            return doc[key]
    nested = doc.get('pilgrimage_points') or doc.get('point_result') or {}
    if isinstance(nested, dict):
        for key in ['points', 'anitabi_points', 'landmarks', 'all_points']:
            if isinstance(nested.get(key), list):
                return nested[key]
    return []


def normalize_routes(doc: dict) -> list[dict]:
    routes_obj = doc.get('routes') or (doc.get('route_plan') or {}).get('routes')
    routes = []
    if isinstance(routes_obj, dict):
        a = routes_obj.get('route_a_full_all_points') or routes_obj.get('route_a') or routes_obj.get('Route A')
        if isinstance(a, dict):
            a = dict(a)
            a.setdefault('route_id', 'route_a_full_all_points')
            a.setdefault('display_name', tr(doc, 'route_a_name'))
            a.setdefault('points', extract_all_points(doc))
            routes.append(a)
        b = routes_obj.get('route_b_time_fit_by_day') or routes_obj.get('route_b') or routes_obj.get('Route B')
        if isinstance(b, list):
            for i, r in enumerate(b):
                if isinstance(r, dict):
                    rr = dict(r)
                    rr.setdefault('route_id', f'route_b_day_{rr.get("day_index") or i + 1}')
                    rr.setdefault('display_name', tr(doc, 'route_b_day', day=rr.get('day_index') or i + 1))
                    routes.append(rr)
        elif isinstance(b, dict):
            b = dict(b)
            b.setdefault('route_id', 'route_b')
            b.setdefault('display_name', tr(doc, 'route_b_name'))
            routes.append(b)
    elif isinstance(routes_obj, list):
        routes = [dict(r) for r in routes_obj if isinstance(r, dict)]
    if not routes:
        pts = extract_all_points(doc)
        if pts:
            routes.append({'route_id': 'route_a_full_all_points', 'display_name': tr(doc, 'route_a_name'), 'points': pts})
    all_pts = extract_all_points(doc)
    has_route_a = any('route_a' in str(r.get('route_id') or '').lower() for r in routes)
    if all_pts and not has_route_a:
        routes.insert(0, {'route_id': 'route_a_full_all_points', 'display_name': tr(doc, 'route_a_name'), 'points': all_pts})
    return routes


def route_points(route: dict) -> list[dict]:
    for key in ['points', 'stops', 'selected_points', 'route_points']:
        if isinstance(route.get(key), list):
            return route[key]
    return []


def route_omitted_points(doc: dict, route: dict, stops: list[dict]) -> list[dict]:
    if isinstance(route.get('omitted_points'), list):
        return route['omitted_points']
    all_pts = extract_all_points(doc)
    selected_ids = {point_id(p) for p in stops}
    return [p for p in all_pts if point_id(p) not in selected_ids]


def weather_summary(doc: dict, route: dict) -> str:
    for src in [route.get('weather_summary'), doc.get('weather_summary')]:
        if isinstance(src, str) and src.strip():
            return src.strip()
    w = doc.get('weather') or route.get('weather') or {}
    if isinstance(w, dict) and isinstance(w.get('summary'), str) and w.get('summary').strip():
        return w.get('summary').strip()
    return tr(doc, 'weather_none')


def css() -> str:
    return """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans SC','Noto Sans JP',Arial,sans-serif;margin:0;background:#faf7f0;color:#102033;line-height:1.55}
header{padding:24px 32px;background:#fff7e8;border-bottom:1px solid #e4d4bd}h1{margin:0 0 12px;font-size:30px}.card{background:#fff;border:1px solid #e2d6c7;border-radius:14px;margin:16px;padding:20px;box-shadow:0 1px 6px rgba(0,0,0,.06)}
.note{border-left:4px solid #e98213;background:#fff4df;padding:12px;margin:12px 0}.muted{color:#666}.small{font-size:12px;color:#666}button{border:1px solid #bfae9b;background:#fff;border-radius:8px;padding:7px 10px;margin:3px;cursor:pointer}button:hover{background:#fff6e7}a{color:#006d77}table{border-collapse:collapse;width:100%;background:#fff}th,td{border:1px solid #ddd;padding:8px;vertical-align:top}th{background:#f3f3f3}.stop-row{cursor:move}.drag-over{outline:2px dashed #e98213}.over-time{background:#fff0f0}.pill{display:inline-block;border-radius:999px;background:#eef;padding:2px 8px;margin:2px}.route-links li{margin:4px 0}@media print{button{display:none}.card{box-shadow:none;break-inside:avoid}body{background:#fff}}
"""


def render_stop_rows(doc: dict, stops: list[dict]) -> str:
    rows = []
    for i, p in enumerate(stops):
        lat, lng = point_lat_lng(p)
        image_url = point_photo_url(p)
        map_url = maps_search_url(lat, lng)
        stay = p.get('stay_min') or p.get('stay_minutes') or p.get('duration_min') or 20
        arrival = p.get('arrival') or p.get('planned_arrival') or p.get('arrival_time') or ''
        departure = p.get('departure') or p.get('planned_departure') or p.get('departure_time') or ''
        status = enum_label(doc, p.get('status') or p.get('schedule_status') or 'scheduled')
        hours = p.get('opening_hours') or p.get('hours') or tr(doc, 'unknown')
        price = p.get('price') or p.get('ticket_price') or p.get('avg_price') or tr(doc, 'unknown')
        notes = p.get('photo_notes') or point_notes(p)
        rows.append(f'''<tr class="stop-row" draggable="true" data-point-id="{esc(point_id(p) or i)}" data-lat="{esc(lat)}" data-lng="{esc(lng)}" data-name="{esc(point_name(p, i))}" data-photo="{esc(image_url)}" data-notes="{esc(notes)}" data-stay-min="{esc(stay)}">
<td class="order" contenteditable="true">{i + 1}</td><td class="arrival" contenteditable="true">{esc(arrival)}</td><td class="departure" contenteditable="true">{esc(departure)}</td><td class="stay" contenteditable="true">{esc(stay)}</td>
<td class="place" contenteditable="true"><strong>{esc(point_name(p, i))}</strong><br><small>{esc(lat)}, {esc(lng)}</small><br><small>{esc(tr(doc,'status'))}：{esc(status)}</small></td>
<td class="notes" contenteditable="true">{esc(notes)}<br>{link_html(image_url, tr(doc,'reference_image'))}</td><td contenteditable="true">{esc(hours)}<br><span class="small">{esc(tr(doc,'manual_confirm'))}</span></td><td contenteditable="true">{esc(price)}</td><td>{link_html(map_url, tr(doc,'map'))}</td><td><button onclick="deleteStopRow(this)">{esc(tr(doc,'delete'))}</button></td></tr>''')
    return '\n'.join(rows)


def render_omitted_rows(doc: dict, omitted: list[dict]) -> str:
    rows = []
    for i, p in enumerate(omitted):
        lat, lng = point_lat_lng(p)
        image_url = point_photo_url(p)
        notes = point_notes(p)
        stay = p.get('stay_min') or p.get('stay_minutes') or p.get('duration_min') or 20
        rows.append(f'''<tr class="omitted-row" draggable="true" data-point-id="{esc(point_id(p) or i)}" data-lat="{esc(lat)}" data-lng="{esc(lng)}" data-name="{esc(point_name(p, i))}" data-photo="{esc(image_url)}" data-notes="{esc(notes)}" data-stay-min="{esc(stay)}">
<td><strong>{esc(point_name(p, i))}</strong><br><small>{esc(lat)}, {esc(lng)}</small></td><td>{esc(notes)}<br>{link_html(image_url, tr(doc,'reference_image'))}</td><td>{link_html(maps_search_url(lat, lng), tr(doc,'map'))}</td><td><button onclick="addOmittedRow(this.closest('tr'))">{esc(tr(doc,'add_b'))}</button></td></tr>''')
    return '\n'.join(rows)


def render_overall_links(doc: dict, overall: dict) -> str:
    parts = overall.get('overall_map_url_parts') or []
    if not parts:
        return f'<p class="muted">{esc(tr(doc,"not_enough_coords"))}</p>'
    items = []
    for p in parts:
        label = tr(doc, 'open_part', n=p.get('part'), count=p.get('stop_count'))
        detail = f'{p.get("from", "")} → {p.get("to", "")}'
        items.append(f'<li>{esc(detail)}：{link_html(p.get("map_url"), label)}</li>')
    main = link_html(overall.get('overall_map_url'), tr(doc, 'open_current'))
    warning = f'<p class="small">{esc(overall.get("warning"))}</p>' if overall.get('warning') else ''
    return f'<p id="overallRouteMainWrap">{main}</p><ul id="overallRouteParts" class="route-links">{"".join(items)}</ul>{warning}'


def render_route(doc: dict, route: dict, idx: int) -> str:
    work = extract_work(doc)
    trip = doc.get('trip_profile') or doc.get('profile') or {}
    stops = route_points(route)
    omitted = route_omitted_points(doc, route, stops)
    rid = str(route.get('route_id') or '').lower()
    is_route_b = 'route_b' in rid or 'time' in str(route.get('selection_policy') or '').lower()
    route_title = route.get('display_name') or (tr(doc, 'route_b_day', day=route.get('day_index')) if route.get('day_index') else tr(doc, 'route_b_name') if is_route_b else tr(doc, 'route_a_name'))
    title = f'{work.get("title") or work.get("name") or "Anime"} {tr(doc, "title_suffix")}'
    date = route.get('date') or trip.get('date') or trip.get('start_date') or doc.get('date') or ''
    start_time = route.get('estimated_start') or route.get('start_time') or trip.get('local_start_time') or trip.get('start_time') or '09:00'
    end_time = route.get('estimated_end') or route.get('end_time') or trip.get('local_end_time') or trip.get('end_time') or '18:00'
    start_node, end_node = route_endpoint_nodes(doc, route)
    start_label = start_node.get('label') or tr(doc, 'unknown')
    end_label = end_node.get('label') or start_label or tr(doc, 'unknown')
    start_query = start_node.get('query') or ''
    end_query = end_node.get('query') or start_query
    endpoint_policy = route.get('end_location_policy') or trip.get('end_location_policy') or ('return_to_start' if end_query == start_query and start_query else 'user_specified')
    map_mode = enum_label(doc, route.get('map_mode') or trip.get('map_mode') or doc.get('map_mode') or 'google_maps_url_only')
    mobility = route.get('mobility') or trip.get('mobility') or doc.get('mobility') or {}
    max_walk = mobility.get('max_walking_distance_km') or route.get('max_walking_distance_km') or 1.5
    try:
        max_walk_f = float(max_walk)
    except Exception:
        max_walk_f = 1.5
    overall = build_overall_route_links(doc, stops, 'walking', int(route.get('max_points_per_url') or 11), route)
    note = tr(doc, 'route_b_note') if is_route_b else tr(doc, 'route_a_note')
    endpoint_note = f'<div class="note">{esc(tr(doc, "endpoint_return"))}</div>' if endpoint_policy == 'return_to_start' else ''
    labels = {**UI['en'], **UI.get(lang_family(lang_code(doc)), UI['en'])}
    labels['not_enough_coords'] = tr(doc, 'not_enough_coords')
    labels['open_current'] = tr(doc, 'open_current')
    html_text = f'''<!doctype html><html lang="{esc(lang_code(doc))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title><style>{css()}</style></head><body>
<header><h1>{esc(title)}</h1><p><strong>{esc(tr(doc,'work'))}：</strong>{esc(work.get('title') or work.get('name') or '')} &nbsp; <strong>{esc(tr(doc,'bangumi_id'))}：</strong>{esc(work.get('bangumi_id') or work.get('id') or doc.get('bangumi_id') or '')}</p>
<p><strong>{esc(tr(doc,'date'))}：</strong>{esc(date)} &nbsp; <strong>{esc(tr(doc,'time'))}：</strong>{esc(start_time)} - {esc(end_time)}</p><p><strong>{esc(tr(doc,'start_end'))}：</strong>{esc(start_label)} → {esc(end_label)} <span class="small">({esc(enum_label(doc, endpoint_policy))})</span></p>
<p><strong>{esc(tr(doc,'route'))}：</strong>{esc(route_title)} &nbsp; <strong>{esc(tr(doc,'route_strategy'))}：</strong>{esc(enum_label(doc, route.get('selection_policy') or route.get('policy') or ('time_fit' if is_route_b else 'all_valid_anitabi_points')))}</p><p><strong>{esc(tr(doc,'map_mode'))}：</strong>{esc(map_mode)} &nbsp; <strong>{esc(tr(doc,'max_walk'))}：</strong>{esc(max_walk_f)} km</p><div class="note">{esc(note)}</div>{endpoint_note}<button onclick="window.print()">{esc(tr(doc,'print'))}</button><button onclick="exportText()">{esc(tr(doc,'export'))}</button></header>
<section class="card"><h2>{esc(tr(doc,'overall_link'))}</h2>{render_overall_links(doc, overall)}<button onclick="rebuildOverallRouteLinks()">{esc(tr(doc,'rebuild'))}</button><button onclick="recalculateSchedule()">{esc(tr(doc,'recalc'))}</button><p class="small">{esc(tr(doc,'maps_reference'))}</p></section>
<section class="card"><h2>{esc(tr(doc,'weather'))}</h2><p contenteditable="true">{esc(weather_summary(doc, route))}</p></section>
<section class="card"><h2>{esc(tr(doc,'limits'))}</h2><ul contenteditable="true"><li>{esc(tr(doc,'warning'))}</li><li>{esc(tr(doc,'start_end'))}：{esc(start_label)} → {esc(end_label)}</li><li>{esc(tr(doc,'map_mode'))}：{esc(map_mode)}</li></ul></section>
<section class="card"><h2>{esc(tr(doc,'timeline_drag') if is_route_b else tr(doc,'timeline'))}</h2><p id="scheduleStatus" class="small">{esc(tr(doc,'manual_confirm'))}</p><table id="stops"><thead><tr><th>{esc(tr(doc,'order'))}</th><th>{esc(tr(doc,'arrival'))}</th><th>{esc(tr(doc,'departure'))}</th><th>{esc(tr(doc,'stay'))}</th><th>{esc(tr(doc,'place'))}</th><th>{esc(tr(doc,'photo'))}</th><th>{esc(tr(doc,'hours'))}</th><th>{esc(tr(doc,'price'))}</th><th>{esc(tr(doc,'map'))}</th><th>{esc(tr(doc,'action'))}</th></tr></thead><tbody>{render_stop_rows(doc, stops)}</tbody></table></section>
<section class="card"><h2>{esc(tr(doc,'segments'))}</h2><table id="segments"><thead><tr><th>#</th><th>{esc(tr(doc,'from'))}</th><th>{esc(tr(doc,'to'))}</th><th>{esc(tr(doc,'mode'))}</th><th>{esc(tr(doc,'distance'))}</th><th>{esc(tr(doc,'duration'))}</th><th>{esc(tr(doc,'link'))}</th></tr></thead><tbody></tbody></table></section>
<section class="card"><h2>{esc(tr(doc,'omitted'))}</h2><p class="small">{esc(tr(doc,'omitted_help_b') if is_route_b else tr(doc,'omitted_help'))}</p><table id="omitted"><thead><tr><th>{esc(tr(doc,'place'))}</th><th>{esc(tr(doc,'photo'))}</th><th>{esc(tr(doc,'map'))}</th><th>{esc(tr(doc,'action'))}</th></tr></thead><tbody>{render_omitted_rows(doc, omitted)}</tbody></table>{'<p class="muted">' + esc(tr(doc,'omitted_empty')) + '</p>' if not omitted else ''}</section>
<section class="card"><h2>{esc(tr(doc,'manual_check'))}</h2><ul contenteditable="true"><li>{esc(tr(doc,'manual_1'))}</li><li>{esc(tr(doc,'manual_2'))}</li><li>{esc(tr(doc,'manual_3'))}</li><li>{esc(tr(doc,'manual_4'))}</li></ul></section>
<script>
const LABELS={js(labels)};const MAX_POINTS_PER_GOOGLE_MAPS_URL=11;const TRIP_START_TIME={js(str(start_time))};const TRIP_END_TIME={js(str(end_time))};const MAX_WALKING_KM={max_walk_f};const ROUTE_START_QUERY={js(start_query)};const ROUTE_END_QUERY={js(end_query)};let draggedRow=null;
function mapsDirUrl(nodes,mode='walking'){{const coords=(nodes||[]).filter(x=>String(x||'').trim());if(coords.length<2)return'';const p=new URLSearchParams();p.set('api','1');p.set('origin',coords[0]);p.set('destination',coords[coords.length-1]);p.set('travelmode',mode);if(coords.length>2)p.set('waypoints',coords.slice(1,-1).join('|'));return 'https://www.google.com/maps/dir/?'+p.toString();}}
function singleSegmentUrl(a,b,mode='walking'){{const p=new URLSearchParams();p.set('api','1');p.set('origin',a.lat+','+a.lng);p.set('destination',b.lat+','+b.lng);p.set('travelmode',mode==='transit'?'transit':'walking');return 'https://www.google.com/maps/dir/?'+p.toString();}}
function rows(){{return Array.from(document.querySelectorAll('#stops tbody tr'));}}function data(row){{return{{pointId:row.dataset.pointId||'',name:row.dataset.name||'',lat:row.dataset.lat||'',lng:row.dataset.lng||'',photo:row.dataset.photo||'',notes:row.dataset.notes||'',stayMin:parseInt((row.querySelector('.stay')?.textContent||row.dataset.stayMin||'20').trim(),10)||20}};}}
function coords(){{return rows().map(r=>[r.dataset.lat,r.dataset.lng]).filter(x=>x[0]&&x[1]).map(x=>x[0]+','+x[1]);}}function routeNodes(){{let c=coords(),nodes=[];if(ROUTE_START_QUERY)nodes.push(ROUTE_START_QUERY);nodes=nodes.concat(c);if(ROUTE_END_QUERY)nodes.push(ROUTE_END_QUERY);return nodes.length>=2?nodes:c;}}
function rebuildOverallRouteLinks(){{const c=routeNodes(),mainWrap=document.getElementById('overallRouteMainWrap'),list=document.getElementById('overallRouteParts');list.innerHTML='';if(c.length<2){{mainWrap.innerHTML=escHtml(LABELS.not_enough_coords||'Not enough coordinates');return;}}let chunks=[];for(let s=0;s<c.length-1;){{let e=Math.min(s+MAX_POINTS_PER_GOOGLE_MAPS_URL,c.length);chunks.push(c.slice(s,e));if(e>=c.length)break;s=e-1;}}mainWrap.innerHTML=linkHtml(mapsDirUrl(chunks[0]),LABELS.open_current||'Open current route');chunks.forEach((ch,i)=>{{let li=document.createElement('li');li.innerHTML=linkHtml(mapsDirUrl(ch),(i+1)+'. Google Maps ('+ch.length+')');list.appendChild(li);}});}}
function parseHHMM(t,f){{const m=String(t||'').match(/([0-9]{{1,2}}):([0-9]{{2}})/);return m?parseInt(m[1])*60+parseInt(m[2]):f;}}function fmt(x){{x=Math.round(x);return String(Math.floor(x/60)%24).padStart(2,'0')+':'+String(x%60).padStart(2,'0');}}
function km(a,b){{const R=6371,la1=Number(a.lat)*Math.PI/180,la2=Number(b.lat)*Math.PI/180,dla=la2-la1,dlo=(Number(b.lng)-Number(a.lng))*Math.PI/180,h=Math.sin(dla/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dlo/2)**2;return 2*R*Math.atan2(Math.sqrt(h),Math.sqrt(1-h));}}
async function leg(a,b){{const d=km(a,b);if(!isFinite(d))return{{distanceKm:0,minutes:0,mode:'walking',source:LABELS.manual_confirm,manual:true}};if(d>MAX_WALKING_KM)return{{distanceKm:d,minutes:Math.max(12,Math.round(d*8+12)),mode:'transit',source:LABELS.manual_confirm,manual:true}};return{{distanceKm:d*1.25,minutes:Math.max(3,Math.round(d*1.25/4.2*60)),mode:'walking',source:'OSRM / OpenStreetMap or distance estimate',manual:true}};}}
function updateOrders(){{rows().forEach((r,i)=>{{const o=r.querySelector('.order');if(o)o.textContent=String(i+1);}});}}function deleteStopRow(btn){{btn.closest('tr')?.remove();updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}}
function escHtml(s){{return String(s||'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}function normalizeUrl(url){{url=String(url||'').trim().replace(/[“”]/g,'"');if(url.startsWith('//'))url='https:'+url;if(!/^https?:[/][/]/i.test(url))return'';return url;}}function linkHtml(url,label){{const u=normalizeUrl(url);if(!u)return'';return `<a href="${{escHtml(u)}}" target="_blank" rel="noopener noreferrer">${{escHtml(label)}}</a>`;}}
function createStopRow(d){{const tr=document.createElement('tr');tr.draggable=true;tr.className='stop-row';Object.assign(tr.dataset,{{pointId:d.pointId||'',lat:d.lat||'',lng:d.lng||'',name:d.name||'',photo:normalizeUrl(d.photo||''),notes:d.notes||'',stayMin:d.stayMin||'20'}});const m=d.lat&&d.lng?'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(d.lat+','+d.lng):'';tr.innerHTML=`<td class="order" contenteditable="true"></td><td class="arrival" contenteditable="true"></td><td class="departure" contenteditable="true"></td><td class="stay" contenteditable="true">${{escHtml(d.stayMin||20)}}</td><td class="place" contenteditable="true"><strong>${{escHtml(d.name||'')}}</strong><br><small>${{escHtml(d.lat||'')}}, ${{escHtml(d.lng||'')}}</small><br><small>${{escHtml(LABELS.status||'Status')}}：${{escHtml(LABELS.manual_added||'Manually added')}}</small></td><td class="notes" contenteditable="true">${{escHtml(d.notes||'')}}<br>${{linkHtml(d.photo,LABELS.reference_image||'Reference image')}}</td><td contenteditable="true">${{escHtml(LABELS.unknown||'Unknown')}}<br>${{escHtml(LABELS.manual_confirm||'Manual confirmation')}}</td><td contenteditable="true">${{escHtml(LABELS.unknown||'Unknown')}}</td><td>${{linkHtml(m,LABELS.map||'Map')}}</td><td><button onclick="deleteStopRow(this)">${{escHtml(LABELS.delete||'Delete')}}</button></td>`;bindStopRowDrag(tr);return tr;}}
function addOmittedRow(row,before=null){{if(!row)return;const d={{pointId:row.dataset.pointId,name:row.dataset.name,lat:row.dataset.lat,lng:row.dataset.lng,photo:row.dataset.photo,notes:row.dataset.notes,stayMin:row.dataset.stayMin}};const tr=createStopRow(d),tb=document.querySelector('#stops tbody');before?tb.insertBefore(tr,before):tb.appendChild(tr);row.remove();updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}}
function bindStopRowDrag(r){{r.addEventListener('dragstart',e=>{{draggedRow=r;e.dataTransfer.effectAllowed='move';}});r.addEventListener('dragover',e=>{{e.preventDefault();r.classList.add('drag-over');}});r.addEventListener('dragleave',()=>r.classList.remove('drag-over'));r.addEventListener('drop',e=>{{e.preventDefault();r.classList.remove('drag-over');if(!draggedRow||draggedRow===r)return;if(draggedRow.classList.contains('omitted-row'))addOmittedRow(draggedRow,r);else document.querySelector('#stops tbody').insertBefore(draggedRow,r);updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}});}}
function bindOmittedDrag(r){{r.addEventListener('dragstart',e=>{{draggedRow=r;e.dataTransfer.effectAllowed='move';}});}}function setupDragDrop(){{document.querySelectorAll('#stops tbody tr').forEach(bindStopRowDrag);document.querySelectorAll('#omitted tbody tr').forEach(bindOmittedDrag);const tb=document.querySelector('#stops tbody');tb.addEventListener('dragover',e=>e.preventDefault());tb.addEventListener('drop',e=>{{e.preventDefault();if(!draggedRow)return;if(draggedRow.classList.contains('omitted-row'))addOmittedRow(draggedRow);else tb.appendChild(draggedRow);updateOrders();rebuildOverallRouteLinks();recalculateSchedule();}});}}
async function recalculateSchedule(){{const rs=rows();let cur=parseHHMM(TRIP_START_TIME,540),limit=parseHHMM(TRIP_END_TIME,1080);const seg=document.querySelector('#segments tbody');seg.innerHTML='';for(let i=0;i<rs.length;i++){{rs[i].classList.remove('over-time');if(i>0){{const a=data(rs[i-1]),b=data(rs[i]),l=await leg(a,b);cur+=l.minutes;const tr=document.createElement('tr');tr.innerHTML=`<td>${{i}}</td><td>${{escHtml(a.name)}}</td><td>${{escHtml(b.name)}}</td><td>${{escHtml(l.mode==='transit'?LABELS.transit:LABELS.walking)}}</td><td>${{l.distanceKm.toFixed(2)}} km</td><td>${{l.minutes}} min<br><small>${{escHtml(l.source)}}</small></td><td>${{linkHtml(singleSegmentUrl(a,b,l.mode),LABELS.route||'Route')}}</td>`;seg.appendChild(tr);}}const stay=parseInt(rs[i].querySelector('.stay')?.textContent||'20',10)||20;rs[i].querySelector('.arrival').textContent=fmt(cur);cur+=stay;rs[i].querySelector('.departure').textContent=fmt(cur);if(limit&&cur>limit)rs[i].classList.add('over-time');}}updateOrders();document.getElementById('scheduleStatus').textContent=(LABELS.manual_confirm||'Manual confirmation')+'; '+fmt(cur);}}
function exportText(){{const blob=new Blob([document.body.innerText],{{type:'text/plain;charset=utf-8'}});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='pilgrimage-itinerary.txt';a.click();URL.revokeObjectURL(url);}}
setupDragDrop();updateOrders();
</script></body></html>'''
    return html_text


def safe_filename(route: dict, idx: int) -> str:
    rid = str(route.get('route_id') or '').lower()
    if 'route_a' in rid or rid == 'a' or (idx == 0 and 'route_b' not in rid):
        return 'pilgrimage_route_A.html'
    day = route.get('day_index')
    if day:
        return f'pilgrimage_route_B_day_{day}.html'
    m = re.search(r'day[_-]?(\d+)', rid)
    if m:
        return f'pilgrimage_route_B_day_{m.group(1)}.html'
    if rid in {'b', 'route_b'}:
        return 'pilgrimage_route_B.html'
    clean = re.sub(r'[^A-Za-z0-9_-]+', '_', rid or f'route_{idx + 1}').strip('_')
    return f'pilgrimage_route_{clean}.html'


def main() -> None:
    parser = argparse.ArgumentParser(description='Build editable HTML anime-pilgrimage itinerary pages.')
    parser.add_argument('json_file')
    parser.add_argument('--output-dir', default='output')
    args = parser.parse_args()
    doc = json.loads(Path(args.json_file).read_text(encoding='utf-8'))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    routes = normalize_routes(doc)
    files = []
    for i, route in enumerate(routes):
        html_text = render_route(doc, route, i)
        name = safe_filename(route, i)
        path = out_dir / name
        path.write_text(html_text, encoding='utf-8')
        files.append({'route_id': route.get('route_id') or name, 'path': str(path), 'editable': True, 'supports_drag_drop_reorder': True, 'supports_route_b_add_omitted_points': True, 'supports_time_recalculation': True, 'includes_start_end_locations': True})
    print(json.dumps({'stage': 'html_itinerary', 'output_language': doc.get('output_language'), 'html_files': files, 'summary': f'Generated {len(files)} HTML itinerary file(s).'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()