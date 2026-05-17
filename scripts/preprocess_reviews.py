#!/usr/bin/env python3
"""
Preprocess raw Google Play reviews into a clean analysis-ready CSV.

Usage (from project root):
    python scripts/preprocess_reviews.py

Input:
    data/raw/reviews_raw.csv

Output:
    data/processed/reviews_clean.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocess import preprocess_reviews, save_cleaned_csv  # noqa: E402

RAW_INPUT = PROJECT_ROOT / "data" / "raw" / "reviews_raw.csv"
CLEAN_OUTPUT = PROJECT_ROOT / "data" / "processed" / "reviews_clean.csv"
STATS_OUTPUT = PROJECT_ROOT / "data" / "processed" / "preprocess_stats.json"


def main() -> None:
    """Load raw reviews, clean, and save processed CSV plus stats JSON."""
    if not RAW_INPUT.exists():
        print(f"Error: raw file not found at {RAW_INPUT}")
        print("Run scripts/scrape_reviews.py first.")
        sys.exit(1)

    import pandas as pd

    raw = pd.read_csv(RAW_INPUT)
    cleaned, stats = preprocess_reviews(raw)

    save_cleaned_csv(cleaned, CLEAN_OUTPUT)
    STATS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    STATS_OUTPUT.write_text(json.dumps(stats, indent=2))

    print(f"Input rows:  {stats['input_rows']}")
    print(f"Output rows: {stats['output_rows']}")
    print(f"Missing data removed: {stats['missing_data_pct']}%")
    print(f"\nSaved cleaned data to {CLEAN_OUTPUT}")
    print("\nPer-bank counts (cleaned):")
    for bank, count in cleaned.groupby("bank").size().items():
        print(f"  {bank}: {count}")


if __name__ == "__main__":
    main()
