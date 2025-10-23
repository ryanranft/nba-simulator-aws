# Autonomous Operation Guide

**ADCE Phase 4 - 24/7 Self-Healing Data Collection System**

**Version:** 1.0
**Last Updated:** October 22, 2025
**Status:** Production Ready

---

## Overview

The Autonomous Loop is the master controller for the NBA Simulator's self-healing data collection ecosystem (ADCE). It operates 24/7 with zero manual intervention, automatically detecting and filling data gaps.

**Key Capabilities:**
- 🔄 Continuous 24/7 operation
- 🔍 Automatic gap detection (hourly)
- 🚀 On-demand data collection
- ❤️ Health monitoring and alerting
- 🛡️ Self-recovery from transient errors
- 📊 Real-time metrics and status

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  AUTONOMOUS LOOP CONTROLLER                      │
│                    (Master Coordinator)                          │
└─────────────────────────────────────────────────────────────────┘
                               |
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌──────────────┐      ┌──────────────┐
│ Reconciliation│      │   Task Queue │      │ Orchestrator │
│    Daemon     │──┬──▶│   Monitor    │──┬──▶│   Engine     │
│  (Phase 2)    │  │   │              │  │   │  (Phase 3)   │
└───────────────┘  │   └──────────────┘  │   └──────────────┘
     │             │                      │          │
     │ Generates   │ Watches             │ Executes │
     │ tasks       │ inventory/gaps.json │ scrapers │
     │ hourly      │                      │          │
     ▼             │                      │          ▼
┌───────────────┐  │                      │   ┌──────────────┐
│ inventory/    │  │                      │   │ Data in S3   │
│ gaps.json     │◀─┘                      │   │              │
└───────────────┘                         │   └──────────────┘
                                          │          │
                                          │ Updates  │
                                          └──────────┘
                                               │
                                               ▼
                               ┌────────────────────────────┐
                               │   Health Monitor (HTTP)    │
                               │   http://localhost:8080    │
                               └────────────────────────────┘
```

---

## Components

### 1. Autonomous Loop Controller
**File:** `scripts/autonomous/autonomous_loop.py`

**Responsibilities:**
- Start and manage reconciliation daemon
- Monitor task queue for new tasks
- Trigger orchestrator when tasks available
- Handle component lifecycle and errors
- Coordinate overall system operation

### 2. Reconciliation Daemon (Phase 2)
**File:** `scripts/reconciliation/reconciliation_daemon.py`

**Responsibilities:**
- Scan S3 bucket (hourly)
- Analyze data coverage
- Detect data gaps
- Generate prioritized task queue

### 3. Scraper Orchestrator (Phase 3)
**File:** `scripts/orchestration/scraper_orchestrator.py`

**Responsibilities:**
- Read task queue
- Execute scrapers by priority (CRITICAL → HIGH → MEDIUM → LOW)
- Track progress and success/failure
- Update inventory after completion

### 4. Health Monitor
**File:** `scripts/autonomous/health_monitor.py`

**Responsibilities:**
- HTTP health check endpoints
- Component status monitoring
- Metrics exposure
- Error tracking

### 5. CLI Management Tool
**File:** `scripts/autonomous/autonomous_cli.py`

**Responsibilities:**
- Start/stop/restart autonomous loop
- Check status and health
- View logs and task queue
- Easy system management

---

## Quick Start

### Installation

No installation required. All components are pre-configured.

### Starting the System

```bash
# Navigate to project directory
cd /Users/ryanranft/nba-simulator-aws

# Start autonomous loop
python scripts/autonomous/autonomous_cli.py start

# Check status
python scripts/autonomous/autonomous_cli.py status
```

### Stopping the System

```bash
# Graceful shutdown
python scripts/autonomous/autonomous_cli.py stop
```

---

## CLI Commands

### `autonomous start`
Start the autonomous loop in background

```bash
python scripts/autonomous/autonomous_cli.py start

# Start in dry-run mode (simulation, no actual execution)
python scripts/autonomous/autonomous_cli.py start --dry-run
```

### `autonomous stop`
Stop the autonomous loop gracefully

```bash
python scripts/autonomous/autonomous_cli.py stop
```

### `autonomous status`
Show current system status

```bash
python scripts/autonomous/autonomous_cli.py status
```

**Example Output:**
```
================================================================================
AUTONOMOUS LOOP STATUS
================================================================================
Status: ✅ RUNNING
PID: 12345

Overall Health: HEALTHY
Last Check: 2025-10-22T20:30:15

Components:
  ✅ reconciliation_daemon: healthy
      Reconciliation daemon is running
  ⏸️  orchestrator: idle
      Orchestrator is idle (not currently running)
  ✅ task_queue: available
      41 tasks in queue
  ✅ s3: healthy
      S3 bucket accessible
  ✅ dims: healthy
      DIMS metrics updated 0.5 hours ago

Task Queue:
  Total: 41
  By Priority: {'critical': 4, 'high': 0, 'medium': 1, 'low': 36}

S3 Inventory:
  Objects: 172,754
  Size: 118.00 GB
================================================================================
```

### `autonomous restart`
Restart the autonomous loop

```bash
python scripts/autonomous/autonomous_cli.py restart
```

### `autonomous health`
Check component health

```bash
python scripts/autonomous/autonomous_cli.py health
```

### `autonomous logs`
View system logs

```bash
# View last 50 lines
python scripts/autonomous/autonomous_cli.py logs

# View last 100 lines
python scripts/autonomous/autonomous_cli.py logs --tail 100

# Follow logs (like tail -f)
python scripts/autonomous/autonomous_cli.py logs --follow
```

### `autonomous tasks`
Show current task queue

```bash
python scripts/autonomous/autonomous_cli.py tasks
```

---

## Health Check Endpoints

The health monitor exposes HTTP endpoints for external monitoring:

### `GET /health`
Overall health status (200 OK if healthy, 503 if unhealthy)

```bash
curl http://localhost:8080/health
```

### `GET /status`
Detailed component status

```bash
curl http://localhost:8080/status
```

### `GET /metrics`
Current cycle metrics

```bash
curl http://localhost:8080/metrics
```

### `GET /tasks`
Current task queue

```bash
curl http://localhost:8080/tasks
```

---

## Configuration

Configuration file: `config/autonomous_config.yaml`

### Key Settings

```yaml
# Enable/disable autonomous mode
enabled: true

# Reconciliation runs every hour
reconciliation_interval_hours: 1

# Trigger orchestrator when >= 1 tasks available
min_tasks_to_trigger: 1

# Kill orchestrator if runs longer than 2 hours
max_orchestrator_runtime_minutes: 120

# Health check port
health_check:
  port: 8080
```

### Modifying Configuration

1. Edit configuration file:
   ```bash
   nano config/autonomous_config.yaml
   ```

2. Restart autonomous loop:
   ```bash
   python scripts/autonomous/autonomous_cli.py restart
   ```

---

## Monitoring

### Real-Time Monitoring

```bash
# Watch status (refresh every 5 seconds)
watch -n 5 'python scripts/autonomous/autonomous_cli.py status'

# Follow logs
python scripts/autonomous/autonomous_cli.py logs --follow
```

### Health Checks

```bash
# Check component health
python scripts/autonomous/autonomous_cli.py health

# Or via HTTP
curl http://localhost:8080/health
```

### Task Queue Monitoring

```bash
# View current task queue
python scripts/autonomous/autonomous_cli.py tasks

# Or via HTTP
curl http://localhost:8080/tasks
```

---

## Operational Workflow

### Daily Operation

The system operates autonomously with this cycle:

1. **Reconciliation** (every hour)
   - Scans S3 bucket using AWS Inventory (1000x faster)
   - Compares HAVE vs SHOULD (expected coverage)
   - Detects data gaps
   - Generates prioritized task queue

2. **Task Queue Monitoring** (every 30 seconds)
   - Checks if tasks are available
   - Triggers orchestrator if tasks >= threshold

3. **Orchestration** (on-demand)
   - Reads task queue
   - Executes scrapers by priority (CRITICAL → LOW)
   - Fills data gaps
   - Updates inventory

4. **Loop** → Back to step 1

### Manual Intervention (Rarely Needed)

```bash
# Check if system needs attention
python scripts/autonomous/autonomous_cli.py status

# View recent errors
python scripts/autonomous/autonomous_cli.py logs --tail 100 | grep ERROR

# Check task queue
python scripts/autonomous/autonomous_cli.py tasks

# Restart if needed
python scripts/autonomous/autonomous_cli.py restart
```

---

## Troubleshooting

### System Not Starting

```bash
# Check if already running
python scripts/autonomous/autonomous_cli.py status

# Check logs for errors
python scripts/autonomous/autonomous_cli.py logs --tail 50

# Try starting in dry-run mode
python scripts/autonomous/autonomous_cli.py start --dry-run
```

### Reconciliation Daemon Stopped

```bash
# Check status
python scripts/autonomous/autonomous_cli.py health

# Restart system
python scripts/autonomous/autonomous_cli.py restart
```

### Orchestrator Timing Out

Check configuration:
```yaml
# In config/autonomous_config.yaml
max_orchestrator_runtime_minutes: 120  # Increase if needed
```

### High Error Rate

```bash
# View recent errors
python scripts/autonomous/autonomous_cli.py logs | grep ERROR

# Check component health
python scripts/autonomous/autonomous_cli.py health

# Check S3 access
aws s3 ls s3://nba-sim-raw-data-lake/ --max-items 1
```

---

## Production Deployment

### Using systemd (Recommended for Production)

1. Copy service file:
   ```bash
   sudo cp scripts/autonomous/autonomous_loop.service /etc/systemd/system/
   ```

2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable service (start on boot):
   ```bash
   sudo systemctl enable autonomous-loop
   ```

4. Start service:
   ```bash
   sudo systemctl start autonomous-loop
   ```

5. Check status:
   ```bash
   sudo systemctl status autonomous-loop
   ```

6. View logs:
   ```bash
   sudo journalctl -u autonomous-loop -f
   ```

---

## Performance

### Expected Metrics

- **Reconciliation Frequency:** Every hour
- **Reconciliation Duration:** 1-10 minutes (with AWS Inventory: <2 min)
- **Orchestration Duration:** 10-120 minutes (depends on task count)
- **Task Success Rate:** 90-95%
- **System Uptime:** 99.9%+ (self-healing)

### Resource Usage

- **Memory:** ~100-500 MB
- **CPU:** 5-20% (peaks during orchestration)
- **Disk:** Minimal (logs rotate automatically)
- **Network:** Dependent on scraper activity

---

## Security

### Access Control

- HTTP endpoints listen on localhost only (127.0.0.1)
- No authentication required (local access only)
- For remote access, use SSH tunneling:
  ```bash
  ssh -L 8080:localhost:8080 user@server
  ```

### Process Management

- Runs as regular user (not root)
- Limited resource usage (memory/CPU quotas)
- Graceful shutdown on signals

---

## Maintenance

### Log Rotation

Logs automatically rotate when they reach 100 MB. Old logs are kept for 5 generations.

### Manual Cleanup

```bash
# Clean old logs
find logs/ -name "*.log.*" -mtime +30 -delete

# Clean old inventory cache
find inventory/cache/ -name "*.json" -mtime +7 -delete
```

### Updates

```bash
# Stop system
python scripts/autonomous/autonomous_cli.py stop

# Pull latest changes
git pull origin main

# Restart system
python scripts/autonomous/autonomous_cli.py start
```

---

## FAQ

**Q: How often does reconciliation run?**
A: Every hour by default. Configure in `config/autonomous_config.yaml`.

**Q: How do I know if the system is working?**
A: Run `python scripts/autonomous/autonomous_cli.py status` to see overall health and component status.

**Q: Can I run this in production?**
A: Yes! Use the systemd service for automatic startup and monitoring.

**Q: What happens if a component fails?**
A: The system will attempt to restart failed components automatically. Check logs for details.

**Q: How do I see what tasks are pending?**
A: Run `python scripts/autonomous/autonomous_cli.py tasks` or check `inventory/gaps.json`.

**Q: Can I pause the system?**
A: Yes! Run `python scripts/autonomous/autonomous_cli.py stop`. Start again with `start`.

---

## Support

For issues or questions:
1. Check logs: `python scripts/autonomous/autonomous_cli.py logs`
2. Check health: `python scripts/autonomous/autonomous_cli.py health`
3. Review configuration: `config/autonomous_config.yaml`
4. See troubleshooting section above

---

**Congratulations! Your autonomous data collection system is now operational.** 🎉

The system will continuously monitor for data gaps and automatically fill them, 24/7, with zero manual intervention.

