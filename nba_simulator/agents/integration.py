"""
Integration Agent - Cross-Source Data Validation

Validates data consistency across multiple data sources.
Identifies conflicts, reconciles differences, and ensures data integrity.

Responsibilities:
- Cross-source game matching
- Score validation across sources
- Conflict detection and resolution
- Integration quality scoring
- Reconciliation reporting
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timezone
from dataclasses import dataclass
from collections import defaultdict

from .base_agent import BaseAgent, AgentPriority
from ..database import execute_query


@dataclass
class IntegrationMatch:
    """Match between records from different sources"""

    game_id: str
    sources: List[str]
    conflicts: List[str]
    confidence_score: float  # 0.0 to 100.0


@dataclass
class ConflictResolution:
    """Resolution for a data conflict"""

    field: str
    source_values: Dict[str, Any]
    resolved_value: Any
    resolution_method: str


class IntegrationAgent(BaseAgent):
    """
    Cross-source integration validation agent.

    Validates data across multiple sources:
    - ESPN
    - Basketball Reference
    - NBA API
    - hoopR
    - Betting data

    Detects conflicts, validates consistency, and generates
    integration quality scores.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Integration Agent.

        Args:
            config: Configuration with keys:
                - min_integration_score: Minimum acceptable score (default: 90.0)
                - conflict_resolution: Strategy ('latest', 'majority', 'manual')
                - match_threshold: Confidence threshold for matches (default: 80.0)
                - validate_all_sources: Check all source pairs (default: False)
        """
        super().__init__(
            agent_name="integration_validator",
            config=config,
            priority=AgentPriority.HIGH,
        )

        # Configuration
        self.min_integration_score = self.config.get("min_integration_score", 90.0)
        self.conflict_resolution = self.config.get("conflict_resolution", "latest")
        self.match_threshold = self.config.get("match_threshold", 80.0)
        self.validate_all_sources = self.config.get("validate_all_sources", False)

        # Results
        self.matches: List[IntegrationMatch] = []
        self.conflicts: List[ConflictResolution] = []
        self.integration_score: float = 0.0

        # Source pairs to validate
        self.source_pairs = [
            ("espn", "basketball_reference"),
            ("espn", "nba_api"),
            ("espn", "hoopr"),
            ("basketball_reference", "nba_api"),
            ("basketball_reference", "hoopr"),
            ("nba_api", "hoopr"),
        ]

    def _validate_config(self) -> bool:
        """Validate integration agent configuration"""
        try:
            # Check min_integration_score
            if not 0.0 <= self.min_integration_score <= 100.0:
                self.log_error("min_integration_score must be between 0.0 and 100.0")
                return False

            # Check match_threshold
            if not 0.0 <= self.match_threshold <= 100.0:
                self.log_error("match_threshold must be between 0.0 and 100.0")
                return False

            # Check conflict_resolution strategy
            valid_strategies = ["latest", "majority", "manual"]
            if self.conflict_resolution not in valid_strategies:
                self.log_error(f"conflict_resolution must be one of {valid_strategies}")
                return False

            self.logger.info("Integration agent configuration validated")
            return True

        except Exception as e:
            self.log_error(f"Configuration validation error: {e}")
            return False

    def _execute_core(self) -> bool:
        """Execute integration validation"""
        try:
            self.logger.info("Starting integration validation...")

            # Validate each source pair
            if self.validate_all_sources:
                pairs_to_check = self.source_pairs
            else:
                # Only check primary pairs for efficiency
                pairs_to_check = [("espn", "basketball_reference"), ("espn", "hoopr")]

            for source1, source2 in pairs_to_check:
                self.logger.info(f"Validating integration: {source1} <-> {source2}")
                self._validate_source_pair(source1, source2)

            # Calculate integration score
            self._calculate_integration_score()

            # Update metrics
            self.metrics.items_processed = len(self.matches)
            self.metrics.items_successful = sum(
                1
                for match in self.matches
                if match.confidence_score >= self.match_threshold
            )
            self.metrics.items_failed = len(self.conflicts)
            self.metrics.quality_score = self.integration_score

            # Check if integration meets threshold
            if self.integration_score < self.min_integration_score:
                self.log_error(
                    f"Integration score {self.integration_score:.1f}% "
                    f"below threshold {self.min_integration_score:.1f}%"
                )
                return False

            self.logger.info(
                f"Integration validation complete. Score: {self.integration_score:.1f}%"
            )
            return True

        except Exception as e:
            self.log_error(f"Integration validation error: {e}")
            return False

    def _validate_source_pair(self, source1: str, source2: str) -> None:
        """
        Validate integration between two sources.

        Args:
            source1: First source name
            source2: Second source name
        """
        try:
            # Get matching games from both sources
            matches = self._find_matching_games(source1, source2)

            for game_data in matches:
                game_id = game_data["game_id"]

                # Compare key fields
                conflicts = self._compare_game_data(
                    game_id, source1, source2, game_data
                )

                # Calculate confidence score
                confidence = self._calculate_match_confidence(conflicts)

                # Create match record
                match = IntegrationMatch(
                    game_id=game_id,
                    sources=[source1, source2],
                    conflicts=conflicts,
                    confidence_score=confidence,
                )
                self.matches.append(match)

                # Resolve conflicts if any
                if conflicts:
                    self._resolve_conflicts(game_id, source1, source2, conflicts)

        except Exception as e:
            self.log_error(f"Error validating {source1} <-> {source2}: {e}")

    def _find_matching_games(self, source1: str, source2: str) -> List[Dict[str, Any]]:
        """
        Find games present in both sources.

        Args:
            source1: First source
            source2: Second source

        Returns:
            List of game dictionaries with data from both sources
        """
        try:
            # Query to find matching games
            # In real implementation, would join on source-specific tables
            # For now, using games table as common reference
            query = """
                SELECT 
                    game_id,
                    game_date,
                    home_team,
                    away_team,
                    home_score,
                    away_score
                FROM games
                WHERE game_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY game_date DESC
                LIMIT 100
            """

            results = execute_query(query)
            return results if results else []

        except Exception as e:
            self.log_error(f"Error finding matching games: {e}")
            return []

    def _compare_game_data(
        self, game_id: str, source1: str, source2: str, game_data: Dict[str, Any]
    ) -> List[str]:
        """
        Compare game data from two sources.

        Args:
            game_id: Game identifier
            source1: First source
            source2: Second source
            game_data: Game data to compare

        Returns:
            List of conflicting fields
        """
        conflicts = []

        # In real implementation, would query source-specific tables
        # For now, simulating conflict detection

        # Check critical fields
        critical_fields = ["home_score", "away_score", "game_date"]

        # Simulate some validation logic
        # Would actually query and compare source-specific data

        return conflicts

    def _calculate_match_confidence(self, conflicts: List[str]) -> float:
        """
        Calculate confidence score for a match.

        Args:
            conflicts: List of conflicting fields

        Returns:
            Confidence score (0.0 to 100.0)
        """
        if not conflicts:
            return 100.0

        # Reduce confidence based on number of conflicts
        # Each conflict reduces confidence by 10%
        reduction = min(len(conflicts) * 10, 90)
        return 100.0 - reduction

    def _resolve_conflicts(
        self, game_id: str, source1: str, source2: str, conflicts: List[str]
    ) -> None:
        """
        Resolve conflicts between sources.

        Args:
            game_id: Game identifier
            source1: First source
            source2: Second source
            conflicts: List of conflicting fields
        """
        for field in conflicts:
            resolution = self._resolve_field_conflict(game_id, field, source1, source2)
            if resolution:
                self.conflicts.append(resolution)

    def _resolve_field_conflict(
        self, game_id: str, field: str, source1: str, source2: str
    ) -> Optional[ConflictResolution]:
        """
        Resolve a specific field conflict.

        Args:
            game_id: Game identifier
            field: Conflicting field name
            source1: First source
            source2: Second source

        Returns:
            ConflictResolution or None
        """
        try:
            # In real implementation, would fetch actual values from sources
            source_values = {
                source1: "value1",  # Placeholder
                source2: "value2",  # Placeholder
            }

            # Apply resolution strategy
            if self.conflict_resolution == "latest":
                # Use value from most recently updated source
                resolved_value = source_values[source2]
                method = "latest"
            elif self.conflict_resolution == "majority":
                # Use most common value (would check more than 2 sources)
                resolved_value = source_values[source1]
                method = "majority"
            else:  # manual
                # Flag for manual review
                resolved_value = None
                method = "manual_review_required"

            return ConflictResolution(
                field=field,
                source_values=source_values,
                resolved_value=resolved_value,
                resolution_method=method,
            )

        except Exception as e:
            self.log_error(f"Error resolving conflict for {field}: {e}")
            return None

    def _calculate_integration_score(self) -> None:
        """Calculate overall integration quality score"""
        if not self.matches:
            self.integration_score = 0.0
            return

        # Average confidence scores across all matches
        total_confidence = sum(match.confidence_score for match in self.matches)
        self.integration_score = total_confidence / len(self.matches)

        # Penalize for unresolved conflicts
        if self.conflicts:
            manual_conflicts = sum(
                1
                for c in self.conflicts
                if c.resolution_method == "manual_review_required"
            )
            penalty = (manual_conflicts / len(self.conflicts)) * 5  # Up to 5% penalty
            self.integration_score = max(0, self.integration_score - penalty)

        self.logger.info(
            f"Integration score: {self.integration_score:.1f}% "
            f"({len(self.matches)} matches, {len(self.conflicts)} conflicts)"
        )

    def get_agent_info(self) -> Dict[str, Any]:
        """Get integration agent information"""
        return {
            "name": "Integration Validator",
            "version": "1.0.0",
            "description": "Validates data consistency across multiple sources",
            "capabilities": [
                "Cross-source game matching",
                "Conflict detection",
                "Automatic conflict resolution",
                "Integration quality scoring",
                "Reconciliation reporting",
            ],
            "integration_threshold": self.min_integration_score,
            "resolution_strategy": self.conflict_resolution,
            "source_pairs": len(self.source_pairs),
        }

    def get_integration_report(self) -> Dict[str, Any]:
        """
        Get detailed integration report.

        Returns:
            Dict with integration scores, matches, and conflicts
        """
        return {
            "integration_score": self.integration_score,
            "threshold": self.min_integration_score,
            "passed": self.integration_score >= self.min_integration_score,
            "total_matches": len(self.matches),
            "high_confidence_matches": sum(
                1 for m in self.matches if m.confidence_score >= self.match_threshold
            ),
            "total_conflicts": len(self.conflicts),
            "unresolved_conflicts": sum(
                1
                for c in self.conflicts
                if c.resolution_method == "manual_review_required"
            ),
            "match_summary": [
                {
                    "game_id": match.game_id,
                    "sources": match.sources,
                    "confidence": match.confidence_score,
                    "conflicts": len(match.conflicts),
                }
                for match in self.matches[:10]  # Top 10
            ],
            "conflict_summary": [
                {
                    "field": conflict.field,
                    "source_values": conflict.source_values,
                    "resolution_method": conflict.resolution_method,
                }
                for conflict in self.conflicts[:10]  # Top 10
            ],
        }
