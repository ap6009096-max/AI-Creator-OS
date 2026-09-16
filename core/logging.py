"""Logging setup for AI Creator OS — structured console and file logging."""

from __future__ import annotations

import logging
from pathlib import Path
import sys

_CONFIGURED = False

LOG_DIR = Path("logs")


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once with structured format, console, app.log and errors.log handlers."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # 2. General App Log File Handler
    app_log_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    app_log_handler.setFormatter(formatter)
    app_log_handler.setLevel(log_level)

    # 3. Errors Log File Handler
    error_log_handler = logging.FileHandler(LOG_DIR / "errors.log", encoding="utf-8")
    error_log_handler.setFormatter(formatter)
    error_log_handler.setLevel(logging.ERROR)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(app_log_handler)
    root.addHandler(error_log_handler)
    root.setLevel(log_level)

    # Keep noisy third-party loggers quieter
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("moviepy").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
