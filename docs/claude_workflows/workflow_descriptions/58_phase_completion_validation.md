# Workflow #58: Phase Completion & Validation

**Version:** 1.0
**Created:** October 23, 2025
**Purpose:** Unified end-to-end workflow for completing and validating any phase or sub-phase
**Trigger:** When any phase/sub-phase is ready for completion validation
**Frequency:** Per phase/sub-phase completion

---

## Overview

This workflow consolidates the complete process for validating and marking a phase as complete. It combines test generation, validation execution, README alignment, DIMS integration, and phase index management into a single streamlined workflow.

**Replaces workflows:**
- #52 (Phase Index Management) - Now Phase 7 of this workflow
- #53 (Phase Test & Validator Organization) - Now Phase 3 of this workflow
- #57 (Phase-README Alignment) - Now Phase 5 of this workflow

**References workflow:**
- #56 (DIMS Management) - Used in Phase 6, but also standalone

---

## When to Use This Workflow

**Use when:**
- Any phase or sub-phase is complete and ready for validation
- Moving from ⏸️ PENDING → ✅ COMPLETE
- Need to generate tests/validators for a new phase
- Validating README accuracy before marking phase complete

**Don't use when:**
- Making minor edits to existing phase documentation
- Phase is still in progress (🔄 IN PROGRESS)
- Just running existing tests (use Workflow #16 or #41 instead)

---

## 8-Phase Completion Process

### Phase 1: Read & Analyze

**Purpose:** Understand what the phase accomplished and what needs validation

#### Step 1.1: Read Phase README

```bash
# Example: Validating Phase 0.0002 (4-digit format per ADR-010)
cat docs/phases/phase_0/0.0002_hoopr_data_collection/README.md
```

**What to look for:**
- Data collected (S3 files, RDS tables, local data)
- Infrastructure created (buckets, databases, scripts)
- Key achievements and metrics
- Expected outcomes

#### Step 1.2: Identify Validation Requirements

**Common validation types:**

| Phase Type | Validation Needed |
|------------|-------------------|
| **Data Collection** | S3 file counts, bucket configuration, upload completeness |
| **Database** | RDS table existence, row counts, schema validation |
| **ETL** | Pipeline execution, data transformations, output quality |
| **ML Model** | Model performance, feature engineering, predictions |
| **Infrastructure** | AWS resources exist, configurations correct, costs within budget |

#### Step 1.3: Determine Required Tests

**Decision tree:**

```
Phase collected S3 data?
  → Need S3BucketConfigValidator
  → Need S3UploadCompletenessValidator

Phase created RDS tables?
  → Need DatabaseSchemaValidator
  → Need TableRowCountValidator

Phase created scripts?
  → Need ScriptExecutionValidator
  → Need OutputFormatValidator
```

---

### Phase 2: Generate Tests & Validators

**Purpose:** Write actual test and validator code (THE MISSING PIECE!)

#### Step 2.1: Generate Validator Template

**File:** `validators/phases/phase_N/validate_N_M_feature.py`

**Template:**

```python
#!/usr/bin/env python3
"""
Validate Phase N.M: [Feature Name]

Description: [What this validator checks]

Usage:
    python validators/phases/phase_N/validate_N_M_feature.py
    python validators/phases/phase_N/validate_N_M_feature.py --verbose
"""

import sys
import boto3
from typing import List, Tuple, Dict
from pathlib import Path

class PhaseNMFeatureValidator:
    """Validates [feature] for Phase N.M."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.failures: List[str] = []
        self.warnings: List[str] = []

        # Initialize AWS clients if needed
        # self.s3 = boto3.client('s3')
        # self.rds = boto3.client('rds')

    def validate_feature_1(self) -> bool:
        """Validate first feature."""
        try:
            # TODO: Add validation logic based on phase requirements
            # Example: Check S3 file count
            # response = self.s3.list_objects_v2(Bucket='bucket-name', Prefix='prefix/')
            # file_count = response.get('KeyCount', 0)
            # expected_count = 100
            # if file_count != expected_count:
            #     self.failures.append(f"Expected {expected_count} files, found {file_count}")
            #     return False

            if self.verbose:
                print("✓ Feature 1 validation passed")
            return True

        except Exception as e:
            self.failures.append(f"Feature 1 validation failed: {e}")
            return False

    def validate_feature_2(self) -> bool:
        """Validate second feature."""
        try:
            # TODO: Add validation logic
            if self.verbose:
                print("✓ Feature 2 validation passed")
            return True

        except Exception as e:
            self.failures.append(f"Feature 2 validation failed: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validations and return results."""
        print(f"\n{'='*60}")
        print(f"Phase N.M: [Feature Name] Validation")
        print(f"{'='*60}\n")

        results = {
            'feature_1_valid': self.validate_feature_1(),
            'feature_2_valid': self.validate_feature_2(),
        }

        all_passed = all(results.values())

        print(f"\n{'='*60}")
        print(f"Results Summary")
        print(f"{'='*60}")

        for check, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{check:40} {status}")

        if self.failures:
            print(f"\n❌ Failures:")
            for failure in self.failures:
                print(f"  - {failure}")

        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print(f"\n{'='*60}")
        if all_passed:
            print("✅ All validations passed!")
        else:
            print("❌ Some validations failed. See details above.")
        print(f"{'='*60}\n")

        return all_passed, results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate Phase N.MMMM [feature] (4-digit format per ADR-010)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    validator = PhaseNMFeatureValidator(verbose=args.verbose)
    all_passed, results = validator.run_all_validations()

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
```

#### Step 2.2: Generate Test Template

**File:** `tests/phases/phase_N/test_N_M_name.py`

**Template:**

```python
"""
Tests for Phase N.M: [Phase Name]

This test suite validates the completion of Phase N.MMMM (4-digit format per ADR-010) by checking:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Usage:
    pytest tests/phases/phase_N/test_N_M_name.py -v
    pytest tests/phases/phase_N/test_N_M_name.py -v -m "not slow"
"""

import pytest
import sys
from pathlib import Path

# Import validators from new location
validators_path = Path(__file__).parent.parent.parent.parent / "validators" / "phases" / f"phase_{N}"
sys.path.insert(0, str(validators_path))

from validate_N_M_feature import PhaseNMFeatureValidator


class TestPhaseNMFeatureValidation:
    """Tests for Phase N.MMMM feature validation (4-digit format per ADR-010)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return PhaseNMFeatureValidator(verbose=False)

    def test_feature_1_validation(self, validator):
        """Test feature 1 validation."""
        assert validator.validate_feature_1() == True, \
            f"Feature 1 validation failed: {validator.failures}"

    def test_feature_2_validation(self, validator):
        """Test feature 2 validation."""
        assert validator.validate_feature_2() == True, \
            f"Feature 2 validation failed: {validator.failures}"

    def test_all_validations(self, validator):
        """Test all validations pass."""
        all_passed, results = validator.run_all_validations()
        assert all_passed == True, \
            f"Not all validations passed. Results: {results}"


class TestPhaseNMIntegration:
    """Integration tests for Phase N.M."""

    def test_phase_complete_validation(self):
        """Comprehensive test that Phase N.MMMM (4-digit format per ADR-010) is complete."""
        validator = PhaseNMFeatureValidator(verbose=False)
        all_passed, results = validator.run_all_validations()

        assert all_passed == True, \
            "Phase N.MMMM completion validation failed"

        # Check specific results
        assert results['feature_1_valid'] == True
        assert results['feature_2_valid'] == True


class TestPhaseNMMetadata:
    """Tests for Phase N.MMMM documentation metadata (4-digit format per ADR-010)."""

    def test_documented_metrics_match_actual(self):
        """Verify documented metrics match actual state."""
        # TODO: Read phase README
        # TODO: Extract documented file counts, table counts, etc.
        # TODO: Compare to actual values from validators
        # Example:
        # readme_path = Path("docs/phases/phase_N/N.MMMM_name/README.md")
        # readme_content = readme_path.read_text()
        # # Extract metrics and compare
        pass
```

#### Step 2.3: Write Actual Validation Logic

**Based on phase requirements, add specific checks:**

**Example - S3 Data Collection:**
```python
def validate_s3_bucket_exists(self) -> bool:
    """Verify S3 bucket exists and is accessible."""
    try:
        self.s3.head_bucket(Bucket='nba-sim-raw-data-lake')
        return True
    except:
        self.failures.append("S3 bucket does not exist or is not accessible")
        return False

def validate_file_count(self) -> bool:
    """Verify expected number of files uploaded."""
    response = self.s3.list_objects_v2(
        Bucket='nba-sim-raw-data-lake',
        Prefix='hoopr_phase1/'
    )
    actual_count = response.get('KeyCount', 0)
    expected_count = 410

    if actual_count < expected_count:
        self.failures.append(f"Expected >= {expected_count} files, found {actual_count}")
        return False
    return True
```

**Example - RDS Database:**
```python
def validate_table_exists(self, table_name: str) -> bool:
    """Verify RDS table exists."""
    import psycopg2
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = %s
        );
    """, (table_name,))
    exists = cursor.fetchone()[0]

    if not exists:
        self.failures.append(f"Table {table_name} does not exist")
    return exists
```

---

### Phase 3: Organization & Deployment

**Purpose:** Ensure tests/validators are in correct directories with proper structure

#### Step 3.1: Verify Directory Structure

```bash
# Check tests directory
ls -la tests/phases/phase_N/

# Should contain:
# - conftest.py (shared fixtures)
# - test_N_M_name.py (your new test file)

# Check validators directory
ls -la validators/phases/phase_N/

# Should contain:
# - validate_N_M_feature.py (your new validator)
```

#### Step 3.2: Create conftest.py if Needed

**File:** `tests/phases/phase_N/conftest.py`

```python
"""
Shared fixtures for Phase N tests.
"""

import pytest
import boto3
import os


@pytest.fixture(scope="module")
def s3_client():
    """Provide S3 client for tests."""
    return boto3.client('s3')


@pytest.fixture(scope="module")
def bucket_name():
    """Provide S3 bucket name."""
    return os.getenv('S3_BUCKET', 'nba-sim-raw-data-lake')


@pytest.fixture(scope="module")
def rds_connection():
    """Provide RDS database connection."""
    import psycopg2
    return psycopg2.connect(
        host=os.getenv('RDS_HOST'),
        database=os.getenv('RDS_DATABASE'),
        user=os.getenv('RDS_USER'),
        password=os.getenv('RDS_PASSWORD')
    )
```

#### Step 3.3: Update Imports and Paths

**Verify imports work:**

```bash
# From test file, can you import validator?
python -c "import sys; sys.path.insert(0, 'validators/phases/phase_N'); from validate_N_M_feature import PhaseNMFeatureValidator; print('✓ Import successful')"
```

---

### Phase 4: Run Validations

**Purpose:** Execute tests and validators to verify phase completion

#### Step 4.1: Deploy Validator Individually

```bash
# Run standalone validator
python validators/phases/phase_N/validate_N_M_feature.py

# Expected output:
# ============================================================
# Phase N.M: [Feature] Validation
# ============================================================
#
# ✓ Feature 1 validation passed
# ✓ Feature 2 validation passed
#
# ============================================================
# Results Summary
# ============================================================
# feature_1_valid                           ✓ PASS
# feature_2_valid                           ✓ PASS
#
# ============================================================
# ✅ All validations passed!
# ============================================================
```

**If validation fails:**
- Read failure messages
- Fix underlying issues (missing data, incorrect config, etc.)
- Re-run validator
- Do NOT proceed to next step until 100% pass rate

#### Step 4.2: Deploy Test Suite

```bash
# Run pytest test suite
pytest tests/phases/phase_N/test_N_M_name.py -v

# Expected output:
# tests/phases/phase_N/test_N_M_name.py::TestPhaseNMFeatureValidation::test_feature_1_validation PASSED
# tests/phases/phase_N/test_N_M_name.py::TestPhaseNMFeatureValidation::test_feature_2_validation PASSED
# tests/phases/phase_N/test_N_M_name.py::TestPhaseNMFeatureValidation::test_all_validations PASSED
# tests/phases/phase_N/test_N_M_name.py::TestPhaseNMIntegration::test_phase_complete_validation PASSED
# tests/phases/phase_N/test_N_M_name.py::TestPhaseNMMetadata::test_documented_metrics_match_actual PASSED
#
# ======================== 5 passed in 3.45s ========================
```

#### Step 4.3: Verify 100% Success Rate

**Requirement:** ALL tests must pass before proceeding

```bash
# Run with strict mode
pytest tests/phases/phase_N/test_N_M_name.py -v --tb=short

# Exit code must be 0
echo $?  # Should print: 0
```

**If any tests fail:**
1. Read test failure output
2. Identify root cause
3. Fix issues (data, code, config)
4. Re-run full test suite
5. Repeat until 100% pass rate

---

### Phase 5: README Alignment

**Purpose:** Ensure phase README aligns with main README vision (Workflow #57)

#### Step 5.1: Validate Temporal Precision Statements

**Check these areas in phase README:**

**Correct temporal precision:**
- Play-by-play data available (~1996-present): Millisecond-precision reconstruction
- Box score data only (1946-1996): Simulation-based temporal reconstruction using econometric + nonparametric methods

**Incorrect (outdated):**
- "2020-2025: Millisecond precision" (too narrow)
- "Minute-level precision" (understates capability)
- "Game-level aggregates" (missing simulation methodology)

#### Step 5.2: Convert Static Numbers to DIMS Commands

**BEFORE (static - will become stale):**
```markdown
### Data Growth Trajectory

| Milestone | Files | Size |
|-----------|-------|------|
| Current Total | 172,719 | 118 GB |
```

**AFTER (dynamic with DIMS):**
```markdown
### Data Growth Tracking (Live - Powered by DIMS)

**Get current S3 metrics (always up-to-date):**
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

**Historical milestones:**
- **Oct 2024 (Phase N.MMMM Initial Upload):** 146,115 files, 119 GB
- **Oct 2025 (ADCE Autonomous Collection):** +25,323 files

**See also:** Workflow #56 (DIMS Management), `inventory/metrics.yaml`
```

#### Step 5.3: Add "How This Phase Enables Vision" Section

**Template:**

```markdown
## How Phase N.MMMM Enables the Simulation Vision

This phase provides [data/infrastructure/capability] that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this phase enables:**

### 1. [Primary Contribution]
- [Specific data/capability provided]
- [How it's used in the system]

### 2. Econometric Causal Inference (Main README: Lines 49-87)
From this phase's outputs, we can:
- [Specific econometric technique enabled]
- [Example: PPP estimation using panel data regression]
- [Example: Instrumental variables for endogeneity correction]

### 3. Nonparametric Event Modeling (Main README: Lines 88-97)
From this phase's data, we build:
- [Specific nonparametric technique enabled]
- [Example: Kernel density estimation for technical fouls]
- [Example: Bootstrap resampling for injury occurrences]

### 4. Context-Adaptive Simulations
Using this phase's data, simulations can adapt to:
- [Game situation context]
- [Player/team specific factors]
- [Temporal dynamics]
```

#### Step 5.4: Update Methodology References

**Replace generic terms:**
- ❌ "simulation" → ✅ "econometric + nonparametric simulation"
- ❌ "machine learning" → ✅ "panel data regression with causal identification"
- ❌ "modeling" → ✅ "structural estimation" or "kernel density estimation"

**Add specific links:**
```markdown
See [main README](../../../README.md#simulation-methodology) for complete methodology:
- Econometric causal inference framework
- Nonparametric event modeling
- Hybrid simulation approach
- Advanced techniques (Bayesian updating, regime-switching, network effects)
```

#### Step 5.5: Test All Cross-Reference Links

```bash
# From phase README directory
cd docs/phases/phase_N/N.MMMM_name/

# Test link to main README
ls ../../../README.md  # Should exist

# Test link to PHASE_N_INDEX.md
ls ../../PHASE_N_INDEX.md  # Should exist

# Test link to PROGRESS.md
ls ../../../../PROGRESS.md  # Should exist
```

---

### Phase 6: DIMS Integration

**Purpose:** Integrate dynamic metrics tracking (Workflow #56)

#### Step 6.1: Add DIMS Commands to Phase README

**For S3-based phases:**
```markdown
**Get current S3 metrics:**
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

**For code/documentation phases:**
```markdown
**Get current project metrics:**
```bash
python scripts/monitoring/dims_cli.py verify --category code_base
python scripts/monitoring/dims_cli.py verify --category documentation
```

#### Step 6.2: Add Historical Baseline Metrics

```markdown
**Historical milestones:**
- **[Date] (Phase N.MMMM [Event]):** [Baseline metric]
- **Example:** Oct 2024 (Phase 0.0001 Initial Upload): 146,115 files, 119 GB
```

#### Step 6.3: Reference inventory/metrics.yaml

```markdown
**Current metrics tracked in:** `inventory/metrics.yaml`

**See also:** [Workflow #56: DIMS Management](../../claude_workflows/workflow_descriptions/56_dims_management.md)
```

---

### Phase 7: Phase Index Update

**Purpose:** Update PHASE_N_INDEX.md to reflect completion (Workflow #52)

#### Step 7.1: Update Phase Status

**File:** `docs/phases/PHASE_N_INDEX.md`

**Change status from ⏸️ PENDING or 🔄 IN PROGRESS to ✅ COMPLETE:**

```markdown
| **N.M** | [Phase Name] | ✅ COMPLETE | ⭐ PRIORITY | Oct 23, 2025 |
```

#### Step 7.2: Update Completion Date

Add actual completion date in the table (last column).

#### Step 7.3: Verify Prerequisites Met

**Check phase index:**

```markdown
**Prerequisites:**
- [✓] Phase 0 complete
- [✓] Phase 1 complete
- [✓] AWS credentials configured
```

All prerequisites must be checked before marking phase complete.

---

### Phase 8: Final Validation

**Purpose:** Comprehensive final check before marking phase complete

#### Step 8.1: Run Full Test Suite One More Time

```bash
# Full test suite with verbose output
pytest tests/phases/phase_N/test_N_M_name.py -v --tb=short

# Must be 100% pass rate
```

#### Step 8.2: Verify DIMS Metrics Current

```bash
# Check metrics last updated timestamp
python scripts/monitoring/dims_cli.py verify

# Should show recent timestamp (< 24 hours old)
```

#### Step 8.3: Confirm README Aligned with Main README

**Checklist:**
- [ ] Temporal precision statements accurate
- [ ] Data tracking uses DIMS commands
- [ ] "How This Phase Enables Vision" section exists
- [ ] Methodology references are specific (econometric + nonparametric)
- [ ] All cross-reference links work
- [ ] Cost estimates align with main README (if applicable)

#### Step 8.4: Check for Deprecated Files in docs/

```bash
# Search for .py files in docs/ (should be none except deprecated)
find docs/phases/phase_N/ -name "*.py"

# If found, verify they have deprecation notices
# Move to proper location (tests/ or validators/)
```

#### Step 8.5: Final Approval

**Before marking ✅ COMPLETE, verify:**
- ✅ All tests pass (100% success rate)
- ✅ All validators pass (100% success rate)
- ✅ README aligned with main README vision
- ✅ DIMS integration complete
- ✅ Phase index updated
- ✅ No deprecated code in docs/

---

## Success Criteria

**Phase is ready to mark ✅ COMPLETE when:**

1. **Tests:** 100% pass rate on pytest suite
2. **Validators:** 100% pass rate on standalone validators
3. **README:** Aligned with main README (6-point checklist from Workflow #57)
4. **DIMS:** Metrics integrated and current
5. **Phase Index:** Status updated to ✅ COMPLETE with date
6. **Code:** Tests/validators in proper directories (tests/, validators/)
7. **Documentation:** No .py files in docs/ except deprecated with notices

---

## Common Scenarios

### Scenario 1: Data Collection Phase (e.g., Phase 0.0001, 0.0002) - 4-digit format per ADR-010

**Validators needed:**
- S3 bucket configuration
- S3 upload completeness
- File naming patterns
- Data quality checks

**Test suite checks:**
- S3 bucket exists and accessible
- Expected file count met
- File sizes reasonable
- No corrupted files

**README requirements:**
- Data source described
- Collection methodology explained
- S3 storage locations documented
- DIMS commands for current file counts

### Scenario 2: Database Phase (e.g., Phase 3)

**Validators needed:**
- RDS instance exists
- Database tables exist
- Schema matches expectations
- Row counts meet minimums

**Test suite checks:**
- Database connection works
- Tables have correct columns
- Indexes created
- Foreign keys enforced

**README requirements:**
- Database schema documented
- Table descriptions provided
- Query examples included
- Connection instructions clear

### Scenario 3: ML Model Phase (e.g., Phase 5)

**Validators needed:**
- Model file exists
- Feature engineering pipeline works
- Model performance meets threshold
- Predictions output correctly

**Test suite checks:**
- Model loads successfully
- Feature shapes correct
- Predictions within expected range
- Model versioning works

**README requirements:**
- Model architecture explained
- Feature engineering described
- Performance metrics documented
- Usage examples provided

---

## Troubleshooting

### Problem: Tests fail with import errors

**Solution:**
```bash
# Check sys.path in test file
# Should include: Path(__file__).parent.parent.parent.parent / "validators" / "phases" / "phase_N"

# Verify validator file exists
ls validators/phases/phase_N/validate_N_M_feature.py
```

### Problem: Validator passes but tests fail

**Solution:**
- Tests may have stricter assertions
- Check test failure message for specifics
- Ensure validator and tests checking same things
- Verify test fixtures provide correct data

### Problem: README still has static numbers

**Solution:**
1. Find static number tables/lists
2. Replace with DIMS commands
3. Move static numbers to "Historical milestones" section
4. Reference `inventory/metrics.yaml` for current values

### Problem: "How This Phase Enables Vision" section unclear

**Solution:**
1. Read main README simulation methodology (lines 20-100)
2. Identify which techniques this phase enables
3. Be specific: name exact econometric/nonparametric methods
4. Give concrete examples with this phase's data

### Problem: Phase index says complete but tests missing

**Solution:**
1. Phase incorrectly marked complete too early
2. Change status back to 🔄 IN PROGRESS
3. Generate tests/validators (Phase 2 of this workflow)
4. Run validations
5. Only then mark ✅ COMPLETE

---

## Integration with Other Workflows

**This workflow orchestrates:**
- **Workflow #52:** Phase Index Management (Phase 7)
- **Workflow #53:** Test & Validator Organization (Phase 3)
- **Workflow #56:** DIMS Management (Phase 6)
- **Workflow #57:** Phase-README Alignment (Phase 5)

**This workflow is called by:**
- **Workflow #14:** Session End (optional check if phase modified)
- **Workflow #20:** Maintenance Schedule (monthly validation)

**Related workflows:**
- **Workflow #16:** Testing - General testing framework
- **Workflow #41:** Testing Framework - Comprehensive test suite guide

---

## Appendix A: Validator Code Examples

### S3 Bucket Configuration Validator

```python
def validate_bucket_encryption(self) -> bool:
    """Verify S3 bucket has encryption enabled."""
    try:
        response = self.s3.get_bucket_encryption(Bucket=self.bucket_name)
        rules = response['ServerSideEncryptionConfiguration']['Rules']

        if not rules:
            self.failures.append("Bucket encryption not enabled")
            return False

        if self.verbose:
            print(f"✓ Bucket encryption: {rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']}")
        return True

    except self.s3.exceptions.ServerSideEncryptionConfigurationNotFoundError:
        self.failures.append("Bucket encryption configuration not found")
        return False
```

### RDS Table Validator

```python
def validate_table_row_count(self, table_name: str, min_rows: int) -> bool:
    """Verify table has minimum number of rows."""
    cursor = self.conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    actual_count = cursor.fetchone()[0]

    if actual_count < min_rows:
        self.failures.append(
            f"Table {table_name} has {actual_count} rows, expected >= {min_rows}"
        )
        return False

    if self.verbose:
        print(f"✓ Table {table_name}: {actual_count:,} rows")
    return True
```

---

## Appendix B: Test Code Examples

### Pytest Fixture for S3

```python
@pytest.fixture(scope="module")
def s3_file_count(s3_client, bucket_name):
    """Get actual S3 file count for testing."""
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix='hoopr_phase1/'
    )
    return response.get('KeyCount', 0)

def test_file_count_meets_minimum(s3_file_count):
    """Verify minimum file count met."""
    min_files = 400
    assert s3_file_count >= min_files, \
        f"Expected >= {min_files} files, found {s3_file_count}"
```

### Pytest Fixture for RDS

```python
@pytest.fixture(scope="module")
def table_exists(rds_connection):
    """Check if table exists."""
    def _check(table_name: str) -> bool:
        cursor = rds_connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table_name,))
        return cursor.fetchone()[0]
    return _check

def test_hoopr_tables_exist(table_exists):
    """Verify all hoopR tables exist."""
    required_tables = [
        'hoopr_play_by_play',
        'hoopr_player_box',
        'hoopr_team_box',
        'hoopr_schedule'
    ]

    for table in required_tables:
        assert table_exists(table) == True, f"Table {table} does not exist"
```

---

**Workflow Owner:** Infrastructure Team
**Last Updated:** October 23, 2025
**Status:** ✅ Active
**Next Review:** November 2025

---

*This workflow replaces #52 (Phase Index Management), #53 (Test & Validator Organization), and #57 (Phase-README Alignment). See this workflow for the complete unified process.*
