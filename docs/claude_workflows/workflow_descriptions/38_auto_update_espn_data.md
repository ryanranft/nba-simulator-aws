# Workflow #38: Auto-Update ESPN Data

**Purpose:** Automatically detect data gaps and run ESPN scraper to fill missing dates

**When to use:**
- Daily/weekly maintenance to keep data current
- After returning from trips or extended absences
- Before running simulations or ML training
- As part of automated cron jobs

**Estimated time:** 5-15 minutes (depending on gap size)

**Cost impact:** $0 (scraping is free, S3 storage minimal)

---

## Prerequisites

- AWS CLI configured
- ESPN scraper installed at `/Users/ryanranft/0espn`
- S3 bucket: `s3://nba-sim-raw-data-lake`
- RDS credentials in `~/nba-sim-credentials.env`

---

## Quick Run

```bash
bash scripts/etl/auto_update_espn_data.sh
```

This script automatically:
1. ✓ Checks today's date
2. ✓ Finds last date with data in S3
3. ✓ Calculates gap (days missing)
4. ✓ Updates ESPN scraper end_date
5. ✓ Runs ESPN scraper for missing dates
6. ✓ Uploads new files to S3
7. ✓ Extracts to RDS database
8. ✓ Verifies results

---

## What the Script Does

### Step 1: Date Detection
```bash
# Get today's date
TODAY=$(date +%Y-%m-%d)

# Find last file in S3
LAST_S3_FILE=$(aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | tail -1)

# Extract date from filename
LAST_S3_DATE=$(date -j -f "%Y%m%d" "$LAST_S3_DATE_RAW" "+%Y-%m-%d")
```

### Step 2: Gap Calculation
```bash
# Calculate days missing
GAP_DAYS=$(( ($TODAY_TS - $LAST_TS) / 86400 ))

# If GAP_DAYS <= 0: Data is up to date, exit
# If GAP_DAYS > 0: Continue with scraping
```

### Step 3: Update Scraper
```bash
# Backup original scraper
cp /Users/ryanranft/0espn/espn/nba/nba_schedule.py \
   /Users/ryanranft/0espn/espn/nba/nba_schedule.py.bak.YYYYMMDD_HHMMSS

# Update end_date to today
sed -i '' "s/end_date = datetime\.date([0-9]\{4\}, [0-9]\{1,2\}, [0-9]\{1,2\})/end_date = datetime.date($TODAY_YEAR, $TODAY_MONTH, $TODAY_DAY)/" \
  /Users/ryanranft/0espn/espn/nba/nba_schedule.py
```

### Step 4: Run ESPN Scraper
```bash
cd /Users/ryanranft/0espn
python espn/nba/nba_schedule.py
```

ESPN scraper will:
- Check local cache first (skip existing files)
- Fetch only missing dates
- Save to `/Users/ryanranft/0espn/data/nba/`

### Step 5: Upload to S3
```bash
aws s3 sync /Users/ryanranft/0espn/data/nba/ \
  s3://nba-sim-raw-data-lake/schedule/ \
  --exclude "*" --include "*.json" --size-only
```

### Step 6: Extract to RDS
```bash
cd /Users/ryanranft/nba-simulator-aws
python scripts/etl/extract_schedule_local.py --year-range LAST_YEAR-CURRENT_YEAR
```

### Step 7: Verification
```bash
# Count new games
psql -h $NBA_SIM_DB_HOST -U $NBA_SIM_DB_USER -d $NBA_SIM_DB_NAME -c \
  "SELECT COUNT(*) FROM games WHERE game_date >= 'LAST_S3_DATE';"

# Check latest date
psql -h $NBA_SIM_DB_HOST -U $NBA_SIM_DB_USER -d $NBA_SIM_DB_NAME -c \
  "SELECT MAX(game_date) FROM games;"
```

---

## Example Output

```
=========================================
ESPN DATA GAP DETECTION & AUTO-UPDATE
=========================================

Step 1: Checking today's date...
  Today: 2025-10-04

Step 2: Finding last date with data in S3...
  Last file: schedule/20250630.json
  Last date: 2025-06-30

Step 3: Calculating data gap...
  Days missing: 96

⚠ Gap detected: 96 days of missing data
  From: 2025-06-30 (exclusive)
  To:   2025-10-04 (inclusive)

Proceed with ESPN scraping? (y/n): y

=========================================
Step 4: Updating ESPN scraper date range...
=========================================

  Backed up: nba_schedule.py.bak.20251004_143022
✓ Updated end_date to: datetime.date(2025, 10, 4)

=========================================
Step 5: Running ESPN scraper...
=========================================

  Working directory: /Users/ryanranft/0espn
  Running: python espn/nba/nba_schedule.py

Fetching schedule for 2025-07-01...
Fetching schedule for 2025-07-02...
...
Fetching schedule for 2025-10-04...

✓ ESPN scraper completed successfully

=========================================
Step 6: Uploading new files to S3...
=========================================

  Files in S3 before sync: 146115
  Files in S3 after sync:  146211
✓ Uploaded 96 new files

=========================================
Step 7: Extracting to RDS database...
=========================================

  Working directory: /Users/ryanranft/nba-simulator-aws
  Running: python scripts/etl/extract_schedule_local.py --year-range 2025-2025

Extracting games for year 2025...
Inserted 247 new games

✓ ETL extraction completed successfully

=========================================
Step 8: Verification...
=========================================

Checking RDS database for new games...
  Games added since 2025-06-30: 247
  Latest date in database: 2025-10-04

=========================================
UPDATE COMPLETE
=========================================

✓ ESPN data updated successfully

Summary:
  - Gap filled: 96 days
  - New files uploaded: 96
  - Date range: 2025-06-30 to 2025-10-04
  - S3 files: 146211 total
  - Database games: 247 new
  - Latest DB date: 2025-10-04

Backup saved: nba_schedule.py.bak.20251004_143022

=========================================
```

---

## Manual Step-by-Step (If Script Fails)

If the automated script fails, follow these manual steps:

### 1. Check Current Gap
```bash
# Today's date
date +%Y-%m-%d

# Last S3 file
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | tail -1
```

### 2. Update ESPN Scraper
```bash
# Backup
cp /Users/ryanranft/0espn/espn/nba/nba_schedule.py \
   /Users/ryanranft/0espn/espn/nba/nba_schedule.py.bak

# Edit line 142 manually
nano /Users/ryanranft/0espn/espn/nba/nba_schedule.py
# Change: end_date = datetime.date(2025, 6, 30)
# To:     end_date = datetime.date(YYYY, MM, DD)  # Today's date
```

### 3. Run Scraper
```bash
cd /Users/ryanranft/0espn
python espn/nba/nba_schedule.py
```

### 4. Upload to S3
```bash
aws s3 sync /Users/ryanranft/0espn/data/nba/ \
  s3://nba-sim-raw-data-lake/schedule/ \
  --exclude "*" --include "*.json" --size-only
```

### 5. Extract to RDS
```bash
cd /Users/ryanranft/nba-simulator-aws
source ~/nba-sim-credentials.env
python scripts/etl/extract_schedule_local.py --year-range 2025-2025
```

### 6. Verify
```bash
psql -h $NBA_SIM_DB_HOST -U $NBA_SIM_DB_USER -d $NBA_SIM_DB_NAME -c \
  "SELECT MAX(game_date), COUNT(*) FROM games WHERE game_date >= '2025-07-01';"
```

---

## Automation Options

### Option 1: Daily Cron Job
```bash
# Add to crontab: crontab -e
0 2 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/auto_update_espn_data.sh >> /tmp/espn_auto_update.log 2>&1
```

Runs every day at 2:00 AM.

### Option 2: Weekly Cron Job
```bash
# Add to crontab: crontab -e
0 2 * * 0 /Users/ryanranft/nba-simulator-aws/scripts/etl/auto_update_espn_data.sh >> /tmp/espn_auto_update.log 2>&1
```

Runs every Sunday at 2:00 AM.

### Option 3: Manual on Demand
```bash
bash scripts/etl/auto_update_espn_data.sh
```

---

## Troubleshooting

### Script says "Data is up to date"
- ✓ This is normal if you ran it recently
- Last S3 date matches today's date
- No action needed

### ESPN scraper fails
```bash
# Check error message
cd /Users/ryanranft/0espn
python espn/nba/nba_schedule.py

# Common issues:
# - Rate limiting: Add sleep delay in scraper
# - Network error: Check internet connection
# - ESPN API change: Review scraper code
```

### S3 upload fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check bucket exists
aws s3 ls s3://nba-sim-raw-data-lake/

# Manually upload
aws s3 cp /Users/ryanranft/0espn/data/nba/20251004.json \
  s3://nba-sim-raw-data-lake/schedule/20251004.json
```

### RDS extraction fails
```bash
# Check credentials
source ~/nba-sim-credentials.env
echo $NBA_SIM_DB_HOST

# Test connection
psql -h $NBA_SIM_DB_HOST -U $NBA_SIM_DB_USER -d $NBA_SIM_DB_NAME -c "SELECT 1;"

# Run extraction manually
python scripts/etl/extract_schedule_local.py --year-range 2025-2025
```

### Backup not restored on failure
```bash
# Manually restore
cp /Users/ryanranft/0espn/espn/nba/nba_schedule.py.bak.YYYYMMDD_HHMMSS \
   /Users/ryanranft/0espn/espn/nba/nba_schedule.py
```

---

## Important Notes

**ESPN Scraper Behavior:**
- Uses local cache: Only fetches missing files
- No rate limiting by default (line 157: `time.sleep(0)`)
- If ESPN blocks: Add `time.sleep(0.25)` in scraper

**S3 Sync:**
- `--size-only` flag: Only uploads if file size differs
- Does NOT overwrite identical files
- Safe to run multiple times

**Date Handling:**
- Script uses macOS `date` command syntax
- For Linux, change: `date -j -f "%Y%m%d"` → `date -d`

**Database:**
- ETL script uses `INSERT ON CONFLICT DO NOTHING`
- Safe to run multiple times (no duplicates)
- Skips games that already exist

---

## Success Criteria

- [ ] Script runs without errors
- [ ] Gap detected and calculated correctly
- [ ] ESPN scraper fetches missing dates
- [ ] New files uploaded to S3
- [ ] Games extracted to RDS
- [ ] Latest DB date matches today
- [ ] Backup created of original scraper

---

## Related Workflows

- **Workflow #37:** Shutdown Compute Instances (before trips)
- **1.0003-1.4:** Data Gap Filling (data quality analysis)
- **Phase 0:** Data Collection & Initial Upload

---

## Cost Impact

**No additional costs:**
- ESPN scraping: Free (HTTP requests)
- S3 storage: ~$0.023/GB/month (96 files ≈ 2MB ≈ $0.00005/month)
- RDS queries: Included in existing db.t4g.micro cost

**Typical gap sizes:**
- Daily run: 0-1 days (0-1 files)
- Weekly run: 7 days (7 files)
- After 1 month trip: 30 days (30 files)
- After 3 month trip: 90 days (90 files)

---

*Last updated: October 4, 2025*
*Automates ESPN data updates with gap detection*