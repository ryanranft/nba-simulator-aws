# ADR-002: 10% Data Extraction Strategy

**Date:** September 29, 2025
**Status:** Accepted
**Decision Maker:** User requirement based on use case analysis

## Context

Raw ESPN JSON files contain extensive metadata, commentary, broadcast information, and historical context:
- 146,115 JSON files
- 119 GB total raw storage
- Average file size: 800 KB
- Hundreds of fields per file
- Mix of essential data and supplementary information

**Problem:** Loading all fields into RDS would be:
- Expensive (storage costs)
- Slow (query performance)
- Wasteful (90% of data not needed for simulations/ML)

## Decision

**Extract only ~10% of fields from each JSON file during ETL process.** Load only essential simulation and analysis fields into RDS.

## Fields to Extract

### Box Scores
**Include:**
- Player: `player_id`, `player_name`, `team_id`, `position`
- Stats: `minutes`, `points`, `rebounds`, `assists`, `steals`, `blocks`, `turnovers`
- Shooting: `FG_made`, `FG_attempted`, `3PT_made`, `3PT_attempted`, `FT_made`, `FT_attempted`

**Exclude:**
- Player photos and headshots
- Biographical details (height, weight, college)
- Career statistics
- Commentary and analysis text

### Play-by-Play
**Include:**
- Core: `game_id`, `period`, `clock`, `play_type`, `scoring_play` (boolean)
- Participants: `player_id`, `team_id`
- Score: `home_score`, `away_score`

**Exclude:**
- Play descriptions/narrative text
- Coordinate data (x, y positions)
- Video links and highlights
- Detailed shot charts
- Broadcast timestamps

### Schedule
**Include:**
- Game: `game_id`, `game_date`, `home_team_id`, `away_team_id`, `home_score`, `away_score`
- Venue: `venue_name`, `attendance` (optional)

**Exclude:**
- Broadcast details (networks, announcers)
- Ticket purchase links
- Weather information
- Betting odds
- Pre-game analysis

### Team Stats
**Include:**
- Aggregate: `team_id`, `game_id`, `points`, `rebounds`, `assists`, `turnovers`, `FG%`, `3PT%`, `FT%`

**Exclude:**
- Historical comparisons
- Season narratives
- Coaching details
- Team photos/logos

**Note:** Exact JSON field paths to be documented after examining sample files (Phase 2.2 prep).

## Rationale

### 1. Storage Efficiency
- **Before:** 119 GB raw data
- **After:** ~12 GB extracted data (90% reduction)
- **RDS storage cost:** $11.50/month → $2-3/month
- **Benefits:** Faster backups, easier to manage, lower costs

### 2. Processing Efficiency
- Glue ETL processes only relevant fields (reduced compute time)
- Simulations query only necessary data (faster performance)
- Reduced data transfer costs between S3 and RDS
- Less network I/O during ETL

### 3. Use Case Alignment

**Simulation engine needs:**
- Game outcomes
- Player performance statistics
- Play-by-play sequences

**ML features need:**
- Statistical aggregates
- Temporal patterns
- Player performance metrics

**Neither needs:**
- Commentary or narrative text
- Images, photos, videos
- Broadcast metadata
- Historical narratives

### 4. Maintainability
- Smaller database easier to backup, restore, and version
- Schema changes impact fewer fields
- Debugging and data quality checks faster
- Cleaner, more focused data model

### 5. Query Performance
- Smaller tables = faster scans
- Less memory required for queries
- Better index effectiveness
- Reduced I/O operations

## Alternatives Considered

### Alternative 1: Extract 100% of Fields
- **Pros:** Complete data available, no need to re-ETL if requirements change
- **Cons:** 119 GB storage ($27/month), slow queries, cluttered schema
- **Why rejected:** 90% of data not needed, wastes resources

### Alternative 2: Extract 50% of Fields (Medium Extraction)
- **Pros:** More fields available, some optimization
- **Cons:** Still includes unnecessary data, only 50% storage savings
- **Why rejected:** Still includes commentary, metadata we don't need

### Alternative 3: Extract Only Core Stats (<5%)
- **Pros:** Minimal storage, maximum performance
- **Cons:** May be too minimal, might need to re-ETL for ML features
- **Why rejected:** Too aggressive, 10% provides good balance

### Alternative 4: Keep Everything in S3, Query with Athena
- **Pros:** No RDS costs, query raw data directly
- **Cons:** $5/TB scanned, slow for repeated queries, no OLTP support
- **Why rejected:** Simulations need fast repeated lookups

## Consequences

### Positive
- **90% storage savings:** $11.50/month → $2-3/month
- **Faster queries:** Smaller tables, better cache hit rates
- **Lower ETL costs:** Process only relevant fields
- **Cleaner schema:** Focused data model, easier to understand
- **Better performance:** Less I/O, faster backups/restores

### Negative
- **Re-processing required:** If additional fields needed, must re-run ETL
- **Analysis limitations:** Cannot explore excluded fields without re-ETL
- **Schema rigidity:** Changing extracted fields requires full re-load

### Mitigation
- **Raw data preserved in S3:** Source of truth maintained
- **Can always extract more fields:** New Glue job can add fields anytime
- **S3 storage cheap:** $2.74/month for complete 119 GB archive
- **ETL is repeatable:** Automated scripts, can re-run easily
- **Document field decisions:** Clear record of what was excluded and why

## Implementation

### Phase 1: Field Analysis (⏸️ Pending)
1. Download sample JSON files
2. Examine structure and field names
3. Document exact field paths
4. Create `scripts/etl/field_mapping.yaml`

### Phase 2: ETL Development (⏸️ Pending)
1. Write PySpark script to extract only specified fields
2. Test with 100 sample files
3. Validate output data quality
4. Run full ETL on 146,115 files

### Phase 3: Validation (⏸️ Pending)
1. Verify ~90% size reduction
2. Check all required fields present
3. Validate no data loss for included fields
4. Test simulation queries

## Success Metrics

This decision is successful if:
- ✅ Achieve ~90% storage reduction (119 GB → 12 GB)
- ✅ RDS storage cost <$5/month
- ✅ All simulation queries can execute with available fields
- ✅ All planned ML features can be computed
- ✅ Query performance <1 second for simulation lookups
- ✅ No need to re-ETL additional fields within first 6 months

## Data Retention Strategy

**Raw JSON files:**
- Permanent storage in S3
- Source of truth
- Can always re-process
- Cost: $2.74/month

**Extracted data:**
- In RDS PostgreSQL
- Can be regenerated from S3 anytime
- Cost: ~$2-3/month storage

**Philosophy:** S3 is cheap, RDS is expensive. Keep everything in S3, extract only what's needed into RDS.

## Review Date

**Review after:** Initial ETL job completion

**Review criteria:**
- Verify 10% extraction meets all simulation requirements
- Verify ML feature engineering is possible with extracted fields
- Check if any critical fields were missed
- Assess query performance

**Re-evaluation triggers:**
- Simulation finds missing required fields
- ML models need excluded fields
- New use cases emerge requiring more data

## References

- PROGRESS.md: ADR-002 (original detailed version)
- ESPN API documentation: Field definitions
- AWS Glue documentation: ETL best practices
- PostgreSQL documentation: Storage and performance

## Notes

### Field Path Documentation
Exact JSON field paths will be documented in `scripts/etl/field_mapping.yaml` after examining sample files. Format:
```yaml
box_scores:
  player_id: "$.players[*].id"
  player_name: "$.players[*].displayName"
  points: "$.players[*].statistics.points"
```

### Future Expansion
If additional fields needed:
1. Update `field_mapping.yaml`
2. Run new Glue ETL job
3. Either replace RDS tables OR add new columns
4. Document change in this ADR

### Cost Savings Calculation
- Storage: $11.50 → $2.50 = **$9/month saved**
- Query performance: ~3x faster
- ETL processing: ~40% less compute
- Total estimated savings: **$15-20/month**

---

**Related ADRs:**
- ADR-001: Redshift Exclusion (related storage optimization decision)
- ADR-003: Python 3.11 for Development (ETL implementation language)

**Supersedes:** None

**Superseded By:** None