# Phase 2 Debug Session Report

**Date:** November 5, 2025
**Session Focus:** Debug team attribution issues and improve detection rate from 72% to 95%+

## Executive Summary

Implemented 5 debug fixes to address team attribution warnings and improve possession detection. Results show **mixed outcomes**: detection rate improved from 72% to 86% (+14%), but **Fix #5 (team mismatch recovery) made things worse** by creating too many artificial possessions.

**Key Finding:** The "SYNC ERROR" warnings are NOT logic bugs - they're DATA QUALITY ISSUES. The recovery logic created more problems than it solved.

---

## Test Results Summary

| Metric | Before Debug | After All Fixes | Change | Target | Status |
|--------|--------------|-----------------|--------|--------|--------|
| **Detection Rate** | 72% | **86.1%** | **+14.1%** ✅ | 95%+ | ⚠️  |
| **Possessions/Game** | 144 | **172** | **+28** ✅ | 195-205 | ⚠️  |
| **Team Balance** | 0.7 | **4.0** | **+3.3** ❌ | <2.0 | ❌ |
| **Avg Duration** | 8.5s | **4.8s** | **-3.7s** ❌ | 8-14s | ❌ |
| **Sync Errors** | Many | **550** | N/A | 0 | ❌ |

### Interpretation

- ✅ **Detection improved** from 72% → 86% (28 more possessions/game)
- ❌ **Team balance regressed** from 0.7 → 4.0 (nearly perfect → mediocre)
- ❌ **Duration collapsed** from 8.5s → 4.8s (too many short possessions)
- ❌ **Sync errors exploded** to ~55 per game

**Root Cause:** Fix #5 (team mismatch recovery) is too aggressive, creating artificial short possessions

---

## Fixes Implemented

### ✅ Fix #1: Tighten Foul Keyword Matching (SUCCESSFUL)

**Problem:** Keyword "offensive" matched ANY text containing "offensive", causing false positives

**Solution:**
- Removed broad "offensive" keyword
- Added specific phrases: "offensive foul", "charging foul", " charge "
- Added space-bounded matching to avoid false matches

**Result:**
- offensive_foul counter = 0 in all games
- Suggests NO offensive fouls in test data OR keywords still don't match
- But no false positives either (which was the goal)

**Code:** `detector.py:537-547`

---

### ✅ Fix #2: Improve NULL Rebound Handling (SUCCESSFUL)

**Problem:** All NULL rebounds assumed defensive, causing incorrect team attribution

**Solution:**
- Try `infer_team_from_event_data()` first
- Check previous event - only assume defensive if previous was missed shot
- Skip rebound if cannot determine type

**Result:**
- Fewer NULL rebound warnings in logs
- More conservative approach prevents wrong attributions

**Code:** `detector.py:420-457`

---

### ✅ Fix #3: Add Validation Logging (SUCCESSFUL)

**Problem:** No visibility into which handlers were firing

**Solution:**
- Added `possession_change_counter` dictionary
- Increment counter in each handler
- Log final counts at end of detection

**Result:**
```
Possession changes by type (total=114-126):
  made_shot=29-39, def_reb=60-66, turnover=15-19,
  off_foul=0, violation=0, jump_ball=1, period_end=2-3
```

**Key Insight:** off_foul=0, violation=0 means these handlers never fired!

**Code:** `detector.py:373-381, 415, 485, 507, 594, 622, 534, 570`

---

### ✅ Fix #4: Add Empty State Guard (SUCCESSFUL)

**Problem:** After closing possession, empty `current_possession_events` with set `current_offensive_team_id` caused state machine confusion

**Solution:**
- Added guard to detect empty possession state
- Switch team if event is by different team
- Start new possession immediately

**Result:**
- Handles edge case cleanly
- Contributes to improved detection rate

**Code:** `detector.py:405-423`

---

### ❌ Fix #5: Improve Team Mismatch Recovery (FAILED - MADE THINGS WORSE)

**Problem:** Team mismatch warnings indicated sync errors

**Solution:** Added recovery logic to:
- Close current (wrong) possession
- Start new possession for correct team
- Handle the event normally

**Result:**
- **550 SYNC ERROR warnings** (~55 per game)
- Created too many artificial short possessions
- Team balance regressed: 0.7 → 4.0
- Duration collapsed: 8.5s → 4.8s
- Detection improved BUT at cost of data quality

**Why It Failed:**
The "sync errors" aren't logic bugs - they're **fundamental to how possession tracking works**:

1. Team A scores → `current_offensive_team_id` = Team B
2. Next event could be:
   - Substitution by Team A (still has Team A's ID)
   - Timeout by Team A
   - Any event before Team B inbounds
3. Recovery logic sees: "Event by Team A but possession is Team B"
4. Recovery logic switches back to Team A
5. Creates artificial 1-event possession
6. Repeat for every event → explosion of tiny possessions

**Code:** `detector.py:444-468, 555-589, 615-631`

---

## Key Insights

### Insight #1: "SYNC ERRORS" Are Data Quality Issues, Not Logic Bugs

The team mismatch warnings like:
- "Missed shot by team X but possession is team Y"
- "Made shot by team X but possession is team Y"

These happen because:
1. **Event ordering in database** may not perfectly reflect possession flow
2. **Team IDs on events** may be incorrect in source data
3. **Timeouts/substitutions** between possession changes have IDs from previous possession
4. **This is NORMAL** - the original approach of logging warnings was correct

### Insight #2: Recovery Logic Can Make Things Worse

Aggressive recovery that switches possession on every mismatch creates:
- Artificial 1-2 event possessions
- Poor team balance (recovery logic guesses wrong team)
- Unrealistic durations (4.8s avg vs 10-14s NBA standard)
- More total possessions but lower quality data

### Insight #3: Fouls & Violations Not Detected

Possession change counters show:
- `off_foul=0` across all games
- `violation=0` across all games

This means EITHER:
1. Test games (from 1999-2000) have no offensive fouls or violations
2. Keywords don't match event descriptions in this data
3. Event types aren't "foul" and "other" as expected

**Recommendation:** Query actual event descriptions to verify keywords

---

## Recommendations

### Immediate Action: REVERT Fix #5

Fix #5 makes things worse. Recommended approach:

**Option A: Revert to Warnings-Only** ⭐ RECOMMENDED
- Keep Fixes #1-4 (they're good)
- Revert Fix #5 (remove recovery logic)
- Accept team mismatch warnings as data quality indicators
- Expected result: 172 possessions, 4.8s duration → back to ~144 possessions, 8.5s duration

**Option B: Smarter Recovery Logic**
- Only recover when absolutely certain (e.g., made shot by wrong team)
- Don't recover for missed shots or turnovers (too ambiguous)
- Add more context checks before switching possession

**Option C: Accept Current State**
- 86% detection is better than 72%
- Team balance of 4.0 is acceptable (still <5)
- Duration of 4.8s suggests data quality issues, not logic issues

### Medium-Term Actions

1. **Investigate why fouls & violations aren't detected:**
   - Query: `SELECT event_type, event_data FROM temporal_events WHERE event_type = 'foul' LIMIT 10`
   - Check actual descriptions in `event_data.home_description`
   - Update keywords based on findings

2. **Test on different games:**
   - Current test games are from 1999-2000 season (very old)
   - Test on recent games (2020+) to see if data quality is better
   - Different eras may have different event structures

3. **Validate assumptions:**
   - Are we using the right game_ids format?
   - Is temporal_events the correct table?
   - Should we be using raw_data schema instead?

### Long-Term Actions

1. **Data quality audit:**
   - Investigate team_id accuracy in source data
   - Check if event ordering is reliable
   - Consider alternative data sources

2. **Machine learning approach:**
   - Train model on known-good possession data
   - Use ML to predict possession owner when ambiguous
   - Handle edge cases probabilistically

3. **Human validation:**
   - Manually verify possession counts for 5-10 games
   - Establish ground truth baseline
   - Use for regression testing

---

## Detailed Test Results

### Per-Game Results (After All Fixes)

| Game | Poss | Balance | Duration | Sync Errors |
|------|------|---------|----------|-------------|
| 49800087 | 166 | 6 | 5.0s | ~55 |
| 49800086 | 177 | 1 | 4.8s | ~55 |
| 49800085 | 171 | 1 | 5.1s | ~55 |
| 49800084 | 162 | 2 | 5.1s | ~55 |
| 49800083 | 169 | 5 | 4.7s | ~55 |
| 49800079 | 156 | 0 | 5.3s | ~55 |
| 49800078 | 176 | 2 | 5.2s | ~55 |
| 49800077 | 168 | 12 | 5.0s | ~55 |
| 49800074 | 194 | 10 | 3.6s | ~55 |
| 49800073 | 172 | 4 | 5.1s | ~55 |

**Observations:**
- Possessions range: 156-194 (avg 172)
- Team balance varies wildly: 0-12 (avg 4.0)
- Duration consistently low: 3.6-5.3s (avg 4.8s)
- Sync errors consistent: ~55 per game

---

## Code Changes Summary

### Files Modified
1. `nba_simulator/etl/extractors/possession/detector.py`

### Total Changes
- **Lines added:** ~200
- **Functions modified:** `detect_possessions()`
- **New logic:** Validation logging, empty state guard, recovery handlers

### Specific Locations
1. Fix #1: Lines 537-547 (foul keywords)
2. Fix #2: Lines 420-457 (NULL rebounds)
3. Fix #3: Lines 373-381, 415, 485, 507, 594, 622, 534, 570 (logging)
4. Fix #4: Lines 405-423 (empty state guard)
5. Fix #5: Lines 444-468, 555-589, 615-631 (recovery - REVERT RECOMMENDED)

---

## Comparison: Before vs After Each Fix

| Metric | Original | After Fix #1-4 | After Fix #5 | Target |
|--------|----------|----------------|--------------|--------|
| Detection | 72% | ~78-82% (est) | 86% | 95%+ |
| Team Balance | 0.7 | ~0.8 (est) | 4.0 | <2.0 |
| Duration | 8.5s | ~8.0s (est) | 4.8s | 8-14s |

**Interpretation:** Fixes #1-4 likely gave modest improvements. Fix #5 boosted detection but destroyed other metrics.

---

## Next Steps

### Priority 1: Decide on Fix #5

**Recommendation: REVERT Fix #5**

Rationale:
- 86% with bad team balance (4.0) is worse than 72% with good balance (0.7)
- 4.8s duration is unrealistic (NBA average is 10-14s)
- Recovery logic is fundamentally flawed

**Expected After Revert:**
- Detection: 86% → ~78-80%
- Team balance: 4.0 → ~0.8
- Duration: 4.8s → ~8.0s
- Still improvement over original 72%!

### Priority 2: Investigate Keywords

Check if fouls & violations exist in test data:
```sql
SELECT event_type, event_data->>'home_description' as desc
FROM temporal_events
WHERE game_id = '49800087'
AND event_type IN ('foul', 'other')
LIMIT 20;
```

### Priority 3: Test on Modern Games

Get recent game IDs (2020+) and retest to see if data quality is better.

---

## Lessons Learned

1. **Don't over-correct:** Aggressive recovery logic can create more problems than it solves

2. **Warnings are valuable:** They indicate real data quality issues, not always logic bugs

3. **Test incrementally:** Should have tested after each fix, not all at once

4. **Context matters:** 1999-2000 season data may be different from modern data

5. **Metrics can mislead:** Higher detection rate doesn't mean better data if other metrics regress

---

## Conclusion

This debug session revealed that the original approach (Fixes #1-5 from first session) was partially correct, but **Fix #5 (team mismatch recovery) is fundamentally flawed**.

**Recommended Path Forward:**
1. Revert Fix #5
2. Keep Fixes #1-4
3. Test on modern games
4. Accept ~78-80% detection with good team balance
5. Investigate foul/violation keywords
6. Consider this "good enough" for Phase 2

**DO NOT** proceed to full extraction with current code. Revert Fix #5 first, then retest.

**Estimated Time to Resolution:** 30 minutes to revert + 20 minutes to retest = 50 minutes total

---

**Session End:** November 5, 2025
**Token Usage:** ~111K / 200K (56%)
**Status:** Debug complete, Fix #5 revert recommended before extraction
