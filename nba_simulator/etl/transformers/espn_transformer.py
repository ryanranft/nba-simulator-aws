"""
ESPN Transformer - Transform ESPN Data to Common Schema

Transforms data from ESPN sources:
- Play-by-play data → temporal_events table
- Box scores → box_score_* tables  
- Schedule data → games table

Based on proven patterns from:
- scripts/etl/extract_pbp_local.py
- scripts/etl/extract_boxscores_local.py
- scripts/etl/load_espn_pbp_to_rds.py

ESPN Data Format:
- JSON files with nested structure
- play-by-play has 'plays' array
- Each play has: clock, period, team, players, coordinates
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json
import re

from .base_transformer import BaseTransformer


class ESPNTransformer(BaseTransformer):
    """
    Main ESPN transformer - routes to specialized transformers.
    """
    
    def __init__(self, **kwargs):
        super().__init__(source_name='espn', **kwargs)
        
        # Specialized transformers
        self.pbp_transformer = ESPNPlayByPlayTransformer(**kwargs)
        self.boxscore_transformer = ESPNBoxScoreTransformer(**kwargs)
    
    def validate_input(self, data: Any) -> Tuple[bool, str]:
        """Validate ESPN data format"""
        if not isinstance(data, dict):
            return False, "ESPN data must be a dictionary"
        
        # Check for expected top-level keys
        if 'header' not in data and 'boxscore' not in data and 'plays' not in data:
            return False, "ESPN data missing expected keys (header/boxscore/plays)"
        
        return True, ""
    
    def _transform_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Route to specialized transformer based on data type"""
        results = []
        
        # Check if this is play-by-play data
        if 'plays' in data:
            results.extend(self.pbp_transformer._transform_data(data))
        
        # Check if this is box score data
        if 'boxscore' in data:
            results.extend(self.boxscore_transformer._transform_data(data))
        
        return results


class ESPNPlayByPlayTransformer(BaseTransformer):
    """
    Transform ESPN play-by-play data to temporal_events format.
    
    ESPN PBP Structure:
    {
        "header": {...game metadata...},
        "plays": [
            {
                "clock": {"displayValue": "12:00"},
                "period": {"number": 1},
                "team": {"id": "1"},
                "text": "Description",
                "scoreValue": 2,
                "coordinate": {"x": 25, "y": 10}
            }
        ]
    }
    
    Target: temporal_events table
    - event_id (bigint, auto)
    - game_id (varchar 20)
    - player_id (varchar 20, nullable)
    - team_id (varchar 20, nullable)
    - wall_clock_utc (timestamp)
    - wall_clock_local (timestamp, nullable)
    - game_clock_seconds (int, nullable)
    - quarter (int, nullable)
    - precision_level (varchar 10)
    - event_type (varchar 50, nullable)
    - event_data (jsonb, nullable)
    - data_source (varchar 20)
    - created_at (timestamp, default CURRENT_TIMESTAMP)
    - updated_at (timestamp, default CURRENT_TIMESTAMP)
    """
    
    def __init__(self, **kwargs):
        super().__init__(source_name='espn_pbp', **kwargs)
    
    def validate_input(self, data: Any) -> Tuple[bool, str]:
        """Validate ESPN play-by-play format"""
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"
        
        if 'plays' not in data:
            return False, "Missing 'plays' key"
        
        if not isinstance(data['plays'], list):
            return False, "'plays' must be a list"
        
        return True, ""
    
    def _transform_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform ESPN plays to temporal_events format"""
        temporal_events = []
        
        # Extract game metadata
        game_id = self._extract_game_id(data)
        game_date = self._extract_game_date(data)
        
        # Process each play
        for play in data.get('plays', []):
            event = self._transform_play(play, game_id, game_date)
            if event:
                temporal_events.append(event)
        
        return temporal_events
    
    def _extract_game_id(self, data: Dict[str, Any]) -> str:
        """Extract game ID from ESPN data"""
        # Try header first
        if 'header' in data:
            if 'id' in data['header']:
                return str(data['header']['id'])
            if 'gameId' in data['header']:
                return str(data['header']['gameId'])
        
        # Try competitions
        if 'header' in data and 'competitions' in data['header']:
            comps = data['header']['competitions']
            if comps and len(comps) > 0:
                return str(comps[0].get('id', 'unknown'))
        
        return 'unknown'
    
    def _extract_game_date(self, data: Dict[str, Any]) -> datetime:
        """Extract game date from ESPN data"""
        # Try header date
        if 'header' in data and 'competitions' in data['header']:
            comps = data['header']['competitions']
            if comps and len(comps) > 0:
                date_str = comps[0].get('date')
                if date_str:
                    try:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass
        
        # Default to now
        return datetime.now(timezone.utc)
    
    def _transform_play(
        self,
        play: Dict[str, Any],
        game_id: str,
        game_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Transform a single play to temporal_event format"""
        try:
            # Extract basic info
            quarter = play.get('period', {}).get('number')
            clock_display = play.get('clock', {}).get('displayValue', '0:00')
            game_clock_seconds = self._parse_clock(clock_display)
            
            # Extract team and player
            team_id = play.get('team', {}).get('id')
            
            # Try to extract player from text (ESPN doesn't always provide player_id)
            player_id = None
            if 'participants' in play and play['participants']:
                player_id = play['participants'][0].get('athlete', {}).get('id')
            
            # Determine event type from play text
            event_type = self._classify_event_type(play.get('text', ''))
            
            # Build event_data (store all original data)
            event_data = {
                'text': play.get('text'),
                'scoreValue': play.get('scoreValue'),
                'shootingPlay': play.get('shootingPlay'),
                'scoringPlay': play.get('scoringPlay'),
                'coordinate': play.get('coordinate'),
                'wallclock': play.get('wallclock'),
                'homeScore': play.get('homeScore'),
                'awayScore': play.get('awayScore')
            }
            
            # Create temporal event
            return {
                'game_id': game_id,
                'player_id': str(player_id) if player_id else None,
                'team_id': str(team_id) if team_id else None,
                'wall_clock_utc': game_date,  # Will be adjusted if wallclock available
                'wall_clock_local': None,
                'game_clock_seconds': game_clock_seconds,
                'quarter': quarter,
                'precision_level': 'play',  # ESPN provides play-level precision
                'event_type': event_type,
                'event_data': event_data,
                'data_source': 'espn'
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to transform play: {e}")
            return None
    
    def _parse_clock(self, clock_str: str) -> Optional[int]:
        """
        Parse game clock to seconds remaining in quarter.
        
        Args:
            clock_str: Clock display like "11:34", "0:45", "12:00"
            
        Returns:
            Seconds remaining (e.g., "11:34" → 694)
        """
        try:
            if ':' in clock_str:
                parts = clock_str.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            return int(clock_str)
        except:
            return None
    
    def _classify_event_type(self, text: str) -> str:
        """
        Classify event type from play description.
        
        Args:
            text: Play description text
            
        Returns:
            Event type (shot, rebound, turnover, etc.)
        """
        text_lower = text.lower()
        
        # Shot types
        if 'makes' in text_lower or 'made' in text_lower:
            if 'three point' in text_lower or '3-pt' in text_lower:
                return 'three_pointer_made'
            elif 'free throw' in text_lower:
                return 'free_throw_made'
            else:
                return 'two_pointer_made'
        
        if 'misses' in text_lower or 'missed' in text_lower:
            if 'three point' in text_lower or '3-pt' in text_lower:
                return 'three_pointer_missed'
            elif 'free throw' in text_lower:
                return 'free_throw_missed'
            else:
                return 'two_pointer_missed'
        
        # Rebounds
        if 'rebound' in text_lower:
            if 'defensive' in text_lower:
                return 'defensive_rebound'
            elif 'offensive' in text_lower:
                return 'offensive_rebound'
            return 'rebound'
        
        # Turnovers
        if 'turnover' in text_lower or 'bad pass' in text_lower:
            return 'turnover'
        
        # Fouls
        if 'foul' in text_lower:
            if 'personal' in text_lower:
                return 'personal_foul'
            elif 'shooting' in text_lower:
                return 'shooting_foul'
            return 'foul'
        
        # Assists
        if 'assist' in text_lower:
            return 'assist'
        
        # Steals
        if 'steal' in text_lower:
            return 'steal'
        
        # Blocks
        if 'block' in text_lower:
            return 'block'
        
        # Timeouts
        if 'timeout' in text_lower:
            return 'timeout'
        
        # Substitutions
        if 'enters the game' in text_lower or 'substitution' in text_lower:
            return 'substitution'
        
        # Default
        return 'other'


class ESPNBoxScoreTransformer(BaseTransformer):
    """
    Transform ESPN box score data to box_score_* tables.
    
    Target tables:
    - box_score_teams: Team-level box scores
    - box_score_players: Player-level box scores
    """
    
    def __init__(self, **kwargs):
        super().__init__(source_name='espn_boxscore', **kwargs)
    
    def validate_input(self, data: Any) -> Tuple[bool, str]:
        """Validate ESPN box score format"""
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"
        
        if 'boxscore' not in data:
            return False, "Missing 'boxscore' key"
        
        return True, ""
    
    def _transform_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform ESPN box scores"""
        results = []
        
        game_id = self._extract_game_id(data)
        boxscore = data.get('boxscore', {})
        
        # Transform team box scores
        if 'teams' in boxscore:
            for team_data in boxscore['teams']:
                team_box = self._transform_team_boxscore(team_data, game_id)
                if team_box:
                    results.append(team_box)
                
                # Transform player box scores
                if 'statistics' in team_data:
                    for player_stats in team_data['statistics']:
                        if 'athletes' in player_stats:
                            for player in player_stats['athletes']:
                                player_box = self._transform_player_boxscore(
                                    player, game_id, team_data['team']['id']
                                )
                                if player_box:
                                    results.append(player_box)
        
        return results
    
    def _extract_game_id(self, data: Dict[str, Any]) -> str:
        """Extract game ID"""
        if 'header' in data:
            return str(data['header'].get('id', 'unknown'))
        return 'unknown'
    
    def _transform_team_boxscore(
        self,
        team_data: Dict[str, Any],
        game_id: str
    ) -> Optional[Dict[str, Any]]:
        """Transform team box score"""
        try:
            team_id = team_data.get('team', {}).get('id')
            stats = team_data.get('statistics', [{}])[0].get('totals', {})
            
            return {
                'table': 'box_score_teams',
                'game_id': game_id,
                'team_id': str(team_id),
                'points': int(stats.get('points', 0)),
                'field_goals_made': int(stats.get('fieldGoalsMade', 0)),
                'field_goals_attempted': int(stats.get('fieldGoalsAttempted', 0)),
                'three_pointers_made': int(stats.get('threePointFieldGoalsMade', 0)),
                'three_pointers_attempted': int(stats.get('threePointFieldGoalsAttempted', 0)),
                'free_throws_made': int(stats.get('freeThrowsMade', 0)),
                'free_throws_attempted': int(stats.get('freeThrowsAttempted', 0)),
                'rebounds': int(stats.get('rebounds', 0)),
                'assists': int(stats.get('assists', 0)),
                'steals': int(stats.get('steals', 0)),
                'blocks': int(stats.get('blocks', 0)),
                'turnovers': int(stats.get('turnovers', 0)),
                'fouls': int(stats.get('fouls', 0)),
                'data_source': 'espn'
            }
        except Exception as e:
            self.logger.warning(f"Failed to transform team boxscore: {e}")
            return None
    
    def _transform_player_boxscore(
        self,
        player_data: Dict[str, Any],
        game_id: str,
        team_id: str
    ) -> Optional[Dict[str, Any]]:
        """Transform player box score"""
        try:
            player_id = player_data.get('athlete', {}).get('id')
            stats = {stat['name']: stat['value'] for stat in player_data.get('stats', [])}
            
            return {
                'table': 'box_score_players',
                'game_id': game_id,
                'player_id': str(player_id),
                'team_id': str(team_id),
                'minutes_played': stats.get('minutes', '0'),
                'points': int(stats.get('points', 0)),
                'field_goals_made': int(stats.get('fieldGoalsMade', 0)),
                'field_goals_attempted': int(stats.get('fieldGoalsAttempted', 0)),
                'three_pointers_made': int(stats.get('threePointFieldGoalsMade', 0)),
                'three_pointers_attempted': int(stats.get('threePointFieldGoalsAttempted', 0)),
                'free_throws_made': int(stats.get('freeThrowsMade', 0)),
                'free_throws_attempted': int(stats.get('freeThrowsAttempted', 0)),
                'rebounds': int(stats.get('rebounds', 0)),
                'assists': int(stats.get('assists', 0)),
                'steals': int(stats.get('steals', 0)),
                'blocks': int(stats.get('blocks', 0)),
                'turnovers': int(stats.get('turnovers', 0)),
                'fouls': int(stats.get('fouls', 0)),
                'plus_minus': int(stats.get('plusMinus', 0)),
                'data_source': 'espn'
            }
        except Exception as e:
            self.logger.warning(f"Failed to transform player boxscore: {e}")
            return None
