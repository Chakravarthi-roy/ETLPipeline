# Transform step: clean, dedupe, sample, and engineer features on raw data

import pandas as pd
from config import TARGET_ROWS, RANDOM_SEED, get_logger

logger = get_logger("transform")


def select_columns(reviews):
    # keep only the fields the pipeline actually uses
    return reviews[[
        "rating", "title", "text", "asin", "parent_asin", "user_id",
        "timestamp", "verified_purchase", "helpful_vote"
    ]].copy()


def drop_missing_essentials(reviews):
    # a review with no rating, product id, user, or timestamp is unusable
    before = len(reviews)
    reviews = reviews.dropna(subset=["rating", "asin", "user_id", "timestamp"])
    logger.info(f"Dropped {before - len(reviews):,} rows with missing essential fields")
    return reviews


def drop_duplicates(reviews):
    # same user, same product, same timestamp = treat as a duplicate submission
    before = len(reviews)
    reviews = reviews.drop_duplicates(subset=["user_id", "asin", "timestamp"])
    logger.info(f"Dropped {before - len(reviews):,} duplicate rows")
    return reviews


def convert_timestamp(reviews):
    # dataset stores time as milliseconds since epoch, per the dataset card
    reviews["review_date"] = pd.to_datetime(reviews["timestamp"], unit="ms")
    reviews = reviews.drop(columns=["timestamp"])
    logger.info(f"Date range: {reviews['review_date'].min()} to {reviews['review_date'].max()}")
    return reviews


def engineer_features(reviews):
    # basic time features for trend analysis
    reviews["review_year"] = reviews["review_date"].dt.year
    reviews["review_month"] = reviews["review_date"].dt.month

    # review length as a simple engagement/effort signal
    reviews["review_length"] = reviews["text"].fillna("").str.len()

    # 4 or 5 star rating counts as a positive review
    reviews["is_positive"] = reviews["rating"] >= 4

    # naive keyword heuristic flagging business/bulk-purchase context
    # this is a regex match, not NLP - expect false positives
    b2b_keywords = r"\b(?:office|bulk|business|team|work|company|reorder|wholesale)\b"
    reviews["mentions_b2b_context"] = (
        reviews["text"].fillna("").str.lower().str.contains(b2b_keywords, regex=True)
    )

    logger.info(f"Flagged {reviews['mentions_b2b_context'].sum():,} reviews with B2B context keywords")
    return reviews


def flag_outliers(reviews):
    # IQR method: flag values far outside the normal range, don't drop them
    # dropping would silently discard real data (e.g. a genuinely long, detailed review)
    # flagging lets an analyst choose to include/exclude them later in SQL
    for col in ["review_length", "helpful_vote"]:
        q1 = reviews[col].quantile(0.25)
        q3 = reviews[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        flag_col = f"is_{col}_outlier"
        reviews[flag_col] = (reviews[col] < lower) | (reviews[col] > upper)

        flagged_count = reviews[flag_col].sum()
        logger.info(f"{col}: normal range [{lower:.1f}, {upper:.1f}], flagged {flagged_count:,} outliers")

    return reviews


def stratified_sample(reviews):
    # sample down to TARGET_ROWS while preserving the rating distribution
    if len(reviews) <= TARGET_ROWS:
        logger.info("Dataset already at or below target size, skipping sampling")
        return reviews

    frac = TARGET_ROWS / len(reviews)
    reviews = (
        reviews.groupby("rating", group_keys=False)
        .apply(lambda x: x.sample(frac=frac, random_state=RANDOM_SEED))
    )
    logger.info(f"Sampled down to {len(reviews):,} rows (stratified by rating)")
    return reviews


def clean_metadata(meta):
    # keep only the product fields needed for joins and analysis
    meta = meta[[
        "parent_asin", "title", "main_category", "average_rating",
        "rating_number", "price", "store"
    ]].copy()
    meta = meta.rename(columns={"title": "product_title"})
    meta["price"] = pd.to_numeric(meta["price"], errors="coerce")

    # log how many products have no usable price, instead of letting it
    # silently disappear from AVG()/GROUP BY in downstream SQL
    null_price_count = meta["price"].isna().sum()
    logger.info(f"{null_price_count:,} products have missing/unparseable price")

    # IQR outlier flag on price - Amazon listings sometimes have $0.01 or
    # $9,999 placeholder prices that would badly skew a naive average
    valid_prices = meta["price"].dropna()
    q1 = valid_prices.quantile(0.25)
    q3 = valid_prices.quantile(0.75)
    iqr = q3 - q1
    lower = max(0, q1 - 1.5 * iqr)
    upper = q3 + 1.5 * iqr
    meta["is_price_outlier"] = (meta["price"] < lower) | (meta["price"] > upper)
    logger.info(f"Price normal range: [{lower:.2f}, {upper:.2f}], "
                f"flagged {meta['is_price_outlier'].sum():,} outlier prices")

    before = len(meta)
    meta = meta.drop_duplicates(subset=["parent_asin"])
    logger.info(f"Dropped {before - len(meta):,} duplicate product rows")
    return meta


def transform(reviews, meta):
    logger.info("Cleaning reviews")
    reviews = select_columns(reviews)
    reviews = drop_missing_essentials(reviews)
    reviews = drop_duplicates(reviews)
    reviews = convert_timestamp(reviews)
    reviews = engineer_features(reviews)
    reviews = flag_outliers(reviews)
    reviews = stratified_sample(reviews)

    logger.info("Cleaning product metadata")
    meta = clean_metadata(meta)

    return reviews, meta