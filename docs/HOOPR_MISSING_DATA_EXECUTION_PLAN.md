# hoopR Missing Data Collection - Complete Execution Plan

**Created:** November 9, 2025
**Purpose:** Collect missing hoopR data (Dec 2, 2024 → Nov 9, 2025)
**Runtime:** ~2 hours total
**Cost:** ~$0.08/month

---

## 🎯 Quick Start

**One Command to Run Everything:**

```bash
cd /Users/ryanranft/nba-simulator-aws
bash scripts/etl/collect_missing_hoopr_data.sh
```

This script:
1. ✅ Activates conda environment
2. ✅ Installs/verifies hoopR package
3. ✅ Collects 2024-2025 season data
4. ✅ Saves to parquet format
5. ✅ Verifies output

---

## 📋 Step-by-Step (Manual)

### Step 1: Collect Data (nba-simulator-aws)

```bash
# Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# Activate environment
conda activate nba-aws

# Run collection script
bash scripts/etl/collect_missing_hoopr_data.sh
```

**What happens:**
- Collects 4 data types: schedule, team box, player box, play-by-play
- For seasons: 2024, 2025
- Saves to: `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/`
- Format: Parquet (optimized, same as existing files)

**Runtime:** ~30-45 minutes

---

### Step 2: Load to Database (nba-mcp-synthesis)

```bash
# Switch to nba-mcp-synthesis
cd /Users/ryanranft/nba-mcp-synthesis

# Activate environment
conda activate mcp-synthesis  # or whatever your env name is

# Load new data
python scripts/load_parquet_to_postgres.py --years 2024-2025
```

**What happens:**
- Reads parquet files for 2024-2025
- Loads into `hoopr_raw.nba_*` tables
- Appends to existing data (doesn't replace)

**Runtime:** ~10-15 minutes

---

### Step 3: Verify Coverage

```bash
# Still in nba-mcp-synthesis
python scripts/validate_hoopr_data.py --years 2024-2025
```

**Expected output:**
```
✅ 2024 Season: 1,318 games (Oct 2024 - Jun 2025)
✅ 2025 Season: ~500 games (Oct 2025 - Nov 2025)
✅ Date range: Dec 2, 2024 → Nov 9, 2025
✅ No gaps detected
```

---

## 🔍 What Gets Collected

### Season 2024 (Oct 2024 - Jun 2025)

**Expected:**
- Games: ~1,300-1,400
- Play-by-play events: ~650K-700K
- Player box scores: ~85K
- Team box scores: ~2,600

**Date range:** Oct 22, 2024 → Jun 16, 2025 (full season)
**Fills gap:** Dec 2, 2024 → Jun 16, 2025

### Season 2025 (Oct 2025 - Jun 2026)

**Expected:**
- Games: ~200-250 (partial season, through Nov 9, 2025)
- Play-by-play events: ~100K-125K
- Player box scores: ~13K
- Team box scores: ~400-500

**Date range:** Oct 22, 2025 → Nov 9, 2025 (current)
**Fills gap:** Oct 22, 2025 → Nov 9, 2025

### Total

**Combined:**
- Games: ~1,500-1,650
- Play-by-play events: ~750K-825K
- Total size: ~800 MB - 1.2 GB

---

## 📁 File Locations

### After Collection

```
/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/
├── load_nba_schedule/parquet/
│   ├── nba_data_2024.parquet  ← NEW
│   └── nba_data_2025.parquet  ← NEW
├── load_nba_team_box/parquet/
│   ├── nba_data_2024.parquet  ← NEW
│   └── nba_data_2025.parquet  ← NEW
├── load_nba_player_box/parquet/
│   ├── nba_data_2024.parquet  ← NEW
│   └── nba_data_2025.parquet  ← NEW
└── load_nba_pbp/parquet/
    ├── nba_data_2024.parquet  ← NEW
    └── nba_data_2025.parquet  ← NEW
```

### After Loading to Database

```
nba_mcp_synthesis database:
  hoopr_raw.nba_schedule:      30,758 + ~1,500 = 32,258 games
  hoopr_raw.nba_play_by_play:  13.1M + ~800K = 13.9M events
  hoopr_raw.nba_player_box:    785K + ~98K = 883K records
  hoopr_raw.nba_team_box:      59K + ~3K = 62K records
```

---

## ✅ Success Criteria

### After Collection

- [ ] 8 new parquet files created (2 seasons × 4 data types)
- [ ] Total size: ~800 MB - 1.2 GB
- [ ] No error messages in collection output
- [ ] Files accessible at backup location

### After Loading

- [ ] Database row counts increased by expected amounts
- [ ] Latest game date: 2025-11-08 or 2025-11-09
- [ ] No gaps: Dec 2, 2024 → Nov 9, 2025
- [ ] No duplicate games (same game_id not inserted twice)

### Final Verification

```bash
# Run in nba-mcp-synthesis
export POSTGRES_DB=nba_mcp_synthesis
python /Users/ryanranft/nba-simulator-aws/scripts/validation/verify_hoopr_coverage.py
```

**Expected:**
```
📊 Overall Coverage:
   Latest Game:   2025-11-09  ← Should be current!
   Total Games:   32,000+

⚠️ POTENTIAL DATA GAPS (>7 days):
   No significant gaps found  ← Success!

✅ Current Season Data Found:
   Last Game:  2025-11-09
   Status:     ✅ Up to date (today)
```

---

## 🔧 Troubleshooting

### "hoopR package not found"

```bash
# In nba-simulator-aws environment
conda activate nba-aws
R
> install.packages("hoopR")
> quit()
```

### "Permission denied" on parquet directory

```bash
sudo chmod -R 755 /Users/ryanranft/Desktop/sports_data_backup/hoopR/
```

### "Database connection failed" during load

```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Start if needed
brew services start postgresql
```

### Collection shows "No data" for a season

**Possible causes:**
- NBA API temporary outage (retry in 10 minutes)
- Season hasn't started yet (e.g., 2025 in October)
- Rate limiting (script has built-in delays)

**Solution:** Check script output for specific errors

### Duplicate key errors during database load

```bash
# Data already exists - safe to ignore if intentional reload
# Or drop and reload:
psql -d nba_mcp_synthesis -c "TRUNCATE hoopr_raw.nba_schedule CASCADE;"
```

---

## 🚀 Optional: Ongoing Automation

### Setup Daily Collection (Recommended)

Once you have complete historical data, set up daily updates:

```bash
# In nba-simulator-aws
crontab -e
```

Add:
```cron
# Daily hoopR collection at 3 AM
0 3 * * * cd /Users/ryanranft/nba-simulator-aws && conda run -n nba-aws Rscript scripts/etl/hoopr_incremental_scraper.R >> logs/hoopr_daily.log 2>&1
```

**Benefits:**
- Automatically collects new games daily
- Updates parquet files
- Keeps nba-mcp-synthesis current
- Zero manual intervention

---

## 📊 Timeline

| Step | Duration | Activity |
|------|----------|----------|
| 1. Setup | 2 min | Navigate, activate env |
| 2. Collection | 30-45 min | hoopR API calls + saves |
| 3. Load to DB | 10-15 min | Parquet → PostgreSQL |
| 4. Verification | 2 min | Run checks |
| **Total** | **45-65 min** | **Complete process** |

---

## 💰 Cost Breakdown

| Resource | Amount | Cost/Month |
|----------|--------|------------|
| hoopR API | FREE | $0.00 |
| Compute | Local | $0.00 |
| S3 Storage | 1 GB | $0.02 |
| PostgreSQL | +1 GB | $0.06 |
| **Total** | | **~$0.08** |

---

## 🎯 Next Steps

**Immediate:**
1. Run `collect_missing_hoopr_data.sh`
2. Load to nba-mcp-synthesis database
3. Verify coverage

**Optional:**
4. Setup daily automation (cron job)
5. Configure S3 upload (already in script)
6. Share parquet files between projects

---

## 📝 Commands Summary

```bash
# === STEP 1: Collect Data ===
cd /Users/ryanranft/nba-simulator-aws
conda activate nba-aws
bash scripts/etl/collect_missing_hoopr_data.sh
# ⏱️ Wait 30-45 minutes

# === STEP 2: Load to Database ===
cd /Users/ryanranft/nba-mcp-synthesis
conda activate mcp-synthesis
python scripts/load_parquet_to_postgres.py --years 2024-2025
# ⏱️ Wait 10-15 minutes

# === STEP 3: Verify ===
export POSTGRES_DB=nba_mcp_synthesis
python /Users/ryanranft/nba-simulator-aws/scripts/validation/verify_hoopr_coverage.py
# ✅ Should show "Up to date (today)"
```

---

**Ready to execute? Start with Step 1!** 🚀

**Questions before running?** Ask me:
- Specific command explanations
- Alternative approaches
- Verification steps
- Automation setup
