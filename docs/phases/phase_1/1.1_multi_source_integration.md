# Phase 1: Multi-Source Data Integration - Detailed Implementation Plan

**Created:** October 6, 2025
**Purpose:** Step-by-step plan for integrating all 5 data sources
**Prerequisites:** Phase 0 complete, critical foundations in place
**Estimated Time:** 12-16 hours
**Estimated Cost:** $0-10/month

---

## Overview

This plan builds on the critical foundations established today:
- ✅ ID mapping expanded for all 5 sources
- ✅ Deduplication rules documented
- ✅ Field mapping schema defined

Now we'll implement the multi-source data collection and integration pipeline.

---

## Table of Contents

1. [Implementation Phases](#implementation-phases)
2. [Sub-Phase 1.7: NBA.com Stats Integration](#sub-phase-17-nbacom-stats-integration)
3. [Sub-Phase 1.8: Kaggle Database Integration](#sub-phase-18-kaggle-database-integration)
4. [Sub-Phase 1.9: SportsDataverse Integration](#sub-phase-19-sportsdataverse-integration)
5. [Sub-Phase 1.10: Basketball Reference Integration](#sub-phase-110-basketball-reference-integration)
6. [Sub-Phase 1.11: Multi-Source Deduplication Pipeline](#sub-phase-111-multi-source-deduplication-pipeline)
7. [Sub-Phase 1.12: Data Quality Dashboard](#sub-phase-112-data-quality-dashboard)
8. [Success Criteria](#success-criteria)

---

## Implementation Phases

### Phase Overview

| Sub-Phase | Task | Time | Priority | Dependencies |
|-----------|------|------|----------|--------------|
| 1.7 | NBA.com Stats Integration | 3 hrs | HIGH | Foundation docs |
| 1.8 | Kaggle Database Integration | 2 hrs | MEDIUM | Foundation docs |
| 1.9 | SportsDataverse Integration | 1 hr | LOW | Foundation docs |
| 1.10 | Basketball Reference Integration | 4 hrs | MEDIUM | Foundation docs |
| 1.11 | Multi-Source Deduplication | 3 hrs | HIGH | All sources integrated |
| 1.12 | Data Quality Dashboard | 2 hrs | MEDIUM | Deduplication complete |

**Total Estimated Time:** 15 hours

---

## Sub-Phase 1.7: NBA.com Stats Integration

**Status:** ⏸️ PENDING
**Time Estimate:** 3 hours
**Purpose:** Integrate NBA.com Stats API as primary verification source

### Implementation Steps

#### Step 1: Create NBA.com Stats Scraper (1 hour)

**Script:** `scripts/etl/scrape_nba_stats_api.py`

```python
#!/usr/bin/env python3
"""
NBA.com Stats API Scraper
Purpose: Fetch game data from official NBA Stats API
Coverage: 1996-present
"""

import requests
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

class NBAStatsAPIClient:
    BASE_URL = "https://stats.nba.com/stats"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://stats.nba.com/"
    }
    RATE_LIMIT_DELAY = 0.6  # 600ms between requests

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_scoreboard(self, game_date: str):
        """
        Fetch scoreboard for a given date

        Args:
            game_date: YYYY-MM-DD format
        """
        url = f"{self.BASE_URL}/scoreboardV2"
        params = {"GameDate": game_date}

        response = requests.get(url, headers=self.HEADERS, params=params)
        time.sleep(self.RATE_LIMIT_DELAY)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching {game_date}: {response.status_code}")
            return None

    def fetch_date_range(self, start_date: str, end_date: str):
        """
        Fetch all games in date range
        """
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            print(f"Fetching {date_str}...")

            data = self.fetch_scoreboard(date_str)
            if data:
                # Save to JSON
                output_file = self.output_dir / f"nba_stats_{date_str}.json"
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)

            current += timedelta(days=1)

if __name__ == "__main__":
    # Example: Fetch October 2024
    client = NBAStatsAPIClient(output_dir="data/nba_stats_raw")
    client.fetch_date_range("2024-10-01", "2024-10-31")
```

**Tasks:**
- [ ] Create script with rate limiting
- [ ] Test API access (verify no API key needed)
- [ ] Implement date range fetching
- [ ] Add error handling and retry logic
- [ ] Save raw responses to `data/nba_stats_raw/`

#### Step 2: Upload NBA.com Data to S3 (30 min)

```bash
# Create S3 prefix for NBA.com Stats data
aws s3 mb s3://nba-sim-raw-data-lake/nba_stats/

# Upload scraped data
aws s3 sync data/nba_stats_raw/ s3://nba-sim-raw-data-lake/nba_stats/ \
  --exclude "*" --include "*.json"
```

**Tasks:**
- [ ] Create S3 prefix: `s3://nba-sim-raw-data-lake/nba_stats/`
- [ ] Upload raw JSON files
- [ ] Verify upload count matches scraped files

#### Step 3: Create NBA.com Stats Parser (1 hour)

**Script:** `scripts/etl/parse_nba_stats.py`

```python
def parse_nba_stats_scoreboard(raw_json: dict) -> list:
    """
    Parse NBA.com Stats scoreboard response to canonical format

    Returns:
        List of games in canonical schema
    """
    games = []

    # Extract game headers
    game_headers = raw_json['resultSets'][0]  # GameHeader
    line_scores = raw_json['resultSets'][1]   # LineScore

    for row in game_headers['rowSet']:
        game_date = row[0]  # GAME_DATE_EST
        game_id = row[1]    # GAME_ID
        home_team_id = row[6]
        away_team_id = row[7]

        # Find scores from LineScore
        home_score = None
        away_score = None

        for line_row in line_scores['rowSet']:
            if line_row[0] == game_id:  # GAME_ID
                team_id = line_row[1]   # TEAM_ID
                points = line_row[21]   # PTS

                if team_id == home_team_id:
                    home_score = points
                elif team_id == away_team_id:
                    away_score = points

        games.append({
            'game_id': game_id,
            'game_date': game_date,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_score': home_score,
            'away_score': away_score,
            'data_source': 'nba_stats'
        })

    return games
```

**Tasks:**
- [ ] Create parser for NBA.com Stats format
- [ ] Map to canonical schema (use `FIELD_MAPPING_SCHEMA.md`)
- [ ] Handle missing data gracefully
- [ ] Test on sample data

#### Step 4: Run Verification (30 min)

**Update existing script:** `scripts/etl/verify_with_nba_stats.py`

```bash
# Run verification with expanded coverage
python scripts/etl/verify_with_nba_stats.py --sample-size 100
```

**Tasks:**
- [ ] Run verification: ESPN vs NBA.com Stats
- [ ] Generate updated `VERIFICATION_RESULTS.md`
- [ ] Review discrepancies (should be < 5%)
- [ ] Log any conflicts to `data_conflicts` table

**Success Criteria:**
- [ ] NBA.com Stats data successfully scraped for sample date range
- [ ] Data uploaded to S3 under `nba_stats/` prefix
- [ ] Parser converts NBA.com format to canonical schema
- [ ] Verification shows ≥ 95% score accuracy

---

## Sub-Phase 1.8: Kaggle Database Integration

**Status:** ⏸️ PENDING
**Time Estimate:** 2 hours
**Purpose:** Integrate Kaggle Basketball Database for historical data (pre-1999)

### Implementation Steps

#### Step 1: Download Kaggle Database (30 min)

**Script:** `scripts/etl/download_kaggle_database.py`

```python
#!/usr/bin/env python3
"""
Download Kaggle Basketball Database
Source: https://www.kaggle.com/datasets/wyattowalsh/basketball
"""

import os
from pathlib import Path

def download_kaggle_dataset():
    """
    Download Kaggle basketball database using Kaggle API

    Prerequisites:
    - Kaggle account
    - Kaggle API key: ~/.kaggle/kaggle.json
    - kaggle CLI: pip install kaggle
    """
    dataset = "wyattowalsh/basketball"
    output_dir = "data/kaggle_basketball"

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Download using Kaggle CLI
    os.system(f"kaggle datasets download -d {dataset} -p {output_dir} --unzip")

    print(f"Downloaded to {output_dir}")
    print(f"Database file: {output_dir}/basketball.sqlite")

if __name__ == "__main__":
    download_kaggle_dataset()
```

**Tasks:**
- [ ] Install Kaggle CLI: `pip install kaggle`
- [ ] Set up Kaggle API credentials
- [ ] Download basketball.sqlite database
- [ ] Verify database size (~2-5 GB)

#### Step 2: Extract Historical Games (1 hour)

**Script:** `scripts/etl/extract_kaggle_games.py`

```python
import sqlite3
import json
from pathlib import Path

def extract_historical_games(db_path: str, start_year: int = 1946, end_year: int = 1998):
    """
    Extract pre-ESPN games from Kaggle database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query games from 1946-1998 (pre-ESPN coverage)
    query = """
    SELECT
        game_date,
        season_id,
        team_abbreviation_home,
        team_abbreviation_away,
        pts_home,
        pts_away
    FROM game
    WHERE season_id >= ? AND season_id <= ?
    ORDER BY game_date
    """

    cursor.execute(query, (start_year, end_year))
    games = cursor.fetchall()

    # Convert to canonical format
    canonical_games = []
    for row in games:
        canonical_games.append({
            'game_date': row[0],
            'season': row[1],
            'home_team_abbr': row[2],
            'away_team_abbr': row[3],
            'home_score': row[4],
            'away_score': row[5],
            'data_source': 'kaggle'
        })

    conn.close()
    return canonical_games

if __name__ == "__main__":
    games = extract_historical_games("data/kaggle_basketball/basketball.sqlite")

    # Save to JSON (for S3 upload)
    output_file = "data/kaggle_basketball/historical_games_1946_1998.json"
    with open(output_file, 'w') as f:
        json.dump(games, f, indent=2)

    print(f"Extracted {len(games)} historical games")
```

**Tasks:**
- [ ] Query Kaggle database for pre-1999 games
- [ ] Convert to canonical schema
- [ ] Save as JSON for S3 upload
- [ ] Validate data completeness

#### Step 3: Upload to S3 (30 min)

```bash
# Upload Kaggle historical data
aws s3 sync data/kaggle_basketball/ s3://nba-sim-raw-data-lake/kaggle/ \
  --exclude "*" --include "*.json"
```

**Success Criteria:**
- [ ] Kaggle database downloaded successfully
- [ ] Historical games (1946-1998) extracted
- [ ] Data uploaded to S3 under `kaggle/` prefix
- [ ] ~50,000+ historical games available

---

## Sub-Phase 1.9: SportsDataverse Integration

**Status:** ⏸️ PENDING
**Time Estimate:** 1 hour
**Purpose:** Integrate SportsDataverse as testing/validation source

### Implementation Steps

#### Step 1: Install SportsDataverse (15 min)

```bash
# Install Python package
pip install sportsdataverse

# Verify installation
python -c "from sportsdataverse.nba import espn_nba_schedule; print('OK')"
```

#### Step 2: Create SportsDataverse Scraper (30 min)

**Script:** `scripts/etl/scrape_sportsdataverse.py`

```python
from sportsdataverse.nba import espn_nba_schedule, espn_nba_pbp
import json

def fetch_games_via_sportsdataverse(season: int = 2024):
    """
    Fetch games using SportsDataverse wrapper

    Note: This wraps ESPN API, so data format is same as ESPN
    """
    # Get schedule
    schedule = espn_nba_schedule(season=season)

    # Save to JSON
    with open(f'data/sportsdataverse/schedule_{season}.json', 'w') as f:
        json.dump(schedule, f, indent=2)

    return schedule

if __name__ == "__main__":
    games = fetch_games_via_sportsdataverse(2024)
    print(f"Fetched {len(games)} games via SportsDataverse")
```

**Tasks:**
- [ ] Test SportsDataverse API
- [ ] Fetch sample season data
- [ ] Compare with ESPN direct API
- [ ] Document any differences

#### Step 3: Cross-Validation (15 min)

**Script:** `scripts/etl/verify_with_sportsdataverse.py`

```python
def compare_espn_vs_sportsdataverse(game_id: str):
    """
    Verify our ESPN parsing matches SportsDataverse parsing
    """
    # Fetch from our ESPN S3 data
    our_data = fetch_from_s3(f"espn/{game_id}.json")

    # Fetch via SportsDataverse
    sdv_data = espn_nba_pbp(game_id=game_id)

    # Compare key fields
    discrepancies = []

    if our_data['home_score'] != sdv_data['home_score']:
        discrepancies.append(f"Score mismatch: {our_data['home_score']} vs {sdv_data['home_score']}")

    return discrepancies
```

**Success Criteria:**
- [ ] SportsDataverse installed and working
- [ ] Data fetched for sample games
- [ ] Cross-validation shows our ESPN parsing is correct

---

## Sub-Phase 1.10: Basketball Reference Integration

**Status:** ⏸️ PENDING
**Time Estimate:** 4 hours
**Purpose:** Integrate Basketball Reference for advanced stats and historical data

### Implementation Steps

#### Step 1: Create Basketball Reference Scraper (2 hours)

**Script:** `scripts/etl/scrape_basketball_reference.py`

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

class BasketballReferenceScraper:
    BASE_URL = "https://www.basketball-reference.com"
    RATE_LIMIT = 3  # 1 request per 3 seconds (TOS compliance)

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NBA-Simulator-Bot/1.0 (Educational Use)'
        })

    def scrape_game(self, game_date: str, home_team_abbr: str):
        """
        Scrape a single game from Basketball Reference

        Args:
            game_date: YYYY-MM-DD
            home_team_abbr: 3-letter code (lowercase for URL)
        """
        # Construct URL
        date_str = game_date.replace('-', '')
        url = f"{self.BASE_URL}/boxscores/{date_str}0{home_team_abbr.lower()}.html"

        print(f"Scraping: {url}")
        response = self.session.get(url)
        time.sleep(self.RATE_LIMIT)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return None

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract scores from tables
        tables = pd.read_html(response.content)

        # Extract basic box score (usually first table)
        away_stats = tables[0]  # Away team stats
        home_stats = tables[1]  # Home team stats

        return {
            'game_date': game_date,
            'home_team': home_team_abbr,
            'url': url,
            'away_stats': away_stats.to_dict(),
            'home_stats': home_stats.to_dict(),
            'data_source': 'basketball_reference'
        }

    def scrape_date_range(self, start_date: str, end_date: str, team_abbr: str):
        """
        Scrape all games for a team in date range
        """
        # Implementation here
        pass

if __name__ == "__main__":
    scraper = BasketballReferenceScraper()

    # Example: Lakers vs Warriors, Dec 25, 2024
    game = scraper.scrape_game("2024-12-25", "LAL")
    print(game)
```

**Important Considerations:**
- **Rate Limiting:** Strict 1 req/3 sec (TOS compliance)
- **Robots.txt:** Check and respect rules
- **User-Agent:** Identify bot clearly
- **Caching:** Store responses to avoid re-scraping

**Tasks:**
- [ ] Implement scraper with rate limiting
- [ ] Test on sample games
- [ ] Parse HTML tables to extract stats
- [ ] Handle errors gracefully (404s, timeouts)

#### Step 2: Extract Advanced Statistics (1 hour)

**Basketball Reference provides:**
- Four Factors (eFG%, TOV%, ORB%, FT/FGA)
- Player advanced metrics (TS%, eFG%, USG%)
- Team ratings (ORtg, DRtg, Pace)

```python
def extract_advanced_stats(soup):
    """
    Extract advanced statistics from Basketball Reference page
    """
    # Find Four Factors table
    four_factors = soup.find('table', {'id': 'four_factors'})

    if four_factors:
        df = pd.read_html(str(four_factors))[0]
        return {
            'pace': df['Pace'].values[0],
            'efg_pct': df['eFG%'].values[0],
            'tov_pct': df['TOV%'].values[0],
            # ...
        }
```

**Tasks:**
- [ ] Identify advanced stat tables
- [ ] Parse Four Factors
- [ ] Parse player advanced stats
- [ ] Map to canonical schema

#### Step 3: Upload to S3 (30 min)

```bash
# Upload Basketball Reference data
aws s3 sync data/basketball_reference/ s3://nba-sim-raw-data-lake/bref/ \
  --exclude "*" --include "*.json"
```

#### Step 4: Compliance & Ethics (30 min)

**Basketball Reference Terms of Service:**
- Academic/personal use: ✅ OK
- Commercial scraping: ❌ Requires permission
- Rate limits: 1 req/3 sec minimum
- Attribution: Required

**Tasks:**
- [ ] Review and document TOS compliance
- [ ] Add attribution in documentation
- [ ] Implement respectful rate limiting
- [ ] Cache aggressively to minimize requests

**Success Criteria:**
- [ ] Basketball Reference scraper working with TOS compliance
- [ ] Advanced statistics extracted successfully
- [ ] Data uploaded to S3 under `bref/` prefix
- [ ] Rate limiting prevents server overload

---

## Sub-Phase 1.11: Multi-Source Deduplication Pipeline

**Status:** ⏸️ PENDING
**Time Estimate:** 3 hours
**Purpose:** Implement deduplication and conflict resolution

### Implementation Steps

#### Step 1: Create Deduplication Engine (2 hours)

**Script:** `scripts/etl/deduplicate_multi_source.py`

```python
from typing import List, Dict
from datetime import datetime

class MultiSourceDeduplicator:
    """
    Deduplicate and merge games from 5 sources
    """

    SOURCE_PRIORITY = ['nba_stats', 'bref', 'espn', 'kaggle', 'sportsdataverse']

    def __init__(self, db_connection):
        self.db = db_connection

    def find_duplicates(self, game_date: str, home_team: str, away_team: str) -> List[Dict]:
        """
        Find all records matching composite key (date + teams)
        """
        query = """
        SELECT * FROM games_staging
        WHERE game_date = %s
        AND home_team_abbr = %s
        AND away_team_abbr = %s
        """

        return self.db.execute(query, (game_date, home_team, away_team))

    def merge_best_field_wins(self, duplicates: List[Dict]) -> Dict:
        """
        Merge duplicates using "best field wins" strategy
        (per DATA_DEDUPLICATION_RULES.md)
        """
        merged = {
            'game_date': duplicates[0]['game_date'],
            'home_team_abbr': duplicates[0]['home_team_abbr'],
            'away_team_abbr': duplicates[0]['away_team_abbr'],
            'data_sources': {},
            'confidence_score': 0
        }

        # Scores: NBA.com Stats > ESPN > Kaggle
        score_priority = ['nba_stats', 'espn', 'kaggle']
        for source in score_priority:
            rec = self._find_source(duplicates, source)
            if rec and rec.get('home_score'):
                merged['home_score'] = rec['home_score']
                merged['away_score'] = rec['away_score']
                merged['data_sources']['scores'] = source
                break

        # Play-by-play: ESPN > NBA.com Stats
        pbp_priority = ['espn', 'nba_stats']
        for source in pbp_priority:
            rec = self._find_source(duplicates, source)
            if rec and rec.get('pbp_data'):
                merged['pbp_data'] = rec['pbp_data']
                merged['data_sources']['pbp'] = source
                break

        # Advanced stats: Basketball Reference > NBA.com
        adv_priority = ['bref', 'nba_stats']
        for source in adv_priority:
            rec = self._find_source(duplicates, source)
            if rec and rec.get('advanced_stats'):
                merged['advanced_stats'] = rec['advanced_stats']
                merged['data_sources']['advanced'] = source
                break

        # Calculate confidence
        merged['confidence_score'] = self._calculate_confidence(duplicates, merged)
        merged['has_conflicts'] = self._detect_conflicts(duplicates)

        return merged

    def _calculate_confidence(self, duplicates: List[Dict], merged: Dict) -> float:
        """
        Calculate confidence score (0.0-1.0)
        per DATA_DEDUPLICATION_RULES.md
        """
        # Source agreement (40%)
        agreement = self._count_agreeing_sources(duplicates) / len(duplicates)
        score = 0.4 * agreement

        # Source quality (40%)
        primary = merged['data_sources'].get('scores', 'unknown')
        if primary in ['nba_stats', 'bref']:
            score += 0.4
        elif primary == 'espn':
            score += 0.3
        else:
            score += 0.2

        # Completeness (20%)
        completeness = len([v for v in merged.values() if v is not None]) / 10
        score += 0.2 * completeness

        return round(score, 2)

    def _detect_conflicts(self, duplicates: List[Dict]) -> bool:
        """
        Check if sources disagree on scores
        """
        scores = set()
        for dup in duplicates:
            if dup.get('home_score'):
                scores.add((dup['home_score'], dup['away_score']))

        return len(scores) > 1  # Conflict if multiple different scores

    def _find_source(self, duplicates: List[Dict], source_name: str) -> Dict:
        """Find record from specific source"""
        for dup in duplicates:
            if dup.get('data_source') == source_name:
                return dup
        return None

if __name__ == "__main__":
    # Example usage
    import psycopg2

    conn = psycopg2.connect(
        host="nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com",
        database="nba_simulator",
        user="postgres",
        password="..."
    )

    dedup = MultiSourceDeduplicator(conn)

    # Find and merge duplicates for a specific game
    duplicates = dedup.find_duplicates('2024-12-25', 'LAL', 'GSW')
    merged = dedup.merge_best_field_wins(duplicates)

    print(f"Merged game: {merged}")
    print(f"Confidence: {merged['confidence_score']}")
    print(f"Sources used: {merged['data_sources']}")
```

**Tasks:**
- [ ] Implement duplicate detection
- [ ] Implement "best field wins" merging
- [ ] Calculate confidence scores
- [ ] Log conflicts to `data_conflicts` table

#### Step 2: Create Conflict Logging (1 hour)

**Database Schema:**
```sql
-- Create conflict logging table
CREATE TABLE data_conflicts (
    conflict_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50),
    game_date DATE,
    field_name VARCHAR(50),

    espn_value TEXT,
    nba_stats_value TEXT,
    kaggle_value TEXT,
    bref_value TEXT,
    sportsdataverse_value TEXT,

    resolved_value TEXT,
    resolution_rule VARCHAR(100),
    confidence VARCHAR(10),

    requires_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tasks:**
- [ ] Create conflict table in RDS
- [ ] Log all conflicts during deduplication
- [ ] Flag high-severity conflicts (> 10% difference)
- [ ] Generate daily conflict report

**Success Criteria:**
- [ ] Deduplication pipeline successfully merges multi-source data
- [ ] Confidence scores calculated for all merged games
- [ ] Conflicts logged and categorized
- [ ] ≥ 95% of games have confidence score ≥ 0.75

---

## Sub-Phase 1.12: Data Quality Dashboard

**Status:** ⏸️ PENDING
**Time Estimate:** 2 hours
**Purpose:** Visualize data quality metrics and source coverage

### Implementation Steps

#### Step 1: Generate Quality Metrics (1 hour)

**Script:** `scripts/analytics/generate_quality_report.py`

```python
def generate_quality_report():
    """
    Generate comprehensive data quality report
    """
    report = {
        'generated_at': datetime.now().isoformat(),
        'sources': {}
    }

    # Per-source metrics
    for source in ['espn', 'nba_stats', 'kaggle', 'bref', 'sportsdataverse']:
        report['sources'][source] = {
            'total_games': count_games(source),
            'date_range': get_date_range(source),
            'completeness_pct': calculate_completeness(source),
            'avg_confidence': get_avg_confidence(source),
            'conflicts': count_conflicts(source)
        }

    # Overall metrics
    report['overall'] = {
        'total_unique_games': count_unique_games(),
        'total_duplicates_resolved': count_duplicates(),
        'avg_confidence': get_overall_confidence(),
        'coverage_by_era': get_coverage_by_era()
    }

    # Save report
    with open('docs/MULTI_SOURCE_QUALITY_REPORT.md', 'w') as f:
        f.write(format_report_markdown(report))

    return report
```

**Tasks:**
- [ ] Calculate per-source metrics
- [ ] Calculate overall data quality score
- [ ] Generate coverage by era (1946-1999, 1999-present)
- [ ] Create markdown report

#### Step 2: Create Visualization Dashboard (1 hour)

**Optional: Simple HTML dashboard**

```html
<!DOCTYPE html>
<html>
<head>
    <title>NBA Data Quality Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>Multi-Source Data Quality Dashboard</h1>

    <canvas id="sourceCompleteness"></canvas>
    <canvas id="confidenceDistribution"></canvas>
    <canvas id="coverageByEra"></canvas>

    <script>
        // Load quality report JSON
        fetch('MULTI_SOURCE_QUALITY_REPORT.json')
            .then(res => res.json())
            .then(data => {
                // Chart 1: Source completeness
                new Chart(document.getElementById('sourceCompleteness'), {
                    type: 'bar',
                    data: {
                        labels: ['ESPN', 'NBA.com', 'Kaggle', 'BRef', 'SportsDataverse'],
                        datasets: [{
                            label: 'Completeness %',
                            data: [/* from report */]
                        }]
                    }
                });

                // Chart 2: Confidence score distribution
                // Chart 3: Coverage by era
            });
    </script>
</body>
</html>
```

**Tasks:**
- [ ] Create simple HTML dashboard
- [ ] Add charts for key metrics
- [ ] Host locally or on S3 static site

**Success Criteria:**
- [ ] Quality report generated automatically
- [ ] Dashboard shows key metrics at a glance
- [ ] Coverage gaps clearly visualized

---

## Success Criteria

### Overall Success Criteria

- [ ] All 5 sources integrated and uploading to S3
- [ ] Deduplication pipeline successfully merging data
- [ ] Conflict resolution working per documented rules
- [ ] Data quality metrics tracked and reported
- [ ] ≥ 95% of games have confidence score ≥ 0.75
- [ ] Historical coverage (1946-1999) filled via Kaggle/BRef
- [ ] Modern coverage (1999-present) verified via NBA.com Stats
- [ ] Zero high-severity unresolved conflicts

### Quality Metrics Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Score Accuracy** | ≥ 99% | TBD | ⏸️ |
| **Date Accuracy** | ≥ 99% | TBD | ⏸️ |
| **Data Completeness** | ≥ 95% | TBD | ⏸️ |
| **Discrepancy Rate** | ≤ 5% | TBD | ⏸️ |
| **Avg Confidence Score** | ≥ 0.80 | TBD | ⏸️ |
| **Historical Coverage (pre-1999)** | ≥ 80% | TBD | ⏸️ |

---

## Cost Summary

| Item | Cost/Month | Notes |
|------|------------|-------|
| **NBA.com Stats API** | $0 | Free, rate-limited |
| **Kaggle Database** | $0 | One-time download |
| **Basketball Reference** | $0 | Free, TOS compliance required |
| **SportsDataverse** | $0 | Open-source |
| **S3 Storage (additional)** | ~$2 | ~50GB additional data |
| **Total** | **~$2/month** | Minimal cost increase |

---

## Next Steps

After completing Phase 1 Multi-Source Integration:

1. **Update PROGRESS.md** - Mark Phase 1 complete
2. **Proceed to Phase 2** - ETL extraction with multi-source data
3. **Enhance database schema** - Add data lineage columns
4. **Set up automated monitoring** - Daily quality reports

---

## Related Documentation

- **[DATA_SOURCE_MAPPING.md](../DATA_SOURCE_MAPPING.md)** - ID mapping reference
- **[DATA_DEDUPLICATION_RULES.md](../DATA_DEDUPLICATION_RULES.md)** - Conflict resolution rules
- **[FIELD_MAPPING_SCHEMA.md](../FIELD_MAPPING_SCHEMA.md)** - Field transformation guide
- **[DATA_SOURCES.md](../DATA_SOURCES.md)** - Source overview

---

*Created: October 6, 2025*
*Next Review: After implementation begins*