"""Tests for text preprocessing pipeline."""

from src.text_pipeline import normalize_text, preprocess_text, remove_stopwords, tokenize


def test_normalize_text_lowercases():
    assert normalize_text("Hello World!") == "hello world"


def test_tokenize_splits_words():
    tokens = tokenize("The app is fast")
    assert "app" in tokens
    assert "the" in tokens


def test_remove_stopwords():
    tokens = remove_stopwords(["the", "app", "is", "fast"])
    assert "the" not in tokens
    assert "app" in tokens


def test_preprocess_text_returns_string():
    result = preprocess_text("Great banking app, very fast transfers!")
    assert isinstance(result, str)
    assert len(result) > 0
