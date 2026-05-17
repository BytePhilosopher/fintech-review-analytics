#!/usr/bin/env python3
"""
Load enriched reviews into PostgreSQL (bank_reviews database).

Prerequisites:
  - PostgreSQL running locally
  - Database created: CREATE DATABASE bank_reviews;
  - Environment variables (or .env): POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

Usage:
    python scripts/analyze_reviews.py   # if not yet run
    python scripts/load_to_postgres.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.db import load_reviews_from_enriched_csv  # noqa: E402

ENRICHED_CSV = PROJECT_ROOT / "data" / "processed" / "reviews_enriched.csv"
SCHEMA_SQL = PROJECT_ROOT / "schema" / "schema.sql"


def main() -> None:
    if not ENRICHED_CSV.exists():
        print(f"Missing {ENRICHED_CSV}. Run scripts/analyze_reviews.py first.")
        sys.exit(1)

    try:
        count = load_reviews_from_enriched_csv(ENRICHED_CSV, schema_path=SCHEMA_SQL)
    except Exception as exc:
        print(f"Database load failed: {exc}")
        print("\nEnsure PostgreSQL is running and bank_reviews database exists.")
        print("See README.md Task 3 section for setup steps.")
        sys.exit(1)

    print(f"Successfully loaded {count} reviews into PostgreSQL.")


if __name__ == "__main__":
    main()
