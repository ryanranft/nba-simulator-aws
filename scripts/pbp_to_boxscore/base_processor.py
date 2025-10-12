"""
Base Play-by-Play to Box Score Processor

Abstract base class defining the interface for all PBP processors.
All specific processors (ESPN, hoopR, NBA API, Kaggle) inherit from this.

Created: October 11, 2025
Phase: 9.0 (System Architecture)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
from copy import deepcopy

from .box_score_snapshot import (
    BoxScoreSnapshot,
    PlayerStats,
    TeamStats,
    VerificationResult,
    calculate_quality_grade
)

# Configure logging
logger = logging.getLogger(__name__)


class BasePlayByPlayProcessor(ABC):
    """
    Abstract base class for play-by-play processors.
    
    All processors must implement:
    - load_game_data: Load raw PBP data
    - parse_event: Parse a single PBP event
    - get_initial_state: Get starting game state
    - get_actual_box_score: Load actual box score for verification
    
    Base class provides:
    - process_game: Main processing logic (shared across all sources)
    - update_box_score: Update running box score with event
    - create_snapshot: Create immutable snapshot
    - verify_final_box_score: Compare generated vs actual
    - track_quarters: Track quarter boundaries
    """
    
    def __init__(self, data_source: str):
        """
        Initialize processor.
        
        Args:
            data_source: Source identifier ('espn', 'hoopr', 'nba_api', 'kaggle')
        """
        self.data_source = data_source
        self.logger = logging.getLogger(f"{__name__}.{data_source}")
    
    # ========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ========================================================================
    
    @abstractmethod
    def load_game_data(self, game_id: str) -> Dict[str, Any]:
        """
        Load raw play-by-play data for a game.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Dict containing game data and events
            
        Raises:
            FileNotFoundError: If game data not found
            ValueError: If game data is malformed
        """
        pass
    
    @abstractmethod
    def parse_event(self, event: Any, event_num: int) -> Dict[str, Any]:
        """
        Parse a single play-by-play event into standardized format.
        
        Args:
            event: Raw event data (format depends on source)
            event_num: Sequential event number
            
        Returns:
            Dict with standardized event fields:
            {
                'event_num': int,
                'event_type': str,  # 'shot_made', 'shot_missed', 'rebound', etc.
                'quarter': int,
                'time_remaining': str,
                'game_clock_seconds': int,
                'player_id': str,
                'team_id': str,
                'points': int,  # For scoring plays
                'stat_updates': Dict[str, int],  # Stats to update
                'substitution': Optional[Dict],  # For substitutions
                ...
            }
        """
        pass
    
    @abstractmethod
    def get_initial_state(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get initial game state (before any events).
        
        Args:
            game_data: Full game data
            
        Returns:
            Dict with:
            {
                'home_team_id': str,
                'away_team_id': str,
                'home_team_name': str,
                'away_team_name': str,
                'starting_lineups': Dict[str, List[str]],  # team_id -> [player_ids]
                'player_info': Dict[str, Dict],  # player_id -> {name, team_id}
                ...
            }
        """
        pass
    
    @abstractmethod
    def get_actual_box_score(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Load actual final box score for verification.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Dict with actual box score, or None if not available
            {
                'home_score': int,
                'away_score': int,
                'players': Dict[str, Dict[str, int]],  # player_id -> stats
                ...
            }
        """
        pass
    
    # ========================================================================
    # SHARED PROCESSING LOGIC
    # ========================================================================
    
    def process_game(self, game_id: str, verify: bool = True) -> Tuple[List[BoxScoreSnapshot], Optional[VerificationResult]]:
        """
        Process entire game and generate box score snapshots.
        
        This is the main entry point for processing a game.
        
        Args:
            game_id: Game identifier
            verify: Whether to verify final box score against actual
            
        Returns:
            Tuple of (snapshots, verification_result)
            - snapshots: List of BoxScoreSnapshot objects (one per event)
            - verification_result: VerificationResult if verify=True, else None
        """
        self.logger.info(f"Processing game {game_id} from {self.data_source}")
        
        try:
            # Load game data
            game_data = self.load_game_data(game_id)
            
            # Get initial state
            initial_state = self.get_initial_state(game_data)
            
            # Initialize running box score
            box_score = self._initialize_box_score(initial_state)
            
            # Process events sequentially
            events = game_data.get('events', [])
            snapshots = []
            
            for event_num, raw_event in enumerate(events):
                # Parse event
                event = self.parse_event(raw_event, event_num)
                
                # Update box score
                box_score = self._update_box_score(box_score, event)
                
                # Create snapshot
                snapshot = self._create_snapshot(game_id, event_num, box_score)
                snapshots.append(snapshot)
            
            self.logger.info(f"✅ Generated {len(snapshots)} snapshots for game {game_id}")
            
            # Verify if requested
            verification = None
            if verify:
                verification = self.verify_final_box_score(game_id, snapshots[-1] if snapshots else None)
            
            return snapshots, verification
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process game {game_id}: {e}", exc_info=True)
            raise
    
    def _initialize_box_score(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize empty box score with starting lineups.
        
        Args:
            initial_state: Initial game state
            
        Returns:
            Box score dictionary
        """
        box_score = {
            'quarter': 1,
            'time_remaining': '12:00',
            'game_clock_seconds': 0,
            'home_team_id': initial_state['home_team_id'],
            'away_team_id': initial_state['away_team_id'],
            'home_score': 0,
            'away_score': 0,
            'players': {},  # player_id -> stats dict
            'teams': {
                initial_state['home_team_id']: self._init_team_stats(initial_state['home_team_id'], initial_state['home_team_name']),
                initial_state['away_team_id']: self._init_team_stats(initial_state['away_team_id'], initial_state['away_team_name'])
            },
            'quarter_stats': {1: {}},  # quarter -> player_id -> stats
            'on_court': {  # team_id -> [player_ids]
                initial_state['home_team_id']: initial_state['starting_lineups'].get(initial_state['home_team_id'], []),
                initial_state['away_team_id']: initial_state['starting_lineups'].get(initial_state['away_team_id'], [])
            },
            'player_info': initial_state['player_info']
        }
        
        # Initialize players from starting lineups
        for team_id, player_ids in box_score['on_court'].items():
            for player_id in player_ids:
                if player_id not in box_score['players']:
                    player_info = box_score['player_info'].get(player_id, {})
                    box_score['players'][player_id] = self._init_player_stats(
                        player_id,
                        player_info.get('name', 'Unknown'),
                        team_id
                    )
                    box_score['players'][player_id]['on_court'] = True
        
        return box_score
    
    def _init_player_stats(self, player_id: str, player_name: str, team_id: str) -> Dict[str, Any]:
        """Initialize empty player stats"""
        return {
            'player_id': player_id,
            'player_name': player_name,
            'team_id': team_id,
            'points': 0,
            'fgm': 0, 'fga': 0,
            'fg3m': 0, 'fg3a': 0,
            'ftm': 0, 'fta': 0,
            'oreb': 0, 'dreb': 0, 'reb': 0,
            'ast': 0, 'stl': 0, 'blk': 0,
            'tov': 0, 'pf': 0,
            'plus_minus': 0,
            'minutes': 0.0,
            'on_court': False
        }
    
    def _init_team_stats(self, team_id: str, team_name: str) -> Dict[str, Any]:
        """Initialize empty team stats"""
        return {
            'team_id': team_id,
            'team_name': team_name,
            'points': 0,
            'fgm': 0, 'fga': 0,
            'fg3m': 0, 'fg3a': 0,
            'ftm': 0, 'fta': 0,
            'oreb': 0, 'dreb': 0, 'reb': 0,
            'ast': 0, 'stl': 0, 'blk': 0,
            'tov': 0, 'pf': 0
        }
    
    def _update_box_score(self, box_score: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update running box score with new event.
        
        Args:
            box_score: Current box score state
            event: Parsed event
            
        Returns:
            Updated box score
        """
        # Update quarter and clock
        if 'quarter' in event:
            box_score['quarter'] = event['quarter']
        if 'time_remaining' in event:
            box_score['time_remaining'] = event['time_remaining']
        if 'game_clock_seconds' in event:
            box_score['game_clock_seconds'] = event['game_clock_seconds']
        
        # Get player and team
        player_id = event.get('player_id')
        team_id = event.get('team_id')
        
        if not player_id or not team_id:
            return box_score  # Event doesn't involve a specific player
        
        # Ensure player exists in box score
        if player_id not in box_score['players']:
            player_info = box_score['player_info'].get(player_id, {})
            box_score['players'][player_id] = self._init_player_stats(
                player_id,
                player_info.get('name', 'Unknown'),
                team_id
            )
        
        player_stats = box_score['players'][player_id]
        team_stats = box_score['teams'][team_id]
        
        # Apply stat updates
        stat_updates = event.get('stat_updates', {})
        for stat, value in stat_updates.items():
            if stat in player_stats:
                player_stats[stat] += value
                if stat in team_stats:
                    team_stats[stat] += value
        
        # Handle substitutions
        if event.get('substitution'):
            sub = event['substitution']
            out_player = sub.get('out_player_id')
            in_player = sub.get('in_player_id')
            
            if out_player and out_player in box_score['players']:
                box_score['players'][out_player]['on_court'] = False
                if out_player in box_score['on_court'][team_id]:
                    box_score['on_court'][team_id].remove(out_player)
            
            if in_player:
                if in_player not in box_score['players']:
                    player_info = box_score['player_info'].get(in_player, {})
                    box_score['players'][in_player] = self._init_player_stats(
                        in_player,
                        player_info.get('name', 'Unknown'),
                        team_id
                    )
                box_score['players'][in_player]['on_court'] = True
                if in_player not in box_score['on_court'][team_id]:
                    box_score['on_court'][team_id].append(in_player)
        
        # Update scores
        if 'points' in stat_updates and stat_updates['points'] > 0:
            if team_id == box_score['home_team_id']:
                box_score['home_score'] += stat_updates['points']
            else:
                box_score['away_score'] += stat_updates['points']
        
        return box_score
    
    def _create_snapshot(self, game_id: str, event_num: int, box_score: Dict[str, Any]) -> BoxScoreSnapshot:
        """
        Create immutable snapshot from current box score state.
        
        Args:
            game_id: Game identifier
            event_num: Event number
            box_score: Current box score state
            
        Returns:
            BoxScoreSnapshot object
        """
        # Convert player stats to PlayerStats objects
        players = {}
        for player_id, stats in box_score['players'].items():
            players[player_id] = PlayerStats(**stats)
        
        # Convert team stats to TeamStats objects
        teams = {}
        for team_id, stats in box_score['teams'].items():
            teams[team_id] = TeamStats(**stats)
        
        # Create snapshot
        snapshot = BoxScoreSnapshot(
            game_id=game_id,
            event_num=event_num,
            data_source=self.data_source,
            quarter=box_score['quarter'],
            time_remaining=box_score['time_remaining'],
            game_clock_seconds=box_score['game_clock_seconds'],
            home_score=box_score['home_score'],
            away_score=box_score['away_score'],
            players=players,
            teams=teams
        )
        
        return snapshot
    
    def verify_final_box_score(self, game_id: str, final_snapshot: Optional[BoxScoreSnapshot]) -> VerificationResult:
        """
        Verify generated final box score against actual.
        
        Args:
            game_id: Game identifier
            final_snapshot: Final snapshot (last event)
            
        Returns:
            VerificationResult
        """
        self.logger.info(f"Verifying game {game_id}")
        
        if not final_snapshot:
            return VerificationResult(
                game_id=game_id,
                data_source=self.data_source,
                final_score_match=False,
                home_score_generated=0,
                away_score_generated=0,
                home_score_actual=0,
                away_score_actual=0,
                total_discrepancies=0,
                discrepancy_details={},
                mae_points=0.0,
                mae_rebounds=0.0,
                mae_assists=0.0,
                quality_grade='F',
                notes="No final snapshot available"
            )
        
        # Load actual box score
        actual = self.get_actual_box_score(game_id)
        if not actual:
            return VerificationResult(
                game_id=game_id,
                data_source=self.data_source,
                final_score_match=False,
                home_score_generated=final_snapshot.home_score,
                away_score_generated=final_snapshot.away_score,
                home_score_actual=0,
                away_score_actual=0,
                total_discrepancies=0,
                discrepancy_details={},
                mae_points=0.0,
                mae_rebounds=0.0,
                mae_assists=0.0,
                quality_grade='F',
                notes="No actual box score available for verification"
            )
        
        # Compare scores
        final_score_match = (
            final_snapshot.home_score == actual.get('home_score', 0) and
            final_snapshot.away_score == actual.get('away_score', 0)
        )
        
        # Compare player stats
        discrepancies = {}
        total_diff = 0
        mae_points_list = []
        mae_reb_list = []
        mae_ast_list = []
        
        for player_id, gen_stats in final_snapshot.players.items():
            act_stats = actual.get('players', {}).get(player_id, {})
            if not act_stats:
                continue
            
            player_disc = {}
            for stat in ['points', 'reb', 'ast', 'stl', 'blk', 'tov']:
                gen_val = getattr(gen_stats, stat, 0)
                act_val = act_stats.get(stat, 0)
                diff = abs(gen_val - act_val)
                
                if diff > 0:
                    player_disc[stat] = {'generated': gen_val, 'actual': act_val, 'diff': diff}
                    total_diff += diff
                    
                    if stat == 'points':
                        mae_points_list.append(diff)
                    elif stat == 'reb':
                        mae_reb_list.append(diff)
                    elif stat == 'ast':
                        mae_ast_list.append(diff)
            
            if player_disc:
                discrepancies[player_id] = player_disc
        
        # Calculate MAEs
        mae_points = sum(mae_points_list) / len(mae_points_list) if mae_points_list else 0.0
        mae_rebounds = sum(mae_reb_list) / len(mae_reb_list) if mae_reb_list else 0.0
        mae_assists = sum(mae_ast_list) / len(mae_ast_list) if mae_ast_list else 0.0
        
        # Calculate quality grade
        quality_grade = calculate_quality_grade(total_diff, final_score_match)
        
        result = VerificationResult(
            game_id=game_id,
            data_source=self.data_source,
            final_score_match=final_score_match,
            home_score_generated=final_snapshot.home_score,
            away_score_generated=final_snapshot.away_score,
            home_score_actual=actual.get('home_score', 0),
            away_score_actual=actual.get('away_score', 0),
            total_discrepancies=total_diff,
            discrepancy_details=discrepancies,
            mae_points=mae_points,
            mae_rebounds=mae_rebounds,
            mae_assists=mae_assists,
            quality_grade=quality_grade
        )
        
        self.logger.info(f"✅ Verification complete: Grade {quality_grade}, {total_diff} discrepancies")
        
        return result

