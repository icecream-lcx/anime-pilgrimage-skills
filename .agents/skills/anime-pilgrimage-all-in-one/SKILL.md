---
name: anime-pilgrimage-all-in-one
description: Plan a complete anime pilgrimage trip from an anime title or keyword, including Bangumi confirmation, Anitabi locations, route/weather/place checks, and editable HTML itinerary output.
---

# Anime Pilgrimage All-in-One Planner

Use this skill when the user wants Codex to plan an anime pilgrimage / 聖地巡礼 / 圣地巡礼 trip from an anime name, keyword, Bangumi ID, Anitabi point ID, destination area, or travel date.

## Goal

Produce one or two realistic route options and editable HTML itinerary files. The itinerary should include anime work information, pilgrimage points, local schedule, transport route notes, weather, photo references, restaurant/attraction opening-hour notes, price notes when available, and source links.

## Required workflow

Follow these stages in order. Do not skip user confirmation of the anime identity unless the user already gave an explicit Bangumi ID or Anitabi point ID.

1. Anime search and confirmation
   - Search Bangumi first. Use other search engines only to disambiguate names, aliases, years, or series seasons.
   - Present 3 to 8 candidates with Bangumi ID, title, aliases, release date, short summary, and source URL.
   - Ask the user to confirm the correct work.
   - If the user already supplied a Bangumi ID, still summarize the matched work and ask only if there is evidence of mismatch.

2. Trip profile collection
   - Ask for missing travel inputs only after the correct work is confirmed.
   - Required fields: trip date, local start time, local end time, starting place/hotel/base, end place if different, transport preference, pace, maximum acceptable walking distance per segment, Google Maps API availability, must-visit/avoid points if any.
   - If the user already gave a field, do not ask again.
   - Ask whether the user has a Google Maps API key available. Do not ask them to paste the key into chat; only ask whether the `GOOGLE_MAPS_API_KEY` environment variable can be configured.
   - If the user has no Google Maps API key or is unsure, set `map_mode` to `google_maps_url_only`, continue with Google Maps URLs, and explicitly warn: cannot automatically retrieve Google real-time routes, opening hours, ratings, or price levels; only search links can be provided or fields must be marked for manual confirmation.
   - Ask for the maximum acceptable walking distance per segment. If missing, use 1.5 km as a conservative default and record it in assumptions.
   - If a field is missing and the user wants immediate planning, make a conservative default and mark it in assumptions.

3. Anitabi point retrieval
   - Use the confirmed Bangumi ID to query Anitabi landmarks.
   - Preserve every Anitabi point that has valid coordinates. Do not drop points because of time limits, distance, missing business data, or lack of reference images.
   - Keep point IDs, names, coordinates, scene/reference images, episode/time metadata, and origin/originURL attribution where provided.
   - Normalize landmarks into the `pilgrimage_points` contract.

4. Route and weather planning
   - Use Google Routes API if `GOOGLE_MAPS_API_KEY` is available.
   - If no Google key exists, provide Google Maps route/search URLs and clearly mark travel times as rough estimates. Do not claim real-time route, opening hour, rating, or price-level data.
   - For each final route option, generate an `overall_map_url` for the whole ordered itinerary, in addition to per-segment links. If there are too many stops for one stable Google Maps URL, generate `overall_map_url_parts` as sequential chunked links.
   - For Route A, include every valid Anitabi point in the HTML table and in the overall route link coverage. If the day is too short, mark overflow points as flexible/unscheduled.
   - For Route B, include only points selected according to the user's time window and route constraints; show omitted Anitabi points separately in the HTML or JSON.
   - For individual point map links, use coordinate-only Google Maps search URLs. Do not append the point name to the coordinate query, because Google Maps may fail to resolve `lat,lng (name)`.
   - For each route segment, compare estimated walking distance with `max_walking_distance_km`. If the distance exceeds the user's limit, prefer public transit and generate a Google Maps transit URL; if public transit cannot be computed, mark it as `transit` with manual confirmation required.
   - Optionally use OSRM/OpenStreetMap only as a rough open-data distance/time estimator for walk/drive/cycle when coordinates are available; do not use it as a source for Google business details or public transit schedules.
   - Use weather APIs such as Open-Meteo for date/location weather. For dates beyond reliable forecast range, mark weather as unavailable or use climate-style guidance only if the user explicitly accepts it.
   - Generate exactly two route options when enough valid coordinate points exist:
     - Route A: all-points route. It must cover every valid Anitabi coordinate point and generate a Google Maps total route link or chunked links that cover all of them.
     - Route B: time-fit route. It should follow the user's date and available time window, and may select only a realistic subset of points.
   - Route A may mark overflow points as flexible or unscheduled when the day is too short.
   - Route B should keep the original time-based selection behavior and list omitted Anitabi points separately when possible.
   - Keep Route B realistic. Include buffer time between stops.

5. Restaurant/attraction enrichment
   - Detect points that are restaurants, cafés, shops, museums, parks, stations, paid attractions, or other businesses.
   - Query Google Places API if a key exists; otherwise create Google Maps search URLs and mark opening hours, ratings, price levels, tickets, and average prices as unknown unless verified from another reliable source.
   - Add opening hours, open-on-trip-date status, official URL, Google Maps URL, average restaurant price or Google `priceLevel` when available, and ticket prices from official pages when found.
   - Never invent prices. If unavailable, write `unknown` and provide a verification note.
   - Always state that opening hours and prices are references only and should be checked again before departure.

6. HTML itinerary generation
   - Generate 1 to 2 editable HTML files, one per route.
   - Route A HTML must include all valid Anitabi points by default and provide a delete button for each row.
   - Route B HTML should include only the time-fit selected points at first, and should show unselected Anitabi points in a separate reference section.
   - Route B HTML must allow unselected Anitabi points to be added back into the main route by clicking an add button or dragging them into the desired position.
   - Route B HTML must allow main route rows to be drag-reordered.
   - After rows are added, deleted, or reordered, provide buttons that rebuild the Google Maps route links and recalculate arrival/departure times from the current table order.
   - In URL-only mode, time recalculation may use OSRM/OpenStreetMap or distance-based estimates, but public-transit and Google real-time route durations must remain manual-confirmation items.
   - HTML must be self-contained when possible and include:
     - title, trip date, work title, route summary
     - editable timeline table with `contenteditable="true"`
     - map links for every segment/stop
     - weather block
     - photo reference block with image URLs/source attribution
     - restaurant/attraction hours and prices
     - assumptions and manual verification checklist
     - buttons for printing/exporting the page when practical
   - Save files to an `output/` folder or the workspace root if no output folder exists.

## Output format

At every major stage, include a short human summary and a JSON block following `shared/references/output-contracts.md`.

Final response must include:

- selected anime work and Bangumi ID
- trip date and planning assumptions
- Route A summary and optional Route B summary
- weather summary
- manual verification list
- file paths to generated HTML itinerary files

## Source and accuracy rules

- Use official APIs or official pages where possible.
- Cite or list source URLs in the JSON and HTML.
- Do not claim business hours, transit duration, prices, or weather as guaranteed.
- Do not silently filter or reduce Anitabi points. Keep all valid coordinate points visible in the final output unless the user explicitly asks to filter them.
- If a Google Maps API key is missing, explain the URL-only fallback and continue with the best available plan. State clearly that Google real-time routes, opening hours, ratings, and price levels cannot be automatically retrieved in this mode.
- Do not expose API keys or tokens in logs, output, HTML, or committed files.
- Do not scrape sites that forbid scraping. Prefer official APIs, structured data, or user-provided information.

## Useful helper scripts

The package includes optional helper scripts in `shared/scripts/`:

- `bangumi_search.py`
- `anitabi_points.py`
- `open_meteo_forecast.py`
- `google_maps_tools.py`
- `osrm_tools.py`
- `build_html_itinerary.py`

Use them when helpful, or create task-specific scripts if the repository already has a better structure.


## Chinese output requirement

For the final user-facing itinerary, HTML pages, weather summaries, route labels, warning text, status fields, and manual-check notes, use Chinese by default. Keep only proper nouns and technical product names such as Bangumi, Anitabi, Google Maps, OSRM, OpenStreetMap, API, URL, HTML, CSV, KML, and JSON in English when needed. Do not output internal enum values such as `google_maps_url_only`, `balanced_time_fit`, `time_fit`, `unknown`, `scheduled`, or `manual-added` directly in the HTML; convert them to Chinese display text.
