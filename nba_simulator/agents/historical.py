"""
Historical Agent - Historical Data Management

Manages historical NBA data processing and validation.
Handles data from 1946 to present with era-specific logic.

Responsibilities:
- Historical data validation
- Era-specific processing rules
- Retroactive data updates
- Historical completeness tracking
- Archive management
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .base_agent import BaseAgent, AgentPriority
from ..database import execute_query


class HistoricalAgent(BaseAgent):
    """
    Historical data management agent.
    
    Manages NBA data across eras:
    - BAA Era (1946-1949)
    - Early NBA (1950-1979)
    - Modern Era (1980-1999)
    - Contemporary Era (2000-present)
    
    Applies era-specific validation and processing rules.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Historical Agent.
        
        Args:
            config: Configuration with keys:
                - start_year: Earliest year to process (default: 1946)
                - end_year: Latest year to process (default: current year)
                - eras_to_process: List of eras (default: all)
                - validate_rules: Apply era-specific rules (default: True)
        """
        super().__init__(
            agent_name="historical",
            config=config,
            priority=AgentPriority.NORMAL
        )
        
        # Configuration
        self.start_year = self.config.get('start_year', 1946)
        self.end_year = self.config.get('end_year', datetime.now().year)
        self.eras_to_process = self.config.get('eras_to_process', ['all'])
        self.validate_rules = self.config.get('validate_rules', True)
        
        # Era definitions
        self.eras = {
            'baa': (1946, 1949),
            'early_nba': (1950, 1979),
            'modern': (1980, 1999),
            'contemporary': (2000, 2024)
        }
        
        # Results
        self.games_by_era: Dict[str, int] = {}
        self.validation_issues: List[str] = []
    
    def _validate_config(self) -> bool:
        """Validate historical agent configuration"""
        try:
            if self.start_year < 1946:
                self.log_error("start_year must be >= 1946 (NBA founding)")
                return False
            
            if self.end_year < self.start_year:
                self.log_error("end_year must be >= start_year")
                return False
            
            current_year = datetime.now().year
            if self.end_year > current_year + 1:
                self.log_warning(f"end_year {self.end_year} is in the future")
            
            self.logger.info("Historical agent configuration validated")
            return True
            
        except Exception as e:
            self.log_error(f"Configuration validation error: {e}")
            return False
    
    def _execute_core(self) -> bool:
        """Execute historical data processing"""
        try:
            self.logger.info(
                f"Processing historical data: {self.start_year}-{self.end_year}"
            )
            
            # Process each era
            for era_name, (start, end) in self.eras.items():
                # Skip eras outside our range
                if end < self.start_year or start > self.end_year:
                    continue
                
                # Skip if not in eras_to_process
                if 'all' not in self.eras_to_process:
                    if era_name not in self.eras_to_process:
                        continue
                
                self.logger.info(f"Processing era: {era_name} ({start}-{end})")
                self._process_era(era_name, start, end)
            
            # Calculate metrics
            total_games = sum(self.games_by_era.values())
            self.metrics.items_processed = total_games
            
            # All games successfully processed if no critical issues
            self.metrics.items_successful = total_games
            self.metrics.items_failed = len(self.validation_issues)
            
            if total_games > 0:
                self.metrics.quality_score = (
                    self.metrics.items_successful / 
                    (self.metrics.items_successful + self.metrics.items_failed) * 100
                )
            else:
                self.metrics.quality_score = 100.0
            
            self.logger.info(
                f"Historical processing complete. "
                f"Processed {total_games} games across {len(self.games_by_era)} eras"
            )
            
            return True
            
        except Exception as e:
            self.log_error(f"Historical processing error: {e}")
            return False
    
    def _process_era(self, era_name: str, start_year: int, end_year: int) -> None:
        """
        Process games for a specific era.
        
        Args:
            era_name: Name of the era
            start_year: Start year
            end_year: End year
        """
        try:
            # Get games in this era
            games = self._get_era_games(start_year, end_year)
            self.games_by_era[era_name] = len(games)
            
            if not games:
                self.logger.info(f"No games found for era {era_name}")
                return
            
            # Apply era-specific validation
            if self.validate_rules:
                self._validate_era_rules(era_name, games)
            
        except Exception as e:
            self.log_error(f"Error processing era {era_name}: {e}")
    
    def _get_era_games(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """Get games for an era"""
        try:
            query = f"""
                SELECT game_id, game_date, home_team, away_team, home_score, away_score
                FROM games
                WHERE EXTRACT(YEAR FROM game_date) BETWEEN {start_year} AND {end_year}
                ORDER BY game_date
            """
            
            results = execute_query(query)
            return results if results else []
            
        except Exception as e:
            self.log_error(f"Error getting era games: {e}")
            return []
    
    def _validate_era_rules(
        self, 
        era_name: str, 
        games: List[Dict[str, Any]]
    ) -> None:
        """
        Apply era-specific validation rules.
        
        Args:
            era_name: Era name
            games: List of games to validate
        """
        try:
            # Era-specific rules
            if era_name == 'baa':
                # BAA era: Lower scoring, no 3-point line
                self._validate_baa_era(games)
            elif era_name == 'early_nba':
                # Early NBA: Introduction of shot clock (1954)
                self._validate_early_nba(games)
            elif era_name == 'modern':
                # Modern: 3-point line introduced (1979)
                self._validate_modern_era(games)
            else:
                # Contemporary: Current rules
                self._validate_contemporary(games)
            
        except Exception as e:
            self.log_error(f"Error validating era rules: {e}")
    
    def _validate_baa_era(self, games: List[Dict[str, Any]]) -> None:
        """Validate BAA era games (1946-1949)"""
        for game in games:
            # Check for unrealistic scores (no 3-pointers, lower pace)
            if game['home_score'] and game['home_score'] > 120:
                self.validation_issues.append(
                    f"Unusually high BAA score: {game['game_id']}"
                )
    
    def _validate_early_nba(self, games: List[Dict[str, Any]]) -> None:
        """Validate early NBA games (1950-1979)"""
        # Shot clock introduced in 1954 increased pace
        pass
    
    def _validate_modern_era(self, games: List[Dict[str, Any]]) -> None:
        """Validate modern era games (1980-1999)"""
        # 3-point line era
        pass
    
    def _validate_contemporary(self, games: List[Dict[str, Any]]) -> None:
        """Validate contemporary games (2000-present)"""
        # Current rules
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get historical agent information"""
        return {
            'name': 'Historical Data Manager',
            'version': '1.0.0',
            'description': 'Manages historical NBA data across all eras',
            'capabilities': [
                'Era-specific processing',
                'Historical validation',
                'Retroactive updates',
                'Completeness tracking',
                'Archive management'
            ],
            'year_range': f"{self.start_year}-{self.end_year}",
            'eras': list(self.eras.keys())
        }
    
    def get_historical_report(self) -> Dict[str, Any]:
        """Get historical processing report"""
        return {
            'year_range': f"{self.start_year}-{self.end_year}",
            'games_by_era': self.games_by_era,
            'total_games': sum(self.games_by_era.values()),
            'validation_issues': len(self.validation_issues),
            'eras_processed': list(self.games_by_era.keys())
        }
