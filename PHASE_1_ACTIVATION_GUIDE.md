# Phase 1 Activation Guide
**NBA Simulator AWS - Priority 1: Activate Existing Systems**

**Created:** October 30, 2025
**Status:** Ready for Activation
**Estimated Time:** 2-4 hours
**Goal:** Production-ready autonomous system in 2 weeks

---

## Executive Summary

Phase 0 discovered that **95% of infrastructure is complete** - it just needs to be activated. This guide provides step-by-step instructions to activate:

1. **ADCE Autonomous Loop** (24/7 data collection)
2. **Phase 8 Box Score Generation** (scheduled processing)
3. **Alert System** (SNS notifications)
4. **Monitoring Dashboard** (health checks)

**Timeline:**
- Week 1: Basic activation and testing
- Week 2: Monitoring, optimization, and production deployment

---

## Prerequisites

✅ **Already Complete:**
- Phase 0 discovery finished
- Comprehensive backups created
- All infrastructure code exists
- Configuration files ready

⏸️ **Needed for Activation:**
- AWS Console access (for SNS setup)
- Email address for alerts
- 2-4 hours of testing time

---

## Part 1: ADCE Autonomous Loop Activation

### Status Check

```bash
# Check if autonomous loop is configured
cat config/autonomous_config.yaml | grep "enabled:"

# Check if CLI is available
python scripts/autonomous/autonomous_cli.py --help
```

**Expected:** `enabled: true` and CLI help output

---

### Option A: Manual Start (Testing)

**Step 1: Test in Dry-Run Mode**

```bash
# Start in dry-run mode (simulates without executing)
python scripts/autonomous/autonomous_cli.py start --dry-run

# Check status
python scripts/autonomous/autonomous_cli.py status

# View logs
tail -f logs/autonomous_loop.log
```

**Step 2: Start Production Mode**

```bash
# Stop dry-run
python scripts/autonomous/autonomous_cli.py stop

# Start production mode
python scripts/autonomous/autonomous_cli.py start

# Verify running
python scripts/autonomous/autonomous_cli.py status
python scripts/autonomous/autonomous_cli.py health
```

**Step 3: Monitor First Cycle**

```bash
# Watch logs in real-time
tail -f logs/autonomous_loop.log

# Check health endpoint
curl http://localhost:8080/health

# View task queue
python scripts/autonomous/autonomous_cli.py tasks
```

---

### Option B: Persistent Service (Production)

**For macOS (LaunchAgent):**

**Step 1: Install LaunchAgent**

```bash
# Copy plist to LaunchAgents
cp config/launchd/com.nba-simulator.adce-autonomous.plist \
   ~/Library/LaunchAgents/

# Enable the service
launchctl load ~/Library/LaunchAgents/com.nba-simulator.adce-autonomous.plist

# Start the service
launchctl start com.nba-simulator.adce-autonomous

# Check status
launchctl list | grep nba-simulator
```

**Step 2: Verify Running**

```bash
# Check process
ps aux | grep autonomous_loop

# View logs
tail -f logs/adce-autonomous.stdout.log
tail -f logs/adce-autonomous.stderr.log

# Check health
curl http://localhost:8080/health
```

**Step 3: Configure Auto-Start**

The LaunchAgent will automatically start on login. To start on boot:

```bash
# Edit plist and change RunAtLoad to true (already set)
# Service will start automatically on next boot
```

---

**For Linux (systemd):**

**Step 1: Install Systemd Service**

```bash
# Copy service file
sudo cp config/systemd/adce-autonomous.service \
        /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable adce-autonomous

# Start service
sudo systemctl start adce-autonomous

# Check status
sudo systemctl status adce-autonomous
```

**Step 2: Monitor**

```bash
# View logs
sudo journalctl -u adce-autonomous -f

# Check health
curl http://localhost:8080/health
```

---

### ADCE Configuration Tuning

**File:** `config/autonomous_config.yaml`

**Key Settings to Review:**

```yaml
# How often to run reconciliation (default: 1 hour)
reconciliation_interval_hours: 1

# Max concurrent scrapers (default: 5)
max_concurrent_scrapers: 5

# Enable alerts (change to true when SNS configured)
alerts:
  enabled: false  # Change to true after SNS setup
```

**Recommended Adjustments:**

- **Development:** `reconciliation_interval_hours: 4` (less frequent)
- **Production:** `reconciliation_interval_hours: 1` (hourly)
- **Aggressive:** `reconciliation_interval_hours: 0.5` (every 30 min)

---

## Part 2: Phase 8 Box Score Generation

### Understanding Phase 8

**What it does:**
- Generates temporal box score snapshots
- Processes play-by-play data into box scores
- Supports quarter/half/interval aggregations
- Enables millisecond-precision temporal queries

**Current Status:** Infrastructure complete, scheduling pending

---

### Option A: On-Demand Generation

**Generate box scores for specific games:**

```bash
# Generate box score for a single game
python scripts/pbp_to_boxscore/box_score_snapshot.py \
    --game-id "0022300001" \
    --timestamp "2023-10-24T19:30:00"

# Generate for all games in date range
python scripts/pbp_to_boxscore/batch_process_espn.py \
    --start-date "2023-10-24" \
    --end-date "2023-10-25"

# Validate generated box scores
python scripts/pbp_to_boxscore/validate_pbp_to_boxscore.py
```

---

### Option B: Scheduled Generation

**Create LaunchAgent for Daily Box Score Generation:**

**File:** `config/launchd/com.nba-simulator.box-score-daily.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nba-simulator.box-score-daily</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/ryanranft/miniconda3/envs/nba-aws/bin/python</string>
        <string>/Users/ryanranft/nba-simulator-aws/scripts/pbp_to_boxscore/batch_process_espn.py</string>
        <string>--yesterday</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/ryanranft/nba-simulator-aws</string>

    <!-- Run daily at 3 AM -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/ryanranft/nba-simulator-aws/logs/box-score-daily.stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/ryanranft/nba-simulator-aws/logs/box-score-daily.stderr.log</string>
</dict>
</plist>
```

**Install:**

```bash
# Copy plist
cp config/launchd/com.nba-simulator.box-score-daily.plist \
   ~/Library/LaunchAgents/

# Load service
launchctl load ~/Library/LaunchAgents/com.nba-simulator.box-score-daily.plist

# Test immediately (don't wait for 3 AM)
launchctl start com.nba-simulator.box-score-daily

# Check logs
tail -f logs/box-score-daily.stdout.log
```

---

### Option C: Integration with ADCE

**Add box score generation to autonomous loop:**

1. Box scores generated as part of ADCE reconciliation cycle
2. Automatically processes new games detected by scraper
3. Validates and stores in temporal_box_score_snapshots table

**This is the recommended production approach** - integrates seamlessly with ADCE.

---

## Part 3: Alert System (SNS Configuration)

### Why Alerts Matter

Alerts notify you when:
- ADCE autonomous loop stops unexpectedly
- Scraper orchestrator times out (>2 hours)
- Error rate exceeds 10%
- Critical tasks remain stale >24 hours

---

### Step 1: Create SNS Topic

**In AWS Console:**

1. Go to **AWS SNS Console**
2. Click **Create topic**
3. **Name:** `nba-simulator-adce-alerts`
4. **Type:** Standard
5. Click **Create topic**

**Or via AWS CLI:**

```bash
# Create SNS topic
aws sns create-topic --name nba-simulator-adce-alerts

# Save the TopicArn (will be something like):
# arn:aws:sns:us-east-1:575734508327:nba-simulator-adce-alerts
```

---

### Step 2: Create Email Subscription

**In AWS Console:**

1. Select the topic: `nba-simulator-adce-alerts`
2. Click **Create subscription**
3. **Protocol:** Email
4. **Endpoint:** your-email@example.com
5. Click **Create subscription**
6. **Check your email** and confirm subscription

**Or via AWS CLI:**

```bash
# Create email subscription
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:575734508327:nba-simulator-adce-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com

# Check your email and confirm
```

---

### Step 3: Configure ADCE Alerts

**Edit:** `config/autonomous_config.yaml`

**Change:**

```yaml
# Alert Configuration
alerts:
  enabled: true  # Change from false to true
  channels:
    email:
      enabled: true  # Enable email
      sns_topic_arn: "arn:aws:sns:us-east-1:575734508327:nba-simulator-adce-alerts"
      subject_prefix: "[ADCE Alert]"
```

**Restart ADCE:**

```bash
# If running as service
launchctl restart com.nba-simulator.adce-autonomous

# If running manually
python scripts/autonomous/autonomous_cli.py restart
```

---

### Step 4: Test Alerts

**Send test alert:**

```bash
# Create test alert script
cat > /tmp/test_alert.py << 'EOF'
import boto3

sns = boto3.client('sns', region_name='us-east-1')
sns.publish(
    TopicArn='arn:aws:sns:us-east-1:575734508327:nba-simulator-adce-alerts',
    Subject='[ADCE Alert] Test Alert',
    Message='This is a test alert from ADCE autonomous loop.'
)
print("✅ Test alert sent!")
EOF

python /tmp/test_alert.py
```

**Check your email** for the test alert.

---

## Part 4: Monitoring Dashboard

### Health Check Endpoints

**ADCE provides health check API:**

```bash
# Overall health
curl http://localhost:8080/health

# Component status
curl http://localhost:8080/status

# Metrics
curl http://localhost:8080/metrics
```

**Expected Response:**

```json
{
  "status": "healthy",
  "components": {
    "reconciliation_daemon": "running",
    "orchestrator": "idle",
    "task_queue": "empty"
  },
  "uptime_seconds": 3600,
  "last_cycle_time": "2025-10-30T15:30:00Z"
}
```

---

### DIMS Integration

**ADCE automatically updates DIMS metrics:**

```bash
# Check DIMS metrics
python scripts/monitoring/dims_cli.py verify

# View DIMS report
python scripts/monitoring/dims_cli.py report

# Open Jupyter notebook for interactive analysis
jupyter notebook docs/monitoring/dims/dims_analysis.ipynb
```

**Metrics tracked:**
- Autonomous cycles completed
- Tasks executed
- Orchestrator success rate
- Error counts
- Data collection velocity

---

### Log Monitoring

**Key log files:**

```bash
# ADCE autonomous loop
tail -f logs/autonomous_loop.log
tail -f logs/adce-autonomous.stdout.log

# Box score generation
tail -f logs/box-score-daily.stdout.log

# Scraper operations
tail -f logs/scraper_orchestrator.log
```

**Log Analysis:**

```bash
# Count errors in last hour
grep ERROR logs/autonomous_loop.log | grep "$(date -u +%Y-%m-%d)" | wc -l

# View recent alerts
grep ALERT logs/autonomous_loop.log | tail -20

# Check success rate
grep "Cycle complete" logs/autonomous_loop.log | tail -10
```

---

## Part 5: Testing & Validation

### Week 1: Initial Testing

**Day 1: Basic Activation**

```bash
# 1. Start ADCE in dry-run mode
python scripts/autonomous/autonomous_cli.py start --dry-run

# 2. Monitor for 1 hour
tail -f logs/autonomous_loop.log

# 3. Verify no errors
grep ERROR logs/autonomous_loop.log

# 4. Stop dry-run
python scripts/autonomous/autonomous_cli.py stop
```

**Day 2: Production Mode**

```bash
# 1. Start production mode
python scripts/autonomous/autonomous_cli.py start

# 2. Monitor first reconciliation cycle (1 hour)
# 3. Check task queue generation
python scripts/autonomous/autonomous_cli.py tasks

# 4. Verify scraper execution
ps aux | grep scraper
```

**Day 3-4: Box Score Testing**

```bash
# 1. Generate box scores for sample games
python scripts/pbp_to_boxscore/batch_process_espn.py --start-date "2023-10-24" --end-date "2023-10-25"

# 2. Validate results
python scripts/pbp_to_boxscore/validate_pbp_to_boxscore.py

# 3. Query temporal box scores
psql -h $RDS_HOST -U $DB_USER -d nba_simulator -c "SELECT COUNT(*) FROM temporal_box_score_snapshots;"
```

**Day 5: Alert Testing**

```bash
# 1. Configure SNS (see Part 3)
# 2. Enable alerts in config
# 3. Send test alert
# 4. Verify email received
```

---

### Week 2: Optimization

**Day 6-7: Performance Tuning**

```bash
# Monitor resource usage
python scripts/autonomous/autonomous_cli.py metrics

# Check memory usage
ps aux | grep python | grep autonomous

# Adjust concurrency if needed
# Edit config/autonomous_config.yaml: max_concurrent_scrapers
```

**Day 8-9: Error Handling**

```bash
# Review error logs
grep ERROR logs/autonomous_loop.log | sort | uniq -c

# Test failure recovery
# (simulate scraper failure, verify retry logic)

# Validate data quality
python scripts/monitoring/dims_cli.py verify
```

**Day 10: Production Readiness**

```bash
# ✅ Checklist:
# - ADCE running for 5+ days without crashes
# - Box scores generating daily
# - Alerts working
# - DIMS metrics healthy
# - Error rate < 10%
# - Task completion rate > 95%

# If all pass: System is production ready!
```

---

## Part 6: Troubleshooting

### ADCE Won't Start

**Symptoms:** `autonomous_cli.py start` fails

**Solutions:**

```bash
# Check if already running
python scripts/autonomous/autonomous_cli.py status

# Check for port conflicts
lsof -i :8080

# Check credentials
test -f /Users/ryanranft/nba-sim-credentials.env && echo "✅ Credentials exist"

# Check database connection
python -c "from nba_simulator.config.database import DatabaseConfig; print(DatabaseConfig.from_env())"

# View detailed error
tail -f logs/autonomous_loop.log
```

---

### High Error Rate

**Symptoms:** Error rate > 10%

**Solutions:**

```bash
# Identify failing scrapers
grep ERROR logs/autonomous_loop.log | grep "Scraper failed" | cut -d: -f4 | sort | uniq -c

# Reduce concurrency
# Edit config/autonomous_config.yaml: max_concurrent_scrapers: 3

# Increase retry delay
# Edit config/autonomous_config.yaml: retry_delay_seconds: 120

# Restart ADCE
python scripts/autonomous/autonomous_cli.py restart
```

---

### Box Scores Not Generating

**Symptoms:** No new records in temporal_box_score_snapshots

**Solutions:**

```bash
# Check if play_by_play data exists
psql -h $RDS_HOST -U $DB_USER -d nba_simulator -c "SELECT COUNT(*) FROM play_by_play WHERE game_date = CURRENT_DATE - 1;"

# Run generation manually
python scripts/pbp_to_boxscore/batch_process_espn.py --yesterday

# Check validation
python scripts/pbp_to_boxscore/validate_pbp_to_boxscore.py

# Review logs
tail -f logs/box-score-daily.stdout.log
```

---

### Alerts Not Receiving

**Symptoms:** No alert emails

**Solutions:**

```bash
# Check SNS subscription status
aws sns list-subscriptions-by-topic \
    --topic-arn arn:aws:sns:us-east-1:575734508327:nba-simulator-adce-alerts

# Verify email confirmed
# (Status should be "Confirmed", not "PendingConfirmation")

# Send test alert
aws sns publish \
    --topic-arn arn:aws:sns:us-east-1:575734508327:nba-simulator-adce-alerts \
    --message "Test alert"

# Check spam folder
# Check AWS SNS delivery logs in CloudWatch
```

---

## Part 7: Success Metrics

### Week 1 Goals

- ✅ ADCE running continuously for 5+ days
- ✅ Zero unhandled crashes
- ✅ Health check endpoint responding
- ✅ At least one complete reconciliation cycle
- ✅ Task queue generating successfully

### Week 2 Goals

- ✅ Box scores generating daily
- ✅ Alerts configured and tested
- ✅ Error rate < 10%
- ✅ Task completion rate > 95%
- ✅ DIMS metrics updating automatically

### Production Ready Criteria

- ✅ ADCE running for 10+ days without manual intervention
- ✅ Box score generation success rate > 98%
- ✅ Alerts working (test monthly)
- ✅ Monitoring dashboard functional
- ✅ Documentation complete (this guide)
- ✅ Team trained on operations

---

## Next Steps After Activation

**Week 3-4: Priority 2 - Orchestration Layer**

Once systems are running reliably:

1. **Build Scraper Orchestrator** (ADCE Phase 3)
   - Intelligent task prioritization
   - Global rate limit enforcement
   - Advanced error handling

2. **Implement Data Reconciliation** (ADCE Phase 2)
   - Real-time gap detection
   - Expected vs actual comparison
   - Automatic backfill

3. **Create Unified Monitoring Dashboard**
   - Grafana/Kibana integration
   - Real-time metrics visualization
   - Custom alerting rules

4. **Set Up CloudWatch Alarms**
   - RDS CPU/memory alerts
   - S3 bucket metrics
   - Lambda function errors

---

## Reference Commands

**Quick Reference Sheet:**

```bash
# ADCE Operations
python scripts/autonomous/autonomous_cli.py start       # Start
python scripts/autonomous/autonomous_cli.py stop        # Stop
python scripts/autonomous/autonomous_cli.py restart     # Restart
python scripts/autonomous/autonomous_cli.py status      # Status
python scripts/autonomous/autonomous_cli.py health      # Health
python scripts/autonomous/autonomous_cli.py logs -n 50  # View logs

# Box Score Generation
python scripts/pbp_to_boxscore/batch_process_espn.py --yesterday
python scripts/pbp_to_boxscore/validate_pbp_to_boxscore.py

# Monitoring
python scripts/monitoring/dims_cli.py verify            # DIMS verify
curl http://localhost:8080/health                       # Health check
tail -f logs/autonomous_loop.log                        # View logs

# LaunchAgent (macOS)
launchctl load ~/Library/LaunchAgents/com.nba-simulator.adce-autonomous.plist
launchctl unload ~/Library/LaunchAgents/com.nba-simulator.adce-autonomous.plist
launchctl start com.nba-simulator.adce-autonomous
launchctl stop com.nba-simulator.adce-autonomous
launchctl list | grep nba-simulator

# Systemd (Linux)
sudo systemctl start adce-autonomous
sudo systemctl stop adce-autonomous
sudo systemctl restart adce-autonomous
sudo systemctl status adce-autonomous
sudo journalctl -u adce-autonomous -f
```

---

## Support & Documentation

**Key Documents:**
- `PHASE_0_DISCOVERY_COMPLETE.md` - System findings
- `BACKUP_MANIFEST.md` - Backup procedures
- `config/autonomous_config.yaml` - ADCE configuration
- `docs/AUTONOMOUS_OPERATION.md` - Detailed operations guide

**Troubleshooting:**
- `docs/TROUBLESHOOTING.md` - Common issues
- `docs/EMERGENCY_RECOVERY.md` - Recovery procedures

**Monitoring:**
- `docs/monitoring/dims/README.md` - DIMS guide
- `docs/SCRAPER_MONITORING_SYSTEM.md` - Scraper monitoring

---

**Activation Guide Version:** 1.0
**Created By:** Claude Code (NBA Simulator Project)
**Date:** October 30, 2025
**Status:** ✅ Ready for Activation

**Estimated Time to Production:** 2 weeks (following this guide)
