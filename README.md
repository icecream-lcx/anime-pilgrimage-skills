# Anime Pilgrimage Skills for Codex

[中文说明](README_CN.md)

A Codex skill package for planning anime pilgrimage trips.

This project can search anime works through Bangumi, fetch pilgrimage landmarks from Anitabi using the confirmed Bangumi ID, and generate editable HTML pilgrimage itineraries based on the user's travel date, available time, starting location, endpoint preference, walking-distance preference, weather information, map links, and requested output language.

It supports two workflows:

* **All-in-one skill**: complete the whole anime pilgrimage planning process with one skill.
* **Staged skill chain**: run the workflow step by step, including anime search, trip profile collection, landmark fetching, route planning, place-information enrichment, and HTML itinerary generation.

## Online Demo

You can view the generated itinerary examples through GitHub Pages:

* [Demo homepage](https://icecream-lcx.github.io/anime-pilgrimage-skills/)
* [Route A: Full landmark route](https://icecream-lcx.github.io/anime-pilgrimage-skills/pilgrimage_route_A.html)
* [Route B: Day 1 time-fit route](https://icecream-lcx.github.io/anime-pilgrimage-skills/pilgrimage_route_B_day_1.html)
* [Route B: Day 2 time-fit route](https://icecream-lcx.github.io/anime-pilgrimage-skills/pilgrimage_route_B_day_2.html)

Route A covers all valid Anitabi coordinate points and is useful for viewing the full distribution of pilgrimage landmarks. Route B provides daily time-fit routes based on the user's available travel time.

The demo pages are generated HTML examples. They support deleting stops, reordering points, rebuilding route links, and recalculating estimated times. Weather, route duration, opening hours, prices, and traffic information are for reference only and should be verified again before departure.

## Features

* Search anime works by title or keyword through Bangumi.

* Fetch anime pilgrimage landmarks from Anitabi using the confirmed Bangumi ID.

* Generate editable HTML pilgrimage itinerary pages.

* Support user-specified output languages, such as Chinese, English, Japanese, Korean, or bilingual output.

* Support Google Maps URL-only fallback when no Google Maps API key is available.

* Ask for the user's maximum acceptable walking distance per segment.

* Generate Google Maps point links and route links.

* Use coordinate-only Google Maps point links to reduce search failure.

* Support endpoint fallback: if the user does not specify an ending location, the route returns to the starting location by default.

* Preserve two route concepts:

  * **Route A: Full landmark route** — covers all valid Anitabi coordinate points.
  * **Route B: Time-fit route** — selects a practical subset of points based on the user's available time.

* Support multi-day itinerary planning:

  * Route A is always preserved as the full landmark route.
  * Route B can be split into daily time-fit plans, such as Route B Day 1 and Route B Day 2.

* Route B supports interactive editing:

  * Add omitted Anitabi points back into the route.
  * Drag points to reorder the route.
  * Delete unwanted points.
  * Rebuild Google Maps route links.
  * Recalculate arrival and departure times.

* Keep stable source scripts under `shared/`.

* Direct temporary helper scripts to `_codex_generated/` or `_scratch/` instead of `shared/`.

## Project Structure

```text
anime-pilgrimage-skills/
├── README.md
├── README_CN.md
├── LICENSE
├── .gitignore
├── .gitattributes
├── .agents/
│   └── skills/
│       ├── anime-pilgrimage-all-in-one/
│       ├── pilgrimage-00-orchestrator/
│       ├── pilgrimage-01-anime-search-confirm/
│       ├── pilgrimage-02-trip-profile/
│       ├── pilgrimage-03-anitabi-points/
│       ├── pilgrimage-04-route-weather/
│       ├── pilgrimage-05-place-hours-prices/
│       ├── pilgrimage-06-html-plan/
│       ├── pilgrimage-constraints/
│       └── shared/
├── examples/
└── docs/
```

Main folders:

* `anime-pilgrimage-all-in-one/`: all-in-one anime pilgrimage planning skill.
* `pilgrimage-00-orchestrator/`: staged workflow controller.
* `pilgrimage-01-anime-search-confirm/`: anime search and confirmation.
* `pilgrimage-02-trip-profile/`: trip profile collection.
* `pilgrimage-03-anitabi-points/`: Anitabi landmark fetching.
* `pilgrimage-04-route-weather/`: route and weather planning.
* `pilgrimage-05-place-hours-prices/`: place opening-hour and price enrichment.
* `pilgrimage-06-html-plan/`: editable HTML itinerary generation.
* `pilgrimage-constraints/`: shared mandatory constraints for route policy, multi-day behavior, language output, endpoint fallback, and file generation.
* `shared/`: shared helper scripts and output contracts.
* `examples/`: curated example outputs.
* `docs/`: GitHub Pages demo pages.

## Installation

Copy the skill folders into a Codex-supported skill directory.

Repository-level installation:

```text
your-project/
└── .agents/
    └── skills/
```

Global-level installation:

```text
$HOME/.agents/skills/
```

Keep the following folders together under `.agents/skills/`:

```text
anime-pilgrimage-all-in-one/
pilgrimage-00-orchestrator/
pilgrimage-01-anime-search-confirm/
pilgrimage-02-trip-profile/
pilgrimage-03-anitabi-points/
pilgrimage-04-route-weather/
pilgrimage-05-place-hours-prices/
pilgrimage-06-html-plan/
pilgrimage-constraints/
shared/
```

The skills depend on the shared constraints, helper scripts, and output contracts.

## Usage

### All-in-one Skill

```text
$anime-pilgrimage-all-in-one 帮我规划《孤独摇滚！》下北泽圣地巡礼，日期是 2026-07-10，上午 9 点到晚上 7 点，从下北泽站出发，回到代代木公园。
```

If the user does not provide an ending location, the route will return to the starting location by default.

Example:

```text
$anime-pilgrimage-all-in-one 帮我规划《冰菓》两天圣地巡礼，日期是 2026-06-19 和 2026-06-20，从高山站出发，早上 9 点到晚上 18 点。
```

In this case, the endpoint is not specified, so the route should return to the starting point by default.

### Language-specific Output

The itinerary language can follow the user's request.

Examples:

```text
$anime-pilgrimage-all-in-one Generate a two-day Hyouka pilgrimage route in English.
```

```text
$anime-pilgrimage-all-in-one 用日文生成《冰菓》的两天圣地巡礼路线。
```

```text
$anime-pilgrimage-all-in-one 帮我生成《孤独摇滚！》中英双语圣地巡礼路线。
```

If the user does not specify a language, the skills infer the output language from the user's latest request.

## Step-by-step Skill Chain

Start with:

```text
$pilgrimage-00-orchestrator
```

Then Codex will follow these stages:

1. `$pilgrimage-01-anime-search-confirm`
2. `$pilgrimage-02-trip-profile`
3. `$pilgrimage-03-anitabi-points`
4. `$pilgrimage-04-route-weather`
5. `$pilgrimage-05-place-hours-prices`
6. `$pilgrimage-06-html-plan`

Each stage should output the JSON contract defined in:

```text
.agents/skills/shared/references/output-contracts.md
```

The shared constraints are defined in:

```text
.agents/skills/pilgrimage-constraints/references/pilgrimage-constraints.md
```

These constraints must be followed by all pilgrimage skills.

## Optional Environment Variables

* `BANGUMI_ACCESS_TOKEN`: optional Bangumi access token.
* `BANGUMI_USER_AGENT`: recommended. Example: `AnimePilgrimageSkill/0.1 (contact@example.com)`.
* `GOOGLE_MAPS_API_KEY`: optional. If configured, the skills can use Google Routes API and Places API.
* `OSRM_BASE_URL`: optional. Default can be `https://router.project-osrm.org`. It is used for rough open-data distance estimates when coordinates are available.

When `GOOGLE_MAPS_API_KEY` is not configured, the skills use Google Maps URL-only mode. In this mode, the package can generate Google Maps route links and place links, but it cannot automatically retrieve Google real-time route durations, opening hours, ratings, or price levels.

## Route Concepts

### Route A: Full Landmark Route

Route A includes every valid Anitabi landmark with coordinates.

Rules:

* Route A must always exist.
* Route A covers all valid Anitabi coordinate points.
* Route A is not filtered by the user's available time.
* Route A is preserved even for multi-day trips.
* If there are too many points for one stable Google Maps URL, the route is split into multiple sequential Google Maps route links.

Route A is useful for viewing the full distribution of pilgrimage points. Users can delete unwanted points in the HTML page and rebuild the route link from the remaining rows.

Recommended output filename:

```text
pilgrimage_route_A.html
```

### Route B: Time-fit Route

Route B selects a realistic subset of points based on the user's available local time, starting location, ending location, maximum acceptable walking distance, estimated stop duration, and weather information.

The Route B HTML page supports:

* Adding omitted Anitabi points back into the route.
* Dragging points to adjust the route order.
* Deleting unwanted points.
* Rebuilding Google Maps route links.
* Recalculating arrival and departure times.

For multi-day trips, Route B may be split into daily pages.

Recommended output filenames:

```text
pilgrimage_route_B_day_1.html
pilgrimage_route_B_day_2.html
pilgrimage_route_B_day_3.html
```

For backward compatibility, a single-day plan may also use:

```text
pilgrimage_route_B.html
```

## Multi-day Itinerary Policy

For multi-day trips, the skills should not replace Route A with daily Route B pages.

For a two-day trip, the expected outputs are:

```text
pilgrimage_route_A.html
pilgrimage_route_B_day_1.html
pilgrimage_route_B_day_2.html
```

Route A should cover all valid Anitabi points across the entire trip.

Route B can be split by day and may include only a practical subset of points for each day.

Omitted points in Route B should be preserved and shown in the generated HTML so that users can add them back manually.

## Endpoint Fallback Policy

If the user does not specify an ending location, the ending location defaults to the starting location.

Rules:

* If the user provides an ending location, use the provided endpoint.
* If the user does not provide an ending location, copy the starting location into the ending location.
* Route A and Route B should both follow this rule.
* For multi-day trips, if the user does not provide daily endpoints, each day should return to that day's starting point or hotel by default.

Recommended JSON fields:

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

## Language Output Policy

The itinerary output language follows the user's request.

Rules:

* If the user explicitly requests a language, use that language.
* If the user requests bilingual output, generate bilingual labels and notes.
* If the user does not specify a language, infer it from the user's latest request.
* Proper nouns and technical terms may remain in their original form when needed.

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
zh-CN        Simplified Chinese
zh-TW        Traditional Chinese
en           English
ja           Japanese
ko           Korean
fr           French
es           Spanish
bilingual    Bilingual output, such as zh-CN + en
```

The selected language should affect:

* HTML page title.
* Route names.
* Route warnings.
* Weather summaries.
* Manual-check notes.
* Button labels.
* Table headers.
* Place notes.
* Transportation notes.
* Price and opening-hour notes.
* Route A / Route B descriptions.
* Omitted-point sections.
* Add, delete, drag, rebuild, and recalculate instructions.

Do not display internal enum values directly in the HTML. Convert them into readable text according to the selected output language.

## Google Maps URL-only Mode

When `GOOGLE_MAPS_API_KEY` is not configured, the package uses Google Maps URL-only mode.

In this mode, it can:

* Generate point links using coordinates.
* Generate route links using origin, destination, and waypoints.
* Split long routes into multiple route links.
* Provide manual-confirmation notes.

In this mode, it cannot automatically retrieve:

* Google real-time route durations.
* Public-transit schedules.
* Opening hours.
* Ratings.
* Price levels.
* Ticket prices.
* Restaurant average prices.

These time-sensitive details should be verified manually before departure.

## Time Recalculation

In Google Maps URL-only mode, the local HTML cannot directly retrieve real-time Google Maps route durations.

When users reorder, add, or delete points in Route B, the generated HTML may:

1. Rebuild the Google Maps route link.
2. Try OSRM / OpenStreetMap distance estimates when coordinates are available.
3. Fall back to distance-based estimates if no routing data is available.
4. Mark public-transit durations as requiring manual confirmation.

The recalculated times are planning references only.

## File Generation Policy

The `shared/` directory is a stable source directory.

During normal itinerary generation, Codex should not create temporary scripts, generated helpers, experiments, debug files, or one-off code inside:

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

* Use existing scripts in `shared/scripts/`.
* If temporary helper code is needed, write it under `_codex_generated/`.
* If temporary notes or experiments are needed, write them under `_scratch/`.
* Runtime itinerary outputs should go to `output/`.
* Curated public examples should go to `examples/` only when explicitly needed.
* Do not modify `shared/` unless the user explicitly asks to update the skill source code itself.

## GitHub-safe Output Policy

Generated temporary folders should not be uploaded to GitHub.

Recommended `.gitignore` entries:

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

The `examples/` folder may be committed when it contains curated public examples.

Do not commit private hotel addresses, API keys, tokens, `.env` files, temporary debug scripts, or raw personal travel information.

## Example

The `examples/` folder provides a sample pilgrimage planning result for *Hyouka*, including:

* Route A full landmark route.
* Route B time-fit route.
* Editable HTML itinerary pages.
* Anitabi landmark JSON.
* Route planning JSON.

The weather, opening hours, traffic duration, and price information in the example are for format demonstration only. Please verify all time-sensitive information before departure.

## Notes

* Use official APIs and respect the terms of each data source.
* Anitabi landmark screenshots may include `origin` and `originURL`; preserve them when presenting photo references.
* Opening hours, public-transit routes, prices, ratings, and weather are time-sensitive.
* Always verify weather, traffic, opening hours, ticket prices, and restaurant information before departure.
* Without a Google Maps API key, the package cannot automatically retrieve precise Google route durations, opening hours, ratings, or price levels.
* The generated itinerary is for planning reference only and does not guarantee travel feasibility or safety.

## License

MIT License is recommended for a simple open-source release.
