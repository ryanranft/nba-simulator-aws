# Basketball Reference Play-by-Play Collection System

**Status:** ✅ Complete system ready for deployment
**Created:** October 18, 2025
**Purpose:** Comprehensive play-by-play data collection from Basketball Reference

---

## Executive Summary

This system collects play-by-play (PBP) data from Basketball Reference using a 3-phase approach:

1. **Discovery** - Find the earliest available PBP data
2. **Historical Backfill** - Collect all historical PBP
3. **Daily Collection** - Keep PBP current with nightly scraping

**Key Question:** Does Basketball Reference have PBP data earlier than ESPN (1993)?

**Current PBP Coverage:**
- **ESPN API:** 1993-2025 (earliest known source)
- **NBA API:** 1996-2025
- **hoopR:** 2002-2025
- **Basketball Reference:** Unknown (to be discovered)

---

## System Architecture

### Three Complementary Scripts

| Script | Purpose | Runtime | When to Run |
|--------|---------|---------|-------------|
| **PBP Discovery** | Find earliest PBP year | ~30 min | Once (before backfill) |
| **PBP Backfill** | Collect all historical PBP | 2-5 days | Once (after discovery) |
| **Daily PBP** | Ongoing collection | ~2-3 min/day | Nightly (3 AM) |

### Data Flow

```
Discovery Script
    ↓
Identifies earliest PBP year (e.g., 2000)
    ↓
Backfill Script (runs once for 2-5 days)
    ↓
Collects all PBP from 2000-2025
    ↓
Daily Script (runs every night)
    ↓
Keeps PBP current going forward
```

---

## Phase 1: Discovery

### Purpose
Find the earliest season with play-by-play data on Basketball Reference.

### How It Works

1. **Start from 2024** (known to have PBP)
2. **Work backwards** year by year (2024 → 2023 → 2022 → ...)
3. **Test 10 random games per season**
4. **Check for PBP table** existence
5. **Count PBP events** in games that have it
6. **Stop early** after 3 consecutive years with no PBP
7. **Generate JSON report** with findings

### Usage

**Basic discovery (recommended):**
```bash
# Test 2024 down to 1990 (10 games per year)
# Runtime: ~30 minutes
# Games tested: ~350
python scripts/etl/basketball_reference_pbp_discovery.py
```

**Custom options:**
```bash
# Test fewer years (faster)
python scripts/etl/basketball_reference_pbp_discovery.py \
    --start-year 2024 --end-year 2000

# Test more games per year (more accurate)
python scripts/etl/basketball_reference_pbp_discovery.py \
    --games-per-year 20

# Verbose output (see every game tested)
python scripts/etl/basketball_reference_pbp_discovery.py --verbose

# Quick test (just 5 recent years)
python scripts/etl/basketball_reference_pbp_discovery.py \
    --start-year 2024 --end-year 2020 --games-per-year 5
```

### Output

**Console report:**
```
======================================================================
BASKETBALL REFERENCE PLAY-BY-PLAY DISCOVERY
======================================================================

Years to test: 2024 down to 1990
Games per year: 10
Total tests: ~350
Estimated time: ~30.0 minutes
Started: 2025-10-18 21:30:00

======================================================================
Testing 2023-24 season...
======================================================================
Testing 10 sample games...

Results:
  Games tested:     10
  Games with PBP:   10 (100.0%)
  Avg events/game:  520
  ✅ PBP DATA FOUND for 2024

...

======================================================================
Testing 1999-00 season...
======================================================================
Testing 10 sample games...

Results:
  Games tested:     10
  Games with PBP:   3 (30.0%)
  Avg events/game:  480
  ✅ PBP DATA FOUND for 2000

...

======================================================================
Testing 1994-95 season...
======================================================================
Testing 10 sample games...

Results:
  Games tested:     10
  Games with PBP:   0 (0.0%)
  Avg events/game:  0
  ❌ NO PBP DATA for 1995

⚠️  Found 3 consecutive years with no PBP. Stopping early.

======================================================================
DISCOVERY REPORT
======================================================================

Testing Summary:
  Total games tested:  240
  Games with PBP:      180
  Earliest PBP year:   2000

Comparison with Other Sources:
  ESPN API:          1993-2025
  NBA API:           1996-2025
  hoopR:             2002-2025
  Basketball Ref:    2000-2025

✅ Basketball Reference has PBP earlier than hoopR (2002)
   This fills a 2-year gap!

Recommendations:
  1. Run historical PBP backfill starting from 2000
  2. Estimated backfill: ~31,250 games over ~4.3 days
  3. Use separate storage path: s3://.../basketball_reference/pbp/
  4. Cross-validate overlapping years with ESPN/NBA API

✓ Detailed report saved to: reports/basketball_reference_pbp_discovery_20251018_213000.json
✓ Complete: 2025-10-18 22:00:00
```

**JSON report file:**
```json
{
  "discovery_date": "2025-10-18T22:00:00",
  "earliest_pbp_year": 2000,
  "total_games_tested": 240,
  "total_pbp_found": 180,
  "results_by_year": {
    "2024": {
      "season": 2024,
      "games_tested": 10,
      "games_with_pbp": 10,
      "total_pbp_events": 5200,
      "sample_game_ids": ["202410050BOS", ...],
      "pbp_game_ids": ["202410050BOS", ...]
    },
    ...
  }
}
```

### Possible Outcomes

**Scenario 1: PBP Earlier Than ESPN (1993)**
- **Example:** Basketball Reference has PBP from 1990
- **Impact:** 🎉 **HUGE WIN!** Fills 3-year gap (1990-1992)
- **Next step:** Run backfill from 1990

**Scenario 2: PBP Between ESPN and hoopR (1993-2002)**
- **Example:** Basketball Reference has PBP from 1998
- **Impact:** ✅ **USEFUL** for filling gaps and cross-validation
- **Next step:** Run backfill from 1998

**Scenario 3: PBP Starts Around 2000-2002**
- **Example:** Basketball Reference has PBP from 2001
- **Impact:** ✅ **STILL VALUABLE** as 4th independent source
- **Next step:** Run backfill from 2001

**Scenario 4: No PBP Found**
- **Example:** Basketball Reference has no PBP tables
- **Impact:** ⚠️ **UNEXPECTED**
- **Next step:** Test manually on recent games

---

## Phase 2: Historical Backfill

### Purpose
Collect all historical play-by-play data from earliest available year to present.

### How It Works

1. **Get games** from scraping_progress table (populated by master game list builder)
2. **Work backwards chronologically** (most recent first - highest value)
3. **Extract ONLY play-by-play data** (skip if no PBP table)
4. **Upload to S3:** `s3://.../basketball_reference/pbp/{YEAR}/{game_id}_pbp.json`
5. **Load into database:** game_play_by_play table
6. **Track progress** in database (resume capability)
7. **Stop automatically** after 100 consecutive games with no PBP (reached historical boundary)

### Usage

**Basic backfill (after discovery):**
```bash
# Start from year discovered to have PBP (e.g., 2000)
# Runtime: 2-5 days depending on start year
python scripts/etl/basketball_reference_pbp_backfill.py --start-year 2000
```

**Options:**
```bash
# Limit number of games (for testing)
python scripts/etl/basketball_reference_pbp_backfill.py \
    --start-year 2000 --max-games 100

# Adjust auto-stop threshold (default: 100 consecutive games with no PBP)
python scripts/etl/basketball_reference_pbp_backfill.py \
    --start-year 2000 --stop-after-no-pbp 200

# Dry run (test without uploading/inserting)
python scripts/etl/basketball_reference_pbp_backfill.py \
    --dry-run --max-games 10

# Skip S3 uploads (database only)
python scripts/etl/basketball_reference_pbp_backfill.py \
    --start-year 2000 --no-s3
```

### Runtime Estimates

Based on 12-second rate limit:

| Start Year | Games | Runtime | Auto-stop Point |
|------------|-------|---------|-----------------|
| 2000 | ~31,250 | ~4.3 days | When reaching pre-2000 games |
| 2010 | ~18,750 | ~2.6 days | When reaching pre-2010 games |
| 2015 | ~12,500 | ~1.7 days | When reaching pre-2015 games |
| 2020 | ~6,250 | ~0.9 days | When reaching pre-2020 games |

**Note:** Backfill automatically stops when it encounters 100 consecutive games without PBP, so actual runtime may be shorter.

### Resume Capability

The backfill script can be stopped and resumed without losing progress:

```bash
# Stop the script (Ctrl+C)
^C

# Resume later - it will continue from where it left off
python scripts/etl/basketball_reference_pbp_backfill.py --start-year 2000
```

Progress is tracked in the database, so the script knows which games have already been processed.

### Output

**Progress updates every 10 games:**
```
======================================================================
Progress: 100/31250 (0.3%)
Elapsed: 0.3h, ETA: 108.7h
With PBP: 85, Without: 15
Total events: 44,200
======================================================================
```

**Final summary:**
```
======================================================================
SUMMARY
======================================================================
Games checked:      31250
Games with PBP:     28500
Games without PBP:  2750
Total PBP events:   14,820,000
Uploaded to S3:     28500
Database inserts:   28500
Errors:             0
======================================================================

Average events per game: 520

✓ Complete: 2025-10-23 15:45:00
```

---

## Phase 3: Daily Collection

### Purpose
Keep play-by-play database current with nightly scraping of new games.

### How It Works

1. **Get yesterday's date** (or user-specified date)
2. **Query ESPN API** for games on that date
3. **Convert to Basketball Reference game IDs**
4. **Extract ONLY play-by-play data** (no box scores)
5. **Upload to S3:** `s3://.../basketball_reference/pbp/{YEAR}/{game_id}_pbp.json`
6. **Load into database:** game_play_by_play table

### Usage

**Daily scraping (typical overnight usage):**
```bash
# Scrape yesterday's games
# Runtime: ~2-3 minutes for typical game day (10-15 games)
python scripts/etl/basketball_reference_daily_pbp.py
```

**Options:**
```bash
# Scrape specific date
python scripts/etl/basketball_reference_daily_pbp.py --date 2023-06-12

# Scrape last N days
python scripts/etl/basketball_reference_daily_pbp.py --days 3

# Dry run (test without uploading/inserting)
python scripts/etl/basketball_reference_daily_pbp.py --dry-run

# Skip S3 uploads (database only)
python scripts/etl/basketball_reference_daily_pbp.py --no-s3
```

### Typical Daily Output

```
======================================================================
BASKETBALL REFERENCE DAILY PBP SCRAPER
======================================================================

Started: 2025-10-19 03:00:00
Dry run: False
Upload to S3: True
Dates to scrape: 2025-10-18

Fetching games for 2025-10-18...
  Found 12 games

Total games found: 12

Estimated time: 2.4 minutes (12 games × 12s)

Checking 202510180BOS (2025-10-18) - MIA @ BOS
  ✓ Found 538 PBP events

Checking 202510180LAL (2025-10-18) - PHX @ LAL
  ✓ Found 512 PBP events

...

======================================================================
SUMMARY
======================================================================
Games checked:      12
Games with PBP:     12
Games without PBP:  0
Total PBP events:   6,240
Uploaded to S3:     12
Database inserts:   12
Errors:             0
======================================================================

Average events per game: 520

✓ Complete: 2025-10-19 03:02:30
```

---

## Integration with Overnight Workflow

### Current 4-Source Workflow

The existing overnight workflow collects from 4 sources:
1. ESPN (last 3 days)
2. hoopR (last 3 days)
3. NBA API (last 3 days)
4. Basketball Reference box scores (yesterday)

### Adding Daily PBP

**Option 1: Separate LaunchAgent (Recommended)**

Create a new LaunchAgent that runs after the main workflow:

**File:** `~/Library/LaunchAgents/com.nba-simulator.basketball-reference-pbp.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nba-simulator.basketball-reference-pbp</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/ryanranft/miniconda3/envs/nba-aws/bin/python</string>
        <string>/Users/ryanranft/nba-simulator-aws/scripts/etl/basketball_reference_daily_pbp.py</string>
    </array>

    <!-- Run at 3:20 AM (after box score collection) -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>20</integer>
    </dict>

    <key>WorkingDirectory</key>
    <string>/Users/ryanranft/nba-simulator-aws</string>

    <key>StandardOutPath</key>
    <string>/tmp/basketball_reference_pbp_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/basketball_reference_pbp_stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/ryanranft/miniconda3/envs/nba-aws/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

**Load:**
```bash
launchctl load ~/Library/LaunchAgents/com.nba-simulator.basketball-reference-pbp.plist
```

**Advantages:**
- Independent of main workflow
- No risk to existing collection
- Easy to disable if needed
- Simple rollback

**Option 2: Integrate into Workflow Script**

Add to `scripts/workflows/overnight_4_source_collection.sh`:

```bash
# Step 5: Basketball Reference Play-by-Play (NEW!)
log_step "Step 5: Basketball Reference Play-by-Play (Yesterday)" | tee -a "$LOG_FILE"
python scripts/etl/basketball_reference_daily_pbp.py --days 1 2>&1 | tee -a "$LOG_FILE"
```

---

## Data Storage

### S3 Structure

```
s3://nba-sim-raw-data-lake/
└── basketball_reference/
    ├── box_scores/           # Box score data (separate system)
    │   └── 2024/
    │       └── 202410050BOS.json
    └── pbp/                   # Play-by-play data (this system)
        └── 2024/
            └── 202410050BOS_pbp.json
```

**Key differences:**
- PBP stored in separate `pbp/` directory
- Filenames have `_pbp` suffix for clarity
- Same year-based organization

### JSON Format

**PBP JSON structure:**
```json
{
  "game_id": "202410050BOS",
  "scraped_at": "2025-10-19T03:00:00",
  "event_count": 538,
  "events": [
    {
      "quarter": "1",
      "time": "12:00",
      "description": "Jump ball: Bam Adebayo vs. Al Horford",
      "away_score": "0",
      "home_score": "0"
    },
    {
      "quarter": "1",
      "time": "11:45",
      "description": "Jayson Tatum makes 3-pt jump shot",
      "away_score": "0",
      "home_score": "3"
    },
    ...
  ]
}
```

### Database Schema

**Table:** `game_play_by_play`

```sql
CREATE TABLE IF NOT EXISTS game_play_by_play (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    event_number INTEGER,
    quarter INTEGER NOT NULL,
    time_remaining TEXT,
    time_elapsed_seconds INTEGER,
    event_type TEXT,
    description TEXT,
    primary_player TEXT,
    secondary_player TEXT,
    offensive_team TEXT,
    defensive_team TEXT,
    home_score INTEGER,
    away_score INTEGER,
    score_diff INTEGER,
    shot_made BOOLEAN,
    shot_type TEXT,
    assist_player TEXT,
    rebound_player TEXT,
    block_player TEXT,
    steal_player TEXT,
    turnover_player TEXT,
    foul_player TEXT,
    substitution_in TEXT,
    substitution_out TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);
```

---

## Complete Workflow

### Step-by-Step Deployment

**1. Run Discovery (once)**
```bash
# Takes ~30 minutes
python scripts/etl/basketball_reference_pbp_discovery.py
```

**2. Review Discovery Results**
```bash
# Check the JSON report
cat reports/basketball_reference_pbp_discovery_*.json | jq '.earliest_pbp_year'
```

**3. Run Historical Backfill (once)**
```bash
# Replace 2000 with discovered earliest year
# Takes 2-5 days depending on start year
python scripts/etl/basketball_reference_pbp_backfill.py --start-year 2000
```

**4. Set Up Daily Collection**
```bash
# Test first
python scripts/etl/basketball_reference_daily_pbp.py --dry-run

# Then set up LaunchAgent (see Integration section above)
launchctl load ~/Library/LaunchAgents/com.nba-simulator.basketball-reference-pbp.plist
```

**5. Monitor**
```bash
# Check logs
tail -f /tmp/basketball_reference_pbp_stdout.log

# Query recent PBP
sqlite3 /tmp/basketball_reference_boxscores.db \
    "SELECT game_id, COUNT(*) as events
     FROM game_play_by_play
     WHERE game_id LIKE '202510%'
     GROUP BY game_id;"
```

---

## Monitoring & Validation

### Daily Health Checks

**Check if yesterday's games were collected:**
```sql
SELECT game_id, COUNT(*) as events
FROM game_play_by_play
WHERE game_id LIKE '20251018%'
GROUP BY game_id;
```

**Expected:** 10-15 games on typical game days, ~520 events per game

### Weekly Validation

**Check PBP coverage over past week:**
```sql
SELECT
    SUBSTR(game_id, 1, 8) as date,
    COUNT(DISTINCT game_id) as games,
    SUM(1) as total_events,
    AVG(1.0) as avg_events_per_game
FROM game_play_by_play
WHERE game_id >= date('now', '-7 days')
GROUP BY SUBSTR(game_id, 1, 8)
ORDER BY date DESC;
```

### S3 Validation

**Check recent PBP uploads:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/pbp/2025/ \
    --recursive | tail -20
```

### Cross-Validation with Other Sources

**Compare PBP coverage:**
```sql
-- Games with Basketball Reference PBP
SELECT COUNT(DISTINCT game_id) as bbref_pbp_games
FROM game_play_by_play
WHERE game_id >= '20241001';

-- Compare with ESPN PBP (from other sources)
-- Should be similar for overlapping years
```

---

## Troubleshooting

### Problem: All games showing "No PBP"

**Likely cause:** Rate limited or testing wrong years

**Solution:**
1. Check if recent games (2023-2024) have PBP manually
2. Wait 10 minutes for rate limits to reset
3. Try with `--start-year 2024 --end-year 2023` first

### Problem: Discovery taking too long

**Solution:** Use fewer games per year or narrower year range
```bash
python scripts/etl/basketball_reference_pbp_discovery.py \
    --start-year 2024 \
    --end-year 2010 \
    --games-per-year 5
```

### Problem: Backfill stopped unexpectedly

**No problem!** Just restart it:
```bash
python scripts/etl/basketball_reference_pbp_backfill.py --start-year 2000
```

It will resume from where it left off.

### Problem: Daily scraper finds no games

**Likely cause:** Offseason or no games scheduled that day

**This is normal.** The scraper will simply report:
```
✓ No games to scrape
```

### Problem: Rate limiting (429 errors)

**Solution:** Wait 10-15 minutes before retrying

All scripts have built-in 12-second rate limiting, but if you've been testing multiple scripts, you may hit cumulative limits.

---

## Cost Impact

### S3 Storage

**PBP data size:**
- ~50 KB per game (JSON)
- ~15 games per day
- ~750 KB per day
- ~270 MB per year

**Historical backfill (if starting from 2000):**
- ~31,250 games
- ~1.5 GB total

**Total S3 cost:** ~$0.03/month additional (negligible)

### No Additional Compute Costs

Daily PBP scraper runs on same overnight schedule, no new infrastructure needed.

---

## Success Metrics

### Immediate (First Week)

- ✅ Discovery completed, earliest PBP year identified
- ✅ Backfill launched and running
- ✅ Daily scraper collecting new games
- ✅ No errors in logs

### Short Term (First Month)

- ✅ Backfill completed (all historical PBP collected)
- ✅ Daily scraper runs automatically every night
- ✅ 95%+ of games have PBP data
- ✅ Average ~520 events per game

### Long Term (Ongoing)

- ✅ No missing games in past 30 days
- ✅ Cross-validation with other PBP sources shows <1% discrepancies
- ✅ Database size growing appropriately (~270 MB/year)
- ✅ S3 costs within budget

---

## Files Created

| File | Purpose | Size |
|------|---------|------|
| `scripts/etl/basketball_reference_pbp_discovery.py` | Discovery script | 14 KB |
| `scripts/etl/basketball_reference_pbp_backfill.py` | Historical backfill | 15 KB |
| `scripts/etl/basketball_reference_daily_pbp.py` | Daily collection | 15 KB |
| `docs/BASKETBALL_REFERENCE_PBP_DISCOVERY.md` | Discovery docs | 13 KB |
| `docs/BASKETBALL_REFERENCE_PBP_SYSTEM.md` | This complete guide | 22 KB |

**Total:** 79 KB of code + documentation

---

## Summary

**Basketball Reference PBP Collection System is complete and ready for deployment.**

**Three complementary scripts:**
1. **Discovery** - Find earliest PBP year (~30 min, run once)
2. **Backfill** - Collect all historical PBP (2-5 days, run once)
3. **Daily** - Keep PBP current (2-3 min/day, automated)

**Next steps:**
1. Run discovery script when rate limits reset
2. Review discovery results
3. Launch historical backfill based on findings
4. Set up daily collection in overnight workflow

**Key benefits:**
- Fills potential gaps in PBP coverage
- 4th independent PBP source for cross-validation
- Automated daily collection
- Separate storage from box scores
- Resume capability for long-running backfill
- Minimal cost impact (~$0.03/month)

---

**Ready to discover Basketball Reference's PBP coverage!** 🔍

**First command:** `python scripts/etl/basketball_reference_pbp_discovery.py`
