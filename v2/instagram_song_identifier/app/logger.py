# app/logger.py
import logging

def setup_logger(log_level=logging.INFO):
    logger = logging.getLogger(__name__)
    if not logger.handlers:  # Check if handlers are already added
        logger.setLevel(log_level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger