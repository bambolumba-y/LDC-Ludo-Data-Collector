"""Match extraction from Liquipedia wikitext."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import mwparserfromhell
from dateutil import parser as date_parser

from .config import DEFAULT_MATCH_TEMPLATES

TEAM_KEYS = ["team1", "team2", "opponent1", "opponent2", "team1name", "team2name"]
SCORE_KEYS = ["score1", "score2", "team1score", "team2score", "score", "score2"]


def _get_param(template: mwparserfromhell.wikicode.Template, key: str) -> str | None:
    if template.has(key):
        return str(template.get(key).value).strip()
    return None


def _first_param(template: mwparserfromhell.wikicode.Template, keys: list[str]) -> str | None:
    for key in keys:
        value = _get_param(template, key)
        if value:
            return value
    return None


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_datetime(date_str: str | None, time_str: str | None) -> str | None:
    if not date_str and not time_str:
        return None
    if date_str and time_str:
        combined = f"{date_str} {time_str}"
    else:
        combined = date_str or time_str
    try:
        parsed = date_parser.parse(combined)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):
        return None


def _winner(score1: int | None, score2: int | None) -> str | None:
    if score1 is None or score2 is None:
        return None
    if score1 > score2:
        return "team1"
    if score2 > score1:
        return "team2"
    return None


def extract_matches_from_wikitext(
    wikitext: str,
    tournament_title: str,
    tier: str,
    match_templates: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract matches from wikitext using configured templates."""
    templates = match_templates or DEFAULT_MATCH_TEMPLATES
    parsed = mwparserfromhell.parse(wikitext)
    matches: list[dict[str, Any]] = []

    for template in parsed.filter_templates(recursive=True):
        name = str(template.name).strip()
        if name not in templates:
            continue

        team1 = _first_param(template, ["team1", "opponent1", "team1name", "team1short"])
        team2 = _first_param(template, ["team2", "opponent2", "team2name", "team2short"])
        score1 = _parse_int(_first_param(template, ["score1", "team1score", "score"]))
        score2 = _parse_int(_first_param(template, ["score2", "team2score"]))
        best_of = _parse_int(_first_param(template, ["bestof", "bo", "best_of"]))
        date_str = _first_param(template, ["date", "match_date"])
        time_str = _first_param(template, ["time", "timezone", "match_time"])
        start_time = _parse_datetime(date_str, time_str)
        stage = _first_param(template, ["stage", "round", "group"]) or None
        match_format = _first_param(template, ["format", "match_format"]) or None
        map_list = _first_param(template, ["map", "map1", "maplist", "maps"])

        debug = {
            "template": name,
            "params": {str(param.name).strip(): str(param.value).strip() for param in template.params},
        }

        matches.append(
            {
                "tournament_page": tournament_title,
                "tournament_tier": tier,
                "team1": team1,
                "team2": team2,
                "score1": score1,
                "score2": score2,
                "best_of": best_of,
                "winner": _winner(score1, score2),
                "start_time_utc": start_time,
                "stage": stage,
                "match_format": match_format,
                "map_list": map_list,
                "source_fields": json.dumps(debug, ensure_ascii=False),
            }
        )

    return matches
