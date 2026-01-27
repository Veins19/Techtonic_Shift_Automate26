# -*- coding: utf-8 -*-
"""
Centralized logging configuration for frontend.

Purpose:
- Single source of truth for logging
- Consistent format across all frontend modules
- Easy to extend later (file logs, JSON logs, etc.)
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    logger_name: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        level: Logging level (default: INFO)
        logger_name: Optional logger name. If None, root logger is used.

    Returns:
        Configured logger
    """

    logger = logging.getLogger(logger_name)

    # Prevent duplicate handlers (VERY important in Streamlit)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.propagate = False

    logger.info("Frontend logging initialized")

    return logger
