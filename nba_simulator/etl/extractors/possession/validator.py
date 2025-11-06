"""
Phase 0.0005: Possession Extraction - Dean Oliver Validator

Validates possession counts using Dean Oliver's formula from
"Basketball on Paper":

Possessions ≈ FGA + 0.44*FTA - OREB + TOV

This validator checks if extracted possessions match expected counts
within acceptable tolerance (typically ±5%).

Author: NBA Simulator AWS Team
Created: November 5, 2025
"""

import logging
from typing import Dict, List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of Dean Oliver validation for a single game."""

    game_id: str
    extracted_possessions: int
    expected_possessions_home: float
    expected_possessions_away: float
    home_error_pct: float
    away_error_pct: float
    passes: bool
    notes: str = ""


class DeanOliverValidator:
    """
    Validates possession counts using Dean Oliver formula.

    Formula per team:
        Possessions ≈ FGA + 0.44*FTA - OREB + TOV

    Where:
        FGA = Field Goal Attempts
        FTA = Free Throw Attempts
        OREB = Offensive Rebounds
        TOV = Turnovers
    """

    def __init__(self, tolerance_pct: float = 5.0):
        """
        Initialize validator.

        Args:
            tolerance_pct: Acceptable error percentage (default: 5%)
        """
        self.tolerance_pct = tolerance_pct
        self.conn = None
        self.cursor = None

    def connect(self, conn_string: str) -> bool:
        """
        Connect to database.

        Args:
            conn_string: PostgreSQL connection string

        Returns:
            True if successful
        """
        try:
            self.conn = psycopg2.connect(conn_string)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Connected to database for validation")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_box_score_stats(self, game_id: str) -> Dict[str, Dict]:
        """
        Get box score statistics needed for Dean Oliver formula.

        Args:
            game_id: Game identifier

        Returns:
            Dict with 'home' and 'away' team stats
        """
        # This is a simplified version - in practice, you'd query from
        # your box score table or calculate from events
        query = """
            SELECT
                team_id,
                SUM(CASE WHEN event_type LIKE '%shot%' OR event_type LIKE '%field goal%' THEN 1 ELSE 0 END) as fga,
                SUM(CASE WHEN event_type LIKE '%free throw%' THEN 1 ELSE 0 END) as fta,
                SUM(CASE WHEN event_type LIKE '%offensive rebound%' THEN 1 ELSE 0 END) as oreb,
                SUM(CASE WHEN event_type LIKE '%turnover%' THEN 1 ELSE 0 END) as tov
            FROM temporal_events
            WHERE game_id = %s
            GROUP BY team_id
        """

        self.cursor.execute(query, (game_id,))
        rows = self.cursor.fetchall()

        stats = {}
        for row in rows:
            stats[row["team_id"]] = {
                "fga": row["fga"] or 0,
                "fta": row["fta"] or 0,
                "oreb": row["oreb"] or 0,
                "tov": row["tov"] or 0,
            }

        return stats

    def calculate_expected_possessions(self, stats: Dict) -> float:
        """
        Calculate expected possessions using Dean Oliver formula.

        Args:
            stats: Dict with 'fga', 'fta', 'oreb', 'tov' keys

        Returns:
            Expected number of possessions (float)
        """
        fga = stats.get("fga", 0)
        fta = stats.get("fta", 0)
        oreb = stats.get("oreb", 0)
        tov = stats.get("tov", 0)

        # Dean Oliver formula
        possessions = fga + 0.44 * fta - oreb + tov

        return possessions

    def get_extracted_possessions(self, game_id: str) -> Dict[str, int]:
        """
        Get extracted possession counts from temporal_possession_stats.

        Args:
            game_id: Game identifier

        Returns:
            Dict with team_id -> possession count
        """
        query = """
            SELECT
                offensive_team_id,
                COUNT(*) as possession_count
            FROM temporal_possession_stats
            WHERE game_id = %s
            GROUP BY offensive_team_id
        """

        self.cursor.execute(query, (game_id,))
        rows = self.cursor.fetchall()

        counts = {}
        for row in rows:
            counts[row["offensive_team_id"]] = row["possession_count"]

        return counts

    def validate_game(self, game_id: str) -> ValidationResult:
        """
        Validate possession counts for a single game.

        Args:
            game_id: Game identifier

        Returns:
            ValidationResult object
        """
        # Get box score stats for Dean Oliver formula
        team_stats = self.get_box_score_stats(game_id)

        # Get extracted possession counts
        extracted_counts = self.get_extracted_possessions(game_id)

        # Identify home/away teams (simplified - could query from game metadata)
        team_ids = list(team_stats.keys())
        if len(team_ids) != 2:
            logger.warning(f"Game {game_id}: Expected 2 teams, found {len(team_ids)}")
            return ValidationResult(
                game_id=game_id,
                extracted_possessions=sum(extracted_counts.values()),
                expected_possessions_home=0,
                expected_possessions_away=0,
                home_error_pct=0,
                away_error_pct=0,
                passes=False,
                notes="Could not identify both teams",
            )

        home_team_id = team_ids[0]
        away_team_id = team_ids[1]

        # Calculate expected possessions
        expected_home = self.calculate_expected_possessions(team_stats[home_team_id])
        expected_away = self.calculate_expected_possessions(team_stats[away_team_id])

        # Get extracted counts
        extracted_home = extracted_counts.get(home_team_id, 0)
        extracted_away = extracted_counts.get(away_team_id, 0)

        # Calculate error percentages
        home_error_pct = (
            abs((extracted_home - expected_home) / expected_home * 100)
            if expected_home > 0
            else 0
        )
        away_error_pct = (
            abs((extracted_away - expected_away) / expected_away * 100)
            if expected_away > 0
            else 0
        )

        # Check if within tolerance
        passes = (
            home_error_pct <= self.tolerance_pct
            and away_error_pct <= self.tolerance_pct
        )

        notes = ""
        if not passes:
            notes = (
                f"Home error: {home_error_pct:.1f}%, Away error: {away_error_pct:.1f}%"
            )

        return ValidationResult(
            game_id=game_id,
            extracted_possessions=extracted_home + extracted_away,
            expected_possessions_home=expected_home,
            expected_possessions_away=expected_away,
            home_error_pct=home_error_pct,
            away_error_pct=away_error_pct,
            passes=passes,
            notes=notes,
        )

    def validate_all_games(self) -> Tuple[int, int, List[ValidationResult]]:
        """
        Validate all games in database.

        Returns:
            Tuple of (total_games, passed_games, failed_results)
        """
        # Get all game IDs
        self.cursor.execute(
            """
            SELECT DISTINCT game_id
            FROM temporal_possession_stats
            ORDER BY game_id
        """
        )
        game_ids = [row["game_id"] for row in self.cursor.fetchall()]

        logger.info(f"Validating {len(game_ids)} games with Dean Oliver formula")

        passed = 0
        failed_results = []

        for i, game_id in enumerate(game_ids, 1):
            result = self.validate_game(game_id)

            if result.passes:
                passed += 1
            else:
                failed_results.append(result)

            # Progress logging
            if i % 100 == 0:
                logger.info(
                    f"Validated {i}/{len(game_ids)} games ({passed/i*100:.1f}% pass rate)"
                )

        logger.info(
            f"Validation complete: {passed}/{len(game_ids)} games passed ({passed/len(game_ids)*100:.1f}%)"
        )

        return len(game_ids), passed, failed_results

    def check_orphaned_events(self) -> int:
        """
        Check for events not assigned to any possession.

        Returns:
            Count of orphaned events
        """
        query = """
            SELECT COUNT(*) as orphaned_count
            FROM temporal_events te
            WHERE NOT EXISTS (
                SELECT 1
                FROM temporal_possession_stats tps
                WHERE te.game_id = tps.game_id
                  AND te.event_id >= tps.start_event_id
                  AND te.event_id <= tps.end_event_id
            )
        """

        self.cursor.execute(query)
        result = self.cursor.fetchone()
        orphaned_count = result["orphaned_count"]

        if orphaned_count > 0:
            logger.warning(
                f"Found {orphaned_count:,} orphaned events not in any possession"
            )
        else:
            logger.info("No orphaned events found - all events assigned to possessions")

        return orphaned_count

    def validate_possession_chains(self) -> Tuple[int, List[str]]:
        """
        Validate that possessions form proper chains (no gaps, no overlaps).

        Returns:
            Tuple of (error_count, list of game_ids with errors)
        """
        query = """
            WITH possession_gaps AS (
                SELECT
                    game_id,
                    possession_number,
                    end_event_id as curr_end,
                    LEAD(start_event_id) OVER (PARTITION BY game_id ORDER BY possession_number) as next_start
                FROM temporal_possession_stats
            )
            SELECT
                game_id,
                COUNT(*) as gap_count
            FROM possession_gaps
            WHERE next_start IS NOT NULL
              AND curr_end != next_start - 1  -- Gap or overlap detected
            GROUP BY game_id
        """

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        error_count = len(results)
        error_games = [row["game_id"] for row in results]

        if error_count > 0:
            logger.warning(f"Found possession chain errors in {error_count} games")
        else:
            logger.info("All possession chains valid - no gaps or overlaps")

        return error_count, error_games

    def generate_report(self) -> Dict:
        """
        Generate comprehensive validation report.

        Returns:
            Dict with validation statistics
        """
        logger.info("Generating validation report...")

        # Dean Oliver validation
        total_games, passed_games, failed_results = self.validate_all_games()

        # Orphaned events check
        orphaned_count = self.check_orphaned_events()

        # Chain validation
        chain_errors, error_games = self.validate_possession_chains()

        report = {
            "dean_oliver_validation": {
                "total_games": total_games,
                "passed_games": passed_games,
                "failed_games": len(failed_results),
                "pass_rate_pct": (
                    (passed_games / total_games * 100) if total_games > 0 else 0
                ),
                "tolerance_pct": self.tolerance_pct,
                "failed_game_ids": [r.game_id for r in failed_results[:10]],  # First 10
            },
            "orphaned_events": {"count": orphaned_count},
            "possession_chains": {
                "games_with_errors": chain_errors,
                "error_game_ids": error_games[:10],  # First 10
            },
            "overall_status": (
                "PASS"
                if passed_games / total_games >= 0.95
                and orphaned_count == 0
                and chain_errors == 0
                else "FAIL"
            ),
        }

        # Log summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Dean Oliver Validation Report")
        logger.info("=" * 60)
        logger.info(f"Games validated: {total_games:,}")
        logger.info(
            f"Games passed: {passed_games:,} ({report['dean_oliver_validation']['pass_rate_pct']:.1f}%)"
        )
        logger.info(f"Orphaned events: {orphaned_count:,}")
        logger.info(f"Chain errors: {chain_errors} games")
        logger.info(f"Overall status: {report['overall_status']}")
        logger.info("=" * 60)

        return report
