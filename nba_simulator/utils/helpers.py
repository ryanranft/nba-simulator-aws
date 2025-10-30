"""
Helper Utilities

Common helper functions for file operations, timestamps, and formatting.
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Union


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists (create if necessary).

    Args:
        path: Directory path

    Returns:
        Path object for the directory

    Example:
        data_dir = ensure_dir("data/raw")
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S", use_utc: bool = False) -> str:
    """
    Get formatted timestamp string.

    Args:
        fmt: Timestamp format (default: YYYY-MM-DD HH:MM:SS)
        use_utc: If True, use UTC; if False, use local time

    Returns:
        Formatted timestamp string

    Example:
        ts = get_timestamp()  # "2025-10-29 19:45:30"
    """
    if use_utc:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now()

    return dt.strftime(fmt)


def parse_timestamp(timestamp_str: str, fmt: Optional[str] = None) -> datetime:
    """
    Parse timestamp string to datetime object.

    Args:
        timestamp_str: Timestamp string
        fmt: Format string (default: auto-detect ISO format)

    Returns:
        datetime object

    Example:
        dt = parse_timestamp("2025-10-29T19:45:30")
    """
    if fmt:
        return datetime.strptime(timestamp_str, fmt)
    else:
        # Try ISO format first
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Try common formats
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%m/%d/%Y",
            ]:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue

            raise ValueError(f"Unable to parse timestamp: {timestamp_str}")


def format_number(
    num: Union[int, float], decimals: int = 0, use_comma: bool = True
) -> str:
    """
    Format number with commas and optional decimals.

    Args:
        num: Number to format
        decimals: Number of decimal places
        use_comma: If True, use comma separators

    Returns:
        Formatted number string

    Example:
        formatted = format_number(1234567)  # "1,234,567"
        formatted = format_number(123.456, decimals=2)  # "123.46"
    """
    if decimals > 0:
        formatted = f"{num:.{decimals}f}"
    else:
        formatted = str(int(num))

    if use_comma:
        # Add commas
        parts = formatted.split(".")
        parts[0] = "{:,}".format(int(parts[0]))
        formatted = ".".join(parts)

    return formatted


def get_file_size(path: Union[str, Path]) -> int:
    """
    Get file size in bytes.

    Args:
        path: File path

    Returns:
        File size in bytes
    """
    return Path(path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 GB")

    Example:
        size = format_file_size(1500000000)  # "1.4 GB"
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"
