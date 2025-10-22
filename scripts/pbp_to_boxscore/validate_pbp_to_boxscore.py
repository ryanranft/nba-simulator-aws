#!/usr/bin/env python3
"""
Play-by-Play to Box Score Validation & Demonstration

Purpose:
1. Process play-by-play data to generate box score snapshots
2. Validate final snapshots against actual box scores (from ESPN/NBA API)
3. Demonstrate temporal query capability (stats at any moment)
4. Extract player performance dynamics for ML
5. Generate quarter-level snapshots for betting models

This validates the core concept: "What were a player's stats at exactly 7:02 PM?"

Created: October 18, 2025
Phase: 9.0 (Validation)
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pbp_to_boxscore.espn_processor import ESPNPlayByPlayProcessor
from pbp_to_boxscore.box_score_snapshot import BoxScoreSnapshot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PBPValidator:
    """
    Validates PBP-to-box-score generation against actual box scores.

    Demonstrates the temporal capability that enables:
    - Query player stats at any exact moment
    - Track performance dynamics throughout the game
    - Generate snapshots for ML models
    - Create quarter-level analytics for betting
    """

    def __init__(self, s3_bucket: str = "nba-sim-raw-data-lake", local_cache: Optional[str] = None):
        self.processor = ESPNPlayByPlayProcessor(
            s3_bucket=s3_bucket,
            local_cache_dir=local_cache
        )
        self.validation_results = []

    def process_game(self, game_id: str) -> Dict[str, Any]:
        """
        Process a single game from PBP to snapshots.

        Returns:
            Dict with:
                - snapshots: List of box score snapshots (one per event)
                - quarter_snapshots: Dict of snapshots at quarter boundaries
                - final_snapshot: Final box score
                - game_info: Basic game information
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing game {game_id}")
        logger.info(f"{'='*70}\n")

        try:
            # Process PBP to snapshots
            logger.info("Loading PBP data...")
            snapshots = self.processor.process_game(game_id)

            if not snapshots:
                logger.error(f"No snapshots generated for game {game_id}")
                return {}

            logger.info(f"✓ Generated {len(snapshots)} snapshots")

            # Extract quarter boundaries
            quarter_snapshots = self._extract_quarter_snapshots(snapshots)

            # Final snapshot = last snapshot
            final_snapshot = snapshots[-1]

            return {
                'game_id': game_id,
                'snapshots': snapshots,
                'quarter_snapshots': quarter_snapshots,
                'final_snapshot': final_snapshot,
                'total_events': len(snapshots),
            }

        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            return {}

    def _extract_quarter_snapshots(self, snapshots: List[BoxScoreSnapshot]) -> Dict[int, BoxScoreSnapshot]:
        """
        Extract snapshots at end of each quarter.

        Returns:
            Dict: {1: Q1_snapshot, 2: Q2_snapshot, 3: Q3_snapshot, 4: Q4_snapshot}
        """
        quarter_snapshots = {}

        for snapshot in snapshots:
            period = snapshot.period

            # If we don't have this quarter yet, or this is later in the quarter
            if period not in quarter_snapshots:
                quarter_snapshots[period] = snapshot
            else:
                # Keep the latest snapshot for this quarter
                if snapshot.sequence_number > quarter_snapshots[period].sequence_number:
                    quarter_snapshots[period] = snapshot

        return quarter_snapshots

    def validate_against_actual_boxscore(self,
                                         game_id: str,
                                         final_snapshot: BoxScoreSnapshot,
                                         actual_boxscore: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare generated final box score against actual box score.

        Args:
            game_id: Game identifier
            final_snapshot: Generated final box score from PBP
            actual_boxscore: Actual box score (from ESPN/NBA API)

        Returns:
            Dict with validation results:
                - accuracy: Percentage match
                - discrepancies: List of differences
                - grade: A-F quality grade
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Validating game {game_id}")
        logger.info(f"{'='*70}\n")

        discrepancies = []
        total_stats_checked = 0
        stats_matched = 0

        # Compare team totals
        for team_id in ['home', 'away']:
            generated_team = (final_snapshot.home_team_stats if team_id == 'home'
                            else final_snapshot.away_team_stats)
            actual_team = actual_boxscore.get(f'{team_id}_team', {})

            for stat in ['points', 'fgm', 'fga', 'fg3m', 'fg3a', 'ftm', 'fta',
                        'oreb', 'dreb', 'reb', 'ast', 'stl', 'blk', 'tov', 'pf']:
                total_stats_checked += 1

                generated_val = getattr(generated_team, stat, 0)
                actual_val = actual_team.get(stat, 0)

                if generated_val == actual_val:
                    stats_matched += 1
                else:
                    discrepancies.append({
                        'team': team_id,
                        'stat': stat,
                        'generated': generated_val,
                        'actual': actual_val,
                        'diff': generated_val - actual_val
                    })

        # Calculate accuracy
        accuracy = (stats_matched / total_stats_checked * 100) if total_stats_checked > 0 else 0

        # Assign grade
        if accuracy >= 99.9:
            grade = 'A'
        elif accuracy >= 99.0:
            grade = 'B'
        elif accuracy >= 95.0:
            grade = 'C'
        elif accuracy >= 90.0:
            grade = 'D'
        else:
            grade = 'F'

        logger.info(f"Accuracy: {accuracy:.2f}%")
        logger.info(f"Grade: {grade}")
        logger.info(f"Stats matched: {stats_matched}/{total_stats_checked}")

        if discrepancies:
            logger.warning(f"Found {len(discrepancies)} discrepancies:")
            for disc in discrepancies[:5]:  # Show first 5
                logger.warning(f"  {disc['team']} {disc['stat']}: "
                             f"generated={disc['generated']}, actual={disc['actual']}")

        return {
            'game_id': game_id,
            'accuracy': accuracy,
            'grade': grade,
            'stats_checked': total_stats_checked,
            'stats_matched': stats_matched,
            'discrepancies': discrepancies
        }

    def demonstrate_temporal_queries(self, game_id: str, snapshots: List[BoxScoreSnapshot]):
        """
        Demonstrate the power of temporal snapshots.

        Shows:
        1. Player stats at specific moments
        2. Team performance progression
        3. Quarter-by-quarter dynamics
        4. In-game momentum shifts
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"TEMPORAL QUERY DEMONSTRATIONS - Game {game_id}")
        logger.info(f"{'='*70}\n")

        if not snapshots:
            logger.error("No snapshots available")
            return

        # Example 1: Stats at end of Q1
        q1_snapshots = [s for s in snapshots if s.period == 1]
        if q1_snapshots:
            q1_final = q1_snapshots[-1]
            logger.info("="*70)
            logger.info("Q1 FINAL BOX SCORE")
            logger.info("="*70)
            logger.info(f"Home: {q1_final.home_team_stats.points} points")
            logger.info(f"Away: {q1_final.away_team_stats.points} points")
            logger.info(f"Total events in Q1: {len(q1_snapshots)}")

        # Example 2: Halftime stats
        q2_snapshots = [s for s in snapshots if s.period == 2]
        if q2_snapshots:
            halftime = q2_snapshots[-1]
            logger.info("\n" + "="*70)
            logger.info("HALFTIME BOX SCORE")
            logger.info("="*70)
            logger.info(f"Home: {halftime.home_team_stats.points} points")
            logger.info(f"Away: {halftime.away_team_stats.points} points")

        # Example 3: Find the exact moment when home team scored their 50th point
        for snapshot in snapshots:
            if snapshot.home_team_stats.points >= 50:
                logger.info("\n" + "="*70)
                logger.info("MOMENT HOME TEAM REACHED 50 POINTS")
                logger.info("="*70)
                logger.info(f"Period: {snapshot.period}")
                logger.info(f"Time: {snapshot.game_clock}")
                logger.info(f"Score: {snapshot.home_team_stats.points} - {snapshot.away_team_stats.points}")
                logger.info(f"Event #: {snapshot.sequence_number}")
                break

        # Example 4: Performance dynamics - scoring rate by quarter
        logger.info("\n" + "="*70)
        logger.info("SCORING DYNAMICS BY QUARTER")
        logger.info("="*70)

        for period in range(1, 5):
            period_snapshots = [s for s in snapshots if s.period == period]
            if period_snapshots:
                start_score = 0 if period == 1 else [s for s in snapshots if s.period == period - 1][-1].home_team_stats.points
                end_score = period_snapshots[-1].home_team_stats.points
                quarter_points = end_score - start_score

                logger.info(f"Q{period}: {quarter_points} points scored by home team")

    def extract_player_dynamics(self, game_id: str, snapshots: List[BoxScoreSnapshot]) -> pd.DataFrame:
        """
        Extract player performance dynamics for ML analysis.

        Creates a time-series dataset showing how each player's stats evolved.
        This is the "nonparametric engine" data the user mentioned.

        Returns:
            DataFrame with columns:
                - game_id
                - player_id
                - player_name
                - event_number
                - period
                - time
                - points (cumulative)
                - fgm, fga, fg3m, fg3a, ftm, fta
                - reb, ast, stl, blk, tov, pf
                - plus_minus
                - on_court (boolean)
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Extracting player dynamics for ML")
        logger.info(f"{'='*70}\n")

        records = []

        for snapshot in snapshots:
            # Process all players in the snapshot
            for player_stats in snapshot.home_players.values():
                records.append({
                    'game_id': game_id,
                    'player_id': player_stats.player_id,
                    'player_name': player_stats.player_name,
                    'team': 'home',
                    'event_number': snapshot.sequence_number,
                    'period': snapshot.period,
                    'time': snapshot.game_clock,
                    'points': player_stats.points,
                    'fgm': player_stats.fgm,
                    'fga': player_stats.fga,
                    'fg3m': player_stats.fg3m,
                    'fg3a': player_stats.fg3a,
                    'ftm': player_stats.ftm,
                    'fta': player_stats.fta,
                    'reb': player_stats.reb,
                    'ast': player_stats.ast,
                    'stl': player_stats.stl,
                    'blk': player_stats.blk,
                    'tov': player_stats.tov,
                    'pf': player_stats.pf,
                    'plus_minus': player_stats.plus_minus,
                    'on_court': player_stats.on_court,
                })

            for player_stats in snapshot.away_players.values():
                records.append({
                    'game_id': game_id,
                    'player_id': player_stats.player_id,
                    'player_name': player_stats.player_name,
                    'team': 'away',
                    'event_number': snapshot.sequence_number,
                    'period': snapshot.period,
                    'time': snapshot.game_clock,
                    'points': player_stats.points,
                    'fgm': player_stats.fgm,
                    'fga': player_stats.fga,
                    'fg3m': player_stats.fg3m,
                    'fg3a': player_stats.fg3a,
                    'ftm': player_stats.ftm,
                    'fta': player_stats.fta,
                    'reb': player_stats.reb,
                    'ast': player_stats.ast,
                    'stl': player_stats.stl,
                    'blk': player_stats.blk,
                    'tov': player_stats.tov,
                    'pf': player_stats.pf,
                    'plus_minus': player_stats.plus_minus,
                    'on_court': player_stats.on_court,
                })

        df = pd.DataFrame(records)

        logger.info(f"Extracted {len(df)} player-event records")
        logger.info(f"Unique players: {df['player_id'].nunique()}")
        logger.info(f"Events tracked: {df['event_number'].nunique()}")

        return df

    def generate_ml_features(self, player_dynamics: pd.DataFrame) -> pd.DataFrame:
        """
        Generate ML features from player dynamics.

        Features include:
        - Momentum indicators (recent scoring rate)
        - Efficiency metrics (FG%, 3P%, FT%)
        - Usage patterns (shot attempts per period)
        - Performance trajectory (improving/declining)
        - Fatigue indicators (stats degradation over time)

        This enables ML models to understand player "nonparametric engines"
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Generating ML features from player dynamics")
        logger.info(f"{'='*70}\n")

        features = player_dynamics.copy()

        # Sort by player and event
        features = features.sort_values(['player_id', 'event_number'])

        # Calculate deltas (change since previous event)
        for col in ['points', 'fgm', 'fga', 'reb', 'ast', 'stl', 'blk', 'tov', 'pf']:
            features[f'{col}_delta'] = features.groupby('player_id')[col].diff().fillna(0)

        # Calculate efficiency metrics
        features['fg_pct'] = (features['fgm'] / features['fga'].replace(0, 1) * 100).fillna(0)
        features['fg3_pct'] = (features['fg3m'] / features['fg3a'].replace(0, 1) * 100).fillna(0)
        features['ft_pct'] = (features['ftm'] / features['fta'].replace(0, 1) * 100).fillna(0)

        # Rolling momentum (last 10 events)
        features['recent_points'] = features.groupby('player_id')['points_delta'].rolling(10, min_periods=1).sum().reset_index(drop=True)

        # Performance trajectory (comparing first half vs current)
        features['avg_points_first_half'] = features[features['period'] <= 2].groupby('player_id')['points'].transform('mean')
        features['avg_points_current_period'] = features.groupby(['player_id', 'period'])['points'].transform('mean')

        logger.info(f"Generated features with {len(features.columns)} columns")
        logger.info(f"Sample features: {list(features.columns[:10])}")

        return features


def main():
    """
    Main demonstration and validation.
    """
    print("\n" + "="*70)
    print("PLAY-BY-PLAY TO BOX SCORE VALIDATION")
    print("="*70)
    print("\nPurpose:")
    print("1. Validate PBP-to-box-score generation")
    print("2. Demonstrate temporal query capability")
    print("3. Extract player performance dynamics")
    print("4. Generate ML features")
    print("\n" + "="*70 + "\n")

    # Initialize validator
    validator = PBPValidator(local_cache="/tmp/espn_pbp_cache")

    # Test with a recent game (2024 Finals Game 1 - BOS vs DAL)
    # This game should be in S3 from our ESPN scraping
    test_game_id = "401584903"  # Adjust to actual game ID we have

    print(f"Testing with game: {test_game_id}")
    print("(This should be a 2024 Finals game)")
    print()

    # Step 1: Process game
    result = validator.process_game(test_game_id)

    if not result:
        print("\n❌ Failed to process game")
        print("This likely means:")
        print("  1. Game not found in S3")
        print("  2. PBP data is malformed")
        print("  3. Need to run ESPN scraper first")
        return

    snapshots = result['snapshots']
    quarter_snapshots = result['quarter_snapshots']
    final_snapshot = result['final_snapshot']

    print(f"\n✓ Processed {result['total_events']} events")
    print(f"✓ Generated {len(snapshots)} snapshots")
    print(f"✓ Extracted {len(quarter_snapshots)} quarter snapshots")

    # Step 2: Demonstrate temporal queries
    validator.demonstrate_temporal_queries(test_game_id, snapshots)

    # Step 3: Extract player dynamics
    player_dynamics = validator.extract_player_dynamics(test_game_id, snapshots)

    # Show sample
    print("\n" + "="*70)
    print("SAMPLE PLAYER DYNAMICS DATA")
    print("="*70)
    print(player_dynamics.head(10).to_string())

    # Step 4: Generate ML features
    ml_features = validator.generate_ml_features(player_dynamics)

    # Show sample ML features
    print("\n" + "="*70)
    print("SAMPLE ML FEATURES")
    print("="*70)
    print(ml_features[['player_name', 'period', 'points', 'points_delta',
                       'fg_pct', 'recent_points']].head(10).to_string())

    # Step 5: Save outputs for further analysis
    output_dir = Path("/tmp/pbp_validation_output")
    output_dir.mkdir(exist_ok=True)

    player_dynamics.to_csv(output_dir / f"{test_game_id}_player_dynamics.csv", index=False)
    ml_features.to_csv(output_dir / f"{test_game_id}_ml_features.csv", index=False)

    print("\n" + "="*70)
    print("OUTPUTS SAVED")
    print("="*70)
    print(f"Player dynamics: {output_dir / f'{test_game_id}_player_dynamics.csv'}")
    print(f"ML features: {output_dir / f'{test_game_id}_ml_features.csv'}")

    print("\n" + "="*70)
    print("✓ VALIDATION COMPLETE")
    print("="*70)
    print("\nKey Capabilities Demonstrated:")
    print("✓ Process PBP to generate box score snapshots")
    print("✓ Query player stats at any exact moment")
    print("✓ Extract player performance dynamics (nonparametric engines)")
    print("✓ Generate quarter-level snapshots for betting models")
    print("✓ Create ML features from temporal data")

    print("\nNext Steps:")
    print("1. Validate against actual box scores (need actual boxscore data)")
    print("2. Process full 2023-2025 seasons (~3,000 games)")
    print("3. Train ML models on player dynamics")
    print("4. Build betting models with quarter snapshots")


if __name__ == "__main__":
    main()
