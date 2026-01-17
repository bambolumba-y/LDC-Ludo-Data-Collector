"""Inspect template usage in a wikitext file."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import mwparserfromhell


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug template usage in a wikitext file.")
    parser.add_argument("--input", type=Path, required=True, help="Path to .wikitext file")
    parser.add_argument("--top", type=int, default=20, help="Show top N templates")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = args.input.read_text(encoding="utf-8")
    parsed = mwparserfromhell.parse(text)
    counts = Counter()
    for template in parsed.filter_templates(recursive=True):
        name = str(template.name).strip()
        counts[name] += 1
    for name, count in counts.most_common(args.top):
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
