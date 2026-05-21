"""Logging configuration using loguru."""

import sys
import os
from typing import Optional

from loguru import logger

from src.config import get_settings

settings = get_settings()


def setup_logging():
    """Configure loguru logging based on settings."""

    # Remove default handler
    logger.remove()

    # Get log level from settings
    log_level = settings.LOG_LEVEL.upper()

    # Add console handler with formatting (always works)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Optional: Add file handler for persistent logs (skip if permission denied)
    try:
        # Ensure logs directory exists
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Test write permission
        test_file = os.path.join(log_dir, ".write_test")
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)

        # Add file handler
        logger.add(
            "logs/app.log",
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
        )
        logger.info("File logging enabled: logs/app.log")

    except (PermissionError, OSError) as e:
        logger.warning(f"Could not set up file logging: {e}. Continuing with console logging only.")

    # Suppress noisy third-party libraries
    logger.disable("httpx")
    logger.disable("httpcore")
    logger.disable("urllib3")

    # Bind initial context
    logger.bind(service="food-analyzer")

    logger.info(f"Logging initialized at level {log_level}")

    return logger


def get_logger(name: Optional[str] = None):
    """Get a logger instance with optional context."""
    if name:
        return logger.bind(module=name)
    return logger