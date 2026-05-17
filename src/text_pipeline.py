"""Text preprocessing: tokenization, stop-word removal, and lemmatization."""

from __future__ import annotations

import re
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

NLTK_RESOURCES = ("punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4")


def ensure_nltk_data() -> None:
    """Download required NLTK corpora if missing."""
    for resource in NLTK_RESOURCES:
        try:
            if resource.startswith("punkt"):
                nltk.data.find(f"tokenizers/{resource}")
            elif resource == "stopwords":
                nltk.data.find("corpora/stopwords")
            else:
                nltk.data.find(f"corpora/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)


@lru_cache(maxsize=1)
def _lemmatizer() -> WordNetLemmatizer:
    ensure_nltk_data()
    return WordNetLemmatizer()


@lru_cache(maxsize=1)
def _stopword_set() -> set[str]:
    ensure_nltk_data()
    return set(stopwords.words("english"))


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    """Tokenize normalized text into words."""
    ensure_nltk_data()
    normalized = normalize_text(text)
    if not normalized:
        return []
    return word_tokenize(normalized)


def remove_stopwords(tokens: list[str]) -> list[str]:
    """Remove English stop words from token list."""
    stops = _stopword_set()
    return [t for t in tokens if t not in stops and len(t) > 1]


def lemmatize_tokens(tokens: list[str]) -> list[str]:
    """Lemmatize tokens using NLTK WordNet lemmatizer."""
    lemmatizer = _lemmatizer()
    return [lemmatizer.lemmatize(t) for t in tokens]


def preprocess_text(text: str, *, lemmatize: bool = True) -> str:
    """
    Full preprocessing pipeline: normalize → tokenize → stopwords → lemmatize.

    Returns a space-joined string of processed tokens for TF-IDF / matching.
    """
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    if lemmatize:
        tokens = lemmatize_tokens(tokens)
    return " ".join(tokens)
