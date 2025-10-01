# Code Style Guide

<!-- AUTO-UPDATE TRIGGER: When code style pattern used 3+ times (establishes precedent) -->
<!-- LAST UPDATED: 2025-10-01 -->
<!-- FREQUENCY: As needed (when patterns emerge) -->
<!-- REMINDER: Add rules for: consistent patterns, readability improvements, team conventions, language-specific best practices -->

**Project:** NBA Game Simulator & ML Platform
**Purpose:** Consistent code style for maintainability and LLM code generation

---

## Philosophy

- **Readability over cleverness** - Code is read more than written
- **Explicit over implicit** - Clear intent beats brevity
- **Consistency over personal preference** - Follow the guide, even if you disagree
- **Pythonic patterns** - Use Python idioms and conventions
- **Data science friendly** - Optimize for exploratory analysis and iteration

---

## Python Style

### General

**Follow PEP 8** with modifications noted below:
- Line length: 100 characters (not 79)
- Use 4 spaces for indentation (never tabs)

**Tools (optional):**
```bash
# Auto-formatting (optional)
pip install black isort

# Run formatter
black scripts/
isort scripts/

# Type checking (optional for critical code)
pip install mypy
mypy scripts/etl/
```

### Naming Conventions

**Files and Modules:**
```python
# Good
glue_etl_job.py
sanitize_command_log.sh
field_mapping.yaml

# Bad
GlueETLJob.py
Sanitize-Command-Log.sh
FieldMapping.yaml
```

**Variables and Functions:**
```python
# Good - snake_case
player_stats = get_player_data(game_id)
total_points = calculate_points(player_stats)

# Bad - camelCase (reserve for classes)
playerStats = getPlayerData(gameId)
totalPoints = calculatePoints(playerStats)
```

**Classes:**
```python
# Good - PascalCase
class GameSimulator:
    pass

class PlayerStatistics:
    pass

# Bad - snake_case
class game_simulator:
    pass
```

**Constants:**
```python
# Good - UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
S3_BUCKET_NAME = "nba-sim-raw-data-lake"

# Bad - lowercase
max_retries = 3
```

**Private/Internal:**
```python
# Good - single underscore prefix
class GameSimulator:
    def _internal_helper(self):
        pass

    def __very_private(self):  # Name mangling
        pass

# Bad - no indication of privacy
class GameSimulator:
    def internal_helper(self):  # Looks public
        pass
```

### Imports

**Order:**
1. Standard library
2. Third-party packages
3. Local modules

**Format:**
```python
# Good
import os
import sys
from typing import List, Dict, Optional

import boto3
import pandas as pd
import numpy as np

from scripts.etl.field_mapping import extract_fields
from scripts.utils.logging import setup_logger

# Bad - mixed order, wildcard imports
from scripts.etl.field_mapping import *
import pandas as pd
import os
import boto3
```

**Avoid wildcard imports:**
```python
# Bad
from pandas import *

# Good
import pandas as pd
# or
from pandas import DataFrame, Series
```

### Documentation

**Module docstrings:**
```python
"""
ETL script for extracting NBA game data from S3 and loading into RDS.

This script processes 146,115 JSON files from S3, extracts ~10% of fields,
and loads the data into PostgreSQL. See ADR-002 for extraction strategy.

Usage:
    python glue_etl_job.py --batch-size 1000 --dry-run

Environment Variables:
    S3_BUCKET: Source S3 bucket name
    DB_HOST: RDS PostgreSQL hostname
    DB_NAME: Database name

Returns:
    Exit code 0 on success, 1 on failure
"""
```

**Function docstrings:**
```python
# Good - Google style (preferred for data science)
def calculate_player_efficiency(stats: Dict[str, float]) -> float:
    """
    Calculate Player Efficiency Rating (PER) from game statistics.

    PER formula: (PTS + REB + AST + STL + BLK - TO - FGA + FTA) / MIN

    Args:
        stats: Dictionary containing player statistics with keys:
            - points: Total points scored
            - rebounds: Total rebounds
            - assists: Total assists
            - minutes: Minutes played

    Returns:
        Float representing PER value, typically between -5 and 40.
        Higher values indicate better performance.

    Raises:
        ValueError: If minutes played is 0 or negative
        KeyError: If required stat fields are missing

    Example:
        >>> stats = {"points": 25, "rebounds": 10, "assists": 8, "minutes": 36}
        >>> calculate_player_efficiency(stats)
        23.5
    """
    if stats["minutes"] <= 0:
        raise ValueError("Minutes must be positive")

    # Implementation here
    pass
```

**Alternative - NumPy style (also acceptable):**
```python
def calculate_player_efficiency(stats):
    """
    Calculate Player Efficiency Rating (PER).

    Parameters
    ----------
    stats : dict
        Dictionary containing player statistics

    Returns
    -------
    float
        Player efficiency rating

    Examples
    --------
    >>> calculate_player_efficiency({"points": 25, "minutes": 36})
    23.5
    """
    pass
```

**Class docstrings:**
```python
class GameSimulator:
    """
    Simulates NBA games using historical statistics and Monte Carlo methods.

    The simulator uses player statistics from the RDS database to generate
    probabilistic game outcomes. See docs/simulation_algorithm.md for details.

    Attributes:
        db_connection: PostgreSQL connection object
        random_seed: Seed for reproducible results (default: None)

    Example:
        >>> simulator = GameSimulator(db_connection)
        >>> result = simulator.simulate_game(home_team_id=1, away_team_id=2)
        >>> print(result["home_score"])
        105
    """
```

### Type Hints

**Use type hints for function signatures:**
```python
# Good
def get_player_stats(player_id: int, season: str) -> Dict[str, float]:
    pass

def load_game_data(game_ids: List[int]) -> pd.DataFrame:
    pass

def calculate_average(values: List[float]) -> Optional[float]:
    """Returns None if list is empty"""
    if not values:
        return None
    return sum(values) / len(values)

# Acceptable - omit for obvious cases or exploratory code
def print_report(data):
    """Print summary report (temporary debug function)"""
    print(data)
```

**Complex types:**
```python
from typing import Dict, List, Tuple, Optional, Union

# Good
PlayerStats = Dict[str, Union[int, float]]
GameResult = Tuple[int, int]  # (home_score, away_score)

def simulate_games(teams: List[int]) -> List[GameResult]:
    pass
```

### Error Handling

**Be specific with exceptions:**
```python
# Good
try:
    connection = psycopg2.connect(host=db_host, database=db_name)
except psycopg2.OperationalError as e:
    logger.error(f"Failed to connect to database: {e}")
    raise
except psycopg2.ProgrammingError as e:
    logger.error(f"Database configuration error: {e}")
    raise

# Bad - too broad
try:
    connection = psycopg2.connect(host=db_host, database=db_name)
except Exception as e:
    print("Error")
```

**Always log before re-raising:**
```python
# Good
try:
    data = process_file(filename)
except FileNotFoundError as e:
    logger.error(f"File not found: {filename}")
    raise  # Re-raise with original traceback

# Bad - silent failure
try:
    data = process_file(filename)
except:
    pass
```

**Use custom exceptions for domain logic:**
```python
# Good
class InvalidGameDataError(Exception):
    """Raised when game data fails validation"""
    pass

def validate_game_data(data):
    if data["home_score"] < 0:
        raise InvalidGameDataError(f"Invalid score: {data['home_score']}")
```

### Data Science Code

**Pandas style:**
```python
# Good - method chaining with line breaks
player_stats = (
    df_games
    .query("season == '2024-25'")
    .groupby("player_id")
    .agg({
        "points": "sum",
        "games": "count",
        "minutes": "mean"
    })
    .assign(ppg=lambda x: x["points"] / x["games"])
    .sort_values("ppg", ascending=False)
)

# Bad - hard to read single line
player_stats = df_games.query("season == '2024-25'").groupby("player_id").agg({"points": "sum", "games": "count"})
```

**NumPy style:**
```python
# Good - explicit shapes
player_matrix = np.zeros((n_players, n_features))  # Shape documented
weights = np.random.rand(n_features, 1)  # (n_features, 1)

# Good - avoid implicit broadcasting surprises
result = player_matrix @ weights  # Explicit matrix multiplication
```

**Jupyter Notebooks:**
```python
# Cell 1: Imports and setup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

%matplotlib inline
%load_ext autoreload
%autoreload 2

# Cell 2: Load data
df = pd.read_csv("data.csv")

# Cell 3: Explore data
df.head()
df.describe()

# Bad - don't put everything in one cell
```

---

## SQL Style

### General Rules

- SQL keywords: UPPERCASE
- Table/column names: lowercase_snake_case
- Indent subqueries
- One column per line in SELECT (for readability)

### Examples

**Good:**
```sql
-- Readable, one column per line
SELECT
    g.game_id,
    g.game_date,
    t1.team_name AS home_team,
    t2.team_name AS away_team,
    g.home_score,
    g.away_score,
    (g.home_score - g.away_score) AS point_differential
FROM
    games AS g
    INNER JOIN teams AS t1 ON g.home_team_id = t1.team_id
    INNER JOIN teams AS t2 ON g.away_team_id = t2.team_id
WHERE
    g.season = '2024-25'
    AND g.game_date >= '2024-10-01'
ORDER BY
    g.game_date DESC,
    g.game_id
LIMIT 100;
```

**Bad:**
```sql
-- Hard to read
select g.game_id, g.game_date, t1.team_name as home_team, t2.team_name as away_team from games g inner join teams t1 on g.home_team_id = t1.team_id inner join teams t2 on g.away_team_id = t2.team_id where g.season = '2024-25' order by g.game_date desc;
```

**Subqueries:**
```sql
-- Good - indented
SELECT
    player_id,
    player_name,
    avg_points
FROM (
    SELECT
        p.player_id,
        p.player_name,
        AVG(ps.points) AS avg_points
    FROM
        players AS p
        INNER JOIN player_stats AS ps ON p.player_id = ps.player_id
    GROUP BY
        p.player_id,
        p.player_name
) AS player_averages
WHERE
    avg_points > 20
ORDER BY
    avg_points DESC;
```

### Table and Column Names

**Good:**
```sql
-- Clear, descriptive names
CREATE TABLE player_game_stats (
    player_id INTEGER,
    game_id INTEGER,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    minutes_played INTEGER
);
```

**Bad:**
```sql
-- Unclear abbreviations
CREATE TABLE plyr_gm_sts (
    pid INTEGER,
    gid INTEGER,
    pts INTEGER,
    reb INTEGER,
    ast INTEGER,
    min INTEGER
);
```

---

## YAML Style

**Use for configuration files:**
```yaml
# Good - consistent indentation (2 spaces)
aws:
  region: us-east-1
  s3:
    bucket: nba-sim-raw-data-lake
    folders:
      - box_scores
      - pbp
      - schedule
      - team_stats

database:
  host: nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com
  port: 5432
  name: nba_simulator

etl:
  batch_size: 1000
  max_retries: 3
  timeout_seconds: 300
```

---

## Bash/Shell Style

**Follow Google Shell Style Guide:**
```bash
#!/bin/bash

# Good - clear variable names, quoted strings
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
LOG_FILE="${PROJECT_ROOT}/COMMAND_LOG.md"

# Function names: lowercase with underscores
check_file_exists() {
    local file_path="$1"

    if [[ -f "$file_path" ]]; then
        echo "✅ File exists: $file_path"
        return 0
    else
        echo "❌ File not found: $file_path"
        return 1
    fi
}

# Always quote variables
if check_file_exists "$LOG_FILE"; then
    echo "Processing log file..."
fi

# Bad - unquoted variables, unclear names
f="/path/to/file"
if [ -f $f ]; then  # Unquoted - breaks with spaces
    echo "ok"
fi
```

---

## Git Commit Messages

**Format:**
```
Brief summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how (the diff shows how).

- Bullet points are okay
- Use present tense: "Add feature" not "Added feature"
- Reference issues: "Fixes #123"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Examples:**
```bash
# Good
git commit -m "Add ETL field extraction logic

Extract only 10% of JSON fields per ADR-002. Reduces RDS storage
from 119 GB to 12 GB. Implements field mapping from field_mapping.yaml.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Bad
git commit -m "fixed stuff"
git commit -m "Updated files"
git commit -m "WIP"
```

---

## File Organization

### Project Structure

```
nba-simulator-aws/
├── scripts/
│   ├── etl/           # ETL scripts
│   ├── simulation/    # Game simulation code
│   ├── aws/           # AWS infrastructure scripts
│   └── utils/         # Shared utilities
├── sql/               # Database schemas
├── notebooks/         # Jupyter notebooks (exploratory)
├── tests/             # Test files (mirror src structure)
├── docs/              # Documentation
└── config/            # Configuration files
```

### File Naming

**Python scripts:**
```
glue_etl_job.py        # Main ETL script
field_mapping.yaml     # Configuration
test_etl_job.py        # Tests
```

**SQL files:**
```
create_tables.sql      # Table definitions
create_indexes.sql     # Index definitions
migration_001.sql      # Migration files (numbered)
```

**Documentation:**
```
STYLE_GUIDE.md         # This file
README.md              # Project overview
ADR-001-*.md           # Architecture decisions
```

---

## Comments

### When to Comment

**DO comment:**
- Complex algorithms or business logic
- Non-obvious performance optimizations
- Workarounds for bugs or limitations
- TODO/FIXME notes

**DON'T comment:**
- Obvious code
- Redundant explanations

**Good:**
```python
# Extract only 10% of fields per ADR-002 to reduce RDS storage costs
fields_to_extract = load_field_mapping("field_mapping.yaml")

# FIXME: Temporary workaround for missing player_id in some files
# See issue #123 - will be fixed in next data refresh
if "player_id" not in data:
    logger.warning(f"Missing player_id in {filename}, skipping...")
    return None

# Performance: Use vectorized operations instead of loop
# 10x faster for large datasets (tested with 100k records)
df["ppg"] = df["total_points"] / df["games_played"]
```

**Bad:**
```python
# Increment counter by 1
counter = counter + 1

# Loop through players
for player in players:
    # Process player
    process_player(player)
```

### TODO Comments

**Format:**
```python
# TODO(username): Add error handling for network timeouts
# TODO: Implement retry logic (see ADR-003)
# FIXME: This breaks when game_id is null
# HACK: Temporary fix until API v2 is available
# NOTE: This must run after database migration 003
```

---

## Testing Style

**Test file naming:**
```
test_etl_job.py        # Tests for etl_job.py
test_game_simulator.py # Tests for game_simulator.py
```

**Test function naming:**
```python
# Good - descriptive
def test_calculate_efficiency_with_valid_stats():
    pass

def test_calculate_efficiency_raises_error_on_zero_minutes():
    pass

# Bad - unclear
def test1():
    pass

def test_calc():
    pass
```

**Test structure - Arrange/Act/Assert:**
```python
def test_calculate_player_efficiency():
    # Arrange
    stats = {
        "points": 25,
        "rebounds": 10,
        "assists": 8,
        "minutes": 36
    }

    # Act
    result = calculate_player_efficiency(stats)

    # Assert
    assert result > 20
    assert result < 30
```

---

## LLM-Specific Guidelines

**For Claude Code generating code:**

1. **Follow this style guide** unless explicitly told otherwise
2. **Include docstrings** for all public functions
3. **Use type hints** for function signatures
4. **Add comments** for non-obvious logic
5. **Prefer readability** over cleverness
6. **Reference ADRs** when making architectural decisions
7. **Ask for clarification** if style preference is ambiguous

**Code generation preferences:**
```python
# Prefer explicit imports
from typing import List, Dict
import pandas as pd

# Over wildcard imports
from typing import *

# Prefer descriptive names
def calculate_player_efficiency_rating(stats: Dict[str, float]) -> float:
    pass

# Over abbreviations
def calc_per(s):
    pass
```

---

## Enforcement

**Manual Review:**
- Review PRs/commits for style consistency
- Use this guide as checklist

**Optional Automation:**
```bash
# Install tools
pip install black isort flake8 mypy

# Format code
black scripts/
isort scripts/

# Check style
flake8 scripts/ --max-line-length=100

# Type check
mypy scripts/etl/
```

**Config files (optional):**

`.flake8`:
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv
```

`pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

---

## Exceptions

**When to break the rules:**

1. **Third-party code** - Don't modify external libraries to match style
2. **Generated code** - SQL migrations, protobuf files, etc.
3. **Legacy code** - Don't reformat entire old codebase at once
4. **Performance** - If style hurts performance significantly
5. **Prototyping** - Exploratory notebooks can be messier

**Document exceptions:**
```python
# NOTE: Ignoring type hints here for compatibility with legacy code
def legacy_function(data):
    pass
```

---

## Style Evolution

This guide will evolve. When updating:

1. **Document the change** in Git commit
2. **Update this file** with rationale
3. **Add date** to changelog below
4. **Notify team** of significant changes

## Changelog

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-09-30 | Initial version | Establish baseline style guide |

---

**Questions or suggestions?** Update this guide via PR or project discussion.

**Last Updated:** 2025-09-30
