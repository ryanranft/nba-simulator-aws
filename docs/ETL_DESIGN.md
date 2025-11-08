# ETL Design: master → raw_data Migration

**Date:** November 5, 2025
**Purpose:** Migrate 14.2M rows from legacy master schema to production raw_data schema
**Effort:** 1-3 days

---

## Source Schema: master (Legacy)

### Table 1: master.nba_games (31,241 rows, 9.3 MB)

**Structure:**
```sql
game_id           VARCHAR(20) PRIMARY KEY
game_date         TIMESTAMP WITH TIME ZONE
season            VARCHAR(10)
home_team         VARCHAR(100)
away_team         VARCHAR(100)
home_abbrev       VARCHAR(10)
away_abbrev       VARCHAR(10)
final_score_home  INTEGER
final_score_away  INTEGER
source            VARCHAR(20) DEFAULT 'ESPN'
created_at        TIMESTAMP WITH TIME ZONE
updated_at        TIMESTAMP WITH TIME ZONE
```

**Sample data:**
```
game_id: 270227011
game_date: 2007-02-27 18:00:00-06
season: 2006-07
home_team: Indiana Pacers
away_team: Phoenix Suns
home_abbrev: IND
away_abbrev: PHX
final_score_home: 92
final_score_away: 103
source: ESPN
```

---

### Table 2: master.nba_plays (14,114,618 rows, 3.5 GB)

**Structure:**
```sql
id               BIGINT PRIMARY KEY
game_id          VARCHAR(20)
play_id          VARCHAR(50)
sequence_number  INTEGER
period           INTEGER
clock            VARCHAR(20)
team_abbrev      VARCHAR(10)
player_name      VARCHAR(100)
event_type       VARCHAR(100)
description      TEXT
score_value      INTEGER
home_score       INTEGER
away_score       INTEGER
created_at       TIMESTAMP WITH TIME ZONE
```

**Sample data:**
```
game_id: 270227011
sequence_number: 2
period: 1
clock: 12:00
event_type: Other
description: Jumpball: Amare Stoudemire vs. Jermaine O'Neal (Raja Bell gains possession)
home_score: 0
away_score: 0
```

---

### Table 3: master.espn_file_validation (44,826 rows, 17 MB)

**Structure:**
```sql
file_name             VARCHAR(100) PRIMARY KEY
game_id               VARCHAR(20)
has_pbp_data          BOOLEAN
has_game_info         BOOLEAN
has_team_data         BOOLEAN
game_date             TIMESTAMP WITH TIME ZONE
season                VARCHAR(10)
league                VARCHAR(20)
home_team             VARCHAR(100)
away_team             VARCHAR(100)
play_count            INTEGER
file_size_bytes       BIGINT
validation_timestamp  TIMESTAMP WITH TIME ZONE
error_message         TEXT
```

---

## Target Schema: raw_data (Production)

### Table 1: raw_data.nba_games

**Structure:**
```sql
id            SERIAL PRIMARY KEY
game_id       VARCHAR(50) UNIQUE NOT NULL
source        VARCHAR(20) NOT NULL
season        VARCHAR(20) NOT NULL
game_date     DATE NOT NULL
collected_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
data          JSONB NOT NULL              -- Game details
metadata      JSONB DEFAULT '{}'::jsonb   -- Collection metadata
```

**JSONB data column structure:**
```json
{
  "game_info": {
    "game_id": "270227011",
    "game_date": "2007-02-27T18:00:00-06:00",
    "season": "2006-07"
  },
  "teams": {
    "home": {
      "name": "Indiana Pacers",
      "abbreviation": "IND",
      "score": 92
    },
    "away": {
      "name": "Phoenix Suns",
      "abbreviation": "PHX",
      "score": 103
    }
  },
  "play_by_play": {
    "total_plays": 453,
    "plays": [
      {
        "sequence": 1,
        "period": 1,
        "clock": "12:00",
        "event_type": "Other",
        "description": "Start of the 1st Quarter",
        "home_score": 0,
        "away_score": 0
      },
      ...
    ]
  },
  "source_data": {
    "original_game_id": "270227011",
    "source": "ESPN"
  }
}
```

**JSONB metadata column structure:**
```json
{
  "collection": {
    "collected_at": "2025-10-13T16:00:14-05:00",
    "updated_at": "2025-10-13T16:05:33-05:00",
    "source_system": "ESPN"
  },
  "migration": {
    "migrated_at": "2025-11-05T14:00:00-06:00",
    "migrated_from": "master.nba_games",
    "migration_version": "1.0.0"
  },
  "validation": {
    "has_play_by_play": true,
    "play_count": 453,
    "validated_at": "2025-10-13T16:05:33-05:00"
  }
}
```

---

### Table 2: raw_data.nba_misc

**Purpose:** Store ESPN file validation records

**JSONB data structure:**
```json
{
  "file_info": {
    "file_name": "161214026.json",
    "file_size_bytes": 687759,
    "validation_timestamp": "2025-10-13T16:02:47-05:00"
  },
  "validation": {
    "has_pbp_data": false,
    "has_game_info": true,
    "has_team_data": true,
    "play_count": 0,
    "error_message": null
  },
  "game_reference": {
    "game_id": "161214026",
    "season": "1996-97",
    "league": "NBA",
    "game_date": "1996-12-14T18:00:00-06:00",
    "home_team": "Utah Jazz",
    "away_team": "Orlando Magic"
  }
}
```

---

## Transformation Logic

### Step 1: master.nba_games → raw_data.nba_games

**Mapping:**
```python
{
  # Top-level fields (for indexing)
  "game_id": master.game_id,
  "source": master.source or "ESPN",
  "season": master.season,
  "game_date": master.game_date::date,
  "collected_at": master.created_at,
  "updated_at": master.updated_at,

  # JSONB data column
  "data": {
    "game_info": {
      "game_id": master.game_id,
      "game_date": master.game_date,
      "season": master.season
    },
    "teams": {
      "home": {
        "name": master.home_team,
        "abbreviation": master.home_abbrev,
        "score": master.final_score_home
      },
      "away": {
        "name": master.away_team,
        "abbreviation": master.away_abbrev,
        "score": master.final_score_away
      }
    },
    "source_data": {
      "original_game_id": master.game_id,
      "source": master.source
    }
  },

  # JSONB metadata column
  "metadata": {
    "collection": {
      "collected_at": master.created_at,
      "updated_at": master.updated_at,
      "source_system": master.source
    },
    "migration": {
      "migrated_at": now(),
      "migrated_from": "master.nba_games",
      "migration_version": "1.0.0"
    }
  }
}
```

---

### Step 2: Enrich with master.nba_plays (14M rows)

**Strategy:** Aggregate plays by game_id and embed in JSONB

**Aggregation query:**
```sql
SELECT
  game_id,
  COUNT(*) as total_plays,
  json_agg(
    json_build_object(
      'sequence', sequence_number,
      'period', period,
      'clock', clock,
      'team_abbrev', team_abbrev,
      'player_name', player_name,
      'event_type', event_type,
      'description', description,
      'score_value', score_value,
      'home_score', home_score,
      'away_score', away_score
    ) ORDER BY sequence_number
  ) as plays
FROM master.nba_plays
GROUP BY game_id;
```

**Decision:**
- **Option A (Full embedding):** Embed all plays in data.play_by_play.plays array
  - Pros: Complete game data in one record
  - Cons: Large JSONB (100KB-500KB per game), slower queries

- **Option B (Summary only):** Only embed play count/summary, keep plays separate
  - Pros: Smaller JSONB, faster queries
  - Cons: Plays data not in production schema

- **Option C (Top N plays):** Embed first/last 100 plays + summary
  - Pros: Balance of completeness and performance
  - Cons: Some data loss

**Recommendation:** Start with **Option B** (summary only) for initial migration. Can enhance to Option A or C later.

---

### Step 3: master.espn_file_validation → raw_data.nba_misc

**Mapping:**
```python
{
  "source": "ESPN",
  "data_type": "file_validation",
  "collected_at": master.validation_timestamp,
  "data": {
    "file_info": {
      "file_name": master.file_name,
      "file_size_bytes": master.file_size_bytes,
      "validation_timestamp": master.validation_timestamp
    },
    "validation": {
      "has_pbp_data": master.has_pbp_data,
      "has_game_info": master.has_game_info,
      "has_team_data": master.has_team_data,
      "play_count": master.play_count,
      "error_message": master.error_message
    },
    "game_reference": {
      "game_id": master.game_id,
      "season": master.season,
      "league": master.league,
      "game_date": master.game_date,
      "home_team": master.home_team,
      "away_team": master.away_team
    }
  },
  "metadata": {
    "migration": {
      "migrated_at": now(),
      "migrated_from": "master.espn_file_validation",
      "migration_version": "1.0.0"
    }
  }
}
```

---

## ETL Implementation Plan

### Phase 1: Games Migration (31K rows)

**Batch size:** 1,000 games per batch
**Estimated time:** 5-10 minutes
**SQL template:**
```sql
INSERT INTO raw_data.nba_games (
  game_id, source, season, game_date,
  collected_at, updated_at, data, metadata
)
SELECT
  game_id,
  COALESCE(source, 'ESPN'),
  season,
  game_date::date,
  created_at,
  updated_at,
  jsonb_build_object(
    'game_info', jsonb_build_object(...),
    'teams', jsonb_build_object(...),
    'source_data', jsonb_build_object(...)
  ),
  jsonb_build_object(
    'collection', jsonb_build_object(...),
    'migration', jsonb_build_object(...)
  )
FROM master.nba_games
WHERE game_id = ANY($1);  -- Batch of game_ids
```

---

### Phase 2: Play Summary Enhancement (31K games)

**Batch size:** 100 games per batch (heavy aggregation)
**Estimated time:** 30-60 minutes

**For each game:**
```sql
UPDATE raw_data.nba_games
SET
  data = jsonb_set(
    data,
    '{play_by_play}',
    jsonb_build_object(
      'total_plays', (SELECT COUNT(*) FROM master.nba_plays WHERE game_id = $1),
      'summary', jsonb_build_object(
        'periods', (SELECT MAX(period) FROM master.nba_plays WHERE game_id = $1),
        'event_types', (SELECT jsonb_object_agg(event_type, count) FROM ...)
      )
    )
  ),
  metadata = jsonb_set(
    metadata,
    '{validation,play_count}',
    to_jsonb((SELECT COUNT(*) FROM master.nba_plays WHERE game_id = $1))
  )
WHERE game_id = $1;
```

---

### Phase 3: File Validation Migration (45K rows)

**Batch size:** 5,000 records per batch
**Estimated time:** 5-10 minutes

**SQL template:**
```sql
INSERT INTO raw_data.nba_misc (
  source, data_type, collected_at, data, metadata
)
SELECT
  'ESPN',
  'file_validation',
  validation_timestamp,
  jsonb_build_object(...),
  jsonb_build_object(...)
FROM master.espn_file_validation
WHERE file_name = ANY($1);  -- Batch of file names
```

---

## Validation Strategy

### Row Count Validation
```sql
-- Games
SELECT COUNT(*) FROM master.nba_games;        -- Expected: 31,241
SELECT COUNT(*) FROM raw_data.nba_games;      -- Should match

-- File validation
SELECT COUNT(*) FROM master.espn_file_validation;  -- Expected: 44,826
SELECT COUNT(*) FROM raw_data.nba_misc
WHERE (data->>'data_type') = 'file_validation';    -- Should match
```

### Data Quality Checks
```sql
-- Check NULL values
SELECT COUNT(*) FROM raw_data.nba_games WHERE data IS NULL;  -- Should be 0
SELECT COUNT(*) FROM raw_data.nba_games WHERE metadata IS NULL;  -- Should be 0

-- Check required fields in JSONB
SELECT COUNT(*) FROM raw_data.nba_games
WHERE NOT (data ? 'game_info' AND data ? 'teams');  -- Should be 0

-- Check play counts match
SELECT
  g.game_id,
  COUNT(p.id) as master_play_count,
  (g.data->'play_by_play'->>'total_plays')::int as raw_data_play_count
FROM raw_data.nba_games g
LEFT JOIN master.nba_plays p ON g.game_id = p.game_id
GROUP BY g.game_id, g.data
HAVING COUNT(p.id) != COALESCE((g.data->'play_by_play'->>'total_plays')::int, 0);
```

### Spot Check Random Samples
```sql
-- Compare 100 random games
SELECT
  m.game_id,
  m.home_team as master_home,
  r.data->'teams'->'home'->>'name' as raw_data_home,
  m.final_score_home as master_score,
  (r.data->'teams'->'home'->>'score')::int as raw_data_score
FROM master.nba_games m
JOIN raw_data.nba_games r ON m.game_id = r.game_id
ORDER BY RANDOM()
LIMIT 100;
```

---

## Performance Considerations

**Batch sizes:**
- Games: 1,000 rows/batch (small records)
- Play summaries: 100 games/batch (heavy aggregation)
- File validation: 5,000 rows/batch (small records)

**Indexes:**
- raw_data.nba_games(game_id) - Already exists (PK)
- raw_data.nba_games USING GIN(data) - Already exists
- Disable during bulk insert, rebuild after

**Disk space:**
- Master: 3.5 GB
- raw_data (estimated): 4-5 GB (JSONB overhead)
- Total during migration: ~8 GB

**Migration time estimate:**
- Games: 10 minutes
- Play summaries: 60 minutes
- File validation: 10 minutes
- **Total: ~80 minutes**

---

## Rollback Plan

**If migration fails:**
```sql
-- Delete all migrated records
DELETE FROM raw_data.nba_games
WHERE metadata->>'migration_version' = '1.0.0';

DELETE FROM raw_data.nba_misc
WHERE (data->>'data_type') = 'file_validation';

-- Verify raw_data is empty
SELECT COUNT(*) FROM raw_data.nba_games;  -- Should be 0
```

**Master schema remains untouched** - can restart migration anytime.

---

## Success Criteria

✅ 31,241 games migrated (row count matches)
✅ All games have valid JSONB data (no NULLs)
✅ Play counts match between master and raw_data
✅ 44,826 validation records migrated
✅ Random spot checks pass (10 samples)
✅ Query performance acceptable (< 100ms for game lookup)
✅ All validators pass for raw_data schema

---

**Design complete:** November 5, 2025
**Ready for implementation**
