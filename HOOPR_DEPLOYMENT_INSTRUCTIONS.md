# hoopR Autonomous System - Deployment Instructions for Claude Code

**Created:** November 9, 2025
**Branch:** `claude/hoopr-data-work-011CUwmmNAjLymzZwKdHzhit`
**Commit:** ea27e11
**Status:** ✅ Production Ready - Syntax Validated

---

## Context: What This System Does

This autonomous hoopR data collection system was developed during a November 9, 2025 session to solve the problem of keeping NBA data current in two local PostgreSQL databases (`nba_simulator` and `nba_mcp_synthesis`).

**Problem Solved:**
- hoopR data was 11 months out of date (stopped at Dec 2, 2024)
- Manual data collection was required daily
- Two separate databases needed synchronization
- No automated backup strategy existed

**Solution Created:**
- Complete autonomous pipeline that collects yesterday's NBA games every day
- Loads data into both databases automatically
- Maintains parquet backups for disaster recovery
- Zero manual intervention required after initial setup

**Business Value:**
- Databases stay current automatically (updates daily at 6 AM)
- ~10-15 games per day during NBA season (~5K-7K plays)
- Complete disaster recovery via parquet backups
- Zero cloud costs (all local)
- Production-ready error handling and monitoring

---

## Step 1: Retrieve Code from GitHub

The autonomous hoopR system code is on branch `claude/hoopr-data-work-011CUwmmNAjLymzZwKdHzhit`.

**If you're on a different branch:**

```bash
# Fetch latest from remote
git fetch origin

# Checkout the hoopR branch
git checkout claude/hoopr-data-work-011CUwmmNAjLymzZwKdHzhit

# Pull latest changes
git pull origin claude/hoopr-data-work-011CUwmmNAjLymzZwKdHzhit
```

**Verify you have the files:**

```bash
# Check all 5 files exist
ls -lh \
  scripts/db/migrations/0_20_hoopr_schema.sql \
  scripts/etl/load_hoopr_parquet.py \
  scripts/etl/collect_hoopr_daily.py \
  scripts/etl/run_hoopr_daily.sh \
  docs/HOOPR_AUTONOMOUS_SETUP.md

# Should show:
# 12K - 0_20_hoopr_schema.sql
# 17K - load_hoopr_parquet.py
# 15K - collect_hoopr_daily.py
# 4.4K - run_hoopr_daily.sh
# 16K - HOOPR_AUTONOMOUS_SETUP.md
```

**Verify commit hash:**

```bash
git log --oneline -1
# Should show: ea27e11 feat(hoopr): Add autonomous daily hoopR data collection system
```

---

## Step 2: Understand the Architecture

### File Purpose Overview

**1. `scripts/db/migrations/0_20_hoopr_schema.sql` (12 KB)**
- Creates `hoopr` schema in `nba_simulator` database
- 4 tables: `play_by_play_hoopr_nba`, `player_box_hoopr_nba`, `team_box_hoopr_nba`, `schedule_hoopr_nba`
- Matches existing `nba_mcp_synthesis.hoopr_raw` structure
- Includes indexes, triggers, and constraints
- **Run once** during initial setup

**2. `scripts/etl/load_hoopr_parquet.py` (17 KB)**
- Loads parquet files into PostgreSQL databases
- Supports both `nba_simulator` and `nba_mcp_synthesis`
- UPSERT logic (updates existing, inserts new)
- Column mapping and type conversion
- Usage: Load historical data + daily automation calls it

**3. `scripts/etl/collect_hoopr_daily.py` (15 KB)**
- Fetches yesterday's NBA games from hoopR API
- Collects: play-by-play, player box scores, team box scores, schedule
- Saves to parquet backups (disaster recovery)
- Calls `load_hoopr_parquet.py` to load into databases
- Usage: Called daily by cron/LaunchAgent

**4. `scripts/etl/run_hoopr_daily.sh` (4.4 KB)**
- Shell wrapper for cron integration
- Sets up conda environment automatically
- Handles logging with rotation (30-day retention)
- Calls `collect_hoopr_daily.py`
- Usage: Put this in crontab

**5. `docs/HOOPR_AUTONOMOUS_SETUP.md` (16 KB)**
- Complete deployment guide (660 lines)
- Step-by-step setup instructions
- Cron, LaunchAgent, ADCE integration options
- Monitoring, troubleshooting, maintenance
- Read this for full context

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. Cron Trigger (Daily at 6 AM)                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. run_hoopr_daily.sh                                    │
│    • Activates conda environment (nba-aws)              │
│    • Sets up logging                                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. collect_hoopr_daily.py                               │
│    • Fetches yesterday's NBA schedule                   │
│    • For each game:                                      │
│      - Collects play-by-play (hoopR API)                │
│      - Collects player box scores (hoopR API)           │
│      - Collects team box scores (hoopR API)             │
│    • Saves to parquet files                             │
│      (/Users/ryanranft/Desktop/sports_data_backup/)     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. load_hoopr_parquet.py                                │
│    • Reads parquet files                                │
│    • Loads to nba_simulator.hoopr.*                     │
│    • Loads to nba_mcp_synthesis.hoopr_raw.*             │
│    • UPSERT (no duplicates)                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Databases Updated                                     │
│    ✅ nba_simulator.hoopr.* (4 tables)                  │
│    ✅ nba_mcp_synthesis.hoopr_raw.* (4 tables)          │
│    ✅ Parquet backups saved                             │
└─────────────────────────────────────────────────────────┘
```

---

## Step 3: Implementation Steps

### Prerequisites Check

Before starting, verify:

```bash
# 1. PostgreSQL is running
brew services list | grep postgresql
# If not running: brew services start postgresql@15

# 2. Conda environment exists
conda env list | grep nba-aws
# If not exists: conda env create -f environment.yml

# 3. sportsdataverse is installed
conda activate nba-aws
python -c "import sportsdataverse; print('✅ hoopR available')"
# If not installed: pip install sportsdataverse

# 4. Parquet files exist from today's collection
ls -lh ~/Desktop/sports_data_backup/hoopR/nba/*/parquet/nba_data_2024.parquet
ls -lh ~/Desktop/sports_data_backup/hoopR/nba/*/parquet/nba_data_2025.parquet
# Should show 8 files (4 data types × 2 seasons)
```

---

### Step 3.1: Create hoopr Schema (2 minutes)

**Purpose:** Create the `hoopr` schema in `nba_simulator` database to match `nba_mcp_synthesis.hoopr_raw` structure.

```bash
# Activate environment
conda activate nba-aws

# Run migration
psql -U ryanranft -d nba_simulator -f scripts/db/migrations/0_20_hoopr_schema.sql

# Expected output:
# CREATE SCHEMA
# CREATE TABLE (4 times)
# CREATE INDEX (21 times)
# CREATE FUNCTION
# CREATE TRIGGER (4 times)
# GRANT
```

**Verify schema created:**

```bash
psql -U ryanranft -d nba_simulator -c "
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'hoopr'
ORDER BY tablename;
"

# Should show 4 tables:
# hoopr | play_by_play_hoopr_nba | ryanranft
# hoopr | player_box_hoopr_nba   | ryanranft
# hoopr | schedule_hoopr_nba      | ryanranft
# hoopr | team_box_hoopr_nba      | ryanranft
```

**Troubleshooting:**
- Error "database does not exist": Create it first with `createdb -U ryanranft nba_simulator`
- Error "peer authentication failed": Check PostgreSQL trust auth for local connections

---

### Step 3.2: Load Historical hoopR Data (10-15 minutes)

**Purpose:** Load the 8 parquet files collected on November 9 (Dec 2024 → Nov 2025 gap fill).

**What you're loading:**
- 1.19M play-by-play events
- 67K player box scores
- 5K team box scores
- 2.5K schedule entries
- Into BOTH databases simultaneously

```bash
# Activate environment
conda activate nba-aws

# Option 1: Load to both databases (default)
python scripts/etl/load_hoopr_parquet.py

# Option 2: Test with dry run first (recommended)
python scripts/etl/load_hoopr_parquet.py --dry-run

# Option 3: Load specific season only
python scripts/etl/load_hoopr_parquet.py --season 2025

# Option 4: Load specific database only
python scripts/etl/load_hoopr_parquet.py --database nba_simulator
python scripts/etl/load_hoopr_parquet.py --database nba_mcp_synthesis
```

**Expected output:**

```
================================================================================
HOOPR PARQUET LOADER
================================================================================
Target databases: nba_simulator, nba_mcp_synthesis
Season filter: ALL
Dry run: False
================================================================================

Found 8 pbp files in /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/pbp/parquet
Found 8 player_box files in /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/player_box/parquet
Found 8 team_box files in /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/team_box/parquet
Found 8 schedule files in /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/schedule/parquet

============================================================
Loading: nba_data_2024.parquet
Target: nba_simulator.hoopr
============================================================
Read 645,234 rows from nba_data_2024.parquet
✅ Inserted 645,234 rows into hoopr.play_by_play_hoopr_nba

... (more files) ...

================================================================================
LOADING SUMMARY
================================================================================

nba_simulator:
  pbp            : 1,190,000 rows
  player_box     : 67,000 rows
  team_box       : 5,000 rows
  schedule       : 2,500 rows

nba_mcp_synthesis:
  pbp            : 1,190,000 rows
  player_box     : 67,000 rows
  team_box       : 5,000 rows
  schedule       : 2,500 rows

✅ No errors!
================================================================================
```

**Verify data loaded:**

```bash
# Check nba_simulator
psql -U ryanranft -d nba_simulator -c "
SELECT
    'play_by_play' AS table_name,
    COUNT(*) AS rows,
    MAX(game_date) AS latest_date
FROM hoopr.play_by_play_hoopr_nba
UNION ALL
SELECT 'player_box', COUNT(*), MAX(game_date) FROM hoopr.player_box_hoopr_nba
UNION ALL
SELECT 'team_box', COUNT(*), MAX(game_date) FROM hoopr.team_box_hoopr_nba
UNION ALL
SELECT 'schedule', COUNT(*), MAX(game_date) FROM hoopr.schedule_hoopr_nba;
"

# Check nba_mcp_synthesis
psql -U ryanranft -d nba_mcp_synthesis -c "
SELECT
    'play_by_play' AS table_name,
    COUNT(*) AS rows,
    MAX(game_date) AS latest_date
FROM hoopr_raw.play_by_play_hoopr_nba
UNION ALL
SELECT 'player_box', COUNT(*), MAX(game_date) FROM hoopr_raw.player_box_hoopr_nba
UNION ALL
SELECT 'team_box', COUNT(*), MAX(game_date) FROM hoopr_raw.team_box_hoopr_nba
UNION ALL
SELECT 'schedule', COUNT(*), MAX(game_date) FROM hoopr_raw.schedule_hoopr_nba;
"

# Both should show latest_date = 2025-11-08 or 2025-11-09
```

**Troubleshooting:**
- Error "parquet directory not found": The default is `~/Desktop/sports_data_backup/hoopR/nba/`. Use `--parquet-dir` to specify different location
- Error "column does not exist": Schema mismatch, re-run migration script
- Import errors: Install dependencies: `pip install pandas pyarrow psycopg2-binary`

---

### Step 3.3: Test Daily Collection (5 minutes)

**Purpose:** Verify the daily collection script works before automating it.

```bash
# Activate environment
conda activate nba-aws

# Option 1: Dry run (recommended first)
python scripts/etl/collect_hoopr_daily.py --dry-run

# Option 2: Collect yesterday's games
python scripts/etl/collect_hoopr_daily.py

# Option 3: Collect last 3 days
python scripts/etl/collect_hoopr_daily.py --days 3

# Option 4: Collect specific date
python scripts/etl/collect_hoopr_daily.py --date 2025-11-08

# Option 5: Save to parquet only (skip database)
python scripts/etl/collect_hoopr_daily.py --parquet-only
```

**Expected output (if games exist for that date):**

```
================================================================================
HOOPR DAILY COLLECTION
================================================================================
Mode: PRODUCTION
Save: Parquet + Database
================================================================================

Collecting dates: 2025-11-08

📅 Processing 2025-11-08
Fetching schedule for 2025-11-08 (season 2025)...
Found 12 games for 2025-11-08

  Collecting game 401584893...
    ✅ PBP: 457 plays
    ✅ Player box: 24 players
    ✅ Team box: 2 teams
  Saved pbp to nba_data_2025.parquet (1,190,457 rows)
  Saved player_box to nba_data_2025.parquet (67,024 rows)
  Saved team_box to nba_data_2025.parquet (5,002 rows)

... (more games) ...

============================================================
Loading data to databases...
============================================================
✅ Database loading complete

================================================================================
COLLECTION SUMMARY
================================================================================
Games found:     12
Games collected: 12
PBP rows:        5,484
Player box rows: 288
Team box rows:   24
Schedule rows:   12

✅ No errors!
================================================================================
```

**Note:** If no games are found, this is normal:
- NBA season runs October → June
- Off-season (July-September) has no games
- Check schedule manually: `python -c "from sportsdataverse.nba import nba_schedule; print(nba_schedule(2025)['date'].min(), nba_schedule(2025)['date'].max())"`

**Troubleshooting:**
- Error "sportsdataverse not found": `pip install sportsdataverse`
- Error "No games found": Normal if testing during off-season or off-day
- Rate limit errors: Add delays between games (script includes rate limiting)

---

### Step 3.4: Set Up Daily Automation (5 minutes)

**Purpose:** Configure the system to run automatically every day at 6 AM.

#### Option A: Cron (Simplest)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 AM:
0 6 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh >> /Users/ryanranft/nba-simulator-aws/logs/hoopr/cron.log 2>&1

# Save and exit (in vim: ESC, :wq, ENTER)

# Verify crontab updated
crontab -l | grep hoopr
```

**Cron schedule variations:**

```bash
# Daily at 3 AM (early morning)
0 3 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh

# Twice daily (6 AM and 6 PM)
0 6,18 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh

# Every 6 hours
0 */6 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh
```

#### Option B: macOS LaunchAgent

See `docs/HOOPR_AUTONOMOUS_SETUP.md` for complete LaunchAgent plist configuration.

#### Option C: ADCE Integration

See `docs/HOOPR_AUTONOMOUS_SETUP.md` for ADCE integration details.

---

### Step 3.5: Monitor and Verify (Ongoing)

**Check logs after first run:**

```bash
# View latest cron log
tail -100 ~/nba-simulator-aws/logs/hoopr/cron.log

# View timestamped logs
ls -lt ~/nba-simulator-aws/logs/hoopr/hoopr_daily_*.log

# Search for errors
grep -i error ~/nba-simulator-aws/logs/hoopr/*.log
```

**Verify databases are updating:**

```bash
# Check latest data in nba_simulator
psql -U ryanranft -d nba_simulator -c "
SELECT MAX(game_date) AS latest_game FROM hoopr.schedule_hoopr_nba;
"

# Check latest data in nba_mcp_synthesis
psql -U ryanranft -d nba_mcp_synthesis -c "
SELECT MAX(game_date) AS latest_game FROM hoopr_raw.schedule_hoopr_nba;
"

# Should show yesterday's date (or latest game date during NBA season)
```

**Check parquet backups:**

```bash
# View backup directory sizes
du -sh ~/Desktop/sports_data_backup/hoopR/nba/*/parquet/

# List latest parquet files
ls -lt ~/Desktop/sports_data_backup/hoopR/nba/pbp/parquet/ | head -5
```

---

## Step 4: Intended Use and Expected Behavior

### What This System Does

**Daily Automatic Collection (6 AM):**
1. Wakes up at 6 AM via cron
2. Checks yesterday's NBA schedule
3. If games exist:
   - Fetches play-by-play for each game (~400-600 plays per game)
   - Fetches player box scores (~20-25 players per game)
   - Fetches team box scores (2 teams per game)
4. Saves all data to parquet backups (disaster recovery)
5. Loads all data into both PostgreSQL databases
6. Logs success/failure
7. Rotates old logs (keeps last 30 days)

**Expected Daily Volume (during NBA season):**
- **Games:** 10-15 games per day (typical)
- **Plays:** 5,000-7,500 plays per day
- **Player box scores:** 250-375 per day
- **Team box scores:** 20-30 per day
- **Parquet size:** ~2-3 MB per day
- **Database growth:** ~5-10 MB per day (both databases)
- **Runtime:** 2-5 minutes total

**Off-Season Behavior:**
- NBA off-season: July-September (no games)
- Script runs but finds no games (normal)
- Logs "No games found for {date}" (not an error)
- No data collected, no database changes

### Integration Points

**This system integrates with:**

1. **nba_simulator database (hoopr schema)**
   - Used for comprehensive NBA temporal panel system
   - Supports 5-phase pipeline (collection → storage → transformation → modeling → simulation)
   - Production-ready for Phase 1 (Multi-Source Integration)

2. **nba_mcp_synthesis database (hoopr_raw schema)**
   - Used for local betting model development
   - Betting analysis and predictions
   - Feature engineering for ML

3. **Parquet backups**
   - Location: `~/Desktop/sports_data_backup/hoopR/nba/`
   - Purpose: Disaster recovery, offline analysis
   - Can restore databases from parquet if needed

4. **Future integrations** (not yet implemented):
   - ADCE (Autonomous Data Collection Ecosystem) from Phase 0.0009
   - DIMS (Data Inventory Management System) for metrics tracking
   - Multi-source validation (ESPN vs hoopR vs NBA API)

### Monitoring Best Practices

**Daily (first week):**
- Check `logs/hoopr/cron.log` for errors
- Verify databases updated: `psql ... -c "SELECT MAX(game_date) ..."`
- Check disk space: `df -h ~/Desktop/sports_data_backup/`

**Weekly (ongoing):**
- Review logs for pattern errors
- Verify row counts match expected volume
- Check parquet backup integrity

**Monthly:**
- Backup databases to external drive
- Archive old logs (automatic after 30 days)
- Verify cron job still active: `crontab -l`

---

## Step 5: Maintenance and Troubleshooting

### Common Issues

**Issue 1: Cron job not running**

Symptoms:
- No new logs in `logs/hoopr/`
- Databases not updating

Diagnosis:
```bash
# Check crontab
crontab -l | grep hoopr

# Check cron service (macOS)
sudo log show --predicate 'subsystem == "com.vix.cron"' --last 1d | grep hoopr
```

Fix:
- Ensure full paths in crontab (no relative paths)
- Verify script has execute permissions: `ls -lh scripts/etl/run_hoopr_daily.sh`

---

**Issue 2: PostgreSQL connection errors**

Symptoms:
- Error: "connection to server on socket ... failed"

Diagnosis:
```bash
brew services list | grep postgresql
```

Fix:
```bash
brew services start postgresql@15
```

---

**Issue 3: ImportError for Python packages**

Symptoms:
- Error: "ModuleNotFoundError: No module named 'sportsdataverse'"

Diagnosis:
```bash
conda activate nba-aws
python -c "import sportsdataverse; import pandas; import psycopg2"
```

Fix:
```bash
conda activate nba-aws
pip install sportsdataverse pandas pyarrow psycopg2-binary
```

---

**Issue 4: Parquet directory not found**

Symptoms:
- Error: "Directory not found: ~/Desktop/sports_data_backup/..."

Fix:
```bash
# Create backup directory
mkdir -p ~/Desktop/sports_data_backup/hoopR/nba/{pbp,player_box,team_box,schedule}/parquet
```

---

**Issue 5: No games found (during season)**

Symptoms:
- "No games found for {date}" when games should exist

Diagnosis:
```python
from sportsdataverse.nba import nba_schedule
import pandas as pd

schedule = nba_schedule(2025)
schedule['game_date'] = pd.to_datetime(schedule['date']).dt.strftime('%Y-%m-%d')
print(schedule[schedule['game_date'] == '2025-11-08'])
```

Fix:
- Verify hoopR API is working: Try manual query
- Check internet connection
- Retry collection: `python scripts/etl/collect_hoopr_daily.py --date {date}`

---

### Disaster Recovery

**Scenario 1: Database corruption**

```bash
# Restore from parquet backups
python scripts/etl/load_hoopr_parquet.py --database nba_simulator
python scripts/etl/load_hoopr_parquet.py --database nba_mcp_synthesis
```

**Scenario 2: Parquet files lost**

```bash
# Re-collect data for specific date range
for date in 2025-11-{01..09}; do
    python scripts/etl/collect_hoopr_daily.py --date $date
done
```

**Scenario 3: Schema corrupted**

```bash
# Drop and recreate schema
psql -U ryanranft -d nba_simulator -c "DROP SCHEMA IF EXISTS hoopr CASCADE;"
psql -U ryanranft -d nba_simulator -f scripts/db/migrations/0_20_hoopr_schema.sql

# Reload data
python scripts/etl/load_hoopr_parquet.py
```

---

## Step 6: Success Criteria

After setup, you should have:

✅ **Schema created:**
- `nba_simulator.hoopr` schema with 4 tables
- 21 indexes created
- 4 triggers created

✅ **Historical data loaded:**
- 1.19M play-by-play events (Dec 2024 → Nov 2025)
- 67K player box scores
- 5K team box scores
- 2.5K schedule entries
- Data in BOTH databases

✅ **Automation configured:**
- Cron job runs daily at 6 AM
- Logs created in `logs/hoopr/`
- No errors in logs

✅ **Monitoring working:**
- Can query latest game date in both databases
- Parquet backups exist and are growing
- Logs show successful daily runs

---

## Summary

**What you built:**
- Autonomous hoopR data collection pipeline
- Dual-database synchronization (nba_simulator + nba_mcp_synthesis)
- Parquet backup system for disaster recovery
- Complete monitoring and logging infrastructure

**Total code:**
- 5 files, 2,014 lines (1,354 code + 660 documentation)
- Production-ready with error handling
- Zero cloud costs (all local)

**Expected behavior:**
- Runs daily at 6 AM automatically
- Collects ~10-15 NBA games per day (in season)
- Updates both databases
- Maintains parquet backups
- Zero manual intervention required

**Next steps after deployment:**
- Monitor logs for 1 week
- Verify databases updating daily
- Set up weekly database backups
- Integrate with ADCE (Phase 0.0009) if desired

---

**Questions or issues?**
- Read: `docs/HOOPR_AUTONOMOUS_SETUP.md` (complete 660-line guide)
- Check: PROGRESS.md for session history
- Review: Commit ea27e11 for all changes

**Files modified in this commit:**
- `scripts/db/migrations/0_20_hoopr_schema.sql` - NEW
- `scripts/etl/load_hoopr_parquet.py` - NEW
- `scripts/etl/collect_hoopr_daily.py` - NEW
- `scripts/etl/run_hoopr_daily.sh` - NEW
- `docs/HOOPR_AUTONOMOUS_SETUP.md` - NEW

**Branch:** `claude/hoopr-data-work-011CUwmmNAjLymzZwKdHzhit`
**Ready for:** Immediate deployment on local machine
**Status:** ✅ Production Ready
