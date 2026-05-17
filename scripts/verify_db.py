#!/usr/bin/env python3
"""Run SQL verification queries against bank_reviews database."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.db import connect  # noqa: E402

QUERIES = {
    "reviews_per_bank": """
        SELECT b.bank_name, COUNT(r.review_id) AS review_count
        FROM banks b
        LEFT JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY review_count DESC;
    """,
    "average_rating_per_bank": """
        SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2) AS avg_rating
        FROM banks b
        JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY avg_rating DESC;
    """,
    "null_check_key_columns": """
        SELECT
            COUNT(*) FILTER (WHERE review_text IS NULL) AS null_review_text,
            COUNT(*) FILTER (WHERE rating IS NULL) AS null_rating,
            COUNT(*) FILTER (WHERE review_date IS NULL) AS null_review_date,
            COUNT(*) FILTER (WHERE sentiment_label IS NULL) AS null_sentiment_label,
            COUNT(*) FILTER (WHERE identified_theme IS NULL) AS null_theme
        FROM reviews;
    """,
    "sentiment_by_bank": """
        SELECT b.bank_name, r.sentiment_label, COUNT(*) AS cnt
        FROM reviews r
        JOIN banks b ON r.bank_id = b.bank_id
        GROUP BY b.bank_name, r.sentiment_label
        ORDER BY b.bank_name, cnt DESC;
    """,
}


def main() -> None:
    try:
        conn = connect()
    except Exception as exc:
        print(f"Connection failed: {exc}")
        sys.exit(1)

    with conn:
        with conn.cursor() as cur:
            for name, sql in QUERIES.items():
                print(f"\n=== {name} ===")
                cur.execute(sql)
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                print(" | ".join(cols))
                print("-" * 40)
                for row in rows:
                    print(" | ".join(str(v) for v in row))

    conn.close()
    print("\nVerification complete.")


if __name__ == "__main__":
    main()
