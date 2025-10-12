#!/usr/bin/env python3
"""
Batch Process ESPN Play-by-Play to Box Score Snapshots

Processes ESPN play-by-play data from S3 and generates box score snapshots
for temporal queries and betting odds integration.

Usage:
    # Test with 10 games
    python3 batch_process_espn.py --season 2024 --limit 10 --verbose

    # Process full season
    python3 batch_process_espn.py --season 2024 --output /tmp/phase9_snapshots/

    # Process multiple seasons
    python3 batch_process_espn.py --start-season 2020 --end-season 2024

    # Full historical (overnight)
    nohup python3 batch_process_espn.py --start-season 1993 --end-season 2025 \
        --output /tmp/phase9_snapshots/ --save-rds > /tmp/phase9_espn_full.log 2>&1 &
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

from scripts.pbp_to_boxscore.espn_processor import ESPNPlayByPlayProcessor

def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def get_espn_game_ids_for_season(season: int) -> List[str]:
    """
    Get list of ESPN game IDs for a season from S3.

    In real implementation, this would query S3.
    For now, returns empty list to avoid actual processing.
    """
    import subprocess

    # List all PBP files in S3 for the season
    # ESPN game IDs typically start with 401 followed by digits
    try:
        result = subprocess.run([
            'aws', 's3', 'ls',
            f's3://nba-sim-raw-data-lake/pbp/',
            '--recursive'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return []

        # Extract game IDs from filenames (e.g., "401736813.json")
        game_ids = []
        for line in result.stdout.split('\n'):
            if '.json' in line and '401' in line:
                # Extract game ID from path
                filename = line.split()[-1]
                game_id = filename.split('/')[-1].replace('.json', '')
                if game_id.startswith('401'):
                    game_ids.append(game_id)

        return game_ids
    except Exception as e:
        logging.error(f"Error listing S3 files: {e}")
        return []

def process_batch(
    processor: ESPNPlayByPlayProcessor,
    game_ids: List[str],
    output_dir: Path,
    save_rds: bool = False,
    logger: Optional[logging.Logger] = None
) -> dict:
    """
    Process a batch of games.

    Returns:
        dict: Statistics about processing
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    stats = {
        'total_games': len(game_ids),
        'processed': 0,
        'errors': 0,
        'total_snapshots': 0,
        'start_time': time.time()
    }

    for i, game_id in enumerate(game_ids, 1):
        try:
            # Process game
            snapshots, verification = processor.process_game(game_id, verify=False)

            if not snapshots:
                logger.warning(f"  [{i}/{len(game_ids)}] {game_id}: No snapshots generated")
                stats['errors'] += 1
                continue

            # Save snapshots to JSON
            output_file = output_dir / f"{game_id}_snapshots.json"
            with open(output_file, 'w') as f:
                json.dump([{
                    'game_id': s.game_id,
                    'event_num': s.event_num,
                    'data_source': s.data_source,
                    'quarter': s.quarter,
                    'time_remaining': s.time_remaining,
                    'game_clock_seconds': s.game_clock_seconds,
                    'home_score': s.home_score,
                    'away_score': s.away_score
                } for s in snapshots], f, indent=2)

            stats['processed'] += 1
            stats['total_snapshots'] += len(snapshots)

            final = snapshots[-1]
            logger.info(
                f"  ✅ [{i}/{len(game_ids)}] {game_id}: "
                f"{len(snapshots)} snapshots, Final: {final.home_score}-{final.away_score}"
            )

            # Progress update every 10 games
            if i % 10 == 0:
                elapsed = time.time() - stats['start_time']
                rate = stats['processed'] / elapsed
                remaining = len(game_ids) - i
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_hours = eta_seconds / 3600

                logger.info(
                    f"\n📊 Progress: {i}/{len(game_ids)} games "
                    f"({i/len(game_ids)*100:.1f}%), "
                    f"{stats['total_snapshots']:,} snapshots, "
                    f"ETA: {eta_hours:.1f}h\n"
                )

        except FileNotFoundError:
            logger.warning(f"  [{i}/{len(game_ids)}] {game_id}: File not found in S3")
            stats['errors'] += 1
        except Exception as e:
            logger.error(f"  ❌ [{i}/{len(game_ids)}] {game_id}: {e}")
            stats['errors'] += 1

    return stats

def main():
    parser = argparse.ArgumentParser(
        description="Batch process ESPN play-by-play to box score snapshots",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Season selection
    parser.add_argument('--season', type=int, help='Single season to process')
    parser.add_argument('--start-season', type=int, default=1993, help='Start season (default: 1993)')
    parser.add_argument('--end-season', type=int, default=2025, help='End season (default: 2025)')

    # Processing options
    parser.add_argument('--limit', type=int, help='Limit number of games to process (for testing)')
    parser.add_argument('--output', type=str, default='/tmp/phase9_snapshots',
                       help='Output directory for snapshots')
    parser.add_argument('--save-rds', action='store_true',
                       help='Save snapshots to RDS (not implemented yet)')
    parser.add_argument('--checkpoint-every', type=int, default=100,
                       help='Save checkpoint every N games')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Setup
    logger = setup_logging(args.verbose)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("ESPN PLAY-BY-PLAY BATCH PROCESSOR")
    logger.info("=" * 80)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"RDS storage: {'Enabled' if args.save_rds else 'Disabled (JSON only)'}")
    logger.info("")

    # Initialize processor
    processor = ESPNPlayByPlayProcessor(local_cache_dir='/tmp/pbp_cache')

    # Determine seasons to process
    if args.season:
        seasons = [args.season]
    else:
        seasons = range(args.start_season, args.end_season + 1)

    logger.info(f"Processing seasons: {min(seasons)} - {max(seasons)} ({len(seasons)} seasons)")
    logger.info("")

    # Process each season
    overall_stats = {
        'total_games': 0,
        'processed': 0,
        'errors': 0,
        'total_snapshots': 0,
        'start_time': time.time()
    }

    for season in seasons:
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"Season {season}")
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Get game IDs for season
        game_ids = get_espn_game_ids_for_season(season)

        if not game_ids:
            logger.warning(f"  No games found for season {season}")
            continue

        # Apply limit if specified
        if args.limit:
            game_ids = game_ids[:args.limit]

        logger.info(f"  Found {len(game_ids)} games")

        # Process batch
        stats = process_batch(processor, game_ids, output_dir, args.save_rds, logger)

        # Update overall stats
        overall_stats['total_games'] += stats['total_games']
        overall_stats['processed'] += stats['processed']
        overall_stats['errors'] += stats['errors']
        overall_stats['total_snapshots'] += stats['total_snapshots']

        logger.info("")
        logger.info(f"Season {season} Complete:")
        logger.info(f"  Processed: {stats['processed']}/{stats['total_games']} games")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info(f"  Snapshots: {stats['total_snapshots']:,}")
        logger.info("")

    # Final summary
    elapsed = time.time() - overall_stats['start_time']
    logger.info("=" * 80)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total games: {overall_stats['total_games']}")
    logger.info(f"Processed: {overall_stats['processed']}")
    logger.info(f"Errors: {overall_stats['errors']}")
    logger.info(f"Success rate: {overall_stats['processed']/overall_stats['total_games']*100:.1f}%")
    logger.info(f"Total snapshots: {overall_stats['total_snapshots']:,}")
    logger.info(f"Runtime: {elapsed/3600:.1f} hours")
    logger.info(f"Output: {output_dir}")
    logger.info("")

    # Save summary
    summary_file = output_dir / "batch_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'total_games': overall_stats['total_games'],
            'processed': overall_stats['processed'],
            'errors': overall_stats['errors'],
            'total_snapshots': overall_stats['total_snapshots'],
            'runtime_seconds': elapsed,
            'success_rate': overall_stats['processed']/overall_stats['total_games']*100,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)

    logger.info(f"Summary saved: {summary_file}")

if __name__ == '__main__':
    main()

