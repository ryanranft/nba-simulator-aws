#!/usr/bin/env python3
"""
ESPN NBA Game ID Decoder

Decodes ESPN game IDs and schedule IDs to extract date information for year-based partitioning.

Two formats:
1. Schedule IDs: YYYYMMDD (simple date format)
   - Example: 19961219 → December 19, 1996

2. Game IDs: YYMMDD### (encoded with 1980 offset)
   - YY: Year code (1980 offset for pre-2018 games)
   - MM: Month (01-12)
   - DD: Day (01-31)
   - ###: Additional sequence digits
   - Examples:
     - 171031017 → Oct 31, 1997 (Year 17 = 1980 + 17 = 1997)
     - 200104005 → Jan 4, 2000 (Year 20 = 1980 + 20 = 2000)
     - 311011004 → Jan 1, 2011 (Year 31 = 1980 + 31 = 2011)
     - 401307856 → 2021 (401 format - different encoding)

Author: Ryan Ranft
Date: 2025-10-01
Phase: 2.2 - ETL Development
"""

from datetime import datetime
from typing import Optional, Tuple
import re


def decode_game_id(game_id: str) -> Optional[dict]:
    """
    Decode ESPN game ID or schedule ID to extract year, month, day.

    Args:
        game_id: ESPN game ID or schedule ID
                 - Schedule: "19961219" (YYYYMMDD)
                 - Game: "171031017" (YYMMDD###)
                 - Game: "401307856" (401 format)

    Returns:
        dict with keys: year, month, day, season, game_date
        None if unable to parse

    Examples:
        >>> decode_game_id("19961219")
        {'year': 1996, 'month': 12, 'day': 19, 'season': '1996-97',
         'game_date': '1996-12-19', 'format': 'schedule'}

        >>> decode_game_id("171031017")
        {'year': 1997, 'month': 10, 'day': 31, 'season': '1997-98',
         'game_date': '1997-10-31', 'format': 'standard'}

        >>> decode_game_id("401307856")
        {'year': 2021, 'month': None, 'day': None, 'season': '2020-21',
         'game_date': None, 'format': '401'}
    """
    if not game_id or not isinstance(game_id, str):
        return None

    # Remove .json extension if present
    game_id = game_id.replace(".json", "")

    # Try schedule format first (YYYYMMDD - 8 digits exactly)
    if len(game_id) == 8 and game_id.isdigit():
        result = _decode_schedule_format(game_id)
        if result:
            return result

    # Try 401 format (2018+)
    if game_id.startswith("401"):
        return _decode_401_format(game_id)

    # Try standard YYMMDD### format (pre-2018)
    return _decode_standard_format(game_id)


def _decode_standard_format(game_id: str) -> Optional[dict]:
    """Decode pre-2018 format: YYMMDD###"""

    # Must be at least 8 digits (YYMMDD + at least 2 sequence digits)
    if len(game_id) < 8 or not game_id.isdigit():
        return None

    try:
        # Extract components
        year_code = int(game_id[0:2])
        month = int(game_id[2:4])
        day = int(game_id[4:6])

        # Validate month and day
        if not (1 <= month <= 12) or not (1 <= day <= 31):
            return None

        # Calculate actual year (1980 offset)
        year = 1980 + year_code

        # Validate year range (NBA founded 1946, data starts ~1997)
        if year < 1990 or year > 2025:
            return None

        # Determine NBA season (Oct-Jun spans two years)
        # If game is Oct-Dec, it's the YYYY-YY+1 season
        # If game is Jan-Jun, it's the YYYY-1-YYYY season
        if month >= 10:  # Oct, Nov, Dec
            season = f"{year}-{str(year + 1)[-2:]}"
        else:  # Jan-Sep
            season = f"{year - 1}-{str(year)[-2:]}"

        # Format game date
        game_date = f"{year:04d}-{month:02d}-{day:02d}"

        return {
            "year": year,
            "month": month,
            "day": day,
            "season": season,
            "game_date": game_date,
            "format": "standard",
        }

    except (ValueError, IndexError):
        return None


def _decode_schedule_format(schedule_id: str) -> Optional[dict]:
    """Decode schedule format: YYYYMMDD (exactly 8 digits)"""

    if len(schedule_id) != 8 or not schedule_id.isdigit():
        return None

    try:
        year = int(schedule_id[0:4])
        month = int(schedule_id[4:6])
        day = int(schedule_id[6:8])

        # Validate date components
        if not (1 <= month <= 12) or not (1 <= day <= 31):
            return None

        # Validate year range
        if year < 1990 or year > 2030:
            return None

        # Determine NBA season
        if month >= 10:  # Oct, Nov, Dec
            season = f"{year}-{str(year + 1)[-2:]}"
        else:  # Jan-Sep
            season = f"{year - 1}-{str(year)[-2:]}"

        # Format game date
        game_date = f"{year:04d}-{month:02d}-{day:02d}"

        return {
            "year": year,
            "month": month,
            "day": day,
            "season": season,
            "game_date": game_date,
            "format": "schedule",
        }

    except (ValueError, IndexError):
        return None


def _decode_401_format(game_id: str) -> Optional[dict]:
    """
    Decode 2018+ format: 401######

    Note: Exact year encoding for 401 format is unknown.
    Using heuristic: 401 games are from 2018-2025 era.

    Future enhancement: Reverse engineer exact year from game_id digits.
    """
    if not game_id.startswith("401") or len(game_id) < 9:
        return None

    try:
        # Extract digits after 401 prefix
        remaining = game_id[3:]

        # Heuristic: First 1-2 digits after 401 might encode year offset
        # 401307856 appears in 2021 data
        # Need more examples to confirm pattern

        # For now, estimate based on known examples
        # This is a placeholder - user can provide more examples to refine
        first_digit = int(remaining[0])

        # Rough estimate (needs refinement with more data):
        # 4013##### → 2021
        # 4014##### → 2022
        # 4015##### → 2023
        # etc.

        if first_digit == 3:
            year = 2021
        elif first_digit == 4:
            year = 2022
        elif first_digit == 5:
            year = 2023
        else:
            # Default to 2020 if unknown
            year = 2020

        # Determine season
        season = f"{year - 1}-{str(year)[-2:]}"

        return {
            "year": year,
            "month": None,  # Cannot extract from 401 format yet
            "day": None,
            "season": season,
            "game_date": None,
            "format": "401",
            "note": "Year estimated - 401 format decoding incomplete",
        }

    except (ValueError, IndexError):
        return None


def extract_year_from_filename(filename: str) -> Optional[int]:
    """
    Extract year from game ID filename.

    Args:
        filename: S3 key or local path (e.g., "s3://bucket/pbp/171031017.json")

    Returns:
        Year as integer, or None if unable to parse

    Examples:
        >>> extract_year_from_filename("171031017.json")
        1997

        >>> extract_year_from_filename("s3://bucket/pbp/401307856.json")
        2021
    """
    # Extract just the filename
    filename = filename.split("/")[-1]
    filename = filename.replace(".json", "")

    result = decode_game_id(filename)
    return result["year"] if result else None


def get_season_from_game_id(game_id: str) -> Optional[str]:
    """
    Get NBA season from game ID.

    Args:
        game_id: ESPN game ID

    Returns:
        Season string (e.g., "2020-21") or None

    Examples:
        >>> get_season_from_game_id("171031017")
        '1997-98'

        >>> get_season_from_game_id("200104005")
        '1999-00'
    """
    result = decode_game_id(game_id)
    return result["season"] if result else None


# PySpark UDF-compatible version
def decode_game_id_udf(game_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Spark UDF version - returns (year, season) tuple for DataFrame use.

    Usage in PySpark:
        from pyspark.sql.functions import udf
        from pyspark.sql.types import StructType, StructField, IntegerType, StringType

        schema = StructType([
            StructField("year", IntegerType(), True),
            StructField("season", StringType(), True)
        ])

        decode_udf = udf(decode_game_id_udf, schema)

        df = df.withColumn("decoded", decode_udf(col("game_id")))
        df = df.withColumn("year", col("decoded.year"))
        df = df.withColumn("season", col("decoded.season"))
    """
    result = decode_game_id(game_id)
    if result:
        return (result["year"], result["season"])
    else:
        return (None, None)


if __name__ == "__main__":
    # Test examples
    test_cases = [
        # Schedule IDs (YYYYMMDD format)
        "19961219",  # Dec 19, 1996 (schedule)
        "20001031",  # Oct 31, 2000 (schedule)
        "20211012",  # Oct 12, 2021 (schedule)
        # Game IDs (YYMMDD### format with 1980 offset)
        "171031017",  # Oct 31, 1997
        "171101024",  # Nov 1, 1997
        "190205001",  # Feb 5, 1999
        "190206002",  # Feb 6, 1999
        "191103005",  # Nov 3, 1999
        "200103002",  # Jan 3, 2000
        "200104005",  # Jan 4, 2000
        "201031017",  # Oct 31, 2000
        "210102005",  # Jan 2, 2001
        "210103015",  # Jan 3, 2001
        "281028002",  # Oct 28, 2008
        "281030005",  # Oct 30, 2008
        "291027005",  # Oct 27, 2009
        "300102017",  # Jan 2, 2010
        "311011004",  # Oct 11, 2011
        # 401 format (2018+)
        "401307856",  # 2021 (401 format)
    ]

    print("ESPN Game ID Decoder - Test Results")
    print("=" * 80)
    print(
        f"{'Game ID':<15} {'Year':<6} {'Month':<7} {'Day':<5} {'Season':<10} {'Game Date':<12}"
    )
    print("-" * 80)

    for game_id in test_cases:
        result = decode_game_id(game_id)
        if result:
            year = result["year"]
            month = result.get("month") or "N/A"
            day = result.get("day") or "N/A"
            season = result["season"]
            game_date = result.get("game_date") or "N/A"
            print(
                f"{game_id:<15} {year:<6} {str(month):<7} "
                f"{str(day):<5} {season:<10} {game_date:<12}"
            )
        else:
            print(f"{game_id:<15} ERROR: Unable to decode")

    print("\n" + "=" * 80)
    print("Test complete!")
