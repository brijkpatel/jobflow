"""Logging configuration for the resume parser framework."""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Set up logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Optional custom format string

    Returns:
        Configured logger instance
    """
    # Get log level from environment or use default
    log_level = level or os.getenv("LOG_LEVEL", "INFO")

    # Default format string
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create logger for this package
    logger = logging.getLogger("resume_parser")

    # Add file handler if log file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logging()
