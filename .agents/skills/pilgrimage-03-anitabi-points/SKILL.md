---
name: pilgrimage-03-anitabi-points
description: Retrieve and normalize Anitabi pilgrimage landmarks by confirmed Bangumi ID, preserving coordinates, scene references, and source attribution.
---

# Stage 3: Anitabi Point Retrieval

## Shared Constraint Requirement

Before executing this skill, read and follow the shared constraints defined in:

```text
.agents/skills/pilgrimage-constraints/references/pilgrimage-constraints.md
```

These constraints are mandatory. They define route structure, multi-day behavior, language output behavior, endpoint fallback, file generation policy, Google Maps fallback behavior, and HTML output requirements.

Do not override these constraints unless the user explicitly asks to change the skill rules.


Use this skill after `confirmed_work_and_trip_profile` is available.

## Inputs

- Confirmed Bangumi ID
- Anime title
- Trip profile
- Optional user filters: area, must-visit scenes, point IDs, restaurants, attractions, walking distance, image-only points

## Process

1. Query Anitabi using the confirmed Bangumi ID.
2. Prefer the details endpoint with coordinates and image data.
3. Normalize all usable points.
4. Filter out invalid points with missing coordinates unless the point is explicitly requested and can be geocoded.
5. Preserve image attribution:
   - image URL
   - origin
   - originURL
6. Add coarse tags such as restaurant, attraction, station, street, shop, viewpoint, shrine, school, bridge, park, unknown.
7. If the dataset is large, select a manageable candidate subset based on geography and the user's time window, but keep the full count and filtering notes.

## Output

Return a concise summary and JSON using the `pilgrimage_points` contract.

## Failure handling

If no points are returned:

- try related season names or related Bangumi IDs only if user approval is not required by ambiguity;
- suggest the user provide an Anitabi URL/point ID;
- do not fabricate pilgrimage points.
