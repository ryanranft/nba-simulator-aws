#!/usr/bin/env python3
"""
Populate data_availability table based on actual database contents
Uses results from assess_data.py to fill the data_availability table
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_era(year: int) -> str:
    """Determine era based on year"""
    if 1946 <= year < 1960:
        return 'early_era'
    elif 1960 <= year < 1990:
        return 'box_score_era'
    elif 1990 <= year <= 2025:
        return 'pbp_era'
    return 'unknown'


def get_fidelity(era: str) -> str:
    """Get fidelity level for era"""
    mapping = {
        'early_era': 'minimal',
        'box_score_era': 'enhanced',
        'pbp_era': 'detailed'
    }
    return mapping.get(era, 'unknown')


def populate_from_assessment(assessment_file: str = 'data_assessment.json'):
    """Populate data_availability table from assessment results"""

    # Load assessment results
    logger.info(f"Loading assessment from {assessment_file}...")
    try:
        with open(assessment_file, 'r') as f:
            assessment = json.load(f)
    except FileNotFoundError:
        logger.error(f"Assessment file not found: {assessment_file}")
        logger.info("Please run: python scripts/assess_data.py first")
        return False

    seasons_data = assessment.get('seasons', {})
    if not seasons_data:
        logger.error("No season data found in assessment")
        return False

    logger.info(f"Found {len(seasons_data)} seasons in assessment")

    # Connect to database
    try:
        conn = psycopg2.connect(
            host=os.getenv('RDS_HOST'),
            port=os.getenv('RDS_PORT', 5432),
            database=os.getenv('RDS_DATABASE'),
            user=os.getenv('RDS_USERNAME'),
            password=os.getenv('RDS_PASSWORD')
        )
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

    try:
        with conn.cursor() as cur:
            # Prepare data for insertion
            records = []

            for season, data in seasons_data.items():
                try:
                    # Parse season (e.g., "2023-24" -> 2023, 2024)
                    parts = season.split('-')
                    start_year = int(parts[0])
                    end_year = int('20' + parts[1]) if len(parts[1]) == 2 else int(parts[1])

                    era = get_era(start_year)
                    fidelity = get_fidelity(era)

                    # Extract counts
                    game_count = data.get('games', 0)
                    box_score_count = data.get('box_scores', 0)
                    pbp_count = data.get('play_by_play', 0)

                    # Calculate completeness (using 82 games as expected for modern seasons)
                    expected_games = 82 if start_year >= 1967 else 80
                    game_completeness = min(1.0, game_count / expected_games) if expected_games > 0 else 0.0

                    # Box score completeness (should be close to 1:1 with games)
                    box_score_completeness = min(1.0, box_score_count / (game_count * 2)) if game_count > 0 else 0.0

                    # PBP completeness (only relevant for pbp_era)
                    pbp_completeness = min(1.0, pbp_count / (game_count * 400)) if game_count > 0 else 0.0

                    # Calculate quality score
                    if era == 'early_era':
                        quality_score = (game_completeness * 0.6) + (box_score_completeness * 0.4)
                    elif era == 'box_score_era':
                        quality_score = (game_completeness * 0.4) + (box_score_completeness * 0.6)
                    else:  # pbp_era
                        quality_score = (game_completeness * 0.3) + (box_score_completeness * 0.3) + (pbp_completeness * 0.4)

                    record = (
                        season,
                        start_year,
                        end_year,
                        era,
                        fidelity,
                        game_count > 0,  # has_games
                        box_score_count > 0,  # has_box_scores
                        pbp_count > 0,  # has_play_by_play
                        False,  # has_advanced_stats (TODO: check actual table)
                        False,  # has_tracking_data
                        False,  # has_shot_chart
                        game_count,
                        box_score_count,
                        pbp_count,
                        game_completeness,
                        box_score_completeness,
                        pbp_completeness,
                        quality_score,
                        quality_score < 0.5,  # has_quality_issues
                        f"Auto-generated from assessment on {datetime.now().isoformat()}"
                    )

                    records.append(record)

                except (ValueError, IndexError, KeyError) as e:
                    logger.warning(f"Skipping season {season}: {e}")
                    continue

            # Insert records
            logger.info(f"Inserting {len(records)} records...")

            insert_query = """
                INSERT INTO data_availability (
                    season, start_year, end_year, era, fidelity_level,
                    has_games, has_box_scores, has_play_by_play,
                    has_advanced_stats, has_tracking_data, has_shot_chart,
                    game_count, box_score_count, pbp_event_count,
                    game_completeness, box_score_completeness, pbp_completeness,
                    data_quality_score, has_quality_issues, quality_notes
                )
                VALUES %s
                ON CONFLICT (season) DO UPDATE SET
                    game_count = EXCLUDED.game_count,
                    box_score_count = EXCLUDED.box_score_count,
                    pbp_event_count = EXCLUDED.pbp_event_count,
                    game_completeness = EXCLUDED.game_completeness,
                    box_score_completeness = EXCLUDED.box_score_completeness,
                    pbp_completeness = EXCLUDED.pbp_completeness,
                    data_quality_score = EXCLUDED.data_quality_score,
                    has_quality_issues = EXCLUDED.has_quality_issues,
                    quality_notes = EXCLUDED.quality_notes,
                    last_assessed = CURRENT_TIMESTAMP
            """

            execute_values(cur, insert_query, records)
            conn.commit()

            logger.info(f"✓ Successfully inserted/updated {len(records)} records")

            # Show summary
            cur.execute("""
                SELECT
                    era,
                    COUNT(*) as season_count,
                    SUM(game_count) as total_games,
                    AVG(data_quality_score) as avg_quality
                FROM data_availability
                GROUP BY era
                ORDER BY era
            """)

            print("\n" + "=" * 80)
            print("DATA AVAILABILITY SUMMARY")
            print("=" * 80)
            for row in cur.fetchall():
                print(f"\n{row[0]}:")
                print(f"  Seasons: {row[1]}")
                print(f"  Total Games: {row[2]:,}")
                print(f"  Avg Quality Score: {row[3]:.2%}")

            print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Failed to populate table: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()
        logger.info("Database connection closed")

    return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Populate data_availability table")
    parser.add_argument(
        '--assessment-file',
        default='data_assessment.json',
        help='Assessment file from assess_data.py (default: data_assessment.json)'
    )

    args = parser.parse_args()

    success = populate_from_assessment(args.assessment_file)

    if success:
        print("\n✅ data_availability table populated successfully!")
        print("\nNext steps:")
        print("  1. Review data quality scores")
        print("  2. Investigate any seasons with has_quality_issues=TRUE")
        print("  3. Use this table to guide simulation fidelity selection")
    else:
        print("\n❌ Failed to populate table. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()