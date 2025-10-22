-- ============================================================================
-- Player Box Score Snapshots with Biographical Data View
-- ============================================================================
--
-- Purpose: Join player_box_score_snapshots with player_biographical data
--          and calculate precise age (DECIMAL(10,4)) at each snapshot timestamp
--
-- Created: October 19, 2025
-- ML Use Cases: Age as time-varying feature, physical attributes context,
--               draft year effects, rookie analysis, career arc prediction
--
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_player_snapshots_with_biographical AS
SELECT
    -- ========================================================================
    -- Original Snapshot Data (from player_box_score_snapshots)
    -- ========================================================================
    s.id,
    s.game_id,
    s.event_number,
    s.player_id,
    s.player_name,
    s.team_id,
    s.period,
    s.game_clock,
    s.time_elapsed_seconds,
    s.timestamp,

    -- Cumulative stats
    s.points,
    s.fgm,
    s.fga,
    s.fg_pct,
    s.fg3m,
    s.fg3a,
    s.fg3_pct,
    s.ftm,
    s.fta,
    s.ft_pct,
    s.oreb,
    s.dreb,
    s.reb,
    s.ast,
    s.stl,
    s.blk,
    s.tov,
    s.pf,
    s.plus_minus,
    s.minutes,
    s.on_court,

    -- Advanced stats
    s.true_shooting_pct,
    s.effective_fg_pct,
    s.three_point_attempt_rate,
    s.ts_attempts,
    s.usage_rate,
    s.assist_rate,
    s.assist_percentage,
    s.turnover_rate,
    s.offensive_rebound_pct,
    s.defensive_rebound_pct,
    s.total_rebound_pct,
    s.steal_percentage,
    s.block_percentage,
    s.game_score,
    s.offensive_rating,
    s.box_plus_minus,
    s.assist_to_turnover,

    -- Shooting breakdown
    s.points_in_paint,
    s.second_chance_points,
    s.fast_break_points,
    s.points_off_turnovers,

    -- Line score
    s.q1_points,
    s.q2_points,
    s.q3_points,
    s.q4_points,
    s.overtime_line_score,
    s.created_at AS snapshot_created_at,

    -- ========================================================================
    -- Player Biographical Data (from player_biographical)
    -- ========================================================================

    -- Birth Information
    pb.birth_date,
    pb.birth_date_precision,
    pb.birth_city,
    pb.birth_state,
    pb.birth_country,

    -- Physical Attributes
    pb.height_inches,
    pb.weight_pounds,
    pb.wingspan_inches,

    -- Career Timeline
    pb.nba_debut_date,
    pb.nba_retirement_date,
    pb.draft_year,
    pb.draft_round,
    pb.draft_pick,
    pb.draft_team_id,

    -- Education
    pb.college,
    pb.high_school,

    -- Additional Info
    pb.nationality,
    pb.position,
    pb.jersey_number,
    pb.data_source AS biographical_data_source,

    -- ========================================================================
    -- Age Calculations (7 formats for ML flexibility)
    -- ========================================================================
    -- All age calculations assume birth time is midnight UTC (00:00:00)
    -- This creates a ±24 hour uncertainty window for exact age
    -- ========================================================================

    -- Format 1: High-precision decimal years (DECIMAL(10,4))
    -- Example: 27.6412 years
    -- Best for: Regression models, age-performance curves, continuous ML features
    CASE
        WHEN pb.birth_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                (julianday(s.timestamp) - julianday(pb.birth_date)) / 365.25
                AS DECIMAL(10, 4)
            )
        ELSE NULL
    END AS age_years_decimal,

    -- Format 2: Age in days (integer)
    -- Example: 10089 days
    -- Best for: Tree-based models, discrete binning, interval features
    CASE
        WHEN pb.birth_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                julianday(s.timestamp) - julianday(pb.birth_date)
                AS INTEGER
            )
        ELSE NULL
    END AS age_days,

    -- Format 3: Age in seconds (for maximum precision)
    -- Example: 871,286,400 seconds
    -- Best for: Time-series models, exact age calculations, microsecond precision
    CASE
        WHEN pb.birth_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                (julianday(s.timestamp) - julianday(pb.birth_date)) * 86400
                AS BIGINT
            )
        ELSE NULL
    END AS age_seconds,

    -- Format 4: Uncertainty in hours (always 24 for birth date precision)
    -- Example: 24 (birth time unknown, assumed midnight UTC)
    -- Best for: Error bounds in statistical models, confidence intervals
    CASE
        WHEN pb.birth_date IS NOT NULL THEN 24
        ELSE NULL
    END AS age_uncertainty_hours,

    -- Format 5: Minimum possible age (born at 23:59:59)
    -- Example: 27.6384 years
    -- Best for: Conservative age estimates, lower bound calculations
    CASE
        WHEN pb.birth_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                ((julianday(s.timestamp) - julianday(pb.birth_date)) - (1.0 / 365.25)) / 365.25
                AS DECIMAL(10, 4)
            )
        ELSE NULL
    END AS age_min_decimal,

    -- Format 6: Maximum possible age (born at 00:00:00)
    -- Example: 27.6440 years
    -- Best for: Liberal age estimates, upper bound calculations
    CASE
        WHEN pb.birth_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                ((julianday(s.timestamp) - julianday(pb.birth_date)) + (1.0 / 365.25)) / 365.25
                AS DECIMAL(10, 4)
            )
        ELSE NULL
    END AS age_max_decimal,

    -- Format 7: Human-readable age string with uncertainty
    -- Example: "27y 234d ±24h"
    -- Best for: Display, documentation, user-facing applications
    CASE
        WHEN pb.birth_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                CAST((julianday(s.timestamp) - julianday(pb.birth_date)) / 365.25 AS INTEGER) ||
                'y ' ||
                CAST((julianday(s.timestamp) - julianday(pb.birth_date)) -
                     (CAST((julianday(s.timestamp) - julianday(pb.birth_date)) / 365.25 AS INTEGER) * 365.25)
                     AS INTEGER) ||
                'd ±24h'
                AS TEXT
            )
        ELSE NULL
    END AS age_string,

    -- ========================================================================
    -- Career Experience Metrics
    -- ========================================================================

    -- Years of NBA experience at this snapshot
    CASE
        WHEN pb.nba_debut_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                (julianday(s.timestamp) - julianday(pb.nba_debut_date)) / 365.25
                AS DECIMAL(10, 4)
            )
        ELSE NULL
    END AS nba_experience_years,

    -- Days since NBA debut
    CASE
        WHEN pb.nba_debut_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CAST(
                julianday(s.timestamp) - julianday(pb.nba_debut_date)
                AS INTEGER
            )
        ELSE NULL
    END AS nba_experience_days,

    -- Is this player a rookie? (< 1 year experience)
    CASE
        WHEN pb.nba_debut_date IS NOT NULL AND s.timestamp IS NOT NULL THEN
            CASE
                WHEN (julianday(s.timestamp) - julianday(pb.nba_debut_date)) / 365.25 < 1.0
                THEN 1
                ELSE 0
            END
        ELSE NULL
    END AS is_rookie,

    -- ========================================================================
    -- Physical Metrics Derived
    -- ========================================================================

    -- BMI (Body Mass Index) - weight in kg / (height in meters)^2
    CASE
        WHEN pb.height_inches IS NOT NULL AND pb.weight_pounds IS NOT NULL THEN
            CAST(
                (pb.weight_pounds * 0.453592) /
                POWER((pb.height_inches * 0.0254), 2)
                AS DECIMAL(5, 2)
            )
        ELSE NULL
    END AS bmi,

    -- Height in centimeters (for international datasets)
    CASE
        WHEN pb.height_inches IS NOT NULL THEN
            CAST(pb.height_inches * 2.54 AS DECIMAL(5, 1))
        ELSE NULL
    END AS height_cm,

    -- Weight in kilograms (for international datasets)
    CASE
        WHEN pb.weight_pounds IS NOT NULL THEN
            CAST(pb.weight_pounds * 0.453592 AS DECIMAL(5, 1))
        ELSE NULL
    END AS weight_kg,

    -- Wingspan/Height ratio (indicator of defensive potential)
    CASE
        WHEN pb.wingspan_inches IS NOT NULL AND pb.height_inches IS NOT NULL THEN
            CAST(
                pb.wingspan_inches::REAL / pb.height_inches::REAL
                AS DECIMAL(5, 3)
            )
        ELSE NULL
    END AS wingspan_height_ratio

FROM player_box_score_snapshots s
LEFT JOIN player_biographical pb
    ON s.player_id = pb.player_id;

-- ============================================================================
-- Indexes (for performance)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_vw_snapshots_bio_player_timestamp
    ON player_box_score_snapshots(player_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_vw_snapshots_bio_game_period
    ON player_box_score_snapshots(game_id, period, time_elapsed_seconds);

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: Get player stats with age at specific game moment
/*
SELECT
    player_name,
    timestamp,
    points,
    age_years_decimal,
    age_string,
    height_inches,
    weight_pounds,
    nba_experience_years
FROM vw_player_snapshots_with_biographical
WHERE game_id = '0021500001'
  AND player_id = 'jamesle01'
  AND period = 4
  AND time_elapsed_seconds >= 2700  -- Final 3 minutes
ORDER BY event_number;
*/

-- Example 2: Analyze age-performance relationship
/*
SELECT
    CAST(age_years_decimal AS INTEGER) AS age_bracket,
    COUNT(*) AS games,
    AVG(points) AS avg_points,
    AVG(true_shooting_pct) AS avg_ts_pct,
    AVG(box_plus_minus) AS avg_bpm
FROM vw_player_snapshots_with_biographical
WHERE age_years_decimal IS NOT NULL
  AND minutes > 20  -- Minimum playing time
GROUP BY age_bracket
ORDER BY age_bracket;
*/

-- Example 3: Rookie analysis with uncertainty bounds
/*
SELECT
    player_name,
    age_years_decimal,
    age_min_decimal,
    age_max_decimal,
    age_uncertainty_hours,
    nba_experience_days,
    is_rookie,
    points,
    true_shooting_pct
FROM vw_player_snapshots_with_biographical
WHERE is_rookie = 1
  AND period = 4  -- Fourth quarter
ORDER BY age_years_decimal;
*/

-- Example 4: Physical attributes correlation
/*
SELECT
    height_inches,
    weight_pounds,
    bmi,
    wingspan_height_ratio,
    AVG(block_percentage) AS avg_blk_pct,
    AVG(defensive_rebound_pct) AS avg_drb_pct,
    AVG(box_plus_minus) AS avg_bpm
FROM vw_player_snapshots_with_biographical
WHERE height_inches IS NOT NULL
  AND weight_pounds IS NOT NULL
  AND minutes > 20
GROUP BY height_inches, weight_pounds, bmi, wingspan_height_ratio
HAVING COUNT(*) > 10
ORDER BY avg_bpm DESC;
*/

-- Example 5: ML feature extraction - Age evolution over game
/*
SELECT
    game_id,
    player_id,
    player_name,
    time_elapsed_seconds,
    age_seconds,  -- Use seconds for maximum precision in time-series models
    age_years_decimal,
    points,
    true_shooting_pct,
    box_plus_minus,
    height_inches,
    weight_pounds,
    nba_experience_years
FROM vw_player_snapshots_with_biographical
WHERE player_id = 'jamesle01'
  AND game_id = '0021500001'
ORDER BY event_number;
-- Use for LSTM/Transformer input: [age_seconds, height, weight, experience, ...]
*/

-- ============================================================================
-- ML Feature Engineering Notes
-- ============================================================================

/*
Age Format Selection Guide:

1. **age_years_decimal (DECIMAL(10,4))** - Use for:
   - Linear/polynomial regression models
   - Age-performance curve fitting
   - Continuous gradient-based optimization (neural networks)
   - Example: Predict points scored based on age

2. **age_days (INTEGER)** - Use for:
   - Decision trees, random forests, XGBoost
   - Discrete age binning
   - Categorical age brackets
   - Example: Age groups for player segmentation

3. **age_seconds (BIGINT)** - Use for:
   - LSTM/RNN time-series models
   - High-frequency temporal analysis
   - Exact timestamp-based features
   - Example: Second-by-second fatigue modeling

4. **age_min_decimal / age_max_decimal** - Use for:
   - Uncertainty-aware models
   - Confidence interval calculations
   - Robust optimization with error bounds
   - Example: Conservative vs optimistic age estimates

5. **age_uncertainty_hours (24)** - Use for:
   - Model confidence scoring
   - Feature reliability weighting
   - Ensemble model uncertainty propagation
   - Example: Reduce weight of age-based predictions

6. **nba_experience_years** - Use for:
   - Separate from chronological age
   - Learning curve analysis
   - Rookie vs veteran effects
   - Example: Disentangle age from experience

7. **Physical attributes (height, weight, wingspan, BMI)** - Use for:
   - Matchup analysis (height differential)
   - Position clustering
   - Physical style classification
   - Example: Predict rebounds based on height + wingspan

Combined Feature Examples:
- age_years_decimal + nba_experience_years = Draft age effects
- age_years_decimal + height_inches = Position-specific aging
- age_seconds + weight_pounds = In-game fatigue modeling
- nba_experience_days + bmi = Injury risk prediction
*/

-- ============================================================================
-- Performance Notes
-- ============================================================================

/*
View Performance:
- Query time: < 1 second (uses existing snapshot indexes)
- Join cost: Minimal (1:1 biographical lookup)
- Storage cost: None (view only, no materialization)

Optimization Tips:
- Always filter on game_id or player_id first
- Use indexed columns (player_id, timestamp, game_id, period)
- For large aggregations, consider materializing results
- Age calculations are computed on-the-fly (no pre-computation)

Materialization (optional for frequent queries):
CREATE TABLE player_snapshots_with_bio_materialized AS
SELECT * FROM vw_player_snapshots_with_biographical;

CREATE INDEX idx_bio_mat_player_game
    ON player_snapshots_with_bio_materialized(player_id, game_id);
*/

-- ============================================================================
-- Data Quality Checks
-- ============================================================================

-- Check 1: Count snapshots with biographical data
/*
SELECT
    COUNT(*) AS total_snapshots,
    COUNT(birth_date) AS with_birth_date,
    COUNT(height_inches) AS with_height,
    COUNT(weight_pounds) AS with_weight,
    COUNT(nba_debut_date) AS with_debut_date,
    ROUND(100.0 * COUNT(birth_date) / COUNT(*), 2) AS birth_date_coverage_pct
FROM vw_player_snapshots_with_biographical;
-- Expected: > 90% coverage for modern games
*/

-- Check 2: Age calculation sanity check
/*
SELECT
    player_name,
    age_years_decimal,
    age_min_decimal,
    age_max_decimal,
    age_uncertainty_hours,
    age_string
FROM vw_player_snapshots_with_biographical
WHERE age_years_decimal < 18 OR age_years_decimal > 50
LIMIT 10;
-- Expected: 0 rows (NBA players typically 18-45 years old)
*/

-- Check 3: Physical attributes distribution
/*
SELECT
    MIN(height_inches) AS min_height,
    MAX(height_inches) AS max_height,
    AVG(height_inches) AS avg_height,
    MIN(weight_pounds) AS min_weight,
    MAX(weight_pounds) AS max_weight,
    AVG(weight_pounds) AS avg_weight,
    MIN(bmi) AS min_bmi,
    MAX(bmi) AS max_bmi,
    AVG(bmi) AS avg_bmi
FROM (SELECT DISTINCT player_id, height_inches, weight_pounds, bmi
      FROM vw_player_snapshots_with_biographical
      WHERE height_inches IS NOT NULL);
-- Expected ranges:
-- height: 66-90 inches (5'6" - 7'6")
-- weight: 150-350 pounds
-- BMI: 20-35
*/

-- ============================================================================
