# NBA Panel Data Monitoring Dashboard - Usage Guide

**Implementation:** rec_3 (Monitoring Dashboards)
**Created:** October 18, 2025
**Status:** ✅ Complete
**Location:** `scripts/monitoring/unified_monitoring_dashboard.py`

---

## Overview

Real-time monitoring dashboard for NBA panel data system with terminal-based UI using Rich library.

**Monitors:**
1. Background data loading processes (Kaggle historical, Player Dashboards)
2. PostgreSQL database status and metrics
3. MLflow experiment tracking
4. System component health
5. Overall progress tracking

---

## Quick Start

### Basic Usage

```bash
# Live monitoring (updates every 10 seconds)
python scripts/monitoring/unified_monitoring_dashboard.py

# Custom refresh rate (updates every 5 seconds)
python scripts/monitoring/unified_monitoring_dashboard.py --refresh 5

# Single snapshot (no live updates)
python scripts/monitoring/unified_monitoring_dashboard.py --once
```

### Keyboard Controls

- **Ctrl+C**: Exit dashboard

---

## Dashboard Sections

### 1. Data Loading Progress

Tracks two major background processes:

**Kaggle Historical (1946-2023):**
- Total: 13,592,899 play-by-play events
- Progress bar with percentage
- Current records loaded
- Processing rate (records/second)
- Estimated time to completion

**Player Dashboards (2024-25 Season):**
- Total: 5,121 players
- Progress bar with percentage
- Current players scraped
- Processing rate (players/minute)
- Estimated time to completion

### 2. PostgreSQL Database

**Metrics:**
- Connection status
- Database name
- Total database size
- Record counts:
  - Play-by-play events
  - Game info records
  - Player records

### 3. MLflow Experiments

**Tracks:**
- Active experiments (nba-game-predictions, nba-panel-data-predictions)
- Total runs per experiment
- Best model accuracy
- Best performing model type

### 4. System Status

**Components:**
- PostgreSQL (Online/Offline)
- MLflow (Online/Offline)
- Kaggle Loader (Running/Complete/Idle)
- Player Scraper (Running/Complete/Idle)

### 5. Overall Progress

Summary statistics across all monitored processes.

---

## Current Monitoring Results (October 18, 2025, 3:45 AM CT)

### Kaggle Historical Loading
- **Progress:** 49.9% (6,779,934 / 13,592,899 records)
- **Rate:** 687 records/second
- **ETA:** ~3.5 hours (~7:15 AM CT completion)
- **Database Size:** 2.2 GB

### Player Dashboards Scraping
- **Progress:** 3.5% (178 / 5,121 players)
- **Updated:** From 164 players earlier (14 new players in ~40 minutes)
- **Rate:** ~0.35 players/minute (slower overnight, likely rate limited)
- **ETA:** ~240 hours remaining (~October 28)

### Database Metrics
- **Status:** ✅ Connected
- **Play-by-Play:** 6,779,934 events loaded
- **Size:** 2,216 MB
- **Performance:** Accepting data smoothly

---

## Technical Details

### Data Sources

**Log Files:**
- Kaggle: `/tmp/kaggle_historical_loading.log`
- Player Dashboards: `/tmp/full_season_player_dashboards.log`

**Data Directories:**
- Player Dashboards: `/tmp/nba_full_season_2024_25/player_dashboards/2024-25/`
- Team Dashboards: `/tmp/nba_full_season_2024_25/team_dashboards/2024-25/`

**Database:**
- Host: localhost
- Database: nba_panel_data
- User: ryanranft
- Tables: nba_play_by_play_historical, nba_game_info_historical, nba_players_historical

**MLflow:**
- Tracking URI: file:///tmp/mlruns
- Experiments: nba-game-predictions, nba-panel-data-predictions

### Requirements

**Python Packages:**
```bash
pip install rich psycopg2-binary mlflow
```

**System:**
- Python 3.7+
- PostgreSQL running on localhost
- Access to log files and data directories

---

## Troubleshooting

### Dashboard shows "Error" for database

**Check PostgreSQL connection:**
```bash
psql -h localhost -U ryanranft -d nba_panel_data -c "SELECT 1;"
```

**Verify credentials:**
```bash
echo $DB_HOST
echo $DB_NAME
echo $DB_USER
```

### No progress showing for Kaggle loader

**Check if log file exists:**
```bash
tail -f /tmp/kaggle_historical_loading.log
```

**Verify process is running:**
```bash
ps aux | grep load_kaggle_historical_panel.py
```

### MLflow shows "Error"

**Check MLflow tracking directory:**
```bash
ls -la /tmp/mlruns
```

**Set tracking URI (if needed):**
```bash
export MLFLOW_TRACKING_URI=file:///tmp/mlruns
```

### Player Dashboards not updating

**Check scraper process:**
```bash
ps aux | grep scrape_nba_api_player_dashboards.py
```

**Count files manually:**
```bash
find /tmp/nba_full_season_2024_25/player_dashboards/2024-25 -name "player_*.json" | wc -l
```

---

## Integration with Other Tools

### Use with screen/tmux for persistent monitoring

```bash
# Start in screen
screen -S nba-dashboard
python scripts/monitoring/unified_monitoring_dashboard.py

# Detach with Ctrl+A, D
# Reattach later with:
screen -r nba-dashboard
```

### Run as background service (snapshot mode)

```bash
# Add to crontab for periodic snapshots
*/5 * * * * python /path/to/scripts/monitoring/unified_monitoring_dashboard.py --once >> /tmp/dashboard_log.txt 2>&1
```

### Export snapshot to file

```bash
python scripts/monitoring/unified_monitoring_dashboard.py --once > dashboard_snapshot_$(date +%Y%m%d_%H%M%S).txt
```

---

## Next Steps

**After Dashboard Monitoring:**

1. Wait for Kaggle historical loading to complete (~7:15 AM CT)
2. Monitor Player Dashboards progress daily
3. Validate data quality after loads complete
4. Launch next scrapers (Player Tracking, Game Advanced)

**Enhancements (Optional):**
- Add drift detection metrics display
- Include S3 bucket monitoring
- Add cost tracking dashboard
- Email/Slack alerts for completion

---

## Implementation Details

**Recommendation:** rec_3 (Monitoring Dashboards)
**Source Book:** Designing Machine Learning Systems (Ch 8, Ch 9)
**Impact:** MEDIUM - Real-time visibility into system operations
**Time Estimate:** 1 day (Actual: ~2 hours)
**Status:** ✅ Complete (October 18, 2025)

**Features Implemented:**
- ✅ Real-time process monitoring
- ✅ PostgreSQL metrics tracking
- ✅ MLflow experiment integration
- ✅ Multi-panel terminal UI with Rich
- ✅ Configurable refresh rates
- ✅ Single snapshot mode
- ✅ Progress bars and ETAs
- ✅ System health indicators

**Test Coverage:** Manual testing with live data ✅

---

**Status:** Production ready
**Last Updated:** October 18, 2025, 3:45 AM CT
**Maintainer:** NBA Simulator System
