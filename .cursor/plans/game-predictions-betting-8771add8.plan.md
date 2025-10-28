<!-- 8771add8-bbc3-45cf-afa4-f27103ea3259 179198cb-e3d6-4b3b-aadc-02e3468abc60 -->
# Dual-Database Odds Collection & Betting Analysis

## Overview

Keep scraper writing to local PostgreSQL (fast, already working) while also syncing data to RDS (for betting scripts and production access). Best of both worlds.

## Phase 1: Set Up Dual-Database Architecture

**Current State**: Scraper writes to `localhost:5432/nba_unified` successfully (14 events, 130+ snapshots per run)

**Goal**: Data flows to BOTH local PostgreSQL AND RDS automatically

### Step 1.1: Verify Local Database Has Data

Check current local database status:

```bash
psql -h localhost -p 5432 -U postgres -d nba_unified -c "
SELECT 
  (SELECT COUNT(*) FROM odds.events) as events,
  (SELECT COUNT(*) FROM odds.odds_snapshots) as snapshots,
  (SELECT MAX(fetched_at) FROM odds.odds_snapshots) as latest_update;
"
```

Expected: Hundreds/thousands of rows from recent scraper runs

### Step 1.2: Create Real-Time Sync Script

Create `scripts/betting/sync_odds_to_rds.py`:

- Connect to both local PostgreSQL and RDS
- Query latest data from local `odds.events` and `odds.odds_snapshots`
- Upsert to RDS (INSERT ON CONFLICT UPDATE)
- Track last sync timestamp for incremental updates
- Run continuously or on schedule (every 1 minute)

Key logic:

```python
# Fetch new records from local since last sync
local_conn = psycopg2.connect("localhost:5432/nba_unified")
rds_conn = psycopg2.connect("nba-sim-db.../nba_simulator")

# Get records updated since last sync
cursor = local_conn.cursor()
cursor.execute("""
    SELECT * FROM odds.odds_snapshots 
    WHERE fetched_at > %s
""", (last_sync_time,))

# Upsert to RDS
for row in cursor:
    rds_cursor.execute("""
        INSERT INTO odds.odds_snapshots (...) 
        VALUES (...) 
        ON CONFLICT (snapshot_id) DO UPDATE SET ...
    """, row)

rds_conn.commit()
```

### Step 1.3: Initial Bulk Sync

Sync all existing local data to RDS:

```bash
cd /Users/ryanranft/nba-simulator-aws
conda activate nba-aws
python3 scripts/betting/sync_odds_to_rds.py --full-sync
```

This copies all historical data from local → RDS as one-time bootstrap.

### Step 1.4: Start Continuous Sync

Launch background sync process:

```bash
python3 scripts/betting/sync_odds_to_rds.py --continuous --interval 60 &
```

Syncs new data every 60 seconds automatically.

### Step 1.5: Verify Data in Both Databases

Check that both databases have matching data:

```bash
# Local
psql -h localhost -p 5432 -d nba_unified -c "SELECT COUNT(*) FROM odds.events"

# RDS
python3 -c "
import psycopg2, os
from dotenv import load_dotenv
load_dotenv('/Users/ryanranft/nba-sim-credentials.env')
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    sslmode='require'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM odds.events')
print(f'RDS: {cur.fetchone()[0]} events')
conn.close()
"
```

Expected: Similar counts in both databases

---

## Phase 2: Execute Betting Analysis

With data in RDS, run comprehensive betting analysis.

### Step 2.1: Create Feature Branch

```bash
cd /Users/ryanranft/nba-simulator-aws
git checkout -b feature/game-predictions-2025-10-28
```

### Step 2.2: Verify October 28 Odds Availability

Check RDS for today's games:

```bash
python3 scripts/betting/fetch_todays_odds.py --date 2025-10-28 --check-only
```

Expected: List of 10-15 NBA games with odds from multiple bookmakers

### Step 2.3: Run Full Betting Analysis Pipeline

Execute master orchestrator:

```bash
python3 scripts/betting/run_full_betting_analysis.py \
    --date 2025-10-28 \
    --n-simulations 10000 \
    --min-edge 0.02
```

This runs all sub-scripts in sequence:

1. Fetch odds from RDS
2. Fetch team/player features
3. Generate ML predictions
4. Run 10K Monte Carlo simulations per game
5. Simulate player props
6. Calculate betting edges (EV, Kelly)
7. Generate reports (Markdown, CSV, JSON)

Duration: 10-15 minutes

### Step 2.4: Review Betting Recommendations

Open generated reports:

```bash
open reports/betting/betting_recommendations_2025-10-28.md
```

Expected output:

- High-confidence bets with +5% edge
- EV calculations for each market
- Kelly Criterion bet sizing
- Player prop opportunities

---

## Alternative: Query Local Database Directly (Simpler)

If sync script is complex, modify betting scripts to query local PostgreSQL:

**Option 1**: Update connection string in betting scripts from RDS to local:

```python
# In scripts/betting/*.py
DB_CONFIG = {
    "host": "localhost",
    "database": "nba_unified",
    "user": "postgres",
    "password": "",  # local password
    "port": 5432,
}
```

**Option 2**: Add `--database` flag to use either local or RDS:

```bash
python3 scripts/betting/run_full_betting_analysis.py --date 2025-10-28 --database local
python3 scripts/betting/run_full_betting_analysis.py --date 2025-10-28 --database rds
```

---

## Key Files

**New Script to Create**:

- `scripts/betting/sync_odds_to_rds.py` - Bidirectional sync between local and RDS

**Existing Betting Scripts** (already created):

- `scripts/betting/fetch_todays_odds.py`
- `scripts/betting/fetch_simulation_features.py`
- `scripts/betting/generate_ml_predictions.py`
- `scripts/betting/run_game_simulations.py`
- `scripts/betting/simulate_player_props.py`
- `scripts/betting/calculate_betting_edges.py`
- `scripts/betting/generate_betting_report.py`
- `scripts/betting/run_full_betting_analysis.py`

**Configuration**:

- Local DB: `localhost:5432/nba_unified` (scraper writes here)
- RDS: `nba-sim-db.../nba_simulator` (betting scripts read here)

---

## Success Criteria

1. ✅ Scraper continues writing to local PostgreSQL (no disruption)
2. ✅ Sync script copies data to RDS in real-time
3. ✅ Both databases have matching odds data
4. ✅ October 28, 2025 games available in RDS
5. ✅ Betting analysis completes successfully
6. ✅ High-confidence recommendations generated

---

## Estimated Timeline

- Phase 1 (Dual-Database Setup): 10-15 minutes
- Phase 2 (Betting Analysis): 10-15 minutes
- **Total: 20-30 minutes**

---

## Which Approach Do You Prefer?

**A) Create sync script** (keeps architecture clean, data in both places)

- Scraper → Local → Sync → RDS
- More robust for production

**B) Modify betting scripts to query local** (simpler, faster to implement)

- Scraper → Local ← Betting Scripts
- No sync needed

**C) Both** (maximum flexibility)

- Sync runs in background for RDS backup
- Betting scripts have --database flag to choose source

### To-dos

- [ ] Verify local PostgreSQL has odds data from scraper
- [ ] Create sync_odds_to_rds.py script for real-time data sync
- [ ] Run initial bulk sync from local to RDS
- [ ] Start continuous sync process in background
- [ ] Verify data in both local and RDS databases match
- [ ] Create feature branch feature/game-predictions-2025-10-28
- [ ] Verify October 28 odds in RDS
- [ ] Run full betting analysis pipeline
- [ ] Review and validate betting recommendations