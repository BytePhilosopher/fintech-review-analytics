"""Review dataset cleaning and normalization."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_OUTPUT_COLUMNS = ("review", "rating", "date", "bank", "source")


def normalize_date(value) -> str | None:
    """Normalize a review timestamp to YYYY-MM-DD."""
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value, utc=True).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def preprocess_reviews(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean raw scraped reviews into an analysis-ready dataset.

    Steps:
      1. Drop duplicate reviews by review_id
      2. Drop rows missing review text or rating
      3. Normalize dates to YYYY-MM-DD
      4. Select final output columns

    Returns cleaned DataFrame and a stats dict for documentation.
    """
    stats: dict = {"input_rows": len(df)}

    if "review_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["review_id"], keep="first")
        stats["duplicates_removed"] = before - len(df)
    else:
        stats["duplicates_removed"] = 0

    missing_review = df["review"].isna() | (df["review"].astype(str).str.strip() == "")
    missing_rating = df["rating"].isna()
    stats["dropped_missing_review"] = int(missing_review.sum())
    stats["dropped_missing_rating"] = int(missing_rating.sum())

    df = df.loc[~missing_review & ~missing_rating].copy()

    df["date"] = df["date"].apply(normalize_date)
    missing_date = df["date"].isna()
    stats["dropped_missing_date"] = int(missing_date.sum())
    df = df.loc[~missing_date].copy()

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype(int)
    invalid_rating = ~df["rating"].between(1, 5)
    stats["dropped_invalid_rating"] = int(invalid_rating.sum())
    df = df.loc[~invalid_rating].copy()

    df["review"] = df["review"].astype(str).str.strip()
    df["bank"] = df["bank"].astype(str).str.strip()
    df["source"] = df["source"].astype(str).str.strip()

    output = df[list(REQUIRED_OUTPUT_COLUMNS)].reset_index(drop=True)
    stats["output_rows"] = len(output)
    stats["missing_data_pct"] = round(
        100 * (stats["input_rows"] - stats["output_rows"]) / max(stats["input_rows"], 1),
        2,
    )

    return output, stats


def save_cleaned_csv(df: pd.DataFrame, path: Path) -> None:
    """Write cleaned dataset to CSV (path should be gitignored)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
