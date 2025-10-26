# Quick Start Guide

<!-- AUTO-UPDATE TRIGGER: When daily workflow changes (new commands, file locations, workflow shortcuts) -->
<!-- LAST UPDATED: 2025-10-07 -->
<!-- FREQUENCY: As needed (when workflow evolves) -->
<!-- REMINDER: Update when new daily commands added, file locations changed, or common troubleshooting steps identified -->

**One-page reference for common tasks - Now with temporal query examples!**

> **🕐 NEW: Temporal Panel Data System** - Query NBA stats at exact timestamps with millisecond precision. See [Temporal Query Examples](#temporal-query-examples) below.

---

## Daily Workflow

```bash
# 1. Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# 2. Activate environment
conda activate nba-aws

# 3. Run session startup (recommended at start of each session)
bash scripts/shell/session_startup.sh

# 4. Check Git status
git status

# 5. Start working!

# 6. At session end
bash scripts/shell/session_end.sh
```

---

## Autonomous Data Collection

**ADCE (Autonomous Data Collection Ecosystem)** runs 24/7 to automatically detect and fill data gaps:

```bash
# Start autonomous loop
python scripts/autonomous/autonomous_cli.py start

# Check system status
python scripts/autonomous/autonomous_cli.py status

# View logs
python scripts/autonomous/autonomous_cli.py logs --tail 100

# Check task queue
python scripts/autonomous/autonomous_cli.py tasks

# Health check
curl http://localhost:8080/health

# Stop system
python scripts/autonomous/autonomous_cli.py stop
```

**Full Documentation:** [Autonomous Operation Guide](docs/AUTONOMOUS_OPERATION.md)
**Phase Documentation:** [0.0009: ADCE](docs/phases/phase_0/0.0009_autonomous_data_collection/README.md)

---

## Common Commands

### Environment
```bash
# Activate conda environment
conda activate nba-aws

# Check Python version
python --version  # Should be 3.11.13

# Check installed packages
pip list
```

### AWS
```bash
# Check who you're logged in as
aws sts get-caller-identity

# List S3 bucket contents
aws s3 ls s3://nba-sim-raw-data-lake/

# Check current AWS costs
./scripts/aws/check_costs.sh

# Download sample file
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json ./sample.json
```

### Git
```bash
# Check status
git status

# Pull latest changes
git pull origin main --rebase

# Stage and commit changes
git add filename
git commit -m "Your message"

# Push to GitHub
git push origin main

# View commit history
git log --oneline -10
```

### Command Logging
```bash
# Load logging functions
source scripts/shell/log_command.sh

# Execute and log command
log_cmd aws s3 ls s3://nba-sim-raw-data-lake/

# Add note to last command
log_note This command lists all S3 folders

# Add solution to last error
log_solution Fixed by updating AWS credentials
```

### Conversation Tracking
```bash
# RECOMMENDED WORKFLOW (captures conversation → commit linkage):

# 1. Export Claude Code conversation
#    - In Claude Code, export this conversation
#    - Save as: CHAT_LOG.md in project root

# 2. Commit your changes
git add .
git commit -m "Your commit message"

# 3. Archive conversation with commit SHA
bash scripts/maintenance/archive_chat_by_next_sha.sh
#    - Saves as: chat-<SHA>-original.md (with credentials)
#    - Saves as: chat-<SHA>-sanitized.md (safe to share)
#    - Archive location: ~/sports-simulator-archives/nba/conversations/

# 4. Clean up (optional)
rm CHAT_LOG.md  # Remove temporary file

# Session end checklist (shows reminders)
bash scripts/shell/session_end.sh
```

---

## Key File Locations

```
/Users/ryanranft/nba-simulator-aws/
├── CLAUDE.md                    # Quick reference for Claude Code
├── PROGRESS.md                  # Detailed project status
├── COMMAND_LOG.md               # Command execution history
├── .env.example                 # Environment variables template
├── docs/
│   ├── SETUP.md                 # Complete setup guide
│   ├── STYLE_GUIDE.md           # Code style preferences
│   ├── TESTING.md               # Testing strategy
│   ├── TROUBLESHOOTING.md       # Common issues & solutions
│   └── adr/                     # Architecture decisions
├── scripts/
│   ├── shell/
│   │   ├── session_startup.sh    # Session initialization checklist
│   │   ├── session_end.sh        # Session end reminder
│   │   ├── check_chat_log.sh     # Verify CHAT_LOG.md before commits
│   │   ├── check_machine_health.sh  # Comprehensive health check
│   │   ├── log_command.sh        # Command logging
│   │   └── sanitize_command_log.sh  # Security sanitization
│   ├── aws/
│   │   └── check_costs.sh        # AWS cost tracking
│   └── etl/                      # ETL scripts (⏸️ to be created)
├── sql/                         # Database schemas (⏸️ to be created)
└── tests/                       # Test files (⏸️ to be created)
```

---

## Quick Checks

### Is my environment set up correctly?
```bash
./scripts/shell/check_machine_health.sh
```

### Can I access AWS?
```bash
aws sts get-caller-identity
aws s3 ls s3://nba-sim-raw-data-lake/
```

### Is GitHub SSH working?
```bash
ssh -T git@github.com
# Should see: "Hi [username]! You've successfully authenticated..."
```

### What are my AWS costs?
```bash
./scripts/aws/check_costs.sh
```

---

## Scraper Operations

**Complete guide:** See Workflow #42 (`docs/claude_workflows/workflow_descriptions/42_scraper_management.md`)

### Launch Scrapers

**NBA API Comprehensive** (5-6 hours, 30 seasons):
```bash
nohup bash scripts/etl/overnight_nba_api_comprehensive.sh > /tmp/nba_api.log 2>&1 &
tail -f /tmp/nba_api.log
```

**hoopR Phase 1B** (30-60 minutes, 24 seasons):
```bash
nohup bash scripts/etl/run_hoopr_phase1b.sh > /tmp/hoopr.log 2>&1 &
tail -f /tmp/hoopr_phase1b_runner.log
```

**Basketball Reference** (3-4 hours, 2020-2025):
```bash
nohup bash scripts/etl/scrape_bbref_incremental.sh 2020 2025 > /tmp/bbref.log 2>&1 &
tail -f /tmp/bbref.log
```

**Kaggle Database** (10-15 minutes, one-time):
```bash
python scripts/etl/download_kaggle_basketball.py
```

**ESPN Gap Filler** (2-3 hours):
```bash
nohup bash scripts/etl/run_espn_scraper.sh > /tmp/espn_gap.log 2>&1 &
```

### Monitor Scrapers

**Check all running scrapers:**
```bash
ps aux | grep -E "scrape_nba_api|scrape_hoopr|scrape_bbref" | grep -v grep
```

**Monitor all logs:**
```bash
tail -f /tmp/nba_api.log /tmp/hoopr.log /tmp/bbref.log
```

**Emergency stop (kill all):**
```bash
ps aux | grep -E "scrape" | grep -v grep | awk '{print $2}' | xargs kill -9
```

### Related Workflows
- **Workflow #38:** Check scraper completion at session start
- **Workflow #41:** Validate scraper output with test suites
- **Workflow #42:** Complete scraper execution guide (900+ lines)

---

## Troubleshooting Quick Fixes

**Problem: Conda environment not found**
```bash
conda create -n nba-aws python=3.11.13 -y
conda activate nba-aws
pip install boto3 pandas numpy psycopg2-binary sqlalchemy
```

**Problem: AWS credentials not configured**
```bash
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1), Output (json)
```

**Problem: SSH permission denied**
```bash
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com
```

**Problem: Git push rejected**
```bash
git pull origin main --rebase
git push origin main
```

**Full troubleshooting guide:** See `docs/TROUBLESHOOTING.md`

---

## Next Steps

**Current Phase:** Phase 0 Complete (Data Collection), All 6 core phases complete

**Next Tasks:**
1. Set up AWS Glue Crawler (45 min) - See PROGRESS.md 2.0001
2. Provision RDS PostgreSQL (2-3 hrs) - See PROGRESS.md 3.0001
3. Create Glue ETL job (6-8 hrs) - See PROGRESS.md 2.0002

**Detailed plan:** See `PROGRESS.md`

---

## Documentation Map

| Need... | Read... |
|---------|---------|
| Claude Code guidelines | `CLAUDE.md` |
| Project status & roadmap | `PROGRESS.md` |
| Setup instructions | `docs/SETUP.md` |
| Code style rules | `docs/STYLE_GUIDE.md` |
| Testing approach | `docs/TESTING.md` |
| Common errors | `docs/TROUBLESHOOTING.md` |
| Why we made decisions | `docs/adr/README.md` |
| Command history | `COMMAND_LOG.md` |

---

## Cost Tracking

**Current:** ~$38.33/month (S3 + RDS + EC2)

**With temporal enhancement:** ~$57-75/month (+ temporal tables)

**Full deployment:** $82-100/month (+ SageMaker)

**Check costs:** `./scripts/aws/check_costs.sh`

---

## Temporal Query Examples

**This project is a temporal panel data system - query NBA stats at exact timestamps with millisecond precision.**

### Quick Temporal Queries

**Connect to database:**
```python
import psycopg2
from datetime import datetime
import pytz

conn = psycopg2.connect(
    host="nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com",
    database="nba_simulator",
    user="your_user",
    password="your_password"
)
cursor = conn.cursor()
```

**Example 1: Get player snapshot at exact timestamp**
```python
# "What were Kobe's stats at 7:02:34 PM on June 19, 2016?"
cursor.execute("""
    SELECT
        snapshot_time,
        games_played,
        career_points,
        career_rebounds,
        career_assists
    FROM
        get_player_snapshot_at_time(
            (SELECT player_id FROM players WHERE name = 'Kobe Bryant'),
            '2016-06-19 19:02:34-05:00'::TIMESTAMPTZ
        )
""")

result = cursor.fetchone()
print(f"At {result[0]}, Kobe had {result[2]} career points")
# Output: At 2016-06-19 19:02:34, Kobe had 33,636 career points
```

**Example 2: Calculate player age at exact moment**
```python
# "How old was Kobe when he scored his last point?"
cursor.execute("""
    SELECT calculate_player_age(
        (SELECT player_id FROM players WHERE name = 'Kobe Bryant'),
        '2016-06-19 22:30:00-05:00'::TIMESTAMPTZ
    )
""")

age = cursor.fetchone()[0]
print(f"Kobe's age: {age}")
# Output: 37 years, 300 days, 10 hours, 30 minutes
```

**Example 3: Get all active games at timestamp**
```python
# "What games were playing at 9:00 PM ET on March 15, 2023?"
cursor.execute("""
    SELECT
        g.home_team,
        g.away_team,
        gs.current_score_home,
        gs.current_score_away,
        gs.quarter
    FROM
        games g
    JOIN
        game_states gs ON g.game_id = gs.game_id
    WHERE
        gs.state_time = (
            SELECT MAX(state_time)
            FROM game_states
            WHERE game_id = g.game_id
              AND state_time <= '2023-03-15 21:00:00-04:00'::TIMESTAMPTZ
        )
        AND g.game_date = '2023-03-15'
    ORDER BY
        g.game_id
""")

for row in cursor.fetchall():
    print(f"{row[1]} @ {row[0]}: {row[3]}-{row[2]} (Q{row[4]})")
# Output: Lakers @ Warriors: 95-92 (Q3)
```

**Example 4: Filter by data precision**
```python
# "Get all second-precision data from 2020+"
cursor.execute("""
    SELECT
        COUNT(*) AS events,
        precision_level,
        data_source
    FROM
        temporal_events
    WHERE
        precision_level IN ('millisecond', 'second')
        AND wall_clock_utc >= '2020-01-01'
    GROUP BY
        precision_level, data_source
""")

for row in cursor.fetchall():
    print(f"{row[2]}: {row[0]:,} events ({row[1]} precision)")
# Output: nba_stats: 500,000 events (second precision)
```

**Complete guide:** See `docs/TEMPORAL_QUERY_GUIDE.md`

---

## Temporal Validation

**Run validation test suite:**
```bash
# Full test suite (25 tests)
pytest tests/test_temporal_queries.py -v

# Specific test class
pytest tests/test_temporal_queries.py::TestSnapshotQueries -v

# Single test
pytest tests/test_temporal_queries.py::TestSnapshotQueries::test_snapshot_query_performance -v
```

**Expected output:**
```
tests/test_temporal_queries.py::TestSnapshotQueries::test_get_player_snapshot_at_exact_time PASSED
tests/test_temporal_queries.py::TestSnapshotQueries::test_snapshot_query_performance PASSED
tests/test_temporal_queries.py::TestSnapshotQueries::test_snapshot_monotonicity PASSED
======================== 25 passed in 45.2s ========================
```

**Validation guide:** See `docs/TEMPORAL_VALIDATION_GUIDE.md`

---

## Temporal Data Availability

**Data precision by era:**

| Era | Precision | Data Source | Use Cases |
|-----|-----------|-------------|-----------|
| 2020-2025 | Millisecond | NBA Live API (future) | Video sync, real-time tracking |
| 2013-2019 | Second | NBA.com Stats | Temporal queries, ML features |
| 1999-2012 | Minute | ESPN API | General analysis, trends |
| 1946-1998 | Game-level | Basketball Reference | Career stats, historical analysis |

**Check precision coverage:**
```sql
SELECT
    precision_level,
    COUNT(*) AS events,
    MIN(wall_clock_utc) AS earliest,
    MAX(wall_clock_utc) AS latest
FROM
    temporal_events
GROUP BY
    precision_level
ORDER BY
    earliest;
```

**Data sources:** See `docs/DATA_SOURCES.md` for complete temporal data quality matrix

**Budget alerts:** Set up in AWS Console → Budgets

---

## Getting Help

1. **Environment issues?** → `./scripts/shell/check_machine_health.sh`
2. **Common errors?** → `docs/TROUBLESHOOTING.md`
3. **How to...?** → `docs/SETUP.md` or `PROGRESS.md`
4. **Why did we...?** → `docs/adr/README.md`
5. **Past solutions?** → `COMMAND_LOG.md`

---

**Last Updated:** 2025-10-02