# Workflow #45: Local Data Inventory System

**Purpose:** Comprehensive system to inventory all local data (disk, database, S3), identify what you have, what's missing, and generate data status reports.

**Created:** October 8, 2025
**Last Updated:** October 8, 2025
**Related Workflows:** #46 (Data Gap Analysis), #40 (Scraper Operations)

---

## When to Use This Workflow

**Use this workflow when:**
- Starting a new session and need to understand current data state
- Planning which scrapers to run next
- Checking if you have data for a specific analysis
- Documenting data collection progress
- Preparing for data processing tasks
- Verifying data integrity after scraping
- Creating data status reports for documentation

**Before running:**
- Ensure project environment is activated (`conda activate nba-aws`)
- AWS credentials configured (`aws configure list`)
- Database credentials available (if checking RDS)

---

## Quick Reference

### Common Data Inventory Commands

```bash
# Quick data summary (fast, <30 seconds)
bash scripts/monitoring/inventory_local_data.sh --quick

# Full data inventory (comprehensive, 2-5 minutes)
bash scripts/monitoring/inventory_local_data.sh --full

# Check specific data source
bash scripts/monitoring/inventory_local_data.sh --source kaggle
bash scripts/monitoring/inventory_local_data.sh --source espn
bash scripts/monitoring/inventory_local_data.sh --source hoopr

# Database inventory
bash scripts/monitoring/inventory_database.sh

# S3 inventory
bash scripts/monitoring/inventory_s3.sh

# Generate data status report
bash scripts/monitoring/generate_data_report.sh
```

---

## Complete Workflow Steps

### Phase 1: Local Disk Data Inventory

**Purpose:** Inventory all data files on local disk

**Step 1.1: Project Data Directory Inventory**

```bash
echo "Inventorying project data directory..."
echo ""

# Primary project data location
PROJECT_DATA="/Users/ryanranft/nba-simulator-aws/data"

if [ -d "$PROJECT_DATA" ]; then
    echo "📁 PROJECT DATA: $PROJECT_DATA"
    echo ""

    # Show size of each subdirectory
    du -sh "$PROJECT_DATA"/* 2>/dev/null
    echo ""

    # Count files by type
    echo "File counts by directory:"
    for dir in "$PROJECT_DATA"/*; do
        if [ -d "$dir" ]; then
            file_count=$(find "$dir" -type f -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
            echo "  $(basename "$dir"): $file_count JSON files"
        fi
    done
    echo ""

    # Total counts
    echo "Total statistics:"
    find "$PROJECT_DATA" -type f -name "*.json" 2>/dev/null | wc -l | xargs echo "  JSON files:"
    find "$PROJECT_DATA" -type f -name "*.csv" 2>/dev/null | wc -l | xargs echo "  CSV files:"
    du -sh "$PROJECT_DATA" | awk '{print "  Total size: " $1}'
else
    echo "⚠️  Project data directory not found: $PROJECT_DATA"
fi
```

**Expected output:**
```
📁 PROJECT DATA: /Users/ryanranft/nba-simulator-aws/data

4.4G    kaggle
 31G    nba_box_score
 40G    nba_pbp
9.2G    nba_schedule_json
 31G    nba_team_stats

File counts by directory:
  kaggle: 0 JSON files
  nba_box_score: 44830 JSON files
  nba_pbp: 44828 JSON files
  nba_schedule_json: 11635 JSON files
  nba_team_stats: 44830 JSON files

Total statistics:
  JSON files: 146115
  CSV files: 18
  Total size: 115 GB
```

**Step 1.1b: External ESPN Data (if used)**

```bash
echo "Checking external ESPN data source..."
echo ""

# External ESPN data location (used by some ETL scripts)
ESPN_DATA="/Users/ryanranft/0espn/data/nba"

if [ -d "$ESPN_DATA" ]; then
    echo "📁 EXTERNAL ESPN DATA: $ESPN_DATA"
    echo ""
    du -sh "$ESPN_DATA"/* 2>/dev/null
    echo ""

    # Count files
    echo "File counts:"
    for dir in "$ESPN_DATA"/*; do
        if [ -d "$dir" ]; then
            file_count=$(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
            echo "  $(basename "$dir"): $file_count files"
        fi
    done
else
    echo "ℹ️  External ESPN data not found (may not be needed)"
fi
```

**Expected output:**
```
📁 EXTERNAL ESPN DATA: /Users/ryanranft/0espn/data/nba

 31G    nba_box_score
 40G    nba_pbp
9.2G    nba_schedule_json
 31G    nba_team_stats
1.5G    box_scores

File counts:
  nba_box_score: 44830 files
  nba_pbp: 44828 files
  nba_schedule_json: 11635 files
  nba_team_stats: 44830 files
  box_scores: 153 files
```

**Step 1.1c: Git Commit Archives**

```bash
echo "Checking git commit archives (conversation logs)..."
echo ""

# Git commit conversation archives
ARCHIVES_DIR="$HOME/sports-simulator-archives/nba"

if [ -d "$ARCHIVES_DIR" ]; then
    echo "📁 GIT COMMIT ARCHIVES: $ARCHIVES_DIR"
    echo ""

    # Count archive directories
    archive_count=$(ls -1 "$ARCHIVES_DIR" | wc -l | tr -d ' ')
    echo "  Archive count: $archive_count conversation logs"

    # Total size
    du -sh "$ARCHIVES_DIR" | awk '{print "  Total size: " $1}'

    # Show latest 5 archives
    echo ""
    echo "  Latest 5 archives:"
    ls -lt "$ARCHIVES_DIR" | head -6 | tail -5 | awk '{print "    " $9}'
else
    echo "ℹ️  No git commit archives found"
fi
```

**Expected output:**
```
📁 GIT COMMIT ARCHIVES: /Users/ryanranft/sports-simulator-archives/nba

  Archive count: 67 conversation logs
  Total size: 26M

  Latest 5 archives:
    9b98954bd7c3a11e096a89bcaa00ac77b70b7d2d
    5b9f3f1491a657a86d2d238d39b166178fc57460
    a52a4d5783f42485163bca4e6da74a34042e8ca4a
    435b57280f42485163bca4e6da74a34042e8ca4a
    ab577e4e96029a354364997f539bd7cfa3380e495a0
```

**Step 1.2: Temporary Data Inventory**

```bash
echo "Checking temporary scraper data directories..."
echo ""

# All scraper temporary directory patterns
TEMP_PATTERNS=(
    "/tmp/temporal_data_*"        # Extracted temporal data ready for RDS
    "/tmp/hoopr_*"                 # hoopR scraper output
    "/tmp/nba_api_*"               # NBA API scraper output
    "/tmp/basketball_reference*"   # Basketball Reference scraper output
    "/tmp/kaggle_*"                # Kaggle dataset extractions
    "/tmp/espn_*"                  # ESPN scraper output
    "/tmp/sportsdataverse*"        # SportsDataverse scraper output
)

echo "📁 TEMPORARY SCRAPER DATA (/tmp/):"
echo ""

total_temp_size=0
total_temp_files=0

for pattern in "${TEMP_PATTERNS[@]}"; do
    for dir in $pattern 2>/dev/null; do
        if [ -d "$dir" ]; then
            size=$(du -sh "$dir" 2>/dev/null | awk '{print $1}')
            file_count=$(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')

            echo "  $(basename "$dir")/"
            echo "    Size: $size"
            echo "    Files: $file_count"
            echo ""
        fi
    done
done

# Check if any temp data exists
if [ "$total_temp_files" -eq 0 ]; then
    echo "  ℹ️  No temporary scraper data found"
    echo "  (This is normal if no scrapers are currently running)"
fi
```

**Step 1.3: Local Cache Inventory**

```bash
echo "Checking local data caches..."
echo ""

# Check if data/ directory exists (should be in .gitignore)
if [ -d data/ ]; then
    echo "⚠️  Warning: data/ directory exists (should be archived)"
    du -sh data/*
fi

# Check for any large files in project
find . -type f -size +100M ! -path "./.git/*" ! -path "./archived-docs/*"
```

---

### Phase 2: S3 Data Inventory

**Purpose:** Inventory all data stored in S3

**Step 2.1: S3 Bucket Overview**

```bash
echo "S3 Bucket: nba-sim-raw-data-lake"
echo ""

# Get total bucket size
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize | \
    grep "Total Size" | awk '{print "Total Size: " $3/1024/1024/1024 " GB"}'

# Count total files
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize | \
    grep "Total Objects" | awk '{print "Total Files: " $3}'
```

**Expected output:**
```
S3 Bucket: nba-sim-raw-data-lake
Total Size: 12.5 GB
Total Files: 146,115
```

**Step 2.2: S3 Inventory by Data Source**

```bash
echo "S3 Inventory by Source:"
echo ""

# Actual S3 bucket prefixes (from aws s3 ls s3://nba-sim-raw-data-lake/)
sources=(
    "athena-results"
    "basketball_reference"
    "box_scores"
    "hoopr_phase1"
    "ml-features"
    "ml-models"
    "ml-predictions"
    "nba_api_comprehensive"
    "nba_api_playbyplay"
    "pbp"
    "schedule"
    "scripts"
    "sportsdataverse"
    "team_stats"
)

printf "%-30s %12s %15s\n" "Source" "Files" "Size (MB)"
echo "---------------------------------------------------------------"

for source in "${sources[@]}"; do
    # Count files
    file_count=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive 2>/dev/null | wc -l | tr -d ' ')

    # Get size in bytes
    size_bytes=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive --summarize 2>/dev/null | \
        grep "Total Size" | awk '{print $3}')

    if [ -n "$size_bytes" ] && [ "$size_bytes" != "0" ]; then
        # Convert to MB
        size_mb=$(echo "scale=2; $size_bytes / 1024 / 1024" | bc)
        printf "%-30s %12s %15s\n" "$source" "$file_count" "$size_mb"
    elif [ "$file_count" -gt 0 ]; then
        printf "%-30s %12s %15s\n" "$source" "$file_count" "0.00"
    fi
done

echo ""
```

**Step 2.3: S3 Date Range Analysis**

```bash
echo "Analyzing S3 data date ranges..."
echo ""

# Check date range for each source
for source in basketball_reference espn hoopr nba_api; do
    echo "=== $source ==="

    # Find earliest and latest files
    aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive | \
        head -1 | awk '{print "Earliest: " $1 " " $2}'

    aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive | \
        tail -1 | awk '{print "Latest: " $1 " " $2}'

    echo ""
done
```

---

### Phase 3: Database Data Inventory

**Purpose:** Inventory all data in RDS PostgreSQL

**Step 3.1: Table Row Counts**

```bash
echo "Database Inventory (RDS PostgreSQL)"
echo ""

# Load credentials
source /Users/ryanranft/nba-sim-credentials.env

# Connect and get table counts
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF
```

**Expected output:**
```
 schemaname | tablename                  | size    | row_count
------------+----------------------------+---------+-----------
 public     | temporal_events            | 2.1 GB  | 18,500,000
 public     | play_by_play               | 890 MB  | 2,400,000
 public     | possession_panel           | 450 MB  | 850,000
 public     | player_game_stats          | 120 MB  | 450,000
 public     | games                      | 15 MB   | 44,828
 public     | players                    | 5 MB    | 4,852
```

**Step 3.2: Database Date Range Analysis**

```bash
echo "Database Date Range Analysis"
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Games date range
SELECT
    'games' AS table_name,
    MIN(game_date) AS earliest,
    MAX(game_date) AS latest,
    COUNT(*) AS total_games
FROM games;

-- Play-by-play date range
SELECT
    'play_by_play' AS table_name,
    MIN(game_date) AS earliest,
    MAX(game_date) AS latest,
    COUNT(DISTINCT game_id) AS games_with_pbp
FROM play_by_play;

-- Possession panel date range
SELECT
    'possession_panel' AS table_name,
    MIN(game_date) AS earliest,
    MAX(game_date) AS latest,
    COUNT(DISTINCT game_id) AS games_with_possessions
FROM possession_panel;
EOF
```

**Step 3.3: Data Completeness Check**

```bash
echo "Data Completeness Analysis"
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Games with complete data
SELECT
    COUNT(*) AS total_games,
    COUNT(CASE WHEN home_score IS NOT NULL AND away_score IS NOT NULL THEN 1 END) AS games_with_scores,
    COUNT(CASE WHEN completed = true THEN 1 END) AS completed_games,
    ROUND(100.0 * COUNT(CASE WHEN completed = true THEN 1 END) / COUNT(*), 2) AS completion_pct
FROM games;

-- Games by season
SELECT
    season,
    COUNT(*) AS games,
    COUNT(CASE WHEN completed = true THEN 1 END) AS completed
FROM games
GROUP BY season
ORDER BY season DESC
LIMIT 10;
EOF
```

---

### Phase 4: Data Source Comparison

**Purpose:** Compare what data exists across different locations

**Step 4.1: Cross-Reference Inventory**

```bash
echo "Cross-Reference: Archives vs S3 vs Database"
echo ""

# Check if data exists in each location
sources=("kaggle" "espn" "hoopr" "nba_api" "basketball_reference")

echo "Source              | Archives | S3       | Database"
echo "------------------------------------------------------------"

for source in "${sources[@]}"; do
    # Check archives
    if [ -d ~/sports-simulator-archives/nba/$source ]; then
        archive_files=$(find ~/sports-simulator-archives/nba/$source -type f | wc -l)
        archive_status="✅ $archive_files"
    else
        archive_status="❌ None"
    fi

    # Check S3
    s3_files=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive 2>/dev/null | wc -l)
    if [ "$s3_files" -gt 0 ]; then
        s3_status="✅ $s3_files"
    else
        s3_status="❌ None"
    fi

    # Check database (simplified - would need table mapping)
    db_status="See DB inventory"

    printf "%-20s | %-8s | %-8s | %s\n" "$source" "$archive_status" "$s3_status" "$db_status"
done
```

**Step 4.2: Identify Data Gaps**

```bash
echo "Identifying Data Gaps..."
echo ""

# Check for expected but missing data
echo "Missing Data Checks:"
echo ""

# Expected seasons range
START_SEASON=2016
END_SEASON=2024

for season in $(seq $START_SEASON $END_SEASON); do
    # Check if season exists in database
    game_count=$(psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" \
        -t -c "SELECT COUNT(*) FROM games WHERE season = $season;")

    if [ "$game_count" -lt 100 ]; then
        echo "⚠️  Season $season: Only $game_count games (expected ~1,230)"
    fi
done
```

---

### Phase 5: Generate Data Report

**Purpose:** Create comprehensive data status report

**Step 5.1: Create Report Template**

```bash
REPORT_FILE="DATA_INVENTORY_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" <<'EOF'
# NBA Simulator Data Inventory Report

**Generated:** $(date)
**System:** $(hostname)

---

## Summary

### Overall Status
- **Local Archives:** [SIZE]
- **S3 Bucket:** [SIZE] ([FILES] files)
- **Database:** [SIZE] ([ROWS] rows across [TABLES] tables)

### Completeness
- **Seasons Covered:** [START] - [END]
- **Total Games:** [COUNT]
- **Completion Rate:** [PERCENT]%

---

## Detailed Inventory

### 1. Local Archives

[ARCHIVE_DETAILS]

### 2. S3 Data Lake

[S3_DETAILS]

### 3. Database (RDS PostgreSQL)

[DB_DETAILS]

---

## Data Gaps Identified

[GAPS]

---

## Recommended Actions

[RECOMMENDATIONS]

EOF

echo "Report template created: $REPORT_FILE"
```

**Step 5.2: Populate Report with Data**

```bash
echo "Populating report with inventory data..."

# Run all inventory commands and save to variables
# Then use sed to replace placeholders in report

# This would be fully implemented in the actual script
```

---

## Output Examples

### Quick Inventory Output

```
=================================================================
NBA SIMULATOR - QUICK DATA INVENTORY
=================================================================
Generated: 2025-10-08 20:30:15

📁 LOCAL ARCHIVES
  Location: ~/sports-simulator-archives/nba/
  Total Size: 12.4 GB
  Total Files: 89,456

☁️  S3 DATA LAKE
  Bucket: nba-sim-raw-data-lake
  Total Size: 12.5 GB
  Total Files: 146,115

💾 DATABASE (RDS)
  Instance: nba-sim-db
  Total Size: 3.8 GB
  Total Tables: 16
  Total Rows: 25,500,000

📊 DATA COVERAGE
  Seasons: 2016-2024 (9 seasons)
  Total Games: 44,828
  Completion: 98.5%

✅ STATUS: Data inventory complete
=================================================================
```

### Full Inventory Output

```
=================================================================
NBA SIMULATOR - FULL DATA INVENTORY
=================================================================

📁 LOCAL ARCHIVES DETAIL
-----------------------------------------------------------------
basketball_reference/    2.5 GB    15,234 files
├── games/               890 MB    12,345 JSON
├── players/             1.2 GB    2,456 JSON
└── teams/               430 MB    433 JSON

espn/                    1.8 GB    23,456 files
├── play_by_play/        1.1 GB    18,234 JSON
├── box_scores/          456 MB    4,567 JSON
└── team_stats/          234 MB    655 JSON

hoopr/                   3.2 GB    34,567 files
├── player_tracking/     2.1 GB    28,456 JSON
├── shot_charts/         890 MB    5,234 JSON
└── lineups/             210 MB    877 JSON

kaggle/                  890 MB    2 files
└── nba.sqlite          890 MB    1 file

nba_api/                 4.1 GB    14,199 files
├── playbyplay/          2.8 GB    10,234 JSON
├── boxscores/           890 MB    2,345 JSON
└── scoreboard/          420 MB    1,620 JSON

☁️  S3 DATA LAKE DETAIL
-----------------------------------------------------------------
basketball_reference/    146,115 files    2.8 GB
espn/                     89,234 files    2.1 GB
hoopr/                   112,456 files    3.5 GB
nba_api/                  45,678 files    2.4 GB
pbpstats/                 12,345 files    890 MB
kaggle/                        1 file    890 MB
ml-features/                   3 files     45 MB

💾 DATABASE DETAIL
-----------------------------------------------------------------
Table                        Rows          Size        Coverage
------------------------------------------------------------------
temporal_events         18,500,000       2.1 GB      2016-2024
play_by_play             2,400,000       890 MB      2016-2024
possession_panel           850,000       450 MB      2016-2024
player_game_stats          450,000       120 MB      2016-2024
team_game_stats             90,000        25 MB      2016-2024
games                       44,828        15 MB      2016-2024
players                      4,852         5 MB      All-time
teams                           30       128 KB      All-time

📊 COMPLETENESS ANALYSIS
-----------------------------------------------------------------
Season    Expected    Actual    Completed    Percent
2024        1,230     1,230        1,189      96.7%
2023        1,230     1,230        1,230     100.0%
2022        1,230     1,230        1,230     100.0%
2021        1,230     1,095        1,095     100.0%  (COVID season)
2020        1,230       971          971     100.0%  (COVID season)
2019        1,230     1,230        1,230     100.0%
2018        1,230     1,230        1,230     100.0%
2017        1,230     1,230        1,230     100.0%
2016        1,230     1,230        1,230     100.0%

⚠️  DATA GAPS IDENTIFIED
-----------------------------------------------------------------
• Season 2024: 41 games incomplete (in progress)
• hoopr source: Missing data before 2018
• pbpstats: Only partial coverage (2020-2024)

=================================================================
```

---

## Data Inventory Scripts

### Quick Inventory Script

Create `scripts/monitoring/inventory_local_data.sh`:

```bash
#!/bin/bash
# Quick local data inventory

echo "==================================================================="
echo "NBA SIMULATOR - QUICK DATA INVENTORY"
echo "==================================================================="
echo "Generated: $(date)"
echo ""

# Archives
if [ -d ~/sports-simulator-archives/nba ]; then
    echo "📁 LOCAL ARCHIVES"
    echo "  Location: ~/sports-simulator-archives/nba/"
    du -sh ~/sports-simulator-archives/nba/ | awk '{print "  Total Size: " $1}'
    find ~/sports-simulator-archives/nba -type f | wc -l | xargs echo "  Total Files:"
    echo ""
fi

# S3
echo "☁️  S3 DATA LAKE"
echo "  Bucket: nba-sim-raw-data-lake"
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | grep "Total Size" | awk '{print "  Total Size: " $3/1024/1024/1024 " GB"}'
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | grep "Total Objects" | awk '{print "  Total Files: " $3}'
echo ""

# Database (if credentials available)
if [ -f /Users/ryanranft/nba-sim-credentials.env ]; then
    source /Users/ryanranft/nba-sim-credentials.env
    echo "💾 DATABASE (RDS)"
    echo "  Instance: nba-sim-db"

    # Get total size and counts
    psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
        SELECT
            pg_size_pretty(pg_database_size('$DB_NAME')) AS total_size,
            COUNT(DISTINCT tablename) AS tables
        FROM pg_stat_user_tables;
    " 2>/dev/null | awk '{print "  Total Size: " $1}'

    psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
        SELECT COUNT(DISTINCT tablename) FROM pg_stat_user_tables;
    " 2>/dev/null | xargs echo "  Total Tables:"

    psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
        SELECT SUM(n_live_tup) FROM pg_stat_user_tables;
    " 2>/dev/null | xargs echo "  Total Rows:"

    echo ""
fi

echo "✅ STATUS: Data inventory complete"
echo "==================================================================="
```

---

## Best Practices

### When to Run Inventory

**Daily:**
- Quick inventory before starting work
- Check if recent scraper runs completed

**Weekly:**
- Full inventory to track data growth
- Compare archives vs S3 vs database

**After Major Operations:**
- After running scrapers
- After loading data to database
- After archiving files
- Before/after data cleanup

### Data Organization Principles

1. **Single Source of Truth**
   - S3 = permanent storage (raw data)
   - Database = processed, queryable data
   - Archives = local backup (temporary)

2. **Archive Management**
   - Archive to S3 weekly
   - Delete local archives after S3 upload verified
   - Keep only current scraping session locally

3. **Database Hygiene**
   - Regular VACUUM ANALYZE
   - Monitor table sizes
   - Archive old data if needed

---

## Troubleshooting

### Issue: Can't Access S3

**Error:** `Unable to locate credentials`

**Solution:**
```bash
# Check AWS credentials
aws configure list

# If not configured
aws configure
```

### Issue: Database Connection Fails

**Error:** `password authentication failed`

**Solution:**
```bash
# Verify credentials file exists
ls -l /Users/ryanranft/nba-sim-credentials.env

# Test connection
source /Users/ryanranft/nba-sim-credentials.env
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -c "SELECT 1;"
```

### Issue: Archive Directory Not Found

**Error:** `No such file or directory`

**Solution:**
```bash
# Create archive structure
mkdir -p ~/sports-simulator-archives/nba/{kaggle,espn,hoopr,nba_api,basketball_reference}
```

---

## Related Workflows

- **Workflow #46:** Data Gap Analysis - Analyze and fill data gaps
- **Workflow #40:** Scraper Operations - Run scrapers to collect data
- **Workflow #42:** Scraper Management - Manage long-running scraper jobs

---

## Success Criteria

✅ Can generate quick inventory in <30 seconds
✅ Can generate full inventory in <5 minutes
✅ Identifies all data sources (archives, S3, database)
✅ Shows size and file counts for each source
✅ Identifies date ranges and completeness
✅ Generates readable reports
✅ Identifies data gaps clearly

---

**Last Updated:** October 8, 2025
**Next Review:** Monthly (update with new data sources)