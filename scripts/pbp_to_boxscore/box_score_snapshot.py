"""
Box Score Snapshot Data Structures

Defines immutable snapshots of game state at each play-by-play event.
Each snapshot represents the complete box score at a specific moment in time.

Created: October 11, 2025
Phase: 9.0 (System Architecture)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from copy import deepcopy


@dataclass(frozen=True)
class PlayerStats:
    """Immutable player statistics at a snapshot"""
    player_id: str
    player_name: str
    team_id: str
    
    # Basic stats
    points: int = 0
    fgm: int = 0  # Field goals made
    fga: int = 0  # Field goals attempted
    fg3m: int = 0  # Three-pointers made
    fg3a: int = 0  # Three-pointers attempted
    ftm: int = 0  # Free throws made
    fta: int = 0  # Free throws attempted
    
    # Rebounds
    oreb: int = 0  # Offensive rebounds
    dreb: int = 0  # Defensive rebounds
    reb: int = 0   # Total rebounds
    
    # Other stats
    ast: int = 0   # Assists
    stl: int = 0   # Steals
    blk: int = 0   # Blocks
    tov: int = 0   # Turnovers
    pf: int = 0    # Personal fouls
    
    # Advanced
    plus_minus: int = 0
    minutes: float = 0.0
    on_court: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'player_id': self.player_id,
            'player_name': self.player_name,
            'team_id': self.team_id,
            'points': self.points,
            'fgm': self.fgm,
            'fga': self.fga,
            'fg3m': self.fg3m,
            'fg3a': self.fg3a,
            'ftm': self.ftm,
            'fta': self.fta,
            'oreb': self.oreb,
            'dreb': self.dreb,
            'reb': self.reb,
            'ast': self.ast,
            'stl': self.stl,
            'blk': self.blk,
            'tov': self.tov,
            'pf': self.pf,
            'plus_minus': self.plus_minus,
            'minutes': self.minutes,
            'on_court': self.on_court
        }
    
    def validate(self) -> List[str]:
        """
        Validate player stats for consistency.
        Returns list of validation errors (empty if valid).
        """
        errors = []
        
        # No negative stats
        if self.points < 0: errors.append(f"Negative points: {self.points}")
        if self.fgm < 0: errors.append(f"Negative FGM: {self.fgm}")
        if self.fga < 0: errors.append(f"Negative FGA: {self.fga}")
        if self.minutes < 0: errors.append(f"Negative minutes: {self.minutes}")
        
        # FGM <= FGA
        if self.fgm > self.fga:
            errors.append(f"FGM ({self.fgm}) > FGA ({self.fga})")
        
        # FG3M <= FG3A
        if self.fg3m > self.fg3a:
            errors.append(f"FG3M ({self.fg3m}) > FG3A ({self.fg3a})")
        
        # FTM <= FTA
        if self.ftm > self.fta:
            errors.append(f"FTM ({self.ftm}) > FTA ({self.fta})")
        
        # Total rebounds = offensive + defensive
        if self.reb != self.oreb + self.dreb:
            errors.append(f"REB ({self.reb}) != OREB ({self.oreb}) + DREB ({self.dreb})")
        
        # Minutes reasonable (<=48 for regulation, <=65 for OT games)
        if self.minutes > 65:
            errors.append(f"Excessive minutes: {self.minutes}")
        
        return errors


@dataclass(frozen=True)
class TeamStats:
    """Immutable team statistics at a snapshot"""
    team_id: str
    team_name: str
    
    # Scores
    points: int = 0
    
    # Shooting
    fgm: int = 0
    fga: int = 0
    fg3m: int = 0
    fg3a: int = 0
    ftm: int = 0
    fta: int = 0
    
    # Rebounds
    oreb: int = 0
    dreb: int = 0
    reb: int = 0
    
    # Other
    ast: int = 0
    stl: int = 0
    blk: int = 0
    tov: int = 0
    pf: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'team_id': self.team_id,
            'team_name': self.team_name,
            'points': self.points,
            'fgm': self.fgm,
            'fga': self.fga,
            'fg3m': self.fg3m,
            'fg3a': self.fg3a,
            'ftm': self.ftm,
            'fta': self.fta,
            'oreb': self.oreb,
            'dreb': self.dreb,
            'reb': self.reb,
            'ast': self.ast,
            'stl': self.stl,
            'blk': self.blk,
            'tov': self.tov,
            'pf': self.pf
        }


@dataclass(frozen=True)
class BoxScoreSnapshot:
    """
    Immutable snapshot of complete game state at a specific play-by-play event.
    
    Represents the cumulative box score at a specific moment in time.
    Can be stored to database and used for temporal queries.
    """
    
    # Identifiers
    game_id: str
    event_num: int
    data_source: str  # 'espn', 'hoopr', 'nba_api', 'kaggle'
    
    # Game State
    quarter: int
    time_remaining: str  # e.g., "7:32"
    game_clock_seconds: int  # Total seconds elapsed
    home_score: int
    away_score: int
    
    # Player Stats (keyed by player_id)
    players: Dict[str, PlayerStats] = field(default_factory=dict)
    
    # Team Stats (keyed by team_id)
    teams: Dict[str, TeamStats] = field(default_factory=dict)
    
    # Quarter Box Scores (cumulative per quarter)
    # Format: {1: {player_id: PlayerStats}, 2: {...}, ...}
    quarter_box_scores: Dict[int, Dict[str, PlayerStats]] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'game_id': self.game_id,
            'event_num': self.event_num,
            'data_source': self.data_source,
            'quarter': self.quarter,
            'time_remaining': self.time_remaining,
            'game_clock_seconds': self.game_clock_seconds,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'players': {pid: pstats.to_dict() for pid, pstats in self.players.items()},
            'teams': {tid: tstats.to_dict() for tid, tstats in self.teams.items()},
            'quarter_box_scores': {
                q: {pid: pstats.to_dict() for pid, pstats in players.items()}
                for q, players in self.quarter_box_scores.items()
            },
            'created_at': self.created_at.isoformat()
        }
    
    def validate(self) -> Dict[str, List[str]]:
        """
        Validate snapshot for consistency.
        Returns dict of validation errors by category.
        """
        errors = {
            'game_state': [],
            'player_stats': [],
            'team_stats': [],
            'consistency': []
        }
        
        # Game state validations
        if self.quarter < 1:
            errors['game_state'].append(f"Invalid quarter: {self.quarter}")
        
        if self.game_clock_seconds < 0:
            errors['game_state'].append(f"Negative game clock: {self.game_clock_seconds}")
        
        if self.home_score < 0 or self.away_score < 0:
            errors['game_state'].append(f"Negative score: H={self.home_score}, A={self.away_score}")
        
        # Player stat validations
        for player_id, player_stats in self.players.items():
            player_errors = player_stats.validate()
            if player_errors:
                errors['player_stats'].extend([f"{player_id}: {e}" for e in player_errors])
        
        # Team stats consistency (sum of player stats should equal team totals)
        for team_id, team_stats in self.teams.items():
            team_players = [p for p in self.players.values() if p.team_id == team_id]
            
            player_total_points = sum(p.points for p in team_players)
            if player_total_points != team_stats.points:
                errors['consistency'].append(
                    f"Team {team_id}: Player points ({player_total_points}) != Team points ({team_stats.points})"
                )
            
            player_total_reb = sum(p.reb for p in team_players)
            if player_total_reb != team_stats.reb:
                errors['consistency'].append(
                    f"Team {team_id}: Player rebounds ({player_total_reb}) != Team rebounds ({team_stats.reb})"
                )
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if snapshot passes all validations"""
        errors = self.validate()
        return all(len(errs) == 0 for errs in errors.values())
    
    def get_score_differential(self) -> int:
        """Get current score differential (home - away)"""
        return self.home_score - self.away_score
    
    def get_on_court_players(self) -> List[PlayerStats]:
        """Get list of players currently on court"""
        return [p for p in self.players.values() if p.on_court]
    
    def get_team_players(self, team_id: str) -> List[PlayerStats]:
        """Get all players for a specific team"""
        return [p for p in self.players.values() if p.team_id == team_id]


@dataclass
class VerificationResult:
    """
    Result of comparing generated box score vs actual box score.
    Used to assess quality of PBP processing.
    """
    game_id: str
    data_source: str
    
    # Final Score Comparison
    final_score_match: bool
    home_score_generated: int
    away_score_generated: int
    home_score_actual: int
    away_score_actual: int
    
    # Discrepancy Metrics
    total_discrepancies: int
    discrepancy_details: Dict[str, Dict[str, Any]]  # player_id -> {stat: {gen, act, diff}}
    
    # Mean Absolute Errors
    mae_points: float
    mae_rebounds: float
    mae_assists: float
    
    # Quality Grade
    quality_grade: str  # 'A', 'B', 'C', 'D', or 'F'
    
    # Optional fields with defaults
    mae_steals: float = 0.0
    mae_blocks: float = 0.0
    mae_turnovers: float = 0.0
    notes: str = ""
    verified_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'game_id': self.game_id,
            'data_source': self.data_source,
            'final_score_match': self.final_score_match,
            'home_score_generated': self.home_score_generated,
            'away_score_generated': self.away_score_generated,
            'home_score_actual': self.home_score_actual,
            'away_score_actual': self.away_score_actual,
            'total_discrepancies': self.total_discrepancies,
            'discrepancy_details': self.discrepancy_details,
            'mae_points': self.mae_points,
            'mae_rebounds': self.mae_rebounds,
            'mae_assists': self.mae_assists,
            'mae_steals': self.mae_steals,
            'mae_blocks': self.mae_blocks,
            'mae_turnovers': self.mae_turnovers,
            'quality_grade': self.quality_grade,
            'notes': self.notes,
            'verified_at': self.verified_at.isoformat()
        }
    
    def is_passing(self) -> bool:
        """Check if verification passed (grade A, B, or C)"""
        return self.quality_grade in ['A', 'B', 'C']


# Utility functions

def calculate_quality_grade(total_discrepancies: int, final_score_match: bool) -> str:
    """
    Calculate quality grade based on discrepancies.
    
    Grade A: Perfect (0 discrepancies)
    Grade B: Excellent (1-5 discrepancies)
    Grade C: Good (6-15 discrepancies)
    Grade D: Fair (16-30 discrepancies)
    Grade F: Failed (>30 discrepancies OR final score doesn't match)
    """
    if not final_score_match:
        return 'F'
    
    if total_discrepancies == 0:
        return 'A'
    elif total_discrepancies <= 5:
        return 'B'
    elif total_discrepancies <= 15:
        return 'C'
    elif total_discrepancies <= 30:
        return 'D'
    else:
        return 'F'


def merge_quarter_stats(q1_stats: PlayerStats, q2_stats: PlayerStats) -> PlayerStats:
    """
    Merge two quarter stats into cumulative stats.
    Used for generating cumulative box scores from quarter data.
    """
    return PlayerStats(
        player_id=q1_stats.player_id,
        player_name=q1_stats.player_name,
        team_id=q1_stats.team_id,
        points=q1_stats.points + q2_stats.points,
        fgm=q1_stats.fgm + q2_stats.fgm,
        fga=q1_stats.fga + q2_stats.fga,
        fg3m=q1_stats.fg3m + q2_stats.fg3m,
        fg3a=q1_stats.fg3a + q2_stats.fg3a,
        ftm=q1_stats.ftm + q2_stats.ftm,
        fta=q1_stats.fta + q2_stats.fta,
        oreb=q1_stats.oreb + q2_stats.oreb,
        dreb=q1_stats.dreb + q2_stats.dreb,
        reb=q1_stats.reb + q2_stats.reb,
        ast=q1_stats.ast + q2_stats.ast,
        stl=q1_stats.stl + q2_stats.stl,
        blk=q1_stats.blk + q2_stats.blk,
        tov=q1_stats.tov + q2_stats.tov,
        pf=q1_stats.pf + q2_stats.pf,
        plus_minus=q1_stats.plus_minus + q2_stats.plus_minus,
        minutes=q1_stats.minutes + q2_stats.minutes,
        on_court=q2_stats.on_court  # Use most recent status
    )

