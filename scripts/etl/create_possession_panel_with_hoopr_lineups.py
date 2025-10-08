"""
Create Possession Panel with hoopR Starting Lineups + Kaggle Events

Integrates:
1. hoopR player box scores → Starting lineups (5 players per team)
2. Kaggle temporal events → Play-by-play possession tracking
3. LineupTracker → Tracks 10 players on court (5 offense + 5 defense)

This creates possession-level panel data suitable for ML training with complete lineups.

Usage:
    python scripts/etl/create_possession_panel_with_hoopr_lineups.py --limit 10  # Test on 10 games
    python scripts/etl/create_possession_panel_with_hoopr_lineups.py              # Process all games
"""

import os
import sys
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import argparse
import logging

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
    """Track current lineups (5 offense + 5 defense) using hoopR starters + Kaggle substitution events"""

    def __init__(self, kaggle_game_id: str, hoopr_game_id: str, home_team_id: str, away_team_id: str):
        self.kaggle_game_id = kaggle_game_id
        self.hoopr_game_id = hoopr_game_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id

        # Current lineups (ESPN player IDs)
        self.home_lineup = []
        self.away_lineup = []

        # Initialized flag
        self.initialized = False

    def initialize_from_hoopr(self, conn):
        """Load starting lineups from hoopR player box scores"""

        cursor = conn.cursor()

        # Get starters for this game from hoopR (using hoopr_game_id)
        query = """
            SELECT player_id, player_name, team_id, starter
            FROM hoopr_player_box
            WHERE game_id = %s
              AND starter = true
            ORDER BY team_id, player_id
        """

        cursor.execute(query, (self.hoopr_game_id,))
        starters = cursor.fetchall()

        if not starters:
            logger.warning(f"No hoopR starters found for hoopr_game_id {self.hoopr_game_id} (Kaggle game_id: {self.kaggle_game_id})")
            return False

        # Separate by team
        for player_id, player_name, team_id, is_starter in starters:
            if str(team_id) == str(self.home_team_id):
                self.home_lineup.append(str(player_id))
            elif str(team_id) == str(self.away_team_id):
                self.away_lineup.append(str(player_id))

        logger.debug(f"Game {self.kaggle_game_id}: Home starters = {len(self.home_lineup)}, Away starters = {len(self.away_lineup)}")

        # Validate we have 5 starters per team
        if len(self.home_lineup) != 5 or len(self.away_lineup) != 5:
            logger.warning(f"Game {self.kaggle_game_id}: Incomplete starters (Home: {len(self.home_lineup)}, Away: {len(self.away_lineup)})")
            return False

        self.initialized = True
        cursor.close()
        return True

    def update_lineup(self, event_text: str, team_id: str):
        """Update lineup based on substitution event"""

        if not self.initialized:
            return

        text_lower = event_text.lower()

        # Kaggle substitution format: "Player Name enters the game for Player Name"
        if 'enters the game for' in text_lower:
            # Parse substitution
            parts = event_text.split(' enters the game for ')
            if len(parts) == 2:
                player_in_name = parts[0].strip()
                player_out_name = parts[1].strip()

                # TODO: Map player names to ESPN IDs
                # For now, we'll track that a sub occurred but not update lineups
                # Full implementation would use player name → ESPN ID mapping
                logger.debug(f"Substitution detected: {player_in_name} in, {player_out_name} out")

    def get_current_lineups(self, offensive_team_id: str):
        """Get current 10-player lineup (5 offense + 5 defense)"""

        if not self.initialized:
            return None

        # Determine which team is on offense
        is_home_offense = (str(offensive_team_id) == str(self.home_team_id))

        if is_home_offense:
            offense_lineup = self.home_lineup.copy()
            defense_lineup = self.away_lineup.copy()
        else:
            offense_lineup = self.away_lineup.copy()
            defense_lineup = self.home_lineup.copy()

        # Ensure exactly 5 players per side
        if len(offense_lineup) != 5 or len(defense_lineup) != 5:
            return None

        return {
            'offense_player_1': offense_lineup[0] if len(offense_lineup) > 0 else None,
            'offense_player_2': offense_lineup[1] if len(offense_lineup) > 1 else None,
            'offense_player_3': offense_lineup[2] if len(offense_lineup) > 2 else None,
            'offense_player_4': offense_lineup[3] if len(offense_lineup) > 3 else None,
            'offense_player_5': offense_lineup[4] if len(offense_lineup) > 4 else None,
            'defense_player_1': defense_lineup[0] if len(defense_lineup) > 0 else None,
            'defense_player_2': defense_lineup[1] if len(defense_lineup) > 1 else None,
            'defense_player_3': defense_lineup[2] if len(defense_lineup) > 2 else None,
            'defense_player_4': defense_lineup[3] if len(defense_lineup) > 3 else None,
            'defense_player_5': defense_lineup[4] if len(defense_lineup) > 4 else None,
        }


class PossessionDetector:
    """Detect possession changes from event sequences"""

    POSSESSION_ENDING_EVENTS = [
        'made', 'field goal', 'free throw',
        'defensive rebound',
        'turnover',
        'end of'
    ]

    @staticmethod
    def is_end_of_free_throw_sequence(event_text: str) -> bool:
        """Check if this is the last free throw in a sequence"""
        if not event_text or 'free throw' not in event_text.lower():
            return False

        text_lower = event_text.lower()

        # Check for "X of Y" pattern
        if ' of ' in text_lower:
            import re
            match = re.search(r'(\d+)\s+of\s+(\d+)', text_lower)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                return current == total

        return True

    @staticmethod
    def is_possession_end(event_text: str, prev_score: tuple, curr_score: tuple,
                          next_event_text: str = None) -> bool:
        """Determine if this event ends a possession"""

        if not event_text:
            return False

        text_lower = event_text.lower()

        # Offensive rebound NEVER ends possession
        if 'off:' in text_lower and 'rebound' in text_lower:
            return False
        if 'offensive rebound' in text_lower:
            return False

        # Defensive rebound = possession change
        if 'def:' in text_lower and 'rebound' in text_lower:
            return True
        if 'defensive rebound' in text_lower:
            return True

        # Turnover = possession change
        if 'turnover' in text_lower:
            return True

        # End of quarter/period
        if 'end of' in text_lower:
            return True

        # Free throw: only end on LAST free throw
        if 'free throw' in text_lower:
            return PossessionDetector.is_end_of_free_throw_sequence(event_text)

        # And-1 detection
        if next_event_text and prev_score != curr_score:
            next_text_lower = next_event_text.lower()
            is_made_shot = (
                'made' in text_lower or
                'layup' in text_lower or
                'dunk' in text_lower or
                ('jumper' in text_lower and 'miss' not in text_lower)
            )
            next_is_ft = 'free throw' in next_text_lower

            if is_made_shot and next_is_ft:
                return False

        # Score changed = possession ended
        if prev_score != curr_score:
            return True

        return False

    @staticmethod
    def categorize_result(events: list, points: int) -> str:
        """Categorize possession result"""
        if points > 0:
            return 'made_fg'

        if not events:
            return 'other'

        last_event = events[-1].get('text', '').lower()

        if 'turnover' in last_event:
            return 'turnover'
        elif 'missed' in last_event or 'miss' in last_event:
            return 'miss'
        elif 'defensive rebound' in last_event:
            return 'miss'
        else:
            return 'other'


class PossessionPanelBuilder:
    """Build possession panel with hoopR lineups"""

    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
        self.detector = PossessionDetector()

    def get_games_to_process(self, limit: int = None) -> list:
        """Get games that have both Kaggle events AND hoopR starters (matched by date+teams)"""

        logger.info("Fetching game list (Kaggle events + hoopR starters matched by date)...")

        # Match Kaggle and hoopR games by date + teams (different game_id formats)
        query = """
        WITH kaggle_games AS (
            SELECT DISTINCT
                g.game_id as kaggle_game_id,
                g.game_date,
                g.season,
                g.home_team_id,
                g.away_team_id
            FROM games g
            WHERE EXISTS (
                SELECT 1 FROM temporal_events te
                WHERE te.game_id = g.game_id
                AND te.data_source = 'kaggle'
            )
        ),
        hoopr_games AS (
            SELECT DISTINCT
                hpb.game_id as hoopr_game_id,
                hpb.game_date,
                hpb.team_id,
                COUNT(*) FILTER (WHERE hpb.starter = true) as starter_count
            FROM hoopr_player_box hpb
            WHERE hpb.starter = true
            GROUP BY hpb.game_id, hpb.game_date, hpb.team_id
        )
        SELECT DISTINCT
            kg.kaggle_game_id,
            kg.game_date,
            kg.season,
            kg.home_team_id,
            kg.away_team_id,
            hg_home.hoopr_game_id as hoopr_game_id
        FROM kaggle_games kg
        -- Match home team by date
        JOIN hoopr_games hg_home
          ON kg.game_date = hg_home.game_date
          AND kg.home_team_id::text = hg_home.team_id::text
          AND hg_home.starter_count = 5
        -- Match away team by date
        JOIN hoopr_games hg_away
          ON kg.game_date = hg_away.game_date
          AND kg.away_team_id::text = hg_away.team_id::text
          AND hg_away.starter_count = 5
          AND hg_home.hoopr_game_id = hg_away.hoopr_game_id  -- Same game
        ORDER BY kg.game_date, kg.kaggle_game_id
        """

        if limit:
            query += f" LIMIT {limit}"

        import time
        start = time.time()

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        elapsed = time.time() - start

        logger.info(f"✓ Found {len(rows)} games with Kaggle events + hoopR starters (query took {elapsed:.1f}s)")

        # Convert to dict list
        games = []
        for row in rows:
            season_str = row[2]
            if season_str and isinstance(season_str, str) and '-' in season_str:
                season_int = int(season_str.split('-')[0])
            else:
                season_int = int(season_str) if season_str else None

            games.append({
                'game_id': row[0],  # Kaggle game_id
                'hoopr_game_id': row[5],  # hoopR game_id
                'game_date': row[1],
                'season': season_int,
                'home_team_id': row[3],
                'away_team_id': row[4]
            })

        return games

    def load_game_events(self, game_id: str) -> pd.DataFrame:
        """Load Kaggle events for a game"""

        query = """
        SELECT
            game_id,
            team_id,
            quarter,
            game_clock_seconds,
            wall_clock_utc,
            event_data
        FROM temporal_events
        WHERE game_id = %s
        AND data_source = 'kaggle'
        ORDER BY quarter ASC, game_clock_seconds DESC, event_id ASC
        """

        self.cursor.execute(query, (game_id,))
        rows = self.cursor.fetchall()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=[
            'game_id', 'team_id', 'quarter', 'game_clock_seconds',
            'wall_clock_utc', 'event_data'
        ])

        return df

    def process_game(self, game: dict) -> list:
        """Process a single game into possessions with lineups"""

        kaggle_game_id = game['game_id']
        hoopr_game_id = game['hoopr_game_id']

        # Initialize lineup tracker with hoopR starters
        lineup_tracker = LineupTracker(
            kaggle_game_id=kaggle_game_id,
            hoopr_game_id=hoopr_game_id,
            home_team_id=game['home_team_id'],
            away_team_id=game['away_team_id']
        )

        # Load starting lineups from hoopR
        if not lineup_tracker.initialize_from_hoopr(self.conn):
            logger.warning(f"Game {kaggle_game_id}: Could not initialize lineups from hoopR, skipping")
            return []

        # Load Kaggle events
        events_df = self.load_game_events(kaggle_game_id)

        if len(events_df) == 0:
            logger.warning(f"No Kaggle events found for game {kaggle_game_id}")
            return []

        logger.debug(f"Processing game {kaggle_game_id} with {len(events_df)} events")

        # Track possessions
        possessions = []
        current_possession = {
            'events': [],
            'team_id': None,
            'start_event': None,
            'start_score': (0, 0)
        }
        possession_number = 0

        prev_score = (0, 0)

        for idx, row in events_df.iterrows():
            event_data = row['event_data']
            if not isinstance(event_data, dict):
                continue

            # Extract event text
            event_text = (
                event_data.get('home_description', '') or
                event_data.get('visitor_description', '') or
                event_data.get('neutral_description', '') or
                ''
            )

            # Get next event text for and-1 detection
            next_event_text = None
            next_idx = idx + 1
            if next_idx in events_df.index:
                next_event_data = events_df.loc[next_idx, 'event_data']
                if isinstance(next_event_data, dict):
                    next_event_text = (
                        next_event_data.get('home_description', '') or
                        next_event_data.get('visitor_description', '') or
                        next_event_data.get('neutral_description', '') or
                        ''
                    )

            # Parse score
            score_str = event_data.get('score', '')
            if score_str and ' - ' in score_str:
                try:
                    parts = score_str.split(' - ')
                    home_score = int(parts[0].strip())
                    away_score = int(parts[1].strip())
                    curr_score = (home_score, away_score)
                except (ValueError, IndexError):
                    curr_score = prev_score
            else:
                curr_score = prev_score

            # Update lineups for substitution events
            if row['team_id']:
                lineup_tracker.update_lineup(event_text, row['team_id'])

            # Detect possession end
            is_possession_end = self.detector.is_possession_end(
                event_text, prev_score, curr_score, next_event_text
            )

            # Add event to current possession
            event_dict = {
                'text': event_text,
                'team_id': row['team_id'],
                'quarter': row['quarter'],
                'game_clock_seconds': row['game_clock_seconds'],
                'wall_clock_utc': row['wall_clock_utc'],
                'home_score': home_score if 'home_score' in locals() else 0,
                'away_score': away_score if 'away_score' in locals() else 0,
                'event_data': event_data
            }
            current_possession['events'].append(event_dict)

            if current_possession['team_id'] is None:
                current_possession['team_id'] = row['team_id']
                current_possession['start_event'] = row

            if is_possession_end and len(current_possession['events']) > 0:
                # Get current lineups
                offensive_team_id = current_possession['team_id'] or game['home_team_id']
                lineups = lineup_tracker.get_current_lineups(offensive_team_id)

                # Aggregate possession with lineups
                poss = self.aggregate_possession(
                    possession_events=current_possession['events'],
                    possession_number=possession_number,
                    game=game,
                    start_score=current_possession['start_score'],
                    end_score=curr_score,
                    lineups=lineups
                )

                if poss:
                    possessions.append(poss)
                    possession_number += 1

                # Start new possession
                current_possession = {
                    'events': [],
                    'team_id': None,
                    'start_event': None,
                    'start_score': curr_score
                }

            prev_score = curr_score

        # Handle last possession
        if len(current_possession['events']) > 0:
            offensive_team_id = current_possession['team_id'] or game['home_team_id']
            lineups = lineup_tracker.get_current_lineups(offensive_team_id)

            poss = self.aggregate_possession(
                current_possession['events'],
                possession_number,
                game,
                current_possession['start_score'],
                end_score=curr_score,
                lineups=lineups
            )
            if poss:
                possessions.append(poss)

        logger.debug(f"Game {kaggle_game_id}: extracted {len(possessions)} possessions with lineups")
        return possessions

    def aggregate_possession(self, possession_events: list,
                            possession_number: int,
                            game: dict,
                            start_score: tuple,
                            end_score: tuple,
                            lineups: dict = None) -> dict:
        """Aggregate events into possession observation with lineups"""

        if not possession_events:
            return None

        first_event = possession_events[0]
        last_event = possession_events[-1]

        # Calculate points scored
        score_change = (end_score[0] - start_score[0], end_score[1] - start_score[1])

        offensive_team_id = first_event['team_id']
        if offensive_team_id is None:
            offensive_team_id = game['home_team_id']

        is_home_offense = (offensive_team_id == game['home_team_id'])

        if is_home_offense:
            points_scored = score_change[0]
            defensive_team_id = game['away_team_id']
        else:
            points_scored = score_change[1]
            defensive_team_id = game['home_team_id']

        points_scored = max(0, points_scored)

        # Categorize result
        result = self.detector.categorize_result(possession_events, points_scored)

        # Calculate duration
        if last_event['game_clock_seconds'] is not None and first_event['game_clock_seconds'] is not None:
            duration = first_event['game_clock_seconds'] - last_event['game_clock_seconds']
            duration = max(0, duration)
        else:
            duration = None

        # Game state
        home_score, away_score = start_score

        if is_home_offense:
            score_diff = home_score - away_score
        else:
            score_diff = away_score - home_score

        quarter = first_event['quarter'] if first_event['quarter'] is not None else 1
        clock_seconds = first_event['game_clock_seconds'] if first_event['game_clock_seconds'] is not None else 0
        seconds_remaining = (4 - quarter) * 720 + clock_seconds

        game_seconds_elapsed = (quarter - 1) * 720 + (720 - clock_seconds)
        game_seconds_elapsed = max(0, game_seconds_elapsed)

        is_clutch = (abs(score_diff) <= 5 and seconds_remaining <= 300 and quarter >= 4)
        is_close = (abs(score_diff) <= 5)
        is_blowout = (abs(score_diff) >= 20)

        # Build possession record
        possession = {
            # Identifiers
            'game_id': game['game_id'],
            'possession_number': possession_number,

            # Time
            'game_date': game['game_date'],
            'season': game['season'],
            'period': quarter,
            'game_seconds_elapsed': game_seconds_elapsed,
            'seconds_remaining': max(0, seconds_remaining),

            # Teams
            'offensive_team_id': offensive_team_id,
            'defensive_team_id': defensive_team_id,

            # Outcomes
            'points_scored': points_scored,
            'possession_result': result,
            'possession_duration_seconds': duration,
            'shot_attempted': any('missed' in e['text'].lower() or 'made' in e['text'].lower()
                                 for e in possession_events),
            'shot_made': points_scored > 0,
            'shot_type': '3PT' if points_scored == 3 else ('2PT' if points_scored == 2 else None),
            'turnover': any('turnover' in e['text'].lower() for e in possession_events),
            'foul_drawn': any('foul' in e['text'].lower() for e in possession_events),
            'offensive_rebound': any('offensive rebound' in e['text'].lower() for e in possession_events),

            # Game state
            'score_differential': score_diff,
            'is_clutch': is_clutch,
            'is_close_game': is_close,
            'is_blowout': is_blowout,

            # Lineups (hoopR starters)
            'offense_player_1': lineups['offense_player_1'] if lineups else None,
            'offense_player_2': lineups['offense_player_2'] if lineups else None,
            'offense_player_3': lineups['offense_player_3'] if lineups else None,
            'offense_player_4': lineups['offense_player_4'] if lineups else None,
            'offense_player_5': lineups['offense_player_5'] if lineups else None,
            'defense_player_1': lineups['defense_player_1'] if lineups else None,
            'defense_player_2': lineups['defense_player_2'] if lineups else None,
            'defense_player_3': lineups['defense_player_3'] if lineups else None,
            'defense_player_4': lineups['defense_player_4'] if lineups else None,
            'defense_player_5': lineups['defense_player_5'] if lineups else None,

            # Metadata
            'is_home_offense': is_home_offense,
            'data_source': 'kaggle+hoopr',
        }

        return possession

    def build_panel(self, limit: int = None):
        """Main ETL pipeline"""

        logger.info("="*60)
        logger.info("Building Possession Panel with hoopR Lineups")
        logger.info("="*60)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get games to process
        games = self.get_games_to_process(limit=limit)

        if not games:
            logger.error("No games found with both Kaggle events and hoopR starters")
            return

        logger.info(f"Processing {len(games)} games...")

        # Process each game
        all_possessions = []
        import time

        for idx, game in enumerate(games):
            start_time = time.time()

            try:
                possessions = self.process_game(game)
                all_possessions.extend(possessions)

                elapsed = time.time() - start_time

                if limit and limit <= 20:
                    logger.info(f"  ✓ Game {idx+1}/{len(games)}: {game['game_id']} → {len(possessions)} possessions ({elapsed:.1f}s)")
                elif (idx + 1) % 10 == 0:
                    logger.info(f"  Progress: {idx+1}/{len(games)} games processed")

            except Exception as e:
                logger.error(f"Error processing game {game['game_id']}: {e}")
                import traceback
                traceback.print_exc()
                continue

        logger.info(f"\n✓ Extracted {len(all_possessions)} possessions from {len(games)} games")
        logger.info(f"  Average: {len(all_possessions)/len(games):.1f} possessions per game")

        # Convert to DataFrame
        logger.info("\nConverting to DataFrame...")
        df = pd.DataFrame(all_possessions)

        # Write to database
        logger.info(f"Writing {len(df)} possessions to database...")
        self.write_to_database(df)

        logger.info("\n" + "="*60)
        logger.info("✅ Possession panel build complete!")
        logger.info("="*60)
        logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return df

    def write_to_database(self, df: pd.DataFrame):
        """Write possession panel to database using COPY"""

        from io import StringIO

        # Get actual table columns
        self.cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'possession_panel'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        actual_table_columns = [row[0] for row in self.cursor.fetchall()]

        # Filter dataframe to only columns that exist in database
        df_write = df[[col for col in df.columns if col in actual_table_columns]].copy()

        # Convert float columns to int
        int_columns = [
            'possession_number', 'season', 'game_seconds_elapsed',
            'period', 'seconds_remaining', 'points_scored',
            'possession_duration_seconds', 'score_differential'
        ]

        for col in int_columns:
            if col in df_write.columns:
                df_write[col] = df_write[col].fillna(-999).astype(int)
                df_write[col] = df_write[col].replace(-999, None)

        # Create CSV buffer
        buffer = StringIO()
        df_write.to_csv(buffer, index=False, header=False, na_rep='\\N')
        buffer.seek(0)

        # Build column list
        columns = ','.join(df_write.columns)

        # COPY to table
        try:
            self.cursor.copy_expert(
                f"COPY possession_panel ({columns}) FROM STDIN WITH CSV NULL '\\N'",
                buffer
            )
            self.conn.commit()
            logger.info(f"✅ Wrote {len(df_write)} possessions to possession_panel table")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error writing to database: {e}")
            raise

    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()


def main():
    """CLI entry point"""

    parser = argparse.ArgumentParser(
        description='Build possession panel with hoopR lineups + Kaggle events'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of games to process (for testing)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--truncate',
        action='store_true',
        help='Truncate possession_panel table before loading'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate credentials
    if not DB_CONFIG['user']:
        logger.error("ERROR: Database user not found")
        sys.exit(1)

    # Build panel
    builder = PossessionPanelBuilder(DB_CONFIG)

    try:
        # Truncate table if requested
        if args.truncate:
            logger.info("Truncating possession_panel table...")
            builder.cursor.execute("TRUNCATE TABLE possession_panel")
            builder.conn.commit()
            logger.info("✓ Table truncated")

        df = builder.build_panel(limit=args.limit)

        # Print summary statistics
        if df is not None and len(df) > 0:
            print("\n" + "="*60)
            print("Summary Statistics")
            print("="*60)
            print(f"\nTotal possessions: {len(df):,}")
            print(f"\nGames processed: {df['game_id'].nunique():,}")
            print(f"Possessions per game: {len(df)/df['game_id'].nunique():.1f}")
            print(f"\nSeasons covered: {df['season'].min()} - {df['season'].max()}")
            print(f"\nPoints distribution:")
            print(df['points_scored'].value_counts().sort_index())
            print(f"\nPossession results:")
            print(df['possession_result'].value_counts())

            # Lineup coverage
            lineup_cols = [f'offense_player_{i}' for i in range(1, 6)] + [f'defense_player_{i}' for i in range(1, 6)]
            complete_lineups = df[lineup_cols].notna().all(axis=1).sum()
            print(f"\nPossessions with complete lineups: {complete_lineups:,} ({complete_lineups/len(df)*100:.1f}%)")

    finally:
        builder.close()


if __name__ == '__main__':
    main()
