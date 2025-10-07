# Data Deduplication & Conflict Resolution Rules

**Created:** October 6, 2025
**Purpose:** Define rules for handling duplicate data and conflicts across 5 data sources
**Status:** Foundation document for multi-source data integration

---

## Overview

When collecting data from 5 sources (ESPN, NBA.com Stats, Kaggle, SportsDataverse, Basketball Reference), duplicate games and conflicting values are inevitable. This document establishes:

- **Deduplication strategy:** How to identify and merge duplicate records
- **Conflict resolution:** Which source wins when values differ
- **Data lineage:** How to track which source provided each field
- **Quality scoring:** How to assess data completeness and reliability

---

## Table of Contents

1. [Source Priority Hierarchy](#source-priority-hierarchy)
2. [Deduplication Strategy](#deduplication-strategy)
3. [Conflict Resolution Rules](#conflict-resolution-rules)
4. [Data Lineage Tracking](#data-lineage-tracking)
5. [Implementation Examples](#implementation-examples)

---

## Source Priority Hierarchy

### Overall Source Reliability Ranking

**Ranked by official status and data quality:**

| Rank | Source | Reliability | Coverage | Update Frequency | Use Case |
|------|--------|-------------|----------|------------------|----------|
| 1 | **NBA.com Stats** | ⭐⭐⭐⭐⭐ | 1996-present | Real-time | Official scores, IDs |
| 2 | **Basketball Reference** | ⭐⭐⭐⭐⭐ | 1946-present | Daily | Advanced stats, historical |
| 3 | **ESPN** | ⭐⭐⭐⭐ | 1999-present | Real-time | Primary source (already have) |
| 4 | **Kaggle DB** | ⭐⭐⭐⭐ | 1946-2024 | Monthly | Historical validation |
| 5 | **SportsDataverse** | ⭐⭐⭐ | 2002-present | Varies | Testing/prototyping |

### Field-Level Priority Matrix

**Different sources are authoritative for different fields:**

| Field Type | Priority Order | Reasoning |
|-----------|----------------|-----------|
| **Game Scores** | NBA.com Stats > ESPN > Kaggle > Basketball Ref | Official API most reliable |
| **Play-by-Play** | ESPN > NBA.com Stats > SportsDataverse | ESPN has best PBP coverage |
| **Advanced Stats** | Basketball Reference > NBA.com Stats > ESPN | BRef has most comprehensive advanced metrics |
| **Historical Games (pre-1999)** | Basketball Reference > Kaggle > ESPN | BRef/Kaggle have pre-ESPN data |
| **Player Metadata** | NBA.com Stats > Basketball Reference > ESPN | Official IDs and biographical data |
| **Team Metadata** | NBA.com Stats > ESPN > Basketball Reference | Official team info |
| **Venue/Attendance** | ESPN > NBA.com Stats > Basketball Reference | ESPN has detailed venue data |
| **Season Context** | NBA.com Stats > ESPN > Kaggle | Official season definitions |

---

## Deduplication Strategy

### Step 1: Identify Duplicates

**Composite Key for Game Matching:**
```
Primary Key = (game_date, home_team_abbr, away_team_abbr)
```

**Duplicate Detection Algorithm:**
1. Extract composite key from each source
2. Group records by composite key
3. If multiple records share same key → duplicate detected
4. Merge records using conflict resolution rules

**Example:**
```python
# Game from 3 sources with same composite key
duplicate_games = {
    'key': ('2024-12-25', 'LAL', 'GSW'),
    'sources': [
        {'source': 'espn', 'game_id': '401585647', 'score': '115-105'},
        {'source': 'nba_stats', 'game_id': '0022400123', 'score': '115-105'},
        {'source': 'kaggle', 'game_id': '54321', 'score': '115-105'}
    ]
}
# → These are duplicates, merge into single record
```

### Step 2: Merge Strategy

**Two approaches:**

#### Approach A: "Best Source Wins" (Simpler)
- Select one source as authoritative
- Use its values for all fields
- Track other sources in metadata

```python
def merge_best_source_wins(duplicates):
    """
    Choose highest-priority source and use its values
    """
    priority_order = ['nba_stats', 'bref', 'espn', 'kaggle', 'sportsdataverse']

    for source_name in priority_order:
        for record in duplicates['sources']:
            if record['source'] == source_name:
                return {
                    **record,
                    'data_sources': [r['source'] for r in duplicates['sources']],
                    'primary_source': source_name
                }
```

#### Approach B: "Best Field Wins" (More Complex, Better Quality)
- Select best source for each field independently
- Combine fields from multiple sources
- Track source for each field

```python
def merge_best_field_wins(duplicates):
    """
    Choose best source for each field
    """
    merged = {
        'composite_key': duplicates['key'],
        'data_sources': {},  # Track source for each field
        'confidence_score': 0
    }

    # Game scores: NBA.com Stats > ESPN > Kaggle
    score_priority = ['nba_stats', 'espn', 'kaggle']
    for source_name in score_priority:
        record = find_source(duplicates, source_name)
        if record and 'score' in record:
            merged['home_score'], merged['away_score'] = parse_score(record['score'])
            merged['data_sources']['scores'] = source_name
            break

    # Play-by-play: ESPN > NBA.com > SportsDataverse
    pbp_priority = ['espn', 'nba_stats', 'sportsdataverse']
    for source_name in pbp_priority:
        record = find_source(duplicates, source_name)
        if record and 'pbp_data' in record:
            merged['pbp_data'] = record['pbp_data']
            merged['data_sources']['pbp'] = source_name
            break

    # Advanced stats: Basketball Reference > NBA.com
    adv_priority = ['bref', 'nba_stats']
    for source_name in adv_priority:
        record = find_source(duplicates, source_name)
        if record and 'advanced_stats' in record:
            merged['advanced_stats'] = record['advanced_stats']
            merged['data_sources']['advanced'] = source_name
            break

    # Calculate confidence score based on source agreement
    merged['confidence_score'] = calculate_agreement(duplicates)

    return merged
```

**Recommended:** Use **Approach B (Best Field Wins)** for production - higher quality but more complex.

---

## Conflict Resolution Rules

### Rule 1: Score Conflicts

**Scenario:** Different sources report different final scores

**Resolution:**
1. Check if all sources agree → high confidence
2. If disagreement:
   - NBA.com Stats value wins (official)
   - Log conflict to `data_quality_log` table
   - Flag record for manual review if difference > 2 points

**Example:**
```python
def resolve_score_conflict(espn_score, nba_score, kaggle_score):
    """
    Resolve conflicting scores
    """
    scores = [espn_score, nba_score, kaggle_score]

    # All sources agree?
    if len(set(scores)) == 1:
        return {'score': scores[0], 'confidence': 'high', 'conflict': False}

    # NBA.com Stats wins
    if nba_score:
        diff = abs(nba_score - espn_score) if espn_score else 0
        return {
            'score': nba_score,
            'confidence': 'medium' if diff <= 2 else 'low',
            'conflict': True,
            'conflict_details': {
                'espn': espn_score,
                'nba_stats': nba_score,
                'kaggle': kaggle_score,
                'max_diff': diff
            }
        }

    # Fallback to ESPN if NBA.com not available
    return {'score': espn_score, 'confidence': 'medium', 'conflict': True}
```

### Rule 2: Date/Time Conflicts

**Scenario:** Different sources report different game dates or times

**Resolution:**
1. NBA.com Stats date/time wins (official schedule)
2. If NBA.com not available, use ESPN
3. Log any discrepancies > 1 hour

**Special Cases:**
- Games postponed/rescheduled: Use most recent date
- Time zone differences: Normalize all to UTC
- Doubleheaders: Use game time to disambiguate

### Rule 3: Player Stat Conflicts

**Scenario:** Different sources report different player stats

**Resolution:**
1. For basic stats (PTS, REB, AST): NBA.com Stats > Basketball Ref > ESPN
2. For advanced stats (PER, TS%, etc.): Basketball Ref > NBA.com Stats
3. If difference > 10%, flag for manual review

### Rule 4: Missing Data Conflicts

**Scenario:** Some sources have data, others are missing

**Resolution:**
1. Use any available data (something > nothing)
2. Track completeness score:
   - All 5 sources: 100% complete
   - 4 sources: 80% complete
   - 3 sources: 60% complete
   - 2 sources: 40% complete
   - 1 source: 20% complete
3. Prefer sources with most complete data

### Rule 5: Historical Data Conflicts (pre-1999)

**Scenario:** ESPN doesn't have data, but Kaggle/Basketball Ref do

**Resolution:**
1. Basketball Reference is authoritative (most comprehensive)
2. Use Kaggle as secondary validation
3. Mark source clearly: `data_source = 'bref'` or `'kaggle'`

---

## Data Lineage Tracking

### Database Schema for Lineage

**Add to RDS `games` table:**
```sql
ALTER TABLE games ADD COLUMN data_sources JSONB;
ALTER TABLE games ADD COLUMN primary_source VARCHAR(20);
ALTER TABLE games ADD COLUMN confidence_score DECIMAL(3,2);
ALTER TABLE games ADD COLUMN has_conflicts BOOLEAN DEFAULT FALSE;
```

**Example values:**
```json
{
  "data_sources": {
    "scores": "nba_stats",
    "pbp": "espn",
    "advanced_stats": "bref",
    "venue": "espn"
  },
  "primary_source": "nba_stats",
  "confidence_score": 0.95,
  "has_conflicts": false
}
```

### Conflict Logging Table

**Create table to track all conflicts:**
```sql
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
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Quality Scoring System

### Confidence Score Formula

**Calculate confidence based on:**
1. Source agreement (do sources agree?)
2. Source quality (is data from authoritative source?)
3. Completeness (how many fields are populated?)

**Formula:**
```python
def calculate_confidence_score(game_data):
    """
    Calculate confidence score 0.0-1.0
    """
    score = 0.0

    # Source agreement (40% of score)
    agreement_ratio = count_agreeing_sources(game_data) / total_sources(game_data)
    score += 0.4 * agreement_ratio

    # Source quality (40% of score)
    if game_data['primary_source'] in ['nba_stats', 'bref']:
        score += 0.4  # High quality source
    elif game_data['primary_source'] == 'espn':
        score += 0.3  # Good quality source
    else:
        score += 0.2  # Acceptable source

    # Data completeness (20% of score)
    completeness = count_populated_fields(game_data) / total_expected_fields
    score += 0.2 * completeness

    return round(score, 2)
```

### Quality Thresholds

**Action based on confidence score:**

| Score Range | Quality Level | Action |
|-------------|---------------|--------|
| 0.90 - 1.00 | Excellent | Use immediately, no review needed |
| 0.75 - 0.89 | Good | Use for analysis, log any conflicts |
| 0.60 - 0.74 | Acceptable | Flag for review if used in critical analysis |
| 0.40 - 0.59 | Poor | Manual review required before use |
| 0.00 - 0.39 | Very Poor | Do not use, investigate source issues |

---

## Implementation Examples

### Example 1: Merging a Game with 3 Sources

**Input:**
```python
game_duplicates = {
    'key': ('2024-12-25', 'LAL', 'GSW'),
    'sources': [
        {
            'source': 'espn',
            'game_id': '401585647',
            'home_score': 115,
            'away_score': 105,
            'attendance': 18997,
            'pbp_data': {...}  # Full play-by-play
        },
        {
            'source': 'nba_stats',
            'game_id': '0022400123',
            'home_score': 115,
            'away_score': 105,
            'advanced_stats': {...}
        },
        {
            'source': 'bref',
            'slug': '202412250lal',
            'home_score': 115,
            'away_score': 105,
            'advanced_stats': {...},  # More comprehensive
            'four_factors': {...}
        }
    ]
}
```

**Merged Output:**
```python
merged_game = {
    'game_date': '2024-12-25',
    'home_team': 'LAL',
    'away_team': 'GSW',

    # Scores: NBA.com Stats (official) - but all agree
    'home_score': 115,
    'away_score': 105,

    # Play-by-play: ESPN (best coverage)
    'pbp_data': {...},

    # Advanced stats: Basketball Reference (most comprehensive)
    'advanced_stats': {...},
    'four_factors': {...},

    # Venue: ESPN (detailed venue data)
    'attendance': 18997,

    # Metadata
    'data_sources': {
        'scores': 'nba_stats',
        'pbp': 'espn',
        'advanced_stats': 'bref',
        'venue': 'espn'
    },
    'primary_source': 'nba_stats',
    'confidence_score': 0.98,  # High - all sources agree on scores
    'has_conflicts': False,

    # Source IDs (for reference)
    'espn_id': '401585647',
    'nba_stats_id': '0022400123',
    'bref_slug': '202412250lal'
}
```

### Example 2: Resolving a Score Conflict

**Input:**
```python
game_conflict = {
    'key': ('1999-03-02', 'CHI', 'DET'),
    'sources': [
        {'source': 'espn', 'home_score': 83, 'away_score': 95},
        {'source': 'nba_stats', 'home_score': None, 'away_score': None},  # Missing
        {'source': 'kaggle', 'home_score': 84, 'away_score': 95}
    ]
}
```

**Resolution:**
```python
resolved = {
    'game_date': '1999-03-02',
    'home_team': 'CHI',
    'away_team': 'DET',

    # Use ESPN (NBA.com Stats missing, ESPN vs Kaggle differ by 1)
    'home_score': 83,
    'away_score': 95,

    # Metadata
    'primary_source': 'espn',
    'confidence_score': 0.65,  # Medium - conflict exists
    'has_conflicts': True,

    # Log conflict
    'conflicts': [
        {
            'field': 'home_score',
            'espn': 83,
            'kaggle': 84,
            'diff': 1,
            'resolution': 'Used ESPN (higher priority)',
            'requires_review': False  # Only 1 point difference
        }
    ]
}
```

---

## Automated Conflict Detection

### Daily Conflict Report

**Run after each ETL batch:**
```python
def generate_conflict_report():
    """
    Identify and report all conflicts from latest ETL run
    """
    conflicts = db.query("""
        SELECT
            game_id,
            game_date,
            COUNT(*) as num_conflicts,
            AVG(confidence_score) as avg_confidence
        FROM data_conflicts
        WHERE created_at > NOW() - INTERVAL '1 day'
        GROUP BY game_id, game_date
        ORDER BY num_conflicts DESC
    """)

    # Generate report
    report = f"""
    # Data Conflict Report - {datetime.now().date()}

    Total conflicts: {len(conflicts)}

    ## High Priority (requires review)
    {conflicts[conflicts['requires_review'] == True]}

    ## Low Priority (auto-resolved)
    {conflicts[conflicts['requires_review'] == False]}
    """

    # Save to docs/
    with open('docs/CONFLICT_REPORT.md', 'w') as f:
        f.write(report)
```

---

## Best Practices

### DO:
✅ Always track which source provided each field (data lineage)
✅ Log all conflicts, even if auto-resolved
✅ Calculate confidence scores for every merged record
✅ Use hierarchical resolution (field-level > source-level)
✅ Prefer official sources (NBA.com Stats) for authoritative data

### DON'T:
❌ Discard conflicting data without logging
❌ Assume one source is always correct for all fields
❌ Merge without tracking source lineage
❌ Auto-resolve high-severity conflicts (> 10% difference)
❌ Use low-confidence data (< 0.60) without review

---

## Next Steps

1. **Implement deduplication pipeline** (Phase 1.7)
2. **Create conflict logging system** (Phase 1.7)
3. **Build confidence scoring** (Phase 1.7)
4. **Set up automated conflict reports** (Phase 1.8)
5. **Integrate with ETL workflow** (Phase 2)

---

## Related Documentation

- **[DATA_SOURCE_MAPPING.md](DATA_SOURCE_MAPPING.md)** - ID and field mapping across sources
- **[DATA_SOURCES.md](DATA_SOURCES.md)** - Overview of all 5 data sources
- **[PHASE_1_FINDINGS.md](PHASE_1_FINDINGS.md)** - Data quality analysis results

---

*Last Updated: October 6, 2025*
*Next Review: After implementing first multi-source ETL run*