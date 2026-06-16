# Output Contracts for Anime Pilgrimage Skills

All staged skills must return both a concise human-readable summary and a machine-readable JSON block. The JSON block is passed to the next skill without rewriting field names.

## Contract 1: anime_candidates

```json
{
  "stage": "anime_candidates",
  "query": "string",
  "candidates": [
    {
      "rank": 1,
      "bangumi_id": 0,
      "title": "string",
      "original_title": "string|null",
      "aliases": ["string"],
      "type": "anime|unknown",
      "date": "YYYY-MM-DD|null",
      "summary": "string|null",
      "score": 0,
      "omitted_points": [
        {
          "point_id": "string",
          "name": "string",
          "lat": 0,
          "lng": 0,
          "reason": "time_limit|distance|weather|user_avoid|other"
        }
      ],
      "source_urls": ["string"]
    }
  ],
  "needs_user_confirmation": true,
  "confirmation_question": "string"
}
```

## Contract 2: confirmed_work_and_trip_profile

```json
{
  "stage": "confirmed_work_and_trip_profile",
  "work": {
    "bangumi_id": 0,
    "title": "string",
    "aliases": ["string"],
    "source_urls": ["string"]
  },
  "trip_profile": {
    "date": "YYYY-MM-DD",
    "timezone": "IANA timezone string|null",
    "local_start_time": "HH:MM",
    "local_end_time": "HH:MM",
    "start_place": "string",
    "end_place": "string|null",
    "hotel_or_base": "string|null",
    "transport_preferences": ["walk", "transit", "taxi", "drive"],
    "mobility": {
      "max_walking_distance_km": 1.5,
      "walking_distance_source": "user|default",
      "switch_to_transit_if_exceeded": true
    },
    "map_access": {
      "has_google_maps_api": true,
      "map_mode": "google_api|google_maps_url_only",
      "api_key_env_var": "GOOGLE_MAPS_API_KEY|null",
      "fallback_notice": "string|null"
    },
    "pace": "relaxed|normal|tight",
    "meal_preferences": "string|null",
    "must_visit": ["string"],
    "avoid": ["string"],
    "budget_note": "string|null"
  },
  "missing_fields": ["string"],
  "ready_for_points": true
}
```

## Contract 3: pilgrimage_points

```json
{
  "stage": "pilgrimage_points",
  "work": { "bangumi_id": 0, "title": "string" },
  "points": [
    {
      "id": "string",
      "name": "string",
      "lat": 0,
      "lng": 0,
      "address": "string|null",
      "episode": "string|null",
      "scene_time": "string|null",
      "image_url": "string|null",
      "origin": "string|null",
      "origin_url": "string|null",
      "tags": ["restaurant", "attraction", "station", "street", "shop", "viewpoint"],
      "source_urls": ["string"]
    }
  ],
  "point_count": 0,
  "filter_notes": ["string"]
}
```

## Contract 4: route_weather_plan

```json
{
  "stage": "route_weather_plan",
  "work": { "bangumi_id": 0, "title": "string" },
  "trip_profile": {},
  "weather": {
    "location_basis": "string",
    "date": "YYYY-MM-DD",
    "summary": "string",
    "hourly": [
      {"time": "YYYY-MM-DDTHH:MM", "temperature_c": 0, "precipitation_probability": 0, "weather_code": 0}
    ],
    "source_urls": ["string"]
  },
  "routes": [
    {
      "route_id": "A|B",
      "route_name": "string",
      "route_type": "all_points|time_fit",
      "strategy": "all_points|balanced_time_fit|shortest|photo_priority|meal_priority|weather_safe|balanced",
      "point_policy": "all_valid_anitabi_points_included|time_fit_selected_subset",
      "estimated_start": "HH:MM",
      "estimated_end": "HH:MM",
      "overall_map_url": "string|null",
      "overall_map_url_parts": [
        {"part": 1, "from": "string", "to": "string", "stop_count": 0, "map_url": "string"}
      ],
      "overall_route_warning": "string|null",
      "segments": [
        {
          "order": 1,
          "from": "string",
          "to": "string",
          "transport_mode": "walk|transit|drive|taxi|unknown",
          "distance_text": "string|null",
          "distance_km": 0,
          "duration_text": "string|null",
          "duration_minutes": 0,
          "walking_limit_exceeded": false,
          "requires_manual_transit_confirmation": false,
          "arrival_time": "HH:MM|null",
          "departure_time": "HH:MM|null",
          "map_url": "string|null",
          "notes": "string|null"
        }
      ],
      "stops": [
        {
          "order": 1,
          "point_id": "string",
          "name": "string",
          "lat": 0,
          "lng": 0,
          "planned_arrival": "HH:MM",
          "planned_departure": "HH:MM",
          "photo_reference": "string|null",
          "photo_notes": "string|null",
          "weather_note": "string|null"
        }
      ],
      "omitted_points": [
        {
          "point_id": "string",
          "name": "string",
          "lat": 0,
          "lng": 0,
          "reason": "time_limit|distance|weather|user_avoid|other"
        }
      ],
      "source_urls": ["string"]
    }
  ],
  "map_mode": "google_api|google_maps_url_only",
  "max_walking_distance_km": 1.5,
  "warnings": ["string"],
  "assumptions": ["string"]
}
```

Notes for `overall_map_url`:

- Route A must represent all valid Anitabi coordinate points, not just a scheduled subset.
- Route B must represent only the time-fit selected subset, according to the user's available time window.
- Individual point map links must use coordinate-only queries such as `query=36.1454%2C137.2568`. Do not include the scene name in the coordinate query.
- If Google Maps URL-only mode is used and the route has too many stops for one stable URL, put the first usable link in `overall_map_url` and put all sequential chunks in `overall_map_url_parts`. The chunks together must cover every valid Anitabi point.
- The HTML generator must display both the main full-route link and chunked links.
- The final HTML should allow users to delete unwanted point rows and rebuild the route links from the remaining rows.
- The HTML generator must not append all omitted points into the Route B main table at initial generation. It should show them in a separate reference section.
- Route B HTML must support adding omitted points back into the main route, including drag-and-drop insertion into the desired route position.
- Route B HTML must support drag-and-drop reordering of the main route rows.
- After Route B is edited, the HTML should rebuild Google Maps route links from the current row order and recalculate arrival/departure times. In Google URL-only mode, recalculated times are estimates based on OSRM/OpenStreetMap when available or distance fallback, and public-transit durations must be confirmed manually in Google Maps.

## Contract 5: enriched_places

```json
{
  "stage": "enriched_places",
  "routes": [],
  "places": [
    {
      "point_id": "string",
      "name": "string",
      "category": "restaurant|attraction|shop|other",
      "google_place_id": "string|null",
      "opening_hours": "string|null",
      "open_on_trip_date": "yes|no|unknown",
      "ticket_price": "string|null",
      "average_price": "string|null",
      "official_url": "string|null",
      "google_maps_url": "string|null",
      "rating": "number|null",
      "price_level": "string|null",
      "api_data_available": true,
      "verification_note": "Opening hours, ratings, price levels, and prices are references only; verify before departure.",
      "source_urls": ["string"]
    }
  ],
  "map_mode": "google_api|google_maps_url_only",
  "warnings": ["string"]
}
```

## Contract 6: html_itinerary

```json
{
  "stage": "html_itinerary",
  "html_files": [
    {
      "route_id": "A",
      "title": "string",
      "path": "string",
      "editable": true,
      "contains_source_links": true,
      "supports_drag_drop_reorder": true,
      "supports_route_b_add_omitted_points": true,
      "supports_time_recalculation": true
    }
  ],
  "summary": "string",
  "remaining_manual_checks": ["string"]
}
```


## Chinese output requirement

For the final user-facing itinerary, HTML pages, weather summaries, route labels, warning text, status fields, and manual-check notes, use Chinese by default. Keep only proper nouns and technical product names such as Bangumi, Anitabi, Google Maps, OSRM, OpenStreetMap, API, URL, HTML, CSV, KML, and JSON in English when needed. Do not output internal enum values such as `google_maps_url_only`, `balanced_time_fit`, `time_fit`, `unknown`, `scheduled`, or `manual-added` directly in the HTML; convert them to Chinese display text.
