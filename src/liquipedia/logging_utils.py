"""Logging helpers for the pipeline."""

from __future__ import annotations

import logging


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging."""
    logging.basicConfig(level=level, format=LOG_FORMAT)
