# hoopR 152 Endpoints - Quick Reference Card

**Created:** October 7, 2025
**Purpose:** Fast lookup for hoopR scraper operations

---

## 🚀 Quick Start Commands

### Run Scraper

```bash
# All seasons (2002-2025), no S3
bash scripts/etl/overnight_hoopr_all_152.sh

# Recent 5 seasons with S3 upload
bash scripts/etl/overnight_hoopr_all_152.sh "2020:2025" --upload-to-s3

# Single season
bash scripts/etl/overnight_hoopr_all_152.sh "2024:2024" --upload-to-s3
```

### Monitor Progress

```bash
# Check if running
ps aux | grep scrape_hoopr_all_152

# View live log
tail -f /tmp/hoopr_all_152_overnight.log

# Count files created
find /tmp/hoopr_all_152 -name "*.csv" | wc -l

# Check total size
du -sh /tmp/hoopr_all_152
```

### Stop Scraper

```bash
# Graceful stop
kill $(cat /tmp/hoopr_all_152.pid)

# Force kill
kill -9 $(cat /tmp/hoopr_all_152.pid)
```

---

## 📂 File Locations

| Item | Path |
|------|------|
| **R Script** | `/Users/ryanranft/nba-simulator-aws/scripts/etl/scrape_hoopr_all_152_endpoints.R` |
| **Shell Wrapper** | `/Users/ryanranft/nba-simulator-aws/scripts/etl/overnight_hoopr_all_152.sh` |
| **Output Dir** | `/tmp/hoopr_all_152/` |
| **Log File** | `/tmp/hoopr_all_152_overnight.log` |
| **PID File** | `/tmp/hoopr_all_152.pid` |
| **S3 Bucket** | `s3://nba-sim-raw-data-lake/hoopr_152/` |
| **Validator** | `/Users/ryanranft/nba-simulator-aws/scripts/validation/validate_hoopr_152_output.R` |
| **Full Guide** | `/Users/ryanranft/nba-simulator-aws/docs/HOOPR_152_ENDPOINTS_GUIDE.md` |

---

## 📊 152 Endpoints Summary

### Phase 1: Bulk Data (4 endpoints)
- `load_nba_pbp` - Play-by-play
- `load_nba_player_box` - Player box scores
- `load_nba_team_box` - Team box scores
- `load_nba_schedule` - Schedules

**Output:** 96 files (4 × 24 seasons)

### Phase 2: Static/Reference (25 endpoints)
- All-time leaders
- Player/team info
- Draft data (history, combine)
- Franchise data
- Scoreboards
- Playoff series

**Output:** ~50 files

### Phase 3: Per-Season Dashboards (40 endpoints)
- League player/team stats
- Clutch stats
- Shot locations
- Player tracking (2013+)
- Lineups
- Standings

**Output:** ~960 files (40 × 24 seasons)

### Phase 4: Per-Game Boxscores (87 endpoints)
- Traditional/Advanced/Scoring/Usage
- Four Factors/Misc/Tracking
- Hustle/Matchups/Defensive
- Shot charts
- Player/Team dashboards
- Synergy play types

**Output:** ~30,000 files (sample mode in script)

---

## ⏱️ Runtime Estimates

### Phases 1-3 (Core Data)
- **API Calls:** ~1,106
- **Runtime:** 45-60 minutes
- **Output:** 10-15 GB
- **Files:** ~1,100

### All Phases (Complete)
- **API Calls:** ~31,106
- **Runtime:** 20-24 hours
- **Output:** 20-32 GB
- **Files:** ~31,000

---

## 🔍 Validation

### Quick Check

```bash
# Validate output
Rscript scripts/validation/validate_hoopr_152_output.R /tmp/hoopr_all_152

# Expected results (Phases 1-3):
# - Phase 1: 96 files (PASS)
# - Phase 2: 50+ files (PARTIAL)
# - Phase 3: 960 files (PARTIAL)
# - Total: 10-15 GB
```

### Manual Checks

```bash
# File counts per phase
ls /tmp/hoopr_all_152/bulk_pbp/*.csv | wc -l          # Expected: 24
ls /tmp/hoopr_all_152/bulk_player_box/*.csv | wc -l   # Expected: 24
ls /tmp/hoopr_all_152/league_dashboards/*.csv | wc -l # Expected: ~240

# Check for empty files
find /tmp/hoopr_all_152 -name "*.csv" -size 0

# Sample data validation
head -5 /tmp/hoopr_all_152/bulk_pbp/pbp_2024.csv
```

---

## 📤 S3 Upload

### Check Upload Status

```bash
# Count S3 objects
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_152/ --recursive | wc -l

# Compare local vs S3
LOCAL=$(find /tmp/hoopr_all_152 -name "*.csv" | wc -l)
S3=$(aws s3 ls s3://nba-sim-raw-data-lake/hoopr_152/ --recursive | wc -l)
echo "Local: $LOCAL | S3: $S3"

# Check S3 size
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_152/ --recursive --summarize | grep "Total Size"
```

### Manual Upload

```bash
# Upload everything
aws s3 sync /tmp/hoopr_all_152/ s3://nba-sim-raw-data-lake/hoopr_152/ --exclude "*.log"

# Upload specific phase
aws s3 sync /tmp/hoopr_all_152/bulk_pbp/ s3://nba-sim-raw-data-lake/hoopr_152/bulk_pbp/
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Process died** | Check log: `tail -50 /tmp/hoopr_all_152_overnight.log` |
| **Memory error** | Reduce season range: `"2020:2022"` |
| **S3 permission denied** | Check credentials: `aws sts get-caller-identity` |
| **Rate limiting** | Increase delay in R script: `RATE_LIMIT_SECONDS <- 5` |
| **Stale PID** | Remove: `rm -f /tmp/hoopr_all_152.pid` |

### Debug Commands

```bash
# Test R packages
Rscript -e "library(hoopR); library(dplyr); library(readr)"

# Test single endpoint
Rscript -e "library(hoopR); data <- nba_leaguedashplayerstats(season='2024-25'); print(head(data))"

# Check disk space
df -h /tmp

# View recent errors
grep ERROR /tmp/hoopr_all_152_overnight.log | tail -20
```

---

## 💾 Data Integration

### Load into PostgreSQL

```sql
-- Create staging table
CREATE TABLE staging.hoopr_pbp (
  game_id VARCHAR(50),
  event_type VARCHAR(100),
  description TEXT
  -- Add all CSV columns
);

-- Load from CSV
\COPY staging.hoopr_pbp FROM '/tmp/hoopr_all_152/bulk_pbp/pbp_2024.csv' CSV HEADER;

-- Verify
SELECT COUNT(*), MIN(game_id), MAX(game_id) FROM staging.hoopr_pbp;
```

### Feature Engineering (Python)

```python
import pandas as pd
import glob

# Load all player box scores
files = glob.glob('/tmp/hoopr_all_152/bulk_player_box/*.csv')
player_box = pd.concat([pd.read_csv(f) for f in files])

# Calculate advanced metrics
player_box['ts_pct'] = player_box['points'] / (2 * (player_box['fga'] + 0.44 * player_box['fta']))
player_box.to_csv('/tmp/hoopr_enriched_player_stats.csv', index=False)
```

---

## 📈 Expected Output Structure

```
/tmp/hoopr_all_152/
├── bulk_pbp/              # 24 files (1 per season)
├── bulk_player_box/       # 24 files
├── bulk_team_box/         # 24 files
├── bulk_schedule/         # 24 files
├── static_data/           # ~10 files
├── player_info/           # ~5 files
├── team_info/             # ~3 files
├── draft/                 # ~30 files (23 years × multiple endpoints)
├── league_dashboards/     # ~240 files (10 endpoints × 24 seasons)
├── lineups/               # 24 files
├── standings/             # 24 files
├── boxscore_*/           # Per-game (sample mode)
└── scraper_log_*.txt     # Comprehensive log
```

---

## 💰 Cost Summary

### S3 Storage (24 seasons, Phases 1-3)
- **Storage:** 15 GB × $0.023/GB = **$0.35/month**
- **PUT requests:** 1,106 × $0.005/1000 = **$0.006**
- **GET requests:** Minimal
- **Total:** **~$0.36/month**

### Full Data (All phases)
- **Storage:** 25 GB × $0.023/GB = **$0.58/month**
- **Requests:** ~$0.16
- **Total:** **~$0.74/month**

---

## 🔄 Maintenance

### Weekly Tasks

```bash
# Check scraper status
ps aux | grep scrape_hoopr_all_152

# Verify S3 uploads
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_152/ --recursive --summarize

# Clean old logs
find /tmp -name "hoopr_all_152_overnight*.log" -mtime +7 -delete
```

### Monthly Tasks

```bash
# Update hoopR package
Rscript -e "update.packages('hoopR')"

# Re-scrape current season
CURRENT_SEASON=$(date +%Y)
bash scripts/etl/overnight_hoopr_all_152.sh "$CURRENT_SEASON:$CURRENT_SEASON" --upload-to-s3
```

---

## 📞 Getting Help

1. **Check full documentation:** `docs/HOOPR_152_ENDPOINTS_GUIDE.md`
2. **Review logs:** `tail -100 /tmp/hoopr_all_152_overnight.log`
3. **Validate output:** `Rscript scripts/validation/validate_hoopr_152_output.R /tmp/hoopr_all_152`
4. **Test endpoints:** `Rscript -e "library(hoopR); data <- nba_scoreboard(game_date='2024-01-01'); print(head(data))"`

---

## 🎯 Success Criteria

**Phase 1-3 Complete:**
- ✅ 96 bulk files (4 × 24 seasons)
- ✅ 50+ static files
- ✅ 960+ dashboard files (40 × 24 seasons)
- ✅ Total size: 10-15 GB
- ✅ Validation: PASS or PARTIAL
- ✅ S3 upload: All files synced

**Ready for Next Steps:**
- Load into PostgreSQL
- Feature engineering pipeline
- ML model training
- Simulation engine enhancement

---

*Last updated: October 7, 2025*
*Quick Reference v1.0*
