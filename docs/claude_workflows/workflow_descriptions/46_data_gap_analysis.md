# Workflow #46: Data Gap Analysis & Remediation

**Purpose:** Identify missing data, analyze gaps, prioritize collection efforts, and create action plans to fill data gaps.

**Created:** October 8, 2025
**Last Updated:** October 8, 2025
**Related Workflows:** #45 (Local Data Inventory), #40 (Scraper Operations), #42 (Scraper Management)

---

## When to Use This Workflow

**Use this workflow when:**
- Starting a new analysis and need to verify data availability
- Planning scraper runs to collect missing data
- After inventory (#45) shows gaps
- Before model training (need complete feature data)
- Preparing for temporal queries (need complete time-series)
- Documenting data collection status
- Prioritizing which scrapers to run next

**Prerequisites:**
- Run Workflow #45 (Local Data Inventory) first
- Understand your analysis requirements
- Know which seasons/data you need

---

## Quick Reference

### Common Gap Analysis Commands

```bash
# Identify missing games by season
bash scripts/analysis/find_missing_games.sh

# Check data source coverage
bash scripts/analysis/check_source_coverage.sh

# Analyze temporal gaps
bash scripts/analysis/find_temporal_gaps.sh

# Compare expected vs actual data
bash scripts/analysis/compare_expected_actual.sh

# Generate gap remediation plan
bash scripts/analysis/generate_gap_plan.sh
```

---

## Gap Analysis Framework

### Types of Data Gaps

**1. Missing Games**
- Games in season schedule but not in database
- Expected ~1,230 games per season, actual may vary

**2. Missing Play-by-Play Data**
- Games exist but no detailed events
- Critical for temporal queries

**3. Missing Player/Team Stats**
- Games exist but incomplete statistics
- Affects feature engineering

**4. Missing Lineups**
- Games exist but no lineup tracking
- Needed for advanced analytics

**5. Temporal Coverage Gaps**
- Missing data for specific date ranges
- Breaks time-series analysis

**6. Source-Specific Gaps**
- Data available from one source but not others
- May affect data quality/completeness

---

## Complete Workflow Steps

### Phase 1: Identify Missing Games

**Purpose:** Find games that should exist but don't

**Step 1.1: Get Expected Game Counts by Season**

```bash
echo "Expected vs Actual Games by Season"
echo ""

# Load credentials
source /Users/ryanranft/nba-sim-credentials.env

# Query database for actual counts
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Expected game counts (regular season)
-- Normal season: 1,230 games (30 teams × 82 games / 2)
-- COVID seasons: 2019-20 (971), 2020-21 (1,095)

WITH expected AS (
    SELECT season, CASE
        WHEN season = 2019 THEN 971   -- COVID shortened
        WHEN season = 2020 THEN 1095  -- COVID shortened
        ELSE 1230                     -- Normal season
    END AS expected_games
    FROM generate_series(2016, 2024) AS season
),
actual AS (
    SELECT
        season,
        COUNT(*) AS actual_games,
        COUNT(CASE WHEN completed = true THEN 1 END) AS completed_games
    FROM games
    GROUP BY season
)
SELECT
    e.season,
    e.expected_games,
    COALESCE(a.actual_games, 0) AS actual_games,
    COALESCE(a.completed_games, 0) AS completed_games,
    e.expected_games - COALESCE(a.actual_games, 0) AS missing_games,
    ROUND(100.0 * COALESCE(a.actual_games, 0) / e.expected_games, 1) AS coverage_pct
FROM expected e
LEFT JOIN actual a ON e.season = a.season
ORDER BY e.season DESC;
EOF
```

**Expected output:**
```
 season | expected_games | actual_games | completed_games | missing_games | coverage_pct
--------+----------------+--------------+-----------------+---------------+--------------
   2024 |           1230 |         1230 |            1189 |             0 |        100.0
   2023 |           1230 |         1230 |            1230 |             0 |        100.0
   2022 |           1230 |         1230 |            1230 |             0 |        100.0
   2021 |           1095 |         1095 |            1095 |             0 |        100.0
   2020 |            971 |          971 |             971 |             0 |        100.0
   2019 |           1230 |         1230 |            1230 |             0 |        100.0
   2018 |           1230 |         1230 |            1230 |             0 |        100.0
   2017 |           1230 |         1230 |            1230 |             0 |        100.0
   2016 |           1230 |         1230 |            1230 |             0 |        100.0
```

**Step 1.2: Find Specific Missing Games**

```bash
echo "Identifying specific missing games..."
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Find games that are not completed
SELECT
    game_id,
    game_date,
    season,
    home_team_id,
    away_team_id,
    CASE
        WHEN completed = false THEN 'Incomplete'
        WHEN home_score IS NULL THEN 'Missing score'
        ELSE 'Other'
    END AS issue
FROM games
WHERE completed = false
   OR home_score IS NULL
   OR away_score IS NULL
ORDER BY game_date DESC
LIMIT 20;
EOF
```

---

### Phase 2: Analyze Play-by-Play Coverage

**Purpose:** Identify games with missing play-by-play data

**Step 2.1: Check Play-by-Play Coverage**

```bash
echo "Play-by-Play Coverage Analysis"
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Games with vs without play-by-play
WITH pbp_coverage AS (
    SELECT DISTINCT game_id
    FROM play_by_play
),
games_by_season AS (
    SELECT
        season,
        COUNT(*) AS total_games,
        COUNT(CASE WHEN g.game_id IN (SELECT game_id FROM pbp_coverage) THEN 1 END) AS games_with_pbp
    FROM games g
    WHERE completed = true
    GROUP BY season
)
SELECT
    season,
    total_games,
    games_with_pbp,
    total_games - games_with_pbp AS games_missing_pbp,
    ROUND(100.0 * games_with_pbp / total_games, 1) AS pbp_coverage_pct
FROM games_by_season
ORDER BY season DESC;
EOF
```

**Step 2.2: Temporal Events Coverage**

```bash
echo "Temporal Events Coverage"
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Check if temporal_events table exists and has data
SELECT
    'temporal_events' AS table_name,
    COUNT(*) AS total_events,
    COUNT(DISTINCT game_id) AS games_covered,
    MIN(wall_clock_utc) AS earliest_event,
    MAX(wall_clock_utc) AS latest_event
FROM temporal_events;

-- Coverage by data source
SELECT
    data_source,
    COUNT(*) AS event_count,
    COUNT(DISTINCT game_id) AS game_count
FROM temporal_events
GROUP BY data_source
ORDER BY event_count DESC;
EOF
```

---

### Phase 3: Identify Data Source Gaps

**Purpose:** Compare coverage across different data sources

**Step 3.1: Source-by-Source Analysis**

```bash
echo "Data Source Coverage Comparison"
echo ""

# Check which sources have data for each season
for season in $(seq 2016 2024); do
    echo "=== Season $season ==="

    # Check S3
    echo "S3 Coverage:"
    for source in kaggle espn hoopr nba_api basketball_reference; do
        count=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive | \
            grep "$season" | wc -l)
        printf "  %-25s: %6d files\n" "$source" "$count"
    done

    # Check database (if applicable)
    echo "Database Coverage:"
    psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
        SELECT COUNT(*) FROM games WHERE season = $season;
    " | xargs printf "  %-25s: %6d games\n" "games table"

    echo ""
done
```

**Step 3.2: Critical Data Source Gaps**

```bash
echo "Critical Gaps by Data Source:"
echo ""

# Define critical data sources and their importance
cat <<EOF
Priority 1 (CRITICAL - needed for temporal queries):
  • ESPN play-by-play: Detailed event data
  • NBA API play-by-play: Alternative event source

Priority 2 (HIGH - needed for features):
  • Hoopr player tracking: Advanced metrics
  • Basketball Reference: Historical stats

Priority 3 (MEDIUM - nice to have):
  • PBPStats: Possession analysis
  • Additional sources: Cross-validation

EOF

# Check each priority 1 source
echo "Checking Priority 1 sources..."
for source in espn nba_api; do
    files=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive | wc -l)
    if [ "$files" -lt 10000 ]; then
        echo "⚠️  $source: Only $files files (may need more collection)"
    else
        echo "✅ $source: $files files (good coverage)"
    fi
done
```

---

### Phase 4: Temporal Gap Analysis

**Purpose:** Find gaps in time-series data

**Step 4.1: Date Range Continuity Check**

```bash
echo "Temporal Continuity Analysis"
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Find date gaps in games table
WITH game_dates AS (
    SELECT DISTINCT game_date::date AS date
    FROM games
    WHERE season >= 2016
    ORDER BY date
),
date_gaps AS (
    SELECT
        date,
        LEAD(date) OVER (ORDER BY date) AS next_date,
        LEAD(date) OVER (ORDER BY date) - date AS days_gap
    FROM game_dates
)
SELECT
    date AS gap_starts,
    next_date AS gap_ends,
    days_gap
FROM date_gaps
WHERE days_gap > 7  -- More than 1 week gap (unusual during season)
ORDER BY days_gap DESC
LIMIT 20;
EOF
```

**Step 4.2: Intra-Season Gaps**

```bash
echo "Finding gaps within NBA seasons..."
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- NBA regular season typically runs October to April
-- Look for unexpected gaps during this period

WITH season_games AS (
    SELECT
        season,
        game_date,
        COUNT(*) AS games_on_date
    FROM games
    WHERE EXTRACT(MONTH FROM game_date) BETWEEN 10 AND 4
       OR EXTRACT(MONTH FROM game_date) IN (10, 11, 12, 1, 2, 3, 4)
    GROUP BY season, game_date
    ORDER BY season, game_date
),
gaps AS (
    SELECT
        season,
        game_date,
        LEAD(game_date) OVER (PARTITION BY season ORDER BY game_date) AS next_game_date,
        LEAD(game_date) OVER (PARTITION BY season ORDER BY game_date) - game_date AS gap_days
    FROM season_games
)
SELECT
    season,
    game_date AS last_game_before_gap,
    next_game_date AS first_game_after_gap,
    gap_days
FROM gaps
WHERE gap_days > 5  -- More than 5 days without games
  AND season >= 2016
ORDER BY gap_days DESC
LIMIT 10;
EOF
```

---

### Phase 5: Cross-Location Data Gaps

**Purpose:** Identify data that exists in one location but not another

**Step 5.1: Local vs S3 Comparison**

```bash
echo "======================================================================"
echo "LOCAL vs S3 DATA COMPARISON"
echo "======================================================================"
echo ""

# Project data directory
PROJECT_DATA="/Users/ryanranft/nba-simulator-aws/data"

echo "Comparing local project data to S3..."
echo ""

# ESPN Play-by-Play
echo "=== ESPN Play-by-Play ==="
local_pbp_count=$(find "$PROJECT_DATA/nba_pbp" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
s3_pbp_count=$(aws s3 ls s3://nba-sim-raw-data-lake/pbp/ --recursive 2>/dev/null | wc -l | tr -d ' ')

echo "  Local (project):  $local_pbp_count files"
echo "  S3 (data lake):   $s3_pbp_count files"
gap=$((local_pbp_count - s3_pbp_count))
if [ "$gap" -gt 0 ]; then
    echo "  ⚠️  GAP: $gap files NOT uploaded to S3"
elif [ "$gap" -lt 0 ]; then
    echo "  ⚠️  GAP: $((gap * -1)) files in S3 but not local"
else
    echo "  ✅ In sync"
fi
echo ""

# ESPN Box Scores
echo "=== ESPN Box Scores ==="
local_box_count=$(find "$PROJECT_DATA/nba_box_score" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
s3_box_count=$(aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ --recursive 2>/dev/null | wc -l | tr -d ' ')

echo "  Local (project):  $local_box_count files"
echo "  S3 (data lake):   $s3_box_count files"
gap=$((local_box_count - s3_box_count))
if [ "$gap" -gt 0 ]; then
    echo "  ⚠️  GAP: $gap files NOT uploaded to S3"
elif [ "$gap" -lt 0 ]; then
    echo "  ⚠️  GAP: $((gap * -1)) files in S3 but not local"
else
    echo "  ✅ In sync"
fi
echo ""

# ESPN Team Stats
echo "=== ESPN Team Stats ==="
local_team_count=$(find "$PROJECT_DATA/nba_team_stats" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
s3_team_count=$(aws s3 ls s3://nba-sim-raw-data-lake/team_stats/ --recursive 2>/dev/null | wc -l | tr -d ' ')

echo "  Local (project):  $local_team_count files"
echo "  S3 (data lake):   $s3_team_count files"
gap=$((local_team_count - s3_team_count))
if [ "$gap" -gt 0 ]; then
    echo "  ⚠️  GAP: $gap files NOT uploaded to S3"
elif [ "$gap" -lt 0 ]; then
    echo "  ⚠️  GAP: $((gap * -1)) files in S3 but not local"
else
    echo "  ✅ In sync"
fi
echo ""

# ESPN Schedule
echo "=== ESPN Schedule ==="
local_sched_count=$(find "$PROJECT_DATA/nba_schedule_json" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
s3_sched_count=$(aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive 2>/dev/null | wc -l | tr -d ' ')

echo "  Local (project):  $local_sched_count files"
echo "  S3 (data lake):   $s3_sched_count files"
gap=$((local_sched_count - s3_sched_count))
if [ "$gap" -gt 0 ]; then
    echo "  ⚠️  GAP: $gap files NOT uploaded to S3"
elif [ "$gap" -lt 0 ]; then
    echo "  ⚠️  GAP: $((gap * -1)) files in S3 but not local"
else
    echo "  ✅ In sync"
fi
echo ""
```

**Expected output:**
```
======================================================================
LOCAL vs S3 DATA COMPARISON
======================================================================

Comparing local project data to S3...

=== ESPN Play-by-Play ===
  Local (project):  44828 files
  S3 (data lake):   44828 files
  ✅ In sync

=== ESPN Box Scores ===
  Local (project):  44830 files
  S3 (data lake):   44830 files
  ✅ In sync

=== ESPN Team Stats ===
  Local (project):  44830 files
  S3 (data lake):   44830 files
  ✅ In sync

=== ESPN Schedule ===
  Local (project):  11635 files
  S3 (data lake):   11635 files
  ✅ In sync
```

**Step 5.2: S3 vs Database Comparison**

```bash
echo "======================================================================"
echo "S3 vs DATABASE COMPARISON"
echo "======================================================================"
echo ""

# Load credentials
source /Users/ryanranft/nba-sim-credentials.env

echo "Comparing S3 data to database tables..."
echo ""

# Check which data sources are loaded
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- First, check if key tables exist
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'games') AS games_exists,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'play_by_play') AS pbp_exists,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'temporal_events') AS events_exists
FROM information_schema.tables
WHERE table_schema = 'public'
LIMIT 1;

-- If tables exist, check data source coverage
DO \$\$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'temporal_events') THEN
        RAISE NOTICE 'Data source coverage in temporal_events:';
        PERFORM data_source, COUNT(*) AS records, COUNT(DISTINCT game_id) AS games
        FROM temporal_events
        GROUP BY data_source
        ORDER BY records DESC;
    ELSE
        RAISE NOTICE 'temporal_events table does not exist yet';
    END IF;
END \$\$;
EOF

echo ""
echo "S3 data sources:"
aws s3 ls s3://nba-sim-raw-data-lake/ | awk '{print "  " $2}' | grep -v "^$"

echo ""
echo "⚠️  To load S3 data to database, see:"
echo "    - scripts/db/load_espn_events.py"
echo "    - scripts/db/load_hoopr_to_local_postgres.py"
echo "    - scripts/etl/create_possession_panel_from_espn.py"
echo ""
```

**Step 5.3: Identify Upload/Load Gaps**

```bash
echo "======================================================================"
echo "GAP IDENTIFICATION SUMMARY"
echo "======================================================================"
echo ""

# Create gap summary
cat > data_location_gaps.md <<'EOF'
# Data Location Gap Summary

**Generated:** $(date)

---

## Local → S3 Upload Gaps

### Files in Local but NOT in S3
$(# Find files that need uploading)
$(find "$PROJECT_DATA/nba_pbp" -name "*.json" | wc -l) local files vs $(aws s3 ls s3://nba-sim-raw-data-lake/pbp/ --recursive | wc -l) S3 files

**Action Required:**
- Upload missing files to S3: `aws s3 sync`
- See Workflow #40 for upload procedures

---

## S3 → Database Load Gaps

### Data in S3 but NOT in Database
- Check if temporal_events table exists
- Check if data sources are loaded
- Compare game counts

**Action Required:**
- Load S3 data to RDS: `scripts/db/load_*.py`
- Create derived tables: `scripts/etl/create_possession_panel_*.py`

---

## Database → S3 Export Gaps

### Data in Database but NOT exported to S3
- ML features generated but not saved
- Processed data not backed up

**Action Required:**
- Export ML features to S3
- Backup processed data

EOF

echo "Gap summary created: data_location_gaps.md"
```

---

### Phase 6: Generate Gap Remediation Plan

**Purpose:** Create actionable plan to fill identified gaps

**Step 5.1: Prioritize Gaps**

```bash
cat > gap_remediation_plan.md <<'EOF'
# Data Gap Remediation Plan

**Generated:** $(date)

---

## Gap Summary

### Critical Gaps (Block Analysis)
- [ ] Missing games: [COUNT] games from [SEASONS]
- [ ] Missing play-by-play: [COUNT] games
- [ ] Missing temporal events: [COUNT] games

### High Priority Gaps (Impact Features)
- [ ] Missing player stats: [COUNT] games
- [ ] Missing team stats: [COUNT] games
- [ ] Missing lineups: [COUNT] games

### Medium Priority Gaps (Nice to Have)
- [ ] Missing advanced metrics: [COUNT] games
- [ ] Missing additional sources: [SOURCES]

---

## Remediation Actions

### Phase 1: Critical Data Collection
**Estimated Time:** [HOURS] hours
**Cost:** $[AMOUNT] (API calls + compute)

1. **Collect missing game data**
   ```bash
   # Run ESPN scraper for missing games
   python scripts/etl/scrape_espn_missing.py --seasons 2024

   # Estimated: [COUNT] games × 2 min = [HOURS] hours
   ```

2. **Collect play-by-play data**
   ```bash
   # Run NBA API play-by-play scraper
   python scripts/etl/scrape_nba_api_playbyplay_only.py --games [LIST]

   # Estimated: [COUNT] games × 3 min = [HOURS] hours
   ```

### Phase 2: Load to Database
**Estimated Time:** [HOURS] hours

1. **Load new data to RDS**
   ```bash
   python scripts/db/load_espn_events.py
   python scripts/etl/create_possession_panel_from_espn.py
   ```

### Phase 3: Verify Completeness
**Estimated Time:** 30 minutes

1. **Re-run gap analysis**
   ```bash
   bash scripts/analysis/find_missing_games.sh
   ```

2. **Verify temporal coverage**
   ```bash
   bash scripts/analysis/find_temporal_gaps.sh
   ```

---

## Timeline

**Total Estimated Time:** [TOTAL] hours
**Recommended Schedule:**
- Day 1: Scrape critical missing data (Phases 1)
- Day 2: Load and process (Phase 2)
- Day 3: Verify and validate (Phase 3)

---

## Success Criteria

- [ ] All expected games present in database
- [ ] Play-by-play coverage >95% for analysis seasons
- [ ] Temporal events coverage >90%
- [ ] No gaps >7 days during regular seasons
- [ ] Re-run gap analysis shows <5% missing data

EOF

echo "Gap remediation plan template created: gap_remediation_plan.md"
```

**Step 5.2: Generate Scraper Commands**

```bash
echo "Generating scraper commands for gap filling..."
echo ""

# Query database for missing game IDs
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
    SELECT game_id
    FROM games
    WHERE completed = false
       OR game_id NOT IN (SELECT DISTINCT game_id FROM play_by_play)
    ORDER BY game_date DESC
    LIMIT 100;
" > missing_game_ids.txt

echo "Missing game IDs saved to: missing_game_ids.txt"
echo ""
echo "To scrape these games:"
echo "  python scripts/etl/scrape_espn_missing.py --game-file missing_game_ids.txt"
```

---

## Gap Analysis Report Template

### Automated Gap Report

```bash
#!/bin/bash
# Generate comprehensive gap analysis report

REPORT_FILE="DATA_GAP_ANALYSIS_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" <<EOF
# NBA Simulator - Data Gap Analysis Report

**Generated:** $(date)
**Analysis Period:** 2016-2024 seasons

---

## Executive Summary

### Overall Data Health
- **Total Expected Games:** [COUNT]
- **Total Actual Games:** [COUNT]
- **Missing Games:** [COUNT] ([PERCENT]%)
- **Play-by-Play Coverage:** [PERCENT]%
- **Temporal Coverage:** [PERCENT]%

### Status
$([ [MISSING_COUNT] -lt 50 ] && echo "✅ Good - Minor gaps only" || echo "⚠️  Attention needed - Significant gaps")

---

## Detailed Gap Analysis

### 1. Missing Games by Season

| Season | Expected | Actual | Missing | Coverage |
|--------|----------|--------|---------|----------|
$(psql -t -c "SELECT season, expected, actual, missing, coverage FROM gap_analysis ORDER BY season DESC")

### 2. Play-by-Play Coverage

| Season | Games | With PBP | Missing PBP | Coverage |
|--------|-------|----------|-------------|----------|
$(psql -t -c "SELECT season, games, pbp_games, missing, coverage FROM pbp_coverage ORDER BY season DESC")

### 3. Data Source Coverage

$(for source in espn nba_api hoopr; do
    echo "**$source:**"
    aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive --summarize | grep "Total"
    echo ""
done)

### 4. Temporal Gaps

**Identified Gaps >7 days:**
$(psql -t -c "SELECT gap_start, gap_end, days FROM temporal_gaps WHERE days > 7 ORDER BY days DESC LIMIT 10")

---

## Recommended Actions

$(if [ [CRITICAL_GAPS] -gt 0 ]; then
    echo "### CRITICAL - Immediate Action Required"
    echo "1. Run missing data scrapers for [COUNT] games"
    echo "2. Load collected data to database"
    echo "3. Re-verify coverage"
else
    echo "### Standard Maintenance"
    echo "1. Monitor ongoing data collection"
    echo "2. Fill minor gaps during regular scraper runs"
fi)

---

## Appendix

### Missing Game IDs
[LIST OF GAME IDS]

### Scraper Commands
[GENERATED COMMANDS]

EOF

echo "Gap analysis report generated: $REPORT_FILE"
```

---

## Common Gap Scenarios

### Scenario 1: Missing Recent Games

**Symptoms:**
- Latest season has <100% coverage
- Recent dates have no games

**Cause:** Ongoing season, games not yet scraped

**Solution:**
```bash
# Scrape most recent games
python scripts/etl/scrape_espn_missing.py --season 2024 --recent-only

# Or run full season update
python scripts/etl/scrape_nba_api_comprehensive.py --season 2024
```

### Scenario 2: Historical Data Gaps

**Symptoms:**
- Older seasons missing significant data
- Play-by-play coverage <50% for certain seasons

**Cause:** Data sources may not have historical data

**Solution:**
```bash
# Try multiple sources for historical data
python scripts/etl/scrape_basketball_reference_complete.py --seasons 2016-2020
python scripts/etl/scrape_nba_api_comprehensive.py --seasons 2016-2020
```

### Scenario 3: Source-Specific Gaps

**Symptoms:**
- One source has data, another doesn't
- Inconsistent coverage across sources

**Cause:** Different data availability by source

**Solution:**
```bash
# Cross-reference and fill from available source
# Use ESPN as backup for NBA API gaps
python scripts/etl/fill_gaps_from_espn.py --target nba_api
```

---

## Best Practices

### Gap Analysis Frequency

**Daily (if actively collecting):**
- Quick check for new gaps
- Verify recent scraper runs completed

**Weekly:**
- Full gap analysis
- Update remediation plan

**Before Major Analysis:**
- Comprehensive gap check
- Ensure required data available

### Documentation

**Always document:**
- When gaps were identified
- What caused the gaps
- Actions taken to remediate
- Verification that gaps were filled

### Prioritization Matrix

| Gap Type | Impact | Urgency | Priority |
|----------|--------|---------|----------|
| Missing games (current season) | High | High | 1 - Critical |
| Missing play-by-play (any season) | High | Medium | 2 - High |
| Missing advanced stats | Medium | Low | 3 - Medium |
| Missing historical data (>5 years old) | Low | Low | 4 - Low |

---

## Success Criteria

✅ Can identify all missing games
✅ Can quantify play-by-play coverage
✅ Can detect temporal gaps
✅ Can compare across data sources
✅ Generates actionable remediation plan
✅ Provides specific scraper commands
✅ Tracks gap resolution progress

---

## Related Workflows

- **Workflow #45:** Local Data Inventory - Identify what data you have
- **Workflow #40:** Scraper Operations - Collect missing data
- **Workflow #42:** Scraper Management - Manage data collection jobs

---

**Last Updated:** October 8, 2025
**Next Review:** Monthly (or after major data collection)