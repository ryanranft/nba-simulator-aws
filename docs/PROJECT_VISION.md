# NBA Temporal Panel Data System - Project Vision

**Document Version:** 1.0
**Date Created:** October 7, 2025
**Last Updated:** October 7, 2025
**Status:** Authoritative project vision document

---

## Executive Summary

This project is building a **temporal panel data system** for NBA basketball that enables snapshot queries of historical data at exact timestamps with millisecond precision.

**Not** a traditional sports analytics platform.
**Not** a simple game simulator or prediction engine.
**Yes** a high-frequency panel data system for temporal statistical analysis.

---

## Core Vision

### Primary Goal

**Create snapshots of NBA history at exact timestamps down to the millisecond.**

Every statistic, every player attribute, every team metric should be query-able at any precise moment in time.

### Example Capabilities

**Query 1: Player Career Snapshot**
```
"What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT
on June 19, 2016?"
```

**Answer:**
- Career points: 33,643
- Career assists: 6,306
- Age at that moment: 37 years, 234 days, 5 hours, 23 minutes, 34.56 seconds
- Current game state: Lakers vs. Jazz, Q2, 6:02 remaining
- All cumulative statistics accurate to that exact millisecond

**Query 2: League-Wide Temporal Analysis**
```
"What was the NBA's average pace at exactly 11:23:45.678 PM on March 15, 2023?"
```

**Answer:**
- Pace at that exact moment across all games in progress
- Historical pace trend up to that timestamp
- Possession counts and game states for active games
- Time-weighted league averages

**Query 3: Game State Reconstruction**
```
"Show me the complete game state at 8:45:30 PM on May 1, 2024"
```

**Answer:**
- Score, quarter, game clock for all active games
- Current lineups on floor
- Player positions and coordinates (if tracking data available)
- Possession status
- Cumulative player statistics up to that moment

---

## Why This Matters

### Traditional Approach (What Everyone Else Does)

**Game-level aggregates:**
- "Kobe scored 60 points in his final game"
- Season averages, career totals, per-game statistics
- No temporal resolution within games

**Problem:** Cannot analyze NBA history at fine-grained temporal resolution.

### Our Approach (Temporal Panel Data)

**Event-level timestamps:**
- "Kobe made a 3-pointer at 7:02:34 PM CT"
- "His career total became 33,646 at that exact moment"
- "He was 37 years, 234 days, 5 hours old at that instant"

**Advantage:** Can reconstruct NBA history at any point in time with precision comparable to financial markets high-frequency trading data.

---

## Technical Architecture

### Data Precision Levels

| Era | Years | Precision | Source | Use Case |
|-----|-------|-----------|--------|----------|
| **Modern (Live)** | 2020-2025 | **Millisecond** | NBA Live API | Video synchronization, frame-level analysis |
| **Digital** | 1993-2019 | **Minute-level** | NBA Stats PlayByPlayV2 | Statistical snapshots, temporal queries |
| **Early Digital** | 1946-1992 | **Game-level** | Basketball Reference | Season aggregates, historical context |

### Core Components

**1. Temporal Events Table**
```sql
CREATE TABLE temporal_events (
    event_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20),
    wall_clock_utc TIMESTAMP(3),  -- Millisecond precision
    wall_clock_local TIMESTAMP(3),
    game_clock_seconds INTEGER,
    quarter INTEGER,
    precision_level VARCHAR(10),   -- 'millisecond', 'second', 'minute', 'game'
    event_type VARCHAR(50),        -- shot, foul, turnover, etc.
    player_id INTEGER,
    team_id INTEGER,
    event_data JSONB,              -- All play-by-play details
    data_source VARCHAR(20)        -- 'nba_live', 'nba_stats', 'espn'
);

CREATE INDEX idx_temporal_events_time ON temporal_events (wall_clock_utc);
CREATE INDEX idx_temporal_events_player ON temporal_events (player_id, wall_clock_utc);
```

**2. Player Snapshots Table**
```sql
CREATE TABLE player_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    player_id INTEGER,
    snapshot_time TIMESTAMP(3),
    age_years DECIMAL(10,4),       -- Calculated from birth date
    career_points INTEGER,
    career_assists INTEGER,
    career_rebounds INTEGER,
    -- All cumulative statistics
    precision_level VARCHAR(10)
);
```

**3. Snapshot Query Engine**

Input: ISO 8601 timestamp (e.g., `2016-06-19T19:02:34.560-05:00`)

Process:
1. Filter all events before timestamp
2. Aggregate player/team cumulative stats
3. Calculate player ages from birth dates
4. Reconstruct game states (score, clock, possession)
5. Return complete NBA state snapshot

Output: JSON with all NBA data at that exact moment

---

## Future Vision: Video Integration

### Phase 1: Temporal Data (Current)
- Wall clock timestamps for all events
- Player birth dates for age calculations
- Game clock synchronization
- Cumulative statistics at any moment

### Phase 2: Video Synchronization (Future)

**Capability:** Align video feeds with temporal data at frame-level precision.

**Video frame rate:** 30fps = ~33ms per frame

**Synchronization:**
```
Event timestamp: 2016-06-19T19:02:34.560-05:00
Video frame: Frame 34,567 at timestamp 2016-06-19T19:02:34.533-05:00
Offset: 27ms (within acceptable tolerance)
```

**Use cases:**
- "Show me all 3-point shots made between 9:15:00 PM and 9:15:30 PM"
- Map video frames to exact statistical moments
- Computer vision analysis synced with temporal statistics

### Phase 3: Coordinate Tracking (Future)

**Capability:** Add ball and player coordinates from tracking systems.

**Data sources:**
- SportVU (2013-2017): 6-camera optical tracking
- Second Spectrum (2017-2023): Advanced optical tracking
- Sony Hawk-Eye (2023-present): Newest tracking system

**Coordinate precision:** 25 updates per second (40ms resolution)

**Use cases:**
- Ball position at exact timestamp
- Player positions for lineup analysis
- Movement patterns over time
- Defensive positioning metrics

---

## Data Sources & Coverage

### Source 1: ESPN API (Primary Historical)
**Coverage:** 1993-2025 (33 seasons)
**Data:** Box scores, play-by-play, schedules, team stats
**Precision:** Second-level (game clock), minute-level (wall clock estimates)
**Status:** ✅ Collected (146,115 files, 119 GB)

### Source 2: NBA Stats API (Temporal Data)
**Coverage:** 1996-2025 (30 seasons)
**Data:** PlayByPlayV2 with wall clock times, player biographical data
**Precision:** Minute-level (wall clock: "7:37 PM", game clock: "12:00")
**Status:** 🔄 Scraper optimized, ready for full collection (~366,486 files)

### Source 3: hoopR (Bulk Loading)
**Coverage:** 2002-2025 (24 seasons)
**Data:** ESPN data via sportsdataverse package (bulk loading)
**Precision:** Second-level
**Status:** ✅ Tested (653,437 records in 30 seconds)

### Source 4: Basketball Reference (Historical)
**Coverage:** 1946-present (79 seasons)
**Data:** Advanced statistics (47 features: PER, TS%, Win Shares, etc.)
**Precision:** Game-level aggregates
**Status:** ✅ Tested (54 games, rate-limited by design)

### Source 5: Kaggle NBA Database (Historical)
**Coverage:** 1946-2024 (78 seasons)
**Data:** SQLite database with 17 tables (player info, team info, historical records)
**Precision:** Season-level and game-level aggregates
**Status:** ⏸️ Pending integration

### Source 6: NBA Live API (Future)
**Coverage:** 2020-2025 (6 seasons)
**Data:** Millisecond-precision timestamps (`2021-01-16T00:40:31.300Z`)
**Precision:** **Millisecond**
**Status:** ⏸️ Future integration for video synchronization

---

## Use Cases

### Statistical Analysis

**1. Temporal Feature Engineering for ML**
- Player fatigue over time (minutes played, rest periods)
- Momentum shifts (scoring runs, possession sequences)
- Clutch performance (statistics in final 5 minutes)
- Age curves (performance vs. player age in real-time)

**2. High-Frequency Panel Data Models**
- Fixed effects estimation (player/team effects)
- Difference-in-differences (rule changes, coaching changes)
- Survival analysis (career length, injury risk)
- Time-varying covariates (age, experience, rest)

### Simulation & Prediction

**3. Temporal Game Simulation**
- Simulate games at event-level resolution
- Update player statistics after each simulated event
- Account for fatigue, momentum, clutch performance
- Generate realistic play-by-play sequences

**4. In-Game Prediction Models**
- Predict outcomes based on current game state
- Update predictions after each event
- Account for lineup changes, foul trouble, fatigue
- Real-time win probability

### Research & Analytics

**5. Historical Counterfactuals**
- "What if Kobe hadn't played in the 4th quarter?"
- Reconstruct game without specific events
- Analyze alternative scenarios at temporal resolution

**6. Video Analysis Preparation**
- Build temporal index for video search
- Map statistical events to video frames
- Enable coordinate tracking integration
- Prepare for computer vision models

---

## Success Metrics

### Phase 1: Temporal Data Collection (Current)
- [x] PlayByPlayV2 endpoint integrated
- [x] Player birth dates collected
- [x] Wall clock timestamps captured
- [x] Testing limits removed (100% data capture)
- [ ] Priority 1 collection complete (2014-2025)
- [ ] All seasons collected (1996-2025)

### Phase 2: Temporal Database (Pending)
- [ ] Temporal events table created
- [ ] Player snapshots table created
- [ ] Snapshot query engine implemented
- [ ] Age calculation system operational
- [ ] Temporal indexing optimized

### Phase 3: Query Validation (Pending)
- [ ] Query Kobe's stats at exact timestamp ✅
- [ ] Query league pace at exact timestamp ✅
- [ ] Reconstruct game state at exact timestamp ✅
- [ ] Calculate player age at exact timestamp ✅
- [ ] Response time < 5 seconds for snapshot queries

### Phase 4: Video Integration (Future)
- [ ] NBA Live API integrated (millisecond precision)
- [ ] Video frame mapping system built
- [ ] Coordinate tracking data ingested
- [ ] Frame-level synchronization validated
- [ ] Computer vision pipeline operational

---

## Timeline

### October 2025 (Current)
- ✅ Week 1: Optimize NBA API scraper for temporal data
- ✅ Week 1: Document temporal panel data vision
- ⏸️ Week 2-3: Start Priority 1 collection (2014-2025, ~14 days runtime)

### November 2025
- Week 1-2: Design and implement temporal database schema
- Week 3: Build snapshot query engine
- Week 4: Validate 
- Week 5: Integrate queries with test cases

### December 2025
- Week 1-2: Complete full historical collection (1996-2025)
- Week 3: Build temporal feature engineering pipeline
- Week 4: Enhance ML models with temporal features

### January 2026+
- Q1 2026: Integrate NBA Live API for millisecond precision
- Q2 2026: Build video frame synchronization system
- Q3 2026: Integrate coordinate tracking data
- Q4 2026: Deploy computer vision pipeline

---

## Key Differentiators

### What Makes This Project Unique

**1. Temporal Resolution**
- Most projects: Game-level or season-level aggregates
- This project: Millisecond-level temporal resolution

**2. Snapshot Queries**
- Most projects: "Show me Kobe's career stats" (total)
- This project: "Show me Kobe's stats at 7:02:34 PM on June 19, 2016" (temporal)

**3. Age Precision**
- Most projects: Player age in years
- This project: Player age to the second at exact event timestamp

**4. Panel Data Structure**
- Most projects: Cross-sectional or time-series
- This project: High-frequency panel data (players × timestamps)

**5. Video Integration Readiness**
- Most projects: Statistics separate from video
- This project: Built for frame-level video synchronization

---

## Technical Challenges

### Challenge 1: Timestamp Precision Varies by Era

**Problem:** Different data sources have different precision levels
- 2020-2025: Millisecond (NBA Live API)
- 1993-2019: Minute-level ("7:37 PM")
- 1946-1992: Game-level only

**Solution:**
- Store precision level with each event
- Query engine accounts for precision in results
- Interpolation only when explicitly requested

### Challenge 2: Wall Clock vs. Game Clock

**Problem:** Need both wall clock time (real-world) and game clock time (in-game)
- Wall clock: "7:37:34 PM CT" (when event occurred)
- Game clock: "6:02" (time remaining in quarter)

**Solution:**
- Store both timestamps in temporal_events table
- Map between wall clock and game clock for each event
- Enable queries by either clock type

### Challenge 3: Time Zone Handling

**Problem:** Games played in different time zones
- Lakers game in LA: 7:30 PM PT
- Celtics game in Boston: 7:30 PM ET
- Need unified temporal ordering

**Solution:**
- Store all timestamps in UTC
- Store local timezone with each game
- Convert to UTC during ingestion
- Display in user's preferred timezone

### Challenge 4: Birth Date Uncertainty

**Problem:** Some historical players have approximate birth dates
- "Born: March 1960" (day unknown)
- "Born: 1945" (month and day unknown)

**Solution:**
- Store birth date precision flag
- Age calculations include uncertainty bounds
- Queries return age ranges when appropriate

### Challenge 5: Missing Play-by-Play Data

**Problem:** Pre-1993 games have no play-by-play timestamps

**Solution:**
- Accept game-level precision for historical data
- Document precision limitations clearly
- Use Basketball Reference for pre-1993 aggregates

---

## Comparison to Similar Systems

### Financial Markets (High-Frequency Trading)
**Similarity:** Millisecond-precision event data
**Difference:** NBA has discrete events, markets have continuous prices

**Lessons learned:**
- Timestamp precision is critical
- Snapshot reconstruction at any moment
- Event ordering matters (causality)

### Medical Panel Data (Longitudinal Studies)
**Similarity:** Track individuals over time with measurements
**Difference:** NBA events are more frequent and precisely timed

**Lessons learned:**
- Handle missing data (injured players)
- Variable precision (different eras)
- Survival analysis (career length)

### IoT Sensor Data (Time-Series)
**Similarity:** High-frequency measurements from multiple sources
**Difference:** NBA has structured events, sensors have raw measurements

**Lessons learned:**
- Time synchronization across sources
- Data quality flags by precision level
- Efficient storage for high-volume data

---

## References

**Key Documentation:**
- `NBA_API_SCRAPER_OPTIMIZATION.md` - Scraper implementation details
- `DATA_AVAILABILITY_MATRIX.md` - Data availability by year and source
- `PROGRESS.md` - Project status and implementation plan
- `README.md` - Project overview and quick start

**Research:**
- Basketball-Reference play-by-play quality warnings
- NBA SportVU technology timeline
- Second Spectrum partnership documentation
- Panel data econometrics literature

---

## Frequently Asked Questions

### Q: Why not just use game-level statistics like everyone else?

**A:** Game-level statistics cannot answer temporal questions like "What were the cumulative statistics at the moment this play occurred?" Our goal is to enable temporal analysis at event-level resolution, similar to financial markets research.

### Q: Isn't millisecond precision overkill for basketball?

**A:** For current statistical analysis, yes. For future video synchronization at 30fps (~33ms per frame), no. We're building infrastructure that will enable frame-level video analysis synced with exact statistical snapshots.

### Q: How is this different from a traditional sports database?

**A:** Traditional databases store game-level aggregates. We store event-level timestamps and can reconstruct cumulative statistics at any point in time. It's the difference between "total career points" and "career points at 7:02:34 PM on June 19, 2016."

### Q: Why collect player birth dates?

**A:** To calculate precise player age at the moment of each event. Age affects performance, and knowing a player was "37 years, 234 days, 5 hours old" is more precise than "37 years old" for statistical modeling.

### Q: What about games before 1993 with no play-by-play data?

**A:** We accept game-level precision for historical data (1946-1992) from Basketball Reference. The temporal system is most valuable for modern data (1993+) where play-by-play exists.

### Q: Will this work with other sports?

**A:** Yes, the temporal panel data architecture is sport-agnostic. Hockey, football, baseball, soccer all have event-level data that could be structured this way. NBA is the pilot implementation.

---

## Conclusion

This project is building infrastructure for temporal panel data analysis in sports, starting with the NBA as a proof of concept.

**Short-term goal:** Query NBA statistics at any exact timestamp from 1993-present.

**Long-term vision:** Frame-level video synchronization with statistical snapshots for computer vision analysis.

**Unique value:** Millisecond-precision temporal resolution for a 79-year historical dataset.

---

*Document maintained by: Claude Code*
*Last reviewed: October 7, 2025*
*Status: Authoritative project vision - All other docs should align with this vision*
