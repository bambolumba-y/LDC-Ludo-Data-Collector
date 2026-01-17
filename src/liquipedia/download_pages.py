"""Download tournament pages as wikitext."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

from .client import LiquipediaClient
from .logging_utils import setup_logging
from .mediawiki import get_wikitext


logger = logging.getLogger(__name__)


def safe_title(title: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_\-]+", "_", title.strip())
    return safe.strip("_") or "untitled"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download tournament wikitext pages.")
    parser.add_argument("--input", type=Path, required=True, help="Path to tournaments.jsonl")
    parser.add_argument("--max_pages", type=int, default=None, help="Max pages to download")
    parser.add_argument("--force", action="store_true", help="Re-download even if file exists")
    parser.add_argument("--log_every", type=int, default=5, help="Log every N pages")
    parser.add_argument("--debug", action="store_true", help="Store debug metadata")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()
    client = LiquipediaClient()

    pages_dir = Path("data/raw/liquipedia/pages")
    pages_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = Path("data/raw/liquipedia/_debug/pages")
    if args.debug:
        debug_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    with args.input.open("r", encoding="utf-8") as handle:
        for line in handle:
            if args.max_pages is not None and count >= args.max_pages:
                break
            record = json.loads(line)
            title = record.get("title")
            if not title:
                continue
            filename = pages_dir / f"{safe_title(title)}.wikitext"
            if filename.exists() and not args.force:
                count += 1
                continue
            wikitext = get_wikitext(client, title)
            filename.write_text(wikitext, encoding="utf-8")
            if args.debug:
                metadata = {
                    "title": title,
                    "path": str(filename),
                    "length": len(wikitext),
                }
                debug_path = debug_dir / f"{safe_title(title)}.json"
                debug_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            count += 1
            if count % args.log_every == 0:
                logger.info("Downloaded %s pages", count)

    logger.info("Finished. Downloaded %s pages", count)


if __name__ == "__main__":
    main()
