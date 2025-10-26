# 0.0019: Testing Infrastructure & CI/CD

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ⏸️ PENDING
**Priority:** ⭐ CRITICAL
**Migrated From:** 6.0000 (Optional Enhancements)
**Timeline:** 1-2 weeks
**Cost Impact:** $0 (GitHub Actions free tier)

---

## Overview

Establish foundational testing infrastructure and CI/CD pipelines to ensure code quality, prevent regressions, and automate deployment workflows. This sub-phase transforms "optional enhancements" into core infrastructure that supports all development work.

**This sub-phase delivers:**
- Comprehensive pytest framework for all phases
- Automated GitHub Actions CI/CD pipelines
- Pre-commit hooks for security and quality
- CloudWatch integration for production monitoring
- Test coverage tracking and reporting
- Automated validation on every push

**Why this is foundational, not optional:**
- Prevents regressions as codebase grows (1,672 Python files)
- Catches security issues before they reach production
- Ensures data quality across 172,719 S3 files
- Enables confident refactoring (like 4-digit renumbering)
- Reduces manual testing burden on every change

---

## Current Testing State

**Existing Infrastructure (from 0.0001-0.18):**
- 643 test files across project
- 44/44 0.0018 tests passing (100%)
- Pre-commit hooks (detect-secrets, bandit, black)
- Validator scripts for each sub-phase

**Gaps to Address:**
- No centralized pytest configuration
- No CI/CD automation (tests run manually)
- Inconsistent test organization
- No coverage tracking
- No automated deployment workflows

---

## Sub-Phase Components

### 1. Pytest Framework Setup

**Goal:** Unified testing framework for entire codebase

**Implementation:**
```python
# pytest.ini - Project root
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --cov=scripts
    --cov=notebooks
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require S3/RDS)
    slow: Slow tests (>1 second)
    autonomous: ADCE autonomous system tests
```

**Test Organization:**
```
tests/
├── unit/                     # Fast, isolated tests
│   ├── test_data_extraction.py
│   ├── test_temporal_queries.py
│   └── test_feature_engineering.py
├── integration/              # Tests requiring AWS resources
│   ├── test_s3_operations.py
│   ├── test_rds_queries.py
│   └── test_adce_pipeline.py
├── phases/                   # Phase-specific tests (existing)
│   ├── phase_0/
│   │   ├── test_0_000001_initial_data_collection.py
│   │   ├── test_0_000018_autonomous_data_collection.py
│   │   └── ...
│   └── phase_5/
└── fixtures/                 # Shared test fixtures
    ├── conftest.py          # pytest configuration
    ├── sample_data.py       # Sample NBA data
    └── mock_aws.py          # Mock AWS responses
```

**Run Commands:**
```bash
# All tests
pytest

# Unit tests only (fast)
pytest -m unit

# Integration tests (requires AWS)
pytest -m integration

# Phase-specific tests
pytest tests/phases/phase_0/ -v

# Coverage report
pytest --cov --cov-report=html
open htmlcov/index.html
```

### 2. GitHub Actions CI/CD

**Goal:** Automated testing, validation, and deployment

**Workflows to Create:**

#### Workflow 1: Test Suite (.github/workflows/test.yml)
```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run unit tests
      run: pytest -m unit -v

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

#### Workflow 2: Security Scan (.github/workflows/security.yml)
```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Detect secrets
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./

    - name: Run bandit
      run: |
        pip install bandit
        bandit -r scripts/ notebooks/ -f json -o bandit-report.json

    - name: Upload results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: bandit-report.json
```

#### Workflow 3: Data Validation (.github/workflows/data-validation.yml)
```yaml
name: Data Validation

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Run DIMS verification
      run: python scripts/monitoring/dims_cli.py verify --all

    - name: Run validators
      run: |
        for validator in validators/phases/phase_0/*.py; do
          python "$validator" || exit 1
        done
```

### 3. Pre-commit Hooks Enhancement

**Goal:** Catch issues before they reach git history

**Enhanced .pre-commit-config.yaml:**
```yaml
repos:
  # Security scanning
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Code quality
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  # Security analysis
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'scripts/', 'notebooks/']
        exclude: '^tests/'

  # Import sorting
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  # Linting
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120', '--ignore=E203,W503']

  # File size and convention checks
  - repo: local
    hooks:
      - id: check-file-sizes
        name: Check file sizes and conventions
        entry: bash scripts/shell/pre_commit_checks.sh
        language: system
        pass_filenames: false

  # Run fast tests
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest -m unit --tb=short
        language: system
        pass_filenames: false
        stages: [commit]
```

**Install hooks:**
```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
```

### 4. CloudWatch Integration

**Goal:** Monitor test results and CI/CD health in production

**Metrics to Track:**
- Test pass rate (unit vs integration)
- Test execution time
- CI/CD pipeline duration
- Pre-commit hook success rate
- Coverage percentage over time

**Implementation:**
```python
# scripts/monitoring/publish_test_metrics.py
import boto3
import json
from datetime import datetime

def publish_test_metrics(results):
    """Publish pytest results to CloudWatch"""
    cloudwatch = boto3.client('cloudwatch')

    metrics = [
        {
            'MetricName': 'TestPassRate',
            'Value': results['passed'] / results['total'] * 100,
            'Unit': 'Percent',
            'Timestamp': datetime.utcnow()
        },
        {
            'MetricName': 'TestDuration',
            'Value': results['duration'],
            'Unit': 'Seconds',
            'Timestamp': datetime.utcnow()
        },
        {
            'MetricName': 'CodeCoverage',
            'Value': results['coverage'],
            'Unit': 'Percent',
            'Timestamp': datetime.utcnow()
        }
    ]

    cloudwatch.put_metric_data(
        Namespace='NBA-Simulator/Testing',
        MetricData=metrics
    )
```

**Usage in GitHub Actions:**
```yaml
- name: Publish metrics to CloudWatch
  run: |
    pytest --json-report --json-report-file=test-results.json
    python scripts/monitoring/publish_test_metrics.py test-results.json
```

---

## Success Criteria

**Minimum Viable Product (MVP):**
- ✅ pytest.ini configured with coverage
- ✅ Tests organized by type (unit/integration/phase)
- ✅ GitHub Actions running on every push
- ✅ Pre-commit hooks enhanced and active
- ✅ All existing 44 0.0018 tests migrated

**Full Success:**
- ✅ 100% of Phase 0 tests automated
- ✅ CI/CD pipeline <5 minutes total
- ✅ Coverage tracking enabled (target: >80%)
- ✅ CloudWatch metrics dashboards created
- ✅ Automated deployment to staging environment
- ✅ Pre-commit hooks enforce security and quality

---

## Implementation Plan

### Week 1: Pytest Framework
**Days 1-2:**
- Create pytest.ini with markers and coverage
- Reorganize existing tests (unit vs integration vs phase-specific)
- Create shared fixtures in tests/fixtures/

**Days 3-4:**
- Migrate all Phase 0 tests to new structure
- Add coverage reporting
- Create test documentation

**Day 5:**
- Run full test suite
- Fix any broken tests
- Validate 100% pass rate

### Week 2: CI/CD & Automation
**Days 1-2:**
- Create GitHub Actions workflows (test.yml, security.yml)
- Configure secrets in GitHub repo
- Test workflows on feature branch

**Days 3-4:**
- Enhance pre-commit hooks (add isort, flake8)
- Create CloudWatch integration script
- Set up metrics dashboard

**Day 5:**
- End-to-end validation
- Document workflows and usage
- Create runbook for CI/CD troubleshooting

---

## Cost Breakdown

| Component | Configuration | Monthly Cost | Notes |
|-----------|--------------|--------------|-------|
| GitHub Actions | Free tier (2,000 min/month) | $0 | Sufficient for small team |
| CloudWatch Metrics | Custom metrics | $0.30-0.50 | ~10-15 metrics |
| **Total** | | **$0.30-0.50/month** | Minimal cost increase |

**Development Time:** 2 weeks (80 hours)

---

## Prerequisites

**Before starting 0.0019:**
- [x] 0.0001-0.18 complete (tests exist)
- [x] Git repository configured
- [x] AWS credentials available
- [ ] GitHub repository exists (or create)
- [ ] CloudWatch access configured

---

## Integration with Existing Systems

### DIMS (Data Inventory Management System)
- CI/CD triggers DIMS verification weekly
- Test results published to CloudWatch via DIMS
- Coverage metrics tracked in inventory/metrics.yaml

### ADCE (Autonomous Data Collection Ecosystem)
- Integration tests validate ADCE health
- Autonomous loop tests run in CI/CD
- CloudWatch monitors ADCE uptime

### Security Protocols
- Pre-commit hooks prevent secrets in commits
- Bandit catches security vulnerabilities
- GitHub Actions enforces security scans

---

## Files to Create

**Configuration:**
```
pytest.ini                              # Pytest configuration (root)
.github/workflows/test.yml             # Test automation
.github/workflows/security.yml         # Security scanning
.github/workflows/data-validation.yml  # Weekly data checks
.pre-commit-config.yaml                # Enhanced hooks (update existing)
```

**Scripts:**
```
scripts/monitoring/publish_test_metrics.py   # CloudWatch integration
scripts/testing/run_test_suite.sh           # Convenience wrapper
scripts/testing/generate_coverage_report.sh # Coverage reporting
```

**Tests:**
```
tests/fixtures/conftest.py             # Shared fixtures
tests/fixtures/sample_data.py          # Sample NBA data
tests/fixtures/mock_aws.py             # Mock AWS responses
tests/unit/                            # Unit tests (new)
tests/integration/                     # Integration tests (new)
```

**Documentation:**
```
docs/testing/TESTING_GUIDE.md          # How to write tests
docs/testing/CI_CD_GUIDE.md            # GitHub Actions usage
docs/testing/COVERAGE_GUIDE.md         # Coverage tracking
```

---

## Common Issues & Solutions

### Issue 1: Tests fail in CI but pass locally
**Cause:** Environment differences (AWS credentials, file paths)
**Solution:**
- Use environment variables for configuration
- Mock AWS services in unit tests
- Use relative paths, not absolute

### Issue 2: Pre-commit hooks too slow
**Cause:** Running all tests on every commit
**Solution:**
- Run only fast unit tests in pre-commit
- Save integration tests for pre-push
- Use pytest markers to control which tests run

### Issue 3: GitHub Actions exceed free tier
**Cause:** Too many workflow runs or long-running tests
**Solution:**
- Optimize test speed (parallel execution)
- Run expensive tests only on main branch
- Use workflow dispatch for manual triggers

### Issue 4: Coverage too low
**Cause:** Legacy code without tests
**Solution:**
- Set incremental coverage targets (70% → 80% → 90%)
- Focus on critical paths first (data collection, ADCE)
- Add tests gradually as code is modified

---

## Workflows Referenced

- **Workflow #41:** Testing Framework - Pytest setup and organization
- **Workflow #16:** General Testing - Test writing best practices
- **Workflow #6:** File Creation - Creating new test files
- **Workflow #2:** Command Logging - Documenting test commands

---

## Related Documentation

**Testing:**
- [TESTING.md](../../../TESTING.md) - Current testing guide (862 lines)
- [TEST_VALIDATOR_MIGRATION_GUIDE.md](../../../TEST_VALIDATOR_MIGRATION_GUIDE.md) - Reorganization guide

**Security:**
- [SECURITY_PROTOCOLS.md](../../../SECURITY_PROTOCOLS.md) - Security scanning procedures
- Pre-commit hook documentation

**Monitoring:**
- [SCRAPER_MONITORING_SYSTEM.md](../../../SCRAPER_MONITORING_SYSTEM.md) - CloudWatch integration
- [Workflow #56: DIMS Management](../../../claude_workflows/workflow_descriptions/56_dims_management.md)

---

## Navigation

**Return to:** [Phase 0 Index](../PHASE_0_INDEX.md)

**Prerequisites:** None (foundational)

**Integrates with:**
- 0.0008: Security Implementation - Security scanning hooks
- 0.0018: Autonomous Data Collection - ADCE testing
- 0.0020: Monitoring & Observability - CloudWatch metrics

---

## How This Enables the Simulation Vision

This sub-phase provides **quality assurance infrastructure** that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this sub-phase enables:**

### 1. Econometric Causal Inference
From this sub-phase's infrastructure, we can:
- **Validate regression results** with automated tests
- **Ensure data quality** for panel data regression (PPP estimation)
- **Prevent statistical errors** via continuous testing

### 2. Nonparametric Event Modeling
From this sub-phase's testing, we build:
- **Validated kernel density estimators** (tested against known distributions)
- **Reliable event sequence models** (integration tests verify temporal accuracy)
- **Regression-tested simulation engines** (prevent model degradation)

### 3. Context-Adaptive Simulations
Using this sub-phase's CI/CD, simulations can:
- **Continuously validate** against real game outcomes
- **Auto-detect drift** when model accuracy degrades
- **Safely refactor** simulation logic with confidence

**See [main README](../../../README.md) for complete methodology.**

---

**Last Updated:** October 25, 2025 (Migrated from 6.0000)
**Status:** ⏸️ PENDING - Ready for implementation
**Migrated By:** Comprehensive Phase Reorganization (ADR-010)
