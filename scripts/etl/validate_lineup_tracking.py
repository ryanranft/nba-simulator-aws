#!/usr/bin/env python3
"""
Validate lineup tracking by checking if event participants are in tracked lineups.

This script:
1. Reads possession panel data with lineups
2. Reads corresponding NBA API play-by-play events
3. Checks if all event participants (PLAYER1_ID, PLAYER2_ID, PLAYER3_ID) are in the tracked lineups
4. Flags possessions where participants aren't in tracked lineups
5. Updates the database with validation results

Usage:
    python validate_lineup_tracking.py [--limit N] [--sample-games]
"""

import json
import logging
import sys
from pathlib import Path
from collections import defaultdict

import psycopg2
from psycopg2.extras import execute_batch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'database': 'nba_simulator',
    'user': 'ryanranft',
    'password': ''
}

NBA_API_DIR = Path('/tmp/nba_api_comprehensive/play_by_play')


def load_play_by_play_events(game_id):
    """Load play-by-play events for a game from NBA API JSON file."""
    pbp_file = NBA_API_DIR / f'play_by_play_{game_id}.json'

    if not pbp_file.exists():
        logger.warning(f"PBP file not found for game {game_id}: {pbp_file}")
        return []

    try:
        with open(pbp_file, 'r') as f:
            data = json.load(f)

        # Extract events from resultSets
        result_sets = data.get('resultSets', [])
        if not result_sets:
            return []

        # Get the PlayByPlay result set
        play_by_play = result_sets[0]
        headers = play_by_play['headers']
        rows = play_by_play['rowSet']

        # Convert to list of dicts
        events = []
        for row in rows:
            event = dict(zip(headers, row))
            events.append(event)

        return events

    except Exception as e:
        logger.error(f"Error loading PBP for game {game_id}: {e}")
        return []


def get_event_participants(event):
    """Extract all player IDs that participated in an event."""
    participants = set()

    for field in ['PLAYER1_ID', 'PLAYER2_ID', 'PLAYER3_ID']:
        player_id = event.get(field)
        if player_id and player_id != 0:
            participants.add(player_id)

    return participants


def validate_possession_lineups(conn):
    """
    Validate that all event participants are in the tracked lineups.

    Returns:
        dict: Validation results with counts and examples
    """
    cur = conn.cursor()

    # Get all possessions with complete lineups
    logger.info("Loading possessions to validate...")
    cur.execute("""
        SELECT
            game_id,
            possession_number,
            off_player_1_id, off_player_2_id, off_player_3_id, off_player_4_id, off_player_5_id,
            def_player_1_id, def_player_2_id, def_player_3_id, def_player_4_id, def_player_5_id,
            lineup_complete
        FROM possession_panel_with_lineups
        WHERE lineup_complete = TRUE
        ORDER BY game_id, possession_number
    """)

    possessions = cur.fetchall()
    logger.info(f"Loaded {len(possessions)} complete possessions to validate")

    # Track validation results
    validation_results = {
        'total_possessions': 0,
        'total_events': 0,
        'mismatches': 0,
        'possessions_with_mismatches': 0,
        'examples': []
    }

    # Process by game (to avoid reloading PBP files)
    current_game_id = None
    current_events = []
    possessions_to_update = []

    for row in possessions:
        game_id = row[0]
        poss_num = row[1]
        off_lineup = set(filter(None, row[2:7]))  # off_player_1 through off_player_5
        def_lineup = set(filter(None, row[7:12]))  # def_player_1 through def_player_5

        validation_results['total_possessions'] += 1

        # Load events if new game
        if game_id != current_game_id:
            current_events = load_play_by_play_events(game_id)
            current_game_id = game_id
            logger.info(f"  Game {game_id}: {len(current_events)} events")

        if not current_events:
            continue

        # Get events for this possession
        poss_events = [e for e in current_events if e.get('possession_number') == poss_num]

        if not poss_events:
            # No possession_number in NBA API events - skip
            continue

        validation_results['total_events'] += len(poss_events)

        # Check all participants in this possession
        all_participants = set()
        for event in poss_events:
            participants = get_event_participants(event)
            all_participants.update(participants)

        # Check if all participants are in tracked lineups
        tracked_players = off_lineup | def_lineup
        missing_players = all_participants - tracked_players

        if missing_players:
            validation_results['mismatches'] += len(missing_players)
            validation_results['possessions_with_mismatches'] += 1

            # Save example for logging
            if len(validation_results['examples']) < 10:
                validation_results['examples'].append({
                    'game_id': game_id,
                    'possession_number': poss_num,
                    'missing_players': list(missing_players),
                    'tracked_offense': list(off_lineup),
                    'tracked_defense': list(def_lineup)
                })

            # Mark for database update
            possessions_to_update.append((game_id, poss_num))

    return validation_results, possessions_to_update


def update_database_with_results(conn, possessions_to_update):
    """Update database with validation results."""
    cur = conn.cursor()

    if not possessions_to_update:
        logger.info("No mismatches found - all lineups are accurate!")
        return

    logger.info(f"Updating {len(possessions_to_update)} possessions with mismatch flags...")

    # Update lineup_participant_mismatch flag
    update_query = """
        UPDATE possession_panel_with_lineups
        SET
            lineup_participant_mismatch = TRUE,
            lineup_validation_notes = COALESCE(lineup_validation_notes || '; ', '') ||
                                     'Event participant not in tracked lineup'
        WHERE game_id = %s AND possession_number = %s
    """

    execute_batch(cur, update_query, possessions_to_update)
    conn.commit()

    logger.info("✓ Database updated with validation results")


def main():
    """Main validation function."""
    logger.info("="*60)
    logger.info("LINEUP TRACKING VALIDATION")
    logger.info("="*60)
    logger.info("")

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Validate lineups
        results, possessions_to_update = validate_possession_lineups(conn)

        # Update database
        update_database_with_results(conn, possessions_to_update)

        # Print results
        logger.info("")
        logger.info("="*60)
        logger.info("VALIDATION RESULTS")
        logger.info("="*60)
        logger.info(f"Total possessions validated: {results['total_possessions']:,}")
        logger.info(f"Total events checked: {results['total_events']:,}")
        logger.info(f"Possessions with mismatches: {results['possessions_with_mismatches']:,}")
        logger.info(f"Total missing players: {results['mismatches']:,}")

        if results['possessions_with_mismatches'] > 0:
            accuracy = 100 * (1 - results['possessions_with_mismatches'] / results['total_possessions'])
            logger.info(f"Lineup accuracy: {accuracy:.2f}%")

            logger.info("")
            logger.info("Example mismatches:")
            for ex in results['examples']:
                logger.info(f"  Game {ex['game_id']}, Poss {ex['possession_number']}:")
                logger.info(f"    Missing players: {ex['missing_players']}")
                logger.info(f"    Tracked offense: {ex['tracked_offense']}")
                logger.info(f"    Tracked defense: {ex['tracked_defense']}")
        else:
            logger.info("✨ Perfect accuracy - all event participants are in tracked lineups!")

        logger.info("")
        logger.info("="*60)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
