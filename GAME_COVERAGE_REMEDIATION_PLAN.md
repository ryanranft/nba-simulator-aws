# Game Coverage Remediation Plan

**Generated:** November 7, 2025
**Analysis Source:** `game_coverage_report_20251107_122209.json`
**Verification Script:** `scripts/validation/verify_game_coverage.py`

---

## Executive Summary

**Total Missing Games: 131** across 4 seasons (2011, 2015, 2017, 2018)

**Impact Assessment:**
- ✅ 2012, 2019 seasons: 100% complete
- ⚠️ 2015, 2017, 2018: 99.9% complete (1 game missing each)
- 🔴 2011: 87% complete (128 games / 13% missing) - **CRITICAL**

**Priority:** High for 2011, Low for 2015/2017/2018

---

## Detailed Gap Analysis

### 1. Season 2011-12 (Lockout): 128 Missing Games 🔴

**Pattern Identified:** ESPN Game ID Format Mismatch

- **Database has:** Games with ID format `3XXXXXXXX` (e.g., `311225018`)
- **Schedule shows:** Games with ID format `400XXXXXX` (e.g., `400237975`)
- **Issue:** These are **two separate datasets** from ESPN

**Teams Affected (by missing game count):**
| Team | Missing Games | % Complete |
|------|--------------|------------|
| **CHI** (Bulls) | 65 | 1.5% |
| **NO** (Hornets) | 65 | 1.5% |
| MEM | 6 | 90.9% |
| SAC | 6 | 90.9% |
| DEN | 5 | 92.4% |
| ATL | 5 | 92.4% |
| IND | 5 | 92.4% |
| MIA | 5 | 92.4% |
| BOS | 5 | 92.4% |
| DET | 5 | 92.4% |
| Others | 3-5 | 92-95% |

**Critical Games (Sample - First 10):**

1. `400237975` - LAL vs CHI (Dec 25, 2011) - **Christmas Day game!**
2. `400237981` - GS vs CHI (Dec 27, 2011)
3. `400237985` - PHX vs NO (Dec 27, 2011)
4. `400238001` - NO vs BOS (Dec 29, 2011)
5. `400238010` - SAC vs CHI (Dec 30, 2011)
6. `400238016` - LAC vs CHI (Dec 31, 2011)
7. `400238020` - NO vs PHX (Dec 31, 2011)
8. `400238029` - CHI vs MEM (Jan 2, 2012)
9. `400238036` - SAC vs NO (Jan 2, 2012)
10. `400238047` - UTAH vs NO (Jan 3, 2012)

**Date Range:** Dec 25, 2011 - April 25, 2012

**S3 Availability Check Needed:**
```bash
# Check if we have these game IDs in S3
aws s3 ls s3://nba-sim-raw-data-lake/espn_box_scores/ | grep "400237975"
aws s3 ls s3://nba-sim-raw-data-lake/espn_play_by_play/ | grep "400237975"
```

**Remediation Options:**

**Option A: Load from S3 (if available)**
- Check S3 for `400XXXXXX` format files
- Load using existing `scripts/etl/espn_incremental_async.py`
- Estimated time: 2-3 hours
- Cost: $0 (data already in S3)

**Option B: Re-scrape from ESPN API**
- Use ESPN's historical API with `400` format game IDs
- Estimated time: 4-6 hours (128 games × 2 endpoints × rate limiting)
- Cost: $0 (API is free)
- Risk: Data may not be available for 2011 season

**Option C: Accept Data Gap**
- Document as known limitation
- 2011 data is 13 years old, less relevant for ML models
- Focus on recent seasons (2012+) which are complete

**Recommendation:** **Option A** first (check S3), then **Option C** (accept gap for 2011)

---

### 2. Season 2015-16: 1 Missing Game

**Game:** `400828893` - WSH vs CHI (March 16, 2016 @ 11:00 PM UTC)

**S3 Check:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/espn_box_scores/400828893.json
aws s3 ls s3://nba-sim-raw-data-lake/espn_play_by_play/400828893.json
```

**Remediation:**
1. Check if file exists in S3
2. If yes: Load using single-game loader
3. If no: Re-scrape from ESPN API

**Priority:** Low (99.9% complete)
**Estimated Time:** 5 minutes
**Cost:** $0

---

### 3. Season 2017-18: 1 Missing Game

**Game:** `400975770` - MEM vs CHI (March 16, 2018 @ 12:00 AM UTC)

**S3 Check:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/espn_box_scores/400975770.json
aws s3 ls s3://nba-sim-raw-data-lake/espn_play_by_play/400975770.json
```

**Remediation:** Same as 2015-16

**Priority:** Low (99.9% complete)
**Estimated Time:** 5 minutes
**Cost:** $0

**Interesting Pattern:** Both 2015 and 2017 missing games involve **CHI (Bulls)** and occur on **March 16**!

---

### 4. Season 2018-19: 1 Missing Game

**Game:** `401070722` - TOR vs CHA (October 22, 2018 @ 11:30 PM UTC)

**S3 Check:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/espn_box_scores/401070722.json
aws s3 ls s3://nba-sim-raw-data-lake/espn_play_by_play/401070722.json
```

**Remediation:** Same as 2015-16

**Priority:** Low (99.9% complete)
**Estimated Time:** 5 minutes
**Cost:** $0

---

## Implementation Plan

### Phase 1: Quick Wins (2015, 2017, 2018) - Est. 15 minutes

**Step 1: Check S3 for missing games**
```bash
# Run S3 availability check
python scripts/validation/check_s3_availability.py \
  --game-ids 400828893,400975770,401070722
```

**Step 2: Load available games from S3**
```bash
# Load single games
python scripts/etl/load_single_game.py --game-id 400828893
python scripts/etl/load_single_game.py --game-id 400975770
python scripts/etl/load_single_game.py --game-id 401070722
```

**Step 3: Re-scrape missing games (if not in S3)**
```bash
# Fetch from ESPN API
python scripts/etl/espn_incremental_async.py \
  --game-ids 400828893,400975770,401070722 \
  --force-rescrape
```

### Phase 2: 2011 Lockout Season - Est. 2-6 hours

**Step 1: Investigate ESPN Game ID formats**
```bash
# Check what 400XXXXXX files exist in S3
aws s3 ls s3://nba-sim-raw-data-lake/espn_box_scores/ | \
  grep "^2025.*400[0-9]" | \
  awk '{print $4}' | \
  sed 's/\.json$//' > s3_400_format_game_ids.txt

# Cross-reference with missing games
python scripts/validation/cross_reference_s3.py \
  --missing-games-file game_coverage_report_20251107_122209.json \
  --season 2011 \
  --s3-list s3_400_format_game_ids.txt
```

**Step 2: Decision Point**

If **50+ games found in S3:**
- Proceed with S3 batch load
- Estimated time: 2-3 hours
- Use: `python scripts/etl/batch_load_from_s3.py --season 2011 --source-file missing_2011_games.json`

If **<50 games found in S3:**
- Document as known data gap
- Update `docs/DATA_QUALITY_BASELINE.md` with 2011 limitations
- Focus on 2012+ seasons for ML training

**Step 3: Verification**
```bash
# Re-run coverage verification after loading
python scripts/validation/verify_game_coverage.py --season 2011
```

---

## Success Criteria

**Phase 1 (Quick Wins):**
- ✅ 2015, 2017, 2018 seasons: 100% complete (1,230 games each)
- ✅ All 3 missing games loaded to database
- ✅ Verification report shows 0 missing games

**Phase 2 (2011 Season):**
- Goal: <10 missing games (99% complete)
- Acceptable: 50-100 missing games (90-95% complete) if data unavailable
- Document: Known limitations in `DATA_QUALITY_BASELINE.md`

---

## Scripts to Create

### 1. `scripts/validation/check_s3_availability.py`
**Purpose:** Check if specific game IDs exist in S3
**Input:** List of game IDs
**Output:** JSON report of found/missing files
**Estimated dev time:** 30 minutes

### 2. `scripts/etl/load_single_game.py`
**Purpose:** Load a single game from S3 to database
**Input:** Game ID
**Output:** Success/failure status
**Estimated dev time:** 1 hour

### 3. `scripts/validation/cross_reference_s3.py`
**Purpose:** Cross-reference missing games with S3 contents
**Input:** Missing games JSON, S3 file list
**Output:** Matched games report
**Estimated dev time:** 30 minutes

### 4. `scripts/etl/batch_load_from_s3.py`
**Purpose:** Batch load multiple games from S3
**Input:** List of game IDs
**Output:** Load summary report
**Estimated dev time:** 1 hour

**Total dev time:** ~3 hours

---

## Risk Assessment

**Low Risk:**
- 2015, 2017, 2018 single-game loads (isolated, minimal impact)
- S3 file checks (read-only operations)

**Medium Risk:**
- 2011 batch load (large volume, potential data quality issues)
- Re-scraping from ESPN (API availability uncertain for 2011)

**Mitigation:**
- Test single-game load on dev database first
- Create database backup before bulk 2011 load
- Implement dry-run mode for batch operations
- Add rollback capability

---

## Cost Estimate

**S3 Storage:**
- Current: 119 GB
- Additional: ~500 MB (128 games × 2 endpoints × 2 MB/file)
- Cost impact: +$0.01/month

**Database:**
- Current: 31,241 games in `raw_data.nba_games`
- Additional: 131 games (0.4% increase)
- Impact: Negligible (estimated +10 MB)

**API Calls (if re-scraping needed):**
- ESPN API: Free
- Rate limit: ~10 requests/second
- Estimated time: 4-6 hours for 128 games

**Total Estimated Cost:** < $0.05/month

---

## Timeline

| Phase | Activity | Duration | Dependencies |
|-------|----------|----------|--------------|
| **Phase 1** | Check S3 for 3 missing games | 5 min | None |
| | Load from S3 or re-scrape | 10 min | S3 check complete |
| | Verify completion | 5 min | Load complete |
| **Total Phase 1** | | **20 min** | |
| | | | |
| **Phase 2** | Investigate 2011 game IDs | 30 min | Phase 1 complete |
| | Cross-reference S3 | 30 min | Investigation done |
| | Decision: Load or Document | 15 min | Cross-ref complete |
| | If loading: Batch load | 2-3 hours | Decision made |
| | Verification | 15 min | Load complete |
| **Total Phase 2** | | **4-6 hours** (if loading) | |
| | | **1.5 hours** (if documenting) | |

**Total Project Duration:**
- Best case: 1.5 hours (document 2011 gaps)
- Typical case: 5-7 hours (load available 2011 data)

---

## Recommendations

### Immediate Actions (Today):
1. ✅ **DONE:** Run verification script (`verify_game_coverage.py`)
2. ✅ **DONE:** Analyze gap patterns
3. **NEXT:** Check S3 for 3 single missing games (2015, 2017, 2018)
4. **NEXT:** Load those 3 games (15 min task)

### Short-term (This Week):
1. Investigate 2011 ESPN game ID format discrepancy
2. Check S3 for `400XXXXXX` format files from 2011
3. Make go/no-go decision on 2011 bulk load

### Long-term (Optional):
1. Document known data limitations in `DATA_QUALITY_BASELINE.md`
2. Add automated coverage verification to DIMS (weekly check)
3. Create alerting for future data gaps

---

## Questions for User

1. **2011 Season Priority:** Given that 2011 is 13 years old and 2012+ seasons are complete, should we:
   - A) Invest 4-6 hours to recover 2011 data (if available)?
   - B) Document as known limitation and proceed with 2012+ data?

2. **Single Game Loads:** Should I proceed immediately with loading the 3 missing games (2015, 2017, 2018)?
   - This is a low-risk, 15-minute task

3. **Automation:** Should I add coverage verification to the autonomous DIMS monitoring system?
   - Would run weekly, alert on new gaps

---

## Files Generated

1. **Verification Script:** `scripts/validation/verify_game_coverage.py`
2. **Gap Report:** `game_coverage_report_20251107_122209.json`
3. **This Plan:** `GAME_COVERAGE_REMEDIATION_PLAN.md`
4. **Log File:** `game_coverage_verification.log`

---

**Next Step:** Await user decision on priorities, then execute Phase 1 (quick wins).
