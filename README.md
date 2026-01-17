# Liquipedia CS2 Data Pipeline

This project downloads Counter-Strike tournament data from Liquipedia (MediaWiki API) and builds a clean dataset for ML experiments.

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your User-Agent (required by Liquipedia):

```bash
export LIQUIPEDIA_USER_AGENT="CS2Diploma/0.1 (email@example.com)"
```

Optional rate limit override (seconds between requests):

```bash
export LIQUIPEDIA_RATE_LIMIT_SECONDS=2.0
```

## Usage

Download tournaments (S/A tier):

```bash
python -m src.liquipedia.download_tournaments --tiers S A --limit 50
```

Download tournament pages:

```bash
python -m src.liquipedia.download_pages --input data/raw/liquipedia/tournaments.jsonl --max_pages 10
```

Build dataset:

```bash
python -m src.liquipedia.build_dataset --input data/raw/liquipedia/tournaments.jsonl --max_pages 10
```

Run tests:

```bash
pytest -q
```

## Output

- Raw responses: `data/raw/liquipedia/`
- Processed dataset: `data/processed/matches.parquet`
- Data quality report: `reports/data_quality.json`

## Next step (optional)

The next milestone after this pipeline is feature engineering and optional model training (e.g., CatBoost). A minimal training script is provided under `src/modeling/train_catboost.py`, but it is not required for data collection or acceptance. To use it, install `catboost` separately and run the script manually.
