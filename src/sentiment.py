"""Sentiment classification using DistilBERT (primary) and VADER (comparison)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
NEUTRAL_THRESHOLD = 0.55  # below this max prob → neutral


def _torch_available() -> bool:
    try:
        import torch  # noqa: F401

        return True
    except ImportError:
        return False


@dataclass
class SentimentResult:
    label: str
    score: float
    positive_prob: float
    negative_prob: float


def _map_distilbert_label(raw_label: str) -> str:
    label = raw_label.upper()
    if "POS" in label:
        return "positive"
    if "NEG" in label:
        return "negative"
    return "neutral"


def distilbert_to_sentiment(prediction: dict) -> SentimentResult:
    """Convert Hugging Face pipeline output to label + confidence."""
    label = _map_distilbert_label(prediction["label"])
    score = float(prediction["score"])

    if label == "positive":
        positive_prob, negative_prob = score, 1.0 - score
    else:
        negative_prob, positive_prob = score, 1.0 - score

    max_prob = max(positive_prob, negative_prob)
    if max_prob < NEUTRAL_THRESHOLD:
        return SentimentResult(
            label="neutral",
            score=max_prob,
            positive_prob=positive_prob,
            negative_prob=negative_prob,
        )

    return SentimentResult(
        label=label,
        score=max_prob,
        positive_prob=positive_prob,
        negative_prob=negative_prob,
    )


def build_distilbert_classifier():
    """Load DistilBERT SST-2 sentiment pipeline (requires torch)."""
    if not _torch_available():
        raise ImportError(
            "torch is required for DistilBERT. Use Python 3.11–3.13 and "
            "pip install torch, or the pipeline will fall back to VADER."
        )
    from transformers import pipeline

    return pipeline("sentiment-analysis", model=MODEL_NAME, truncation=True)


def classify_texts_distilbert(
    texts: Iterable[str],
    classifier=None,
    *,
    batch_size: int = 32,
) -> list[SentimentResult]:
    """Classify a sequence of review texts with DistilBERT."""
    if classifier is None:
        classifier = build_distilbert_classifier()

    text_list = list(texts)
    results: list[SentimentResult] = []
    for start in range(0, len(text_list), batch_size):
        batch = text_list[start : start + batch_size]
        preds = classifier(batch)
        if isinstance(preds, dict):
            preds = [preds]
        for pred in preds:
            results.append(distilbert_to_sentiment(pred))
    return results


def classify_texts(
    texts: Iterable[str],
    classifier=None,
    *,
    batch_size: int = 32,
    prefer_distilbert: bool = True,
) -> tuple[list[SentimentResult], str]:
    """
    Classify texts with DistilBERT when torch is available, else VADER.

    Returns results and the model name used.
    """
    text_list = list(texts)
    if prefer_distilbert and _torch_available():
        try:
            return classify_texts_distilbert(
                text_list, classifier=classifier, batch_size=batch_size
            ), MODEL_NAME
        except Exception:
            pass

    return [classify_vader(t) for t in text_list], "VADER (fallback)"


def classify_vader(text: str) -> SentimentResult:
    """Lexicon-based sentiment for comparison."""
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    confidence = abs(compound)
    pos = scores["pos"]
    neg = scores["neg"]
    return SentimentResult(
        label=label,
        score=confidence,
        positive_prob=pos / max(pos + neg, 1e-6),
        negative_prob=neg / max(pos + neg, 1e-6),
    )


def aggregate_sentiment_by_bank_rating(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sentiment score grouped by bank and star rating."""
    grouped = (
        df.groupby(["bank", "rating"], as_index=False)
        .agg(
            review_count=("sentiment_score", "count"),
            mean_sentiment_score=("sentiment_score", "mean"),
            positive_pct=("sentiment_label", lambda s: (s == "positive").mean() * 100),
            negative_pct=("sentiment_label", lambda s: (s == "negative").mean() * 100),
            neutral_pct=("sentiment_label", lambda s: (s == "neutral").mean() * 100),
        )
        .round(4)
    )
    return grouped


def compare_distilbert_vader(
    df: pd.DataFrame,
    *,
    sample_size: int = 200,
) -> pd.DataFrame:
    """Compare DistilBERT vs VADER labels on a sample (for documentation)."""
    sample = df.head(sample_size) if len(df) > sample_size else df
    vader_labels = [classify_vader(t).label for t in sample["review_text"]]
    comparison = sample[["review_id", "sentiment_label"]].copy()
    comparison.columns = ["review_id", "distilbert_label"]
    comparison["vader_label"] = vader_labels
    comparison["agreement"] = comparison["distilbert_label"] == comparison["vader_label"]
    return comparison
