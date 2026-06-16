---
name: pilgrimage-04-route-weather
description: Build two anime pilgrimage route options: Route A covers all Anitabi points, Route B is time-fit according to the user's available schedule.
---

# Stage 4: Route and Weather Planning

Use this skill after `pilgrimage_points` and `trip_profile` are available.

## Inputs

- Confirmed work and Bangumi ID
- Trip profile: date, local start/end time, start/end place, transport preference, Google Maps API availability, maximum walking distance per segment
- Normalized Anitabi points

## Required two-route policy

Always generate **two route options** when there are enough valid Anitabi coordinate points.

### Route A: 全量点位路线 / All Anitabi Points Route

- `route_id`: `A`
- `route_type`: `all_points`
- `strategy`: `all_points`
- `point_policy`: `all_valid_anitabi_points_included`
- Purpose: cover **all valid Anitabi coordinate points**.
- Do not drop, hide, reorder by subjective preference, or replace Anitabi points because the day is too short.
- You may optimize geographic order for route convenience, but every valid coordinate point must remain visible in `routes[0].stops`.
- If the user's time window cannot realistically cover all points, keep overflow points and mark their `planned_arrival` / `planned_departure` as `灵活安排`, `未排定`, or similar.
- Generate `overall_map_url` and `overall_map_url_parts` from the full Route A stop list.

### Route B: 时间适配路线 / Time-Fit Selected Route

- `route_id`: `B`
- `route_type`: `time_fit`
- `strategy`: `balanced_time_fit` or another suitable time-fit strategy
- `point_policy`: `time_fit_selected_subset`
- Purpose: respect the user's available date/time window and produce a more realistic route.
- This route should keep the original behavior of selecting only a subset of points according to:
  - local start/end time
  - estimated stop duration
  - estimated walking/transit time
  - maximum walking distance per segment
  - weather and meal/rest needs
  - must-visit / avoid preferences
- It is allowed to omit points that do not fit the user's available time.
- Put omitted valid Anitabi points into `routes[1].omitted_points` where possible, or leave them in the global `points` list so the HTML generator can display them separately.
- Include enough metadata for omitted points, especially `point_id`, `name`, `lat`, `lng`, `image_url`, `episode`, `scene_time`, and `source_urls`, so the HTML page can add them back into Route B.
- Generate `overall_map_url` and `overall_map_url_parts` from only the selected Route B stops at initial generation time. The Route B HTML page may later rebuild links after the user adds or reorders points.

## Point and coordinate rules

1. Keep original Anitabi point identity, coordinates, image URL, episode/time metadata, and source attribution.
2. Do not modify point coordinates. If a Google Maps search fails with a name, use coordinate-only links.
3. Individual point map links must use coordinate-only Google Maps search URLs, for example `https://www.google.com/maps/search/?api=1&query=36.1454%2C137.2568`.
4. Do not append the scene name inside the coordinate query, because `lat,lng (name)` can make Google Maps treat it as text search and fail.

## Maps, walking limit, and transit

- Read `trip_profile.map_access.map_mode` or infer it from `GOOGLE_MAPS_API_KEY`.
- If `GOOGLE_MAPS_API_KEY` is available, use Google Routes API and/or Places APIs.
- If the key is missing, create Google Maps directions/search URLs and mark durations as rough estimates.
- In URL-only mode, warn that Google real-time routes, opening hours, ratings, and price levels cannot be automatically retrieved.
- For each route option, create an `overall_map_url` and `overall_map_url_parts` from that route's stop list:
  - Route A links cover all valid Anitabi coordinate points.
  - Route B links cover only the time-fit selected subset.
- If the route has too many stops for one stable Google Maps URL, create chunked `overall_map_url_parts`. Use the last stop of each part as the first stop of the next part.
- Read `trip_profile.mobility.max_walking_distance_km`.
- If a walking segment exceeds the user's limit, switch that segment to public transit unless the user explicitly prefers taxi/drive.
- In URL-only mode, generate a Google Maps directions URL with `travelmode=transit` and mark schedule/duration as manual confirmation required.
- OSRM/OpenStreetMap may be used only for rough walk/drive/cycle distance and time estimates when coordinates exist. It does not provide Google real-time traffic, business opening hours, ratings, prices, or reliable public transit schedules.
- Route B HTML must support post-generation editing: users can add omitted Anitabi points into the route, drag rows to the desired order, rebuild route links, and recalculate arrival/departure times. In URL-only mode, recalculated times are estimates and should be clearly marked as needing map confirmation when appropriate.

## Weather

- Use weather forecast data for the relevant coordinates and date.
- Prefer hourly summary around the itinerary time window.
- Add weather-aware photo notes.
- If the date is outside reliable forecast range, state that forecast is unavailable or only tentative.

## Output

Return a summary and JSON using the `route_weather_plan` contract. Include:

- Route A: all valid Anitabi points
- Route B: time-fit selected subset
- `map_mode`
- `max_walking_distance_km`
- `overall_map_url`
- `overall_map_url_parts`
- URL-only warnings and manual confirmation notes


## Chinese output requirement

For the final user-facing itinerary, HTML pages, weather summaries, route labels, warning text, status fields, and manual-check notes, use Chinese by default. Keep only proper nouns and technical product names such as Bangumi, Anitabi, Google Maps, OSRM, OpenStreetMap, API, URL, HTML, CSV, KML, and JSON in English when needed. Do not output internal enum values such as `google_maps_url_only`, `balanced_time_fit`, `time_fit`, `unknown`, `scheduled`, or `manual-added` directly in the HTML; convert them to Chinese display text.
