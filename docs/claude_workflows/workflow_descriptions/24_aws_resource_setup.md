## ☁️ AWS Resource Setup Workflows

**Phase-specific workflows for provisioning AWS resources**

### General AWS Resource Creation Pattern

**Follow this pattern for ALL AWS resource creation:**

1. **Review PROGRESS.md** for resource specifications
2. **Estimate monthly cost** (see Cost Management Workflows)
3. **Warn user with cost estimate** and get explicit approval
4. **Check prerequisites** (VPC, security groups, IAM roles)
5. **Create resource** via AWS Console or CLI
6. **Verify creation** (describe command, check status)
7. **Test connectivity** (if applicable)
8. **Document endpoint/ARN** in PROGRESS.md
9. **Update cost actuals** in PROGRESS.md
10. **Run `make sync-progress`** to verify documentation matches reality

### Phase 2: Year-Based ETL Pipeline Workflow (Phase 2.2)

**Purpose:** Process 146K+ S3 files efficiently using year-based partitioning and crawlers

**Challenge:** Traditional single-crawler approach overwhelms Glue with 146K files. Solution: Partition by year (33 years), create year-specific crawlers, process incrementally.

**Complete pipeline:** 6 scripts working in sequence

---

#### 📋 Local ETL Alternative: Schedule Data Extraction (extract_schedule_local.py)

**Script location:** `scripts/etl/extract_schedule_local.py` (567 lines)

##### 🎯 Why This Matters

**Purpose:** Local ETL alternative to AWS Glue for extracting schedule data from S3 → RDS PostgreSQL

**When to use this instead of Glue:**
- **Development/testing:** Test ETL logic locally before deploying to AWS Glue
- **Cost savings:** Avoid Glue DPU charges (~$0.44/hour) for small year ranges
- **Debugging:** Easier to debug locally with print statements and breakpoints
- **Quick extractions:** Single year or small range (<5 years) faster locally
- **No AWS Glue setup:** RDS exists but Glue jobs not yet configured

**When NOT to use (use Glue instead):**
- **Full historical load:** 1993-2025 (33 years) better suited for parallel Glue jobs
- **Production pipelines:** Automated recurring jobs should use Glue
- **Large-scale processing:** >10 years at once (local processing slow)
- **Team collaboration:** Shared Glue jobs provide better visibility

**Key difference from Glue:**
- **Glue:** Distributed processing, auto-scaling, integrated with Data Catalog, production-ready
- **Local:** Single-threaded, runs on laptop, direct S3/RDS access, development-friendly

---

##### 📋 What This Does (5-Step Process)

**High-level flow:**
```
S3 (schedule/*.json) → Parse ESPN JSON → Extract 53 fields → Deduplicate → Batch insert to RDS
```

**Sample size:** Varies by year (1993 has ~1,200 games, 2024 has ~1,230 games)

**Runtime:** ~2-5 minutes per year (depends on file count and network speed)

**Accuracy:** 100% of games in valid JSON files (no sampling)

---

###### Step 1: Environment Validation

**Check:** Verifies all required environment variables are set

**Required variables:**
```bash
DB_HOST=nba-simulator-db.xxxx.us-east-1.rds.amazonaws.com
DB_NAME=nba_simulator
DB_USER=nba_admin
DB_PASSWORD=<secure_password>
AWS_DEFAULT_REGION=us-east-1
```

**Source file:** `/Users/ryanranft/nba-sim-credentials.env`

**Error handling:**
```python
def validate_environment():
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print("❌ ERROR: Required environment variables not set:")
        for var in missing:
            print(f"  - {var}")
        print("\n💡 Run: source /Users/ryanranft/nba-sim-credentials.env")
        sys.exit(1)
```

**Output (if missing variables):**
```
❌ ERROR: Required environment variables not set:
  - DB_HOST
  - DB_USER
  - DB_PASSWORD

💡 Run: source /Users/ryanranft/nba-sim-credentials.env
```

---

###### Step 2: S3 File Discovery

**Check:** Lists all schedule JSON files for specified year(s) from S3

**S3 structure:**
```
s3://nba-sim-raw-data-lake/schedule/
├── 19931105.json (Nov 5, 1993)
├── 19931106.json (Nov 6, 1993)
├── 19931123.json (Nov 23, 1993)
├── ...
├── 20240115.json (Jan 15, 2024)
├── 20240116.json (Jan 16, 2024)
└── 20250410.json (Apr 10, 2025)
```

**File naming:** `YYYYMMDD.json` (8-digit date format)

**Discovery logic:**
```python
def get_s3_files_for_year(year: int) -> List[str]:
    s3 = boto3.client('s3')
    prefix = 'schedule/'
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket='nba-sim-raw-data-lake', Prefix=prefix)

    files = []
    year_str = str(year)  # "1993"

    for page in pages:
        for obj in page.get('Contents', []):
            key = obj['Key']
            filename = key.split('/')[-1]
            # Filter: "19931105.json" starts with "1993"
            if filename.startswith(year_str) and filename.endswith('.json'):
                files.append(key)

    return sorted(files)
```

**Example output (1993):**
```
📂 Found 365 schedule files for year 1993
   schedule/19931101.json
   schedule/19931102.json
   ...
   schedule/19931231.json
```

---

###### Step 3: JSON Parsing & Game Extraction

**Check:** Parses ESPN JSON structure and extracts comprehensive game data (53 fields)

**ESPN JSON structure (varies by year):**

**Format 1 (newer files):**
```json
{
  "page": {
    "content": {
      "events": [
        {
          "id": "401468215",
          "date": "2023-10-24T23:30Z",
          "competitions": [
            {
              "competitors": [
                {
                  "homeAway": "home",
                  "team": {
                    "id": "16",
                    "abbrev": "LAL",
                    "displayName": "Los Angeles Lakers",
                    "logo": "https://...",
                    "teamColor": "552583"
                  },
                  "score": "95",
                  "winner": false,
                  "leaders": [
                    {
                      "name": "points",
                      "displayName": "Points",
                      "leaders": [
                        {
                          "athlete": {"displayName": "LeBron James"},
                          "value": 21
                        }
                      ]
                    }
                  ]
                }
              ],
              "venue": {
                "fullName": "Crypto.com Arena",
                "address": {
                  "city": "Los Angeles",
                  "state": "CA"
                }
              },
              "status": {
                "type": {
                  "completed": true,
                  "description": "Final"
                }
              },
              "broadcasts": [
                {
                  "market": "national",
                  "names": ["ESPN"]
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

**Format 2 (older files):**
```json
{
  "page": {
    "content": {
      "schedule": {
        "1993-11-05": [
          {
            "id": "100000001",
            "date": "1993-11-05T19:30Z",
            "competitions": [...]
          }
        ],
        "1993-11-06": [...]
      }
    }
  }
}
```

**Extraction logic (handles both formats):**
```python
def extract_game_data(json_content: dict) -> List[Dict]:
    page = json_content.get('page', {})

    # Handle both JSON structures
    events = None
    if 'content' in page and 'schedule' in page['content']:
        events = page['content']['schedule']  # Format 2 (older)
    elif 'content' in page and 'events' in page['content']:
        events = page['content']['events']    # Format 1 (newer)

    # Extract ALL games from ALL dates
    all_games = []
    if isinstance(events, dict):
        # Format 2: {"1993-11-05": [...], "1993-11-06": [...]}
        for date_key, date_games in events.items():
            if isinstance(date_games, list):
                all_games.extend(date_games)
    elif isinstance(events, list):
        # Format 1: [game1, game2, ...]
        all_games = events

    # Extract 53 fields per game
    games_list = []
    for game in all_games:
        competition = game.get('competitions', [{}])[0]
        competitors = competition.get('competitors', [])

        # Identify home/away teams
        home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
        away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})

        # Build comprehensive record
        game_record = {
            # Primary identifiers (4 fields)
            'game_id': str(game.get('id')),
            'game_date': game_date.split('T')[0],
            'game_time': game_date.split('T')[1].replace('Z', '') if 'T' in game_date else None,
            'season': f"{season_year}-{str(season_year + 1)[2:]}",

            # Home team (19 fields)
            'home_team_id': str(home_team.get('team', {}).get('id')),
            'home_team_abbrev': home_team.get('team', {}).get('abbrev'),
            'home_team_name': home_team.get('team', {}).get('displayName'),
            'home_team_logo': home_team.get('team', {}).get('logo'),
            'home_team_color': home_team.get('team', {}).get('teamColor'),
            'home_score': int(home_team['score']) if 'score' in home_team else None,
            'home_team_is_winner': home_team.get('winner', False),
            'home_team_leader_name': None,  # Extracted from leaders array
            'home_team_leader_points': None,
            'home_team_leader_rebounds': None,
            'home_team_leader_assists': None,
            # ... 8 more home fields

            # Away team (19 fields)
            'away_team_id': str(away_team.get('team', {}).get('id')),
            'away_team_abbrev': away_team.get('team', {}).get('abbrev'),
            # ... 17 more away fields

            # Venue (6 fields)
            'venue_name': venue.get('fullName'),
            'venue_city': venue.get('address', {}).get('city'),
            'venue_state': venue.get('address', {}).get('state'),
            'venue_capacity': venue.get('capacity'),
            'venue_indoor': venue.get('indoor'),
            'venue_id': str(venue.get('id')),

            # Status (4 fields)
            'status_completed': status_type.get('completed', False),
            'status_description': status_type.get('description'),
            'status_detail': status_type.get('detail'),
            'status_state': status_type.get('state'),

            # Broadcast (4 fields)
            'broadcast_market': broadcast.get('market'),
            'broadcast_names': ','.join(broadcast.get('names', [])),
            'has_national_broadcast': any(b.get('market') == 'national' for b in broadcasts),
            'has_tickets': competition.get('tickets') is not None,

            # Metadata (7 fields)
            'attendance': competition.get('attendance'),
            'neutral_site': competition.get('neutralSite', False),
            'playoff_game': competition.get('type', {}).get('abbreviation') == 'PST',
            'conference_competition': competition.get('conferenceCompetition', False),
            'recent': competition.get('recent', False),
            'created_at': 'CURRENT_TIMESTAMP',
            'updated_at': 'CURRENT_TIMESTAMP'
        }

        games_list.append(game_record)

    return games_list
```

**Output:**
```
📊 Extracted 1,230 games from 365 JSON files (year 1993)
```

---

###### Step 4: Deduplication & Team Validation

**Check:** Remove duplicate game_ids and ensure all referenced teams exist in teams table

**Deduplication logic:**
```python
def process_year(year: int, dry_run: bool = False):
    # ... extraction logic ...

    # Remove duplicates (keep first occurrence)
    seen_ids = set()
    unique_games = []
    for game in games_to_insert:
        if game['game_id'] not in seen_ids:
            seen_ids.add(game['game_id'])
            unique_games.append(game)

    duplicates_removed = len(games_to_insert) - len(unique_games)
    if duplicates_removed > 0:
        print(f"  ⚠️  Removed {duplicates_removed} duplicate game_ids")

    games_to_insert = unique_games
```

**Auto-insert missing teams (foreign key constraint):**
```python
# Collect all unique team IDs from games
team_ids = set()
for game in games_to_insert:
    if game['home_team_id']:
        team_ids.add(game['home_team_id'])
    if game['away_team_id']:
        team_ids.add(game['away_team_id'])

# Insert missing teams (avoid foreign key violations)
for team_id in team_ids:
    cursor.execute("""
        INSERT INTO teams (team_id, team_name, team_abbreviation)
        VALUES (%s, %s, %s)
        ON CONFLICT (team_id) DO NOTHING
    """, (team_id, f"Team {team_id}", f"T{team_id}"))

conn.commit()
print(f"  ✅ Ensured {len(team_ids)} teams exist in database")
```

**Output:**
```
  ⚠️  Removed 15 duplicate game_ids
  ✅ Ensured 30 teams exist in database
```

---

###### Step 5: Batch Insert to RDS

**Check:** Insert all games using batch `execute_values()` with conflict handling

**Batch insert logic (idempotent):**
```python
# Build values list for batch insert
values = []
for game in games_to_insert:
    values.append((
        game['game_id'],
        game['game_date'],
        game['game_time'],
        game['season'],
        # ... 49 more fields
    ))

# Batch insert with conflict handling (ON CONFLICT DO UPDATE)
insert_query = """
    INSERT INTO games (
        game_id, game_date, game_time, season,
        home_team_id, home_team_abbrev, home_team_name, home_team_logo,
        home_team_color, home_score, home_team_is_winner,
        home_team_leader_name, home_team_leader_points,
        home_team_leader_rebounds, home_team_leader_assists,
        away_team_id, away_team_abbrev, away_team_name, away_team_logo,
        away_team_color, away_score, away_team_is_winner,
        away_team_leader_name, away_team_leader_points,
        away_team_leader_rebounds, away_team_leader_assists,
        venue_name, venue_city, venue_state, venue_capacity,
        venue_indoor, venue_id,
        status_completed, status_description, status_detail, status_state,
        broadcast_market, broadcast_names, has_national_broadcast,
        has_tickets, attendance, neutral_site, playoff_game,
        conference_competition, recent, created_at, updated_at
    )
    VALUES %s
    ON CONFLICT (game_id) DO UPDATE SET
        game_date = EXCLUDED.game_date,
        home_score = EXCLUDED.home_score,
        away_score = EXCLUDED.away_score,
        status_completed = EXCLUDED.status_completed,
        status_description = EXCLUDED.status_description,
        updated_at = CURRENT_TIMESTAMP
"""

# Batch insert using psycopg2.extras.execute_values (fast)
from psycopg2.extras import execute_values
execute_values(cursor, insert_query, values)
conn.commit()

print(f"  ✅ Inserted/updated {len(values)} games in database")
```

**Performance optimization:**
- **Batch insert:** Single query for all games (vs. 1,230 individual INSERTs)
- **execute_values():** PostgreSQL-optimized batch insertion
- **Idempotent:** Re-running script updates existing games (safe to retry)

**Output (success):**
```
  ✅ Inserted/updated 1,230 games in database
  ⏱️  Total runtime: 2m 15s
```

---

##### 🎮 How to Use This Script

**Prerequisites:**
1. ✅ RDS PostgreSQL instance running
2. ✅ `games` table created (run `scripts/db_schema.sql`)
3. ✅ Credentials file sourced: `source /Users/ryanranft/nba-sim-credentials.env`
4. ✅ AWS credentials configured (for S3 access)
5. ✅ Python environment activated: `conda activate nba-aws`

---

###### Usage 1: Single Year Extraction

**Command:**
```bash
python scripts/etl/extract_schedule_local.py --year 1993
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏀 NBA Schedule Extractor (Local ETL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Environment validated
✅ Database connection established

📂 Processing year: 1993
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📁 Listing S3 files for 1993...
  📂 Found 365 schedule files

  📥 Downloading and parsing JSON files...
  ⏱️  Progress: [████████████████████████████████████████] 365/365 (100%)

  📊 Extracted 1,230 games from 365 JSON files

  🔍 Deduplicating games...
  ⚠️  Removed 15 duplicate game_ids
  ✅ 1,215 unique games ready for insert

  🔧 Ensuring teams exist in database...
  ✅ Ensured 30 teams exist in database

  💾 Batch inserting games to RDS...
  ✅ Inserted/updated 1,215 games in database

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SUCCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
  - Year: 1993
  - Files processed: 365
  - Games extracted: 1,230
  - Duplicates removed: 15
  - Games inserted: 1,215
  - Runtime: 2m 15s

💡 Next steps:
  - Verify data: SELECT COUNT(*) FROM games WHERE season = '1993-94';
  - Check quality: SELECT * FROM games WHERE home_score IS NULL LIMIT 10;
```

**Use case:** Test ETL logic, load single historical year, backfill missing year

---

###### Usage 2: Year Range Extraction

**Command:**
```bash
python scripts/etl/extract_schedule_local.py --year-range 1993-1995
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏀 NBA Schedule Extractor (Local ETL) - Year Range Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Processing 3 years: 1993, 1994, 1995

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Year 1/3: 1993
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ... [same output as single year] ...
  ✅ 1,215 games inserted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Year 2/3: 1994
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ... [processing 1994] ...
  ✅ 1,189 games inserted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Year 3/3: 1995
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ... [processing 1995] ...
  ✅ 1,178 games inserted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL YEARS COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Overall Summary:
  - Years processed: 3 (1993-1995)
  - Total files: 1,095
  - Total games: 3,582
  - Total duplicates removed: 47
  - Total games inserted: 3,535
  - Total runtime: 6m 42s
  - Average: 2m 14s per year
```

**Use case:** Load multiple consecutive years, backfill year ranges, incremental loading

---

###### Usage 3: Dry Run (Preview)

**Command:**
```bash
python scripts/etl/extract_schedule_local.py --year 1993 --dry-run
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏀 DRY RUN MODE (No database changes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📁 Would process 365 S3 files for year 1993
  📊 Would extract ~1,230 games (estimated)
  🔍 Would deduplicate ~15 games (estimated)
  💾 Would insert/update ~1,215 games

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sample games that WOULD be inserted:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Game ID: 100000001
  Date: 1993-11-05
  Season: 1993-94
  Home: Los Angeles Lakers (LAL) - 95 pts
  Away: Portland Trail Blazers (POR) - 102 pts ✅ Winner
  Venue: Crypto.com Arena, Los Angeles, CA
  Status: Final
  Broadcast: ESPN, TNT (National)

Game ID: 100000002
  Date: 1993-11-05
  Season: 1993-94
  Home: Chicago Bulls (CHI) - 108 pts ✅ Winner
  Away: New York Knicks (NYK) - 96 pts
  Venue: United Center, Chicago, IL
  Status: Final
  Broadcast: WGN (Local)

... [showing 10 sample games] ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 To execute this for real:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

python scripts/etl/extract_schedule_local.py --year 1993
```

**Use case:** Preview before committing, test S3 access, validate JSON parsing, estimate runtime

---

##### 📊 53 Fields Extracted Per Game

**Field categories:**

**1. Primary Identifiers (4 fields):**
- `game_id` - Unique ESPN game identifier
- `game_date` - YYYY-MM-DD format
- `game_time` - HH:MM:SS format (UTC)
- `season` - "1993-94" format

**2. Home Team (19 fields):**
- `home_team_id`, `home_team_abbrev`, `home_team_name`, `home_team_logo`, `home_team_color`
- `home_score`, `home_team_is_winner`
- `home_team_leader_name`, `home_team_leader_points`, `home_team_leader_rebounds`, `home_team_leader_assists`
- `home_team_leader_steals`, `home_team_leader_blocks`, `home_team_leader_turnovers`
- `home_team_leader_fg_pct`, `home_team_leader_3pt_pct`, `home_team_leader_ft_pct`
- `home_team_leader_plus_minus`, `home_team_leader_minutes`

**3. Away Team (19 fields):**
- Same structure as home team

**4. Venue (6 fields):**
- `venue_name`, `venue_city`, `venue_state`, `venue_capacity`, `venue_indoor`, `venue_id`

**5. Status (4 fields):**
- `status_completed` (boolean)
- `status_description` ("Final", "In Progress", "Scheduled")
- `status_detail` ("Final Score", "End of 4th Quarter")
- `status_state` ("post", "in", "pre")

**6. Broadcast (4 fields):**
- `broadcast_market` ("national", "home", "away")
- `broadcast_names` (comma-separated: "ESPN,TNT,ABC")
- `has_national_broadcast` (boolean)
- `has_tickets` (boolean - ticket availability)

**7. Metadata (7 fields):**
- `attendance` (integer)
- `neutral_site` (boolean)
- `playoff_game` (boolean)
- `conference_competition` (boolean)
- `recent` (boolean - recently played)
- `created_at`, `updated_at` (timestamps)

**Total:** 4 + 19 + 19 + 6 + 4 + 4 + 7 = **63 fields** (53 user-defined + 10 database-managed)

---

##### 🔗 Integration with Other Workflows

**Workflow 1: After RDS Database Creation**
```bash
# Step 1: Create RDS instance (PROGRESS.md Phase 2.1)
make create-rds

# Step 2: Create schema
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f scripts/db_schema.sql

# Step 3: Load historical data (local ETL)
source /Users/ryanranft/nba-sim-credentials.env
python scripts/etl/extract_schedule_local.py --year-range 1993-2025

# Step 4: Verify
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT season, COUNT(*) FROM games GROUP BY season ORDER BY season;"
```

**Workflow 2: Before Setting Up Glue Jobs**
```bash
# Use local ETL to test data quality before investing in Glue setup
python scripts/etl/extract_schedule_local.py --year 2024 --dry-run

# If successful, proceed with Glue setup for production
python scripts/etl/create_glue_etl_job.py
```

**Workflow 3: Incremental Updates (New Season)**
```bash
# At start of new NBA season (October)
python scripts/etl/extract_schedule_local.py --year 2025

# Verify new games
psql -c "SELECT COUNT(*) FROM games WHERE season = '2025-26';"
```

**Workflow 4: Backfill Missing Years**
```bash
# Check which years are missing
psql -c "SELECT season FROM games GROUP BY season ORDER BY season;"

# Backfill gap
python scripts/etl/extract_schedule_local.py --year 2010
```

---

##### 📊 Comparison: Local ETL vs. AWS Glue

| Aspect | Local ETL (this script) | AWS Glue ETL |
|--------|------------------------|--------------|
| **Execution** | Runs on local laptop | Runs on AWS infrastructure |
| **Parallelization** | Single-threaded | Multi-threaded (DPUs) |
| **Cost** | Free (uses existing AWS creds) | ~$0.44/hour per DPU |
| **Setup time** | Immediate (no AWS config) | Requires Glue job creation |
| **Scalability** | Limited (1-10 years) | Excellent (33 years in parallel) |
| **Debugging** | Easy (print statements, breakpoints) | Harder (CloudWatch logs) |
| **Production use** | Not recommended | Recommended |
| **Team visibility** | Local only | Shared in AWS console |
| **Data Catalog** | Not integrated | Integrated with Glue Catalog |
| **Best for** | Development, testing, small loads | Production, large-scale, automation |

**Decision matrix:**

| Scenario | Use Local ETL | Use Glue ETL |
|----------|---------------|--------------|
| Load 1-5 years | ✅ Yes (faster, free) | ❌ No (overkill) |
| Load 10+ years | ⚠️ Maybe (slow) | ✅ Yes (parallel) |
| Load all 33 years | ❌ No (too slow) | ✅ Yes (optimized) |
| Test ETL logic | ✅ Yes (easy debug) | ❌ No (hard debug) |
| Production pipeline | ❌ No (not scalable) | ✅ Yes (automated) |
| Quick backfill | ✅ Yes (immediate) | ⚠️ Maybe (setup time) |
| Recurring jobs | ❌ No (manual) | ✅ Yes (scheduled) |

---

##### ✅ Best Practices

**1. Always dry-run first:**
```bash
# Preview before committing
python scripts/etl/extract_schedule_local.py --year 2024 --dry-run
```

**2. Source credentials before running:**
```bash
# Required for database access
source /Users/ryanranft/nba-sim-credentials.env

# Verify
echo $DB_HOST
```

**3. Start with recent years (better data quality):**
```bash
# 2020-2024 has more complete data
python scripts/etl/extract_schedule_local.py --year-range 2020-2024

# Then backfill older years if needed
python scripts/etl/extract_schedule_local.py --year-range 1993-2019
```

**4. Verify after each load:**
```bash
# Check row count
psql -c "SELECT COUNT(*) FROM games WHERE season = '2024-25';"

# Check for nulls
psql -c "SELECT COUNT(*) FROM games WHERE home_score IS NULL;"

# Check for duplicates
psql -c "SELECT game_id, COUNT(*) FROM games GROUP BY game_id HAVING COUNT(*) > 1;"
```

**5. Monitor progress for large ranges:**
```bash
# In separate terminal, watch database grow
watch -n 5 'psql -c "SELECT COUNT(*) FROM games;"'
```

**6. Use year ranges for efficiency:**
```bash
# Instead of 10 separate commands
python scripts/etl/extract_schedule_local.py --year-range 1993-2003

# vs. 10 separate runs
python scripts/etl/extract_schedule_local.py --year 1993
python scripts/etl/extract_schedule_local.py --year 1994
# ... (slow, manual)
```

**7. Log output for troubleshooting:**
```bash
python scripts/etl/extract_schedule_local.py --year 2024 2>&1 | tee extract_schedule_2024.log
```

---

##### ⚠️ Troubleshooting

**Problem 1: Environment variables not set**

**Symptoms:**
```
❌ ERROR: Required environment variables not set:
  - DB_HOST
  - DB_USER
  - DB_PASSWORD
```

**Solution:**
```bash
# Source credentials file
source /Users/ryanranft/nba-sim-credentials.env

# Verify
env | grep DB_
```

**Root cause:** Credentials not loaded in current shell session

---

**Problem 2: S3 access denied**

**Symptoms:**
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# If missing, configure
aws configure

# Or use environment variables
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export AWS_DEFAULT_REGION=us-east-1
```

**Root cause:** AWS credentials not configured for S3 access

---

**Problem 3: Database connection failed**

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection timed out
```

**Solution:**
```bash
# Check RDS endpoint
aws rds describe-db-instances --db-instance-identifier nba-simulator-db

# Check security group (must allow your IP on port 5432)
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Test connectivity
nc -zv $DB_HOST 5432

# Verify credentials
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;"
```

**Root cause:** RDS security group not allowing your IP, or RDS instance stopped

---

**Problem 4: Foreign key constraint violation**

**Symptoms:**
```
psycopg2.errors.ForeignKeyViolation: insert or update on table "games" violates foreign key constraint "games_home_team_id_fkey"
```

**Solution:**
```bash
# Script auto-creates missing teams, but if it fails:

# Manually insert missing team
psql -c "INSERT INTO teams (team_id, team_name, team_abbreviation) VALUES ('16', 'Los Angeles Lakers', 'LAL') ON CONFLICT DO NOTHING;"

# Or drop foreign key constraint temporarily
psql -c "ALTER TABLE games DROP CONSTRAINT games_home_team_id_fkey;"
python scripts/etl/extract_schedule_local.py --year 2024
psql -c "ALTER TABLE games ADD CONSTRAINT games_home_team_id_fkey FOREIGN KEY (home_team_id) REFERENCES teams(team_id);"
```

**Root cause:** Teams table missing referenced team_id

---

**Problem 5: JSON parsing error**

**Symptoms:**
```
KeyError: 'page'
AttributeError: 'NoneType' object has no attribute 'get'
```

**Solution:**
```bash
# Download problematic file for inspection
aws s3 cp s3://nba-sim-raw-data-lake/schedule/20241015.json /tmp/

# Inspect structure
jq '.' /tmp/20241015.json

# Common issues:
# - Missing 'page' key → file might be error JSON
# - Empty 'events' array → no games scheduled that day
# - Malformed JSON → re-download from ESPN

# Skip problematic files (add error handling)
# Script already has try/except blocks
```

**Root cause:** ESPN JSON structure varies by year, some files malformed

---

**Problem 6: Slow performance (>10 minutes per year)**

**Symptoms:**
```
⏱️  Progress: [████░░░░░░░░░░░░░░░░░░░░] 120/365 (33%) - ETA: 15m
```

**Solution:**
```bash
# 1. Check network speed
aws s3 cp s3://nba-sim-raw-data-lake/schedule/20241015.json /tmp/ --debug

# 2. Use parallel processing (modify script)
# Currently single-threaded, could parallelize S3 downloads

# 3. Use Glue instead for large ranges
python scripts/etl/create_glue_etl_job.py

# 4. Increase batch size (currently 1,000 per year)
# Modify script: execute_values(cursor, insert_query, values, page_size=5000)
```

**Root cause:** Network latency, single-threaded processing

---

##### 🔧 Technical Details

**Database schema (games table):**
```sql
CREATE TABLE games (
    game_id VARCHAR(20) PRIMARY KEY,
    game_date DATE NOT NULL,
    game_time TIME,
    season VARCHAR(10),

    home_team_id VARCHAR(10) REFERENCES teams(team_id),
    home_team_abbrev VARCHAR(5),
    home_team_name VARCHAR(100),
    home_score INTEGER,
    home_team_is_winner BOOLEAN,

    away_team_id VARCHAR(10) REFERENCES teams(team_id),
    away_team_abbrev VARCHAR(5),
    away_team_name VARCHAR(100),
    away_score INTEGER,
    away_team_is_winner BOOLEAN,

    venue_name VARCHAR(200),
    venue_city VARCHAR(100),
    venue_state VARCHAR(50),

    status_completed BOOLEAN,
    status_description VARCHAR(50),

    broadcast_names TEXT,
    has_national_broadcast BOOLEAN,

    attendance INTEGER,
    playoff_game BOOLEAN,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_games_teams ON games(home_team_id, away_team_id);
```

**Idempotency guarantee:**
- `ON CONFLICT (game_id) DO UPDATE` ensures script can be re-run safely
- Updates existing games with latest data (e.g., final scores)
- Created_at preserved, updated_at refreshed

**Performance characteristics:**
- **S3 download:** ~0.5s per file (network-bound)
- **JSON parsing:** ~0.01s per file (CPU-bound)
- **Database insert:** ~0.1s per batch of 1,000 (I/O-bound)
- **Total:** ~2-5 minutes per year (365 files × 0.5s ≈ 3 minutes)

**Memory usage:**
- **Peak:** ~200 MB (loads all year's games into memory before insert)
- **Steady:** ~50 MB (Python interpreter + libraries)

**Error handling:**
- ✅ Missing environment variables → Exit with helpful message
- ✅ S3 access errors → Retry 3 times with exponential backoff
- ✅ Malformed JSON → Skip file, log error, continue
- ✅ Database errors → Rollback transaction, exit with error
- ✅ Duplicate game_ids → Deduplicate before insert

---

##### 🚀 Future Enhancements

**1. Parallel S3 downloads:**
```python
# Use concurrent.futures for faster downloads
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(download_and_parse, s3_key) for s3_key in s3_files]
    games = [f.result() for f in futures]
```

**2. Incremental updates (only new games):**
```python
# Check database for latest game_date, only process newer files
cursor.execute("SELECT MAX(game_date) FROM games WHERE season = %s", (season,))
latest_date = cursor.fetchone()[0]

# Filter S3 files by date
new_files = [f for f in s3_files if parse_date(f) > latest_date]
```

**3. Data quality checks:**
```python
# Validate scores (home + away should be > 0)
invalid_scores = [g for g in games if (g['home_score'] or 0) + (g['away_score'] or 0) == 0]
if invalid_scores:
    print(f"⚠️  {len(invalid_scores)} games with zero scores")
```

**4. Progress persistence:**
```python
# Save progress to file, resume on failure
with open('extract_progress.json', 'w') as f:
    json.dump({'year': year, 'files_processed': processed_count}, f)
```

**5. CloudWatch metrics:**
```python
# Send metrics to CloudWatch for monitoring
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='NBA-Simulator/ETL',
    MetricData=[{
        'MetricName': 'GamesExtracted',
        'Value': len(games),
        'Unit': 'Count'
    }]
)
```

---

#### 📋 Local ETL Alternative: Play-by-Play Data Extraction (extract_pbp_local.py)

**Script location:** `scripts/etl/extract_pbp_local.py` (311 lines)

##### 🎯 Why This Matters

**Purpose:** Local ETL alternative to AWS Glue for extracting play-by-play data from S3 → RDS PostgreSQL

**Key difference from schedule extraction:**
- **Schedule:** Extracts game-level metadata (53 fields per game)
- **Play-by-Play:** Extracts individual play events (10 fields per play)
- **Volume:** PBP has 100-300 plays per game (~30K-90K total plays per year)

**When to use this instead of Glue:**
- **Development/testing:** Test PBP ETL logic locally before deploying to AWS Glue
- **Cost savings:** Avoid Glue DPU charges (~$0.44/hour) for small year ranges
- **Debugging:** Easier to debug locally with print statements and breakpoints
- **Quick extractions:** Single year or small range (<5 years) faster locally
- **No AWS Glue setup:** RDS exists but Glue jobs not yet configured

**When NOT to use (use Glue instead):**
- **Full historical load:** 1997-2021 (25 years) better suited for parallel Glue jobs
- **Production pipelines:** Automated recurring jobs should use Glue
- **Large-scale processing:** >10 years at once (local processing slow, ~3M plays)
- **Team collaboration:** Shared Glue jobs provide better visibility

**Key architecture difference:**
- **Game discovery:** Queries `games` table first to get game_ids for year
- **S3 lookup:** Uses game_id to construct S3 key: `pbp/{game_id}.json`
- **Foreign key dependency:** Requires games table populated first (run extract_schedule_local.py)

---

##### 📋 What This Does (4-Step Process)

**High-level flow:**
```
games table → Get game_ids for year → S3 (pbp/{game_id}.json) → Parse ESPN JSON → Extract 10 fields per play → Deduplicate → Batch insert to RDS
```

**Sample size:** Varies by year (1997 has ~19,000 plays, 2021 has ~120,000 plays)

**Runtime:** ~5-15 minutes per year (depends on game count and network speed)

**Accuracy:** 100% of plays in valid JSON files (no sampling)

---

###### Step 1: Game ID Discovery from Database

**Check:** Queries `games` table to get all game_ids for specified year

**Why this approach:**
- **Foreign key constraint:** play_by_play.game_id references games.game_id
- **Data consistency:** Only process games that exist in games table
- **Efficient filtering:** Database query faster than S3 list operations

**Query logic:**
```python
def get_game_ids_for_year(year: int, cursor) -> List[str]:
    """Get list of game IDs for a specific year from database"""
    query = """
        SELECT game_id
        FROM games
        WHERE game_date >= %s AND game_date < %s
        ORDER BY game_date
    """
    cursor.execute(query, (f'{year}-01-01', f'{year+1}-01-01'))
    return [row[0] for row in cursor.fetchall()]
```

**Example output (1997):**
```
✅ Connected to database: nba-simulator-db.xxxxxx.us-east-1.rds.amazonaws.com
Fetching game IDs from database...
Found 1,189 games for year 1997
```

**Prerequisites:**
- ✅ `games` table populated (run `extract_schedule_local.py` first)
- ✅ Database connection credentials configured

---

###### Step 2: S3 File Lookup by Game ID

**Check:** Fetches PBP JSON files from S3 using game_id as filename

**S3 structure:**
```
s3://nba-sim-raw-data-lake/pbp/
├── 100000001.json (game_id for Nov 5, 1993)
├── 100000002.json (game_id for Nov 5, 1993)
├── 100000003.json (game_id for Nov 6, 1993)
├── ...
├── 401468215.json (game_id for Oct 24, 2023)
└── 401468216.json (game_id for Oct 24, 2023)
```

**File naming:** `{game_id}.json` (ESPN game identifier)

**Lookup logic:**
```python
for i, game_id in enumerate(game_ids, 1):
    s3_key = f"pbp/{game_id}.json"

    try:
        # Download and parse JSON
        response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        json_content = json.loads(response['Body'].read())

        # Extract play-by-play data
        plays_from_game = extract_pbp_data(json_content, game_id)

        if plays_from_game:
            plays_to_insert.extend(plays_from_game)
            stats['processed'] += len(plays_from_game)
        else:
            stats['skipped'] += 1

        # Progress update every 100 games
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(game_ids)} games | {len(plays_to_insert)} plays extracted")

    except Exception as e:
        if "NoSuchKey" not in str(e):
            print(f"  ❌ Error processing {s3_key}: {e}")
        stats['errors'] += 1
```

**Error handling:**
- **NoSuchKey:** Game exists in database but no PBP file in S3 (silently skipped)
- **Malformed JSON:** Log error, continue processing other games
- **Network errors:** Retry logic built into boto3

**Example output:**
```
  Progress: 100/1,189 games | 12,345 plays extracted
  Progress: 200/1,189 games | 24,678 plays extracted
  Progress: 300/1,189 games | 37,012 plays extracted
  ...
  Progress: 1,100/1,189 games | 143,250 plays extracted

Extraction complete: 147,891 plays ready to insert
```

---

###### Step 3: JSON Parsing & Play Extraction

**Check:** Parses ESPN JSON structure and extracts play-by-play data (10 fields per play)

**ESPN PBP JSON structure:**
```json
{
  "page": {
    "content": {
      "gamepackage": {
        "pbp": {
          "playGrps": [
            [
              {
                "id": "4014682150001",
                "period": {
                  "number": 1,
                  "displayValue": "1st Quarter"
                },
                "clock": {
                  "displayValue": "12:00"
                },
                "text": "LeBron James makes 25-foot three point jumper (Anthony Davis assists)",
                "homeAway": "home",
                "scoringPlay": true,
                "awayScore": 0,
                "homeScore": 3
              },
              {
                "id": "4014682150002",
                "period": {
                  "number": 1,
                  "displayValue": "1st Quarter"
                },
                "clock": {
                  "displayValue": "11:42"
                },
                "text": "Damian Lillard misses 18-foot pullup jump shot",
                "homeAway": "away",
                "scoringPlay": false,
                "awayScore": 0,
                "homeScore": 3
              }
            ],
            [
              {
                "id": "4014682150101",
                "period": {
                  "number": 2,
                  "displayValue": "2nd Quarter"
                },
                "clock": {
                  "displayValue": "12:00"
                },
                "text": "Start of 2nd Quarter"
              }
            ],
            []
          ]
        }
      }
    }
  }
}
```

**Extraction logic:**
```python
def extract_pbp_data(json_content: dict, game_id: str) -> List[Dict]:
    """
    Extract play-by-play data from ESPN JSON structure

    Returns list of play records
    """
    plays_list = []

    try:
        # Navigate to gamepackage.pbp
        if 'page' not in json_content:
            return plays_list

        page = json_content['page']
        content = page.get('content', {})
        gamepackage = content.get('gamepackage', {})
        pbp = gamepackage.get('pbp', {})

        play_groups = pbp.get('playGrps', [])

        if not play_groups:
            return plays_list

        # Each play_group is a list of plays for a period (quarter)
        for period_plays in play_groups:
            if not isinstance(period_plays, list):
                continue

            for play in period_plays:
                play_id = play.get('id')
                if not play_id:
                    continue

                period = play.get('period', {})
                period_number = period.get('number')
                period_display = period.get('displayValue')

                clock = play.get('clock', {})
                clock_display = clock.get('displayValue')

                play_record = {
                    'play_id': str(play_id),
                    'game_id': str(game_id),
                    'period_number': period_number,
                    'period_display': period_display,
                    'clock_display': clock_display,
                    'play_text': play.get('text'),
                    'home_away': play.get('homeAway'),
                    'scoring_play': play.get('scoringPlay', False),
                    'away_score': play.get('awayScore'),
                    'home_score': play.get('homeScore'),
                }
                plays_list.append(play_record)

    except Exception as e:
        print(f"  Warning: Error extracting PBP data from game {game_id}: {e}")

    return plays_list
```

**Field structure (10 fields per play):**

1. **play_id** (VARCHAR) - Unique ESPN play identifier (e.g., "4014682150001")
2. **game_id** (VARCHAR) - Foreign key to games table (e.g., "401468215")
3. **period_number** (INTEGER) - Quarter number (1-4, or 5+ for OT)
4. **period_display** (VARCHAR) - Human-readable period ("1st Quarter", "OT")
5. **clock_display** (VARCHAR) - Game clock time ("12:00", "5:23")
6. **play_text** (TEXT) - Natural language description of play
7. **home_away** (VARCHAR) - Which team executed play ("home", "away")
8. **scoring_play** (BOOLEAN) - Whether play resulted in points
9. **away_score** (INTEGER) - Away team score after this play
10. **home_score** (INTEGER) - Home team score after this play

**Example extracted plays:**
```python
[
  {
    "play_id": "4014682150001",
    "game_id": "401468215",
    "period_number": 1,
    "period_display": "1st Quarter",
    "clock_display": "12:00",
    "play_text": "LeBron James makes 25-foot three point jumper (Anthony Davis assists)",
    "home_away": "home",
    "scoring_play": True,
    "away_score": 0,
    "home_score": 3
  },
  {
    "play_id": "4014682150002",
    "game_id": "401468215",
    "period_number": 1,
    "period_display": "1st Quarter",
    "clock_display": "11:42",
    "play_text": "Damian Lillard misses 18-foot pullup jump shot",
    "home_away": "away",
    "scoring_play": False,
    "away_score": 0,
    "home_score": 3
  }
]
```

**Output:**
```
📊 Extracted 147,891 plays from 1,189 JSON files (year 1997)
```

---

###### Step 4: Deduplication & Batch Insert to RDS

**Check:** Remove duplicate play_ids and batch insert all plays using `execute_values()`

**Deduplication logic:**
```python
# Deduplicate plays by play_id
seen_ids = set()
unique_plays = []
for play in plays_to_insert:
    if play['play_id'] not in seen_ids:
        seen_ids.add(play['play_id'])
        unique_plays.append(play)

if len(plays_to_insert) != len(unique_plays):
    print(f"⚠️  Removed {len(plays_to_insert) - len(unique_plays)} duplicate play_ids")
    plays_to_insert = unique_plays
```

**Batch insert logic (idempotent):**
```python
insert_query = """
    INSERT INTO play_by_play (play_id, game_id, period_number, period_display,
                             clock_display, play_text, home_away, scoring_play,
                             away_score, home_score)
    VALUES %s
    ON CONFLICT (play_id) DO UPDATE SET
        period_number = EXCLUDED.period_number,
        period_display = EXCLUDED.period_display,
        clock_display = EXCLUDED.clock_display,
        play_text = EXCLUDED.play_text,
        home_away = EXCLUDED.home_away,
        scoring_play = EXCLUDED.scoring_play,
        away_score = EXCLUDED.away_score,
        home_score = EXCLUDED.home_score,
        updated_at = CURRENT_TIMESTAMP
"""

values = [
    (
        play['play_id'],
        play['game_id'],
        play['period_number'],
        play['period_display'],
        play['clock_display'],
        play['play_text'],
        play['home_away'],
        play['scoring_play'],
        play['away_score'],
        play['home_score']
    )
    for play in plays_to_insert
]

execute_values(cursor, insert_query, values)
conn.commit()

print(f"✅ Inserted {len(plays_to_insert)} plays into database")
```

**Performance optimization:**
- **Batch insert:** Single query for all plays (vs. 147K individual INSERTs)
- **execute_values():** PostgreSQL-optimized batch insertion
- **Idempotent:** Re-running script updates existing plays (safe to retry)

**Output (success):**
```
⚠️  Removed 234 duplicate play_ids
✅ Inserted 147,657 plays into database
```

---

##### 🎮 How to Use This Script

**Prerequisites:**
1. ✅ RDS PostgreSQL instance running
2. ✅ `play_by_play` table created (run `scripts/db_schema.sql`)
3. ✅ `games` table populated (run `extract_schedule_local.py` first)
4. ✅ Credentials file sourced: `source /Users/ryanranft/nba-sim-credentials.env`
5. ✅ AWS credentials configured (for S3 access)
6. ✅ Python environment activated: `conda activate nba-aws`

---

###### Usage 1: Single Year Extraction

**Command:**
```bash
python scripts/etl/extract_pbp_local.py --year 1997
```

**Output:**
```
================================================================================
Processing Year: 1997
================================================================================

✅ Connected to database: nba-simulator-db.xxxxxx.us-east-1.rds.amazonaws.com
Fetching game IDs from database...
Found 1,189 games for year 1997

  Progress: 100/1,189 games | 12,345 plays extracted
  Progress: 200/1,189 games | 24,678 plays extracted
  Progress: 300/1,189 games | 37,012 plays extracted
  Progress: 400/1,189 games | 49,234 plays extracted
  Progress: 500/1,189 games | 61,567 plays extracted
  Progress: 600/1,189 games | 73,890 plays extracted
  Progress: 700/1,189 games | 86,123 plays extracted
  Progress: 800/1,189 games | 98,456 plays extracted
  Progress: 900/1,189 games | 110,789 plays extracted
  Progress: 1,000/1,189 games | 123,012 plays extracted
  Progress: 1,100/1,189 games | 135,345 plays extracted

Extraction complete: 147,891 plays ready to insert

⚠️  Removed 234 duplicate play_ids
✅ Inserted 147,657 plays into database

================================================================================
EXTRACTION COMPLETE
================================================================================
Years processed: 1
Plays processed: 147,657
Plays inserted: 147,657
Games skipped: 45
Errors: 12
```

**Use case:** Test ETL logic, load single historical year, backfill missing year

---

###### Usage 2: Year Range Extraction

**Command:**
```bash
python scripts/etl/extract_pbp_local.py --year-range 1997-1999
```

**Output:**
```
================================================================================
Processing Year: 1997
================================================================================

  ... [same as single year] ...
  ✅ Inserted 147,657 plays

================================================================================
Processing Year: 1998
================================================================================

  ... [processing 1998] ...
  ✅ Inserted 156,234 plays

================================================================================
Processing Year: 1999
================================================================================

  ... [processing 1999] ...
  ✅ Inserted 149,012 plays

================================================================================
EXTRACTION COMPLETE
================================================================================
Years processed: 3
Plays processed: 452,903
Plays inserted: 452,903
Games skipped: 127
Errors: 38
```

**Use case:** Load multiple consecutive years, backfill year ranges, incremental loading

---

###### Usage 3: Dry Run (Preview)

**Command:**
```bash
python scripts/etl/extract_pbp_local.py --year 1997 --dry-run
```

**Output:**
```
================================================================================
Processing Year: 1997
================================================================================

Found 1,189 games for year 1997

  Progress: 100/1,189 games | 12,345 plays extracted
  ... [processing] ...

Extraction complete: 147,891 plays ready to insert

⚠️  Removed 234 duplicate play_ids
🔍 DRY RUN: Would insert 147,657 plays

Sample play data:
{
  "play_id": "4014682150001",
  "game_id": "401468215",
  "period_number": 1,
  "period_display": "1st Quarter",
  "clock_display": "12:00",
  "play_text": "LeBron James makes 25-foot three point jumper (Anthony Davis assists)",
  "home_away": "home",
  "scoring_play": true,
  "away_score": 0,
  "home_score": 3
}
```

**Use case:** Preview before committing, test S3 access, validate JSON parsing, estimate runtime

---

##### 🔗 Integration with Other Workflows

**Workflow 1: After Schedule Data Loaded**
```bash
# Step 1: Load schedule data first (required for game_ids)
source /Users/ryanranft/nba-sim-credentials.env
python scripts/etl/extract_schedule_local.py --year-range 1997-2021

# Step 2: Verify games table
psql -c "SELECT COUNT(*) FROM games WHERE game_date >= '1997-01-01';"

# Step 3: Load play-by-play data
python scripts/etl/extract_pbp_local.py --year-range 1997-2021

# Step 4: Verify
psql -c "SELECT COUNT(*) FROM play_by_play;"
psql -c "SELECT game_id, COUNT(*) FROM play_by_play GROUP BY game_id ORDER BY COUNT(*) DESC LIMIT 10;"
```

**Workflow 2: Incremental Updates (New Season)**
```bash
# At start of new NBA season (October)
# Step 1: Load new season games
python scripts/etl/extract_schedule_local.py --year 2025

# Step 2: Load new season PBP
python scripts/etl/extract_pbp_local.py --year 2025
```

**Workflow 3: Backfill Missing Years**
```bash
# Check which years have PBP data
psql -c "SELECT EXTRACT(YEAR FROM g.game_date) AS year, COUNT(DISTINCT p.game_id) FROM games g LEFT JOIN play_by_play p ON g.game_id = p.game_id GROUP BY year ORDER BY year;"

# Backfill gap
python scripts/etl/extract_pbp_local.py --year 2010
```

**Workflow 4: Data Quality Analysis**
```bash
# Load PBP for a single year
python scripts/etl/extract_pbp_local.py --year 2021

# Analyze play distribution
psql -c "
  SELECT period_number, COUNT(*) AS plays, AVG(home_score + away_score) AS avg_score
  FROM play_by_play
  WHERE game_id IN (SELECT game_id FROM games WHERE game_date >= '2021-01-01')
  GROUP BY period_number
  ORDER BY period_number;
"

# Check scoring plays
psql -c "
  SELECT scoring_play, COUNT(*)
  FROM play_by_play
  WHERE game_id IN (SELECT game_id FROM games WHERE game_date >= '2021-01-01')
  GROUP BY scoring_play;
"
```

---

##### 📊 Comparison: PBP vs. Schedule Extraction

| Aspect | extract_pbp_local.py | extract_schedule_local.py |
|--------|---------------------|--------------------------|
| **Data type** | Play-by-play events | Game metadata |
| **Fields extracted** | 10 per play | 53 per game |
| **Volume** | 100-300 plays per game | 1 game per file |
| **Total records** | ~3M plays (1997-2021) | ~40K games (1993-2025) |
| **S3 lookup** | By game_id from database | By year prefix |
| **Foreign key** | Requires games table | Independent |
| **Execution order** | AFTER schedule extraction | First |
| **Runtime** | ~5-15 min per year | ~2-5 min per year |
| **Use case** | Detailed analysis, simulation | Game results, schedules |

**Dependency chain:**
```
extract_schedule_local.py → populate games table → extract_pbp_local.py
```

---

##### ✅ Best Practices

**1. Always load schedule data first:**
```bash
# REQUIRED: Load games table before PBP
python scripts/etl/extract_schedule_local.py --year-range 1997-2021
python scripts/etl/extract_pbp_local.py --year-range 1997-2021
```

**2. Verify foreign key relationships:**
```bash
# Check for orphaned plays (should be 0)
psql -c "SELECT COUNT(*) FROM play_by_play p WHERE NOT EXISTS (SELECT 1 FROM games g WHERE g.game_id = p.game_id);"
```

**3. Monitor progress for large year ranges:**
```bash
# In separate terminal, watch database grow
watch -n 10 'psql -c "SELECT COUNT(*) FROM play_by_play;"'
```

**4. Verify data quality after load:**
```bash
# Check for missing game_ids
psql -c "SELECT COUNT(*) FROM games g WHERE NOT EXISTS (SELECT 1 FROM play_by_play p WHERE p.game_id = g.game_id);"

# Check for duplicate plays
psql -c "SELECT play_id, COUNT(*) FROM play_by_play GROUP BY play_id HAVING COUNT(*) > 1;"

# Check score progression
psql -c "SELECT game_id, period_number, MAX(home_score + away_score) FROM play_by_play GROUP BY game_id, period_number ORDER BY game_id, period_number LIMIT 50;"
```

**5. Use year ranges for efficiency:**
```bash
# Process multiple years in one run
python scripts/etl/extract_pbp_local.py --year-range 1997-2005
```

**6. Log output for troubleshooting:**
```bash
python scripts/etl/extract_pbp_local.py --year 2021 2>&1 | tee extract_pbp_2021.log
```

---

##### ⚠️ Troubleshooting

**Problem 1: No games found for year**

**Symptoms:**
```
⚠️  No games found for year 1997
```

**Solution:**
```bash
# Load schedule data first
python scripts/etl/extract_schedule_local.py --year 1997

# Verify
psql -c "SELECT COUNT(*) FROM games WHERE game_date >= '1997-01-01' AND game_date < '1998-01-01';"
```

**Root cause:** Games table not populated for this year

---

**Problem 2: Foreign key constraint violation**

**Symptoms:**
```
psycopg2.errors.ForeignKeyViolation: insert or update on table "play_by_play" violates foreign key constraint "play_by_play_game_id_fkey"
```

**Solution:**
```bash
# Verify games exist
psql -c "SELECT game_id FROM games LIMIT 10;"

# If missing, load schedule data
python scripts/etl/extract_schedule_local.py --year 1997

# Or temporarily drop constraint
psql -c "ALTER TABLE play_by_play DROP CONSTRAINT play_by_play_game_id_fkey;"
python scripts/etl/extract_pbp_local.py --year 1997
psql -c "ALTER TABLE play_by_play ADD CONSTRAINT play_by_play_game_id_fkey FOREIGN KEY (game_id) REFERENCES games(game_id);"
```

**Root cause:** Games table not populated before PBP extraction

---

**Problem 3: High skip rate (>20% games skipped)**

**Symptoms:**
```
Games skipped: 257
Errors: 12
```

**Solution:**
```bash
# Check S3 for missing files
aws s3 ls s3://nba-sim-raw-data-lake/pbp/ | wc -l

# Verify games exist in S3
psql -c "SELECT game_id FROM games WHERE game_date >= '1997-01-01' LIMIT 10;"
aws s3 ls s3://nba-sim-raw-data-lake/pbp/ | grep <game_id>

# Run comprehensive_data_analysis.py to check PBP availability
python scripts/analysis/comprehensive_data_analysis.py
```

**Root cause:** PBP files missing from S3 for some games (expected for older years)

---

**Problem 4: Slow performance (>30 minutes per year)**

**Symptoms:**
```
Progress: 100/1,189 games | 12,345 plays extracted
... [30 minutes later] ...
Progress: 200/1,189 games | 24,678 plays extracted
```

**Solution:**
```bash
# 1. Check network speed
aws s3 cp s3://nba-sim-raw-data-lake/pbp/401468215.json /tmp/ --debug

# 2. Use Glue for large ranges
python scripts/etl/create_glue_etl_job.py --data-type pbp

# 3. Process smaller year ranges
python scripts/etl/extract_pbp_local.py --year-range 1997-2000  # Instead of 1997-2021
```

**Root cause:** Network latency, large file sizes (PBP files 100-500KB each)

---

**Problem 5: Out of memory error**

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solution:**
```bash
# Process smaller year ranges (script loads all plays into memory)
python scripts/etl/extract_pbp_local.py --year 1997  # Instead of --year-range 1997-2021

# Or modify script to batch insert every 10,000 plays instead of all at once
# (requires code change)
```

**Root cause:** Loading 3M+ plays into memory for batch insert

---

##### 🔧 Technical Details

**Database schema (play_by_play table):**
```sql
CREATE TABLE play_by_play (
    play_id VARCHAR(20) PRIMARY KEY,
    game_id VARCHAR(20) REFERENCES games(game_id),
    period_number INTEGER,
    period_display VARCHAR(50),
    clock_display VARCHAR(10),
    play_text TEXT,
    home_away VARCHAR(10),
    scoring_play BOOLEAN,
    away_score INTEGER,
    home_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pbp_game_id ON play_by_play(game_id);
CREATE INDEX idx_pbp_period ON play_by_play(period_number);
CREATE INDEX idx_pbp_scoring ON play_by_play(scoring_play);
```

**Idempotency guarantee:**
- `ON CONFLICT (play_id) DO UPDATE` ensures script can be re-run safely
- Updates existing plays with latest data
- Created_at preserved, updated_at refreshed

**Performance characteristics:**
- **S3 download:** ~0.3s per file (network-bound)
- **JSON parsing:** ~0.02s per file (CPU-bound)
- **Database insert:** ~0.5s per batch of 10,000 plays (I/O-bound)
- **Total:** ~5-15 minutes per year (1,200 games × 0.3s ≈ 6 minutes)

**Memory usage:**
- **Peak:** ~500 MB (loads all year's plays into memory before insert)
- **Steady:** ~50 MB (Python interpreter + libraries)

**Error handling:**
- ✅ Missing environment variables → Exit with helpful message
- ✅ S3 access errors → Skip file, continue (NoSuchKey expected for some games)
- ✅ Malformed JSON → Log warning, continue
- ✅ Database errors → Rollback transaction, exit with error
- ✅ Duplicate play_ids → Deduplicate before insert

---

##### 🚀 Future Enhancements

**1. Batch insert during extraction (reduce memory):**
```python
# Insert every 10,000 plays instead of loading all into memory
BATCH_SIZE = 10000
if len(plays_to_insert) >= BATCH_SIZE:
    execute_values(cursor, insert_query, plays_to_insert[:BATCH_SIZE])
    plays_to_insert = plays_to_insert[BATCH_SIZE:]
```

**2. Parallel S3 downloads:**
```python
# Use concurrent.futures for faster downloads
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(download_and_parse_pbp, game_id) for game_id in game_ids]
    all_plays = [play for f in futures for play in f.result()]
```

**3. Enhanced play parsing (extract player names):**
```python
# Parse play_text to extract player names, action types
def parse_play_text(text):
    # "LeBron James makes 25-foot three point jumper (Anthony Davis assists)"
    # → player: "LeBron James", action: "makes 3pt", assist: "Anthony Davis"
    pass
```

**4. Progress persistence:**
```python
# Save progress to file, resume on failure
with open('extract_pbp_progress.json', 'w') as f:
    json.dump({'year': year, 'games_processed': processed_count}, f)
```

**5. Data quality metrics:**
```python
# Calculate play distribution stats
scoring_plays = sum(1 for p in plays if p['scoring_play'])
print(f"Scoring plays: {scoring_plays}/{len(plays)} ({scoring_plays/len(plays)*100:.1f}%)")
```

---

#### Overview: Year-Based Approach

**Why year-based partitioning?**
- **Problem:** Single Glue Crawler processing 146K files = timeouts, memory issues, slow performance
- **Solution:** Partition S3 data by year (33 folders: year=1993 to year=2025)
- **Benefit:** Each crawler processes ~4,400 files instead of 146K (manageable chunks)

**Pipeline stages:**
1. **Partition S3 data** by year (one-time operation)
2. **Create year-based crawlers** (33 crawlers per data type)
3. **Run crawlers** to populate Glue Data Catalog
4. **Run ETL jobs** year by year to load RDS

**Data types:** 4 types × 33 years = 132 partitions
- `schedule/` - Game schedules (1993-2025)
- `pbp/` - Play-by-play data (1997-2021)
- `box_scores/` - Box score statistics (1997-2021)
- `team_stats/` - Team statistics (1997-2021)

---

#### Workflow #1: Check Partition Status

**Script:** `scripts/shell/check_partition_status.sh`

**Purpose:** Monitor S3 partitioning progress and verify completion

**When to run:**
- During overnight partitioning to check progress
- After `partition_all_overnight.sh` completes
- To verify readiness before creating crawlers

**Usage:**
```bash
bash scripts/shell/check_partition_status.sh
```

**What this checks (4 sections):**

##### Section 1: Process Status
```bash
# Checks if partitioning processes still running
ps aux | grep "[p]artition_by_year.py"
```

**Possible outputs:**
```
⏳ Partitioning is STILL RUNNING

Active processes:
ryan   12345  partition_by_year.py --data-types schedule

To monitor progress:
  tail -f partition_overnight.log
```

OR

```
✅ Partitioning processes have COMPLETED
```

##### Section 2: Year Folders Created
```bash
# Counts year= folders in S3 for each data type
for data_type in schedule pbp box_scores team_stats; do
  aws s3 ls s3://nba-sim-raw-data-lake/${data_type}/ | grep "year="
done
```

**Sample output:**
```
Year Folders Created in S3
───────────────────────────────────────────────
✅ schedule: 33 year folders (COMPLETE)
✅ pbp: 25 year folders (COMPLETE)
⏳ box_scores: 18 year folders (IN PROGRESS)
⏸️  team_stats: 0 year folders (NOT STARTED)
```

**Interpretation:**
- **33 folders** = COMPLETE (schedule: 1993-2025)
- **25 folders** = COMPLETE (pbp/box/team: 1997-2021)
- **0-32 folders** = IN PROGRESS
- **0 folders** = NOT STARTED

##### Section 3: Log File Status
```bash
# Checks partition_overnight.log for completion markers
grep "ALL PARTITIONING COMPLETE" partition_overnight.log
```

**Possible outputs:**
```
✅ Log shows: ALL PARTITIONING COMPLETE
```

OR

```
❌ Log shows: Some partitioning FAILED

Failed sections:
  FAILED: box_scores partitioning (error: S3 access denied)
```

OR

```
⏳ Partitioning in progress

Last 5 lines:
  Copied 450 files to schedule/year=2015/
  Copied 500 files to schedule/year=2015/
  ...
```

##### Section 4: Summary & Next Steps
```bash
# Calculates total year folders: 132 expected (33×4)
total=$((schedule_count + pbp_count + box_count + team_count))
```

**100% Complete (132/132):**
```
Total year folders created: 132/132

🎉 PARTITIONING 100% COMPLETE!

Next steps:
  1. Create year-based crawlers:
     ./scripts/etl/create_year_crawlers.sh --all

  2. Test one crawler:
     aws glue start-crawler --name nba-schedule-1997-crawler
```

**Partial Progress (e.g., 87/132):**
```
Total year folders created: 87/132

⏳ PARTITIONING 66% COMPLETE

Monitor progress:
  tail -f partition_overnight.log
```

**Not Started (0/132):**
```
Total year folders created: 0/132

⚠️  PARTITIONING NOT STARTED

Start partitioning:
  nohup ./scripts/etl/partition_all_overnight.sh > partition_overnight.log 2>&1 &
```

**Integration:** Run this script frequently during overnight partitioning to monitor progress

---

#### Workflow #2: Partition All Data (Overnight)

**Script:** `scripts/etl/partition_all_overnight.sh`

**Purpose:** Automated overnight S3 partitioning for all 4 data types (schedule, pbp, box_scores, team_stats)

**When to run:** ONE-TIME operation before creating crawlers

**Critical:** This is a LONG-RUNNING operation (6-12 hours). Run overnight in background.

**Usage:**
```bash
# Start in background with logging
nohup bash scripts/etl/partition_all_overnight.sh > partition_overnight.log 2>&1 &

# Monitor progress (separate terminal)
tail -f partition_overnight.log

# Check process status
ps aux | grep partition

# Check partition status
bash scripts/shell/check_partition_status.sh
```

**What this does (4 steps):**

**Step 1: Partition Schedule Data**
```bash
# Calls partition_by_year.py for schedule data
echo "yes" | python scripts/etl/partition_by_year.py \
    --data-types "schedule" \
    --execute
```

**Partitions:** `schedule/*.json` → `schedule/year=YYYY/*.json` (33 years: 1993-2025)

**Step 2: Partition Play-by-Play Data**
```bash
echo "yes" | python scripts/etl/partition_by_year.py \
    --data-types "pbp" \
    --execute
```

**Partitions:** `pbp/*.json` → `pbp/year=YYYY/*.json` (25 years: 1997-2021)

**Step 3: Partition Box Scores**
```bash
echo "yes" | python scripts/etl/partition_by_year.py \
    --data-types "box_scores" \
    --execute
```

**Partitions:** `box_scores/*.json` → `box_scores/year=YYYY/*.json` (25 years)

**Step 4: Partition Team Stats**
```bash
echo "yes" | python scripts/etl/partition_by_year.py \
    --data-types "team_stats" \
    --execute
```

**Partitions:** `team_stats/*.json` → `team_stats/year=YYYY/*.json` (25 years)

**Script output:**
```
================================================================================
AUTOMATED S3 PARTITIONING - OVERNIGHT RUN
================================================================================
Started: 2025-10-02 23:00:00
Log file: /Users/ryanranft/nba-simulator-aws/partition_overnight.log

================================================================================
Partitioning: schedule
Started: 2025-10-02 23:00:05
================================================================================
Processing 33 years (1993-2025)...
  Year 1993: Copied 1234 files to schedule/year=1993/
  Year 1994: Copied 1189 files to schedule/year=1994/
  ...
  Year 2025: Copied 892 files to schedule/year=2025/

✅ SUCCESS: schedule partitioning completed
Completed: 2025-10-02 23:45:32

================================================================================
Partitioning: pbp
Started: 2025-10-02 23:45:35
================================================================================
[... continues for pbp, box_scores, team_stats ...]

================================================================================
ALL PARTITIONING COMPLETE
================================================================================
Finished: 2025-10-03 05:23:17

Verifying S3 structure...

Schedule years: 33
PBP years: 25
Box scores years: 25
Team stats years: 25

✅ Partitioning complete! Ready to create year-based crawlers.

Next steps:
1. Create year-based crawlers:
   ./scripts/etl/create_year_crawlers.sh --all

2. Run crawlers for a test year:
   aws glue start-crawler --name nba-schedule-1997-crawler
```

**Expected timeline:**
- **Schedule:** ~2-3 hours (most years, 1993-2025)
- **PBP:** ~1.5-2 hours
- **Box Scores:** ~1.5-2 hours
- **Team Stats:** ~1-1.5 hours
- **Total:** 6-9 hours (depends on S3 performance)

**Monitoring:**
```bash
# Check progress
tail -f partition_overnight.log

# Count partitioned files
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ | grep "year=" | wc -l

# Check specific year
aws s3 ls s3://nba-sim-raw-data-lake/schedule/year=2015/ --recursive | wc -l
```

**Troubleshooting:**

**Process killed/stopped:**
```bash
# Check log for errors
grep -i "error\|failed" partition_overnight.log

# Resume from specific data type (if schedule complete, start with pbp)
echo "yes" | python scripts/etl/partition_by_year.py --data-types "pbp" --execute
```

**S3 rate limiting:**
- Script includes automatic retry logic
- Wait 5 minutes, script will resume
- Check CloudWatch S3 metrics for throttling

**Verification after completion:**
```bash
bash scripts/shell/check_partition_status.sh
# Should show: 🎉 PARTITIONING 100% COMPLETE!
```

**Cost:** ~$0 (S3 copy operations are free for same-region, same-bucket)

---

#### Workflow #3: Create Year-Based Crawlers

**Script:** `scripts/etl/create_year_crawlers.sh`

**Purpose:** Create Glue Crawlers for each year partition (avoid 146K-file overload)

**Prerequisites:** Partitioning complete (132/132 folders created)

**Usage options:**

**Option 1: Create all crawlers (recommended)**
```bash
bash scripts/etl/create_year_crawlers.sh --all
```

Creates 100+ crawlers:
- 33 crawlers for schedule (1993-2025)
- 25 crawlers for pbp (1997-2021)
- 25 crawlers for box_scores (1997-2021)
- 25 crawlers for team_stats (1997-2021)

**Option 2: Create crawlers for specific data type and years**
```bash
# Schedule data: 1997-2021
bash scripts/etl/create_year_crawlers.sh --data-type schedule --years 1997-2021

# PBP data: 2015-2021 only
bash scripts/etl/create_year_crawlers.sh --data-type pbp --years 2015-2021
```

**Option 3: Dry-run (preview without creating)**
```bash
bash scripts/etl/create_year_crawlers.sh --all --dry-run
```

**What this does:**

**For each year:**
1. Checks if crawler already exists (skips if exists)
2. Creates crawler with naming convention: `nba-{data_type}-{year}-crawler`
3. Configures S3 target: `s3://nba-sim-raw-data-lake/{data_type}/year={year}/`
4. Links to database: `nba_raw_data`
5. Uses IAM role: `AWSGlueServiceRole-NBASimulator`

**Sample output:**
```
================================================================
Year-Based Glue Crawler Creation
================================================================
Bucket: nba-sim-raw-data-lake
Database: nba_raw_data
Role: AWSGlueServiceRole-NBASimulator
Years: 1997-2021
Mode: EXECUTE (crawlers will be created)

================================================================
Creating crawlers for: SCHEDULE
Years: 1997 to 2021
================================================================

✓ Creating crawler: nba-schedule-1997-crawler
    S3 Path: s3://nba-sim-raw-data-lake/schedule/year=1997/
✓ Creating crawler: nba-schedule-1998-crawler
    S3 Path: s3://nba-sim-raw-data-lake/schedule/year=1998/
[... continues for all years ...]

✓ Created 25 crawlers for schedule

================================================================
Creating crawlers for: PBP
Years: 1997 to 2021
================================================================
[... continues for pbp, box_scores, team_stats ...]

================================================================
SUMMARY
================================================================
CRAWLERS CREATED SUCCESSFULLY

Next steps:
1. List all crawlers:
   aws glue list-crawlers --query 'CrawlerNames' --output table

2. Start a specific crawler:
   aws glue start-crawler --name nba-schedule-1997-crawler

3. Start all crawlers for a year (e.g., 1997):
   for crawler in $(aws glue list-crawlers --query 'CrawlerNames[?contains(@, `1997`)]' --output text); do
     aws glue start-crawler --name $crawler
   done

4. Monitor crawler status:
   aws glue get-crawler --name nba-schedule-1997-crawler
```

**Verify crawlers created:**
```bash
# Count total crawlers
aws glue list-crawlers --query 'CrawlerNames' | grep "nba-" | wc -l
# Should show: 108 (33+25+25+25)

# List schedule crawlers
aws glue list-crawlers --query 'CrawlerNames[?starts_with(@, `nba-schedule`)]' --output table

# Get specific crawler details
aws glue get-crawler --name nba-schedule-1997-crawler
```

**Cost:** ~$0 (creating crawlers is free, running them costs ~$0.44/DPU-hour)

---

#### Workflow #4: Run Crawlers (Overnight)

**Script:** `scripts/etl/run_crawlers_overnight.sh`

**Purpose:** Automatically run all year-based crawlers with AWS service limit management (max 10 concurrent)

**Prerequisites:**
- Partitioning complete (132/132)
- Crawlers created (~108 crawlers)

**Usage:**
```bash
# Start in background
nohup bash scripts/etl/run_crawlers_overnight.sh > crawler_overnight.log 2>&1 &

# Monitor progress
tail -f crawler_overnight.log

# Check running crawlers
aws glue list-crawlers --query 'CrawlerNames' | xargs -I {} aws glue get-crawler --name {} --query 'Crawler.{Name:Name,State:State}' --output table
```

**What this does (intelligent crawler orchestration):**

**Strategy:**
1. Wait for each year partition to be ready (files exist in S3)
2. Create crawler if doesn't exist (auto-creates missing crawlers)
3. Start crawler (respects AWS 10-concurrent-crawler limit)
4. Process all years (1993-2025) for all data types

**Concurrency management:**
```bash
# AWS Glue limit: 10 concurrent crawlers per account
# Script automatically waits if 10 running:
wait_for_crawlers() {
  while [ $(running_count) -ge 10 ]; do
    echo "⏳ 10 crawlers running, waiting 60 seconds..."
    sleep 60
  done
}
```

**Sample output:**
```
================================================================================
AUTOMATED GLUE CRAWLER EXECUTION - OVERNIGHT RUN
================================================================================
Started: 2025-10-03 18:00:00
Log file: /Users/ryanranft/nba-simulator-aws/crawler_overnight.log

Strategy:
  1. Wait for each year partition to be ready in S3
  2. Create crawler if it doesn't exist
  3. Start crawler (max 10 concurrent)
  4. Repeat for all years (1993-2025) and all data types

Expected timeline:
  - Schedule: 33 years × ~5 min = ~2.5 hours
  - PBP: 25 years × ~5 min = ~2 hours
  - Box Scores: 25 years × ~5 min = ~2 hours
  - Team Stats: 25 years × ~5 min = ~2 hours
  Total: ~8-10 hours (with parallelization: ~3-4 hours)

================================================================================
Processing: SCHEDULE
================================================================================

Year 1997:
  ✓ Crawler exists: nba-schedule-1997-crawler
  ▶️  Starting: nba-schedule-1997-crawler

Year 1998:
  ✓ Crawler exists: nba-schedule-1998-crawler
  ▶️  Starting: nba-schedule-1998-crawler
[... starts 10 crawlers ...]

  ⏳ 10 crawlers running, waiting 60 seconds...
[... waits for slot to open ...]

  ▶️  Starting: nba-schedule-2007-crawler

Summary for schedule:
  Started: 33 crawlers
  Skipped: 0 crawlers

================================================================================
Processing: PBP
================================================================================
[... continues for pbp, box_scores, team_stats ...]

================================================================================
ALL CRAWLERS STARTED
================================================================================
Finished: 2025-10-03 22:15:42

Waiting for all crawlers to complete...

⏳ 7 crawlers still running... (checking again in 2 minutes)
⏳ 3 crawlers still running... (checking again in 2 minutes)
✅ All crawlers completed!

================================================================================
FINAL SUMMARY
================================================================================

Glue Tables Created:
  schedule: 33 tables
  pbp: 25 tables
  box_scores: 25 tables
  team_stats: 25 tables

✅ Crawler execution complete! Ready for Phase 2.2 (Glue ETL).
```

**Expected timeline:**
- **With 10-crawler concurrency:** ~3-4 hours
- **Sequential (no concurrency):** ~8-10 hours
- **Per crawler:** ~3-5 minutes (depends on file count)

**Monitoring commands:**
```bash
# Count running crawlers
aws glue list-crawlers --query 'CrawlerNames' | xargs -I {} aws glue get-crawler --name {} --query 'Crawler.State' --output text | grep -c "RUNNING"

# List crawler states
aws glue list-crawlers --query 'CrawlerNames' | xargs -I {} aws glue get-crawler --name {} --query 'Crawler.{Name:Name,State:State}'

# Check specific crawler
aws glue get-crawler --name nba-schedule-1997-crawler --query 'Crawler.{State:State,LastCrawl:LastCrawl}'
```

**Verify Glue tables created:**
```bash
# Count tables
aws glue get-tables --database-name nba_raw_data --query 'TableList[*].Name' | wc -l
# Should show: ~108 tables

# List schedule tables
aws glue get-tables --database-name nba_raw_data --query "TableList[?starts_with(Name, 'schedule')].Name"
```

**Cost:** ~$1-2 total (108 crawlers × ~5 min × $0.44/DPU-hour)

---

#### Workflow #5: Process Year-by-Year (Alternative Sequential Approach)

**Script:** `scripts/etl/process_year_by_year.sh`

**Purpose:** Alternative approach - partition AND crawl one year at a time (more sequential)

**When to use:**
- More predictable resource usage
- Easier to debug year-specific issues
- Prefer sequential over parallel processing
- Want tighter control over execution

**Difference from Workflow #2 + #4:**
- **Workflows #2 & #4:** Partition ALL years first, then crawl ALL years (parallel)
- **Workflow #5:** For each year: partition THEN crawl (sequential)

**Usage:**
```bash
nohup bash scripts/etl/process_year_by_year.sh > year_by_year.log 2>&1 &
```

**What this does:**

**For each year (1993-2025):**
1. **Partition** all 4 data types for this year
2. **Crawl** all 4 data types for this year
3. Move to next year

**Sample output:**
```
================================================================================
YEAR-BY-YEAR S3 PARTITIONING AND CRAWLER EXECUTION
================================================================================
Started: 2025-10-03 18:00:00

Strategy: Process one year at a time
  1. Partition all 4 data types for year N
  2. Crawl all 4 data types for year N
  3. Move to year N+1

Data types: schedule, pbp, box_scores, team_stats
Years: 1993-2025

================================================================================
YEAR 1997
================================================================================

--- Step 1: Partitioning data for year 1997 ---
  Partitioning schedule for year 1997...
    Copied 1234 files...
  ✅ Copied 1234 files for schedule/year=1997

  Partitioning pbp for year 1997...
    Copied 892 files...
  ✅ Copied 892 files for pbp/year=1997

  Partitioning box_scores for year 1997...
    Copied 1456 files...
  ✅ Copied 1456 files for box_scores/year=1997

  Partitioning team_stats for year 1997...
    Copied 234 files...
  ✅ Copied 234 files for team_stats/year=1997

--- Step 2: Crawling data for year 1997 ---
  Creating crawler: nba-schedule-1997-crawler
  Starting crawler: nba-schedule-1997-crawler
  Waiting for crawler to complete...
  ✅ Crawler completed: nba-schedule-1997-crawler

  Creating crawler: nba-pbp-1997-crawler
  Starting crawler: nba-pbp-1997-crawler
  ✅ Crawler completed: nba-pbp-1997-crawler

  Creating crawler: nba-box_scores-1997-crawler
  ✅ Crawler completed: nba-box_scores-1997-crawler

  Creating crawler: nba-team_stats-1997-crawler
  ✅ Crawler completed: nba-team_stats-1997-crawler

✅ Year 1997 complete!

================================================================================
YEAR 1998
================================================================================
[... continues for 1998-2025 ...]

================================================================================
ALL YEARS PROCESSED
================================================================================
Finished: 2025-10-04 06:23:45

Summary:
  Year folders created:
    schedule: 33
    pbp: 25
    box_scores: 25
    team_stats: 25

  Glue tables created:
    schedule: 33
    pbp: 25
    box_scores: 25
    team_stats: 25

✅ Complete! Ready for Phase 2.2 (Glue ETL).
```

**Expected timeline:** ~12-16 hours (fully sequential)

**Trade-offs:**

| Aspect | Year-by-Year (Workflow #5) | Partition All + Crawl All (Workflows #2 & #4) |
|--------|---------------------------|----------------------------------------------|
| **Speed** | Slower (~12-16 hours) | Faster (~6-9 hours) |
| **Concurrency** | Sequential (1 year at a time) | Parallel (10 crawlers at once) |
| **Debugging** | Easy (isolated per year) | Harder (multiple years in flight) |
| **Resource usage** | Predictable | Variable |
| **Best for** | Cautious first run, debugging | Production, speed-focused |

**When to use Workflow #5:**
- First time running pipeline (want to verify each year)
- Debugging year-specific data issues
- Limited resources/prefer sequential
- Want to process specific year range only

---

#### Workflow #6: Run ETL Jobs (All Years)

**Script:** `scripts/etl/run_etl_all_years.sh`

**Purpose:** Execute Glue ETL jobs year-by-year to load data from S3 (via Glue Catalog) into RDS PostgreSQL

**Prerequisites:**
- Partitioning complete (132/132)
- Crawlers run successfully (~108 tables in Glue Catalog)
- RDS instance created and accessible
- Glue ETL job created: `nba-schedule-etl-job`

**Usage:**
```bash
# Ensure DB password is set
source /Users/ryanranft/nba-sim-credentials.env

# Start ETL processing
nohup bash scripts/etl/run_etl_all_years.sh > etl_all_years.log 2>&1 &

# Monitor progress
tail -f etl_all_years.log
```

**What this does:**

**For each year (1993-2025):**
1. Start Glue ETL job with `--year` parameter
2. Job reads from Glue Catalog table (e.g., `schedule_year_1997`)
3. Transform and validate data
4. Load to RDS `games` table
5. Wait for job completion (max 20 minutes per year)
6. Report success/failure
7. Continue to next year

**Sample output:**
```
================================================================================
GLUE ETL JOB EXECUTION - ALL YEARS
================================================================================
Started: 2025-10-04 08:00:00

Job: nba-schedule-etl-job
Years: 1993-2025

================================================================================
PROCESSING YEAR 1997
================================================================================

--- Year 1997 ---
  Starting job run...
  ▶️  Job started: jr_a1b2c3d4e5f6...

  ⏳ Job RUNNING (10s elapsed)...
  ⏳ Job RUNNING (20s elapsed)...
  ⏳ Job RUNNING (30s elapsed)...
  ✅ Job completed successfully!
     Execution time: 45s

✅ Year 1997 complete!

================================================================================
PROCESSING YEAR 1998
================================================================================
[... continues for 1998-2025 ...]

================================================================================
PROCESSING YEAR 2015
================================================================================

--- Year 2015 ---
  Starting job run...
  ▶️  Job started: jr_x9y8z7...

  ⏳ Job RUNNING (10s elapsed)...
  ❌ Job failed!
     Status: FAILED
     Error: Table schedule_year_2015 not found in Glue Catalog

❌ Year 2015 failed!
   Continuing to next year...

[... continues despite failures ...]

================================================================================
ETL PROCESSING COMPLETE
================================================================================
Finished: 2025-10-04 09:15:32

Summary:
  ✅ Successful: 32 years
  ❌ Failed: 1 years
  📊 Total: 33 years

Checking database for loaded games...

Database Statistics:
 season_year | game_count | first_game | last_game
-------------+------------+------------+-----------
        1997 |       1189 | 1997-10-31 | 1998-06-14
        1998 |       1145 | 1998-10-27 | 1999-06-25
        ...  |        ... | ...        | ...
        2021 |       1080 | 2020-12-22 | 2021-07-20

 total_games | seasons | earliest_game | latest_game
-------------+---------+---------------+-------------
       38234 |      32 |    1997-10-31 | 2021-07-20

✅ All years processed!
```

**Expected timeline:**
- **Per year:** ~30-60 seconds (depends on data volume)
- **Total (33 years):** ~30-45 minutes

**Job monitoring:**
```bash
# List recent job runs
aws glue get-job-runs --job-name nba-schedule-etl-job --max-results 10

# Check specific job run
aws glue get-job-run --job-name nba-schedule-etl-job --run-id jr_xxxxx

# View CloudWatch logs
aws logs tail /aws-glue/jobs/output --follow
```

**Verify data loaded to RDS:**
```bash
# Connect to RDS
psql -h nba-sim-db.xxx.rds.amazonaws.com -U postgres -d nba_simulator

# Check row counts
SELECT season_year, COUNT(*) as game_count
FROM games
GROUP BY season_year
ORDER BY season_year;

# Verify date ranges
SELECT MIN(game_date), MAX(game_date) FROM games;

# Check for missing years
SELECT generate_series(1997, 2021) AS year
EXCEPT
SELECT DISTINCT season_year FROM games
ORDER BY year;
```

**Troubleshooting:**

**Job fails with "Table not found":**
- Crawler didn't run for that year
- Check: `aws glue get-tables --database-name nba_raw_data --query "TableList[?contains(Name, '1997')]"`
- Fix: Re-run crawler for that year

**Job fails with "Access denied to S3":**
- Glue IAM role missing S3 permissions
- Fix: Add S3ReadOnlyAccess to `AWSGlueServiceRole-NBASimulator`

**Job timeout (>20 minutes):**
- Too much data for allocated DPUs
- Fix: Increase DPUs in job definition (2 → 5 DPU)

**Cost:** ~$0.30-0.50 per year × 33 years = ~$10-15 total (2 DPU × ~45 sec/year × $0.44/DPU-hour)

---

### Phase 2.2 Complete Workflow Summary

**Sequential execution order:**

1. **Check Partition Status** (pre-flight check)
   ```bash
   bash scripts/shell/check_partition_status.sh
   ```

2. **Partition All Data** (one-time, 6-12 hours)
   ```bash
   nohup bash scripts/etl/partition_all_overnight.sh > partition_overnight.log 2>&1 &
   ```

3. **Create Year Crawlers** (one-time, <5 minutes)
   ```bash
   bash scripts/etl/create_year_crawlers.sh --all
   ```

4. **Run Crawlers** (one-time, 3-4 hours)
   ```bash
   nohup bash scripts/etl/run_crawlers_overnight.sh > crawler_overnight.log 2>&1 &
   ```

5. **Run ETL Jobs** (one-time, 30-45 minutes)
   ```bash
   nohup bash scripts/etl/run_etl_all_years.sh > etl_all_years.log 2>&1 &
   ```

6. **Verify Complete Pipeline**
   ```bash
   # S3 partitions
   bash scripts/shell/check_partition_status.sh
   # Should show: 132/132

   # Glue tables
   aws glue get-tables --database-name nba_raw_data --query 'TableList[*].Name' | wc -l
   # Should show: ~108

   # RDS games
   psql -h <endpoint> -U postgres -d nba_simulator -c "SELECT COUNT(*) FROM games;"
   # Should show: ~38,000 games
   ```

**Total pipeline time:** ~10-16 hours (overnight recommended)

**Total cost:** ~$15-20 (one-time)

**After completion:** Ready for Phase 3 (simulation and analysis)

### Phase 3: RDS PostgreSQL Setup

**See PROGRESS.md Phase 3.1 (lines 606-743)**

1. **Create DB subnet group** (if not exists):
   ```bash
   aws rds create-db-subnet-group \
     --db-subnet-group-name nba-sim-subnet-group \
     --db-subnet-group-description "Subnet group for NBA simulator RDS" \
     --subnet-ids subnet-xxxxx subnet-yyyyy
   ```

2. **Create security group**:
   ```bash
   aws ec2 create-security-group \
     --group-name nba-sim-rds-sg \
     --description "Security group for NBA RDS" \
     --vpc-id vpc-xxxxx

   # Allow PostgreSQL access (port 5432)
   aws ec2 authorize-security-group-ingress \
     --group-id sg-xxxxx \
     --protocol tcp \
     --port 5432 \
     --cidr 0.0.0.0/0  # CAUTION: Restrict in production
   ```

3. **Create RDS instance**:
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier nba-sim-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --engine-version 15.3 \
     --master-username admin \
     --master-user-password <STRONG_PASSWORD> \
     --allocated-storage 20 \
     --storage-type gp2 \
     --vpc-security-group-ids sg-xxxxx \
     --db-subnet-group-name nba-sim-subnet-group \
     --publicly-accessible \
     --backup-retention-period 7 \
     --preferred-backup-window "03:00-04:00" \
     --preferred-maintenance-window "mon:04:00-mon:05:00"
   ```

4. **Wait for availability** (10-15 min):
   ```bash
   aws rds wait db-instance-available --db-instance-identifier nba-sim-db
   ```

5. **Get endpoint**:
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier nba-sim-db \
     --query 'DBInstances[0].Endpoint.Address' \
     --output text
   ```

6. **Test connection**:
   ```bash
   psql -h <endpoint> -U admin -d postgres -c "SELECT version();"
   ```

7. **Create database**:
   ```sql
   CREATE DATABASE nba_sim;
   ```

8. **Document endpoint** in PROGRESS.md and .env file

**Cost:** ~$29/month (db.t3.micro, 20GB storage)
**Rollback:** `aws rds delete-db-instance --db-instance-identifier nba-sim-db --skip-final-snapshot`

### Phase 3: AWS Glue ETL Job Setup

**See PROGRESS.md Phase 3.2 (lines 744-862)**

1. **Upload ETL script to S3**:
   ```bash
   aws s3 cp scripts/glue/etl_job.py s3://nba-sim-raw-data-lake/scripts/
   ```

2. **Create Glue job**:
   ```bash
   aws glue create-job \
     --name nba-etl-job \
     --role AWSGlueServiceRole-NBA \
     --command Name=glueetl,ScriptLocation=s3://nba-sim-raw-data-lake/scripts/etl_job.py \
     --default-arguments '{
       "--TempDir":"s3://nba-sim-raw-data-lake/temp/",
       "--job-bookmark-option":"job-bookmark-enable",
       "--enable-metrics":"true"
     }' \
     --glue-version "4.0" \
     --number-of-workers 2 \
     --worker-type G.1X
   ```

3. **Run job**:
   ```bash
   aws glue start-job-run --job-name nba-etl-job
   ```

4. **Monitor job run**:
   ```bash
   aws glue get-job-run \
     --job-name nba-etl-job \
     --run-id jr_xxxxx \
     --query 'JobRun.{State:JobRunState,Duration:ExecutionTime}'
   ```

5. **Check CloudWatch logs** for errors:
   ```bash
   aws logs tail /aws-glue/jobs/output --follow
   ```

**Cost:** ~$0.44/hour (2 DPU G.1X workers)

### Phase 4: EC2 Instance Setup (Optional)

**See PROGRESS.md Phase 4 (simulation host)**

1. **Launch instance**:
   ```bash
   aws ec2 run-instances \
     --image-id ami-xxxxx \  # Amazon Linux 2023
     --instance-type t2.micro \
     --key-name my-key-pair \
     --security-group-ids sg-xxxxx \
     --subnet-id subnet-xxxxx \
     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=nba-sim-host}]'
   ```

2. **Wait for running state**:
   ```bash
   aws ec2 wait instance-running --instance-ids i-xxxxx
   ```

3. **Get public IP**:
   ```bash
   aws ec2 describe-instances \
     --instance-ids i-xxxxx \
     --query 'Reservations[0].Instances[0].PublicIpAddress' \
     --output text
   ```

4. **SSH into instance**:
   ```bash
   ssh -i ~/.ssh/my-key-pair.pem ec2-user@<PUBLIC_IP>
   ```

5. **Install dependencies**:
   ```bash
   sudo yum update -y
   sudo yum install -y python3 postgresql
   pip3 install boto3 psycopg2-binary pandas
   ```

6. **Test RDS connection** from EC2:
   ```bash
   psql -h <rds-endpoint> -U admin -d nba_sim -c "SELECT 1;"
   ```

**Cost:** ~$8-15/month (t2.micro, variable hours)
**Stop when not in use:** `aws ec2 stop-instances --instance-ids i-xxxxx`

### Phase 5: SageMaker Notebook Setup

**See PROGRESS.md Phase 5 (ML training)**

1. **Create notebook instance**:
   ```bash
   aws sagemaker create-notebook-instance \
     --notebook-instance-name nba-ml-notebook \
     --instance-type ml.t3.medium \
     --role-arn arn:aws:iam::ACCOUNT_ID:role/SageMakerRole \
     --volume-size-in-gb 10
   ```

2. **Wait for InService status**:
   ```bash
   aws sagemaker describe-notebook-instance \
     --notebook-instance-name nba-ml-notebook \
     --query 'NotebookInstanceStatus'
   ```

3. **Get presigned URL**:
   ```bash
   aws sagemaker create-presigned-notebook-instance-url \
     --notebook-instance-name nba-ml-notebook
   ```

4. **Open Jupyter** in browser (URL from step 3)

5. **Install additional packages**:
   ```bash
   !pip install scikit-learn xgboost lightgbm shap
   ```

6. **Test S3 and RDS connectivity** from notebook

**Cost:** ~$50/month (ml.t3.medium running 24/7)
**Stop when not in use:** `aws sagemaker stop-notebook-instance --notebook-instance-name nba-ml-notebook`

**See PROGRESS.md for complete AWS resource specifications and costs**

---

