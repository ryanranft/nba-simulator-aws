# 0.7: Odds API Data

**Sub-Phase:** 0.7 (Data Collection - Betting Odds)
**Parent Phase:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Status:** 🔵 PLANNED
**Priority:** ⭐ MEDIUM
**Data Source:** The Odds API + Local odds-api Repository

---

## Overview

Integration of historical and real-time betting odds from The Odds API and local odds-api repository data. This provides actual sportsbook lines (spreads, moneylines, over/under) to complement ML predictions and enable betting strategy validation.

**Planned Capabilities:**
- Historical odds data from local repository
- Real-time odds from The Odds API
- 20+ sportsbooks coverage
- Integration with prediction system
- Cost-efficient API usage

---

## Data Sources

### 1. Local odds-api Repository

**Location:** `/Users/ryanranft/odds-api/`
**Status:** Available but not yet documented
**Content:** Historical betting odds data

**To be investigated:**
- File formats and structure
- Date range coverage
- Sportsbooks included
- Update frequency
- Data quality metrics

### 2. The Odds API (Real-time)

**Website:** https://the-odds-api.com/
**Free Tier:** 500 requests/month
**Cost:** $0.01-0.05 per request above free tier
**Response Time:** ~200-500ms
**Update Frequency:** Every 5-10 minutes

**Coverage:**
- Pre-game odds (spreads, moneylines, totals)
- Live odds (real-time during games)
- 20+ sportsbooks (DraftKings, FanDuel, BetMGM, etc.)
- Historical odds (via paid tier)

---

## Planned Data Coverage

### Temporal Coverage
- **Historical:** Data from local repository (date range TBD)
- **Real-time:** Current season onwards
- **Future:** Daily updates during NBA season

### Odds Types

| Market Type | Description | Use Case |
|-------------|-------------|----------|
| **Spreads** | Point spread (e.g., -5.5, +5.5) | Win margin predictions |
| **Moneylines** | Win probability odds (e.g., -150, +130) | Straight win predictions |
| **Totals** | Over/Under (e.g., 220.5 points) | Scoring predictions |
| **Live Odds** | In-game betting lines | Real-time model validation |

---

## Planned Schema

### Database Table: `betting_odds`

```sql
CREATE TABLE IF NOT EXISTS betting_odds (
    -- Primary Key
    odds_id SERIAL PRIMARY KEY,

    -- Game Reference
    game_id VARCHAR(20) NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    game_date DATE NOT NULL,

    -- Odds Metadata
    bookmaker VARCHAR(50) NOT NULL,  -- e.g., 'draftkings', 'fanduel'
    market VARCHAR(20) NOT NULL,     -- 'spreads', 'h2h' (moneyline), 'totals'
    last_update TIMESTAMP NOT NULL,  -- When odds were last updated by bookmaker

    -- Home Team Odds
    home_team VARCHAR(5),
    home_team_price INTEGER,         -- Moneyline odds (e.g., -110, +150)
    home_team_point DECIMAL(4,1),    -- Spread (e.g., -5.5) or total point

    -- Away Team Odds
    away_team VARCHAR(5),
    away_team_price INTEGER,         -- Moneyline odds
    away_team_point DECIMAL(4,1),    -- Spread (e.g., +5.5) or total point

    -- Over/Under (for totals market)
    over_price INTEGER,              -- Over odds (e.g., -110)
    over_point DECIMAL(4,1),         -- Total line (e.g., 220.5)
    under_price INTEGER,             -- Under odds (e.g., -110)
    under_point DECIMAL(4,1),        -- Total line (same as over_point)

    -- Metadata
    source VARCHAR(20),              -- 'odds_api' or 'local_repo'
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_latest BOOLEAN DEFAULT TRUE,

    -- Constraints
    CONSTRAINT unique_odds UNIQUE (game_id, bookmaker, market, last_update)
);

-- Indexes for common queries
CREATE INDEX idx_odds_game ON betting_odds(game_id);
CREATE INDEX idx_odds_date ON betting_odds(game_date);
CREATE INDEX idx_odds_bookmaker ON betting_odds(bookmaker);
CREATE INDEX idx_odds_latest ON betting_odds(is_latest) WHERE is_latest = TRUE;
```

---

## Planned Implementation

### Phase 1: Local Data Discovery (2 hours)

**Investigate `/Users/ryanranft/odds-api/` repository:**

```bash
# Explore repository structure
cd /Users/ryanranft/odds-api
find . -type f -name "*.json" -o -name "*.csv" -o -name "*.parquet" | head -20

# Check file sizes and counts
du -sh * | sort -h

# Sample data structure
head -100 [first_data_file]
```

**Document:**
- File formats
- Date range coverage
- Sportsbooks included
- Data schema
- Quality assessment

### Phase 2: S3 Upload (1 hour)

```bash
# Upload historical odds data to S3
aws s3 sync /Users/ryanranft/odds-api/ \
  s3://nba-sim-raw-data-lake/odds_api/ \
  --exclude "*" \
  --include "*.json" \
  --include "*.csv" \
  --include "*.parquet"
```

### Phase 3: Database Integration (4-6 hours)

**Script:** `scripts/db/load_odds_to_rds.py`

```python
import pandas as pd
import psycopg2
import json
import boto3
from datetime import datetime

def load_historical_odds_to_rds():
    """Load historical odds data from S3 to RDS"""

    s3 = boto3.client('s3')
    conn = psycopg2.connect(...)

    # Create table
    create_odds_table(conn)

    # Load historical data
    bucket = 'nba-sim-raw-data-lake'
    prefix = 'odds_api/'

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            # Download and parse
            response = s3.get_object(Bucket=bucket, Key=obj['Key'])
            data = json.loads(response['Body'].read())

            # Transform to schema
            odds_records = transform_odds_data(data)

            # Bulk insert
            insert_odds_batch(conn, odds_records)

    conn.commit()
    print("Historical odds loaded successfully")

def transform_odds_data(raw_data):
    """Transform raw odds data to database schema"""
    records = []

    for game in raw_data.get('games', []):
        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                record = {
                    'game_id': game['id'],
                    'game_date': game['commence_time'][:10],
                    'bookmaker': bookmaker['key'],
                    'market': market['key'],
                    'last_update': bookmaker['last_update'],
                    'source': 'local_repo'
                }

                # Parse outcomes based on market type
                if market['key'] == 'h2h':  # Moneyline
                    for outcome in market['outcomes']:
                        if outcome['name'] == game['home_team']:
                            record['home_team'] = outcome['name']
                            record['home_team_price'] = outcome['price']
                        else:
                            record['away_team'] = outcome['name']
                            record['away_team_price'] = outcome['price']

                elif market['key'] == 'spreads':
                    for outcome in market['outcomes']:
                        if outcome['name'] == game['home_team']:
                            record['home_team_point'] = outcome['point']
                            record['home_team_price'] = outcome['price']
                        else:
                            record['away_team_point'] = outcome['point']
                            record['away_team_price'] = outcome['price']

                elif market['key'] == 'totals':
                    for outcome in market['outcomes']:
                        if outcome['name'] == 'Over':
                            record['over_point'] = outcome['point']
                            record['over_price'] = outcome['price']
                        else:
                            record['under_point'] = outcome['point']
                            record['under_price'] = outcome['price']

                records.append(record)

    return records
```

### Phase 4: Real-time API Integration (3-4 hours)

**Script:** `scripts/etl/fetch_realtime_odds.py`

```python
import requests
import os
from datetime import datetime, timedelta

class OddsAPIClient:
    """Client for The Odds API"""

    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.sport = 'basketball_nba'

    def get_upcoming_games_odds(self):
        """Fetch odds for upcoming NBA games"""

        url = f"{self.base_url}/sports/{self.sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        # Check remaining requests
        remaining = response.headers.get('x-requests-remaining')
        used = response.headers.get('x-requests-used')
        print(f"API Usage: {used} used, {remaining} remaining")

        return response.json()

    def save_to_database(self, odds_data):
        """Save fetched odds to database"""
        conn = psycopg2.connect(...)

        for game in odds_data:
            # Mark old odds as not latest
            mark_odds_not_latest(conn, game['id'])

            # Insert new odds
            transformed = transform_odds_data([game])
            insert_odds_batch(conn, transformed)

        conn.commit()

# Daily job to fetch odds
def daily_odds_fetch():
    """Fetch odds once per day during NBA season"""
    client = OddsAPIClient()
    odds = client.get_upcoming_games_odds()
    client.save_to_database(odds)
    print(f"Fetched odds for {len(odds)} games")

# Usage: Run via cron during NBA season
# 0 10 * * * cd /Users/ryanranft/nba-simulator-aws && python scripts/etl/fetch_realtime_odds.py
```

---

## Integration with Predictions

### Compare ML Predictions vs Market

```python
def compare_predictions_vs_market():
    """Compare ML model predictions with betting market odds"""

    conn = psycopg2.connect(...)

    query = """
        WITH predictions AS (
            SELECT
                game_id,
                predicted_winner,
                win_probability,
                predicted_spread
            FROM ml_predictions
            WHERE game_date = CURRENT_DATE
        ),
        consensus_odds AS (
            SELECT
                game_id,
                AVG(CASE
                    WHEN home_team_point < 0 THEN home_team_point
                    ELSE -away_team_point
                END) as avg_spread,
                AVG(home_team_price) as avg_moneyline
            FROM betting_odds
            WHERE game_date = CURRENT_DATE
              AND market = 'spreads'
              AND is_latest = TRUE
            GROUP BY game_id
        )
        SELECT
            p.game_id,
            p.predicted_winner,
            p.predicted_spread,
            c.avg_spread as market_spread,
            p.predicted_spread - c.avg_spread as edge
        FROM predictions p
        JOIN consensus_odds c ON p.game_id = c.game_id
        WHERE ABS(p.predicted_spread - c.avg_spread) > 3.0
        ORDER BY ABS(edge) DESC;
    """

    opportunities = pd.read_sql(query, conn)
    print(f"Found {len(opportunities)} games with 3+ point edge")
    return opportunities
```

### Betting Strategy Validation

```python
def backtest_betting_strategy(start_date, end_date):
    """Backtest betting strategy using historical odds and outcomes"""

    query = """
        WITH game_outcomes AS (
            SELECT
                g.game_id,
                g.game_date,
                g.home_team,
                g.away_team,
                g.home_score - g.away_score as actual_margin
            FROM games g
            WHERE g.game_date BETWEEN %s AND %s
        ),
        odds_at_open AS (
            SELECT DISTINCT ON (game_id, bookmaker)
                game_id,
                bookmaker,
                home_team_point as spread,
                home_team_price as odds
            FROM betting_odds
            WHERE market = 'spreads'
              AND game_date BETWEEN %s AND %s
            ORDER BY game_id, bookmaker, last_update ASC
        )
        SELECT
            o.game_id,
            go.game_date,
            o.spread,
            go.actual_margin,
            CASE
                WHEN go.actual_margin + o.spread > 0 THEN 'WIN'
                WHEN go.actual_margin + o.spread < 0 THEN 'LOSS'
                ELSE 'PUSH'
            END as bet_result,
            o.odds
        FROM game_outcomes go
        JOIN odds_at_open o ON go.game_id = o.game_id
        WHERE o.bookmaker = 'draftkings';
    """

    results = pd.read_sql(query, conn, params=(start_date, end_date,
                                                 start_date, end_date))

    # Calculate ROI
    wins = (results['bet_result'] == 'WIN').sum()
    losses = (results['bet_result'] == 'LOSS').sum()
    win_rate = wins / (wins + losses)

    print(f"Win Rate: {win_rate:.1%}")
    print(f"Record: {wins}-{losses}")

    return results
```

---

## Cost Projections

### The Odds API Costs

**Free Tier:** 500 requests/month

**Usage Scenarios:**

| Scenario | Daily Requests | Monthly | Annual Cost |
|----------|----------------|---------|-------------|
| Once daily | 1 | 30 | **$0** (free tier) |
| Morning + evening | 2 | 60 | **$0** (free tier) |
| Every 6 hours | 4 | 120 | **$0** (free tier) |
| Hourly (season) | 24 | 720 | ~$26 |

**Recommendation:** Fetch once daily during season = **$0/month**

### Storage Costs

- **S3 Storage:** ~1 GB × $0.023/GB = **$0.02/month**
- **RDS Storage:** ~2 GB × $0.115/GB = **$0.23/month**
- **Total:** **$0.25/month**

---

## Use Cases

### 1. Model Validation
Compare ML predictions against market consensus to validate model accuracy

### 2. Value Betting
Identify games where model disagrees significantly with market odds

### 3. Line Movement Analysis
Track how odds change over time to understand market sentiment

### 4. Bookmaker Comparison
Compare odds across sportsbooks to find best lines

### 5. Historical Performance
Backtest betting strategies using historical odds and outcomes

---

## Related Documentation

- **[Phase 7: Betting Odds Integration](../../phase_7/7.0_betting_odds_integration.md)** - Detailed implementation guide
- **[PREDICTIONS_README.md](../../../PREDICTIONS_README.md)** - ML prediction system
- **[DATA_CATALOG.md](../../../DATA_CATALOG.md)** - All data sources

---

## Next Steps

1. **Investigate local repository:** Document `/Users/ryanranft/odds-api/` structure
2. **Upload to S3:** Transfer historical odds data
3. **Create database schema:** Implement `betting_odds` table
4. **Load historical data:** ETL pipeline for local data
5. **Setup API integration:** Daily odds fetching
6. **Build comparison tools:** ML predictions vs market odds

---

## Navigation

**Return to:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Previous:** [0.6: ESPN Additional Scraping](../0.6_espn_additional_scraping/)
**Next:** [0.8: Security Implementation](../0.8_security_implementation/README.md)

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Data Sources:**
- Local: `/Users/ryanranft/odds-api/`
- API: The Odds API (https://the-odds-api.com/)
**Status:** 🔵 Planned - Ready for implementation

