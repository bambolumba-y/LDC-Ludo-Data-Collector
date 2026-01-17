"""Optional CatBoost training script.

This script is not part of the data pipeline acceptance checks.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import catboost
import pandas as pd

from src.liquipedia.logging_utils import setup_logging


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a minimal CatBoost model (optional).")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/matches.parquet"),
        help="Path to matches.parquet",
    )
    parser.add_argument("--iterations", type=int, default=50, help="Number of boosting iterations")
    parser.add_argument("--output", type=Path, default=Path("reports/catboost_model.cbm"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()

    df = pd.read_parquet(args.input)
    df = df.dropna(subset=["score1", "score2", "winner"])
    if df.empty:
        raise ValueError("No training data available. Ensure matches.parquet has scores and winners.")

    df = df.assign(winner_label=(df["winner"] == "team1").astype(int))
    features = df[["score1", "score2", "best_of"]].fillna(0)
    target = df["winner_label"]

    model = catboost.CatBoostClassifier(
        iterations=args.iterations,
        depth=6,
        learning_rate=0.1,
        loss_function="Logloss",
        verbose=False,
    )
    model.fit(features, target)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(args.output))
    logger.info("Saved model to %s", args.output)


if __name__ == "__main__":
    main()
