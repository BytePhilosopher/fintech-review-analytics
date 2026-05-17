# Scripts

| Script | Description |
|--------|-------------|
| `scrape_reviews.py` | Scrape Google Play reviews for three bank apps → `data/raw/reviews_raw.csv` |
| `preprocess_reviews.py` | Clean and normalize raw reviews → `data/processed/reviews_clean.csv` |
| `analyze_reviews.py` | Sentiment + thematic analysis → `data/processed/reviews_analyzed.csv` |
| `load_to_postgres.py` | Load enriched reviews into PostgreSQL |
| `verify_db.py` | Run integrity verification SQL queries |

Run from the project root:

```bash
python scripts/scrape_reviews.py
python scripts/preprocess_reviews.py
```
