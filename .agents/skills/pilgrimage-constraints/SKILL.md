---
name: pilgrimage-constraints
description: Shared constraints and mandatory rules for anime pilgrimage planning skills, including route policy, multi-day itinerary rules, language output policy, endpoint fallback, file generation policy, Google Maps fallback behavior, and GitHub-safe output handling.
---

# Pilgrimage Constraints

Use this skill as the shared rule source for all anime pilgrimage planning skills.

This skill does not perform anime search, route planning, map generation, or HTML generation by itself. It defines mandatory constraints that must be followed by the all-in-one skill, orchestrator skill, trip-profile skill, route-planning skill, HTML-generation skill, and any other related pilgrimage skill.

Before generating itinerary results, route JSON, helper files, or HTML pages, read and follow:

```text
.agents/skills/pilgrimage-constraints/references/pilgrimage-constraints.md
```

## Mandatory Usage

When another pilgrimage skill is used, the assistant must apply these constraints:

1. Preserve Route A as the full Anitabi landmark route.
2. Preserve Route B as the time-fit route.
3. For multi-day trips, Route A must still exist and cover all valid Anitabi points.
4. Route B may be split by day.
5. If the user does not specify an ending location, default to returning to the starting location.
6. Ask or infer the user's preferred output language for the itinerary.
7. Generate route labels, notes, warnings, weather summaries, and HTML interface text in the user's requested language.
8. Do not create temporary scripts inside `shared/`.
9. Temporary helper code must be written to `_codex_generated/` or `_scratch/`.
10. Runtime outputs must be written to `output/`.
11. Curated examples may be written to `examples/` only when the user explicitly asks.
12. Do not display internal enum values directly in user-facing HTML.
