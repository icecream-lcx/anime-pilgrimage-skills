---
name: pilgrimage-05-place-hours-prices
description: Enrich pilgrimage stops that are restaurants, cafés, shops, or attractions with Google Maps links, opening hours, and price/ticket notes when available.
---

# Stage 5: Place Hours and Price Enrichment

## Shared Constraint Requirement

Before executing this skill, read and follow the shared constraints defined in:

```text
.agents/skills/pilgrimage-constraints/references/pilgrimage-constraints.md
```

These constraints are mandatory. They define route structure, multi-day behavior, language output behavior, endpoint fallback, file generation policy, Google Maps fallback behavior, and HTML output requirements.

Do not override these constraints unless the user explicitly asks to change the skill rules.


Use this skill after route options are generated.

## Inputs

- Route and stop list
- Trip date
- Place-like pilgrimage points: restaurants, cafés, shops, attractions, museums, parks, temples/shrines, paid facilities

## Process

1. Identify route stops that likely need business/attraction checks.
2. If `GOOGLE_MAPS_API_KEY` is available:
   - search the place through Google Places API;
   - retrieve opening hours, Google Maps URI, website, price level when available;
   - infer open-on-trip-date only when the data supports it.
3. If no API key is available:
   - create Google Maps search links;
   - do not claim Google opening hours, ratings, price levels, business status, or average prices;
   - mark hours/prices/ratings/price levels as unknown or manually checked only if reliable non-Google sources are available;
   - add the warning: `未配置 Google Maps API，无法自动获取 Google 的实时路线、营业时间、评分和价格等级；这里只提供搜索链接或人工确认项。`
4. For attraction tickets:
   - prefer official venue/ticket pages;
   - do not rely on random blog prices unless no official source exists and mark it as unverified.
5. For restaurants:
   - if Google price level exists, convert it to a broad price note only;
   - if exact average price is found from reliable sources, include it with a source URL;
   - never invent per-person cost.

## Required caveat

For every business/attraction, include:

`Opening hours and prices are references only; verify before departure.`

In Chinese output, use:

`营业时间和价格仅供参考，出发前建议再次自行确认。`

## Output

Return a concise list and JSON using the `enriched_places` contract.
