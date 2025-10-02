# Overnight Automation Status - S3 Partitioning + Glue Crawlers

**Started:** 2025-10-01 22:19:42 (partitioning), 22:25:27 (crawlers)
**Process IDs:**
- Partitioning: 48440 (wrapper), 48453 (Python)
- Crawlers: 50899 (wrapper)

---

## What's Running Overnight

You now have **TWO automated processes** running in parallel:

### 1. ✅ S3 Partitioning (IN PROGRESS)

**Script:** `partition_all_overnight.sh`
**Log:** `partition_overnight.log`
**Status:** Currently partitioning schedule data (year 1995, ~300 files done)

**Will Complete:**
- ✅ Schedule (11,633 files → 33 year folders)
- ⏸️ PBP (44,826 files → 25 year folders)
- ⏸️ Box Scores (44,828 files → 25 year folders)
- ⏸️ Team Stats (44,828 files → 25 year folders)

**Estimated Time:** 2-3 hours total

### 2. ✅ Glue Crawler Automation (IN PROGRESS)

**Script:** `run_crawlers_overnight.sh`
**Log:** `crawler_overnight.log`
**Status:** Currently running nba-schedule-1994-crawler

**Strategy:**
- Waits for each year partition to complete in S3
- Creates crawler if it doesn't exist
- Starts crawler (max 10 concurrent)
- Processes all years (1993-2025) for all 4 data types

**Will Complete:**
- Schedule: 33 crawlers (1993-2025)
- PBP: 25 crawlers (1997-2021)
- Box Scores: 25 crawlers (1997-2021)
- Team Stats: 25 crawlers (1997-2021)

**Total:** 108 crawlers

**Estimated Time:** 3-4 hours (with parallelization)

---

## How They Work Together

```
Partitioning Process          Crawler Process
─────────────────            ─────────────────

Copy schedule/1993/*.json  → Detects files ready → Creates crawler → Starts crawler
Copy schedule/1994/*.json  → Detects files ready → Creates crawler → Starts crawler
Copy schedule/1995/*.json  → Detects files ready → Creates crawler → Starts crawler
...                          ...
Copy pbp/1997/*.json       → Detects files ready → Creates crawler → Starts crawler
...                          ...
```

**Key Feature:** The crawler process **automatically waits** for partitions to be ready, so it coordinates with the partitioning process without manual intervention.

---

## Monitor Progress

### Quick Status Check

```bash
# Check both processes at once
./scripts/shell/check_partition_status.sh  # S3 partitioning progress
tail -20 crawler_overnight.log             # Crawler progress

# Or watch live
tail -f partition_overnight.log  # Partitioning (Ctrl+C to exit)
tail -f crawler_overnight.log    # Crawlers (Ctrl+C to exit)
```

### Detailed Monitoring

**S3 Partitioning:**
```bash
# Count year folders created
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ | grep "year=" | wc -l
aws s3 ls s3://nba-sim-raw-data-lake/pbp/ | grep "year=" | wc -l

# Check processes
ps aux | grep partition | grep -v grep
```

**Glue Crawlers:**
```bash
# List all crawlers
aws glue list-crawlers --query 'CrawlerNames' --output table

# Count running crawlers
aws glue list-crawlers --query 'CrawlerNames' --output text | \
  tr '\t' '\n' | \
  xargs -I {} aws glue get-crawler --name {} --query 'Crawler.State' | \
  grep "RUNNING" | wc -l

# Check specific crawler
aws glue get-crawler --name nba-schedule-1994-crawler
```

---

## Current Status (as of 22:26)

### S3 Partitioning
- Schedule: Year 1995 (300+ of 365 files)
- Folders created: year=1993/, year=1994/, year=1995/
- Progress: ~3% complete (3 of 33 schedule years)

### Glue Crawlers
- Crawlers created: nba-schedule-1993-crawler, nba-schedule-1994-crawler, nba-schedule-1995-crawler
- Currently running: nba-schedule-1994-crawler (RUNNING state)
- 1993 crawler: Completed (state was STOPPING when script checked)

---

## Expected Completion

**Best Case (All Parallel):**
- S3 Partitioning: ~2 hours (by 12:30 AM)
- Glue Crawlers: ~3 hours (by 1:30 AM)
- **Total: ~3-4 hours** (complete by 1:30-2:30 AM)

**Worst Case (Sequential Issues):**
- S3 Partitioning: ~3 hours
- Glue Crawlers: ~8 hours (if not parallelized)
- **Total: ~8-10 hours** (complete by 6:30-8:30 AM)

**Most Likely:** Complete by 2:00-3:00 AM

---

## What Happens If There's an Error

### S3 Partitioning Errors
- Script will continue with other data types
- Check `partition_overnight.log` for "FAILED" messages
- Manually re-run failed data type:
  ```bash
  echo "yes" | python scripts/etl/partition_by_year.py --data-types <type> --execute
  ```

### Crawler Errors
- Script will skip failed year and continue
- Check `crawler_overnight.log` for timeout messages
- Manually start failed crawler:
  ```bash
  aws glue start-crawler --name nba-<type>-<year>-crawler
  ```

---

## Next Steps (When Complete)

### Morning Checklist

1. **Verify Completion**
   ```bash
   ./scripts/shell/check_partition_status.sh  # Should show 132/132 year folders
   tail -50 crawler_overnight.log             # Should show "ALL CRAWLERS STARTED"
   ```

2. **Check Glue Tables Created**
   ```bash
   aws glue get-tables --database-name nba_raw_data --query 'TableList[].Name' --output table
   ```
   Expected: ~108 tables (one per year per data type)

3. **Verify Sample Data**
   ```bash
   # Check one table
   aws glue get-table --database-name nba_raw_data --name schedule_year_1997

   # Preview data with Athena (in AWS Console)
   SELECT * FROM nba_raw_data.schedule_year_1997 LIMIT 10;
   ```

4. **Update PROGRESS.md**
   - Mark Phase 2.1 as ✅ COMPLETE
   - Update with actual completion time
   - Note any issues encountered

5. **Begin Phase 2.2: Glue ETL Job**
   - Design ETL to extract 10% of fields
   - Create transformation scripts
   - Test on one year of data

---

## Cost Impact

**S3 Operations:**
- 146,115 copy operations (within same bucket)
- Cost: ~$0.10-0.15

**Glue Crawlers:**
- 108 crawlers × 5 min avg = ~9 hours total
- With 10 parallel: ~1 hour real time
- Cost: ~$0.88 (108 × 5 min × $0.44/DPU-hour)

**Total Overnight Cost:** ~$1.00

**Monthly Recurring Cost:** None (one-time operations)

---

## Process Details

### Process Tree
```
Terminal
├── partition_all_overnight.sh (PID 48440)
│   └── partition_by_year.py (PID 48453)
│       └── boto3 S3 copy operations
└── run_crawlers_overnight.sh (PID 50899)
    ├── AWS Glue API calls (create crawlers)
    └── AWS Glue API calls (start crawlers)
        └── Glue Crawlers running in AWS (10 max concurrent)
```

### Data Flow
```
Original S3 Structure (Flat)         Partitioned S3 Structure           Glue Tables
─────────────────────────           ────────────────────────           ───────────
schedule/19961219.json      →       schedule/                   →      nba_raw_data.schedule_year_1996
schedule/19961220.json              └── year=1996/                     nba_raw_data.schedule_year_1997
schedule/19971015.json                  ├── 19961219.json              ...
pbp/171031017.json                      └── 19961220.json
...                                 pbp/
                                    └── year=1997/
                                        └── 171031017.json
```

---

## Recovery Commands (If Needed)

**If partitioning process dies:**
```bash
nohup ./scripts/etl/partition_all_overnight.sh > partition_overnight.log 2>&1 &
echo $! > partition.pid
```

**If crawler process dies:**
```bash
nohup ./scripts/etl/run_crawlers_overnight.sh > crawler_overnight.log 2>&1 &
echo $! > crawler.pid
```

**Kill everything and start over:**
```bash
# Kill processes
kill $(cat partition.pid) 2>/dev/null
kill $(cat crawler.pid) 2>/dev/null

# Wait 5 seconds
sleep 5

# Restart both
nohup ./scripts/etl/partition_all_overnight.sh > partition_overnight.log 2>&1 &
echo $! > partition.pid
nohup ./scripts/etl/run_crawlers_overnight.sh > crawler_overnight.log 2>&1 &
echo $! > crawler.pid
```

---

**Note:** Both processes use `nohup` and run in the background, so they will continue even if:
- Your terminal disconnects
- Your computer goes to sleep (may pause, will resume when wakes)
- You close your laptop (SSH connections will persist)

Sleep well! Everything should be ready by morning. 🌙