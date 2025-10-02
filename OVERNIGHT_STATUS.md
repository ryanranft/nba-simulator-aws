# Overnight Extraction & Schema Update Status

**Date Started:** October 2, 2025 12:35 AM

---

## What's Running

### 1. Schema Update (PID 51309) - IN PROGRESS
**Script:** `scripts/etl/complete_schema_update.py`
**Log:** `schema_update.log`
**Status:** Adding 25 missing columns to games table
**Progress:** 4/25 columns added (as of 12:50 AM)
- ✅ away_team_record_summary
- ✅ away_team_standing_summary
- ✅ away_team_location
- ✅ away_team_is_winner
- ⏳ 21 remaining columns

**Estimated Completion:** ~1:00 AM (~1 minute per column)

### 2. Play-by-Play Extraction - IN PROGRESS
**Script:** `scripts/etl/extract_pbp_local.py`
**Log:** `extract_pbp_1997_2021.log`
**Years:** 1997-2021
**Current Year:** 2013
**Progress:**
- 2012: ✅ 706,290 plays inserted
- 2013: ⏳ 639,227 plays extracted, ready to insert

**Estimated Remaining:** 8 more years (2014-2021)

### 3. Box Scores Extraction - IN PROGRESS
**Script:** `scripts/etl/extract_boxscores_local.py`
**Log:** `extract_boxscores_1997_2021.log`
**Years:** 1997-2021
**Current Year:** 2011
**Progress:** 1997-2010 complete, 2011 in progress

**Estimated Remaining:** 10 more years (2012-2021)

### 4. Enhanced Schedule Extraction - WAITING
**Script:** `scripts/etl/extract_schedule_local.py`
**Status:** ⏸️ NOT STARTED - Waiting for schema update to complete
**Reason:** Requires all 53 fields in games table
**Will Start:** Automatically after schema update completes (~1:00 AM)

---

## Progress Check Commands

### Monitor Extraction Progress

```bash
# Check schema update progress
tail -50 schema_update.log

# Check PBP extraction
tail -20 extract_pbp_1997_2021.log

# Check box scores extraction
tail -20 extract_boxscores_1997_2021.log

# Check enhanced schedule extraction (will start after schema completes)
tail -20 extract_schedule_full_1993_2025.log

# Check if processes are still running
ps aux | grep python | grep extract
ps -p 51309  # Schema update process
```

### Check for Completion

```bash
# Schema update should show:
grep "Successfully added" schema_update.log

# PBP should show year 2021:
grep "Processing Year: 2021" extract_pbp_1997_2021.log

# Box scores should show year 2021:
grep "Processing Year: 2021" extract_boxscores_1997_2021.log

# Enhanced schedule should show year 2025:
grep "Processing Year: 2025" extract_schedule_full_1993_2025.log
```

---

## Expected Final Counts

When all extractions complete successfully:

**Database Tables:**
- **games:** ~35,000-40,000 records (1993-2025, all 58 columns including 53 enhanced fields)
- **play_by_play:** ~10,000,000+ plays (1997-2021)
- **player_game_stats:** ~800,000+ records (1997-2021)
- **team_game_stats:** ~80,000+ records (1997-2021)

**Column Count:**
- **games table:** 58 total columns (33 original + 25 new)

---

## Data Completeness Summary

### ✅ PBP Data (1997-2021)
- All 9 fields from original script
- Bonus field: scoring_play boolean
- Matches user's original comprehensive extraction

### ✅ Box Scores Data (1997-2021)
- Team-level stats (all fields from original script)
- Player-level stats (all fields from original script)
- Matches user's original comprehensive extraction

### ⏳ Schedule Data (1993-2025) - ENHANCED TO 53 FIELDS
**User Requirement:** *"I would like the schedule to have all of the data and be as rich as possible"*

**Delivered:** 53 total fields (up from 9 fields = 488% more data)

**Fields by Category:**
- Core (4): game_id, game_date, game_time, season
- Home Team (14): id, abbrev, name, short_name, logo, color, alt_color, uid, record_summary, standing_summary, location, score, is_winner, leader (name + stat)
- Away Team (14): (same as home team)
- Venue (6): name, id, city, state, country, indoor
- Status (4): game_status, status_id, status_state, status_detail
- Broadcast (4): name, market, type, count
- Metadata (7): completed, is_tie, periods, time_valid, game_link, header_postfix, has_tickets

---

## Next Steps (When Complete - Tomorrow Morning)

### 1. Verify Schema Update Completed
```bash
tail -50 schema_update.log
# Should show: "✅ Successfully added 25/25 columns"
# Should show: "📊 Final games table has 58 columns"
```

### 2. Start Enhanced Schedule Extraction (if not auto-started)
```bash
source /Users/ryanranft/nba-sim-credentials.env && \
nohup python -u scripts/etl/extract_schedule_local.py --year-range 1993-2025 \
> extract_schedule_full_1993_2025.log 2>&1 & \
echo $! > extract_schedule_full.pid
```

### 3. Verify All Extractions Complete
```bash
# Check final year in each log
grep "Processing Year: 2021" extract_pbp_1997_2021.log
grep "Processing Year: 2021" extract_boxscores_1997_2021.log
grep "Processing Year: 2025" extract_schedule_full_1993_2025.log
```

### 4. Verify Data in Database
```bash
source /Users/ryanranft/nba-sim-credentials.env && python3 << 'EOF'
import psycopg2
import os

conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    port=os.environ['DB_PORT']
)
cursor = conn.cursor()

# Check row counts
cursor.execute("SELECT COUNT(*) FROM games")
print(f"Games: {cursor.fetchone()[0]:,}")

cursor.execute("SELECT COUNT(*) FROM play_by_play")
print(f"Plays: {cursor.fetchone()[0]:,}")

cursor.execute("SELECT COUNT(*) FROM player_game_stats")
print(f"Player stats: {cursor.fetchone()[0]:,}")

cursor.execute("SELECT COUNT(*) FROM team_game_stats")
print(f"Team stats: {cursor.fetchone()[0]:,}")

# Check games table columns
cursor.execute("""
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_name = 'games'
""")
print(f"\nGames table columns: {cursor.fetchone()[0]} (should be 58)")

cursor.close()
conn.close()
EOF
```

### 5. Update PROGRESS.md
Mark Phase 2 tasks as complete and update actual counts/costs.

### 6. Check AWS Costs
```bash
make check-costs
```

### 7. Backup Logs
```bash
mkdir -p backups
cp *.log backups/
```

---

## Verification Checklist

When you wake up, verify:

- [ ] Schema update completed (25/25 columns, 58 total)
- [ ] Enhanced schedule extraction started and completed (1993-2025)
- [ ] PBP extraction completed (year 2021 processed)
- [ ] Box scores extraction completed (year 2021 processed)
- [ ] No error messages in any logs
- [ ] Database row counts match expectations
- [ ] Games table has 58 columns
- [ ] All process PIDs are no longer running

---

## What to Watch For

**Potential Issues:**
1. **Schema update timeout** - If schema_update.log stops before 25/25 columns, run remaining ALTER TABLE commands manually
2. **Enhanced schedule not auto-started** - If schema completes but schedule doesn't start, run command from Step 2 above
3. **Database connection errors** - Check RDS instance status, security groups, and credentials
4. **Disk space** - Log files may grow large; monitor disk usage

**Success Indicators:**
- ✅ All logs show final year completed
- ✅ No "❌" or "ERROR" messages in logs
- ✅ Database queries return expected row counts
- ✅ Games table has all 58 columns
- ✅ User requirement satisfied: Schedule data is "as rich as possible" with all 53 fields

---

**Note:** All processes run with `nohup` to continue even if terminal disconnects or computer sleeps. All output is captured in log files for morning review.