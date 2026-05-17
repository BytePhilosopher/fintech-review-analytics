"""Orchestrate sentiment and thematic analysis on cleaned reviews."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import BANK_APPS
from src.sentiment import (
    MODEL_NAME,
    aggregate_sentiment_by_bank_rating,
    classify_texts,
    compare_distilbert_vader,
)
from src.text_pipeline import preprocess_text
from src.themes import assign_themes_batch, build_bank_theme_summary

ANALYSIS_COLUMNS = (
    "review_id",
    "review_text",
    "sentiment_label",
    "sentiment_score",
    "identified_theme",
)


def load_reviews_with_ids(
    clean_path: Path,
    raw_path: Path,
) -> pd.DataFrame:
    """Merge cleaned reviews with review_id from raw scrape."""
    clean = pd.read_csv(clean_path)
    raw = pd.read_csv(raw_path)
    raw = raw.copy()
    raw["date"] = pd.to_datetime(raw["date"], utc=True).dt.strftime("%Y-%m-%d")

    merged = clean.merge(
        raw[["review_id", "review", "bank", "rating", "date"]],
        left_on=["review", "bank", "rating", "date"],
        right_on=["review", "bank", "rating", "date"],
        how="left",
    )

    missing_ids = merged["review_id"].isna().sum()
    if missing_ids:
        merged.loc[merged["review_id"].isna(), "review_id"] = [
            f"synthetic-{i}" for i in range(missing_ids)
        ]

    merged = merged.rename(columns={"review": "review_text"})
    merged = merged.drop_duplicates(subset=["review_id"], keep="first")
    return merged.reset_index(drop=True)


def run_analysis(df: pd.DataFrame, *, classifier=None) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """
    Run full NLP pipeline: preprocess → sentiment → themes.

    Returns analyzed DataFrame and summary statistics dict.
    """
    df = df.copy()
    df["processed_text"] = df["review_text"].apply(preprocess_text)

    sentiments, model_used = classify_texts(df["review_text"], classifier=classifier)
    df["sentiment_label"] = [s.label for s in sentiments]
    df["sentiment_score"] = [s.score for s in sentiments]

    df = assign_themes_batch(df)

    output = df[list(ANALYSIS_COLUMNS)].copy()

    labeled_pct = 100 * len(output) / max(len(df), 1)
    bank_theme_summary = build_bank_theme_summary(df)
    aggregates = aggregate_sentiment_by_bank_rating(df)
    vader_comparison = compare_distilbert_vader(df, sample_size=min(200, len(df)))

    stats = {
        "total_reviews": len(output),
        "sentiment_labeled_pct": round(labeled_pct, 2),
        "sentiment_distribution": df["sentiment_label"].value_counts().to_dict(),
        "bank_theme_summary": bank_theme_summary,
        "aggregate_by_bank_rating": aggregates.to_dict(orient="records"),
        "vader_agreement_pct": round(vader_comparison["agreement"].mean() * 100, 2),
        "tool_selection": {
            "primary": model_used,
            "target_model": MODEL_NAME,
            "comparison": "VADER",
            "rationale": (
                "DistilBERT (SST-2) is preferred for contextual accuracy on informal "
                "reviews. VADER is used for comparison and as fallback when torch is "
                "unavailable (e.g. Python 3.14). Neutral labels when confidence < 0.55."
            ),
        },
    }

    return output, stats, df


def bank_app_lookup() -> dict[str, str]:
    """Map bank_name → display app name."""
    return {app.bank_name: app.display_name for app in BANK_APPS}


def save_analysis_outputs(
    analyzed: pd.DataFrame,
    stats: dict,
    *,
    output_csv: Path,
    stats_json: Path,
    enriched_csv: Path | None = None,
    full_df: pd.DataFrame | None = None,
) -> None:
    """Persist analysis CSV and summary JSON."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    analyzed.to_csv(output_csv, index=False)
    stats_json.write_text(json.dumps(stats, indent=2, default=str))

    if enriched_csv and full_df is not None:
        full_df.to_csv(enriched_csv, index=False)
