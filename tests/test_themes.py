"""Tests for theme assignment logic."""

from src.themes import DEFAULT_THEME, assign_theme, extract_tfidf_keywords


def test_assign_theme_login():
    match = assign_theme("Cannot login to my account, password reset fails")
    assert match.theme == "Account Access Issues"
    assert match.score >= 1


def test_assign_theme_transfer():
    match = assign_theme("Transfer is very slow and pending for hours")
    assert match.theme == "Transaction Performance"


def test_assign_theme_general_fallback():
    match = assign_theme("ok")
    assert match.theme == DEFAULT_THEME


def test_tfidf_keywords_nonempty():
    texts = [
        "login error password reset",
        "slow transfer payment pending",
        "login failed again password",
    ]
    keywords = extract_tfidf_keywords(texts, top_k=5)
    assert len(keywords) > 0
