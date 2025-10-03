## 🗄️ Database Migration Workflow

**For setting up PostgreSQL schema and loading data**

### Initial Schema Setup

1. **Connect to RDS instance**:
   ```bash
   psql -h <rds-endpoint> -U admin -d nba_sim
   ```

2. **Create schema from DDL file**:
   ```sql
   \i scripts/sql/schema.sql
   ```

   **Or run commands individually**:
   ```sql
   CREATE SCHEMA IF NOT EXISTS nba;

   CREATE TABLE nba.games (
     game_id VARCHAR(50) PRIMARY KEY,
     season INTEGER NOT NULL,
     game_date DATE NOT NULL,
     home_team VARCHAR(50) NOT NULL,
     away_team VARCHAR(50) NOT NULL,
     home_score INTEGER,
     away_score INTEGER
   );

   CREATE TABLE nba.player_stats (
     stat_id SERIAL PRIMARY KEY,
     game_id VARCHAR(50) REFERENCES nba.games(game_id),
     player_id VARCHAR(50) NOT NULL,
     player_name VARCHAR(255),
     team VARCHAR(50),
     minutes DECIMAL(5,2),
     points INTEGER,
     rebounds INTEGER,
     assists INTEGER
   );

   -- Add indexes for common queries
   CREATE INDEX idx_games_season ON nba.games(season);
   CREATE INDEX idx_games_date ON nba.games(game_date);
   CREATE INDEX idx_player_stats_game ON nba.player_stats(game_id);
   CREATE INDEX idx_player_stats_player ON nba.player_stats(player_id);
   ```

3. **Verify schema created**:
   ```sql
   \dt nba.*
   \d+ nba.games
   ```

4. **Set permissions** (if multi-user):
   ```sql
   GRANT ALL PRIVILEGES ON SCHEMA nba TO admin;
   GRANT SELECT ON ALL TABLES IN SCHEMA nba TO readonly_user;
   ```

### Data Loading from Glue ETL

**After Glue ETL job completes, data automatically loads to RDS**

**Verify data loaded:**
```sql
-- Check row counts
SELECT 'games' as table_name, COUNT(*) as row_count FROM nba.games
UNION ALL
SELECT 'player_stats', COUNT(*) FROM nba.player_stats;

-- Check date range
SELECT MIN(game_date), MAX(game_date) FROM nba.games;

-- Sample data
SELECT * FROM nba.games ORDER BY game_date DESC LIMIT 10;
```

### Manual Data Loading (Alternative)

**If loading from local CSV files:**

```bash
# Copy CSV to S3
aws s3 cp data/games.csv s3://nba-sim-raw-data-lake/temp/

# Load from S3 to RDS using psql
psql -h <endpoint> -U admin -d nba_sim -c "
  COPY nba.games FROM 's3://nba-sim-raw-data-lake/temp/games.csv'
  WITH (FORMAT csv, HEADER true);
"
```

**Or use Python script:**
```python
import pandas as pd
import psycopg2

# Read CSV
df = pd.read_csv('data/games.csv')

# Connect to RDS
conn = psycopg2.connect(
    host='<endpoint>',
    database='nba_sim',
    user='admin',
    password='<password>'
)

# Load to database
df.to_sql('games', conn, schema='nba', if_exists='append', index=False)
```

### Schema Modifications (Adding Columns/Tables)

1. **Create migration script** (`scripts/sql/migrations/001_add_column.sql`):
   ```sql
   ALTER TABLE nba.games ADD COLUMN playoff_game BOOLEAN DEFAULT FALSE;
   ```

2. **Test on local database first** (if available)

3. **Backup RDS before migration**:
   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier nba-sim-db \
     --db-snapshot-identifier nba-sim-pre-migration-$(date +%Y%m%d)
   ```

4. **Run migration**:
   ```bash
   psql -h <endpoint> -U admin -d nba_sim -f scripts/sql/migrations/001_add_column.sql
   ```

5. **Verify migration**:
   ```sql
   \d+ nba.games  -- Check column added
   ```

6. **Document migration** in COMMAND_LOG.md:
   - Migration file path
   - What changed (DDL statements)
   - Why changed (business reason)
   - Data impact (rows affected, downtime)

### Database Maintenance

**Regular maintenance tasks:**

```sql
-- Vacuum and analyze (rebuild indexes, update statistics)
VACUUM ANALYZE nba.games;
VACUUM ANALYZE nba.player_stats;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'nba'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan AS index_scans
FROM pg_stat_user_indexes
WHERE schemaname = 'nba'
ORDER BY idx_scan ASC;  -- Low scans = unused index

-- Check for bloat
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  ROUND(100 * pg_total_relation_size(schemaname||'.'||tablename) / pg_database_size(current_database()), 2) AS percent_of_db
FROM pg_tables
WHERE schemaname = 'nba';
```

**Schedule maintenance:**
- **Weekly:** VACUUM ANALYZE
- **Monthly:** Review index usage, check for bloat
- **Quarterly:** Consider VACUUM FULL (requires downtime)

**See `docs/RDS_CONNECTION.md` for complete database procedures**

---

