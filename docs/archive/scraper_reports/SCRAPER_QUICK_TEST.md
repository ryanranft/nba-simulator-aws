# Quick Scraper Test Commands

**Purpose:** Test each scraper with a single season to catch errors before running overnight

---

## 1. NBA API (Currently Running ✅)

```bash
# Check status
ps aux | grep 14497
tail -50 /tmp/nba_api_comprehensive_restart.log

# When complete, verify data
find /tmp/nba_api_comprehensive -type f -name "*.json" | wc -l
du -sh /tmp/nba_api_comprehensive
```

---

## 2. hoopR NBA Stats (Quick Test - 5 mins)

```bash
# Test single season
python scripts/etl/scrape_hoopr_nba_stats.py \
  --season 2024 \
  --all-endpoints \
  --output-dir /tmp/test_hoopr

# Expected output:
# - Schedule: 1,322 games
# - PBP data: ~500k plays
# - Box scores: player + team
# Runtime: ~5 minutes

# Verify
find /tmp/test_hoopr -type f | wc -l
du -sh /tmp/test_hoopr
```

---

## 3. SportsDataverse (Quick Test - 3 mins)

```bash
# Test single season
python scripts/etl/scrape_sportsdataverse.py \
  --season 2024 \
  --output-dir /tmp/test_sportsdataverse

# Expected output:
# - Schedule: ~500 games
# - PBP: Available if requested
# - Box scores: Available if requested
# Runtime: ~3 minutes

# Verify
find /tmp/test_sportsdataverse -type f | wc -l
du -sh /tmp/test_sportsdataverse
```

---

## 4. Basketball Reference (Quick Test - 2 mins)

```bash
# Test single season schedule only (fast)
python scripts/etl/scrape_basketball_reference.py \
  --season 2024 \
  --schedule \
  --output-dir /tmp/test_bref

# Expected output:
# - Schedule data
# Runtime: ~1-2 minutes (rate limited)

# Full test (slower - 5 minutes)
python scripts/etl/scrape_basketball_reference.py \
  --season 2024 \
  --all \
  --output-dir /tmp/test_bref

# Verify
ls -lh /tmp/test_bref/
```

---

## 5. Kaggle Database (Quick Test - 30 secs)

```bash
# Test download (doesn't extract data)
python scripts/etl/download_kaggle_database.py \
  --output-dir /tmp/test_kaggle

# Expected output:
# - basketball.zip (~300 MB)
# - basketball.sqlite (after extraction)
# Runtime: ~30 seconds

# Verify
ls -lh /tmp/test_kaggle/
```

---

## Parallel Testing (Run All At Once)

```bash
# Run all scrapers in parallel for 2024 season
python scripts/etl/scrape_hoopr_nba_stats.py --season 2024 --all-endpoints --output-dir /tmp/test_hoopr > /tmp/hoopr_test.log 2>&1 &
python scripts/etl/scrape_sportsdataverse.py --season 2024 --output-dir /tmp/test_sportsdataverse > /tmp/sdv_test.log 2>&1 &
python scripts/etl/scrape_basketball_reference.py --season 2024 --schedule --output-dir /tmp/test_bref > /tmp/bref_test.log 2>&1 &

# Check progress
tail -f /tmp/hoopr_test.log
tail -f /tmp/sdv_test.log
tail -f /tmp/bref_test.log

# Wait for completion (~5-10 minutes)
wait

# Review results
echo "hoopR files: $(find /tmp/test_hoopr -type f | wc -l)"
echo "SportsDataverse files: $(find /tmp/test_sportsdataverse -type f | wc -l)"
echo "Basketball Ref files: $(find /tmp/test_bref -type f | wc -l)"
```

---

## Error Detection

```bash
# Check for Python errors in logs
grep -i "error\|exception\|failed" /tmp/hoopr_test.log
grep -i "error\|exception\|failed" /tmp/sdv_test.log
grep -i "error\|exception\|failed" /tmp/bref_test.log

# Check for HTTP errors (Basketball Ref)
grep -i "403\|429\|500\|502\|503" /tmp/bref_test.log

# Check for empty output directories
[ -z "$(ls -A /tmp/test_hoopr)" ] && echo "⚠️ hoopR output empty"
[ -z "$(ls -A /tmp/test_sportsdataverse)" ] && echo "⚠️ SportsDataverse output empty"
[ -z "$(ls -A /tmp/test_bref)" ] && echo "⚠️ Basketball Ref output empty"
```

---

## Expected Runtimes

| Scraper | Test (1 season) | Full (30 seasons) |
|---------|----------------|-------------------|
| NBA API | ~10 min | 4-5 hours |
| hoopR | ~5 min | 3-4 hours |
| SportsDataverse | ~3 min | 2-3 hours |
| Basketball Ref | ~5 min | 30 hours |
| Kaggle | ~30 sec | ~30 sec |

---

## Success Criteria

✅ **hoopR:**
- Files created: 50+ JSON files
- Size: 50-100 MB
- No import errors

✅ **SportsDataverse:**
- Files created: 10+ JSON files
- Size: 20-50 MB
- No import errors

✅ **Basketball Ref:**
- Files created: 1-3 JSON/CSV files
- Size: 1-5 MB
- No HTTP 429 (rate limit) errors

✅ **Kaggle:**
- File: basketball.sqlite exists
- Size: ~1 GB
- No authentication errors

---

*Created: 2025-10-07 10:35 AM*
*Use these commands to quickly verify all scrapers before overnight runs*