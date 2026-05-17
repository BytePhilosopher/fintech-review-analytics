# Scripts

| Script | Description |
|--------|-------------|
| `scrape_reviews.py` | Scrape Google Play reviews for three bank apps → `data/raw/reviews_raw.csv` |
| `preprocess_reviews.py` | Clean and normalize raw reviews → `data/processed/reviews_clean.csv` |

Run from the project root:

```bash
python scripts/scrape_reviews.py
python scripts/preprocess_reviews.py
```
