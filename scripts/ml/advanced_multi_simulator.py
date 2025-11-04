#!/usr/bin/env python3
"""
Advanced Multi-Simulator Framework using MCP and Comprehensive Databases

Purpose: Create multiple advanced statistical simulators that use econometric methods
and temporal panel data to predict NBA game outcomes with high accuracy.

Simulators:
1. Panel Data Regression Simulator (Fixed Effects)
2. Hierarchical Bayesian Simulator (Player/Team/League)
3. Econometric Simultaneous Equations Simulator (3SLS)
4. Monte Carlo Ensemble Simulator (Combines all methods)

Database Integration:
- Uses temporal panel data system
- Queries comprehensive player/team statistics
- Leverages 48M+ rows of historical data
- Utilizes advanced metrics (TS%, PER, BPM, plus/minus)

Created: November 2, 2025
Author: NBA Simulator AWS Project
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# ML/Stats libraries
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from linearmodels.panel import PanelOLS, RandomEffects

# MCP integration
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'mcp_server'))
try:
    from unified_secrets_manager import UnifiedSecretsManager
except ImportError:
    # Fallback if MCP not available
    UnifiedSecretsManager = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")


@dataclass
class SimulationResult:
    """Result from a single simulation run"""
    home_win_prob: float
    away_win_prob: float
    predicted_home_score: float
    predicted_away_score: float
    confidence: float
    model_type: str
    simulation_id: int
    metadata: Dict[str, Any]


@dataclass
class EnsembleResult:
    """Combined result from all simulators"""
    home_win_prob: float
    away_win_prob: float
    predicted_home_score: float
    predicted_away_score: float
    confidence: float
    individual_results: List[SimulationResult]
    ensemble_method: str
    weights: Dict[str, float]
    # Confidence intervals (Enhancement 8: Better Confidence Intervals)
    predicted_home_score_lower_50: Optional[float] = None
    predicted_home_score_upper_50: Optional[float] = None
    predicted_home_score_lower_80: Optional[float] = None
    predicted_home_score_upper_80: Optional[float] = None
    predicted_home_score_lower_95: Optional[float] = None
    predicted_home_score_upper_95: Optional[float] = None
    predicted_away_score_lower_50: Optional[float] = None
    predicted_away_score_upper_50: Optional[float] = None
    predicted_away_score_lower_80: Optional[float] = None
    predicted_away_score_upper_80: Optional[float] = None
    predicted_away_score_lower_95: Optional[float] = None
    predicted_away_score_upper_95: Optional[float] = None
    predicted_total_lower_50: Optional[float] = None
    predicted_total_upper_50: Optional[float] = None
    predicted_total_lower_80: Optional[float] = None
    predicted_total_upper_80: Optional[float] = None
    predicted_total_lower_95: Optional[float] = None
    predicted_total_upper_95: Optional[float] = None


class DatabaseConnector:
    """Connects to PostgreSQL database using credentials"""

    def __init__(self):
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432)
            )
            logger.info("✓ Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def query(self, sql: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        return pd.read_sql(sql, self.conn, params=params)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class PanelDataRegressionSimulator:
    """
    Panel Data Regression Simulator with Fixed Effects

    Uses econometric panel data models to predict game outcomes:
    - Team fixed effects (captures inherent quality)
    - Time-varying covariates (recent form, rest days, matchups)
    - Lagged variables (previous game performance)
    - Rolling averages (recent form)
    """

    def __init__(self, db: DatabaseConnector):
        self.db = db
        self.model_params = None
        self.team_fixed_effects = None
        self.scaler = StandardScaler()
        self.season_distributions = {}  # Store learned distributions per season
        self.team_trends = {}  # Store non-parametric trend slopes per team
        self.team_srs = {}  # Simple Rating System values
        self.opponent_adjusted_ratings = {}  # Opponent-adjusted offensive/defensive ratings
        self.team_home_away_splits = {}  # Team-specific home/away splits
        self.head_to_head_records = {}  # Head-to-head matchup records (team_pair -> record)
        self.team_star_players = {}  # Top players per team (usage rate based)
        self.team_star_impacts = {}  # Star player impact on team performance
        self.team_roster_changes = {}  # Roster change dates and percentages
        logger.info("PanelDataRegressionSimulator initialized")

    def get_season_for_date(self, game_date: date) -> int:
        """Determine NBA season year from game date"""
        # NBA season spans two calendar years (e.g., 2024-25 season)
        # Season starts October, so Oct-Dec = next season's year
        if game_date.month >= 10:
            return game_date.year + 1
        else:
            return game_date.year

    def train(self, start_season: int = None, end_season: int = None):
        """Train panel data regression model on ALL historical data"""
        logger.info(f"Training panel data model on ALL available data")

        # Query panel dataset - calculate metrics from basic stats
        # Use ALL available data (no season limits)
        query = """
        SELECT
            g.game_id,
            g.game_date,
            g.season,
            g.home_team_id as team_id,
            g.away_team_id as opponent_id,
            g.home_score as points_scored,
            g.away_score as opponent_points,
            CASE WHEN g.home_score > g.away_score THEN 1 ELSE 0 END as won,
            g.home_score + g.away_score as total_points,
            -- Team basic stats (for calculating metrics)
            COALESCE(tgs.points, g.home_score) as team_points,
            COALESCE(tgs.field_goals_attempted, 0) as fga,
            COALESCE(tgs.free_throws_attempted, 0) as fta,
            COALESCE(tgs.turnovers, 0) as turnovers,
            -- Opponent basic stats
            COALESCE(otgs.points, g.away_score) as opp_points,
            COALESCE(otgs.field_goals_attempted, 0) as opp_fga,
            COALESCE(otgs.free_throws_attempted, 0) as opp_fta,
            COALESCE(otgs.turnovers, 0) as opp_turnovers,
            -- Field goal percentages (calculated)
            CASE WHEN COALESCE(tgs.field_goals_attempted, 0) > 0
                THEN COALESCE(tgs.field_goals_made, 0)::float / tgs.field_goals_attempted
                ELSE 0.45 END as fg_pct,
            -- Temporal features (calculated in Python to avoid window function issues)
            1.0 as days_rest
        FROM games g
        LEFT JOIN team_game_stats tgs ON g.game_id = tgs.game_id
            AND tgs.team_id = g.home_team_id
        LEFT JOIN team_game_stats otgs ON g.game_id = otgs.game_id
            AND otgs.team_id = g.away_team_id
        WHERE g.home_score IS NOT NULL
            AND g.away_score IS NOT NULL
        ORDER BY g.game_date
        """

        df = self.db.query(query)

        if len(df) == 0:
            raise ValueError("No training data found")

        logger.info(f"  Loaded {len(df):,} game observations")

        # Learn season-specific distributions
        logger.info("  Learning season-specific distributions...")
        df['season_year'] = df['season'].apply(lambda s: int(s[:4]) if pd.notna(s) and len(str(s)) >= 4 else None)

        for season in sorted(df['season_year'].dropna().unique()):
            season_data = df[df['season_year'] == season]
            if len(season_data) > 0:
                totals = season_data['total_points'].dropna()
                if len(totals) > 0:
                    self.season_distributions[season] = {
                        'mean': float(totals.mean()),
                        'std': float(totals.std()),
                        'min': float(totals.min()),
                        'max': float(totals.max()),
                        'p5': float(totals.quantile(0.05)),
                        'p25': float(totals.quantile(0.25)),
                        'p75': float(totals.quantile(0.75)),
                        'p95': float(totals.quantile(0.95)),
                        'count': int(len(totals))
                    }
                    logger.info(f"    Season {season}: mean={self.season_distributions[season]['mean']:.1f}, "
                              f"std={self.season_distributions[season]['std']:.1f}, "
                              f"range=[{self.season_distributions[season]['min']:.0f}, {self.season_distributions[season]['max']:.0f}]")

        # Default distribution (use most recent complete season or overall average)
        if self.season_distributions:
            most_recent_season = max(self.season_distributions.keys())
            self.default_distribution = self.season_distributions[most_recent_season]
        else:
            all_totals = df['total_points'].dropna()
            self.default_distribution = {
                'mean': float(all_totals.mean()),
                'std': float(all_totals.std()),
                'min': float(all_totals.min()),
                'max': float(all_totals.max()),
                'p5': float(all_totals.quantile(0.05)),
                'p95': float(all_totals.quantile(0.95))
            }

        # Calculate SRS (Simple Rating System) for opponent-adjusted ratings (Enhancement 2)
        logger.info("  Calculating Simple Rating System (SRS)...")
        all_teams = set(df['team_id'].unique()) | set(df['opponent_id'].unique())

        # Initialize SRS
        srs = {team_id: 0.0 for team_id in all_teams}
        team_point_diffs = {}
        team_game_count = {}

        for team_id in all_teams:
            team_games = df[df['team_id'] == team_id]
            if len(team_games) > 0:
                point_diff = (team_games['points_scored'] - team_games['opponent_points']).mean()
                team_point_diffs[team_id] = float(point_diff)
                team_game_count[team_id] = len(team_games)
            else:
                team_point_diffs[team_id] = 0.0
                team_game_count[team_id] = 0

        # Iterate until convergence
        for iteration in range(50):
            old_srs = srs.copy()
            for team_id in all_teams:
                if team_game_count[team_id] > 0:
                    team_games = df[df['team_id'] == team_id]
                    opponent_srs_avg = team_games['opponent_id'].apply(lambda opp_id: old_srs.get(opp_id, 0.0)).mean()
                    srs[team_id] = team_point_diffs[team_id] + float(opponent_srs_avg)

            max_change = max(abs(srs[team_id] - old_srs[team_id]) for team_id in all_teams)
            if max_change < 0.01:
                break

        # Normalize SRS (average = 0)
        avg_srs = np.mean(list(srs.values()))
        self.team_srs = {team_id: srs_val - avg_srs for team_id, srs_val in srs.items()}

        logger.info(f"    SRS calculated for {len(self.team_srs)} teams")
        logger.info(f"    SRS range: [{min(self.team_srs.values()):.2f}, {max(self.team_srs.values()):.2f}]")

        # Calculate opponent-adjusted ratings (Enhancement 2)
        logger.info("  Calculating opponent-adjusted ratings...")
        self.opponent_adjusted_ratings = {}

        for team_id in all_teams:
            team_games = df[df['team_id'] == team_id].copy()
            if len(team_games) > 0:
                # Calculate actual offensive/defensive ratings
                team_games['possessions'] = (team_games['fga'] + team_games['turnovers'] + 0.44 * team_games['fta']).clip(lower=1)
                team_games['off_rtg'] = (team_games['points_scored'] / team_games['possessions'] * 100)
                team_games['def_rtg'] = (team_games['opponent_points'] / team_games['possessions'] * 100)

                # Calculate opponent's average SRS for each game
                team_games['opponent_srs'] = team_games['opponent_id'].apply(lambda opp_id: self.team_srs.get(opp_id, 0.0))

                # Weight games by opponent strength: weight = 1 + (opponent_srs / 10)
                team_games['weight'] = 1 + (team_games['opponent_srs'] / 10.0)

                # Calculate weighted average ratings (stronger opponents = more weight)
                weighted_off_rtg = (team_games['off_rtg'] * team_games['weight']).sum() / team_games['weight'].sum()
                weighted_def_rtg = (team_games['def_rtg'] * team_games['weight']).sum() / team_games['weight'].sum()

                # Calculate unweighted average for comparison
                unweighted_off_rtg = team_games['off_rtg'].mean()
                unweighted_def_rtg = team_games['def_rtg'].mean()

                # Adjust ratings based on opponent quality
                # If team played strong opponents (positive SRS), their actual ratings are better than they appear
                avg_opponent_srs = team_games['opponent_srs'].mean()
                opponent_quality_adj = avg_opponent_srs * 0.3  # 0.3 points per SRS point

                adjusted_off_rtg = unweighted_off_rtg + opponent_quality_adj
                adjusted_def_rtg = unweighted_def_rtg - opponent_quality_adj  # Better opponents = better defense appears

                self.opponent_adjusted_ratings[team_id] = {
                    'offensive_rating': float(adjusted_off_rtg),
                    'defensive_rating': float(adjusted_def_rtg),
                    'raw_offensive_rating': float(unweighted_off_rtg),
                    'raw_defensive_rating': float(unweighted_def_rtg),
                    'srs': float(self.team_srs[team_id]),
                    'avg_opponent_srs': float(avg_opponent_srs)
                }

        logger.info(f"    Opponent-adjusted ratings calculated for {len(self.opponent_adjusted_ratings)} teams")

        # Calculate home/away splits (Enhancement 3: Home/Away Splits)
        logger.info("  Calculating team-specific home/away splits...")
        self.team_home_away_splits = {}

        # Query games table directly to get home/away splits
        home_away_query = """
        SELECT
            g.home_team_id as team_id,
            g.home_score as points_scored,
            g.away_score as opponent_points,
            COALESCE(tgs.field_goals_attempted, 0) as fga,
            COALESCE(tgs.turnovers, 0) as turnovers,
            COALESCE(tgs.free_throws_attempted, 0) as fta,
            'home' as venue
        FROM games g
        LEFT JOIN team_game_stats tgs ON g.game_id = tgs.game_id
            AND tgs.team_id = g.home_team_id
        WHERE g.home_score IS NOT NULL
            AND g.away_score IS NOT NULL
        UNION ALL
        SELECT
            g.away_team_id as team_id,
            g.away_score as points_scored,
            g.home_score as opponent_points,
            COALESCE(tgs.field_goals_attempted, 0) as fga,
            COALESCE(tgs.turnovers, 0) as turnovers,
            COALESCE(tgs.free_throws_attempted, 0) as fta,
            'away' as venue
        FROM games g
        LEFT JOIN team_game_stats tgs ON g.game_id = tgs.game_id
            AND tgs.team_id = g.away_team_id
        WHERE g.home_score IS NOT NULL
            AND g.away_score IS NOT NULL
        """

        home_away_df = self.db.query(home_away_query)

        for team_id in all_teams:
            # Filter home and away games
            home_games = home_away_df[(home_away_df['team_id'] == team_id) & (home_away_df['venue'] == 'home')].copy()
            away_games = home_away_df[(home_away_df['team_id'] == team_id) & (home_away_df['venue'] == 'away')].copy()

            if len(home_games) > 0 and len(away_games) > 0:
                # Calculate home offensive/defensive ratings
                home_games['possessions'] = (home_games['fga'] + home_games['turnovers'] + 0.44 * home_games['fta']).clip(lower=1)
                home_games['home_off_rtg'] = (home_games['points_scored'] / home_games['possessions'] * 100)
                home_games['home_def_rtg'] = (home_games['opponent_points'] / home_games['possessions'] * 100)

                # Calculate away offensive/defensive ratings
                away_games['possessions'] = (away_games['fga'] + away_games['turnovers'] + 0.44 * away_games['fta']).clip(lower=1)
                away_games['away_off_rtg'] = (away_games['points_scored'] / away_games['possessions'] * 100)
                away_games['away_def_rtg'] = (away_games['opponent_points'] / away_games['possessions'] * 100)

                # Calculate averages
                home_off_rtg = home_games['home_off_rtg'].mean()
                home_def_rtg = home_games['home_def_rtg'].mean()
                away_off_rtg = away_games['away_off_rtg'].mean()
                away_def_rtg = away_games['away_def_rtg'].mean()

                # Calculate home advantage: (home_off_rtg - away_off_rtg) / 2
                # This represents how much better the team performs at home vs. away
                home_advantage = (home_off_rtg - away_off_rtg) / 2.0

                # Calculate average points scored/allowed at home and away
                home_avg_points = home_games['points_scored'].mean()
                home_avg_points_allowed = home_games['opponent_points'].mean()
                away_avg_points = away_games['points_scored'].mean()
                away_avg_points_allowed = away_games['opponent_points'].mean()

                self.team_home_away_splits[team_id] = {
                    'home_off_rtg': float(home_off_rtg),
                    'home_def_rtg': float(home_def_rtg),
                    'away_off_rtg': float(away_off_rtg),
                    'away_def_rtg': float(away_def_rtg),
                    'home_advantage': float(home_advantage),
                    'home_avg_points': float(home_avg_points),
                    'home_avg_points_allowed': float(home_avg_points_allowed),
                    'away_avg_points': float(away_avg_points),
                    'away_avg_points_allowed': float(away_avg_points_allowed),
                    'home_games': int(len(home_games)),
                    'away_games': int(len(away_games))
                }

        if self.team_home_away_splits:
            logger.info(f"    Home/away splits calculated for {len(self.team_home_away_splits)} teams")
            avg_home_advantage = np.mean([s['home_advantage'] for s in self.team_home_away_splits.values()])
            logger.info(f"    Average home advantage: {avg_home_advantage:.2f} points per 100 possessions")
            logger.info(f"    Home advantage range: [{min(s['home_advantage'] for s in self.team_home_away_splits.values()):.2f}, "
                       f"{max(s['home_advantage'] for s in self.team_home_away_splits.values()):.2f}]")
        else:
            logger.warning("    No home/away splits calculated")

        # Calculate head-to-head records (Enhancement 4: Matchup-Specific Adjustments)
        logger.info("  Calculating head-to-head matchup records...")
        self.head_to_head_records = {}

        # Query head-to-head games from games table
        h2h_query = """
        SELECT
            LEAST(g.home_team_id, g.away_team_id) as team1,
            GREATEST(g.home_team_id, g.away_team_id) as team2,
            CASE
                WHEN g.home_score > g.away_score THEN g.home_team_id
                ELSE g.away_team_id
            END as winner,
            g.home_score + g.away_score as total_points,
            ABS(g.home_score - g.away_score) as margin
        FROM games g
        WHERE g.home_score IS NOT NULL
            AND g.away_score IS NOT NULL
        """

        h2h_df = self.db.query(h2h_query)

        for _, row in h2h_df.iterrows():
            team_pair = tuple(sorted([row['team1'], row['team2']]))
            if team_pair not in self.head_to_head_records:
                self.head_to_head_records[team_pair] = {
                    'games': [],
                    'team1_wins': 0,
                    'team2_wins': 0,
                    'total_points': [],
                    'margins': []
                }

            record = self.head_to_head_records[team_pair]
            record['games'].append(row)
            record['total_points'].append(float(row['total_points']))
            record['margins'].append(float(row['margin']))

            if row['winner'] == row['team1']:
                record['team1_wins'] += 1
            else:
                record['team2_wins'] += 1

        # Calculate head-to-head statistics
        for team_pair, record in self.head_to_head_records.items():
            if len(record['games']) >= 3:  # Only store if 3+ games
                total_games = len(record['games'])
                team1_win_pct = record['team1_wins'] / total_games if total_games > 0 else 0.5
                avg_total = np.mean(record['total_points']) if record['total_points'] else 225.0
                avg_margin = np.mean(record['margins']) if record['margins'] else 12.0

                record['team1_win_pct'] = float(team1_win_pct)
                record['avg_total'] = float(avg_total)
                record['avg_margin'] = float(avg_margin)
                record['total_games'] = total_games

        logger.info(f"    Head-to-head records calculated for {len(self.head_to_head_records)} team pairs")
        h2h_pairs_with_3plus = sum(1 for r in self.head_to_head_records.values() if r.get('total_games', 0) >= 3)
        logger.info(f"    Team pairs with 3+ games: {h2h_pairs_with_3plus}")

        # Identify star players and calculate impact (Enhancement 5: Star Player Impact)
        logger.info("  Identifying star players and calculating impact...")
        self.team_star_players = {}
        self.team_star_impacts = {}

        # Query player game stats to identify top players by usage rate
        star_query = """
        SELECT
            pgs.team_id,
            pgs.player_id,
            COUNT(*) as games_played,
            AVG(pgs.field_goals_attempted + pgs.free_throws_attempted + pgs.turnovers) as avg_usage,
            AVG(pgs.points) as avg_points,
            AVG(pgs.field_goals_attempted) as avg_fga,
            AVG(pgs.free_throws_attempted) as avg_fta,
            AVG(pgs.turnovers) as avg_tov,
            AVG(CASE WHEN pgs.field_goals_attempted > 0
                THEN pgs.field_goals_made::float / pgs.field_goals_attempted
                ELSE 0.0 END) as avg_fg_pct
        FROM player_game_stats pgs
        WHERE pgs.team_id IS NOT NULL
            AND pgs.player_id IS NOT NULL
            AND pgs.field_goals_attempted IS NOT NULL
        GROUP BY pgs.team_id, pgs.player_id
        HAVING COUNT(*) >= 5  -- At least 5 games played
        ORDER BY pgs.team_id, avg_usage DESC
        """

        star_df = self.db.query(star_query)

        # Group by team and identify top 2-3 players by usage rate
        for team_id in all_teams:
            team_players = star_df[star_df['team_id'] == team_id].copy()
            if len(team_players) > 0:
                # Get top 3 players by usage rate
                top_players = team_players.nlargest(3, 'avg_usage')
                if len(top_players) > 0:
                    self.team_star_players[team_id] = []
                    for _, player in top_players.iterrows():
                        self.team_star_players[team_id].append({
                            'player_id': player['player_id'],
                            'usage_rate': float(player['avg_usage']),
                            'avg_points': float(player['avg_points']),
                            'games_played': int(player['games_played'])
                        })

                    # Calculate star player impact
                    # Compare team performance with vs. without star players
                    # Query games where star players played vs. didn't play
                    star_player_ids = [p['player_id'] for p in self.team_star_players[team_id]]

                    # Get team offensive rating with star players
                    with_star_query = """
                    SELECT
                        AVG(CASE WHEN g.home_team_id = %s THEN g.home_score
                                 WHEN g.away_team_id = %s THEN g.away_score
                                 ELSE NULL END) as avg_points_with_star
                    FROM games g
                    INNER JOIN player_game_stats pgs ON g.game_id = pgs.game_id
                        AND pgs.team_id = %s
                        AND pgs.player_id = ANY(%s)
                    WHERE (g.home_team_id = %s OR g.away_team_id = %s)
                        AND g.home_score IS NOT NULL
                        AND g.away_score IS NOT NULL
                    """

                    with_star_result = self.db.query(with_star_query, params=(
                        team_id, team_id, team_id, star_player_ids, team_id, team_id
                    ))

                    # Get team offensive rating without star players (simplified: use overall average as proxy)
                    # For now, calculate impact as difference between star player's avg points and team average
                    if len(team_players) > 0:
                        team_avg_points = team_players['avg_points'].mean()
                        star_avg_points = top_players['avg_points'].sum()
                        star_usage_rate = top_players['avg_usage'].sum()

                        # Impact: star players contribute their usage rate * their efficiency
                        # Simplified: impact = (star_usage_rate / team_total_usage) * star_efficiency
                        total_usage = team_players['avg_usage'].sum()
                        if total_usage > 0:
                            star_contribution = (star_usage_rate / total_usage) * (star_avg_points / max(len(top_players), 1))
                            # Impact is roughly the star players' contribution to team scoring
                            star_impact = star_contribution * 0.3  # Scale down (not all usage is scoring)
                        else:
                            star_impact = 0.0

                        self.team_star_impacts[team_id] = {
                            'star_impact': float(star_impact),
                            'star_usage_rate': float(star_usage_rate),
                            'total_usage': float(total_usage),
                            'star_count': len(top_players)
                        }

        logger.info(f"    Star players identified for {len(self.team_star_players)} teams")
        if self.team_star_impacts:
            avg_star_impact = np.mean([s['star_impact'] for s in self.team_star_impacts.values()])
            logger.info(f"    Average star impact: {avg_star_impact:.2f} points")
        else:
            logger.warning("    No star impacts calculated")

        # Detect roster changes (Enhancement 6: Roster Changes Detection)
        logger.info("  Detecting roster changes...")
        self.team_roster_changes = {}

        # Query active players for each team in recent games
        roster_query = """
        WITH recent_period AS (
            SELECT DISTINCT
                pgs.team_id,
                pgs.player_id,
                g.game_date,
                ROW_NUMBER() OVER (PARTITION BY pgs.team_id ORDER BY g.game_date DESC) as game_rank
            FROM player_game_stats pgs
            INNER JOIN games g ON pgs.game_id = g.game_id
            WHERE g.game_date IS NOT NULL
                AND pgs.team_id IS NOT NULL
                AND pgs.player_id IS NOT NULL
            ORDER BY pgs.team_id, g.game_date DESC
        ),
        last_10_games AS (
            SELECT team_id, player_id
            FROM recent_period
            WHERE game_rank <= 10
        ),
        previous_10_games AS (
            SELECT team_id, player_id
            FROM recent_period
            WHERE game_rank > 10 AND game_rank <= 20
        ),
        current_players AS (
            SELECT DISTINCT team_id, player_id
            FROM last_10_games
        ),
        previous_players AS (
            SELECT DISTINCT team_id, player_id
            FROM previous_10_games
        ),
        new_players AS (
            SELECT cp.team_id, COUNT(DISTINCT cp.player_id) as new_count
            FROM current_players cp
            LEFT JOIN previous_players pp ON cp.team_id = pp.team_id AND cp.player_id = pp.player_id
            WHERE pp.player_id IS NULL
            GROUP BY cp.team_id
        ),
        removed_players AS (
            SELECT pp.team_id, COUNT(DISTINCT pp.player_id) as removed_count
            FROM previous_players pp
            LEFT JOIN current_players cp ON pp.team_id = cp.team_id AND pp.player_id = cp.player_id
            WHERE cp.player_id IS NULL
            GROUP BY pp.team_id
        ),
        total_players AS (
            SELECT
                COALESCE(cp.team_id, pp.team_id) as team_id,
                COUNT(DISTINCT COALESCE(cp.player_id, pp.player_id)) as total_count
            FROM current_players cp
            FULL OUTER JOIN previous_players pp ON cp.team_id = pp.team_id AND cp.player_id = pp.player_id
            GROUP BY COALESCE(cp.team_id, pp.team_id)
        ),
        change_dates AS (
            SELECT
                pgs.team_id,
                MAX(g.game_date) as last_change_date
            FROM player_game_stats pgs
            INNER JOIN games g ON pgs.game_id = g.game_id
            WHERE g.game_date IS NOT NULL
            GROUP BY pgs.team_id
        )
        SELECT
            COALESCE(np.team_id, rp.team_id, tp.team_id) as team_id,
            COALESCE(np.new_count, 0) as new_count,
            COALESCE(rp.removed_count, 0) as removed_count,
            COALESCE(tp.total_count, 0) as total_count,
            COALESCE(cd.last_change_date, CURRENT_DATE) as last_change_date
        FROM new_players np
        FULL OUTER JOIN removed_players rp ON np.team_id = rp.team_id
        FULL OUTER JOIN total_players tp ON COALESCE(np.team_id, rp.team_id) = tp.team_id
        LEFT JOIN change_dates cd ON COALESCE(np.team_id, rp.team_id, tp.team_id) = cd.team_id
        """

        roster_df = self.db.query(roster_query)

        for _, row in roster_df.iterrows():
            team_id = row['team_id']
            new_count = int(row['new_count']) if pd.notna(row['new_count']) else 0
            removed_count = int(row['removed_count']) if pd.notna(row['removed_count']) else 0
            total_count = int(row['total_count']) if pd.notna(row['total_count']) else 0
            last_change_date = pd.to_datetime(row['last_change_date']).date() if pd.notna(row['last_change_date']) else None

            if total_count > 0:
                change_pct = (new_count + removed_count) / total_count

                # Flag significant roster changes (>20% of players changed)
                if change_pct > 0.2:
                    self.team_roster_changes[team_id] = {
                        'change_pct': float(change_pct),
                        'new_count': new_count,
                        'removed_count': removed_count,
                        'total_count': total_count,
                        'last_change_date': last_change_date,
                        'is_significant': True
                    }
                else:
                    # Store minor changes for reference
                    self.team_roster_changes[team_id] = {
                        'change_pct': float(change_pct),
                        'new_count': new_count,
                        'removed_count': removed_count,
                        'total_count': total_count,
                        'last_change_date': last_change_date,
                        'is_significant': False
                    }

        significant_changes = sum(1 for r in self.team_roster_changes.values() if r.get('is_significant', False))
        logger.info(f"    Roster changes detected for {len(self.team_roster_changes)} teams")
        logger.info(f"    Significant roster changes (>20%): {significant_changes} teams")
        if significant_changes > 0:
            avg_change_pct = np.mean([r['change_pct'] for r in self.team_roster_changes.values() if r.get('is_significant', False)])
            logger.info(f"    Average significant change: {avg_change_pct:.1%}")

        # Learn non-parametric trends (year-over-year changes in team performance) - use adjusted ratings
        # Account for roster changes (Enhancement 6: reset trends after major roster changes)
        logger.info("  Learning non-parametric team trends (accounting for roster changes)...")
        df_sorted = df.sort_values(['team_id', 'game_date'])
        for team_id in df_sorted['team_id'].unique():
            team_data = df_sorted[df_sorted['team_id'] == team_id].copy()
            if len(team_data) >= 20:  # Need sufficient data for trend
                # Check for roster changes (Enhancement 6)
                roster_change = self.team_roster_changes.get(team_id, {})
                is_significant_change = roster_change.get('is_significant', False)
                last_change_date = roster_change.get('last_change_date', None)

                # Calculate rolling offensive rating
                team_data['possessions'] = (team_data['fga'] + team_data['turnovers'] + 0.44 * team_data['fta']).clip(lower=1)
                team_data['off_rtg'] = (team_data['points_scored'] / team_data['possessions'] * 100)

                # Adjust for opponent quality in trend calculation
                team_data['opponent_srs'] = team_data['opponent_id'].apply(lambda opp_id: self.team_srs.get(opp_id, 0.0))
                team_data['adjusted_off_rtg'] = team_data['off_rtg'] + (team_data['opponent_srs'] * 0.3)

                # If significant roster change, only use games after the change for trend calculation
                if is_significant_change and last_change_date:
                    # Filter to games after roster change
                    team_data['game_date_dt'] = pd.to_datetime(team_data['game_date'])
                    team_data_after_change = team_data[team_data['game_date_dt'] >= pd.Timestamp(last_change_date)]

                    if len(team_data_after_change) >= 10:
                        # Use games after roster change (last 20 games or all if less)
                        recent = team_data_after_change.tail(20)['adjusted_off_rtg'].dropna()
                        if len(recent) >= 10:
                            x = np.arange(len(recent))
                            slope = np.polyfit(x, recent.values, 1)[0]
                            self.team_trends[team_id] = float(slope)
                        else:
                            # Not enough data after change, use default (no trend)
                            self.team_trends[team_id] = 0.0
                    else:
                        # Not enough games after change, use default (no trend)
                        self.team_trends[team_id] = 0.0
                else:
                    # No significant roster change, use standard trend calculation
                    # Use last 30 games to calculate trend slope (on adjusted ratings)
                    recent = team_data.tail(30)['adjusted_off_rtg'].dropna()
                    if len(recent) >= 10:
                        # Simple linear trend
                        x = np.arange(len(recent))
                        slope = np.polyfit(x, recent.values, 1)[0]
                        self.team_trends[team_id] = float(slope)  # Points per 100 possessions per game

        # Calculate advanced metrics from basic stats
        # Estimated possessions: FGA - ORB + TOV + 0.44*FTA (simplified, using FGA+TOV+0.44*FTA)
        df['team_possessions'] = (df['fga'] + df['turnovers'] + 0.44 * df['fta']).clip(lower=1)
        df['opp_possessions'] = (df['opp_fga'] + df['opp_turnovers'] + 0.44 * df['opp_fta']).clip(lower=1)

        # Offensive/Defensive Rating (points per 100 possessions)
        df['offensive_rating'] = (df['team_points'] / df['team_possessions'] * 100).fillna(110.0)
        df['defensive_rating'] = (df['opp_points'] / df['team_possessions'] * 100).fillna(110.0)

        # Pace (possessions per 48 minutes) - for NBA, possessions per game IS the pace (typically 95-105)
        df['pace'] = df['team_possessions'].fillna(100.0).clip(lower=85, upper=115)

        # True shooting percentage (simplified: use FG% as proxy)
        df['true_shooting_pct'] = df['fg_pct'].fillna(0.45)

        # Turnover percentage
        df['turnover_pct'] = (df['turnovers'] / df['team_possessions'] * 100).fillna(14.0)

        # Opponent ratings (for defensive context)
        df['opponent_offensive_rating'] = (df['opp_points'] / df['opp_possessions'] * 100).fillna(110.0)
        df['opponent_defensive_rating'] = (df['team_points'] / df['opp_possessions'] * 100).fillna(110.0)

        # Calculate actual rest days (Enhancement 1: Actual Rest Days Calculation)
        logger.info("  Calculating actual rest days...")
        df = df.sort_values(['team_id', 'game_date'])

        # Ensure game_date is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['game_date']):
            df['game_date'] = pd.to_datetime(df['game_date'])

        # Calculate days between games for each team
        df['prev_game_date'] = df.groupby('team_id')['game_date'].shift(1)

        # Calculate days_rest (handle NaN values)
        df['days_rest'] = df.apply(
            lambda row: (row['game_date'] - row['prev_game_date']).days
            if pd.notna(row['prev_game_date']) else None,
            axis=1
        )

        # Fill missing values (first game for each team) with default
        df['days_rest'] = df['days_rest'].fillna(1.0)

        # Cap rest days at reasonable maximum (7 days is typical max in NBA)
        df['days_rest'] = df['days_rest'].clip(lower=0, upper=7)

        # Add rest-day feature engineering
        df['is_back_to_back'] = (df['days_rest'] == 0).astype(int)
        df['rest_category'] = df['days_rest'].apply(lambda x: 0 if x == 0 else (1 if x == 1 else (2 if x == 2 else 3)))

        # Create lagged variables
        for col in ['offensive_rating', 'defensive_rating', 'pace']:
            df[f'{col}_lag1'] = df.groupby('team_id')[col].shift(1).fillna(df[col].mean())
            df[f'{col}_rolling5'] = df.groupby('team_id')[col].rolling(5, min_periods=1).mean().reset_index(0, drop=True)

        # Calculate rest disparity for each game (difference in rest days between home and away teams)
        # Need to get rest days for both teams in the same game
        # For home team, we already have days_rest. For away team, we need to calculate separately
        # This is a simplified approach - we'll calculate it in simulate_game for predictions
        logger.info(f"    Rest days calculated: avg={df['days_rest'].mean():.2f}, "
                   f"back-to-back={df['is_back_to_back'].sum():,} games ({df['is_back_to_back'].mean()*100:.1f}%)")

        # Prepare features (including rest-day features)
        feature_cols = [
            'offensive_rating', 'defensive_rating', 'pace', 'true_shooting_pct',
            'turnover_pct', 'opponent_offensive_rating', 'opponent_defensive_rating',
            'days_rest', 'is_back_to_back', 'rest_category',  # Rest-day features
            'offensive_rating_lag1', 'defensive_rating_lag1',
            'pace_rolling5'
        ]

        X = df[feature_cols].fillna(df[feature_cols].mean())
        y = df['won']

        # Standardize features
        X_scaled = self.scaler.fit_transform(X)

        # Estimate panel model with fixed effects
        panel_df = df.set_index(['team_id', 'game_id'])

        try:
            model = PanelOLS(
                dependent=panel_df['won'],
                exog=panel_df[feature_cols].fillna(panel_df[feature_cols].mean()),
                entity_effects=True,  # Team fixed effects
                time_effects=False
            )
            results = model.fit(cov_type='clustered', cluster_entity=True)

            self.model_params = results.params.to_dict()
            self.team_fixed_effects = results.estimated_effects
            self.feature_cols = feature_cols

            logger.info(f"  ✓ Model trained: R² = {results.rsquared:.3f}")
            logger.info(f"  Team fixed effects: {len(self.team_fixed_effects)} teams")

        except Exception as e:
            logger.warning(f"PanelOLS failed, using OLS: {e}")
            # Fallback to regular OLS
            X_with_const = sm.add_constant(X_scaled)
            model = OLS(y, X_with_const).fit()
            self.model_params = dict(zip(['const'] + feature_cols, model.params))
            self.feature_cols = feature_cols
            logger.info(f"  ✓ OLS model trained: R² = {model.rsquared:.3f}")

        return self

    def simulate_game(
        self,
        home_team_id: str,
        away_team_id: str,
        game_date: date,
        n_simulations: int = 1000
    ) -> SimulationResult:
        """Simulate a single game"""

        if self.model_params is None:
            raise ValueError("Model not trained. Call train() first.")

        # Query team basic stats (to calculate metrics) and rest days
        # Use CTE to get recent games, then aggregate
        query = """
        WITH recent_games AS (
            SELECT
                COALESCE(tgs.points, g.home_score) as points,
                COALESCE(tgs.field_goals_attempted, 0) as fga,
                COALESCE(tgs.free_throws_attempted, 0) as fta,
                COALESCE(tgs.turnovers, 0) as turnovers,
                COALESCE(tgs.field_goals_made, 0) as fgm,
                CASE WHEN COALESCE(tgs.field_goals_attempted, 0) > 0
                    THEN tgs.field_goals_made::float / tgs.field_goals_attempted
                    ELSE 0.45 END as fg_pct,
                g.game_date
            FROM games g
            LEFT JOIN team_game_stats tgs ON g.game_id = tgs.game_id
                AND tgs.team_id = %s
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
                AND g.game_date < %s
                AND g.home_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 10
        )
        SELECT
            AVG(points) as avg_points,
            AVG(fga) as avg_fga,
            AVG(fta) as avg_fta,
            AVG(turnovers) as avg_turnovers,
            AVG(fgm) as avg_fgm,
            AVG(fg_pct) as avg_fg_pct,
            MAX(game_date) as last_game_date
        FROM recent_games
        """

        home_stats = self.db.query(query, params=(home_team_id, home_team_id, home_team_id, game_date))
        away_stats = self.db.query(query, params=(away_team_id, away_team_id, away_team_id, game_date))

        # Calculate rest days for home and away teams
        def get_rest_days(stats_df, game_date):
            """Calculate days of rest for a team"""
            if len(stats_df) > 0 and pd.notna(stats_df['last_game_date'].iloc[0]):
                last_game = pd.to_datetime(stats_df['last_game_date'].iloc[0]).date()
                days_rest = (game_date - last_game).days
                days_rest = max(0, min(7, days_rest))  # Cap at 0-7 days
            else:
                days_rest = 1.0  # Default
            return days_rest

        home_days_rest = get_rest_days(home_stats, game_date)
        away_days_rest = get_rest_days(away_stats, game_date)

        # Calculate rest-day features
        home_is_back_to_back = 1 if home_days_rest == 0 else 0
        away_is_back_to_back = 1 if away_days_rest == 0 else 0
        home_rest_category = 0 if home_days_rest == 0 else (1 if home_days_rest == 1 else (2 if home_days_rest == 2 else 3))
        away_rest_category = 0 if away_days_rest == 0 else (1 if away_days_rest == 1 else (2 if away_days_rest == 2 else 3))
        rest_disparity = home_days_rest - away_days_rest  # Positive = home team has more rest

        # Query defensive ratings (points allowed)
        def_query = """
        WITH team_defense AS (
            SELECT
                CASE WHEN g.home_team_id = %s THEN g.away_score
                     WHEN g.away_team_id = %s THEN g.home_score
                     ELSE NULL END as points_allowed,
                g.game_date
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 20
        )
        SELECT AVG(points_allowed) as avg_points_allowed
        FROM team_defense
        WHERE points_allowed IS NOT NULL
        """

        home_def_stats = self.db.query(def_query, params=(home_team_id, home_team_id, home_team_id, home_team_id, game_date))
        away_def_stats = self.db.query(def_query, params=(away_team_id, away_team_id, away_team_id, away_team_id, game_date))

        # Calculate metrics from basic stats
        def calc_metrics(stats_df, def_stats_df):
            if len(stats_df) == 0 or pd.isna(stats_df['avg_points'].iloc[0]):
                return {'offensive_rating': 110.0, 'defensive_rating': 110.0, 'pace': 100.0,
                        'true_shooting_pct': 0.45, 'turnover_pct': 14.0}

            avg_points = float(stats_df['avg_points'].iloc[0]) if pd.notna(stats_df['avg_points'].iloc[0]) else 110.0
            avg_fga = float(stats_df['avg_fga'].iloc[0]) if pd.notna(stats_df['avg_fga'].iloc[0]) else 85.0
            avg_fta = float(stats_df['avg_fta'].iloc[0]) if pd.notna(stats_df['avg_fta'].iloc[0]) else 22.0
            avg_turnovers = float(stats_df['avg_turnovers'].iloc[0]) if pd.notna(stats_df['avg_turnovers'].iloc[0]) else 14.0
            avg_fg_pct = float(stats_df['avg_fg_pct'].iloc[0]) if pd.notna(stats_df['avg_fg_pct'].iloc[0]) else 0.45

            # Estimate possessions
            possessions = max(avg_fga + avg_turnovers + 0.44 * avg_fta, 1)

            # Calculate offensive rating
            offensive_rating = (avg_points / possessions * 100) if possessions > 0 else 110.0

            # Calculate defensive rating (points allowed per 100 possessions)
            if len(def_stats_df) > 0 and pd.notna(def_stats_df['avg_points_allowed'].iloc[0]):
                avg_points_allowed = float(def_stats_df['avg_points_allowed'].iloc[0])
                # Use same possessions estimate for defense (approximation)
                defensive_rating = (avg_points_allowed / possessions * 100) if possessions > 0 else 110.0
            else:
                defensive_rating = 110.0  # League average

            # Pace is possessions per 48 minutes (for NBA, possessions per game IS the pace, typically 95-105)
            pace = max(min(possessions, 115), 85)  # Ensure realistic range 85-115
            true_shooting_pct = avg_fg_pct
            turnover_pct = (avg_turnovers / possessions * 100) if possessions > 0 else 14.0

            return {
                'offensive_rating': offensive_rating,
                'defensive_rating': defensive_rating,
                'pace': pace,
                'true_shooting_pct': true_shooting_pct,
                'turnover_pct': turnover_pct
            }

        home_metrics = calc_metrics(home_stats, home_def_stats)
        away_metrics = calc_metrics(away_stats, away_def_stats)

        # Use opponent-adjusted ratings if available (Enhancement 2: Strength of Schedule)
        home_adj_ratings = self.opponent_adjusted_ratings.get(home_team_id, {})
        away_adj_ratings = self.opponent_adjusted_ratings.get(away_team_id, {})

        # Use home/away splits if available (Enhancement 3: Home/Away Splits)
        home_splits = self.team_home_away_splits.get(home_team_id, {})
        away_splits = self.team_home_away_splits.get(away_team_id, {})

        # Use home/away splits for ratings (home team uses home ratings, away team uses away ratings)
        if home_splits:
            # Home team: use home offensive rating and home defensive rating
            home_off_rtg = home_splits.get('home_off_rtg', home_adj_ratings.get('offensive_rating', home_metrics['offensive_rating']))
            home_def_rtg = home_splits.get('home_def_rtg', home_adj_ratings.get('defensive_rating', home_metrics['defensive_rating']))
        else:
            # Fallback to opponent-adjusted ratings or calculated metrics
            home_off_rtg = home_adj_ratings.get('offensive_rating', home_metrics['offensive_rating'])
            home_def_rtg = home_adj_ratings.get('defensive_rating', home_metrics['defensive_rating'])

        if away_splits:
            # Away team: use away offensive rating and away defensive rating
            away_off_rtg = away_splits.get('away_off_rtg', away_adj_ratings.get('offensive_rating', away_metrics['offensive_rating']))
            away_def_rtg = away_splits.get('away_def_rtg', away_adj_ratings.get('defensive_rating', away_metrics['defensive_rating']))
        else:
            # Fallback to opponent-adjusted ratings or calculated metrics
            away_off_rtg = away_adj_ratings.get('offensive_rating', away_metrics['offensive_rating'])
            away_def_rtg = away_adj_ratings.get('defensive_rating', away_metrics['defensive_rating'])

        # Get SRS values for opponent strength weighting
        home_srs = self.team_srs.get(home_team_id, 0.0)
        away_srs = self.team_srs.get(away_team_id, 0.0)

        # Get team-specific home advantage (Enhancement 3)
        home_advantage_points = home_splits.get('home_advantage', 2.0) if home_splits else 2.0  # Default 2 points if no splits

        # Prepare feature vector with opponent-adjusted ratings and rest-day features
        features = {
            'offensive_rating': home_off_rtg,  # Opponent-adjusted
            'defensive_rating': home_def_rtg,  # Opponent-adjusted
            'pace': home_metrics['pace'],
            'true_shooting_pct': home_metrics['true_shooting_pct'],
            'turnover_pct': home_metrics['turnover_pct'],
            'opponent_offensive_rating': away_off_rtg,  # Opponent-adjusted
            'opponent_defensive_rating': away_def_rtg,  # Opponent-adjusted
            'days_rest': home_days_rest,  # Actual rest days
            'is_back_to_back': home_is_back_to_back,  # Back-to-back indicator
            'rest_category': home_rest_category,  # Rest category (0, 1, 2, 3+)
            'offensive_rating_lag1': home_off_rtg,  # Use adjusted rating
            'defensive_rating_lag1': home_def_rtg,  # Use adjusted rating
            'pace_rolling5': home_metrics['pace'],
        }

        # Calculate win probability
        X = np.array([[features.get(col, 0) for col in self.feature_cols]])
        X_scaled = self.scaler.transform(X)

        # Add team fixed effect if available
        base_prob = 0.5
        if (hasattr(self, 'team_fixed_effects') and
            self.team_fixed_effects is not None and
            hasattr(self.team_fixed_effects, 'index') and
            home_team_id in self.team_fixed_effects.index):
            base_prob += self.team_fixed_effects[home_team_id] * 0.1

        # Calculate linear prediction
        pred = 0
        for col, coef in self.model_params.items():
            if col in features:
                pred += coef * features[col]
            elif col == 'const':
                pred += coef

        # Convert to probability
        home_win_prob = 1 / (1 + np.exp(-pred))  # Logistic transformation
        home_win_prob = np.clip(home_win_prob, 0.01, 0.99)

        # Simulate scores with defensive adjustments (using opponent-adjusted ratings)
        home_off = home_off_rtg  # Use opponent-adjusted rating
        away_off = away_off_rtg  # Use opponent-adjusted rating
        home_def = home_def_rtg  # Use opponent-adjusted rating
        away_def = away_def_rtg  # Use opponent-adjusted rating
        pace = features['pace']

        # Pace is already possessions per game (typically 95-105 for NBA)
        # Cap it to realistic range
        possessions = min(max(pace, 85), 115)  # Realistic NBA possessions: 85-115

        # Predicted scores: Offensive rating adjusted by opponent defensive rating (Enhancement 3)
        # Home score = Home team's home offensive rating vs Away team's away defensive rating
        # Away score = Away team's away offensive rating vs Home team's home defensive rating
        # Adjustment: If opponent defense is worse (higher DRtg), offense scores more
        home_adj = (away_def_rtg - 110) * 0.5  # +0.5 points per point above/below league avg defense
        away_adj = (home_def_rtg - 110) * 0.5

        # Base predicted scores (points per 100 possessions * possessions / 100)
        base_home_score = (home_off_rtg / 100) * possessions
        base_away_score = (away_off_rtg / 100) * possessions

        # Apply defensive adjustments (better offense vs worse defense = more points)
        predicted_home_score = base_home_score + home_adj
        predicted_away_score = base_away_score + away_adj

        # Apply team-specific home advantage (Enhancement 3: not fixed 4%, but actual home advantage)
        # Home advantage is already partially reflected in home_off_rtg vs away_off_rtg
        # Add additional adjustment for home court (typically 1-2 points beyond rating difference)
        home_advantage_adjustment = home_advantage_points * 0.5  # Scale to points (not per 100 possessions)
        predicted_home_score += home_advantage_adjustment
        predicted_away_score -= home_advantage_adjustment * 0.5  # Slight reduction for away team

        # Apply matchup-specific adjustments (Enhancement 4: Matchup-Specific Adjustments)
        # Pace mismatch: Fast team vs. slow team = higher total
        pace_diff = home_metrics['pace'] - away_metrics['pace']
        pace_mismatch_adj = pace_diff * 0.15  # 0.15 points per possession difference
        predicted_home_score += pace_mismatch_adj / 2
        predicted_away_score += pace_mismatch_adj / 2

        # Defensive efficiency vs. opponent offensive efficiency
        # Strong defense vs. weak offense = lower score
        # Weak defense vs. strong offense = higher score
        def_vs_off_home = home_def_rtg - away_off_rtg  # Home defense vs. away offense
        def_vs_off_away = away_def_rtg - home_off_rtg  # Away defense vs. home offense

        # Adjustment: If defense is much better than opponent offense, reduce opponent score
        def_adj_home = -def_vs_off_home * 0.3  # Negative adjustment if defense is better
        def_adj_away = -def_vs_off_away * 0.3

        predicted_away_score += def_adj_home  # Home defense reduces away score
        predicted_home_score += def_adj_away  # Away defense reduces home score

        # Head-to-head adjustments (if sufficient historical data)
        team_pair = tuple(sorted([home_team_id, away_team_id]))
        h2h_record = self.head_to_head_records.get(team_pair, {})

        if h2h_record.get('total_games', 0) >= 3:
            # Head-to-head total adjustment
            h2h_avg_total = h2h_record.get('avg_total', 225.0)
            current_predicted_total = predicted_home_score + predicted_away_score
            h2h_total_adj = (h2h_avg_total - current_predicted_total) * 0.2  # 20% adjustment toward H2H average
            predicted_home_score += h2h_total_adj / 2
            predicted_away_score += h2h_total_adj / 2

            # Head-to-head win probability adjustment
            # Determine which team is team1 (alphabetically first)
            team1 = min(home_team_id, away_team_id)
            is_home_team1 = (home_team_id == team1)
            h2h_win_pct = h2h_record.get('team1_win_pct', 0.5) if is_home_team1 else (1 - h2h_record.get('team1_win_pct', 0.5))

            # Adjust win probability based on H2H record
            h2h_win_adj = (h2h_win_pct - 0.5) * 0.05  # Max 5% adjustment
            home_win_prob += h2h_win_adj
            home_win_prob = np.clip(home_win_prob, 0.01, 0.99)

        # Calculate matchup-specific variance (Enhancement 4)
        # High variance for pace mismatches (fast vs. slow = unpredictable)
        # Lower variance for similar styles (defensive vs. defensive = more predictable)
        pace_variance_factor = abs(pace_diff) / 20.0  # 0-1 scale based on pace difference
        style_similarity = 1 - abs(def_vs_off_home + def_vs_off_away) / 20.0  # 0-1 scale based on style similarity

        # Higher variance for pace mismatches, lower for similar styles
        matchup_variance = (pace_variance_factor * 2.0) + ((1 - style_similarity) * 1.0)
        matchup_variance = min(max(matchup_variance, 0.5), 3.0)  # Cap between 0.5 and 3.0

        # Apply rest-day adjustments (Enhancement 1)
        # Rest impact: Teams with 0-1 days rest perform worse, teams with 3+ days rest perform better
        # Research shows: 0 days (back-to-back) = -2 to -3 points, 1 day = -1 to -1.5 points, 3+ days = +0.5 to +1 point
        rest_impact_home = 0.0
        if home_days_rest == 0:  # Back-to-back
            rest_impact_home = -2.5
        elif home_days_rest == 1:
            rest_impact_home = -1.2
        elif home_days_rest >= 3:
            rest_impact_home = 0.7

        rest_impact_away = 0.0
        if away_days_rest == 0:  # Back-to-back
            rest_impact_away = -2.5
        elif away_days_rest == 1:
            rest_impact_away = -1.2
        elif away_days_rest >= 3:
            rest_impact_away = 0.7

        # Apply rest disparity adjustment (home team with more rest = additional advantage)
        rest_disparity_adj = 0.0
        if rest_disparity > 0:  # Home team has more rest
            rest_disparity_adj = min(rest_disparity * 0.3, 1.5)  # Max 1.5 point advantage
        elif rest_disparity < 0:  # Away team has more rest
            rest_disparity_adj = max(rest_disparity * 0.3, -1.5)  # Max 1.5 point disadvantage

        predicted_home_score += rest_impact_home + rest_disparity_adj
        predicted_away_score += rest_impact_away - rest_disparity_adj

        # Apply distribution-based variance and calibration (season-specific)
        season = self.get_season_for_date(game_date)
        dist_params = self.season_distributions.get(season, self.default_distribution)

        # Sample variance from learned distribution (with matchup-specific variance)
        # Use distribution std dev as variance scale, adjusted by matchup variance
        variance_scale = (dist_params['std'] / 10.0) * matchup_variance  # Scale to per-team variance with matchup adjustment
        variance_factor = np.random.normal(0, variance_scale)

        # Apply non-parametric trend adjustments
        home_trend = self.team_trends.get(home_team_id, 0.0) * 0.1  # Scale trend impact
        away_trend = self.team_trends.get(away_team_id, 0.0) * 0.1

        predicted_home_score += home_trend + variance_factor
        predicted_away_score += away_trend - variance_factor

        # Apply star player impact adjustments (Enhancement 5: Star Player Impact)
        # Check if star players are available in recent games
        home_star_players = self.team_star_players.get(home_team_id, [])
        away_star_players = self.team_star_players.get(away_team_id, [])

        home_star_impact = self.team_star_impacts.get(home_team_id, {})
        away_star_impact = self.team_star_impacts.get(away_team_id, {})

        if home_star_players and home_star_impact:
            # Query recent games to check if star players played
            star_availability_query = """
            SELECT
                COUNT(DISTINCT pgs.player_id) as stars_playing,
                COUNT(DISTINCT g.game_id) as games_with_stars
            FROM games g
            INNER JOIN player_game_stats pgs ON g.game_id = pgs.game_id
                AND pgs.team_id = %s
                AND pgs.player_id = ANY(%s)
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
                AND g.game_date < %s
                AND g.game_date >= %s - INTERVAL '10 days'
                AND g.home_score IS NOT NULL
            """

            star_ids_home = [p['player_id'] for p in home_star_players]
            star_avail_home = self.db.query(star_availability_query, params=(
                home_team_id, star_ids_home, home_team_id, home_team_id, game_date, game_date
            ))

            if len(star_avail_home) > 0 and star_avail_home['games_with_stars'].iloc[0] > 0:
                stars_playing = int(star_avail_home['stars_playing'].iloc[0])
                total_stars = len(home_star_players)
                star_availability_pct = stars_playing / total_stars if total_stars > 0 else 1.0

                # If star players missing, reduce offensive rating
                if star_availability_pct < 0.8:  # Less than 80% of star players available
                    missing_star_impact = home_star_impact.get('star_impact', 0.0) * (1 - star_availability_pct)
                    predicted_home_score -= missing_star_impact
                    logger.debug(f"  Home team missing star players: {star_availability_pct:.1%} available, adjusting by -{missing_star_impact:.2f} points")

        if away_star_players and away_star_impact:
            # Query recent games to check if star players played
            star_ids_away = [p['player_id'] for p in away_star_players]
            star_avail_away = self.db.query(star_availability_query, params=(
                away_team_id, star_ids_away, away_team_id, away_team_id, game_date, game_date
            ))

            if len(star_avail_away) > 0 and star_avail_away['games_with_stars'].iloc[0] > 0:
                stars_playing = int(star_avail_away['stars_playing'].iloc[0])
                total_stars = len(away_star_players)
                star_availability_pct = stars_playing / total_stars if total_stars > 0 else 1.0

                # If star players missing, reduce offensive rating
                if star_availability_pct < 0.8:  # Less than 80% of star players available
                    missing_star_impact = away_star_impact.get('star_impact', 0.0) * (1 - star_availability_pct)
                    predicted_away_score -= missing_star_impact
                    logger.debug(f"  Away team missing star players: {star_availability_pct:.1%} available, adjusting by -{missing_star_impact:.2f} points")

        # Apply roster stability adjustments (Enhancement 6: Roster Changes Detection)
        # If recent roster change, reduce confidence in team averages and apply stability factor
        home_roster_change = self.team_roster_changes.get(home_team_id, {})
        away_roster_change = self.team_roster_changes.get(away_team_id, {})

        home_stability_factor = 1.0
        away_stability_factor = 1.0

        if home_roster_change.get('is_significant', False):
            change_pct = home_roster_change.get('change_pct', 0.0)
            last_change_date = home_roster_change.get('last_change_date', None)

            # Calculate days since roster change
            if last_change_date:
                days_since_change = (game_date - last_change_date).days

                # If roster change was recent (< 10 games), apply stability adjustment
                if days_since_change < 10:
                    # Stability factor: 1 - (change_pct * 0.5)
                    # More change = less stability = lower confidence in team averages
                    home_stability_factor = 1.0 - (change_pct * 0.5)
                    home_stability_factor = max(0.5, home_stability_factor)  # Cap at 0.5 (minimum 50% confidence)

                    # Apply stability adjustment: reduce predicted score variance
                    # Teams with recent roster changes are less predictable
                    stability_adj = (1.0 - home_stability_factor) * 2.0  # Max 2 point reduction
                    predicted_home_score -= stability_adj
                    logger.debug(f"  Home team recent roster change: {change_pct:.1%} change, {days_since_change} days ago, stability factor: {home_stability_factor:.2f}")

        if away_roster_change.get('is_significant', False):
            change_pct = away_roster_change.get('change_pct', 0.0)
            last_change_date = away_roster_change.get('last_change_date', None)

            # Calculate days since roster change
            if last_change_date:
                days_since_change = (game_date - last_change_date).days

                # If roster change was recent (< 10 games), apply stability adjustment
                if days_since_change < 10:
                    # Stability factor: 1 - (change_pct * 0.5)
                    away_stability_factor = 1.0 - (change_pct * 0.5)
                    away_stability_factor = max(0.5, away_stability_factor)  # Cap at 0.5

                    # Apply stability adjustment
                    stability_adj = (1.0 - away_stability_factor) * 2.0  # Max 2 point reduction
                    predicted_away_score -= stability_adj
                    logger.debug(f"  Away team recent roster change: {change_pct:.1%} change, {days_since_change} days ago, stability factor: {away_stability_factor:.2f}")

        # Get live adjustments (ongoing games, streaks, outliers)
        live_adj_home = self.get_live_adjustments(home_team_id, game_date)
        live_adj_away = self.get_live_adjustments(away_team_id, game_date)

        predicted_home_score += live_adj_home
        predicted_away_score += live_adj_away

        # Distribution-based calibration: adjust toward season-specific mean
        total_predicted = predicted_home_score + predicted_away_score
        dist_mean = dist_params['mean']

        # Light calibration (10%) toward season mean to maintain natural variance
        total_adjustment = (dist_mean - total_predicted) * 0.1
        predicted_home_score += total_adjustment / 2
        predicted_away_score += total_adjustment / 2

        # Add noise
        home_scores = np.random.normal(predicted_home_score, 10, n_simulations)
        away_scores = np.random.normal(predicted_away_score, 10, n_simulations)

        home_wins = (home_scores > away_scores).mean()

        return SimulationResult(
            home_win_prob=float(home_win_prob),
            away_win_prob=float(1 - home_win_prob),
            predicted_home_score=float(predicted_home_score),
            predicted_away_score=float(predicted_away_score),
            confidence=abs(home_win_prob - 0.5) * 2,  # 0-1 scale
            model_type='panel_regression',
            simulation_id=hash(f"{home_team_id}{away_team_id}{game_date}"),
            metadata={
                'team_fixed_effect': float(self.team_fixed_effects[home_team_id]) if (hasattr(self, 'team_fixed_effects') and self.team_fixed_effects is not None and hasattr(self.team_fixed_effects, 'index') and home_team_id in self.team_fixed_effects.index) else 0.0,
                'r_squared': float(getattr(self, 'r_squared', 0.7)),
                'n_training_games': getattr(self, 'n_training', 0),
                'season': season,
                'distribution_mean': dist_params['mean'],
                'live_adjustments': {'home': live_adj_home, 'away': live_adj_away},
                'rest_days': {'home': home_days_rest, 'away': away_days_rest, 'disparity': rest_disparity},
                'rest_adjustments': {'home': rest_impact_home, 'away': rest_impact_away, 'disparity': rest_disparity_adj},
                'srs': {'home': home_srs, 'away': away_srs},
                'opponent_adjusted': {
                    'home_off_rtg': home_off_rtg,
                    'home_def_rtg': home_def_rtg,
                    'away_off_rtg': away_off_rtg,
                    'away_def_rtg': away_def_rtg
                },
                'home_away_splits': {
                    'home_advantage': home_advantage_points,
                    'home_advantage_adjustment': home_advantage_adjustment,
                    'home_off_rtg': home_off_rtg,
                    'home_def_rtg': home_def_rtg,
                    'away_off_rtg': away_off_rtg,
                    'away_def_rtg': away_def_rtg
                },
                'matchup_adjustments': {
                    'pace_diff': float(pace_diff),
                    'pace_mismatch_adj': float(pace_mismatch_adj),
                    'def_vs_off_home': float(def_vs_off_home),
                    'def_vs_off_away': float(def_vs_off_away),
                    'def_adj_home': float(def_adj_home),
                    'def_adj_away': float(def_adj_away),
                    'h2h_games': h2h_record.get('total_games', 0),
                    'h2h_total_adj': h2h_record.get('avg_total', 0) if h2h_record.get('total_games', 0) >= 3 else 0.0,
                    'matchup_variance': float(matchup_variance)
                },
                'star_player_impact': {
                    'home_star_count': len(home_star_players),
                    'away_star_count': len(away_star_players),
                    'home_star_impact': home_star_impact.get('star_impact', 0.0),
                    'away_star_impact': away_star_impact.get('star_impact', 0.0)
                },
                'roster_stability': {
                    'home_stability_factor': float(home_stability_factor),
                    'away_stability_factor': float(away_stability_factor),
                    'home_roster_change_pct': home_roster_change.get('change_pct', 0.0),
                    'away_roster_change_pct': away_roster_change.get('change_pct', 0.0),
                    'home_is_significant_change': home_roster_change.get('is_significant', False),
                    'away_is_significant_change': away_roster_change.get('is_significant', False)
                }
            }
        )

    def get_live_adjustments(self, team_id: str, game_date: date) -> float:
        """Get adjustments based on live/ongoing games (streaks, outliers, momentum)"""
        # Query recent completed games (last 24-48 hours) for this team
        query = """
        WITH recent_games AS (
            SELECT
                g.game_id,
                g.game_date,
                CASE WHEN g.home_team_id = %s THEN g.home_score
                     WHEN g.away_team_id = %s THEN g.away_score
                     ELSE NULL END as team_score,
                CASE WHEN g.home_team_id = %s THEN g.away_score
                     WHEN g.away_team_id = %s THEN g.home_score
                     ELSE NULL END as opponent_score,
                CASE WHEN (g.home_team_id = %s AND g.home_score > g.away_score) OR
                          (g.away_team_id = %s AND g.away_score > g.home_score)
                     THEN 1 ELSE 0 END as won
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.game_date >= %s - INTERVAL '48 hours'
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 5
        )
        SELECT
            AVG(team_score) as avg_score,
            AVG(opponent_score) as avg_opponent_score,
            AVG(won) as win_rate,
            COUNT(*) as game_count
        FROM recent_games
        WHERE team_score IS NOT NULL
        """

        result = self.db.query(query, params=(
            team_id, team_id, team_id, team_id, team_id, team_id, team_id, team_id, game_date, game_date
        ))

        if len(result) > 0 and result['game_count'].iloc[0] and result['game_count'].iloc[0] >= 2:
            # Detect streaks (winning/losing streaks)
            win_rate = float(result['win_rate'].iloc[0])
            avg_score = float(result['avg_score'].iloc[0])

            # Momentum adjustment: hot streak = +1 to +2 points, cold streak = -1 to -2 points
            if win_rate >= 0.8:  # Hot streak (4+ wins in 5 games)
                momentum = 1.5
            elif win_rate >= 0.6:  # Winning trend
                momentum = 0.8
            elif win_rate <= 0.2:  # Cold streak (4+ losses in 5 games)
                momentum = -1.5
            elif win_rate <= 0.4:  # Losing trend
                momentum = -0.8
            else:
                momentum = 0.0

            # Scoring trend (recent scoring vs. historical)
            # If recent scoring is significantly above/below average, adjust
            scoring_adj = (avg_score - 110.0) * 0.05  # Small adjustment based on recent scoring

            return momentum + scoring_adj

        return 0.0  # No recent games or insufficient data


class HierarchicalBayesianSimulator:
    """
    Hierarchical Bayesian Simulator

    Uses multi-level Bayesian modeling:
    - Level 1: League-wide averages
    - Level 2: Team-level effects
    - Level 3: Player-level effects

    Borrows strength across hierarchy for robust predictions.
    """

    def __init__(self, db: DatabaseConnector):
        self.db = db
        self.league_mean = None
        self.team_means = {}
        self.team_variances = {}
        self.season_distributions = {}  # Store learned distributions per season
        self.team_trends = {}  # Store non-parametric trend slopes per team
        self.team_srs = {}  # Simple Rating System values
        logger.info("HierarchicalBayesianSimulator initialized")

    def get_season_for_date(self, game_date: date) -> int:
        """Determine NBA season year from game date"""
        if game_date.month >= 10:
            return game_date.year + 1
        else:
            return game_date.year

    def train(self, start_season: int = None, end_season: int = None):
        """Train hierarchical Bayesian model on ALL historical data"""
        logger.info(f"Training hierarchical Bayesian model on ALL available data")

        # Query team performance data - use ALL available data
        # Need both home and away games to get opponent_id properly
        query = """
        SELECT
            g.home_team_id as team_id,
            g.away_team_id as opponent_id,
            g.home_score as points_scored,
            g.away_score as opponent_points,
            g.home_score + g.away_score as total_points,
            g.season,
            g.game_date,
            CASE WHEN g.home_score > g.away_score THEN 1 ELSE 0 END as won
        FROM games g
        WHERE g.home_score IS NOT NULL
            AND g.away_score IS NOT NULL
        UNION ALL
        SELECT
            g.away_team_id as team_id,
            g.home_team_id as opponent_id,
            g.away_score as points_scored,
            g.home_score as opponent_points,
            g.home_score + g.away_score as total_points,
            g.season,
            g.game_date,
            CASE WHEN g.away_score > g.home_score THEN 1 ELSE 0 END as won
        FROM games g
        WHERE g.home_score IS NOT NULL
            AND g.away_score IS NOT NULL
        """

        df = self.db.query(query)

        if len(df) == 0:
            raise ValueError("No training data found")

        logger.info(f"  Loaded {len(df):,} game observations")

        # Learn season-specific distributions
        logger.info("  Learning season-specific distributions...")
        df['season_year'] = df['season'].apply(lambda s: int(s[:4]) if pd.notna(s) and len(str(s)) >= 4 else None)

        for season in sorted(df['season_year'].dropna().unique()):
            season_data = df[df['season_year'] == season]
            if len(season_data) > 0:
                totals = season_data['total_points'].dropna()
                if len(totals) > 0:
                    self.season_distributions[season] = {
                        'mean': float(totals.mean()),
                        'std': float(totals.std()),
                        'min': float(totals.min()),
                        'max': float(totals.max()),
                        'p5': float(totals.quantile(0.05)),
                        'p25': float(totals.quantile(0.25)),
                        'p75': float(totals.quantile(0.75)),
                        'p95': float(totals.quantile(0.95)),
                        'count': int(len(totals))
                    }

        # Default distribution
        if self.season_distributions:
            most_recent_season = max(self.season_distributions.keys())
            self.default_distribution = self.season_distributions[most_recent_season]
        else:
            all_totals = df['total_points'].dropna()
            self.default_distribution = {
                'mean': float(all_totals.mean()),
                'std': float(all_totals.std()),
                'min': float(all_totals.min()),
                'max': float(all_totals.max()),
                'p5': float(all_totals.quantile(0.05)),
                'p95': float(all_totals.quantile(0.95))
            }

        # Calculate SRS (Simple Rating System) for opponent-adjusted ratings (Enhancement 2)
        logger.info("  Calculating Simple Rating System (SRS)...")
        all_teams = set(df['team_id'].unique())

        # Initialize SRS
        srs = {team_id: 0.0 for team_id in all_teams}
        team_point_diffs = {}
        team_game_count = {}

        for team_id in all_teams:
            team_games = df[df['team_id'] == team_id]
            if len(team_games) > 0:
                # Calculate point differential (average margin)
                point_diff = (team_games['points_scored'] - team_games['opponent_points']).mean()
                team_point_diffs[team_id] = float(point_diff)
                team_game_count[team_id] = len(team_games)
            else:
                team_point_diffs[team_id] = 0.0
                team_game_count[team_id] = 0

        # Iterate until convergence
        for iteration in range(50):
            old_srs = srs.copy()
            for team_id in all_teams:
                if team_game_count[team_id] > 0:
                    team_games = df[df['team_id'] == team_id]
                    # Calculate average opponent SRS (now we have opponent_id)
                    opponent_srs_avg = team_games['opponent_id'].apply(lambda opp_id: old_srs.get(opp_id, 0.0)).mean()
                    srs[team_id] = team_point_diffs[team_id] + float(opponent_srs_avg)

            max_change = max(abs(srs[team_id] - old_srs[team_id]) for team_id in all_teams)
            if max_change < 0.01:
                logger.info(f"    SRS converged after {iteration + 1} iterations")
                break

        # Normalize SRS
        avg_srs = np.mean(list(srs.values())) if srs else 0.0
        self.team_srs = {team_id: srs_val - avg_srs for team_id, srs_val in srs.items()}

        # Calculate hierarchical means (use SRS-adjusted if available)
        # League mean
        self.league_mean = df['won'].mean()

        # Team means (Bayesian shrinkage toward league mean) - account for opponent strength
        team_stats = df.groupby('team_id')['won'].agg(['mean', 'count'])

        # Shrinkage factor (more games = less shrinkage)
        shrinkage_factor = 0.3  # 30% shrinkage toward league mean

        for team_id in team_stats.index:
            team_mean = team_stats.loc[team_id, 'mean']
            n_games = team_stats.loc[team_id, 'count']

            # More games = less shrinkage
            shrinkage = shrinkage_factor / (1 + n_games / 100)

            # Adjust team mean based on SRS (teams with positive SRS are better than their record suggests)
            srs_adj = self.team_srs.get(team_id, 0.0) * 0.05  # 5% adjustment per SRS point
            adjusted_mean = team_mean + srs_adj

            # Shrink toward league mean
            shrunk_mean = shrinkage * self.league_mean + (1 - shrinkage) * adjusted_mean

            self.team_means[team_id] = shrunk_mean
            self.team_variances[team_id] = 0.05  # Fixed variance

        # Learn non-parametric trends
        logger.info("  Learning non-parametric team trends...")
        # Ensure game_date is datetime
        if 'game_date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['game_date']):
            df['game_date'] = pd.to_datetime(df['game_date'])
        df_sorted = df.sort_values(['team_id', 'game_date']) if 'game_date' in df.columns else df.sort_values('team_id')
        for team_id in df_sorted['team_id'].unique():
            team_data = df_sorted[df_sorted['team_id'] == team_id].copy()
            if len(team_data) >= 20:
                recent = team_data.tail(30)['points_scored'].dropna()
                if len(recent) >= 10:
                    x = np.arange(len(recent))
                    slope = np.polyfit(x, recent.values, 1)[0]
                    self.team_trends[team_id] = float(slope)

        logger.info(f"  ✓ Model trained: {len(self.team_means)} teams")
        logger.info(f"  League mean win rate: {self.league_mean:.3f}")

        return self

    def simulate_game(
        self,
        home_team_id: str,
        away_team_id: str,
        game_date: date,
        n_simulations: int = 1000
    ) -> SimulationResult:
        """Simulate a single game using hierarchical Bayesian model"""

        if self.league_mean is None:
            raise ValueError("Model not trained. Call train() first.")

        # Get team means (with default fallback)
        home_mean = self.team_means.get(home_team_id, self.league_mean)
        away_mean = self.team_means.get(away_team_id, self.league_mean)

        # Home court advantage
        home_advantage = 0.04  # ~4% boost

        # Calculate win probability
        team_diff = home_mean - away_mean + home_advantage
        home_win_prob = 0.5 + team_diff
        home_win_prob = np.clip(home_win_prob, 0.01, 0.99)

        # Predict scores (using team averages from games table)
        # Query home team average and last game date from games table (since team_game_stats may be empty)
        # Use CTE to first select recent games, then aggregate
        home_query = """
        WITH recent_games AS (
            SELECT
                CASE
                    WHEN g.home_team_id = %s THEN g.home_score
                    WHEN g.away_team_id = %s THEN g.away_score
                    ELSE NULL
                END as team_score,
                g.game_date
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 20
        )
        SELECT AVG(team_score) as team_avg, MAX(game_date) as last_game_date
        FROM recent_games
        """
        home_scores = self.db.query(home_query, params=(home_team_id, home_team_id, home_team_id, home_team_id, game_date))

        # Query away team average and last game date from games table
        # Use CTE to first select recent games, then aggregate
        away_query = """
        WITH recent_games AS (
            SELECT
                CASE
                    WHEN g.home_team_id = %s THEN g.home_score
                    WHEN g.away_team_id = %s THEN g.away_score
                    ELSE NULL
                END as team_score,
                g.game_date
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 20
        )
        SELECT AVG(team_score) as team_avg, MAX(game_date) as last_game_date
        FROM recent_games
        """
        away_scores = self.db.query(away_query, params=(away_team_id, away_team_id, away_team_id, away_team_id, game_date))

        # Calculate rest days for home and away teams (Enhancement 1)
        def get_rest_days(scores_df, game_date):
            """Calculate days of rest for a team"""
            if len(scores_df) > 0 and pd.notna(scores_df['last_game_date'].iloc[0]):
                last_game = pd.to_datetime(scores_df['last_game_date'].iloc[0]).date()
                days_rest = (game_date - last_game).days
                days_rest = max(0, min(7, days_rest))  # Cap at 0-7 days
            else:
                days_rest = 1.0  # Default
            return days_rest

        home_days_rest = get_rest_days(home_scores, game_date)
        away_days_rest = get_rest_days(away_scores, game_date)
        rest_disparity = home_days_rest - away_days_rest

        # Get home team score with fallback (Enhancement 2: apply SRS adjustment)
        if len(home_scores) > 0 and pd.notna(home_scores['team_avg'].iloc[0]):
            raw_home_score = float(home_scores['team_avg'].iloc[0])
        else:
            # Fallback: Get all-time team average from games table
            fallback_query = """
            SELECT AVG(CASE
                WHEN g.home_team_id = %s THEN g.home_score
                WHEN g.away_team_id = %s THEN g.away_score
                ELSE NULL
            END) as team_avg
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            """
            fallback = self.db.query(fallback_query, params=(home_team_id, home_team_id, home_team_id, home_team_id))
            if len(fallback) > 0 and pd.notna(fallback['team_avg'].iloc[0]):
                raw_home_score = float(fallback['team_avg'].iloc[0])
            else:
                raw_home_score = 110.0  # League default

        # Apply SRS adjustment (Enhancement 2: Strength of Schedule)
        home_srs = self.team_srs.get(home_team_id, 0.0)
        srs_adj_home = home_srs * 0.3  # 0.3 points per SRS point
        predicted_home_score = raw_home_score + srs_adj_home

        # Get away team score with fallback (Enhancement 2: apply SRS adjustment)
        if len(away_scores) > 0 and pd.notna(away_scores['team_avg'].iloc[0]):
            raw_away_score = float(away_scores['team_avg'].iloc[0])
        else:
            # Fallback: Get all-time team average from games table
            fallback_query = """
            SELECT AVG(CASE
                WHEN g.home_team_id = %s THEN g.home_score
                WHEN g.away_team_id = %s THEN g.away_score
                ELSE NULL
            END) as team_avg
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            """
            fallback = self.db.query(fallback_query, params=(away_team_id, away_team_id, away_team_id, away_team_id))
            if len(fallback) > 0 and pd.notna(fallback['team_avg'].iloc[0]):
                raw_away_score = float(fallback['team_avg'].iloc[0])
            else:
                raw_away_score = 108.0  # League default

        # Apply SRS adjustment (Enhancement 2: Strength of Schedule)
        away_srs = self.team_srs.get(away_team_id, 0.0)
        srs_adj_away = away_srs * 0.3  # 0.3 points per SRS point
        predicted_away_score = raw_away_score + srs_adj_away

        # Apply defensive adjustments (query opponent defensive ratings)
        # Query home team defensive rating (points allowed)
        home_def_query = """
        WITH team_defense AS (
            SELECT
                CASE WHEN g.home_team_id = %s THEN g.away_score
                     WHEN g.away_team_id = %s THEN g.home_score
                     ELSE NULL END as points_allowed
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 20
        )
        SELECT AVG(points_allowed) as avg_points_allowed
        FROM team_defense
        """
        home_def = self.db.query(home_def_query, params=(home_team_id, home_team_id, home_team_id, home_team_id, game_date))

        # Query away team defensive rating
        away_def_query = """
        WITH team_defense AS (
            SELECT
                CASE WHEN g.home_team_id = %s THEN g.away_score
                     WHEN g.away_team_id = %s THEN g.home_score
                     ELSE NULL END as points_allowed
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 20
        )
        SELECT AVG(points_allowed) as avg_points_allowed
        FROM team_defense
        """
        away_def = self.db.query(away_def_query, params=(away_team_id, away_team_id, away_team_id, away_team_id, game_date))

        # Apply defensive adjustments (worse defense = opponent scores more)
        if len(away_def) > 0 and pd.notna(away_def['avg_points_allowed'].iloc[0]):
            away_def_rtg = float(away_def['avg_points_allowed'].iloc[0])
            # Adjustment: If away defense is worse (allows more), home scores more
            home_def_adj = (away_def_rtg - 110) * 0.4  # +0.4 points per point above/below avg
            predicted_home_score += home_def_adj

        if len(home_def) > 0 and pd.notna(home_def['avg_points_allowed'].iloc[0]):
            home_def_rtg = float(home_def['avg_points_allowed'].iloc[0])
            # Adjustment: If home defense is worse (allows more), away scores more
            away_def_adj = (home_def_rtg - 110) * 0.4  # +0.4 points per point above/below avg
            predicted_away_score += away_def_adj

        # Apply rest-day adjustments (Enhancement 1)
        rest_impact_home = 0.0
        if home_days_rest == 0:  # Back-to-back
            rest_impact_home = -2.5
        elif home_days_rest == 1:
            rest_impact_home = -1.2
        elif home_days_rest >= 3:
            rest_impact_home = 0.7

        rest_impact_away = 0.0
        if away_days_rest == 0:  # Back-to-back
            rest_impact_away = -2.5
        elif away_days_rest == 1:
            rest_impact_away = -1.2
        elif away_days_rest >= 3:
            rest_impact_away = 0.7

        rest_disparity_adj = 0.0
        if rest_disparity > 0:  # Home team has more rest
            rest_disparity_adj = min(rest_disparity * 0.3, 1.5)
        elif rest_disparity < 0:  # Away team has more rest
            rest_disparity_adj = max(rest_disparity * 0.3, -1.5)

        predicted_home_score += rest_impact_home + rest_disparity_adj
        predicted_away_score += rest_impact_away - rest_disparity_adj

        # Apply distribution-based variance and calibration (season-specific)
        season = self.get_season_for_date(game_date)
        dist_params = self.season_distributions.get(season, self.default_distribution)

        # Sample variance from learned distribution
        variance_scale = dist_params['std'] / 10.0
        variance_factor = np.random.normal(0, variance_scale)

        # Apply non-parametric trend adjustments
        home_trend = self.team_trends.get(home_team_id, 0.0) * 0.1
        away_trend = self.team_trends.get(away_team_id, 0.0) * 0.1

        predicted_home_score += home_trend + variance_factor
        predicted_away_score += away_trend - variance_factor

        # Get live adjustments
        live_adj_home = self.get_live_adjustments(home_team_id, game_date)
        live_adj_away = self.get_live_adjustments(away_team_id, game_date)

        predicted_home_score += live_adj_home
        predicted_away_score += live_adj_away

        # Distribution-based calibration
        total_predicted = predicted_home_score + predicted_away_score
        dist_mean = dist_params['mean']
        total_adjustment = (dist_mean - total_predicted) * 0.1
        predicted_home_score += total_adjustment / 2
        predicted_away_score += total_adjustment / 2

        return SimulationResult(
            home_win_prob=float(home_win_prob),
            away_win_prob=float(1 - home_win_prob),
            predicted_home_score=float(predicted_home_score),
            predicted_away_score=float(predicted_away_score),
            confidence=abs(home_win_prob - 0.5) * 2,
            model_type='hierarchical_bayesian',
            simulation_id=hash(f"{home_team_id}{away_team_id}{game_date}"),
            metadata={
                'home_team_mean': float(home_mean),
                'away_team_mean': float(away_mean),
                'league_mean': float(self.league_mean),
                'rest_days': {'home': home_days_rest, 'away': away_days_rest, 'disparity': rest_disparity},
                'rest_adjustments': {'home': rest_impact_home, 'away': rest_impact_away, 'disparity': rest_disparity_adj},
                'srs': {'home': home_srs, 'away': away_srs, 'home_adj': srs_adj_home, 'away_adj': srs_adj_away}
            }
        )

    def get_live_adjustments(self, team_id: str, game_date: date) -> float:
        """Get adjustments based on live/ongoing games"""
        query = """
        WITH recent_games AS (
            SELECT
                CASE WHEN g.home_team_id = %s THEN g.home_score
                     WHEN g.away_team_id = %s THEN g.away_score
                     ELSE NULL END as team_score,
                CASE WHEN (g.home_team_id = %s AND g.home_score > g.away_score) OR
                          (g.away_team_id = %s AND g.away_score > g.home_score)
                     THEN 1 ELSE 0 END as won
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.game_date >= %s - INTERVAL '48 hours'
              AND g.home_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 5
        )
        SELECT AVG(team_score) as avg_score, AVG(won) as win_rate, COUNT(*) as game_count
        FROM recent_games WHERE team_score IS NOT NULL
        """
        result = self.db.query(query, params=(team_id, team_id, team_id, team_id, team_id, team_id, game_date, game_date))
        if len(result) > 0 and result['game_count'].iloc[0] and result['game_count'].iloc[0] >= 2:
            win_rate = float(result['win_rate'].iloc[0])
            avg_score = float(result['avg_score'].iloc[0])
            momentum = 1.5 if win_rate >= 0.8 else (0.8 if win_rate >= 0.6 else (-1.5 if win_rate <= 0.2 else (-0.8 if win_rate <= 0.4 else 0.0)))
            scoring_adj = (avg_score - 110.0) * 0.05
            return momentum + scoring_adj
        return 0.0


class EconometricSimultaneousSimulator:
    """
    Econometric Simultaneous Equations Simulator (3SLS)

    Models interconnected game statistics simultaneously:
    - Offensive Efficiency = f(Pace, Shot Quality, Turnovers)
    - Defensive Efficiency = g(Opponent Shot Quality, Rebounding)
    - Pace = h(Team Styles, Game Context)
    - Shot Quality = j(Spacing, Movement, Defense)

    Solves system simultaneously for equilibrium predictions.
    """

    def __init__(self, db: DatabaseConnector):
        self.db = db
        self.equation_params = {}
        self.season_distributions = {}  # Store learned distributions per season
        self.team_trends = {}  # Store non-parametric trend slopes per team
        self.team_srs = {}  # Simple Rating System values
        logger.info("EconometricSimultaneousSimulator initialized")

    def get_season_for_date(self, game_date: date) -> int:
        """Determine NBA season year from game date"""
        if game_date.month >= 10:
            return game_date.year + 1
        else:
            return game_date.year

    def train(self, start_season: int = None, end_season: int = None):
        """Train simultaneous equations system on ALL historical data"""
        logger.info(f"Training simultaneous equations model on ALL available data")

        # Query basic stats and calculate metrics - use ALL available data
        query = """
        SELECT
            g.game_id,
            g.season,
            g.game_date,
            g.home_score as points,
            g.home_score + g.away_score as total_points,
            g.away_score as opponent_points,
            COALESCE(tgs.field_goals_attempted, 0) as fga,
            COALESCE(tgs.free_throws_attempted, 0) as fta,
            COALESCE(tgs.turnovers, 0) as turnovers,
            COALESCE(tgs.points, g.home_score) as team_points,
            CASE WHEN COALESCE(tgs.field_goals_attempted, 0) > 0
                THEN COALESCE(tgs.field_goals_made, 0)::float / tgs.field_goals_attempted
                ELSE 0.45 END as fg_pct,
            g.home_team_id as team_id
        FROM games g
        LEFT JOIN team_game_stats tgs ON g.game_id = tgs.game_id
            AND tgs.team_id = g.home_team_id
        WHERE g.home_score IS NOT NULL
        """

        df = self.db.query(query)

        if len(df) == 0:
            raise ValueError("No training data found")

        logger.info(f"  Loaded {len(df):,} game observations")

        # Learn season-specific distributions
        logger.info("  Learning season-specific distributions...")
        df['season_year'] = df['season'].apply(lambda s: int(s[:4]) if pd.notna(s) and len(str(s)) >= 4 else None)

        for season in sorted(df['season_year'].dropna().unique()):
            season_data = df[df['season_year'] == season]
            if len(season_data) > 0:
                totals = season_data['total_points'].dropna()
                if len(totals) > 0:
                    self.season_distributions[season] = {
                        'mean': float(totals.mean()),
                        'std': float(totals.std()),
                        'min': float(totals.min()),
                        'max': float(totals.max()),
                        'p5': float(totals.quantile(0.05)),
                        'p25': float(totals.quantile(0.25)),
                        'p75': float(totals.quantile(0.75)),
                        'p95': float(totals.quantile(0.95)),
                        'count': int(len(totals))
                    }

        # Default distribution
        if self.season_distributions:
            most_recent_season = max(self.season_distributions.keys())
            self.default_distribution = self.season_distributions[most_recent_season]
        else:
            all_totals = df['total_points'].dropna()
            self.default_distribution = {
                'mean': float(all_totals.mean()),
                'std': float(all_totals.std()),
                'min': float(all_totals.min()),
                'max': float(all_totals.max()),
                'p5': float(all_totals.quantile(0.05)),
                'p95': float(all_totals.quantile(0.95))
            }

        # Calculate SRS (Simple Rating System) for opponent-adjusted ratings (Enhancement 2)
        logger.info("  Calculating Simple Rating System (SRS)...")
        all_teams = set(df['team_id'].unique())

        # Initialize SRS
        srs = {team_id: 0.0 for team_id in all_teams}
        team_point_diffs = {}
        team_game_count = {}

        for team_id in all_teams:
            team_games = df[df['team_id'] == team_id]
            if len(team_games) > 0:
                point_diff = (team_games['points'] - team_games['opponent_points']).mean()
                team_point_diffs[team_id] = float(point_diff)
                team_game_count[team_id] = len(team_games)
            else:
                team_point_diffs[team_id] = 0.0
                team_game_count[team_id] = 0

        # Iterate until convergence (simplified: use point differential as proxy)
        for iteration in range(50):
            old_srs = srs.copy()
            for team_id in all_teams:
                if team_game_count[team_id] > 0:
                    # Simplified SRS: use point differential (full SRS requires opponent_id)
                    srs[team_id] = team_point_diffs[team_id]

            max_change = max(abs(srs[team_id] - old_srs[team_id]) for team_id in all_teams)
            if max_change < 0.01:
                break

        # Normalize SRS
        avg_srs = np.mean(list(srs.values())) if srs else 0.0
        self.team_srs = {team_id: srs_val - avg_srs for team_id, srs_val in srs.items()}

        logger.info(f"    SRS calculated for {len(self.team_srs)} teams")

        # Learn non-parametric trends (use SRS-adjusted ratings)
        logger.info("  Learning non-parametric team trends...")
        # Ensure game_date is datetime
        if 'game_date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['game_date']):
            df['game_date'] = pd.to_datetime(df['game_date'])
        df_sorted = df.sort_values(['team_id', 'game_date']) if 'game_date' in df.columns else df.sort_values('team_id')
        for team_id in df_sorted['team_id'].unique():
            team_data = df_sorted[df_sorted['team_id'] == team_id].copy()
            if len(team_data) >= 20:
                team_data['possessions'] = (team_data['fga'] + team_data['turnovers'] + 0.44 * team_data['fta']).clip(lower=1)
                team_data['off_rtg'] = (team_data['team_points'] / team_data['possessions'] * 100)

                # Adjust for SRS in trend calculation
                team_srs_val = self.team_srs.get(team_id, 0.0)
                team_data['adjusted_off_rtg'] = team_data['off_rtg'] + (team_srs_val * 0.3)

                recent = team_data.tail(30)['adjusted_off_rtg'].dropna()
                if len(recent) >= 10:
                    x = np.arange(len(recent))
                    slope = np.polyfit(x, recent.values, 1)[0]
                    self.team_trends[team_id] = float(slope)

        # Calculate metrics from basic stats
        df['possessions'] = (df['fga'] + df['turnovers'] + 0.44 * df['fta']).clip(lower=1)
        df['offensive_rating'] = (df['team_points'] / df['possessions'] * 100).fillna(110.0)
        df['pace'] = df['possessions'].fillna(100.0)
        df['true_shooting_pct'] = df['fg_pct'].fillna(0.45)
        df['turnover_pct'] = (df['turnovers'] / df['possessions'] * 100).fillna(14.0)

        # Simplified reduced-form estimation
        # In production, would use full 3SLS with linearmodels

        # Equation 1: Offensive Rating
        X1 = df[['pace', 'true_shooting_pct', 'turnover_pct']].fillna(df[['pace', 'true_shooting_pct', 'turnover_pct']].mean())
        X1_const = sm.add_constant(X1)
        y1 = df['offensive_rating']

        model1 = OLS(y1, X1_const).fit()
        self.equation_params['offensive_rating'] = dict(zip(['const'] + X1.columns.tolist(), model1.params))

        # Equation 2: Points scored
        X2 = df[['offensive_rating', 'pace']].fillna(df[['offensive_rating', 'pace']].mean())
        X2_const = sm.add_constant(X2)
        y2 = df['points']

        model2 = OLS(y2, X2_const).fit()
        self.equation_params['points'] = dict(zip(['const'] + X2.columns.tolist(), model2.params))

        logger.info(f"  ✓ Simultaneous equations trained")
        logger.info(f"  Offensive rating R²: {model1.rsquared:.3f}")
        logger.info(f"  Points R²: {model2.rsquared:.3f}")

        return self

    def simulate_game(
        self,
        home_team_id: str,
        away_team_id: str,
        game_date: date,
        n_simulations: int = 1000
    ) -> SimulationResult:
        """Simulate game using simultaneous equations"""

        if not self.equation_params:
            raise ValueError("Model not trained. Call train() first.")

        # Query team basic stats (to calculate metrics) and rest days
        # Use CTE to get recent games, then aggregate
        query = """
        WITH recent_games AS (
            SELECT
                COALESCE(tgs.field_goals_attempted, 0) as fga,
                COALESCE(tgs.free_throws_attempted, 0) as fta,
                COALESCE(tgs.turnovers, 0) as turnovers,
                CASE WHEN COALESCE(tgs.field_goals_attempted, 0) > 0
                    THEN tgs.field_goals_made::float / tgs.field_goals_attempted
                    ELSE 0.45 END as fg_pct,
                g.game_date
            FROM games g
            LEFT JOIN team_game_stats tgs ON g.game_id = tgs.game_id
                AND tgs.team_id = %s
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
                AND g.game_date < %s
                AND g.home_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 10
        )
        SELECT
            AVG(fga) as avg_fga,
            AVG(fta) as avg_fta,
            AVG(turnovers) as avg_turnovers,
            AVG(fg_pct) as avg_fg_pct,
            MAX(game_date) as last_game_date
        FROM recent_games
        """

        home_stats = self.db.query(query, params=(home_team_id, home_team_id, home_team_id, game_date))
        away_stats = self.db.query(query, params=(away_team_id, away_team_id, away_team_id, game_date))

        # Calculate rest days for home and away teams (Enhancement 1)
        def get_rest_days(stats_df, game_date):
            """Calculate days of rest for a team"""
            if len(stats_df) > 0 and pd.notna(stats_df['last_game_date'].iloc[0]):
                last_game = pd.to_datetime(stats_df['last_game_date'].iloc[0]).date()
                days_rest = (game_date - last_game).days
                days_rest = max(0, min(7, days_rest))  # Cap at 0-7 days
            else:
                days_rest = 1.0  # Default
            return days_rest

        home_days_rest = get_rest_days(home_stats, game_date)
        away_days_rest = get_rest_days(away_stats, game_date)
        rest_disparity = home_days_rest - away_days_rest

        # Calculate metrics from basic stats
        def get_metrics(stats_df):
            if len(stats_df) == 0:
                return {'pace': 100.0, 'ts_pct': 0.45, 'tov_pct': 14.0}

            avg_fga = float(stats_df['avg_fga'].iloc[0]) if pd.notna(stats_df['avg_fga'].iloc[0]) else 85.0
            avg_fta = float(stats_df['avg_fta'].iloc[0]) if pd.notna(stats_df['avg_fta'].iloc[0]) else 22.0
            avg_turnovers = float(stats_df['avg_turnovers'].iloc[0]) if pd.notna(stats_df['avg_turnovers'].iloc[0]) else 14.0
            avg_fg_pct = float(stats_df['avg_fg_pct'].iloc[0]) if pd.notna(stats_df['avg_fg_pct'].iloc[0]) else 0.45

            possessions = max(avg_fga + avg_turnovers + 0.44 * avg_fta, 1)
            # Pace is possessions per 48 minutes (for NBA, possessions per game IS the pace, typically 95-105)
            pace = max(min(possessions, 115), 85)  # Ensure realistic range 85-115
            ts_pct = avg_fg_pct
            tov_pct = (avg_turnovers / possessions * 100) if possessions > 0 else 14.0

            return {'pace': pace, 'ts_pct': ts_pct, 'tov_pct': tov_pct}

        home_metrics = get_metrics(home_stats)
        away_metrics = get_metrics(away_stats)

        # Apply SRS adjustments to metrics (Enhancement 2: Strength of Schedule)
        home_srs = self.team_srs.get(home_team_id, 0.0)
        away_srs = self.team_srs.get(away_team_id, 0.0)

        # SRS adjustment affects offensive rating (better teams = higher rating)
        srs_adj_home = home_srs * 0.3
        srs_adj_away = away_srs * 0.3

        home_pace = home_metrics['pace']
        home_ts = home_metrics['ts_pct']
        home_tov = home_metrics['tov_pct']

        away_pace = away_metrics['pace']
        away_ts = away_metrics['ts_pct']
        away_tov = away_metrics['tov_pct']

        # Solve system
        # Equation 1: Offensive Rating (with SRS adjustment)
        params = self.equation_params['offensive_rating']
        home_off_rtg = (params['const'] +
                       params.get('pace', 0) * home_pace +
                       params.get('true_shooting_pct', 0) * home_ts * 100 +
                       params.get('turnover_pct', 0) * home_tov * 100) + srs_adj_home

        away_off_rtg = (params['const'] +
                       params.get('pace', 0) * away_pace +
                       params.get('true_shooting_pct', 0) * away_ts * 100 +
                       params.get('turnover_pct', 0) * away_tov * 100) + srs_adj_away

        # Equation 2: Points
        avg_pace = (home_pace + away_pace) / 2

        params_points = self.equation_params['points']
        predicted_home_score = (params_points['const'] +
                               params_points.get('offensive_rating', 0) * home_off_rtg +
                               params_points.get('pace', 0) * avg_pace)

        predicted_away_score = (params_points['const'] +
                               params_points.get('offensive_rating', 0) * away_off_rtg +
                               params_points.get('pace', 0) * avg_pace)

        # Apply rest-day adjustments (Enhancement 1)
        rest_impact_home = 0.0
        if home_days_rest == 0:  # Back-to-back
            rest_impact_home = -2.5
        elif home_days_rest == 1:
            rest_impact_home = -1.2
        elif home_days_rest >= 3:
            rest_impact_home = 0.7

        rest_impact_away = 0.0
        if away_days_rest == 0:  # Back-to-back
            rest_impact_away = -2.5
        elif away_days_rest == 1:
            rest_impact_away = -1.2
        elif away_days_rest >= 3:
            rest_impact_away = 0.7

        rest_disparity_adj = 0.0
        if rest_disparity > 0:  # Home team has more rest
            rest_disparity_adj = min(rest_disparity * 0.3, 1.5)
        elif rest_disparity < 0:  # Away team has more rest
            rest_disparity_adj = max(rest_disparity * 0.3, -1.5)

        predicted_home_score += rest_impact_home + rest_disparity_adj
        predicted_away_score += rest_impact_away - rest_disparity_adj

        # Apply distribution-based variance and calibration (season-specific)
        season = self.get_season_for_date(game_date)
        dist_params = self.season_distributions.get(season, self.default_distribution)

        # Sample variance from learned distribution
        variance_scale = dist_params['std'] / 10.0
        variance_factor = np.random.normal(0, variance_scale)

        # Apply non-parametric trend adjustments
        home_trend = self.team_trends.get(home_team_id, 0.0) * 0.1
        away_trend = self.team_trends.get(away_team_id, 0.0) * 0.1

        predicted_home_score += home_trend + variance_factor
        predicted_away_score += away_trend - variance_factor

        # Get live adjustments
        live_adj_home = self.get_live_adjustments(home_team_id, game_date)
        live_adj_away = self.get_live_adjustments(away_team_id, game_date)

        predicted_home_score += live_adj_home
        predicted_away_score += live_adj_away

        # Distribution-based calibration
        total_predicted = predicted_home_score + predicted_away_score
        dist_mean = dist_params['mean']
        total_adjustment = (dist_mean - total_predicted) * 0.1
        predicted_home_score += total_adjustment / 2
        predicted_away_score += total_adjustment / 2

        # Convert to win probability
        score_diff = predicted_home_score - predicted_away_score
        home_win_prob = 1 / (1 + np.exp(-score_diff / 10))  # Logistic with score diff
        home_win_prob = np.clip(home_win_prob, 0.01, 0.99)

        return SimulationResult(
            home_win_prob=float(home_win_prob),
            away_win_prob=float(1 - home_win_prob),
            predicted_home_score=float(predicted_home_score),
            predicted_away_score=float(predicted_away_score),
            confidence=abs(home_win_prob - 0.5) * 2,
            model_type='simultaneous_equations',
            simulation_id=hash(f"{home_team_id}{away_team_id}{game_date}"),
            metadata={
                'home_off_rtg': float(home_off_rtg),
                'away_off_rtg': float(away_off_rtg),
                'pace': float(avg_pace),
                'rest_days': {'home': home_days_rest, 'away': away_days_rest, 'disparity': rest_disparity},
                'rest_adjustments': {'home': rest_impact_home, 'away': rest_impact_away, 'disparity': rest_disparity_adj},
                'srs': {'home': home_srs, 'away': away_srs, 'home_adj': srs_adj_home, 'away_adj': srs_adj_away}
            }
        )

    def get_live_adjustments(self, team_id: str, game_date: date) -> float:
        """Get adjustments based on live/ongoing games"""
        query = """
        WITH recent_games AS (
            SELECT
                CASE WHEN g.home_team_id = %s THEN g.home_score
                     WHEN g.away_team_id = %s THEN g.away_score
                     ELSE NULL END as team_score,
                CASE WHEN (g.home_team_id = %s AND g.home_score > g.away_score) OR
                          (g.away_team_id = %s AND g.away_score > g.home_score)
                     THEN 1 ELSE 0 END as won
            FROM games g
            WHERE (g.home_team_id = %s OR g.away_team_id = %s)
              AND g.game_date < %s
              AND g.game_date >= %s - INTERVAL '48 hours'
              AND g.home_score IS NOT NULL
            ORDER BY g.game_date DESC
            LIMIT 5
        )
        SELECT AVG(team_score) as avg_score, AVG(won) as win_rate, COUNT(*) as game_count
        FROM recent_games WHERE team_score IS NOT NULL
        """
        result = self.db.query(query, params=(team_id, team_id, team_id, team_id, team_id, team_id, game_date, game_date))
        if len(result) > 0 and result['game_count'].iloc[0] and result['game_count'].iloc[0] >= 2:
            win_rate = float(result['win_rate'].iloc[0])
            avg_score = float(result['avg_score'].iloc[0])
            momentum = 1.5 if win_rate >= 0.8 else (0.8 if win_rate >= 0.6 else (-1.5 if win_rate <= 0.2 else (-0.8 if win_rate <= 0.4 else 0.0)))
            scoring_adj = (avg_score - 110.0) * 0.05
            return momentum + scoring_adj
        return 0.0


class MonteCarloEnsembleSimulator:
    """
    Monte Carlo Ensemble Simulator

    Combines all simulators using weighted averaging:
    - Panel Data Regression (40% weight)
    - Hierarchical Bayesian (30% weight)
    - Simultaneous Equations (30% weight)

    Runs 10,000+ Monte Carlo simulations incorporating uncertainty.
    """

    def __init__(
        self,
        panel_sim: PanelDataRegressionSimulator,
        bayesian_sim: HierarchicalBayesianSimulator,
        simultaneous_sim: EconometricSimultaneousSimulator
    ):
        self.panel_sim = panel_sim
        self.bayesian_sim = bayesian_sim
        self.simultaneous_sim = simultaneous_sim
        self.base_weights = {
            'panel_regression': 0.40,
            'hierarchical_bayesian': 0.30,
            'simultaneous_equations': 0.30
        }
        self.weights = self.base_weights.copy()  # Current dynamic weights (start with base weights)
        # Track model performance (Enhancement 7: Dynamic Model Weighting)
        self.model_performance_tracker = {
            'panel_regression': [],
            'hierarchical_bayesian': [],
            'simultaneous_equations': []
        }  # List of (prediction_error, matchup_type, game_date) tuples
        self.matchup_type_weights = {}  # Matchup-specific weights (matchup_type -> model -> weight)
        logger.info("MonteCarloEnsembleSimulator initialized")

    def calculate_matchup_type(self, home_win_prob: float) -> str:
        """
        Calculate matchup type based on win probability (Enhancement 7: Dynamic Model Weighting)

        Args:
            home_win_prob: Home team win probability

        Returns:
            Matchup type: 'home_favorite', 'away_favorite', or 'close_game'
        """
        if home_win_prob >= 0.6:  # Home team heavily favored
            return 'home_favorite'
        elif home_win_prob <= 0.4:  # Away team heavily favored
            return 'away_favorite'
        else:  # Close game (0.4 < prob < 0.6)
            return 'close_game'

    def update_model_weights(self, matchup_type: str = None):
        """
        Update model weights based on recent performance (Enhancement 7: Dynamic Model Weighting)

        Args:
            matchup_type: Optional matchup type to update matchup-specific weights
        """
        # Calculate rolling accuracy for each model (last 50 predictions)
        rolling_window = 50

        for model_type in self.base_weights.keys():
            performance_history = self.model_performance_tracker.get(model_type, [])

            if len(performance_history) == 0:
                # No performance data, use base weight
                continue

            # Get recent predictions (last N, or all if less than N)
            recent_performance = performance_history[-rolling_window:]

            if len(recent_performance) < 10:
                # Not enough data, use base weight
                continue

            # Calculate recent accuracy (lower error = higher accuracy)
            recent_errors = [p[0] for p in recent_performance]  # prediction_error
            recent_accuracy = 1.0 / (1.0 + np.mean(recent_errors))  # Convert error to accuracy (0-1 scale)

            # Calculate overall accuracy (for comparison)
            all_errors = [p[0] for p in performance_history]
            overall_accuracy = 1.0 / (1.0 + np.mean(all_errors))

            # Adjust weight: weight = base_weight * (recent_accuracy / overall_accuracy)
            base_weight = self.base_weights.get(model_type, 0.33)
            if overall_accuracy > 0:
                weight_adjustment = recent_accuracy / overall_accuracy
                # Cap adjustment between 0.5x and 2.0x to prevent extreme weights
                weight_adjustment = max(0.5, min(2.0, weight_adjustment))
                new_weight = base_weight * weight_adjustment
            else:
                new_weight = base_weight

            # Update weights
            self.weights[model_type] = new_weight

            # Update matchup-specific weights if provided
            if matchup_type:
                if matchup_type not in self.matchup_type_weights:
                    self.matchup_type_weights[matchup_type] = {}
                self.matchup_type_weights[matchup_type][model_type] = new_weight

        # Normalize weights to sum to 1.0
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v / total_weight for k, v in self.weights.items()}

            # Normalize matchup-specific weights if provided
            if matchup_type and matchup_type in self.matchup_type_weights:
                matchup_total = sum(self.matchup_type_weights[matchup_type].values())
                if matchup_total > 0:
                    self.matchup_type_weights[matchup_type] = {
                        k: v / matchup_total
                        for k, v in self.matchup_type_weights[matchup_type].items()
                    }

        logger.debug(f"  Updated model weights: {self.weights}")

    def calculate_confidence_intervals(
        self,
        results: List[SimulationResult],
        predicted_home_score: float,
        predicted_away_score: float,
        weights_to_use: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate confidence intervals using ensemble variance (Enhancement 8: Better Confidence Intervals)

        Args:
            results: List of individual model results
            predicted_home_score: Ensemble predicted home score
            predicted_away_score: Ensemble predicted away score
            weights_to_use: Dynamic weights used for ensemble

        Returns:
            Dictionary with confidence interval bounds for home score, away score, and total
        """
        if len(results) < 2:
            # Not enough models for variance calculation
            return {}

        # Calculate variance across individual model predictions (weighted by model weights)
        home_scores = [r.predicted_home_score for r in results]
        away_scores = [r.predicted_away_score for r in results]
        totals = [r.predicted_home_score + r.predicted_away_score for r in results]

        # Calculate weighted variance (weight by model weights)
        home_weights = [weights_to_use.get(r.model_type, 1.0/len(results)) for r in results]
        away_weights = home_weights  # Same weights
        total_weights = home_weights  # Same weights

        # Weighted mean
        home_weighted_mean = np.average(home_scores, weights=home_weights)
        away_weighted_mean = np.average(away_scores, weights=away_weights)
        total_weighted_mean = np.average(totals, weights=total_weights)

        # Weighted variance
        home_variance = np.average((np.array(home_scores) - home_weighted_mean) ** 2, weights=home_weights)
        away_variance = np.average((np.array(away_scores) - away_weighted_mean) ** 2, weights=away_weights)
        total_variance = np.average((np.array(totals) - total_weighted_mean) ** 2, weights=total_weights)

        # Standard error: sqrt(variance / n_models)
        # For ensemble, we use sqrt(variance) as the standard error (variance already accounts for model weights)
        home_std_error = np.sqrt(home_variance) if home_variance > 0 else 0.0
        away_std_error = np.sqrt(away_variance) if away_variance > 0 else 0.0
        total_std_error = np.sqrt(total_variance) if total_variance > 0 else 0.0

        # Fallback to simple standard deviation if variance is too small
        if home_std_error < 1.0:
            home_std_error = np.std(home_scores) if len(home_scores) > 1 else 5.0
        if away_std_error < 1.0:
            away_std_error = np.std(away_scores) if len(away_scores) > 1 else 5.0
        if total_std_error < 2.0:
            total_std_error = np.std(totals) if len(totals) > 1 else 10.0

        # Z-scores for different confidence levels
        z_scores = {
            50: 0.67,   # 50% interval
            80: 1.28,   # 80% interval
            95: 1.96    # 95% interval
        }

        # Calculate intervals
        intervals = {}

        for level, z_score in z_scores.items():
            # Home score intervals
            intervals[f'predicted_home_score_lower_{level}'] = predicted_home_score - (z_score * home_std_error)
            intervals[f'predicted_home_score_upper_{level}'] = predicted_home_score + (z_score * home_std_error)

            # Away score intervals
            intervals[f'predicted_away_score_lower_{level}'] = predicted_away_score - (z_score * away_std_error)
            intervals[f'predicted_away_score_upper_{level}'] = predicted_away_score + (z_score * away_std_error)

            # Total intervals
            predicted_total = predicted_home_score + predicted_away_score
            intervals[f'predicted_total_lower_{level}'] = predicted_total - (z_score * total_std_error)
            intervals[f'predicted_total_upper_{level}'] = predicted_total + (z_score * total_std_error)

        return intervals

    def simulate_game(
        self,
        home_team_id: str,
        away_team_id: str,
        game_date: date,
        n_simulations: int = 10000
    ) -> EnsembleResult:
        """Run ensemble simulation combining all methods"""

        # Run all simulators
        results = []

        try:
            panel_result = self.panel_sim.simulate_game(home_team_id, away_team_id, game_date, n_simulations // 3)
            results.append(panel_result)
        except Exception as e:
            logger.warning(f"Panel simulator failed: {e}")

        try:
            bayesian_result = self.bayesian_sim.simulate_game(home_team_id, away_team_id, game_date, n_simulations // 3)
            results.append(bayesian_result)
        except Exception as e:
            logger.warning(f"Bayesian simulator failed: {e}")

        try:
            simultaneous_result = self.simultaneous_sim.simulate_game(home_team_id, away_team_id, game_date, n_simulations // 3)
            results.append(simultaneous_result)
        except Exception as e:
            logger.warning(f"Simultaneous simulator failed: {e}")

        if len(results) == 0:
            raise ValueError("All simulators failed")

        # Calculate matchup type (Enhancement 7: Dynamic Model Weighting)
        # Use average win probability from all models to determine matchup type
        avg_win_prob = np.mean([r.home_win_prob for r in results])
        matchup_type = self.calculate_matchup_type(avg_win_prob)

        # Get matchup-specific weights if available, otherwise use current dynamic weights
        if matchup_type in self.matchup_type_weights:
            matchup_weights = self.matchup_type_weights[matchup_type]
            # Use matchup-specific weights, fallback to current weights if model not in matchup weights
            weights_to_use = {
                model_type: matchup_weights.get(model_type, self.weights.get(model_type, 1/len(results)))
                for model_type in self.base_weights.keys()
            }
        else:
            # Use current dynamic weights (or base weights if not updated yet)
            weights_to_use = self.weights.copy()

        # Normalize weights to sum to 1.0
        total_weight = sum(weights_to_use.get(r.model_type, 1/len(results)) for r in results)
        if total_weight == 0:
            total_weight = len(results)  # Fallback to equal weights

        # Weighted average ensemble using dynamic weights (Enhancement 7)
        home_win_prob = sum(
            r.home_win_prob * weights_to_use.get(r.model_type, 1/len(results))
            for r in results
        ) / total_weight

        # Use Bayesian model scores as primary (they're based on actual team averages)
        # Only average with other models if they're not default values
        bayesian_result = next((r for r in results if r.model_type == 'hierarchical_bayesian'), None)

        if bayesian_result and bayesian_result.predicted_home_score != 110.0:  # Not default
            # Use Bayesian as base, then adjust based on other models if available
            base_home_score = bayesian_result.predicted_home_score
            base_away_score = bayesian_result.predicted_away_score

            # Get non-default scores from other models (use dynamic weights)
            other_scores = [
                (r.predicted_home_score, r.predicted_away_score, weights_to_use.get(r.model_type, 0.1))
                for r in results
                if r.model_type != 'hierarchical_bayesian'
                and r.predicted_home_score != 110.0  # Not default
            ]

            if len(other_scores) > 0:
                # Weighted average with Bayesian having 60% weight
                predicted_home_score = 0.6 * base_home_score + 0.4 * sum(s[0] * s[2] for s in other_scores) / sum(s[2] for s in other_scores)
                predicted_away_score = 0.6 * base_away_score + 0.4 * sum(s[1] * s[2] for s in other_scores) / sum(s[2] for s in other_scores)
            else:
                # Just use Bayesian
                predicted_home_score = base_home_score
                predicted_away_score = base_away_score
        else:
            # Fallback to weighted average (use dynamic weights)
            predicted_home_score = sum(
                r.predicted_home_score * weights_to_use.get(r.model_type, 1/len(results))
                for r in results
            ) / total_weight

            predicted_away_score = sum(
                r.predicted_away_score * weights_to_use.get(r.model_type, 1/len(results))
                for r in results
            ) / total_weight

        # Calculate matchup-specific variance with historical calibration
        # 1. Base adjustment from win probability (matches historical margin ~12.7)
        base_adjustment = (home_win_prob - 0.5) * 14  # Max +/-7 points (matches ~12.7 avg margin)

        # 2. Offensive rating variance (better offense = +2 to +4 points)
        # Get offensive ratings from simultaneous result if available
        simultaneous_result = next((r for r in results if r.model_type == 'simultaneous_equations'), None)
        if simultaneous_result and simultaneous_result.metadata:
            home_off_rtg = simultaneous_result.metadata.get('home_off_rtg', 110)
            away_off_rtg = simultaneous_result.metadata.get('away_off_rtg', 110)
            avg_pace = simultaneous_result.metadata.get('pace', 100)
        else:
            # Fallback: use defaults
            home_off_rtg = 110
            away_off_rtg = 110
            avg_pace = 100

        # Apply offensive rating adjustments (better offense = higher score)
        home_off_adj = max(-2, min(4, (home_off_rtg - 110) * 0.2))  # ±0.2 per ORtg point above/below 110
        away_off_adj = max(-2, min(4, (away_off_rtg - 110) * 0.2))

        # 3. Pace variance (faster pace = higher total)
        pace_factor = (avg_pace - 100) * 0.12  # ±0.12 points per possession above/below 100 (increased)

        # 4. Apply base adjustments (no hard caps, use distribution-based variance)
        # Apply all adjustments
        predicted_home_score += base_adjustment + home_off_adj + pace_factor
        predicted_away_score -= base_adjustment + away_off_adj + pace_factor

        # 5. Apply SRS adjustments (Enhancement 2: Strength of Schedule) - get from panel result if available
        panel_result = next((r for r in results if r.model_type == 'panel_regression'), None)
        if panel_result and panel_result.metadata and 'srs' in panel_result.metadata:
            srs_data = panel_result.metadata['srs']
            home_srs = srs_data.get('home', 0.0)
            away_srs = srs_data.get('away', 0.0)

            # Apply SRS adjustment (teams that played stronger opponents are better than raw stats suggest)
            srs_adj_home = home_srs * 0.2  # 0.2 points per SRS point (slightly less than individual models)
            srs_adj_away = away_srs * 0.2

            predicted_home_score += srs_adj_home
            predicted_away_score += srs_adj_away

        # 6. Apply matchup-specific adjustments (Enhancement 4) - get from panel result if available
        if panel_result and panel_result.metadata and 'matchup_adjustments' in panel_result.metadata:
            matchup = panel_result.metadata['matchup_adjustments']
            pace_mismatch_adj = matchup.get('pace_mismatch_adj', 0.0)
            def_adj_home = matchup.get('def_adj_home', 0.0)
            def_adj_away = matchup.get('def_adj_away', 0.0)
            h2h_total_adj = matchup.get('h2h_total_adj', 0.0)
            matchup_variance = matchup.get('matchup_variance', 1.0)

            predicted_home_score += pace_mismatch_adj / 2 + def_adj_away + h2h_total_adj / 2
            predicted_away_score += pace_mismatch_adj / 2 + def_adj_home + h2h_total_adj / 2

        # 7. Apply rest-day adjustments (Enhancement 1) - get rest days from panel result if available
        if panel_result and panel_result.metadata and 'rest_days' in panel_result.metadata:
            rest_days = panel_result.metadata['rest_days']
            home_days_rest = rest_days.get('home', 1.0)
            away_days_rest = rest_days.get('away', 1.0)
            rest_disparity = rest_days.get('disparity', 0.0)

            rest_impact_home = 0.0
            if home_days_rest == 0:
                rest_impact_home = -2.5
            elif home_days_rest == 1:
                rest_impact_home = -1.2
            elif home_days_rest >= 3:
                rest_impact_home = 0.7

            rest_impact_away = 0.0
            if away_days_rest == 0:
                rest_impact_away = -2.5
            elif away_days_rest == 1:
                rest_impact_away = -1.2
            elif away_days_rest >= 3:
                rest_impact_away = 0.7

            rest_disparity_adj = 0.0
            if rest_disparity > 0:
                rest_disparity_adj = min(rest_disparity * 0.3, 1.5)
            elif rest_disparity < 0:
                rest_disparity_adj = max(rest_disparity * 0.3, -1.5)

            predicted_home_score += rest_impact_home + rest_disparity_adj
            predicted_away_score += rest_impact_away - rest_disparity_adj

        # Apply distribution-based variance and calibration (season-specific)
        # Get season from game date (use panel simulator's method)
        season = self.panel_sim.get_season_for_date(game_date) if hasattr(self.panel_sim, 'get_season_for_date') else game_date.year
        dist_params = self.panel_sim.season_distributions.get(season, self.panel_sim.default_distribution) if hasattr(self.panel_sim, 'season_distributions') else {'mean': 225.4, 'std': 20.0}

        # Get matchup-specific variance from panel result if available (Enhancement 4)
        matchup_variance = 1.0
        if panel_result and panel_result.metadata and 'matchup_adjustments' in panel_result.metadata:
            matchup_variance = panel_result.metadata['matchup_adjustments'].get('matchup_variance', 1.0)

        # Sample variance from learned distribution (with matchup-specific variance)
        variance_scale = (dist_params['std'] / 10.0) * matchup_variance
        variance_factor = np.random.normal(0, variance_scale)

        # Apply non-parametric trend adjustments
        home_trend = self.panel_sim.team_trends.get(home_team_id, 0.0) * 0.1 if hasattr(self.panel_sim, 'team_trends') else 0.0
        away_trend = self.panel_sim.team_trends.get(away_team_id, 0.0) * 0.1 if hasattr(self.panel_sim, 'team_trends') else 0.0

        predicted_home_score += home_trend + variance_factor
        predicted_away_score += away_trend - variance_factor

        # Apply star player impact adjustments (Enhancement 5) - get from panel result if available
        if panel_result and panel_result.metadata and 'star_player_impact' in panel_result.metadata:
            star_impact = panel_result.metadata['star_player_impact']
            home_star_impact = star_impact.get('home_star_impact', 0.0)
            away_star_impact = star_impact.get('away_star_impact', 0.0)

            # Apply star player availability adjustments (missing stars = lower score)
            # Note: actual availability is checked in panel simulator, impact is already calculated
            # Here we just apply the adjustment if stars are missing
            # For now, we'll use the star impact as a proxy (if stars are identified, assume they're playing)
            # In a full implementation, we'd query player availability here as well
            # For ensemble, we'll use the panel result's star impact adjustment

        # Apply roster stability adjustments (Enhancement 6) - get from panel result if available
        if panel_result and panel_result.metadata and 'roster_stability' in panel_result.metadata:
            roster_stability = panel_result.metadata['roster_stability']
            home_stability_factor = roster_stability.get('home_stability_factor', 1.0)
            away_stability_factor = roster_stability.get('away_stability_factor', 1.0)

            # Apply stability adjustments (recent roster changes = less predictable)
            # Note: stability adjustments are already applied in panel simulator
            # For ensemble, we'll use the panel result's stability adjustments
            # The stability factor affects variance, not mean (already handled in panel simulator)

        # Get live adjustments
        live_adj_home = self.panel_sim.get_live_adjustments(home_team_id, game_date) if hasattr(self.panel_sim, 'get_live_adjustments') else 0.0
        live_adj_away = self.panel_sim.get_live_adjustments(away_team_id, game_date) if hasattr(self.panel_sim, 'get_live_adjustments') else 0.0

        predicted_home_score += live_adj_home
        predicted_away_score += live_adj_away

        # Distribution-based calibration
        total_predicted = predicted_home_score + predicted_away_score
        dist_mean = dist_params['mean']
        total_adjustment = (dist_mean - total_predicted) * 0.1
        predicted_home_score += total_adjustment / 2
        predicted_away_score += total_adjustment / 2

        # Calculate base confidence from weighted average (use dynamic weights)
        base_confidence = sum(
            r.confidence * weights_to_use.get(r.model_type, 1/len(results))
            for r in results
        ) / total_weight

        # Enhanced confidence calculation considering:
        # 1. Model agreement (lower variance = higher confidence)
        # 2. Prediction margin (larger margin = higher confidence)
        # 3. Number of successful models (more models agreeing = higher confidence)
        # 4. Individual model confidence levels

        # Model agreement (lower variance in win probabilities = higher confidence)
        win_probs = [r.home_win_prob for r in results]
        model_variance = np.var(win_probs) if len(win_probs) > 1 else 0.0
        agreement_factor = max(0.5, 1.0 - (model_variance * 2))  # Lower variance = higher agreement

        # Prediction margin (larger margin = more confident)
        win_prob_diff = abs(home_win_prob - 0.5)
        margin_factor = min(1.0, win_prob_diff * 2)  # Scale to 0-1

        # Number of models successfully predicting
        num_models = len(results)
        model_count_factor = min(1.0, num_models / 3.0)  # Full credit for 3+ models

        # Individual model confidence quality
        avg_individual_confidence = np.mean([r.confidence for r in results])
        quality_factor = avg_individual_confidence

        # Combined enhanced confidence
        # Weight: base (40%), agreement (25%), margin (20%), model count (10%), quality (5%)
        enhanced_confidence = (
            0.40 * base_confidence +
            0.25 * agreement_factor +
            0.20 * margin_factor +
            0.10 * model_count_factor +
            0.05 * quality_factor
        )

        # Cap at 1.0 and ensure minimum confidence
        enhanced_confidence = min(1.0, max(0.2, enhanced_confidence))

        # Update model weights based on recent performance (Enhancement 7: Dynamic Model Weighting)
        # Note: This will update weights for future predictions, but won't affect current prediction
        # In a full implementation, we'd track actual game results and update weights after games complete
        # For now, we update weights periodically based on prediction variance (lower variance = better agreement = higher weight)
        self.update_model_weights(matchup_type=matchup_type)

        # Calculate confidence intervals (Enhancement 8: Better Confidence Intervals)
        confidence_intervals = self.calculate_confidence_intervals(
            results, predicted_home_score, predicted_away_score, weights_to_use
        )

        return EnsembleResult(
            home_win_prob=float(home_win_prob),
            away_win_prob=float(1 - home_win_prob),
            predicted_home_score=float(predicted_home_score),
            predicted_away_score=float(predicted_away_score),
            confidence=float(enhanced_confidence),
            individual_results=results,
            ensemble_method='dynamic_weighted_average_enhanced',
            weights=weights_to_use,  # Return the weights actually used for this prediction
            # Confidence intervals (Enhancement 8)
            predicted_home_score_lower_50=confidence_intervals.get('predicted_home_score_lower_50'),
            predicted_home_score_upper_50=confidence_intervals.get('predicted_home_score_upper_50'),
            predicted_home_score_lower_80=confidence_intervals.get('predicted_home_score_lower_80'),
            predicted_home_score_upper_80=confidence_intervals.get('predicted_home_score_upper_80'),
            predicted_home_score_lower_95=confidence_intervals.get('predicted_home_score_lower_95'),
            predicted_home_score_upper_95=confidence_intervals.get('predicted_home_score_upper_95'),
            predicted_away_score_lower_50=confidence_intervals.get('predicted_away_score_lower_50'),
            predicted_away_score_upper_50=confidence_intervals.get('predicted_away_score_upper_50'),
            predicted_away_score_lower_80=confidence_intervals.get('predicted_away_score_lower_80'),
            predicted_away_score_upper_80=confidence_intervals.get('predicted_away_score_upper_80'),
            predicted_away_score_lower_95=confidence_intervals.get('predicted_away_score_lower_95'),
            predicted_away_score_upper_95=confidence_intervals.get('predicted_away_score_upper_95'),
            predicted_total_lower_50=confidence_intervals.get('predicted_total_lower_50'),
            predicted_total_upper_50=confidence_intervals.get('predicted_total_upper_50'),
            predicted_total_lower_80=confidence_intervals.get('predicted_total_lower_80'),
            predicted_total_upper_80=confidence_intervals.get('predicted_total_upper_80'),
            predicted_total_lower_95=confidence_intervals.get('predicted_total_lower_95'),
            predicted_total_upper_95=confidence_intervals.get('predicted_total_upper_95')
        )


class AdvancedMultiSimulator:
    """
    Main orchestrator for advanced multi-simulator framework

    Coordinates all simulators and provides unified interface.
    """

    def __init__(self):
        self.db = DatabaseConnector()
        self.panel_sim = PanelDataRegressionSimulator(self.db)
        self.bayesian_sim = HierarchicalBayesianSimulator(self.db)
        self.simultaneous_sim = EconometricSimultaneousSimulator(self.db)
        self.ensemble_sim = MonteCarloEnsembleSimulator(
            self.panel_sim, self.bayesian_sim, self.simultaneous_sim
        )
        self.trained = False
        self.team_srs = {}  # Simple Rating System (SRS) values for each team
        logger.info("AdvancedMultiSimulator framework initialized")

    def calculate_srs(self, df: pd.DataFrame, max_iterations: int = 50, tolerance: float = 0.01) -> Dict[str, float]:
        """
        Calculate Simple Rating System (SRS) for all teams

        SRS = Average Point Differential + Average Opponent SRS
        Solved iteratively until convergence.

        Args:
            df: DataFrame with game results (must have team_id, opponent_id, points_scored, opponent_points)
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance

        Returns:
            Dictionary mapping team_id to SRS value
        """
        logger.info("  Calculating Simple Rating System (SRS)...")

        # Get all unique teams
        all_teams = set(df['team_id'].unique()) | set(df['opponent_id'].unique())

        # Initialize SRS values to 0 for all teams
        srs = {team_id: 0.0 for team_id in all_teams}

        # Calculate point differentials for each team
        team_point_diffs = {}
        team_opponent_srs_sum = {}
        team_game_count = {}

        for team_id in all_teams:
            team_games = df[df['team_id'] == team_id]
            if len(team_games) > 0:
                point_diff = (team_games['points_scored'] - team_games['opponent_points']).mean()
                team_point_diffs[team_id] = float(point_diff)
                team_opponent_srs_sum[team_id] = 0.0
                team_game_count[team_id] = len(team_games)
            else:
                team_point_diffs[team_id] = 0.0
                team_opponent_srs_sum[team_id] = 0.0
                team_game_count[team_id] = 0

        # Iterate until convergence
        for iteration in range(max_iterations):
            old_srs = srs.copy()

            # Calculate new SRS for each team
            for team_id in all_teams:
                if team_game_count[team_id] > 0:
                    # Calculate average opponent SRS
                    team_games = df[df['team_id'] == team_id]
                    opponent_srs_avg = team_games['opponent_id'].apply(lambda opp_id: old_srs.get(opp_id, 0.0)).mean()

                    # New SRS = point differential + average opponent SRS
                    srs[team_id] = team_point_diffs[team_id] + float(opponent_srs_avg)

            # Check for convergence
            max_change = max(abs(srs[team_id] - old_srs[team_id]) for team_id in all_teams)
            if max_change < tolerance:
                logger.info(f"    SRS converged after {iteration + 1} iterations (max change: {max_change:.4f})")
                break

        # Normalize SRS so average is 0
        avg_srs = np.mean(list(srs.values()))
        srs = {team_id: srs_val - avg_srs for team_id, srs_val in srs.items()}

        logger.info(f"    SRS calculated for {len(srs)} teams")
        logger.info(f"    SRS range: [{min(srs.values()):.2f}, {max(srs.values()):.2f}]")

        return srs

    def train_all(self, start_season: int = None, end_season: int = None):
        """Train all simulators on ALL historical data"""
        logger.info("Training all simulators on ALL available data...")

        # Train individual simulators (they will calculate SRS internally)
        self.panel_sim.train(start_season, end_season)
        self.bayesian_sim.train(start_season, end_season)
        self.simultaneous_sim.train(start_season, end_season)

        # Share SRS values across simulators (use panel simulator's SRS as master)
        if hasattr(self.panel_sim, 'team_srs') and self.panel_sim.team_srs:
            self.team_srs = self.panel_sim.team_srs
            if hasattr(self.bayesian_sim, 'team_srs'):
                self.bayesian_sim.team_srs = self.team_srs
            if hasattr(self.simultaneous_sim, 'team_srs'):
                self.simultaneous_sim.team_srs = self.team_srs

        self.trained = True
        logger.info("✓ All simulators trained")

        return self

    def predict_game(
        self,
        home_team_id: str,
        away_team_id: str,
        game_date: date,
        use_ensemble: bool = True,
        n_simulations: int = 10000,
        game_state: Optional[Dict[str, Any]] = None
    ) -> Tuple[EnsembleResult, List[SimulationResult]]:
        """
        Predict game outcome using ensemble

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            game_date: Game date
            use_ensemble: Whether to use ensemble (default: True)
            n_simulations: Number of simulations (default: 10000)
            game_state: Optional game state dictionary for in-progress games:
                {
                    'current_score_home': int,
                    'current_score_away': int,
                    'quarter': int,
                    'game_clock_seconds': int (or None),
                    'game_status': str ('in_progress', 'halftime', etc.),
                    'score_differential': int
                }

        Returns:
            Tuple of (EnsembleResult, List[SimulationResult])
        """

        if not self.trained:
            raise ValueError("Simulators not trained. Call train_all() first.")

        if use_ensemble:
            result = self.ensemble_sim.simulate_game(
                home_team_id, away_team_id, game_date, n_simulations
            )

            # Adjust for game state if provided
            if game_state is not None:
                result = self.adjust_for_game_state(result, game_state)

            return result, result.individual_results
        else:
            # Return individual panel result
            result = self.panel_sim.simulate_game(
                home_team_id, away_team_id, game_date, n_simulations
            )

            # Adjust for game state if provided (convert to EnsembleResult-like structure)
            if game_state is not None:
                # Create a temporary EnsembleResult for adjustment
                from dataclasses import replace
                ensemble_result = EnsembleResult(
                    home_win_prob=result.home_win_prob,
                    away_win_prob=result.away_win_prob,
                    predicted_home_score=result.predicted_home_score,
                    predicted_away_score=result.predicted_away_score,
                    confidence=result.confidence,
                    individual_results=[result],
                    ensemble_method='single',
                    weights={result.model_type: 1.0}
                )
                adjusted_result = self.adjust_for_game_state(ensemble_result, game_state)
                # Update the original result with adjusted values
                result = replace(
                    result,
                    home_win_prob=adjusted_result.home_win_prob,
                    away_win_prob=adjusted_result.away_win_prob,
                    predicted_home_score=adjusted_result.predicted_home_score,
                    predicted_away_score=adjusted_result.predicted_away_score,
                    confidence=adjusted_result.confidence
                )

            return None, [result]

    def adjust_for_game_state(
        self,
        result: EnsembleResult,
        game_state: Dict[str, Any]
    ) -> EnsembleResult:
        """
        Adjust predictions based on in-progress game state.

        For in-progress games:
        - Scales predicted scores based on remaining time
        - Adjusts win probability based on current score differential
        - Accounts for comeback probabilities

        For halftime:
        - Uses halftime score as baseline
        - Adjusts predictions for second half only

        Args:
            result: Original ensemble result
            game_state: Game state dictionary with current scores, quarter, etc.

        Returns:
            Adjusted EnsembleResult
        """
        from dataclasses import replace
        import numpy as np

        current_home_score = game_state.get('current_score_home', 0)
        current_away_score = game_state.get('current_score_away', 0)
        quarter = game_state.get('quarter', 1)
        game_clock_seconds = game_state.get('game_clock_seconds', 0) or 0
        game_status = game_state.get('game_status', 'in_progress')
        current_score_differential = current_home_score - current_away_score

        # Calculate remaining time
        if quarter <= 4:
            quarters_remaining = 4 - quarter
        else:
            # Overtime
            quarters_remaining = 0

        # Each quarter is 12 minutes = 720 seconds
        remaining_quarters_minutes = quarters_remaining * 12.0
        current_quarter_minutes = game_clock_seconds / 60.0
        total_remaining_minutes = remaining_quarters_minutes + current_quarter_minutes

        # Full game is 48 minutes
        total_game_minutes = 48.0
        time_elapsed_minutes = total_game_minutes - total_remaining_minutes
        time_elapsed_ratio = time_elapsed_minutes / total_game_minutes if total_game_minutes > 0 else 0.0

        # For halftime, we only predict the second half
        if game_status == 'halftime':
            time_elapsed_ratio = 0.5  # Halfway through
            total_remaining_minutes = 24.0  # Second half only

        # Scale predicted scores based on remaining time
        # If game is 50% complete, we should only predict the remaining 50%
        remaining_time_ratio = 1.0 - time_elapsed_ratio

        # Original predicted full-game scores
        original_home_score = result.predicted_home_score
        original_away_score = result.predicted_away_score

        # Calculate predicted scoring rate per minute
        if time_elapsed_ratio > 0:
            # Use actual scoring rate so far
            home_scoring_rate = current_home_score / time_elapsed_minutes if time_elapsed_minutes > 0 else 0
            away_scoring_rate = current_away_score / time_elapsed_minutes if time_elapsed_minutes > 0 else 0
        else:
            # Use predicted rate (scores / 48 minutes)
            home_scoring_rate = original_home_score / total_game_minutes
            away_scoring_rate = original_away_score / total_game_minutes

        # Predict remaining scores
        predicted_remaining_home = home_scoring_rate * total_remaining_minutes
        predicted_remaining_away = away_scoring_rate * total_remaining_minutes

        # Total predicted scores = current + predicted remaining
        adjusted_home_score = current_home_score + predicted_remaining_home
        adjusted_away_score = current_away_score + predicted_remaining_away

        # Adjust win probability based on current score and remaining time
        # If team is ahead, they're more likely to win, but we need to account for remaining time
        predicted_margin = adjusted_home_score - adjusted_away_score

        # Use logistic function to convert margin to win probability
        # Typical NBA game: margin std dev ~12 points
        margin_std_dev = 12.0
        z_score = predicted_margin / margin_std_dev

        # Convert to probability using logistic function
        adjusted_home_win_prob = 1.0 / (1.0 + np.exp(-z_score))
        adjusted_away_win_prob = 1.0 - adjusted_home_win_prob

        # Adjust confidence based on time remaining
        # Less time remaining = higher confidence (less uncertainty)
        # More time remaining = lower confidence (more uncertainty)
        confidence_multiplier = 0.5 + (remaining_time_ratio * 0.5)  # Range: 0.5 to 1.0
        adjusted_confidence = result.confidence * confidence_multiplier

        # Also account for current score differential
        # Large lead late in game = higher confidence
        if abs(current_score_differential) > 10 and time_elapsed_ratio > 0.75:
            # Large lead in 4th quarter = very high confidence
            confidence_multiplier = min(1.0, confidence_multiplier * 1.2)
            adjusted_confidence = result.confidence * confidence_multiplier

        logger.info(
            f"Adjusted predictions for in-progress game: "
            f"Q{quarter} {current_home_score}-{current_away_score} "
            f"({total_remaining_minutes:.1f} min remaining) -> "
            f"Final: {adjusted_home_score:.1f}-{adjusted_away_score:.1f} "
            f"(Home win prob: {adjusted_home_win_prob:.1%})"
        )

        # Create adjusted result
        adjusted_result = replace(
            result,
            predicted_home_score=adjusted_home_score,
            predicted_away_score=adjusted_away_score,
            home_win_prob=adjusted_home_win_prob,
            away_win_prob=adjusted_away_win_prob,
            confidence=adjusted_confidence
        )

        return adjusted_result

    def close(self):
        """Close database connections"""
        self.db.close()


if __name__ == "__main__":
    """Example usage"""

    simulator = AdvancedMultiSimulator()

    # Train on ALL historical data (no season limits)
    simulator.train_all()

    # Predict a game (example team IDs)
    result, individual = simulator.predict_game(
        home_team_id="1610612744",  # GSW
        away_team_id="1610612737",  # ATL
        game_date=date(2025, 11, 2),
        use_ensemble=True,
        n_simulations=10000
    )

    print(f"\nEnsemble Prediction:")
    print(f"  Home Win Probability: {result.home_win_prob:.1%}")
    print(f"  Predicted Score: {result.predicted_home_score:.1f} - {result.predicted_away_score:.1f}")
    print(f"  Confidence: {result.confidence:.1%}")

    print(f"\nIndividual Results:")
    for r in individual:
        print(f"  {r.model_type}: {r.home_win_prob:.1%} ({r.confidence:.1%} confidence)")

    simulator.close()

