"""Unit tests for review preprocessing pipeline."""

from datetime import datetime, timezone

import pandas as pd
import pytest

from src.preprocess import normalize_date, preprocess_reviews


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_id": "r1",
                "review": "Great app!",
                "rating": 5,
                "date": datetime(2024, 3, 15, tzinfo=timezone.utc),
                "bank": "Dashen Bank",
                "source": "Google Play",
            },
            {
                "review_id": "r1",
                "review": "Great app!",
                "rating": 5,
                "date": datetime(2024, 3, 15, tzinfo=timezone.utc),
                "bank": "Dashen Bank",
                "source": "Google Play",
            },
            {
                "review_id": "r2",
                "review": "",
                "rating": 4,
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "bank": "Awash Bank",
                "source": "Google Play",
            },
            {
                "review_id": "r3",
                "review": "Crashes often",
                "rating": None,
                "date": datetime(2024, 2, 1, tzinfo=timezone.utc),
                "bank": "CBE",
                "source": "Google Play",
            },
            {
                "review_id": "r4",
                "review": "Slow transfers",
                "rating": 2,
                "date": datetime(2023, 12, 5, tzinfo=timezone.utc),
                "bank": "CBE",
                "source": "Google Play",
            },
        ]
    )


def test_normalize_date_iso_format():
    assert normalize_date(datetime(2024, 6, 1, tzinfo=timezone.utc)) == "2024-06-01"


def test_normalize_date_invalid_returns_none():
    assert normalize_date("not-a-date") is None


def test_preprocess_removes_duplicates_and_missing(sample_raw_df):
    cleaned, stats = preprocess_reviews(sample_raw_df)

    assert stats["duplicates_removed"] == 1
    assert stats["dropped_missing_review"] == 1
    assert stats["dropped_missing_rating"] == 1
    assert len(cleaned) == 2


def test_preprocess_output_columns(sample_raw_df):
    cleaned, _ = preprocess_reviews(sample_raw_df)
    assert list(cleaned.columns) == ["review", "rating", "date", "bank", "source"]


def test_preprocess_date_format(sample_raw_df):
    cleaned, _ = preprocess_reviews(sample_raw_df)
    assert cleaned["date"].iloc[0] == "2024-03-15"
    assert cleaned["rating"].dtype == int
