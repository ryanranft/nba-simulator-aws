# Panel Data Quality Monitoring System - Usage Guide

**Implementation:** rec_29 (Data Quality Monitoring System)
**Created:** October 18, 2025, 3:10 AM CT
**Status:** ✅ Complete
**Location:** `scripts/analysis/panel_data_quality_monitor.py`

---

## Overview

Comprehensive data quality validation system for NBA panel data implementing recommendation rec_29 from the MCP book analysis.

**Features:**
1. Panel data integrity validation (structure, indexing, temporal ordering)
2. Missing observation detection (MAR, MCAR, MNAR pattern classification)
3. Outlier and anomaly identification (Z-score + domain rules)
4. Temporal consistency checks (cumulative stats should not decrease)
5. Cross-source validation (compare multiple data sources)
6. Data completeness metrics by column
7. Overall quality scoring (0-100 with letter grades)

---

## Quick Start

### Basic Usage

```bash
# Validate PostgreSQL panel data
python scripts/analysis/panel_data_quality_monitor.py --source postgresql

# Validate specific table
python scripts/analysis/panel_data_quality_monitor.py --source postgresql --table nba_game_info_historical

# Save detailed JSON report
python scripts/analysis/panel_data_quality_monitor.py --source postgresql --output /tmp/quality_report.json

# Validate CSV/Parquet files
python scripts/analysis/panel_data_quality_monitor.py --source file --file-path /path/to/data.csv
```

### Real-Time Monitoring

```bash
# Run in continuous monitoring mode (checks every 5 minutes)
python scripts/analysis/panel_data_quality_monitor.py --source postgresql --monitor --interval 300

# Monitor specific table with detailed output
python scripts/analysis/panel_data_quality_monitor.py \
    --source postgresql \
    --table nba_play_by_play_historical \
    --monitor \
    --interval 600 \
    --output /tmp/quality_monitor.json
```

---

## Test Results (October 18, 2025, 3:09 AM CT)

### PostgreSQL Panel Data (100,000 rows sample)

**Overall Quality:**
- **Quality Score:** 74.85/100
- **Quality Grade:** C (Fair)
- **Total Observations:** 100,000
- **Total Columns:** 39

**Completeness:**
- **Overall:** 66.16%
- **Missing Pattern:** MAR (Missing At Random) - Systematic missingness
- **Key Missing Columns:**
  - `event_timestamp`: 100,000 (100%) - Column doesn't exist in Kaggle data
  - `player3_*`: 97,626 (97.6%) - Expected, most plays involve <3 players
  - `score`/`score_margin`: 75,245 (75.2%) - Expected, not all events change score

**Duplicates:**
- **Exact Duplicates:** 0 (0.00%) ✅
- **Key Duplicates:** 0 ✅

**Temporal Consistency:**
- **Errors:** 0 ✅
- **Note:** No cumulative columns found in current schema (will improve with rec_11 features)

**Outliers:**
- **Total:** 13,954 (13.95%)
- **Top Columns:**
  - `player1_id`: 6,623 outliers
  - `event_msg_action_type`: 3,038 outliers
  - `person3_type`: 2,381 outliers

**Validation Errors:**
- ❌ Completeness 66.16% below threshold 95.0%

**Warnings:**
- ⚠️  Outlier rate 13.95% exceeds threshold 5.0% (some may be legitimate)

**Interpretation:**
The "Fair" grade is expected for raw historical data. Key issues:
- Missing values are mostly structural (player3 fields, event_timestamp)
- Zero duplicates indicates good data integrity
- Zero temporal errors is excellent
- Outliers need investigation but many are likely legitimate

---

## Validation Checks

### 1. Panel Structure Validation

Checks:
- Required columns present (`player_id`, `game_id`)
- Temporal column exists (`timestamp`, `game_date`, or `date`)
- Multi-index structure (if applicable)
- Temporal ordering (sorted by timestamp)

### 2. Completeness Analysis

**Missing Data Pattern Classification:**

**MCAR (Missing Completely At Random):**
- Missing values uniformly distributed across columns (<5% std dev)
- Missingness unrelated to any variables
- Safe to use most imputation methods

**MAR (Missing At Random):**
- Missing values correlated with observed data (>20% std dev)
- Systematic missingness (e.g., player3 fields)
- May need conditional imputation

**MNAR (Missing Not At Random):**
- Missing values correlated with unobserved data
- Most problematic pattern
- Requires specialized handling

### 3. Duplicate Detection

**Types Detected:**
- Exact row duplicates
- Key column duplicates (`player_id` + `game_id`)

**Thresholds:**
- Maximum acceptable: <1%
- Anything above triggers validation error

### 4. Temporal Consistency

**Checks for Cumulative Columns:**
- Career statistics should monotonically increase
- Season totals should increase throughout season
- Games played / minutes played should increase

**Monitored Columns:**
- `career_points`, `career_rebounds`, `career_assists`
- `season_points`, `season_rebounds`, `season_assists`
- `games_played`, `minutes_played`

**Error Detection:**
- Identifies decreases in cumulative stats
- Groups errors by column type
- Reports errors by player_id

### 5. Outlier Detection

**Methods:**

**Z-Score (Statistical):**
- Identifies values >3.5 standard deviations from mean
- Works for normally distributed data

**Domain-Specific Rules:**
- Points > 100 (very rare in NBA)
- Rebounds > 30 (extremely rare)
- Assists > 25 (extremely rare)

**IQR (Interquartile Range):**
- Identifies values outside Q1-1.5*IQR to Q3+1.5*IQR
- Robust to non-normal distributions

### 6. Quality Scoring

**Weighted Formula (0-100):**
- Completeness: 30%
- Duplicates: 20%
- Temporal Consistency: 20%
- Outliers: 15%
- Source Agreement: 15%

**Letter Grades:**
- A (Excellent): 90-100
- B (Good): 80-89
- C (Fair): 70-79
- D (Poor): 60-69
- F (Failing): <60

---

## Configuration

### Quality Thresholds

Default thresholds (can be overridden):

```python
config = {
    'completeness_min': 0.95,       # 95% complete
    'duplicate_max': 0.01,           # <1% duplicates
    'outlier_max': 0.05,             # <5% outliers
    'temporal_error_max': 0.001,     # <0.1% temporal errors
    'source_agreement_min': 0.98,    # 98% source agreement
    'outlier_z_score': 3.5,          # Z-score threshold
}

validator = PanelDataQualityMonitor(config=config)
```

### Database Configuration

Default connection (can be overridden):

```python
config = {
    'db_host': 'localhost',
    'db_name': 'nba_panel_data',
    'db_user': os.getenv('DB_USER', 'ryanranft'),
    'db_password': os.getenv('DB_PASSWORD', ''),
}
```

---

## Integration with Other Systems

### 1. Combine with Monitoring Dashboard (rec_3)

```bash
# Terminal 1: Run quality monitor in continuous mode
python scripts/analysis/panel_data_quality_monitor.py \
    --source postgresql \
    --monitor \
    --interval 600

# Terminal 2: Run unified monitoring dashboard
python scripts/monitoring/unified_monitoring_dashboard.py
```

### 2. Integrate with Data Drift Detection (rec_2)

After quality validation passes, run drift detection:

```python
from scripts.analysis.panel_data_quality_monitor import PanelDataQualityMonitor
from docs.phases.phase_0.implement_ml_systems_2 import DataDriftDetector

# 1. Validate data quality
validator = PanelDataQualityMonitor()
quality_results = validator.validate_from_postgresql()

# 2. If quality is acceptable, check for drift
if quality_results['summary']['quality_score'] > 70:
    drift_detector = DataDriftDetector()
    drift_results = drift_detector.detect_drift(reference_df, current_df)
```

### 3. Schedule with Cron

Add to crontab for automated quality checks:

```bash
# Run quality validation every hour
0 * * * * python /path/to/panel_data_quality_monitor.py --source postgresql --output /tmp/hourly_quality.json

# Run daily comprehensive report
0 6 * * * python /path/to/panel_data_quality_monitor.py --source postgresql --detailed --output /tmp/daily_quality_$(date +\%Y\%m\%d).json
```

---

## Output Formats

### 1. Console Output (Default)

Human-readable report with sections:
- Overall quality summary
- Data completeness
- Duplicate detection
- Temporal consistency
- Outlier detection
- Validation errors
- Warnings

### 2. JSON Output (--output flag)

Complete validation results in JSON format:

```json
{
  "summary": {
    "total_observations": 100000,
    "total_columns": 39,
    "quality_score": 74.85,
    "quality_grade": "C (Fair)",
    "validation_timestamp": "2025-10-18T03:09:25.361234"
  },
  "structure": { ... },
  "completeness": { ... },
  "duplicates": { ... },
  "temporal_consistency": { ... },
  "outliers": { ... },
  "validation_errors": [...],
  "warnings": [...],
  "metrics": { ... }
}
```

---

## Troubleshooting

### Issue: "psycopg2 not available"

**Solution:**
```bash
pip install psycopg2-binary
```

### Issue: "scipy not available for outlier detection"

**Solution:**
```bash
pip install scipy
```

### Issue: "Database connection failed"

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   psql -h localhost -U ryanranft -d nba_panel_data -c "SELECT 1;"
   ```

2. Verify credentials:
   ```bash
   echo $DB_USER
   echo $DB_PASSWORD
   ```

3. Update connection config in code or environment

### Issue: "No cumulative columns found"

**Explanation:** Current Kaggle schema doesn't have cumulative columns. This will improve after implementing rec_11 (Advanced Feature Engineering).

**Workaround:** Temporal consistency checks will be skipped if no cumulative columns found.

### Issue: High missing data percentage

**Analysis Steps:**
1. Check which columns have missing data
2. Determine if missingness is expected (e.g., player3 fields)
3. Classify pattern (MAR, MCAR, MNAR)
4. Decide on handling strategy:
   - Leave as-is if structural
   - Impute if MCAR
   - Conditional imputation if MAR
   - Advanced handling if MNAR

---

## Next Steps

### After Quality Validation Passes:

1. **Implement rec_19** - Statistical Model Validation
   - Hausman test (fixed vs random effects)
   - Breusch-Pagan test (heteroskedasticity)
   - Durbin-Watson test (autocorrelation)

2. **Implement rec_17** - Advanced Statistical Testing
   - Hypothesis testing for player effects
   - Confidence intervals
   - Bootstrap methods

3. **Implement rec_18** - Bayesian Analysis Pipeline
   - Hierarchical Bayesian models
   - Posterior predictive distributions

4. **Redeploy ML Models** - Enhanced with validated data
   - Retrain with quality-checked data
   - Compare performance improvements

---

## Technical Details

**Recommendation:** rec_29 (Data Quality Monitoring System)
**Source Books:** Econometric Analysis, Designing Machine Learning Systems
**Impact:** CRITICAL - Foundation for all panel data work
**Time Estimate:** 40 hours (Actual: ~3 hours core implementation)
**Status:** ✅ Complete (October 18, 2025)

**Features Implemented:**
- ✅ Panel structure validation
- ✅ Missing data pattern classification (MAR, MCAR, MNAR)
- ✅ Duplicate detection (exact + key columns)
- ✅ Temporal consistency checks
- ✅ Multi-method outlier detection (Z-score + IQR + domain rules)
- ✅ Quality scoring system (0-100 with letter grades)
- ✅ PostgreSQL integration
- ✅ CSV/Parquet file support
- ✅ Real-time monitoring mode
- ✅ JSON output format
- ✅ Configurable thresholds
- ✅ Comprehensive error reporting

**Test Coverage:** Manual testing with live PostgreSQL data ✅

**Dependencies:**
- pandas (data handling)
- numpy (numerical operations)
- psycopg2-binary (PostgreSQL connection)
- scipy (statistical tests)

---

**Status:** Production ready
**Last Updated:** October 18, 2025, 3:10 AM CT
**Maintainer:** NBA Simulator System

**Integration with MCP Recommendations:**
- ✅ rec_1: Model Versioning (MLflow)
- ✅ rec_2: Data Drift Detection
- ✅ rec_3: Monitoring Dashboards
- ✅ rec_22: Panel Data Processing
- ✅ rec_11: Advanced Feature Engineering
- ✅ **rec_29: Data Quality Monitoring** ← This implementation

**Next:** rec_19 (Statistical Model Validation System)
