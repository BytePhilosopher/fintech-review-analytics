"""Google Play review scraping utilities."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
from google_play_scraper import Sort, reviews
from google_play_scraper.exceptions import NotFoundError

from src.config import (
    BANK_APPS,
    BATCH_SIZE,
    DEFAULT_COUNTRY,
    DEFAULT_LANG,
    MIN_REVIEWS_PER_BANK,
    SOURCE,
    BankApp,
)


def fetch_reviews_for_app(
    app: BankApp,
    *,
    min_reviews: int = MIN_REVIEWS_PER_BANK,
    lang: str = DEFAULT_LANG,
    country: str = DEFAULT_COUNTRY,
    batch_size: int = BATCH_SIZE,
    pause_seconds: float = 1.0,
) -> list[dict[str, Any]]:
    """
    Fetch reviews for a single bank app, paginating until min_reviews is reached.

    Uses NEWEST sort first, then falls back to MOST_RELEVANT if needed.
    """
    collected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for sort_order in (Sort.NEWEST, Sort.MOST_RELEVANT):
        continuation_token = None
        while len(collected) < min_reviews:
            try:
                batch, continuation_token = reviews(
                    app.package_id,
                    lang=lang,
                    country=country,
                    sort=sort_order,
                    count=batch_size,
                    continuation_token=continuation_token,
                )
            except NotFoundError as exc:
                raise NotFoundError(
                    f"App not found: {app.display_name} ({app.package_id})"
                ) from exc

            if not batch:
                break

            for review in batch:
                review_id = review.get("reviewId") or review.get("review_id")
                if review_id and review_id in seen_ids:
                    continue
                if review_id:
                    seen_ids.add(review_id)

                collected.append(
                    {
                        "review_id": review_id,
                        "review": (review.get("content") or "").strip(),
                        "rating": review.get("score"),
                        "date": review.get("at"),
                        "bank": app.bank_name,
                        "app_name": app.display_name,
                        "source": SOURCE,
                    }
                )

                if len(collected) >= min_reviews:
                    break

            if continuation_token is None:
                break

            time.sleep(pause_seconds)

        if len(collected) >= min_reviews:
            break

    return collected


def scrape_all_banks(
    *,
    min_reviews_per_bank: int = MIN_REVIEWS_PER_BANK,
    lang: str = DEFAULT_LANG,
    country: str = DEFAULT_COUNTRY,
) -> pd.DataFrame:
    """Scrape reviews for all configured bank apps and return a combined DataFrame."""
    all_rows: list[dict[str, Any]] = []

    for app in BANK_APPS:
        print(f"Scraping {app.display_name} ({app.package_id})...")
        rows = fetch_reviews_for_app(
            app,
            min_reviews=min_reviews_per_bank,
            lang=lang,
            country=country,
        )
        print(f"  Collected {len(rows)} reviews for {app.bank_name}")
        all_rows.extend(rows)
        time.sleep(2.0)

    return pd.DataFrame(all_rows)
