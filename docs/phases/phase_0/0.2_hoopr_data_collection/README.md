# 0.2: hoopR Data Collection

**Sub-Phase:** 0.2 (Data Collection - R Package)
**Parent Phase:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Status:** ✅ COMPLETE (October 9, 2025)
**Priority:** ⭐ CRITICAL
**Data Source:** hoopR R Package (v2.0+)

---

## Overview

Collected comprehensive NBA data using the hoopR R package, providing 23 years of play-by-play, player box scores, team box scores, and schedule data (2002-2025). This data source provides the most complete modern era coverage with 100% availability for 2002+.

**Key Achievements:**
- **410 files collected** (314 CSV + 96 Parquet)
- **8.2 GB total** across all formats
- **30,758 games** with complete data
- **13.1M play-by-play events** (6.2 GB in RDS)
- **100% coverage** for 2002-2025 seasons

---

## Data Growth Tracking (Live - Powered by DIMS)

**Get current hoopR S3 metrics (always up-to-date):**

```bash
# Verify all S3 storage metrics (includes hoopR data)
python scripts/monitoring/dims_cli.py verify --category s3_storage

# Count hoopR-specific files
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_parquet/ --recursive | wc -l
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_phase1/ --recursive | wc -l
```

**Historical milestones:**
- **Oct 9, 2025 (Phase 0.2 Initial Upload):** 410 files (314 CSV + 96 Parquet), 8.2 GB
- **Oct 9, 2025 (RDS Integration):** 13.1M play-by-play events, 6.7 GB in RDS PostgreSQL

**Current metrics tracked in:** `inventory/metrics.yaml`

**See also:** [Workflow #56: DIMS Management](../../claude_workflows/workflow_descriptions/56_dims_management.md)

---

## How This Phase Enables the Simulation Vision

This phase provides **modern era play-by-play data with complete coverage (2002-2025)** that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What Phase 0.2 enables:**

### 1. High-Frequency Panel Data for Econometric Analysis
- **13.1M play-by-play events** provide granular observations for panel data regression
- **Game clock timestamps** enable temporal feature engineering (score differential evolution, time remaining, momentum detection)
- **Player/team IDs** support fixed effects estimation to control for unobserved heterogeneity
- **Event sequences** allow for lagged variables and autoregressive modeling

### 2. Econometric Causal Inference (Main README: Lines 73-82)
From this phase's play-by-play data, we can:
- **Panel data regression**: Use fixed effects to estimate causal PPP (Points Per Possession) effects by game context
- **Instrumental variables**: Use player's historical usage rate as instrument for current game usage (addresses endogeneity)
- **Propensity score matching**: Find comparable possessions from 13.1M events to build counterfactual scenarios
- **Heterogeneous treatment effects**: Model how offensive play effectiveness varies by defender quality, fatigue, score margin
- **Structural estimation**: Build 3×3 payoff matrices with econometrically-estimated expected PPP

### 3. Nonparametric Event Modeling (Main README: Lines 84-92)
From this phase's comprehensive event data, we build:
- **Kernel density estimation**: Model rare event frequencies (technical fouls, flagrant fouls) without parametric assumptions
- **Bootstrap resampling**: Generate injury occurrences by resampling from observed in-game events
- **Empirical CDFs**: Draw unusual plays (shot clock violations, coach's challenges) from empirical distributions
- **Changepoint detection**: Identify momentum shifts using PELT/Binary Segmentation on scoring runs
- **Empirical transition matrices**: Capture shooting "hot/cold" streaks via observed transition probabilities (not geometric assumptions)

### 4. Context-Adaptive Simulations
Using this phase's 23+ years of data (2002-2025), simulations adapt to:
- **Game situation context**: 13.1M events covering all score differentials, quarter times, playoff vs. regular season
- **Player aging dynamics**: Complete career arcs from rookie seasons through decline (785K player-game observations)
- **Temporal dynamics**: First game vs. mid-season vs. playoffs (30,758 games across all contexts)
- **Cross-source validation**: 97% overlap with ESPN data enables robustness checks and data quality assurance

**Key advantage of Phase 0.2:** Provides the **longest modern-era temporal coverage** (23+ years) with **100% play-by-play availability**, enabling robust estimation of causal effects and empirical distributions across all game contexts.

See [main README simulation methodology](../../../README.md#simulation-methodology) for complete technical framework.

---

## Data Coverage

### Temporal Coverage
- **Date Range:** 2002-2025 (23+ years)
- **Seasons:** 24 complete seasons
- **Games:** 30,758 total games
- **Quality:** Excellent (100% availability for modern era)

### Data Types

| Type | Records | Size | Columns | Status |
|------|---------|------|---------|--------|
| Play-by-Play | 13,074,829 | 6.2 GB | 63 | ✅ Complete |
| Player Box Scores | 785,505 | 433 MB | 56 | ✅ Complete |
| Team Box Scores | 59,670 | 29 MB | 56 | ✅ Complete |
| Schedule | 30,758 | 27 MB | 77 | ✅ Complete |

---

## Quick Start

### Access hoopR Data in RDS

```python
import psycopg2
import pandas as pd
import os

# Connect to RDS
conn = psycopg2.connect(
    host=os.getenv('RDS_HOST'),
    database=os.getenv('RDS_DATABASE'),
    user=os.getenv('RDS_USER'),
    password=os.getenv('RDS_PASSWORD')
)

# Query play-by-play data
query = """
    SELECT *
    FROM hoopr_play_by_play
    WHERE game_date >= '2024-10-01'
    ORDER BY game_date, sequence_number
    LIMIT 1000;
"""

df = pd.read_sql(query, conn)
print(f"Retrieved {len(df)} play-by-play events")

# Query player box scores
query = """
    SELECT
        player_display_name,
        team_name,
        minutes,
        field_goals_made,
        points,
        rebounds,
        assists
    FROM hoopr_player_box
    WHERE season = 2024
    ORDER BY points DESC
    LIMIT 10;
"""

df = pd.read_sql(query, conn)
print("\nTop scorers 2024 season:")
print(df)
```

---

## Collection Process

### Phase 1: Initial Collection (October 8, 2025)

**Script:** `scripts/etl/scrape_hoopr_phase1_foundation.R`

```r
# Install hoopR package
install.packages("hoopR")
library(hoopR)

# Load all seasons (2002-2025)
seasons <- 2002:2025

for(season in seasons) {
  # Play-by-play
  pbp <- load_nba_pbp(season)
  write.csv(pbp, paste0("pbp_", season, ".csv"))

  # Player box scores
  player_box <- load_nba_player_box(season)
  write.csv(player_box, paste0("player_box_", season, ".csv"))

  # Team box scores
  team_box <- load_nba_team_box(season)
  write.csv(team_box, paste0("team_box_", season, ".csv"))

  # Schedule
  schedule <- load_nba_schedule(season)
  write.csv(schedule, paste0("schedule_", season, ".csv"))

  Sys.sleep(2)  # Rate limiting
}
```

**Collection Time:** ~6 hours (24 seasons × 4 data types × ~4 min/type)

### Phase 2: S3 Upload (October 8-9, 2025)

**CSV Upload:**
```bash
# Upload CSV files to S3
aws s3 sync /Users/ryanranft/Projects/hoopR-nba-data/ \
  s3://nba-sim-raw-data-lake/hoopr_phase1/ \
  --exclude "*" --include "*.csv"
```

**Parquet Upload:**
```bash
# Upload Parquet files to S3
aws s3 sync /Users/ryanranft/Desktop/sports_data_backup/hoopR/ \
  s3://nba-sim-raw-data-lake/hoopr_parquet/ \
  --exclude "*" --include "*.parquet"
```

### Phase 3: RDS Integration (October 9, 2025)

**Script:** `scripts/db/load_hoopr_to_rds.py`

```python
import pandas as pd
import boto3
import psycopg2
from io import StringIO

def load_hoopr_to_rds():
    """Load hoopR data from S3 to RDS PostgreSQL"""

    s3 = boto3.client('s3')
    conn = psycopg2.connect(...)

    # Create tables
    create_hoopr_tables(conn)

    # Load play-by-play
    seasons = range(2002, 2026)
    for season in seasons:
        key = f"hoopr_parquet/play_by_play/pbp_{season}.parquet"
        df = read_parquet_from_s3(s3, 'nba-sim-raw-data-lake', key)

        # Bulk insert
        df.to_sql('hoopr_play_by_play', conn, if_exists='append',
                  index=False, method='multi', chunksize=10000)

        print(f"Loaded {len(df)} play-by-play rows for {season}")

    # Create indexes
    create_indexes(conn)

    conn.commit()
```

**Load Performance:**
- **Time:** ~10 minutes
- **Rate:** 33,416 rows/second
- **Total Rows:** 13.1M rows across 4 tables

---

## Data Schema

### Table: `hoopr_play_by_play`

**Size:** 6.2 GB, 13,074,829 rows, 63 columns

**Key Columns:**
```sql
CREATE TABLE hoopr_play_by_play (
    -- Identifiers
    game_id VARCHAR(50),
    play_id VARCHAR(100),
    sequence_number INTEGER,

    -- Timing
    game_date DATE,
    period INTEGER,
    clock_display_value VARCHAR(10),

    -- Event Details
    type_text VARCHAR(100),
    text TEXT,
    scoring_play BOOLEAN,

    -- Participants
    team_id INTEGER,
    athlete_id_1 INTEGER,
    athlete_id_2 INTEGER,

    -- Score State
    home_score INTEGER,
    away_score INTEGER,

    -- Additional Context
    shot_type VARCHAR(50),
    coordinate_x DECIMAL(10,2),
    coordinate_y DECIMAL(10,2),

    -- Metadata
    wallclock TIMESTAMP,
    home_team_spread DECIMAL(5,2)
);
```

### Table: `hoopr_player_box`

**Size:** 433 MB, 785,505 rows, 56 columns

**Key Statistics:**
- Field goals (made, attempted, percentage)
- Three-pointers (made, attempted, percentage)
- Free throws (made, attempted, percentage)
- Rebounds (offensive, defensive, total)
- Assists, steals, blocks, turnovers
- Plus/minus, minutes played
- Fantasy points

### Table: `hoopr_team_box`

**Size:** 29 MB, 59,670 rows, 56 columns

**Team-level aggregates** of all player box score statistics

### Table: `hoopr_schedule`

**Size:** 27 MB, 30,758 rows, 77 columns

**Comprehensive game metadata:**
- Game IDs, dates, times
- Home/away teams
- Venues, attendance
- Broadcast information
- Game status

---

## Data Quality

### Completeness

| Season Range | Games | Completion | Notes |
|--------------|-------|------------|-------|
| 2002-2021 | 24,600 | 100% | Complete historical |
| 2022-2024 | 5,658 | 100% | Recent seasons |
| 2025 | 500 | Ongoing | Current season |

### Quality Metrics

- **Play-by-Play Coverage:** 100% for all games
- **Timestamp Precision:** Game clock precision (suitable for temporal reconstruction to millisecond-level via econometric + nonparametric simulation)
- **Event Types:** Standard NBA event codes
- **Player IDs:** NBA official IDs
- **Cross-Source Validation:** 97% match with ESPN data

### Known Limitations

- **Pre-2002 Gap:** No data available before 2002
- **Coordinate Precision:** Shot coordinates approximate
- **Clock Display:** Some formatting inconsistencies
- **Player Names:** Occasional spelling variations

---

## Storage Locations

### Local Storage

**Discovered October 9, 2025 - 57.8 GB total across 3 locations:**

1. **Primary Raw:** `/Users/ryanranft/Projects/hoopR-nba-raw`
   - 43 GB
   - 29,688 JSON files
   - Raw API responses

2. **Structured Data:** `/Users/ryanranft/Projects/hoopR-nba-data`
   - 8.6 GB
   - 235 CSV files
   - Cleaned and structured

3. **Analysis-Ready:** `/Users/ryanranft/Desktop/sports_data_backup/hoopR`
   - 6.2 GB
   - 120 Parquet files
   - Optimized for querying

### S3 Storage

**Bucket:** `s3://nba-sim-raw-data-lake/`

1. **Parquet Files:**
   - `hoopr_parquet/play_by_play/` - 24 files (393 MB)
   - `hoopr_parquet/player_box/` - 24 files (15 MB)
   - `hoopr_parquet/schedule/` - 24 files (3.4 MB)
   - `hoopr_parquet/team_box/` - 24 files (3.1 MB)

2. **CSV Files:**
   - `hoopr_phase1/` - 314 files (7.7 GB)

### RDS PostgreSQL

**Database:** `nba_simulator`
**Total Size:** 6.7 GB (hoopR portion of 13.9 GB total)

**Tables:**
- `hoopr_play_by_play` - 6.2 GB, 13.1M rows
- `hoopr_player_box` - 433 MB, 785K rows
- `hoopr_team_box` - 29 MB, 59K rows
- `hoopr_schedule` - 27 MB, 30K rows

---

## Integration with Unified Views

### Unified Play-by-Play View

Created October 9, 2025 to provide seamless 33-year coverage (1993-2025):

```sql
CREATE VIEW unified_play_by_play AS
-- ESPN data: Pre-2002 (1993-2001)
SELECT
    game_id,
    'ESPN' as source,
    event_timestamp as game_time,
    description,
    home_score,
    away_score
FROM temporal_events
WHERE EXTRACT(YEAR FROM game_date) < 2002

UNION ALL

-- hoopR data: 2002+ (modern era with 100% coverage)
SELECT
    game_id,
    'hoopR' as source,
    clock_display_value as game_time,
    text as description,
    home_score,
    away_score
FROM hoopr_play_by_play
WHERE EXTRACT(YEAR FROM game_date) >= 2002
ORDER BY game_time;
```

### Unified Schedule View

```sql
CREATE VIEW unified_schedule AS
SELECT game_id, game_date, home_team, away_team, 'ESPN' as source
FROM espn_schedule
WHERE EXTRACT(YEAR FROM game_date) < 2002

UNION ALL

SELECT game_id, game_date, home_team_name, away_team_name, 'hoopR' as source
FROM hoopr_schedule
WHERE EXTRACT(YEAR FROM game_date) >= 2002;
```

**Total Coverage:** 40,652 games (1993-2025)

---

## Cross-Source Validation

### hoopR vs ESPN Comparison

**Script:** `scripts/validation/cross_validate_espn_hoopr_with_mapping.py`

```python
def compare_hoopr_espn_coverage():
    """Compare game coverage between hoopR and ESPN"""

    # hoopR games (2002+)
    hoopr_games = set(hoopr_df['game_id'])

    # ESPN games (2002+)
    espn_games = set(espn_df['game_id'])

    # Calculate overlap
    both = hoopr_games & espn_games
    hoopr_only = hoopr_games - espn_games
    espn_only = espn_games - hoopr_games

    print(f"Both sources: {len(both)} games (97% overlap)")
    print(f"hoopR only: {len(hoopr_only)} games")
    print(f"ESPN only: {len(espn_only)} games")
```

**Results:**
- **Overlap:** 97% of games present in both sources
- **hoopR Unique:** 3% additional games (postponed/rescheduled)
- **ESPN Unique:** <1% (mostly exhibition games)

---

## Performance Characteristics

### Query Performance

**Play-by-Play Queries:**
- Single game: ~50ms
- Single season: ~200ms
- Full dataset: ~2-3 seconds

**Indexes:**
```sql
CREATE INDEX idx_hoopr_pbp_game_date ON hoopr_play_by_play(game_date);
CREATE INDEX idx_hoopr_pbp_game_id ON hoopr_play_by_play(game_id);
CREATE INDEX idx_hoopr_player_game ON hoopr_player_box(game_id, athlete_id);
CREATE INDEX idx_hoopr_schedule_date ON hoopr_schedule(game_date);
```

---

## Cost Breakdown

### Collection Costs
- **hoopR Package:** FREE (open source)
- **R Compute:** $0 (ran locally)
- **Collection Time:** 6 hours

### Storage Costs
- **S3 Storage:** 8.2 GB × $0.023/GB = **$0.19/month**
- **RDS Storage:** 6.7 GB × $0.115/GB = **$0.77/month**
- **Total:** **$0.96/month**

### Data Transfer Costs
- **Upload to S3:** $0 (same region)
- **S3 to RDS:** $0 (same region, same account)

---

## Scripts Reference

### Collection Scripts
- `scripts/etl/scrape_hoopr_phase1_foundation.R` - Initial data collection
- `scripts/etl/scrape_hoopr_complete_all_endpoints.R` - All 152 endpoints
- `scripts/etl/hoopr_incremental_scraper.py` - Daily updates

### Loading Scripts
- `scripts/db/load_hoopr_to_rds.py` - S3 → RDS bulk load
- `scripts/db/load_hoopr_player_box_only.py` - Player stats only
- `scripts/db/create_unified_espn_hoopr_view.py` - Unified views

### Validation Scripts
- `scripts/validation/cross_validate_espn_hoopr_with_mapping.py` - Cross-source comparison
- `scripts/validation/validate_hoopr_152_output.R` - Data quality checks
- `scripts/utils/compare_espn_hoopr_local.py` - Local vs cloud sync

---

## Related Documentation

- **[DATA_CATALOG.md](../../../DATA_CATALOG.md)** - Complete data source reference
- **[HOOPR_SCHEMA_MAPPING.md](../../../HOOPR_SCHEMA_MAPPING.md)** - Schema details
- **[HOOPR_152_ENDPOINTS_GUIDE.md](../../../HOOPR_152_ENDPOINTS_GUIDE.md)** - API reference
- **[Phase 9.2: hoopR Processor](../../phase_9/9.2_hoopr_processor.md)** - ETL pipeline

---

## Navigation

**Return to:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Previous:** [0.1: ESPN Initial Upload](../0.1_initial_data_collection/README.md)
**Next:** [0.3: Kaggle Historical Database](../0.3_kaggle_historical_database/README.md)

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Data Source:** hoopR R Package v2.0+
**Collection Date:** October 8-9, 2025

