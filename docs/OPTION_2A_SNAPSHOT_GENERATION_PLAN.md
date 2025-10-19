# Option 2A: Phase 9 Snapshot Generation - Implementation Plan

**Date:** October 19, 2025
**Status:** 🔄 IN PROGRESS - Architecture Designed
**Complexity:** HIGH - Requires NLP + Complex State Machine

---

## Executive Summary

To populate plus/minus tables for all 44,826 games, we must **FIRST** generate Phase 9 snapshots (box_score_snapshots) from play-by-play data. This is a **prerequisite step** that was not included in the original Option 2 estimate.

### Current Data Status

```
Available Data:
✅ games table:           44,828 unique games
✅ play_by_play table:    14,798 unique games (6.78M events)
✅ box_score_players:     15,699 unique games (final box scores)

Missing Data (Must Generate):
❌ box_score_snapshots:   Only 1 game (need 14,798)
❌ player_snapshot_stats: Only 1 game (need 14,798)

Target:
🎯 Generate snapshots for 14,798 games
🎯 Then populate plus/minus tables
```

---

## The Challenge: Natural Language Processing

### What We Have (play_by_play table)

```sql
play_text: "Kevin Garnett missed 11 ft jumper."
play_text: "Ervin Johnson defensive rebound."
play_text: "LeBron James makes 25 ft three point jumper (Dwyane Wade assists)."
play_text: "Timeout."
play_text: "Kobe Bryant enters game for Derek Fisher."
```

### What We Need To Extract

From each play_text, we need to:
1. **Identify player(s)** - "Kevin Garnett", "LeBron James", "Dwyane Wade"
2. **Parse action type** - shot made/missed, rebound, assist, substitution, etc.
3. **Extract details** - shot distance (11 ft, 25 ft), shot type (jumper, layup, three pointer)
4. **Update stats** - FGA +1, FGM +1, points +3, assists +1, etc.
5. **Track lineups** - Who's on court after substitutions
6. **Calculate cumulative stats** - Running totals for each player

### Complexity: This is an NLP + State Machine Problem

**Example Play Sequence:**
```
Event 1: "LeBron James makes 25 ft three point jumper (Dwyane Wade assists)."
  → LeBron: FG3M +1, FG3A +1, FGM +1, FGA +1, Points +3
  → Wade: Assists +1
  → Create snapshot with all player cumulative stats

Event 2: "Kevin Garnett defensive rebound."
  → Garnett: DREB +1, REB +1
  → Create snapshot

Event 3: "Timeout."
  → No stat changes
  → Create snapshot (for temporal continuity)

Event 4: "Derek Fisher enters game for Kobe Bryant."
  → Fisher: on_court = TRUE
  → Kobe: on_court = FALSE
  → Update lineup hash
  → Create snapshot
```

---

## Architecture Required

### Components Needed

1. **Play Text Parser** (NLP)
   - Regular expressions for ~50 play patterns
   - Player name extraction
   - Action type classification
   - Stat extraction (points, shot types, etc.)

2. **Game State Machine**
   - Track cumulative stats for all players
   - Track on-court lineups
   - Handle substitutions
   - Calculate plus/minus
   - Track quarter boundaries

3. **Snapshot Generator**
   - Create BoxScoreSnapshot after each event
   - Store to box_score_snapshots table
   - Store player stats to player_snapshot_stats table
   - Maintain referential integrity

4. **Batch Processor**
   - Process 14,798 games
   - Error handling and retry logic
   - Progress tracking
   - Data validation

---

## Revised Time Estimates

### Complexity Breakdown

| Task | Estimated Time | Complexity |
|------|----------------|------------|
| **1. Build Play Text Parser (NLP)** | 3-4 hours | HIGH |
| - Define regex patterns for ~50 play types | 1 hour | MEDIUM |
| - Player name extraction logic | 30 min | LOW |
| - Stat extraction and mapping | 1 hour | MEDIUM |
| - Testing and validation | 1.5 hours | MEDIUM |
| **2. Build Game State Machine** | 2-3 hours | HIGH |
| - Cumulative stat tracking | 1 hour | MEDIUM |
| - Lineup and substitution tracking | 1 hour | MEDIUM |
| - Plus/minus calculation | 30 min | LOW |
| - Testing with sample games | 30 min | LOW |
| **3. Create Snapshot Generator** | 1-2 hours | MEDIUM |
| - BoxScoreSnapshot creation | 30 min | LOW |
| - Database insertion logic | 30 min | LOW |
| - Batch processing framework | 1 hour | MEDIUM |
| **4. Test with 10 Games** | 1 hour | MEDIUM |
| - Run end-to-end pipeline | 30 min | LOW |
| - Validate against actual box scores | 30 min | MEDIUM |
| **5. Scale to 14,798 Games** | 4-6 hours | MEDIUM |
| - Batch processing (458 events/game avg) | 3-4 hours | LOW |
| - Error handling and retry | 1 hour | MEDIUM |
| - Progress monitoring | 30 min | LOW |
| **6. Validation and QA** | 1-2 hours | MEDIUM |
| - Compare generated vs actual box scores | 1 hour | MEDIUM |
| - Data quality checks | 30 min | LOW |
| - Fix any discrepancies | 30 min | VARIABLE |

**Total Estimated Time:** **12-18 hours**

---

## Storage Requirements

### Database Growth

| Table | Current Size | After 14,798 Games | Growth |
|-------|--------------|---------------------|--------|
| box_score_snapshots | 1 row | ~6.78M rows | +6.78M |
| player_snapshot_stats | 2,159 rows | ~135M rows | +135M |
| game_state_snapshots | 200 rows | ~2.96M rows | +2.96M |

**Total Storage Estimate:** 50-100 GB (depending on indexing)

**RDS Impact:**
- Current: db.t3.micro (20 GB storage)
- Needed: db.t3.small or larger (200+ GB storage)
- **Cost Impact:** +$15-30/month for larger instance + storage

---

## Alternative Approaches

### Option A: Simplified Parser (Faster, Less Accurate)

**Time:** 6-8 hours
**Accuracy:** 85-90%

**Approach:**
- Only parse basic play types (shots, rebounds, assists)
- Skip complex plays (technical fouls, challenges, etc.)
- Accept some data loss
- Validate against final box scores

**Pros:**
- Faster implementation
- Still provides snapshots for most events
- Good enough for ML training

**Cons:**
- Missing some events
- Lower temporal resolution
- May have small stat discrepancies

---

### Option B: Use Existing Code (If Available)

**Time:** 2-4 hours
**Accuracy:** Depends on existing code

**Approach:**
- Search for existing ESPN play-by-play parsers in codebase
- Adapt to RDS data format
- Test and validate

**Pros:**
- Much faster
- Likely already tested
- Production-ready

**Cons:**
- May not exist
- May need adaptation
- Unknown accuracy

---

### Option C: Process Subset First (100-1,000 Games)

**Time:** 8-10 hours for full implementation, 1-2 hours for 100 games
**Accuracy:** High (95-98%)

**Approach:**
- Build complete parser
- Test thoroughly on 10 games
- Scale to 100 games
- Validate quality
- Then decide if we scale to 14,798

**Pros:**
- Validates approach before full commit
- Provides sample data for plus/minus testing
- Lower risk

**Cons:**
- Still requires full implementation
- Not complete dataset

---

## Recommended Path Forward

### 🥇 Recommended: Option C (Subset Processing)

**Phase 1: Build & Test (4-6 hours)**
1. Build play text parser (3-4 hours)
2. Build game state machine (1-2 hours)
3. Test on 10 games (1 hour)

**Phase 2: Small Scale Validation (1-2 hours)**
1. Process 100 games (1 hour)
2. Validate data quality (1 hour)
3. Test plus/minus population (30 min)

**Phase 3: Scale Decision**
- If quality is good (>95% accuracy): Scale to all 14,798 games (4-6 hours)
- If quality is poor: Refine parser and retry
- If good enough: Use 100 games for development

**Total Time: 8-12 hours** (split into 3 phases)

---

## Implementation Status

### Current Progress

- [x] ✅ **Architecture designed** - Understand requirements
- [x] ✅ **Data assessment complete** - 14,798 games available
- [ ] ⏸️ **Play text parser** - Not started
- [ ] ⏸️ **Game state machine** - Not started
- [ ] ⏸️ **Snapshot generator** - Not started
- [ ] ⏸️ **Batch processor** - Not started

### Next Steps (Immediate)

**User Decision Required:**
1. **Proceed with Option C (Subset)** - Build parser, test on 10 games, scale to 100
2. **Simplify to Option A** - Basic parser, accept 85-90% accuracy, faster completion
3. **Search for Option B** - Look for existing ESPN parser code
4. **Pivot to different option** - Consider Options 3, 4, or 5 instead

---

## Files That Will Be Created

### Implementation Files

| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `scripts/pbp_to_boxscore/rds_pbp_processor.py` | Main processor | 800-1000 |
| `scripts/pbp_to_boxscore/play_text_parser.py` | NLP parser | 500-700 |
| `scripts/pbp_to_boxscore/game_state_tracker.py` | State machine | 400-600 |
| `scripts/pbp_to_boxscore/batch_snapshot_generator.py` | Batch processor | 300-400 |
| `scripts/pbp_to_boxscore/validate_snapshots.py` | Validation | 200-300 |

**Total Code:** ~2,200-3,000 lines

### Documentation Files

| File | Purpose |
|------|---------|
| `docs/SNAPSHOT_GENERATION_COMPLETE.md` | Completion report |
| `docs/PLAY_TEXT_PARSER_PATTERNS.md` | Parser documentation |
| `docs/SNAPSHOT_VALIDATION_REPORT.md` | Quality metrics |

---

## Risk Assessment

### High Risks

1. **Parsing Accuracy** - NLP may miss edge cases
   - Mitigation: Validate against final box scores

2. **Performance** - 6.78M events may be slow
   - Mitigation: Batch processing, progress tracking

3. **Storage** - 50-100 GB may exceed RDS limits
   - Mitigation: Monitor storage, upgrade instance if needed

### Medium Risks

1. **Data Quality** - Some plays may be unparseable
   - Mitigation: Skip unparseable plays, log warnings

2. **Complexity** - 50+ play types to handle
   - Mitigation: Start with top 10 most common types

### Low Risks

1. **Time Overrun** - May take longer than estimated
   - Mitigation: Phased approach allows stopping early

---

## Conclusion

Option 2A (Generate Phase 9 Snapshots) is **significantly more complex** than the original Option 2 estimate (2-4 hours → 12-18 hours).

**Recommended Next Step:** Get user approval for **Option C (Subset Processing)** which provides:
- ✅ Complete implementation (production-ready)
- ✅ Small scale test (100 games)
- ✅ Option to scale or stop
- ✅ Lower risk, phased approach

**OR** Pivot to Options 3, 4, or 5 which are simpler and provide immediate value.

---

**Author:** Claude Code (claude.ai/code)
**Date:** October 19, 2025
**Version:** 1.0
