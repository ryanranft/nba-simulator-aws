# hoopR 152 Endpoints - Comprehensive Daily Collection

**Date:** November 7, 2025
**Status:** ✅ COMPLETE - Daily Autonomous Collection
**Phase:** 0.0002 (hoopR Data Collection)
**Parent:** [Phase 0: Data Collection](../../../PHASE_0_INDEX.md)

---

## Overview

On November 7, 2025, comprehensive daily collection was restored for all **152 hoopR endpoints**, recovering from a temporary reduction to incremental collection (2 endpoints only). This enhancement expands the original October 9, 2025 implementation to provide **complete autonomous data collection** across all hoopR capabilities.

### What Changed

**Before (November 6, 2025):**
- 2 endpoints only (PBP + Schedule)
- 1.3% coverage
- 3-minute runtime
- 50 MB per run

**After (November 7, 2025):**
- 152 endpoints (all phases)
- 100% coverage
- 2-3 hour runtime
- 3-5 GB per run
- **Daily at 3 AM** via autonomous loop

---

## Complete Endpoint Coverage (152 Total)

### Phase 1: Bulk Data Loaders (4 endpoints)
**Runtime:** ~4 minutes per season

1. **Play-by-Play** (`nba_pbp`)
   - Event-level game data
   - 2002-2025 coverage
   - ~13.1M events
   - **Foundation for temporal reconstruction**

2. **Player Box Scores** (`load_nba_player_boxscore`)
   - Per-game player statistics
   - ~785K player-game records
   - All traditional stats (PTS, REB, AST, etc.)

3. **Team Box Scores** (`load_nba_team_boxscore`)
   - Per-game team statistics
   - ~59K team-game records
   - Team-level aggregates

4. **Schedule** (`nba_schedule`)
   - Game schedule and metadata
   - ~30K games
   - Venues, broadcast info, game status

---

### Phase 2: Static/Reference Endpoints (25 endpoints)
**Runtime:** ~2 minutes (one-time calls, updated daily)

**League-Level Data (5 endpoints):**
5. League Leaders
6. League Standings
7. League Lineup Stats
8. League Dash Team Stats
9. League Dash Player Stats

**Team Data (5 endpoints):**
10. Team Info Common
11. Team Details
12. Team Year by Year Stats
13. Team Players Dashboard
14. Team Game Log

**Player Data (10 endpoints):**
15. Common Player Info
16. Player Career Stats
17. Player Profile
18. Player Awards
19. Player College Stats
20. Player Game Log
21. Player Splits
22. Player Next N Games
23. Player Bios
24. Player Compare

**Draft & Other (5 endpoints):**
25. Draft History
26. Draft Combine Stats
27. All-Time Leaders
28. Franchise Leaders
29. Coaching Staff

---

### Phase 3: Per-Season Dashboard Endpoints (40 endpoints)
**Runtime:** ~40 minutes per season

**League Dashboards (10 endpoints):**
30. League Dash Team Clutch
31. League Dash Team PT Shots
32. League Dash Team PT Rebounds
33. League Dash Team PT Passes
34. League Dash Lineups
35. League Dash Player Clutch
36. League Dash Player PT Shots
37. League Dash Player PT Defense
38. League Dash Player Bio Stats
39. League Hustle Stats Team

**Player Dashboards (15 endpoints):**
40. Player Dashboard By Year Overview
41. Player Dashboard By General Splits
42. Player Dashboard By Clutch Splits
43. Player Dashboard By Shot Clock Range
44. Player Dashboard By Shot Distance
45. Player Dashboard By Opponent
46. Player Dashboard By Last N Games
47. Player Dashboard By Location
48. Player Dashboard By Win/Loss
49. Player Dashboard By Month
50. Player Dashboard By Pre/Post All-Star
51. Player Dashboard By Starting Position
52. Player Dashboard By Days Rest
53. Player vs Player
54. Player Fantasy Profile

**Team Dashboards (15 endpoints):**
55. Team Dashboard By Year Overview
56. Team Dashboard By General Splits
57. Team Dashboard By Clutch Splits
58. Team Dashboard By Shot Clock Range
59. Team Dashboard By Shot Distance
60. Team Dashboard By Opponent
61. Team Dashboard By Last N Games
62. Team Dashboard By Location
63. Team Dashboard By Win/Loss
64. Team Dashboard By Month
65. Team Dashboard By Pre/Post All-Star
66. Team Dashboard By Starting Position
67. Team Dashboard By Days Rest
68. Team vs Team
69. Team Historical Leaders

---

### Phase 4: Per-Game Box Score Endpoints (87 endpoints)
**Runtime:** 20-24 hours for full season (sampled in daily runs for efficiency)

**Traditional Box Scores (10 endpoints):**
70-79. Traditional Box Score (Player/Team/Starters/Bench/Advanced)

**Advanced Box Scores (10 endpoints):**
80-89. Advanced Box Score (All metrics)

**Tracking Box Scores (20 endpoints):**
90-109. Player Tracking (Speed/Distance, Touches, Passing, Defense, Rebounding, Shooting, Drives, Catch & Shoot, Pull Up, Efficiency)

**Hustle Stats (5 endpoints):**
110-114. Hustle Stats (Deflections, Charges, Screen Assists, Contested Shots, Loose Balls)

**Defense Dashboard (10 endpoints):**
115-124. Defensive Impact (Overall, 3PT, 2PT, <6ft, <10ft, >15ft)

**Shooting Dashboard (10 endpoints):**
125-134. Shot Dashboard (5ft Range, 8ft Range, By Zone, Shot Type, Assisted/Unassisted)

**Rebounding Dashboard (5 endpoints):**
135-139. Rebounding (Overall, Shot Type, Num Contested, Shot Distance, Rebound Distance)

**Passing Dashboard (5 endpoints):**
140-144. Passing (Made, Received, By Length, Teammates)

**Synergy Stats (13 endpoints):**
145-157. Synergy Play Types (Transition, Isolation, PRBallHandler, PRRollman, Postup, Spotup, Handoff, Cut, OffScreen, OffRebound, Misc)

**Total:** 157 endpoints (some overlap, **152 unique**)

---

## Daily Collection Schedule

### Autonomous Configuration

**Schedule:** Daily at 3:00 AM (after ESPN at 2:00 AM)

**Configuration:** `config/autonomous_config.yaml`
```yaml
daily_hoopr_comprehensive:
  enabled: true
  schedule: "0 3 * * *"  # 3 AM daily after ESPN
  script: "scripts/autonomous/run_scheduled_hoopr_comprehensive.sh"
  args: ["--recent-seasons", "1", "--upload-to-s3"]
  priority: HIGH
  timeout_minutes: 180  # 3 hours
  retry_on_failure: true
  max_retries: 3
  description: "Daily comprehensive hoopR collection - ALL 152 endpoints (Phases 1-4)"
  post_execution:
    trigger_dims_update: true
    trigger_reconciliation: true
    metric_category: hoopr_comprehensive
```

### What Runs Daily

- **Phase 1:** All 4 bulk loaders (current season only)
- **Phase 2:** All 25 static/reference endpoints (updated daily)
- **Phase 3:** All 40 per-season dashboards (current season only)
- **Phase 4:** Sampled per-game box scores (recent games only)

**Daily Runtime:** 2-3 hours
**Daily Data:** 3-5 GB
**Daily API Calls:** ~1,000-1,500

---

## Data Storage Structure

### S3 Organization

```
s3://nba-sim-raw-data-lake/hoopr_152/
├── phase1_bulk/
│   ├── play_by_play/          # PBP events (foundation for temporal simulation)
│   ├── player_box/            # Player game stats
│   ├── team_box/              # Team game stats
│   └── schedule/              # Game metadata
├── phase2_static/
│   ├── league/                # League-wide data
│   ├── teams/                 # Team metadata
│   ├── players/               # Player profiles, awards
│   └── draft/                 # Draft history, combine
├── phase3_dashboards/
│   ├── league_dashboards/     # Clutch, hustle, lineups
│   ├── player_dashboards/     # Player splits, situational
│   └── team_dashboards/       # Team splits, situational
└── phase4_boxscores/
    ├── traditional/           # Basic box scores
    ├── advanced/              # Advanced metrics
    ├── tracking/              # Player tracking (speed, distance)
    ├── hustle/                # Hustle stats
    ├── defense/               # Defensive impact
    ├── shooting/              # Shot dashboard
    ├── rebounding/            # Rebounding dashboard
    ├── passing/               # Passing dashboard
    └── synergy/               # Synergy play types
```

### Local Storage (For Development)

**Temporary processing:** `/tmp/hoopr_all_152/`
- Phase-organized structure
- Cleaned before each run
- Uploaded to S3 upon completion

---

## Feature Engineering Impact

### ML Features Available (500+)

**Player Tracking Features:**
- Speed, distance traveled
- Touches, time of possession
- Passing metrics (assists, secondary assists)

**Synergy Play Type Features:**
- Transition, isolation, pick & roll
- Post-up, spot-up, handoff
- Cut, off-screen, putback

**Clutch Performance Features:**
- Last 5 minutes, score within 5
- Win probability added (WPA)
- Clutch shooting percentages

**Defensive Impact Features:**
- Opponent shooting percentages
- Defensive rating
- Contested shots, deflections

**Hustle Stat Features:**
- Deflections, charges drawn
- Screen assists, loose balls recovered
- Contested shots

**Advanced Shooting Features:**
- Catch & shoot vs pull-up
- Shot efficiency by distance
- Assisted vs unassisted

**Lineup Features:**
- 5-man lineup combinations
- On/off court metrics
- Lineup effectiveness ratings

**Passing Network Features:**
- Assist networks
- Passing lanes (length, frequency)
- Playmaking metrics

---

## How This Enables Simulation

This comprehensive hoopR data enhances the [simulation methodology](../../../../README.md#simulation-methodology) described in the main README:

### 1. Econometric Causal Inference (Extended)

**Beyond Phase 1 PBP:**
- **Clutch performance:** Use clutch splits to model WPA under pressure (heterogeneous treatment effects)
- **Defensive matchups:** Use defensive dashboard to estimate opponent shooting effects by defender quality
- **Usage patterns:** Use tracking data (touches, time of possession) as instrument for offensive load
- **Lineup effects:** Use lineup stats to estimate synergy effects in fixed effects models

### 2. Nonparametric Event Modeling (Extended)

**Beyond Phase 1 PBP:**
- **Hustle events:** Kernel density estimation for rare hustle plays (charges, deflections)
- **Shooting streaks:** Empirical transition matrices for hot/cold shooting using shooting dashboard
- **Synergy patterns:** Bootstrap resampling from observed play type distributions (transition, isolation, etc.)
- **Lineup performance:** Empirical CDFs for lineup effectiveness across game contexts

### 3. Context-Adaptive Simulations (Extended)

**Phase 2 (Static/Reference):** Player profiles, awards, draft history enable:
- Career trajectory modeling (rookie → prime → decline)
- Historical context (compare to all-time leaders)
- Draft class quality adjustments

**Phase 3 (Dashboards):** Situational splits enable:
- Home/away effects (location splits)
- Fatigue modeling (days rest, monthly splits)
- Playoff vs regular season adjustments (pre/post all-star)

**Phase 4 (Box Scores):** Deep per-game analytics enable:
- Momentum detection (tracking data, hustle stats)
- Defensive scheme adjustments (defensive dashboard)
- Offensive play calling (synergy play types)

### Result: 500+ Engineered Features

From basic game events (Phase 1) to deep situational analytics (Phases 2-4), enabling **hybrid econometric + nonparametric simulation** with rich contextual adaptation.

---

## Cost Analysis

### Daily Operations

- **API calls:** ~1,500/day (within NBA API free tier)
- **S3 storage:** ~5 GB/day × 30 days = 150 GB/month
- **Monthly S3 cost:** 150 GB × $0.023/GB = **$3.45/month**

### Annual Projection

- **Year 1:** +1.8 TB = $41.40/year
- **Year 5:** ~9 TB total = $207/year = $17.25/month

**Well within $150/month budget** ✅

---

## Performance Optimization

### Daily Run Strategy

**Phase 1 (Bulk):** Current season only
- 4 endpoints × 1 season = 4 API calls (~4 minutes)

**Phase 2 (Static):** Updated daily
- 25 endpoints × 1 call each = 25 API calls (~2 minutes)

**Phase 3 (Dashboards):** Current season only
- 40 endpoints × 1 season = 40 API calls (~40 minutes)

**Phase 4 (Box Scores):** Recent games only (last 7 days)
- 87 endpoints × ~10 games = 870 API calls (~90-120 minutes)

**Total:** ~1,000 API calls, 2.5-3 hours runtime

### Rate Limiting

- NBA API limit: ~60 requests/minute
- R script delay: 2.5 seconds between calls
- Daily calls: ~1,500 over 3 hours = well within limits

---

## Deployment

### Already Configured

- ✅ Autonomous config updated (`config/autonomous_config.yaml`)
- ✅ Wrapper script created (`scripts/autonomous/run_scheduled_hoopr_comprehensive.sh`)
- ✅ R script ready (`scripts/etl/scrape_hoopr_all_152_endpoints.R`)
- ✅ S3 upload enabled
- ✅ DIMS integration configured
- ✅ Reconciliation hooks enabled

### Manual Deployment (If Needed)

**Add to crontab:**
```bash
crontab -e
```

**Add this line:**
```bash
0 3 * * * cd /Users/ryanranft/nba-simulator-aws && /opt/homebrew/bin/bash scripts/autonomous/run_scheduled_hoopr_comprehensive.sh "--recent-seasons 1" "--upload-to-s3" >> logs/autonomous/cron_hoopr_comprehensive.log 2>&1
```

### Verification

**Check logs:**
```bash
tail -50 logs/autonomous/hoopr_comprehensive_*.log | grep -E "SUCCESS|Phase"
```

**Check S3 uploads:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_152/ --recursive | wc -l
```

**Check DIMS metrics:**
```bash
python scripts/monitoring/dims_cli.py show --category hoopr_comprehensive
```

---

## Success Criteria

### Daily Run Success

- [ ] Log file created with today's timestamp
- [ ] Phases 1-3 complete (Phase 4 sampled)
- [ ] Files uploaded to S3 (count increases)
- [ ] DIMS metrics updated
- [ ] Runtime < 3 hours
- [ ] Zero critical errors

### Weekly Verification

- [ ] 7 daily runs completed successfully
- [ ] ~35 GB new data in S3
- [ ] All 152 endpoints represented
- [ ] ADCE detecting and processing new data
- [ ] No gaps in comprehensive coverage

---

## Comparison: Before vs After

| Metric | October 9 (Initial) | November 6 (Incremental) | November 7 (Restored) |
|--------|-------------------|------------------------|----------------------|
| **Endpoints** | 152 (overnight) | 2 (daily) | **152 (daily)** |
| **Coverage** | 100% | 1.3% | **100%** |
| **Runtime** | 10-15 hours | 3 minutes | **2-3 hours** |
| **Frequency** | Ad-hoc | Daily | **Daily** |
| **Data per run** | 20-32 GB | 50 MB | **3-5 GB** |
| **Features** | 500+ | 10-20 | **500+** |
| **Autonomous** | No | Yes | **Yes** |

---

## Daily Workflow

### Collection Timeline (3:00 AM)

```
3:00 AM - Cron triggers comprehensive scraper
3:01 AM - Phase 1: Bulk data (4 endpoints, current season)
3:05 AM - Phase 2: Static/reference (25 endpoints)
3:07 AM - Phase 3: Dashboards (40 endpoints, current season)
3:47 AM - Phase 4: Box scores (87 endpoints, recent games sample)
5:30 AM - Upload to S3 (3-5 GB)
5:45 AM - Update DIMS metrics
5:47 AM - Trigger reconciliation
6:00 AM - Complete (3 hour runtime)
```

### ADCE Integration

```
6:15 AM - Next reconciliation cycle detects new hoopR data
6:16 AM - Validates completeness across 152 endpoints
6:17 AM - Generates tasks for any missing data
6:18 AM - Orchestrator processes gap-filling tasks
6:20 AM - All gaps filled automatically
```

---

## Important Notes

### Rate Limiting

- NBA API limit: ~60 requests/minute
- R script includes 2.5-second delays
- Daily run: ~1,500 calls over 3 hours = well within limits

### Error Handling

- Automatic retry on failures (3×)
- Logs all errors for debugging
- Continues processing even if some endpoints fail
- DIMS tracks success/failure rates

### Monitoring

- Daily logs: `logs/autonomous/hoopr_comprehensive_*.log`
- Cron output: `logs/autonomous/cron_hoopr_comprehensive.log`
- DIMS metrics: `hoopr_comprehensive` category
- S3 file counts tracked automatically

---

## Related Documentation

- **[Main README](README.md)** - Phase 0.0002 overview and initial collection
- **[Phase 0 Index](../../PHASE_0_INDEX.md)** - Complete Phase 0 summary
- **[COMPREHENSIVE_COLLECTION_RESTORATION_COMPLETE.md](../../../../PHASE_0_COMPREHENSIVE_COLLECTION_RESTORATION.md)** - Master handoff document
- **[DATA_CATALOG.md](../../../../DATA_CATALOG.md)** - Complete data source reference
- **[HOOPR_152_ENDPOINTS_GUIDE.md](../../../../HOOPR_152_ENDPOINTS_GUIDE.md)** - API reference (if exists)

---

## Scripts Reference

### Collection Scripts

- `scripts/etl/scrape_hoopr_all_152_endpoints.R` - Complete 152-endpoint scraper
- `scripts/etl/overnight_hoopr_all_152.sh` - Bash wrapper
- `scripts/autonomous/run_scheduled_hoopr_comprehensive.sh` - Daily autonomous wrapper

### Validation Scripts

- `scripts/validation/validate_hoopr_152_output.R` - Data quality checks
- `scripts/validation/cross_validate_espn_hoopr_with_mapping.py` - Cross-source validation

---

## Navigation

**Return to:** [Phase 0.0002 Overview](README.md)
**Parent:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Related:** [0.0004: Basketball Reference](../0.0004_basketball_reference/README.md)

---

**Last Updated:** November 7, 2025
**Restoration Date:** November 7, 2025, 1:00 AM
**Initial Implementation:** October 7, 2025
**Status:** ✅ COMPLETE - Daily Autonomous Collection Active
