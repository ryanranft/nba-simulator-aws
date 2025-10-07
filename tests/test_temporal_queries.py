"""
Test suite for NBA Temporal Panel Data System

Tests temporal query functionality, data precision, snapshot accuracy,
and age calculations at exact timestamps.

Run with: pytest tests/test_temporal_queries.py -v
"""

import pytest
import psycopg2
from datetime import datetime, timedelta
import pytz


# Test Configuration
TEST_DB_CONFIG = {
    'host': 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com',
    'database': 'nba_simulator',
    'user': 'your_user',  # Update with actual credentials
    'password': 'your_password'
}

TEST_PLAYER_ID = 977  # Kobe Bryant (example)
TEST_PLAYER_NAME = "Kobe Bryant"
TEST_GAME_ID = "401234567"  # Example game ID
TEST_TIMESTAMP = "2016-06-19T19:02:34.560"  # Kobe's last game


# Fixtures
@pytest.fixture(scope="module")
def db_connection():
    """Create database connection for all tests."""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def test_cursor(db_connection):
    """Create cursor for database queries."""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


# Helper Functions
def parse_timestamp(timestamp_str, timezone='America/Chicago'):
    """Convert timestamp string to timezone-aware datetime."""
    tz = pytz.timezone(timezone)
    dt = datetime.fromisoformat(timestamp_str)
    return tz.localize(dt) if dt.tzinfo is None else dt.astimezone(tz)


class TestTemporalDataAvailability:
    """Test that temporal tables exist and contain data."""

    def test_temporal_events_table_exists(self, test_cursor):
        """Verify temporal_events table exists."""
        test_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'temporal_events'
            );
        """)
        assert test_cursor.fetchone()[0], "temporal_events table does not exist"

    def test_player_snapshots_table_exists(self, test_cursor):
        """Verify player_snapshots table exists."""
        test_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'player_snapshots'
            );
        """)
        assert test_cursor.fetchone()[0], "player_snapshots table does not exist"

    def test_game_states_table_exists(self, test_cursor):
        """Verify game_states table exists."""
        test_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'game_states'
            );
        """)
        assert test_cursor.fetchone()[0], "game_states table does not exist"

    def test_player_biographical_table_exists(self, test_cursor):
        """Verify player_biographical table exists."""
        test_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'player_biographical'
            );
        """)
        assert test_cursor.fetchone()[0], "player_biographical table does not exist"

    def test_temporal_events_has_data(self, test_cursor):
        """Verify temporal_events table contains data."""
        test_cursor.execute("SELECT COUNT(*) FROM temporal_events;")
        count = test_cursor.fetchone()[0]
        assert count > 0, f"temporal_events table is empty (expected > 0 rows, got {count})"

    def test_player_snapshots_has_data(self, test_cursor):
        """Verify player_snapshots table contains data."""
        test_cursor.execute("SELECT COUNT(*) FROM player_snapshots;")
        count = test_cursor.fetchone()[0]
        assert count > 0, f"player_snapshots table is empty (expected > 0 rows, got {count})"


class TestBRINIndexes:
    """Test BRIN indexes for temporal queries."""

    def test_temporal_events_brin_index_exists(self, test_cursor):
        """Verify BRIN index on temporal_events.wall_clock_utc."""
        test_cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'temporal_events'
              AND indexname LIKE '%brin%';
        """)
        indexes = test_cursor.fetchall()
        assert len(indexes) > 0, "BRIN index on temporal_events not found"

    def test_player_snapshots_brin_index_exists(self, test_cursor):
        """Verify BRIN index on player_snapshots.snapshot_time."""
        test_cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'player_snapshots'
              AND indexname LIKE '%brin%';
        """)
        indexes = test_cursor.fetchall()
        assert len(indexes) > 0, "BRIN index on player_snapshots not found"


class TestStoredProcedures:
    """Test stored procedures for snapshot queries."""

    def test_get_player_snapshot_function_exists(self, test_cursor):
        """Verify get_player_snapshot_at_time() function exists."""
        test_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'get_player_snapshot_at_time'
            );
        """)
        assert test_cursor.fetchone()[0], "get_player_snapshot_at_time() function does not exist"

    def test_calculate_player_age_function_exists(self, test_cursor):
        """Verify calculate_player_age() function exists."""
        test_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'calculate_player_age'
            );
        """)
        assert test_cursor.fetchone()[0], "calculate_player_age() function does not exist"


class TestSnapshotQueries:
    """Test snapshot query accuracy and performance."""

    def test_get_player_snapshot_at_exact_time(self, test_cursor):
        """Test retrieving player snapshot at exact timestamp."""
        timestamp = parse_timestamp(TEST_TIMESTAMP)

        test_cursor.execute("""
            SELECT
                snapshot_time,
                games_played,
                career_points,
                career_rebounds,
                career_assists
            FROM
                get_player_snapshot_at_time(%s, %s)
        """, (TEST_PLAYER_ID, timestamp))

        result = test_cursor.fetchone()
        assert result is not None, f"No snapshot found for player {TEST_PLAYER_ID} at {timestamp}"

        snapshot_time, games, points, rebounds, assists = result
        assert snapshot_time <= timestamp, "Snapshot time should be <= requested time"
        assert games > 0, f"Expected games_played > 0, got {games}"
        assert points > 0, f"Expected career_points > 0, got {points}"

    def test_snapshot_query_performance(self, test_cursor):
        """Test that snapshot query completes within 5 seconds."""
        timestamp = parse_timestamp(TEST_TIMESTAMP)

        import time
        start = time.time()

        test_cursor.execute("""
            SELECT * FROM get_player_snapshot_at_time(%s, %s)
        """, (TEST_PLAYER_ID, timestamp))

        test_cursor.fetchone()
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Snapshot query took {elapsed:.2f}s (expected < 5s)"

    def test_snapshot_monotonicity(self, test_cursor):
        """Test that player stats never decrease over time (career cumulative)."""
        # Get snapshot at two different times
        time1 = parse_timestamp("2016-06-19T18:00:00")
        time2 = parse_timestamp("2016-06-19T22:00:00")

        test_cursor.execute("""
            SELECT career_points FROM get_player_snapshot_at_time(%s, %s)
        """, (TEST_PLAYER_ID, time1))
        points1 = test_cursor.fetchone()[0]

        test_cursor.execute("""
            SELECT career_points FROM get_player_snapshot_at_time(%s, %s)
        """, (TEST_PLAYER_ID, time2))
        points2 = test_cursor.fetchone()[0]

        assert points2 >= points1, f"Career points decreased over time ({points1} -> {points2})"


class TestPrecisionLevels:
    """Test data precision tracking and filtering."""

    def test_precision_level_values(self, test_cursor):
        """Verify precision_level values are valid."""
        test_cursor.execute("""
            SELECT DISTINCT precision_level
            FROM temporal_events
            WHERE precision_level NOT IN ('millisecond', 'second', 'minute', 'game', 'unknown');
        """)
        invalid = test_cursor.fetchall()
        assert len(invalid) == 0, f"Found invalid precision_level values: {invalid}"

    def test_precision_by_era(self, test_cursor):
        """Test that precision levels match expected eras."""
        # Modern data (2020+) should have second or better precision
        test_cursor.execute("""
            SELECT COUNT(*)
            FROM temporal_events
            WHERE wall_clock_utc >= '2020-01-01'
              AND precision_level IN ('millisecond', 'second');
        """)
        modern_count = test_cursor.fetchone()[0]

        test_cursor.execute("""
            SELECT COUNT(*)
            FROM temporal_events
            WHERE wall_clock_utc >= '2020-01-01';
        """)
        total_modern = test_cursor.fetchone()[0]

        if total_modern > 0:
            precision_pct = (modern_count / total_modern) * 100
            assert precision_pct > 80, f"Modern data precision too low ({precision_pct:.1f}%)"

    def test_data_source_tracking(self, test_cursor):
        """Verify data_source field is populated."""
        test_cursor.execute("""
            SELECT DISTINCT data_source
            FROM temporal_events
            WHERE data_source IS NOT NULL;
        """)
        sources = [row[0] for row in test_cursor.fetchall()]

        valid_sources = {'nba_live', 'nba_stats', 'espn', 'hoopr', 'basketball_ref', 'kaggle'}
        invalid_sources = set(sources) - valid_sources

        assert len(invalid_sources) == 0, f"Found invalid data sources: {invalid_sources}"


class TestAgeCalculations:
    """Test player age calculations at exact timestamps."""

    def test_birth_date_available(self, test_cursor):
        """Verify test player has birth date."""
        test_cursor.execute("""
            SELECT birth_date, birth_date_precision
            FROM player_biographical
            WHERE player_id = %s
        """, (TEST_PLAYER_ID,))

        result = test_cursor.fetchone()
        assert result is not None, f"No birth date for player {TEST_PLAYER_ID}"

        birth_date, precision = result
        assert birth_date is not None, "Birth date is NULL"
        assert precision in ('day', 'month', 'year'), f"Invalid precision: {precision}"

    def test_calculate_age_at_timestamp(self, test_cursor):
        """Test age calculation at specific timestamp."""
        timestamp = parse_timestamp(TEST_TIMESTAMP)

        test_cursor.execute("""
            SELECT calculate_player_age(%s, %s)
        """, (TEST_PLAYER_ID, timestamp))

        age_str = test_cursor.fetchone()[0]
        assert age_str is not None, "Age calculation returned NULL"
        assert "years" in age_str, f"Age string malformed: {age_str}"

    def test_age_precision_by_birth_date_precision(self, test_cursor):
        """Test that age precision matches birth date precision."""
        test_cursor.execute("""
            SELECT
                pb.birth_date_precision,
                calculate_player_age(pb.player_id, '2020-01-01 00:00:00'::TIMESTAMPTZ)
            FROM
                player_biographical pb
            WHERE
                pb.birth_date IS NOT NULL
            LIMIT 10;
        """)

        results = test_cursor.fetchall()
        assert len(results) > 0, "No players with birth dates found"

        for precision, age_str in results:
            if precision == 'day':
                assert "days" in age_str or "hours" in age_str, \
                    f"Day precision should show days/hours, got: {age_str}"


class TestTimestampConsistency:
    """Test timestamp consistency across tables."""

    def test_wall_clock_vs_game_clock(self, test_cursor):
        """Verify wall clock and game clock relationship."""
        test_cursor.execute("""
            SELECT
                wall_clock_utc,
                game_clock_seconds,
                quarter
            FROM
                temporal_events
            WHERE
                game_clock_seconds IS NOT NULL
                AND quarter IS NOT NULL
            LIMIT 100;
        """)

        events = test_cursor.fetchall()
        assert len(events) > 0, "No events with game clock data"

        for wall_clock, game_clock, quarter in events:
            assert 0 <= game_clock <= 720, \
                f"Invalid game_clock_seconds: {game_clock} (expected 0-720)"
            assert 1 <= quarter <= 4 or quarter > 4, \
                f"Invalid quarter: {quarter}"

    def test_timestamp_timezone_aware(self, test_cursor):
        """Verify timestamps are timezone-aware (TIMESTAMPTZ)."""
        test_cursor.execute("""
            SELECT pg_typeof(wall_clock_utc)
            FROM temporal_events
            LIMIT 1;
        """)

        type_name = test_cursor.fetchone()[0]
        assert "timestamp with time zone" in type_name.lower(), \
            f"wall_clock_utc should be TIMESTAMPTZ, got {type_name}"


class TestGameStateReconstruction:
    """Test game state reconstruction at timestamps."""

    def test_game_state_at_timestamp(self, test_cursor):
        """Test retrieving game state at specific timestamp."""
        test_cursor.execute("""
            SELECT
                g.game_id,
                gs.state_time,
                gs.current_score_home,
                gs.current_score_away,
                gs.quarter
            FROM
                games g
            JOIN
                game_states gs ON g.game_id = gs.game_id
            WHERE
                gs.state_time = (
                    SELECT MAX(state_time)
                    FROM game_states
                    WHERE game_id = g.game_id
                      AND state_time <= '2023-03-15 21:00:00-04:00'::TIMESTAMPTZ
                )
            LIMIT 5;
        """)

        results = test_cursor.fetchall()
        if len(results) > 0:
            for game_id, state_time, home, away, quarter in results:
                assert home >= 0, f"Invalid home score: {home}"
                assert away >= 0, f"Invalid away score: {away}"
                assert 1 <= quarter <= 4 or quarter > 4, f"Invalid quarter: {quarter}"


class TestDataQualityValidation:
    """Test data quality flags and cross-source validation."""

    def test_no_duplicate_events(self, test_cursor):
        """Verify no duplicate events at same timestamp."""
        test_cursor.execute("""
            SELECT
                game_id,
                player_id,
                wall_clock_utc,
                COUNT(*)
            FROM
                temporal_events
            GROUP BY
                game_id, player_id, wall_clock_utc
            HAVING
                COUNT(*) > 1
            LIMIT 10;
        """)

        duplicates = test_cursor.fetchall()
        assert len(duplicates) == 0, \
            f"Found {len(duplicates)} duplicate events: {duplicates}"

    def test_snapshot_consistency(self, test_cursor):
        """Test that snapshots are consistent with raw events."""
        # Get snapshot career points
        test_cursor.execute("""
            SELECT career_points
            FROM player_snapshots
            WHERE player_id = %s
            ORDER BY snapshot_time DESC
            LIMIT 1;
        """, (TEST_PLAYER_ID,))

        snapshot_points = test_cursor.fetchone()

        # Get sum of all event points
        test_cursor.execute("""
            SELECT SUM((event_data->>'points')::INTEGER)
            FROM temporal_events
            WHERE player_id = %s
              AND event_type IN ('made_shot', 'free_throw');
        """, (TEST_PLAYER_ID,))

        event_sum = test_cursor.fetchone()

        if snapshot_points and event_sum:
            # Allow 5% tolerance for data discrepancies
            diff_pct = abs(snapshot_points[0] - event_sum[0]) / snapshot_points[0] * 100
            assert diff_pct < 5, \
                f"Snapshot vs events mismatch: {snapshot_points[0]} vs {event_sum[0]} ({diff_pct:.1f}%)"


class TestPerformanceBenchmarks:
    """Test query performance benchmarks."""

    def test_time_range_query_performance(self, test_cursor):
        """Test time-range query performance (BRIN index benefit)."""
        import time

        start = time.time()
        test_cursor.execute("""
            SELECT COUNT(*)
            FROM temporal_events
            WHERE wall_clock_utc BETWEEN '2023-01-01' AND '2023-01-31'
        """)
        test_cursor.fetchone()
        elapsed = time.time() - start

        assert elapsed < 10.0, f"Time-range query too slow: {elapsed:.2f}s (expected < 10s)"

    def test_player_career_aggregation_performance(self, test_cursor):
        """Test full career aggregation performance."""
        import time

        start = time.time()
        test_cursor.execute("""
            SELECT
                COUNT(*) AS games,
                SUM((event_data->>'points')::INTEGER) AS points
            FROM
                temporal_events
            WHERE
                player_id = %s
        """, (TEST_PLAYER_ID,))
        test_cursor.fetchone()
        elapsed = time.time() - start

        assert elapsed < 15.0, \
            f"Career aggregation too slow: {elapsed:.2f}s (expected < 15s)"


# Test Suite Summary
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
