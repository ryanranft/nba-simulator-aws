# Phase 2.2: Glue ETL Job - Implementation Plan

**Created:** 2025-10-01
**Status:** ⏸️ PENDING (Planning Complete, Ready to Implement)
**Prerequisites:** ✅ Phase 3.1 Complete (RDS Available)

---

## Executive Summary

**Goal:** Extract 10% of relevant JSON fields from S3, filter empty files, transform data, and load into RDS PostgreSQL.

**Approach:** Custom PySpark ETL script (skipping Glue Crawler due to OOM error with 146K+ files)

**Key Challenge:** 17% of files are empty (24,507 files) - must pre-filter before processing

**Estimated Time:** 6-8 hours development + 3 hours runtime
**Estimated Cost:** $13/month for monthly runs

---

## Data Quality Findings

From comprehensive data analysis (Session 8):

| Data Type | Total Files | Valid Files | Valid % | Filter Criteria |
|-----------|-------------|-------------|---------|-----------------|
| **Play-by-Play** | 44,826 | ~31,378 | 70% | `pbp.playGrps` has plays |
| **Box Scores** | 44,828 | ~40,494 | 90% | `bxscr` has 2 teams |
| **Team Stats** | 44,828 | ~38,103 | 85% | `tmStats` has keys |
| **Schedule** | 11,633 | ~11,633 | 100% | No filter needed |
| **TOTAL** | **146,115** | **~121,608** | **83%** | Pre-filter saves 17% compute |

**Storage Impact:**
- Total: ~119 GB
- Usable: ~99 GB (83%)
- Waste: ~20 GB (17%)

**Cost Savings:**
- Pre-filtering saves ~$2.21/month
- Runtime reduction: ~17% faster

---

## JSON Data Structure Reference

**See:** `docs/DATA_STRUCTURE_GUIDE.md` for complete field mappings

### Play-by-Play Files (nba_pbp/)

**JSON Path:** `page.content.gamepackage`

**Data to Extract:**

1. **Play-by-Play Events** (`pbp.playGrps`):
   ```python
   # Structure: [[period1_plays], [period2_plays], ...]
   plays = data['page']['content']['gamepackage']['pbp']['playGrps']

   # Each play:
   {
     'id': '4013078567',
     'period': {'number': 1, 'displayValue': '1st Quarter'},
     'text': 'Markieff Morris makes driving layup',
     'homeAway': 'home',
     'awayScore': 0,
     'homeScore': 2,
     'clock': {'displayValue': '11:34'},
     'scoringPlay': True,  # Optional
     'athlete': {'id': '6461', 'name': 'Markieff Morris'}  # Optional
   }
   ```

2. **Shot Chart Data** (`shtChrt.plays`):
   ```python
   shots = data['page']['content']['gamepackage']['shtChrt']['plays']

   # Each shot:
   {
     'id': '4013078567',
     'coordinate': {'x': 25, 'y': 3},  # Shot location
     'shootingPlay': True,
     'type': {'id': '110', 'txt': 'Driving Layup Shot'}
   }
   ```

3. **Game Info** (`gmInfo`):
   ```python
   info = data['page']['content']['gamepackage']['gmInfo']

   # Fields: attnd, dtTm, loc, refs, venue
   ```

### Box Score Files (nba_box_score/)

**JSON Path:** `page.content.gamepackage.bxscr`

**Data to Extract:**
```python
# List of 2 teams
teams = data['page']['content']['gamepackage']['bxscr']

# Each team:
{
  'tm': {
    'id': '13',
    'displayName': 'Los Angeles Lakers',
    'abbreviation': 'LAL'
  },
  'stats': [
    {'name': 'MIN', 'displayValue': '240'},
    {'name': 'FG', 'displayValue': '42-88'},
    # ... all box score stats
  ]
}
```

### Schedule Files (nba_schedule_json/)

**JSON Path:** `page.content.events`

**Data to Extract:**
```python
games = data['page']['content']['events']

# Each game:
{
  'id': '401307856',
  'date': '2021-05-12T21:30:00Z',
  'competitors': [
    {
      'homeAway': 'home',
      'team': {'id': '13', 'abbreviation': 'LAL'},
      'score': '124'
    },
    {
      'homeAway': 'away',
      'team': {'id': '10', 'abbreviation': 'HOU'},
      'score': '122'
    }
  ],
  'venue': {
    'fullName': 'crypto.com Arena',
    'address': {'city': 'Los Angeles', 'state': 'CA'}
  }
}
```

---

## Database Schema Mapping

**Target Tables:** (from `sql/create_tables.sql`)

### 1. teams
**Source:** schedule/events → competitors → team
```sql
INSERT INTO teams (team_id, team_name, abbreviation, conference, division)
VALUES (...);
```
**Note:** Conference/division not in files - will need static mapping or separate API call

### 2. players
**Source:** pbp/playGrps → plays → athlete
```sql
INSERT INTO players (player_id, player_name, position, team_id)
VALUES (...);
```
**Note:** Position not in pbp files - may need box_score data

### 3. games
**Source:** schedule/events
```sql
INSERT INTO games (game_id, game_date, home_team_id, away_team_id,
                   home_score, away_score, venue_name, city, state)
VALUES (...);
```

### 4. plays
**Source:** pbp/playGrps → plays
```sql
INSERT INTO plays (play_id, game_id, period, clock, play_type,
                   play_text, home_score, away_score, team_id,
                   player_id, scoring_play, shot_x, shot_y)
VALUES (...);
```

### 5. team_game_stats
**Source:** box_scores/bxscr OR team_stats/tmStats
```sql
INSERT INTO team_game_stats (game_id, team_id, minutes_played,
                             field_goals_made, field_goals_attempted, ...)
VALUES (...);
```

### 6. player_game_stats
**Source:** **NOT FOUND in current dataset**
```sql
-- May need additional ESPN scrape or different endpoint
-- Current files don't have individual player box scores
```

---

## PySpark ETL Script Structure

**File:** `scripts/etl/glue_etl_job.py`

### Script Outline

```python
#!/usr/bin/env python3
"""
NBA Data ETL Job for AWS Glue

Extracts 10% of JSON fields from S3, filters empty files, transforms,
and loads into RDS PostgreSQL.

Processes:
- Schedule files: 11,633 files (100% valid)
- Box score files: ~40,494 valid files (90% of 44,828)
- Play-by-play files: ~31,378 valid files (70% of 44,826)
- Team stats files: ~38,103 valid files (85% of 44,828)

Total: ~121,608 files to process
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.types import *


def main():
    # Initialize Glue context
    args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET', 'RDS_ENDPOINT'])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)

    # 1. Process Schedule Files (teams + games)
    teams_df, games_df = process_schedule_files(spark, args['S3_BUCKET'])

    # 2. Process Play-by-Play Files (plays + players)
    plays_df, players_df = process_pbp_files(spark, args['S3_BUCKET'])

    # 3. Process Box Score Files (team_game_stats)
    team_stats_df = process_box_score_files(spark, args['S3_BUCKET'])

    # 4. Write to RDS
    write_to_rds(teams_df, 'teams', args['RDS_ENDPOINT'])
    write_to_rds(players_df, 'players', args['RDS_ENDPOINT'])
    write_to_rds(games_df, 'games', args['RDS_ENDPOINT'])
    write_to_rds(plays_df, 'plays', args['RDS_ENDPOINT'])
    write_to_rds(team_stats_df, 'team_game_stats', args['RDS_ENDPOINT'])

    job.commit()


def process_schedule_files(spark, bucket):
    """Extract teams and games from schedule files."""
    # Read schedule JSON files
    df = spark.read.json(f"s3://{bucket}/schedule/*.json")

    # All schedule files are valid (100%)
    # Extract events
    events_df = df.select(F.explode(F.col("page.content.events")).alias("event"))

    # Extract teams (deduplicated)
    teams_df = events_df.select(
        F.explode(F.col("event.competitors")).alias("competitor")
    ).select(
        F.col("competitor.team.id").alias("team_id"),
        F.col("competitor.team.displayName").alias("team_name"),
        F.col("competitor.team.abbreviation").alias("abbreviation")
    ).distinct()

    # Extract games
    games_df = events_df.select(
        F.col("event.id").alias("game_id"),
        F.col("event.date").alias("game_date"),
        # TODO: Extract home/away team IDs, scores, venue
    )

    return teams_df, games_df


def process_pbp_files(spark, bucket):
    """Extract plays and players from play-by-play files."""
    # Read PBP JSON files
    df = spark.read.json(f"s3://{bucket}/pbp/*.json")

    # FILTER: Keep only files with plays (70% valid)
    df_valid = df.filter(
        F.size(F.col("page.content.gamepackage.pbp.playGrps")) > 0
    )

    print(f"Filtered PBP files: {df.count()} -> {df_valid.count()} (kept {df_valid.count()/df.count()*100:.1f}%)")

    # Explode playGrps (periods) and plays
    plays_df = df_valid.select(
        F.explode(F.col("page.content.gamepackage.pbp.playGrps")).alias("period")
    ).select(
        F.explode(F.col("period")).alias("play")
    ).select(
        F.col("play.id").alias("play_id"),
        # TODO: Extract period, clock, text, scores, etc.
    )

    # Extract players (deduplicated)
    players_df = plays_df.select(
        F.col("play.athlete.id").alias("player_id"),
        F.col("play.athlete.name").alias("player_name")
    ).where(F.col("player_id").isNotNull()).distinct()

    return plays_df, players_df


def process_box_score_files(spark, bucket):
    """Extract team stats from box score files."""
    # Read box score JSON files
    df = spark.read.json(f"s3://{bucket}/box_scores/*.json")

    # FILTER: Keep only files with bxscr data (90% valid)
    df_valid = df.filter(
        F.size(F.col("page.content.gamepackage.bxscr")) >= 2
    )

    print(f"Filtered box score files: {df.count()} -> {df_valid.count()} (kept {df_valid.count()/df.count()*100:.1f}%)")

    # Explode teams
    team_stats_df = df_valid.select(
        F.explode(F.col("page.content.gamepackage.bxscr")).alias("team")
    ).select(
        F.col("team.tm.id").alias("team_id"),
        # TODO: Extract stats array and parse
    )

    return team_stats_df


def write_to_rds(df, table_name, rds_endpoint):
    """Write DataFrame to RDS PostgreSQL."""
    jdbc_url = f"jdbc:postgresql://{rds_endpoint}:5432/nba_simulator"

    df.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", table_name) \
        .option("user", "postgres") \
        .option("password", "${DB_PASSWORD}") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

    print(f"Wrote {df.count()} rows to {table_name}")


if __name__ == "__main__":
    main()
```

---

## Implementation Steps

### Step 1: Local Development (2-3 hours)

1. **Set up local PySpark environment:**
   ```bash
   pip install pyspark==3.3.0  # Match Glue 4.0
   ```

2. **Download sample files for testing:**
   ```bash
   aws s3 cp s3://nba-sim-raw-data-lake/schedule/20210512.json ./samples/
   aws s3 cp s3://nba-sim-raw-data-lake/pbp/401307856.json ./samples/
   aws s3 cp s3://nba-sim-raw-data-lake/box_scores/401307856.json ./samples/
   ```

3. **Develop ETL script incrementally:**
   - Start with schedule files (simplest, 100% valid)
   - Add PBP processing with filtering
   - Add box score processing
   - Test each section independently

4. **Test locally with sample data:**
   ```bash
   python scripts/etl/glue_etl_job.py \
     --JOB_NAME local-test \
     --S3_BUCKET nba-sim-raw-data-lake \
     --RDS_ENDPOINT localhost
   ```

### Step 2: AWS Glue Job Setup (30 min)

1. **Create Glue job via Console:**
   - Name: `nba-etl-job`
   - Type: Spark
   - Glue version: 4.0 (Python 3.11, Spark 3.3)
   - IAM role: `AWSGlueServiceRole-NBASimulator`
   - DPU: 10 (standard for 100K+ files)
   - Script location: Upload `scripts/etl/glue_etl_job.py`

2. **Configure job parameters:**
   ```
   --S3_BUCKET = nba-sim-raw-data-lake
   --RDS_ENDPOINT = nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com
   --DB_PASSWORD = ${SecretsManager:nba-db-password}
   ```

3. **Set up RDS connection:**
   - VPC: same as RDS
   - Subnet: same as RDS
   - Security group: Allow Glue to connect to RDS (port 5432)

### Step 3: Testing (1-2 hours)

1. **Test with 100 files:**
   - Modify script to limit: `.limit(100)`
   - Run job and monitor CloudWatch logs
   - Verify data in RDS

2. **Validate data quality:**
   ```sql
   SELECT COUNT(*) FROM teams;
   SELECT COUNT(*) FROM players;
   SELECT COUNT(*) FROM games;
   SELECT COUNT(*) FROM plays;
   SELECT COUNT(*) FROM team_game_stats;

   -- Check for NULLs in required fields
   SELECT COUNT(*) FROM games WHERE home_team_id IS NULL;
   ```

3. **Check for duplicates:**
   ```sql
   SELECT team_id, COUNT(*) FROM teams GROUP BY team_id HAVING COUNT(*) > 1;
   ```

### Step 4: Full Production Run (3 hours runtime)

1. **Remove test limits from script**
2. **Run full ETL job on all 121,608 files**
3. **Monitor progress via CloudWatch**
4. **Verify final row counts**

---

## Expected Results

**Estimated Row Counts:**

| Table | Estimated Rows | Source |
|-------|----------------|--------|
| teams | ~30 | Schedule files (unique teams) |
| players | ~5,000 | PBP files (unique athletes) |
| games | ~120,000 | Schedule files (all games 1993-2025) |
| plays | ~15,000,000 | PBP files (~468 plays × 31,378 games) |
| team_game_stats | ~240,000 | Box score files (2 teams × 120,000 games) |
| player_game_stats | 0 | **Not available in current dataset** |

**Database Size After Load:**
- Estimated: ~12 GB (based on 10% extraction from 119 GB)
- Breakdown:
  - plays table: ~10 GB (largest, 15M rows)
  - team_game_stats: ~1 GB
  - games: ~500 MB
  - Other tables: ~500 MB

---

## Monitoring & Validation

### During ETL Run

**CloudWatch Logs:**
```bash
aws logs tail /aws-glue/jobs/output --log-stream-name nba-etl-job --follow
```

**Job Status:**
```bash
aws glue get-job-run --job-name nba-etl-job --run-id jr_xxx
```

### Post-ETL Validation

**SQL Validation Queries:**
```sql
-- 1. Row counts
SELECT 'teams' AS table_name, COUNT(*) AS row_count FROM teams
UNION ALL
SELECT 'players', COUNT(*) FROM players
UNION ALL
SELECT 'games', COUNT(*) FROM games
UNION ALL
SELECT 'plays', COUNT(*) FROM plays
UNION ALL
SELECT 'team_game_stats', COUNT(*) FROM team_game_stats;

-- 2. Data quality checks
-- No NULL game_ids
SELECT COUNT(*) FROM plays WHERE game_id IS NULL;

-- No orphaned records (referential integrity)
SELECT COUNT(*) FROM plays p
LEFT JOIN games g ON p.game_id = g.game_id
WHERE g.game_id IS NULL;

-- 3. Date range verification
SELECT
    MIN(game_date) AS earliest_game,
    MAX(game_date) AS latest_game,
    COUNT(DISTINCT EXTRACT(YEAR FROM game_date)) AS years_covered
FROM games;

-- 4. Completeness check
-- Expected: ~120,000 games from 1993-2025
SELECT
    EXTRACT(YEAR FROM game_date) AS year,
    COUNT(*) AS games_per_year
FROM games
GROUP BY EXTRACT(YEAR FROM game_date)
ORDER BY year;
```

---

## Error Handling

**Common Issues:**

1. **OOM Errors during Processing:**
   - Increase DPU allocation (10 → 20)
   - Process in batches by year/month
   - Use partitioning: `partitionBy("year", "month")`

2. **RDS Connection Timeout:**
   - Check security group allows Glue CIDR
   - Verify VPC settings
   - Use connection pooling in JDBC options

3. **Data Type Mismatches:**
   - Cast JSON strings to appropriate types
   - Handle NULL values explicitly
   - Use `try_cast()` for safe conversions

4. **Duplicate Key Violations:**
   - Use `INSERT ... ON CONFLICT DO NOTHING` (PostgreSQL upsert)
   - Or deduplicate in PySpark before write

---

## Cost Breakdown

**One-Time Development:**
- Testing runs (100-file samples): ~$2-5
- Debugging and iteration: ~$5-10
- **Total development cost:** ~$10

**Full Production Run:**
- 10 DPUs × 3 hours × $0.44/DPU-hour = $13.20

**Monthly Recurring (if run monthly):**
- $13.20/month

**Optimization Options:**
- Run quarterly: $13.20/quarter = ~$4.40/month
- Run only on-demand: Pay per run

---

## Success Criteria

- ✅ ETL job completes without errors
- ✅ All 121,608 valid files processed
- ✅ Row counts match expected values (±5%)
- ✅ No NULL values in required fields
- ✅ Foreign key relationships valid
- ✅ Data spans expected date range (1993-2025)
- ✅ Sample queries return correct results
- ✅ Database size ~12 GB

---

## Next Steps After Completion

1. **Mark Phase 2.2 as ✅ COMPLETE in PROGRESS.md**
2. **Update cost estimates with actuals**
3. **Document any issues in LESSONS_LEARNED.md**
4. **Create ADR-008:** Skip Glue Crawler for Large Datasets
5. **Proceed to Phase 4.1:** EC2 Simulation Engine setup

---

## References

- **Data Structure Guide:** `docs/DATA_STRUCTURE_GUIDE.md`
- **RDS Connection:** `docs/RDS_CONNECTION.md`
- **Database Schema:** `sql/create_tables.sql`
- **PROGRESS.md:** Phase 2.2 details
- **AWS Glue Documentation:** https://docs.aws.amazon.com/glue/

---

**Last Updated:** 2025-10-01
**Next Review:** When starting Phase 2.2 implementation