# ⚠️ THIS FILE HAS MOVED

**Date:** October 4, 2025
**Reason:** Phase reorganization (ADR-008)

---

> **🔴 THIS CONTENT HAS BEEN REORGANIZED:**
>
> This file (Phase 0: Data Source Definition & Verification) has been **split and reorganized** as of October 4, 2025.
>
> **The new phase structure is:**
> - **Phase 0:** [Data Collection & Initial Upload](PHASE_0_DATA_COLLECTION.md) ← Start here for new sports
> - **Phase 1:** [Data Quality & Gap Analysis](PHASE_1_DATA_QUALITY.md) ← This is where most of the old Phase 0 content went
>
> **Why the change?**
> - Logical data flow: Collect → Analyze → Extract → Store
> - Eliminates duplicate upload instructions
> - Clear separation of concerns
> - See `docs/adr/008-phase-reorganization.md` for full rationale
>
> **⚠️ DO NOT USE THIS FILE - IT IS DEPRECATED**
>
> **For new sessions:**
> 1. Read [Phase 0: Data Collection](PHASE_0_DATA_COLLECTION.md) first
> 2. Then read [Phase 1: Data Quality](PHASE_1_DATA_QUALITY.md)
>
> **Backup of old content:** `PHASE_0_DATA_SOURCES.md.backup`

---

# OLD CONTENT BELOW (DEPRECATED)

---

# Phase 0: Data Source Definition & Verification

**Status:** ❌ DEPRECATED (see new Phase 0 and Phase 1 above)
**Prerequisites:** None (this is the foundation)
**Estimated Time:** 4-8 hours (per sport)
**Estimated Cost:** $0-10/month (depending on API choices)

---

## Overview

Phase 0 defines the data foundation for your entire sports simulator platform. This phase is **sport-agnostic** and designed for **easy replication** across NBA, NFL, MLB, NHL, Soccer, etc.

**What this phase establishes:**
- Primary data source(s) identification
- Verification/validation source(s) selection
- Data quality baseline metrics
- Cross-source mapping strategy
- Multi-sport replication template

**Why Phase 0 matters:**
- Bad data = bad predictions (garbage in, garbage out)
- Multiple sources catch errors and fill gaps
- Standardized process = faster sport replication
- Quality metrics enable continuous improvement

---

## Sport-Specific Implementation Registry

**Current implementations:**

### NBA (Basketball)
**Status:** ✅ PRIMARY SOURCES DEFINED, ⏸️ VERIFICATION PENDING
**Primary Sources:**
- ESPN JSON files (146,115 files, 119GB, S3)
  - Coverage: 1999-2025
  - Data quality: 83% valid files
  - Missing: 17% empty files (~24,507)
  - Fields extracted: 53 (games), play-by-play, player stats, team stats

**Verification Sources:** (User must specify - see options below)
- [ ] NBA.com Stats API
- [ ] Basketball Reference
- [ ] SportsData.io
- [ ] balldontlie API
- [ ] Other: ________________

**Critical Fields to Verify:**
- [ ] Game scores (home_score, away_score)
- [ ] Game dates/times
- [ ] Team IDs/names
- [ ] Player stats
- [ ] Other: ________________

**Started:** September 29, 2025
**Primary ETL Complete:** October 2, 2025
**Verification Status:** Pending user input

---

### NFL (American Football)
**Status:** ⏸️ NOT STARTED
**Primary Sources:** (To be defined by user)
**Verification Sources:** (To be defined by user)

---

### MLB (Baseball)
**Status:** ⏸️ NOT STARTED
**Primary Sources:** (To be defined by user)
**Verification Sources:** (To be defined by user)

---

### NHL (Hockey)
**Status:** ⏸️ NOT STARTED
**Primary Sources:** (To be defined by user)
**Verification Sources:** (To be defined by user)

---

### Soccer (Football)
**Status:** ⏸️ NOT STARTED
**Primary Sources:** (To be defined by user)
**Verification Sources:** (To be defined by user)

---

## Data Source Selection Framework

### Step 1: Define Primary Source(s)

**Primary source = where you get most/all of your data**

**Questions to answer:**
1. What format is the data? (JSON files, API, CSV, database, HTML scraping)
2. How much data? (file count, GB, date range)
3. What's the quality? (completeness %, known gaps)
4. What fields are included? (list of all available fields)
5. What's missing? (fields you need but don't have)

**Example (NBA - ESPN):**
```yaml
sport: NBA
primary_source: ESPN JSON Files
format: JSON (nested)
location: S3 bucket (s3://nba-sim-raw-data-lake/)
volume: 146,115 files, 119GB
coverage: 1999-2025
quality: 83% valid files
fields_extracted: 53 (see docs/DATA_STRUCTURE_GUIDE.md)
missing_data:
  - Betting odds (only provider metadata, no actual lines)
  - 17% empty files (coverage gaps)
  - Some player stats incomplete
```

---

### Step 2: Choose Verification Source(s)

**Verification source = authoritative source to validate/clean primary data**

**Common verification source types:**

#### Type A: Official League APIs (Highest Authority)
- **Examples:** NBA.com Stats, NFL.com, MLB.com
- **Pros:** Official data, authoritative
- **Cons:** Rate limits, reverse-engineering required, no guarantees

#### Type B: Sports Reference Sites (Most Comprehensive)
- **Examples:** Basketball Reference, Pro Football Reference, Baseball Reference
- **Pros:** Historical depth, well-structured, free
- **Cons:** HTML scraping, terms of service restrictions

#### Type C: Commercial APIs (Easiest Integration)
- **Examples:** SportsData.io, The Odds API, Sportradar
- **Pros:** Official APIs, documentation, reliability
- **Cons:** Cost, usage limits

#### Type D: Community APIs (Free, Simple)
- **Examples:** balldontlie (NBA), TheSportsDB (multi-sport)
- **Pros:** Free, unlimited, simple REST
- **Cons:** Data quality varies, community-maintained

**Recommendation:** Use at least 2 sources (primary + 1 verification)

---

### Step 3: Map Data Sources to Use Cases

**Define what each source is used for:**

| Use Case | Primary Source | Verification Source | Why |
|----------|---------------|-------------------|-----|
| **Game scores** | ESPN JSON | NBA.com Stats | Official scores as ground truth |
| **Player stats** | ESPN JSON | Basketball Reference | Most complete historical stats |
| **Betting odds** | The Odds API | None (new data) | ESPN doesn't have real odds |
| **Schedules** | ESPN JSON | NBA.com Stats | Validate dates/times |
| **Team info** | ESPN JSON | NBA.com Stats | Standardize team IDs |

**For Claude:** When implementing a new sport, create this mapping table FIRST.

---

## Data Quality Metrics (Sport-Agnostic)

**Every sport implementation should track:**

### 1. Completeness
```python
completeness = (records_with_data / total_expected_records) * 100

# Example (NBA):
# Expected: ~82 games/team/season * 30 teams = ~2,460 games/season
# Actual: Check S3 files vs expected
```

### 2. Accuracy
```python
accuracy = (matching_records / verified_records) * 100

# Example (NBA):
# Verified 1,000 random games against NBA.com
# 987 scores matched exactly
# Accuracy = 98.7%
```

### 3. Freshness
```python
freshness = days_since_last_update

# Example (NBA):
# Last game added: 2025-04-10
# Today: 2025-10-04
# Freshness: 177 days (offseason, acceptable)
```

### 4. Consistency
```python
consistency = (records_without_conflicts / total_records) * 100

# Example (NBA):
# Team name variations: "LA Lakers" vs "Los Angeles Lakers"
# Player name variations: "LeBron James" vs "Lebron James"
# Consistency check: canonical names exist for all
```

---

## Multi-Sport Replication Template

**When adding a new sport, follow this checklist:**

### Pre-Phase 0 (User Input Required)

**Claude must ask:**
- [ ] Sport name: ________________
- [ ] Primary data source: ________________
- [ ] Data format: (JSON/CSV/API/HTML/Database/Other)
- [ ] Data location: (S3/local/API endpoint/URL)
- [ ] Data volume estimate: (files, GB, date range)
- [ ] Known data quality issues: ________________
- [ ] Verification source preference: ________________
- [ ] Critical fields needed: ________________
- [ ] Auto-fix tolerance: (auto-fix all / review critical / manual all)

### Phase 0.1: Primary Source Analysis

- [ ] Access primary data source
- [ ] Document data structure (create DATA_STRUCTURE_GUIDE.md)
- [ ] Calculate completeness metrics
- [ ] Identify coverage gaps
- [ ] List all available fields
- [ ] Document known issues

**Output:** `docs/sports/{sport}/DATA_STRUCTURE_GUIDE.md`

### Phase 0.2: Verification Source Setup

- [ ] Select verification source(s)
- [ ] Test API access / scraping capability
- [ ] Document rate limits / costs
- [ ] Create API key management (if needed)
- [ ] Test sample data fetch

**Output:** API credentials in `~/{sport}-sim-credentials.env`

### Phase 0.3: Cross-Source Mapping

- [ ] Map team names (primary → verification)
- [ ] Map player names (if applicable)
- [ ] Map field names (different sources use different terminology)
- [ ] Create canonical ID system

**Output:** `scripts/etl/{sport}/mapping_tables.py`

### Phase 0.4: Database Schema (Verification)

- [ ] Create verification_runs table
- [ ] Create game_discrepancies table (or {sport}_discrepancies)
- [ ] Create data_quality_metrics table
- [ ] Add verification status columns to main tables

**Output:** `sql/{sport}/create_verification_tables.sql`

### Phase 0.5: ETL Scripts

- [ ] Create verification fetch script (`scripts/etl/verify_{sport}_games.py`)
- [ ] Implement comparison logic
- [ ] Build discrepancy detection
- [ ] Add automated fix rules
- [ ] Create reporting tools

**Output:** 3-5 Python scripts in `scripts/etl/` and `scripts/analysis/`

### Phase 0.6: Quality Baseline

- [ ] Run initial verification
- [ ] Document baseline metrics (completeness, accuracy, consistency)
- [ ] Identify top 10 issues
- [ ] Create fix priority list

**Output:** `docs/sports/{sport}/QUALITY_BASELINE.md`

### Phase 0.7: ESPN Data Analysis & Gap Filling (NBA-Specific)

**When to run:**
- Initial setup: "analyze existing ESPN data and upload to S3"
- Ongoing maintenance: "scrape ESPN for missing data to [DATE]"

**Purpose:**
1. Upload existing ESPN JSON files to S3 for baseline analysis
2. Use existing ESPN scraping code to fill coverage gaps

**Prerequisites:**
- [ ] ESPN scraping code exists (`/Users/ryanranft/0espn/`)
- [ ] S3 bucket accessible
- [ ] RDS database running (for verification)

---

#### Step 0: Upload Existing ESPN Data to S3 (First-Time Setup)

**When to run:** Before using Workflow #38, to establish baseline

**Purpose:** Upload existing local ESPN JSON files to S3 so Claude can:
- Analyze what data already exists
- Determine date coverage gaps
- Identify empty/invalid files
- Plan gap-filling strategy

**Local ESPN data location:**
```bash
/Users/ryanranft/0espn/data/nba/
```

**Instructions for Claude:**

When user says **"upload existing ESPN data to S3"** or **"analyze ESPN data"**:

1. **Check local ESPN data directory**

```bash
# Navigate to ESPN data directory
cd /Users/ryanranft/0espn/data/nba/

# Count total files
find . -name "*.json" | wc -l

# Check file size
du -sh .

# Show date range (first and last files)
ls -1 *.json 2>/dev/null | head -1
ls -1 *.json 2>/dev/null | tail -1

# Sample file structure
ls -lh | head -20
```

2. **Analyze data coverage before upload**

```bash
# Get date distribution
ls -1 *.json 2>/dev/null | grep -oE '[0-9]{8}' | sort | uniq | head -20
ls -1 *.json 2>/dev/null | grep -oE '[0-9]{8}' | sort | uniq | tail -20

# Count files by year
for year in {1993..2025}; do
  count=$(ls -1 *${year}*.json 2>/dev/null | wc -l | xargs)
  if [ $count -gt 0 ]; then
    echo "$year: $count files"
  fi
done

# Check for empty files
find . -name "*.json" -size 0 | wc -l
```

3. **Upload to S3 (initial sync)**

```bash
# Upload all JSON files to S3
aws s3 sync /Users/ryanranft/0espn/data/nba/ \
  s3://nba-sim-raw-data-lake/schedule/ \
  --exclude "*" \
  --include "*.json" \
  --size-only

# Note: --size-only prevents re-uploading identical files
```

4. **Verify S3 upload**

```bash
# Count files in S3
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | wc -l

# Check S3 storage size
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive --summarize | grep "Total Size"

# Find first and last dates
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | head -1
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | tail -1
```

5. **Analyze gaps in S3 data**

```bash
# List all dates with files (extract YYYYMMDD from filenames)
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | \
  grep "\.json$" | \
  grep -oE '[0-9]{8}' | \
  sort | uniq > /tmp/s3_dates.txt

# Show total unique dates
wc -l /tmp/s3_dates.txt

# Check for gaps (compare consecutive dates)
# Claude: Write Python script to detect date gaps > 7 days
```

6. **Report to user**

After upload, report:
- Total files uploaded
- Date range covered (earliest to latest)
- Gaps detected (dates with no data)
- Empty files found (if any)
- Recommended next steps

**Example output:**
```
✓ Uploaded ESPN data to S3

Summary:
- Total files: 146,115
- Size: 119GB
- Date range: 1993-08-25 to 2025-06-30
- Unique dates: 11,765
- Empty files: 24,507 (17%)

Gaps detected:
- 2020-03-11 to 2020-07-30 (COVID shutdown)
- 2025-07-01 to 2025-10-04 (96 days missing)

Next steps:
1. Run Workflow #38 to fill 2025-07-01 to today
2. Verify empty files (may be off-season dates)
3. Extract to RDS database
```

---

#### Step 1: Automated Gap Filling (Recommended)

**Follow Workflow #38:** [Auto-Update ESPN Data](../claude_workflows/workflow_descriptions/38_auto_update_espn_data.md)

**Quick run:**
```bash
bash scripts/etl/auto_update_espn_data.sh
```

This automated workflow:
1. ✓ Checks today's date
2. ✓ Finds last date with data in S3
3. ✓ Calculates gap (days missing)
4. ✓ Updates ESPN scraper end_date automatically
5. ✓ Runs ESPN scraper for missing dates
6. ✓ Uploads new files to S3
7. ✓ Extracts to RDS database
8. ✓ Verifies results

**Use this workflow when:**
- Returning from trips or extended absences
- Running daily/weekly maintenance
- Before simulations or ML training
- As part of automated cron jobs

---

#### Manual Workflow (Fallback)

**If automated script fails, follow these steps:**

1. **Identify missing dates**

```bash
# Check current S3 coverage
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | tail -1

# Current coverage ends: 2025-06-30 (from Phase 0 analysis)
# User specifies new end date: [USER_DATE]
```

2. **Update ESPN scraper date range**

```bash
# Edit /Users/ryanranft/0espn/espn/nba/nba_schedule.py
# Line 142: end_date = datetime.date(2025, 6, 30)
# Change to: end_date = datetime.date([YEAR], [MONTH], [DAY])
```

3. **Run ESPN scraper for missing dates only**

```bash
cd /Users/ryanranft/0espn

# Activate ESPN environment
conda activate espn  # Or whatever env name

# Run schedule scraper
python espn/nba/nba_schedule.py

# Output: JSON files cached to /Users/ryanranft/0espn/data/nba/
```

4. **Upload new files to S3**

```bash
# Upload newly scraped files to S3
aws s3 sync /Users/ryanranft/0espn/data/nba/ s3://nba-sim-raw-data-lake/schedule/ \
  --exclude "*" \
  --include "*.json" \
  --size-only

# Verify upload
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | wc -l
```

5. **Run ETL extraction for new data**

```bash
cd /Users/ryanranft/nba-simulator-aws
source ~/nba-sim-credentials.env

# Extract new games only (specify date range)
python scripts/etl/extract_schedule_local.py --year-range [START_YEAR]-[END_YEAR]
```

6. **Verify data completeness**

```bash
# Check database for new games
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << 'EOF'
SELECT
    MIN(game_date) as earliest_game,
    MAX(game_date) as latest_game,
    COUNT(*) as total_games
FROM games;
EOF
```

**Validation:**
- [ ] New files uploaded to S3
- [ ] ETL extracted new games to RDS
- [ ] Coverage gap filled (database has games through target date)
- [ ] Data quality maintained (no errors in new games)

**Example: Fill gap from 2025-06-30 to 2025-10-04**

```bash
# 1. Check current coverage
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ | grep "202510" | wc -l
# Output: 0 (no October 2025 files)

# 2. Update scraper
# Edit: /Users/ryanranft/0espn/espn/nba/nba_schedule.py
# Change line 142: end_date = datetime.date(2025, 10, 4)

# 3. Run scraper (will skip cached dates, only fetch new)
cd /Users/ryanranft/0espn
python espn/nba/nba_schedule.py

# 4. Upload to S3
aws s3 sync /Users/ryanranft/0espn/data/nba/ s3://nba-sim-raw-data-lake/schedule/ \
  --exclude "*" --include "*.json" --size-only

# 5. Extract to database
cd /Users/ryanranft/nba-simulator-aws
python scripts/etl/extract_schedule_local.py --year-range 2025-2025

# 6. Verify
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c \
  "SELECT COUNT(*) FROM games WHERE game_date >= '2025-07-01' AND game_date <= '2025-10-04';"
```

**Claude Instructions:**

When user says **"scrape ESPN for missing data to [DATE]"**:

1. **Ask user:** "What end date should I scrape to? (YYYY-MM-DD format)"
2. **Calculate gap:** Current coverage (2025-06-30) to user's target date
3. **Estimate time:** ~0.25 seconds per day * number of days
4. **Warn about rate limits:** ESPN has no hard limits, but recommend politeness (0.25s delay is safe)
5. **Execute steps 1-6 above**
6. **Report:** "Scraped [X] new days, uploaded [Y] files, extracted [Z] games"

**Output:** Updated S3 bucket with filled coverage gaps

---

## Database Schema (Sport-Agnostic)

**These tables work for ANY sport:**

### verification_runs
```sql
CREATE TABLE IF NOT EXISTS verification_runs (
    run_id SERIAL PRIMARY KEY,
    sport VARCHAR(20) NOT NULL,          -- 'NBA', 'NFL', 'MLB', etc.
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) NOT NULL,    -- 'nba_stats', 'nfl_api', etc.
    records_checked INTEGER DEFAULT 0,
    discrepancies_found INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',
    notes TEXT
);
```

### {sport}_discrepancies
```sql
-- Example: game_discrepancies (NBA), match_discrepancies (Soccer)
CREATE TABLE IF NOT EXISTS game_discrepancies (
    discrepancy_id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES verification_runs(run_id),
    record_id VARCHAR(50) NOT NULL,      -- game_id, match_id, etc.
    record_type VARCHAR(20),             -- 'game', 'player_stat', 'team', etc.

    field_name VARCHAR(50) NOT NULL,
    primary_value TEXT,                  -- Value from primary source
    verification_value TEXT,             -- Value from verification source

    discrepancy_type VARCHAR(30),        -- 'mismatch', 'missing_primary', 'missing_verification'
    severity VARCHAR(10),                -- 'low', 'medium', 'high', 'critical'

    resolved BOOLEAN DEFAULT FALSE,
    resolution_action VARCHAR(100),
    resolved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### data_quality_metrics
```sql
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    sport VARCHAR(20) NOT NULL,
    run_id INTEGER REFERENCES verification_runs(run_id),

    metric_name VARCHAR(50) NOT NULL,    -- 'completeness', 'accuracy', 'consistency'
    metric_value DECIMAL(5,2),           -- 0.00 to 100.00
    metric_details JSONB,                -- Flexible JSON for sport-specific details

    total_records INTEGER,
    valid_records INTEGER,
    invalid_records INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Data Source Options Reference

### Basketball (NBA)

| Source | Type | Cost | Coverage | Quality | Notes |
|--------|------|------|----------|---------|-------|
| **ESPN** | JSON/API | Free | 1999-present | ⭐⭐⭐⭐ | Primary (your current source) |
| **NBA.com Stats** | API | Free | 1996-present | ⭐⭐⭐⭐⭐ | Official, rate-limited |
| **Basketball Reference** | HTML | Free | 1946-present | ⭐⭐⭐⭐⭐ | Most comprehensive |
| **SportsData.io** | API | $19/mo | 1999-present | ⭐⭐⭐⭐ | Clean API |
| **balldontlie** | API | Free | 1979-present | ⭐⭐⭐ | Community |

### Football (NFL)

| Source | Type | Cost | Coverage | Quality | Notes |
|--------|------|------|----------|---------|-------|
| **ESPN** | JSON/API | Free | 2000-present | ⭐⭐⭐⭐ | Similar to NBA |
| **NFL.com** | API | Free | 2009-present | ⭐⭐⭐⭐⭐ | Official |
| **Pro Football Reference** | HTML | Free | 1920-present | ⭐⭐⭐⭐⭐ | Comprehensive |
| **SportsData.io** | API | $29/mo | 2000-present | ⭐⭐⭐⭐ | |

### Baseball (MLB)

| Source | Type | Cost | Coverage | Quality | Notes |
|--------|------|------|----------|---------|-------|
| **ESPN** | JSON/API | Free | 2000-present | ⭐⭐⭐⭐ | |
| **MLB Stats API** | API | Free | 2008-present | ⭐⭐⭐⭐⭐ | Official |
| **Baseball Reference** | HTML | Free | 1871-present | ⭐⭐⭐⭐⭐ | Historical gold mine |
| **SportsData.io** | API | $19/mo | 2000-present | ⭐⭐⭐⭐ | |

### Hockey (NHL)

| Source | Type | Cost | Coverage | Quality | Notes |
|--------|------|------|----------|---------|-------|
| **ESPN** | JSON/API | Free | 2000-present | ⭐⭐⭐⭐ | |
| **NHL.com API** | API | Free | 2010-present | ⭐⭐⭐⭐⭐ | Official |
| **Hockey Reference** | HTML | Free | 1917-present | ⭐⭐⭐⭐⭐ | |
| **SportsData.io** | API | $29/mo | 2000-present | ⭐⭐⭐⭐ | |

### Soccer (Multiple Leagues)

| Source | Type | Cost | Coverage | Quality | Notes |
|--------|------|------|----------|---------|-------|
| **ESPN** | JSON/API | Free | 2010-present | ⭐⭐⭐⭐ | Multiple leagues |
| **API-Football** | API | $0-30/mo | 2010-present | ⭐⭐⭐⭐⭐ | 900+ leagues |
| **TheSportsDB** | API | Free | 2000-present | ⭐⭐⭐ | Community |
| **FBref** | HTML | Free | 2010-present | ⭐⭐⭐⭐ | Advanced stats |

---

## Instructions for Claude: New Sport Implementation

**When a user says "I want to add [SPORT]", follow this protocol:**

### Step 1: Initial Questions (MUST ASK FIRST)
```
Claude: "Great! Let's set up the data foundation for [SPORT]. I need to ask some questions first:

1. Do you already have a primary data source for [SPORT]?
   (ESPN files, API dumps, database, scraped data, etc.)

2. If yes:
   - What format is it? (JSON, CSV, database, etc.)
   - Where is it stored? (S3, local, API endpoint)
   - How much data? (approx. GB, date range, # of records)

3. What verification/validation source would you prefer?
   Options:
   - Official league API ([SPORT].com)
   - Sports Reference sites (if available)
   - Commercial API (SportsData.io, etc.)
   - Community API
   - Multiple sources

4. What fields are most critical for your use case?
   - Game scores (always)
   - Player stats
   - Team stats
   - Betting odds
   - Advanced metrics
   - Other: ___________

5. Do you want automated fixes or manual review for discrepancies?
   - Auto-fix everything (fast, risky)
   - Auto-fix low severity, review high/critical (recommended)
   - Manual review all (slow, safe)

Once you answer these, I'll create the Phase 0 implementation plan for [SPORT]."
```

### Step 2: Document in Phase 0

After user answers, update this file:
1. Add sport to "Sport-Specific Implementation Registry"
2. Fill in primary sources, verification sources, critical fields
3. Set status to "🔄 IN PROGRESS"

### Step 3: Create Sport-Specific Docs

Create these files:
- `docs/sports/{sport}/DATA_STRUCTURE_GUIDE.md`
- `docs/sports/{sport}/MAPPING_TABLES.md`
- `docs/sports/{sport}/QUALITY_BASELINE.md`

### Step 4: Proceed to Sub-Phases 0.1-0.6

Follow the "Multi-Sport Replication Template" checklist above.

### Step 5: Only Then Move to Phase 1

**Do NOT start Phase 1 (S3 Data Lake) until Phase 0 is complete.**

---

## Current Status: NBA Implementation

**User must complete this section before proceeding:**

### Primary Source: ✅ DEFINED - ESPN XHR API
- **Method:** Direct HTTP requests to ESPN XHR endpoints
- **Scraping Code Location:** `/Users/ryanranft/0espn/`
- **Current Data:** 146,115 files (119GB) in S3
- **Coverage:** 1993-08-25 to 2025-06-30
- **Data Quality:** 83% valid files, 17% empty (24,507 files)
- **ETL Status:** Complete (Phase 2), Database loaded (Phase 3)

**ESPN Endpoints Used:**
- Schedule: `https://www.espn.com/nba/schedule/_/date/{YYYYMMDD}&_xhr=1`
- Box Score: (from `/Users/ryanranft/0espn/espn/nba/nba_box_score.py`)
- Play-by-Play: (from `/Users/ryanranft/0espn/espn/nba/nba_pbp.py`)

**Available Multi-Sport Modules:**
Your existing scraping system at `/Users/ryanranft/0espn/espn/` has modules for:
- ✅ NBA (active)
- ⏸️ NFL (code exists, not activated)
- ⏸️ NHL (code exists, not activated)
- ⏸️ NCAAM (code exists, not activated)
- ⏸️ NCAAW (code exists, not activated)
- ⏸️ CFB (code exists, not activated)
- ⏸️ WNBA (code exists, not activated)

### Verification Source: ⏸️ PENDING USER INPUT

**Claude: Ask user to choose:**
1. NBA.com Stats API (free, official)
2. Basketball Reference (free, comprehensive)
3. SportsData.io (paid, $19/month)
4. balldontlie (free, community)
5. Multiple sources (best quality, more work)

**User choice:** ________________

### Critical Fields: ⏸️ PENDING USER INPUT

**Claude: Ask user to rank priority (1-5):**
- [ ] Game scores (home_score, away_score)
- [ ] Game dates/times
- [ ] Team IDs/names
- [ ] Player stats
- [ ] Venue information
- [ ] Other: ________________

### Auto-Fix Rules: ⏸️ PENDING USER INPUT

**Claude: Ask user preference:**
- [ ] Auto-fix all discrepancies (fastest)
- [ ] Auto-fix low/medium, review high/critical (recommended)
- [ ] Manual review all (safest)

---

## Success Criteria (Per Sport)

- [ ] Primary data source documented and accessible
- [ ] Verification source(s) selected and tested
- [ ] Cross-source mapping complete (teams, players, fields)
- [ ] Verification database schema created
- [ ] ETL scripts written and tested
- [ ] Initial verification run complete
- [ ] Quality baseline metrics documented
- [ ] Top 10 issues identified and prioritized

**Target metrics (per sport):**
- [ ] Completeness > 95%
- [ ] Accuracy > 99%
- [ ] Consistency > 98%
- [ ] Critical discrepancies = 0

---

## Cost Analysis (Multi-Sport)

**Per sport costs (monthly):**

| Sport | Free Option | Paid Option | Recommended |
|-------|-------------|-------------|-------------|
| **NBA** | $0 (NBA.com/balldontlie) | $19 (SportsData.io) | Free (start), paid (scale) |
| **NFL** | $0 (NFL.com) | $29 (SportsData.io) | Free |
| **MLB** | $0 (MLB API) | $19 (SportsData.io) | Free |
| **NHL** | $0 (NHL API) | $29 (SportsData.io) | Free |
| **Soccer** | $0 (TheSportsDB) | $30 (API-Football) | Depends on leagues |

**AWS costs (incremental per sport):**
- RDS storage: +$0.50-2/month per sport (more data)
- S3 storage: +$1-5/month per sport (more files)
- Lambda executions: +$0.20/month per sport

**Total per sport: $0-10/month (free sources), $20-50/month (paid sources)**

---

## Next Steps

**For NBA (current):**
1. User: Answer verification source questions above
2. Claude: Implement Sub-Phases 0.1-0.6 based on user choices
3. User: Review quality baseline report
4. Claude: Fix top 10 issues
5. Move to Phase 1 (already complete, but may need data refresh)

**For next sport:**
1. User: "I want to add [SPORT]"
2. Claude: Ask Step 1 questions (see "Instructions for Claude" above)
3. Follow multi-sport replication template
4. Complete Phase 0 before starting Phase 1

---

## Related Documentation

- **Multi-Sport Reproduction:** See workflow #33
- **Data Structure Guide:** `docs/DATA_STRUCTURE_GUIDE.md` (NBA-specific, template for others)
- **ETL Scripts:** `scripts/etl/` (NBA scripts can be templated for other sports)

---

*Last updated: 2025-10-03*
*Phase Type: Foundation (must complete before Phase 1)*
*Multi-Sport Ready: Yes*
*Status: NBA verification pending user input*