#!/usr/bin/env python3
"""
Scrape Google Play Store reviews for Ethiopian bank mobile apps.

Usage (from project root):
    python scripts/scrape_reviews.py

Output:
    data/raw/reviews_raw.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import MIN_REVIEWS_PER_BANK  # noqa: E402
from src.scraper import scrape_all_banks  # noqa: E402

RAW_OUTPUT = PROJECT_ROOT / "data" / "raw" / "reviews_raw.csv"


def main() -> None:
    """Scrape reviews and persist raw CSV."""
    print(f"Target: {MIN_REVIEWS_PER_BANK}+ reviews per bank")
    df = scrape_all_banks(min_reviews_per_bank=MIN_REVIEWS_PER_BANK)

    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_OUTPUT, index=False)

    print(f"\nSaved {len(df)} raw reviews to {RAW_OUTPUT}")
    print("\nPer-bank counts:")
    for bank, count in df.groupby("bank").size().items():
        status = "OK" if count >= MIN_REVIEWS_PER_BANK else "BELOW TARGET"
        print(f"  {bank}: {count} [{status}]")


if __name__ == "__main__":
    main()
