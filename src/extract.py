# Extract step: loads the raw parquet files produced by download.py

import os
import pandas as pd
from config import RAW_DATA_DIR, get_logger

logger = get_logger("extract")


def extract():
    # load the two raw parquet files into memory
    logger.info("Reading raw parquet files")
    reviews = pd.read_parquet(os.path.join(RAW_DATA_DIR, "reviews.parquet"))
    meta = pd.read_parquet(os.path.join(RAW_DATA_DIR, "metadata.parquet"))
    logger.info(f"reviews: {len(reviews):,} rows | metadata: {len(meta):,} rows")
    return reviews, meta


if __name__ == "__main__":
    extract()