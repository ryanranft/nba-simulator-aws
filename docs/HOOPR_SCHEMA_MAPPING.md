# hoopR CSV to PostgreSQL Schema Mapping

**Created:** October 8, 2025
**Purpose:** Document column mapping between hoopR CSV files and PostgreSQL tables

---

## Schema Mismatch Analysis

### Problem
The PostgreSQL table schemas are oversimplified and missing many columns present in the hoopR CSV files. This causes INSERT failures with "column does not exist" errors.

### Solution Options
1. ✅ **Expand PostgreSQL tables to match CSV schema** (RECOMMENDED)
2. ❌ Select only matching columns from CSV (loses 80%+ of data)

---

## 1. Play-by-Play Schema

### Current PostgreSQL Table (`hoopr_play_by_play`)
```sql
id, game_id, season, game_date, event_num, period, clock, team_id, player_id,
event_type, description, score_home, score_away, created_at
```
**Columns:** 14

### Actual CSV Schema (`pbp_2020.csv`)
```
game_play_number, id, sequence_number, type_id, type_text, text, away_score, home_score,
period_number, period_display_value, clock_display_value, scoring_play, score_value, team_id,
athlete_id_1, athlete_id_2, athlete_id_3, wallclock, shooting_play, coordinate_x_raw,
coordinate_y_raw, game_id, season, season_type, home_team_id, home_team_name, home_team_mascot,
home_team_abbrev, home_team_name_alt, away_team_id, away_team_name, away_team_mascot,
away_team_abbrev, away_team_name_alt, game_spread, home_favorite, game_spread_available,
home_team_spread, qtr, time, clock_minutes, clock_seconds, home_timeout_called, away_timeout_called,
half, game_half, lead_qtr, lead_half, start_quarter_seconds_remaining, start_half_seconds_remaining,
start_game_seconds_remaining, end_quarter_seconds_remaining, end_half_seconds_remaining,
end_game_seconds_remaining, period, lag_qtr, lag_half, coordinate_x, coordinate_y, game_date,
game_date_time, type_abbreviation
```
**Columns:** 63

### Recommended Mapping

**Keep columns (critical for analysis):**
- `id` → `event_id` (PRIMARY KEY)
- `game_id` → `game_id`
- `season` → `season`
- `season_type` → `season_type` (NEW - playoffs vs regular season)
- `game_date` → `game_date`
- `game_date_time` → `game_datetime` (NEW - timestamp)
- `sequence_number` → `sequence_number` (NEW - event order)
- `game_play_number` → `game_play_number` (NEW - play counter)
- `period` → `period`
- `period_number` → `period_number` (NEW)
- `clock_display_value` → `clock`
- `clock_minutes` → `clock_minutes` (NEW)
- `clock_seconds` → `clock_seconds` (NEW)
- `type_id` → `type_id` (NEW)
- `type_text` → `type_text`
- `type_abbreviation` → `type_abbreviation` (NEW)
- `text` → `description`
- `team_id` → `team_id`
- `athlete_id_1` → `athlete_id_1` (NEW - primary player)
- `athlete_id_2` → `athlete_id_2` (NEW - secondary player)
- `athlete_id_3` → `athlete_id_3` (NEW - third player)
- `home_score` → `home_score`
- `away_score` → `away_score`
- `scoring_play` → `scoring_play` (NEW - boolean)
- `score_value` → `score_value` (NEW - points scored)
- `shooting_play` → `shooting_play` (NEW - boolean)
- `coordinate_x` → `coordinate_x` (NEW - shot location)
- `coordinate_y` → `coordinate_y` (NEW - shot location)
- `wallclock` → `wallclock` (NEW - real-world timestamp)
- `home_team_id` → `home_team_id` (NEW)
- `home_team_name` → `home_team_name` (NEW)
- `home_team_abbrev` → `home_team_abbrev` (NEW)
- `away_team_id` → `away_team_id` (NEW)
- `away_team_name` → `away_team_name` (NEW)
- `away_team_abbrev` → `away_team_abbrev` (NEW)

**Total recommended columns:** 36 (vs current 14)

---

## 2. Player Box Schema

### Current PostgreSQL Table (`hoopr_player_box`)
```sql
id, game_id, season, season_type, game_date, team_id, player_id, player_name,
minutes, fgm, fga, fg_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct, oreb, dreb,
reb, ast, stl, blk, tov, pf, pts, plus_minus, starter, created_at
```
**Columns:** 30

### Actual CSV Schema (`player_box_2020.csv`)
```
game_id, season, season_type, game_date, game_date_time, athlete_id, athlete_display_name,
team_id, team_name, team_location, team_short_display_name, minutes, field_goals_made,
field_goals_attempted, three_point_field_goals_made, three_point_field_goals_attempted,
free_throws_made, free_throws_attempted, offensive_rebounds, defensive_rebounds, rebounds,
assists, steals, blocks, turnovers, fouls, plus_minus, points, starter, ejected, did_not_play,
reason, active, athlete_jersey, athlete_short_name, athlete_headshot_href, athlete_position_name,
athlete_position_abbreviation, team_display_name, team_uid, team_slug, team_logo,
team_abbreviation, team_color, team_alternate_color, home_away, team_winner, team_score,
opponent_team_id, opponent_team_name, opponent_team_location, opponent_team_display_name,
opponent_team_abbreviation, opponent_team_logo, opponent_team_color, opponent_team_alternate_color,
opponent_team_score
```
**Columns:** 57

### Schema Mismatch
**Current table HAS `season_type` column** (line 81 in loader script)
**BUT:** Column mapping function doesn't handle it properly!

**Missing columns causing errors:**
- CSV has `season_type` but loader tries to select it without mapping
- CSV has `game_date_time` but table only has `game_date`

**Fix:** Add proper column selection that matches existing table schema.

---

## 3. Team Box Schema

### Current PostgreSQL Table (`hoopr_team_box`)
```sql
id, game_id, season, game_date, team_id, team_name, fgm, fga, fg_pct, fg3m, fg3a,
fg3_pct, ftm, fta, ft_pct, oreb, dreb, reb, ast, stl, blk, tov, pf, pts, created_at
```
**Columns:** 25

### Actual CSV Schema (`team_box_2020.csv`)
```
game_id, season, season_type, game_date, game_date_time, team_id, team_uid, team_slug,
team_location, team_name, team_abbreviation, team_display_name, team_short_display_name,
team_color, team_alternate_color, team_logo, team_home_away, team_score, team_winner,
assists, blocks, defensive_rebounds, fast_break_points, field_goal_pct, field_goals_made,
field_goals_attempted, flagrant_fouls, fouls, free_throw_pct, free_throws_made,
free_throws_attempted, largest_lead, offensive_rebounds, points_in_paint, steals,
team_turnovers, technical_fouls, three_point_field_goal_pct, three_point_field_goals_made,
three_point_field_goals_attempted, total_rebounds, total_technical_fouls, total_turnovers,
turnover_points, turnovers, opponent_team_id, opponent_team_uid, opponent_team_slug,
opponent_team_location, opponent_team_name, opponent_team_abbreviation, opponent_team_display_name,
opponent_team_short_display_name, opponent_team_color, opponent_team_alternate_color,
opponent_team_logo, opponent_team_score
```
**Columns:** 58

**Missing:** `season_type`, advanced stats (fast break points, points in paint, etc.)

---

## 4. Schedule Schema

### Current PostgreSQL Table (`hoopr_schedule`)
```sql
id, game_id, season, game_date, home_team_id, away_team_id, home_team_name,
away_team_name, home_score, away_score, game_status, created_at
```
**Columns:** 12

### Actual CSV Schema (`schedule_2020.csv`)
```
id, uid, date, attendance, time_valid, neutral_site, conference_competition,
play_by_play_available, recent, start_date, broadcast, highlights, notes_type,
notes_headline, broadcast_market, broadcast_name, type_id, type_abbreviation, venue_id,
venue_full_name, venue_address_city, venue_address_state, venue_indoor, status_clock,
status_display_clock, status_period, status_type_id, status_type_name, status_type_state,
status_type_completed, status_type_description, status_type_detail, status_type_short_detail,
format_regulation_periods, home_id, home_uid, home_location, home_name, home_abbreviation,
home_display_name, home_short_display_name, home_color, home_alternate_color, home_is_active,
home_venue_id, home_logo, home_score, home_winner, home_linescores, home_records, away_id,
away_uid, away_location, away_name, away_abbreviation, away_display_name,
away_short_display_name, away_is_active, away_score, away_winner, away_linescores, away_records,
game_id, season, season_type, status_type_alt_detail, away_color, away_alternate_color,
away_venue_id, away_logo, game_json, game_json_url, game_date_time, game_date, PBP, team_box,
player_box
```
**Columns:** 77

**Missing:** `uid`, `season_type`, venue info, broadcast info, status details

---

## Recommended Action Plan

### Option 1: Minimal Fix (FAST - 30 minutes)
**Just fix the column selection to match existing tables**
- Update loader to only select columns that exist in current schema
- Skip columns that don't exist in PostgreSQL
- Trade-off: Lose 60-70% of available data

### Option 2: Full Schema Update (BETTER - 2 hours)
**Expand PostgreSQL tables to capture all important columns**
- Update all 4 table CREATE statements
- Add missing columns (especially `season_type`, coordinates, advanced stats)
- Update loader to map all columns
- Trade-off: More storage, but complete data

### Option 3: Hybrid (RECOMMENDED - 1 hour)
**Expand tables with most valuable columns only**
- Add critical missing columns (season_type, coordinates, team names)
- Skip less important columns (team colors, logos, broadcast info)
- Capture ~80% of data value with ~40% of columns

---

## Immediate Fix Strategy

**For this session, use Option 1 (Minimal Fix):**

1. Update `load_csv_to_table()` function to handle all 4 table types
2. Add column filtering that only keeps columns existing in PostgreSQL
3. Re-run load with corrected column selection

**Result:** Should load successfully with current schema (lose extra data but get core stats)

**Next session:** Implement Option 3 (Hybrid expansion) to capture coordinates, season_type, etc.

---

**Status:** Analysis complete, ready to fix loader script
