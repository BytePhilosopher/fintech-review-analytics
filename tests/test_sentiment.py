"""Tests for sentiment label mapping (no model download)."""

from src.sentiment import distilbert_to_sentiment


def test_distilbert_positive_label():
    result = distilbert_to_sentiment({"label": "POSITIVE", "score": 0.92})
    assert result.label == "positive"
    assert result.score == 0.92


def test_distilbert_negative_label():
    result = distilbert_to_sentiment({"label": "NEGATIVE", "score": 0.88})
    assert result.label == "negative"


def test_distilbert_low_confidence_neutral():
    result = distilbert_to_sentiment({"label": "POSITIVE", "score": 0.51})
    assert result.label == "neutral"


def test_vader_positive():
    from src.sentiment import classify_vader

    result = classify_vader("I love this app, it is amazing and wonderful!")
    assert result.label == "positive"
