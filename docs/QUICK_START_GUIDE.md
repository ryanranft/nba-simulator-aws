# NBA Simulator - Quick Start Guide

**Version:** 1.0.0
**Last Updated:** October 29, 2025

---

## Overview

The `nba_simulator` package provides a structured interface to the NBA Simulator production system with data models, validation, monitoring, and CLI capabilities.

---

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL database credentials
- AWS credentials (for S3 access)

### Install Package

```bash
cd /Users/ryanranft/nba-simulator-aws
pip install -e .
```

### Verify Installation

```python
import nba_simulator
print(nba_simulator.__version__)  # Should print: 1.0.0
```

---

## Configuration

### Database Credentials

The package loads credentials from environment variables or `.env` file:

```bash
# Required environment variables
export RDS_HOST="your-db-host"
export RDS_PORT="5432"
export RDS_DATABASE="nba_simulator"
export RDS_USERNAME="your-username"
export RDS_PASSWORD="your-password"
```

Or use the credentials file:

```bash
source /Users/ryanranft/nba-sim-credentials.env
```

---

## Basic Usage

### 1. Data Models

#### Game Model

```python
from datetime import datetime
from nba_simulator.models import Game

# Create a game
game = Game(
    game_id="401584893",
    season=2024,
    game_date=datetime(2024, 10, 29, 19, 0),
    home_team_id="LAL",
    away_team_id="DEN",
    home_score=110,
    away_score=105,
    status="final",
    venue="Crypto.com Arena"
)

# Use helper methods
print(f"Winner: {game.winner()}")         # LAL
print(f"Margin: {game.margin()}")         # 5
print(f"Total: {game.total_points()}")    # 215

# Serialize
game_dict = game.to_dict()
game_json = game.to_json(indent=2)

# Deserialize
restored = Game.from_dict(game_dict)
```

#### Player Model

```python
from datetime import date
from nba_simulator.models import Player

# Create a player
player = Player(
    player_id="2544",
    first_name="LeBron",
    last_name="James",
    birth_date=date(1984, 12, 30),
    height_inches=81,
    weight_pounds=250,
    position="SF",
    jersey_number=23,
    team_id="LAL",
    rookie_year=2003
)

# Use helper methods
print(player.full_name())           # LeBron James
print(player.age())                 # 40
print(player.height_feet_inches())  # 6'9"
print(player.years_in_league())     # 22
```

#### Team Model

```python
from nba_simulator.models import Team

# Create a team
team = Team(
    team_id="LAL",
    team_name="Los Angeles Lakers",
    team_city="Los Angeles",
    team_nickname="Lakers",
    conference="Western",
    division="Pacific",
    founded_year=1947,
    arena="Crypto.com Arena",
    arena_capacity=18997
)

# Use helper methods
print(team.full_name())              # Los Angeles Lakers
print(team.years_since_founded())    # 79
```

### 2. Database Queries

```python
from nba_simulator.database import execute_query

# Query games
games = execute_query("SELECT * FROM games WHERE season = 2024 LIMIT 10")
print(f"Found {len(games)} games")

# Query with parameters (prevents SQL injection)
from nba_simulator.database import DatabaseConnection

db = DatabaseConnection()
with db.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM games WHERE home_team_id = %s",
            ("LAL",)
        )
        results = cur.fetchall()
```

### 3. Data Validation

```python
from nba_simulator.validation import validate_database_health, validate_game_data

# Validate entire database
report = validate_database_health()
print(f"Errors: {report['error_count']}")
print(f"Warnings: {report['warning_count']}")
print(f"Status: {'PASSED' if report['passed'] else 'FAILED'}")

# Validate specific game
game_report = validate_game_data("401584893")
if game_report['passed']:
    print("✅ Game data is valid")
```

### 4. Data Quality Monitoring

```python
from nba_simulator.monitoring import monitor_critical_tables, DataQualityMonitor

# Monitor all critical tables
report = monitor_critical_tables()
for table_name, metrics in report['tables'].items():
    print(f"\n{table_name}:")
    for check, value in metrics['checks'].items():
        print(f"  {check}: {value}")

# Monitor specific table
monitor = DataQualityMonitor()
health = monitor.check_table_health('games')
print(f"Table: {health['table_name']}")
print(f"Rows: {health['row_count']:,}")
```

### 5. CLI Interface

```bash
# Show database info
python -m nba_simulator.cli info

# Run validation
python -m nba_simulator.cli validate

# Run monitoring
python -m nba_simulator.cli monitor

# Execute query
python -m nba_simulator.cli query "SELECT COUNT(*) FROM games"

# Get help
python -m nba_simulator.cli --help
```

---

## Common Patterns

### Pattern 1: Query and Model

```python
from nba_simulator.database import execute_query
from nba_simulator.models import Game

# Query database
results = execute_query("SELECT * FROM games WHERE season = 2024 LIMIT 1")

# Create model from database row
game = Game.from_db_row(results[0])
print(f"Winner: {game.winner()}")
```

### Pattern 2: Validate Before Use

```python
from nba_simulator.models import Player, ValidationError

try:
    player = Player(
        player_id="test",
        first_name="Test",
        last_name="Player",
        birth_date=date(1990, 1, 1),
        height_inches=75,
        weight_pounds=200,
        position="PG",
        rookie_year=2010
    )
    print("✅ Player is valid")
except ValidationError as e:
    print(f"❌ Validation failed: {e}")
```

### Pattern 3: Batch Processing

```python
from nba_simulator.database import execute_query
from nba_simulator.models import Game

# Get all games for a season
games_data = execute_query("SELECT * FROM games WHERE season = 2024")

# Convert to models
games = [Game.from_db_row(row) for row in games_data]

# Process
for game in games:
    if game.is_completed():
        print(f"{game.game_id}: {game.winner()} by {game.margin()}")
```

### Pattern 4: Monitor with Alerts

```python
from nba_simulator.validation import DataValidator

validator = DataValidator()

# Run validation
validator.validate_games_integrity()
validator.validate_temporal_events_integrity()

# Get report
report = validator.get_validation_report()

# Alert if errors
if report['error_count'] > 0:
    print("⚠️ ALERT: Validation errors detected!")
    for error in report['errors']:
        print(f"  - {error}")
```

---

## Troubleshooting

### Issue: Import Error

**Problem:** `ModuleNotFoundError: No module named 'nba_simulator'`

**Solution:**
```bash
cd /Users/ryanranft/nba-simulator-aws
pip install -e .
```

### Issue: Database Connection Failed

**Problem:** `Error connecting to database`

**Solution:**
1. Check credentials are loaded:
   ```bash
   echo $RDS_HOST
   ```
2. Source credentials file:
   ```bash
   source /Users/ryanranft/nba-sim-credentials.env
   ```
3. Verify database is accessible:
   ```bash
   psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DATABASE
   ```

### Issue: Validation Errors

**Problem:** `ValidationError: Season must be 1946 or later`

**Solution:** Models have built-in validation. Check your input data:
- Game seasons: 1946-present
- Player heights: 60-100 inches
- Jersey numbers: 0-99
- Team IDs: 2-3 uppercase letters

### Issue: CLI Not Working

**Problem:** `python -m nba_simulator.cli` shows error

**Solution:**
1. Ensure package is installed
2. Load credentials before running
3. Use full command:
   ```bash
   source /Users/ryanranft/nba-sim-credentials.env
   python -m nba_simulator.cli info
   ```

---

## Next Steps

1. **Read API Reference:** `docs/API_REFERENCE.md` (when available)
2. **Review Best Practices:** `docs/BEST_PRACTICES.md` (when available)
3. **Explore Examples:** `examples/` directory (when available)
4. **Run Tests:** `pytest tests/ -v`

---

## Getting Help

- **Documentation:** `docs/` directory
- **Code Issues:** Check `tests/` for examples
- **Performance:** Run monitoring dashboard
- **Data Issues:** Run validators

---

## Key Features

- ✅ Type-safe data models with automatic validation
- ✅ Backward-compatible with existing scripts
- ✅ Connection pooling for efficiency
- ✅ Comprehensive validation and monitoring
- ✅ CLI interface for common operations
- ✅ JSON/dict serialization
- ✅ Database row mapping

---

**Last Updated:** October 29, 2025
**Package Version:** 1.0.0
**Status:** Production Ready

