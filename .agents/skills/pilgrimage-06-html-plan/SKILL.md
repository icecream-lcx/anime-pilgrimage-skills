---
name: pilgrimage-06-html-plan
description: Generate one or two editable HTML anime pilgrimage itinerary tables from planned routes, weather, place details, and photo references.
---

# Stage 6: Editable HTML Itinerary Builder

## Shared Constraint Requirement

Before executing this skill, read and follow the shared constraints defined in:

```text
.agents/skills/pilgrimage-constraints/references/pilgrimage-constraints.md
```

These constraints are mandatory. They define route structure, multi-day behavior, language output behavior, endpoint fallback, file generation policy, Google Maps fallback behavior, and HTML output requirements.

Do not override these constraints unless the user explicitly asks to change the skill rules.


Use this skill after route, weather, and place enrichment are available.

## Goal

Generate 1 to 2 editable HTML files that the user can open locally, modify directly, print, or save as PDF.

## Required HTML contents

Each HTML itinerary must include:

- anime title and Bangumi ID
- trip date and local time window
- route name and strategy
- weather summary and hourly notes
- editable timeline table
- stop list with coordinates, scene notes, photo reference links, and source attribution
- whole-route Google Maps link for each itinerary route
- chunked whole-route links when a single Google Maps URL cannot safely include all stops
- transport segment table with Google Maps links
- restaurant/attraction opening hours and price notes
- assumptions
- manual verification checklist
- source links

## Editable behavior

Use simple HTML/CSS/JS. Do not require a build system.

- Add `contenteditable="true"` to schedule cells and note cells.
- Add buttons for:
  - print / save as PDF
  - export current table text or JSON when practical
- Keep the page usable even without internet.
- External map links may require internet.

## File output

- Create an `output/` folder if needed.
- Save one file per route, for example:
  - `output/pilgrimage_route_A.html`
  - `output/pilgrimage_route_B.html`

## Output

Return the file paths and JSON using the `html_itinerary` contract.

## v6 route display and editing policy

- Route A (`route_type=all_points` or `route_id=A`) must display all valid Anitabi coordinate points and generate total/chunked Google Maps links covering all of them.
- Route B (`route_type=time_fit` or `point_policy=time_fit_selected_subset`) must display only the time-fit selected stops. Do not automatically append all omitted points into the Route B main table.
- For Route B, show omitted Anitabi points in a separate section so the user can still review them.
- Route B HTML must allow the user to add omitted Anitabi points back into the main route table by clicking an add button or dragging the omitted-point row into the desired position.
- Route B main route rows must support drag-and-drop reordering.
- After the user adds, deletes, or reorders Route B rows, provide buttons to rebuild the Google Maps route links and recalculate arrival/departure times from the current table order.
- Time recalculation should use available route durations when known. In URL-only mode, it may try OSRM/OpenStreetMap for walking estimates and then fall back to distance-based estimates; public transit durations must be marked as requiring Google Maps confirmation.
- Both Route A and Route B pages must support deleting rows and rebuilding route links from the current table.


## Chinese output requirement

For the final user-facing itinerary, HTML pages, weather summaries, route labels, warning text, status fields, and manual-check notes, use Chinese by default. Keep only proper nouns and technical product names such as Bangumi, Anitabi, Google Maps, OSRM, OpenStreetMap, API, URL, HTML, CSV, KML, and JSON in English when needed. Do not output internal enum values such as `google_maps_url_only`, `balanced_time_fit`, `time_fit`, `unknown`, `scheduled`, or `manual-added` directly in the HTML; convert them to Chinese display text.

## Multi-day HTML Output Policy

For multi-day trips, do not overwrite Route A with daily Route B files.

Required outputs:

- `pilgrimage_route_A.html`: full all-point route across the whole trip.
- `pilgrimage_route_B_day_1.html`, `pilgrimage_route_B_day_2.html`, ...: daily time-fit routes.

Route A must always exist if any valid Anitabi coordinate points exist.

## Output Language Rendering

Read `output_language` from the input JSON. All visible HTML text, table headers, buttons, route labels, weather summaries, warnings, and manual-check notes must follow the selected language. Keep proper nouns such as Bangumi, Anitabi, Google Maps, OSRM, OpenStreetMap, API, URL, HTML, JSON unchanged when needed.
