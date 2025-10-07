# Data Source Mapping & ID Crosswalk

**Created:** October 6, 2025
**Purpose:** Map identifiers and data structures across all 5 data sources
**Status:** Phase 1, Sub-Phase 1.6 (Verification Sources Setup)

---

## Overview

This document provides comprehensive mapping between different NBA data sources to enable:
- **Cross-validation:** Verify game scores and statistics across sources
- **Gap filling:** Use alternative sources when primary source is incomplete
- **ID mapping:** Convert between ESPN, NBA.com, and other ID formats

---

## Table of Contents

1. [Identifier Mapping](#identifier-mapping)
2. [Data Structure Comparison](#data-structure-comparison)
3. [Field Mappings by Source](#field-mappings-by-source)
4. [ID Conversion Strategies](#id-conversion-strategies)
5. [Verification Workflows](#verification-workflows)

---

## Identifier Mapping

### Game Identifiers

Each data source uses different game ID formats:

| Source | Game ID Format | Example | Notes |
|--------|----------------|---------|-------|
| **ESPN** | Variable format | `190302004` or `401585647` | See ESPN ID decoding below |
| **NBA.com Stats** | 10-character string | `0022300123` | Format: `00[season][season_type][game_num]` |
| **Kaggle DB** | Integer (primary key) | `12345` | Auto-incremented database ID |
| **SportsDataverse** | Uses ESPN IDs | `401585647` | Wraps ESPN API directly |
| **Basketball Reference** | String slug | `202312250LAL` | Format: `YYYYMMDD0{TEAM}` |

**Key Findings:**
- There is **no direct mapping** between ESPN IDs and NBA.com IDs
- ESPN has **two different ID formats** (legacy and modern)
- **Duplicate game IDs exist** for the same game (different ID systems)

**Solution:** Match games using **date + team combination** instead of game IDs.

---

### ESPN Game ID Decoding

**ESPN uses two formats for game IDs:**

#### Format 1: Legacy Format (Pre-2018) - `YYMMDD###`

**Structure:**
- **YY**: Year code (2 digits)
- **MM**: Month (01-12)
- **DD**: Day (01-31)
- **###**: Sequence number (game number for that day)

**Year Encoding Formula:**
```
Actual Year = 1980 + Year Code
```

**Examples:**
| Game ID | Breakdown | Decoded Date | Formula |
|---------|-----------|--------------|---------|
| `190302004` | 19-03-02-004 | 1999-03-02 (game #4) | 1980 + 19 = 1999 |
| `200104005` | 20-01-04-005 | 2000-01-04 (game #5) | 1980 + 20 = 2000 |
| `311011004` | 31-10-11-004 | 2011-10-11 (game #4) | 1980 + 31 = 2011 |
| `170214021` | 17-02-14-021 | 1997-02-14 (game #21) | 1980 + 17 = 1997 |

**Valid Range:** 1980-2017 (year codes 00-37)

#### Format 2: Modern Format (2018+) - `40########`

**Structure:**
- Starts with `400` or `401`
- 9 digits total
- Date **not encoded** in the ID

**Examples:**
- `401585647` (2024 game)
- `401307856` (2021 game)
- `400975186` (2017-2018 transition)

**Note:** Modern format does not encode the date. You must query ESPN API by ID to get the game date.

#### Duplicate Game IDs

**ESPN has duplicate IDs for the same game:**

Example from March 2, 1999 (Bulls vs Pistons):
- **Legacy ID:** `190302004` → Decodes to 1999-03-02
- **Modern ID:** `400216894` → Same game, different system

**Why duplicates exist:**
- Data migration from old to new system
- Both IDs remain active in ESPN's API
- May have different data completeness

**Verification strategy:**
1. Group games by team matchup (e.g., `DET@CHI`)
2. If multiple IDs found for same matchup, select the one with most complete data (highest score sum)
3. Log duplicate detection for review

---

### Team Identifiers

| Source | Team ID Format | Example (Lakers) | Abbreviation |
|--------|----------------|------------------|--------------|
| **ESPN** | Integer | `13` | `LAL` |
| **NBA.com Stats** | Integer | `1610612747` | `LAL` |
| **Kaggle DB** | Integer | `1610612747` | `LAL` |
| **SportsDataverse** | Uses ESPN IDs | `13` | `LAL` |
| **Basketball Reference** | String | `LAL` | `LAL` |

**Mapping Strategy:** Use **team abbreviation** (3-letter code) as the common key.

**Team Abbreviation Mapping Table:**

| Team | ESPN ID | NBA.com ID | Abbreviation | City | Name |
|------|---------|------------|--------------|------|------|
| Lakers | 13 | 1610612747 | LAL | Los Angeles | Lakers |
| Celtics | 2 | 1610612738 | BOS | Boston | Celtics |
| Warriors | 9 | 1610612744 | GSW | Golden State | Warriors |
| Bulls | 4 | 1610612741 | CHI | Chicago | Bulls |
| Heat | 14 | 1610612748 | MIA | Miami | Heat |
| Knicks | 18 | 1610612752 | NYK | New York | Knicks |
| *...* | *...* | *...* | *...* | *...* | *...* |

**Complete mapping:** See `scripts/mapping/team_id_mapping.json` (to be created)

---

### Player Identifiers

| Source | Player ID Format | Example (LeBron James) |
|--------|------------------|------------------------|
| **ESPN** | Integer | `1966` |
| **NBA.com Stats** | Integer | `2544` |
| **Kaggle DB** | Integer | `2544` (NBA.com format) |
| **SportsDataverse** | Uses ESPN IDs | `1966` |
| **Basketball Reference** | String slug | `jamesle01` |

**Mapping Strategy:** Use **player name + birthdate** for matching across sources.

**Player Name Normalization Rules:**
- Remove accents/diacritics (José → Jose)
- Standardize case (lowercase for matching)
- Handle suffixes consistently (Jr., Sr., III)
- Resolve nicknames (Giannis → Giannis Antetokounmpo)

---

## ID Conversion Reference Table

### Cross-Source Game ID Mapping Strategy

**Problem:** No direct 1:1 mapping exists between ESPN and NBA.com game IDs.

**Solution:** Use composite key matching:

| Matching Strategy | Fields Used | Reliability | Use Case |
|-------------------|-------------|-------------|----------|
| **Date + Teams** | `game_date`, `home_team_abbr`, `away_team_abbr` | 99.9% | Primary matching strategy |
| **Date + Teams + Time** | Above + `game_time` | 99.99% | Rare doubleheader disambiguation |
| **Season + Game Number** | `season`, `game_sequence_num` | 95% | Secondary for season-level queries |
| **ESPN ID Decoding** | Decode legacy IDs → date | 90% | Pre-2018 games only |

**Implementation:**
```python
def match_games_across_sources(game_date: str, home_team: str, away_team: str):
    """
    Match a game across all 5 sources using composite key

    Returns:
        dict with keys: 'espn_id', 'nba_stats_id', 'kaggle_id', 'bref_slug'
    """
    # Normalize team abbreviations to 3-letter codes
    home_abbr = normalize_team_abbr(home_team)
    away_abbr = normalize_team_abbr(away_team)

    # Query each source
    espn_game = query_espn_by_date_teams(game_date, home_abbr, away_abbr)
    nba_game = query_nba_stats_by_date_teams(game_date, home_abbr, away_abbr)
    kaggle_game = query_kaggle_by_date_teams(game_date, home_abbr, away_abbr)
    bref_game = construct_bref_slug(game_date, home_abbr)

    return {
        'espn_id': espn_game['game_id'] if espn_game else None,
        'nba_stats_id': nba_game['game_id'] if nba_game else None,
        'kaggle_id': kaggle_game['id'] if kaggle_game else None,
        'bref_slug': bref_game,
        'match_confidence': calculate_confidence(espn_game, nba_game, kaggle_game)
    }
```

---

### NBA.com Stats ID Format Decoding

**Format:** `00[SEASON][TYPE][GAME_NUM]`

**Structure:**
- **00**: Constant prefix
- **SEASON**: 1-digit season code (last digit of year)
- **TYPE**: 1-digit game type code
- **GAME_NUM**: 5-digit game sequence number

**Game Type Codes:**
| Code | Type | Example |
|------|------|---------|
| `1` | Preseason | `0011300001` |
| `2` | Regular Season | `0022300123` |
| `3` | All-Star | `0032300001` |
| `4` | Playoffs | `0042300101` |

**Examples:**
- `0022300123` → 2023 Regular Season, Game 123
- `0042300401` → 2023 Playoffs, Game 401
- `0032200001` → 2022 All-Star Game

**Decoding Function:**
```python
def decode_nba_stats_id(game_id: str) -> dict:
    """
    Decode NBA.com Stats game ID

    Example: '0022300123' → {'season': 2023, 'type': 'regular', 'game_num': 123}
    """
    if len(game_id) != 10 or not game_id.startswith('00'):
        return None

    season_code = int(game_id[2])
    type_code = int(game_id[3])
    game_num = int(game_id[4:])

    # Map type code to readable type
    type_map = {1: 'preseason', 2: 'regular', 3: 'allstar', 4: 'playoffs'}

    # Calculate full season year (assumes 2000s/2010s/2020s)
    # This is approximate - may need adjustment for older games
    current_decade = 2020
    season = current_decade + season_code

    return {
        'season': season,
        'type': type_map.get(type_code, 'unknown'),
        'game_num': game_num
    }
```

---

### Basketball Reference Slug Format

**Format:** `YYYYMMDD0{TEAM_ABBR}`

**Structure:**
- **YYYY**: 4-digit year
- **MM**: 2-digit month
- **DD**: 2-digit day
- **0**: Constant separator
- **TEAM_ABBR**: 3-letter home team abbreviation

**Examples:**
- `202312250LAL` → Dec 25, 2023, Lakers home game
- `199903020CHI` → Mar 2, 1999, Bulls home game

**URL Construction:**
```python
def construct_bref_url(game_date: str, home_team_abbr: str) -> str:
    """
    Construct Basketball Reference game URL

    Args:
        game_date: 'YYYY-MM-DD' format
        home_team_abbr: 3-letter team code

    Returns:
        Full URL to game page
    """
    date_str = game_date.replace('-', '')  # YYYYMMDD
    slug = f"{date_str}0{home_team_abbr}"
    return f"https://www.basketball-reference.com/boxscores/{slug}.html"
```

**Important:** Basketball Reference uses **lowercase** team abbreviations in URLs (e.g., `lal` not `LAL`).

---

## Data Structure Comparison

### ESPN API Structure

**Endpoint:** `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}`

```json
{
  "header": {
    "id": "401585647",
    "uid": "s:40~l:46~e:401585647",
    "season": {"year": 2024, "type": 2},
    "timeValid": true,
    "competitions": [
      {
        "id": "401585647",
        "uid": "s:40~l:46~e:401585647~c:401585647",
        "date": "2024-12-25T20:00Z",
        "attendance": 18997,
        "venue": {
          "id": "1934",
          "fullName": "Crypto.com Arena",
          "address": {"city": "Los Angeles", "state": "CA"}
        },
        "competitors": [
          {
            "id": "13",
            "uid": "s:40~l:46~t:13",
            "type": "team",
            "order": 0,
            "homeAway": "home",
            "team": {
              "id": "13",
              "uid": "s:40~l:46~t:13",
              "location": "Los Angeles",
              "name": "Lakers",
              "abbreviation": "LAL",
              "displayName": "Los Angeles Lakers",
              "color": "552583",
              "alternateColor": "fdb927"
            },
            "score": "115",
            "winner": true
          },
          {
            "id": "9",
            "uid": "s:40~l:46~t:9",
            "type": "team",
            "order": 1,
            "homeAway": "away",
            "team": {
              "id": "9",
              "abbreviation": "GSW",
              "displayName": "Golden State Warriors"
            },
            "score": "105",
            "winner": false
          }
        ]
      }
    ]
  },
  "boxscore": { /* player stats */ },
  "plays": [ /* play-by-play events */ ]
}
```

**Key Fields for Matching:**
- `header.competitions[0].date` - Game date/time
- `header.competitions[0].competitors[].team.abbreviation` - Team abbreviations (LAL, GSW)
- `header.competitions[0].competitors[].score` - Final scores

---

### NBA.com Stats API Structure

**Endpoint:** `https://stats.nba.com/stats/scoreboardV2?GameDate=2024-12-25`

```json
{
  "resultSets": [
    {
      "name": "GameHeader",
      "headers": ["GAME_DATE_EST", "GAME_ID", "GAME_STATUS_TEXT", "HOME_TEAM_ID", "VISITOR_TEAM_ID"],
      "rowSet": [
        [
          "2024-12-25",
          "0022400123",
          "Final",
          1610612747,  // Lakers (NBA.com ID)
          1610612744,  // Warriors (NBA.com ID)
          "...other fields..."
        ]
      ]
    },
    {
      "name": "LineScore",
      "headers": ["GAME_ID", "TEAM_ID", "TEAM_ABBREVIATION", "PTS"],
      "rowSet": [
        ["0022400123", 1610612747, "LAL", 115],
        ["0022400123", 1610612744, "GSW", 105]
      ]
    }
  ]
}
```

**Key Fields for Matching:**
- `GameHeader.GAME_DATE_EST` - Game date
- `LineScore.TEAM_ABBREVIATION` - Team abbreviation
- `LineScore.PTS` - Final score

---

### Kaggle Database Schema

**Table:** `game`

```sql
CREATE TABLE game (
    id INTEGER PRIMARY KEY,
    game_date TEXT,
    season_id INTEGER,
    team_id_home INTEGER,  -- NBA.com team ID
    team_abbreviation_home TEXT,
    team_id_away INTEGER,
    team_abbreviation_away TEXT,
    pts_home INTEGER,
    pts_away INTEGER,
    -- ...other fields...
);
```

**Key Fields for Matching:**
- `game_date` - Game date (YYYY-MM-DD)
- `team_abbreviation_home` / `team_abbreviation_away` - Team abbreviations
- `pts_home` / `pts_away` - Final scores

---

### SportsDataverse Structure

**Python API:**
```python
from sportsdataverse.nba import espn_nba_pbp

# Returns ESPN data directly (same structure as ESPN API)
game_data = espn_nba_pbp(game_id=401585647)
```

**Uses ESPN IDs and structure** - no additional mapping needed.

---

### Basketball Reference Structure

**URL Pattern:** `https://www.basketball-reference.com/boxscores/202412250LAL.html`

**HTML Table Structure:**
- Game ID in URL: `{YYYYMMDD}0{TEAM}`
- Team abbreviations in table headers
- Scores in table cells

**Scraping:**
```python
import pandas as pd

url = "https://www.basketball-reference.com/boxscores/202412250LAL.html"
tables = pd.read_html(url)
# Extract scores from tables
```

---

## Field Mappings by Source

### Game-Level Fields

| Field | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref |
|-------|------|---------------|-----------|----------------|
| **Game Date** | `header.competitions[0].date` | `GameHeader.GAME_DATE_EST` | `game_date` | URL slug |
| **Home Team** | `competitors[0].team.abbreviation` | `LineScore.TEAM_ABBREVIATION` | `team_abbreviation_home` | Table header |
| **Away Team** | `competitors[1].team.abbreviation` | `LineScore.TEAM_ABBREVIATION` | `team_abbreviation_away` | Table header |
| **Home Score** | `competitors[0].score` | `LineScore.PTS` (home row) | `pts_home` | Table cell |
| **Away Score** | `competitors[1].score` | `LineScore.PTS` (away row) | `pts_away` | Table cell |
| **Attendance** | `header.competitions[0].attendance` | `GameInfo.ATTENDANCE` | `attendance` | Page text |
| **Venue** | `header.competitions[0].venue.fullName` | N/A | N/A | Page text |
| **Season** | `header.season.year` | `GameHeader.SEASON` | `season_id` | URL/page |

### Player-Level Fields

| Field | ESPN | NBA.com Stats | Kaggle DB | Basketball Ref |
|-------|------|---------------|-----------|----------------|
| **Player Name** | `boxscore.players[].athlete.displayName` | `PlayerStats.PLAYER_NAME` | `player_name` | Table row |
| **Points** | `boxscore.players[].stats[].points` | `PlayerStats.PTS` | `pts` | Table cell |
| **Rebounds** | `boxscore.players[].stats[].rebounds` | `PlayerStats.REB` | `reb` | Table cell |
| **Assists** | `boxscore.players[].stats[].assists` | `PlayerStats.AST` | `ast` | Table cell |
| **Minutes** | `boxscore.players[].stats[].minutes` | `PlayerStats.MIN` | `min` | Table cell |
| **FG Made** | `boxscore.players[].stats[].fieldGoalsMade` | `PlayerStats.FGM` | `fgm` | Table cell |
| **FG Attempted** | `boxscore.players[].stats[].fieldGoalsAttempted` | `PlayerStats.FGA` | `fga` | Table cell |

---

## ID Conversion Strategies

### Strategy 1: Date + Team Matching (Recommended)

**Use Case:** Match ESPN games to NBA.com Stats API

**Algorithm:**
1. Extract game date from ESPN data: `2024-12-25`
2. Extract home/away team abbreviations: `LAL`, `GSW`
3. Query NBA.com Stats API for that date
4. Find game where teams match
5. Compare scores

**Python Implementation:**
```python
def match_game_by_date_teams(espn_data, nba_api_data):
    """
    Match ESPN game to NBA.com game using date + teams
    """
    # Extract from ESPN
    espn_date = espn_data['header']['competitions'][0]['date'][:10]
    espn_home = espn_data['header']['competitions'][0]['competitors'][0]['team']['abbreviation']
    espn_away = espn_data['header']['competitions'][0]['competitors'][1]['team']['abbreviation']

    # Search NBA.com games for matching date + teams
    for game in nba_api_data['resultSets'][0]['rowSet']:
        nba_date = game[0]  # GAME_DATE_EST
        nba_home_id = game[3]  # HOME_TEAM_ID
        nba_away_id = game[4]  # VISITOR_TEAM_ID

        # Convert NBA.com IDs to abbreviations
        nba_home_abbr = get_abbr_from_nba_id(nba_home_id)
        nba_away_abbr = get_abbr_from_nba_id(nba_away_id)

        # Match on date + teams
        if (espn_date == nba_date and
            espn_home == nba_home_abbr and
            espn_away == nba_away_abbr):
            return game  # Found matching game

    return None  # No match found
```

---

### Strategy 2: Team Abbreviation Lookup

**Use Case:** Convert between ESPN team IDs and NBA.com team IDs

**Mapping Table:** `scripts/mapping/team_id_mapping.json`

```json
{
  "LAL": {
    "espn_id": 13,
    "nba_id": 1610612747,
    "name": "Los Angeles Lakers",
    "city": "Los Angeles",
    "abbreviation": "LAL"
  },
  "BOS": {
    "espn_id": 2,
    "nba_id": 1610612738,
    "name": "Boston Celtics",
    "city": "Boston",
    "abbreviation": "BOS"
  }
  // ...all 30 teams
}
```

**Python Implementation:**
```python
import json

with open('scripts/mapping/team_id_mapping.json') as f:
    TEAM_MAPPING = json.load(f)

def espn_id_to_nba_id(espn_id):
    """Convert ESPN team ID to NBA.com team ID"""
    for abbr, data in TEAM_MAPPING.items():
        if data['espn_id'] == espn_id:
            return data['nba_id']
    return None

def get_abbr_from_nba_id(nba_id):
    """Get team abbreviation from NBA.com ID"""
    for abbr, data in TEAM_MAPPING.items():
        if data['nba_id'] == nba_id:
            return abbr
    return None
```

---

### Strategy 3: Player Name + Birthdate Matching

**Use Case:** Match players across sources when player IDs differ

**Algorithm:**
1. Normalize player names (lowercase, remove punctuation)
2. If multiple players with same name, use birthdate
3. Create player mapping table

**Python Implementation:**
```python
import re

def normalize_player_name(name):
    """Normalize player name for matching"""
    name = name.lower()
    name = re.sub(r'[^a-z\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
    return name

def match_player(espn_name, nba_name):
    """Check if two player names match"""
    return normalize_player_name(espn_name) == normalize_player_name(nba_name)
```

---

## Verification Workflows

### Workflow 1: Score Verification (ESPN vs NBA.com)

**Goal:** Verify ESPN scores match official NBA.com scores

**Steps:**
1. Sample 100 random games from ESPN S3 data
2. For each game:
   - Extract: date, home team, away team, scores
   - Query NBA.com API: scoreboardV2 for that date
   - Match game using date + team abbreviations
   - Compare scores
3. Log discrepancies to `docs/VERIFICATION_RESULTS.md`

**Success Criteria:**
- ≥99% score accuracy
- ≥95% games found in both sources

**Script:** `scripts/etl/verify_with_nba_stats.py` (needs update for date+team matching)

---

### Workflow 2: Historical Gap Filling (Kaggle DB)

**Goal:** Fill pre-1999 games using Kaggle database

**Steps:**
1. Download Kaggle basketball database
2. Extract games from 1946-1998
3. Convert to ESPN-compatible format
4. Upload to S3: `s3://nba-sim-raw-data-lake/kaggle/`
5. Mark source in database: `data_source = 'kaggle'`

**Script:** `scripts/etl/fill_gaps_from_kaggle.py` (to be created)

---

### Workflow 3: SportsDataverse Cross-Check

**Goal:** Verify our ESPN parsing logic against SportsDataverse

**Steps:**
1. Select 10 random ESPN game IDs
2. Fetch same games using SportsDataverse API
3. Compare parsed results field-by-field
4. Ensure we're extracting same values

**Script:** `scripts/etl/verify_with_sportsdataverse.py` (to be created)

---

## Implementation Checklist

### Immediate (Phase 1)
- [ ] Create team ID mapping table: `scripts/mapping/team_id_mapping.json`
- [ ] Update `verify_with_nba_stats.py` to use date+team matching
- [ ] Run verification and generate VERIFICATION_RESULTS.md

### Short-term (Phase 2-3)
- [ ] Create player ID mapping table (if needed for ETL)
- [ ] Implement Kaggle database download script
- [ ] Extract historical games (1946-1998) from Kaggle

### Long-term (Phase 5+)
- [ ] Implement Basketball Reference scraper for advanced stats
- [ ] Create unified data quality dashboard
- [ ] Automated discrepancy resolution

---

## Key Takeaways

1. ✅ **No direct game ID mapping** exists between ESPN and NBA.com
2. ✅ **Solution:** Match using date + team abbreviations
3. ✅ **Team abbreviations** are the universal key across all sources
4. ✅ **SportsDataverse** uses ESPN IDs directly (no conversion needed)
5. ⚠️ **Player matching** requires name normalization (different IDs across sources)

---

## Related Documentation

- **[DATA_SOURCES.md](DATA_SOURCES.md)** - Overview of all 5 data sources
- **[PHASE_1_FINDINGS.md](PHASE_1_FINDINGS.md)** - Data quality analysis results
- **[DATA_STRUCTURE_GUIDE.md](DATA_STRUCTURE_GUIDE.md)** - Detailed ESPN S3 structure

---

*Last Updated: October 6, 2025*
*Next Review: After implementing verification scripts*