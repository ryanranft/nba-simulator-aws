# Phase 1 Scraper Test Results

**Date:** October 7, 2025 - 11:00 AM

## Key Finding: SportsDataverse is Redundant

**Both use `sportsdataverse` package:**
- **hoopR**: `load_nba_*` bulk loaders → ✅ 653,437 records, 0 errors, 30 sec
- **SportsDataverse**: `espn_nba_*` per-game → ❌ Multiple errors, slow

**Recommendation: Use hoopR only. Delete SportsDataverse scraper.**

---

## Test Results

| Scraper | Status | Data Points | Errors |
|---------|--------|-------------|--------|
| NBA API | ✅ Fixed | 5,857+ files | 0 (after fix) |
| hoopR | ✅ Perfect | 653,437 | 0 |
| SportsDataverse | ❌ Broken | Partial | Multiple |
| Basketball Ref | ✅ Working | 54 games | 0 |

**Working scrapers: 3 of 4 (SportsDataverse deprecated)**

---

## Details

### hoopR ✅
- 614,447 play-by-play records
- 35,028 player box scores
- 2,640 team box scores
- 1,322 games
- Runtime: 30 seconds
- **Perfect for bulk data collection**

### Basketball Reference ✅
- Schedule: 54 games saved
- Rate limit: 3.5s (TOS compliant)
- **Best for advanced stats (47 features)**
- Slow but reliable (30 hours for 30 seasons)

### SportsDataverse ❌
- PBP serialization errors
- DataFrame filtering errors
- **REDUNDANT - Use hoopR instead**

---

## Recommendation

**Keep:**
- `scrape_nba_api_comprehensive.py` ✅
- `scrape_hoopr_nba_stats.py` ✅
- `scrape_basketball_reference.py` ✅
- `download_kaggle_database.py` ✅

**Delete:**
- `scrape_sportsdataverse.py` ❌ (redundant with hoopR)
- `run_sportsdataverse_overnight.sh` ❌

---

## Failure Recovery Procedures

### General Recovery Protocol

**If scraper fails mid-run:**

1. **Check process status**
   ```bash
   ps aux | grep [scraper_name]
   # If still running, check logs
   tail -100 /tmp/[scraper]_log.log
   ```

2. **Identify failure point**
   ```bash
   # Check output files
   ls -lht /tmp/[output_dir]/ | head -20

   # Check error logs
   grep -i "error\|exception\|failed" /tmp/[scraper]_log.log
   ```

3. **Preserve partial results**
   ```bash
   # Count files before cleanup
   ls /tmp/[output_dir]/ | wc -l

   # Backup partial results to S3 (if valuable)
   aws s3 sync /tmp/[output_dir]/ s3://nba-sim-raw-data-lake/[source]_partial/
   ```

4. **Fix issue and restart**
   ```bash
   # Stop failed process
   kill -9 [PID]

   # Fix code/config
   # ...

   # Restart scraper
   bash scripts/etl/overnight_[scraper].sh
   ```

---

### NBA API Comprehensive Scraper

**Common failures:**

#### Failure 1: Missing Team ID (Player Tracking Endpoints)

**Symptom:**
```
400 Client Error: Bad Request
Missing required parameter: team_id
```

**Cause:** Player tracking endpoints require `team_id` parameter

**Fix:**
1. Add team_id lookup from roster data
2. Filter to only active players (ROSTERSTATUS=1, TEAM_ID≠0)

**Recovery:**
```bash
# Check how many files saved before failure
ls /tmp/nba_api_comprehensive/ | wc -l

# If > 1000 files saved, preserve them
aws s3 sync /tmp/nba_api_comprehensive/ s3://nba-sim-raw-data-lake/nba_api_partial/

# Stop failed process
ps aux | grep scrape_nba_api
kill -9 [PID]

# Fix: Edit scrape_nba_api_comprehensive.py
# Add team_id parameter to player tracking endpoints

# Restart
bash scripts/etl/overnight_nba_api_comprehensive.sh
```

**Status:** ✅ Fixed (Oct 7, 10:04 AM)

---

#### Failure 2: Rate Limit Exceeded

**Symptom:**
```
429 Too Many Requests
Rate limit exceeded
```

**Cause:** Too many API calls in short period

**Recovery:**
```bash
# No code fix needed - rate limiter already at 600ms
# Just restart after cooldown period

# Wait 5 minutes
sleep 300

# Restart scraper
bash scripts/etl/overnight_nba_api_comprehensive.sh
```

**Prevention:** Scraper already has 600ms delay between calls (1.67 req/sec)

---

#### Failure 3: Network Timeout

**Symptom:**
```
requests.exceptions.ConnectionError: Connection timeout
```

**Recovery:**
```bash
# Check network
ping stats.nba.com

# If network OK, restart immediately
bash scripts/etl/overnight_nba_api_comprehensive.sh

# Scraper will skip already-downloaded files (checks existing .json)
```

**Auto-recovery:** Scraper skips existing files, safe to restart anytime

---

### hoopR Scraper

**Common failures:**

#### Failure 1: Memory Error (Large Datasets)

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Cause:** Loading 30 seasons at once (600K+ rows)

**Recovery:**
```bash
# Reduce batch size: Edit scrape_hoopr_nba_stats.py
# Change: seasons = range(2002, 2025)
# To:     seasons = range(2002, 2010)  # Process in batches

# Run batch 1 (2002-2009)
python scripts/etl/scrape_hoopr_nba_stats.py --seasons 2002-2009

# Run batch 2 (2010-2017)
python scripts/etl/scrape_hoopr_nba_stats.py --seasons 2010-2017

# Run batch 3 (2018-2025)
python scripts/etl/scrape_hoopr_nba_stats.py --seasons 2018-2025
```

---

#### Failure 2: sportsdataverse Package Error

**Symptom:**
```
ModuleNotFoundError: No module named 'sportsdataverse'
```

**Recovery:**
```bash
# Reinstall package
pip install --upgrade sportsdataverse

# Restart scraper
bash scripts/etl/run_hoopr_overnight.sh
```

---

### Basketball Reference Scraper

**Common failures:**

#### Failure 1: Rate Limit Block (HTTP 429)

**Symptom:**
```
429 Too Many Requests
Your IP has been temporarily blocked
```

**Cause:** Scraped too fast (TOS requires 3 seconds between requests)

**Recovery:**
```bash
# STOP immediately to avoid permanent ban
kill -9 [PID]

# Wait 24 hours before resuming
# Basketball Reference blocks are usually temporary

# Resume after 24 hours with slower rate
# Edit scrape_basketball_reference.py
# Increase: time.sleep(3.5)  # Was 3.0
```

**Prevention:** Never reduce rate limit below 3 seconds

---

#### Failure 2: HTML Structure Changed

**Symptom:**
```
IndexError: list index out of range
No table found with id='schedule'
```

**Cause:** Basketball Reference changed HTML structure

**Recovery:**
```bash
# Inspect current HTML
curl "https://www.basketball-reference.com/leagues/NBA_2024_games.html" > test.html

# Check table IDs
grep "id=" test.html | grep "table"

# Update scraper with new table ID
# Edit scrape_basketball_reference.py
```

---

### Kaggle Database Download

**Common failures:**

#### Failure 1: Authentication Error

**Symptom:**
```
401 Unauthorized: You must be authenticated
```

**Cause:** Missing or expired Kaggle API token

**Recovery:**
```bash
# Re-download token from Kaggle account settings
# https://www.kaggle.com/[username]/account

# Save to correct location
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Retry download
python scripts/etl/download_kaggle_database.py
```

**See:** `docs/KAGGLE_API_SETUP.md` for detailed token setup

---

#### Failure 2: Disk Space Full

**Symptom:**
```
OSError: [Errno 28] No space left on device
```

**Cause:** Kaggle database is 2-5 GB

**Recovery:**
```bash
# Check disk space
df -h

# Clean up temp files
rm -rf /tmp/nba_*

# Retry download
python scripts/etl/download_kaggle_database.py
```

---

## Monitoring Best Practices

### Pre-Flight Checks

**Before starting overnight scraper:**
```bash
# 1. Check disk space (need 10+ GB free)
df -h /tmp

# 2. Check network
ping stats.nba.com
ping www.basketball-reference.com

# 3. Check credentials (if needed)
cat ~/.kaggle/kaggle.json  # For Kaggle
aws sts get-caller-identity  # For S3 upload

# 4. Check process not already running
ps aux | grep scrape_

# 5. Backup existing output (if resuming)
if [ -d "/tmp/nba_api_comprehensive" ]; then
    mv /tmp/nba_api_comprehensive /tmp/nba_api_backup_$(date +%s)
fi
```

---

### During Execution

**Monitor progress:**
```bash
# Watch log file
tail -f /tmp/[scraper]_log.log

# Check file count (updates every few seconds)
watch -n 5 'ls /tmp/[output_dir]/ | wc -l'

# Check error rate
grep -i "error" /tmp/[scraper]_log.log | wc -l
```

**Kill criteria:**
- Error rate > 10% → Stop and investigate
- No new files for 10+ minutes → Stop (likely stuck)
- Disk space < 1 GB → Stop (will run out of space)

---

### Post-Execution

**Validation checklist:**
```bash
# 1. Check process exited cleanly
echo $?  # Should be 0

# 2. Count output files
ls /tmp/[output_dir]/ | wc -l
# Compare to expected count

# 3. Check for errors in log
grep -i "error\|exception" /tmp/[scraper]_log.log

# 4. Validate sample files (check JSON validity)
python -m json.tool /tmp/[output_dir]/[file1].json
python -m json.tool /tmp/[output_dir]/[file2].json

# 5. Upload to S3
aws s3 sync /tmp/[output_dir]/ s3://nba-sim-raw-data-lake/[source]/

# 6. Verify S3 upload
aws s3 ls s3://nba-sim-raw-data-lake/[source]/ | wc -l

# 7. Clean up local files
rm -rf /tmp/[output_dir]/
```

---

## Emergency Contact

**If all recovery procedures fail:**

1. **Stop scraper immediately** - Prevent further damage
2. **Preserve logs** - Copy to S3 for debugging
3. **Document error** - Create GitHub issue with logs
4. **Check source status** - Website may be down

**Useful commands:**
```bash
# Save logs to S3
aws s3 cp /tmp/[scraper]_log.log s3://nba-sim-raw-data-lake/logs/failure_$(date +%s).log

# Check source website status
curl -I https://stats.nba.com
curl -I https://www.basketball-reference.com

# Create GitHub issue
gh issue create --title "Scraper failure: [name]" --body "$(cat /tmp/[scraper]_log.log | tail -100)"
```

---

*Last updated: October 7, 2025*
*For detailed scraper status, see: `docs/SCRAPER_STATUS_REPORT.md`*
