# hoopR Autonomous Data Collection Setup

**Created:** November 9, 2025
**Purpose:** Set up autonomous daily hoopR data collection for both databases

---

## Overview

This guide sets up autonomous hoopR data collection that:
- ✅ Collects yesterday's NBA games every day
- ✅ Loads data into both `nba_simulator` and `nba_mcp_synthesis` databases
- ✅ Saves parquet backups for disaster recovery
- ✅ Runs automatically via cron (no manual intervention needed)

**Result:** Your databases stay current with latest NBA data automatically.

---

## Quick Start

### Step 1: Create hoopr Schema in nba_simulator

```bash
# Start PostgreSQL (if not running)
brew services start postgresql@15

# Run migration
psql -U ryanranft -d nba_simulator -f scripts/db/migrations/0_20_hoopr_schema.sql
```

**Expected output:**
```
CREATE SCHEMA
CREATE TABLE (4 tables created)
CREATE INDEX (multiple indexes)
CREATE TRIGGER (4 triggers)
GRANT
```

**Verify schema created:**
```bash
psql -U ryanranft -d nba_simulator -c "SELECT tablename FROM pg_tables WHERE schemaname = 'hoopr' ORDER BY tablename;"
```

Should show:
- `play_by_play_hoopr_nba`
- `player_box_hoopr_nba`
- `schedule_hoopr_nba`
- `team_box_hoopr_nba`

---

### Step 2: Load Existing hoopR Data (Nov 9 Collection)

Load the 8 parquet files collected today (Dec 2024 → Nov 2025):

```bash
# Load to both databases (default)
python scripts/etl/load_hoopr_parquet.py

# Or load to specific database
python scripts/etl/load_hoopr_parquet.py --database nba_simulator
python scripts/etl/load_hoopr_parquet.py --database nba_mcp_synthesis

# Or test with dry run first
python scripts/etl/load_hoopr_parquet.py --dry-run
```

**Expected output:**
```
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
```

---

### Step 3: Set Up Daily Autonomous Collection

#### Option A: Cron (Recommended)

Add to crontab to run daily at 6 AM:

```bash
# Edit crontab
crontab -e

# Add this line:
0 6 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh >> /Users/ryanranft/nba-simulator-aws/logs/hoopr/cron.log 2>&1
```

**Cron Schedule Options:**
```bash
# Daily at 6 AM (default - recommended)
0 6 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh

# Daily at 3 AM (early morning)
0 3 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh

# Twice daily (6 AM and 6 PM)
0 6,18 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh

# Every 6 hours
0 */6 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh
```

#### Option B: LaunchAgent (macOS native)

Create LaunchAgent plist:

```bash
# Create plist file
cat > ~/Library/LaunchAgents/com.nba.hoopr.daily.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nba.hoopr.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/ryanranft/nba-simulator-aws/logs/hoopr/launch_agent.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/ryanranft/nba-simulator-aws/logs/hoopr/launch_agent_error.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/ryanranft/nba-simulator-aws</string>
</dict>
</plist>
EOF

# Load LaunchAgent
launchctl load ~/Library/LaunchAgents/com.nba.hoopr.daily.plist

# Verify it's loaded
launchctl list | grep hoopr
```

#### Option C: Integrate with ADCE

Add to ADCE autonomous loop (if using Phase 0.0009):

```python
# Add to scripts/autonomous/autonomous_cli.py task list

DAILY_TASKS = [
    # ... existing tasks ...
    {
        'name': 'hoopr_daily',
        'script': 'scripts/etl/run_hoopr_daily.sh',
        'interval': 24 * 3600,  # Once per day
        'priority': 2
    }
]
```

---

### Step 4: Test Autonomous Collection

Test the daily collection script manually:

```bash
# Collect yesterday's games (dry run)
bash scripts/etl/run_hoopr_daily.sh --dry-run

# Collect yesterday's games (production)
bash scripts/etl/run_hoopr_daily.sh

# Collect last 3 days
bash scripts/etl/run_hoopr_daily.sh --days 3

# Collect specific date
python scripts/etl/collect_hoopr_daily.py --date 2025-11-08
```

**Expected output:**
```
========================================
hoopR Daily Collection - 2025-11-09 06:00:00
========================================
[2025-11-09 06:00:01] Setting up environment...
[2025-11-09 06:00:01] Conda environment activated: nba-aws
[2025-11-09 06:00:01] ✅ Environment ready

========================================
Running hoopR Daily Collection
========================================
[2025-11-09 06:00:02] Executing: python scripts/etl/collect_hoopr_daily.py

📅 Processing 2025-11-08
Found 12 games for 2025-11-08
  Collecting game 401584893...
    ✅ PBP: 457 plays
    ✅ Player box: 24 players
    ✅ Team box: 2 teams

... (more games) ...

COLLECTION SUMMARY
================================================================================
Games found:     12
Games collected: 12
PBP rows:        5,484
Player box rows: 288
Team box rows:   24
Schedule rows:   12

✅ No errors!

========================================
Loading data to databases...
========================================
✅ Database loading complete

🎉 hoopR daily collection COMPLETE
```

---

## File Structure

```
nba-simulator-aws/
├── scripts/
│   ├── db/
│   │   └── migrations/
│   │       └── 0_20_hoopr_schema.sql        # Schema migration
│   └── etl/
│       ├── load_hoopr_parquet.py             # Parquet → PostgreSQL loader
│       ├── collect_hoopr_daily.py            # Daily collector (Python)
│       └── run_hoopr_daily.sh                # Cron wrapper (Shell)
├── docs/
│   └── HOOPR_AUTONOMOUS_SETUP.md             # This file
└── logs/
    └── hoopr/                                 # Collection logs
        ├── cron.log                           # Cron output
        ├── hoopr_daily_20251109_060000.log   # Timestamped logs
        └── ...
```

---

## Database Schema

### nba_simulator.hoopr

```sql
-- Play-by-play (event-level detail)
hoopr.play_by_play_hoopr_nba
  - event_id (PK)
  - game_id, season, season_type
  - type_text, description
  - home_score, away_score
  - athlete_id_1, athlete_id_2, athlete_id_3
  - coordinate_x, coordinate_y (shot location)
  - raw_data (JSONB - full event data)

-- Player box scores
hoopr.player_box_hoopr_nba
  - game_id, athlete_id (UNIQUE)
  - fgm, fga, fg3m, fg3a, ftm, fta
  - pts, reb, ast, stl, blk, tov
  - plus_minus, starter
  - raw_data (JSONB)

-- Team box scores
hoopr.team_box_hoopr_nba
  - game_id, team_id (UNIQUE)
  - fgm, fga, fg_pct, pts
  - fast_break_points, points_in_paint
  - raw_data (JSONB)

-- Schedule
hoopr.schedule_hoopr_nba
  - game_id (PK)
  - home_team_id, away_team_id
  - home_score, away_score
  - status_type, game_completed
  - pbp_available, team_box_available
  - raw_data (JSONB)
```

### nba_mcp_synthesis.hoopr_raw

Same table structure as above, but in `hoopr_raw` schema.

---

## Data Flow

```
┌──────────────────────────────────────────────────────────┐
│ 1. Daily Trigger (6 AM)                                   │
│    - Cron job / LaunchAgent / ADCE                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. run_hoopr_daily.sh                                     │
│    - Sets up conda environment                           │
│    - Calls collect_hoopr_daily.py                        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 3. collect_hoopr_daily.py                                │
│    - Fetches yesterday's schedule from hoopR             │
│    - Collects PBP, player box, team box for each game    │
│    - Saves to parquet backups                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 4. load_hoopr_parquet.py                                 │
│    - Loads parquet files to PostgreSQL                   │
│    - UPSERT (updates existing, inserts new)              │
│    - Loads to both databases                             │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 5. Databases Updated                                      │
│    - nba_simulator.hoopr.*                               │
│    - nba_mcp_synthesis.hoopr_raw.*                       │
└──────────────────────────────────────────────────────────┘
```

---

## Monitoring

### Check Logs

```bash
# View latest log
tail -100 /Users/ryanranft/nba-simulator-aws/logs/hoopr/cron.log

# View all logs from today
ls -lt /Users/ryanranft/nba-simulator-aws/logs/hoopr/hoopr_daily_$(date +%Y%m%d)*.log

# Search for errors
grep -i error /Users/ryanranft/nba-simulator-aws/logs/hoopr/*.log
```

### Check Database

```bash
# Check row counts in nba_simulator
psql -U ryanranft -d nba_simulator << 'EOF'
SELECT
    'play_by_play' AS table_name,
    COUNT(*) AS rows,
    MAX(game_date) AS latest_date
FROM hoopr.play_by_play_hoopr_nba
UNION ALL
SELECT
    'player_box',
    COUNT(*),
    MAX(game_date)
FROM hoopr.player_box_hoopr_nba
UNION ALL
SELECT
    'team_box',
    COUNT(*),
    MAX(game_date)
FROM hoopr.team_box_hoopr_nba
UNION ALL
SELECT
    'schedule',
    COUNT(*),
    MAX(game_date)
FROM hoopr.schedule_hoopr_nba;
EOF

# Check row counts in nba_mcp_synthesis
psql -U ryanranft -d nba_mcp_synthesis << 'EOF'
SELECT
    'play_by_play' AS table_name,
    COUNT(*) AS rows,
    MAX(game_date) AS latest_date
FROM hoopr_raw.play_by_play_hoopr_nba
UNION ALL
SELECT
    'player_box',
    COUNT(*),
    MAX(game_date)
FROM hoopr_raw.player_box_hoopr_nba
UNION ALL
SELECT
    'team_box',
    COUNT(*),
    MAX(game_date)
FROM hoopr_raw.team_box_hoopr_nba
UNION ALL
SELECT
    'schedule',
    COUNT(*),
    MAX(game_date)
FROM hoopr_raw.schedule_hoopr_nba;
EOF
```

### Check Parquet Backups

```bash
# Check parquet backup sizes
du -sh ~/Desktop/sports_data_backup/hoopR/nba/*/parquet/

# List latest files
ls -lt ~/Desktop/sports_data_backup/hoopR/nba/pbp/parquet/ | head -5
```

---

## Troubleshooting

### Issue: Cron job not running

**Check crontab:**
```bash
crontab -l
```

**Check cron logs:**
```bash
tail -100 /var/log/system.log | grep cron
```

**Solution:** Ensure full paths are used in crontab.

---

### Issue: PostgreSQL connection error

**Check PostgreSQL is running:**
```bash
brew services list | grep postgresql
```

**Start PostgreSQL:**
```bash
brew services start postgresql@15
```

**Check connection:**
```bash
psql -U ryanranft -d nba_simulator -c "SELECT 1;"
```

---

### Issue: sportsdataverse not found

**Activate conda environment:**
```bash
conda activate nba-aws
```

**Install sportsdataverse:**
```bash
pip install sportsdataverse
```

---

### Issue: No games found for date

**This is normal:**
- NBA games don't happen every day
- Off-season: April-September has no games
- Lockouts/strikes affect schedule

**Check schedule manually:**
```python
from sportsdataverse.nba import nba_schedule
import pandas as pd

schedule = nba_schedule(2025)
schedule['game_date'] = pd.to_datetime(schedule['date']).dt.strftime('%Y-%m-%d')
print(schedule[schedule['game_date'] == '2025-11-08'])
```

---

## Maintenance

### Backup Strategy

**Parquet files are automatically saved to:**
```
~/Desktop/sports_data_backup/hoopR/nba/
├── pbp/parquet/
├── player_box/parquet/
├── team_box/parquet/
└── schedule/parquet/
```

**Database backups (recommended weekly):**
```bash
# Backup nba_simulator.hoopr schema
pg_dump -U ryanranft -d nba_simulator -n hoopr \
  -f ~/Desktop/sports_data_backup/postgres/nba_simulator_hoopr_$(date +%Y%m%d).sql

# Backup nba_mcp_synthesis.hoopr_raw schema
pg_dump -U ryanranft -d nba_mcp_synthesis -n hoopr_raw \
  -f ~/Desktop/sports_data_backup/postgres/nba_mcp_synthesis_hoopr_raw_$(date +%Y%m%d).sql
```

### Log Rotation

Old logs are automatically deleted after 30 days (see `run_hoopr_daily.sh`).

**Manual cleanup:**
```bash
# Remove logs older than 30 days
find /Users/ryanranft/nba-simulator-aws/logs/hoopr/ -name "hoopr_daily_*.log" -mtime +30 -delete
```

---

## Cost

**Storage:**
- PostgreSQL: ~100 MB per season (both databases = ~200 MB/season)
- Parquet backups: ~50 MB per season
- Logs: ~1 MB per month

**Total:** ~250 MB per season (~$0.00/month, all local storage)

**No cloud costs** - all data stored locally on your machine.

---

## Next Steps

After setup:

1. ✅ **Verify schema created** - Check tables exist in both databases
2. ✅ **Load historical data** - Load Nov 9 parquet files (11 months of data)
3. ✅ **Test daily collection** - Run manually to verify it works
4. ✅ **Set up cron job** - Enable automatic daily collection
5. ✅ **Monitor for 1 week** - Check logs daily to ensure no errors
6. ✅ **Verify data quality** - Run validation queries weekly

**After 1 week:** hoopR data collection is fully autonomous! ✨

---

## Related Documentation

- `HOOPR_DATA_SOURCES_EXPLAINED.md` - Understanding hoopR data sources
- `NBA_MCP_SYNTHESIS_RELATIONSHIP.md` - Project relationships
- `HOOPR_MISSING_DATA_EXECUTION_PLAN.md` - Gap filling strategy
- `scripts/etl/collect_missing_hoopr_data.sh` - Gap collection script

---

**Created:** November 9, 2025
**Author:** Claude + Ryan
**Status:** ✅ Production Ready
