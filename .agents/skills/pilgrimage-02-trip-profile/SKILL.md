---
name: pilgrimage-02-trip-profile
description: Collect and normalize trip date, local time window, hotel/start location, transport preferences, and pace for an anime pilgrimage plan.
---

# Stage 2: Trip Profile Collection

## Shared Constraint Requirement

Before executing this skill, read and follow the shared constraints defined in:

```text
.agents/skills/pilgrimage-constraints/references/pilgrimage-constraints.md
```

These constraints are mandatory. They define route structure, multi-day behavior, language output behavior, endpoint fallback, file generation policy, Google Maps fallback behavior, and HTML output requirements.

Do not override these constraints unless the user explicitly asks to change the skill rules.


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

## Output Language Collection

Ask or infer the user's preferred output language for the final route and HTML itinerary.

Rules:

- If the user explicitly requests a language, store it in `output_language.primary`.
- If the user requests bilingual output, set `output_language.mode` to `bilingual` and store the second language in `output_language.secondary`.
- If the user does not specify a language, infer it from the user's latest request.
- Preserve the selected language in `trip_profile.output_language` so downstream route planning and HTML generation can use it.

## Endpoint Fallback

Ask for the starting location and the ending location. If the user does not provide an ending location, use the starting location as the ending location and set:

```json
{
  "end_location_policy": "return_to_start"
}
```

User-facing explanation should follow the selected output language. In Chinese, say: `未指定终点，默认最终返回出发地。`
