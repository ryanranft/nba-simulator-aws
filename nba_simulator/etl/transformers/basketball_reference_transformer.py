"""
Basketball Reference Transformer - Transform BBRef Data to Common Schema

Transforms data from Basketball Reference's comprehensive collection:
- 13-tier data collection system
- Player statistics
- Team data
- Game logs
- Advanced metrics
- Historical data back to 1946

Based on proven patterns from:
- scripts/etl/build_master_game_list_robust.py
- scripts/etl/scrape_basketball_reference_comprehensive.py
- scripts/etl/basketball_reference_async_scraper.py

BBRef Data Characteristics:
- HTML scraping (BeautifulSoup)
- Structured tables
- Extensive historical coverage
- Multiple data granularities
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re

from .base_transformer import BaseTransformer


class BasketballReferenceTransformer(BaseTransformer):
    """
    Transform Basketball Reference data to common schema.
    
    Handles multiple BBRef data types:
    - Player statistics (per game, per 36, advanced)
    - Team statistics  
    - Game logs
    - Box scores
    - Play-by-play
    - Historical data
    
    13-Tier System:
    Tier 1: Season schedules
    Tier 2: Box scores
    Tier 3: Play-by-play
    Tier 4: Player game logs
    Tier 5: Team stats
    Tier 6: Player season stats
    Tier 7: Advanced metrics
    Tier 8: Shooting stats
    Tier 9: Lineup data
    Tier 10: Plus/minus
    Tier 11: Draft data
    Tier 12: Transactions
    Tier 13: Historical archives
    """
    
    def __init__(self, tier: Optional[int] = None, **kwargs):
        """
        Initialize Basketball Reference transformer.
        
        Args:
            tier: BBRef tier number (1-13), None for auto-detect
            **kwargs: BaseTransformer arguments
        """
        super().__init__(source_name='basketball_reference', **kwargs)
        self.tier = tier
        
        # Tier-specific transformers
        self._tier_transformers = {
            1: self._transform_tier1_schedule,
            2: self._transform_tier2_boxscore,
            3: self._transform_tier3_playbyplay,
            4: self._transform_tier4_gamelogs,
            5: self._transform_tier5_teamstats,
            6: self._transform_tier6_playerstats,
            7: self._transform_tier7_advanced,
        }
    
    def validate_input(self, data: Any) -> Tuple[bool, str]:
        """Validate Basketball Reference data format"""
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"
        
        # Should have either 'tier' or 'data_type' to identify format
        if 'tier' not in data and 'data_type' not in data and 'table' not in data:
            return False, "Missing tier/data_type identifier"
        
        return True, ""
    
    def _transform_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Route to tier-specific transformer"""
        # Determine tier
        tier = data.get('tier', self.tier)
        
        if tier is None:
            # Auto-detect tier from data structure
            tier = self._detect_tier(data)
        
        # Get tier transformer
        transformer = self._tier_transformers.get(tier, self._transform_generic)
        
        try:
            return transformer(data)
        except Exception as e:
            self.logger.error(f"Tier {tier} transformation failed: {e}")
            return []
    
    def _detect_tier(self, data: Dict[str, Any]) -> int:
        """Auto-detect tier from data structure"""
        # Check for table type in data
        table_type = data.get('table_type', '').lower()
        
        if 'schedule' in table_type:
            return 1
        elif 'box' in table_type or 'boxscore' in table_type:
            return 2
        elif 'play' in table_type or 'pbp' in table_type:
            return 3
        elif 'game_log' in table_type:
            return 4
        elif 'team_stats' in table_type:
            return 5
        elif 'player' in table_type:
            return 6
        elif 'advanced' in table_type:
            return 7
        
        # Default to generic
        return 0
    
    def _transform_tier1_schedule(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform Tier 1: Season schedules
        
        Target: games table
        """
        results = []
        games = data.get('games', [])
        
        for game_data in games:
            try:
                game = {
                    'table': 'games',
                    'game_id': game_data.get('game_id'),
                    'game_date': game_data.get('date'),
                    'season': game_data.get('season'),
                    'home_team': game_data.get('home_team'),
                    'away_team': game_data.get('away_team'),
                    'home_score': game_data.get('home_score'),
                    'away_score': game_data.get('away_score'),
                    'overtime': game_data.get('overtime', False),
                    'arena': game_data.get('arena'),
                    'attendance': game_data.get('attendance'),
                    'data_source': 'basketball_reference',
                    'bbref_tier': 1
                }
                results.append(game)
            except Exception as e:
                self.logger.warning(f"Failed to transform game: {e}")
                self.metrics.records_failed += 1
        
        return results
    
    def _transform_tier2_boxscore(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform Tier 2: Box scores
        
        Target: box_score_teams, box_score_players tables
        """
        results = []
        
        # Game metadata
        game_id = data.get('game_id')
        
        # Team box scores
        for team_data in data.get('teams', []):
            try:
                team_box = {
                    'table': 'box_score_teams',
                    'game_id': game_id,
                    'team_id': team_data.get('team_id'),
                    'points': self._parse_stat(team_data, 'points'),
                    'field_goals_made': self._parse_stat(team_data, 'fg'),
                    'field_goals_attempted': self._parse_stat(team_data, 'fga'),
                    'field_goal_pct': self._parse_stat(team_data, 'fg_pct'),
                    'three_pointers_made': self._parse_stat(team_data, '3p'),
                    'three_pointers_attempted': self._parse_stat(team_data, '3pa'),
                    'three_point_pct': self._parse_stat(team_data, '3p_pct'),
                    'free_throws_made': self._parse_stat(team_data, 'ft'),
                    'free_throws_attempted': self._parse_stat(team_data, 'fta'),
                    'free_throw_pct': self._parse_stat(team_data, 'ft_pct'),
                    'offensive_rebounds': self._parse_stat(team_data, 'orb'),
                    'defensive_rebounds': self._parse_stat(team_data, 'drb'),
                    'total_rebounds': self._parse_stat(team_data, 'trb'),
                    'assists': self._parse_stat(team_data, 'ast'),
                    'steals': self._parse_stat(team_data, 'stl'),
                    'blocks': self._parse_stat(team_data, 'blk'),
                    'turnovers': self._parse_stat(team_data, 'tov'),
                    'personal_fouls': self._parse_stat(team_data, 'pf'),
                    'data_source': 'basketball_reference',
                    'bbref_tier': 2
                }
                results.append(team_box)
            except Exception as e:
                self.logger.warning(f"Failed to transform team boxscore: {e}")
                self.metrics.records_failed += 1
        
        # Player box scores
        for player_data in data.get('players', []):
            try:
                player_box = {
                    'table': 'box_score_players',
                    'game_id': game_id,
                    'player_id': player_data.get('player_id'),
                    'team_id': player_data.get('team_id'),
                    'starter': player_data.get('starter', False),
                    'minutes': player_data.get('mp'),
                    'points': self._parse_stat(player_data, 'pts'),
                    'field_goals_made': self._parse_stat(player_data, 'fg'),
                    'field_goals_attempted': self._parse_stat(player_data, 'fga'),
                    'three_pointers_made': self._parse_stat(player_data, '3p'),
                    'three_pointers_attempted': self._parse_stat(player_data, '3pa'),
                    'free_throws_made': self._parse_stat(player_data, 'ft'),
                    'free_throws_attempted': self._parse_stat(player_data, 'fta'),
                    'offensive_rebounds': self._parse_stat(player_data, 'orb'),
                    'defensive_rebounds': self._parse_stat(player_data, 'drb'),
                    'total_rebounds': self._parse_stat(player_data, 'trb'),
                    'assists': self._parse_stat(player_data, 'ast'),
                    'steals': self._parse_stat(player_data, 'stl'),
                    'blocks': self._parse_stat(player_data, 'blk'),
                    'turnovers': self._parse_stat(player_data, 'tov'),
                    'personal_fouls': self._parse_stat(player_data, 'pf'),
                    'plus_minus': self._parse_stat(player_data, 'plus_minus'),
                    'data_source': 'basketball_reference',
                    'bbref_tier': 2
                }
                results.append(player_box)
            except Exception as e:
                self.logger.warning(f"Failed to transform player boxscore: {e}")
                self.metrics.records_failed += 1
        
        return results
    
    def _transform_tier3_playbyplay(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform Tier 3: Play-by-play
        
        Target: temporal_events table
        """
        results = []
        
        game_id = data.get('game_id')
        game_date = data.get('game_date', datetime.now())
        
        for play in data.get('plays', []):
            try:
                event = {
                    'table': 'temporal_events',
                    'game_id': game_id,
                    'player_id': play.get('player_id'),
                    'team_id': play.get('team_id'),
                    'wall_clock_utc': game_date,
                    'game_clock_seconds': self._parse_clock(play.get('time')),
                    'quarter': play.get('quarter'),
                    'precision_level': 'play',
                    'event_type': play.get('play_type'),
                    'event_data': {
                        'description': play.get('description'),
                        'score_home': play.get('score_home'),
                        'score_away': play.get('score_away')
                    },
                    'data_source': 'basketball_reference',
                    'bbref_tier': 3
                }
                results.append(event)
            except Exception as e:
                self.logger.warning(f"Failed to transform play: {e}")
                self.metrics.records_failed += 1
        
        return results
    
    def _transform_tier4_gamelogs(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform Tier 4: Player game logs
        
        Target: player_game_stats table
        """
        results = []
        
        for game in data.get('games', []):
            try:
                game_stats = {
                    'table': 'player_game_stats',
                    'player_id': data.get('player_id'),
                    'game_id': game.get('game_id'),
                    'game_date': game.get('date'),
                    'team_id': game.get('team_id'),
                    'opponent_id': game.get('opponent_id'),
                    'home_game': game.get('home_game', True),
                    'minutes': game.get('mp'),
                    'points': self._parse_stat(game, 'pts'),
                    'field_goals_made': self._parse_stat(game, 'fg'),
                    'field_goals_attempted': self._parse_stat(game, 'fga'),
                    'three_pointers_made': self._parse_stat(game, '3p'),
                    'three_pointers_attempted': self._parse_stat(game, '3pa'),
                    'free_throws_made': self._parse_stat(game, 'ft'),
                    'free_throws_attempted': self._parse_stat(game, 'fta'),
                    'rebounds': self._parse_stat(game, 'trb'),
                    'assists': self._parse_stat(game, 'ast'),
                    'steals': self._parse_stat(game, 'stl'),
                    'blocks': self._parse_stat(game, 'blk'),
                    'turnovers': self._parse_stat(game, 'tov'),
                    'fouls': self._parse_stat(game, 'pf'),
                    'plus_minus': self._parse_stat(game, 'plus_minus'),
                    'game_score': self._parse_stat(game, 'game_score'),
                    'data_source': 'basketball_reference',
                    'bbref_tier': 4
                }
                results.append(game_stats)
            except Exception as e:
                self.logger.warning(f"Failed to transform game log: {e}")
                self.metrics.records_failed += 1
        
        return results
    
    def _transform_tier5_teamstats(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform Tier 5: Team statistics
        
        Target: team_seasons table
        """
        results = []
        
        for team in data.get('teams', []):
            try:
                team_stats = {
                    'table': 'team_seasons',
                    'team_id': team.get('team_id'),
                    'season': data.get('season'),
                    'wins': team.get('wins'),
                    'losses': team.get('losses'),
                    'win_pct': team.get('win_pct'),
                    'points_per_game': self._parse_stat(team, 'pts_per_g'),
                    'opponent_points_per_game': self._parse_stat(team, 'opp_pts_per_g'),
                    'pace': self._parse_stat(team, 'pace'),
                    'offensive_rating': self._parse_stat(team, 'off_rtg'),
                    'defensive_rating': self._parse_stat(team, 'def_rtg'),
                    'net_rating': self._parse_stat(team, 'net_rtg'),
                    'data_source': 'basketball_reference',
                    'bbref_tier': 5
                }
                results.append(team_stats)
            except Exception as e:
                self.logger.warning(f"Failed to transform team stats: {e}")
                self.metrics.records_failed += 1
        
        return results
    
    def _transform_tier6_playerstats(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform Tier 6: Player season statistics
        
        Target: players table (season aggregates)
        """
        results = []
        
        for player in data.get('players', []):
            try:
                player_stats = {
                    'table': 'players',
                    'player_id': player.get('player_id'),
                    'player_name': player.get('player_name'),
                    'season': data.get('season'),
                    'team_id': player.get('team_id'),
                    'position': player.get('pos'),
                    'age': player.get('age'),
                    'games_played': player.get('g'),
                    'games_started': player.get('gs'),
                    'minutes_per_game': self._parse_stat(player, 'mp_per_g'),
                    'points_per_game': self._parse_stat(player, 'pts_per_g'),
                    'rebounds_per_game': self._parse_stat(player, 'trb_per_g'),
                    'assists_per_game': self._parse_stat(player, 'ast_per_g'),
                    'field_goal_pct': self._parse_stat(player, 'fg_pct'),
                    'three_point_pct': self._parse_stat(player, '3p_pct'),
                    'free_throw_pct': self._parse_stat(player, 'ft_pct'),
                    'data_source': 'basketball_reference',
                    'bbref_tier': 6
                }
                results.append(player_stats)
            except Exception as e:
                self.logger.warning(f"Failed to transform player stats: {e}")
                self.metrics.records_failed += 1
        
        return results
    
    def _transform_tier7_advanced(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform Tier 7: Advanced metrics
        
        Target: player_game_stats (with advanced metrics)
        """
        results = []
        
        for player in data.get('players', []):
            try:
                advanced_stats = {
                    'table': 'player_game_stats',
                    'player_id': player.get('player_id'),
                    'game_id': player.get('game_id'),
                    'true_shooting_pct': self._parse_stat(player, 'ts_pct'),
                    'effective_fg_pct': self._parse_stat(player, 'efg_pct'),
                    'three_point_attempt_rate': self._parse_stat(player, '3par'),
                    'free_throw_rate': self._parse_stat(player, 'ftr'),
                    'offensive_rebound_pct': self._parse_stat(player, 'orb_pct'),
                    'defensive_rebound_pct': self._parse_stat(player, 'drb_pct'),
                    'total_rebound_pct': self._parse_stat(player, 'trb_pct'),
                    'assist_pct': self._parse_stat(player, 'ast_pct'),
                    'steal_pct': self._parse_stat(player, 'stl_pct'),
                    'block_pct': self._parse_stat(player, 'blk_pct'),
                    'turnover_pct': self._parse_stat(player, 'tov_pct'),
                    'usage_pct': self._parse_stat(player, 'usg_pct'),
                    'offensive_rating': self._parse_stat(player, 'off_rtg'),
                    'defensive_rating': self._parse_stat(player, 'def_rtg'),
                    'box_plus_minus': self._parse_stat(player, 'bpm'),
                    'data_source': 'basketball_reference',
                    'bbref_tier': 7
                }
                results.append(advanced_stats)
            except Exception as e:
                self.logger.warning(f"Failed to transform advanced stats: {e}")
                self.metrics.records_failed += 1
        
        return results
    
    def _transform_generic(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generic transformation for unknown tiers"""
        self.logger.warning("Using generic transformer - data structure unknown")
        
        # Just pass through with metadata
        return [{
            'table': 'raw_data.basketball_reference',
            'raw_data': data,
            'data_source': 'basketball_reference',
            'bbref_tier': 0
        }]
    
    def _parse_stat(self, data: Dict[str, Any], stat_name: str, default: Any = 0) -> Any:
        """Parse a statistic value, handling various formats"""
        value = data.get(stat_name, default)
        
        # Handle empty strings
        if value == '' or value is None:
            return default
        
        # Try to convert to appropriate type
        try:
            if '.' in str(value):
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _parse_clock(self, time_str: str) -> Optional[int]:
        """Parse game clock to seconds"""
        if not time_str:
            return None
        
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            return int(float(time_str))
        except:
            return None
