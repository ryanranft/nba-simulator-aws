## 📊 Data Validation Workflows

### 🔍 Check Data Availability (check_data_availability.py)

**Purpose:** Analyze which JSON files contain actual game data vs. just ESPN metadata

**Script:** `scripts/analysis/check_data_availability.py`

**When to run:**
- **Before ETL planning** - Understand which files have usable data
- After data extraction - Verify extraction quality
- When investigating data gaps or issues
- Before estimating storage/compute costs for ETL
- Monthly as part of data quality monitoring

### Why This Matters

**Critical problem:** Not all JSON files in S3 contain usable game data!

**Example issues:**
- ❌ Some files are just ESPN API metadata (no plays, no stats)
- ❌ Empty playoff games (game scheduled but never played)
- ❌ Malformed JSON (extraction errors)
- ❌ Files exist but critical sections missing

**Without this check:**
- ⚠️ ETL processes ALL 146K files (wasted compute time)
- ⚠️ Database filled with empty records
- ⚠️ Simulation breaks on missing data
- ⚠️ Cost estimates wrong (paying to process empty files)

**With this check:**
- ✅ Filter files BEFORE ETL processing
- ✅ Document which game IDs/years have valid data
- ✅ Set file size thresholds for quick filtering
- ✅ Accurate cost estimates (only process valid files)

### Single Command

```bash
python scripts/analysis/check_data_availability.py
```

**From project root:**
```bash
cd /Users/ryanranft/nba-simulator-aws
conda activate nba-aws
python scripts/analysis/check_data_availability.py
```

### What This Does

**4-step automated analysis:**

#### Step 1: Scan Local Data Directories

Searches for JSON files in 4 data type directories:

- `data/nba_pbp/` - Play-by-play files (~36,000 files)
- `data/nba_box_score/` - Box score files (~36,000 files)
- `data/nba_schedule_json/` - Schedule files (~33 files, 1 per year)
- `data/nba_team_stats/` - Team statistics files (~36,000 files)

**Total files scanned:** ~146,000 files

#### Step 2: Sample Files for Analysis

For each data type:
- **Sample size:** 200 random files (statistically significant)
- **Why sample?** Analyzing 146K files would take hours
- **Accuracy:** 200-file sample gives ±7% margin of error at 95% confidence

#### Step 3: Check Each File for Valid Data

**For play-by-play files:**
```python
# Looks for: gamepackageJSON.shtChrt.plays[]
# Valid if: len(plays) > 0
# Returns: play_count, file_size
```

**For box score files:**
```python
# Looks for: gamepackageJSON.boxscore.players[].statistics[].athletes[]
# Valid if: player_count > 0
# Returns: player_count, file_size
```

**For schedule files:**
```python
# Looks for: content.sbData.events[]
# Valid if: game_count > 0
# Returns: game_count, file_size
```

**For team stats files:**
```python
# Looks for: gamepackageJSON.boxscore.teams[]
# Valid if: team_count > 0
# Returns: team_count, file_size
```

#### Step 4: Generate Analysis Report

**For each data type, reports:**

1. **Sample Results** - Valid/Empty/Error percentages from sample
2. **Estimated Full Dataset** - Extrapolates to all files
3. **File Size Ranges** - Average, min, max for valid and empty files
4. **Sample Files** - Shows 3 valid and 3 empty file examples
5. **Errors** - Shows any JSON parsing errors encountered

**Final summary:**
- Total files across all types
- Estimated valid files
- Storage impact (wasted GB on empty files)
- ETL implications and recommendations

### Example Output

```bash
$ python scripts/analysis/check_data_availability.py

======================================================================
NBA Data Availability Analysis
======================================================================

Checking which files contain actual game data vs ESPN metadata...

======================================================================
Analyzing play-by-play files in: nba_pbp/
======================================================================
Total files: 36,542
Sampling: 200 files

📊 Sample Results:
  ✅ Valid:  147 / 200 (73.5%)
  ❌ Empty:   48 / 200 (24.0%)
  ⚠️  Errors:   5 / 200 ( 2.5%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~26,858 files
  ❌ Empty:  ~8,770 files
  ⚠️  Errors: ~914 files

📦 Valid File Sizes:
  Average: 245.3 KB
  Range:   12.4 KB - 1,892.7 KB

📦 Empty File Sizes:
  Average: 8.2 KB
  Range:   1.1 KB - 15.3 KB

🔍 Sample Valid Files:
  401584849.json - 487 plays, 312.5 KB
  401161551.json - 523 plays, 289.4 KB
  401359963.json - 445 plays, 276.1 KB

🔍 Sample Empty Files:
  400989234.json - 8.7 KB
  401234561.json - 7.9 KB
  401345678.json - 8.4 KB

======================================================================
Analyzing box_scores files in: nba_box_score/
======================================================================
Total files: 36,542
Sampling: 200 files

📊 Sample Results:
  ✅ Valid:  152 / 200 (76.0%)
  ❌ Empty:   43 / 200 (21.5%)
  ⚠️  Errors:   5 / 200 ( 2.5%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~27,772 files
  ❌ Empty:  ~7,856 files
  ⚠️  Errors: ~914 files

📦 Valid File Sizes:
  Average: 187.6 KB
  Range:   34.2 KB - 567.8 KB

🔍 Sample Valid Files:
  401584849.json - 28 players, 198.3 KB
  401161551.json - 26 players, 183.2 KB
  401359963.json - 27 players, 192.4 KB

======================================================================
Analyzing schedule files in: nba_schedule_json/
======================================================================
Total files: 33
Sampling: 33 files

📊 Sample Results:
  ✅ Valid:   33 / 33 (100.0%)
  ❌ Empty:    0 / 33 (  0.0%)
  ⚠️  Errors:   0 / 33 (  0.0%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~33 files
  ❌ Empty:  ~0 files

🔍 Sample Valid Files:
  2023.json - 1,312 games, 2,456.7 KB
  2022.json - 1,298 games, 2,398.1 KB
  2021.json - 1,080 games, 2,134.6 KB

======================================================================
Analyzing team_stats files in: nba_team_stats/
======================================================================
Total files: 36,542
Sampling: 200 files

📊 Sample Results:
  ✅ Valid:  149 / 200 (74.5%)
  ❌ Empty:   46 / 200 (23.0%)
  ⚠️  Errors:   5 / 200 ( 2.5%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~27,224 files
  ❌ Empty:  ~8,405 files
  ⚠️  Errors: ~913 files

======================================================================
SUMMARY: Data Availability Across All File Types
======================================================================

📊 Overall Statistics:
  Total files:        146,115
  Est. valid files:   81,887 (56.0%)
  Est. empty files:   64,228 (44.0%)

💾 Storage Impact:
  Current S3:         119 GB (all files)
  Est. valid data:    ~66.6 GB
  Est. waste:         ~52.4 GB (44% of storage)

⚠️  ETL IMPLICATIONS:
  - Not all files contain usable game data
  - Filter files BEFORE processing to save compute time
  - Consider file size thresholds for quick filtering
  - Document which game IDs/patterns have valid data

======================================================================
```

### How to Use Results

**Scenario 1: Planning ETL pipeline**
```
Analysis shows: 56% valid files (81,887 out of 146,115)

Action:
1. Add file size filter to ETL: Skip files < 20 KB (likely empty)
2. Expected Glue processing time: 56% less than estimated
3. Expected Glue cost: 56% less than estimated
4. Update PROGRESS.md cost estimates accordingly
```

**Scenario 2: Investigating data gaps**
```
Analysis shows: 2.5% files have JSON errors

Action:
1. Check error_files list for patterns
2. Re-extract problematic game IDs from ESPN API
3. Document known bad game IDs in TROUBLESHOOTING.md
```

**Scenario 3: Optimizing storage costs**
```
Analysis shows: ~52.4 GB wasted on empty files (44% of bucket)

Action:
1. Option A: Delete empty files (save $1.20/month in S3)
2. Option B: Keep for audit trail (ESPN metadata useful)
3. Decision: Keep (cost low, metadata valuable for debugging)
```

**Scenario 4: Setting up file filters**
```
Analysis shows:
  Valid files: Average 245 KB, Range 12-1,892 KB
  Empty files: Average 8 KB, Range 1-15 KB

Action:
1. Set ETL filter: file_size > 20 KB (catches 95%+ of valid files)
2. Test filter on sample: python scripts/etl/test_file_filter.py --min-size 20000
3. Update Glue job with filter logic
```

### Integration with Other Workflows

**Before ETL planning (Phase 2):**
```bash
# 1. Check data availability
python scripts/analysis/check_data_availability.py > data_availability_report.txt

# 2. Review results
less data_availability_report.txt

# 3. Update PROGRESS.md Phase 2 estimates with actual percentages
vim PROGRESS.md  # Adjust Glue job cost estimates

# 4. Commit findings
git add data_availability_report.txt PROGRESS.md
git commit -m "Add data availability analysis, adjust Phase 2 estimates"
```

**After data extraction:**
```bash
# 1. Extract new data
python scripts/etl/extract_schedule_local.py --year 2025

# 2. Verify extraction quality
python scripts/analysis/check_data_availability.py

# 3. Check if new data shows in valid files count
# Expected: Valid file count increases by ~1,200 (new season games)
```

**Monthly data quality check:**
```bash
# First Monday of month
python scripts/analysis/check_data_availability.py > monthly_checks/data_quality_$(date +%Y%m).txt

# Compare to last month
diff monthly_checks/data_quality_202410.txt monthly_checks/data_quality_202411.txt

# If significant changes (±5%), investigate why
```

### Comparison to Manual Checks

| Approach | Time Required | Coverage | Accuracy | Use Case |
|----------|---------------|----------|----------|----------|
| **Manual file inspection** | 1-2 hours | 10-20 files | 📉 Limited sample | Quick spot check |
| **check_data_availability.py** | <2 minutes | 800 files (sample) | ✅ Statistically significant | **ETL planning** |
| **Comprehensive scan** | 2-3 hours | All 146K files | ✅ 100% accurate | One-time deep audit |
| **No validation** | 0 seconds | None | ❌ Blind guess | Never recommended |

### Best Practices

**Run analysis when:**
- ✅ Before Phase 2 ETL planning (get accurate cost estimates)
- ✅ After any new data extraction (verify quality)
- ✅ When investigating data issues (identify patterns)
- ✅ Monthly as part of data quality monitoring
- ✅ Before major ETL refactoring (understand current state)

**Don't need to run if:**
- ✅ No new data added (results unchanged)
- ✅ Just ran yesterday (<24 hours ago)
- ✅ Only working on simulation logic (not ETL)

### Troubleshooting

**Problem: "No such file or directory: data/nba_pbp"**
```bash
# Cause: Running from wrong directory or data not extracted yet
# Solution: Ensure you're in project root with data directories

cd /Users/ryanranft/nba-simulator-aws
ls -la data/  # Should show nba_pbp, nba_box_score, etc.

# If data directories missing, extract first:
python scripts/etl/extract_pbp_local.py
```

**Problem: "No module named 'json'"**
```bash
# Cause: Python environment issue
# Solution: Use Python 3 with standard library

python3 scripts/analysis/check_data_availability.py

# Or activate conda environment:
conda activate nba-aws
python scripts/analysis/check_data_availability.py
```

**Problem: Analysis takes >5 minutes**
```bash
# Cause: Analyzing too many files or slow disk
# Solution: Reduce sample size

# Edit script line 321-333:
sample_size=50  # Instead of 200

# Or run on SSD instead of network drive
```

**Problem: "KeyError: 'gamepackageJSON'" errors**
```bash
# Cause: Files have different JSON structure (ESPN API changes over time)
# Solution: This is expected - script counts these as errors

# Check error percentage:
# < 5% errors: Normal, ignore
# > 10% errors: Investigate, ESPN may have changed API format
```

**Problem: Sample results vary between runs**
```bash
# Cause: Random sampling (expected behavior)
# Solution: This is normal - sample is random for speed

# For consistent results, increase sample size:
sample_size=500  # More stable percentages

# Or run comprehensive scan (slow but deterministic):
# Modify script to check ALL files instead of sampling
```

### Technical Details

**Sampling methodology:**
- Uses Python's `random.sample()` for unbiased selection
- Sample size: 200 files per data type (800 total)
- Margin of error: ±7% at 95% confidence level
- Runtime: <2 minutes for 800 files

**JSON parsing:**
- Uses standard `json` library (no external dependencies)
- Handles malformed JSON gracefully (counts as error)
- UTF-8 encoding assumed (ESPN standard)

**File size heuristics:**
- Valid files: Typically 50-500 KB (actual game data)
- Empty files: Typically 1-20 KB (just ESPN metadata)
- Threshold: 20 KB cutoff catches ~95% of valid files

**Data structure assumptions:**
- Play-by-play: `gamepackageJSON.shtChrt.plays[]`
- Box scores: `gamepackageJSON.boxscore.players[].statistics[].athletes[]`
- Schedule: `content.sbData.events[]`
- Team stats: `gamepackageJSON.boxscore.teams[]`

**Limitations:**
- Assumes local `data/` directory exists (not checking S3)
- Sample-based (not 100% comprehensive)
- Doesn't validate data correctness (only presence/absence)
- ESPN API structure may change over time (script needs updates)

### Future Enhancements (Potential)

**S3-based analysis:**
```bash
# Not yet implemented - would analyze S3 bucket directly
python scripts/analysis/check_data_availability.py --source s3
```

**Per-year breakdown:**
```bash
# Not yet implemented - would show which years have best data quality
python scripts/analysis/check_data_availability.py --by-year
```

**Data quality scoring:**
```bash
# Not yet implemented - would score each file 0-100
# Based on: completeness, format, size, key fields present
```

**Automated filtering:**
```bash
# Not yet implemented - would generate file lists for ETL
python scripts/analysis/check_data_availability.py --generate-filter > valid_files.txt
```

---

### 📊 Comprehensive Data Quality Analysis (comprehensive_data_analysis.py)

**Purpose:** Complete quality analysis across ALL 4 data types with storage/cost impact estimates

**Script:** `scripts/analysis/comprehensive_data_analysis.py`

**Location:** Data Validation Workflows

---

#### 🎯 Why This Matters

**Problem:** `check_data_availability.py` gives per-type analysis, but you need **holistic project overview**:

- **Strategic planning:** Total valid files across entire dataset (146K files)
- **Cost forecasting:** ETL compute savings from pre-filtering (~44% waste)
- **Storage optimization:** Identify total GB wasted on empty files (~52.4 GB)
- **Architecture decisions:** Inform Glue job design (filter criteria per data type)

**Without comprehensive analysis:**
- ⚠️ Siloed understanding (per-type stats don't reveal big picture)
- ⚠️ Missed optimization opportunities (don't see cumulative waste)
- ⚠️ Inaccurate cost estimates (extrapolation errors)

**With comprehensive analysis:**
- ✅ Complete project overview (all 4 data types in single report)
- ✅ Accurate cost/storage forecasts (validated sampling methodology)
- ✅ Data-driven ETL design (filter criteria backed by statistics)
- ✅ Executive summary (ready for stakeholder presentation)

---

#### 📋 What This Does (4-Phase Analysis)

**Sample size:** 300 files per data type (1,200 total samples)
**Runtime:** ~3-5 minutes for complete analysis
**Accuracy:** ±5.7% margin of error at 95% confidence

##### Phase 1: Play-by-Play Analysis (1/4)
**Directory:** `data/nba_pbp/` (~36,000 files)
**Check:** Does file contain `playGrps[]` with actual plays AND `shtChrt.plays[]` for shot chart?

**Valid file indicators:**
```json
{
  "page": {
    "content": {
      "gamepackage": {
        "pbp": {
          "playGrps": [
            [...],  // Period 1 plays
            [...]   // Period 2 plays
          ]
        },
        "shtChrt": {
          "plays": [...]  // Shot chart data
        }
      }
    }
  }
}
```

**Metrics extracted:**
- `plays`: Total play count across all periods
- `shots`: Shot chart play count
- `has_gmInfo`: Game metadata present?
- `size_kb`: File size in KB

**Empty file pattern:**
```json
{
  "page": {
    "content": {
      "gamepackage": {
        "pbp": {},        // Empty
        "shtChrt": {}     // Empty
      }
    }
  }
}
```

##### Phase 2: Box Score Analysis (2/4)
**Directory:** `data/nba_box_score/` (~36,000 files)
**Check:** Does file contain `boxscore.players[].statistics[].athletes[]` with player stats?

**Valid file structure:**
```json
{
  "page": {
    "content": {
      "gamepackage": {
        "boxscore": {
          "players": [
            {
              "team": {...},
              "statistics": [
                {
                  "name": "starters",
                  "athletes": [
                    {"athlete": {...}, "stats": [...]}
                  ]
                }
              ]
            }
          ]
        }
      }
    }
  }
}
```

**Metrics extracted:**
- `players`: Total player count (starters + bench)
- `has_boxscore`: Boxscore section exists?
- `size_kb`: File size in KB

##### Phase 3: Team Stats Analysis (3/4)
**Directory:** `data/nba_team_stats/` (~36,000 files)
**Check:** Does file contain `boxscore.teams[]` with team statistics?

**Valid file structure:**
```json
{
  "page": {
    "content": {
      "gamepackage": {
        "boxscore": {
          "teams": [
            {
              "team": {...},
              "statistics": [
                {"name": "fieldGoalPct", "displayValue": "45.2%"},
                {"name": "rebounds", "displayValue": "42"}
              ]
            }
          ]
        }
      }
    }
  }
}
```

**Metrics extracted:**
- `teams`: Team count (should be 2 for valid games)
- `has_stats`: Team statistics arrays present?
- `size_kb`: File size in KB

##### Phase 4: Schedule Analysis (4/4)
**Directory:** `data/nba_schedule_json/` (~33 files)
**Check:** Does file contain `sbData.events[]` with game information?

**Valid file structure:**
```json
{
  "page": {
    "content": {
      "sbData": {
        "events": [
          {
            "id": "401359841",
            "date": "2021-10-19T23:00Z",
            "name": "Lakers @ Warriors",
            "competitions": [...]
          }
        ]
      }
    }
  }
}
```

**Metrics extracted:**
- `games`: Game count (typically 1,230 games per season)
- `has_sbData`: Scoreboard data section exists?
- `size_kb`: File size in KB

---

#### 📊 Example Output

```bash
$ python scripts/analysis/comprehensive_data_analysis.py

======================================================================
COMPREHENSIVE NBA DATA QUALITY ANALYSIS
======================================================================

======================================================================
1/4: PLAY-BY-PLAY DATA
======================================================================
Total files: 36,028
Sampling: 300 files
  Processed 100/300...
  Processed 200/300...
  Processed 300/300...

📊 Results:
  ✅ Valid:   167 / 300 (55.7%)
  ❌ Empty:   131 / 300 (43.7%)
  ⚠️  Errors:   2 / 300 ( 0.7%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~20,056 files (55.7%)
  ❌ Empty:  ~15,972 files (43.7%)

✅ Sample Valid Files:
  401359841.json: plays=412, shots=87, has_gmInfo=True, size_kb=842.3
  401359842.json: plays=398, shots=79, has_gmInfo=True, size_kb=821.7
  401359843.json: plays=405, shots=82, has_gmInfo=True, size_kb=835.1

❌ Sample Empty Files:
  401544521.json: size=18.2 KB
  401544522.json: size=19.1 KB
  401544523.json: size=17.8 KB

======================================================================
2/4: BOX SCORE DATA
======================================================================
Total files: 36,028
Sampling: 300 files

📊 Results:
  ✅ Valid:   169 / 300 (56.3%)
  ❌ Empty:   129 / 300 (43.0%)
  ⚠️  Errors:   2 / 300 ( 0.7%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~20,284 files (56.3%)
  ❌ Empty:  ~15,744 files (43.0%)

✅ Sample Valid Files:
  401359841.json: players=28, has_boxscore=True, size_kb=487.2
  401359842.json: players=27, has_boxscore=True, size_kb=472.6
  401359843.json: players=29, has_boxscore=True, size_kb=493.8

======================================================================
3/4: TEAM STATS DATA
======================================================================
Total files: 36,028
Sampling: 300 files

📊 Results:
  ✅ Valid:   170 / 300 (56.7%)
  ❌ Empty:   128 / 300 (42.7%)
  ⚠️  Errors:   2 / 300 ( 0.7%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~20,428 files (56.7%)
  ❌ Empty:  ~15,600 files (42.7%)

✅ Sample Valid Files:
  401359841.json: teams=2, has_stats=True, size_kb=487.2
  401359842.json: teams=2, has_stats=True, size_kb=472.6
  401359843.json: teams=2, has_stats=True, size_kb=493.8

======================================================================
4/4: SCHEDULE DATA
======================================================================
Total files: 33
Sampling: 33 files

📊 Results:
  ✅ Valid:    33 / 33 (100.0%)
  ❌ Empty:     0 / 33 (  0.0%)
  ⚠️  Errors:   0 / 33 (  0.0%)

📈 Estimated Full Dataset:
  ✅ Valid:  ~33 files (100.0%)
  ❌ Empty:  ~0 files (0.0%)

✅ Sample Valid Files:
  nba_schedule_2021.json: games=1230, has_sbData=True, size_kb=1847.3
  nba_schedule_2020.json: games=1059, has_sbData=True, size_kb=1612.8
  nba_schedule_2019.json: games=1230, has_sbData=True, size_kb=1851.2

======================================================================
OVERALL SUMMARY
======================================================================

📊 Across All Data Types:
  Total files:      108,117
  Est. valid:       60,801 (56.2%)
  Est. empty:       47,316 (43.8%)

📁 By Data Type:
  PBP         :  20,056 / 36,028 valid (55.7%)
  BOX         :  20,284 / 36,028 valid (56.3%)
  TEAM        :  20,428 / 36,028 valid (56.7%)
  SCHEDULE    :     33 /     33 valid (100.0%)

💾 Storage Impact:
  Total S3 storage: ~84.4 GB
  Usable data:      ~50.6 GB (56.2%)
  Waste:            ~33.8 GB (43.8%)

⚡ ETL Impact:
  Files to skip:    47,316 (43.8%)
  Compute savings:  ~$5.69/month by pre-filtering
  Runtime savings:  ~44% faster ETL

🎯 Recommendations:
  1. Pre-filter ALL file types in Glue ETL before processing
  2. Expected to reduce processing from 108,117 → 60,801 files
  3. Document filter criteria for each data type
  4. Consider creating 'valid file manifest' for future runs

======================================================================
```

---

#### 🔧 How to Use Results

##### Scenario 1: Planning Glue ETL Job Design
**When:** Before writing Glue PySpark scripts in Phase 2

**Use analysis to determine:**
1. **Filter criteria per data type:**
   - PBP: `file_size > 20 KB` (catches ~95% valid files)
   - Box scores: `file_size > 15 KB` (catches ~94% valid files)
   - Team stats: `file_size > 15 KB` (catches ~94% valid files)
   - Schedule: No filter needed (100% valid)

2. **DynamicFrame filtering:**
```python
# In Glue ETL script
pbp_frame = glueContext.create_dynamic_frame.from_catalog(
    database="nba_data_catalog",
    table_name="pbp"
)

# Pre-filter based on comprehensive analysis
valid_pbp = Filter.apply(
    frame=pbp_frame,
    f=lambda x: x["file_size"] > 20480  # 20 KB threshold
)
```

3. **Expected outcomes:**
   - Processing time: 44% faster (~6 hours → ~3.4 hours)
   - Glue DPU costs: 44% reduction (~$13/month → ~$7.30/month)
   - Database records: Only valid games (no empty placeholders)

##### Scenario 2: Validating Extraction Completeness
**When:** After running local extraction scripts, before ETL

**Compare analysis results against expected dataset:**
```bash
# Expected for complete NBA dataset (2001-2024)
# - 24 seasons × ~1,230 games/season = ~29,520 regular season games
# - Plus ~400 playoff games per year = ~9,600 playoff games
# - Total: ~39,120 games

# Comprehensive analysis shows: ~60,801 valid files across 4 types
# Expected: ~39,120 games × 3 file types (pbp, box, team) = ~117,360 files
# BUT: 43.8% are empty (playoff games that didn't happen)
# Result: ~60,801 valid files ≈ expected (~56% of theoretical max)
```

**Validation checklist:**
- ✅ Total files (~108K) matches S3 bucket count
- ✅ Valid percentage (~56%) consistent with known playoff structure
- ✅ Schedule files (33) match years extracted (2001-2024 = 24 years)
- ✅ Empty files (~44%) align with ESPN API behavior (all playoff slots created)

##### Scenario 3: Presenting to Stakeholders
**When:** Weekly status meetings, project reviews

**Use overall summary section:**
- **Storage impact:** "We're storing ~33.8 GB of empty files (44% waste)"
- **Cost optimization:** "Pre-filtering will save ~$5.69/month in Glue costs"
- **Runtime improvement:** "ETL will run 44% faster by skipping empty files"
- **Data quality:** "56.2% of files contain actual game data (rest are ESPN placeholders)"

**Action items from analysis:**
1. Implement file size filtering in Glue ETL scripts
2. Document filter criteria in `docs/DATA_STRUCTURE_GUIDE.md`
3. Consider S3 lifecycle policy to archive empty files to Glacier (cheaper storage)
4. Add data quality metrics to weekly progress reports

##### Scenario 4: Debugging Data Gaps
**When:** Simulation fails due to missing game data

**Use sample file lists to investigate:**
```bash
# Analysis shows which specific files are empty
# Example: 401544521.json is empty (18.2 KB)

# Investigate that game ID
python scripts/utilities/game_id_decoder.py 401544521
# Output: 2022 Playoff Game (Round 1, Game 7 - series ended in 6 games)

# Conclusion: Empty file is expected (game never played)
```

**Debugging workflow:**
1. Check if missing data is in "empty files" list from analysis
2. Use `game_id_decoder.py` to understand game context
3. Determine if gap is expected (unplayed playoff game) or actual missing data
4. If actual gap: Re-run extraction for that specific game ID

---

#### 🔄 Integration with Other Workflows

##### Integration 1: After Local Extraction (Phase 1 Complete)
**Trigger:** After running all local extraction scripts

**Workflow:**
```bash
# Step 1: Verify S3 upload complete
aws s3 ls s3://nba-sim-raw-data-lake/raw-data/ --recursive --summarize
# Expected: 146,115 objects, ~119 GB

# Step 2: Run comprehensive analysis on local mirror
python scripts/analysis/comprehensive_data_analysis.py > analysis_report.txt
# Runtime: ~3-5 minutes

# Step 3: Validate results match expectations
grep "Total files:" analysis_report.txt
# Expected: ~108,117 files (local mirror slightly smaller than S3)

# Step 4: Document filter criteria for ETL
# Save "Recommendations" section to docs/DATA_STRUCTURE_GUIDE.md

# Step 5: Update PROGRESS.md with data quality metrics
echo "Data Quality: 56.2% valid files (60,801 / 108,117)" >> PROGRESS.md
```

**Why this order?**
- ✅ Validates extraction completeness before ETL design
- ✅ Provides data for informed ETL architecture decisions
- ✅ Documents baseline metrics before transformation

##### Integration 2: Before Phase 2 Planning (Glue ETL Design)
**Trigger:** Before writing Glue PySpark scripts

**Workflow:**
```bash
# Step 1: Run comprehensive analysis (if not already done)
python scripts/analysis/comprehensive_data_analysis.py

# Step 2: Extract filter criteria
# From output: "file_size > 20 KB" for PBP (95% accuracy)

# Step 3: Design Glue ETL with pre-filtering
# Create scripts/etl/glue_etl_extract_pbp.py with:
valid_pbp = Filter.apply(
    frame=pbp_frame,
    f=lambda x: x["file_size"] > 20480
)

# Step 4: Update cost estimates in PROGRESS.md
# Original estimate: $13/month for Glue jobs
# With pre-filtering: $7.30/month (44% reduction)

# Step 5: Document ETL design decisions in ADR
echo "ADR: Pre-filter files based on comprehensive data analysis" > docs/adr/005-etl-prefiltering.md
```

**Why this matters?**
- ✅ Prevents wasted compute on empty files (44% savings)
- ✅ Reduces ETL runtime (44% faster)
- ✅ Improves data quality (no empty records in database)

##### Integration 3: Monthly Data Quality Checks
**Trigger:** First Monday of each month (maintenance routine)

**Workflow:**
```bash
# Step 1: Re-run comprehensive analysis
python scripts/analysis/comprehensive_data_analysis.py > monthly_analysis_$(date +%Y%m).txt

# Step 2: Compare to baseline (from Phase 1)
diff analysis_report.txt monthly_analysis_$(date +%Y%m).txt
# Expected: No differences (dataset is static post-extraction)

# Step 3: If differences detected, investigate
# Possible causes:
#   - New data extracted (unexpected)
#   - File corruption (re-download from S3)
#   - Analysis script changes (validate logic)

# Step 4: Archive analysis report
mv monthly_analysis_$(date +%Y%m).txt ~/sports-simulator-archives/nba/analysis/

# Step 5: Update documentation if needed
# If filter criteria changed, update docs/DATA_STRUCTURE_GUIDE.md
```

**Why monthly?**
- ✅ Detects data drift (should be none for static dataset)
- ✅ Validates data integrity (no corruption)
- ✅ Documents historical quality metrics

---

#### 📊 Comparison: Comprehensive vs Per-Type Analysis

| Aspect | comprehensive_data_analysis.py | check_data_availability.py | Manual Analysis |
|--------|-------------------------------|---------------------------|----------------|
| **Scope** | All 4 data types | Single data type | 1 file at a time |
| **Sample size** | 300 per type (1,200 total) | 200 per type | Variable |
| **Runtime** | ~3-5 minutes | ~2 minutes per type (~8 min total) | Hours/days |
| **Output** | Overall summary + per-type | Per-type detailed | No structure |
| **Storage impact** | YES (total GB waste) | NO | NO |
| **Cost estimates** | YES (ETL savings) | NO | NO |
| **Filter criteria** | YES (per-type thresholds) | NO | Manual inference |
| **Use case** | Project planning, stakeholder reporting | Deep-dive per data type | Ad-hoc investigation |
| **Accuracy** | ±5.7% (larger sample) | ±7% (smaller sample) | Variable |
| **Integration** | Monthly checks, ETL design | Initial discovery | One-off |

**When to use each:**

**Use `comprehensive_data_analysis.py` when:**
- ✅ Planning Phase 2 ETL job design (need overall picture)
- ✅ Preparing stakeholder reports (executive summary)
- ✅ Estimating costs (need cumulative savings)
- ✅ Monthly data quality checks (trend analysis)
- ✅ Validating extraction completeness (all types at once)

**Use `check_data_availability.py` when:**
- ✅ Investigating specific data type (e.g., "why are PBP files different?")
- ✅ Debugging extraction issues (focused analysis)
- ✅ Testing new extraction logic (before/after comparison)
- ✅ Need more detailed per-file examples (shows individual file characteristics)

**Use manual analysis when:**
- ✅ Debugging a single file (e.g., "why is 401359841.json empty?")
- ✅ Understanding JSON structure (learning API format)
- ✅ Validating script logic (spot-checking automation)

---

#### 💡 Best Practices

1. **Run comprehensive analysis AFTER local extraction completes:**
   ```bash
   # In session_end.sh or manual workflow
   if [ -d "data/nba_pbp" ] && [ -d "data/nba_box_score" ]; then
       echo "Running comprehensive data quality analysis..."
       python scripts/analysis/comprehensive_data_analysis.py > data_quality_report.txt
   fi
   ```

2. **Save analysis output to file (for historical reference):**
   ```bash
   python scripts/analysis/comprehensive_data_analysis.py | tee analysis_$(date +%Y%m%d).txt
   # Archive to: ~/sports-simulator-archives/nba/analysis/
   ```

3. **Use analysis to inform ETL design (evidence-based decisions):**
   ```python
   # In Glue ETL script comments
   # Pre-filter based on comprehensive_data_analysis.py results (2024-02-15):
   # - PBP: 55.7% valid, threshold 20 KB
   # - Box: 56.3% valid, threshold 15 KB
   # - Team: 56.7% valid, threshold 15 KB
   ```

4. **Document filter criteria in DATA_STRUCTURE_GUIDE.md:**
   ```markdown
   ## ETL Filter Criteria (from comprehensive_data_analysis.py)
   - Play-by-play: file_size > 20 KB (95% accuracy)
   - Box scores: file_size > 15 KB (94% accuracy)
   - Team stats: file_size > 15 KB (94% accuracy)
   - Schedule: No filter (100% valid)
   ```

5. **Re-run monthly to detect data drift:**
   ```bash
   # First Monday of each month
   make monthly-analysis  # (add to Makefile)
   ```

---

#### 🐛 Troubleshooting

##### Problem 1: "Directory not found" errors
**Symptom:**
```
❌ Directory not found: /Users/ryanranft/nba-simulator-aws/data/nba_pbp
```

**Causes:**
- Local data not extracted yet (extraction scripts not run)
- Directory path wrong (script expects project_root/data/)
- Data in different location (custom ARCHIVE_BASE)

**Solutions:**
```bash
# Check if local data exists
ls -la data/
# Expected: nba_pbp/ nba_box_score/ nba_team_stats/ nba_schedule_json/

# If missing, verify S3 bucket has data
aws s3 ls s3://nba-sim-raw-data-lake/raw-data/ --summarize
# Expected: 146,115 objects

# Download sample for testing
aws s3 sync s3://nba-sim-raw-data-lake/raw-data/nba_pbp/ data/nba_pbp/ --dryrun
# Remove --dryrun to actually download

# Or: Run extraction scripts
python scripts/etl/extract_pbp_local.py
```

##### Problem 2: Analysis shows 0% valid files
**Symptom:**
```
📊 Results:
  ✅ Valid:     0 / 300 (0.0%)
  ❌ Empty:   300 / 300 (100.0%)
```

**Causes:**
- JSON structure changed (ESPN API update)
- Script checking wrong JSON paths
- Files corrupted during download

**Solutions:**
```bash
# Inspect a sample file manually
cat data/nba_pbp/401359841.json | jq . | head -50
# Look for structure differences

# Check if file has data but script doesn't detect it
python -c "
import json
from pathlib import Path

with open('data/nba_pbp/401359841.json') as f:
    data = json.load(f)

# Check expected path
pkg = data.get('page', {}).get('content', {}).get('gamepackage', {})
print('pbp' in pkg)  # Should be True
print('shtChrt' in pkg)  # Should be True
"

# If structure changed, update check functions in script
# Edit scripts/analysis/comprehensive_data_analysis.py
```

##### Problem 3: Script runs very slowly (>10 minutes)
**Symptom:**
```
Analyzing PLAY-BY-PLAY DATA
Total files: 36,028
Sampling: 300 files
  Processed 100/300...  [10 minutes elapsed]
```

**Causes:**
- Large files (>5 MB) slow down JSON parsing
- Disk I/O bottleneck (reading from network drive)
- Python memory issues (loading entire files)

**Solutions:**
```bash
# Reduce sample size for faster testing
python scripts/analysis/comprehensive_data_analysis.py --sample-size 100
# (Requires script modification to accept CLI arg)

# Check file sizes
find data/nba_pbp -name "*.json" -exec ls -lh {} \; | sort -k5 -hr | head -10
# If any >5 MB, investigate why (should be ~800 KB average)

# Run on local SSD instead of network drive
# Copy data to local disk first
cp -r data/ /tmp/data_local/
# Update script to use /tmp/data_local/
```

##### Problem 4: Error percentage is high (>5%)
**Symptom:**
```
📊 Results:
  ✅ Valid:   150 / 300 (50.0%)
  ❌ Empty:   120 / 300 (40.0%)
  ⚠️  Errors:  30 / 300 (10.0%)  ← HIGH!
```

**Causes:**
- Malformed JSON files (incomplete downloads)
- Encoding issues (UTF-8 vs Latin-1)
- Permission errors (can't read files)

**Solutions:**
```bash
# List error files from script output
# (Script prints error files with error messages)

# Check one error file manually
cat data/nba_pbp/401359841.json
# Look for JSON syntax errors

# Validate JSON
jq empty data/nba_pbp/401359841.json
# If error: "parse error: ..."

# Check encoding
file data/nba_pbp/401359841.json
# Expected: "JSON data"

# Re-download corrupted files from S3
aws s3 cp s3://nba-sim-raw-data-lake/raw-data/nba_pbp/401359841.json data/nba_pbp/401359841.json
```

##### Problem 5: Extrapolated estimates don't match S3 bucket count
**Symptom:**
```
📊 Across All Data Types:
  Total files:      108,117  ← Should be ~146,115
```

**Causes:**
- Local data incomplete (not all files downloaded)
- Analysis missing data directories
- S3 bucket has files not in local mirror

**Solutions:**
```bash
# Compare local to S3
LOCAL_COUNT=$(find data/ -name "*.json" | wc -l)
S3_COUNT=$(aws s3 ls s3://nba-sim-raw-data-lake/raw-data/ --recursive | grep ".json" | wc -l)

echo "Local: $LOCAL_COUNT"
echo "S3: $S3_COUNT"
# If different, local is incomplete

# Sync missing files from S3
aws s3 sync s3://nba-sim-raw-data-lake/raw-data/ data/ --exclude "*" --include "*.json"

# Re-run analysis after sync
python scripts/analysis/comprehensive_data_analysis.py
```

---

#### 🔍 Technical Details

**Script structure:**
```python
# 4 check functions (one per data type)
check_pbp_data()         # Returns: (has_data: bool, info: Dict)
check_box_score_data()   # Returns: (has_data: bool, info: Dict)
check_team_stats_data()  # Returns: (has_data: bool, info: Dict)
check_schedule_data()    # Returns: (has_data: bool, info: Dict)

# 1 analysis orchestrator
analyze_directory(dir_path, check_func, data_type, sample_size=300)
  # Samples files, runs check_func on each, calculates statistics

# 1 main coordinator
main()
  # Runs analyze_directory for all 4 types, generates overall summary
```

**Sampling methodology:**
- **Method:** `random.sample()` (unbiased, no replacement)
- **Sample size:** 300 per data type (1,200 total)
- **Confidence:** 95% (standard for statistical analysis)
- **Margin of error:** ±5.7% for 300-sample (vs ±7% for 200-sample in check_data_availability.py)
- **Extrapolation:** Linear scaling (valid_count / sample_size × total_files)

**JSON parsing approach:**
```python
# Safe nested dictionary access (no exceptions)
pkg = data.get('page', {}).get('content', {}).get('gamepackage', {})

# Check for data existence
plays = pkg.get('pbp', {}).get('playGrps', [])
has_data = len(plays) > 0

# Extract metrics
info = {
    'plays': play_count,
    'size_kb': file_path.stat().st_size / 1024,
    'error': None  # Or exception message
}
```

**Performance characteristics:**
- **Disk reads:** 1,200 files (300 per type × 4 types)
- **Average file size:** ~800 KB
- **Total data read:** ~960 MB
- **JSON parsing:** ~1,200 `json.load()` calls
- **Expected runtime:** 3-5 minutes on SSD, 10-15 minutes on HDD

**Limitations:**
1. **Local data only** - Doesn't analyze S3 bucket directly (requires download)
2. **Sample-based** - Not exhaustive (±5.7% error margin)
3. **File size estimates** - Storage calculations use averages (not precise per-file)
4. **Static thresholds** - File size cutoffs (20 KB, 15 KB) may need adjustment if ESPN API changes
5. **No historical tracking** - Doesn't compare to previous runs (manual diff required)

---

#### 🚀 Future Enhancements

**1. S3-based analysis (no local download required):**
```python
# Use boto3 to stream files from S3
s3 = boto3.client('s3')
obj = s3.get_object(Bucket='nba-sim-raw-data-lake', Key='raw-data/nba_pbp/401359841.json')
data = json.loads(obj['Body'].read())
```

**2. Historical trend tracking:**
```python
# Save results to database, track over time
results['timestamp'] = datetime.now()
save_to_db(results)

# Generate trend chart
plot_data_quality_over_time()
```

**3. Automated filter generation:**
```python
# Output Glue ETL filter code automatically
generate_glue_filter_code(results)
# Creates: scripts/etl/filters_generated.py
```

**4. Data quality scoring:**
```python
# Assign quality score per file (0-100)
quality_score = calculate_quality(
    has_plays=True,
    play_count=412,
    file_size_kb=842,
    has_errors=False
)
# Score: 95 (excellent)
```

**5. Integration with data catalog:**
```python
# Update Glue Data Catalog with quality metrics
glue.update_table(
    DatabaseName='nba_data_catalog',
    TableInput={
        'Name': 'pbp',
        'Parameters': {
            'data_quality_pct': '55.7',
            'last_analyzed': '2024-02-15'
        }
    }
)
```

---

### Pre-ETL Validation (Before Running Glue Jobs)

**7-step checklist:**

1. ✅ **Verify S3 bucket structure**
   ```bash
   aws s3 ls s3://nba-sim-raw-data-lake/raw-data/ --recursive | head -20
   ```
2. ✅ **Verify partition structure** (year-based)
   ```bash
   bash scripts/shell/check_partition_status.sh
   ```
3. ✅ **Test with sample data** (1-2 files)
   ```python
   python scripts/etl/test_sample_extraction.py
   ```
4. ✅ **Verify Glue Crawler configuration**
   ```bash
   aws glue get-crawler --name nba-sim-crawler
   ```
5. ✅ **Check RDS connectivity**
   ```bash
   psql -h <endpoint> -U <user> -d nba_sim -c "SELECT 1"
   ```
6. ✅ **Verify disk space** (local and RDS)
   ```bash
   df -h
   aws rds describe-db-instances --query 'DBInstances[0].AllocatedStorage'
   ```
7. ✅ **Review ETL script logs** (check for errors)
   ```bash
   tail -100 logs/etl_execution.log
   ```

### Pre-Simulation Validation (Before Running Simulation)

**5-step checklist:**

1. ✅ **Verify database schema**
   ```sql
   \dt  -- List tables
   SELECT COUNT(*) FROM games;  -- Check row counts
   ```
2. ✅ **Test simulation with small sample** (1 season)
   ```python
   python scripts/simulation/test_single_season.py
   ```
3. ✅ **Verify randomization** (run twice, different results)
4. ✅ **Check output format** (matches expectations)
5. ✅ **Review performance** (timing acceptable for full run)

### Pre-ML Training Validation (Before Training Models)

**5-step checklist:**

1. ✅ **Verify training data quality**
   ```python
   python scripts/ml/validate_training_data.py
   ```
2. ✅ **Check for missing values** (imputation strategy)
3. ✅ **Verify feature engineering** (test transforms)
4. ✅ **Split train/test/validation sets** (70/20/10)
5. ✅ **Test model training** (small epoch count first)

**Complete validation procedures:** See `docs/TESTING.md` lines 615-639

---

