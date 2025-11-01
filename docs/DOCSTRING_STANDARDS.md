# Python Docstring Standards

**Version:** 1.0.0
**Last Updated:** October 31, 2025
**Style:** Google Python Style Guide
**Enforcement:** pydocstyle (pre-commit hooks)

---

## Table of Contents

- [Overview](#overview)
- [Google Style Docstrings](#google-style-docstrings)
- [Module Docstrings](#module-docstrings)
- [Class Docstrings](#class-docstrings)
- [Function/Method Docstrings](#functionmethod-docstrings)
- [Type Hints](#type-hints)
- [Examples by Use Case](#examples-by-use-case)
- [Common Patterns](#common-patterns)
- [Enforcement & Tools](#enforcement--tools)
- [Migration Guide](#migration-guide)

---

## Overview

### Why Docstrings Matter

Good docstrings:
- ✅ **Help developers** understand code quickly
- ✅ **Enable auto-generated** documentation (Sphinx)
- ✅ **Improve IDE support** (autocomplete, tooltips)
- ✅ **Reduce bugs** by clarifying expectations
- ✅ **Support onboarding** for new team members
- ✅ **Aid LLMs** (like Claude Code) in understanding context

### Our Standard: Google Style

We use **Google Python Style Guide** docstrings because:
- ✅ Clean, readable format
- ✅ Well-supported by tools (Sphinx Napoleon)
- ✅ Widely adopted in Python community
- ✅ Easy to learn and write

**Rejected alternatives:**
- ❌ **NumPy style** - Too verbose for our use case
- ❌ **reStructuredText** - Harder to read in code
- ❌ **Epytext** - Outdated, poor tooling

---

## Google Style Docstrings

### Basic Structure

```python
def function_name(param1, param2):
    """One-line summary (imperative mood, ends with period).

    More detailed description if needed. Can span multiple paragraphs.
    Explain the purpose, behavior, and any important context.

    Args:
        param1: Description of param1 (type inferred from type hints)
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ErrorType: Description of when this error is raised

    Examples:
        >>> function_name(1, 2)
        3

    Note:
        Additional notes or warnings

    See Also:
        related_function(): Description of related function
    """
    pass
```

### Key Principles

1. **One-line summary:**
   - Use imperative mood ("Extract data" not "Extracts data")
   - Be concise but descriptive
   - End with a period

2. **Blank line after summary:**
   - Separate summary from detailed description

3. **Detailed description (optional):**
   - Explain behavior, edge cases, context
   - Use multiple paragraphs if needed

4. **Sections in order:**
   - Args
   - Returns
   - Yields (for generators)
   - Raises
   - Examples
   - Note/Warning
   - See Also

---

## Module Docstrings

**Location:** Top of file, after shebang and before imports

**Purpose:** Describe what the module does and how to use it

```python
#!/usr/bin/env python3
"""Data extraction utilities for NBA Simulator.

This module provides functions for extracting and transforming NBA game data
from multiple sources (ESPN, NBA API, Basketball Reference, hoopR). It handles
data validation, error recovery, and S3 upload.

Typical usage example:

    from nba_simulator.etl import extract_game_data

    game_data = extract_game_data(
        game_id=401584866,
        source='espn',
        validate=True
    )

Key Features:
    - Multi-source data extraction with automatic fallback
    - Built-in data validation and quality checks
    - Automatic retry on transient failures
    - S3 upload with deduplication

Dependencies:
    - boto3: AWS SDK for S3 operations
    - requests: HTTP library for API calls
    - pandas: Data manipulation

See Also:
    - scripts/etl/basketball_reference_async_scraper.py
    - docs/DATA_STRUCTURE_GUIDE.md
"""

import boto3
import requests
# ... rest of imports
```

### When to Include Module Docstrings

**Always include:**
- ✅ Public-facing modules
- ✅ Complex modules (>200 lines)
- ✅ Modules with non-obvious purpose
- ✅ Entry point scripts

**Can skip:**
- ⭕ Simple utility modules (obvious purpose)
- ⭕ Test files (purpose is clear from filename)
- ⭕ `__init__.py` files (unless exporting public API)

---

## Class Docstrings

**Location:** Immediately after class definition

**Purpose:** Describe the class's purpose, attributes, and usage

```python
class DataCollectionOrchestrator:
    """Orchestrates multi-source NBA data collection tasks.

    This class manages the execution of data collection tasks from various
    sources (ESPN, NBA API, Basketball Reference). It handles task queuing,
    priority scheduling, rate limiting, and error recovery.

    The orchestrator maintains a priority queue of tasks and executes them
    based on configurable scheduling policies. It supports concurrent execution
    with rate limit coordination across scrapers.

    Attributes:
        config: Configuration dictionary loaded from YAML
        task_queue: PriorityQueue of pending tasks
        active_scrapers: Set of currently running scraper PIDs
        stats: TaskStatistics object tracking success/failure rates
        rate_limiter: GlobalRateLimitCoordinator instance

    Example:
        >>> orchestrator = DataCollectionOrchestrator(config_path='config.yaml')
        >>> orchestrator.load_tasks('gaps.json')
        >>> orchestrator.execute_all_tasks()
        Completed 45/50 tasks (90% success rate)

    Note:
        This class is thread-safe for reading task status, but task execution
        should not be called concurrently from multiple threads.

    See Also:
        scraper_orchestrator.py: Implementation details
        autonomous_loop.py: Integration with autonomous system
    """

    def __init__(self, config_path: str):
        """Initialize the orchestrator with configuration.

        Args:
            config_path: Path to YAML configuration file

        Raises:
            FileNotFoundError: If config_path does not exist
            yaml.YAMLError: If config file is malformed
        """
        pass
```

### Class Attributes Documentation

**Document public attributes:**
```python
class Player:
    """Represents an NBA player with career statistics.

    Attributes:
        player_id: Unique NBA player identifier (integer)
        name: Full player name (e.g., "LeBron James")
        position: Primary position ('PG', 'SG', 'SF', 'PF', 'C')
        team: Current team abbreviation (e.g., 'LAL') or None if retired
        stats: PlayerStats object containing career aggregates
        birth_date: Player birth date (datetime.date object)
    """

    def __init__(self, player_id: int, name: str):
        self.player_id = player_id
        self.name = name
        self.position = None
        self.team = None
        self.stats = PlayerStats()
        self.birth_date = None
```

---

## Function/Method Docstrings

### Standard Function

```python
def extract_game_data(
    game_id: int,
    source: str = "espn",
    validate: bool = True,
    retry_count: int = 3
) -> dict:
    """Extract raw game data from specified source.

    Retrieves complete game data including play-by-play, box scores,
    and metadata. Supports multiple data sources with automatic fallback
    if the primary source fails. Data is validated if validate=True.

    The function implements exponential backoff retry logic for transient
    failures (HTTP 5xx, network timeouts). It caches successful responses
    to reduce API load on subsequent requests for the same game.

    Args:
        game_id: NBA game identifier (e.g., 401584866). Must be a valid
            integer from the specified source's game ID system.
        source: Data source name. Supported values:
            - 'espn': ESPN API (default, most reliable)
            - 'nba_api': Official NBA Stats API
            - 'hoopr': hoopR R package data
            - 'basketball_reference': Basketball Reference scraper
        validate: If True, runs data quality checks before returning.
            Validation includes schema checks, null value detection, and
            logical consistency (e.g., quarters sum to final score).
        retry_count: Number of retry attempts for transient failures.
            Set to 0 to disable retries. Default: 3.

    Returns:
        Dictionary containing game data with the following structure:
            {
                'game_id': int,
                'date': datetime,
                'home_team': str (3-letter abbreviation),
                'away_team': str (3-letter abbreviation),
                'play_by_play': list[dict] (all game events),
                'box_score': dict (final statistics),
                'metadata': dict (venue, attendance, officials)
            }

        If validation is enabled and fails, returns dict with 'validation_errors'
        key containing list of error messages.

    Raises:
        ValueError: If game_id is invalid (<=0) or source is unknown.
        requests.HTTPError: If API request fails after all retries.
        DataQualityError: If extracted data fails critical validation checks
            (only raised if validate=True and errors are critical).

    Examples:
        Extract game from ESPN (default):
        >>> game_data = extract_game_data(401584866)
        >>> print(game_data['home_team'])
        'LAL'

        Extract from specific source with no validation:
        >>> game_data = extract_game_data(
        ...     game_id=401584866,
        ...     source='nba_api',
        ...     validate=False
        ... )
        >>> len(game_data['play_by_play'])
        342

        Handle validation errors:
        >>> game_data = extract_game_data(401584866, validate=True)
        >>> if 'validation_errors' in game_data:
        ...     print(f"Errors: {game_data['validation_errors']}")

    Note:
        - Automatically caches results for 24 hours to reduce API calls
        - Retries use exponential backoff: 1s, 2s, 4s, 8s, ...
        - Falls back to alternate source if primary completely fails
        - Rate limiting applied: max 60 requests/minute per source

    See Also:
        validate_game_data(): Validation logic implementation
        upload_to_s3(): Upload extracted data to S3
        DataQualityError: Custom exception for validation failures
    """
    pass
```

### Method with Self Parameter

```python
def calculate_player_stats(self, timestamp: datetime) -> PlayerStats:
    """Calculate player statistics at exact timestamp.

    Aggregates all play-by-play events up to the specified timestamp
    to compute career statistics at that precise moment. This enables
    temporal queries like "What were LeBron's stats on June 19, 2016?"

    Args:
        timestamp: Exact moment to calculate statistics. Must include
            timezone information. Uses millisecond precision if available.

    Returns:
        PlayerStats object with cumulative statistics:
            - points, rebounds, assists, etc.
            - games_played (count of games before timestamp)
            - shooting_percentages (calculated from attempts)

    Raises:
        ValueError: If timestamp is in the future
        DatabaseError: If query fails or connection lost

    Examples:
        >>> from datetime import datetime
        >>> import pytz
        >>> timestamp = datetime(2016, 6, 19, 19, 0, 0, tzinfo=pytz.timezone('US/Central'))
        >>> stats = player.calculate_player_stats(timestamp)
        >>> print(f"Points: {stats.points}")
        Points: 32292
    """
    pass
```

### Generator Function

```python
def stream_game_events(game_id: int) -> Generator[dict, None, None]:
    """Stream play-by-play events for a game.

    Yields events one at a time to reduce memory usage for large games.
    Events are yielded in chronological order (by period and clock).

    Args:
        game_id: NBA game identifier

    Yields:
        dict: Play-by-play event with keys:
            - event_id: Unique event identifier
            - period: Quarter/overtime number
            - clock: Time remaining in period
            - description: Human-readable event description
            - player_ids: List of involved player IDs
            - score: Current score after event

    Raises:
        GameNotFoundError: If game_id does not exist
        DatabaseError: If database connection fails

    Examples:
        >>> for event in stream_game_events(401584866):
        ...     if event['event_type'] == 'shot':
        ...         print(f"{event['player_name']}: {event['description']}")
        Jayson Tatum: makes 2-pt shot
        Luka Doncic: misses 3-pt shot
    """
    pass
```

### Private Function (Underscore Prefix)

```python
def _validate_schema(data: dict) -> list[str]:
    """Validate data structure against expected schema.

    This is an internal validation helper used by extract_game_data().
    Not intended for direct use by external callers.

    Args:
        data: Game data dictionary to validate

    Returns:
        List of validation error messages. Empty list if valid.

    Note:
        This function does not raise exceptions, it returns error messages
        for the caller to handle.
    """
    pass
```

**Docstring for private functions:**
- ⭕ Optional for very simple helpers
- ✅ Required if complex logic or called from multiple places
- ✅ Use shorter format (no Examples, See Also sections)

---

## Type Hints

### Always Use Type Hints

Type hints + docstrings = best combination:

```python
def process_data(
    input_file: str,
    output_format: Literal['json', 'csv', 'parquet'] = 'json',
    validate: bool = True
) -> dict[str, Any]:
    """Process data file and convert to specified format.

    Args:
        input_file: Path to input file (absolute or relative)
        output_format: Desired output format
        validate: Whether to validate data before processing

    Returns:
        Dictionary with processing statistics:
            - rows_processed: Number of rows
            - errors: List of error messages
            - output_path: Path to output file
    """
    pass
```

**Type hints cover:**
- ✅ Parameter types
- ✅ Return type
- ✅ Generic types (List, Dict, Optional)

**Docstrings cover:**
- ✅ Detailed descriptions
- ✅ Valid values/ranges
- ✅ Edge cases
- ✅ Examples

### Complex Types

Use type hints for structure, docstrings for details:

```python
from typing import TypedDict, Optional

class GameData(TypedDict):
    game_id: int
    date: datetime
    home_team: str
    away_team: str
    play_by_play: list[dict]

def extract_game_data(game_id: int) -> Optional[GameData]:
    """Extract game data.

    Args:
        game_id: NBA game identifier

    Returns:
        GameData dictionary with keys:
            - game_id: Integer game ID
            - date: Game date/time (datetime object)
            - home_team: 3-letter home team abbreviation
            - away_team: 3-letter away team abbreviation
            - play_by_play: List of play-by-play event dicts

        Returns None if game not found.
    """
    pass
```

---

## Examples by Use Case

### ETL / Data Processing

```python
def transform_box_score(
    raw_data: dict,
    include_advanced: bool = False
) -> pd.DataFrame:
    """Transform raw box score JSON into structured DataFrame.

    Extracts player statistics from ESPN API response and converts to
    pandas DataFrame with standardized column names. Optionally includes
    advanced statistics (PER, TS%, etc.) if available in source data.

    Args:
        raw_data: Raw JSON response from ESPN API containing 'boxscore' key
        include_advanced: If True, calculate and include advanced metrics

    Returns:
        DataFrame with columns:
            - player_id (int)
            - player_name (str)
            - minutes (float)
            - points (int)
            - rebounds (int)
            - assists (int)
            - [... basic stats ...]
            - per (float, if include_advanced=True)
            - ts_percent (float, if include_advanced=True)

    Raises:
        KeyError: If required keys missing from raw_data
        ValueError: If statistics are malformed (negative values, etc.)

    Examples:
        >>> raw_data = fetch_espn_box_score(401584866)
        >>> df = transform_box_score(raw_data)
        >>> df[['player_name', 'points']].head()
                 player_name  points
        0      Jayson Tatum      31
        1    Jaylen Brown      21
        2  Kristaps Porzingis 12

    Note:
        Advanced metrics calculated using formulas from Basketball Reference.
        PER formula: (Points + Rebounds + Assists - Missed Shots) / Minutes
    """
    pass
```

### Database Operations

```python
def execute_temporal_query(
    query: str,
    timestamp: datetime,
    params: Optional[dict] = None
) -> list[dict]:
    """Execute SQL query with temporal snapshot semantics.

    Runs query against database with temporal filtering to return results
    as they existed at the specified timestamp. Uses time-travel features
    to reconstruct historical state.

    Args:
        query: SQL query string (parameterized with :param_name placeholders)
        timestamp: Point-in-time for query snapshot
        params: Query parameters (optional). Keys should match placeholders
            in query string. Example: {'team': 'LAL', 'min_points': 20}

    Returns:
        List of dictionaries, one per row. Column names are keys.
        Returns empty list if no rows match.

    Raises:
        DatabaseError: If connection fails or query has syntax error
        ValueError: If timestamp is invalid or in the future
        KeyError: If required param missing from params dict

    Examples:
        Query player stats at specific time:
        >>> query = "SELECT * FROM player_stats WHERE player_id = :pid"
        >>> timestamp = datetime(2016, 6, 19, 19, 0, 0, tzinfo=timezone.utc)
        >>> results = execute_temporal_query(
        ...     query=query,
        ...     timestamp=timestamp,
        ...     params={'pid': 2544}
        ... )
        >>> print(results[0]['points'])
        32292

    Note:
        Uses PostgreSQL temporal tables with SYSTEM_TIME AS OF clause.
        Query performance depends on temporal index coverage.

    See Also:
        docs/TEMPORAL_QUERY_GUIDE.md: Complete temporal query documentation
    """
    pass
```

### Machine Learning

```python
def train_prediction_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    model_type: Literal['logistic', 'xgboost', 'neural_net'] = 'xgboost',
    hyperparams: Optional[dict] = None
) -> TrainedModel:
    """Train NBA game outcome prediction model.

    Trains a supervised learning model to predict game outcomes (win/loss)
    based on team/player features. Supports multiple model architectures
    with automatic hyperparameter tuning if hyperparams not specified.

    Args:
        X_train: Training features, shape (n_samples, n_features).
            Features should be standardized before calling this function.
        y_train: Training labels, shape (n_samples,).
            Binary labels: 0 = home loss, 1 = home win.
        model_type: Type of model to train:
            - 'logistic': Logistic regression (fast, interpretable)
            - 'xgboost': Gradient boosted trees (best accuracy)
            - 'neural_net': Feed-forward neural network
        hyperparams: Model-specific hyperparameters. If None, uses defaults
            optimized via Bayesian optimization. Example for XGBoost:
            {
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8
            }

    Returns:
        TrainedModel object containing:
            - model: Fitted scikit-learn or xgboost model
            - feature_names: List of feature names
            - training_metrics: Dict of training metrics (accuracy, AUC, etc.)
            - validation_metrics: Dict of cross-validation metrics
            - hyperparams: Final hyperparameters used

    Raises:
        ValueError: If X_train and y_train shapes incompatible
        ValueError: If model_type not recognized
        ConvergenceWarning: If model training does not converge

    Examples:
        Train default XGBoost model:
        >>> X_train, y_train = load_training_data()
        >>> model = train_prediction_model(X_train, y_train)
        >>> print(f"Training accuracy: {model.training_metrics['accuracy']:.3f}")
        Training accuracy: 0.872

        Train with custom hyperparameters:
        >>> hyperparams = {'max_depth': 8, 'learning_rate': 0.05}
        >>> model = train_prediction_model(
        ...     X_train, y_train,
        ...     model_type='xgboost',
        ...     hyperparams=hyperparams
        ... )

    Note:
        - Uses stratified 5-fold cross-validation for metrics
        - Automatically handles class imbalance via class weights
        - Model artifacts saved to models/ directory with timestamp
        - Feature importance scores available via model.feature_importances_

    See Also:
        feature_engineering.py: Feature extraction from raw data
        evaluate_model(): Model evaluation on test set
        docs/phases/phase_5/5.0001_hyperparameter_optimization/README.md
    """
    pass
```

### CLI Scripts

```python
def main():
    """NBA Simulator ADCE autonomous loop main entry point.

    This script runs the master autonomous loop that coordinates data collection,
    gap detection, and scraper orchestration. It should be run as a long-running
    daemon process (via launchd on macOS or systemd on Linux).

    Command-line usage:
        python scripts/autonomous/autonomous_loop.py [--config CONFIG]

    Options:
        --config: Path to configuration YAML file.
                  Default: config/autonomous_config.yaml

    Environment variables:
        ADCE_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        ADCE_DRY_RUN: If 'true', run without executing tasks (testing)

    Exit codes:
        0: Normal shutdown (SIGTERM/SIGINT received)
        1: Configuration error
        2: Database connection error
        3: S3 access error
        4: Unexpected exception

    Examples:
        Run with default config:
        $ python scripts/autonomous/autonomous_loop.py

        Run with custom config:
        $ python scripts/autonomous/autonomous_loop.py --config custom.yaml

        Run in dry-run mode:
        $ ADCE_DRY_RUN=true python scripts/autonomous/autonomous_loop.py

    Note:
        - Logs written to logs/autonomous_loop.log with rotation
        - Health check endpoint on http://localhost:8080/health
        - Graceful shutdown on SIGTERM (waits for current task to complete)
        - Automatic restart on crashes (via launchd/systemd)

    See Also:
        autonomous_cli.py: Command-line interface for ADCE management
        docs/AUTONOMOUS_OPERATION.md: Complete operational guide
    """
    pass
```

---

## Common Patterns

### Optional Parameters with Defaults

```python
def upload_to_s3(
    local_file: str,
    s3_key: Optional[str] = None,
    overwrite: bool = False,
    metadata: Optional[dict] = None
) -> str:
    """Upload file to S3 bucket.

    Args:
        local_file: Path to local file to upload
        s3_key: S3 object key. If None, uses basename of local_file.
        overwrite: If False (default), raises error if S3 key exists.
                   If True, overwrites existing object.
        metadata: Optional metadata dict to attach to S3 object.
                  Common keys: 'source', 'date', 'version'

    Returns:
        S3 URI of uploaded object (s3://bucket/key)
    """
    pass
```

### Multiple Return Values

```python
def validate_and_parse(data: str) -> tuple[bool, dict, list[str]]:
    """Validate and parse JSON data string.

    Args:
        data: JSON string to validate and parse

    Returns:
        Tuple of (is_valid, parsed_data, errors):
            - is_valid (bool): True if data is valid JSON
            - parsed_data (dict): Parsed dictionary if valid, else {}
            - errors (list[str]): List of validation error messages
                                  Empty list if valid

    Examples:
        >>> is_valid, data, errors = validate_and_parse('{"key": "value"}')
        >>> if is_valid:
        ...     print(data['key'])
        value
    """
    pass
```

### Context Managers

```python
class DatabaseConnection:
    """Context manager for database connections.

    Handles connection pooling, automatic commit/rollback, and resource cleanup.

    Examples:
        >>> with DatabaseConnection() as conn:
        ...     result = conn.execute("SELECT * FROM games LIMIT 10")
        ...     print(len(result))
        10

    Note:
        Automatically commits on successful exit, rolls back on exception.
    """

    def __enter__(self) -> 'DatabaseConnection':
        """Acquire database connection from pool.

        Returns:
            Self (DatabaseConnection instance)

        Raises:
            DatabaseError: If connection pool exhausted or connection fails
        """
        pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Release connection and handle commit/rollback.

        Args:
            exc_type: Exception type if exception occurred, else None
            exc_val: Exception value if exception occurred, else None
            exc_tb: Exception traceback if exception occurred, else None

        Returns:
            False (do not suppress exceptions)
        """
        pass
```

---

## Enforcement & Tools

### pydocstyle Configuration

Add to `.pydocstyle`:
```ini
[pydocstyle]
inherit = false
convention = google
add-ignore = D100,D104,D105,D107
match = (?!test_).*\.py
match-dir = ^(?!(tests|docs|\.)).*
```

**Ignored error codes:**
- D100: Missing docstring in public module (optional for simple modules)
- D104: Missing docstring in public package (`__init__.py`)
- D105: Missing docstring in magic method (often self-explanatory)
- D107: Missing docstring in `__init__` (if trivial)

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:
```yaml
- repo: https://github.com/PyCQA/pydocstyle
  rev: 6.3.0
  hooks:
    - id: pydocstyle
      args: ['--config=.pydocstyle']
      additional_dependencies: ['toml']
```

**Install and run:**
```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run pydocstyle --all-files

# Run on specific file
pre-commit run pydocstyle --files scripts/monitoring/dims_cli.py
```

### Check Docstring Coverage

```bash
# Count functions with docstrings
grep -r "^def " scripts/ | wc -l  # Total functions
grep -r '"""' scripts/ | wc -l    # Docstring count

# Or use interrogate tool
pip install interrogate
interrogate scripts/ notebooks/ -v

# Expected output:
# Interrogated 42 files.
# Docstring coverage: 87.2% (246/282)
```

### Auto-generate Sphinx Docs

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Generate docs
cd docs/reference
sphinx-apidoc -o source/ ../../scripts/ ../../notebooks/
make html

# View docs
open _build/html/index.html
```

---

## Migration Guide

### Auditing Current Codebase

```bash
# Find functions without docstrings
grep -r "^def " scripts/ | while read line; do
    file=$(echo $line | cut -d: -f1)
    func=$(echo $line | cut -d: -f2)
    if ! grep -A1 "$func" "$file" | grep -q '"""'; then
        echo "Missing: $file - $func"
    fi
done > missing_docstrings.txt

# Review results
cat missing_docstrings.txt
```

### Adding Docstrings Gradually

**Priority order:**
1. ✅ Public API functions (used by other modules)
2. ✅ Complex functions (>30 lines, non-obvious logic)
3. ✅ Entry point scripts (CLI, main functions)
4. ✅ Functions with bugs or confusion historically
5. ⭕ Simple helper functions
6. ⭕ Test functions (less critical)

**Weekly goal:** Add docstrings to 10-15 functions

### Template for Quick Docstrings

```python
def function_name(param1, param2):
    """[One-line summary].

    Args:
        param1: [Description]
        param2: [Description]

    Returns:
        [Description]
    """
    pass
```

---

## Best Practices Summary

### DO:
- ✅ Write docstrings for all public functions/classes
- ✅ Use imperative mood for one-line summaries
- ✅ Include type hints alongside docstrings
- ✅ Provide examples for complex functions
- ✅ Document edge cases and gotchas
- ✅ Keep docstrings up-to-date when code changes

### DON'T:
- ❌ Repeat information from type hints
- ❌ Write docstrings for trivial getters/setters
- ❌ Include implementation details (use code comments instead)
- ❌ Write novels (keep it concise)
- ❌ Use passive voice ("Data is extracted" → "Extract data")

---

## References

**Official Style Guides:**
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)

**Tools:**
- [pydocstyle Documentation](http://www.pydocstyle.org/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Napoleon Extension (Google Style)](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)

**Related Documentation:**
- [DEVELOPER_ONBOARDING.md](DEVELOPER_ONBOARDING.md) - New developer guide
- [STYLE_GUIDE.md](STYLE_GUIDE.md) - General code style
- [API_VERSIONING_POLICY.md](API_VERSIONING_POLICY.md) - API standards

---

**Version History:**
- **1.0.0** (2025-10-31) - Initial docstring standards

**Last Updated:** October 31, 2025
**Maintained By:** NBA Simulator Dev Team
**Review Date:** January 31, 2026
