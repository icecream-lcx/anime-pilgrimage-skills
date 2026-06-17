# Anime Pilgrimage Skills for Codex

[中文说明](README_CN.md)

A Codex skill package for planning anime pilgrimage trips.

This project can search anime works through Bangumi, fetch pilgrimage landmarks from Anitabi using the confirmed Bangumi ID, and generate editable HTML pilgrimage itineraries based on the user's travel date, available time, starting location, walking-distance preference, weather information, and map links.

It supports two workflows:

* **All-in-one skill**: complete the whole pilgrimage planning process with one skill.
* **Staged skill chain**: run the workflow step by step, including anime search, trip profile collection, landmark fetching, route planning, and HTML itinerary generation.

## Online Demo

You can view the generated itinerary examples through GitHub Pages:

* [Route A: Full landmark route](https://icecream-lcx.github.io/anime-pilgrimage-skills/pilgrimage_route_A.html)
* [Route B: Time-fit route](https://icecream-lcx.github.io/anime-pilgrimage-skills/pilgrimage_route_B.html)

Route A covers all valid Anitabi coordinate points, while Route B provides a time-fit route based on the user's available travel time.

The demo pages are generated HTML examples. Weather, route duration, opening hours, prices, and traffic information are for reference only and should be verified again before departure.


## Features

* Search anime works by title or keyword through Bangumi.
* Fetch anime pilgrimage landmarks from Anitabi using the confirmed Bangumi ID.
* Support Google Maps URL-only fallback when no Google Maps API key is available.
* Ask for the user's maximum acceptable walking distance per segment.
* Generate Google Maps point links and route links.
* Generate two route concepts:

  * **Route A: Full landmark route** — covers all valid Anitabi coordinate points.
  * **Route B: Time-fit route** — selects a realistic subset of points based on the user's available time.
* Route B supports interactive editing:

  * Add omitted Anitabi points back into the route.
  * Drag points to reorder the route.
  * Delete unwanted points.
  * Rebuild Google Maps route links.
  * Recalculate arrival and departure times.
* Generate editable, printable HTML itinerary pages that can be saved as PDF.

## Project Structure

```text
anime-pilgrimage-skills/
├── README.md
├── README_CN.md
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
│       └── shared/
└── examples/
```

Main folders:

* `anime-pilgrimage-all-in-one/`: all-in-one pilgrimage planning skill.
* `pilgrimage-00-orchestrator/`: staged workflow controller.
* `pilgrimage-01-anime-search-confirm/`: anime search and confirmation.
* `pilgrimage-02-trip-profile/`: trip profile collection.
* `pilgrimage-03-anitabi-points/`: Anitabi landmark fetching.
* `pilgrimage-04-route-weather/`: route and weather planning.
* `pilgrimage-05-place-hours-prices/`: place opening-hour and price enrichment.
* `pilgrimage-06-html-plan/`: editable HTML itinerary generation.
* `shared/`: shared helper scripts and output contracts.

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

Keep the `shared/` folder next to the other skill folders, because the skills depend on the helper scripts and output contracts inside it.

## Usage

### All-in-one Skill

```text
$anime-pilgrimage-all-in-one 帮我规划《孤独摇滚！》下北泽圣地巡礼，日期是 2026-07-10，上午 9 点到晚上 7 点，从下北泽站出发，回到下北泽站。
```

### Step-by-step Skill Chain

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
shared/references/output-contracts.md
```

This allows the next stage to consume the previous stage's result.

## Optional Environment Variables

* `BANGUMI_ACCESS_TOKEN`: optional Bangumi access token.
* `BANGUMI_USER_AGENT`: recommended. Example: `MiriaGoPlanningSkill/0.1 (contact@example.com)`.
* `GOOGLE_MAPS_API_KEY`: optional. If configured, the skills can use Google Routes API and Places API.
* `OSRM_BASE_URL`: optional. Default can be `https://router.project-osrm.org`. It is used for rough open-data distance estimates when coordinates are available.

When `GOOGLE_MAPS_API_KEY` is not configured, the skills will use Google Maps URL-only mode. In this mode, the package can generate Google Maps route links and place search links, but it cannot automatically retrieve Google real-time route durations, opening hours, ratings, or price levels.

## Route Concepts

### Route A: Full Landmark Route

Route A includes every valid Anitabi landmark with coordinates.

If there are too many points for one stable Google Maps URL, the route is automatically split into multiple sequential Google Maps route links. These links together cover the full route.

Route A is useful for viewing the full distribution of pilgrimage points. Users can delete unwanted points in the HTML page and rebuild the route link from the remaining rows.

### Route B: Time-fit Route

Route B selects a realistic subset of points based on the user's available local time, starting location, maximum acceptable walking distance, and estimated stop duration.

The Route B HTML page supports:

* Adding omitted Anitabi points back into the route.
* Dragging points to adjust the route order.
* Deleting unwanted points.
* Rebuilding Google Maps route links.
* Recalculating arrival and departure times.

In Google Maps URL-only mode, the local HTML cannot directly retrieve real-time Google Maps route durations. Time recalculation will first try OSRM / OpenStreetMap estimates when available, then fall back to distance-based estimates. Public-transit durations should still be confirmed manually in Google Maps before departure.

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

## Chinese Output Requirement

Final user-facing itineraries, HTML pages, weather summaries, route labels, warning text, status fields, and manual-check notes should use Chinese by default.

Proper nouns and technical terms such as Bangumi, Anitabi, Google Maps, OSRM, OpenStreetMap, API, URL, HTML, CSV, KML, and JSON may remain in English when needed.

Do not output internal enum values such as `google_maps_url_only`, `balanced_time_fit`, `time_fit`, `unknown`, `scheduled`, or `manual-added` directly in the HTML. Convert them into readable Chinese display text.

## License

Choose a license according to your needs. MIT License is recommended for a simple open-source release.
