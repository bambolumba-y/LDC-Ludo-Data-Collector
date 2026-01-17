"""MediaWiki API client with caching and rate limiting."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://liquipedia.net/counterstrike/api.php"
CACHE_DIR = Path("data/raw/liquipedia/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class LiquipediaClient:
    """Client for the Liquipedia MediaWiki API."""

    rate_limit_seconds: float | None = None
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()
        if self.rate_limit_seconds is None:
            self.rate_limit_seconds = float(os.environ.get("LIQUIPEDIA_RATE_LIMIT_SECONDS", "2.0"))
        self._last_request_time = 0.0

    def _headers(self) -> dict[str, str]:
        user_agent = os.environ.get("LIQUIPEDIA_USER_AGENT")
        if not user_agent:
            raise RuntimeError(
                "LIQUIPEDIA_USER_AGENT environment variable is required. "
                "Example: 'CS2Diploma/0.1 (email@example.com)'."
            )
        return {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip",
        }

    def _cache_path(self, params: dict[str, Any]) -> Path:
        hash_input = BASE_URL + "?" + "&".join(
            f"{key}={params[key]}" for key in sorted(params)
        )
        digest = hashlib.sha1(hash_input.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{digest}.json"

    def _respect_rate_limit(self) -> None:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)

    def get_json(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get JSON response, using cache and retry logic."""
        cache_path = self._cache_path(params)
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

        self._respect_rate_limit()
        headers = self._headers()

        retries = 3
        backoff = 1.0
        while True:
            response = self.session.get(BASE_URL, params=params, headers=headers, timeout=30)
            if response.status_code in {429, 500, 502, 503, 504} and retries > 0:
                time.sleep(backoff)
                backoff *= 2
                retries -= 1
                continue
            response.raise_for_status()
            data = response.json()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            self._last_request_time = time.time()
            return data
