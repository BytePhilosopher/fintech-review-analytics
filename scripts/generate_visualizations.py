#!/usr/bin/env python3
"""
Generate stakeholder-ready plots for Task 4 insights.

Usage:
    python scripts/generate_visualizations.py

Outputs (reports/figures/):
    01_sentiment_by_bank.png
    02_rating_distribution.png
    03_theme_frequency.png
    04_top_keywords.png
    05_sentiment_trend.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

ENRICHED_CSV = PROJECT_ROOT / "data" / "processed" / "reviews_enriched.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

BANK_ORDER = [
    "Commercial Bank of Ethiopia",
    "Dashen Bank",
    "Bank of Abyssinia",
]
SENTIMENT_ORDER = ["positive", "neutral", "negative"]
PALETTE = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}


def _load_data() -> pd.DataFrame:
    df = pd.read_csv(ENRICHED_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df["bank"] = pd.Categorical(df["bank"], categories=BANK_ORDER, ordered=True)
    return df


def plot_sentiment_by_bank(df: pd.DataFrame) -> None:
    """Stacked bar chart: sentiment distribution by bank."""
    counts = (
        df.groupby(["bank", "sentiment_label"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
    )
    pct = counts.div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = pd.Series(0.0, index=pct.index)
    for sentiment in SENTIMENT_ORDER:
        ax.bar(
            pct.index.astype(str),
            pct[sentiment],
            bottom=bottom,
            label=sentiment.capitalize(),
            color=PALETTE[sentiment],
            edgecolor="white",
        )
        bottom += pct[sentiment]

    ax.set_ylabel("Share of reviews (%)")
    ax.set_xlabel("Bank")
    ax.set_title("Sentiment Distribution by Bank", fontsize=14, fontweight="bold")
    ax.legend(title="Sentiment", loc="upper right")
    ax.set_ylim(0, 100)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "01_sentiment_by_bank.png", dpi=150)
    plt.close(fig)


def plot_rating_distribution(df: pd.DataFrame) -> None:
    """Boxplot of star ratings per bank."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        data=df,
        x="bank",
        y="rating",
        order=BANK_ORDER,
        color="#5dade2",
        ax=ax,
    )
    sns.stripplot(
        data=df.sample(min(200, len(df)), random_state=42),
        x="bank",
        y="rating",
        order=BANK_ORDER,
        color="0.25",
        alpha=0.25,
        size=3,
        ax=ax,
    )
    ax.set_xlabel("Bank")
    ax.set_ylabel("Star rating")
    ax.set_title("Rating Distribution per Bank", fontsize=14, fontweight="bold")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "02_rating_distribution.png", dpi=150)
    plt.close(fig)


def plot_theme_frequency(df: pd.DataFrame) -> None:
    """Grouped horizontal bar chart of theme frequency (excl. General Feedback)."""
    themed = df[df["identified_theme"] != "General Feedback"].copy()
    counts = (
        themed.groupby(["bank", "identified_theme"], observed=True)
        .size()
        .reset_index(name="count")
    )
    top_themes = (
        counts.groupby("identified_theme")["count"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )
    counts = counts[counts["identified_theme"].isin(top_themes)]

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(
        data=counts,
        y="identified_theme",
        x="count",
        hue="bank",
        hue_order=BANK_ORDER,
        order=top_themes[::-1],
        ax=ax,
    )
    ax.set_xlabel("Number of reviews")
    ax.set_ylabel("Theme")
    ax.set_title("Theme Frequency by Bank (Top 5 Themes)", fontsize=14, fontweight="bold")
    ax.legend(title="Bank", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "03_theme_frequency.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_top_keywords(df: pd.DataFrame) -> None:
    """Top TF-IDF keywords per bank (horizontal bars)."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharex=True)
    for ax, bank in zip(axes, BANK_ORDER):
        texts = df.loc[df["bank"] == bank, "processed_text"].fillna("").tolist()
        vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2), min_df=3)
        try:
            matrix = vec.fit_transform(texts)
            scores = matrix.mean(axis=0).A1
            terms = vec.get_feature_names_out()
            ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)[:8]
        except ValueError:
            ranked = []

        labels = [t for t, _ in ranked][::-1]
        values = [s for _, s in ranked][::-1]
        ax.barh(labels, values, color="#3498db")
        ax.set_title(bank.replace("Commercial Bank of Ethiopia", "CBE"), fontsize=10)
        ax.set_xlabel("Mean TF-IDF weight")

    fig.suptitle("Top Keywords per Bank", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "04_top_keywords.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_sentiment_trend(df: pd.DataFrame) -> None:
    """Monthly mean sentiment score trend."""
    monthly = (
        df.set_index("date")
        .groupby([pd.Grouper(freq="ME"), "bank"])["sentiment_score"]
        .mean()
        .reset_index()
    )
    monthly["month"] = monthly["date"].dt.strftime("%Y-%m")

    fig, ax = plt.subplots(figsize=(11, 6))
    for bank in BANK_ORDER:
        subset = monthly[monthly["bank"] == bank]
        ax.plot(
            subset["month"],
            subset["sentiment_score"],
            marker="o",
            linewidth=2,
            label=bank.replace("Commercial Bank of Ethiopia", "CBE"),
        )

    ax.set_xlabel("Month")
    ax.set_ylabel("Mean sentiment confidence score")
    ax.set_title("Sentiment Trend Over Time", fontsize=14, fontweight="bold")
    ax.legend(title="Bank")
    plt.xticks(rotation=45, ha="right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "05_sentiment_trend.png", dpi=150)
    plt.close(fig)


def main() -> None:
    if not ENRICHED_CSV.exists():
        print(f"Missing {ENRICHED_CSV}. Run analyze_reviews.py first.")
        sys.exit(1)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=1.05)
    df = _load_data()

    print("Generating visualizations...")
    plot_sentiment_by_bank(df)
    plot_rating_distribution(df)
    plot_theme_frequency(df)
    plot_top_keywords(df)
    plot_sentiment_trend(df)
    print(f"Saved 5 figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
