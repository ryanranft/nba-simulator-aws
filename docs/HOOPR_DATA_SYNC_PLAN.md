# hoopR Data Sync Plan: Dec 2024 → Nov 2025

**Created:** November 9, 2025
**Issue:** nba-mcp-synthesis has data through Dec 2, 2024 only
**Gap:** Dec 2, 2024 → Nov 9, 2025 (11 months missing)

---

## Situation Summary

### nba-mcp-synthesis Database Status
- **Schema:** `hoopr_raw.*`
- **Coverage:** Oct 30, 2001 → Dec 2, 2024 ✅
- **Missing:** Dec 2, 2024 → Nov 9, 2025 ❌
- **Source:** Static parquet backup from December 2024
- **Total:** 30,758 games, 13.07M events

### Why the Gap?
The parquet backup is a **snapshot** from when it was created (Dec 3-4, 2024). It contains:
- ✅ All historical data through early December 2024
- ✅ Future schedule (pre-scheduled games through April 2025)
- ❌ NO actual game results after Dec 2, 2024

---

## Option 1: Copy from nba-simulator-aws (Fastest) ⚡

**If nba-simulator-aws has current data**, copy it over.

### Step 1: Check nba-simulator-aws Coverage

```bash
cd /Users/ryanranft/nba-simulator-aws
bash scripts/validation/check_nba_simulator_aws_coverage.sh
```

### Step 2: If Current, Export Recent Data

```bash
# Export games from Dec 2024 onwards
psql -d nba_simulator -c "
COPY (
  SELECT * FROM hoopr_schedule
  WHERE game_date >= '2024-12-02'
  ORDER BY game_date
) TO '/tmp/hoopr_recent_schedule.csv' CSV HEADER;
"

# Export play-by-play
psql -d nba_simulator -c "
COPY (
  SELECT pbp.* FROM hoopr_play_by_play pbp
  JOIN hoopr_schedule s ON pbp.game_id = s.game_id
  WHERE s.game_date >= '2024-12-02'
  ORDER BY s.game_date, pbp.sequence_number
) TO '/tmp/hoopr_recent_pbp.csv' CSV HEADER;
"
```

### Step 3: Import to nba-mcp-synthesis

```bash
# Switch to nba-mcp-synthesis database
export POSTGRES_DB=nba_mcp_synthesis

# Import schedule
psql -d nba_mcp_synthesis -c "
COPY hoopr_raw.nba_schedule FROM '/tmp/hoopr_recent_schedule.csv' CSV HEADER;
"

# Import play-by-play
psql -d nba_mcp_synthesis -c "
COPY hoopr_raw.nba_play_by_play FROM '/tmp/hoopr_recent_pbp.csv' CSV HEADER;
"
```

**Time:** ~5 minutes
**Data:** ~50-100 games + play-by-play

---

## Option 2: Collect from hoopR API (If Option 1 Doesn't Work) 🔄

**If nba-simulator-aws is also stale**, collect fresh data from NBA Stats API.

### Step 1: Check for Updated Parquet Backup

```bash
# Check if newer parquet files exist
ls -lh /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/play_by_play/
ls -lh /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/schedule/

# Look for files modified after Dec 4, 2024
find /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/ -name "*.parquet" -newer /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/play_by_play/nba_play_by_play_2024.parquet
```

### Step 2A: If Newer Parquet Files Exist

Load them like you did before:
```bash
cd /Users/ryanranft/nba-mcp-synthesis
python scripts/load_parquet_to_postgres.py --season 2025
```

### Step 2B: If No Parquet Files, Run hoopR Scraper

```bash
# In nba-simulator-aws directory
cd /Users/ryanranft/nba-simulator-aws

# Collect 2024-25 season data
Rscript scripts/etl/scrape_hoopr_all_152_endpoints.R \
  --season 2025 \
  --all-phases \
  --upload-to-s3

# Or just Phase 1 (faster, ~30 minutes)
Rscript scripts/etl/scrape_hoopr_phase1_foundation.R \
  --season 2025
```

**Time:**
- Phase 1 only: ~30 minutes
- All 152 endpoints: ~2-3 hours

### Step 3: Export New Parquet to CSV and Load

Once collected in nba-simulator-aws:
```bash
# Export new data
psql -d nba_simulator -c "
COPY (SELECT * FROM hoopr_schedule WHERE game_date >= '2024-12-02')
TO '/tmp/hoopr_2025_schedule.csv' CSV HEADER;
"

# Import to nba-mcp-synthesis
psql -d nba_mcp_synthesis -c "
COPY hoopr_raw.nba_schedule FROM '/tmp/hoopr_2025_schedule.csv' CSV HEADER;
"
```

---

## Option 3: Direct Load to nba-mcp-synthesis (Advanced) 🎯

**Run hoopR scraper directly into nba-mcp-synthesis database.**

### Requirements:
- Modify scraper to use `hoopr_raw` schema
- Or create tables without schema prefix
- Or use a Python wrapper to handle schema

### Python Wrapper (Recommended):

```python
# scripts/sync_hoopr_to_mcp_synthesis.py
import subprocess
import pandas as pd
from sqlalchemy import create_engine

# 1. Run hoopR scraper to CSV
subprocess.run([
    'Rscript',
    'scripts/etl/scrape_hoopr_phase1_foundation.R',
    '--season', '2025',
    '--output', '/tmp/hoopr_2025'
])

# 2. Load CSV to nba-mcp-synthesis
engine = create_engine('postgresql://localhost/nba_mcp_synthesis')

# Load schedule
schedule_df = pd.read_csv('/tmp/hoopr_2025/nba_schedule_2025.csv')
schedule_df.to_sql('nba_schedule', engine, schema='hoopr_raw',
                   if_exists='append', index=False)

# Load play-by-play
pbp_df = pd.read_csv('/tmp/hoopr_2025/nba_play_by_play_2025.csv')
pbp_df.to_sql('nba_play_by_play', engine, schema='hoopr_raw',
              if_exists='append', index=False)

print("✅ Data synced to nba-mcp-synthesis!")
```

---

## Recommended Approach

### Best Path:

1. **First:** Run `check_nba_simulator_aws_coverage.sh`

2. **If nba-simulator-aws is current:**
   - Use Option 1 (copy data over)
   - ⚡ Fastest (5 minutes)

3. **If nba-simulator-aws is also stale:**
   - Use Option 2B (run scraper)
   - Then copy to both databases
   - 📊 Most complete

4. **Long-term solution:**
   - Keep nba-simulator-aws autonomous collection running
   - Periodically sync to nba-mcp-synthesis
   - Or query nba-simulator-aws directly for current data

---

## Verification After Sync

```bash
# Check coverage in nba-mcp-synthesis
psql -d nba_mcp_synthesis -c "
SELECT
    MAX(game_date) as latest_game,
    COUNT(*) FILTER (WHERE game_date >= '2024-12-02') as new_games,
    CURRENT_DATE - MAX(game_date)::date as days_behind
FROM hoopr_raw.nba_schedule;
"
```

Expected result:
- `latest_game`: 2025-11-08 or 2025-11-09
- `new_games`: ~200-250 games
- `days_behind`: 0 or 1

---

## Timeline Estimate

| Option | Time Required | Pros | Cons |
|--------|---------------|------|------|
| Option 1 (Copy) | 5 minutes | ⚡ Fastest | Requires current data in nba-simulator-aws |
| Option 2A (Parquet) | 10 minutes | Easy if files exist | Need updated parquet files |
| Option 2B (Scraper) | 30 min - 3 hours | Gets fresh data from API | Slower, hits NBA API |
| Option 3 (Direct) | 30 minutes + setup | Most integrated | Requires code modifications |

---

## Next Steps

1. Run the quick check script (created above)
2. Based on results, choose best option
3. Execute sync
4. Verify coverage

Ready to help with any of these options! Which would you like to try first? 🚀
