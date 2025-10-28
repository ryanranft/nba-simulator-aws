"""
Centralized Logging Configuration

Provides consistent logging across all modules with:
- File and console output
- Configurable log levels
- Rotation to prevent disk fill
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    name: str = "nba_simulator",
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: project_root/logs)
        console: Enable console output
        file: Enable file output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if file:
        if log_dir is None:
            # Default to project_root/logs
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "logs"

        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{name}.log"

        # Rotate when file reaches 10MB, keep 5 backups
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Default logger instance
logger = setup_logging()

