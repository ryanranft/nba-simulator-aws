# hoopR Data Verification Scripts

These scripts check for gaps in your hoopR data collection and help identify what needs to be backfilled.

---

## Quick Start

### 1. Verify Overall Coverage

```bash
python scripts/validation/verify_hoopr_coverage.py
```

**What it checks:**
- ✅ Earliest to latest game dates
- ✅ Total games and seasons covered
- ✅ Coverage by NBA season
- ✅ Current season (2025-26) status
- ✅ Recent collection activity
- ⚠️ Large data gaps (>7 days)

**Example Output:**
```
================================================================================
HOOPR DATA COVERAGE OVERVIEW
================================================================================

📊 Overall Coverage:
   Earliest Game: 2002-10-29
   Latest Game:   2025-11-09
   Total Games:   30,758
   Seasons:       24
   Time Span:     8,412 days (23.0 years)

================================================================================
COVERAGE BY NBA SEASON
================================================================================

Season     Games      First Game      Last Game       Span (days)  Status
---------------------------------------------------------------------------------
2025-26    45         2025-10-22      2025-11-09      18           🔄 Current
2024-25    1,318      2024-10-22      2025-04-13      173          ✅ Complete
2023-24    1,230      2023-10-24      2024-04-14      173          ✅ Complete
...

================================================================================
POTENTIAL DATA GAPS (>7 days with no games)
================================================================================

Gap Start       Gap End         Days       Likely Reason
-----------------------------------------------------------------
2025-06-19      2025-10-22      125        Offseason (expected)
2025-03-15      2025-06-19      96         ⚠️  DATA MISSING
...

================================================================================
CURRENT SEASON (2025-26) STATUS
================================================================================

✅ Current Season Data Found:
   Games:      45
   First Game: 2025-10-22
   Last Game:  2025-11-09
   Status:     ✅ Up to date (today)
```

---

### 2. Identify Specific Gaps

```bash
python scripts/validation/identify_hoopr_gaps.py
```

**What it does:**
- Finds all date gaps in the data
- Categorizes by severity (critical, important, minor, offseason)
- Saves detailed JSON report

**With JSON output:**
```bash
python scripts/validation/identify_hoopr_gaps.py --output gaps_report.json
```

**For specific date range:**
```bash
python scripts/validation/identify_hoopr_gaps.py \
  --start-date 2025-03-01 \
  --end-date 2025-10-31
```

**Generate backfill script:**
```bash
python scripts/validation/identify_hoopr_gaps.py --generate-backfill
```

This creates `scripts/backfill_hoopr_gaps.R` with seasons that need backfilling.

---

## Common Usage Patterns

### Check if you're up to date
```bash
# Quick check
python scripts/validation/verify_hoopr_coverage.py

# Look for "Latest Game" and "Status" under current season
```

### Find what's missing
```bash
# Get detailed gap analysis
python scripts/validation/verify_hoopr_coverage.py --detailed

# Save gaps to file
python scripts/validation/identify_hoopr_gaps.py --output gaps.json
```

### Check specific season
```bash
# Check 2025-26 season
python scripts/validation/verify_hoopr_coverage.py --season 2025

# Check all seasons
python scripts/validation/verify_hoopr_coverage.py
```

---

## Understanding the Output

### Gap Categories

**Critical (>7 days):**
- Large gaps during NBA season
- Likely missing data that needs backfill
- **Action:** Run comprehensive scraper for those dates

**Important (3-7 days):**
- Medium gaps during season
- Could be All-Star break or data issue
- **Action:** Verify if legitimate break or missing data

**Minor (1-3 days):**
- Small gaps, often weekends or travel days
- Usually not a problem
- **Action:** None needed unless consistent pattern

**Offseason (June-September):**
- Expected gaps between seasons
- No action needed
- **Action:** None

---

## What to Do If Gaps Are Found

### Gap in 2025-26 Current Season

```bash
# Start autonomous collection (will catch up automatically)
python scripts/autonomous/autonomous_cli.py start

# Or manually collect recent games
Rscript scripts/etl/scrape_hoopr_all_152_endpoints.R --season 2025 --recent-games
```

### Gap in Previous Season (e.g., March-October 2025)

```bash
# Run comprehensive collection for that season
Rscript scripts/etl/scrape_hoopr_all_152_endpoints.R --season 2025 --all-phases

# This will:
# - Collect all 152 endpoints
# - Only get data not already in database
# - Upload to S3
# - Take 2-3 hours
```

### Multiple Seasons Missing

```bash
# Generate backfill script
python scripts/validation/identify_hoopr_gaps.py --generate-backfill

# Review the generated script
cat scripts/backfill_hoopr_gaps.R

# Run it (will take several hours per season)
Rscript scripts/backfill_hoopr_gaps.R
```

---

## Database Connection

Scripts use these environment variables (with defaults):

```bash
export POSTGRES_HOST=localhost        # Default: localhost
export POSTGRES_DB=nba_simulator      # Default: nba_simulator
export POSTGRES_USER=ryanranft        # Default: ryanranft
export POSTGRES_PASSWORD=             # Default: empty (trust auth)
export POSTGRES_PORT=5432             # Default: 5432
```

For RDS connection:
```bash
export POSTGRES_HOST=<your-rds-endpoint>
export POSTGRES_DB=nba_simulator
export POSTGRES_USER=<your-username>
export POSTGRES_PASSWORD=<your-password>
```

---

## Interpreting Results

### Good Coverage Example
```
✅ Current Season Data Found:
   Games:      45
   Last Game:  2025-11-09
   Status:     ✅ Up to date (today)

✅ No significant gaps found (all gaps < 7 days)

✅ Data coverage looks good! No major issues detected.
```

### Needs Attention Example
```
❌ NO DATA for 2025-26 season (started ~Oct 22, 2025)

⚠️  LARGE DATA GAPS DETECTED:
   2025-03-15 to 2025-10-22 (221 days)

⚠️  STALE DATA: Latest game is 15 days old

📋 Actions to Take:
   1. Start autonomous collection system
   2. Run backfill script for missing periods
```

---

## Troubleshooting

### "Database connection failed"
- Check PostgreSQL is running: `psql -d nba_simulator -c "SELECT 1;"`
- Verify credentials with environment variables
- Ensure `hoopr_schedule` table exists

### "No data found in hoopr_schedule table"
- Table might be empty or in different schema
- Check: `psql -d nba_simulator -c "SELECT COUNT(*) FROM hoopr_schedule;"`
- If zero, you need to load data first

### "psycopg2 not installed"
```bash
pip install psycopg2-binary
```

---

## Files Created

- `verify_hoopr_coverage.py` - Main verification script (overview + gaps)
- `identify_hoopr_gaps.py` - Detailed gap analysis + JSON export
- `backfill_hoopr_gaps.R` - Auto-generated backfill script (when using --generate-backfill)
- `gaps_report.json` - Detailed gap report (when using --output)

---

## Next Steps After Running

1. **If gaps found:** Use backfill scripts to collect missing data
2. **If current:** Start autonomous system to keep updated
3. **If stale:** Run incremental scraper or restart autonomous system

---

**Created:** November 9, 2025
**For:** hoopR data verification and gap detection
