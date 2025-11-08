# ESPN Feature Coverage Analysis

**Created:** November 5, 2025
**Purpose:** Map ESPN features from S3 to raw_data schema and identify ML readiness
**Status:** Phase 1 Session 1 - Foundation

---

## Executive Summary

**Current State:**
- ✅ **S3 Files:** 172,951 ESPN JSON files (119.32 GB, 100% quality)
- ✅ **Database:** 31,241 games in raw_data schema (migrated from master)
- ⚠️ **Feature Coverage:** Basic subset currently in database (10-15 of 58 features)

**Finding:** Current raw_data JSONB contains minimal migrated data. Full ESPN feature extraction requires parsing S3 JSON files.

**Recommendation:** Extract full ESPN features from S3 → enrich raw_data JSONB → enable ML readiness

---

## Feature Mapping Overview

### Currently in raw_data.nba_games (Migrated from Master)

| Category | Features Available | JSONB Path | Count |
|----------|-------------------|------------|-------|
| **Game Info** | game_id, game_date, season, season_year | `data.game_info.*` | 4 |
| **Team Basic** | home_name, away_name, home_abbr, away_abbr | `data.teams.{home\|away}.{name\|abbreviation}` | 4 |
| **Scores** | home_score, away_score | `data.teams.{home\|away}.score` | 2 |
| **PBP Summary** | total_plays, periods, event_type_counts | `data.play_by_play.*` | 3 |
| **Source** | source, original_game_id | `data.source_data.*` | 2 |

**Total: ~15 features** currently accessible via JSONB helpers

---

## Full ESPN Feature Set (58 Features from ML Catalog)

### Game-Level Features (20)

| Feature | Available in S3? | In Database? | JSONB Path (proposed) | Priority |
|---------|-----------------|--------------|----------------------|----------|
| game_date | ✅ | ✅ | `data.game_info.game_date` | CRITICAL |
| season | ✅ | ✅ | `data.game_info.season` | HIGH |
| season_type | ✅ | ❌ | `data.game_info.season_type` | HIGH |
| home_team_abbr | ✅ | ✅ | `data.teams.home.abbreviation` | HIGH |
| away_team_abbr | ✅ | ✅ | `data.teams.away.abbreviation` | HIGH |
| home_score | ✅ | ✅ | `data.teams.home.score` | CRITICAL |
| away_score | ✅ | ✅ | `data.teams.away.score` | CRITICAL |
| home_q1_score | ✅ | ❌ | `data.scoring.home.quarters[0]` | MEDIUM |
| home_q2_score | ✅ | ❌ | `data.scoring.home.quarters[1]` | MEDIUM |
| home_q3_score | ✅ | ❌ | `data.scoring.home.quarters[2]` | MEDIUM |
| home_q4_score | ✅ | ❌ | `data.scoring.home.quarters[3]` | MEDIUM |
| venue_name | ✅ | ❌ | `data.venue.name` | LOW |
| venue_city | ✅ | ❌ | `data.venue.city` | MEDIUM |
| attendance | ✅ | ❌ | `data.game_info.attendance` | MEDIUM |
| sold_out | ❓ | ❌ | `data.game_info.sold_out` | LOW |
| broadcast_network | ✅ | ❌ | `data.game_info.broadcast` | MEDIUM |
| game_duration | ❓ | ❌ | `data.game_info.duration` | MEDIUM |
| referee_1 | ✅ | ❌ | `data.officials[0].name` | MEDIUM |
| overtime | ✅ | ❌ | `data.game_info.overtime` | HIGH |
| margin_of_victory | ➕ | ❌ | *Derived: abs(home_score - away_score)* | HIGH |

**Coverage: 7/20 in database, 18+/20 available in S3**

### Player Box Score Features (25)

| Feature | Available in S3? | In Database? | JSONB Path (proposed) | Priority |
|---------|-----------------|--------------|----------------------|----------|
| minutes | ✅ | ❌ | `data.box_score.players[*].stats.minutes` | HIGH |
| points | ✅ | ❌ | `data.box_score.players[*].stats.points` | CRITICAL |
| rebounds | ✅ | ❌ | `data.box_score.players[*].stats.rebounds` | CRITICAL |
| offensive_rebounds | ✅ | ❌ | `data.box_score.players[*].stats.offensive_rebounds` | HIGH |
| defensive_rebounds | ✅ | ❌ | `data.box_score.players[*].stats.defensive_rebounds` | HIGH |
| assists | ✅ | ❌ | `data.box_score.players[*].stats.assists` | CRITICAL |
| steals | ✅ | ❌ | `data.box_score.players[*].stats.steals` | HIGH |
| blocks | ✅ | ❌ | `data.box_score.players[*].stats.blocks` | HIGH |
| turnovers | ✅ | ❌ | `data.box_score.players[*].stats.turnovers` | HIGH |
| fouls | ✅ | ❌ | `data.box_score.players[*].stats.fouls` | MEDIUM |
| field_goals_made | ✅ | ❌ | `data.box_score.players[*].stats.field_goals_made` | HIGH |
| field_goals_attempted | ✅ | ❌ | `data.box_score.players[*].stats.field_goals_attempted` | HIGH |
| field_goal_pct | ➕ | ❌ | *Derived: FGM / FGA* | HIGH |
| three_pointers_made | ✅ | ❌ | `data.box_score.players[*].stats.three_pointers_made` | HIGH |
| three_pointers_attempted | ✅ | ❌ | `data.box_score.players[*].stats.three_pointers_attempted` | HIGH |
| three_point_pct | ➕ | ❌ | *Derived: 3PM / 3PA* | HIGH |
| free_throws_made | ✅ | ❌ | `data.box_score.players[*].stats.free_throws_made` | HIGH |
| free_throws_attempted | ✅ | ❌ | `data.box_score.players[*].stats.free_throws_attempted` | HIGH |
| free_throw_pct | ➕ | ❌ | *Derived: FTM / FTA* | MEDIUM |
| plus_minus | ✅ | ❌ | `data.box_score.players[*].stats.plus_minus` | CRITICAL |
| starter | ✅ | ❌ | `data.box_score.players[*].starter` | MEDIUM |
| position | ✅ | ❌ | `data.box_score.players[*].position` | HIGH |
| jersey_number | ✅ | ❌ | `data.box_score.players[*].jersey` | LOW |
| double_double | ➕ | ❌ | *Derived: (PTS≥10 & REB≥10) \|\| (PTS≥10 & AST≥10) \|\| (REB≥10 & AST≥10)* | MEDIUM |
| triple_double | ➕ | ❌ | *Derived: 3+ stats ≥ 10* | MEDIUM |

**Coverage: 0/25 in database, 20+/25 available in S3, 5 can be derived**

### Play-by-Play Features (13)

| Feature | Available in S3? | In Database? | JSONB Path (proposed) | Priority |
|---------|-----------------|--------------|----------------------|----------|
| shot_x_coord | ✅ | ❌ | `data.plays[*].coordinates.x` | HIGH |
| shot_y_coord | ✅ | ❌ | `data.plays[*].coordinates.y` | HIGH |
| shot_distance | ➕ | ❌ | *Derived: sqrt((x-hoop_x)² + (y-hoop_y)²)* | HIGH |
| shot_made | ✅ | ❌ | `data.plays[*].shot_result` | CRITICAL |
| shot_type | ✅ | ❌ | `data.plays[*].shot_type` | HIGH |
| shot_value | ✅ | ❌ | `data.plays[*].shot_value` | HIGH |
| assist_player_id | ✅ | ❌ | `data.plays[*].assist_player_id` | HIGH |
| event_type | ✅ | ⚠️ | `data.play_by_play.summary.event_types` (aggregated only) | MEDIUM |
| period | ✅ | ⚠️ | `data.play_by_play.summary.periods` (max only) | MEDIUM |
| clock | ✅ | ❌ | `data.plays[*].clock` | MEDIUM |
| score_margin | ➕ | ❌ | *Derived: running score differential* | HIGH |
| possession_team | ✅ | ❌ | `data.plays[*].team` | MEDIUM |
| event_description | ✅ | ❌ | `data.plays[*].description` | LOW |

**Coverage: 0/13 in database (summaries only), 10+/13 available in S3, 2 can be derived**

---

## Data Availability Summary

| Source | Total Features | In Database | In S3 (extractable) | Derivable | Needs External API |
|--------|---------------|-------------|-------------------|-----------|-------------------|
| **Game-Level** | 20 | 7 | 18 | 2 | 0 |
| **Player Box** | 25 | 0 | 20 | 5 | 0 |
| **Play-by-Play** | 13 | 0 | 10 | 2 | 1 |
| **TOTAL** | 58 | 7 | 48 | 9 | 1 |

**Key Findings:**
1. ✅ **48/58 features (83%)** are available in S3 ESPN JSON files
2. ➕ **9 additional features** can be derived from available data
3. ❌ **1 feature** may require external API (sold_out flag - if ESPN doesn't provide)
4. **Gap:** Only 7/58 currently in database (12% coverage)

---

## Recommended JSONB Structure Expansion

### Current Structure (Minimal)
```json
{
  "game_info": {
    "game_id": "401468003",
    "game_date": "2023-11-05T19:00:00",
    "season": "2023-24",
    "season_year": 2023
  },
  "teams": {
    "home": {
      "name": "Los Angeles Lakers",
      "abbreviation": "LAL",
      "score": 105
    },
    "away": { ... }
  },
  "source_data": {
    "source": "ESPN",
    "original_game_id": "401468003"
  },
  "play_by_play": {
    "total_plays": 452,
    "summary": {
      "periods": 4,
      "event_types": { ... }
    }
  }
}
```

### Proposed Structure (Full ESPN Features)
```json
{
  "game_info": {
    "game_id": "401468003",
    "game_date": "2023-11-05T19:00:00",
    "season": "2023-24",
    "season_year": 2023,
    "season_type": "regular",                  // NEW
    "attendance": 18997,                        // NEW
    "overtime": false,                          // NEW
    "broadcast": ["ESPN", "TNT"]                // NEW
  },
  "teams": {
    "home": {
      "name": "Los Angeles Lakers",
      "abbreviation": "LAL",
      "score": 105,
      "team_id": "13"                           // NEW
    },
    "away": { ... }
  },
  "scoring": {                                  // NEW SECTION
    "home": {
      "quarters": [28, 30, 29, 18],
      "total": 105
    },
    "away": {
      "quarters": [25, 24, 27, 22],
      "total": 98
    }
  },
  "venue": {                                    // NEW SECTION
    "name": "Crypto.com Arena",
    "city": "Los Angeles",
    "state": "CA"
  },
  "officials": [                                // NEW SECTION
    {"name": "John Doe", "number": "42"},
    {"name": "Jane Smith", "number": "31"}
  ],
  "box_score": {                                // NEW SECTION
    "home": {
      "players": [
        {
          "player_id": "2544",
          "name": "LeBron James",
          "jersey": "23",
          "position": "F",
          "starter": true,
          "stats": {
            "minutes": 35,
            "points": 28,
            "rebounds": 10,
            "offensive_rebounds": 3,
            "defensive_rebounds": 7,
            "assists": 8,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
            "fouls": 2,
            "field_goals_made": 10,
            "field_goals_attempted": 20,
            "three_pointers_made": 3,
            "three_pointers_attempted": 8,
            "free_throws_made": 5,
            "free_throws_attempted": 6,
            "plus_minus": 12
          }
        }
      ],
      "team_stats": {
        "total_rebounds": 45,
        "total_assists": 25,
        "total_turnovers": 12,
        "team_rebounds": 4
      }
    },
    "away": { ... }
  },
  "plays": [                                    // NEW SECTION (detail or summary)
    {
      "play_id": 1,
      "period": 1,
      "clock": "11:42",
      "team": "LAL",
      "player_id": "2544",
      "event_type": "shot",
      "shot_type": "jump shot",
      "shot_value": 2,
      "shot_result": true,
      "coordinates": {"x": 145, "y": 220},
      "assist_player_id": "952",
      "score": {"home": 2, "away": 0},
      "description": "LeBron James makes 18-ft jump shot (D. Russell assists)"
    }
  ],
  "source_data": {
    "source": "ESPN",
    "original_game_id": "401468003",
    "s3_key": "season=2023/league=nba/401468003.json"   // NEW
  }
}
```

---

## ML Readiness Assessment

### What's ML-Ready Now (From Database)
- ✅ **Basic Game Outcomes:** home_score, away_score, game_date
- ✅ **Team Identifiers:** team names, abbreviations
- ✅ **Play Counts:** total_plays (proxy for pace)
- ✅ **Event Summaries:** event_type distributions

**Use Cases:**
- Very basic win/loss prediction (using team ID + score only)
- Pace analysis (plays per game over time)
- Not sufficient for player-level ML

### What's ML-Ready After S3 Extraction
- ✅ **Full Box Scores:** All 25 player stats
- ✅ **Advanced Game Context:** quarter scores, venue, officials
- ✅ **Play-by-Play:** Shot locations, assists, possession data
- ✅ **Derived Features:** Shooting %s, double-doubles, margins

**Use Cases:**
- Player performance prediction (points, rebounds, assists)
- Shot selection optimization (coordinates + success)
- Lineup efficiency analysis (plus/minus)
- Game outcome prediction with context
- Playoff probability forecasting

### What Requires External APIs
- ❌ **Advanced Metrics:** PER, BPM, VORP, Win Shares, Usage Rate
  - Source: Basketball Reference or NBA.com Stats API
  - These require complex formulas and league-wide context

- ❌ **Defensive Stats:** Defensive Rating, opponent FG% at rim
  - Source: NBA.com Stats API (defensive tracking)

- ❌ **Historical Pre-1993:** Games before ESPN coverage
  - Source: Kaggle historical dataset, Basketball Reference

---

## Implementation Roadmap

### Phase 1: Extract ESPN Features from S3
**Goal:** Get all 48 available ESPN features into raw_data.nba_games

**Steps:**
1. ✅ Create S3 file reader utility
2. ❌ Parse ESPN JSON → extract full structure
3. ❌ Update raw_data ETL to enrich JSONB
4. ❌ Backfill 31,241 existing games
5. ❌ Validate feature extraction (validator update)

**Estimated Time:** 8-12 hours
**Deliverable:** 48/58 ESPN features accessible via JSONB helpers

### Phase 2: Add Derived Features
**Goal:** Calculate 9 derivable features

**Features to Derive:**
1. margin_of_victory (abs(home_score - away_score))
2. field_goal_pct (FGM / FGA)
3. three_point_pct (3PM / 3PA)
4. free_throw_pct (FTM / FTA)
5. shot_distance (from coordinates)
6. score_margin (running differential)
7. double_double (boolean from stats)
8. triple_double (boolean from stats)
9. overtime (derived from periods > 4)

**Estimated Time:** 2-3 hours
**Deliverable:** 57/58 features complete

### Phase 3: External API Integration
**Goal:** Get advanced metrics from Basketball Reference / NBA.com

**Out of Scope for ESPN Coverage** - See Phase 1 sub-phases 1.0007, 1.0010

---

## Validation Plan

### Feature Extraction Validator
Create `validators/phases/phase_1/validate_espn_features.py`:

**Checks:**
1. All 48 ESPN features present in 95%+ of games
2. Player box score arrays have reasonable sizes (10-15 players)
3. Play-by-play arrays match total_plays counts
4. Derived features calculate correctly
5. No NULL values in critical features
6. Value ranges reasonable (e.g., scores 50-200, minutes 0-48)

**Sample Validation Query:**
```sql
SELECT
  COUNT(*) as total_games,
  COUNT(*) FILTER (WHERE data->'box_score'->'home'->'players' IS NOT NULL) as has_box_scores,
  AVG(jsonb_array_length(data->'box_score'->'home'->'players')) as avg_players_per_team,
  COUNT(*) FILTER (WHERE data->'scoring'->'home'->'quarters' IS NOT NULL) as has_quarter_scores
FROM raw_data.nba_games
WHERE source = 'ESPN';
```

---

## Next Steps

**Immediate (This Session):**
1. ✅ Document ESPN feature coverage (this file)
2. ❌ Test monitoring scripts for raw_data compatibility
3. ❌ Plan S3 extraction ETL design

**Session 2 (Next):**
1. Build S3 → JSONB extractor
2. Parse ESPN JSON structure
3. Test on sample games
4. Create enrichment validator

**Future Sessions:**
5. Backfill full dataset (31K games)
6. Create ESPN feature extraction helpers
7. Build ML feature preparation utilities
8. Integrate with external APIs (Basketball Ref, NBA.com)

---

**Status:** ✅ Complete - ESPN coverage mapped, gaps identified, roadmap created
**Next:** Test monitoring scripts, then build S3 extractor