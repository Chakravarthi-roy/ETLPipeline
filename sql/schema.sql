-- Documents the relational structure created by src/pipeline.py
-- SQLite infers types on load; this file is the human-readable reference

CREATE TABLE dim_products (
    parent_asin      TEXT PRIMARY KEY,
    product_title    TEXT,
    main_category    TEXT,
    average_rating   REAL,
    rating_number    INTEGER,
    price            REAL,
    store            TEXT,
    is_price_outlier BOOLEAN
);

CREATE TABLE fact_reviews (
    rating                    REAL,
    title                     TEXT,
    text                      TEXT,
    asin                      TEXT,
    parent_asin               TEXT REFERENCES dim_products(parent_asin),
    user_id                   TEXT,
    verified_purchase         BOOLEAN,
    helpful_vote              INTEGER,
    review_date               TIMESTAMP,
    review_year               INTEGER,
    review_month              INTEGER,
    review_length             INTEGER,
    is_positive               BOOLEAN,
    mentions_b2b_context      BOOLEAN,
    is_review_length_outlier  BOOLEAN,
    is_helpful_vote_outlier   BOOLEAN
);