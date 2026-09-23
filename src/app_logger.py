from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config import LOG_PATH, ensure_runtime_dirs


def configure_logging() -> logging.Logger:
    ensure_runtime_dirs()

    logger = logging.getLogger("jam")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1_500_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = configure_logging()
