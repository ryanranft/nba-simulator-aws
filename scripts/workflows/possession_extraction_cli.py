#!/usr/bin/env python3
"""
Phase 0.0005: Possession Extraction - Command Line Interface

CLI tool for extracting basketball possessions from temporal_events table.
Provides flexible options for batch processing, validation, and monitoring.

Usage Examples:
    # Extract all possessions
    python possession_extraction_cli.py

    # Extract specific season
    python possession_extraction_cli.py --season 2024

    # Extract single game
    python possession_extraction_cli.py --game-id 401584893

    # Dry run (validate only, no writes)
    python possession_extraction_cli.py --dry-run --verbose

    # Extract with validation
    python possession_extraction_cli.py --season 2024 --validate --report

Author: NBA Simulator AWS Team
Created: November 5, 2025
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from nba_simulator.etl.extractors.possession.config import load_config

# TODO: Import when implemented
# from docs.phases.phase_0.possession_extraction.possession_extractor import PossessionExtractor
# from docs.phases.phase_0.possession_extraction.dean_oliver_validator import DeanOliverValidator


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Configure logging for CLI.

    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Optional log file path
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)

    logger.info(f"Logging initialized at {'DEBUG' if verbose else 'INFO'} level")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Extract basketball possessions from temporal_events table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all possessions in database
  %(prog)s
  
  # Extract specific season
  %(prog)s --season 2024
  
  # Extract single game with validation
  %(prog)s --game-id 401584893 --validate --verbose
  
  # Extract date range
  %(prog)s --start-date 2024-01-01 --end-date 2024-01-31
  
  # Dry run (validation only)
  %(prog)s --season 2024 --dry-run --report
  
  # Resume interrupted extraction
  %(prog)s --resume --resume-from game_id_123
        """,
    )

    # Input selection
    input_group = parser.add_argument_group("Input Selection")
    input_group.add_argument(
        "--season",
        type=int,
        help="Extract possessions for specific season (e.g., 2024)",
    )
    input_group.add_argument(
        "--game-id", type=str, help="Extract possessions for specific game ID"
    )
    input_group.add_argument(
        "--start-date", type=str, help="Extract possessions from this date (YYYY-MM-DD)"
    )
    input_group.add_argument(
        "--end-date", type=str, help="Extract possessions to this date (YYYY-MM-DD)"
    )
    input_group.add_argument(
        "--team-id", type=int, help="Extract possessions for specific team"
    )

    # Processing options
    process_group = parser.add_argument_group("Processing Options")
    process_group.add_argument(
        "--dry-run", action="store_true", help="Validate only, do not write to database"
    )
    process_group.add_argument(
        "--parallel",
        type=int,
        metavar="N",
        help="Number of games to process in parallel (default: from config)",
    )
    process_group.add_argument(
        "--batch-size",
        type=int,
        metavar="N",
        help="Batch size for database queries (default: from config)",
    )
    process_group.add_argument(
        "--resume", action="store_true", help="Resume from interrupted extraction"
    )
    process_group.add_argument(
        "--resume-from",
        type=str,
        metavar="GAME_ID",
        help="Resume from specific game ID",
    )
    process_group.add_argument(
        "--force", action="store_true", help="Force overwrite existing possessions"
    )

    # Validation options
    validation_group = parser.add_argument_group("Validation Options")
    validation_group.add_argument(
        "--validate",
        action="store_true",
        help="Run Dean Oliver validation on extracted possessions",
    )
    validation_group.add_argument(
        "--validation-only",
        action="store_true",
        help="Only run validation, skip extraction",
    )
    validation_group.add_argument(
        "--tolerance",
        type=float,
        metavar="PCT",
        help="Oliver validation tolerance percentage (default: 5.0)",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--report", action="store_true", help="Generate detailed validation report"
    )
    output_group.add_argument(
        "--report-format",
        choices=["markdown", "json", "csv"],
        default="markdown",
        help="Report format (default: markdown)",
    )
    output_group.add_argument(
        "--output-dir",
        type=str,
        metavar="DIR",
        help="Output directory for reports (default: from config)",
    )
    output_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    output_group.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )
    output_group.add_argument(
        "--log-file", type=str, metavar="FILE", help="Write logs to file"
    )

    # Configuration
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        type=str,
        metavar="FILE",
        help="Path to configuration YAML file (default: config/default_config.yaml)",
    )

    # Diagnostics
    diag_group = parser.add_argument_group("Diagnostics")
    diag_group.add_argument(
        "--diagnose", action="store_true", help="Run diagnostic checks on event data"
    )
    diag_group.add_argument(
        "--profile", action="store_true", help="Profile extraction performance"
    )
    diag_group.add_argument(
        "--check-indexes", action="store_true", help="Verify database indexes exist"
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate argument combinations.

    Args:
        args: Parsed arguments

    Raises:
        ValueError: If argument combination is invalid
    """
    # Check for conflicting options
    if args.dry_run and args.force:
        raise ValueError("Cannot use --dry-run with --force")

    if args.validation_only and args.dry_run:
        raise ValueError("Cannot use --validation-only with --dry-run")

    # Validate date format if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD"
            )

    if args.end_date:
        try:
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD"
            )


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Validate arguments
        validate_arguments(args)

        # Setup logging
        setup_logging(verbose=args.verbose, log_file=args.log_file)
        logger = logging.getLogger(__name__)

        # Load configuration
        logger.info("Loading configuration...")
        if args.config:
            config = load_config(args.config)
        else:
            config = load_config()

        # Override config with CLI arguments
        if args.parallel:
            config.processing.parallel_games = args.parallel
        if args.batch_size:
            config.processing.batch_size = args.batch_size
        if args.tolerance:
            config.validation.oliver_tolerance_pct = args.tolerance

        # Validate configuration
        config.validate()
        config.ensure_directories()

        logger.info(f"Configuration loaded: {config}")

        # Import extractors
        from nba_simulator.etl.extractors.possession import PossessionExtractor
        from nba_simulator.etl.extractors.possession.validator import (
            DeanOliverValidator,
        )

        # Main extraction logic
        logger.info("=" * 70)
        logger.info("Phase 0.0005: Possession Extraction CLI")
        logger.info("=" * 70)

        if args.dry_run:
            logger.info("DRY RUN MODE - No database writes will be performed")
            logger.warning("Dry run mode not fully implemented - exiting")
            return 0

        if args.game_id:
            logger.info(f"Extracting possessions for game: {args.game_id}")
        elif args.season:
            logger.info(f"Extracting possessions for season: {args.season}")
        elif args.start_date and args.end_date:
            logger.info(
                f"Extracting possessions from {args.start_date} to {args.end_date}"
            )
        else:
            logger.info("Extracting possessions for entire database")

        # Initialize extractor
        extractor = PossessionExtractor(config)

        # Connect to database
        if not extractor.connect():
            logger.error("Failed to connect to database")
            return 1

        try:
            # Run extraction
            limit = None  # No limit - extract all games
            resume_from = args.resume_from if args.resume_from else None

            logger.info(f"Starting extraction (resume_from={resume_from})")
            results = extractor.extract_all_games(limit=limit, resume_from=resume_from)

            logger.info("")
            logger.info("=" * 70)
            logger.info("Extraction Results")
            logger.info("=" * 70)
            logger.info(f"Games processed: {results['games_processed']:,}")
            logger.info(f"Games failed: {results['games_failed']:,}")
            logger.info(f"Possessions extracted: {results['possessions_extracted']:,}")
            logger.info(f"Events processed: {results['events_processed']:,}")

            # Run validation if requested
            if args.validate:
                logger.info("")
                logger.info("Running Dean Oliver validation...")
                validator = DeanOliverValidator(tolerance_pct=5.0)
                if validator.connect(config.database.connection_string):
                    validation_report = validator.generate_report()

                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("Validation Results")
                    logger.info("=" * 70)
                    logger.info(
                        f"Dean Oliver pass rate: {validation_report['dean_oliver_validation']['pass_rate_pct']:.1f}%"
                    )
                    logger.info(
                        f"Orphaned events: {validation_report['orphaned_events']['count']:,}"
                    )
                    logger.info(
                        f"Chain errors: {validation_report['possession_chains']['games_with_errors']}"
                    )
                    logger.info(
                        f"Overall status: {validation_report['overall_status']}"
                    )

                    validator.disconnect()
                else:
                    logger.warning("Failed to connect validator to database")

        finally:
            # Clean up
            extractor.disconnect()

        logger.info("")
        logger.info("=" * 70)
        logger.info("Possession Extraction Complete")
        logger.info("=" * 70)

        return 0

    except KeyboardInterrupt:
        logger.warning("\nExtraction interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
