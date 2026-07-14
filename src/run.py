# Runs the full project in order: download -> pipeline (ETL) -> demo (indexing)

from config import get_logger
import download
from pipeline import run_pipeline
from demo import run_demo

logger = get_logger("run")

if __name__ == "__main__":
    logger.info("STEP 1/3: Download")
    download.download_reviews()
    download.download_metadata()

    logger.info("STEP 2/3: Pipeline (extract, transform, load)")
    run_pipeline()

    logger.info("STEP 3/3: Demo (indexing before/after)")
    run_demo()

    logger.info("Run finished")