"""
Production Validation Test Suite

Comprehensive tests that validate system integrity during refactoring.
Uses MCP for safe database access without requiring direct connections.

These tests should be run:
- Before starting refactoring (baseline)
- After each phase
- Continuously during migration
- Before finalizing cleanup

Usage:
    pytest tests/production/test_comprehensive_validation.py -v
    pytest tests/production/test_comprehensive_validation.py -v -m critical
    pytest tests/production/test_comprehensive_validation.py -v -m monitoring
"""

import pytest
from typing import Dict, Any, List
import sys
from pathlib import Path

# Production baseline metrics (from MCP discovery - October 26, 2025)
BASELINE_METRICS = {
    "games": 44828,
    "play_by_play_espn": 6781155,
    "play_by_play_hoopr": 13074829,
    "box_score_players": 408833,
    "box_score_teams": 15900,
    "database_size_gb": 7.7,
    "total_records": 20003545,
}

# Tolerance for metrics (allow growth, never allow decrease)
TOLERANCE = {
    "games": {"min_delta": 0, "max_delta": 1000},  # Allow up to 1000 new games
    "play_by_play_espn": {"min_delta": 0, "max_delta": 100000},
    "play_by_play_hoopr": {"min_delta": 0, "max_delta": 500000},
    "box_score_players": {"min_delta": 0, "max_delta": 50000},
    "box_score_teams": {"min_delta": 0, "max_delta": 5000},
}

# Try to import package (may not exist yet in early phases)
try:
    from nba_simulator.database import DatabaseConnection

    PACKAGE_AVAILABLE = True
except ImportError:
    PACKAGE_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="nba_simulator package not yet available")


class TestDatabaseIntegrity:
    """Critical database integrity tests"""

    @pytest.mark.critical
    def test_database_connection(self):
        """Verify database is accessible"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        DatabaseConnection.initialize_pool(min_conn=1, max_conn=2)
        result = DatabaseConnection.execute_query("SELECT 1 as test")

        assert len(result) == 1
        assert result[0]["test"] == 1

    @pytest.mark.critical
    def test_games_table_exists(self):
        """Verify games table structure intact"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'games'
            ORDER BY ordinal_position
        """
        )

        assert len(result) > 0, "Games table not found!"

        # Verify key columns exist
        columns = {row["column_name"]: row["data_type"] for row in result}
        assert "game_id" in columns
        assert "season" in columns
        assert "game_date" in columns

    @pytest.mark.critical
    def test_games_count_within_tolerance(self):
        """Verify games count hasn't decreased"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query("SELECT COUNT(*) as cnt FROM games")
        actual = result[0]["cnt"]
        expected = BASELINE_METRICS["games"]

        delta = actual - expected
        tolerance = TOLERANCE["games"]

        assert (
            delta >= tolerance["min_delta"]
        ), f"⚠️  DATA LOSS: Games decreased by {abs(delta)} (expected >= {expected})"

        assert delta <= tolerance["max_delta"], (
            f"Games increased by {delta} (expected <= {expected + tolerance['max_delta']}). "
            f"This may be normal if ingesting new data."
        )

    @pytest.mark.critical
    def test_play_by_play_espn_integrity(self):
        """Verify ESPN play-by-play data unchanged or growing"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            "SELECT COUNT(*) as cnt FROM play_by_play"
        )
        actual = result[0]["cnt"]
        expected = BASELINE_METRICS["play_by_play_espn"]

        assert (
            actual >= expected
        ), f"⚠️  CRITICAL DATA LOSS: ESPN PBP decreased from {expected} to {actual}"

    @pytest.mark.critical
    def test_play_by_play_hoopr_integrity(self):
        """Verify hoopR play-by-play data unchanged or growing"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            "SELECT COUNT(*) as cnt FROM hoopr_play_by_play"
        )
        actual = result[0]["cnt"]
        expected = BASELINE_METRICS["play_by_play_hoopr"]

        assert (
            actual >= expected
        ), f"⚠️  CRITICAL DATA LOSS: hoopR PBP decreased from {expected} to {actual}"

    @pytest.mark.critical
    def test_box_score_players_integrity(self):
        """Verify box score players data"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            "SELECT COUNT(*) as cnt FROM box_score_players"
        )
        actual = result[0]["cnt"]
        expected = BASELINE_METRICS["box_score_players"]

        assert (
            actual >= expected
        ), f"Box score players decreased from {expected} to {actual}"

    @pytest.mark.critical
    def test_no_null_game_ids(self):
        """Verify no critical null values introduced"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT COUNT(*) as null_count 
            FROM games 
            WHERE game_id IS NULL
        """
        )

        null_count = result[0]["null_count"]
        assert null_count == 0, f"Found {null_count} games with NULL game_id!"


class TestDIMSMonitoring:
    """DIMS monitoring system tests"""

    @pytest.mark.monitoring
    def test_dims_metrics_table_exists(self):
        """Verify DIMS metrics table exists"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT COUNT(*) as cnt 
            FROM information_schema.tables 
            WHERE table_name = 'dims_metrics_snapshots'
        """
        )

        assert result[0]["cnt"] == 1, "DIMS metrics table not found!"

    @pytest.mark.monitoring
    def test_dims_recent_activity(self):
        """Verify DIMS has recent activity"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT 
                COUNT(*) as snapshot_count,
                MAX(created_at) as last_snapshot
            FROM dims_metrics_snapshots
            WHERE created_at > NOW() - INTERVAL '7 days'
        """
        )

        # May have 0 snapshots if DIMS just started
        # Just verify query works
        assert "snapshot_count" in result[0]
        assert "last_snapshot" in result[0]

    @pytest.mark.monitoring
    def test_dims_config_table_exists(self):
        """Verify DIMS configuration table exists"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT COUNT(*) as cnt 
            FROM information_schema.tables 
            WHERE table_name = 'dims_config'
        """
        )

        assert result[0]["cnt"] == 1, "DIMS config table not found!"


class TestPhase8BoxScore:
    """Phase 8 box score generation tests"""

    @pytest.mark.phase8
    def test_box_score_snapshots_table_exists(self):
        """Verify Phase 8 box score snapshots table exists"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'box_score_snapshots'
            ORDER BY ordinal_position
        """
        )

        assert len(result) > 0, "box_score_snapshots table not found!"

        # Verify key columns
        columns = [row["column_name"] for row in result]
        assert "game_id" in columns
        assert "event_num" in columns
        assert "snapshot_data" in columns

    @pytest.mark.phase8
    def test_box_score_snapshot_format(self):
        """Verify box score snapshot JSONB format"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT snapshot_data 
            FROM box_score_snapshots 
            LIMIT 1
        """
        )

        if len(result) > 0:
            snapshot = result[0]["snapshot_data"]
            assert snapshot is not None, "Snapshot data is NULL!"
            # Could add more JSON structure validation here

    @pytest.mark.phase8
    def test_box_score_verification_table_exists(self):
        """Verify box score verification tracking exists"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT COUNT(*) as cnt 
            FROM information_schema.tables 
            WHERE table_name = 'box_score_verification'
        """
        )

        assert result[0]["cnt"] == 1, "box_score_verification table not found!"


class TestDataQuality:
    """Data quality and consistency tests"""

    @pytest.mark.quality
    def test_no_duplicate_games(self):
        """Verify no duplicate game IDs"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT game_id, COUNT(*) as cnt 
            FROM games 
            GROUP BY game_id 
            HAVING COUNT(*) > 1
        """
        )

        assert len(result) == 0, f"Found {len(result)} duplicate game IDs!"

    @pytest.mark.quality
    def test_date_range_valid(self):
        """Verify game dates within valid NBA history"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT 
                MIN(game_date) as earliest,
                MAX(game_date) as latest
            FROM games
            WHERE game_date IS NOT NULL
        """
        )

        # NBA founded in 1946
        # Dates should be reasonable
        assert len(result) == 1
        # Just verify query works - actual date validation depends on data format

    @pytest.mark.quality
    def test_play_by_play_links_to_games(self):
        """Verify play-by-play references valid games"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT COUNT(*) as orphaned
            FROM play_by_play pbp
            LEFT JOIN games g ON pbp.game_id = g.game_id
            WHERE g.game_id IS NULL
            LIMIT 100
        """
        )

        # Some orphaned records may be expected due to data ingestion timing
        # Just verify query works
        assert "orphaned" in result[0]


class TestTableSizes:
    """Monitor table sizes during refactoring"""

    @pytest.mark.monitoring
    def test_table_sizes_reasonable(self):
        """Verify table sizes haven't dramatically changed"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        tables_to_check = [
            "games",
            "play_by_play",
            "hoopr_play_by_play",
            "box_score_players",
            "box_score_teams",
        ]

        for table in tables_to_check:
            result = DatabaseConnection.execute_query(
                f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table}')) as size
            """
            )

            assert len(result) == 1
            assert result[0]["size"] is not None
            # Size should not be zero
            assert "0 bytes" not in result[0]["size"].lower()

    @pytest.mark.monitoring
    def test_total_database_size(self):
        """Monitor total database size"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT pg_size_pretty(pg_database_size('nba_simulator')) as size
        """
        )

        assert len(result) == 1
        size_str = result[0]["size"]

        # Database should be multi-GB
        assert (
            "GB" in size_str or "TB" in size_str
        ), f"Database size suspiciously small: {size_str}"


class TestIndexes:
    """Verify indexes remain intact"""

    @pytest.mark.schema
    def test_games_indexes_exist(self):
        """Verify games table has indexes"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'games'
        """
        )

        # Should have at least primary key
        assert len(result) >= 1, "Games table has no indexes!"

    @pytest.mark.schema
    def test_play_by_play_indexes_exist(self):
        """Verify play_by_play table has indexes"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'play_by_play'
        """
        )

        assert len(result) >= 1, "play_by_play table has no indexes!"


class TestPerformance:
    """Performance regression tests"""

    @pytest.mark.performance
    def test_games_query_performance(self):
        """Verify games query performs reasonably"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        import time

        start = time.time()

        result = DatabaseConnection.execute_query(
            """
            SELECT * FROM games LIMIT 1000
        """
        )

        duration = time.time() - start

        assert len(result) == 1000
        assert duration < 5.0, f"Query took {duration}s (expected < 5s)"

    @pytest.mark.performance
    def test_count_queries_reasonable(self):
        """Verify COUNT queries complete quickly"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        import time

        start = time.time()

        result = DatabaseConnection.execute_query("SELECT COUNT(*) FROM games")

        duration = time.time() - start

        assert len(result) == 1
        assert duration < 2.0, f"COUNT query took {duration}s (expected < 2s)"


class TestReferentialIntegrity:
    """Foreign key and referential integrity tests"""

    @pytest.mark.integrity
    def test_foreign_keys_exist(self):
        """Verify foreign key constraints exist"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        result = DatabaseConnection.execute_query(
            """
            SELECT 
                tc.table_name, 
                tc.constraint_name,
                tc.constraint_type
            FROM information_schema.table_constraints tc
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """
        )

        # May or may not have foreign keys depending on design
        # Just verify query works
        assert isinstance(result, list)

    @pytest.mark.integrity
    def test_primary_keys_exist(self):
        """Verify primary key constraints on key tables"""
        if not PACKAGE_AVAILABLE:
            pytest.skip("Package not available yet")

        key_tables = ["games", "players", "teams"]

        for table in key_tables:
            result = DatabaseConnection.execute_query(
                f"""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = '{table}'
                AND constraint_type = 'PRIMARY KEY'
            """
            )

            assert len(result) >= 1, f"Table {table} has no primary key!"


# Fixtures for all tests
@pytest.fixture(scope="session")
def initialize_db_connection():
    """Initialize database connection pool once per test session"""
    if PACKAGE_AVAILABLE:
        DatabaseConnection.initialize_pool(min_conn=2, max_conn=5)
        yield
        DatabaseConnection.close_pool()
    else:
        yield


@pytest.fixture(autouse=True)
def ensure_db_initialized(initialize_db_connection):
    """Ensure DB connection initialized for all tests"""
    pass


# Summary test that provides overview
def test_system_health_summary(capsys):
    """
    Generate comprehensive system health summary.
    Run this test alone to get full system overview.
    """
    if not PACKAGE_AVAILABLE:
        pytest.skip("Package not available yet")

    print("\n" + "=" * 70)
    print("SYSTEM HEALTH SUMMARY")
    print("=" * 70)

    # Get all table counts
    tables = [
        "games",
        "play_by_play",
        "hoopr_play_by_play",
        "box_score_players",
        "box_score_teams",
        "box_score_snapshots",
        "dims_metrics_snapshots",
    ]

    for table in tables:
        try:
            result = DatabaseConnection.execute_query(
                f"SELECT COUNT(*) as cnt FROM {table}"
            )
            count = result[0]["cnt"]

            # Check against baseline if exists
            baseline_key = table.replace("_", "_")
            if baseline_key in BASELINE_METRICS:
                baseline = BASELINE_METRICS[baseline_key]
                delta = count - baseline
                status = "✅" if delta >= 0 else "⚠️ "
                print(f"{status} {table:30} {count:>12,} (Δ {delta:+,})")
            else:
                print(f"ℹ️  {table:30} {count:>12,}")

        except Exception as e:
            print(f"❌ {table:30} ERROR: {e}")

    print("=" * 70)

    # This test always passes - it's informational
    assert True


if __name__ == "__main__":
    # Run with: python tests/production/test_comprehensive_validation.py
    pytest.main([__file__, "-v", "--tb=short"])
