---
name: pilgrimage-01-anime-search-confirm
description: Search Bangumi and related sources for an anime title or keyword, present candidate works, and obtain the correct Bangumi ID before pilgrimage planning.
---

# Stage 1: Anime Search and Confirmation

Use this skill when the user provides an anime name, alias, keyword, season name, or Bangumi ID and wants to start a pilgrimage plan.

## Inputs

Accept any of:

- anime title or keyword
- Bangumi ID
- Anitabi point ID or URL
- destination keyword plus anime keyword

## Process

1. Search Bangumi first.
   - Prefer official Bangumi API.
   - Use `shared/scripts/bangumi_search.py` if helpful.
   - Use access token only if available in `BANGUMI_ACCESS_TOKEN`.
   - Use a clear User-Agent from `BANGUMI_USER_AGENT` when available.
2. If results are ambiguous, search the web for aliases, release years, or season names.
3. Produce 3 to 8 candidate works when possible.
4. Ask the user to confirm the correct work unless they already supplied an exact Bangumi ID and the result is unambiguous.

## Candidate ranking preference

Prefer candidates that:

- are anime type, not book/game/music unless the user asked otherwise;
- match the exact title or common alias;
- have a release year matching user wording;
- are likely to have Anitabi pilgrimage points;
- are not recap, compilation, or unrelated season unless the user specified it.

## Output

Return a concise list for the user and a JSON block using the `anime_candidates` contract from `shared/references/output-contracts.md`.

## Stop condition

Do not move to route planning until the user confirms the correct candidate or provides a Bangumi ID.
