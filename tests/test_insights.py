"""Tests for insight extraction logic."""

import pandas as pd

from src.insights import bank_comparison_table, extract_bank_insights


def _sample_df() -> pd.DataFrame:
    rows = []
    for i in range(3):
        rows.append(
            {
                "review_text": f"Fast and easy transfers, love this app {i}",
                "rating": 5,
                "sentiment_label": "positive",
                "sentiment_score": 0.9,
                "identified_theme": "Transaction Performance",
                "bank": "Dashen Bank",
                "processed_text": "fast easy transfer love app",
            }
        )
    rows.append(
        {
            "review_text": "Great UI very simple and easy to use",
            "rating": 5,
            "sentiment_label": "positive",
            "sentiment_score": 0.85,
            "identified_theme": "UI & Design",
            "bank": "Dashen Bank",
            "processed_text": "great ui simple easy",
        }
    )
    for i in range(3):
        rows.append(
            {
                "review_text": f"Login failed OTP not working case {i}",
                "rating": 1,
                "sentiment_label": "negative",
                "sentiment_score": 0.8,
                "identified_theme": "Account Access Issues",
                "bank": "Dashen Bank",
                "processed_text": "login fail otp not work",
            }
        )
    for i in range(3):
        rows.append(
            {
                "review_text": f"Slow pending transfer worst experience {i}",
                "rating": 2,
                "sentiment_label": "negative",
                "sentiment_score": 0.7,
                "identified_theme": "Transaction Performance",
                "bank": "Dashen Bank",
                "processed_text": "slow pending transfer worst",
            }
        )
    return pd.DataFrame(rows)


def test_extract_bank_insights_has_drivers_and_pains():
    insights = extract_bank_insights(_sample_df(), "Dashen Bank")
    assert len(insights.drivers) >= 1
    assert len(insights.pain_points) >= 1
    assert len(insights.recommendations) >= 2


def test_bank_comparison_table_columns():
    table = bank_comparison_table(_sample_df())
    assert "avg_rating" in table.columns
    assert len(table) == 1
