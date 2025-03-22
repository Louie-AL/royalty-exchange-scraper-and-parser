# utils.py

import time
import random
import logging

def delay(min_sec=4, max_sec=7):
    time.sleep(random.uniform(min_sec, max_sec))

def setup_logger():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    return logging.getLogger(__name__)
