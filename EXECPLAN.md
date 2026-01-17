# Liquipedia CS2 Data Pipeline (Data collection + dataset building)

This ExecPlan is a living document. While working, keep these sections updated:
- Progress
- Surprises & Discoveries
- Decision Log
- Outcomes & Retrospective

## Purpose / Big Picture

We want a Python program that collects historical CS2 match data from Liquipedia (Counter-Strike wiki) and builds a clean dataset for later machine learning.

This plan is “data-only”:
- The agent must implement data collection and dataset building.
- The agent may add optional training scripts, but training must NOT be required for acceptance and must NOT be run.

Target outputs:
- Raw downloads in `data/raw/liquipedia/`
- Processed dataset in `data/processed/matches.parquet` (required)
- Optional per-map dataset in `data/processed/maps.parquet` (only if discoverable)
- Tests that pass (`pytest -q`)
- README instructions to run end-to-end

## Progress

- [ ] (YYYY-MM-DD HH:MMZ) Milestone 1: Create project skeleton (folders, dependencies, CLI entrypoints, logging).
- [ ] (YYYY-MM-DD HH:MMZ) Milestone 2: Implement Liquipedia MediaWiki API client (headers, rate limit, retries, disk cache).
- [ ] (YYYY-MM-DD HH:MMZ) Milestone 3: Tournament discovery via categories (S-tier/A-tier) with pagination.
- [ ] (YYYY-MM-DD HH:MMZ) Milestone 4: Download tournament pages (wikitext) with resume and caching.
- [ ] (YYYY-MM-DD HH:MMZ) Milestone 5: Extract matches from tournament wikitext (prototype → generalize).
- [ ] (YYYY-MM-DD HH:MMZ) Milestone 6: Build `matches.parquet` + dedup + basic validation report.
- [ ] (YYYY-MM-DD HH:MMZ) Milestone 7: Add unit tests (pagination, extraction, normalization) and run them.
- [ ] (YYYY-MM-DD HH:MMZ) Milestone 8: Update README and do an end-to-end smoke run.

## Surprises & Discoveries

(Write down unexpected response shapes, template name changes, missing fields, or any API limitations encountered. Include small evidence like a short log snippet.)

## Decision Log

(Keep a running log of decisions.)
- Decision: Use Liquipedia MediaWiki Action API (api.php) instead of any private/paid API.
  Rationale: No keys required; works from a public endpoint; we can rate limit and cache.
  Date/Author: YYYY-MM-DD / Codex

## Outcomes & Retrospective

(To be filled at the end: what works, what doesn’t, what should be improved next.)

---

## Context and constraints (must follow)

Liquipedia Counter-Strike wiki uses MediaWiki Action API:
- Base endpoint: https://liquipedia.net/counterstrike/api.php

Request rules (must comply):
- Always send a descriptive User-Agent header with contact info.
- Always send `Accept-Encoding: gzip`.
- Rate limit: about 1 request per 2 seconds on average.
- `action=parse` is heavy and should be avoided for bulk work (only for debugging).
- Cache responses and support resume.

Because the agent runs in a repo-only environment, do not depend on interactive browser steps.
Everything must be runnable from CLI.

---

## Data model (what we want to extract)

We build one main table: one row per match.

Minimum columns in `data/processed/matches.parquet`:
- match_id (stable string; if no native id exists, create a stable hash from key fields)
- tournament_page (Liquipedia page title)
- tournament_tier (S or A for this pipeline)
- start_time_utc (ISO string or pandas datetime; may be null if not present)
- team1 (string)
- team2 (string)
- score1 (int or null)
- score2 (int or null)
- best_of (int 1/3/5 or null)
- winner (string: "team1" or "team2" or null)

Optional columns if discoverable:
- stage
- match_format
- map_list (list or comma-separated)
- source_fields (small JSON blob for debugging)

---

## Implementation plan

### Milestone 1: Skeleton
Create:
- `src/` package with `__init__.py`
- `src/liquipedia/` package with `__init__.py`
- `data/raw/liquipedia/`, `data/processed/`, `reports/`
- dependency management: `requirements.txt`
- minimal logging utility
- CLI entrypoints:
  - `python -m src.liquipedia.download_tournaments`
  - `python -m src.liquipedia.download_pages`
  - `python -m src.liquipedia.build_dataset`
  - `python -m src.liquipedia.debug_templates` (debug helper)

### Milestone 2: MediaWiki API client
Implement `src/liquipedia/client.py` with:
- Base URL: https://liquipedia.net/counterstrike/api.php
- Headers:
  - User-Agent must come from env `LIQUIPEDIA_USER_AGENT`. If missing, error with clear message.
  - Accept-Encoding: gzip
- Rate limit:
  - enforce minimum delay between requests, from env `LIQUIPEDIA_RATE_LIMIT_SECONDS` (default 2.0)
- Retries:
  - retry 429 and 5xx up to 3 times with exponential backoff
- Disk cache:
  - cache key: hash(url + sorted params)
  - store JSON to `data/raw/liquipedia/cache/<hash>.json`
  - if present, load from cache instead of calling network
- Provide:
  - `get_json(params: dict) -> dict`

### Milestone 3: Tournament discovery (categories)
Implement `src/liquipedia/mediawiki.py` function:
- `iter_category_members(cmtitle: str, cmlimit: int) -> iterator[dict]`
Use API:
- action=query
- list=categorymembers
- cmtitle=Category:<name>
- cmlimit=<limit>
Pagination:
- handle `continue.cmcontinue`

Create `download_tournaments` CLI:
- inputs: `--tiers S A` and `--limit`
- map tiers to categories (start with):
  - Category:S-Tier_Tournaments
  - Category:A-Tier_Tournaments
- output: `data/raw/liquipedia/tournaments.jsonl` with one JSON per line:
  { "title": "<page title>", "pageid": <int>, "tier": "S" }

### Milestone 4: Download tournament pages (wikitext)
Implement `get_wikitext(title)` using:
- action=query
- prop=revisions
- rvprop=content
- rvslots=main
- titles=<title>

Store to:
- `data/raw/liquipedia/pages/<safe_title>.wikitext`

Create `download_pages` CLI:
- input: tournaments.jsonl
- args: `--max_pages`, `--force`
- resume: if file exists and not force, skip
- log progress every N pages

### Milestone 5: Extract matches from wikitext
Add dependency: `mwparserfromhell`

Create `debug_templates` CLI:
- loads a single page wikitext
- parses it and prints top template names (name + count)
Goal:
- discover which templates contain match data.

Then implement `src/liquipedia/extract_matches.py`:
- `extract_matches_from_wikitext(wikitext: str, tournament_title: str, tier: str) -> list[dict]`
Strategy:
1) Look for templates that likely represent matches (based on discovery).
2) For each match template, try to extract:
   - team names (team1/team2)
   - scores
   - best_of (if exists)
   - date/time (if exists)
3) Be resilient:
   - missing fields -> null
   - store a small debug blob (template name + key params) if extraction is partial

Important: implement extraction in a way that can evolve:
- keep a configurable list of match template names in `src/liquipedia/config.py`

### Milestone 6: Build dataset + validation
Implement `build_dataset` CLI:
- reads tournaments.jsonl
- loads each page’s wikitext (download if missing unless `--offline`)
- extracts matches
- builds a pandas dataframe
- creates stable `match_id`:
  - if no native id, use sha1 of: tournament_title + team1 + team2 + start_time_utc + score1 + score2
- deduplicate on match_id
- save `data/processed/matches.parquet`

Print/save a validation report:
- total tournaments processed
- total matches extracted
- % matches with both teams
- % matches with scores
- % matches with start_time
- top extraction warnings count (if tracked)
Also write report to `reports/data_quality.json`.

### Milestone 7: Tests
Add tests (no internet):
- pagination test for categorymembers:
  - mock client.get_json to return two pages with continue.cmcontinue
- extraction test:
  - create a small fixture wikitext containing 2–3 match templates (based on discovered templates)
  - verify extracted rows count and key fields
- normalization test:
  - winner logic from score1/score2
  - best_of mapping if present

Run:
- `pytest -q`

### Milestone 8: README + smoke run
Update README with:
- required env var:
  - LIQUIPEDIA_USER_AGENT="YourProject/0.1 (contact@example.com)"
- commands:
  - download tournaments
  - download pages
  - build dataset
  - run tests

Do a small smoke run (limit small to be polite to API):
- download 10 tournaments
- download 5 pages
- build dataset
Confirm dataset non-empty.

---

## Validation and Acceptance (must pass)

Acceptance is met if, on a fresh clone:

1) Install dependencies:
   - `pip install -r requirements.txt`

2) Download tournaments (small run):
   - `LIQUIPEDIA_USER_AGENT="CS2Diploma/0.1 (email@example.com)" python -m src.liquipedia.download_tournaments --tiers S A --limit 50`
   Expected:
   - file `data/raw/liquipedia/tournaments.jsonl` exists and has >= 10 lines

3) Download pages:
   - `LIQUIPEDIA_USER_AGENT="CS2Diploma/0.1 (email@example.com)" python -m src.liquipedia.download_pages --input data/raw/liquipedia/tournaments.jsonl --max_pages 10`
   Expected:
   - at least 3 wikitext files exist in `data/raw/liquipedia/pages/`

4) Build dataset:
   - `LIQUIPEDIA_USER_AGENT="CS2Diploma/0.1 (email@example.com)" python -m src.liquipedia.build_dataset --input data/raw/liquipedia/tournaments.jsonl --max_pages 10`
   Expected:
   - `data/processed/matches.parquet` exists and has >= 20 rows

5) Tests:
   - `pytest -q` passes

---

## Idempotence and Recovery

- All download commands must support resume: if a raw file exists, skip unless `--force`.
- Client must cache JSON responses on disk so re-runs do not spam the API.
- Provide `--debug` flags that store example responses and extraction traces under `data/raw/liquipedia/_debug/`.

---

## Optional (not required for acceptance)

- Add a script `src/modeling/train_catboost.py` that reads `matches.parquet` or a features file, but do not run training by default.
- Add an outline of “next step: feature engineering” in README.

