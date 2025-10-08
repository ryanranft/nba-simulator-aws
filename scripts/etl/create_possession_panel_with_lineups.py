"""
Create Possession Panel with Lineup Tracking (pbpstats-style)

This script replicates the key pbpstats feature: tracking all 10 players on court
for each possession by monitoring substitution events.

Key features:
1. Possession detection using event types (like existing script)
2. Lineup tracking via substitution events (NEW - like pbpstats)
3. Starting lineups from period-begin events
4. Defensive team lineup tracking

Output: possession panel with 10 player IDs per possession (5 offense + 5 defense)
"""

import os
import json
import psycopg2
import pandas as pd
from datetime import datetime
import argparse
import logging
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Local PostgreSQL database config
DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'nba_simulator',
    'user': 'ryanranft',
    'password': '',
    'port': 5432
}


class LineupTracker:
    """Track current players on court for both teams (pbpstats-style)"""

    def __init__(self, home_team_id, away_team_id):
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id

        # Current players on court (sets for each team)
        self.home_lineup = set()
        self.away_lineup = set()

    def process_substitution(self, event):
        """
        Process substitution event to update lineups

        Args:
            event: dict with PLAYER1_ID (player out), PLAYER2_ID (player in), PLAYER1_TEAM_ID
        """
        team_id = event.get('PLAYER1_TEAM_ID')
        player_out = event.get('PLAYER1_ID')
        player_in = event.get('PLAYER2_ID')

        if not team_id or not player_in:
            return

        # Determine which team's lineup to update
        if team_id == self.home_team_id:
            lineup = self.home_lineup
        elif team_id == self.away_team_id:
            lineup = self.away_lineup
        else:
            return

        # Remove player going out (if specified)
        if player_out and player_out in lineup:
            lineup.remove(player_out)

        # Add player coming in
        lineup.add(player_in)

    def set_starting_lineup(self, team_id, player_ids):
        """Set starting lineup for a team"""
        if team_id == self.home_team_id:
            self.home_lineup = set(player_ids)
        elif team_id == self.away_team_id:
            self.away_lineup = set(player_ids)

    def get_lineup(self, team_id):
        """Get current lineup for a team (returns sorted list of 5 player IDs)"""
        if team_id == self.home_team_id:
            lineup = list(self.home_lineup)
        elif team_id == self.away_team_id:
            lineup = list(self.away_lineup)
        else:
            return [None] * 5

        # Sort and pad to exactly 5 players
        lineup = sorted(lineup)[:5]
        while len(lineup) < 5:
            lineup.append(None)

        return lineup

    def get_lineup_hash(self, team_id):
        """Get lineup hash (sorted player IDs joined by hyphen, like pbpstats)"""
        lineup = self.get_lineup(team_id)
        return '-'.join(str(p) for p in lineup if p is not None)


def load_starting_lineups_from_boxscore(game_id, boxscore_dir='/tmp/nba_api_comprehensive/boxscores_advanced'):
    """
    Load official starting lineups from box score data

    Returns: dict with {team_id: [player_ids]} or None if not found
    """
    try:
        boxscore_file = Path(boxscore_dir) / f'advanced_{game_id}.json'

        if not boxscore_file.exists():
            return None

        with open(boxscore_file, 'r') as f:
            boxscore_data = json.load(f)

        # Get PlayerStats result set
        player_stats = None
        for rs in boxscore_data.get('resultSets', []):
            if rs.get('name') == 'PlayerStats':
                player_stats = rs
                break

        if not player_stats:
            return None

        headers = player_stats['headers']
        rows = player_stats['rowSet']

        # Find indices
        start_pos_idx = headers.index('START_POSITION')
        player_id_idx = headers.index('PLAYER_ID')
        team_id_idx = headers.index('TEAM_ID')

        # Collect starters by team
        starters_by_team = defaultdict(list)
        for row in rows:
            start_position = row[start_pos_idx]
            if start_position and start_position != '':  # Non-empty = starter
                team_id = row[team_id_idx]
                player_id = row[player_id_idx]
                starters_by_team[team_id].append(player_id)

        # Return dict with team_id -> list of 5 player IDs
        result = {}
        for team_id, player_ids in starters_by_team.items():
            result[team_id] = player_ids[:5]  # Ensure exactly 5

        return result if len(result) == 2 else None

    except Exception as e:
        logger.debug(f"Could not load boxscore for game {game_id}: {e}")
        return None


def infer_starting_lineups(events, home_team_id, away_team_id):
    """
    Infer starting lineups from first events of the game (fallback method)

    Returns: dict with {team_id: [player_ids]}
    """
    home_starters = set()
    away_starters = set()

    # Look at first 20 events to find starting players
    for event in events[:20]:
        event_type = event.get('EVENTMSGTYPE')

        # Skip non-playing events
        if event_type in [8, 9, 10, 11, 12, 13, 18]:
            continue

        # Collect players from playing events
        for player_key in ['PLAYER1_ID', 'PLAYER2_ID', 'PLAYER3_ID']:
            player_id = event.get(player_key)
            team_id = event.get(f'{player_key.replace("ID", "TEAM_ID")}')

            if player_id and team_id:
                if team_id == home_team_id:
                    home_starters.add(player_id)
                elif team_id == away_team_id:
                    away_starters.add(player_id)

            # Stop once we have 5 players for each team
            if len(home_starters) >= 5 and len(away_starters) >= 5:
                break

    return {
        home_team_id: list(home_starters)[:5],
        away_team_id: list(away_starters)[:5]
    }


def extract_possessions_with_lineups(game_data):
    """
    Extract possessions with lineup tracking

    Returns:
        list of possession dicts with lineup information
    """
    possessions = []

    try:
        game_id = game_data['parameters']['GameID']
        result_sets = game_data.get('resultSets', [])

        if not result_sets:
            logger.warning(f"No result sets for game {game_id}")
            return []

        pbp_data = result_sets[0]
        headers = pbp_data['headers']
        rows = pbp_data['rowSet']

        events = [dict(zip(headers, row)) for row in rows]

        if not events:
            logger.warning(f"No events for game {game_id}")
            return []

        # Get team IDs from player events (NBA API doesn't have HOME_TEAM_ID/VISITOR_TEAM_ID)
        # Instead, we collect team IDs from PLAYER1_TEAM_ID, PLAYER2_TEAM_ID, PLAYER3_TEAM_ID
        team_ids = set()
        for event in events[:50]:  # Check first 50 events to find both teams
            for player_key in ['PLAYER1_TEAM_ID', 'PLAYER2_TEAM_ID', 'PLAYER3_TEAM_ID']:
                team_id = event.get(player_key)
                if team_id and team_id != 0:
                    team_ids.add(team_id)
            if len(team_ids) >= 2:
                break

        if len(team_ids) < 2:
            logger.warning(f"Could not determine both team IDs for game {game_id}")
            return []

        # Arbitrarily assign first team as "home" and second as "away"
        # (doesn't matter for lineup tracking, just need to distinguish them)
        team_list = sorted(list(team_ids))
        home_team_id = team_list[0]
        away_team_id = team_list[1]

        # Initialize lineup tracker
        tracker = LineupTracker(home_team_id, away_team_id)

        # Get starting lineups - try boxscore first, fallback to inference
        starting_lineups = load_starting_lineups_from_boxscore(game_id)

        if starting_lineups and len(starting_lineups) == 2:
            # Use official starters from box score
            for team_id, player_ids in starting_lineups.items():
                tracker.set_starting_lineup(team_id, player_ids)
            logger.debug(f"  Using official starters from boxscore for game {game_id}")
        else:
            # Fallback to inference
            starting_lineups = infer_starting_lineups(events, home_team_id, away_team_id)
            tracker.set_starting_lineup(home_team_id, starting_lineups[home_team_id])
            tracker.set_starting_lineup(away_team_id, starting_lineups[away_team_id])
            logger.debug(f"  Inferred starters from events for game {game_id}")

        # Process events
        current_possession = {
            'events': [],
            'offense_team_id': None,
            'start_score': None
        }

        possession_number = 0

        for i, event in enumerate(events):
            next_event = events[i + 1] if i + 1 < len(events) else None
            event_type = event.get('EVENTMSGTYPE')

            # Process substitutions to update lineups
            if event_type == 8:  # SUBSTITUTION
                tracker.process_substitution(event)
                continue

            # Skip other non-game events
            if event_type in [9, 10, 11, 12, 18]:  # TIMEOUT, JUMP_BALL, etc.
                continue

            # Period begin - reset lineups to starters
            if event_type == 12:  # PERIOD_BEGIN
                tracker.set_starting_lineup(home_team_id, starting_lineups[home_team_id])
                tracker.set_starting_lineup(away_team_id, starting_lineups[away_team_id])
                continue

            # Add event to current possession
            current_possession['events'].append(event)

            # Track offense team
            if current_possession['offense_team_id'] is None:
                team_id = event.get('PLAYER1_TEAM_ID')
                if team_id:
                    current_possession['offense_team_id'] = team_id

            # Track start score
            if current_possession['start_score'] is None:
                score = event.get('SCORE')
                if score:
                    current_possession['start_score'] = score

            # Check if possession ends
            if is_possession_end(event, next_event):
                # Get offense and defense teams
                offense_team = current_possession['offense_team_id']
                defense_team = home_team_id if offense_team == away_team_id else away_team_id

                # Get lineups (THIS IS THE KEY PBPSTATS FEATURE!)
                offense_lineup = tracker.get_lineup(offense_team)
                defense_lineup = tracker.get_lineup(defense_team)

                # Calculate points scored
                end_score = event.get('SCORE') or current_possession['start_score']
                start_score = current_possession['start_score'] or '0 - 0'

                try:
                    if start_score:
                        away_start, home_start = map(int, start_score.split(' - '))
                    else:
                        away_start, home_start = 0, 0

                    if end_score:
                        away_end, home_end = map(int, end_score.split(' - '))
                    else:
                        away_end, home_end = away_start, home_start

                    points_scored = (away_end - away_start) + (home_end - home_start)
                except (ValueError, AttributeError):
                    points_scored = 0

                # Create possession record with lineups
                possession = {
                    'game_id': game_id,
                    'possession_number': possession_number,
                    'period': event.get('PERIOD', 1),
                    'time_remaining': event.get('PCTIMESTRING'),
                    'offense_team_id': offense_team,
                    'defense_team_id': defense_team,
                    'points_scored': points_scored,
                    'possession_result': categorize_result(current_possession['events']),
                    'num_events': len(current_possession['events']),

                    # Lineup tracking (pbpstats feature!)
                    'off_player_1_id': offense_lineup[0],
                    'off_player_2_id': offense_lineup[1],
                    'off_player_3_id': offense_lineup[2],
                    'off_player_4_id': offense_lineup[3],
                    'off_player_5_id': offense_lineup[4],
                    'off_lineup_hash': tracker.get_lineup_hash(offense_team),

                    'def_player_1_id': defense_lineup[0],
                    'def_player_2_id': defense_lineup[1],
                    'def_player_3_id': defense_lineup[2],
                    'def_player_4_id': defense_lineup[3],
                    'def_player_5_id': defense_lineup[4],
                    'def_lineup_hash': tracker.get_lineup_hash(defense_team),
                }

                possessions.append(possession)
                possession_number += 1

                # Reset for next possession
                current_possession = {
                    'events': [],
                    'offense_team_id': None,
                    'start_score': end_score
                }

        logger.info(f"  Game {game_id}: extracted {len(possessions)} possessions with lineups")
        return possessions

    except Exception as e:
        logger.error(f"Error processing game: {e}")
        import traceback
        traceback.print_exc()
        return []


def is_possession_end(event, next_event=None):
    """Determine if event ends possession (same logic as original script)"""
    event_type = event.get('EVENTMSGTYPE')
    event_action = event.get('EVENTMSGACTIONTYPE', 0)

    # Made FG (check for and-1)
    if event_type == 1:
        if next_event and next_event.get('EVENTMSGTYPE') == 3:
            return False
        return True

    # Defensive rebound
    if event_type == 4:
        return event_action == 0

    # Turnover
    if event_type == 5:
        return True

    # Last free throw
    if event_type == 3:
        desc = (event.get('HOMEDESCRIPTION') or event.get('VISITORDESCRIPTION') or '')
        if ' of ' in desc:
            parts = desc.split(' of ')
            if len(parts) >= 2:
                try:
                    current = int(parts[0].split()[-1])
                    total = int(parts[1].split()[0])
                    return current == total
                except:
                    pass
        return True

    # Period end
    if event_type == 13:
        return True

    return False


def categorize_result(events):
    """Categorize possession result"""
    if not events:
        return 'other'

    last_event = events[-1]
    event_type = last_event.get('EVENTMSGTYPE')

    if event_type == 1:
        return 'made_fg'
    elif event_type == 2:
        return 'miss'
    elif event_type == 5:
        return 'turnover'
    else:
        return 'other'


def main():
    parser = argparse.ArgumentParser(description='Build possession panel with lineups')
    parser.add_argument('--limit', type=int, help='Limit number of games')
    parser.add_argument('--truncate', action='store_true', help='Truncate table first')
    parser.add_argument('--data-dir', default='/tmp/nba_api_comprehensive/play_by_play',
                       help='Directory with NBA API PBP files')
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("Building Possession Panel WITH LINEUP TRACKING")
    logger.info("(pbpstats-style implementation)")
    logger.info("="*60)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Create/truncate table
    if args.truncate:
        logger.info("Creating possession_panel_with_lineups table...")
        cur.execute("DROP TABLE IF EXISTS possession_panel_with_lineups CASCADE")
        cur.execute("""
            CREATE TABLE possession_panel_with_lineups (
                game_id VARCHAR(20),
                possession_number INTEGER,
                period INTEGER,
                time_remaining VARCHAR(10),
                offense_team_id BIGINT,
                defense_team_id BIGINT,
                points_scored INTEGER,
                possession_result VARCHAR(20),
                num_events INTEGER,

                -- Offensive lineup (pbpstats feature!)
                off_player_1_id BIGINT,
                off_player_2_id BIGINT,
                off_player_3_id BIGINT,
                off_player_4_id BIGINT,
                off_player_5_id BIGINT,
                off_lineup_hash VARCHAR(100),

                -- Defensive lineup (pbpstats feature!)
                def_player_1_id BIGINT,
                def_player_2_id BIGINT,
                def_player_3_id BIGINT,
                def_player_4_id BIGINT,
                def_player_5_id BIGINT,
                def_lineup_hash VARCHAR(100),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(game_id, possession_number)
            )
        """)

        # Create index on lineup hashes
        cur.execute("""
            CREATE INDEX idx_off_lineup ON possession_panel_with_lineups(off_lineup_hash)
        """)
        cur.execute("""
            CREATE INDEX idx_def_lineup ON possession_panel_with_lineups(def_lineup_hash)
        """)

        conn.commit()
        logger.info("✓ Table created with lineup columns")

    # Find PBP files
    data_dir = Path(args.data_dir)
    pbp_files = sorted(data_dir.glob('play_by_play_*.json'))

    if args.limit:
        pbp_files = pbp_files[:args.limit]

    logger.info(f"Found {len(pbp_files)} games to process")

    # Process games
    all_possessions = []

    for i, pbp_file in enumerate(pbp_files, 1):
        try:
            with open(pbp_file, 'r') as f:
                game_data = json.load(f)

            possessions = extract_possessions_with_lineups(game_data)
            all_possessions.extend(possessions)

            if i % 50 == 0:
                logger.info(f"  Progress: {i}/{len(pbp_files)} games")

        except Exception as e:
            logger.error(f"Error reading {pbp_file}: {e}")

    logger.info(f"\n✓ Extracted {len(all_possessions):,} possessions with lineup tracking")
    logger.info(f"  Average: {len(all_possessions) / max(len(pbp_files), 1):.1f} poss/game")

    # Write to database
    if all_possessions:
        df = pd.DataFrame(all_possessions)

        logger.info(f"Writing {len(df):,} possessions to database...")

        # Insert using pandas
        from sqlalchemy import create_engine
        engine = create_engine(f"postgresql://{DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
        df.to_sql('possession_panel_with_lineups', engine, if_exists='append', index=False, method='multi', chunksize=1000)

        logger.info(f"✅ Wrote {len(df):,} possessions with lineup tracking!")

        # Post-process: Fill incomplete lineups by forward-filling from first complete lineup
        logger.info("Post-processing: Filling incomplete lineups...")

        fill_query = """
            -- Fill incomplete lineups from first complete lineup in each game
            WITH first_complete AS (
                SELECT DISTINCT ON (game_id, offense_team_id)
                    game_id, offense_team_id AS team_id,
                    off_player_1_id AS p1, off_player_2_id AS p2, off_player_3_id AS p3,
                    off_player_4_id AS p4, off_player_5_id AS p5
                FROM possession_panel_with_lineups
                WHERE off_player_5_id IS NOT NULL
                ORDER BY game_id, offense_team_id, possession_number
            )
            UPDATE possession_panel_with_lineups p
            SET
                off_player_1_id = COALESCE(p.off_player_1_id, f.p1),
                off_player_2_id = COALESCE(p.off_player_2_id, f.p2),
                off_player_3_id = COALESCE(p.off_player_3_id, f.p3),
                off_player_4_id = COALESCE(p.off_player_4_id, f.p4),
                off_player_5_id = COALESCE(p.off_player_5_id, f.p5),
                off_lineup_hash = (
                    SELECT string_agg(pid::text, '-' ORDER BY pid)
                    FROM unnest(ARRAY[
                        COALESCE(p.off_player_1_id, f.p1), COALESCE(p.off_player_2_id, f.p2),
                        COALESCE(p.off_player_3_id, f.p3), COALESCE(p.off_player_4_id, f.p4),
                        COALESCE(p.off_player_5_id, f.p5)
                    ]) AS pid WHERE pid IS NOT NULL
                )
            FROM first_complete f
            WHERE p.game_id = f.game_id AND p.offense_team_id = f.team_id
              AND p.off_player_5_id IS NULL;

            WITH first_complete AS (
                SELECT DISTINCT ON (game_id, defense_team_id)
                    game_id, defense_team_id AS team_id,
                    def_player_1_id AS p1, def_player_2_id AS p2, def_player_3_id AS p3,
                    def_player_4_id AS p4, def_player_5_id AS p5
                FROM possession_panel_with_lineups
                WHERE def_player_5_id IS NOT NULL
                ORDER BY game_id, defense_team_id, possession_number
            )
            UPDATE possession_panel_with_lineups p
            SET
                def_player_1_id = COALESCE(p.def_player_1_id, f.p1),
                def_player_2_id = COALESCE(p.def_player_2_id, f.p2),
                def_player_3_id = COALESCE(p.def_player_3_id, f.p3),
                def_player_4_id = COALESCE(p.def_player_4_id, f.p4),
                def_player_5_id = COALESCE(p.def_player_5_id, f.p5),
                def_lineup_hash = (
                    SELECT string_agg(pid::text, '-' ORDER BY pid)
                    FROM unnest(ARRAY[
                        COALESCE(p.def_player_1_id, f.p1), COALESCE(p.def_player_2_id, f.p2),
                        COALESCE(p.def_player_3_id, f.p3), COALESCE(p.def_player_4_id, f.p4),
                        COALESCE(p.def_player_5_id, f.p5)
                    ]) AS pid WHERE pid IS NOT NULL
                )
            FROM first_complete f
            WHERE p.game_id = f.game_id AND p.defense_team_id = f.team_id
              AND p.def_player_5_id IS NULL;
        """

        cur.execute(fill_query)
        conn.commit()
        logger.info("✓ Incomplete lineups filled")

        # Summary
        print("\n" + "="*60)
        print("✅ SUCCESS - Possession Panel with Lineup Tracking Complete!")
        print("="*60)
        print(f"\nTotal possessions: {len(df):,}")
        print(f"Games processed: {len(pbp_files)}")
        print(f"Avg possessions/game: {len(df) / max(len(pbp_files), 1):.1f}")

        # Re-query for accurate final counts
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN off_player_5_id IS NOT NULL THEN 1 END) as complete_off,
                COUNT(CASE WHEN def_player_5_id IS NOT NULL THEN 1 END) as complete_def,
                COUNT(DISTINCT off_lineup_hash) as unique_off,
                COUNT(DISTINCT def_lineup_hash) as unique_def
            FROM possession_panel_with_lineups
        """)
        total, complete_off, complete_def, unique_off, unique_def = cur.fetchone()

        print(f"\nLineup tracking:")
        print(f"  - Complete offensive lineups: {complete_off:,} ({100*complete_off/total:.1f}%)")
        print(f"  - Complete defensive lineups: {complete_def:,} ({100*complete_def/total:.1f}%)")
        print(f"  - Unique offensive lineups: {unique_off:,}")
        print(f"  - Unique defensive lineups: {unique_def:,}")
        print("\nReady for game simulation! ✨")
        print()

    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
