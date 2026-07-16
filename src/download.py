# Downloads reviews + metadata for the configured category from Hugging Face
# Reviews are streamed and capped at DOWNLOAD_LIMIT, since a full category
# can run several GB and we only need enough rows to reach TARGET_ROWS
# after cleaning and sampling in transform.py

import os
import pandas as pd
from datasets import load_dataset
from config import CATEGORY, RAW_DATA_DIR, DOWNLOAD_LIMIT, get_logger

logger = get_logger("download")


def download_reviews():
    # stream reviews and stop once we have enough rows, instead of pulling
    # the entire category file (some categories are several GB)
    logger.info(f"Streaming reviews for category: {CATEGORY} (limit: {DOWNLOAD_LIMIT:,})")
    stream = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_review_{CATEGORY}",
        split="full",
        trust_remote_code=True,
        streaming=True,
    )

    rows = []
    for i, example in enumerate(stream):
        if i >= DOWNLOAD_LIMIT:
            break
        rows.append(example)
        if (i + 1) % 100_000 == 0:
            logger.info(f"  streamed {i + 1:,} reviews so far")

    reviews = pd.DataFrame(rows)
    out_path = os.path.join(RAW_DATA_DIR, "reviews.parquet")
    reviews.to_parquet(out_path)
    logger.info(f"Saved {len(reviews):,} reviews -> {out_path}")


META_FIELDS = ["parent_asin", "title", "main_category", "average_rating", "rating_number", "price", "store"]


def download_metadata():
    # stream metadata and keep only the fields transform.py actually uses -
    # the raw metadata includes heavy nested fields (images, videos,
    # description, details) that are slow to deserialize and thrown away
    # later anyway, so we drop them per-row instead of loading them at all
    logger.info(f"Streaming product metadata for category: {CATEGORY}")
    stream = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_meta_{CATEGORY}",
        split="full",
        trust_remote_code=True,
        streaming=True,
    )

    rows = []
    for i, example in enumerate(stream):
        rows.append({field: example.get(field) for field in META_FIELDS})
        if (i + 1) % 100_000 == 0:
            logger.info(f"  streamed {i + 1:,} products so far")

    meta = pd.DataFrame(rows)
    out_path = os.path.join(RAW_DATA_DIR, "metadata.parquet")
    meta.to_parquet(out_path)
    logger.info(f"Saved {len(meta):,} products -> {out_path}")


if __name__ == "__main__":
    download_reviews()
    download_metadata()
    logger.info("Download complete")