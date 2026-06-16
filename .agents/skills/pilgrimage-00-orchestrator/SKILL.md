---
name: pilgrimage-00-orchestrator
description: Orchestrate the staged anime pilgrimage planning workflow by passing each stage's JSON output into the next skill.
---

# Anime Pilgrimage Skill Orchestrator

Use this skill when the user wants a multi-stage anime pilgrimage planning workflow, or when they say they want each skill output to become the next skill input.

## Required staged order

Run or instruct Codex to follow this order:

1. `$pilgrimage-01-anime-search-confirm`
2. `$pilgrimage-02-trip-profile`
3. `$pilgrimage-03-anitabi-points`
4. `$pilgrimage-04-route-weather`
5. `$pilgrimage-05-place-hours-prices`
6. `$pilgrimage-06-html-plan`

Each stage must output the JSON contract in `shared/references/output-contracts.md`. Preserve the JSON exactly enough that the next stage can consume it.

## Conversation policy

- Do not ask the user for all information at the beginning.
- First confirm the anime work.
- After the work is confirmed, collect trip date, local schedule, start/end place, transport preference, pace, maximum acceptable walking distance per segment, Google Maps API availability, must-visit points, avoid points, and budget/meal preferences if relevant. Do not ask the user to paste any API key into chat; only ask whether `GOOGLE_MAPS_API_KEY` can be configured.
- If the user asks to proceed without details, make conservative assumptions and record them.

## State handoff

Maintain a planning state object:

```json
{
  "anime_candidates": null,
  "confirmed_work_and_trip_profile": null,
  "pilgrimage_points": null,
  "route_weather_plan": null,
  "enriched_places": null,
  "html_itinerary": null
}
```

After each skill finishes, insert its JSON output into the state object under the matching key.

## Failure handling

- If Bangumi search is ambiguous, stop and ask for confirmation.
- If Anitabi has no points for the selected work, suggest searching by related season, alias, location keyword, or Anitabi point ID.
- If Google Maps API is unavailable, continue with Google Maps route/search URLs and rough estimates. Warn that real-time Google routes, opening hours, ratings, and price levels cannot be automatically retrieved and must be manually confirmed.
- If an estimated walking segment exceeds `max_walking_distance_km`, choose public transit or mark the segment as transit/manual-confirmation instead of forcing walking.
- If weather forecast is unavailable for the date, mark it as unavailable and keep the plan route-focused.
- If price or hours cannot be verified, write `unknown` instead of guessing.
- Route planning must produce two distinct options: Route A covers all valid Anitabi coordinate points, while Route B is filtered according to the user's available time window. Do not make both routes identical unless there are so few points that all fit comfortably.
- Route B HTML should remain editable after generation: omitted points can be added back, rows can be dragged to reorder, route links can be rebuilt, and times can be recalculated from the edited order.

## Final output

Return:

- Route A summary: all-point coverage and total/chunked Google Maps links
- Route B summary: time-fit selected subset, omitted point count, and note that omitted points can be added back in the HTML
- weather summary
- restaurant/attraction hours and price notes
- manual verification list
- generated editable HTML file paths


## Chinese output requirement

For the final user-facing itinerary, HTML pages, weather summaries, route labels, warning text, status fields, and manual-check notes, use Chinese by default. Keep only proper nouns and technical product names such as Bangumi, Anitabi, Google Maps, OSRM, OpenStreetMap, API, URL, HTML, CSV, KML, and JSON in English when needed. Do not output internal enum values such as `google_maps_url_only`, `balanced_time_fit`, `time_fit`, `unknown`, `scheduled`, or `manual-added` directly in the HTML; convert them to Chinese display text.
