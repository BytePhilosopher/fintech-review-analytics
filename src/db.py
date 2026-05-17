"""PostgreSQL connection and data loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

from src.analysis import bank_app_lookup
from src.config import BANK_APPS

load_dotenv()

DEFAULT_DB = "bank_reviews"


def get_connection_params() -> dict[str, Any]:
    """Read PostgreSQL connection settings from environment."""
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", DEFAULT_DB),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }


def connect():
    """Open a psycopg2 connection."""
    return psycopg2.connect(**get_connection_params())


def init_schema(schema_path: Path) -> None:
    """Execute schema SQL file against the database."""
    sql = schema_path.read_text()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def upsert_banks(conn) -> dict[str, int]:
    """Insert bank metadata; return bank_name → bank_id map."""
    app_names = bank_app_lookup()
    rows = [(app.bank_name, app_names[app.bank_name]) for app in BANK_APPS]

    bank_ids: dict[str, int] = {}
    with conn.cursor() as cur:
        for bank_name, app_name in rows:
            cur.execute(
                """
                INSERT INTO banks (bank_name, app_name)
                VALUES (%s, %s)
                ON CONFLICT (bank_name) DO UPDATE SET app_name = EXCLUDED.app_name
                RETURNING bank_id
                """,
                (bank_name, app_name),
            )
            bank_ids[bank_name] = cur.fetchone()[0]
    conn.commit()
    return bank_ids


def load_reviews_from_enriched_csv(
    csv_path: Path,
    *,
    schema_path: Path | None = None,
) -> int:
    """
    Load enriched review CSV into PostgreSQL.

    Expects columns: review_id, review_text, rating, date, bank, source,
    sentiment_label, sentiment_score, identified_theme
    """
    df = pd.read_csv(csv_path)
    if schema_path:
        init_schema(schema_path)

    with connect() as conn:
        bank_ids = upsert_banks(conn)

        records = []
        for _, row in df.iterrows():
            records.append(
                (
                    row["review_id"],
                    bank_ids[row["bank"]],
                    row["review_text"],
                    int(row["rating"]),
                    row["date"],
                    row.get("sentiment_label"),
                    float(row["sentiment_score"]) if pd.notna(row.get("sentiment_score")) else None,
                    row.get("identified_theme"),
                    row.get("source", "Google Play"),
                )
            )

        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO reviews (
                    review_id, bank_id, review_text, rating, review_date,
                    sentiment_label, sentiment_score, identified_theme, source
                ) VALUES %s
                ON CONFLICT (review_id) DO UPDATE SET
                    review_text = EXCLUDED.review_text,
                    rating = EXCLUDED.rating,
                    review_date = EXCLUDED.review_date,
                    sentiment_label = EXCLUDED.sentiment_label,
                    sentiment_score = EXCLUDED.sentiment_score,
                    identified_theme = EXCLUDED.identified_theme
                """,
                records,
            )
        conn.commit()

    return len(records)
