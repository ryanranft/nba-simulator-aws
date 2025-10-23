## 📊 DIMS Management Workflow

**Purpose:** Verify and update project metrics using the Data Inventory Management System (DIMS)

**System:** DIMS v1.0.0 - Comprehensive data inventory tracking and verification

**When to run:**
- Automatically at session start (via `session_manager.sh`)
- Automatically at session end (via `session_end.sh`)
- Weekly maintenance (Monday or every 7 days)
- Before creating reports or status updates
- After major file changes (adding/removing 10+ files)
- When metrics appear stale (>7 days old)

### Quick Commands

```bash
# Daily verification (quick check)
python scripts/monitoring/dims_cli.py verify

# Verify and auto-update drifted metrics
python scripts/monitoring/dims_cli.py verify --update

# Full system refresh (weekly)
python scripts/monitoring/dims_cli.py snapshot
python scripts/monitoring/dims_cli.py update
python scripts/monitoring/dims_cli.py generate

# View specific metric trend
python scripts/monitoring/dims_cli.py history s3_storage.total_objects --days 30

# Cache management
python scripts/monitoring/dims_cli.py cache info
python scripts/monitoring/dims_cli.py cache cleanup
```

### What is DIMS?

**DIMS (Data Inventory Management System)** automatically tracks and verifies 25+ project metrics across 9 categories:

**Tracked Metrics:**
1. **S3 Storage** - Object counts, storage size, hoopr files (volatile)
2. **Prediction System** - Line counts for 7 ML scripts (stable)
3. **Plus/Minus System** - Python, SQL, documentation lines (stable)
4. **Code Base** - Python files, ML scripts, test files (volatile)
5. **Documentation** - Markdown files, total size (volatile)
6. **Git Metrics** - Book recommendation commits (stable)
7. **Workflows** - Workflow count in `docs/claude_workflows/` (stable)
8. **SQL Schemas** - Total lines in master schema (stable)
9. **Local Data** - ESPN data size (disabled by default, volatile)

**Key Capabilities:**
- ✅ Auto-detect drift from baseline values
- ✅ TTL-based caching (reduces AWS API calls)
- ✅ Daily snapshots (historical trend tracking)
- ✅ Multi-format output (Markdown, JSON, HTML, Jupyter)
- ✅ Per-metric verification and updates
- ✅ Configurable thresholds for drift severity

### Automated Integration

**Session Start (Workflow #01):**
```bash
# Runs automatically in scripts/shell/session_manager.sh
python scripts/monitoring/dims_cli.py verify --quiet

# Shows:
# ✅ All metrics OK (no drift)
# OR
# ⚠️  3 metrics drifted (s3_storage.total_objects +5.2%, code_base.python_files +2.1%, documentation.markdown_files +3.8%)
```

**Session End (Workflow #14):**
```bash
# Runs automatically in scripts/shell/session_end.sh
python scripts/monitoring/dims_cli.py verify --update

# Auto-updates any drifted metrics before session closes
```

### Manual Operations

#### Verify Metrics (No Changes)

**All metrics:**
```bash
python scripts/monitoring/dims_cli.py verify

# Output:
# ✅ s3_storage.total_objects: 172,726 (OK)
# ✅ s3_storage.total_size_gb: 118.26 GB (OK)
# ⚠️  code_base.python_files: 1,308 (drifted +3.2% from 1,268)
# ✅ documentation.markdown_files: 1,719 (OK)
# ...
#
# Summary: 22/25 OK, 3 drifted
```

**Single category:**
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage

# Verifies only: total_objects, total_size_gb, hoopr_files
```

**Single metric:**
```bash
python scripts/monitoring/dims_cli.py verify --category code_base --metric python_files

# Verifies only: code_base.python_files
```

#### Update Metrics (Save Changes)

**Auto-update drifted metrics:**
```bash
python scripts/monitoring/dims_cli.py verify --update

# Verifies all metrics, updates only those with drift
```

**Update all metrics:**
```bash
python scripts/monitoring/dims_cli.py update

# Forces refresh of all 25 metrics (ignores cache)
```

**Update single metric:**
```bash
python scripts/monitoring/dims_cli.py update --category s3_storage --metric total_objects

# Updates only s3_storage.total_objects (useful after S3 sync)
```

#### Generate Reports

**All formats:**
```bash
python scripts/monitoring/dims_cli.py generate

# Creates:
# - inventory/outputs/metrics_report.md (Markdown table)
# - inventory/outputs/metrics_report.json (structured data)
# - inventory/outputs/metrics_report.html (web dashboard)
# - inventory/outputs/metrics_report.ipynb (Jupyter notebook)
```

**Single format:**
```bash
python scripts/monitoring/dims_cli.py generate --format markdown
python scripts/monitoring/dims_cli.py generate --format json
```

#### Snapshots and History

**Create daily snapshot:**
```bash
python scripts/monitoring/dims_cli.py snapshot

# Saves current metrics to: inventory/historical/YYYY-MM-DD.yaml
```

**View metric trend:**
```bash
# Last 30 days
python scripts/monitoring/dims_cli.py history s3_storage.total_objects --days 30

# Output:
# 2025-10-01: 168,432 objects
# 2025-10-08: 170,891 objects (+2,459)
# 2025-10-15: 171,523 objects (+632)
# 2025-10-22: 172,726 objects (+1,203)
#
# Trend: +4,294 objects over 30 days (+2.5%)
```

**Compare snapshots:**
```bash
# Compare current metrics to snapshot from 7 days ago
python scripts/monitoring/dims_cli.py diff --since 2025-10-16

# Shows deltas for all metrics
```

#### Cache Management

**View cache stats:**
```bash
python scripts/monitoring/dims_cli.py cache info

# Output:
# Cache backend: file
# Cache location: inventory/cache/
# Total entries: 18
# Active (not expired): 12
# Expired: 6
# Total size: 2.4 MB
```

**Clear expired entries:**
```bash
python scripts/monitoring/dims_cli.py cache cleanup

# Removes only expired entries (recommended)
```

**Clear all cache:**
```bash
python scripts/monitoring/dims_cli.py cache clear

# Forces full refresh on next verify/update
```

### Drift Detection

DIMS automatically detects when metrics drift from their baseline values.

**Drift Thresholds:**

| Drift % | Status | Volatile Metrics | Stable Metrics |
|---------|--------|------------------|----------------|
| 0% | ✅ OK | None | None |
| <5% | ⚠️ Minor | Low | Medium |
| 5-15% | ⚠️ Moderate | Medium | High |
| 15-25% | ⚠️ Major | High | Critical |
| >25% | ❌ Critical | Critical | Critical |

**Metric Volatility:**

**Volatile metrics** (expected to change frequently):
- `s3_storage.*` - S3 buckets change with scraper runs
- `code_base.python_files` - New scripts added regularly
- `code_base.test_files` - Tests added/removed
- `documentation.markdown_files` - Docs frequently updated

**Stable metrics** (should rarely change):
- `prediction_system.*` - Core ML pipeline stable
- `plus_minus_system.*` - Feature implementation complete
- `git.book_recommendation_commits` - Historical count (214)
- `sql_schemas.total_lines` - Schema changes are rare

**Example - Volatile metric with 8% drift:**
```
⚠️  s3_storage.total_objects: 186,234 (drifted +8.2% from 172,000)
Severity: Medium (volatile metric, moderate drift)
Action: No immediate action needed (expected growth from scraper)
```

**Example - Stable metric with 8% drift:**
```
❌ prediction_system.total_lines: 2,271 (drifted +8.0% from 2,103)
Severity: High (stable metric, moderate drift)
Action: Investigate - stable code should not change this much
```

### Integration with Other Workflows

**Workflow #01 (Session Start):**
```bash
# session_manager.sh runs DIMS verify
bash scripts/shell/session_manager.sh start

# Shows drift status in startup summary
```

**Workflow #13 (File Inventory):**
```bash
# Both track project files - use together
make inventory              # Updates FILE_INVENTORY.md
dims_cli.py verify --update # Updates DIMS metrics

# FILE_INVENTORY: Detailed file-by-file metadata
# DIMS: High-level aggregate counts and trends
```

**Workflow #14 (Session End):**
```bash
# session_end.sh runs DIMS auto-update
bash scripts/shell/session_end.sh

# Ensures metrics stay current as files change
```

**Workflow #20 (Maintenance Schedule):**
```bash
# Weekly maintenance (every Monday)
dims_cli.py snapshot     # Capture weekly baseline
dims_cli.py update       # Refresh all metrics
dims_cli.py generate     # Regenerate reports
dims_cli.py cache cleanup # Remove stale cache
```

### Use Cases

**1. Project Health Check**
```bash
# Quick status before starting work
dims_cli.py verify

# ✅ All systems normal
# OR
# ⚠️  Unexpected drift detected - investigate before proceeding
```

**2. Track S3 Growth Over Time**
```bash
# View S3 object count trend
dims_cli.py history s3_storage.total_objects --days 90

# Use to:
# - Verify scraper is collecting data consistently
# - Detect unexpected S3 deletions (negative trend)
# - Correlate with cost increases (Workflow #18)
```

**3. Verify Code Reorganization**
```bash
# Before reorganization
dims_cli.py snapshot

# After moving files
dims_cli.py verify

# Confirm file counts match expected changes
# Example: Moved 20 test files → test_files should be same count
```

**4. Documentation Completeness**
```bash
# Check documentation growth
dims_cli.py history documentation.markdown_files --days 30

# Ensure docs keep pace with code:
# - Code growing faster than docs? → Need more documentation
# - Docs growing but code stable? → Good documentation practice
```

**5. Pre-Report Verification**
```bash
# Before creating status report
dims_cli.py update
dims_cli.py generate --format markdown

# Use inventory/outputs/metrics_report.md in reports
```

**6. Troubleshooting Test Failures**
```bash
# Check if test files changed unexpectedly
dims_cli.py verify --category code_base --metric test_files

# If drifted:
# - Expected? New tests added
# - Unexpected? Tests deleted or moved - investigate
```

### Best Practices

**Update frequency:**
- ✅ Session start: Verify only (quick check)
- ✅ Session end: Verify + auto-update (keep current)
- ✅ Weekly: Full refresh (snapshot + update + generate)
- ✅ Monthly: Review historical trends

**When to investigate drift:**
- ✅ Stable metric drifts >5% → Always investigate
- ✅ Volatile metric drifts >25% → Investigate unusual spike
- ✅ Negative drift → Investigate potential data loss

**Cache strategy:**
- ✅ Use cache for S3 metrics (slow to query)
- ✅ Weekly cleanup of expired cache
- ✅ Clear cache after major infrastructure changes

**Snapshot strategy:**
- ✅ Daily snapshots during active development
- ✅ Weekly snapshots during maintenance
- ✅ Keep snapshots for 90 days minimum
- ✅ Archive yearly snapshots permanently

### Troubleshooting

**Problem: DIMS verify shows all metrics as "Unknown"**
```bash
# Cause: inventory/metrics.yaml missing or corrupt
# Solution: Run full update to rebuild metrics
dims_cli.py update

# This will query all metrics fresh and save to metrics.yaml
```

**Problem: "ModuleNotFoundError: No module named 'dims'"**
```bash
# Cause: Running from wrong directory
# Solution: DIMS must run from project root
cd /Users/ryanranft/nba-simulator-aws
python scripts/monitoring/dims_cli.py verify
```

**Problem: S3 metrics show "Command failed" error**
```bash
# Cause: AWS credentials not loaded
# Solution: Source AWS credentials first
source ~/.aws/nba_simulator_credentials.sh
dims_cli.py verify --category s3_storage
```

**Problem: Metrics show extreme drift (>50%) after code changes**
```bash
# Cause: Metrics not updated after file reorganization
# Solution: Update metrics to new baseline
dims_cli.py update

# Then create snapshot for future comparison
dims_cli.py snapshot
```

**Problem: Cache shows large size (>10 MB)**
```bash
# Cause: Cache accumulation over time
# Solution: Clear cache and rebuild
dims_cli.py cache clear
dims_cli.py verify --update
```

**Problem: History command shows "No historical data"**
```bash
# Cause: No snapshots exist yet
# Solution: Create initial snapshot
dims_cli.py snapshot

# Future snapshots will enable trend analysis
```

**Problem: Verify runs very slowly (>2 minutes)**
```bash
# Cause: S3 metrics querying large bucket without cache
# Solution: Enable cache for S3 metrics

# Check cache status
dims_cli.py cache info

# If disabled, enable in inventory/config.yaml:
# cache:
#   enabled: true
#   backend: file
```

**Problem: "Permission denied" when writing metrics**
```bash
# Cause: inventory/ directory permissions
# Solution: Check and fix permissions
ls -la inventory/
chmod 755 inventory/
chmod 644 inventory/metrics.yaml
```

### Technical Details

**File Locations:**
```
inventory/
├── config.yaml          # DIMS configuration (254 lines)
├── metrics.yaml         # Current metrics - SSOT (167 lines)
├── cache/               # TTL-based cache storage
├── historical/          # Daily snapshots (YYYY-MM-DD.yaml)
└── outputs/             # Generated reports (MD, JSON, HTML, IPYNB)

scripts/monitoring/
├── dims_cli.py          # Command-line interface (488 lines)
└── dims/
    ├── core.py          # CRUD operations (551 lines)
    ├── cache.py         # TTL caching (448 lines)
    └── outputs.py       # Report generation (582 lines)

docs/monitoring/dims/
├── IMPLEMENTATION_SUMMARY.md  # System overview
├── QUICK_REFERENCE.md         # Command reference
└── PHASE_2_SUMMARY.md         # Future enhancements
```

**Total:** ~2,490 lines of production code

**Performance:**
- Verify (cached): <2 seconds
- Verify (uncached S3): 10-15 seconds
- Update all: 15-30 seconds
- Snapshot: <1 second
- Generate reports: 2-5 seconds

**Future Enhancements (Phase 2 - Planned):**
- PostgreSQL backend (currently YAML)
- Event streaming (real-time metric updates)
- Alert system (email/Slack on critical drift)
- Web dashboard (live metric monitoring)
- Cost correlation (link S3 growth to AWS costs)
- Automated recommendations ("S3 growing 10%/week - increase budget")

### Related Documentation

- **DIMS Implementation:** `docs/monitoring/dims/IMPLEMENTATION_SUMMARY.md`
- **Quick Reference:** `docs/monitoring/dims/QUICK_REFERENCE.md`
- **Configuration:** `inventory/config.yaml` (metric definitions, thresholds)
- **ADCE System:** `docs/automation/ADCE_MASTER_INDEX.md` (related automation)
- **Workflow #13:** File Inventory (complementary file tracking)
- **Workflow #20:** Maintenance Schedule (weekly DIMS refresh)

---

**Last Updated:** October 23, 2025
**DIMS Version:** 1.0.0
**Status:** ✅ Phase 1 Complete - Integrated into session workflows
