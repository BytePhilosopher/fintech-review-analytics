"""Thematic analysis: TF-IDF keyword extraction and rule-based theme assignment."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.text_pipeline import preprocess_text

# Business-relevant themes with keyword / n-gram triggers (grouping logic)
THEME_DEFINITIONS: dict[str, list[str]] = {
    "Account Access Issues": [
        "login",
        "log in",
        "password",
        "otp",
        "verify",
        "verification",
        "locked",
        "access",
        "account",
        "sign in",
        "pin",
        "authentication",
        "blocked",
    ],
    "Transaction Performance": [
        "transfer",
        "transaction",
        "slow",
        "pending",
        "payment",
        "delay",
        "failed",
        "fail",
        "processing",
        "timeout",
        "deposit",
        "withdraw",
    ],
    "UI & Design": [
        "ui",
        "interface",
        "design",
        "screen",
        "layout",
        "easy",
        "simple",
        "beautiful",
        "look",
        "navigate",
        "user friendly",
    ],
    "Customer Support": [
        "support",
        "service",
        "call",
        "help",
        "agent",
        "response",
        "branch",
        "staff",
        "customer care",
        "complaint",
    ],
    "Feature Requests": [
        "feature",
        "add",
        "wish",
        "need",
        "should",
        "update",
        "improve",
        "option",
        "request",
        "missing",
        "include",
    ],
}

DEFAULT_THEME = "General Feedback"


@dataclass
class ThemeMatch:
    theme: str
    score: int
    matched_keywords: list[str]


def _find_keyword_matches(text: str, keywords: list[str]) -> list[str]:
    """Return keywords found in text (case-insensitive, phrase-aware)."""
    lowered = text.lower()
    matched = []
    for kw in keywords:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, lowered):
            matched.append(kw)
    return matched


def assign_theme(review_text: str, processed_text: str | None = None) -> ThemeMatch:
    """
    Assign the best-matching theme by keyword hit count.

    Uses raw text for phrase matching; processed text as fallback token check.
    """
    best_theme = DEFAULT_THEME
    best_score = 0
    best_matches: list[str] = []

    search_text = review_text.lower()
    if processed_text:
        search_text = f"{search_text} {processed_text}"

    for theme, keywords in THEME_DEFINITIONS.items():
        matched = _find_keyword_matches(search_text, keywords)
        score = len(matched)
        if score > best_score:
            best_score = score
            best_theme = theme
            best_matches = matched

    return ThemeMatch(theme=best_theme, score=best_score, matched_keywords=best_matches)


def extract_tfidf_keywords(
    texts: list[str],
    *,
    ngram_range: tuple[int, int] = (1, 2),
    top_k: int = 15,
) -> list[tuple[str, float]]:
    """Extract top TF-IDF terms from a corpus of preprocessed texts."""
    if not texts or all(not t.strip() for t in texts):
        return []

    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range,
        max_features=5000,
        min_df=2,
    )
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []

    scores = matrix.mean(axis=0).A1
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


def build_bank_theme_summary(df: pd.DataFrame) -> dict[str, dict]:
    """
    Per-bank theme stats: count, example keywords from TF-IDF, sample reviews.
    """
    summary: dict[str, dict] = {}

    for bank, bank_df in df.groupby("bank"):
        processed = bank_df["processed_text"].fillna("").tolist()
        tfidf_terms = extract_tfidf_keywords(processed, top_k=20)

        theme_counts = bank_df["identified_theme"].value_counts().to_dict()
        theme_examples: dict[str, list[str]] = {}

        for theme in theme_counts:
            if theme == DEFAULT_THEME:
                continue
            keywords = THEME_DEFINITIONS.get(theme, [])
            theme_examples[theme] = keywords[:8]

        summary[bank] = {
            "theme_counts": theme_counts,
            "tfidf_top_terms": [t for t, _ in tfidf_terms[:10]],
            "theme_keyword_examples": theme_examples,
            "distinct_themes": len([t for t in theme_counts if t != DEFAULT_THEME]),
        }

    return summary


def assign_themes_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Add identified_theme column based on review text."""
    themes = []
    for _, row in df.iterrows():
        processed = row.get("processed_text") or preprocess_text(row["review_text"])
        match = assign_theme(row["review_text"], processed)
        themes.append(match.theme)
    df = df.copy()
    df["identified_theme"] = themes
    return df
