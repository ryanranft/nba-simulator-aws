"""
hoopR Play-by-Play to Box Score Processor

Processes hoopR play-by-play data from RDS PostgreSQL into box score snapshots.
Covers 2002-2025 games with focus on 2023-2025 for cross-validation with ESPN.

Created: October 13, 2025
Phase: 9.2 (hoopR Processor)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import os

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.pbp_to_boxscore.base_processor import BasePlayByPlayProcessor
from scripts.pbp_to_boxscore.box_score_snapshot import (
    BoxScoreSnapshot,
    VerificationResult,
    TeamStats,
)

logger = logging.getLogger(__name__)


class HoopRPlayByPlayProcessor(BasePlayByPlayProcessor):
    """
    Processor for hoopR play-by-play data from RDS PostgreSQL.

    hoopR data structure (based on actual RDS table):
    - Location: RDS PostgreSQL hoopr_play_by_play table (13M rows)
    - Date Range: 2002-2025 (focus on 2023-2025 for validation)
    - Format: PostgreSQL rows with standardized columns

    Key fields:
    - game_id: Game identifier
    - sequence_number: Event sequence
    - type_text: Event type (Substitution, Free Throw, etc.)
    - text: Play description
    - period_number: Quarter/period number
    - clock_display_value: Time remaining (e.g., "0:42.0")
    - away_score/home_score: Current scores
    - athlete_id_1/athlete_id_2/athlete_id_3: Player IDs involved
    - team_id: Team identifier
    - scoring_play: Boolean (is this a scoring play?)
    - score_value: Points scored (for scoring plays)
    """

    def __init__(self):
        """
        Initialize hoopR processor with RDS connection.
        """
        super().__init__(data_source="hoopr")

        # Load credentials from external file
        load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

        # Database configuration
        self.db_config = {
            "host": os.getenv(
                "DB_HOST", "nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com"
            ),
            "database": os.getenv("DB_NAME", "nba_simulator"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "port": os.getenv("DB_PORT", 5432),
            "sslmode": "require",
        }

    # ========================================================================
    # ABSTRACT METHODS IMPLEMENTATION
    # ========================================================================

    def load_game_data(self, game_id: str) -> Dict[str, Any]:
        """
        Load hoopR game data from RDS PostgreSQL.

        Args:
            game_id: hoopR game ID (e.g., '400278393')

        Returns:
            Dict with game data and events list

        Raises:
            FileNotFoundError: If game data not found
            ValueError: If game data is malformed
        """
        self.logger.debug(f"Loading hoopR game {game_id} from RDS")

        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get game events ordered by sequence
            cur.execute(
                """
                SELECT * FROM hoopr_play_by_play
                WHERE game_id = %s
                ORDER BY sequence_number::integer
            """,
                (int(game_id),),
            )

            events = cur.fetchall()

            if not events:
                raise FileNotFoundError(f"No hoopR data found for game {game_id}")

            # Convert to list of dicts
            events_list = [dict(event) for event in events]

            # Extract game metadata from first event
            first_event = events_list[0]
            game_data = {
                "game_id": game_id,
                "away_team_id": first_event["away_team_id"],
                "away_team_name": first_event["away_team_name"],
                "away_team_abbrev": first_event["away_team_abbrev"],
                "home_team_id": first_event["home_team_id"],
                "home_team_name": first_event["home_team_name"],
                "home_team_abbrev": first_event["home_team_abbrev"],
                "game_date": first_event["game_date"],
                "events": events_list,
            }

            self.logger.info(f"Loaded {len(events_list)} events for game {game_id}")
            return game_data

        except Exception as e:
            self.logger.error(f"Error loading hoopR game {game_id}: {e}")
            raise
        finally:
            cur.close()
            conn.close()

    def parse_event(self, event: Dict[str, Any], event_num: int) -> Dict[str, Any]:
        """
        Parse a hoopR event into standardized format.

        Args:
            event: Raw hoopR event data
            event_num: Sequential event number

        Returns:
            Dict with standardized event fields
        """
        # Parse time remaining (e.g., "0:42.0" -> seconds)
        time_remaining = event["clock_display_value"]
        game_clock_seconds = self._parse_time_to_seconds(time_remaining)

        # Determine event type
        event_type = self._map_hoopr_event_type(event["type_text"])

        # Extract player and team info
        player_id = str(event["athlete_id_1"]) if event["athlete_id_1"] else None
        team_id = (
            str(int(event["team_id"])) if event["team_id"] else None
        )  # Convert float to int then string

        # Calculate points for scoring plays
        points = event["score_value"] if event["scoring_play"] else 0

        # Determine stat updates based on event type
        stat_updates = self._get_stat_updates_for_event(event_type, event)

        # Handle substitutions
        substitution = None
        if event_type == "substitution":
            substitution = {
                "player_in": (
                    str(event["athlete_id_1"]) if event["athlete_id_1"] else None
                ),
                "player_out": (
                    str(event["athlete_id_2"]) if event["athlete_id_2"] else None
                ),
                "team_id": team_id,
            }

        return {
            "event_num": event_num,
            "event_type": event_type,
            "quarter": event["period_number"],
            "time_remaining": time_remaining,
            "game_clock_seconds": game_clock_seconds,
            "player_id": player_id,
            "team_id": team_id,
            "points": points,
            "stat_updates": stat_updates,
            "substitution": substitution,
            "description": event["text"],
            "raw_event": event,  # Keep original for debugging
        }

    def get_initial_state(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get initial game state for hoopR data.

        Args:
            game_data: Game data from load_game_data

        Returns:
            Dict with initial game state
        """
        away_team_id = str(game_data["away_team_id"])
        home_team_id = str(game_data["home_team_id"])

        # For hoopR, we'll start with empty stats and let the events build them up
        # This is different from ESPN where we might have starting lineups

        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_team_name": game_data["home_team_name"],
            "away_team_name": game_data["away_team_name"],
            "starting_lineups": {
                home_team_id: [],  # We don't have starting lineup info in hoopR
                away_team_id: [],
            },
            "player_info": {},  # We'll build this as we process events
        }

    def get_actual_box_score(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Load actual box score for verification.

        Args:
            game_id: Game identifier

        Returns:
            Dict with actual box score or None if not available
        """
        # For hoopR, we can get final stats from the last event
        # or query a separate box score table if it exists
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get final scores from last event
            cur.execute(
                """
                SELECT away_score, home_score, away_team_id, home_team_id
                FROM hoopr_play_by_play
                WHERE game_id = %s
                ORDER BY sequence_number::integer DESC
                LIMIT 1
            """,
                (int(game_id),),
            )

            result = cur.fetchone()
            if not result:
                return None

            # Return final box score as dictionary
            return {
                "game_id": game_id,
                "away_team_id": str(result["away_team_id"]),
                "home_team_id": str(result["home_team_id"]),
                "away_score": result["away_score"],
                "home_score": result["home_score"],
                "final": True,
            }

        except Exception as e:
            self.logger.error(f"Error getting actual box score for game {game_id}: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _parse_time_to_seconds(self, time_str: str) -> int:
        """
        Parse time string (e.g., "0:42.0") to total seconds.

        Args:
            time_str: Time string in format "M:SS.S"

        Returns:
            Total seconds remaining in quarter
        """
        if not time_str or time_str == "":
            return 0

        try:
            # Handle format like "0:42.0" or "12:00.0"
            parts = time_str.split(":")
            minutes = int(parts[0])
            seconds_part = parts[1].split(".")[0]  # Remove decimal
            seconds = int(seconds_part)

            return minutes * 60 + seconds
        except (ValueError, IndexError):
            self.logger.warning(f"Could not parse time string: {time_str}")
            return 0

    def _map_hoopr_event_type(self, type_text: str) -> str:
        """
        Map hoopR event types to standardized event types.

        Args:
            type_text: hoopR event type text

        Returns:
            Standardized event type
        """
        type_mapping = {
            "Substitution": "substitution",
            "Free Throw - 1 of 1": "shot_made",
            "Free Throw - 1 of 2": "shot_made",
            "Free Throw - 2 of 2": "shot_made",
            "Free Throw - 3 of 3": "shot_made",
            "Free Throw - 1 of 3": "shot_made",
            "Free Throw - 2 of 3": "shot_made",
            "Free Throw - 3 of 3": "shot_made",
            "Free Throw - 1 of 1": "shot_made",
            "Free Throw - 2 of 2": "shot_made",
            "Free Throw - 3 of 3": "shot_made",
            "Missed Free Throw - 1 of 1": "shot_missed",
            "Missed Free Throw - 1 of 2": "shot_missed",
            "Missed Free Throw - 2 of 2": "shot_missed",
            "Missed Free Throw - 3 of 3": "shot_missed",
            "2-Point Field Goal": "shot_made",
            "3-Point Field Goal": "shot_made",
            "Missed 2-Point Field Goal": "shot_missed",
            "Missed 3-Point Field Goal": "shot_missed",
            "Rebound": "rebound",
            "Offensive Rebound": "rebound",
            "Defensive Rebound": "rebound",
            "Assist": "assist",
            "Steal": "steal",
            "Block": "block",
            "Turnover": "turnover",
            "Foul": "foul",
            "Technical Foul": "foul",
            "Flagrant Foul": "foul",
            "Timeout": "timeout",
            "Jump Ball": "jump_ball",
            "End of Period": "period_end",
            "Start of Period": "period_start",
        }

        return type_mapping.get(type_text, "unknown")

    def _get_stat_updates_for_event(
        self, event_type: str, event: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Get stat updates for a specific event type.

        Args:
            event_type: Standardized event type
            event: Raw event data

        Returns:
            Dict of stat updates
        """
        updates = {}

        if event_type == "shot_made":
            if "3-Point" in event["type_text"]:
                updates["fg3m"] = 1
                updates["fg3a"] = 1
                updates["pts"] = event["score_value"]
            else:
                updates["fg2m"] = 1
                updates["fg2a"] = 1
                updates["pts"] = event["score_value"]

        elif event_type == "shot_missed":
            if "3-Point" in event["type_text"]:
                updates["fg3a"] = 1
            else:
                updates["fg2a"] = 1

        elif event_type == "rebound":
            if "Offensive" in event["type_text"]:
                updates["oreb"] = 1
            else:
                updates["dreb"] = 1

        elif event_type == "assist":
            updates["ast"] = 1

        elif event_type == "steal":
            updates["stl"] = 1

        elif event_type == "block":
            updates["blk"] = 1

        elif event_type == "turnover":
            updates["tov"] = 1

        elif event_type == "foul":
            updates["pf"] = 1

        return updates

    # ========================================================================
    # CROSS-VALIDATION METHODS
    # ========================================================================

    def cross_validate_with_espn(self, game_id: str, espn_processor) -> Dict[str, Any]:
        """
        Cross-validate hoopR results with ESPN processor.

        Args:
            game_id: Game identifier
            espn_processor: ESPN processor instance

        Returns:
            Validation results
        """
        try:
            # Process game with both sources
            hoopr_snapshots = self.process_game(game_id)
            espn_snapshots = espn_processor.process_game(game_id)

            if not hoopr_snapshots or not espn_snapshots:
                return {
                    "status": "failed",
                    "reason": "No data from one or both sources",
                }

            # Compare final snapshots
            hoopr_final = hoopr_snapshots[-1]
            espn_final = espn_snapshots[-1]

            differences = self._compare_box_scores(hoopr_final, espn_final)

            return {
                "status": "success",
                "hoopr_events": len(hoopr_snapshots),
                "espn_events": len(espn_snapshots),
                "differences": differences,
                "total_diff": differences["total_difference"],
                "recommendation": self._get_recommendation(differences),
            }

        except Exception as e:
            self.logger.error(f"Cross-validation failed for game {game_id}: {e}")
            return {"status": "error", "error": str(e)}

    def _compare_box_scores(
        self, hoopr_snapshot: BoxScoreSnapshot, espn_snapshot: BoxScoreSnapshot
    ) -> Dict[str, Any]:
        """
        Compare two box score snapshots.

        Args:
            hoopr_snapshot: hoopR generated snapshot
            espn_snapshot: ESPN generated snapshot

        Returns:
            Detailed comparison results
        """
        differences = {
            "score_diff": abs(hoopr_snapshot.away_score - espn_snapshot.away_score)
            + abs(hoopr_snapshot.home_score - espn_snapshot.home_score),
            "total_difference": 0,
            "player_differences": {},
            "team_differences": {},
        }

        # Compare scores
        differences["total_difference"] += differences["score_diff"]

        # Compare team stats
        hoopr_team = hoopr_snapshot.away_team_stats
        espn_team = espn_snapshot.away_team_stats

        team_diff = (
            abs(hoopr_team.fg2m - espn_team.fg2m)
            + abs(hoopr_team.fg2a - espn_team.fg2a)
            + abs(hoopr_team.fg3m - espn_team.fg3m)
            + abs(hoopr_team.fg3a - espn_team.fg3a)
            + abs(hoopr_team.ftm - espn_team.ftm)
            + abs(hoopr_team.fta - espn_team.fta)
            + abs(hoopr_team.oreb - espn_team.oreb)
            + abs(hoopr_team.dreb - espn_team.dreb)
            + abs(hoopr_team.ast - espn_team.ast)
            + abs(hoopr_team.stl - espn_team.stl)
            + abs(hoopr_team.blk - espn_team.blk)
            + abs(hoopr_team.tov - espn_team.tov)
            + abs(hoopr_team.pf - espn_team.pf)
        )

        differences["team_differences"]["away"] = team_diff
        differences["total_difference"] += team_diff

        return differences

    def _get_recommendation(self, differences: Dict[str, Any]) -> str:
        """
        Get recommendation based on differences.

        Args:
            differences: Comparison results

        Returns:
            Recommendation string
        """
        total_diff = differences["total_difference"]

        if total_diff < 5:
            return "both_accurate"
        elif total_diff < 15:
            return "minor_differences"
        else:
            return "significant_differences"


# ========================================================================
# BATCH PROCESSING FUNCTIONS
# ========================================================================


def process_hoopr_games_batch(
    game_ids: List[str], output_dir: str = "/tmp/hoopr_box_scores"
) -> Dict[str, Any]:
    """
    Process multiple hoopR games in batch.

    Args:
        game_ids: List of game IDs to process
        output_dir: Output directory for results

    Returns:
        Batch processing results
    """
    processor = HoopRPlayByPlayProcessor()
    results = {"processed": 0, "failed": 0, "errors": [], "output_files": []}

    for game_id in game_ids:
        try:
            snapshots = processor.process_game(game_id)
            if snapshots:
                # Save to file
                output_file = f"{output_dir}/hoopr_game_{game_id}.json"
                # Implementation would save snapshots to JSON
                results["processed"] += 1
                results["output_files"].append(output_file)
            else:
                results["failed"] += 1
                results["errors"].append(f"Game {game_id}: No snapshots generated")

        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Game {game_id}: {str(e)}")

    return results


if __name__ == "__main__":
    # Test the processor
    processor = HoopRPlayByPlayProcessor()

    # Test with a sample game
    test_game_id = "400278393"  # From the sample data we saw earlier

    try:
        print(f"Testing hoopR processor with game {test_game_id}")
        snapshots, verification = processor.process_game(test_game_id)
        print(f"Generated {len(snapshots)} snapshots")

        if snapshots:
            final_snapshot = snapshots[-1]
            print(
                f"Final score: {final_snapshot.away_score} - {final_snapshot.home_score}"
            )
            print("✅ hoopR processor test successful!")
        else:
            print("❌ No snapshots generated")

    except Exception as e:
        print(f"❌ Test failed: {e}")
