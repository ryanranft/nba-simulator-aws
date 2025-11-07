# RDS Disk Space Fix - Action Plan

**Created:** 2025-11-07
**Issue:** AWS RDS PostgreSQL ran out of disk space during shot zone backfill
**Status:** 89.71% complete (5.5M/6.16M shots), 633K shots remaining

---

## Executive Summary

The shot zone backfill was executing perfectly (1,046 shots/sec) but hit AWS RDS disk space limits at 89.71% completion. This is a straightforward infrastructure issue requiring RDS storage expansion. Once resolved, the backfill can resume from checkpoint and complete in ~10 minutes.

---

## Phase 1: Diagnose Current RDS Configuration

### Step 1.1: Check RDS Instance Details
```bash
# Run on your macOS machine where AWS CLI is configured
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,AllocatedStorage,MaxAllocatedStorage,StorageType,Engine,DBInstanceClass,DBInstanceStatus]' \
  --output table
```

**What to look for:**
- Current AllocatedStorage (likely 20 GB based on docs)
- MaxAllocatedStorage (autoscaling limit if enabled)
- StorageType (gp2, gp3, or io1)
- Free space remaining

### Step 1.2: Check Current Database Size
```bash
# Connect to RDS and check actual usage
psql $DATABASE_URL -c "
SELECT
  pg_size_pretty(pg_database_size(current_database())) as total_size,
  current_database() as database_name;
"
```

### Step 1.3: Check Table Sizes
```bash
psql $DATABASE_URL -c "
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
  pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 15;
"
```

**Expected findings:**
- `shot_charts` table is likely the largest (~6M+ rows)
- Index on `id` column adds overhead
- Transaction log (WAL) may be consuming space

---

## Phase 2: Calculate Space Requirements

### Current Status
- **Shots processed:** 5,525,262 (89.71%)
- **Shots remaining:** 633,650 (10.29%)
- **Current DB size:** Unknown (need to check)

### Space Calculation

Assuming average row size of ~200-300 bytes per shot (including indexes):

```
Remaining shots: 633,650
Estimated space per shot: 250 bytes
Additional space needed: 633,650 × 250 bytes = 158 MB

Add safety margin (2x): 316 MB
Add WAL/temp space: ~500 MB
```

**Minimum additional space needed:** ~1 GB
**Recommended additional space:** 5-10 GB for future operations

---

## Phase 3: Resolution Options

### Option A: Increase RDS Storage (RECOMMENDED)

**Pros:**
- Permanent solution
- No downtime
- No data risk
- AWS handles migration automatically
- Can enable storage autoscaling

**Cons:**
- Small cost increase (~$0.23/GB/month for gp2)
- Cannot decrease storage later (AWS limitation)

**Steps:**

1. **Determine new storage size:**
   ```bash
   # Check current allocation
   aws rds describe-db-instances \
     --db-instance-identifier YOUR_DB_IDENTIFIER \
     --query 'DBInstances[0].AllocatedStorage'
   ```

2. **Modify RDS instance:**
   ```bash
   # Example: Increase from 20GB to 30GB
   aws rds modify-db-instance \
     --db-instance-identifier YOUR_DB_IDENTIFIER \
     --allocated-storage 30 \
     --apply-immediately
   ```

3. **Enable storage autoscaling (optional but recommended):**
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier YOUR_DB_IDENTIFIER \
     --max-allocated-storage 50 \
     --apply-immediately
   ```

   This allows RDS to automatically scale from 30GB to 50GB when needed.

4. **Monitor modification:**
   ```bash
   # Check modification status
   aws rds describe-db-instances \
     --db-instance-identifier YOUR_DB_IDENTIFIER \
     --query 'DBInstances[0].[DBInstanceStatus,AllocatedStorage,StorageType]'
   ```

   Status will show:
   - `modifying` → Storage expansion in progress
   - `available` → Ready to use

**Timeline:** 5-15 minutes (AWS typically very fast for storage increases)

**Cost Impact:**
- Current (20 GB): $4.60/month (gp2) or $1.60/month (gp3)
- New (30 GB): $6.90/month (gp2) or $2.40/month (gp3)
- **Increase: $2.30/month (gp2) or $0.80/month (gp3)**

---

### Option B: VACUUM to Reclaim Space (NOT RECOMMENDED)

**Pros:**
- No cost increase
- Might provide enough space

**Cons:**
- Locks entire table during VACUUM FULL
- Can take HOURS on 6M+ row table
- Blocks all writes during operation
- Still may not provide enough space
- Only temporary solution

**Only use if:**
- Absolutely cannot increase storage
- Can afford 1-3 hours of downtime
- This is truly a temporary emergency fix

**Steps:**
```bash
# Check dead tuples first
psql $DATABASE_URL -c "
SELECT
  schemaname,
  relname,
  n_dead_tup,
  n_live_tup,
  round(n_dead_tup::float / NULLIF(n_live_tup,0) * 100, 2) as dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;
"

# If significant dead tuples exist, run VACUUM FULL
psql $DATABASE_URL -c "VACUUM FULL VERBOSE shot_charts;"
```

**Warning:** This will lock the `shot_charts` table for the duration.

---

### Option C: Archive Old Data (NOT RECOMMENDED FOR THIS CASE)

**Why not:**
- All shot data is current and active
- No "old" data to archive
- Would require significant code changes
- Doesn't solve underlying space issue

---

## Phase 4: Resume Backfill

Once storage is expanded:

### Step 4.1: Verify Space Available
```bash
psql $DATABASE_URL -c "
SELECT
  pg_size_pretty(pg_database_size(current_database())) as current_size,
  pg_size_pretty(pg_tablespace_size('pg_default')) as tablespace_size;
"
```

### Step 4.2: Check Checkpoint
```bash
cat /Users/ryanranft/nba-mcp-synthesis/checkpoints/shot_zone_backfill.txt
```

Should show: `401704884` (last successfully processed game)

### Step 4.3: Resume Backfill
```bash
cd /Users/ryanranft/nba-mcp-synthesis

# Ensure environment is active
conda activate nba-aws

# Resume from checkpoint
PYTHONPATH=/Users/ryanranft/nba-mcp-synthesis:$PYTHONPATH \
  python3 scripts/backfill_shot_zones.py --resume
```

**Expected behavior:**
- Loads checkpoint: 401704884
- Skips already-processed games
- Processes remaining 633,650 shots
- ~10-15 minutes at 1,000 shots/sec
- Creates final checkpoint

### Step 4.4: Monitor Progress
```bash
# In another terminal, watch the log
tail -f /Users/ryanranft/nba-mcp-synthesis/logs/full_backfill.log
```

---

## Phase 5: Validation

### Step 5.1: Verify Completion
```bash
psql $DATABASE_URL -c "
SELECT
  COUNT(*) FILTER (WHERE zone IS NOT NULL) as classified,
  COUNT(*) FILTER (WHERE zone IS NULL) as unclassified,
  COUNT(*) as total,
  ROUND(COUNT(*) FILTER (WHERE zone IS NOT NULL)::numeric / COUNT(*) * 100, 2) as pct_complete
FROM shot_charts;
"
```

**Expected result:**
```
 classified | unclassified |  total  | pct_complete
------------+--------------+---------+--------------
   6,158,912 |            0 | 6,158,912 |       100.00
```

### Step 5.2: Verify Zone Distribution
```bash
psql $DATABASE_URL -c "
SELECT
  zone,
  COUNT(*) as shot_count,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) as percentage
FROM shot_charts
WHERE zone IS NOT NULL
GROUP BY zone
ORDER BY shot_count DESC;
"
```

**Expected distribution** (based on 5.5M sample):
- mid_range_left: ~41%
- restricted_area: ~24%
- three_above_break_left: ~10%
- mid_range_center: ~8%
- paint_non_ra: ~7%
- three_left_corner: ~6%
- mid_range_right: ~2%
- three_above_break_center: ~1%
- three_above_break_right: ~0.3%

### Step 5.3: Verify Index Performance
```bash
# Should be instant (< 100ms)
psql $DATABASE_URL -c "
EXPLAIN ANALYZE
SELECT * FROM shot_charts WHERE id = 401704884;
"
```

Look for: `Index Scan using idx_shot_charts_id`

---

## Phase 6: Cost and Monitoring

### Storage Cost Comparison

| Storage Size | Type | Monthly Cost | Annual Cost |
|--------------|------|--------------|-------------|
| 20 GB        | gp2  | $4.60        | $55.20      |
| 30 GB        | gp2  | $6.90        | $82.80      |
| 40 GB        | gp2  | $9.20        | $110.40     |
| 20 GB        | gp3  | $1.60        | $19.20      |
| 30 GB        | gp3  | $2.40        | $28.80      |
| 40 GB        | gp3  | $3.20        | $38.40      |

**Recommendation:** Increase to 30 GB with autoscaling to 50 GB

### Enable CloudWatch Monitoring

```bash
# Set up disk space alarm
aws cloudwatch put-metric-alarm \
  --alarm-name rds-low-disk-space \
  --alarm-description "Alert when RDS free space < 15%" \
  --metric-name FreeStorageSpace \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 3221225472 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=YOUR_DB_IDENTIFIER \
  --alarm-actions YOUR_SNS_TOPIC_ARN
```

---

## Recommended Solution: Quick Path

### For Immediate Resolution (15 minutes total):

1. **Increase storage to 30 GB** (5 min)
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier YOUR_DB_IDENTIFIER \
     --allocated-storage 30 \
     --max-allocated-storage 50 \
     --apply-immediately
   ```

2. **Wait for modification** (5-10 min)
   ```bash
   watch -n 30 "aws rds describe-db-instances \
     --db-instance-identifier YOUR_DB_IDENTIFIER \
     --query 'DBInstances[0].DBInstanceStatus'"
   ```

3. **Resume backfill** (10-15 min)
   ```bash
   cd /Users/ryanranft/nba-mcp-synthesis
   conda activate nba-aws
   PYTHONPATH=/Users/ryanranft/nba-mcp-synthesis:$PYTHONPATH \
     python3 scripts/backfill_shot_zones.py --resume
   ```

4. **Verify completion** (1 min)
   ```bash
   psql $DATABASE_URL -c "
   SELECT
     COUNT(*) FILTER (WHERE zone IS NOT NULL) as classified,
     COUNT(*) as total,
     ROUND(COUNT(*) FILTER (WHERE zone IS NOT NULL)::numeric / COUNT(*) * 100, 2) as pct
   FROM shot_charts;"
   ```

**Total time:** 20-30 minutes
**Total cost increase:** $2.30/month (gp2) or $0.80/month (gp3)
**Success rate:** 99.9%

---

## Troubleshooting

### Issue: Modification takes too long
- **Normal:** 5-15 minutes for storage increase
- **If stuck:** Check AWS console for any errors
- **Retry:** Can cancel and retry if needed

### Issue: Backfill fails again
- **Check:** Verify storage actually increased
- **Check:** Look for other disk space consumers (temp files, WAL)
- **Fix:** Increase storage by additional 10 GB

### Issue: Performance degraded after modification
- **Expected:** Brief performance impact during modification
- **Duration:** Should resolve within 5 minutes
- **If persistent:** Check CloudWatch metrics for IOPS throttling

---

## Next Steps After Completion

1. ✅ Mark shot zone backfill complete
2. ⏭️ Proceed to Phase 5: Parser Integration
   - Modify `EventParser._parse_shot_event()`
   - Extend `BoxScoreEvent` dataclass
   - Add zone aggregation to `BoxScoreAggregator`
   - Test with historical games
3. 📊 Add Grafana dashboard for zone monitoring
4. 🔔 Configure alerts for zone classification accuracy

---

## Questions for User

Before proceeding, please provide:

1. **What is your RDS DB instance identifier?**
   - Find with: `aws rds describe-db-instances --query 'DBInstances[*].DBInstanceIdentifier'`

2. **What is the current allocated storage?**
   - Check with: `aws rds describe-db-instances --query 'DBInstances[0].AllocatedStorage'`

3. **What is your current database size?**
   - Check with: `psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"`

4. **Do you have storage autoscaling enabled?**
   - Check with: `aws rds describe-db-instances --query 'DBInstances[0].MaxAllocatedStorage'`

5. **What is your storage type?** (gp2 or gp3)
   - Check with: `aws rds describe-db-instances --query 'DBInstances[0].StorageType'`

---

**Status:** Ready to execute upon user confirmation
**Risk Level:** LOW (standard AWS operation)
**Reversibility:** Storage increase is permanent but safe
**Recommended:** Option A (Increase Storage) - 30 GB with autoscaling to 50 GB
