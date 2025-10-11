# NBA Data Structure Guide

<!-- AUTO-UPDATE TRIGGER: When discovering new JSON structures or updating ETL field mappings -->
<!-- LAST UPDATED: 2025-10-01 -->

**Purpose:** Complete reference for ESPN NBA JSON data structure across all file types. Critical for writing ETL scripts and understanding data availability.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Quality Summary](#data-quality-summary)
3. [Play-by-Play Files (nba_pbp/)](#play-by-play-files-nba_pbp)
4. [Box Score Files (nba_box_score/)](#box-score-files-nba_box_score)
5. [Team Stats Files (nba_team_stats/)](#team-stats-files-nba_team_stats)
6. [Schedule Files (nba_schedule_json/)](#schedule-files-nba_schedule_json)
7. [ETL Filter Criteria](#etl-filter-criteria)
8. [Field Extraction Map](#field-extraction-map)

---

## Overview

**Total Dataset:** 146,115 JSON files (119 GB in S3)

**Folder Structure:**
```
s3://nba-sim-raw-data-lake/
├── pbp/          44,826 files - Play-by-play game data
├── box_scores/   44,828 files - Box score statistics
├── team_stats/   44,828 files - Team statistics
└── schedule/     11,633 files - Daily game schedules
```

**Key Insight:** Each folder type was scraped from **different ESPN web pages**, so they have **different JSON structures** even for the same game ID.

---

## Data Quality Summary

**Analysis Results** (based on 300-file random samples per folder):

| Folder | Total Files | Valid Files | Valid % | Empty % | Est. Usable |
|--------|-------------|-------------|---------|---------|-------------|
| **nba_pbp** | 44,826 | ~31,378 | 70.0% | 30.0% | ~31,378 |
| **nba_box_score** | 44,828 | ~40,494 | 90.3% | 9.7% | ~40,494 |
| **nba_team_stats** | 44,828 | ~38,103 | 85.0% | 15.0% | ~38,103 |
| **nba_schedule_json** | 11,633 | ~11,633 | 100.0% | 0.0% | ~11,633 |
| **TOTAL** | **146,115** | **~121,608** | **83.2%** | **16.8%** | **~121,608** |

**Storage Impact:**
- Total S3 storage: ~119 GB (all files)
- Usable data: ~99 GB (83%)
- Waste: ~20 GB (17% empty files)

**ETL Impact:**
- Files to skip: ~24,507 (17%)
- Potential cost savings: ~$2.21/month by pre-filtering
- Runtime improvement: ~17% faster

---

## Play-by-Play Files (nba_pbp/)

**Source:** ESPN game detail pages (e.g., `espn.com/nba/game/_/gameId/401307856`)

### Data Availability
- **70% valid** (~31,378 files have play data)
- **30% empty** (~13,448 files have no plays)

### JSON Structure

**Root Path:** `page.content.gamepackage`

**Key Sections:**

#### 1. Play-by-Play Data (`pbp.playGrps`)

```json
{
  "pbp": {
    "playGrps": [
      [  // Period 1 (1st Quarter)
        {
          "id": "4013078567",
          "period": {"number": 1, "displayValue": "1st Quarter"},
          "text": "Markieff Morris makes driving layup",
          "homeAway": "home",
          "awayScore": 0,
          "homeScore": 2,
          "clock": {"displayValue": "11:34"},
          "scoringPlay": true,  // Optional - only on scoring plays
          "athlete": {"id": "6461", "name": "Markieff Morris"}  // Optional
        }
        // ... ~100-150 plays per period
      ],
      [...],  // Period 2
      [...],  // Period 3
      [...]   // Period 4
    ]
  }
}
```

**Stats:**
- **Average:** 468 plays per game (4 periods × ~117 plays/period)
- **Play types:** Shots, fouls, turnovers, timeouts, substitutions, rebounds, assists
- **Keys per play:** `id`, `period`, `text`, `homeAway`, `awayScore`, `homeScore`, `clock`, optional: `scoringPlay`, `athlete`

#### 2. Shot Chart Data (`shtChrt.plays`)

```json
{
  "shtChrt": {
    "plays": [
      {
        "id": "4013078567",
        "period": {"number": 1, "displayValue": "1st Quarter"},
        "text": "Markieff Morris makes driving layup",
        "homeAway": "home",
        "scoringPlay": true,
        "athlete": {"id": "6461", "name": "Markieff Morris"},
        "coordinate": {"x": 25, "y": 3},  // Shot location
        "shootingPlay": true,
        "type": {"id": "110", "txt": "Driving Layup Shot"}
      }
      // ... ~225 shots per game
    ]
  }
}
```

**Stats:**
- **Average:** 225 shots per game
- **Includes:** Shot coordinates (x, y), shot type, make/miss status

#### 3. Game Info (`gmInfo`)

```json
{
  "gmInfo": {
    "attnd": 4087,
    "dtTm": "2021-05-12T21:30:00Z",
    "loc": "Los Angeles, CA",
    "refs": [
      {"dspNm": "John Goble"},
      {"dspNm": "Eric Dalen"},
      {"dspNm": "Curtis Blair"}
    ],
    "venue": "crypto.com Arena"
  }
}
```

### Filter Criteria (ETL)

**✅ Valid file:** `pbp.playGrps` has at least 1 play

```python
# PySpark filter
df_valid = df.filter(
    F.size(F.col("page.content.gamepackage.pbp.playGrps")) > 0
)
```

**❌ Empty file:** `pbp.playGrps` is empty list `[]`

### Sample Files

- **Valid:** `data/nba_pbp/401307856.json` (1.0 MB, 468 plays, 225 shots)
- **Empty:** `data/nba_pbp/131105001.json` (718 KB, 0 plays)

---

## Box Score Files (nba_box_score/)

**Source:** ESPN box score pages (e.g., `espn.com/nba/boxscore/_/gameId/401307856`)

### Data Availability
- **90.3% valid** (~40,494 files have box score data)
- **9.7% empty** (~4,334 files have no box score)

### JSON Structure

**Root Path:** `page.content.gamepackage`

**Key Section:** `bxscr` (list of 2 teams)

```json
{
  "bxscr": [
    {  // Team 1 (home)
      "tm": {
        "id": "13",
        "uid": "s:40~l:46~t:13",
        "displayName": "Los Angeles Lakers",
        "abbreviation": "LAL"
      },
      "stats": [
        {
          "name": "MIN",
          "displayValue": "240"
        },
        {
          "name": "FG",
          "displayValue": "42-88"
        }
        // ... all box score stats
      ]
    },
    {  // Team 2 (away)
      // ... same structure
    }
  ]
}
```

**Note:** Box score files do NOT contain individual player statistics in the sample examined. The `bxscr` section contains team-level aggregated stats.

### Filter Criteria (ETL)

**✅ Valid file:** `bxscr` list has 2 teams

```python
# PySpark filter
df_valid = df.filter(
    F.size(F.col("page.content.gamepackage.bxscr")) >= 2
)
```

---

## Team Stats Files (nba_team_stats/)

**Source:** ESPN team stats pages

### Data Availability
- **85.0% valid** (~38,103 files have team stats)
- **15.0% empty** (~6,725 files have no stats)

### JSON Structure

**Root Path:** `page.content.gamepackage`

**Key Sections:**

```json
{
  "tmStats": {
    "awayTeamStat": [...],
    "homeTeamStat": [...],
    "labels": [...]
  },
  "tmStatsGrph": {
    // Team stats graph data
  },
  "gmLdrs": {
    // Game leaders (top performers)
  }
}
```

### Filter Criteria (ETL)

**✅ Valid file:** `tmStats` dict has keys

```python
# PySpark filter
df_valid = df.filter(
    F.size(F.map_keys(F.col("page.content.gamepackage.tmStats"))) > 0
)
```

---

## Schedule Files (nba_schedule_json/)

**Source:** ESPN daily schedule pages (e.g., `espn.com/nba/schedule/_/date/20210512`)

### Data Availability
- **100% valid** (~11,633 files have schedule data)
- **0% empty** (all schedule files contain games for that date)

### JSON Structure

**Root Path:** `page.content`

**Key Section:** `events` (list of games for that date)

```json
{
  "page": {
    "content": {
      "events": [
        {
          "id": "401307856",
          "date": "2021-05-12T21:30:00Z",
          "name": "Houston Rockets at Los Angeles Lakers",
          "shortName": "HOU @ LAL",
          "competitors": [
            {
              "id": "14",
              "homeAway": "home",
              "team": {
                "id": "13",
                "abbreviation": "LAL",
                "displayName": "Los Angeles Lakers"
              },
              "score": "124"
            },
            {
              "id": "10",
              "homeAway": "away",
              "team": {
                "id": "10",
                "abbreviation": "HOU",
                "displayName": "Houston Rockets"
              },
              "score": "122"
            }
          ],
          "status": {
            "type": {
              "state": "post",
              "completed": true
            }
          },
          "venue": {
            "fullName": "crypto.com Arena",
            "address": {
              "city": "Los Angeles",
              "state": "CA"
            }
          }
        }
        // ... typically 5-15 games per date
      ],
      "calendar": [...],
      "calendarData": {...}
    }
  }
}
```

**Stats:**
- **Average:** 9 games per date
- **Date range:** 1993-2025 (11,633 dates with NBA games)
- **Filename format:** `YYYYMMDD.json` (e.g., `20210512.json`)

### Filter Criteria (ETL)

**All schedule files are valid** - no filtering needed

```python
# No filter required - all files have events
df_schedule = spark.read.json("s3://nba-sim-raw-data-lake/schedule/*.json")
```

---

## ETL Filter Criteria

### Summary Table

| Data Type | JSON Path to Check | Filter Condition | Est. Pass Rate |
|-----------|-------------------|------------------|----------------|
| **Play-by-Play** | `page.content.gamepackage.pbp.playGrps` | Array size > 0 | 70% |
| **Box Scores** | `page.content.gamepackage.bxscr` | Array size >= 2 | 90% |
| **Team Stats** | `page.content.gamepackage.tmStats` | Dict has keys | 85% |
| **Schedule** | `page.content.events` | No filter needed | 100% |

### PySpark Implementation

```python
from pyspark.sql import functions as F

# 1. Play-by-Play - Filter for games with plays
df_pbp = spark.read.json("s3://nba-sim-raw-data-lake/pbp/*.json")
df_pbp_valid = df_pbp.filter(
    F.size(F.col("page.content.gamepackage.pbp.playGrps")) > 0
)
print(f"PBP: {df_pbp.count()} → {df_pbp_valid.count()} files")

# 2. Box Scores - Filter for games with team stats
df_box = spark.read.json("s3://nba-sim-raw-data-lake/box_scores/*.json")
df_box_valid = df_box.filter(
    F.size(F.col("page.content.gamepackage.bxscr")) >= 2
)
print(f"Box: {df_box.count()} → {df_box_valid.count()} files")

# 3. Team Stats - Filter for games with stats
df_team = spark.read.json("s3://nba-sim-raw-data-lake/team_stats/*.json")
df_team_valid = df_team.filter(
    F.size(F.map_keys(F.col("page.content.gamepackage.tmStats"))) > 0
)
print(f"Team: {df_team.count()} → {df_team_valid.count()} files")

# 4. Schedule - No filter needed
df_schedule = spark.read.json("s3://nba-sim-raw-data-lake/schedule/*.json")
print(f"Schedule: {df_schedule.count()} files (all valid)")
```

---

## Field Extraction Map

### Database Schema Mapping

**Target PostgreSQL tables:** (from `sql/create_tables.sql`)

1. **teams** (from schedule/events)
2. **players** (from pbp/plays - athlete info)
3. **games** (from schedule/events)
4. **player_game_stats** (NOT in current files - need different ESPN page)
5. **plays** (from pbp/playGrps)
6. **team_game_stats** (from box_scores/bxscr or team_stats/tmStats)

### Extraction Paths (10% of fields per ADR-002)

#### From Play-by-Play Files (nba_pbp/)

**Table: plays**
```
Source: page.content.gamepackage.pbp.playGrps[period][play]

Extraction:
- play_id          ← id
- game_id          ← (from filename or header)
- period           ← period.number
- clock            ← clock.displayValue
- play_type        ← (infer from text/scoringPlay)
- play_text        ← text
- home_score       ← homeScore
- away_score       ← awayScore
- team_id          ← (map homeAway + header.competitions.competitors)
- player_id        ← athlete.id (if present)
- scoring_play     ← scoringPlay (if present)
```

**Table: players**
```
Source: page.content.gamepackage.pbp.playGrps[period][play].athlete

Extraction:
- player_id        ← id
- player_name      ← name
- position         ← (not in pbp files)
- team_id          ← (map from game context)
```

#### From Box Score Files (nba_box_score/)

**Table: team_game_stats**
```
Source: page.content.gamepackage.bxscr[team]

Extraction:
- game_id          ← (from filename or header)
- team_id          ← tm.id
- team_name        ← tm.displayName
- stats            ← stats[] (parse FG, 3PT, FT, etc.)
```

#### From Schedule Files (nba_schedule_json/)

**Table: games**
```
Source: page.content.events[game]

Extraction:
- game_id          ← id
- game_date        ← date
- home_team_id     ← competitors[homeAway='home'].team.id
- away_team_id     ← competitors[homeAway='away'].team.id
- home_score       ← competitors[homeAway='home'].score
- away_score       ← competitors[homeAway='away'].score
- venue_name       ← venue.fullName
- city             ← venue.address.city
- state            ← venue.address.state
```

**Table: teams**
```
Source: page.content.events[game].competitors[].team

Extraction:
- team_id          ← id
- team_name        ← displayName
- abbreviation     ← abbreviation
- conference       ← (not in schedule files - need separate API)
- division         ← (not in schedule files - need separate API)
```

---

## Notes

### Missing Data

**Fields NOT found in current dataset:**

1. **Individual player box score stats** (points, rebounds, assists per player per game)
   - Required for `player_game_stats` table
   - Not in pbp/, box_scores/, or team_stats/ folders
   - May need to scrape ESPN player stats pages separately

2. **Team conference/division**
   - Not in schedule files
   - May need to scrape ESPN team pages or use static mapping

### Data Quality Issues

See `docs/LESSONS_LEARNED.md` Issue #10 for details on:
- 17% of files are empty (no usable data)
- Validation criteria for each file type
- Impact on ETL costs and performance

### Future Improvements

1. **Create valid file manifest:**
   - Run analysis once, save list of valid file paths
   - Use manifest in ETL to skip empty files without re-checking

2. **Add missing data sources:**
   - Player box scores (if needed for player_game_stats table)
   - Team conference/division (static mapping or additional scrape)

3. **Optimize S3 storage:**
   - Consider moving empty files to separate S3 prefix (optional)
   - Use S3 Intelligent-Tiering for cost optimization

---

## References

- **Analysis Script:** `scripts/analysis/comprehensive_data_analysis.py`
- **Sample Valid Files:** `data/nba_pbp/401307856.json`, `data/nba_schedule_json/20210512.json`
- **Sample Empty Files:** `data/nba_pbp/131105001.json`
- **Database Schema:** `sql/create_tables.sql`
- **ADR-002:** 10% Field Extraction Strategy
- **LESSONS_LEARNED.md:** Issue #10 - Data Quality Issues
