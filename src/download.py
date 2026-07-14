# Downloads reviews + metadata for the configured category from Hugging Face

import os
from datasets import load_dataset
from config import CATEGORY, RAW_DATA_DIR, get_logger

logger = get_logger("download_data")


def download_reviews():
    # pull the review-level data for this category
    logger.info(f"Downloading reviews for category: {CATEGORY}")
    reviews = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_review_{CATEGORY}",
        trust_remote_code=True,
    )["full"]

    out_path = os.path.join(RAW_DATA_DIR, "reviews.parquet")
    reviews.to_parquet(out_path)
    logger.info(f"Saved {len(reviews):,} reviews -> {out_path}")


def download_metadata():
    # pull the product-level metadata for this category
    logger.info(f"Downloading product metadata for category: {CATEGORY}")
    meta = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_meta_{CATEGORY}",
        split="full",
        trust_remote_code=True,
    )

    out_path = os.path.join(RAW_DATA_DIR, "metadata.parquet")
    meta.to_parquet(out_path)
    logger.info(f"Saved {len(meta):,} products -> {out_path}")


if __name__ == "__main__":
    download_reviews()
    download_metadata()
    logger.info("Download complete")