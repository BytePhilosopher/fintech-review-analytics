-- PostgreSQL schema for bank review analytics (Task 3)
-- Database: bank_reviews

CREATE TABLE IF NOT EXISTS banks (
    bank_id SERIAL PRIMARY KEY,
    bank_name VARCHAR(255) NOT NULL UNIQUE,
    app_name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id VARCHAR(64) PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks (bank_id) ON DELETE CASCADE,
    review_text TEXT NOT NULL,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date DATE NOT NULL,
    sentiment_label VARCHAR(20),
    sentiment_score REAL,
    identified_theme VARCHAR(100),
    source VARCHAR(50) NOT NULL DEFAULT 'Google Play',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reviews_bank_id ON reviews (bank_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews (rating);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews (sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reviews_theme ON reviews (identified_theme);
