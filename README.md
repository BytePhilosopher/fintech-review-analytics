# Fintech Review Analytics

Analysis of Google Play Store user reviews for Ethiopian bank mobile applications. This repository supports a data pipeline from web scraping through NLP, database storage, and visualization (Tasks 1–4).

## Task 1: Data Collection & Preprocessing

### Banks & Apps Scraped

| Bank | App Name | Package ID |
|------|----------|------------|
| Commercial Bank of Ethiopia | Commercial Bank of Ethiopia Mobile | `com.combanketh.mobilebanking` |
| Dashen Bank | Dashen Bank Super App | `com.dashen.dashensuperapp` |
| Bank of Abyssinia | BoA Mobile | `com.boa.boaMobileBanking` |

### Scraping Methodology

- **Library:** [google-play-scraper](https://github.com/JoMingyu/google-play-scraper) (Python)
- **Fields collected:** review text, rating (1–5), review date, bank name, source (`Google Play`), plus `review_id` for deduplication
- **Sort order:** `NEWEST` first; falls back to `MOST_RELEVANT` if needed
- **Locale:** `lang=en`, `country=us` (Google Play returns the same review pool for `et`/`gb` in testing)
- **Batch size:** 200 reviews per API request, with 1–2 second pauses between requests to reduce rate-limit risk
- **Target:** 400+ reviews per bank (1,200 total)

### Date Range

Reviews are returned in reverse chronological order (newest first). The effective date range is **whatever the Play Store exposes for each app**—typically from app launch through the scrape date (**2026-05-17**). No manual start/end date filter is applied; pagination continues until 400 unique reviews per bank are collected.

### Limitations

| Issue | Detail |
|-------|--------|
| **Awash Bank unavailable** | *Awash-Online* (`pegasus.project.awash.mobile.android.bundle.mobilebank`) exposes only **~128 reviews** via the Google Play API (pagination returns empty batches after the first page). A broader date range cannot increase this count. **Bank of Abyssinia (BoA Mobile)** was substituted as the third bank to meet the 400-review minimum. |
| **API caps** | `google-play-scraper` may not return every review listed on the Play Store web UI. |
| **Language** | Reviews are fetched with `lang=en`; Amharic-only reviews may be underrepresented. |

### Preprocessing

Script: `scripts/preprocess_reviews.py` (logic in `src/preprocess.py`)

1. **Deduplicate** on `review_id`
2. **Drop** rows missing review text or rating
3. **Normalize** dates to `YYYY-MM-DD`
4. **Validate** ratings are integers 1–5
5. **Output columns:** `review`, `rating`, `date`, `bank`, `source`

**Latest run stats:**

| Metric | Value |
|--------|-------|
| Raw reviews | 1,200 |
| Clean reviews | 1,200 |
| Missing data removed | 0.0% |
| Per bank | 400 each |

Output files (gitignored):

- `data/raw/reviews_raw.csv`
- `data/processed/reviews_clean.csv`

### Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/scrape_reviews.py
python scripts/preprocess_reviews.py
pytest tests/ -v
```

### Project Structure

```
fintech-review-analytics/
├── .github/workflows/unittests.yml   # CI on push to main
├── data/                             # gitignored (raw + processed CSVs)
├── scripts/                          # scrape & preprocess entry points
├── src/                              # scraper, preprocessor, config
├── tests/                            # unit tests
├── notebooks/                        # exploratory analysis (later tasks)
└── requirements.txt
```

### CI/CD

GitHub Actions workflow `.github/workflows/unittests.yml` installs dependencies and runs `pytest` on every push to `main`.

## License

Educational use — 10 Academy Week 2 challenge.
