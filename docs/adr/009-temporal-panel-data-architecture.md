# ADR-009: Temporal Panel Data Architecture

**Date:** October 7, 2025
**Status:** Accepted
**Decision Maker:** Project lead based on temporal analysis requirements

## Context

The original project goal was to create a "game simulator and ML platform" with traditional game-level statistics. After deeper analysis, the project vision evolved into a **temporal panel data system** capable of snapshot queries at exact timestamps with millisecond precision.

The project now requires:
- Query cumulative player statistics at any exact moment in time
- Example: "What were Kobe Bryant's career stats at exactly 7:02:34.56 PM CT on June 19, 2016?"
- Support for future video feed synchronization at 30fps (~33ms per frame)
- High-frequency panel data structure similar to financial markets data
- Player age calculations accurate to the second

Traditional sports analytics databases cannot support these temporal queries.

## Decision

**Implement a temporal panel data architecture** with four new database tables, BRIN time-series indexes, and PostgreSQL stored procedures for snapshot queries.

**Core components:**
1. `temporal_events` table (500M+ rows) - Event-level timestamps with millisecond precision
2. `player_snapshots` table (50M+ rows) - Pre-computed cumulative statistics at checkpoints
3. `game_states` table (10M+ rows) - Game state reconstruction data
4. `player_biographical` table (5K+ rows) - Birth dates for age calculations

**Index strategy:** BRIN (Block Range Index) for time-series data, 70%+ storage savings vs. B-tree

**Query strategy:** Pre-computed snapshots for common queries + on-the-fly aggregation for ad-hoc queries

## Rationale

### 1. Temporal Precision Requirements

**Traditional approach:**
- Game-level aggregates: "Kobe scored 60 points in his final game"
- Season averages, career totals
- No intra-game temporal resolution

**Our requirement:**
- Event-level timestamps: "Kobe made a 3-pointer at 7:02:34 PM"
- Cumulative statistics at exact moments: "Career total became 33,646 at that instant"
- Player age at event time: "He was 37 years, 234 days, 5 hours old"

**Why this matters:** Enables temporal feature engineering for ML models, high-frequency statistical analysis, and future video synchronization.

### 2. PostgreSQL vs. TimescaleDB

**Considered alternatives:**
- **TimescaleDB:** Time-series database extension for PostgreSQL
- **InfluxDB:** Purpose-built time-series database
- **Native PostgreSQL:** Standard PostgreSQL with BRIN indexes

**Decision:** Use native PostgreSQL with BRIN indexes

**Rationale:**
- **No additional setup complexity:** TimescaleDB requires extension installation
- **RDS compatibility:** AWS RDS PostgreSQL doesn't support TimescaleDB extension
- **Sufficient performance:** BRIN indexes provide 70%+ storage savings, excellent for time-series
- **Avoid vendor lock-in:** Native PostgreSQL is portable
- **Lower operational overhead:** No new technology to learn/maintain

**Performance comparison:**
- BRIN index on 500M rows: ~500 MB index size (vs. 50 GB B-tree)
- Query time for single player snapshot: 2-5 seconds (acceptable)
- TimescaleDB benefit: Marginal for our query patterns (mostly point lookups)

### 3. Dual Timestamp Strategy (Wall Clock + Game Clock)

**Challenge:** NBA games have two temporal dimensions:
- **Wall clock:** Real-world time (e.g., "7:37:34 PM CT")
- **Game clock:** In-game time (e.g., "6:02 remaining in Q2")

**Decision:** Store both timestamps in `temporal_events` table

**Rationale:**
- **Wall clock enables:** Temporal ordering across multiple games, video synchronization
- **Game clock enables:** Within-game analysis, possession calculations
- **Example use case:** "Show me all games at exactly 9:00 PM ET on March 15, 2023" (wall clock)
- **Example use case:** "Show me Kobe's stats with 2:00 remaining in 4th quarters" (game clock)

**Storage cost:** Negligible (16 bytes per row for two TIMESTAMP(3) columns)

### 4. Precision Level Flags

**Challenge:** Data precision varies by era:
- 2020-2025: Millisecond precision (NBA Live API)
- 1993-2019: Minute-level precision (NBA Stats PlayByPlayV2: "7:37 PM")
- 1946-1992: Game-level only (Basketball Reference)

**Decision:** Store `precision_level` VARCHAR(10) with every event

**Values:** 'millisecond', 'second', 'minute', 'game', 'unknown'

**Rationale:**
- **Transparency:** Queries know the precision of returned data
- **Quality control:** Can filter by precision level for high-confidence analysis
- **Future-proofing:** As precision improves, old data is properly flagged
- **Example:** Research requiring millisecond precision can filter to 2020+ data only

### 5. Pre-Computed Snapshots vs. On-The-Fly Aggregation

**Challenge:** Aggregating 500M+ events for every query is slow

**Decision:** Hybrid approach
- **Pre-compute:** Player snapshots at common intervals (every game, every quarter)
- **On-the-fly:** Ad-hoc queries for exact timestamps between checkpoints

**player_snapshots table strategy:**
- Create snapshot after each game for every player (~1,230 games × 500 players × 30 seasons = 18M rows)
- Create snapshot after each quarter for active players (~1,230 games × 4 qtrs × 10 active players = 50K rows per season)
- **Total projected:** 50M snapshots

**Query logic:**
1. Check if pre-computed snapshot exists at/before requested timestamp
2. If yes, return snapshot (fast: < 1 second)
3. If no, aggregate events from nearest checkpoint (slower: 2-5 seconds)

**Storage tradeoff:**
- Pre-computed snapshots: +10-20 GB storage
- Query time improvement: 100x faster (5s → 0.05s)
- **Verdict:** Worth it for common queries

### 6. Birth Date Storage for Age Calculations

**Challenge:** Player age affects performance, need precise age at event time

**Decision:** Create `player_biographical` table with birth dates and precision flags

**Birth date precision levels:**
- 'day': Full date known (e.g., "August 23, 1978")
- 'month': Month and year known (e.g., "March 1960")
- 'year': Year only (e.g., "1945")
- 'unknown': No birth date available

**Age calculation:**
```sql
age_years = EXTRACT(EPOCH FROM (event_timestamp - birth_date)) / (365.25 * 24 * 60 * 60)
```

**Example:** Kobe Bryant born August 23, 1978
- At 7:02:34 PM on June 19, 2016: 37.8145 years old (or 37 years, 297 days, 5 hours)

**Rationale:**
- **Temporal feature engineering:** Age is a critical ML feature
- **Research applications:** Study aging curves at fine-grained temporal resolution
- **Transparency:** Precision flag indicates confidence in age calculation

### 7. JSONB for Event Data

**Challenge:** Play-by-play events have variable structure depending on event type

**Decision:** Store full play-by-play JSON in `event_data JSONB` column

**Rationale:**
- **Flexibility:** Can query nested JSON without schema changes
- **Completeness:** Preserve all original data for future analysis
- **Performance:** PostgreSQL JSONB has GIN indexes for fast queries
- **Example query:** `WHERE event_data->>'shot_distance' > '25'` (3-pointers from 25+ feet)

**Alternative considered:** Normalized relational schema (separate tables for shots, fouls, turnovers)
- **Rejected because:** Too rigid, requires schema changes for new event types, query complexity

### 8. Data Provenance Tracking

**Decision:** Store `data_source` VARCHAR(20) with every event

**Values:** 'nba_live', 'nba_stats', 'espn', 'hoopr', 'basketball_ref', 'kaggle'

**Rationale:**
- **Data quality:** Some sources more reliable than others
- **Debugging:** Can trace data quality issues to source
- **Research:** Compare same event from multiple sources
- **Example:** ESPN might have "7:37 PM" while NBA Stats has "7:37:22 PM" for same event

## Consequences

### Positive

1. **Enables novel queries:** Can answer questions impossible with traditional databases
   - "Show me Kobe's stats at exactly 7:02:34 PM on June 19, 2016"
   - "What was league average pace at 11:23:45 PM on March 15, 2023?"

2. **Future-proof for video integration:** Millisecond precision supports 30fps video synchronization

3. **Advanced ML features:** Temporal features like fatigue, momentum, clutch performance

4. **Research applications:** High-frequency panel data analysis similar to financial markets

5. **Scalable:** BRIN indexes keep storage manageable even with 500M+ rows

### Negative

1. **Increased storage costs:** +$20-30/month for temporal tables
   - 500M temporal_events rows: ~200-300 GB
   - 50M player_snapshots rows: ~10-20 GB
   - **Mitigation:** BRIN indexes reduce index size by 70%+

2. **Query complexity:** Temporal queries are more complex than traditional SQL
   - Requires understanding of TIMESTAMP(3), time zones, precision levels
   - **Mitigation:** Provide stored procedures for common queries

3. **Data ingestion complexity:** Must parse and normalize timestamps from multiple sources
   - ESPN: "7:37 PM" (minute-level)
   - NBA Live: "2021-01-16T00:40:31.300Z" (millisecond-level)
   - **Mitigation:** ETL pipeline handles timestamp normalization

4. **Snapshot maintenance:** Pre-computed snapshots must be recalculated when data changes
   - Example: If a game's play-by-play is corrected, all downstream snapshots must update
   - **Mitigation:** Snapshot generation is idempotent, can recompute as needed

5. **Initial implementation time:** 6-8 hours to design and implement temporal schema
   - **Mitigation:** Phased approach - implement core tables first, optimize later

## Alternatives Considered

### Alternative 1: Continue with Traditional Game-Level Database

**Approach:** Keep existing schema, add game-level statistics only

**Pros:**
- Simpler implementation
- Lower storage costs
- Easier queries

**Cons:**
- Cannot answer temporal questions
- No support for video synchronization
- Limited ML feature engineering
- No competitive advantage over existing sports databases

**Verdict:** Rejected - doesn't achieve project vision

### Alternative 2: TimescaleDB Extension

**Approach:** Use TimescaleDB extension for PostgreSQL

**Pros:**
- Purpose-built for time-series data
- Automatic partitioning by time
- Optimized time-based queries

**Cons:**
- Not available on AWS RDS (requires self-managed PostgreSQL)
- Additional operational complexity
- Vendor lock-in risk
- Performance benefit marginal for our query patterns

**Verdict:** Rejected - complexity not justified by benefits

### Alternative 3: Separate Time-Series Database (InfluxDB, Prometheus)

**Approach:** Use dedicated time-series database alongside PostgreSQL

**Pros:**
- Optimized for time-series data
- High write throughput
- Efficient compression

**Cons:**
- Another system to manage and learn
- Data synchronization complexity
- Overkill for our write volume (~500M events one-time load)
- Limited support for complex joins and aggregations
- Cost: +$50-100/month for managed InfluxDB

**Verdict:** Rejected - unnecessary complexity

### Alternative 4: NoSQL Document Database (MongoDB, DynamoDB)

**Approach:** Store events as documents with flexible schema

**Pros:**
- Schema flexibility
- Horizontal scalability
- Fast writes

**Cons:**
- Weak support for time-range queries
- No native snapshot query capabilities
- Complex aggregation queries
- Less mature ecosystem for panel data analysis
- Cost: ~$50-75/month for managed MongoDB

**Verdict:** Rejected - poor fit for temporal queries

## Implementation Plan

**Phase 1: Core Tables (Week 1)**
- Create `temporal_events` table with BRIN indexes
- Create `player_biographical` table
- Load player birth dates from NBA Stats API
- Test basic timestamp storage and retrieval

**Phase 2: Snapshot System (Week 2)**
- Create `player_snapshots` table
- Implement snapshot generation logic
- Create `get_player_snapshot_at_time()` stored procedure
- Generate snapshots for test dataset (1 season)

**Phase 3: Game States (Week 3)**
- Create `game_states` table
- Implement game state reconstruction
- Test snapshot queries with game state data

**Phase 4: Validation & Optimization (Week 4)**
- Create validation test suite
- Performance testing with full dataset
- Index tuning and query optimization
- Documentation and examples

**Phase 5: Production Load (Month 2)**
- Load all temporal_events (500M rows)
- Generate all player_snapshots (50M rows)
- Monitor query performance and storage growth
- Adjust indexes and snapshots as needed

## Success Metrics

1. **Query performance:** Single player snapshot < 5 seconds
2. **Storage efficiency:** BRIN indexes < 1% of data size
3. **Data completeness:** 95%+ of events have timestamps
4. **Precision coverage:** 90%+ of modern data (2013+) has second or better precision
5. **Age accuracy:** Player age calculations accurate to ±1 second where birth date known

## Risks & Mitigations

### Risk 1: Query Performance Degradation

**Risk:** Queries become too slow as data grows beyond 500M rows

**Likelihood:** Medium (depends on query patterns)

**Impact:** High (makes temporal queries impractical)

**Mitigation:**
- Pre-compute common snapshots (reduces query load)
- Use BRIN indexes (efficient for time-series)
- Partition `temporal_events` by year if needed
- Consider read replicas for analytics queries

### Risk 2: Storage Costs Exceed Budget

**Risk:** Temporal tables grow larger than projected

**Likelihood:** Low (estimates based on known data volumes)

**Impact:** Medium (might need to reduce snapshot frequency)

**Mitigation:**
- Monitor storage growth weekly
- Adjust snapshot granularity (fewer checkpoints)
- Compress old data (PostgreSQL compression)
- Archive historical snapshots to S3 (long-term storage)

### Risk 3: Timestamp Precision Inconsistency

**Risk:** Different data sources have conflicting timestamps for same event

**Likelihood:** Medium (known issue with historical data)

**Impact:** Medium (affects query accuracy)

**Mitigation:**
- Store `data_source` with each event
- Document precision limitations by era
- Allow queries to filter by precision level
- Provide confidence intervals for imprecise data

### Risk 4: Birth Date Unavailability

**Risk:** Many historical players lack birth dates

**Likelihood:** High (especially pre-1960s players)

**Impact:** Low (age calculations return NULL, queries still work)

**Mitigation:**
- Store birth date precision flag
- Return NULL for age when birth date unknown
- Document data completeness by era
- Gradually improve coverage with additional sources

## References

**Related Documentation:**
- `docs/PROJECT_VISION.md` - Overall temporal panel data vision
- `docs/phases/PHASE_3_DATABASE.md` - Database implementation details
- `docs/NBA_API_SCRAPER_OPTIMIZATION.md` - Data collection strategy

**Technical Research:**
- PostgreSQL BRIN indexes: https://www.postgresql.org/docs/current/brin.html
- Panel data econometrics: Wooldridge (2010) "Econometric Analysis of Cross Section and Panel Data"
- Time-series database comparison: https://db-engines.com/en/system/InfluxDB%3BPostgreSQL%3BTimescaleDB

**Industry Examples:**
- Financial markets: High-frequency trading data (millisecond precision)
- Medical research: Longitudinal patient data (variable precision)
- IoT systems: Sensor time-series data (multi-source timestamps)

---

**Document Status:** Accepted
**Review Date:** October 7, 2025
**Next Review:** After 3.0005 implementation (estimated November 2025)

---

*This ADR documents the most significant architectural decision in the project - the shift from traditional sports analytics to temporal panel data system.*
