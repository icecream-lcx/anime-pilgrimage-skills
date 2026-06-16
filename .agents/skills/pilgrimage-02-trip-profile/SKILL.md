---
name: pilgrimage-02-trip-profile
description: Collect and normalize trip date, local time window, hotel/start location, transport preferences, and pace for an anime pilgrimage plan.
---

# Stage 2: Trip Profile Collection

Use this skill after the anime work has been confirmed.

## Required inputs

Consume the selected work from the `anime_candidates` output or direct user confirmation.

Collect these fields:

- trip date in `YYYY-MM-DD`
- local start time and local end time
- starting place, hotel, station, or local base
- end place if different from start place
- transport preferences: walking, public transit, taxi, drive, mixed
- maximum acceptable walking distance per segment, in kilometers or meters
- Google Maps API availability: whether the user can configure `GOOGLE_MAPS_API_KEY` in the environment; never ask them to paste the key into chat
- map mode: `google_api` if a key is available, otherwise `google_maps_url_only`
- pace: relaxed, normal, tight
- must-visit points or scenes if any
- points/categories to avoid if any
- meal preferences or budget notes if relevant

## Default assumptions when user wants to continue immediately

Use these only when necessary and mark them clearly:

- date: ask again if missing; do not invent a date unless the user explicitly asks for a sample plan
- time window: 09:00-18:00
- start and end: nearest major station in the destination area if known, otherwise hotel/base unknown
- transport: walking + public transit
- maximum acceptable walking distance: 1.5 km per segment
- Google Maps API availability: unknown; if not confirmed, use `google_maps_url_only` and warn about manual verification
- pace: normal

## Output

Return a short summary and JSON using the `confirmed_work_and_trip_profile` contract.

Set `ready_for_points` to true only when the work is confirmed and enough trip profile data exists to retrieve and route points.

## Required warning when no Google Maps API key is available

If the user says they do not have a Google Maps API key, or if availability is unknown and you proceed in fallback mode, include this warning in the human summary and JSON assumptions:

`未配置 Google Maps API 时，将改用 Google Maps URL 链接模式；无法自动获取 Google 的实时路线、营业时间、评分和价格等级，只能提供搜索链接，或将这些字段标注为需要人工确认。`
