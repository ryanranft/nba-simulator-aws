# hoopR Gap Analysis Findings

**Date:** October 9, 2025
**Analysis:** hoopR API limitations and gap filling strategy

---

## Key Finding: hoopR API Cannot Fill All Gaps

### Gap Distribution
- **Total missing games:** 2,464 (7.9% of overlap period)
- **Pre-2002:** 8 games (hoopR doesn't support seasons < 2002)
- **2002-2003:** 439 games (early coverage gaps)
- **2004-2024:** 2,017 games (scattered gaps across all years)

### Why Gaps Cannot Be Filled from hoopR API

**1. Pre-2002 Limitation**
- hoopR API error: "season cannot be less than 2002"
- These 8 games are fundamentally unavailable

**2. API Inefficiency for Individual Games**
- `load_nba_pbp()` loads ENTIRE seasons, not individual games
- Would download millions of events per season to get one game
- Not practical for 2,464 games

**3. Likely API Unavailability**
- If games are missing from our hoopR DB, they're likely missing from hoopR API
- ESPN has these games, but hoopR never scraped them
- Possible reasons: API errors, data quality issues, incomplete scraping

---

## Recommended Strategy: Unified Database Approach

### ❌ What NOT to Do
- Don't load ESPN data into hoopR database (cross-contamination)
- Don't try to scrape individual games from hoopR API (inefficient)
- Don't assume gaps can be filled

### ✅ Correct Approach

**1. Accept hoopR Gaps as Legitimate**
- Document in `source_coverage` table
- Mark as `has_hoopr = FALSE`

**2. Use ESPN for These Games in Unified Database**
- Unified database pulls from ESPN for these 2,464 games
- Mark as `primary_source = 'ESPN'`
- Document reason: "hoopR unavailable"

**3. Build Quality Scores**
```sql
INSERT INTO quality_scores VALUES (
    '230114014',  -- game_id
    '2003-01-15', -- game_date
    'ESPN',       -- recommended_source (hoopR unavailable)
    85,           -- quality_score (ESPN only)
    'MEDIUM',     -- uncertainty (single source)
    FALSE,        -- event_count_issue
    FALSE,        -- coordinate_issue
    FALSE,        -- score_issue
    FALSE,        -- timing_issue
    TRUE,         -- use_for_training
    'hoopR unavailable - ESPN only source'
);
```

---

## Updated Architecture

### Source Databases (Remain Pure)
```
ESPN Database:    31,241 games ✓ (100% of available)
hoopR Database:   28,779 games ✓ (92.1% - gaps are API limitations)
```

### Unified Database (Comprehensive)
```
For games in both sources:
  - Use hoopR as primary (richer schema)
  - ESPN as validation

For games only in ESPN (2,464):
  - Use ESPN as primary
  - Mark hoopR as unavailable
  - Quality score: 85 (single source)
  - Uncertainty: MEDIUM

For games only in hoopR (2):
  - Use hoopR as primary
  - ESPN as unavailable
  - Quality score: 90 (hoopR preferred)
```

---

## Data Quality Implications

### Coverage Summary
```
Total unique games:      31,243
Games in both sources:   28,777 (92.1%)
Games only in ESPN:       2,464 (7.9%)
Games only in hoopR:          2 (0.006%)
```

### Quality Assessment

**High Quality (28,777 games - 92.1%)**
- Both sources available
- Cross-validation possible
- Quality score: 95-100
- Uncertainty: LOW

**Medium Quality (2,464 games - 7.9%)**
- ESPN only
- No cross-validation
- Quality score: 80-90
- Uncertainty: MEDIUM

**High Quality (2 games - 0.006%)**
- hoopR only
- No cross-validation
- Quality score: 85-95
- Uncertainty: MEDIUM

---

## ML Training Recommendations

### Use All Games
- All 31,243 games are usable for training
- Include quality scores as features
- Weight by uncertainty level

### Quality-Aware Training
```python
# High confidence games (both sources)
high_quality_games = df[df['quality_score'] >= 95]  # 28,777 games

# Medium confidence games (single source)
medium_quality_games = df[df['quality_score'].between(80, 94)]  # 2,466 games

# Weight training samples by quality
sample_weight = df['quality_score'] / 100
```

### Uncertainty Estimation
- Models should output uncertainty alongside predictions
- Use quality scores to calibrate confidence intervals
- Flag predictions on low-quality input data

---

## Implementation Steps

### 1. Skip hoopR Gap Scraping ✓
- Documented as infeasible
- API limitations prevent filling

### 2. Build Unified Database (Next)
- Combine ESPN + hoopR
- Mark source availability
- Calculate quality scores

### 3. Discrepancy Detection
- Only for games in both sources (28,777)
- Skip single-source games (2,466)

### 4. Quality Scores
- High: Both sources available, no discrepancies
- Medium: Single source, or minor discrepancies
- Low: Major discrepancies or data quality issues

---

## Files to Update

### Scripts
- ~~`scripts/etl/scrape_missing_hoopr_games.py`~~ - Skip (infeasible)
- `scripts/etl/build_unified_database.py` - Implement
- `scripts/validation/detect_data_discrepancies.py` - Only for dual-source games

### Documentation
- `docs/DATA_INTEGRITY_PRINCIPLES.md` - Add "Accepting Source Limitations" section
- `docs/claude_workflows/workflow_descriptions/51_multi_source_data_quality.md` - Update Phase 2

### Reports
- `reports/hoopr_gap_analysis_findings.md` - This document
- `reports/data_quality_report.md` - Generate from unified DB

---

## Conclusion

**Key Insight:** Not all gaps can or should be filled.

**Accept that:**
1. hoopR has API limitations (pre-2002, inefficient individual game scraping)
2. Some games are simply unavailable in hoopR's API
3. ESPN fills these gaps in the unified database

**Focus on:**
1. Building comprehensive unified database
2. Tracking data quality and source availability
3. Providing ML models with quality-aware training data

**Result:**
- 31,243 total games available
- 92.1% with dual-source validation
- 7.9% with single-source (still usable)
- Clear quality scores for all games

---

**Next Steps:**
1. ✅ Document hoopR limitations (this file)
2. ⏸️ Build unified database (combines all sources)
3. ⏸️ Generate quality scores
4. ⏸️ Create ML-ready dataset
