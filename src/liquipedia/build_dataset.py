"""Build a matches dataset from downloaded Liquipedia pages."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .client import LiquipediaClient
from .download_pages import safe_title
from .extract_matches import extract_matches_from_wikitext
from .logging_utils import setup_logging
from .mediawiki import get_wikitext


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build matches dataset from wikitext.")
    parser.add_argument("--input", type=Path, required=True, help="Path to tournaments.jsonl")
    parser.add_argument("--max_pages", type=int, default=None, help="Max pages to process")
    parser.add_argument("--offline", action="store_true", help="Do not download missing pages")
    parser.add_argument("--debug", action="store_true", help="Store extraction traces")
    return parser.parse_args()


def _match_id(record: dict[str, Any]) -> str:
    key = "|".join(
        [
            record.get("tournament_page") or "",
            record.get("team1") or "",
            record.get("team2") or "",
            record.get("start_time_utc") or "",
            str(record.get("score1") or ""),
            str(record.get("score2") or ""),
        ]
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def main() -> None:
    args = parse_args()
    setup_logging()
    client = LiquipediaClient()

    pages_dir = Path("data/raw/liquipedia/pages")
    pages_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = Path("data/raw/liquipedia/_debug/extraction")
    if args.debug:
        debug_dir.mkdir(parents=True, exist_ok=True)

    all_matches: list[dict[str, Any]] = []
    processed = 0

    with args.input.open("r", encoding="utf-8") as handle:
        for line in handle:
            if args.max_pages is not None and processed >= args.max_pages:
                break
            record = json.loads(line)
            title = record.get("title")
            tier = record.get("tier")
            if not title:
                continue

            filename = pages_dir / f"{safe_title(title)}.wikitext"
            if not filename.exists():
                if args.offline:
                    continue
                wikitext = get_wikitext(client, title)
                filename.write_text(wikitext, encoding="utf-8")
            else:
                wikitext = filename.read_text(encoding="utf-8")

            matches = extract_matches_from_wikitext(wikitext, title, tier)
            for match in matches:
                match["match_id"] = _match_id(match)
            all_matches.extend(matches)

            if args.debug:
                debug_path = debug_dir / f"{safe_title(title)}.json"
                debug_payload = {
                    "title": title,
                    "tier": tier,
                    "matches_extracted": len(matches),
                }
                debug_path.write_text(json.dumps(debug_payload, ensure_ascii=False, indent=2), encoding="utf-8")

            processed += 1
            if processed % 5 == 0:
                logger.info("Processed %s pages", processed)

    if not all_matches:
        logger.warning("No matches extracted.")

    df = pd.DataFrame(all_matches)
    if not df.empty:
        df = df.drop_duplicates(subset=["match_id"])  # type: ignore[arg-type]

    output_path = Path("data/processed/matches.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    report = {
        "tournaments_processed": processed,
        "matches_extracted": len(df),
        "pct_with_teams": float(df.dropna(subset=["team1", "team2"]).shape[0] / len(df)) if len(df) else 0.0,
        "pct_with_scores": float(df.dropna(subset=["score1", "score2"]).shape[0] / len(df)) if len(df) else 0.0,
        "pct_with_start_time": float(df.dropna(subset=["start_time_utc"]).shape[0] / len(df)) if len(df) else 0.0,
    }

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "data_quality.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Saved dataset to %s", output_path)
    logger.info("Saved report to %s", report_path)


if __name__ == "__main__":
    main()
