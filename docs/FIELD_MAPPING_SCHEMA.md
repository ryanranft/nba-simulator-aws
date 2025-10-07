# Field Mapping Schema - Multi-Source Integration

**Created:** October 6, 2025
**Purpose:** Standardized field names and transformations across all 5 data sources
**Status:** Foundation document for ETL and data integration

---

## Overview

Each data source (ESPN, NBA.com Stats, Kaggle, SportsDataverse, Basketball Reference) uses different field names for the same data. This document establishes:

- **Canonical field names** (RDS database schema)
- **Source-specific field names** (how each source labels fields)
- **Transformation rules** (how to convert source fields to canonical format)
- **Data type standards** (consistent types across all fields)

---

## Table of Contents

1. [Canonical Schema (RDS Database)](#canonical-schema-rds-database)
2. [Game-Level Field Mappings](#game-level-field-mappings)
3. [Player-Level Field Mappings](#player-level-field-mappings)
4. [Team-Level Field Mappings](#team-level-field-mappings)
5. [Play-by-Play Field Mappings](#play-by-play-field-mappings)
6. [Transformation Functions](#transformation-functions)

---

## Canonical Schema (RDS Database)

### Core Principles

1. **Use snake_case** for all field names (e.g., `home_score` not `homeScore`)
2. **Descriptive names** that explain the data (e.g., `field_goals_made` not `fgm`)
3. **Consistent prefixes** for related fields (e.g., `home_*`, `away_*`, `player_*`)
4. **Standard data types** (INTEGER for counts, VARCHAR for text, TIMESTAMP for dates)

### Tables Overview

| Table | Purpose | Canonical Fields |
|-------|---------|-----------------|
| `games` | Game-level data | 58 fields (see current schema) |
| `box_score_players` | Player statistics per game | 25+ fields |
| `box_score_teams` | Team statistics per game | 30+ fields |
| `play_by_play` | Event stream per game | 15+ fields |
| `players` | Player metadata | 10+ fields |
| `teams` | Team metadata | 8+ fields |

---

## Game-Level Field Mappings

### Basic Game Information

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `game_id` | VARCHAR(50) | `header.id` | `GameHeader.GAME_ID` | `id` | Constructed slug | Primary key |
| `game_date` | DATE | `header.competitions[0].date` | `GameHeader.GAME_DATE_EST` | `game_date` | URL slug (YYYYMMDD) | ISO format: YYYY-MM-DD |
| `game_time` | TIME | `header.competitions[0].date` | `GameHeader.GAME_TIME` | `game_time` | Page text | 24-hour format: HH:MM:SS |
| `season` | INTEGER | `header.season.year` | `GameHeader.SEASON` | `season_id` | URL/page | 4-digit year (2024) |
| `season_type` | VARCHAR(20) | `header.season.type` | Game ID type code | `season_type` | Page context | 'regular', 'playoffs', 'preseason' |
| `game_status` | VARCHAR(20) | `header.competitions[0].status.type.name` | `GameHeader.GAME_STATUS_TEXT` | `game_status` | Page indicator | 'Final', 'In Progress', 'Scheduled' |

**Transformation Example:**
```python
def map_game_date(espn_data):
    """
    ESPN: "2024-12-25T20:00Z" (ISO 8601 with timezone)
    NBA.com: "2024-12-25" (date only)
    Kaggle: "2024-12-25" (date only)

    → Canonical: "2024-12-25" (DATE type)
    """
    if isinstance(espn_data, str) and 'T' in espn_data:
        return espn_data.split('T')[0]  # Extract date part
    return espn_data
```

### Team Information

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `home_team_id` | INTEGER | `competitors[0].id` | `GameHeader.HOME_TEAM_ID` | `team_id_home` | N/A | Source-specific ID |
| `home_team_abbr` | VARCHAR(3) | `competitors[0].team.abbreviation` | `LineScore.TEAM_ABBREVIATION` | `team_abbreviation_home` | URL slug | **Universal key** (LAL, BOS) |
| `home_team_name` | VARCHAR(100) | `competitors[0].team.displayName` | Team lookup | `team_name_home` | Page text | Full name |
| `away_team_id` | INTEGER | `competitors[1].id` | `GameHeader.VISITOR_TEAM_ID` | `team_id_away` | N/A | Source-specific ID |
| `away_team_abbr` | VARCHAR(3) | `competitors[1].team.abbreviation` | `LineScore.TEAM_ABBREVIATION` | `team_abbreviation_away` | URL slug | **Universal key** |
| `away_team_name` | VARCHAR(100) | `competitors[1].team.displayName` | Team lookup | `team_name_away` | Page text | Full name |

### Score Information

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `home_score` | INTEGER | `competitors[0].score` | `LineScore.PTS` (home) | `pts_home` | Table cell | Final score |
| `away_score` | INTEGER | `competitors[1].score` | `LineScore.PTS` (away) | `pts_away` | Table cell | Final score |
| `home_q1_score` | INTEGER | `boxscore.teams[0].statistics[].displayValue` | `LineScore.PTS_QTR1` | `q1_home` | Table cell | Quarter 1 |
| `home_q2_score` | INTEGER | Similar | `LineScore.PTS_QTR2` | `q2_home` | Table cell | Quarter 2 |
| `home_q3_score` | INTEGER | Similar | `LineScore.PTS_QTR3` | `q3_home` | Table cell | Quarter 3 |
| `home_q4_score` | INTEGER | Similar | `LineScore.PTS_QTR4` | `q4_home` | Table cell | Quarter 4 |
| `home_ot_score` | INTEGER | Similar | `LineScore.PTS_OT*` | `ot_home` | Table cell | Overtime (if any) |

**Transformation Example:**
```python
def map_quarter_scores(espn_data):
    """
    ESPN: Nested in boxscore.teams[].statistics array
    NBA.com: Direct fields (PTS_QTR1, PTS_QTR2, etc.)
    Kaggle: Direct fields (q1_home, q2_home, etc.)

    → Canonical: home_q1_score, home_q2_score, etc. (INTEGER)
    """
    espn_stats = espn_data['boxscore']['teams'][0]['statistics']

    # Find "scoring" statistic type
    for stat in espn_stats:
        if stat.get('name') == 'scoring':
            quarters = stat.get('displayValue', '').split('-')
            return {
                'home_q1_score': int(quarters[0]) if len(quarters) > 0 else None,
                'home_q2_score': int(quarters[1]) if len(quarters) > 1 else None,
                'home_q3_score': int(quarters[2]) if len(quarters) > 2 else None,
                'home_q4_score': int(quarters[3]) if len(quarters) > 3 else None,
            }
```

### Game Context

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `venue_name` | VARCHAR(100) | `header.competitions[0].venue.fullName` | N/A | `arena` | Page text | Arena/stadium name |
| `venue_city` | VARCHAR(50) | `header.competitions[0].venue.address.city` | N/A | `city` | Page text | City |
| `venue_state` | VARCHAR(2) | `header.competitions[0].venue.address.state` | N/A | `state` | Page text | State abbreviation |
| `attendance` | INTEGER | `header.competitions[0].attendance` | `GameInfo.ATTENDANCE` | `attendance` | Page text | Number of fans |
| `sold_out` | BOOLEAN | `header.competitions[0].soldOut` | N/A | N/A | Page indicator | True if sold out |

### Additional Metadata

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `broadcast_network` | VARCHAR(50) | `header.competitions[0].broadcasts[0].media.shortName` | N/A | N/A | Page text | ABC, ESPN, TNT, etc. |
| `broadcast_market` | VARCHAR(20) | `header.competitions[0].broadcasts[0].market.type` | N/A | N/A | N/A | 'national' or 'local' |
| `game_duration` | INTERVAL | Calculated | N/A | N/A | Page text | Actual game length |
| `referee_1` | VARCHAR(100) | `gameInfo.officials[0].displayName` | N/A | N/A | Page text | Lead referee |
| `referee_2` | VARCHAR(100) | `gameInfo.officials[1].displayName` | N/A | N/A | Page text | Referee 2 |
| `referee_3` | VARCHAR(100) | `gameInfo.officials[2].displayName` | N/A | N/A | Page text | Referee 3 |

---

## Player-Level Field Mappings

### Player Identification

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `player_id` | INTEGER | `athlete.id` | `PlayerStats.PLAYER_ID` | `person_id` | N/A | Source-specific ID |
| `player_name` | VARCHAR(100) | `athlete.displayName` | `PlayerStats.PLAYER_NAME` | `player_name` | Table row | Full name |
| `player_position` | VARCHAR(10) | `athlete.position.abbreviation` | `CommonPlayerInfo.POSITION` | `position` | Table context | PG, SG, SF, PF, C |
| `player_jersey` | VARCHAR(3) | `athlete.jersey` | `CommonPlayerInfo.JERSEY` | `jersey` | Table text | Jersey number |
| `starter` | BOOLEAN | `starter` | `PlayerStats.START_POSITION` | `starter` | Table indicator | True if started |

### Basic Stats

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `minutes` | INTEGER | `stats[].minutes` | `PlayerStats.MIN` | `min` | Table cell | Minutes played |
| `points` | INTEGER | `stats[].points` | `PlayerStats.PTS` | `pts` | Table cell | Points scored |
| `rebounds` | INTEGER | `stats[].rebounds` | `PlayerStats.REB` | `reb` | Table cell | Total rebounds |
| `offensive_rebounds` | INTEGER | `stats[].offensiveRebounds` | `PlayerStats.OREB` | `oreb` | Table cell | Offensive rebounds |
| `defensive_rebounds` | INTEGER | `stats[].defensiveRebounds` | `PlayerStats.DREB` | `dreb` | Table cell | Defensive rebounds |
| `assists` | INTEGER | `stats[].assists` | `PlayerStats.AST` | `ast` | Table cell | Assists |
| `steals` | INTEGER | `stats[].steals` | `PlayerStats.STL` | `stl` | Table cell | Steals |
| `blocks` | INTEGER | `stats[].blocks` | `PlayerStats.BLK` | `blk` | Table cell | Blocks |
| `turnovers` | INTEGER | `stats[].turnovers` | `PlayerStats.TO` | `tov` | Table cell | Turnovers |
| `fouls` | INTEGER | `stats[].fouls` | `PlayerStats.PF` | `pf` | Table cell | Personal fouls |

### Shooting Stats

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `field_goals_made` | INTEGER | `stats[].fieldGoalsMade` | `PlayerStats.FGM` | `fgm` | Table cell | FG made |
| `field_goals_attempted` | INTEGER | `stats[].fieldGoalsAttempted` | `PlayerStats.FGA` | `fga` | Table cell | FG attempted |
| `field_goal_percentage` | DECIMAL(4,3) | Calculated | `PlayerStats.FG_PCT` | `fg_pct` | Table cell | FG% (0.000-1.000) |
| `three_pointers_made` | INTEGER | `stats[].threePointFieldGoalsMade` | `PlayerStats.FG3M` | `fg3m` | Table cell | 3PT made |
| `three_pointers_attempted` | INTEGER | `stats[].threePointFieldGoalsAttempted` | `PlayerStats.FG3A` | `fg3a` | Table cell | 3PT attempted |
| `three_point_percentage` | DECIMAL(4,3) | Calculated | `PlayerStats.FG3_PCT` | `fg3_pct` | Table cell | 3PT% |
| `free_throws_made` | INTEGER | `stats[].freeThrowsMade` | `PlayerStats.FTM` | `ftm` | Table cell | FT made |
| `free_throws_attempted` | INTEGER | `stats[].freeThrowsAttempted` | `PlayerStats.FTA` | `fta` | Table cell | FT attempted |
| `free_throw_percentage` | DECIMAL(4,3) | Calculated | `PlayerStats.FT_PCT` | `ft_pct` | Table cell | FT% |

**Transformation Example:**
```python
def map_player_stats(espn_data):
    """
    ESPN: stats[].{fieldGoalsMade, fieldGoalsAttempted}
    NBA.com: {FGM, FGA}
    Kaggle: {fgm, fga}

    → Canonical: {field_goals_made, field_goals_attempted}
    """
    return {
        'field_goals_made': espn_data.get('fieldGoalsMade'),
        'field_goals_attempted': espn_data.get('fieldGoalsAttempted'),
        'field_goal_percentage': (
            espn_data.get('fieldGoalsMade') / espn_data.get('fieldGoalsAttempted')
            if espn_data.get('fieldGoalsAttempted', 0) > 0 else None
        )
    }
```

### Advanced Stats (Basketball Reference Only)

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `plus_minus` | INTEGER | `stats[].plusMinus` | `PlayerStats.PLUS_MINUS` | `plus_minus` | Table cell | +/- |
| `true_shooting_pct` | DECIMAL(4,3) | N/A | `PlayerStats.TS_PCT` | N/A | Calculated | TS% |
| `effective_fg_pct` | DECIMAL(4,3) | N/A | `PlayerStats.EFG_PCT` | N/A | Calculated | eFG% |
| `usage_rate` | DECIMAL(4,3) | N/A | N/A | N/A | Calculated | USG% |
| `game_score` | DECIMAL(5,2) | N/A | N/A | N/A | Calculated | John Hollinger's Game Score |
| `box_plus_minus` | DECIMAL(5,2) | N/A | N/A | N/A | Calculated | BPM |

---

## Team-Level Field Mappings

### Team Stats Per Game

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `team_points` | INTEGER | `statistics[].points` | `TeamStats.PTS` | `pts` | Table cell | Team total points |
| `team_field_goals_made` | INTEGER | `statistics[].fieldGoalsMade` | `TeamStats.FGM` | `fgm` | Table cell | Team FG made |
| `team_field_goals_attempted` | INTEGER | `statistics[].fieldGoalsAttempted` | `TeamStats.FGA` | `fga` | Table cell | Team FG attempted |
| `team_three_pointers_made` | INTEGER | `statistics[].threePointFieldGoalsMade` | `TeamStats.FG3M` | `fg3m` | Table cell | Team 3PT made |
| `team_free_throws_made` | INTEGER | `statistics[].freeThrowsMade` | `TeamStats.FTM` | `ftm` | Table cell | Team FT made |
| `team_rebounds` | INTEGER | `statistics[].rebounds` | `TeamStats.REB` | `reb` | Table cell | Team total rebounds |
| `team_assists` | INTEGER | `statistics[].assists` | `TeamStats.AST` | `ast` | Table cell | Team assists |
| `team_turnovers` | INTEGER | `statistics[].turnovers` | `TeamStats.TO` | `tov` | Table cell | Team turnovers |
| `team_steals` | INTEGER | `statistics[].steals` | `TeamStats.STL` | `stl` | Table cell | Team steals |
| `team_blocks` | INTEGER | `statistics[].blocks` | `TeamStats.BLK` | `blk` | Table cell | Team blocks |

### Four Factors (Basketball Reference)

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `pace` | DECIMAL(5,2) | N/A | `TeamStats.PACE` | N/A | Calculated | Possessions per 48 min |
| `offensive_rating` | DECIMAL(5,2) | N/A | `TeamStats.OFF_RATING` | N/A | Calculated | Points per 100 poss |
| `defensive_rating` | DECIMAL(5,2) | N/A | `TeamStats.DEF_RATING` | N/A | Calculated | Opp points per 100 poss |
| `effective_fg_pct` | DECIMAL(4,3) | N/A | Calculated | N/A | Calculated | eFG% |
| `turnover_pct` | DECIMAL(4,3) | N/A | Calculated | N/A | Calculated | TOV% |
| `offensive_reb_pct` | DECIMAL(4,3) | N/A | Calculated | N/A | Calculated | ORB% |
| `free_throw_rate` | DECIMAL(4,3) | N/A | Calculated | N/A | Calculated | FT/FGA |

---

## Play-by-Play Field Mappings

### Event Information

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `event_id` | INTEGER | `id` | `PlayByPlay.EVENTNUM` | N/A | N/A | Sequence number |
| `period` | INTEGER | `period.number` | `PlayByPlay.PERIOD` | N/A | N/A | Quarter (1-4) or OT (5+) |
| `clock` | TIME | `clock.displayValue` | `PlayByPlay.PCTIMESTRING` | N/A | N/A | Time remaining in period |
| `event_type` | VARCHAR(50) | `type.text` | `PlayByPlay.EVENTMSGTYPE` | N/A | N/A | 'shot', 'foul', 'turnover', etc. |
| `event_description` | TEXT | `text` | `PlayByPlay.HOMEDESCRIPTION` or `VISITORDESCRIPTION` | N/A | N/A | Human-readable description |
| `team_id` | INTEGER | `team.id` | `PlayByPlay.PLAYER1_TEAM_ID` | N/A | N/A | Team that caused event |
| `player_id` | INTEGER | `participants[0].athlete.id` | `PlayByPlay.PLAYER1_ID` | N/A | N/A | Primary player |
| `player_name` | VARCHAR(100) | `participants[0].athlete.displayName` | Player lookup | N/A | N/A | Primary player name |

### Shot Events

| Canonical Field | Data Type | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref | Notes |
|----------------|-----------|------|---------------|-----------|----------------|-------|
| `shot_made` | BOOLEAN | `scoringPlay` | `PlayByPlay.EVENTMSGTYPE=1` | N/A | N/A | True if made |
| `shot_type` | VARCHAR(20) | `shootingPlay.shotType` | `PlayByPlay.EVENTMSGACTIONTYPE` | N/A | N/A | 'jump shot', 'layup', 'dunk' |
| `shot_distance` | INTEGER | `coordinate.x` (calculated) | `PlayByPlay.SHOT_DISTANCE` | N/A | N/A | Distance in feet |
| `shot_x` | INTEGER | `coordinate.x` | N/A | N/A | N/A | X coordinate on court |
| `shot_y` | INTEGER | `coordinate.y` | N/A | N/A | N/A | Y coordinate on court |
| `shot_value` | INTEGER | Inferred from type | `PlayByPlay.EVENTMSGACTIONTYPE` | N/A | N/A | 2 or 3 points |
| `assist_player_id` | INTEGER | `participants[1].athlete.id` | `PlayByPlay.PLAYER2_ID` | N/A | N/A | Assisting player (if any) |

---

## Transformation Functions

### Universal Transformations

**1. Team Abbreviation Normalization**
```python
def normalize_team_abbr(abbr: str) -> str:
    """
    Normalize team abbreviation to 3-letter uppercase

    Handles variations:
    - LA Lakers → LAL
    - Brooklyn → BKN
    - Golden State → GSW
    """
    abbr_map = {
        'LA LAKERS': 'LAL',
        'LA CLIPPERS': 'LAC',
        'BROOKLYN': 'BKN',
        'GOLDEN STATE': 'GSW',
        'NEW YORK': 'NYK',
        'NEW ORLEANS': 'NOP',
        'SAN ANTONIO': 'SAS',
        # ...all 30 teams
    }

    abbr_upper = abbr.strip().upper()
    return abbr_map.get(abbr_upper, abbr_upper[:3])
```

**2. Player Name Normalization**
```python
import unicodedata
import re

def normalize_player_name(name: str) -> str:
    """
    Normalize player name for matching across sources

    - Remove accents: José → Jose
    - Lowercase: LeBron James → lebron james
    - Remove punctuation: O'Neal → oneal
    - Standardize spacing: "John  Smith" → "john smith"
    """
    # Remove accents
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')

    # Lowercase
    name = name.lower()

    # Remove punctuation except spaces
    name = re.sub(r'[^a-z\s]', '', name)

    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    return name
```

**3. Percentage Conversion**
```python
def convert_percentage(value: any) -> float:
    """
    Convert percentage to decimal (0.0-1.0)

    Handles:
    - ESPN: "45.5" (string)
    - NBA.com: 0.455 (decimal)
    - Kaggle: 45.5 (float)
    - Basketball Ref: "45.5%" (string with %)
    """
    if value is None:
        return None

    # Remove % sign if present
    if isinstance(value, str):
        value = value.replace('%', '').strip()

    value = float(value)

    # Convert to decimal if > 1 (assume it's a percentage)
    if value > 1:
        value = value / 100.0

    return round(value, 3)
```

**4. Time Conversion**
```python
from datetime import time

def convert_game_time(time_str: str) -> time:
    """
    Convert game time to canonical format

    ESPN: "12:05" (MM:SS remaining)
    NBA.com: "12:05" (MM:SS remaining)

    → Canonical: time(00, 12, 05) (HH:MM:SS)
    """
    if not time_str:
        return None

    # Split MM:SS
    parts = time_str.split(':')
    minutes = int(parts[0])
    seconds = int(parts[1]) if len(parts) > 1 else 0

    return time(0, minutes, seconds)
```

**5. Date/Time Conversion**
```python
from datetime import datetime

def convert_datetime(dt_str: str, source: str) -> datetime:
    """
    Convert date/time to canonical format

    ESPN: "2024-12-25T20:00Z" (ISO 8601 UTC)
    NBA.com: "2024-12-25T20:00:00" (no timezone)
    Kaggle: "2024-12-25 20:00:00" (space separator)

    → Canonical: datetime object in UTC
    """
    formats = {
        'espn': '%Y-%m-%dT%H:%M%z',
        'nba_stats': '%Y-%m-%dT%H:%M:%S',
        'kaggle': '%Y-%m-%d %H:%M:%S',
        'bref': '%Y-%m-%d'  # Date only
    }

    fmt = formats.get(source, '%Y-%m-%dT%H:%M:%S')

    # Handle timezone suffix
    if dt_str.endswith('Z'):
        dt_str = dt_str.replace('Z', '+0000')

    return datetime.strptime(dt_str, fmt)
```

---

## ETL Mapping Pipeline

### Step-by-Step Transformation

**Example: Mapping ESPN game data to canonical format**

```python
def map_espn_game_to_canonical(espn_data):
    """
    Transform ESPN API response to canonical RDS schema
    """
    competition = espn_data['header']['competitions'][0]
    home_team = competition['competitors'][0]
    away_team = competition['competitors'][1]

    return {
        # Game identification
        'game_id': espn_data['header']['id'],
        'game_date': map_game_date(competition['date']),
        'game_time': convert_datetime(competition['date'], 'espn').time(),
        'season': espn_data['header']['season']['year'],
        'season_type': map_season_type(espn_data['header']['season']['type']),

        # Team info
        'home_team_id': home_team['id'],
        'home_team_abbr': home_team['team']['abbreviation'],
        'home_team_name': home_team['team']['displayName'],
        'away_team_id': away_team['id'],
        'away_team_abbr': away_team['team']['abbreviation'],
        'away_team_name': away_team['team']['displayName'],

        # Scores
        'home_score': int(home_team['score']) if home_team.get('score') else None,
        'away_score': int(away_team['score']) if away_team.get('score') else None,

        # Venue
        'venue_name': competition.get('venue', {}).get('fullName'),
        'venue_city': competition.get('venue', {}).get('address', {}).get('city'),
        'venue_state': competition.get('venue', {}).get('address', {}).get('state'),
        'attendance': competition.get('attendance'),

        # Metadata
        'data_source': 'espn',
        'created_at': datetime.utcnow()
    }
```

---

## Validation Rules

### Data Type Validation

```python
FIELD_VALIDATORS = {
    'game_date': lambda x: isinstance(x, (date, str)) and len(str(x)) == 10,
    'season': lambda x: isinstance(x, int) and 1946 <= x <= 2030,
    'home_score': lambda x: x is None or (isinstance(x, int) and 0 <= x <= 200),
    'field_goal_percentage': lambda x: x is None or (isinstance(x, float) and 0 <= x <= 1),
    'team_abbr': lambda x: isinstance(x, str) and len(x) == 3,
}

def validate_canonical_data(data):
    """
    Validate data against canonical schema rules
    """
    errors = []

    for field, validator in FIELD_VALIDATORS.items():
        if field in data and not validator(data[field]):
            errors.append(f"Invalid {field}: {data[field]}")

    return errors
```

---

## Best Practices

### DO:
✅ Always use canonical field names in database
✅ Transform at ingestion time (ETL layer)
✅ Validate data types before inserting
✅ Log transformation errors for debugging
✅ Keep source-specific field names in raw data S3

### DON'T:
❌ Store source-specific field names in database
❌ Mix field naming conventions in same table
❌ Skip data type conversions (causes query errors)
❌ Assume field names are consistent across sources
❌ Hard-code transformations (use mapping tables)

---

## Related Documentation

- **[DATA_SOURCE_MAPPING.md](DATA_SOURCE_MAPPING.md)** - ID mapping across sources
- **[DATA_DEDUPLICATION_RULES.md](DATA_DEDUPLICATION_RULES.md)** - Conflict resolution
- **[DATA_SOURCES.md](DATA_SOURCES.md)** - Source overview

---

*Last Updated: October 6, 2025*
*Next Review: After Phase 2 ETL implementation*