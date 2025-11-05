# NBA Simulator AWS - Workflow Deployment Guide

**Version:** 1.0.0
**Date:** November 5, 2025
**Status:** Production Ready

---

## Overview

This guide covers deployment of the 3 Python workflows migrated from shell scripts:

1. **Overnight Unified Workflow** (`overnight_unified_cli.py`) - Daily 3:00 AM
2. **3-Source Validation Workflow** (`validation_cli.py`) - Daily 4:00 AM
3. **Daily Update Workflow** (`daily_update_cli.py`) - Every 6 hours

**Deployment Options:**
- **Systemd** (Linux) - Recommended for production servers
- **Cron** (Linux/macOS) - Simple alternative
- **LaunchAgent** (macOS) - Native macOS scheduler

---

## Prerequisites

### System Requirements
- Python 3.11+
- 4GB+ RAM (8GB recommended)
- 50GB+ disk space
- Network access to AWS S3, data sources

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import asyncpg; print(' asyncpg installed')"
python -c "from nba_simulator.workflows import BaseWorkflow; print(' workflows ready')"
```

### Environment Setup
```bash
# 1. Clone/update repository
cd /Users/ryanranft/nba-simulator-aws
git pull origin main

# 2. Activate conda environment
conda activate nba-aws

# 3. Create log directories
mkdir -p logs/{cron,overnight,validation,daily_update}
mkdir -p reports/{validation,quality}
mkdir -p .workflow_state

# 4. Verify AWS credentials
aws s3 ls s3://nba-sim-raw-data-lake/ || echo "  AWS credentials needed"

# 5. Test dry-run mode
python scripts/workflows/overnight_unified_cli.py --dry-run
python scripts/workflows/validation_cli.py --dry-run
python scripts/workflows/daily_update_cli.py --dry-run
```

---

## Deployment Option 1: Systemd (Recommended)

### 1. Install Service Files

```bash
# Copy service and timer files
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo cp deployment/systemd/*.timer /etc/systemd/system/

# Set permissions
sudo chmod 644 /etc/systemd/system/nba-*.{service,timer}
sudo chmod 644 /etc/systemd/system/overnight-unified.{service,timer}
sudo chmod 644 /etc/systemd/system/validation.{service,timer}
sudo chmod 644 /etc/systemd/system/daily-update.{service,timer}

# Reload systemd
sudo systemctl daemon-reload
```

### 2. Enable Timers

```bash
# Enable timers (start on boot)
sudo systemctl enable overnight-unified.timer
sudo systemctl enable validation.timer
sudo systemctl enable daily-update.timer

# Start timers immediately
sudo systemctl start overnight-unified.timer
sudo systemctl start validation.timer
sudo systemctl start daily-update.timer

# Verify timers are active
systemctl list-timers --all | grep nba
```

### 3. Verify Installation

```bash
# Check timer status
systemctl status overnight-unified.timer
systemctl status validation.timer
systemctl status daily-update.timer

# View next run times
systemctl list-timers | grep -E "(overnight|validation|daily-update)"

# Expected output:
# NEXT                          LEFT        LAST  PASSED  UNIT                       ACTIVATES
# Wed 2025-11-06 03:00:00 CST  7h left     n/a   n/a     overnight-unified.timer    overnight-unified.service
# Wed 2025-11-06 04:00:00 CST  8h left     n/a   n/a     validation.timer           validation.service
# Wed 2025-11-06 00:00:00 CST  4h left     n/a   n/a     daily-update.timer         daily-update.service
```

### 4. Monitor Execution

```bash
# View logs (real-time)
journalctl -u overnight-unified.service -f
journalctl -u validation.service -f
journalctl -u daily-update.service -f

# View logs (historical)
journalctl -u overnight-unified.service --since "1 hour ago"
journalctl -u validation.service --since today
journalctl -u daily-update.service -n 100

# Check last run status
systemctl status overnight-unified.service
systemctl status validation.service
systemctl status daily-update.service
```

### 5. Manual Execution

```bash
# Trigger workflow manually (bypasses timer)
sudo systemctl start overnight-unified.service
sudo systemctl start validation.service
sudo systemctl start daily-update.service

# Watch execution
journalctl -u overnight-unified.service -f
```

### 6. Disable/Remove

```bash
# Stop timers
sudo systemctl stop overnight-unified.timer
sudo systemctl stop validation.timer
sudo systemctl stop daily-update.timer

# Disable (won't start on boot)
sudo systemctl disable overnight-unified.timer
sudo systemctl disable validation.timer
sudo systemctl disable daily-update.timer

# Remove (optional)
sudo rm /etc/systemd/system/nba-*.{service,timer}
sudo rm /etc/systemd/system/overnight-unified.{service,timer}
sudo rm /etc/systemd/system/validation.{service,timer}
sudo rm /etc/systemd/system/daily-update.{service,timer}
sudo systemctl daemon-reload
```

---

## Deployment Option 2: Cron

### 1. Install Crontab

```bash
# Create log directory
mkdir -p logs/cron

# Install crontab
crontab deployment/cron/nba-workflows.crontab

# Verify installation
crontab -l

# Expected output:
# 0 3 * * * cd /Users/ryanranft/nba-simulator-aws && /opt/homebrew/bin/python3 scripts/workflows/overnight_unified_cli.py >> logs/cron/overnight-unified.log 2>&1
# 0 4 * * * cd /Users/ryanranft/nba-simulator-aws && /opt/homebrew/bin/python3 scripts/workflows/validation_cli.py >> logs/cron/validation.log 2>&1
# 0 */6 * * * cd /Users/ryanranft/nba-simulator-aws && /opt/homebrew/bin/python3 scripts/workflows/daily_update_cli.py >> logs/cron/daily-update.log 2>&1
```

### 2. Monitor Execution

```bash
# View logs (real-time)
tail -f logs/cron/overnight-unified.log
tail -f logs/cron/validation.log
tail -f logs/cron/daily-update.log

# View logs (last 50 lines)
tail -50 logs/cron/overnight-unified.log
tail -50 logs/cron/validation.log
tail -50 logs/cron/daily-update.log

# Check cron service status
# Linux:
systemctl status cron
# macOS:
sudo launchctl list | grep cron
```

### 3. Manual Execution

```bash
# Run workflow manually (same as cron would execute)
cd /Users/ryanranft/nba-simulator-aws
/opt/homebrew/bin/python3 scripts/workflows/overnight_unified_cli.py >> logs/cron/overnight-unified.log 2>&1
```

### 4. Disable/Remove

```bash
# Remove crontab entries
crontab -e  # Edit and delete lines

# Or remove entire crontab
crontab -r

# Verify removal
crontab -l
```

---

## Deployment Option 3: Manual CLI

For testing or one-off executions:

```bash
# Navigate to project directory
cd /Users/ryanranft/nba-simulator-aws

# Activate environment
conda activate nba-aws

# Run workflows
python scripts/workflows/overnight_unified_cli.py
python scripts/workflows/validation_cli.py
python scripts/workflows/daily_update_cli.py

# With options
python scripts/workflows/overnight_unified_cli.py --dry-run
python scripts/workflows/overnight_unified_cli.py --resume
python scripts/workflows/overnight_unified_cli.py --verbose
python scripts/workflows/overnight_unified_cli.py --status
```

---

## Workflow Configuration

### Default Schedules

| Workflow | Schedule | Duration | Description |
|----------|----------|----------|-------------|
| **Overnight Unified** | Daily 3:00 AM | 30-60 min | Multi-source data collection |
| **Validation** | Daily 4:00 AM | 10-20 min | Cross-source validation |
| **Daily Update** | Every 6 hours | 5-10 min | Quick ESPN updates |

### Custom Configuration

Edit YAML files in workflow directories:

```bash
# Overnight Unified
vim docs/phases/phase_0/0.0023_overnight_unified/config/default_config.yaml

# Validation
vim docs/phases/phase_0/0.0024_validation_workflow/config/default_config.yaml

# Daily Update
vim docs/phases/phase_0/0.0025_daily_update/config/default_config.yaml
```

**Common Parameters:**
- `scraping.days_back`: Number of days to scrape (default: 3-7)
- `scraping.rate_limit`: Requests per second (default: 0.5)
- `dims.enabled`: DIMS metrics tracking (default: true)
- `notifications.slack_enabled`: Slack notifications (default: false)

---

## Monitoring & Alerting

### Log Locations

**Systemd:**
```bash
journalctl -u overnight-unified.service
journalctl -u validation.service
journalctl -u daily-update.service
```

**Cron:**
```bash
logs/cron/overnight-unified.log
logs/cron/validation.log
logs/cron/daily-update.log
```

**Workflow-specific:**
```bash
logs/overnight/workflow_*.log
logs/validation/workflow_*.log
logs/daily_update/workflow_*.log
```

### Health Checks

```bash
# Check workflow status
python scripts/workflows/overnight_unified_cli.py --status
python scripts/workflows/validation_cli.py --status
python scripts/workflows/daily_update_cli.py --status

# Check DIMS metrics
python scripts/monitoring/dims_cli.py verify

# Check ADCE autonomous loop
python scripts/autonomous/autonomous_cli.py status
```

### Success Indicators

 **Overnight Unified**
- All 11 tasks complete
- Quality score e 85%
- No critical task failures

 **Validation**
- At least 2/3 sources succeed
- Discrepancies < 5%
- Cross-validation report generated

 **Daily Update**
- ESPN scraper triggered
- Local database updated
- Catalog refreshed

### Alert Conditions

  **Warning**
- Non-critical task failure
- Quality score 70-85%
- 1 source failed (validation)

=¨ **Critical**
- Critical task failure
- Quality score < 70%
- 2+ sources failed (validation)
- Workflow timeout

---

## Troubleshooting

### Common Issues

**Issue: Workflow won't start**
```bash
# Check systemd timer
systemctl status overnight-unified.timer

# Check service file syntax
systemd-analyze verify /etc/systemd/system/overnight-unified.service

# Check Python environment
which python3
python3 --version  # Should be 3.11+
```

**Issue: Import errors**
```bash
# Verify all imports work
python -c "from nba_simulator.workflows import BaseWorkflow; print('')"

# Check asyncpg
python -c "import asyncpg; print(' asyncpg installed')"

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: Permission denied**
```bash
# Check file permissions
ls -la scripts/workflows/*.py

# Make executable
chmod +x scripts/workflows/*.py

# Check systemd service user
sudo systemctl cat overnight-unified.service | grep User=
```

**Issue: AWS credentials**
```bash
# Verify credentials
aws s3 ls s3://nba-sim-raw-data-lake/

# Check .env file
cat .env | grep AWS

# Reconfigure
aws configure
```

**Issue: Workflow stuck/hanging**
```bash
# Check running processes
ps aux | grep python | grep workflow

# Kill stuck process
pkill -f overnight_unified_cli.py

# Check logs for errors
tail -100 logs/cron/overnight-unified.log
```

---

## Rollback Procedures

### Revert to Shell Scripts

If Python workflows fail, original shell scripts are archived:

```bash
# Restore shell scripts
cp scripts/archive/pre_python_migration/*.sh scripts/workflows/

# Make executable
chmod +x scripts/workflows/*.sh

# Run manually
bash scripts/workflows/overnight_multi_source_unified.sh
bash scripts/workflows/overnight_3_source_validation.sh
bash scripts/workflows/daily_espn_update.sh
```

### Disable Python Workflows

```bash
# Systemd
sudo systemctl stop overnight-unified.timer
sudo systemctl stop validation.timer
sudo systemctl stop daily-update.timer
sudo systemctl disable overnight-unified.timer
sudo systemctl disable validation.timer
sudo systemctl disable daily-update.timer

# Cron
crontab -e  # Comment out workflow lines
```

---

## Production Checklist

Before deploying to production:

- [ ] All dependencies installed (`requirements.txt`)
- [ ] AWS credentials configured
- [ ] Log directories created
- [ ] Dry-run mode tested (all 3 workflows)
- [ ] Configuration files reviewed
- [ ] Deployment method chosen (systemd/cron)
- [ ] Services installed and enabled
- [ ] First run monitored
- [ ] Logs verified
- [ ] Health checks passing
- [ ] DIMS metrics integrated
- [ ] Slack notifications configured (optional)
- [ ] Backup procedures documented

---

## Support

**Documentation:**
- Workflow Migration: `docs/phases/phase_0/0.0023-0.0025_MIGRATION_SUMMARY.md`
- Import Issues: `docs/phases/phase_0/0.0023-0.0025_IMPORT_ISSUES_RESOLVED.md`
- Testing Framework: `docs/claude_workflows/workflow_descriptions/41_testing_framework.md`

**Commands:**
```bash
# Get help
python scripts/workflows/overnight_unified_cli.py --help
python scripts/workflows/validation_cli.py --help
python scripts/workflows/daily_update_cli.py --help

# Validate configuration
python scripts/workflows/overnight_unified_cli.py --validate-config
python scripts/workflows/validation_cli.py --validate-config
python scripts/workflows/daily_update_cli.py --validate-config
```

**Logs:**
- GitHub Issues: https://github.com/ryanranft/nba-simulator-aws/issues
- Project Documentation: `docs/README.md`
- PROGRESS.md: Latest updates and status

---

**Last Updated:** November 5, 2025
**Version:** 1.0.0
**Status:**  Production Ready
