# Basketball Reference Play-by-Play Discovery System

**Status:** ✅ Discovery script ready to run
**Created:** October 18, 2025
**Purpose:** Find the earliest available play-by-play data on Basketball Reference

---

## Quick Summary

We don't know how far back Basketball Reference's play-by-play data goes. This discovery script will find out!

**Current known PBP coverage:**
- **ESP API:** 1993-2025 (earliest source)
- **NBA API:** 1996-2025
- **hoopR:** 2002-2025
- **Basketball Reference:** Unknown (this is what we're discovering!)

**Key question:** Does Basketball Reference have PBP data from **before 1993**?

---

## How It Works

### Discovery Strategy

1. **Start from 2024** (we know recent games have PBP)
2. **Work backwards** year by year (2024 → 2023 → 2022 → ...)
3. **Test 10 random games per season**
4. **Check each game** for PBP table existence
5. **Count PBP events** in games that have it
6. **Stop early** if 3 consecutive years have no PBP
7. **Generate report** with findings

### Why This Approach?

- **Sample testing** is faster than checking every game (~350 games vs ~70,000)
- **Random sampling** gives representative coverage
- **Working backwards** from known good data is efficient
- **Early termination** saves time once we find the boundary

---

## Running the Discovery

### Basic Run (Recommended)

```bash
# Test 2024 down to 1990 (10 games per year)
python scripts/etl/basketball_reference_pbp_discovery.py
```

**Runtime:** ~30 minutes
**Games tested:** ~350
**Rate limit:** 12 seconds/game (Basketball Reference requirement)

### Custom Options

```bash
# Test fewer years (faster)
python scripts/etl/basketball_reference_pbp_discovery.py --start-year 2024 --end-year 2000

# Test more games per year (more accurate)
python scripts/etl/basketball_reference_pbp_discovery.py --games-per-year 20

# Verbose output (see every game tested)
python scripts/etl/basketball_reference_pbp_discovery.py --verbose

# Quick test (just 5 recent years)
python scripts/etl/basketball_reference_pbp_discovery.py --start-year 2024 --end-year 2020 --games-per-year 5
```

---

## Expected Output

### Console Output (Real-time)

```
======================================================================
BASKETBALL REFERENCE PLAY-BY-PLAY DISCOVERY
======================================================================

Years to test: 2024 down to 1990
Games per year: 10
Total tests: ~350
Estimated time: ~30.0 minutes
Started: 2025-10-18 21:30:00

======================================================================
Testing 2023-24 season...
======================================================================
Testing 10 sample games...

Results:
  Games tested:     10
  Games with PBP:   10 (100.0%)
  Avg events/game:  520
  ✅ PBP DATA FOUND for 2024

...

======================================================================
Testing 1999-00 season...
======================================================================
Testing 10 sample games...

Results:
  Games tested:     10
  Games with PBP:   3 (30.0%)
  Avg events/game:  480
  ✅ PBP DATA FOUND for 2000

...

======================================================================
Testing 1994-95 season...
======================================================================
Testing 10 sample games...

Results:
  Games tested:     10
  Games with PBP:   0 (0.0%)
  Avg events/game:  0
  ❌ NO PBP DATA for 1995

⚠️  Found 3 consecutive years with no PBP. Stopping early.
```

### Discovery Report

```
======================================================================
DISCOVERY REPORT
======================================================================

Testing Summary:
  Total games tested:  240
  Games with PBP:      180
  Earliest PBP year:   2000

Year-by-Year Results:
Year     Tested     With PBP     % Coverage   Status
----------------------------------------------------------------------
2024     10         10           100.0%     ✅ HAS PBP
2023     10         10           100.0%     ✅ HAS PBP
2022     10         10           100.0%     ✅ HAS PBP
...
2000     10         8            80.0%      ✅ HAS PBP
1999     10         2            20.0%      ✅ HAS PBP
1998     10         0            0.0%       ❌ NO PBP
1997     10         0            0.0%       ❌ NO PBP

Comparison with Other Sources:
  ESPN API:          1993-2025
  NBA API:           1996-2025
  hoopR:             2002-2025
  Basketball Ref:    2000-2025

✅ Basketball Reference has PBP earlier than hoopR (2002)
   This fills a 2-year gap!

Recommendations:
  1. Run historical PBP backfill starting from 2000
  2. Estimated backfill: ~31,250 games over ~4.3 days
  3. Use separate storage path: s3://.../basketball_reference/pbp/
  4. Cross-validate overlapping years with ESPN/NBA API

✓ Detailed report saved to: reports/basketball_reference_pbp_discovery_20251018_213000.json
✓ Complete: 2025-10-18 22:00:00
```

### JSON Report File

Located at: `reports/basketball_reference_pbp_discovery_{timestamp}.json`

```json
{
  "discovery_date": "2025-10-18T22:00:00",
  "earliest_pbp_year": 2000,
  "total_games_tested": 240,
  "total_pbp_found": 180,
  "results_by_year": {
    "2024": {
      "season": 2024,
      "games_tested": 10,
      "games_with_pbp": 10,
      "total_pbp_events": 5200,
      "sample_game_ids": ["202410050BOS", ...],
      "pbp_game_ids": ["202410050BOS", ...]
    },
    ...
  }
}
```

---

## Possible Outcomes

### Scenario 1: PBP Earlier Than ESPN (1993)
**Example:** Basketball Reference has PBP from 1990

**Impact:** 🎉 **HUGE WIN!**
- Fills 3-year gap (1990-1992)
- First-ever PBP data from early 1990s
- ~3,750 new games with PBP

**Next step:** Immediately run historical backfill from 1990

### Scenario 2: PBP Between ESPN and hoopR (1993-2002)
**Example:** Basketball Reference has PBP from 1998

**Impact:** ✅ **USEFUL**
- Fills gap in 1990s coverage
- Cross-validates ESPN/NBA API data
- ~5,000-12,500 additional games

**Next step:** Run historical backfill, focus on cross-validation

### Scenario 3: PBP Starts Around 2000-2002
**Example:** Basketball Reference has PBP from 2001

**Impact:** ✅ **STILL VALUABLE**
- Same timeline as other sources
- Excellent for cross-validation
- 4th independent PBP source
- ~30,000 games for validation

**Next step:** Use for data quality checks and validation

### Scenario 4: No PBP Found
**Example:** Basketball Reference has no PBP tables

**Impact:** ⚠️ **UNEXPECTED**
- May need to test more recent years
- May need different game samples
- Box score scraper already extracts PBP where available

**Next step:** Test manually on known recent games (2023-2024)

---

## What Happens After Discovery

### If PBP Found (Most Likely)

1. **Review discovery report** (check JSON file)
2. **Note earliest year** with good coverage (>50% of games)
3. **Create PBP backfill scraper** based on earliest year
4. **Test on 10 sample games** across different years
5. **Launch historical backfill** (runs for days/weeks)
6. **Create daily PBP scraper** for ongoing maintenance

### If Uncertain Results

1. **Run focused discovery** on specific year ranges
2. **Increase games-per-year** for better accuracy
3. **Test manually** on known playoff/finals games
4. **Check Basketball Reference website** for PBP table visibility

---

## Files Created

| File | Purpose | Size |
|------|---------|------|
| `scripts/etl/basketball_reference_pbp_discovery.py` | Discovery script | 14 KB |
| `reports/basketball_reference_pbp_discovery_{timestamp}.json` | Discovery results | ~50 KB |
| `docs/BASKETBALL_REFERENCE_PBP_DISCOVERY.md` | This documentation | - |

---

## Rate Limiting Notes

- **Basketball Reference enforces 12 seconds/request**
- Discovery script respects this automatically
- Testing 350 games = ~70 minutes (350 × 12s / 60)
- If you get 429 errors, wait 10+ minutes before retrying
- Script has early termination to minimize requests

---

## Troubleshooting

### Problem: All games showing "No PBP"
**Likely cause:** Rate limited or testing wrong years
**Solution:**
1. Check if recent games (2023-2024) have PBP manually
2. Wait 10 minutes for rate limits to reset
3. Try with `--start-year 2024 --end-year 2023` first

### Problem: Script taking too long
**Solution:** Use fewer games per year or narrower year range
```bash
python scripts/etl/basketball_reference_pbp_discovery.py \
    --start-year 2024 \
    --end-year 2010 \
    --games-per-year 5
```

### Problem: Can't find game IDs
**Cause:** Random game ID generation may not always match real games
**Impact:** Some tested games return 404 (this is normal, script handles it)
**Note:** We test 10 games per year to account for this

---

## Next Steps

### Immediate (Tonight)
Run the discovery script:
```bash
python scripts/etl/basketball_reference_pbp_discovery.py
```

### After Discovery (~30 min later)
1. Review the JSON report
2. Check the earliest PBP year found
3. Decide on next steps based on findings

### Future Work (Based on Results)
- Create PBP backfill scraper targeting discovered year range
- Create daily PBP scraper for ongoing collection
- Integrate with overnight workflow
- Set up cross-validation with other PBP sources

---

## Questions This Answers

1. **Does Basketball Reference have PBP data?** Yes/No + from which year
2. **Is it earlier than ESPN (1993)?** Critical question for historical gap-filling
3. **How complete is their PBP coverage?** % of games per year with PBP
4. **How many PBP events per game?** Quality/completeness indicator
5. **Should we build a PBP backfill scraper?** Based on coverage findings

---

**Ready to discover Basketball Reference's PBP coverage!** 🔍

Run: `python scripts/etl/basketball_reference_pbp_discovery.py`
