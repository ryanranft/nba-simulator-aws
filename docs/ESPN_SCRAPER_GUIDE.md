# ESPN Scraper Guide

**Last Updated:** October 9, 2025
**Scraper Location:** `~/0espn/`
**Current Data:** 44,826 games (1993-2025), 14.1M play-by-play events

---

## Overview

The ESPN scraper is an external Python package located in `~/0espn/` that scrapes NBA data from ESPN's JSON APIs. It has been running since 2024 and has collected comprehensive NBA data from 1993-2025.

---

## Scraper Location & Structure

**Root Directory:** `/Users/ryanranft/0espn/`

```
~/0espn/
├── espn/
│   └── nba/
│       ├── nba_schedule.py         # Schedule scraper (dates→game IDs)
│       ├── nba_schedule_2.py       # Alternative schedule scraper
│       ├── nba_box_score.py        # Box score scraper
│       ├── nba_pbp.py              # Play-by-play scraper
│       ├── nba_pbp_json.py         # PBP JSON processor
│       ├── nba_team_stats_json.py  # Team stats processor
│       └── ...
├── data/
│   └── nba/                        # Output directory for scraped JSON files
├── .env                            # Configuration (API keys if needed)
└── main.py                         # Main scraper entry point
```

**Data Output:** `/Users/ryanranft/0espn/data/nba/`
**Project Data:** `/Users/ryanranft/nba-simulator-aws/data/nba_pbp/` (44,826 files synced)

---

## How the Scraper Works

### 1. Date Range Configuration

The scraper is configured with a date range in `nba_schedule.py`:

```python
# Lines 137-138
start_date = datetime.date(1993, 8, 25)
end_date = datetime.date(2025, 6, 30)
```

**To update for new seasons:**
1. Open `~/0espn/espn/nba/nba_schedule.py`
2. Update `end_date` to extend coverage
3. Re-run scraper

### 2. API Endpoints Used

**Schedule API:**
```
https://www.espn.com/nba/schedule/_/date/{YYYYMMDD}&_xhr=1
```

**Game Data APIs:**
- Box Score: `https://www.espn.com/nba/boxscore/_/gameId/{game_id}`
- Play-by-Play: `https://www.espn.com/nba/playbyplay/_/gameId/{game_id}`
- Team Stats: `https://www.espn.com/nba/matchup/_/gameId/{game_id}`

### 3. Data Collected

**Per Game:**
- Game metadata (date, teams, venue, scores)
- Box scores (player stats)
- Play-by-play events (quarter-by-quarter)
- Team statistics
- Broadcast information
- Venue details

---

## Running the Scraper

### Manual Execution

```bash
# Activate conda environment (if needed)
conda activate espn-scraper  # Or appropriate environment

# Navigate to scraper directory
cd ~/0espn

# Run schedule scraper
python espn/nba/nba_schedule.py

# Expected runtime:
# - 1 day of schedule: ~1-2 seconds
# - Full 1993-2025 range: ~8-12 hours

# Output: data/nba/*.json files
```

### Using Project Auto-Update Script

**From project directory:**
```bash
cd /Users/ryanranft/nba-simulator-aws

# Run auto-update script (detects gaps and scrapes)
bash scripts/etl/auto_update_espn_data.sh

# This script:
# 1. Checks latest date in S3
# 2. Detects gaps since latest date
# 3. Updates scraper end_date
# 4. Runs ESPN scraper
# 5. Uploads new files to S3
# 6. Loads to RDS (optional)
```

### Manual Gap Filling

```bash
# Scrape specific date range
python scripts/etl/scrape_missing_espn_data.py \
    --start-date 2024-10-01 \
    --end-date 2025-04-13 \
    --upload-to-s3

# This uses ESPN API directly (doesn't require ~/0espn)
```

---

## Data Coverage Analysis

### Current Status (October 2025)

**Total Files:** 44,826 games
**Date Range:** 1993-11-06 to 2025-04-13
**Storage:** 40 GB local, 119 GB in S3

### Coverage by Era

| Era | Years | Games | With PBP | Coverage | Avg Events/Game |
|-----|-------|-------|----------|----------|----------------|
| **Early** | 1993-2001 | 11,210 | 590 | 5.3% | 22 |
| **Digital** | 2002-2010 | 14,464 | 12,569 | 86.9% | 382 |
| **Modern** | 2011-2025 | 19,152 | 18,082 | 94.4% | 435 |

**Key Findings:**
- **1993-2001:** Metadata only, minimal play-by-play (5.3%)
- **2002-2010:** Good PBP coverage (86.9%), ~382 events/game
- **2011-2025:** Excellent PBP coverage (94.4%), ~435 events/game

### Best Coverage Years

| Year | Games | PBP Coverage | Avg Events |
|------|-------|--------------|------------|
| 2018 | 1,383 | 99.9% | 477 |
| 2023 | 1,395 | 99.9% | 466 |
| 2013 | 1,438 | 99.9% | 450 |
| 2022 | 1,391 | 99.8% | 470 |
| 2016 | 1,415 | 99.8% | 456 |

---

## Daily Update Workflow

### Recommended Schedule

**Frequency:** Daily (during season), Weekly (off-season)

**Steps:**
1. Check for new games (compare latest date with today)
2. Run scraper if gaps detected
3. Upload new files to S3
4. Load to local SQLite database
5. Optional: Load to RDS

### Automation Options

**Option 1: Cron Job (Recommended)**
```bash
# Add to crontab (run daily at 3 AM)
0 3 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/etl/auto_update_espn_data.sh >> /tmp/espn_daily_update.log 2>&1
```

**Option 2: Manual (Session Start)**
```bash
# Run at start of each session
bash scripts/etl/auto_update_espn_data.sh
```

**Option 3: AWS Lambda (Future)**
- Trigger daily at 3 AM UTC
- Check S3 for latest date
- Run scraper on EC2 spot instance
- Upload results to S3

---

## Data Storage Locations

### 1. ESPN Scraper Output (~/0espn)
**Location:** `/Users/ryanranft/0espn/data/nba/`
**Format:** Individual JSON files per date (schedule)
**Purpose:** Raw scraper output

### 2. Project Data (nba-simulator-aws)
**Location:** `/Users/ryanranft/nba-simulator-aws/data/nba_pbp/`
**Files:** 44,826 game JSON files
**Size:** 40 GB
**Purpose:** Working copy for local processing

### 3. S3 Bucket (Cloud Storage)
**Bucket:** `s3://nba-sim-raw-data-lake/`
**Prefixes:**
- `schedule/` - Schedule files by date
- `box_scores/` - Box scores by game ID
- `team_stats/` - Team statistics by game ID
- `pbp/` - Play-by-play events (not yet uploaded from local)

**Files:** 146,115 total
**Size:** 119 GB
**Purpose:** Persistent cloud storage, AWS Glue input

### 4. Local SQLite Database (Fast Queries)
**Location:** `/tmp/espn_local.db`
**Size:** 1.7 GB
**Records:**
- 44,826 games
- 14.1M play-by-play events
**Purpose:** Fast local queries without RDS costs

### 5. RDS PostgreSQL (Production)
**Host:** `nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com`
**Database:** `nba_simulator`
**Tables:**
- `games` - Game metadata
- `temporal_events` - Play-by-play events with wall clock timestamps
**Status:** Needs loading (ESPN events not yet loaded)

---

## Data Sync Workflow

```
ESPN Scraper (~/0espn)
    ↓ (generates)
Raw JSON files (/Users/ryanranft/0espn/data/nba/)
    ↓ (copy to)
Project Data (/Users/ryanranft/nba-simulator-aws/data/nba_pbp/)
    ↓ (upload to)
S3 Bucket (s3://nba-sim-raw-data-lake/)
    ↓ (load to)
Local SQLite (/tmp/espn_local.db) ← Fast queries
    ↓ (load to)
RDS PostgreSQL (Production database) ← ML training
```

---

## Troubleshooting

### Issue: Scraper Not Finding Games

**Symptoms:** Schedule API returns empty `events` array

**Causes:**
- Date range outside NBA season (June-September)
- API endpoint changed
- Rate limiting

**Solutions:**
1. Check date range in `nba_schedule.py`
2. Verify API endpoint still works: `curl "https://www.espn.com/nba/schedule/_/date/20241225&_xhr=1"`
3. Add delay between requests (currently 1-2 seconds)

### Issue: Play-by-Play Data Missing

**Symptoms:** Games have metadata but no PBP events

**Causes:**
- Pre-2002 games often lack PBP
- Game not yet played (future game)
- API didn't return PBP data

**Solutions:**
1. Check game date (pre-2002 games have 5.3% PBP coverage)
2. Verify game status (only completed games have full PBP)
3. Re-scrape specific game: `python espn/nba/nba_pbp.py --game-id XXXXXXXXX`

### Issue: Files Not Syncing to S3

**Symptoms:** Local files exist but not in S3

**Causes:**
- AWS credentials not configured
- S3 sync not run
- Network issues

**Solutions:**
1. Check AWS credentials: `aws s3 ls s3://nba-sim-raw-data-lake/`
2. Manually sync: `aws s3 sync ~/0espn/data/nba/ s3://nba-sim-raw-data-lake/schedule/`
3. Use auto-update script: `bash scripts/etl/auto_update_espn_data.sh`

---

## Data Quality Notes

### Play-by-Play Coverage Quality

**Excellent (99%+ coverage):**
- 2013-2023 seasons
- All regular season and playoff games
- ~450-470 events per game

**Good (85-95% coverage):**
- 2002-2012 seasons
- Most regular season games
- ~380-440 events per game

**Poor (< 10% coverage):**
- 1993-2001 seasons
- Metadata only, minimal PBP
- ~20-30 events per game (when available)

### Known Limitations

1. **Player IDs Missing:** ESPN PBP doesn't include player IDs (use NBA API for mapping)
2. **Timestamps:** Minute-level precision only (game clock, not wall clock)
3. **Historical Data:** Pre-2002 games lack detailed play-by-play
4. **Shot Coordinates:** Not available in ESPN data (use NBA API for shot charts)

---

## Integration with Other Data Sources

### ESPN Provides:
✅ Game metadata (date, teams, scores)
✅ Play-by-play text descriptions
✅ Box scores (basic stats)
✅ Venue information
✅ Broadcast details

### ESPN Does NOT Provide:
❌ Player IDs (need NBA API)
❌ Shot coordinates (need NBA API or hoopR)
❌ Advanced stats (need NBA API)
❌ Lineup data (need hoopR or NBA API)
❌ Tracking data (need NBA API)

### Recommended Supplements:
- **hoopR:** Lineups, shot charts, advanced stats (1997-2021)
- **NBA API:** Player IDs, shot coordinates, tracking (1996-2025)
- **Basketball Reference:** Historical validation (1946-2025)

---

## Next Steps

1. ✅ **Local Database Created:** `/tmp/espn_local.db` (1.7 GB)
2. ⏸️ **Compare with RDS:** `python scripts/analysis/compare_espn_local_vs_rds.py`
3. ⏸️ **Load to RDS:** `python scripts/db/load_espn_events.py`
4. ⏸️ **Daily Automation:** Set up cron job for auto-updates
5. ⏸️ **Supplement with NBA API:** Scrape player IDs and shot data

---

## References

- **Auto-Update Script:** `scripts/etl/auto_update_espn_data.sh`
- **Manual Scraper:** `scripts/etl/scrape_missing_espn_data.py`
- **Local Database Creation:** `scripts/db/create_local_espn_database.py`
- **RDS Loader:** `scripts/db/load_espn_events.py`
- **Comparison Tool:** `scripts/analysis/compare_espn_local_vs_rds.py`
- **Data Sources:** `docs/DATA_SOURCES.md`

---

*For questions or issues, see `docs/TROUBLESHOOTING.md` or LESSONS_LEARNED.md*
