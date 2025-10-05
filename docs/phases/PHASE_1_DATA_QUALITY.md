# Phase 1: Data Quality & Gap Analysis

**Status:** ⏸️ PENDING (verification sources not yet defined)
**Prerequisites:** Phase 0 complete (data in S3)
**Estimated Time:** 4-8 hours (per sport)
**Estimated Cost:** $0-10/month (depending on API choices)

---

> **📌 NOTE - Phase Reorganization:**
>
> This is the NEW Phase 1 as of October 4, 2025 (ADR-008).
> Previously, this content was in Phase 0 (Data Source Definition & Verification).
>
> **Old structure:** Phase 0 = Data Verification → Phase 1 = S3 Upload
> **New structure:** Phase 0 = Data Collection → Phase 1 = Quality Analysis
>
> See `docs/adr/008-phase-reorganization.md` for rationale.

---

## Overview

Analyze S3 data quality, identify coverage gaps, and establish baseline metrics. This phase ensures data completeness and accuracy before extraction (Phase 2) and database loading (Phase 3).

**This phase establishes:**
- Data quality baseline metrics (completeness, accuracy, freshness)
- Coverage gap identification (missing dates, empty files)
- Verification source selection and setup
- Automated gap-filling workflows

**Why Phase 1 matters:**
- Bad data = bad predictions (garbage in, garbage out)
- Multiple sources catch errors and fill gaps
- Quality metrics enable continuous improvement
- Standardized process for multi-sport replication

---

## Prerequisites

Before starting this phase:
- [x] Phase 0 complete (data uploaded to S3)
- [x] S3 bucket accessible
- [ ] Data structure documented (`docs/DATA_STRUCTURE_GUIDE.md`)
- [ ] User has chosen verification sources (see options below)

---

## Implementation Steps

###Sub-Phase 1.1: Analyze S3 Data Coverage

**Status:** ⏸️ PENDING
**Time Estimate:** 1 hour

**Purpose:** Understand what data exists in S3, identify quality issues

**Follow these workflows:**
- Workflow #21 ([Data Validation](../claude_workflows/workflow_descriptions/21_data_validation.md))
  - **When to run:** First step after Phase 0 completes
  - **Purpose:** Sample S3 files, check for valid JSON, identify empty files

**Tasks:**

1. **Count total files in S3:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | grep "\.json$" | wc -l
```

2. **Check S3 storage size:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | grep "Total Size"
```

3. **Find date range:**
```bash
# First file (earliest date)
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | head -1

# Last file (latest date)
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | tail -1
```

4. **Sample files for quality:**
```bash
# Download 100 random files
for i in {1..100}; do
  FILE=$(aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | shuf -n 1 | awk '{print $4}')
  aws s3 cp "s3://nba-sim-raw-data-lake/$FILE" "/tmp/sample_$i.json"

  # Check if valid JSON and non-empty
  if python -m json.tool "/tmp/sample_$i.json" > /dev/null 2>&1; then
    SIZE=$(stat -f%z "/tmp/sample_$i.json")
    if [ $SIZE -gt 100 ]; then
      echo "Valid: $FILE ($SIZE bytes)"
    else
      echo "Empty: $FILE"
    fi
  else
    echo "Invalid JSON: $FILE"
  fi
done
```

**Output:** `docs/DATA_QUALITY_BASELINE.md` with:
- Total files count
- Date range coverage
- % valid vs empty files
- Average file size
- Known issues

---

### Sub-Phase 1.2: Identify Coverage Gaps

**Status:** ⏸️ PENDING
**Time Estimate:** 1 hour

**Purpose:** Find missing dates and data holes

**Tasks:**

1. **Extract all dates from S3 filenames:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | \
  grep "\.json$" | \
  grep -oE '[0-9]{8}' | \
  sort | uniq > /tmp/s3_dates.txt

echo "Total unique dates: $(wc -l < /tmp/s3_dates.txt)"
```

2. **Detect gaps > 7 days:**
```python
# scripts/analysis/detect_date_gaps.py
from datetime import datetime, timedelta

with open('/tmp/s3_dates.txt') as f:
    dates = [datetime.strptime(line.strip(), '%Y%m%d') for line in f]

dates.sort()
gaps = []

for i in range(len(dates) - 1):
    diff = (dates[i+1] - dates[i]).days
    if diff > 7:
        gaps.append({
            'start': dates[i],
            'end': dates[i+1],
            'days_missing': diff
        })

print(f"Found {len(gaps)} gaps:")
for gap in gaps:
    print(f"  {gap['start'].date()} to {gap['end'].date()}: {gap['days_missing']} days")
```

3. **Identify today's gap:**
```bash
LAST_DATE=$(tail -1 /tmp/s3_dates.txt)
TODAY=$(date +%Y%m%d)

echo "Last date in S3: $LAST_DATE"
echo "Today's date: $TODAY"
echo "Gap: $(( ($(date -j -f "%Y%m%d" "$TODAY" "+%s") - $(date -j -f "%Y%m%d" "$LAST_DATE" "+%s")) / 86400 )) days"
```

**Output:** List of coverage gaps, prioritized by severity

---

### Sub-Phase 1.3: Upload Local ESPN Data to Fill Known Gaps (If Applicable)

**Status:** ⏸️ PENDING (NBA: may already be complete from Phase 0)
**Time Estimate:** 30 minutes

**When to run:** If you have local ESPN data that's more recent than S3 data

**Purpose:** Sync any local ESPN files not yet in S3

**Commands:**
```bash
# Check if local data is newer than S3
LOCAL_LAST=$(ls -1 /Users/ryanranft/0espn/data/nba/*.json | tail -1 | grep -oE '[0-9]{8}')
S3_LAST=$(aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive | grep "\.json$" | tail -1 | grep -oE '[0-9]{8}')

echo "Local last date: $LOCAL_LAST"
echo "S3 last date: $S3_LAST"

# If local is newer, sync
if [ "$LOCAL_LAST" -gt "$S3_LAST" ]; then
  echo "Uploading newer local files to S3..."
  aws s3 sync /Users/ryanranft/0espn/data/nba/ \
    s3://nba-sim-raw-data-lake/schedule/ \
    --exclude "*" --include "*.json" --size-only
else
  echo "S3 is up to date with local files"
fi
```

**Validation:**
- [ ] S3 last date >= local last date
- [ ] File counts match

---

### Sub-Phase 1.4: Run Automated Gap Filling (Workflow #38)

**Status:** ⏸️ PENDING
**Time Estimate:** 10-60 minutes (depending on gap size)

**Purpose:** Automatically scrape ESPN for missing dates up to today

**Follow Workflow #38:** [Auto-Update ESPN Data](../claude_workflows/workflow_descriptions/38_auto_update_espn_data.md)

**Quick run:**
```bash
bash scripts/etl/auto_update_espn_data.sh
```

**This workflow:**
1. ✓ Checks today's date
2. ✓ Finds last date with data in S3
3. ✓ Calculates gap (days missing)
4. ✓ Updates ESPN scraper end_date automatically
5. ✓ Runs ESPN scraper for missing dates
6. ✓ Uploads new files to S3
7. ✓ Extracts to RDS database (if Phase 3 complete)
8. ✓ Verifies results

**Validation:**
- [ ] Gap filled: S3 last date == today
- [ ] New files uploaded successfully
- [ ] No errors in scraping process

---

### Sub-Phase 1.5: Establish Data Quality Baseline

**Status:** ⏸️ PENDING
**Time Estimate:** 2 hours

**Purpose:** Calculate and document baseline quality metrics

**Quality metrics to track:**

#### 1. Completeness
```python
# Expected games per season: ~82 games/team * 30 teams = ~2,460 games
# Actual: Check S3 files vs expected

import boto3
from datetime import datetime

s3 = boto3.client('s3')
bucket = 'nba-sim-raw-data-lake'

# Count files per season
seasons = {}
response = s3.list_objects_v2(Bucket=bucket, Prefix='schedule/')

for obj in response.get('Contents', []):
    key = obj['Key']
    if key.endswith('.json'):
        # Extract year from YYYYMMDD
        date_str = key.split('/')[-1].replace('.json', '')
        year = int(date_str[:4])
        month = int(date_str[4:6])

        # NBA season spans Oct-Jun
        season = year if month >= 10 else year - 1
        seasons[season] = seasons.get(season, 0) + 1

for season, count in sorted(seasons.items()):
    expected = 1230  # ~82 games/team * 30 teams / 2
    completeness = (count / expected) * 100
    print(f"Season {season}-{season+1}: {count} games ({completeness:.1f}% complete)")
```

#### 2. Accuracy
```python
# Verify against NBA.com Stats API (if chosen as verification source)
# Sample 100 random games, compare scores
# Track: matches / total_checked * 100
```

#### 3. Freshness
```python
from datetime import datetime

last_date = "2025-06-30"  # From S3 analysis
today = datetime.today()
freshness_days = (today - datetime.strptime(last_date, '%Y-%m-%d')).days

print(f"Data freshness: {freshness_days} days old")
# NBA offseason: acceptable if < 180 days
# NBA season: should be < 1 day
```

#### 4. Consistency
```python
# Check for team name variations, player name inconsistencies
# Ensure canonical IDs exist for all entities
```

**Output:** `docs/DATA_QUALITY_BASELINE.md` with all 4 metrics

---

### Sub-Phase 1.6: Data Source Verification Setup (Optional)

**Status:** ⏸️ PENDING USER INPUT
**Time Estimate:** 3-4 hours

**Purpose:** Set up secondary data sources for validation

**User must choose verification source:**

| Source | Type | Cost | Pros | Cons |
|--------|------|------|------|------|
| **NBA.com Stats** | API | Free | Official, authoritative | Rate limits, reverse-engineering |
| **Basketball Reference** | HTML | Free | Most comprehensive | Scraping required, TOS restrictions |
| **SportsData.io** | API | $19/mo | Clean API, reliable | Cost |
| **balldontlie** | API | Free | Simple REST, unlimited | Community-maintained, less reliable |

**Steps for NBA.com Stats API (example):**

1. **Test API access:**
```python
import requests

url = "https://stats.nba.com/stats/scoreboardV2"
params = {'GameDate': '2023-04-10'}
headers = {'User-Agent': 'Mozilla/5.0'}

response = requests.get(url, params=params, headers=headers)
if response.status_code == 200:
    print("✓ NBA.com Stats API accessible")
    print(f"Games on 2023-04-10: {len(response.json()['resultSets'][0]['rowSet'])}")
else:
    print(f"✗ API error: {response.status_code}")
```

2. **Document rate limits:**
- NBA.com Stats: ~10-20 requests/minute (unofficial)
- Implement exponential backoff

3. **Create verification script:**
```python
# scripts/etl/verify_nba_games.py
# Compare ESPN data vs NBA.com Stats
# Log discrepancies to database table
```

4. **Add credentials to environment:**
```bash
# No API key needed for NBA.com Stats
# But add User-Agent to ~/nba-sim-credentials.env
echo 'NBA_STATS_USER_AGENT="Mozilla/5.0"' >> ~/nba-sim-credentials.env
```

**Output:**
- Verification source chosen and documented
- Test script working
- Credentials configured
- Rate limits documented

---

## Multi-Sport Replication Framework

**When adding a new sport (NFL, MLB, NHL, Soccer):**

### Step 1: Ask User for Sport-Specific Data Sources

**Claude must ask:**
```
Great! Let's set up data quality analysis for [SPORT]. I need to know:

1. Do you already have data in S3 for [SPORT]?
   (If not, complete Phase 0 first)

2. What verification/validation source do you prefer?
   Options for [SPORT]:
   - Official league API ([SPORT].com)
   - Sports Reference sites
   - Commercial API (SportsData.io, etc.)
   - Community API

3. What fields are most critical to verify?
   - Game scores (always)
   - Player stats
   - Team stats
   - Betting odds
   - Other: ___________

4. Auto-fix or manual review?
   - Auto-fix everything (fast, risky)
   - Auto-fix low severity, review high/critical (recommended)
   - Manual review all (slow, safe)
```

### Step 2: Run Sub-Phases 1.1-1.6 for New Sport

Same process as NBA:
1. Analyze S3 coverage
2. Identify gaps
3. Upload local data (if applicable)
4. Run automated gap filling (adapt Workflow #38 for sport)
5. Establish quality baseline
6. Set up verification sources

### Step 3: Document Sport-Specific Findings

Create `docs/sports/{sport}/QUALITY_BASELINE.md`

---

## Cost Analysis

**Per sport costs (monthly):**

| Verification Source | Cost | Notes |
|---------------------|------|-------|
| **NBA.com Stats** | $0 | Free, rate-limited |
| **Basketball Reference** | $0 | Free, scraping |
| **SportsData.io** | $19/mo | Paid API |
| **balldontlie** | $0 | Free, community |

**AWS costs (this phase):**
- S3 GET requests: ~$0.01/month (checking files)
- Lambda (if automated): ~$0.20/month
- **Total: $0-20/month depending on verification source choice**

---

## Success Criteria

- [ ] Data coverage analyzed (file counts, date ranges)
- [ ] Coverage gaps identified and documented
- [ ] Automated gap-filling workflow tested (Workflow #38)
- [ ] Quality baseline metrics calculated:
  - [ ] Completeness > 95%
  - [ ] Freshness < 7 days (in-season)
  - [ ] Consistency checked (canonical IDs)
- [ ] Verification source chosen (optional for Phase 2-3)

---

## Next Steps

After completing this phase:
1. ✅ Data quality baseline established
2. ✅ Coverage gaps filled (S3 up to date)
3. ✅ Update PROGRESS.md status
4. → Proceed to [Phase 2: ETL Development](PHASE_2_AWS_GLUE.md)

**Phase 1 establishes the quality foundation for extraction and database loading.**

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md) | **Workflows:** [Workflow Index](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related phases:**
- Previous: [Phase 0: Data Collection & Initial Upload](PHASE_0_DATA_COLLECTION.md)
- Next: [Phase 2: ETL Development](PHASE_2_AWS_GLUE.md)
- Formerly: This was Phase 0 before ADR-008 reorganization

---

## Additional Resources

**Data Source Options Reference** - see old Phase 0 backup for complete tables

**Multi-sport data quality templates available for:**
- NFL (American Football)
- MLB (Baseball)
- NHL (Hockey)
- Soccer (Multiple Leagues)

---

*For Claude Code: See CLAUDE.md for navigation instructions and context management strategies.*

---

*Last updated: 2025-10-04 (reorganized per ADR-008)*
*Status: NBA pending verification source selection*