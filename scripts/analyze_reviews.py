#!/usr/bin/env python3
"""
Run sentiment and thematic analysis on cleaned reviews.

Usage (from project root):
    python scripts/analyze_reviews.py

Outputs:
    data/processed/reviews_analyzed.csv
    data/processed/reviews_enriched.csv  (full fields for DB load)
    data/processed/analysis_stats.json
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis import (  # noqa: E402
    load_reviews_with_ids,
    run_analysis,
    save_analysis_outputs,
)

CLEAN_INPUT = PROJECT_ROOT / "data" / "processed" / "reviews_clean.csv"
RAW_INPUT = PROJECT_ROOT / "data" / "raw" / "reviews_raw.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "reviews_analyzed.csv"
ENRICHED_CSV = PROJECT_ROOT / "data" / "processed" / "reviews_enriched.csv"
STATS_JSON = PROJECT_ROOT / "data" / "processed" / "analysis_stats.json"


def main() -> None:
    if not CLEAN_INPUT.exists() or not RAW_INPUT.exists():
        print("Missing input data. Run scrape and preprocess scripts first.")
        sys.exit(1)

    print("Loading reviews...")
    df = load_reviews_with_ids(CLEAN_INPUT, RAW_INPUT)
    print(f"  {len(df)} reviews loaded")

    print("Running sentiment + theme analysis (DistilBERT)...")
    analyzed, stats, enriched = run_analysis(df)

    save_analysis_outputs(
        analyzed,
        stats,
        output_csv=OUTPUT_CSV,
        stats_json=STATS_JSON,
        enriched_csv=ENRICHED_CSV,
        full_df=enriched,
    )

    print(f"\nSaved {len(analyzed)} analyzed reviews to {OUTPUT_CSV}")
    print(f"Model used: {stats['tool_selection']['primary']}")
    print(f"Sentiment labeled: {stats['sentiment_labeled_pct']}%")
    print(f"VADER agreement (sample): {stats['vader_agreement_pct']}%")
    print("\nSentiment distribution:", stats["sentiment_distribution"])
    print("\nThemes per bank:")
    for bank, info in stats["bank_theme_summary"].items():
        print(f"  {bank}: {info['distinct_themes']} distinct themes")
        print(f"    counts: {info['theme_counts']}")


if __name__ == "__main__":
    main()
