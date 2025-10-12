"""
ESPN Play-by-Play to Box Score Processor

Processes ESPN play-by-play JSON files from S3 into box score snapshots.
Covers 2023-2025 games with highest data quality.

Created: October 11, 2025
Phase: 9.1 (ESPN Processor)
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from .base_processor import BasePlayByPlayProcessor
from .box_score_snapshot import BoxScoreSnapshot, VerificationResult

logger = logging.getLogger(__name__)


class ESPNPlayByPlayProcessor(BasePlayByPlayProcessor):
    """
    Processor for ESPN play-by-play data.
    
    ESPN data structure (based on actual scraped files):
    - Location: s3://nba-sim-raw-data-lake/pbp/{game_id}.json
    - Path: page.content.gamepackage.pbp.playGrps
    - Play Groups: List of lists (one list per quarter/period)
    - Team Info: page.content.gamepackage.pbp.tms (home/away)
    
    Each play contains:
    - id: Unique play identifier
    - text: Play description
    - period.number: Quarter/period number
    - clock.displayValue: Time remaining (e.g., "7:32")
    - homeScore: Current home score
    - awayScore: Current away score
    - scoringPlay: Boolean (is this a scoring play?)
    - participants: List of players involved
    - type.text: Event type (Made Shot, Missed Shot, Rebound, etc.)
    """
    
    def __init__(self, s3_bucket: str = 'nba-sim-raw-data-lake', local_cache_dir: Optional[str] = None):
        """
        Initialize ESPN processor.
        
        Args:
            s3_bucket: S3 bucket name
            local_cache_dir: Optional local directory for caching files
        """
        super().__init__(data_source='espn')
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3')
        self.local_cache_dir = Path(local_cache_dir) if local_cache_dir else None
        
        if self.local_cache_dir:
            self.local_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # ABSTRACT METHODS IMPLEMENTATION
    # ========================================================================
    
    def load_game_data(self, game_id: str) -> Dict[str, Any]:
        """
        Load ESPN game data from S3 and flatten play groups.
        
        Args:
            game_id: ESPN game ID (e.g., '401584903')
            
        Returns:
            Dict with game data and flattened events list
            
        Raises:
            FileNotFoundError: If game file not found in S3
            ValueError: If game data is malformed
        """
        # Check local cache first
        if self.local_cache_dir:
            local_path = self.local_cache_dir / f"{game_id}.json"
            if local_path.exists():
                self.logger.debug(f"Loading game {game_id} from local cache")
                with open(local_path, 'r') as f:
                    raw_data = json.load(f)
            else:
                raw_data = self._download_from_s3(game_id)
        else:
            raw_data = self._download_from_s3(game_id)
        
        # Flatten play groups into events list
        return self._flatten_play_groups(raw_data)
    
    def _download_from_s3(self, game_id: str) -> Dict[str, Any]:
        """Download game JSON from S3"""
        s3_key = f"pbp/{game_id}.json"
        self.logger.debug(f"Downloading game {game_id} from S3: {s3_key}")
        
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            game_data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Cache locally if configured
            if self.local_cache_dir:
                local_path = self.local_cache_dir / f"{game_id}.json"
                with open(local_path, 'w') as f:
                    json.dump(game_data, f)
            
            return game_data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"Game {game_id} not found in S3: {s3_key}")
            else:
                raise
    
    def _flatten_play_groups(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten ESPN's nested playGrps structure into a simple events list.
        
        ESPN structure: pbp.playGrps = [[period 1 plays], [period 2 plays], ...]
        We need: {'events': [all plays in order], ...}
        """
        gp = raw_data.get('page', {}).get('content', {}).get('gamepackage', {})
        pbp = gp.get('pbp', {})
        play_groups = pbp.get('playGrps', [])
        
        # Flatten nested lists
        events = []
        for period_plays in play_groups:
            if isinstance(period_plays, list):
                events.extend(period_plays)
        
        # Return simplified structure
        return {
            'raw_data': raw_data,
            'events': events
        }
    
    def get_initial_state(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract initial game state from ESPN data.
        
        Args:
            game_data: Processed game data (with 'raw_data' and 'events')
            
        Returns:
            Dict with team info, starting lineups, player info
        """
        try:
            # Navigate to gamepackage from raw_data
            raw_data = game_data.get('raw_data', game_data)
            gp = raw_data.get('page', {}).get('content', {}).get('gamepackage', {})
            pbp = gp.get('pbp', {})
            tms = pbp.get('tms', {})
            
            # Extract team info
            home_team = tms.get('home', {})
            away_team = tms.get('away', {})
            
            initial_state = {
                'home_team_id': home_team.get('id', 'unknown'),
                'away_team_id': away_team.get('id', 'unknown'),
                'home_team_name': home_team.get('displayName', 'Unknown'),
                'away_team_name': away_team.get('displayName', 'Unknown'),
                'home_abbrev': home_team.get('abbrev', ''),
                'away_abbrev': away_team.get('abbrev', ''),
                'starting_lineups': {
                    home_team.get('id', 'unknown'): [],
                    away_team.get('id', 'unknown'): []
                },
                'player_info': {}
            }
            
            # Extract player info from events
            events = game_data.get('events', [])
            for event in events[:50]:  # Look at first 50 events to find starters
                participants = event.get('participants', [])
                for participant in participants:
                    athlete = participant.get('athlete', {})
                    player_id = athlete.get('id')
                    if player_id and player_id not in initial_state['player_info']:
                        initial_state['player_info'][player_id] = {
                            'name': athlete.get('displayName', 'Unknown'),
                            'team_id': participant.get('team', {}).get('id')
                        }
            
            return initial_state
            
        except Exception as e:
            self.logger.error(f"Error extracting initial state: {e}", exc_info=True)
            raise ValueError(f"Malformed ESPN game data: {e}")
    
    def parse_event(self, event: Any, event_num: int) -> Dict[str, Any]:
        """
        Parse ESPN play into standardized event format.
        
        Args:
            event: ESPN play dict
            event_num: Sequential event number
            
        Returns:
            Standardized event dict
        """
        try:
            # Extract basic info
            parsed = {
                'event_num': event_num,
                'play_id': event.get('id'),
                'text': event.get('text', ''),
                'quarter': event.get('period', {}).get('number', 1),
                'time_remaining': event.get('clock', {}).get('displayValue', '12:00'),
                'game_clock_seconds': self._calculate_game_clock_seconds(
                    event.get('period', {}).get('number', 1),
                    event.get('clock', {}).get('value', 720.0)  # ESPN provides seconds remaining in period
                ),
                'home_score': event.get('homeScore', 0),
                'away_score': event.get('awayScore', 0),
                'scoring_play': event.get('scoringPlay', False),
                'event_type': event.get('type', {}).get('text', 'unknown'),
                'stat_updates': {},
                'substitution': None,
                'player_id': None,
                'team_id': None
            }
            
            # Extract player and team from participants
            participants = event.get('participants', [])
            if participants:
                primary_participant = participants[0]
                parsed['player_id'] = primary_participant.get('athlete', {}).get('id')
                parsed['team_id'] = primary_participant.get('team', {}).get('id')
            
            # Parse event type and extract stat updates
            event_type = parsed['event_type'].lower()
            
            if 'made' in event_type:
                # Scoring plays
                if 'three point' in event_type or '3-pt' in event_type:
                    parsed['stat_updates'] = {'points': 3, 'fgm': 1, 'fga': 1, 'fg3m': 1, 'fg3a': 1}
                elif 'free throw' in event_type:
                    parsed['stat_updates'] = {'points': 1, 'ftm': 1, 'fta': 1}
                else:
                    parsed['stat_updates'] = {'points': 2, 'fgm': 1, 'fga': 1}
            
            elif 'missed' in event_type:
                # Missed shots
                if 'three point' in event_type or '3-pt' in event_type:
                    parsed['stat_updates'] = {'fga': 1, 'fg3a': 1}
                elif 'free throw' in event_type:
                    parsed['stat_updates'] = {'fta': 1}
                else:
                    parsed['stat_updates'] = {'fga': 1}
            
            elif 'rebound' in event_type:
                if 'offensive' in event_type:
                    parsed['stat_updates'] = {'oreb': 1, 'reb': 1}
                else:
                    parsed['stat_updates'] = {'dreb': 1, 'reb': 1}
            
            elif 'assist' in event_type:
                parsed['stat_updates'] = {'ast': 1}
            
            elif 'steal' in event_type:
                parsed['stat_updates'] = {'stl': 1}
            
            elif 'block' in event_type:
                parsed['stat_updates'] = {'blk': 1}
            
            elif 'turnover' in event_type:
                parsed['stat_updates'] = {'tov': 1}
            
            elif 'foul' in event_type:
                parsed['stat_updates'] = {'pf': 1}
            
            elif 'substitution' in event_type:
                # Handle substitutions
                if len(participants) >= 2:
                    parsed['substitution'] = {
                        'in_player_id': participants[0].get('athlete', {}).get('id'),
                        'out_player_id': participants[1].get('athlete', {}).get('id') if len(participants) > 1 else None
                    }
            
            return parsed
            
        except Exception as e:
            self.logger.warning(f"Error parsing event {event_num}: {e}", exc_info=True)
            # Return minimal event to avoid breaking processing
            return {
                'event_num': event_num,
                'play_id': None,
                'text': '',
                'quarter': 1,
                'time_remaining': '12:00',
                'game_clock_seconds': 0,
                'home_score': 0,
                'away_score': 0,
                'scoring_play': False,
                'event_type': 'unknown',
                'stat_updates': {},
                'substitution': None,
                'player_id': None,
                'team_id': None
            }
    
    def get_actual_box_score(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Load actual box score for verification.
        
        ESPN box scores are in separate files: box_score/{game_id}.json
        
        Args:
            game_id: ESPN game ID
            
        Returns:
            Dict with actual box score, or None if not available
        """
        s3_key = f"box_score/{game_id}.json"
        
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            box_score_data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Parse box score structure (ESPN box score format)
            # TODO: Implement actual box score parsing
            # For now, return None (verification will be skipped)
            
            return None
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.debug(f"Box score not found for game {game_id}")
                return None
            else:
                self.logger.error(f"Error loading box score for game {game_id}: {e}")
                return None
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_game_clock_seconds(self, period: int, seconds_remaining_in_period: float) -> int:
        """
        Calculate total game seconds elapsed from quarter and clock.
        
        Args:
            period: Quarter number (1-4, 5+ for OT)
            seconds_remaining_in_period: Seconds remaining in current period
            
        Returns:
            Total seconds elapsed since start of game
        """
        # Each quarter is 12 minutes (720 seconds)
        # OT periods are 5 minutes (300 seconds)
        
        if period <= 4:
            # Regular quarters
            seconds_before_period = (period - 1) * 720
            seconds_elapsed_in_period = 720 - seconds_remaining_in_period
        else:
            # Overtime
            seconds_before_period = 4 * 720 + (period - 5) * 300
            seconds_elapsed_in_period = 300 - seconds_remaining_in_period
        
        return int(seconds_before_period + seconds_elapsed_in_period)
    
    def process_game_from_s3(self, game_id: str, verify: bool = True) -> tuple[List[BoxScoreSnapshot], Optional[VerificationResult]]:
        """
        Convenience method to process game directly from S3.
        
        Args:
            game_id: ESPN game ID
            verify: Whether to verify final box score
            
        Returns:
            Tuple of (snapshots, verification_result)
        """
        return self.process_game(game_id, verify=verify)


# Batch processing functions

def process_games_batch(
    game_ids: List[str],
    output_dir: Optional[str] = None,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Process multiple games in batch.
    
    Args:
        game_ids: List of ESPN game IDs
        output_dir: Optional directory to save snapshots (JSON)
        verify: Whether to verify box scores
        
    Returns:
        Dict with processing stats
    """
    processor = ESPNPlayByPlayProcessor()
    
    stats = {
        'processed': 0,
        'failed': 0,
        'total_snapshots': 0,
        'verified': 0,
        'verification_passed': 0,
        'verification_failed': 0
    }
    
    for i, game_id in enumerate(game_ids, 1):
        logger.info(f"Processing game {i}/{len(game_ids)}: {game_id}")
        
        try:
            snapshots, verification = processor.process_game(game_id, verify=verify)
            stats['processed'] += 1
            stats['total_snapshots'] += len(snapshots)
            
            if verification:
                stats['verified'] += 1
                if verification.is_passing():
                    stats['verification_passed'] += 1
                else:
                    stats['verification_failed'] += 1
            
            # Save to file if output_dir specified
            if output_dir and snapshots:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Save snapshots as JSON
                with open(output_path / f"{game_id}_snapshots.json", 'w') as f:
                    json.dump([s.to_dict() for s in snapshots], f, indent=2)
                
                # Save verification if available
                if verification:
                    with open(output_path / f"{game_id}_verification.json", 'w') as f:
                        json.dump(verification.to_dict(), f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to process game {game_id}: {e}", exc_info=True)
            stats['failed'] += 1
    
    return stats


def process_season(
    season: int,
    output_dir: Optional[str] = None,
    verify: bool = True,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process all games from a season.
    
    Args:
        season: Season year (e.g., 2024)
        output_dir: Optional directory to save snapshots
        verify: Whether to verify box scores
        limit: Optional limit on number of games
        
    Returns:
        Dict with processing stats
    """
    # TODO: Get game IDs for season from RDS or S3
    # For now, placeholder
    game_ids = []  # Would query RDS or list S3 files
    
    if limit:
        game_ids = game_ids[:limit]
    
    return process_games_batch(game_ids, output_dir=output_dir, verify=verify)

