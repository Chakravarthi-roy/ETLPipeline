# Central configuration, loaded from .env, shared by every script

import os
import logging
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CATEGORY = os.getenv("CATEGORY", "Office_Products")
TARGET_ROWS = int(os.getenv("TARGET_ROWS", 1_500_000))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))

RAW_DATA_DIR = os.path.join(BASE_DIR, os.getenv("RAW_DATA_DIR", "data/raw"))
DB_PATH = os.path.join(BASE_DIR, os.getenv("DB_PATH", "data/office_products.db"))
LOG_DIR = os.path.join(BASE_DIR, os.getenv("LOG_DIR", "logs"))

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name):
    # returns a logger that writes to both console and logs/pipeline.log
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(os.path.join(LOG_DIR, "pipeline.log"))
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger