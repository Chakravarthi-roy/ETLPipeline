from config import get_logger
from extract import extract
from transform import transform
from load import load

logger = get_logger("pipeline")


def run_pipeline():
    reviews, meta = extract()
    reviews, meta = transform(reviews, meta)
    load(reviews, meta)
    logger.info(f"Summary: fact_reviews={len(reviews):,} rows | dim_products={len(meta):,} rows")


if __name__ == "__main__":
    run_pipeline()