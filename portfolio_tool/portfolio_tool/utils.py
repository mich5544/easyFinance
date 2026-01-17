from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

LOGGER_NAME = "portfolio_tool"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def normalize_tickers(raw: str | Iterable[str]) -> List[str]:
    if isinstance(raw, str):
        parts = [p.strip().upper() for p in raw.split(",")]
    else:
        parts = [str(p).strip().upper() for p in raw]
    return [p for p in parts if p]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
