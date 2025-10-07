"""
Create Possession Panel from ESPN Temporal Events

Aggregates ESPN play-by-play events into possession-level observations
for econometric ML training.

Features:
1. Detects possession changes by tracking score changes and team switches
2. Calculates possession outcomes (points, result, duration)
3. Extracts game state at possession start
4. Handles missing data gracefully (no lineup tracking initially)

Usage:
    python scripts/etl/create_possession_panel_from_espn.py --limit 100  # Test on 100 games
    python scripts/etl/create_possession_panel_from_espn.py              # Process all games
"""

import os
import sys
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Database config
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', 5432)
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
    def is_possession_end(event_text: str, prev_score: tuple, curr_score: tuple) -> bool:
        """
        Determine if this event ends a possession

        Args:
            event_text: Event description
            prev_score: (home, away) before event
            curr_score: (home, away) after event

        Returns:
            True if possession ends
        """
        if not event_text:
            return False

        text_lower = event_text.lower()

        # Score changed = possession ended with points
        if prev_score != curr_score:
            return True

        # Defensive rebound = possession change
        if 'defensive rebound' in text_lower:
            return True

        # Turnover = possession change
        if 'turnover' in text_lower:
            return True

        # End of quarter/period
        if 'end of' in text_lower:
            return True

        return False

    @staticmethod
    def extract_points_from_event(event_text: str) -> int:
        """Extract points scored from event text"""
        if not event_text:
            return 0

        text_lower = event_text.lower()

        if 'three point' in text_lower or '3-pt' in text_lower:
            if 'made' in text_lower:
                return 3
        elif 'two point' in text_lower or 'layup' in text_lower or 'dunk' in text_lower:
            if 'made' in text_lower:
                return 2
        elif 'free throw' in text_lower:
            if 'made' in text_lower:
                return 1

        return 0

    @staticmethod
    def categorize_result(events: list, points: int) -> str:
        """Categorize possession result"""
        if points > 0:
            return 'made_fg'

        # Check last event
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
    """Build possession panel from ESPN temporal events"""

    def __init__(self, db_config: dict):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
        self.detector = PossessionDetector()

    def get_games_to_process(self, limit: int = None) -> list:
        """Get list of games to process"""

        logger.info("Fetching game list from database...")

        # Use games table directly instead of DISTINCT on temporal_events
        # Much faster query
        query = """
        SELECT
            g.game_id,
            g.game_date,
            g.season,
            g.home_team_id,
            g.away_team_id
        FROM games g
        WHERE EXISTS (
            SELECT 1 FROM temporal_events te
            WHERE te.game_id = g.game_id
            AND te.data_source = 'espn'
        )
        ORDER BY g.game_date, g.game_id
        """

        if limit:
            query += f" LIMIT {limit}"

        import time
        start = time.time()

        # Use cursor for faster execution
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        elapsed = time.time() - start

        logger.info(f"✓ Found {len(rows)} games to process (query took {elapsed:.1f}s)")

        # Convert to dict list
        games = []
        for row in rows:
            # Convert season from "2013-14" to 2013
            season_str = row[2]
            if season_str and isinstance(season_str, str) and '-' in season_str:
                season_int = int(season_str.split('-')[0])
            else:
                season_int = int(season_str) if season_str else None

            games.append({
                'game_id': row[0],
                'game_date': row[1],
                'season': season_int,
                'home_team_id': row[3],
                'away_team_id': row[4]
            })

        return games

    def load_game_events(self, game_id: str) -> pd.DataFrame:
        """Load all events for a game"""

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
        AND data_source = 'espn'
        ORDER BY quarter, game_clock_seconds DESC, event_id
        """

        # Use cursor instead of pandas for faster loading
        self.cursor.execute(query, (game_id,))
        rows = self.cursor.fetchall()

        # Convert to DataFrame manually
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=[
            'game_id', 'team_id', 'quarter', 'game_clock_seconds',
            'wall_clock_utc', 'event_data'
        ])

        return df

    def process_game(self, game: dict) -> list:
        """Process a single game into possessions"""

        game_id = game['game_id']

        # Load events
        events_df = self.load_game_events(game_id)

        if len(events_df) == 0:
            logger.warning(f"No events found for game {game_id}")
            return []

        logger.debug(f"Processing game {game_id} with {len(events_df)} events")

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

            event_text = event_data.get('text', '')
            home_score = event_data.get('homeScore', 0) or 0
            away_score = event_data.get('awayScore', 0) or 0
            curr_score = (home_score, away_score)

            # Detect possession end
            is_possession_end = self.detector.is_possession_end(
                event_text, prev_score, curr_score
            )

            if is_possession_end and len(current_possession['events']) > 0:
                # Finalize possession
                poss = self.aggregate_possession(
                    possession_events=current_possession['events'],
                    possession_number=possession_number,
                    game=game,
                    start_score=current_possession['start_score']
                )

                if poss:
                    possessions.append(poss)
                    possession_number += 1

                # Start new possession
                current_possession = {
                    'events': [],
                    'team_id': row['team_id'],
                    'start_event': row,
                    'start_score': curr_score
                }

            # Add event to current possession
            event_dict = {
                'text': event_text,
                'team_id': row['team_id'],
                'quarter': row['quarter'],
                'game_clock_seconds': row['game_clock_seconds'],
                'wall_clock_utc': row['wall_clock_utc'],
                'home_score': home_score,
                'away_score': away_score,
                'event_data': event_data
            }
            current_possession['events'].append(event_dict)

            if current_possession['team_id'] is None:
                current_possession['team_id'] = row['team_id']
                current_possession['start_event'] = row

            prev_score = curr_score

        # Handle last possession
        if len(current_possession['events']) > 0:
            poss = self.aggregate_possession(
                current_possession['events'],
                possession_number,
                game,
                current_possession['start_score']
            )
            if poss:
                possessions.append(poss)

        logger.debug(f"Game {game_id}: extracted {len(possessions)} possessions")
        return possessions

    def aggregate_possession(self, possession_events: list,
                            possession_number: int,
                            game: dict,
                            start_score: tuple) -> dict:
        """Aggregate events into a single possession observation"""

        if not possession_events:
            return None

        first_event = possession_events[0]
        last_event = possession_events[-1]

        # Calculate points scored
        points_scored = 0
        for event in possession_events:
            points = self.detector.extract_points_from_event(event['text'])
            points_scored += points

        # Alternative: use score differential
        score_change = (last_event['home_score'] - first_event['home_score'],
                       last_event['away_score'] - first_event['away_score'])

        # Determine which team scored
        offensive_team_id = first_event['team_id']

        # If first event team is None, try to infer from game data
        if offensive_team_id is None:
            # Default to home team
            offensive_team_id = game['home_team_id']

        is_home_offense = (offensive_team_id == game['home_team_id'])

        if is_home_offense:
            points_scored = score_change[0]
            defensive_team_id = game['away_team_id']
        else:
            points_scored = score_change[1]
            defensive_team_id = game['home_team_id']

        # Ensure non-negative
        points_scored = max(0, points_scored)

        # Categorize result
        result = self.detector.categorize_result(possession_events, points_scored)

        # Calculate duration
        if first_event['game_clock_seconds'] and last_event['game_clock_seconds']:
            duration = first_event['game_clock_seconds'] - last_event['game_clock_seconds']
            duration = max(0, duration)  # Ensure non-negative
        else:
            duration = None

        # Calculate game state
        home_score, away_score = first_event['home_score'], first_event['away_score']

        if is_home_offense:
            score_diff = home_score - away_score
        else:
            score_diff = away_score - home_score

        # Calculate time remaining
        quarter = first_event['quarter'] if first_event['quarter'] is not None else 1
        clock_seconds = first_event['game_clock_seconds'] if first_event['game_clock_seconds'] is not None else 0
        seconds_remaining = (4 - quarter) * 720 + clock_seconds

        # Game seconds elapsed (ensure all values are numeric)
        game_seconds_elapsed = (quarter - 1) * 720 + (720 - clock_seconds)
        game_seconds_elapsed = max(0, game_seconds_elapsed)  # Ensure non-negative

        # Clutch indicator
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

            # Teams (lineups will be NULL for now)
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

            # Metadata
            'is_home_offense': is_home_offense,
            'data_source': 'espn',

            # All other fields will be NULL initially (filled during enrichment)
        }

        return possession

    def build_panel(self, limit: int = None):
        """Main ETL pipeline"""

        logger.info("="*60)
        logger.info("Building Possession Panel from ESPN Events")
        logger.info("="*60)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get games to process
        games = self.get_games_to_process(limit=limit)

        if not games:
            logger.error("No games found to process")
            return

        logger.info(f"Processing {len(games)} games...")

        # Process each game
        all_possessions = []
        import time
        total_events_processed = 0

        for idx, game in enumerate(games):
            start_time = time.time()

            try:
                possessions = self.process_game(game)
                all_possessions.extend(possessions)

                elapsed = time.time() - start_time

                # Log progress every game for small batches, every 10 games for larger batches
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

        # Select only columns that exist in the table
        table_columns = [
            'game_id', 'possession_number', 'game_date', 'season',
            'game_seconds_elapsed', 'period', 'seconds_remaining',
            'offensive_team_id', 'defensive_team_id',
            'points_scored', 'possession_result', 'possession_duration_seconds',
            'shot_attempted', 'shot_made', 'shot_type',
            'turnover', 'foul_drawn', 'offensive_rebound',
            'score_differential', 'is_clutch', 'is_close_game', 'is_blowout',
            'is_home_offense', 'data_source'
        ]

        # Filter to existing columns
        df_write = df[[col for col in table_columns if col in df.columns]].copy()

        # Convert float columns to int (PostgreSQL doesn't accept "0.0" for INTEGER columns)
        int_columns = [
            'possession_number', 'season', 'game_seconds_elapsed',
            'period', 'seconds_remaining', 'points_scored',
            'possession_duration_seconds', 'score_differential'
        ]

        for col in int_columns:
            if col in df_write.columns:
                # Convert to int, handling NaN values
                df_write[col] = df_write[col].fillna(-999).astype(int)
                # Convert -999 back to None for PostgreSQL NULL
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
        description='Build possession panel from ESPN temporal events'
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

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate credentials
    if not DB_CONFIG['user'] or not DB_CONFIG['password']:
        logger.error("ERROR: Database credentials not found in .env file")
        sys.exit(1)

    # Build panel
    builder = PossessionPanelBuilder(DB_CONFIG)

    try:
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
            print(f"\nClutch possessions: {df['is_clutch'].sum():,} ({df['is_clutch'].sum()/len(df)*100:.1f}%)")

    finally:
        builder.close()


if __name__ == '__main__':
    main()
