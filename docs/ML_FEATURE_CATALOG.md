# ML Feature Catalog - Complete Multi-Source Feature Set

**Created:** October 6, 2025
**Purpose:** Comprehensive catalog of all ML features from all 5 data sources
**Target:** 150-200 features per player/game for SageMaker training
**Status:** Planning document for Phase 1 multi-source integration

---

## Overview

This catalog documents ALL available features across all 5 data sources for maximum ML granularity. Each source contributes unique features that ESPN alone cannot provide.

**Feature Count Summary:**
- ESPN: 58 features ✅ (already have)
- Basketball Reference: 47 features ⏸️ (to implement)
- NBA.com Stats: 92 features ⏸️ (to implement)
- Kaggle: 12 features ⏸️ (historical only)
- **Total: 209 unique features**

**SageMaker Use Cases:**
- Game outcome prediction (win/loss)
- Player performance prediction (points, rebounds, assists)
- Playoff probability forecasting
- Player efficiency modeling
- Defensive impact quantification

---

## Table of Contents

1. [ESPN Features (58)](#espn-features-58)
2. [Basketball Reference Features (47)](#basketball-reference-features-47)
3. [NBA.com Stats Features (92)](#nbacom-stats-features-92)
4. [Kaggle Features (12)](#kaggle-features-12)
5. [Derived Features (20+)](#derived-features-20)
6. [Feature Groups by ML Use Case](#feature-groups-by-ml-use-case)

---

## ESPN Features (58)

**Source:** Already in S3 (70,522 files)
**Coverage:** 1999-present
**Quality:** 89.9% complete

### Game-Level Features (20)

| Feature | Type | ML Value | Example |
|---------|------|----------|---------|
| `game_date` | DATE | MEDIUM | 2024-12-25 |
| `season` | INT | HIGH | 2024 |
| `season_type` | VARCHAR | HIGH | regular, playoffs |
| `home_team_abbr` | VARCHAR | HIGH | LAL |
| `away_team_abbr` | VARCHAR | HIGH | GSW |
| `home_score` | INT | CRITICAL | 115 |
| `away_score` | INT | CRITICAL | 105 |
| `home_q1_score` | INT | MEDIUM | 28 |
| `home_q2_score` | INT | MEDIUM | 30 |
| `home_q3_score` | INT | MEDIUM | 29 |
| `home_q4_score` | INT | MEDIUM | 28 |
| `venue_name` | VARCHAR | LOW | Crypto.com Arena |
| `venue_city` | VARCHAR | MEDIUM | Los Angeles |
| `attendance` | INT | MEDIUM | 18997 |
| `sold_out` | BOOLEAN | LOW | true |
| `broadcast_network` | VARCHAR | MEDIUM | ESPN, TNT, ABC |
| `game_duration` | INTERVAL | MEDIUM | 2:15:00 |
| `referee_1` | VARCHAR | MEDIUM | Official name |
| `overtime` | BOOLEAN | HIGH | false |
| `margin_of_victory` | INT | HIGH | 10 |

### Player Box Score Features (25)

| Feature | Type | ML Value | Example |
|---------|------|----------|---------|
| `minutes` | INT | HIGH | 35 |
| `points` | INT | CRITICAL | 28 |
| `rebounds` | INT | CRITICAL | 10 |
| `offensive_rebounds` | INT | HIGH | 3 |
| `defensive_rebounds` | INT | HIGH | 7 |
| `assists` | INT | CRITICAL | 8 |
| `steals` | INT | HIGH | 2 |
| `blocks` | INT | HIGH | 1 |
| `turnovers` | INT | HIGH | 3 |
| `fouls` | INT | MEDIUM | 2 |
| `field_goals_made` | INT | HIGH | 10 |
| `field_goals_attempted` | INT | HIGH | 20 |
| `field_goal_pct` | DECIMAL | HIGH | 0.500 |
| `three_pointers_made` | INT | HIGH | 3 |
| `three_pointers_attempted` | INT | HIGH | 8 |
| `three_point_pct` | DECIMAL | HIGH | 0.375 |
| `free_throws_made` | INT | HIGH | 5 |
| `free_throws_attempted` | INT | HIGH | 6 |
| `free_throw_pct` | DECIMAL | MEDIUM | 0.833 |
| `plus_minus` | INT | CRITICAL | +12 |
| `starter` | BOOLEAN | MEDIUM | true |
| `position` | VARCHAR | HIGH | SG |
| `jersey_number` | VARCHAR | LOW | 23 |
| `double_double` | BOOLEAN | MEDIUM | true |
| `triple_double` | BOOLEAN | MEDIUM | false |

### Play-by-Play Features (13)

| Feature | Type | ML Value | Example |
|---------|------|----------|---------|
| `shot_x_coord` | INT | HIGH | 145 |
| `shot_y_coord` | INT | HIGH | 220 |
| `shot_distance` | DECIMAL | HIGH | 18.5 |
| `shot_made` | BOOLEAN | CRITICAL | true |
| `shot_type` | VARCHAR | HIGH | jump shot, layup, dunk |
| `shot_value` | INT | HIGH | 2 or 3 |
| `assist_player_id` | INT | HIGH | 2544 |
| `event_type` | VARCHAR | MEDIUM | shot, foul, turnover |
| `period` | INT | MEDIUM | 1-4 or 5+ (OT) |
| `clock` | TIME | MEDIUM | 10:25 |
| `score_margin` | INT | HIGH | +5 |
| `possession_team` | VARCHAR | MEDIUM | LAL |
| `event_description` | TEXT | LOW | LeBron makes 3-pt shot |

---

## Basketball Reference Features (47)

**Source:** Web scraping (TOS compliance required)
**Coverage:** 1946-present (most comprehensive historical)
**Quality:** Highest (gold standard)

### Advanced Shooting Metrics (8)

| Feature | Type | ML Value | Formula | Example |
|---------|------|----------|---------|---------|
| `true_shooting_pct` | DECIMAL | CRITICAL | PTS / (2 * (FGA + 0.44 * FTA)) | 0.612 |
| `effective_fg_pct` | DECIMAL | CRITICAL | (FGM + 0.5 * 3PM) / FGA | 0.565 |
| `three_point_attempt_rate` | DECIMAL | HIGH | 3PA / FGA | 0.400 |
| `free_throw_rate` | DECIMAL | MEDIUM | FTA / FGA | 0.300 |
| `shooting_efficiency` | DECIMAL | HIGH | TS% * 100 | 61.2 |
| `two_point_pct` | DECIMAL | MEDIUM | 2PM / 2PA | 0.520 |
| `at_rim_pct` | DECIMAL | HIGH | FGM at rim / FGA at rim | 0.680 |
| `mid_range_pct` | DECIMAL | MEDIUM | FGM mid / FGA mid | 0.420 |

### Advanced Impact Metrics (10)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `player_efficiency_rating` | DECIMAL | CRITICAL | (PTS + REB + AST + STL + BLK - Missed FG - Missed FT - TO) / MIN | 24.5 |
| `box_plus_minus` | DECIMAL | CRITICAL | Player's contribution per 100 possessions | +6.2 |
| `offensive_bpm` | DECIMAL | HIGH | Offensive contribution per 100 poss | +4.8 |
| `defensive_bpm` | DECIMAL | HIGH | Defensive contribution per 100 poss | +1.4 |
| `value_over_replacement` | DECIMAL | CRITICAL | Total value above replacement level | 4.2 |
| `win_shares` | DECIMAL | CRITICAL | Player's contribution to team wins | 8.5 |
| `win_shares_per_48` | DECIMAL | HIGH | WS normalized per 48 minutes | 0.185 |
| `offensive_win_shares` | DECIMAL | MEDIUM | Win shares from offense | 5.2 |
| `defensive_win_shares` | DECIMAL | MEDIUM | Win shares from defense | 3.3 |
| `game_score` | DECIMAL | MEDIUM | John Hollinger's game score | 18.7 |

### Usage & Percentage Metrics (12)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `usage_rate` | DECIMAL | CRITICAL | % of team plays used while on court | 0.285 |
| `offensive_rebound_pct` | DECIMAL | HIGH | % of available ORB grabbed | 0.085 |
| `defensive_rebound_pct` | DECIMAL | HIGH | % of available DRB grabbed | 0.240 |
| `total_rebound_pct` | DECIMAL | HIGH | % of all rebounds grabbed | 0.162 |
| `assist_pct` | DECIMAL | HIGH | % of teammate FG assisted | 0.325 |
| `steal_pct` | DECIMAL | MEDIUM | Steals per 100 opponent possessions | 2.1 |
| `block_pct` | DECIMAL | MEDIUM | Blocks per 100 opponent 2PA | 3.5 |
| `turnover_pct` | DECIMAL | HIGH | Turnovers per 100 plays used | 0.115 |
| `assist_to_turnover` | DECIMAL | HIGH | AST / TO ratio | 2.8 |
| `steal_to_foul` | DECIMAL | MEDIUM | STL / PF ratio | 1.0 |
| `minutes_pct` | DECIMAL | MEDIUM | % of available minutes played | 0.729 |
| `possessions` | INT | HIGH | Estimated individual possessions | 68 |

### Team Ratings & Pace (7)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `offensive_rating` | DECIMAL | CRITICAL | Points per 100 possessions | 118.5 |
| `defensive_rating` | DECIMAL | CRITICAL | Opp points per 100 possessions | 108.2 |
| `net_rating` | DECIMAL | CRITICAL | ORtg - DRtg | +10.3 |
| `pace` | DECIMAL | HIGH | Possessions per 48 minutes | 98.5 |
| `assist_ratio` | DECIMAL | MEDIUM | AST per 100 possessions | 18.5 |
| `turnover_ratio` | DECIMAL | MEDIUM | TO per 100 possessions | 12.3 |
| `effective_possession_ratio` | DECIMAL | MEDIUM | Good possessions / total poss | 0.685 |

### Four Factors (Team & Individual) (10)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `four_factors_efg` | DECIMAL | HIGH | Team eFG% | 0.545 |
| `four_factors_tov` | DECIMAL | HIGH | Team TOV% | 0.115 |
| `four_factors_orb` | DECIMAL | HIGH | Team ORB% | 0.285 |
| `four_factors_ftr` | DECIMAL | MEDIUM | Team FT/FGA | 0.240 |
| `four_factors_opp_efg` | DECIMAL | HIGH | Opponent eFG% | 0.505 |
| `four_factors_opp_tov` | DECIMAL | HIGH | Opponent TOV% | 0.135 |
| `four_factors_opp_orb` | DECIMAL | HIGH | Opponent ORB% | 0.245 |
| `four_factors_opp_ftr` | DECIMAL | MEDIUM | Opponent FT/FGA | 0.220 |
| `four_factors_margin` | DECIMAL | CRITICAL | Own - Opp (all 4 factors) | +0.040 |
| `pythagorean_wins` | DECIMAL | MEDIUM | Expected wins from efficiency | 52.3 |

---

## NBA.com Stats Features (92)

**Source:** Official NBA Stats API
**Coverage:** 1996-present
**Quality:** Highest (official)

### Player Tracking - Movement (12)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `dist_feet` | DECIMAL | HIGH | Total distance traveled (feet) | 12847.5 |
| `dist_miles` | DECIMAL | HIGH | Total distance (miles) | 2.43 |
| `avg_speed` | DECIMAL | HIGH | Average speed (mph) | 4.25 |
| `avg_speed_off` | DECIMAL | MEDIUM | Speed on offense | 4.8 |
| `avg_speed_def` | DECIMAL | MEDIUM | Speed on defense | 3.7 |
| `distance_off_court` | DECIMAL | LOW | Distance off court (warmups) | 425.0 |
| `distance_on_court` | DECIMAL | HIGH | Distance during play | 12422.5 |
| `sprints` | INT | MEDIUM | Number of sprints (>15 mph) | 18 |
| `sprint_distance` | DECIMAL | MEDIUM | Distance covered sprinting | 876.3 |
| `walk_pct` | DECIMAL | LOW | % time walking | 0.45 |
| `jog_pct` | DECIMAL | LOW | % time jogging | 0.35 |
| `run_pct` | DECIMAL | MEDIUM | % time running | 0.20 |

### Player Tracking - Ball Handling (15)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `touches` | INT | CRITICAL | Total ball touches | 82 |
| `time_of_possession` | DECIMAL | HIGH | Seconds with ball | 245.8 |
| `avg_sec_per_touch` | DECIMAL | MEDIUM | Seconds per touch | 3.0 |
| `avg_dribbles_per_touch` | DECIMAL | HIGH | Dribbles per touch | 2.5 |
| `total_dribbles` | INT | MEDIUM | Total dribbles | 205 |
| `drives` | INT | CRITICAL | Number of drives | 12 |
| `drive_pts` | INT | HIGH | Points from drives | 8 |
| `drive_fg_pct` | DECIMAL | HIGH | FG% on drives | 0.583 |
| `drive_to_pct` | DECIMAL | MEDIUM | TO% on drives | 0.083 |
| `drive_pass_pct` | DECIMAL | MEDIUM | Pass% on drives | 0.417 |
| `elbow_touches` | INT | MEDIUM | Touches at elbow | 15 |
| `post_touches` | INT | MEDIUM | Touches in post | 8 |
| `paint_touches` | INT | HIGH | Touches in paint | 22 |
| `front_ct_touches` | INT | MEDIUM | Touches frontcourt | 78 |
| `passes_made` | INT | MEDIUM | Total passes | 45 |

### Player Tracking - Shot Quality (18)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `contested_shots` | INT | CRITICAL | Shots with defender <4ft | 15 |
| `contested_shot_pct` | DECIMAL | MEDIUM | % of shots contested | 0.682 |
| `uncontested_shots` | INT | HIGH | Shots with defender >4ft | 7 |
| `contested_fg_pct` | DECIMAL | CRITICAL | FG% when contested | 0.467 |
| `uncontested_fg_pct` | DECIMAL | HIGH | FG% when open | 0.714 |
| `contested_2pt_fg_pct` | DECIMAL | HIGH | 2PT FG% contested | 0.520 |
| `contested_3pt_fg_pct` | DECIMAL | HIGH | 3PT FG% contested | 0.350 |
| `uncontested_2pt_fg_pct` | DECIMAL | HIGH | 2PT FG% open | 0.680 |
| `uncontested_3pt_fg_pct` | DECIMAL | HIGH | 3PT FG% open | 0.450 |
| `defender_distance_lt_2ft` | INT | CRITICAL | Shots defender <2ft | 8 |
| `defender_distance_2_4ft` | INT | HIGH | Shots defender 2-4ft | 7 |
| `defender_distance_4_6ft` | INT | MEDIUM | Shots defender 4-6ft | 4 |
| `defender_distance_gt_6ft` | INT | MEDIUM | Shots defender >6ft | 3 |
| `shot_clock_lt_7` | INT | HIGH | Shots with <7 sec clock | 4 |
| `shot_clock_7_15` | INT | MEDIUM | Shots 7-15 sec clock | 8 |
| `shot_clock_15_24` | INT | MEDIUM | Shots >15 sec clock | 10 |
| `dribbles_before_shot_0_1` | INT | MEDIUM | Catch-and-shoot | 6 |
| `dribbles_before_shot_gt_7` | INT | HIGH | ISO shots (7+ dribbles) | 3 |

### Player Tracking - Shot Creation (10)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `pull_up_fg_pct` | DECIMAL | HIGH | FG% on pull-ups | 0.425 |
| `catch_shoot_fg_pct` | DECIMAL | HIGH | FG% catch-and-shoot | 0.485 |
| `pull_up_3pt_pct` | DECIMAL | HIGH | 3PT% on pull-ups | 0.365 |
| `catch_shoot_3pt_pct` | DECIMAL | HIGH | 3PT% catch-and-shoot | 0.420 |
| `shots_off_dribble` | INT | HIGH | Total shots off dribble | 12 |
| `shots_off_catch` | INT | HIGH | Total catch-and-shoot | 10 |
| `touch_time_lt_2` | INT | MEDIUM | Quick shots (<2 sec) | 8 |
| `touch_time_2_6` | INT | MEDIUM | Normal shots (2-6 sec) | 10 |
| `touch_time_gt_6` | INT | LOW | Slow shots (>6 sec) | 4 |
| `self_created_shots` | INT | CRITICAL | Unassisted shots | 14 |

### Hustle Stats (12)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `deflections` | INT | CRITICAL | Deflections caused | 5 |
| `charges_drawn` | INT | HIGH | Charges drawn | 1 |
| `screen_assists` | INT | HIGH | Screen assists | 4 |
| `screen_assist_pts` | INT | HIGH | Points from screen assists | 10 |
| `loose_balls_recovered` | INT | HIGH | Loose balls recovered | 3 |
| `contested_shots_def` | INT | CRITICAL | Shots contested on defense | 18 |
| `contested_2pt_def` | INT | HIGH | 2PT contested on defense | 12 |
| `contested_3pt_def` | INT | HIGH | 3PT contested on defense | 6 |
| `deflections_per_36` | DECIMAL | MEDIUM | Deflections per 36 min | 4.3 |
| `charges_per_36` | DECIMAL | LOW | Charges per 36 min | 0.9 |
| `screens_per_36` | DECIMAL | MEDIUM | Screens per 36 min | 3.4 |
| `hustle_score` | DECIMAL | MEDIUM | Composite hustle metric | 7.8 |

### Defensive Impact (15)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `defensive_fg_pct` | DECIMAL | CRITICAL | Opp FG% when guarded | 0.425 |
| `defensive_3pt_pct` | DECIMAL | HIGH | Opp 3PT% when guarded | 0.320 |
| `defensive_fga` | INT | HIGH | Shots defended | 18 |
| `defensive_fgm` | INT | MEDIUM | Shots made when defended | 8 |
| `matchup_fgm` | INT | HIGH | Direct matchup FGM | 6 |
| `matchup_fga` | INT | HIGH | Direct matchup FGA | 14 |
| `matchup_fg_pct` | DECIMAL | CRITICAL | Direct matchup FG% | 0.429 |
| `matchup_3pm` | INT | HIGH | Direct matchup 3PM | 2 |
| `matchup_3pa` | INT | HIGH | Direct matchup 3PA | 6 |
| `matchup_3pt_pct` | DECIMAL | HIGH | Direct matchup 3PT% | 0.333 |
| `matchup_pts` | INT | CRITICAL | Points allowed (matchup) | 16 |
| `matchup_ast` | INT | MEDIUM | Assists allowed (matchup) | 4 |
| `rim_protection_pct` | DECIMAL | HIGH | FG% at rim defended | 0.520 |
| `perimeter_defense_pct` | DECIMAL | HIGH | 3PT% defended | 0.340 |
| `defensive_rating_on` | DECIMAL | CRITICAL | Team DRtg when on court | 105.2 |

### Miscellaneous & Scoring (10)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `points_off_tov` | INT | HIGH | Points from turnovers | 12 |
| `second_chance_pts` | INT | HIGH | Points from ORB | 8 |
| `fast_break_pts` | INT | HIGH | Fast break points | 10 |
| `paint_pts` | INT | HIGH | Points in paint | 16 |
| `mid_range_pts` | INT | MEDIUM | Mid-range points | 6 |
| `three_pt_pts` | INT | HIGH | 3-point points | 12 |
| `free_throw_pts` | INT | MEDIUM | Free throw points | 8 |
| `pts_created_ast` | INT | HIGH | Points created via assists | 18 |
| `offensive_rating_on` | DECIMAL | CRITICAL | Team ORtg when on court | 115.8 |
| `plus_minus_on_off` | DECIMAL | CRITICAL | Team +/- on vs off court | +8.5 |

---

## Kaggle Features (12)

**Source:** Kaggle Basketball Database (SQLite)
**Coverage:** 1946-2024 (historical only)
**Use Case:** Fill pre-1999 gaps, historical analysis

| Feature | Type | ML Value | Coverage | Example |
|---------|------|----------|----------|---------|
| `game_date_historical` | DATE | MEDIUM | 1946-1998 | 1987-06-09 |
| `season_historical` | INT | MEDIUM | 1946-1998 | 1987 |
| `home_score_historical` | INT | HIGH | 1946-1998 | 105 |
| `away_score_historical` | INT | HIGH | 1946-1998 | 98 |
| `pts_historical` | INT | HIGH | 1946-1998 | 28 |
| `reb_historical` | INT | HIGH | 1946-1998 | 10 |
| `ast_historical` | INT | HIGH | 1946-1998 | 8 |
| `fgm_historical` | INT | MEDIUM | 1946-1998 | 12 |
| `fga_historical` | INT | MEDIUM | 1946-1998 | 24 |
| `ftm_historical` | INT | MEDIUM | 1946-1998 | 4 |
| `fta_historical` | INT | MEDIUM | 1946-1998 | 5 |
| `era_indicator` | VARCHAR | HIGH | All | modern, golden, early |

---

## Derived Features (20+)

**Created during feature engineering from multi-source data**

### Efficiency Metrics (8)

| Feature | Type | ML Value | Formula | Example |
|---------|------|----------|---------|---------|
| `pts_per_touch` | DECIMAL | HIGH | PTS / touches | 0.341 |
| `pts_per_minute` | DECIMAL | HIGH | PTS / MIN | 0.800 |
| `pts_per_shot` | DECIMAL | MEDIUM | PTS / FGA | 1.400 |
| `efficiency_score` | DECIMAL | CRITICAL | PTS * TS% | 17.15 |
| `true_impact` | DECIMAL | HIGH | BPM * MIN / 48 | +4.53 |
| `scoring_burden` | DECIMAL | MEDIUM | PTS / team_pts | 0.243 |
| `usage_efficiency` | DECIMAL | HIGH | TS% / USG% | 2.15 |
| `impact_per_poss` | DECIMAL | CRITICAL | (PTS + AST*2 - TO) / poss | 0.618 |

### Contextual Features (7)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `days_rest` | INT | HIGH | Days since last game | 2 |
| `back_to_back` | BOOLEAN | CRITICAL | Second game in 2 days | false |
| `home_away` | BOOLEAN | CRITICAL | Home game indicator | true |
| `playoff_game` | BOOLEAN | HIGH | Playoff indicator | false |
| `conference_game` | BOOLEAN | MEDIUM | Same conference | true |
| `division_game` | BOOLEAN | MEDIUM | Same division | false |
| `rival_game` | BOOLEAN | MEDIUM | Rivalry matchup | false |

### Momentum Features (5)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `last_5_wins` | INT | HIGH | Wins in last 5 games | 3 |
| `last_10_wins` | INT | HIGH | Wins in last 10 games | 6 |
| `streak` | INT | MEDIUM | Current W/L streak | +3 |
| `pts_avg_last_5` | DECIMAL | MEDIUM | Avg points last 5 games | 112.4 |
| `opponent_strength` | DECIMAL | HIGH | Opponent win % | 0.625 |

### Meta Features (from multi-source) (5)

| Feature | Type | ML Value | Description | Example |
|---------|------|----------|-------------|---------|
| `data_confidence` | DECIMAL | HIGH | Confidence score 0-1 | 0.95 |
| `sources_count` | INT | MEDIUM | # sources with data | 4 |
| `espn_available` | BOOLEAN | MEDIUM | ESPN has data | true |
| `bref_available` | BOOLEAN | HIGH | BRef has advanced stats | true |
| `tracking_available` | BOOLEAN | CRITICAL | Tracking data available | true |

---

## Feature Groups by ML Use Case

### Use Case 1: Game Outcome Prediction (Win/Loss)

**Top 20 Features (by ML value):**
1. `net_rating` (BRef) - CRITICAL
2. `plus_minus` (ESPN) - CRITICAL
3. `offensive_rating_on` (NBA.com) - CRITICAL
4. `defensive_rating_on` (NBA.com) - CRITICAL
5. `last_10_wins` (Derived) - HIGH
6. `opponent_strength` (Derived) - HIGH
7. `home_away` (Derived) - CRITICAL
8. `back_to_back` (Derived) - CRITICAL
9. `offensive_rating` (BRef) - CRITICAL
10. `defensive_rating` (BRef) - CRITICAL
11. `four_factors_margin` (BRef) - CRITICAL
12. `true_shooting_pct` (BRef) - CRITICAL
13. `turnover_pct` (BRef) - HIGH
14. `pace` (BRef) - HIGH
15. `defensive_fg_pct` (NBA.com) - CRITICAL
16. `deflections` (NBA.com) - CRITICAL
17. `contested_fg_pct` (NBA.com) - CRITICAL
18. `playoff_game` (Derived) - HIGH
19. `conference_game` (Derived) - MEDIUM
20. `data_confidence` (Derived) - HIGH

### Use Case 2: Player Performance Prediction (Points)

**Top 20 Features:**
1. `usage_rate` (BRef) - CRITICAL
2. `touches` (NBA.com) - CRITICAL
3. `true_shooting_pct` (BRef) - CRITICAL
4. `drives` (NBA.com) - CRITICAL
5. `pts_per_touch` (Derived) - HIGH
6. `contested_fg_pct` (NBA.com) - CRITICAL
7. `uncontested_fg_pct` (NBA.com) - HIGH
8. `minutes` (ESPN) - HIGH
9. `field_goals_attempted` (ESPN) - HIGH
10. `three_pointers_attempted` (ESPN) - HIGH
11. `free_throws_attempted` (ESPN) - HIGH
12. `shot_clock_lt_7` (NBA.com) - HIGH
13. `pull_up_fg_pct` (NBA.com) - HIGH
14. `catch_shoot_fg_pct` (NBA.com) - HIGH
15. `self_created_shots` (NBA.com) - CRITICAL
16. `paint_touches` (NBA.com) - HIGH
17. `efficiency_score` (Derived) - CRITICAL
18. `scoring_burden` (Derived) - MEDIUM
19. `last_5_pts_avg` (Derived) - MEDIUM
20. `tracking_available` (Derived) - CRITICAL

### Use Case 3: Defensive Impact Modeling

**Top 20 Features:**
1. `defensive_rating` (BRef) - CRITICAL
2. `defensive_bpm` (BRef) - CRITICAL
3. `defensive_fg_pct` (NBA.com) - CRITICAL
4. `contested_shots_def` (NBA.com) - CRITICAL
5. `deflections` (NBA.com) - CRITICAL
6. `charges_drawn` (NBA.com) - HIGH
7. `steals` (ESPN) - HIGH
8. `blocks` (ESPN) - HIGH
9. `matchup_fg_pct` (NBA.com) - CRITICAL
10. `rim_protection_pct` (NBA.com) - HIGH
11. `perimeter_defense_pct` (NBA.com) - HIGH
12. `steal_pct` (BRef) - MEDIUM
13. `block_pct` (BRef) - MEDIUM
14. `defensive_win_shares` (BRef) - MEDIUM
15. `contested_2pt_def` (NBA.com) - HIGH
16. `contested_3pt_def` (NBA.com) - HIGH
17. `defensive_3pt_pct` (NBA.com) - HIGH
18. `matchup_pts` (NBA.com) - CRITICAL
19. `hustle_score` (Derived) - MEDIUM
20. `plus_minus_on_off` (NBA.com) - CRITICAL

### Use Case 4: Playoff Probability Forecasting

**Top 20 Features:**
1. `net_rating` (BRef) - CRITICAL
2. `pythagorean_wins` (BRef) - MEDIUM
3. `last_10_wins` (Derived) - HIGH
4. `opponent_strength` (Derived) - HIGH
5. `four_factors_margin` (BRef) - CRITICAL
6. `plus_minus_on_off` (NBA.com) - CRITICAL
7. `offensive_rating` (BRef) - CRITICAL
8. `defensive_rating` (BRef) - CRITICAL
9. `true_shooting_pct` (BRef) - CRITICAL
10. `turnover_pct` (BRef) - HIGH
11. `conference_game` (Derived) - MEDIUM
12. `division_game` (Derived) - MEDIUM
13. `home_away` (Derived) - CRITICAL
14. `back_to_back` (Derived) - CRITICAL
15. `offensive_bpm` (BRef) - HIGH
16. `defensive_bpm` (BRef) - HIGH
17. `win_shares` (BRef) - CRITICAL
18. `value_over_replacement` (BRef) - CRITICAL
19. `streak` (Derived) - MEDIUM
20. `data_confidence` (Derived) - HIGH

---

## Data Availability Matrix

**Which features are available for which time periods:**

| Time Period | ESPN | BRef | NBA.com | Kaggle | Total Features |
|-------------|------|------|---------|--------|----------------|
| **1946-1979** | ❌ | ✅ | ❌ | ✅ | ~50 (BRef + Kaggle) |
| **1980-1995** | ❌ | ✅ | ❌ | ✅ | ~50 (BRef + Kaggle) |
| **1996-1998** | ❌ | ✅ | ✅ | ✅ | ~120 (BRef + NBA.com + Kaggle) |
| **1999-2015** | ✅ | ✅ | ✅ | ✅ | ~180 (All sources, limited tracking) |
| **2016-present** | ✅ | ✅ | ✅ | ❌ | ~209 (ESPN + BRef + NBA.com full) |

**Key insight:** Maximum feature granularity (209 features) is only available for 2016-present games.

---

## SageMaker Integration

### Feature Vector Format

**CSV format for SageMaker training:**
```csv
player_id,game_id,season,minutes,points,rebounds,...,true_shooting_pct,usage_rate,...,touches,drives,deflections,...,data_confidence,label
2544,401585647,2024,35,28,10,...,0.612,0.285,...,82,12,5,...,0.95,1
```

**Recommended approach:**
1. Export features to S3 as Parquet (columnar, compressed)
2. Use SageMaker Data Wrangler to transform
3. Train with SageMaker XGBoost or custom algorithm
4. Deploy to SageMaker endpoint

### Feature Engineering Pipeline

**Create unified feature vector:**
```python
# scripts/ml/create_feature_vectors.py

def create_ml_features(player_id: int, game_id: str) -> dict:
    """
    Combine all sources into single feature vector
    """
    features = {}

    # ESPN (58 features)
    espn = get_espn_features(player_id, game_id)
    features.update(espn)

    # Basketball Reference (47 features)
    bref = get_bref_features(player_id, game_id)
    features.update(bref)

    # NBA.com Stats (92 features)
    nba = get_nba_features(player_id, game_id)
    features.update(nba)

    # Derived features (20+)
    derived = calculate_derived_features(features)
    features.update(derived)

    # Meta features
    features['data_confidence'] = calculate_confidence(player_id, game_id)
    features['sources_count'] = count_sources(player_id, game_id)

    return features  # 209+ features
```

---

## Missing Data Strategy

**How to handle missing features:**

| Scenario | Strategy | Example |
|----------|----------|---------|
| **Historical gap (pre-1996)** | Use Kaggle/BRef only | NBA.com tracking = NULL |
| **ESPN PBP missing (10%)** | Use NULL, flag with `pbp_available=false` | Shot coords = NULL |
| **BRef unavailable** | Use ESPN + NBA.com | Advanced metrics = NULL |
| **Tracking data missing** | Impute with player/team averages | Deflections = team_avg |
| **All sources missing** | Drop record or impute with season avg | Skip game or use season_avg |

**NULL handling for SageMaker:**
- Option 1: Impute with mean/median
- Option 2: Use -1 as sentinel value
- Option 3: Create `_missing` boolean flag for each feature
- **Recommended:** Option 3 (preserve missing data signal)

---

## Next Steps

1. **Implement Basketball Reference scraper** (Sub-1.0010)
2. **Expand NBA.com Stats scraper** (Sub-1.0007 - add 10 more endpoints)
3. **Create feature engineering pipeline** (Sub-1.0013)
4. **Export to SageMaker-ready format** (Parquet in S3)
5. **Train initial models** (Phase 5 continuation)

---

## Related Documentation

- **[PHASE_1_MULTI_SOURCE_PLAN.md](phases/PHASE_1_MULTI_SOURCE_PLAN.md)** - Implementation roadmap
- **[FIELD_MAPPING_SCHEMA.md](FIELD_MAPPING_SCHEMA.md)** - Field transformations
- **[DATA_DEDUPLICATION_RULES.md](DATA_DEDUPLICATION_RULES.md)** - Keep-all-sources strategy
- **[PHASE_5_MACHINE_LEARNING.md](phases/PHASE_5_MACHINE_LEARNING.md)** - SageMaker setup

---

*Last Updated: October 6, 2025*
*Total Features: 209 (58 ESPN + 47 BRef + 92 NBA.com + 12 Kaggle)*
*For ML Use: Basketball Reference and NBA.com Stats are CRITICAL for advanced metrics*
