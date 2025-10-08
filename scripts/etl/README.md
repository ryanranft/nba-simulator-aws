# ETL Scripts Directory

**Last Updated:** October 8, 2025

---

## 📋 Quick Reference

**Complete documentation:** See Workflow #42 (`docs/claude_workflows/workflow_descriptions/42_scraper_management.md`)

---

## Active Scripts (Use These)

### Core Scrapers

#### 1. NBA API Comprehensive
- **Script:** `scrape_nba_api_comprehensive.py`
- **Wrapper:** `overnight_nba_api_comprehensive.sh`
- **Coverage:** 1996-2025 (30 seasons), 24 endpoints
- **Runtime:** 5-6 hours
- **Rate Limit:** 600ms between requests
- **Output:** `/tmp/nba_api_comprehensive/`

#### 2. hoopR Scraper (R-based)
- **Scripts:** `scrape_hoopr_phase1_foundation.R`, `scrape_hoopr_phase1b_only.R`
- **Wrappers:** `run_hoopr_phase1.sh`, `run_hoopr_phase1b.sh`
- **Coverage:** 2002-2025 (24 seasons)
- **Runtime:** Phase 1A (30 sec), Phase 1B (30-60 min)
- **Rate Limit:** None
- **Output:** `/tmp/hoopr_phase1/`, `/tmp/hoopr_phase1b/`

#### 3. Basketball Reference
- **Script:** `scrape_basketball_reference_complete.py`
- **Wrapper:** `overnight_basketball_reference_comprehensive.sh`, `scrape_bbref_incremental.sh`
- **Coverage:** 1946-present (complete history)
- **Runtime:** 3-4 hours (incremental), 30 hours (full)
- **Rate Limit:** 3.5s between requests (strict!)
- **Output:** `/tmp/basketball_reference_incremental/`

#### 4. Kaggle Database
- **Script:** `download_kaggle_basketball.py`
- **Coverage:** 1946-2024 (historical completeness)
- **Runtime:** 10-15 minutes
- **Prerequisites:** Kaggle API token configured
- **Output:** `~/.kaggle/datasets/wyattowalsh/basketball/`

#### 5. ESPN Gap Filler
- **Script:** `scrape_missing_espn_data.py`
- **Wrapper:** `run_espn_scraper.sh`
- **Coverage:** 2022-2025 (recent seasons)
- **Runtime:** 2-3 hours
- **Rate Limit:** None
- **Output:** `/tmp/espn_missing/`

### Extraction Scripts

#### Temporal Format Converters
- **ESPN:** `extract_espn_local_to_temporal_v2.py` (active version)
- **Kaggle:** `extract_kaggle_to_temporal.py`

#### Other Extractors
- `extract_pbp_local.py` - Play-by-play extraction
- `extract_boxscores_local.py` - Box score extraction
- `extract_schedule_local.py` - Schedule extraction
- `extract_teams_by_year.py` - Team data by year

### Possession Panel Builders
- `create_possession_panel_from_espn.py` - ESPN possession panels
- `create_possession_panel_from_kaggle.py` - Kaggle possession panels
- `create_possession_panel_from_nba_api.py` - NBA API possession panels
- `create_possession_panel_from_pbpstats.py` - PBPStats possession panels
- `create_possession_panel_with_lineups.py` - With lineup integration
- `create_possession_panel_with_hoopr_lineups.py` - hoopR lineup integration

### Utilities
- `create_player_id_mapping.py` - Player ID mapping across sources
- `game_id_decoder.py` - Decode game IDs
- `validate_lineup_tracking.py` - Lineup validation
- `verify_with_nba_stats.py` - Cross-source verification

---

## Deprecated Scripts

**Location:** `scripts/archive/deprecated/`

### Archived Files
- `extract_espn_local_to_temporal.py` (v1 - replaced by v2)
- `extract_espn_local_to_temporal_UPDATED.py` (replaced by v2)
- `download_kaggle_database.py` (replaced by download_kaggle_basketball.py)
- `scrape_sportsdataverse.py` (redundant with hoopR)

**Why archived:** These scripts have been superseded by newer versions or are no longer needed. They are preserved for reference but should not be used in production.

---

## Quick Start Commands

### Launch Scrapers (Overnight)

```bash
# NBA API (5-6 hours)
nohup bash scripts/etl/overnight_nba_api_comprehensive.sh > /tmp/nba_api.log 2>&1 &

# hoopR Phase 1B (30-60 minutes)
nohup bash scripts/etl/run_hoopr_phase1b.sh > /tmp/hoopr.log 2>&1 &

# Basketball Reference (3-4 hours, 2020-2025)
nohup bash scripts/etl/scrape_bbref_incremental.sh 2020 2025 > /tmp/bbref.log 2>&1 &

# Kaggle (10-15 minutes)
python scripts/etl/download_kaggle_basketball.py

# ESPN Gap Filler (2-3 hours)
nohup bash scripts/etl/run_espn_scraper.sh > /tmp/espn_gap.log 2>&1 &
```

### Monitor Progress

```bash
# Check all running scrapers
ps aux | grep -E "scrape_nba_api|scrape_hoopr|scrape_bbref" | grep -v grep

# Monitor all logs
tail -f /tmp/nba_api.log /tmp/hoopr.log /tmp/bbref.log

# Emergency stop (kill all)
ps aux | grep -E "scrape" | grep -v grep | awk '{print $2}' | xargs kill -9
```

---

## Integration with Workflows

- **Workflow #38:** Check scraper completion at session start
- **Workflow #41:** Validate scraper output with test suites
- **Workflow #42:** Complete scraper execution guide (900+ lines)

---

## Best Practices

1. **Always check disk space** before launching overnight scrapers (need 10+ GB free)
2. **Never reduce Basketball Reference rate limit** below 3 seconds (risk permanent ban)
3. **Always upload to S3** after completion before cleaning up local files
4. **Document scraper runs** in PROGRESS.md and COMMAND_LOG.md
5. **Run pre-flight checklist** from Workflow #42 before overnight launches
6. **Validate output** with test suites from Workflow #41

---

## Troubleshooting

**Common issues:**
- Duplicate files → Archived old versions to `scripts/archive/deprecated/`
- Which version to use? → Check this README or Workflow #42
- Script not working? → Verify it's not in deprecated folder
- Rate limit errors → Check Workflow #42 for recovery procedures

**Full troubleshooting guide:** See Workflow #42

---

## File Organization

```
scripts/etl/
├── README.md (this file)
├── scrape_*.py (core scrapers)
├── overnight_*.sh (overnight wrappers)
├── run_*.sh (standard wrappers)
├── extract_*.py (format converters)
├── create_*.py (possession panel builders)
└── scripts/archive/deprecated/ (old versions)
```

---

*For detailed documentation, see Workflow #42: `docs/claude_workflows/workflow_descriptions/42_scraper_management.md`*
