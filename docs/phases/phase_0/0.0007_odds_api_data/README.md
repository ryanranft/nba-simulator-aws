# 0.7: Odds API Data Integration

**Sub-Phase:** 0.7 (Data Collection - Betting Odds)
**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
**Status:** ✅ COMPLETE
**Priority:** ⭐ HIGH
**Completed:** October 23, 2025
**Implementation ID:** phase_0_7

---

## Overview

Phase 0.7 integrates betting odds data from The Odds API into the nba-simulator-aws system. **This integration uses a separate autonomous scraper project** ([odds-api](https://github.com/ryanranft/odds-api)) that continuously collects betting odds and writes to the shared RDS PostgreSQL database.

**Key Achievement:** Real-time betting market data integrated with ML predictions for value betting identification and strategy validation.

---

## Architecture

### Two-Project Integration

This phase represents an integration between **two separate projects**:

1. **[odds-api](file:///Users/ryanranft/odds-api/)** - Autonomous scraper (separate repository)
   - Continuously collects betting odds from The Odds API
   - Handles API quota management and rate limiting
   - Writes to `odds` schema in shared RDS database
   - Runs independently with its own monitoring and logging

2. **[nba-simulator-aws](https://github.com/ryanranft/nba-simulator-aws)** - ML/simulation system (this project)
   - Reads odds data from shared RDS database
   - Compares ML predictions vs. market odds
   - Identifies value betting opportunities
   - Validates betting strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                        Shared RDS PostgreSQL                     │
│                  nba-sim-db.ck96ciigs7fy.us-east-1              │
│                                                                  │
│  ┌──────────────┐                    ┌───────────────────────┐  │
│  │ odds schema  │◄───────────────────┤   odds-api scraper    │  │
│  │              │    Writes odds     │   (autonomous)        │  │
│  │ - events     │                    │                       │  │
│  │ - odds_*     │                    │   /Users/ryanranft/   │  │
│  │ - bookmakers │                    │   odds-api/           │  │
│  └──────────────┘                    └───────────────────────┘  │
│         │                                                        │
│         │ Reads odds                                            │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ nba-simulator│                                               │
│  │ - predictions│                                               │
│  │ - models     │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## odds-api Scraper System

### Location
**Repository:** `/Users/ryanranft/odds-api/`
**Documentation:** [odds-api README.md](file:///Users/ryanranft/odds-api/README.md)

### Features

- **Comprehensive Market Coverage:** Moneylines, spreads, totals, player props, period markets, alternate lines
- **Multi-Region Support:** Chicago/IL, US offshore, UK, Australian, European bookmakers
- **Intelligent Collection:** Incremental storage (only saves when odds change), gap detection, automated backfill
- **Production Ready:** Async/await, connection pooling, circuit breakers, health checks
- **Data Quality:** Duplicate detection, range validation, completeness checks
- **Observability:** Prometheus metrics, Grafana dashboards, anomaly detection
- **Quota Management:** Smart bookmaker selection, dynamic throttling

### Collection Modes

The scraper adapts its collection frequency based on game timing:

| Mode | Frequency | Timing | Purpose |
|------|-----------|--------|---------|
| **Continuous** | Every 5 minutes | 24+ hours before game | Featured markets monitoring |
| **Pre-Game** | Every 1 hour | 24 hours before tip-off | Market discovery + comprehensive collection |
| **Game Day** | Every 1 minute | 2 hours before tip-off | All markets, all bookmakers |
| **Live Game** | Every 30 seconds | During games | Real-time odds + scores |
| **Post-Game** | One-time | After game ends | Final snapshot + scores |

### API Quota Management

**The Odds API Tiers:**
- **Free Tier:** 500 credits/month (limited, not suitable for NBA)
- **20K Plan:** 20,000 credits/month (~$100/month, recommended)
- **100K Plan:** 100,000 credits/month (~$400/month, high-frequency trading)

**Current Setup:** 20K monthly plan provides comprehensive NBA coverage

---

## Database Schema

The odds-api scraper creates an `odds` schema in the shared RDS database:

### Core Tables

#### 1. `odds.events`
Game metadata from The Odds API

```sql
CREATE TABLE odds.events (
    event_id VARCHAR(100) PRIMARY KEY,        -- Unique event ID from API
    sport_key VARCHAR(50) NOT NULL,           -- 'basketball_nba'
    sport_title VARCHAR(100),                 -- 'NBA'
    commence_time TIMESTAMP NOT NULL,         -- Game start time
    home_team VARCHAR(100) NOT NULL,          -- Home team name
    away_team VARCHAR(100) NOT NULL,          -- Away team name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `odds.bookmakers`
Sportsbook reference data

```sql
CREATE TABLE odds.bookmakers (
    bookmaker_id SERIAL PRIMARY KEY,
    bookmaker_key VARCHAR(50) UNIQUE NOT NULL,    -- 'draftkings', 'fanduel'
    bookmaker_title VARCHAR(100) NOT NULL,        -- 'DraftKings', 'FanDuel'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Pre-loaded Bookmakers:**
- DraftKings
- FanDuel
- BetMGM
- PointsBet
- William Hill (US)
- Barstool Sportsbook
- BetOnline.ag
- Bovada
- MyBookie.ag
- WynnBET

#### 3. `odds.market_types`
Market type catalog

```sql
CREATE TABLE odds.market_types (
    market_type_id SERIAL PRIMARY KEY,
    market_key VARCHAR(50) UNIQUE NOT NULL,       -- 'h2h', 'spreads', 'totals'
    market_name VARCHAR(100) NOT NULL,            -- 'Head to Head (Moneyline)'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Pre-loaded Markets:**
- h2h (Head to Head / Moneyline)
- spreads (Point Spreads)
- totals (Over/Under)
- h2h_q1, h2h_q2, h2h_q3, h2h_q4 (Quarter moneylines)
- h2h_h1, h2h_h2 (Half moneylines)

#### 4. `odds.odds_snapshots`
Main temporal odds storage (temporal panel data)

```sql
CREATE TABLE odds.odds_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL REFERENCES odds.events(event_id) ON DELETE CASCADE,
    bookmaker_id INTEGER NOT NULL REFERENCES odds.bookmakers(bookmaker_id),
    market_type_id INTEGER NOT NULL REFERENCES odds.market_types(market_type_id),
    outcome_name VARCHAR(100) NOT NULL,           -- 'Los Angeles Lakers'
    price DECIMAL(10, 2),                         -- -110, +150 (American odds)
    point DECIMAL(10, 2),                         -- -5.5, 220.5 (spread/total)
    last_update TIMESTAMP NOT NULL,               -- When bookmaker updated odds
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When we fetched it
    is_latest BOOLEAN DEFAULT TRUE                -- Latest odds snapshot flag
);

-- Indexes for high-frequency queries
CREATE INDEX idx_odds_snapshots_event ON odds.odds_snapshots(event_id);
CREATE INDEX idx_odds_snapshots_is_latest ON odds.odds_snapshots(is_latest) WHERE is_latest = TRUE;
```

#### 5. `odds.scores`
Game outcomes for validation

```sql
CREATE TABLE odds.scores (
    score_id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL REFERENCES odds.events(event_id) ON DELETE CASCADE,
    home_score INTEGER,
    away_score INTEGER,
    is_final BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Additional Tables

The odds-api scraper also creates:
- `odds.participants` - Canonical team/player names
- `odds.odds_changes` - Incremental storage (only when odds move)
- `odds.api_quota_tracking` - Real-time API quota monitoring
- `odds.scraper_runs` - Execution tracking
- `odds.data_quality_checks` - Validation tracking
- `odds.collection_gaps` - Missing data tracking

See [`/Users/ryanranft/odds-api/sql/create_tables.sql`](file:///Users/ryanranft/odds-api/sql/create_tables.sql) for complete schema.

---

## Data Characteristics

### Temporal Coverage
- **Real-time:** Current NBA season (updated every 30 seconds to 5 minutes)
- **Historical:** All collected odds snapshots with full temporal history
- **Future:** Upcoming games with pre-game odds

### Bookmaker Coverage
- **Primary Focus:** Chicago/IL legal sportsbooks (DraftKings, FanDuel, BetMGM)
- **Secondary:** US offshore books (Bovada, BetOnline, MyBookie)
- **10+ bookmakers** tracked per game

### Market Coverage
- **Full Game:** Moneylines, spreads, totals
- **Quarters:** Q1-Q4 moneylines
- **Halves:** First half, second half lines
- **Player Props:** Points, rebounds, assists (future expansion)
- **Alternate Lines:** Alternate spreads/totals (future expansion)

### Data Volume Estimates

| Collection Frequency | Games/Day | Snapshots/Day | Monthly Volume |
|---------------------|-----------|---------------|----------------|
| Continuous (5 min) | 10 | 2,880 | 86,400 |
| Pre-Game (1 hour) | 10 | 240 | 7,200 |
| Game Day (1 min) | 10 | 7,200 | 216,000 |
| Live (30 sec) | 10 | 14,400 | 432,000 |
| **Total** | - | **24,720/day** | **~740K/month** |

---

## Integration with nba-simulator-aws

### Querying Odds Data

From nba-simulator-aws, query odds data using standard PostgreSQL connection:

```python
import psycopg2
import os
from dotenv import load_dotenv

# Load shared credentials
load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME", "nba_simulator"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", 5432),
    sslmode="require"
)

# Get latest odds for upcoming games
query = """
SELECT
    e.event_id,
    e.home_team,
    e.away_team,
    e.commence_time,
    b.bookmaker_title,
    mt.market_name,
    os.outcome_name,
    os.price,
    os.point
FROM odds.events e
JOIN odds.odds_snapshots os ON e.event_id = os.event_id
JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
WHERE e.commence_time > NOW()
  AND os.is_latest = true
  AND b.bookmaker_key = 'draftkings'
  AND mt.market_key = 'spreads'
ORDER BY e.commence_time;
"""

import pandas as pd
df = pd.read_sql(query, conn)
print(df)
```

### Comparing ML Predictions vs. Market Odds

```python
def find_betting_edges():
    """Find games where ML model disagrees with betting market."""

    query = """
    WITH model_predictions AS (
        SELECT
            game_id,
            home_team,
            away_team,
            predicted_home_win_prob,
            predicted_spread
        FROM ml_predictions
        WHERE game_date = CURRENT_DATE
    ),
    market_consensus AS (
        SELECT
            e.event_id,
            e.home_team,
            e.away_team,
            AVG(os.point) FILTER (WHERE mt.market_key = 'spreads'
                                  AND os.outcome_name = e.home_team) as avg_spread,
            AVG(os.price) FILTER (WHERE mt.market_key = 'h2h'
                                  AND os.outcome_name = e.home_team) as avg_moneyline
        FROM odds.events e
        JOIN odds.odds_snapshots os ON e.event_id = os.event_id
        JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
        JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
        WHERE e.commence_time::date = CURRENT_DATE
          AND os.is_latest = true
          AND b.bookmaker_key IN ('draftkings', 'fanduel', 'betmgm')
        GROUP BY e.event_id, e.home_team, e.away_team
    )
    SELECT
        mp.game_id,
        mp.home_team,
        mp.away_team,
        mp.predicted_spread as model_spread,
        mc.avg_spread as market_spread,
        mp.predicted_spread - mc.avg_spread as edge,
        CASE
            WHEN ABS(mp.predicted_spread - mc.avg_spread) > 3.0 THEN 'Strong Edge'
            WHEN ABS(mp.predicted_spread - mc.avg_spread) > 2.0 THEN 'Moderate Edge'
            ELSE 'No Edge'
        END as edge_classification
    FROM model_predictions mp
    JOIN market_consensus mc
        ON mp.home_team = mc.home_team
        AND mp.away_team = mc.away_team
    WHERE ABS(mp.predicted_spread - mc.avg_spread) > 2.0
    ORDER BY ABS(edge) DESC;
    """

    return pd.read_sql(query, conn)

# Find today's betting opportunities
edges = find_betting_edges()
print(f"Found {len(edges)} games with 2+ point edge")
print(edges)
```

### Calculating Implied Probabilities

```python
def american_odds_to_probability(odds):
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def calculate_market_vig(home_odds, away_odds):
    """Calculate bookmaker's vig (overround)."""
    home_prob = american_odds_to_probability(home_odds)
    away_prob = american_odds_to_probability(away_odds)
    vig = (home_prob + away_prob - 1.0) * 100
    return vig

# Example: DraftKings Lakers vs. Celtics
home_odds = -150  # Lakers favored
away_odds = +130  # Celtics underdog

home_implied_prob = american_odds_to_probability(home_odds)  # 60.0%
away_implied_prob = american_odds_to_probability(away_odds)  # 43.5%
vig = calculate_market_vig(home_odds, away_odds)             # 3.5%

print(f"Home Implied Prob: {home_implied_prob:.1%}")
print(f"Away Implied Prob: {away_implied_prob:.1%}")
print(f"Bookmaker Vig: {vig:.2f}%")
```

---

## Validation & Testing

### Validator: `validators/phases/phase_0/validate_0_7_odds_api.py`

**Validation Checks:**
1. ✅ Database schema exists (`odds` schema + 5 core tables)
2. ✅ Reference data populated (10+ bookmakers, 9+ market types)
3. ✅ Data freshness (odds updated within last 24 hours)
4. ✅ Data completeness (games have odds from 3+ bookmakers)
5. ✅ Data quality (valid price ranges, no nulls in required fields)
6. ✅ Integration test (can query odds for upcoming games)

**Run Validator:**
```bash
python validators/phases/phase_0/validate_0_7_odds_api.py
```

### Tests: `tests/phases/phase_0/test_0_7_odds_api.py`

**Test Coverage:**
1. Database connection (using `rds_connection` fixture)
2. Table existence and schema validation
3. Data presence (row counts, date ranges)
4. Odds calculation logic (implied probabilities, vig)
5. Bookmaker coverage (DraftKings, FanDuel, BetMGM)
6. Market type coverage (spreads, moneylines, totals)
7. Integration queries (model predictions vs. market odds)

**Run Tests:**
```bash
pytest tests/phases/phase_0/test_0_7_odds_api.py -v
```

---

## Operational Notes

### odds-api Scraper Management

**Location:** `/Users/ryanranft/odds-api/`

**Start Scraper:**
```bash
cd /Users/ryanranft/odds-api
source venv/bin/activate
python scripts/run_scraper.py --continuous
```

**Check Status:**
```bash
# View logs
tail -f /Users/ryanranft/odds-api/logs/scraper.log

# Check quota usage
python scripts/check_quota.py

# View recent collections
python scripts/view_recent_data.py
```

**Monitor Performance:**
- Prometheus metrics: http://localhost:8000/metrics
- Grafana dashboard: Import `dashboards/odds_scraper_dashboard.json`

### Cost Summary

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| **The Odds API** | ~$100 | 20K credits plan (recommended) |
| **RDS Storage** | +$0.23 | ~2 GB odds data |
| **Total** | **~$100.23/month** | Shared RDS, API cost only new expense |

**API Quota Optimization:**
- Use featured markets for distant games (saves credits)
- Increase frequency as game time approaches
- Collect comprehensive data 2 hours before tip-off
- Monitor quota usage with `odds.api_quota_tracking` table

---

## Use Cases

### 1. Value Betting Identification
Compare ML model predictions against betting market consensus to find mispriced lines

### 2. Line Shopping
Find best odds across multiple sportsbooks for optimal bet placement

### 3. Line Movement Analysis
Track how odds change over time to understand market sentiment and sharp money

### 4. Closing Line Value (CLV)
Measure betting strategy quality by comparing bet odds to closing line

### 5. Model Calibration
Validate ML model probability estimates against market-implied probabilities

### 6. Arbitrage Detection
Identify risk-free arbitrage opportunities across bookmakers (rare but possible)

---

## Future Enhancements

### Phase 1: Player Props Integration
- Expand to player prop markets (points, rebounds, assists)
- Individual player prop predictions vs. market
- Correlation analysis (player props affect game totals)

### Phase 2: Live Betting Integration
- Real-time in-game odds collection (30-second intervals)
- Live model predictions vs. live betting lines
- In-game betting strategy validation

### Phase 3: Historical Odds Analysis
- Backtest betting strategies using historical odds
- Calculate ROI, Sharpe ratio, maximum drawdown
- Identify profitable betting patterns

### Phase 4: Automated Betting
- API integration with sportsbooks for bet placement
- Kelly Criterion position sizing
- Automated value betting execution
- Risk management and bankroll tracking

---

## Related Documentation

### This Project (nba-simulator-aws)
- [Phase 0: Data Collection](../PHASE_0_INDEX.md)
- [Phase 5: Machine Learning Models](../../phase_5/5.0_machine_learning_models.md)
- [Phase 7: Betting Odds Integration](../../phase_7/7.0000_betting_odds_integration.md)

### Separate Project (odds-api)
- [odds-api README](file:///Users/ryanranft/odds-api/README.md)
- [Autonomous System Guide](file:///Users/ryanranft/odds-api/docs/guides/AUTONOMOUS_SYSTEM_GUIDE.md)
- [20K Quota Management](file:///Users/ryanranft/odds-api/docs/guides/20K_QUOTA_GUIDE.md)
- [Database Integration](file:///Users/ryanranft/odds-api/docs/reference/DATABASE_INTEGRATION.md)

### Betting Strategy
- [Closing Line Value](https://www.pinnacle.com/en/betting-articles/Betting-Strategy/closing-line-value-betting/9FLB9VJZJZ4BFMPQ)
- [Kelly Criterion](https://www.investopedia.com/articles/trading/04/091504.asp)
- [Expected Value Betting](https://help.smarkets.com/hc/en-gb/articles/214058369-What-is-expected-value-and-expected-value-betting-)

---

## Navigation

**Return to:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
**Previous:** [0.4: Basketball Reference](../0.4_basketball_reference/README.md)
**Next:** [0.8: Security Implementation](../0.8_security_implementation/README.md)

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Integration Partner:** [odds-api scraper](https://github.com/ryanranft/odds-api)
**Status:** ✅ Complete - Autonomous odds collection operational