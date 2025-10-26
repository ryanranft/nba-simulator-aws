# Workflow #35: Pre-Deployment Testing

**Category:** Testing & Quality
**Priority:** High
**When to Use:** Before deploying any new AWS phase or running production ETL
**Related Workflows:** #16 (Testing), #27 (TDD), #21 (Data Validation)

---

## Overview

This workflow provides phase-specific testing checklists to run before deploying to AWS. Use this to catch errors locally before incurring AWS costs or creating bad data in production databases.

**Purpose:** Prevent costly deployment errors through systematic pre-deployment validation.

---

## When to Use This Workflow

✅ **USE before:**
- Running full ETL on 146K+ files (Phase 2)
- Deploying to RDS production database (Phase 3)
- Launching EC2 simulation engine (Phase 4)
- Starting SageMaker ML training (Phase 5)
- Any production deployment that costs money

❌ **DON'T NEED when:**
- Running local development tests
- Working on exploratory notebooks
- Making trivial code changes
- Already completed this phase successfully

---

## General Pre-Deployment Checklist

**Run before ANY AWS deployment:**

### 1. Local Environment Validation
```bash
# Check system health
bash scripts/shell/check_machine_health.sh

# Verify all checks pass
# Expected: All ✅ green checkmarks
```

### 2. Code Quality Checks
```bash
# Run all unit tests
pytest

# Check test coverage
pytest --cov=scripts --cov-report=term-missing

# Minimum coverage: 70% for critical ETL/simulation code
```

### 3. Data Sample Testing
```bash
# Test with small sample FIRST (10-100 files)
# Never jump straight to full dataset
```

### 4. Cost Estimate
```bash
# Estimate costs for this phase
# See workflow #18 (Cost Management)

# Get user approval if >$10/month
```

### 5. Backup Critical Data
```bash
# Before any destructive operation
# See workflow #19 (Backup & Recovery)
```

---

## Phase 2: Pre-ETL Testing

**Before running Glue ETL on full dataset (146K files)**

### Phase 2.1: Sample Data Validation

#### Test 1: Process 10 Sample Files
```python
# scripts/tests/test_etl_sample.py
import json
from scripts.etl.field_mapping import extract_player_stats

def test_etl_with_10_files():
    """Test ETL logic with 10 sample files"""
    sample_files = [
        "data/nba_pbp/401307856.json",  # Known valid file
        "data/nba_pbp/131105001.json",  # Known empty file
        # ... 8 more diverse samples
    ]

    results = []
    errors = []

    for file in sample_files:
        try:
            with open(file) as f:
                data = json.load(f)

            # Extract data
            extracted = extract_player_stats(data)
            results.append(extracted)
        except Exception as e:
            errors.append((file, str(e)))

    # Assertions
    assert len(results) > 0, "No files processed successfully"
    assert len(errors) < len(sample_files), "Too many errors"

    # Log results
    print(f"Processed: {len(results)}/{len(sample_files)}")
    print(f"Errors: {len(errors)}")
    for file, error in errors:
        print(f"  {file}: {error}")
```

**Run test:**
```bash
pytest scripts/tests/test_etl_sample.py -v
```

**Success criteria:**
- [ ] At least 70% of sample files process successfully
- [ ] Known valid files extract expected data
- [ ] Known empty files handled gracefully (no crashes)
- [ ] Error messages are clear and actionable

#### Test 2: Data Quality Validation
```python
def test_extracted_data_quality():
    """Validate data quality of extracted records"""
    # Sample extraction
    with open("data/nba_pbp/401307856.json") as f:
        data = json.load(f)

    result = extract_player_stats(data)

    # Data quality checks
    assert result["player_id"] is not None, "Player ID required"
    assert isinstance(result["points"], (int, type(None))), "Points must be int or None"
    assert result["points"] is None or result["points"] >= 0, "Points must be non-negative"
    assert result["player_name"] and len(result["player_name"]) > 0, "Player name required"
```

### Phase 2.2: Schema Compliance

**Test 3: Database Schema Validation**
```python
def test_schema_compliance():
    """Ensure extracted data matches RDS schema"""
    # Extract sample data
    with open("data/nba_pbp/401307856.json") as f:
        data = json.load(f)

    result = extract_player_stats(data)

    # Expected schema (from scripts/sql/schema.sql)
    required_fields = ["player_id", "player_name", "points", "rebounds", "assists"]

    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

    # Data types
    assert isinstance(result["player_id"], str), "player_id must be string"
    assert isinstance(result["player_name"], str), "player_name must be string"
    assert isinstance(result["points"], (int, type(None))), "points must be int or None"
```

### Phase 2.3: Pre-Full Run Checklist

**Before running ETL on 146K files:**

- [ ] **Sample tests pass** (10 files, then 100 files)
- [ ] **Data quality validated** (no null required fields, valid ranges)
- [ ] **Schema compliance verified** (matches RDS table structure)
- [ ] **Error handling tested** (malformed JSON, missing fields, empty files)
- [ ] **Performance estimated** (extrapolate from sample runtime)
- [ ] **Cost approved** (~$13/month for monthly Glue runs)
- [ ] **RDS connection tested** (can write sample data to database)
- [ ] **Rollback plan ready** (can restore RDS from snapshot if needed)

**Commands to run:**
```bash
# Test with 10 files
pytest scripts/tests/test_etl_sample.py -v

# Test with 100 files
python scripts/etl/test_etl_100_files.py

# Test RDS connection
python scripts/tests/test_rds_connection.py

# Estimate costs
bash scripts/aws/check_costs.sh
```

---

## Phase 3: Pre-RDS Deployment Testing

**Before deploying RDS PostgreSQL database**

### Phase 3.1: Local Database Testing

#### Test 1: Schema Creation
```bash
# Test schema SQL locally (if you have local PostgreSQL)
psql -U postgres -d test_nba -f scripts/sql/schema.sql

# Verify tables created
psql -U postgres -d test_nba -c "\dt"

# Expected: games, player_stats, teams tables
```

#### Test 2: Sample Data Load
```python
# scripts/tests/test_database_load.py
import psycopg2
import os

def test_load_sample_data_to_rds():
    """Test loading sample data to RDS"""
    # Connect to RDS
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    cursor = conn.cursor()

    # Insert sample game
    cursor.execute("""
        INSERT INTO games (game_id, season, game_date, home_team, away_team, home_score, away_score)
        VALUES ('TEST001', 2024, '2024-01-01', 'LAL', 'GSW', 100, 95)
        ON CONFLICT (game_id) DO NOTHING
    """)

    conn.commit()

    # Verify inserted
    cursor.execute("SELECT * FROM games WHERE game_id = 'TEST001'")
    result = cursor.fetchone()

    assert result is not None, "Sample game not inserted"
    assert result[5] == 100, "Home score incorrect"

    # Cleanup
    cursor.execute("DELETE FROM games WHERE game_id = 'TEST001'")
    conn.commit()

    cursor.close()
    conn.close()
```

### Phase 3.2: Pre-Production Deployment Checklist

**Before creating RDS instance:**

- [ ] **Cost approved** (~$29/month for db.t3.small)
- [ ] **Region selected** (us-east-1)
- [ ] **PostgreSQL version checked** (15.14 available, not 16.x)
- [ ] **Password valid** (no @ / " / space characters)
- [ ] **Security group planned** (allow port 5432 from your IP)
- [ ] **Backup retention set** (7 days minimum)
- [ ] **Schema SQL tested** (locally or dry-run)
- [ ] **Connection tested** (from local machine with test credentials)

**Commands to run:**
```bash
# Check PostgreSQL versions available
aws rds describe-db-engine-versions \
  --engine postgres \
  --query 'DBEngineVersions[*].EngineVersion' \
  --output table

# Estimate costs
echo "RDS db.t3.small: ~$29/month"
echo "20 GB storage: ~$2.30/month"
echo "Total: ~$31/month"

# Test schema locally (if PostgreSQL installed)
psql -U postgres -f scripts/sql/schema.sql
```

---

## Phase 4: Pre-EC2 Simulation Deployment

**Before launching EC2 instance for game simulation**

### Phase 4.1: Local Simulation Testing

#### Test 1: Run 10 Test Simulations
```python
# scripts/tests/test_simulation.py
from scripts.simulation.game_simulator import simulate_game

def test_simulation_basic():
    """Test basic game simulation"""
    # Sample teams
    home_team = "LAL"
    away_team = "GSW"

    # Run simulation
    result = simulate_game(home_team, away_team, season=2024)

    # Validate output
    assert "home_score" in result
    assert "away_score" in result
    assert result["home_score"] >= 0
    assert result["away_score"] >= 0
    assert result["home_score"] < 200  # Realistic NBA score
    assert result["away_score"] < 200

    print(f"Simulation result: {home_team} {result['home_score']} - {away_team} {result['away_score']}")
```

#### Test 2: Validate Realistic Scores
```python
def test_simulation_score_distribution():
    """Verify simulated scores are realistic"""
    # Run 100 simulations
    scores = []
    for _ in range(100):
        result = simulate_game("LAL", "GSW", season=2024)
        scores.append((result["home_score"], result["away_score"]))

    # Calculate average
    avg_home = sum(s[0] for s in scores) / len(scores)
    avg_away = sum(s[1] for s in scores) / len(scores)

    # NBA average is ~110 points per team
    assert 90 <= avg_home <= 130, f"Home average {avg_home} unrealistic"
    assert 90 <= avg_away <= 130, f"Away average {avg_away} unrealistic"

    # Check variance (not all same score)
    unique_scores = len(set(scores))
    assert unique_scores > 50, "Too little variance in simulation"
```

### Phase 4.2: Pre-EC2 Launch Checklist

**Before launching EC2 instance:**

- [ ] **Local simulation tested** (10+ test games)
- [ ] **Scores realistic** (90-130 range, reasonable variance)
- [ ] **No crashes** (handles edge cases gracefully)
- [ ] **Output format validated** (matches expected schema)
- [ ] **Different matchups tested** (various team combinations)
- [ ] **Instance type selected** (t2.micro for testing, t2.small for production)
- [ ] **Cost approved** (~$8-15/month depending on instance type)
- [ ] **Security group configured** (SSH port 22 from your IP only)
- [ ] **Key pair created** (for SSH access)

**Commands to run:**
```bash
# Run simulation tests
pytest scripts/tests/test_simulation.py -v

# Test different matchups
python scripts/simulation/test_matchups.py

# Estimate EC2 costs
echo "t2.micro: ~$8/month (testing)"
echo "t2.small: ~$15/month (production)"
```

---

## Phase 5: Pre-ML Training Testing

**Before running SageMaker ML training**

### Phase 5.0001: Feature Engineering Validation

#### Test 1: Feature Data Quality
```python
# scripts/tests/test_ml_features.py
import pandas as pd
from scripts.ml.feature_engineering import create_features

def test_feature_quality():
    """Validate ML feature engineering produces clean data"""
    # Load sample games
    sample_data = pd.read_csv("data/sample_games.csv")

    # Create features
    features = create_features(sample_data)

    # Data quality checks
    assert features.isnull().sum().sum() == 0, "Features contain null values"
    assert not features.isin([float('inf'), float('-inf')]).any().any(), "Features contain infinite values"
    assert features.shape[0] > 0, "No features generated"
    assert features.shape[1] >= 10, "Too few features"

    print(f"Generated {features.shape[1]} features for {features.shape[0]} samples")
```

#### Test 2: Training Data Size
```python
def test_training_data_sufficient():
    """Ensure enough data for ML training"""
    # Query RDS for available data
    import psycopg2
    import os

    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM games")
    game_count = cursor.fetchone()[0]

    # Minimum data requirements
    assert game_count >= 1000, f"Only {game_count} games, need 1000+ for training"

    # Recommended: 10K+ games for good model
    if game_count < 10000:
        print(f"⚠️ Warning: Only {game_count} games. Recommended: 10,000+ for best results")

    cursor.close()
    conn.close()
```

### Phase 5.0002: Model Training Test

#### Test 3: Sample Model Training
```python
# scripts/tests/test_ml_training.py
from scripts.ml.train_model import train_basic_model
import pandas as pd

def test_model_training_smoke_test():
    """Test that model can train on sample data"""
    # Load sample features
    features = pd.read_csv("data/sample_features.csv")
    labels = pd.read_csv("data/sample_labels.csv")

    # Train model on small sample
    model = train_basic_model(features, labels, max_iter=10)

    # Verify model exists
    assert model is not None, "Model training failed"

    # Test prediction
    sample_input = features.iloc[0:1]
    prediction = model.predict(sample_input)

    assert prediction is not None, "Model prediction failed"
    assert len(prediction) == 1, "Unexpected prediction shape"

    print(f"Model trained successfully, sample prediction: {prediction[0]}")
```

### Phase 5.0003: Pre-SageMaker Launch Checklist

**Before starting SageMaker training:**

- [ ] **Feature engineering tested** (no null/infinite values)
- [ ] **Training data validated** (1000+ games minimum, 10K+ recommended)
- [ ] **Sample model trained locally** (smoke test passes)
- [ ] **Model predictions work** (can make predictions on new data)
- [ ] **Input data size known** (estimate SageMaker training time)
- [ ] **Instance type selected** (ml.t3.medium for testing, ml.m5.xlarge for production)
- [ ] **Cost approved** (~$40-60/month for notebook + training)
- [ ] **Model evaluation metrics defined** (accuracy, precision, recall, F1)
- [ ] **Baseline model created** (for comparison)

**Commands to run:**
```bash
# Run ML tests
pytest scripts/tests/test_ml_features.py -v
pytest scripts/tests/test_ml_training.py -v

# Check data size
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM games"

# Estimate costs
echo "SageMaker ml.t3.medium notebook: ~$40/month"
echo "Training jobs: ~$0.05/hour (ml.m5.xlarge)"
echo "Total: ~$50-60/month"
```

---

## Master Pre-Deployment Checklist

**Use this comprehensive checklist before ANY production deployment:**

### 1. Planning & Approval
- [ ] Phase requirements documented in PROGRESS.md
- [ ] Cost estimate calculated (workflow #18)
- [ ] User approval obtained for costs
- [ ] Timeline estimated
- [ ] Rollback plan documented

### 2. Environment & Dependencies
- [ ] Conda environment verified (check_machine_health.sh)
- [ ] AWS credentials valid (aws sts get-caller-identity)
- [ ] All Python packages installed (pip list)
- [ ] System health check passes (all ✅)

### 3. Code Quality
- [ ] All unit tests pass (pytest)
- [ ] Test coverage >70% for critical code
- [ ] No known bugs or errors
- [ ] Code reviewed (or ADR documented for decisions)

### 4. Data Validation
- [ ] Sample data tested (10 files minimum)
- [ ] Data quality validated (no nulls in required fields)
- [ ] Schema compliance verified
- [ ] Edge cases handled (empty files, malformed data)

### 5. Integration Testing
- [ ] Local testing complete
- [ ] Sample AWS deployment tested (if applicable)
- [ ] Database connections verified
- [ ] API endpoints tested

### 6. Security & Backup
- [ ] No credentials in code (security scan passed)
- [ ] Backup created before destructive operations
- [ ] Archive conversation (if at 75%+ context)
- [ ] Sensitive files gitignored

### 7. Documentation
- [ ] PROGRESS.md updated with current phase status
- [ ] README.md reflects current architecture
- [ ] New workflows documented (if process changed)
- [ ] Lessons learned captured (if issues encountered)

### 8. Final Checks
- [ ] Reviewed LESSONS_LEARNED.md for this phase (workflow #34)
- [ ] Double-checked phase prerequisites
- [ ] User explicitly approves deployment
- [ ] Ready to monitor deployment for errors

---

## Common Testing Mistakes to Avoid

### ❌ Mistake 1: Skipping Sample Testing

**Bad:**
```bash
# Jump straight to full dataset
aws glue start-job-run --job-name etl-job --arguments '{"--input":"s3://bucket/all-data/"}'
```

**Good:**
```bash
# Test with small sample first
python scripts/etl/test_sample.py --files 10
python scripts/etl/test_sample.py --files 100
# THEN run full dataset
```

### ❌ Mistake 2: Not Validating Data Quality

**Bad:**
```python
# Just check if it runs
def test_etl():
    run_etl(sample_files)
    # No assertions!
```

**Good:**
```python
def test_etl_data_quality():
    run_etl(sample_files)

    # Validate output
    df = pd.read_sql("SELECT * FROM games", conn)
    assert df.shape[0] > 0, "No data loaded"
    assert df["home_score"].isnull().sum() == 0, "Null scores found"
    assert (df["home_score"] >= 0).all(), "Negative scores found"
```

### ❌ Mistake 3: Ignoring Edge Cases

**Bad:**
```python
# Only test happy path
test_data = load_valid_sample()
```

**Good:**
```python
# Test edge cases
test_valid_data()
test_empty_files()
test_malformed_json()
test_missing_fields()
test_extreme_values()
```

---

## Integration with Other Workflows

**Before deployment:**
1. Read PROGRESS.md for phase requirements
2. Check LESSONS_LEARNED.md for known issues (workflow #34)
3. Review cost estimates (workflow #18)
4. **Run this pre-deployment checklist** (workflow #35)
5. Get user approval for deployment

**After successful deployment:**
1. Update PROGRESS.md phase status to ✅ COMPLETE
2. Document in COMMAND_LOG.md (workflow #2)
3. Archive conversation if needed (workflow #9)
4. Commit changes (workflow #8)

**If deployment fails:**
1. Document error in TROUBLESHOOTING.md (workflow #22)
2. Add to LESSONS_LEARNED.md (workflow #34)
3. Rollback using backup (workflow #19)
4. Fix issues and re-run this checklist

---

## Resources

**Testing Tools:**
```bash
pip install pytest pytest-cov pytest-mock moto
```

**Related Documentation:**
- `docs/TESTING.md` - Complete testing strategy
- Workflow #16 - General testing workflow
- Workflow #27 - TDD workflow
- Workflow #21 - Data validation workflow
- Workflow #34 - Lessons learned review

**Pre-Deployment Scripts:**
```bash
bash scripts/shell/check_machine_health.sh  # System verification
pytest                                       # Run all tests
pytest --cov=scripts                        # Coverage report
python scripts/aws/check_costs.sh           # Cost check
```

---

**Last Updated:** 2025-10-02
**Source:** docs/TESTING.md (lines 617-641)