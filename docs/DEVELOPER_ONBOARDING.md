# NBA Simulator - Developer Onboarding Guide

**Estimated Time:** 2 hours
**Prerequisites:** MacBook Pro (Apple Silicon preferred), AWS account, GitHub access
**Last Updated:** October 31, 2025

---

## Quick Navigation

- [Hour 1: Environment Setup](#hour-1-environment-setup)
- [Hour 2: First Contribution](#hour-2-first-contribution)
- [Common Gotchas](#common-gotchas)
- [Next Steps](#next-steps)

---

## Project Overview (5 minutes)

**What is this project?**
The NBA Simulator is a temporal panel data system that enables snapshot queries of NBA history at exact timestamps with millisecond precision. It's NOT traditional sports analytics - it's a research platform for econometric causal inference and nonparametric event modeling.

**Core Capability:**
Query cumulative NBA statistics at any exact moment in time:
- "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"
- "What was the NBA's average pace at 11:23:45.678 PM on March 15, 2023?"

**Key Technologies:**
- **AWS:** S3 (172K+ files), RDS PostgreSQL (40 tables, 13.6M+ events)
- **Python:** 3.11, pandas, boto3, psycopg2, statsmodels
- **Data Sources:** ESPN, NBA API, Basketball Reference, hoopR, Kaggle

**Current Status:**
- Phase 0: Data Collection - ✅ COMPLETE (18/20 sub-phases)
- Phase 1: Data Validation - 🔄 IN PROGRESS
- Autonomous Data Collection Ecosystem (ADCE) - ✅ OPERATIONAL

---

## Hour 1: Environment Setup

### Step 1: Clone Repository (5 min)

```bash
# Clone via SSH (recommended)
git clone git@github.com:ryanranft/nba-simulator-aws.git
cd nba-simulator-aws

# OR clone via HTTPS
git clone https://github.com/ryanranft/nba-simulator-aws.git
cd nba-simulator-aws
```

**Verify:**
```bash
ls -la
# Should see: PROGRESS.md, CLAUDE.md, README.md, scripts/, docs/, etc.
```

### Step 2: Install Dependencies (20 min)

**A. Install Miniconda (if not already installed):**
```bash
# Download Miniconda for Apple Silicon
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh

# Install
bash Miniconda3-latest-MacOSX-arm64.sh

# Restart terminal or source:
source ~/.bash_profile  # or ~/.zshrc
```

**B. Create conda environment:**
```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate nba-aws

# Verify Python version
python --version
# Should show: Python 3.11.x
```

**C. Install additional dependencies:**
```bash
# Install Python packages
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Verify installation
pre-commit --version
```

### Step 3: Configure AWS (15 min)

**A. Get AWS credentials from team lead:**
- AWS Access Key ID
- AWS Secret Access Key
- Region: `us-east-1`

**B. Configure AWS CLI:**
```bash
# Install AWS CLI (if not installed)
brew install awscli

# Configure credentials
aws configure
# AWS Access Key ID: [paste your key]
# AWS Secret Access Key: [paste your secret]
# Default region name: us-east-1
# Default output format: json
```

**C. Test AWS access:**
```bash
# Test S3 access
aws s3 ls s3://nba-sim-raw-data-lake/ --max-items 5

# Expected output:
# PRE espn/
# PRE hoopr/
# PRE kaggle/
# ...

# Test RDS access (requires .env file - next step)
```

**D. Create .env file:**
```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

**Add these values to .env:**
```bash
# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=nba-sim-raw-data-lake
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# RDS PostgreSQL
RDS_HOST=nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=nba_simulator
RDS_USERNAME=postgres
RDS_PASSWORD=get_from_team_lead

# Optional: Set project root
PROJECT_ROOT=/Users/your_username/nba-simulator-aws
```

**⚠️ IMPORTANT:** Never commit `.env` to git! It's already in `.gitignore`.

### Step 4: Verify Setup (15 min)

**A. Run DIMS verification:**
```bash
# Verify S3 storage
python scripts/monitoring/dims_cli.py verify --category s3_storage

# Expected output:
# ✅ S3 bucket exists: nba-sim-raw-data-lake
# ✅ Object count matches: 172,719 files
# ✅ Total size: 118.2 GB
```

**B. Test database connection:**
```bash
# Test PostgreSQL connection
python << 'EOF'
from nba_simulator.database import execute_query

result = execute_query("SELECT COUNT(*) as count FROM games")
print(f"✅ Database connected: {result[0]['count']:,} games")
EOF

# Expected output:
# ✅ Database connected: 65,642 games
```

**C. Run basic tests:**
```bash
# Run Phase 0 tests
pytest tests/phases/phase_0/ -v --tb=short

# Run validator scripts
python validators/phases/phase_0/validate_0_1_s3_bucket_config.py

# Expected: Most tests pass (some may be skipped)
```

**D. Check ADCE status:**
```bash
# Check autonomous system
python scripts/autonomous/autonomous_cli.py status

# Expected output:
# Status: RUNNING
# Uptime: XX hours
# Tasks completed: XXX
```

### Step 5: Explore Codebase (15 min)

**A. Read core documentation:**
```bash
# Project status and roadmap
cat PROGRESS.md

# AI assistant instructions (understand project structure)
cat CLAUDE.md

# Quick command reference
cat QUICKSTART.md

# Main project vision
cat README.md
```

**B. Understand project structure:**
```bash
# View directory tree
tree -L 2 -d

# Key directories:
# - scripts/          # All Python scripts
# - docs/             # Documentation (1,720+ files)
# - tests/            # Test suites
# - validators/       # Data validators
# - config/           # Configuration files
# - inventory/        # DIMS metrics
# - logs/             # System logs (gitignored)
```

**C. Browse phase documentation:**
```bash
# Read Phase 0 index
cat docs/phases/phase_0/PHASE_0_INDEX.md

# List all phases
ls -la docs/phases/

# Read workflow descriptions
ls docs/claude_workflows/workflow_descriptions/
```

**D. Check data structure:**
```bash
# Understand S3 layout
cat docs/DATA_STRUCTURE_GUIDE.md

# View data sources
cat docs/DATA_CATALOG.md

# Check current metrics
cat inventory/metrics.yaml
```

---

## Hour 2: First Contribution

### Step 1: Pick a Task (10 min)

**Option A: Browse PROGRESS.md**
```bash
# Find pending tasks
grep "⏸️ PENDING" PROGRESS.md

# Find in-progress tasks
grep "🔄 IN PROGRESS" PROGRESS.md
```

**Option B: Check GitHub Issues**
- Browse: https://github.com/ryanranft/nba-simulator-aws/issues
- Filter by label: `good first issue`

**Option C: Ask Team Lead**
- Join Slack channel
- Ask: "What's a good first task for a new developer?"

**Recommended First Tasks:**
1. Add docstrings to undocumented functions
2. Write tests for untested modules
3. Fix DIMS metric drift (update inventory/metrics.yaml)
4. Improve error messages in validators
5. Add logging to existing scripts

### Step 2: Create Feature Branch (5 min)

**Branch naming conventions:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `test/description` - Test additions
- `refactor/description` - Code refactoring

```bash
# Create and checkout new branch
git checkout -b feature/add-docstrings-to-dims-cli

# Verify branch
git branch
# Should show: * feature/add-docstrings-to-dims-cli
```

### Step 3: Make Changes (35 min)

**A. Follow code standards:**
```bash
# Read style guide
cat docs/STYLE_GUIDE.md

# Read docstring standards (after this onboarding completes)
cat docs/DOCSTRING_STANDARDS.md
```

**B. Write code:**
```python
# Example: Adding docstrings to dims_cli.py

def verify_metrics(category: str = "all") -> dict:
    """Verify DIMS metrics against current system state.

    Compares metrics in inventory/metrics.yaml with actual values
    from AWS S3, RDS, and local filesystem. Reports discrepancies
    and suggests updates.

    Args:
        category: Metric category to verify. Options:
            - 's3_storage': S3 bucket metrics only
            - 'database': RDS PostgreSQL metrics only
            - 'all': All metric categories (default)

    Returns:
        Dictionary containing:
            - 'verified': int - Count of verified metrics
            - 'drift': int - Count of metrics with drift
            - 'errors': list[str] - Error messages

    Raises:
        ValueError: If category is invalid
        boto3.exceptions.NoCredentialsError: If AWS credentials missing

    Examples:
        >>> result = verify_metrics(category='s3_storage')
        >>> print(f"Verified: {result['verified']}")
        Verified: 5

    See Also:
        - update_metrics(): Update drifted metrics
        - report_metrics(): Generate metric reports
    """
    # Implementation...
```

**C. Write tests:**
```python
# tests/test_dims_cli.py

import pytest
from scripts.monitoring.dims_cli import verify_metrics

def test_verify_metrics_s3_storage():
    """Test S3 storage metric verification."""
    result = verify_metrics(category='s3_storage')

    assert 'verified' in result
    assert 'drift' in result
    assert isinstance(result['verified'], int)
    assert result['verified'] >= 0

def test_verify_metrics_invalid_category():
    """Test error handling for invalid category."""
    with pytest.raises(ValueError, match="Invalid category"):
        verify_metrics(category='invalid')
```

**D. Run tests locally:**
```bash
# Run your new tests
pytest tests/test_dims_cli.py -v

# Run related tests
pytest tests/phases/phase_0/ -v

# Check coverage
pytest tests/test_dims_cli.py --cov=scripts.monitoring.dims_cli --cov-report=term-missing
```

### Step 4: Commit and Push (20 min)

**A. Check changes:**
```bash
# View modified files
git status

# View diff
git diff

# Stage specific files
git add scripts/monitoring/dims_cli.py
git add tests/test_dims_cli.py
```

**B. Run pre-commit hooks:**
```bash
# Hooks run automatically on commit, but you can test first:
pre-commit run --all-files

# Fix any issues the hooks identify
```

**C. Commit with conventional commit message:**
```bash
# Commit format: <type>(<scope>): <description>
# Types: feat, fix, docs, test, refactor, style, chore

git commit -m "docs(dims): Add comprehensive docstrings to dims_cli.py

- Add Google-style docstrings to all public functions
- Include Args, Returns, Raises, Examples sections
- Add type hints for all parameters

Related to #42 (issue number if applicable)"
```

**D. Push to GitHub:**
```bash
# Push your branch
git push origin feature/add-docstrings-to-dims-cli

# If this is your first push on this branch:
git push -u origin feature/add-docstrings-to-dims-cli
```

**E. Create Pull Request:**
```bash
# Using GitHub CLI (recommended)
gh pr create --title "docs: Add comprehensive docstrings to dims_cli" \
  --body "## Summary
- Added Google-style docstrings to all public functions in dims_cli.py
- Added type hints for better IDE support
- Updated tests to cover new parameter validations

## Testing
- All existing tests pass
- Added 3 new test cases for edge cases
- Verified docstring rendering with pydocstyle

## Checklist
- [x] Tests pass locally
- [x] Pre-commit hooks pass
- [x] Documentation updated
- [x] No breaking changes"

# OR create PR via web interface:
# https://github.com/ryanranft/nba-simulator-aws/compare
```

---

## Common Gotchas

### 1. AWS Credentials Not Found

**Error:**
```
boto3.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution:**
```bash
# Check if credentials are configured
aws configure list

# If empty, reconfigure:
aws configure

# Or check .env file exists:
cat .env | grep AWS_ACCESS_KEY_ID
```

### 2. Pre-commit Hook Fails

**Error:**
```
Pre-commit hook failed: flake8 found issues
```

**Solution:**
```bash
# See what failed
pre-commit run --all-files

# Fix issues (usually formatting)
black scripts/monitoring/dims_cli.py
isort scripts/monitoring/dims_cli.py

# Try again
git commit -m "your message"
```

### 3. Tests Fail Locally

**Error:**
```
ImportError: No module named 'nba_simulator'
```

**Solution:**
```bash
# Ensure you're in project root
pwd
# Should show: /Users/your_username/nba-simulator-aws

# Ensure conda environment is activated
conda activate nba-aws

# Verify Python version
python --version
# Should show: Python 3.11.x (not 3.9 or 3.12)

# Install package in editable mode
pip install -e .
```

### 4. S3 Access Denied

**Error:**
```
botocore.exceptions.ClientError: An error occurred (403) when calling the ListObjectsV2 operation: Forbidden
```

**Solution:**
```bash
# Check IAM permissions with team lead
# Your IAM user needs:
# - s3:ListBucket
# - s3:GetObject
# - s3:PutObject

# Verify you're using correct AWS profile
aws sts get-caller-identity

# Should show your IAM user ARN
```

### 5. Database Connection Timeout

**Error:**
```
psycopg2.OperationalError: could not connect to server: Connection timed out
```

**Solution:**
```bash
# Check if VPN is required (ask team lead)

# Verify RDS endpoint in .env
cat .env | grep RDS_HOST

# Test connection with psql
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres -d nba_simulator

# If VPN required, connect first:
# (VPN instructions from team lead)
```

### 6. ADCE System Not Running

**Error:**
```
ADCE Status: STOPPED
```

**Solution:**
```bash
# Start autonomous system
python scripts/autonomous/autonomous_cli.py start

# Check logs
tail -f logs/autonomous_loop.log

# If issues, check health
python scripts/autonomous/autonomous_cli.py health
```

### 7. Git Push Rejected

**Error:**
```
! [rejected] main -> main (fetch first)
```

**Solution:**
```bash
# Pull latest changes first
git pull origin main --rebase

# Resolve any conflicts
git status

# Push again
git push origin your-branch-name
```

---

## Next Steps

### After Onboarding (Within First Week)

**Day 1-2:**
- [ ] Complete first PR and get it merged
- [ ] Join team Slack channel
- [ ] Attend daily standup
- [ ] Review open GitHub issues

**Day 3-4:**
- [ ] Read all ADRs in `docs/adr/`
- [ ] Understand ADCE architecture (0.0018)
- [ ] Review Phase 0 completion (PHASE_0_INDEX.md)
- [ ] Pair program with senior developer

**Day 5:**
- [ ] Pick a larger task (2-4 hours)
- [ ] Review someone else's PR
- [ ] Write documentation for a feature you learned

### Continuous Learning

**Essential Reading (prioritize these):**
- `PROGRESS.md` - Updated frequently, shows current status
- `docs/phases/phase_0/PHASE_0_INDEX.md` - Foundation of the system
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `docs/TEMPORAL_QUERY_GUIDE.md` - Core system capability

**Advanced Topics (after 1-2 weeks):**
- `docs/phases/phase_5/PHASE_5_INDEX.md` - ML frameworks
- Econometric methodology in README.md
- Book recommendations: `BOOK_RECOMMENDATIONS_PROGRESS.md`

**Weekly Activities:**
- Attend weekly retrospective
- Review new ADRs as they're created
- Update DIMS metrics: `python scripts/monitoring/dims_cli.py update`
- Check ADCE health: `python scripts/autonomous/autonomous_cli.py status`

---

## Useful Commands Cheat Sheet

**Daily Workflow:**
```bash
# Start work session
conda activate nba-aws
bash scripts/shell/session_manager.sh start

# Check system status
python scripts/autonomous/autonomous_cli.py status
python scripts/monitoring/dims_cli.py verify

# Make changes, commit
git add .
git commit -m "feat: your message"
git push

# End session
bash scripts/shell/session_manager.sh end
```

**Testing:**
```bash
# Run all tests
pytest tests/ -v

# Run specific phase tests
pytest tests/phases/phase_0/ -v

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run validators
for v in validators/phases/phase_0/*.py; do python "$v"; done
```

**Monitoring:**
```bash
# DIMS metrics
python scripts/monitoring/dims_cli.py verify
python scripts/monitoring/dims_cli.py update
python scripts/monitoring/dims_cli.py report

# ADCE status
python scripts/autonomous/autonomous_cli.py status
python scripts/autonomous/autonomous_cli.py health
tail -f logs/autonomous_loop.log
```

**Documentation:**
```bash
# Search documentation
grep -r "keyword" docs/

# View workflow
cat docs/claude_workflows/workflow_descriptions/XX_workflow_name.md

# Generate file inventory
python scripts/maintenance/generate_file_inventory.py
```

**AWS Operations:**
```bash
# S3 operations
aws s3 ls s3://nba-sim-raw-data-lake/espn/ --recursive | wc -l
aws s3 cp local_file.json s3://nba-sim-raw-data-lake/path/

# RDS operations
psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DATABASE -c "SELECT COUNT(*) FROM games;"
```

---

## Team Communication

**Slack Channels:**
- `#nba-simulator-dev` - General development
- `#nba-simulator-data` - Data quality issues
- `#nba-simulator-alerts` - Automated alerts from ADCE

**GitHub Workflow:**
- Create issue before starting large work
- Reference issue numbers in commit messages
- Request review from at least one teammate
- Merge only after approval and CI passes

**Asking for Help:**
1. Check `docs/TROUBLESHOOTING.md` first
2. Search GitHub issues for similar problems
3. Ask in Slack with context (error messages, what you tried)
4. Pair program if stuck for >30 minutes

---

## Success Checklist

**You're ready to contribute when you can:**
- [ ] Clone repo and activate conda environment
- [ ] Run DIMS verification successfully
- [ ] Connect to RDS database
- [ ] Run test suite (most tests pass)
- [ ] Create feature branch and commit changes
- [ ] Push to GitHub and create PR
- [ ] Understand project structure and key files
- [ ] Know where to find documentation
- [ ] Use Slack to ask questions

**By end of Week 1, you should:**
- [ ] Have 1+ PRs merged
- [ ] Understand ADCE architecture
- [ ] Be able to add tests independently
- [ ] Know how to monitor system health
- [ ] Feel comfortable with git workflow

---

## Additional Resources

**External Documentation:**
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python 3.11 Documentation](https://docs.python.org/3.11/)
- [Pytest Documentation](https://docs.pytest.org/)

**Project-Specific:**
- [GitHub Repository](https://github.com/ryanranft/nba-simulator-aws)
- [API Documentation](docs/api/) - (In progress, see 0.0021)
- [ADR Index](docs/adr/README.md)
- [Workflow Index](docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Getting Help:**
- Team Slack: `#nba-simulator-dev`
- GitHub Issues: Create issue with `question` label
- Team Lead: Direct message for urgent issues

---

## Feedback

**This onboarding guide is a living document.** If you found steps unclear or ran into issues:

1. Create an issue: "Onboarding: [brief description of problem]"
2. Suggest improvements via PR to this file
3. Share feedback in retrospective meetings

**Estimated Completion Time:** 2 hours
**Last Updated:** October 31, 2025
**Maintained By:** NBA Simulator Dev Team
