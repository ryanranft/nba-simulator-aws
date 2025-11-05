"""
NBA Simulator AWS - Root pytest Configuration
Shared fixtures and test utilities for all test suites
Enhanced for Phase 5: Comprehensive Testing Infrastructure
"""

import pytest
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock


# ============================================================================
# PROJECT CONFIGURATION
# ============================================================================


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Return the test data directory."""
    return project_root / "tests" / "fixtures" / "sample_data"


# ============================================================================
# AWS CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def aws_region():
    """Default AWS region for tests."""
    return os.getenv("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def s3_bucket_name():
    """S3 bucket name for tests."""
    return os.getenv("S3_BUCKET", "nba-sim-raw-data-lake")


@pytest.fixture
def mock_s3_client():
    """Mock boto3 S3 client."""
    mock = MagicMock()
    mock.put_object.return_value = {"ETag": '"mock-etag"'}
    mock.get_object.return_value = {"Body": Mock(read=lambda: b'{"test": "data"}')}
    mock.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "test/file1.json", "Size": 1024},
            {"Key": "test/file2.json", "Size": 2048},
        ]
    }
    return mock


# ============================================================================
# DATABASE CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def rds_config():
    """RDS database configuration for integration tests."""
    return {
        "host": os.getenv("RDS_HOST", "localhost"),
        "port": int(os.getenv("RDS_PORT", "5432")),
        "database": os.getenv("RDS_DATABASE", "nba_simulator"),
        "username": os.getenv("RDS_USERNAME", "postgres"),
        "password": os.getenv("RDS_PASSWORD", ""),
    }


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    mock_cursor.rowcount = 0
    return mock_conn


@pytest.fixture
def mock_db_pool():
    """Mock database connection pool."""
    mock_pool = MagicMock()
    mock_pool.getconn.return_value = MagicMock()
    return mock_pool


# ============================================================================
# NBA DATA FIXTURES - GAMES
# ============================================================================


@pytest.fixture
def sample_game_id():
    """Sample game ID for testing."""
    return "401584876"


@pytest.fixture
def sample_game_data():
    """Sample game data structure."""
    return {
        "game_id": "401584876",
        "game_date": "2024-10-23",
        "season": "2024-25",
        "home_team": "BOS",
        "away_team": "NYK",
        "home_score": 108,
        "away_score": 104,
        "status": "Final",
        "venue": "TD Garden",
    }


@pytest.fixture
def sample_games_df():
    """Sample games DataFrame for testing."""
    data = {
        "game_id": ["401584876", "401584877", "401584878"],
        "game_date": ["2024-10-23", "2024-10-23", "2024-10-24"],
        "season": ["2024-25", "2024-25", "2024-25"],
        "home_team": ["BOS", "LAL", "GSW"],
        "away_team": ["NYK", "DEN", "PHX"],
        "home_score": [108, 115, 120],
        "away_score": [104, 110, 118],
        "status": ["Final", "Final", "Final"],
    }
    return pd.DataFrame(data)


# ============================================================================
# NBA DATA FIXTURES - PLAYERS
# ============================================================================


@pytest.fixture
def sample_player_id():
    """Sample player ID for testing."""
    return "2544"  # LeBron James


@pytest.fixture
def sample_player_data():
    """Sample player data structure."""
    return {
        "player_id": "2544",
        "player_name": "LeBron James",
        "team": "LAL",
        "position": "F",
        "height": "6-9",
        "weight": "250",
        "birth_date": "1984-12-30",
    }


@pytest.fixture
def sample_players_df():
    """Sample players DataFrame for testing."""
    data = {
        "player_id": ["2544", "1966", "3975"],
        "player_name": ["LeBron James", "Stephen Curry", "Kevin Durant"],
        "team": ["LAL", "GSW", "PHX"],
        "position": ["F", "G", "F"],
        "height": ["6-9", "6-2", "6-10"],
        "weight": ["250", "185", "240"],
    }
    return pd.DataFrame(data)


# ============================================================================
# NBA DATA FIXTURES - TEAMS
# ============================================================================


@pytest.fixture
def sample_team_data():
    """Sample team data structure."""
    return {
        "team_id": "LAL",
        "team_name": "Los Angeles Lakers",
        "abbreviation": "LAL",
        "conference": "Western",
        "division": "Pacific",
    }


@pytest.fixture
def sample_teams_df():
    """Sample teams DataFrame for testing."""
    data = {
        "team_id": ["LAL", "BOS", "GSW", "NYK"],
        "team_name": [
            "Los Angeles Lakers",
            "Boston Celtics",
            "Golden State Warriors",
            "New York Knicks",
        ],
        "abbreviation": ["LAL", "BOS", "GSW", "NYK"],
        "conference": ["Western", "Eastern", "Western", "Eastern"],
        "division": ["Pacific", "Atlantic", "Pacific", "Atlantic"],
    }
    return pd.DataFrame(data)


# ============================================================================
# NBA DATA FIXTURES - PLAY-BY-PLAY
# ============================================================================


@pytest.fixture
def sample_pbp_event():
    """Sample play-by-play event."""
    return {
        "game_id": "401584876",
        "event_id": "1",
        "period": 1,
        "clock": "12:00",
        "team": "BOS",
        "player": "Jayson Tatum",
        "event_type": "shot",
        "description": "Jayson Tatum makes 2-pt jump shot",
        "score_home": 2,
        "score_away": 0,
    }


@pytest.fixture
def sample_pbp_df():
    """Sample play-by-play DataFrame."""
    data = {
        "game_id": ["401584876"] * 5,
        "event_id": ["1", "2", "3", "4", "5"],
        "period": [1, 1, 1, 1, 1],
        "clock": ["12:00", "11:45", "11:30", "11:15", "11:00"],
        "team": ["BOS", "NYK", "BOS", "BOS", "NYK"],
        "event_type": ["shot", "shot", "rebound", "shot", "shot"],
        "score_home": [2, 2, 2, 4, 4],
        "score_away": [0, 2, 2, 2, 4],
    }
    return pd.DataFrame(data)


# ============================================================================
# NBA DATA FIXTURES - BOX SCORES
# ============================================================================


@pytest.fixture
def sample_box_score():
    """Sample box score data."""
    return {
        "game_id": "401584876",
        "player_id": "2544",
        "player_name": "LeBron James",
        "team": "LAL",
        "minutes": 35,
        "points": 28,
        "rebounds": 8,
        "assists": 6,
        "steals": 2,
        "blocks": 1,
        "turnovers": 3,
        "fgm": 10,
        "fga": 20,
        "fg3m": 2,
        "fg3a": 6,
        "ftm": 6,
        "fta": 8,
    }


@pytest.fixture
def sample_box_scores_df():
    """Sample box scores DataFrame."""
    data = {
        "game_id": ["401584876"] * 3,
        "player_id": ["2544", "1966", "3975"],
        "player_name": ["LeBron James", "Stephen Curry", "Kevin Durant"],
        "team": ["LAL", "GSW", "PHX"],
        "minutes": [35, 38, 36],
        "points": [28, 32, 30],
        "rebounds": [8, 5, 9],
        "assists": [6, 8, 5],
        "fgm": [10, 11, 10],
        "fga": [20, 22, 18],
    }
    return pd.DataFrame(data)


# ============================================================================
# ML FIXTURES - FEATURES & MODELS
# ============================================================================


@pytest.fixture
def sample_features_df():
    """Sample features DataFrame for ML."""
    np.random.seed(42)
    data = {
        "home_offensive_rating": np.random.uniform(100, 120, 100),
        "away_offensive_rating": np.random.uniform(100, 120, 100),
        "home_defensive_rating": np.random.uniform(100, 120, 100),
        "away_defensive_rating": np.random.uniform(100, 120, 100),
        "home_pace": np.random.uniform(95, 105, 100),
        "away_pace": np.random.uniform(95, 105, 100),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_labels():
    """Sample labels for ML (binary: home team win/loss)."""
    np.random.seed(42)
    return np.random.randint(0, 2, 100)


@pytest.fixture
def sample_scores_df():
    """Sample scores DataFrame for ML."""
    np.random.seed(42)
    data = {
        "home_score": np.random.randint(90, 130, 100),
        "away_score": np.random.randint(90, 130, 100),
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_ml_model():
    """Mock ML model for testing."""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1, 0, 1, 0, 1])
    mock_model.predict_proba.return_value = np.array(
        [[0.3, 0.7], [0.6, 0.4], [0.2, 0.8], [0.7, 0.3], [0.4, 0.6]]
    )
    mock_model.score.return_value = 0.85
    return mock_model


# ============================================================================
# API MOCK RESPONSES
# ============================================================================


@pytest.fixture
def mock_espn_api_response():
    """Mock ESPN API response."""
    return {
        "id": "401584876",
        "date": "2024-10-23T19:30Z",
        "name": "New York Knicks at Boston Celtics",
        "competitions": [
            {
                "competitors": [
                    {
                        "team": {"abbreviation": "BOS"},
                        "score": "108",
                        "homeAway": "home",
                    },
                    {
                        "team": {"abbreviation": "NYK"},
                        "score": "104",
                        "homeAway": "away",
                    },
                ],
                "status": {"type": {"completed": True}},
            }
        ],
    }


@pytest.fixture
def mock_basketball_reference_html():
    """Mock Basketball Reference HTML response."""
    return """
    <html>
        <body>
            <table id="box-score">
                <tr>
                    <td>LeBron James</td>
                    <td>35</td>
                    <td>28</td>
                    <td>8</td>
                    <td>6</td>
                </tr>
            </table>
        </body>
    </html>
    """


# ============================================================================
# ETL FIXTURES - SCRAPERS & TRANSFORMERS
# ============================================================================


@pytest.fixture
def mock_scraper():
    """Mock base scraper for testing."""
    mock = MagicMock()
    mock.scrape.return_value = {"data": "sample"}
    mock.is_rate_limited.return_value = False
    return mock


@pytest.fixture
def mock_transformer():
    """Mock base transformer for testing."""
    mock = MagicMock()
    mock.transform.return_value = pd.DataFrame({"col": [1, 2, 3]})
    return mock


@pytest.fixture
def mock_loader():
    """Mock base loader for testing."""
    mock = MagicMock()
    mock.load.return_value = {"success": True, "records_loaded": 100}
    return mock


# ============================================================================
# AGENT & WORKFLOW FIXTURES
# ============================================================================


@pytest.fixture
def mock_agent():
    """Mock autonomous agent for testing."""
    mock = MagicMock()
    mock.run.return_value = {"status": "success", "actions_taken": 5}
    mock.get_status.return_value = "ready"
    return mock


@pytest.fixture
def mock_workflow():
    """Mock workflow orchestrator for testing."""
    mock = MagicMock()
    mock.execute.return_value = {
        "status": "completed",
        "steps_executed": 10,
        "duration": 120,
    }
    return mock


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def sample_season():
    """Sample season for testing."""
    return "2024-25"


@pytest.fixture
def sample_date_range():
    """Sample date range for testing."""
    return {"start_date": "2024-10-23", "end_date": "2024-10-30"}


@pytest.fixture
def test_config():
    """Test configuration dictionary."""
    return {
        "aws": {"region": "us-east-1", "s3_bucket": "nba-sim-raw-data-lake"},
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "nba_simulator_test",
        },
        "etl": {"batch_size": 100, "max_retries": 3, "rate_limit": 10},
    }


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring external resources"
    )
    config.addinivalue_line("markers", "slow: Tests that take >1 second to run")
    config.addinivalue_line("markers", "database: Tests requiring database connection")
    config.addinivalue_line("markers", "s3: Tests requiring S3 access")
    config.addinivalue_line("markers", "api: Tests requiring external API calls")
    config.addinivalue_line("markers", "ml: Machine learning tests")


def pytest_collection_modifyitems(config, items):
    """Automatically skip integration tests if resources not configured."""
    # Skip integration tests if AWS credentials not configured
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        skip_aws = pytest.mark.skip(reason="AWS credentials not configured")
        for item in items:
            if "integration" in item.keywords or "s3" in item.keywords:
                item.add_marker(skip_aws)

    # Skip database tests if database not configured
    if not os.getenv("RDS_HOST"):
        skip_db = pytest.mark.skip(reason="Database not configured")
        for item in items:
            if "database" in item.keywords:
                item.add_marker(skip_db)


# ============================================================================
# TEST UTILITIES
# ============================================================================


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary directory for test files."""
    test_dir = tmp_path / "nba_test"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_json_file(temp_test_dir):
    """Create a sample JSON file for testing."""
    json_file = temp_test_dir / "sample.json"
    data = {"game_id": "401584876", "home_team": "BOS", "away_team": "NYK"}
    json_file.write_text(json.dumps(data, indent=2))
    return json_file


@pytest.fixture(autouse=True)
def reset_environment_variables():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================


@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = datetime.now()

        def stop(self):
            self.end_time = datetime.now()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return None

    return Timer()
