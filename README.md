# Amazon Office Products: B2B Purchase & Review Analytics Pipeline

An end-to-end ETL and SQL analytics project built on Amazon's own Office
Products review data, focused on B2B / business-buyer purchasing patterns.

## What this project demonstrates
- ETL: extract, clean, feature-engineer, and load into a relational database
- SQL: schema design, joins, aggregations, business-focused queries
- Indexing: measured before/after query performance using EXPLAIN QUERY PLAN
- Config-driven design: no hardcoded paths, everything set via .env

## Dataset
Amazon Reviews 2023 (McAuley Lab), Office_Products category, sampled to
~1.5M reviews. https://amazon-reviews-2023.github.io/

## Project structure
```
amazon-b2b-analysis/
├── data/                  # raw + processed data (gitignored)
├── logs/                  # pipeline.log output (gitignored)
├── sql/
│   ├── schema.sql          # documented table structure
│   └── queries.sql         # business insight queries
├── src/
│   ├── config.py           # loads .env, shared by every script
│   ├── download.py         # pulls raw data from Hugging Face
│   ├── extract.py          # reads raw parquet files
│   ├── transform.py        # clean, dedupe, sample, engineer features
│   ├── load.py             # writes cleaned data into SQLite
│   ├── pipeline.py         # orchestrates extract -> transform -> load
│   ├── demo.py             # before/after indexing performance test
│   └── run.py              # runs download -> pipeline -> demo in order
├── .env                    # environment variables (category, paths, etc.)
├── .gitignore
└── requirements.txt
```

## Architecture
Linear, single-machine batch pipeline — not distributed or streaming:
```
download.py  -->  extract.py  -->  transform.py  -->  load.py
  (Hugging Face)     (read parquet)   (clean/engineer)   (write SQLite)
                                          |
                                    pipeline.py orchestrates the 3 steps above
                                          |
                                    demo.py measures indexing impact after load
```
This design is appropriate for ~1.5M rows on a laptop. It does **not**
scale to distributed processing — a production version of this at 100M+
rows would need chunked/streaming reads and a tool like Spark or an
Airflow-orchestrated batch job instead of loading everything into pandas
in memory.

## Feature engineering
`transform.py` derives the following columns from raw review data:

| Feature | Derivation | Purpose |
|---|---|---|
| `review_year`, `review_month` | Parsed from `review_date` | Time-based trend queries |
| `review_length` | Character count of review text | Engagement/effort proxy |
| `is_positive` | `rating >= 4` | Binary satisfaction metric |
| `mentions_b2b_context` | Regex match on business/bulk keywords in review text | Core B2B signal for this project's analysis angle |
| `is_review_length_outlier`, `is_helpful_vote_outlier` | IQR method (1.5x IQR beyond Q1/Q3) | Flags extreme values without deleting data |
| `is_price_outlier` (on `dim_products`) | Same IQR method, applied to price | Flags placeholder/junk prices (e.g. $0.01, $9999) |

`mentions_b2b_context` is a **naive keyword regex**, not NLP — it will
have false positives (e.g. "great for my home office" reads the same as
"we bulk-ordered 50 for the team"). This is a known, stated limitation,
not an oversight — a real next step would be a proper text classifier.

## Data quality handling
**Missing values:**
- Rows missing `rating`, `asin`, `user_id`, or `timestamp` are dropped —
  logged as an exact count each run (these fields are non-negotiable;
  a review without them isn't usable)
- Missing `price` in product metadata is **not dropped** — it's counted
  and logged, then left as `NULL`. Dropping would lose the review data
  attached to that product; SQL aggregates (`AVG`, etc.) naturally
  exclude `NULL` on their own

**Duplicates:** rows with identical `(user_id, asin, timestamp)` are
treated as duplicate submissions and dropped, logged as a count. This is
a heuristic, not a guarantee — two genuinely different reviews submitted
in the same millisecond by the same user would incorrectly collide (rare
in practice, but worth naming as a limitation).

**Outliers:** detected using the IQR method (values beyond 1.5x the
interquartile range) on `review_length`, `helpful_vote`, and `price`.
These are **flagged, not removed or capped** — the reasoning is that a
genuinely long, detailed review or a viral review with thousands of
helpful votes is real signal, not noise. Deleting it would bias the
dataset. Flagging lets a downstream SQL query decide whether to include
or exclude them (`WHERE is_helpful_vote_outlier = 0`, for example).

**Sampling:** when the dataset exceeds `TARGET_ROWS`, sampling is
stratified by `rating` so the original rating distribution is preserved
in the smaller sample rather than skewed by whatever a plain random
slice happens to grab.

## Known limitations
- No chunked/streaming reads — everything loads fully into pandas memory
- No dtype optimization (e.g. downcasting `rating` from float64) —
  acceptable at this scale, would matter at 10x the size
- `mentions_b2b_context` is regex-based, not a trained classifier
- SQLite is single-file/single-writer — fine for a portfolio project,
  not a production-grade concurrent-write database
- Outlier bounds (1.5x IQR) are a standard statistical default, not
  tuned against this specific dataset's distribution

## How to run
```bash
pip install -r requirements.txt
python src/download.py
python src/pipeline.py
python src/demo.py
```
Or run all three in sequence with:
```bash
python src/run.py
```

## Configuration
All settings live in `.env`, loaded through `config.py`:

| Variable | Purpose | Default |
|---|---|---|
| `CATEGORY` | Amazon Reviews 2023 category to pull | `Office_Products` |
| `TARGET_ROWS` | Row count to sample down to | `1500000` |
| `RANDOM_SEED` | Seed for reproducible sampling | `42` |
| `RAW_DATA_DIR` | Where raw parquet files are saved | `data/raw` |
| `DB_PATH` | SQLite database location | `data/office_products.db` |
| `LOG_DIR` | Where pipeline.log is written | `logs` |

Changing `CATEGORY` (e.g. to `Home_and_Kitchen`) re-runs the entire
pipeline against a different product category with no code changes.

## Logs
Every script logs to both the console and `logs/pipeline.log`, including
row counts dropped at each cleaning step, date ranges found, and query
timings — a full audit trail of what the pipeline did on each run.

## Resume bullets generated by this project
- Built an end-to-end ETL pipeline processing 1.5M+ Amazon product reviews
  using Python and SQL, loading into a normalized relational database
- Designed a config-driven pipeline (.env-based) enabling the same codebase
  to process any Amazon Reviews 2023 category without code changes
- Measured and improved SQL query performance through targeted indexing,
  verified with EXPLAIN QUERY PLAN, achieving significant speedups on
  high-frequency lookup queries
- Wrote business-focused SQL analyses identifying purchasing and
  satisfaction patterns among business/bulk buyers

## Next steps (optional extensions)
- Pull results into Excel: pivot tables + a macro for a monthly report
- Build a Tableau dashboard: rating trends, price tier vs. satisfaction
- Swap SQLite for Postgres for a closer-to-production setup