"""Download tournament list from Liquipedia categories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .client import LiquipediaClient
from .logging_utils import setup_logging
from .mediawiki import iter_category_members

TIER_CATEGORIES = {
    "S": "S-Tier_Tournaments",
    "A": "A-Tier_Tournaments",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download tournaments from Liquipedia.")
    parser.add_argument("--tiers", nargs="+", default=["S", "A"], help="Tournament tiers to fetch.")
    parser.add_argument("--limit", type=int, default=50, help="Max entries per API call.")
    parser.add_argument("--debug", action="store_true", help="Store example API responses.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/liquipedia/tournaments.jsonl"),
        help="Output JSONL path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()
    client = LiquipediaClient()
    debug_dir = "data/raw/liquipedia/_debug" if args.debug else None

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for tier in args.tiers:
            category = TIER_CATEGORIES.get(tier)
            if not category:
                raise ValueError(f"Unsupported tier: {tier}")
            for member in iter_category_members(client, category, cmlimit=args.limit, debug_dir=debug_dir):
                record = {
                    "title": member.get("title"),
                    "pageid": member.get("pageid"),
                    "tier": tier,
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
