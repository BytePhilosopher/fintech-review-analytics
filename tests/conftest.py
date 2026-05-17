"""Shared pytest fixtures."""

import pytest

from src.text_pipeline import ensure_nltk_data


@pytest.fixture(scope="session", autouse=True)
def _download_nltk() -> None:
    ensure_nltk_data()
