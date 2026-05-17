"""Extract business insights, drivers, pain points, and recommendations from review data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

DRIVER_KEYWORDS = [
    "fast",
    "easy",
    "good",
    "great",
    "love",
    "best",
    "smooth",
    "convenient",
    "reliable",
    "excellent",
    "simple",
    "helpful",
    "secure",
    "stable",
    "working",
]

PAIN_KEYWORDS = [
    "crash",
    "slow",
    "fail",
    "error",
    "bug",
    "otp",
    "login",
    "password",
    "pending",
    "worst",
    "terrible",
    "stuck",
    "freeze",
    "unable",
    "problem",
    "issue",
]


@dataclass
class Evidence:
    title: str
    theme: str
    mention_count: int
    avg_rating: float
    positive_pct: float
    sample_quotes: list[str] = field(default_factory=list)


@dataclass
class BankInsights:
    bank: str
    avg_rating: float
    sentiment_distribution: dict[str, int]
    dominant_themes: list[tuple[str, int]]
    drivers: list[Evidence]
    pain_points: list[Evidence]
    recommendations: list[str]


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lowered)]


def _sample_quotes(df: pd.DataFrame, n: int = 2) -> list[str]:
    quotes = []
    for text in df["review_text"].head(20):
        t = str(text).strip()
        if len(t) > 15:
            quotes.append(t[:160] + ("…" if len(t) > 160 else ""))
        if len(quotes) >= n:
            break
    return quotes


def _build_driver_evidence(bank_df: pd.DataFrame, keyword: str) -> Evidence | None:
    subset = bank_df[
        (bank_df["rating"] >= 4)
        & (bank_df["sentiment_label"] == "positive")
        & bank_df["review_text"].str.lower().str.contains(rf"\b{keyword}\b", regex=True)
    ]
    if len(subset) < 3:
        return None
    return Evidence(
        title=f"Positive mentions of '{keyword}'",
        theme=subset["identified_theme"].mode().iloc[0] if len(subset) else "General Feedback",
        mention_count=len(subset),
        avg_rating=round(subset["rating"].mean(), 2),
        positive_pct=100.0,
        sample_quotes=_sample_quotes(subset),
    )


def _build_pain_evidence(bank_df: pd.DataFrame, theme: str) -> Evidence | None:
    subset = bank_df[
        (bank_df["identified_theme"] == theme)
        & ((bank_df["rating"] <= 2) | (bank_df["sentiment_label"] == "negative"))
    ]
    if len(subset) < 3:
        subset = bank_df[bank_df["identified_theme"] == theme]
    if len(subset) < 3:
        return None
    neg_pct = (subset["sentiment_label"] == "negative").mean() * 100
    return Evidence(
        title=theme,
        theme=theme,
        mention_count=len(subset),
        avg_rating=round(subset["rating"].mean(), 2),
        positive_pct=round(100 - neg_pct, 1),
        sample_quotes=_sample_quotes(subset.sort_values("rating")),
    )


def _recommendations_for_bank(bank: str, pains: list[Evidence], drivers: list[Evidence]) -> list[str]:
    recs: list[str] = []
    pain_themes = {p.theme for p in pains}

    if "Account Access Issues" in pain_themes:
        recs.append(
            "Stabilize login and OTP flows with retry logic, clearer error messages, "
            "and offline-friendly session recovery to reduce authentication drop-offs."
        )
    if "Transaction Performance" in pain_themes:
        recs.append(
            "Prioritize transfer pipeline performance: surface real-time status, "
            "reduce pending-state duration, and alert users proactively on delays."
        )
    if "UI & Design" in pain_themes:
        recs.append(
            "Run targeted UX fixes on navigation and onboarding screens highlighted "
            "in negative UI-themed reviews; A/B test simplified transfer flows."
        )
    if "Customer Support" in pain_themes:
        recs.append(
            "Add in-app support chat with SLA targets and integrate branch/call-back "
            "options for unresolved tickets."
        )
    if "Feature Requests" in pain_themes:
        recs.append(
            "Publish a public roadmap for top-requested features and deliver quick wins "
            "(e.g., bill-pay shortcuts, statement export) within one quarter."
        )

    if len(recs) < 2 and drivers:
        recs.append(
            f"Double down on strengths users praise ({drivers[0].title.lower()}) "
            f"in marketing and onboarding while measuring retention impact."
        )
    if len(recs) < 2:
        recs.append(
            "Establish a monthly review triage ritual with product, engineering, and "
            "support leads to close the highest-volume complaint themes."
        )

    if bank == "Commercial Bank of Ethiopia" and len(recs) < 3:
        recs.append(
            "Maintain CBE's rating lead by regression-testing releases against "
            "transfer and login flows before rollout."
        )

    return recs[:3]


def extract_bank_insights(df: pd.DataFrame, bank: str) -> BankInsights:
    """Build structured insights for a single bank."""
    bank_df = df[df["bank"] == bank]
    sentiment_dist = bank_df["sentiment_label"].value_counts().to_dict()
    theme_counts = (
        bank_df["identified_theme"].value_counts().head(6).items()
    )
    dominant = [(t, int(c)) for t, c in theme_counts if t != "General Feedback"][:5]

    drivers: list[Evidence] = []
    for kw in DRIVER_KEYWORDS:
        ev = _build_driver_evidence(bank_df, kw)
        if ev:
            drivers.append(ev)
        if len(drivers) >= 3:
            break

    # Theme-based drivers for high-rating segments
    for theme in ["UI & Design", "Transaction Performance"]:
        subset = bank_df[
            (bank_df["identified_theme"] == theme) & (bank_df["rating"] >= 4)
        ]
        if len(subset) >= 5 and len(drivers) < 4:
            drivers.append(
                Evidence(
                    title=f"Strong satisfaction with {theme}",
                    theme=theme,
                    mention_count=len(subset),
                    avg_rating=round(subset["rating"].mean(), 2),
                    positive_pct=round(
                        (subset["sentiment_label"] == "positive").mean() * 100, 1
                    ),
                    sample_quotes=_sample_quotes(subset),
                )
            )

    pains: list[Evidence] = []
    for theme in [
        "Account Access Issues",
        "Transaction Performance",
        "UI & Design",
        "Customer Support",
    ]:
        ev = _build_pain_evidence(bank_df, theme)
        if ev:
            pains.append(ev)
        if len(pains) >= 3:
            break

    for kw in PAIN_KEYWORDS:
        if len(pains) >= 4:
            break
        subset = bank_df[
            (bank_df["rating"] <= 2)
            & bank_df["review_text"].str.lower().str.contains(rf"\b{kw}\b", regex=True)
        ]
        if len(subset) >= 3:
            pains.append(
                Evidence(
                    title=f"Negative mentions of '{kw}'",
                    theme=subset["identified_theme"].mode().iloc[0],
                    mention_count=len(subset),
                    avg_rating=round(subset["rating"].mean(), 2),
                    positive_pct=round(
                        (subset["sentiment_label"] == "positive").mean() * 100, 1
                    ),
                    sample_quotes=_sample_quotes(subset),
                )
            )

    # Deduplicate pains by theme
    seen: set[str] = set()
    unique_pains: list[Evidence] = []
    for p in pains:
        if p.theme not in seen:
            seen.add(p.theme)
            unique_pains.append(p)

    recommendations = _recommendations_for_bank(bank, unique_pains[:3], drivers[:2])

    return BankInsights(
        bank=bank,
        avg_rating=round(bank_df["rating"].mean(), 2),
        sentiment_distribution=sentiment_dist,
        dominant_themes=dominant,
        drivers=drivers[:3],
        pain_points=unique_pains[:3],
        recommendations=recommendations[:3],
    )


def extract_all_insights(df: pd.DataFrame) -> dict[str, BankInsights]:
    """Extract insights for every bank in the dataset."""
    return {bank: extract_bank_insights(df, bank) for bank in sorted(df["bank"].unique())}


def bank_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-bank comparison metrics."""
    rows = []
    for bank, grp in df.groupby("bank"):
        rows.append(
            {
                "bank": bank,
                "reviews": len(grp),
                "avg_rating": round(grp["rating"].mean(), 2),
                "positive_pct": round((grp["sentiment_label"] == "positive").mean() * 100, 1),
                "negative_pct": round((grp["sentiment_label"] == "negative").mean() * 100, 1),
                "top_theme": grp["identified_theme"]
                .replace("General Feedback", pd.NA)
                .dropna()
                .mode()
                .iloc[0]
                if len(grp["identified_theme"].replace("General Feedback", pd.NA).dropna())
                else "General Feedback",
            }
        )
    return pd.DataFrame(rows).sort_values("avg_rating", ascending=False)
