# Load step: writes cleaned reviews and metadata into SQLite

import sqlite3
from config import DB_PATH, get_logger

logger = get_logger("load")


def load(reviews, meta):
    # write both tables into a SQLite database, replacing if they exist
    logger.info(f"Loading into SQLite database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    meta.to_sql("dim_products", conn, if_exists="replace", index=False)
    reviews.to_sql("fact_reviews", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    logger.info("Load complete")