"""
Tests for Phase 0.0007: Odds API Data Integration

This test suite validates the completion of Phase 0.0007 by checking:
- Database schema existence (odds schema)
- Core table creation (events, bookmakers, market_types, odds_snapshots, scores)
- Reference data population
- Data presence (lenient - scraper runs separately)
- Odds calculation logic (American odds conversions)
- Integration capability (query odds from nba-simulator-aws)

Note: Tests are lenient about data presence since odds-api scraper
runs separately at /Users/ryanranft/odds-api/

Usage:
    pytest tests/phases/phase_0/test_0_0007_odds_api.py -v
    pytest tests/phases/phase_0/test_0_0007_odds_api.py -v --verbose
"""

import pytest
import sys
import os
from pathlib import Path

# Import validator from validators directory
validators_path = (
    Path(__file__).parent.parent.parent.parent / "validators" / "phases" / "phase_0"
)
sys.path.insert(0, str(validators_path))

from validate_0_7_odds_api import Phase07OddsAPIValidator


class TestPhase07OddsSchema:
    """Tests for Phase 0.0007 database schema validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase07OddsAPIValidator(verbose=False)

    def test_schema_exists(self, validator):
        """Test odds schema exists in RDS."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_schema_exists() == True
        ), f"Schema validation failed: {validator.failures}"

    def test_core_tables_exist(self, validator):
        """Test all core tables exist in odds schema."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_core_tables() == True
        ), f"Core tables validation failed: {validator.failures}"


class TestPhase07ReferenceData:
    """Tests for Phase 0.0007 reference data validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase07OddsAPIValidator(verbose=False)

    def test_bookmakers_populated(self, validator):
        """Test bookmakers table is populated."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM odds.bookmakers")
        count = cursor.fetchone()[0]

        assert count >= 5, f"Expected >= 5 bookmakers, found {count}"

    def test_market_types_populated(self, validator):
        """Test market_types table is populated."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM odds.market_types")
        count = cursor.fetchone()[0]

        assert count >= 3, f"Expected >= 3 market types, found {count}"

    def test_bookmakers_have_required_fields(self, validator):
        """Test bookmakers have key and title."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute(
            """
            SELECT bookmaker_key, bookmaker_title
            FROM odds.bookmakers
            WHERE bookmaker_key IS NULL OR bookmaker_title IS NULL
        """
        )
        null_records = cursor.fetchall()

        assert (
            len(null_records) == 0
        ), f"Found {len(null_records)} bookmakers with NULL key/title"

    def test_market_types_have_required_fields(self, validator):
        """Test market types have key and name."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute(
            """
            SELECT market_key, market_name
            FROM odds.market_types
            WHERE market_key IS NULL OR market_name IS NULL
        """
        )
        null_records = cursor.fetchall()

        assert (
            len(null_records) == 0
        ), f"Found {len(null_records)} market types with NULL key/name"


class TestPhase07DataPresence:
    """Tests for Phase 0.0007 data presence (lenient - scraper runs separately)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase07OddsAPIValidator(verbose=False)

    def test_data_presence_check_passes(self, validator):
        """Test data presence check passes (even with no data)."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_data_presence() == True
        ), f"Data presence check failed: {validator.failures}"

    def test_data_freshness_check_passes(self, validator):
        """Test data freshness check passes (even with no data)."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_data_freshness() == True
        ), f"Data freshness check failed: {validator.failures}"

    def test_events_table_accessible(self, validator):
        """Test events table is accessible."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM odds.events")
        count = cursor.fetchone()[0]

        # Pass regardless of count - scraper populates data
        assert count >= 0, "events table should be queryable"

    def test_odds_snapshots_table_accessible(self, validator):
        """Test odds_snapshots table is accessible."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM odds.odds_snapshots")
        count = cursor.fetchone()[0]

        # Pass regardless of count - scraper populates data
        assert count >= 0, "odds_snapshots table should be queryable"


class TestPhase07DataQuality:
    """Tests for Phase 0.0007 data quality (if data exists)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase07OddsAPIValidator(verbose=False)

    def test_data_quality_check_passes(self, validator):
        """Test data quality validation passes."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_data_quality() == True
        ), f"Data quality check failed: {validator.failures}"

    def test_no_orphaned_snapshots(self, validator):
        """Test odds snapshots reference valid events."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM odds.odds_snapshots os
            WHERE NOT EXISTS (
                SELECT 1 FROM odds.events e
                WHERE e.event_id = os.event_id
            )
        """
        )
        orphaned_count = cursor.fetchone()[0]

        assert orphaned_count == 0, f"Found {orphaned_count} orphaned odds snapshots"

    def test_no_orphaned_scores(self, validator):
        """Test scores reference valid events."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM odds.scores s
            WHERE NOT EXISTS (
                SELECT 1 FROM odds.events e
                WHERE e.event_id = s.event_id
            )
        """
        )
        orphaned_count = cursor.fetchone()[0]

        assert orphaned_count == 0, f"Found {orphaned_count} orphaned scores"


class TestPhase07OddsCalculations:
    """Tests for odds calculation logic."""

    def test_american_odds_to_probability_positive(self):
        """Test American odds to probability conversion (positive odds)."""
        # +150 odds (underdog)
        odds = 150
        expected_prob = 100 / (150 + 100)  # 0.40 or 40%
        actual_prob = self.american_odds_to_probability(odds)
        assert abs(actual_prob - expected_prob) < 0.001

    def test_american_odds_to_probability_negative(self):
        """Test American odds to probability conversion (negative odds)."""
        # -150 odds (favorite)
        odds = -150
        expected_prob = 150 / (150 + 100)  # 0.60 or 60%
        actual_prob = self.american_odds_to_probability(odds)
        assert abs(actual_prob - expected_prob) < 0.001

    def test_american_odds_to_probability_even(self):
        """Test American odds to probability conversion (even odds)."""
        # +100 odds (even)
        odds = 100
        expected_prob = 0.5
        actual_prob = self.american_odds_to_probability(odds)
        assert abs(actual_prob - expected_prob) < 0.001

    def test_market_vig_calculation(self):
        """Test bookmaker vig calculation."""
        # Lakers -150, Celtics +130
        home_odds = -150
        away_odds = 130

        home_prob = self.american_odds_to_probability(home_odds)  # 0.60
        away_prob = self.american_odds_to_probability(away_odds)  # 0.4348

        vig = (home_prob + away_prob - 1.0) * 100

        # Vig should be positive (bookmaker edge)
        assert vig > 0, "Vig should be positive"
        assert vig < 10, "Vig should be < 10% for major markets"

    @staticmethod
    def american_odds_to_probability(odds: int) -> float:
        """Convert American odds to implied probability."""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)


class TestPhase07Integration:
    """Tests for Phase 0.0007 integration capability."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return Phase07OddsAPIValidator(verbose=False)

    def test_integration_capability_passes(self, validator):
        """Test integration capability check passes."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        assert (
            validator.validate_integration_capability() == True
        ), f"Integration capability check failed: {validator.failures}"

    def test_can_query_upcoming_events(self, validator):
        """Test ability to query upcoming events."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute(
            """
            SELECT event_id, home_team, away_team, commence_time
            FROM odds.events
            WHERE commence_time > NOW()
            ORDER BY commence_time
            LIMIT 5
        """
        )
        results = cursor.fetchall()

        # Pass regardless of count - scraper populates data
        assert results is not None, "Should be able to query upcoming events"

    def test_can_join_odds_with_bookmakers(self, validator):
        """Test ability to join odds snapshots with bookmakers."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute(
            """
            SELECT b.bookmaker_title, COUNT(*) as snapshot_count
            FROM odds.odds_snapshots os
            JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
            GROUP BY b.bookmaker_title
            LIMIT 10
        """
        )
        results = cursor.fetchall()

        # Pass regardless of count
        assert results is not None, "Should be able to join odds with bookmakers"

    def test_can_join_odds_with_markets(self, validator):
        """Test ability to join odds snapshots with market types."""
        if not validator.rds_available:
            pytest.skip("RDS connection not available")

        cursor = validator.conn.cursor()
        cursor.execute(
            """
            SELECT mt.market_name, COUNT(*) as snapshot_count
            FROM odds.odds_snapshots os
            JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
            GROUP BY mt.market_name
            LIMIT 10
        """
        )
        results = cursor.fetchall()

        # Pass regardless of count
        assert results is not None, "Should be able to join odds with market types"


class TestPhase07FullValidation:
    """Full validator run test."""

    def test_full_validator_passes(self):
        """Test full validator execution passes."""
        validator = Phase07OddsAPIValidator(verbose=False)
        passed, failed = validator.run()

        assert failed == 0, f"Validator failed {failed} checks: {validator.failures}"
        assert passed == 7, f"Expected 7 passing checks, got {passed}"
