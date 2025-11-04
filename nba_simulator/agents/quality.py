"""
Quality Agent - Data Quality Validation and Scoring

Validates data quality across all sources and generates quality scores.
Detects anomalies, missing data, and inconsistencies.

Responsibilities:
- Data completeness validation
- Statistical anomaly detection
- Cross-field consistency checks
- Quality score calculation
- Issue reporting and tracking
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
import statistics

from .base_agent import BaseAgent, AgentPriority
from ..database import execute_query


@dataclass
class QualityCheck:
    """Individual quality check result"""
    check_name: str
    passed: bool
    score: float  # 0.0 to 100.0
    message: str
    details: Dict[str, Any]


class QualityAgent(BaseAgent):
    """
    Data quality validation agent.
    
    Performs comprehensive quality checks:
    - Completeness: Required fields present
    - Consistency: Cross-field validation
    - Accuracy: Value range validation
    - Timeliness: Data freshness
    - Anomalies: Statistical outliers
    
    Generates overall quality score and detailed reports.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Quality Agent.
        
        Args:
            config: Configuration with keys:
                - min_quality_score: Minimum acceptable score (default: 80.0)
                - check_completeness: Enable completeness checks (default: True)
                - check_consistency: Enable consistency checks (default: True)
                - check_anomalies: Enable anomaly detection (default: True)
                - anomaly_threshold: Standard deviations for anomalies (default: 3.0)
        """
        super().__init__(
            agent_name="quality_validator",
            config=config,
            priority=AgentPriority.HIGH
        )
        
        # Configuration
        self.min_quality_score = self.config.get('min_quality_score', 80.0)
        self.check_completeness = self.config.get('check_completeness', True)
        self.check_consistency = self.config.get('check_consistency', True)
        self.check_anomalies = self.config.get('check_anomalies', True)
        self.anomaly_threshold = self.config.get('anomaly_threshold', 3.0)
        
        # Results
        self.quality_checks: List[QualityCheck] = []
        self.overall_quality_score: float = 0.0
        self.critical_issues: List[str] = []
        self.warnings: List[str] = []
        
        # Data sources to validate
        self.sources = ['espn', 'basketball_reference', 'nba_api', 'hoopr', 'betting']
    
    def _validate_config(self) -> bool:
        """Validate quality agent configuration"""
        try:
            # Check min_quality_score
            if not 0.0 <= self.min_quality_score <= 100.0:
                self.log_error("min_quality_score must be between 0.0 and 100.0")
                return False
            
            # Check anomaly_threshold
            if not isinstance(self.anomaly_threshold, (int, float)) or self.anomaly_threshold <= 0:
                self.log_error("anomaly_threshold must be positive number")
                return False
            
            # Check boolean flags
            for flag in ['check_completeness', 'check_consistency', 'check_anomalies']:
                if not isinstance(getattr(self, flag), bool):
                    self.log_error(f"{flag} must be boolean")
                    return False
            
            self.logger.info("Quality agent configuration validated")
            return True
            
        except Exception as e:
            self.log_error(f"Configuration validation error: {e}")
            return False
    
    def _execute_core(self) -> bool:
        """Execute quality validation"""
        try:
            self.logger.info("Starting quality validation...")
            
            # Run quality checks
            if self.check_completeness:
                self._check_data_completeness()
            
            if self.check_consistency:
                self._check_data_consistency()
            
            if self.check_anomalies:
                self._check_anomalies()
            
            # Calculate overall quality score
            self._calculate_quality_score()
            
            # Update metrics
            self.metrics.items_processed = len(self.quality_checks)
            self.metrics.items_successful = sum(
                1 for check in self.quality_checks if check.passed
            )
            self.metrics.items_failed = sum(
                1 for check in self.quality_checks if not check.passed
            )
            self.metrics.quality_score = self.overall_quality_score
            
            # Check if quality meets threshold
            if self.overall_quality_score < self.min_quality_score:
                self.log_error(
                    f"Quality score {self.overall_quality_score:.1f}% "
                    f"below threshold {self.min_quality_score:.1f}%"
                )
                return False
            
            self.logger.info(
                f"Quality validation complete. Score: {self.overall_quality_score:.1f}%"
            )
            return True
            
        except Exception as e:
            self.log_error(f"Quality validation error: {e}")
            return False
    
    def _check_data_completeness(self) -> None:
        """Check data completeness across all sources"""
        try:
            self.logger.info("Checking data completeness...")
            
            # Check games table
            games_check = self._check_games_completeness()
            self.quality_checks.append(games_check)
            
            # Check play-by-play data
            pbp_check = self._check_pbp_completeness()
            self.quality_checks.append(pbp_check)
            
            # Check box scores
            box_check = self._check_box_score_completeness()
            self.quality_checks.append(box_check)
            
            # Check source-specific data
            for source in self.sources:
                source_check = self._check_source_completeness(source)
                if source_check:
                    self.quality_checks.append(source_check)
            
        except Exception as e:
            self.log_error(f"Completeness check error: {e}")
    
    def _check_games_completeness(self) -> QualityCheck:
        """Check games table completeness"""
        try:
            # Get games with missing critical fields
            query = """
                SELECT 
                    COUNT(*) as total_games,
                    SUM(CASE WHEN game_date IS NULL THEN 1 ELSE 0 END) as missing_date,
                    SUM(CASE WHEN home_team IS NULL THEN 1 ELSE 0 END) as missing_home,
                    SUM(CASE WHEN away_team IS NULL THEN 1 ELSE 0 END) as missing_away,
                    SUM(CASE WHEN home_score IS NULL THEN 1 ELSE 0 END) as missing_home_score,
                    SUM(CASE WHEN away_score IS NULL THEN 1 ELSE 0 END) as missing_away_score
                FROM games
            """
            
            result = execute_query(query)
            if not result:
                return QualityCheck(
                    check_name="games_completeness",
                    passed=False,
                    score=0.0,
                    message="Could not query games table",
                    details={}
                )
            
            data = result[0]
            total = data['total_games']
            
            if total == 0:
                return QualityCheck(
                    check_name="games_completeness",
                    passed=False,
                    score=0.0,
                    message="No games found in database",
                    details=data
                )
            
            # Calculate missing percentage
            missing_fields = (
                data['missing_date'] +
                data['missing_home'] +
                data['missing_away'] +
                data['missing_home_score'] +
                data['missing_away_score']
            )
            total_fields = total * 5  # 5 critical fields
            completeness = ((total_fields - missing_fields) / total_fields) * 100
            
            passed = completeness >= 95.0  # Require 95% completeness
            
            return QualityCheck(
                check_name="games_completeness",
                passed=passed,
                score=completeness,
                message=f"Games table {completeness:.1f}% complete",
                details=data
            )
            
        except Exception as e:
            self.log_error(f"Games completeness check error: {e}")
            return QualityCheck(
                check_name="games_completeness",
                passed=False,
                score=0.0,
                message=f"Check failed: {str(e)}",
                details={}
            )
    
    def _check_pbp_completeness(self) -> QualityCheck:
        """Check play-by-play completeness"""
        try:
            # Check for games with PBP data
            query = """
                SELECT 
                    COUNT(DISTINCT g.game_id) as total_games,
                    COUNT(DISTINCT pbp.game_id) as games_with_pbp
                FROM games g
                LEFT JOIN play_by_play pbp ON g.game_id = pbp.game_id
                WHERE g.game_date >= CURRENT_DATE - INTERVAL '30 days'
            """
            
            result = execute_query(query)
            if not result:
                return QualityCheck(
                    check_name="pbp_completeness",
                    passed=False,
                    score=0.0,
                    message="Could not query play-by-play data",
                    details={}
                )
            
            data = result[0]
            total = data['total_games']
            with_pbp = data['games_with_pbp']
            
            if total == 0:
                completeness = 100.0
            else:
                completeness = (with_pbp / total) * 100
            
            passed = completeness >= 80.0  # Require 80% of recent games
            
            return QualityCheck(
                check_name="pbp_completeness",
                passed=passed,
                score=completeness,
                message=f"Play-by-play {completeness:.1f}% complete for recent games",
                details=data
            )
            
        except Exception as e:
            self.log_error(f"PBP completeness check error: {e}")
            return QualityCheck(
                check_name="pbp_completeness",
                passed=False,
                score=0.0,
                message=f"Check failed: {str(e)}",
                details={}
            )
    
    def _check_box_score_completeness(self) -> QualityCheck:
        """Check box score completeness"""
        try:
            query = """
                SELECT 
                    COUNT(DISTINCT g.game_id) as total_games,
                    COUNT(DISTINCT bs.game_id) as games_with_box
                FROM games g
                LEFT JOIN box_scores bs ON g.game_id = bs.game_id
                WHERE g.game_date >= CURRENT_DATE - INTERVAL '30 days'
            """
            
            result = execute_query(query)
            if not result:
                return QualityCheck(
                    check_name="box_score_completeness",
                    passed=False,
                    score=0.0,
                    message="Could not query box score data",
                    details={}
                )
            
            data = result[0]
            total = data['total_games']
            with_box = data['games_with_box']
            
            if total == 0:
                completeness = 100.0
            else:
                completeness = (with_box / total) * 100
            
            passed = completeness >= 90.0
            
            return QualityCheck(
                check_name="box_score_completeness",
                passed=passed,
                score=completeness,
                message=f"Box scores {completeness:.1f}% complete",
                details=data
            )
            
        except Exception as e:
            self.log_error(f"Box score completeness check error: {e}")
            return QualityCheck(
                check_name="box_score_completeness",
                passed=False,
                score=0.0,
                message=f"Check failed: {str(e)}",
                details={}
            )
    
    def _check_source_completeness(self, source: str) -> Optional[QualityCheck]:
        """Check completeness for a specific data source"""
        # Placeholder - would check source-specific tables
        return None
    
    def _check_data_consistency(self) -> None:
        """Check data consistency across fields"""
        try:
            self.logger.info("Checking data consistency...")
            
            # Check score consistency
            score_check = self._check_score_consistency()
            self.quality_checks.append(score_check)
            
            # Check date consistency
            date_check = self._check_date_consistency()
            self.quality_checks.append(date_check)
            
        except Exception as e:
            self.log_error(f"Consistency check error: {e}")
    
    def _check_score_consistency(self) -> QualityCheck:
        """Check that scores are logical"""
        try:
            # Check for negative scores or extreme values
            query = """
                SELECT 
                    COUNT(*) as total_games,
                    SUM(CASE WHEN home_score < 0 OR away_score < 0 THEN 1 ELSE 0 END) as negative_scores,
                    SUM(CASE WHEN home_score > 200 OR away_score > 200 THEN 1 ELSE 0 END) as extreme_scores
                FROM games
                WHERE home_score IS NOT NULL AND away_score IS NOT NULL
            """
            
            result = execute_query(query)
            if not result:
                return QualityCheck(
                    check_name="score_consistency",
                    passed=False,
                    score=0.0,
                    message="Could not check score consistency",
                    details={}
                )
            
            data = result[0]
            total = data['total_games']
            issues = data['negative_scores'] + data['extreme_scores']
            
            if total == 0:
                consistency = 100.0
            else:
                consistency = ((total - issues) / total) * 100
            
            passed = consistency >= 99.0  # Very high bar for score consistency
            
            return QualityCheck(
                check_name="score_consistency",
                passed=passed,
                score=consistency,
                message=f"Score consistency: {consistency:.1f}%",
                details=data
            )
            
        except Exception as e:
            self.log_error(f"Score consistency check error: {e}")
            return QualityCheck(
                check_name="score_consistency",
                passed=False,
                score=0.0,
                message=f"Check failed: {str(e)}",
                details={}
            )
    
    def _check_date_consistency(self) -> QualityCheck:
        """Check date field consistency"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_games,
                    SUM(CASE WHEN game_date > CURRENT_DATE THEN 1 ELSE 0 END) as future_dates,
                    SUM(CASE WHEN game_date < '1946-01-01' THEN 1 ELSE 0 END) as invalid_dates
                FROM games
            """
            
            result = execute_query(query)
            if not result:
                return QualityCheck(
                    check_name="date_consistency",
                    passed=False,
                    score=0.0,
                    message="Could not check date consistency",
                    details={}
                )
            
            data = result[0]
            total = data['total_games']
            issues = data['future_dates'] + data['invalid_dates']
            
            if total == 0:
                consistency = 100.0
            else:
                consistency = ((total - issues) / total) * 100
            
            passed = consistency >= 99.9
            
            return QualityCheck(
                check_name="date_consistency",
                passed=passed,
                score=consistency,
                message=f"Date consistency: {consistency:.1f}%",
                details=data
            )
            
        except Exception as e:
            self.log_error(f"Date consistency check error: {e}")
            return QualityCheck(
                check_name="date_consistency",
                passed=False,
                score=0.0,
                message=f"Check failed: {str(e)}",
                details={}
            )
    
    def _check_anomalies(self) -> None:
        """Detect statistical anomalies"""
        try:
            self.logger.info("Checking for anomalies...")
            
            # Check for score anomalies
            score_anomaly_check = self._detect_score_anomalies()
            if score_anomaly_check:
                self.quality_checks.append(score_anomaly_check)
            
        except Exception as e:
            self.log_error(f"Anomaly detection error: {e}")
    
    def _detect_score_anomalies(self) -> Optional[QualityCheck]:
        """Detect anomalous game scores using statistical methods"""
        try:
            # Get recent game scores
            query = """
                SELECT home_score, away_score
                FROM games
                WHERE game_date >= CURRENT_DATE - INTERVAL '365 days'
                AND home_score IS NOT NULL 
                AND away_score IS NOT NULL
            """
            
            results = execute_query(query)
            if not results or len(results) < 30:  # Need minimum sample size
                return None
            
            # Calculate statistics
            all_scores = []
            for row in results:
                all_scores.extend([row['home_score'], row['away_score']])
            
            mean_score = statistics.mean(all_scores)
            stdev_score = statistics.stdev(all_scores)
            
            # Find anomalies (scores beyond threshold standard deviations)
            threshold = self.anomaly_threshold
            lower_bound = mean_score - (threshold * stdev_score)
            upper_bound = mean_score + (threshold * stdev_score)
            
            anomalies = sum(
                1 for score in all_scores 
                if score < lower_bound or score > upper_bound
            )
            
            anomaly_rate = (anomalies / len(all_scores)) * 100
            score = 100 - (anomaly_rate * 10)  # Penalize anomalies
            score = max(0, min(100, score))
            
            passed = anomaly_rate < 1.0  # Less than 1% anomalies acceptable
            
            return QualityCheck(
                check_name="score_anomaly_detection",
                passed=passed,
                score=score,
                message=f"Anomaly rate: {anomaly_rate:.2f}%",
                details={
                    'mean_score': mean_score,
                    'stdev_score': stdev_score,
                    'anomalies_found': anomalies,
                    'total_scores': len(all_scores)
                }
            )
            
        except Exception as e:
            self.log_error(f"Score anomaly detection error: {e}")
            return None
    
    def _calculate_quality_score(self) -> None:
        """Calculate overall quality score from all checks"""
        if not self.quality_checks:
            self.overall_quality_score = 0.0
            return
        
        # Weighted average of all check scores
        total_score = sum(check.score for check in self.quality_checks)
        self.overall_quality_score = total_score / len(self.quality_checks)
        
        # Identify critical issues (failed checks with score < 50)
        self.critical_issues = [
            check.check_name 
            for check in self.quality_checks 
            if not check.passed and check.score < 50.0
        ]
        
        self.logger.info(
            f"Overall quality score: {self.overall_quality_score:.1f}% "
            f"({len(self.quality_checks)} checks, "
            f"{len(self.critical_issues)} critical issues)"
        )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get quality agent information"""
        return {
            'name': 'Quality Validator',
            'version': '1.0.0',
            'description': 'Validates data quality and generates quality scores',
            'capabilities': [
                'Data completeness validation',
                'Cross-field consistency checks',
                'Statistical anomaly detection',
                'Quality score calculation',
                'Issue tracking and reporting'
            ],
            'quality_threshold': self.min_quality_score,
            'checks_enabled': {
                'completeness': self.check_completeness,
                'consistency': self.check_consistency,
                'anomalies': self.check_anomalies
            }
        }
    
    def get_quality_report(self) -> Dict[str, Any]:
        """
        Get detailed quality report.
        
        Returns:
            Dict with quality scores, check results, and issues
        """
        return {
            'overall_score': self.overall_quality_score,
            'threshold': self.min_quality_score,
            'passed': self.overall_quality_score >= self.min_quality_score,
            'total_checks': len(self.quality_checks),
            'passed_checks': sum(1 for c in self.quality_checks if c.passed),
            'failed_checks': sum(1 for c in self.quality_checks if not c.passed),
            'critical_issues': self.critical_issues,
            'check_results': [
                {
                    'name': check.check_name,
                    'passed': check.passed,
                    'score': check.score,
                    'message': check.message
                }
                for check in self.quality_checks
            ]
        }
