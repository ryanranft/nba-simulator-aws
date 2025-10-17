"""
Create Possession Panel from NBA API Play-by-Play Data

Uses event type classification (like pbpstats) instead of text matching
for more accurate possession detection.

Key differences from Kaggle script:
1. Event type classification (EVENTMSGTYPE)
2. No text pattern matching
3. Proper and-1 detection
4. Accurate free throw sequence handling

Expected output: ~200-220 possessions per game (pbpstats baseline)
"""

import os
import json
import psycopg2
import pandas as pd
from datetime import datetime
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Local PostgreSQL database config
DB_CONFIG = {
    "host": "localhost",
    "dbname": "nba_simulator",
    "user": "ryanranft",
    "password": "",
    "port": 5432,
}

# NBA API Event Message Types
# https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/library/eventmsgtype.md
EVENT_MSG_TYPE = {
    1: "FIELD_GOAL_MADE",
    2: "FIELD_GOAL_MISSED",
    3: "FREE_THROW",
    4: "REBOUND",
    5: "TURNOVER",
    6: "FOUL",
    7: "VIOLATION",
    8: "SUBSTITUTION",
    9: "TIMEOUT",
    10: "JUMP_BALL",
    11: "EJECTION",
    12: "PERIOD_BEGIN",
    13: "PERIOD_END",
    18: "INSTANT_REPLAY",
}


class NBAAPIPossessionDetector:
    """Detect possessions from NBA API play-by-play events using event types"""

    @staticmethod
    def is_possession_end(event, next_event=None):
        """
        Determine if event ends a possession using event type classification

        Args:
            event: dict with EVENTMSGTYPE, EVENTMSGACTIONTYPE, etc.
            next_event: Next event dict (for and-1 detection)

        Returns:
            True if possession ends
        """
        event_type = event.get("EVENTMSGTYPE")
        event_action = event.get("EVENTMSGACTIONTYPE", 0)

        # Made field goal ends possession (unless it's an and-1)
        if event_type == 1:  # FIELD_GOAL_MADE
            # Check for and-1: made FG followed by FT
            if next_event and next_event.get("EVENTMSGTYPE") == 3:
                # This is an and-1 - FT will end the possession
                return False
            return True

        # Defensive rebound ends possession
        if event_type == 4:  # REBOUND
            # Check if it's a defensive rebound
            # In NBA API, EVENTMSGACTIONTYPE for rebounds:
            # 0 = defensive, 1 = offensive
            if event_action == 0:
                return True
            # Offensive rebound extends possession
            return False

        # Turnover ends possession
        if event_type == 5:  # TURNOVER
            return True

        # Free throw handling - only last FT ends possession
        if event_type == 3:  # FREE_THROW
            # Parse description to find if it's last FT
            desc = event.get("HOMEDESCRIPTION") or event.get("VISITORDESCRIPTION") or ""

            # Look for "X of X" pattern
            if " of " in desc:
                parts = desc.split(" of ")
                if len(parts) >= 2:
                    try:
                        current = int(parts[0].split()[-1])
                        total = int(parts[1].split()[0])
                        # Only last FT ends possession
                        return current == total
                    except (ValueError, IndexError):
                        pass

            # If we can't determine, assume it ends possession
            # (conservative approach)
            return True

        # Period end
        if event_type == 13:  # PERIOD_END
            return True

        # Everything else continues possession
        return False

    @staticmethod
    def categorize_possession_result(events):
        """
        Determine possession result from event sequence

        Returns: 'made_fg', 'miss', 'turnover', or 'other'
        """
        if not events:
            return "other"

        last_event = events[-1]
        event_type = last_event.get("EVENTMSGTYPE")

        if event_type == 1:  # Made FG
            return "made_fg"
        elif event_type == 2:  # Missed FG (with defensive rebound)
            return "miss"
        elif event_type == 5:  # Turnover
            return "turnover"
        else:
            return "other"  # Free throws, fouls, end of period, etc.


def extract_possessions_from_game(game_data):
    """
    Extract possessions from a single game

    Args:
        game_data: dict with play-by-play data from NBA API

    Returns:
        list of possession dicts
    """
    possessions = []

    try:
        game_id = game_data["parameters"]["GameID"]
        result_sets = game_data.get("resultSets", [])

        if not result_sets:
            logger.warning(f"No result sets for game {game_id}")
            return []

        pbp_data = result_sets[0]  # First result set is PlayByPlay
        headers = pbp_data["headers"]
        rows = pbp_data["rowSet"]

        # Convert to list of dicts
        events = [dict(zip(headers, row)) for row in rows]

        if not events:
            logger.warning(f"No events for game {game_id}")
            return []

        # Group events into possessions
        current_possession = {
            "events": [],
            "start_score": None,
            "offense_team_id": None,
        }

        possession_number = 0

        for i, event in enumerate(events):
            next_event = events[i + 1] if i + 1 < len(events) else None

            # Skip non-game events
            event_type = event.get("EVENTMSGTYPE")
            if event_type in [8, 9, 10, 11, 12, 18]:  # SUB, TIMEOUT, JUMP_BALL, etc.
                continue

            # Add event to current possession
            current_possession["events"].append(event)

            # Track offense team
            if current_possession["offense_team_id"] is None:
                # Use first player's team
                team_id = event.get("PLAYER1_TEAM_ID")
                if team_id:
                    current_possession["offense_team_id"] = team_id

            # Track start score
            if current_possession["start_score"] is None:
                score = event.get("SCORE")
                if score:
                    current_possession["start_score"] = score

            # Check if possession ends
            if NBAAPIPossessionDetector.is_possession_end(event, next_event):
                # Calculate possession stats
                end_score = event.get("SCORE") or current_possession["start_score"]
                start_score = current_possession["start_score"] or "0 - 0"

                # Parse scores
                try:
                    if start_score:
                        away_start, home_start = map(int, start_score.split(" - "))
                    else:
                        away_start, home_start = 0, 0

                    if end_score:
                        away_end, home_end = map(int, end_score.split(" - "))
                    else:
                        away_end, home_end = away_start, home_start

                    points_scored = (away_end - away_start) + (home_end - home_start)
                except (ValueError, AttributeError):
                    points_scored = 0

                # Create possession record
                possession = {
                    "game_id": game_id,
                    "possession_number": possession_number,
                    "period": event.get("PERIOD", 1),
                    "time_remaining": event.get("PCTIMESTRING"),
                    "offense_team_id": current_possession["offense_team_id"],
                    "start_score_margin": None,  # TODO: Calculate from scores
                    "points_scored": points_scored,
                    "possession_result": NBAAPIPossessionDetector.categorize_possession_result(
                        current_possession["events"]
                    ),
                    "num_events": len(current_possession["events"]),
                }

                possessions.append(possession)
                possession_number += 1

                # Reset for next possession
                current_possession = {
                    "events": [],
                    "start_score": end_score,
                    "offense_team_id": None,
                }

        logger.info(f"  Game {game_id}: extracted {len(possessions)} possessions")
        return possessions

    except Exception as e:
        logger.error(f"Error processing game {game_id}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Build possession panel from NBA API data"
    )
    parser.add_argument("--limit", type=int, help="Limit number of games to process")
    parser.add_argument(
        "--truncate", action="store_true", help="Truncate table before inserting"
    )
    parser.add_argument(
        "--data-dir",
        default="/tmp/nba_api_comprehensive/play_by_play",
        help="Directory containing NBA API play-by-play JSON files",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Building Possession Panel from NBA API Play-by-Play")
    logger.info("=" * 60)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Truncate table if requested
    if args.truncate:
        logger.info("Truncating possession_panel_nba_api table...")
        cur.execute("DROP TABLE IF EXISTS possession_panel_nba_api CASCADE")
        cur.execute(
            """
            CREATE TABLE possession_panel_nba_api (
                game_id VARCHAR(20),
                possession_number INTEGER,
                period INTEGER,
                time_remaining VARCHAR(10),
                offense_team_id BIGINT,
                start_score_margin INTEGER,
                points_scored INTEGER,
                possession_result VARCHAR(20),
                num_events INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        logger.info("✓ Table created")

    # Find all play-by-play files
    data_dir = Path(args.data_dir)
    pbp_files = sorted(data_dir.glob("play_by_play_*.json"))

    if args.limit:
        pbp_files = pbp_files[: args.limit]

    logger.info(f"Found {len(pbp_files)} games to process")

    # Process each game
    all_possessions = []

    for i, pbp_file in enumerate(pbp_files, 1):
        try:
            with open(pbp_file, "r") as f:
                game_data = json.load(f)

            possessions = extract_possessions_from_game(game_data)
            all_possessions.extend(possessions)

            if i % 50 == 0:
                logger.info(f"  Progress: {i}/{len(pbp_files)} games processed")

        except Exception as e:
            logger.error(f"Error reading {pbp_file}: {e}")

    logger.info(
        f"\n✓ Extracted {len(all_possessions):,} possessions from {len(pbp_files)} games"
    )
    logger.info(
        f"  Average: {len(all_possessions) / len(pbp_files):.1f} possessions per game"
    )

    # Convert to DataFrame and write to database
    if all_possessions:
        logger.info("\nConverting to DataFrame...")
        df = pd.DataFrame(all_possessions)

        # Fix data types
        df["offense_team_id"] = df["offense_team_id"].fillna(0).astype(int)
        df["start_score_margin"] = df["start_score_margin"].fillna(0).astype(int)

        logger.info(f"Writing {len(df):,} possessions to database...")

        # Write to database
        from io import StringIO

        buffer = StringIO()
        df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        cur.copy_from(
            buffer,
            "possession_panel_nba_api",
            sep=",",
            columns=[
                "game_id",
                "possession_number",
                "period",
                "time_remaining",
                "offense_team_id",
                "start_score_margin",
                "points_scored",
                "possession_result",
                "num_events",
            ],
        )
        conn.commit()

        logger.info(
            f"✅ Wrote {len(df):,} possessions to possession_panel_nba_api table"
        )

        # Print summary statistics
        logger.info("\n" + "=" * 60)
        logger.info("✅ Possession panel build complete!")
        logger.info("=" * 60)
        logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n" + "=" * 60)
        print("Summary Statistics")
        print("=" * 60)
        print(f"\nTotal possessions: {len(df):,}")
        print(f"\nGames processed: {len(pbp_files)}")
        print(f"Possessions per game: {len(df) / len(pbp_files):.1f}")
        print(f"\nPoints distribution:")
        print(df["points_scored"].value_counts().sort_index())
        print(f"\nPossession results:")
        print(df["possession_result"].value_counts())
        print()

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
