# Measures query speed before and after adding indexes on fact_reviews

import sqlite3
import time
from config import DB_PATH, get_logger

logger = get_logger("demo")

TEST_QUERIES = [
    {
        "name": "Lookup all reviews for a single product (parent_asin)",
        "sql": "SELECT * FROM fact_reviews WHERE parent_asin = ?",
        "index_sql": "CREATE INDEX idx_reviews_parent_asin ON fact_reviews(parent_asin)",
    },
    {
        "name": "Filter reviews by year and rating (business trend query)",
        "sql": "SELECT COUNT(*) FROM fact_reviews WHERE review_year = 2022 AND rating >= 4",
        "index_sql": "CREATE INDEX idx_reviews_year_rating ON fact_reviews(review_year, rating)",
    },
    {
        "name": "Filter verified purchases mentioning B2B context",
        "sql": "SELECT COUNT(*) FROM fact_reviews WHERE verified_purchase = 1 AND mentions_b2b_context = 1",
        "index_sql": "CREATE INDEX idx_reviews_verified_b2b ON fact_reviews(verified_purchase, mentions_b2b_context)",
    },
]


def get_sample_asin(conn):
    # grab one real parent_asin to use as a lookup parameter
    cur = conn.execute("SELECT parent_asin FROM fact_reviews LIMIT 1")
    return cur.fetchone()[0]


def explain_and_time(conn, sql, params=()):
    # capture the query plan and measure execution time
    cur = conn.cursor()
    plan_rows = cur.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    plan_text = "\n".join(str(row) for row in plan_rows)

    start = time.perf_counter()
    cur.execute(sql, params).fetchall()
    elapsed = time.perf_counter() - start

    return plan_text, elapsed


def run_query_test(conn, query_config, sample_asin):
    # run a query before and after its index exists, then report the difference
    params = (sample_asin,) if "?" in query_config["sql"] else ()

    logger.info(f"Testing: {query_config['name']}")

    plan_before, time_before = explain_and_time(conn, query_config["sql"], params)
    logger.info(f"BEFORE INDEX | {time_before*1000:.2f} ms | plan: {plan_before}")

    try:
        conn.execute(query_config["index_sql"])
        conn.commit()
    except sqlite3.OperationalError as e:
        logger.warning(f"Index may already exist: {e}")

    plan_after, time_after = explain_and_time(conn, query_config["sql"], params)
    logger.info(f"AFTER INDEX  | {time_after*1000:.2f} ms | plan: {plan_after}")

    speedup = time_before / time_after if time_after > 0 else float("inf")
    logger.info(f"Speedup: {speedup:.1f}x")

    return {
        "query": query_config["name"],
        "time_before_ms": time_before * 1000,
        "time_after_ms": time_after * 1000,
        "speedup": speedup,
    }


def run_demo():
    conn = sqlite3.connect(DB_PATH)
    sample_asin = get_sample_asin(conn)

    results = [run_query_test(conn, q, sample_asin) for q in TEST_QUERIES]
    conn.close()

    logger.info("SUMMARY")
    for r in results:
        logger.info(f"{r['query']}: {r['time_before_ms']:.2f}ms -> {r['time_after_ms']:.2f}ms "
                     f"({r['speedup']:.1f}x faster)")


if __name__ == "__main__":
    run_demo()