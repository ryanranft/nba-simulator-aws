# Workflow #51: Phase 9 Overnight Batch Processing

**Purpose:** Process ESPN play-by-play data into box score snapshots overnight
**Category:** Data Processing
**Prerequisites:** Phase 9.0 (System Architecture) and 9.1 (ESPN Processor) complete
**Related Workflows:**
- Workflow #38: [Overnight Scraper Handoff Protocol](38_overnight_scraper_handoff.md)
- Workflow #40: [Scraper Operations Complete](40_scraper_operations_complete.md)

---

## Overview

Phase 9 converts raw play-by-play data into granular box score snapshots for temporal queries. This workflow handles overnight batch processing of 44,826 ESPN games.

**Key Capabilities:**
- Generate box score snapshots after each play-by-play event
- Track quarter-by-quarter statistics
- Verify final box scores against actual
- Support temporal queries ("what was the score at 7:32 Q3?")
- Enable betting odds integration (quarter outcomes)

---

## Pre-Launch Checklist

### 1. Verify System Architecture

**Check database schema exists:**
```bash
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres -d nba_simulator \
     -c "\dt phase9.*"
```

Expected tables:
- `phase9.game_state_snapshots`
- `phase9.player_snapshot_stats`
- `phase9.quarter_box_scores`
- `phase9.box_score_verification`

**Check processor code:**
```bash
ls -lh scripts/pbp_to_boxscore/
```

Expected files:
- `box_score_snapshot.py` (data structures)
- `base_processor.py` (abstract base)
- `espn_processor.py` (ESPN implementation)

### 2. Verify Data Availability

**Check ESPN play-by-play data:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/pbp/ --recursive | wc -l
```

Expected: 44,826 files

**Test sample processing:**
```python
from scripts.pbp_to_boxscore.espn_processor import ESPNPlayByPlayProcessor

processor = ESPNPlayByPlayProcessor()
snapshots, verification = processor.process_game('401736813')
print(f"Test: {len(snapshots)} snapshots, Final: {snapshots[-1].home_score}-{snapshots[-1].away_score}")
```

### 3. Check Resources

**Disk space:**
```bash
df -h /tmp
# Need: 10GB minimum for temp snapshots
```

**Memory:**
```bash
free -h
# Recommended: 4GB+ available
```

**RDS connection:**
```bash
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres -d nba_simulator -c "SELECT version();"
```

---

## Batch Processing Modes

### Mode 1: Test Run (Recommended First)

Process small batch to verify everything works:

```bash
python3 scripts/pbp_to_boxscore/batch_process_espn.py \
  --season 2024 \
  --limit 10 \
  --output /tmp/phase9_test/ \
  --verbose
```

**Expected output:**
- 10 games processed
- ~4,590 snapshots (459 avg per game)
- All validations pass
- No errors

### Mode 2: Single Season

Process one season overnight:

```bash
nohup python3 scripts/pbp_to_boxscore/batch_process_espn.py \
  --season 2024 \
  --output /tmp/phase9_snapshots/ \
  --save-rds \
  > /tmp/phase9_espn_2024.log 2>&1 &
```

**Expected:**
- ~1,230 games (typical season)
- ~565,000 snapshots
- Runtime: 2-4 hours
- Storage: ~100MB RDS, ~50MB S3

### Mode 3: Full Historical (All Games)

Process all 44,826 games overnight:

```bash
nohup python3 scripts/pbp_to_boxscore/batch_process_espn.py \
  --start-season 1993 \
  --end-season 2025 \
  --output /tmp/phase9_snapshots/ \
  --save-rds \
  --checkpoint-every 100 \
  > /tmp/phase9_espn_full.log 2>&1 &
```

**Expected:**
- 44,826 games
- ~22 million snapshots
- Runtime: 15-20 hours
- Storage: ~2GB RDS, ~500MB S3 Parquet

---

## Monitoring During Processing

### Quick Status Check

```bash
tail -50 /tmp/phase9_espn_full.log | grep "Progress\|ERROR"
```

### Detailed Progress

```bash
# Check games processed
grep "Processed game" /tmp/phase9_espn_full.log | wc -l

# Check current game
tail -20 /tmp/phase9_espn_full.log

# Check error count
grep -c "ERROR" /tmp/phase9_espn_full.log

# Check snapshot count
find /tmp/phase9_snapshots/ -name "*.json" | wc -l
```

### Monitor Resource Usage

```bash
# Check process is running
ps aux | grep batch_process_espn

# Check memory usage
ps aux | grep batch_process_espn | awk '{print $4"%"}'

# Check disk usage
du -sh /tmp/phase9_snapshots/
```

---

## Validation Procedures

### 1. Snapshot Validation

**Check snapshot structure:**
```python
import json

with open('/tmp/phase9_snapshots/401736813_snapshot_100.json') as f:
    snapshot = json.load(f)

print(f"Game ID: {snapshot['game_id']}")
print(f"Event: {snapshot['event_num']}")
print(f"Score: {snapshot['home_score']}-{snapshot['away_score']}")
print(f"Quarter: {snapshot['quarter']}")
print(f"Players tracked: {len(snapshot['player_stats'])}")
```

### 2. Final Score Verification

**Compare against ESPN box scores:**
```bash
# Get final snapshots
find /tmp/phase9_snapshots/ -name "*_final.json" | head -10 | while read file; do
  echo "$(basename $file): $(jq -r '.home_score + "-" + .away_score' $file)"
done
```

### 3. Database Validation

**Check RDS snapshot counts:**
```sql
-- Connect to RDS
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator

-- Check snapshot counts
SELECT
  COUNT(*) as total_snapshots,
  COUNT(DISTINCT game_id) as games_processed,
  AVG(snapshot_count) as avg_snapshots_per_game
FROM (
  SELECT game_id, COUNT(*) as snapshot_count
  FROM phase9.game_state_snapshots
  GROUP BY game_id
) sub;

-- Check score progression
SELECT game_id, event_num, home_score, away_score
FROM phase9.game_state_snapshots
WHERE game_id = '401736813'
ORDER BY event_num
LIMIT 20;
```

### 4. Quality Checks

**Validation pass rate:**
```bash
grep "Validation" /tmp/phase9_espn_full.log | \
  awk '{sum+=$NF; count++} END {print "Average validation rate: " sum/count "%"}'
```

**Target:** > 95% validation pass rate

**Error breakdown:**
```bash
grep "ERROR" /tmp/phase9_espn_full.log | \
  awk -F: '{print $NF}' | \
  sort | uniq -c | sort -rn
```

---

## Completion Checklist

After batch processing completes:

- [ ] All games processed (check log for "Completed X/44826 games")
- [ ] No critical errors (< 5% error rate acceptable)
- [ ] Snapshots saved to RDS (verify with SQL query)
- [ ] S3 Parquet files created (check `s3://nba-sim-raw-data-lake/phase9_snapshots/`)
- [ ] Final scores match ESPN data (spot check 10-20 games)
- [ ] Validation rate > 95%
- [ ] Database indexes created (for performance)
- [ ] Views working (test `phase9.latest_snapshots`)
- [ ] Documentation updated (PROGRESS.md, phase 9 docs)

---

## Troubleshooting

### No Snapshots Generated

**Check:**
1. Game data exists in S3
2. Game data format is correct (has 'events' field)
3. No connection errors to S3

**Fix:**
```bash
# Test single game
python3 -c "
from scripts.pbp_to_boxscore.espn_processor import ESPNPlayByPlayProcessor
processor = ESPNPlayByPlayProcessor()
processor.process_game('401736813')
"
```

### High Error Rate (> 10%)

**Check:**
1. RDS connection stable
2. S3 access working
3. Sufficient disk space
4. Sufficient memory

**Fix:**
```bash
# Check RDS connectivity
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator -c "SELECT 1;"

# Check S3 access
aws s3 ls s3://nba-sim-raw-data-lake/pbp/ | head -10

# Check resources
df -h /tmp
free -h
```

### Validation Failures

**Check:**
1. ESPN data quality for specific games
2. Parser logic handling edge cases
3. Score calculation logic

**Debug specific game:**
```python
from scripts.pbp_to_boxscore.espn_processor import ESPNPlayByPlayProcessor

processor = ESPNPlayByPlayProcessor()
snapshots, verification = processor.process_game('GAME_ID', verify=True)

if verification:
    print(f"Final score match: {verification.final_score_match}")
    print(f"Discrepancies: {verification.total_discrepancies}")
    print(f"Details: {verification.discrepancy_details}")
```

---

## Performance Optimization

### For Faster Processing

**1. Parallel Processing:**
```bash
# Process multiple seasons in parallel
for season in 2020 2021 2022 2023 2024; do
  nohup python3 scripts/pbp_to_boxscore/batch_process_espn.py \
    --season $season \
    > /tmp/phase9_${season}.log 2>&1 &
done
```

**2. RDS Batch Inserts:**
- Use COPY instead of individual INSERTs
- Batch size: 1000 snapshots per transaction
- Disable indexes during bulk load, rebuild after

**3. S3 Optimization:**
- Use multipart upload for large files
- Compress with gzip before upload
- Upload in batches (every 100 games)

---

## Integration with Betting Odds (Phase 7)

Once Phase 9 is complete, quarter box scores enable:

1. **Quarter-by-quarter predictions**
   - Predict Q1, Q2, Q3, Q4 outcomes independently
   - Compare against betting odds

2. **Live game modeling**
   - Update win probability after each event
   - Track against real-time odds

3. **Historical backtesting**
   - Test betting strategies on 22M snapshots
   - Calculate ROI per strategy

**Next Step:** Phase 9.8 (Betting Integration)

---

## Related Documentation

- **Phase 9 Index:** `docs/phases/PHASE_9_INDEX.md`
- **System Architecture:** `docs/phases/phase_9/9.0_system_architecture.md`
- **ESPN Processor:** `docs/phases/phase_9/9.1_espn_processor.md`
- **Database Schema:** `sql/phase9_box_score_snapshots.sql`

---

*Created: October 12, 2025*
*Status: Active - Phase 9.0 and 9.1 Complete*








