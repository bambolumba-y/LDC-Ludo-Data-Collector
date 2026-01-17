"""Helpers for MediaWiki API actions."""

from __future__ import annotations

from typing import Iterator

from .client import LiquipediaClient


def iter_category_members(
    client: LiquipediaClient,
    cmtitle: str,
    cmlimit: int = 50,
    debug_dir: str | None = None,
) -> Iterator[dict]:
    """Iterate over category members for a category title."""
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": f"Category:{cmtitle}",
        "cmlimit": cmlimit,
    }
    page_index = 1
    while True:
        payload = client.get_json(params)
        if debug_dir:
            from pathlib import Path
            import json

            Path(debug_dir).mkdir(parents=True, exist_ok=True)
            debug_path = Path(debug_dir) / f"category_{cmtitle}_{page_index}.json"
            with debug_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            page_index += 1
        members = payload.get("query", {}).get("categorymembers", [])
        for member in members:
            yield member
        cont = payload.get("continue", {})
        if "cmcontinue" not in cont:
            break
        params["cmcontinue"] = cont["cmcontinue"]


def get_wikitext(client: LiquipediaClient, title: str) -> str:
    """Fetch wikitext for a page title."""
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "titles": title,
    }
    payload = client.get_json(params)
    pages = payload.get("query", {}).get("pages", {})
    if not pages:
        raise ValueError(f"No pages found for title: {title}")
    page = next(iter(pages.values()))
    revisions = page.get("revisions", [])
    if not revisions:
        return ""
    slot = revisions[0].get("slots", {}).get("main", {})
    return slot.get("*") or slot.get("content", "")
