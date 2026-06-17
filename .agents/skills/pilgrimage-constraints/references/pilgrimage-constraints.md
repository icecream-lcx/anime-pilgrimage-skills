# Anime Pilgrimage Planning Constraints

This file defines mandatory constraints for all anime pilgrimage planning skills.

These rules override normal route-planning preferences unless the user explicitly asks to change them.

---

## 1. Language Output Policy

The itinerary language must follow the user's request.

Rules:

- If the user explicitly requests a language, use that language for all final user-facing outputs.
- If the user does not specify a language, use the language of the user's latest request.
- If the user mixes languages but mainly uses Chinese, default to Chinese.
- If the user asks for bilingual output, generate bilingual labels and notes.
- Proper nouns may remain in their original form when translation would reduce clarity.

The selected language must be stored in the trip profile, route plan, and final HTML generation input.

Recommended JSON fields:

```json
{
  "output_language": {
    "primary": "zh-CN",
    "secondary": null,
    "mode": "single",
    "source": "user_requested|inferred|default"
  }
}
```

Supported examples:

```text
zh-CN        简体中文
zh-TW        繁體中文
en           English
ja           日本語
ko           한국어
fr           Français
es           Español
bilingual    Bilingual output, such as zh-CN + en
```

The selected language must affect:

- HTML page title.
- Route names.
- Route warnings.
- Weather summaries.
- Manual-check notes.
- Button labels.
- Table headers.
- Place notes.
- Transportation notes.
- Price and opening-hour notes.
- Route A / Route B descriptions.
- Omitted-point section.
- Add, delete, drag, rebuild, and recalculate instructions.

Do not translate these proper nouns or technical terms unless the user explicitly asks:

```text
Bangumi
Anitabi
Google Maps
OSRM
OpenStreetMap
API
URL
HTML
CSV
KML
JSON
Route A
Route B
```

However, explanatory text around them should follow the selected language.

Examples:

Chinese:

```text
Route A：全量点位路线
Route B：时间适配路线
未配置 Google Maps API 时，只能提供 Google Maps URL 链接和人工确认项。
```

English:

```text
Route A: Full landmark route
Route B: Time-fit route
When Google Maps API is not configured, only Google Maps URL links and manual-confirmation items can be provided.
```

Japanese:

```text
Route A：全ランドマークルート
Route B：時間適応ルート
Google Maps API が設定されていない場合、Google Maps URL と手動確認項目のみを提供します。
```

---

## 2. Route A and Route B Policy

Always preserve two route concepts.

### Route A: Full Anitabi Landmark Route

Route A must include every valid Anitabi point with coordinates.

Rules:

- Route A must always exist.
- Route A must not be filtered by the user's available time.
- Route A must not be removed in multi-day trips.
- Route A must cover all valid Anitabi coordinate points.
- If there are too many points for one stable Google Maps URL, generate sequential chunked Google Maps route links that together cover all points.
- Route A is used as the complete landmark coverage route.

Recommended output filename:

```text
pilgrimage_route_A.html
```

### Route B: Time-fit Route

Route B is the practical route based on the user's available travel time.

Rules:

- Route B may select only a realistic subset of points.
- Route B should consider the user's date, available time, start location, walking-distance preference, weather, and stop duration.
- Omitted Anitabi points must not be deleted.
- Omitted points must be shown in the generated HTML.
- Users must be able to add omitted points back into Route B.
- Users must be able to drag points to reorder Route B.
- Users must be able to delete unwanted points from Route B.
- After editing Route B, users must be able to rebuild Google Maps route links and recalculate arrival/departure times.

Recommended output filenames for multi-day trips:

```text
pilgrimage_route_B_day_1.html
pilgrimage_route_B_day_2.html
pilgrimage_route_B_day_3.html
```

---

## 3. Multi-day Trip Policy

When the user's trip spans multiple days, do not replace Route A with daily Route B pages.

For a two-day trip, the expected outputs are:

```text
pilgrimage_route_A.html
pilgrimage_route_B_day_1.html
pilgrimage_route_B_day_2.html
```

Route A must cover all valid Anitabi points across the entire trip.

Route B may be split by day and may filter points according to the user's daily available time.

Daily Route B pages must preserve omitted points and allow users to add them back manually.

---

## 4. Endpoint Fallback Policy

If the user does not specify an ending location, use the starting location as the ending location.

Rules:

- If the user provides an ending location, set `end_location_policy` to `user_specified`.
- If the user does not provide an ending location, copy `start_location` into `end_location`.
- In that case, set `end_location_policy` to `return_to_start`.
- Do not leave `end_location` empty when `start_location` is available.
- Route A and Route B must both follow this rule.
- For multi-day trips, if the user does not provide daily ending locations, each day should default to returning to that day's start location or hotel.

Chinese explanation:

```text
未指定终点，默认最终返回出发地。
```

English explanation:

```text
No ending location was specified, so the route will return to the starting point by default.
```

Expected JSON fields:

```json
{
  "start_location": {
    "name": "",
    "address": "",
    "lat": null,
    "lng": null
  },
  "end_location": {
    "name": "",
    "address": "",
    "lat": null,
    "lng": null
  },
  "end_location_policy": "user_specified|return_to_start"
}
```

---

## 5. Google Maps API Fallback Policy

If `GOOGLE_MAPS_API_KEY` is not configured, use Google Maps URL-only mode.

Rules:

- Generate Google Maps point links using coordinate-only URLs.
- Generate Google Maps route links using origin, destination, and waypoints.
- If a route has too many points, split it into sequential route parts.
- Do not claim that real-time route durations, opening hours, ratings, or price levels were automatically retrieved.
- Mark real-time routes, opening hours, ratings, and price levels as unavailable or requiring manual confirmation.
- Public-transit durations should be checked manually in Google Maps before departure.

Chinese warning:

```text
未配置 Google Maps API 时，只能提供 Google Maps URL 链接和人工确认项，无法自动获取 Google 的实时路线、营业时间、评分和价格等级。
```

English warning:

```text
When Google Maps API is not configured, only Google Maps URL links and manual-confirmation items can be provided. Real-time routes, opening hours, ratings, and price levels cannot be retrieved automatically.
```

---

## 6. Walking Distance Policy

Ask the user for the maximum acceptable walking distance per segment.

Rules:

- If the user provides a maximum walking distance, use that value.
- If a walking segment exceeds the user's limit, switch the segment to public transit or mark it for manual transit confirmation.
- If the user does not provide a value, use a reasonable default and clearly state it.

Expected JSON field:

```json
{
  "mobility": {
    "max_walking_distance_km": 1.5,
    "walking_distance_source": "user|default",
    "switch_to_transit_if_exceeded": true
  }
}
```

---

## 7. File Generation Policy

The `shared/` directory is a stable source directory.

Do not create temporary scripts, generated helpers, experiments, debug files, or one-off code inside:

```text
.agents/skills/shared/scripts/
.agents/skills/shared/references/
```

Allowed write locations during normal execution:

```text
output/
_codex_generated/
_scratch/
tmp/
temp/
```

Rules:

- Use existing scripts in `shared/scripts/`.
- If temporary helper code is needed, write it under `_codex_generated/`.
- If temporary notes or experiments are needed, write them under `_scratch/`.
- Runtime itinerary outputs should go to `output/`.
- Curated public examples should go to `examples/` only when the user explicitly asks.
- Do not modify `shared/` unless the user explicitly asks to update the Skill source code itself.

---

## 8. GitHub-safe Output Policy

Generated temporary folders should not be uploaded to GitHub.

The repository `.gitignore` should include:

```gitignore
output/
_codex_generated/
_scratch/
tmp/
temp/
.env
.env.*
*.key
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
*.tmp
*.log
```

The `examples/` folder may be committed only when it contains curated public examples.

Do not commit private hotel addresses, API keys, tokens, `.env` files, temporary debug scripts, or raw personal travel information.

---

## 9. HTML Output Policy

Final user-facing HTML must follow the selected `output_language`.

Rules:

- Weather summaries must follow the selected language.
- Route labels must follow the selected language.
- Warning text must follow the selected language.
- Manual-check notes must follow the selected language.
- Button labels and table headers must follow the selected language.
- Internal enum values must not be displayed directly.

Convert internal enum values before displaying.

Chinese display mapping:

```text
google_maps_url_only → 仅使用 Google Maps 链接模式
balanced_time_fit → 均衡时间适配
time_fit → 时间适配路线
unknown → 未知
scheduled → 已安排
unscheduled → 灵活安排
manual-added → 手动加入
walking → 步行
transit → 公共交通
return_to_start → 返回出发地
user_specified → 用户指定终点
```

English display mapping:

```text
google_maps_url_only → Google Maps URL-only mode
balanced_time_fit → Balanced time-fit
time_fit → Time-fit route
unknown → Unknown
scheduled → Scheduled
unscheduled → Flexible
manual-added → Manually added
walking → Walking
transit → Public transit
return_to_start → Return to start
user_specified → User-specified endpoint
```

If a requested language is not explicitly covered by a mapping table, translate labels naturally and keep proper nouns unchanged.

---

## 10. Required Route Plan Structure

Route planning output should preserve both route concepts.

Recommended structure:

```json
{
  "stage": "route_plan",
  "output_language": {
    "primary": "zh-CN",
    "secondary": null,
    "mode": "single",
    "source": "user_requested|inferred|default"
  },
  "routes": {
    "route_a_full_all_points": {
      "route_id": "route_a_full_all_points",
      "display_name": "Route A：全量点位路线",
      "scope": "all_days",
      "selection_policy": "all_valid_anitabi_points",
      "points": [],
      "omitted_points": [],
      "overall_map_url": "",
      "overall_map_url_parts": []
    },
    "route_b_time_fit_by_day": [
      {
        "route_id": "route_b_day_1",
        "display_name": "Route B：第 1 天时间适配路线",
        "scope": "single_day",
        "day_index": 1,
        "date": "",
        "selection_policy": "time_fit_subset",
        "points": [],
        "omitted_points": [],
        "overall_map_url": "",
        "overall_map_url_parts": []
      }
    ]
  }
}
```

Rules:

- `route_a_full_all_points` is required for every itinerary.
- `route_a_full_all_points.points` must include all valid Anitabi points with coordinates.
- `route_b_time_fit_by_day` may contain one or more daily time-fit routes.
- Multi-day trips must not remove Route A.
- Omitted points in Route B must still be preserved and shown in the generated HTML.
- The selected `output_language` must be preserved from trip profile to route plan to final HTML.
