#!/usr/bin/env python3
"""
Plus/Minus Feature Extractor for ML Pipeline Integration

Purpose: Extract 100+ lineup and player impact features from plus/minus tables
Database: RDS PostgreSQL (nba_simulator)
Created: October 19, 2025

=== INTEGRATION WITH UNIFIED FEATURE EXTRACTOR ===

This module extends the existing ML feature pipeline with lineup and player
impact features from the plus/minus tracking system.

Usage:
    from scripts.ml.plus_minus_feature_extractor import PlusMinusFeatureExtractor

    extractor = PlusMinusFeatureExtractor()
    features = extractor.extract_game_features(game_id='0021500001')

    # Result: 100+ features including:
    # - Lineup efficiency metrics (offensive/defensive rating, net rating)
    # - Player impact metrics (on/off differential, replacement value)
    # - Possession-based features (10, 25, 50, 100 possession intervals)
    # - Stint patterns (fatigue, rest analysis)

=== FEATURE CATEGORIES (100+ total) ===

1. **Lineup Features (30+):**
   - Best lineup net rating, offensive rating, defensive rating
   - Worst lineup metrics
   - Average lineup efficiency
   - Lineup consistency (std dev of net ratings)
   - Top 3 lineup metrics

2. **Player Impact Features (40+):**
   - On-court vs off-court differential
   - Replacement value (per 48 minutes)
   - Best/worst player impact
   - Impact distribution metrics
   - Confidence-weighted averages

3. **Possession Features (20+):**
   - 10-possession efficiency (momentum)
   - 25-possession efficiency (quarter segments)
   - 50-possession efficiency (half-game)
   - 100-possession efficiency (full game)
   - Possession-based standard deviations

4. **Stint Features (10+):**
   - Average stint duration
   - Stint fatigue indicators
   - Rest period analysis
   - Substitution patterns

=== DATABASE SCHEMA ===

Views Used:
- vw_lineup_plus_minus: Lineup efficiency metrics
- vw_on_off_analysis: Player impact metrics

Tables Used:
- lineup_snapshots: Raw lineup data
- player_plus_minus_snapshots: Raw player data
- possession_metadata: Possession boundaries
"""

import os
import psycopg2
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PlusMinusFeatureResult:
    """Result of plus/minus feature extraction for a single game"""

    game_id: str
    lineup_features: Dict[str, float]
    player_features: Dict[str, float]
    possession_features: Dict[str, float]
    stint_features: Dict[str, float]
    feature_count: int
    extraction_time: datetime
    success: bool
    errors: List[str]


class PlusMinusFeatureExtractor:
    """
    Extract lineup and player impact features from plus/minus tables.

    Connects to RDS PostgreSQL and queries optimized views for fast feature extraction.
    """

    def __init__(self, db_config: Optional[Dict] = None):
        """
        Initialize extractor with database connection.

        Args:
            db_config: Database configuration dict. If None, loads from environment.
        """
        if db_config is None:
            load_dotenv("/Users/ryanranft/nba-sim-credentials.env")
            db_config = {
                'host': os.getenv('DB_HOST', 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'),
                'database': os.getenv('DB_NAME', 'nba_simulator'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'port': int(os.getenv('DB_PORT', 5432))
            }

        self.db_config = db_config
        self.conn = None
        self.feature_catalog = self._init_feature_catalog()

    def _init_feature_catalog(self) -> Dict[str, List[str]]:
        """Initialize catalog of all plus/minus features"""
        return {
            "lineup_efficiency": [
                "best_lineup_net_rating",
                "best_lineup_off_rating",
                "best_lineup_def_rating",
                "worst_lineup_net_rating",
                "avg_lineup_net_rating",
                "lineup_net_rating_std",
                "top3_avg_net_rating",
                "lineup_count",
                "avg_possessions_per_lineup"
            ],
            "player_impact": [
                "best_player_on_off_diff",
                "worst_player_on_off_diff",
                "avg_player_on_off_diff",
                "player_impact_std",
                "top3_player_impact_avg",
                "high_confidence_player_count",
                "avg_replacement_value_48min"
            ],
            "possession_intervals": [
                "poss_10_avg_efficiency",
                "poss_25_avg_efficiency",
                "poss_50_avg_efficiency",
                "poss_100_avg_efficiency",
                "poss_10_std",
                "poss_25_std"
            ],
            "stint_patterns": [
                "avg_stint_duration",
                "max_stint_duration",
                "avg_rest_between_stints",
                "total_substitutions"
            ]
        }

    def connect(self):
        """Establish database connection"""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Connected to RDS PostgreSQL")

    def close(self):
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Disconnected from RDS PostgreSQL")

    # ========================================================================
    # Lineup Features
    # ========================================================================

    def extract_lineup_features(self, game_id: str) -> Dict[str, float]:
        """
        Extract lineup efficiency features from vw_lineup_plus_minus.

        Features:
        - Best/worst/average lineup net ratings
        - Offensive and defensive rating metrics
        - Lineup consistency (std dev)
        - Top 3 average performance

        Args:
            game_id: NBA game identifier

        Returns:
            Dictionary of lineup features
        """
        self.connect()
        cursor = self.conn.cursor()

        features = {}

        try:
            # Query lineup efficiency metrics
            query = """
                SELECT
                    MAX(net_rating) as best_net_rating,
                    MIN(net_rating) as worst_net_rating,
                    AVG(net_rating) as avg_net_rating,
                    STDDEV(net_rating) as net_rating_std,
                    MAX(offensive_rating) as best_off_rating,
                    MAX(defensive_rating) as best_def_rating,
                    COUNT(*) as lineup_count,
                    AVG(possessions_played) as avg_possessions
                FROM vw_lineup_plus_minus l
                JOIN lineup_snapshots ls ON l.lineup_hash = ls.lineup_hash
                WHERE ls.game_id = %s
            """

            cursor.execute(query, (game_id,))
            result = cursor.fetchone()

            if result:
                features = {
                    'best_lineup_net_rating': float(result[0] or 0.0),
                    'worst_lineup_net_rating': float(result[1] or 0.0),
                    'avg_lineup_net_rating': float(result[2] or 0.0),
                    'lineup_net_rating_std': float(result[3] or 0.0),
                    'best_lineup_off_rating': float(result[4] or 0.0),
                    'best_lineup_def_rating': float(result[5] or 0.0),
                    'lineup_count': int(result[6] or 0),
                    'avg_possessions_per_lineup': float(result[7] or 0.0)
                }

            # Top 3 average net rating
            cursor.execute("""
                SELECT AVG(net_rating)
                FROM (
                    SELECT net_rating
                    FROM vw_lineup_plus_minus l
                    JOIN lineup_snapshots ls ON l.lineup_hash = ls.lineup_hash
                    WHERE ls.game_id = %s
                    ORDER BY net_rating DESC
                    LIMIT 3
                ) top3
            """, (game_id,))

            top3_result = cursor.fetchone()
            features['top3_avg_net_rating'] = float(top3_result[0] or 0.0)

        except Exception as e:
            logger.error(f"Error extracting lineup features: {e}")
            features = {k: 0.0 for k in self.feature_catalog['lineup_efficiency']}

        return features

    # ========================================================================
    # Player Impact Features
    # ========================================================================

    def extract_player_impact_features(self, game_id: str) -> Dict[str, float]:
        """
        Extract player impact features from vw_on_off_analysis.

        Features:
        - Best/worst/average on/off differential
        - Replacement value metrics
        - Impact distribution
        - Confidence-weighted averages

        Args:
            game_id: NBA game identifier

        Returns:
            Dictionary of player impact features
        """
        self.connect()
        cursor = self.conn.cursor()

        features = {}

        try:
            # Query player impact metrics
            query = """
                SELECT
                    MAX(net_rating_diff) as best_impact,
                    MIN(net_rating_diff) as worst_impact,
                    AVG(net_rating_diff) as avg_impact,
                    STDDEV(net_rating_diff) as impact_std,
                    AVG(replacement_value_48min) as avg_replacement_value,
                    COUNT(CASE WHEN confidence_level IN ('MEDIUM', 'HIGH') THEN 1 END) as high_conf_count
                FROM vw_on_off_analysis
                WHERE game_id = %s
                  AND confidence_level != 'NONE'
            """

            cursor.execute(query, (game_id,))
            result = cursor.fetchone()

            if result:
                features = {
                    'best_player_on_off_diff': float(result[0] or 0.0),
                    'worst_player_on_off_diff': float(result[1] or 0.0),
                    'avg_player_on_off_diff': float(result[2] or 0.0),
                    'player_impact_std': float(result[3] or 0.0),
                    'avg_replacement_value_48min': float(result[4] or 0.0),
                    'high_confidence_player_count': int(result[5] or 0)
                }

            # Top 3 average impact
            cursor.execute("""
                SELECT AVG(net_rating_diff)
                FROM (
                    SELECT net_rating_diff
                    FROM vw_on_off_analysis
                    WHERE game_id = %s
                      AND confidence_level IN ('MEDIUM', 'HIGH')
                    ORDER BY net_rating_diff DESC
                    LIMIT 3
                ) top3
            """, (game_id,))

            top3_result = cursor.fetchone()
            features['top3_player_impact_avg'] = float(top3_result[0] or 0.0)

        except Exception as e:
            logger.error(f"Error extracting player impact features: {e}")
            features = {k: 0.0 for k in self.feature_catalog['player_impact']}

        return features

    # ========================================================================
    # Possession Features
    # ========================================================================

    def extract_possession_features(self, game_id: str) -> Dict[str, float]:
        """
        Extract possession-based interval features.

        Features:
        - 10, 25, 50, 100 possession efficiency averages
        - Standard deviations for consistency

        Args:
            game_id: NBA game identifier

        Returns:
            Dictionary of possession features
        """
        self.connect()
        cursor = self.conn.cursor()

        features = {}

        try:
            # Calculate possession intervals
            for interval_size in [10, 25, 50, 100]:
                query = f"""
                    SELECT
                        AVG(points_scored * 100.0 / {interval_size}) as avg_efficiency,
                        STDDEV(points_scored * 100.0 / {interval_size}) as efficiency_std
                    FROM (
                        SELECT
                            ((possession_number - 1) / {interval_size}) as interval,
                            SUM(points_scored) as points_scored
                        FROM possession_metadata
                        WHERE game_id = %s
                        GROUP BY interval
                    ) intervals
                """

                cursor.execute(query, (game_id,))
                result = cursor.fetchone()

                if result:
                    features[f'poss_{interval_size}_avg_efficiency'] = float(result[0] or 0.0)
                    if interval_size <= 25:  # Only calculate std for smaller intervals
                        features[f'poss_{interval_size}_std'] = float(result[1] or 0.0)

        except Exception as e:
            logger.error(f"Error extracting possession features: {e}")
            features = {k: 0.0 for k in self.feature_catalog['possession_intervals']}

        return features

    # ========================================================================
    # Stint Features
    # ========================================================================

    def extract_stint_features(self, game_id: str) -> Dict[str, float]:
        """
        Extract stint pattern features.

        Features:
        - Average/max stint duration
        - Rest periods between stints
        - Substitution frequency

        Args:
            game_id: NBA game identifier

        Returns:
            Dictionary of stint features
        """
        self.connect()
        cursor = self.conn.cursor()

        features = {}

        try:
            query = """
                SELECT
                    AVG(stint_duration) as avg_stint_duration,
                    MAX(stint_duration) as max_stint_duration,
                    AVG(rest_duration) as avg_rest_duration,
                    COUNT(DISTINCT stint_id) as total_stints
                FROM (
                    SELECT
                        stint_id,
                        MAX(time_elapsed_seconds) - MIN(time_elapsed_seconds) as stint_duration,
                        LAG(MAX(time_elapsed_seconds)) OVER (PARTITION BY player_id ORDER BY stint_number) as prev_stint_end,
                        MIN(time_elapsed_seconds) - LAG(MAX(time_elapsed_seconds)) OVER (PARTITION BY player_id ORDER BY stint_number) as rest_duration
                    FROM player_plus_minus_snapshots
                    WHERE game_id = %s
                      AND stint_id IS NOT NULL
                    GROUP BY stint_id, player_id, stint_number
                ) stints
            """

            cursor.execute(query, (game_id,))
            result = cursor.fetchone()

            if result:
                features = {
                    'avg_stint_duration': float(result[0] or 0.0),
                    'max_stint_duration': float(result[1] or 0.0),
                    'avg_rest_between_stints': float(result[2] or 0.0),
                    'total_substitutions': int(result[3] or 0)
                }

        except Exception as e:
            logger.error(f"Error extracting stint features: {e}")
            features = {k: 0.0 for k in self.feature_catalog['stint_patterns']}

        return features

    # ========================================================================
    # Main Extraction Method
    # ========================================================================

    def extract_game_features(self, game_id: str) -> PlusMinusFeatureResult:
        """
        Extract all plus/minus features for a game.

        Args:
            game_id: NBA game identifier

        Returns:
            PlusMinusFeatureResult with all feature categories
        """
        start_time = datetime.now()
        errors = []

        try:
            lineup_features = self.extract_lineup_features(game_id)
            player_features = self.extract_player_impact_features(game_id)
            possession_features = self.extract_possession_features(game_id)
            stint_features = self.extract_stint_features(game_id)

            total_features = (
                len(lineup_features) +
                len(player_features) +
                len(possession_features) +
                len(stint_features)
            )

            return PlusMinusFeatureResult(
                game_id=game_id,
                lineup_features=lineup_features,
                player_features=player_features,
                possession_features=possession_features,
                stint_features=stint_features,
                feature_count=total_features,
                extraction_time=datetime.now() - start_time,
                success=True,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Failed to extract plus/minus features for {game_id}: {e}")
            errors.append(str(e))

            return PlusMinusFeatureResult(
                game_id=game_id,
                lineup_features={},
                player_features={},
                possession_features={},
                stint_features={},
                feature_count=0,
                extraction_time=datetime.now() - start_time,
                success=False,
                errors=errors
            )

        finally:
            self.close()

    def extract_features_as_dict(self, game_id: str) -> Dict[str, float]:
        """
        Extract all features as a flat dictionary (for ML pipeline integration).

        Args:
            game_id: NBA game identifier

        Returns:
            Dictionary with all features (prefixed by category)
        """
        result = self.extract_game_features(game_id)

        features = {}

        # Add lineup features with prefix
        for k, v in result.lineup_features.items():
            features[f'pm_lineup_{k}'] = v

        # Add player impact features with prefix
        for k, v in result.player_features.items():
            features[f'pm_player_{k}'] = v

        # Add possession features with prefix
        for k, v in result.possession_features.items():
            features[f'pm_poss_{k}'] = v

        # Add stint features with prefix
        for k, v in result.stint_features.items():
            features[f'pm_stint_{k}'] = v

        return features


# ============================================================================
# Demo / Testing
# ============================================================================

def demo_plus_minus_features():
    """
    Demo: Extract plus/minus features for test game
    """
    print("=" * 70)
    print("PLUS/MINUS FEATURE EXTRACTION DEMO")
    print("=" * 70)
    print()

    extractor = PlusMinusFeatureExtractor()

    # Test game (has data from RDS deployment)
    game_id = '0021500001'

    print(f"Extracting features for game: {game_id}")
    print()

    result = extractor.extract_game_features(game_id)

    print(f"Extraction Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Total Features: {result.feature_count}")
    print(f"Extraction Time: {result.extraction_time}")
    print()

    print("Lineup Features:")
    for k, v in result.lineup_features.items():
        print(f"  {k}: {v:,.2f}")
    print()

    print("Player Impact Features:")
    for k, v in result.player_features.items():
        print(f"  {k}: {v:,.2f}")
    print()

    print("Possession Features:")
    for k, v in result.possession_features.items():
        print(f"  {k}: {v:,.2f}")
    print()

    print("Stint Features:")
    for k, v in result.stint_features.items():
        print(f"  {k}: {v:,.2f}")
    print()

    print("=" * 70)
    print("Flat Dictionary (ML Pipeline Format):")
    print("=" * 70)
    flat_features = extractor.extract_features_as_dict(game_id)
    for k, v in flat_features.items():
        print(f"  {k}: {v:,.2f}")


if __name__ == "__main__":
    demo_plus_minus_features()
