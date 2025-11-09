# nba-simulator-aws ↔ nba-mcp-synthesis Relationship

**Created:** November 9, 2025
**Purpose:** Clarify how the two projects share hoopR data

---

## Quick Summary

**TL;DR:** Both projects use the SAME hoopR data from the parquet backup, but for different purposes:
- **nba-simulator-aws:** Production temporal panel system (cloud-based, comprehensive)
- **nba-mcp-synthesis:** Local betting analysis (local PostgreSQL, Phase 1 only)

**The parquet files are NOT new data - they're a backup that's already in nba-simulator-aws.**

---

## Project Comparison

| Aspect | nba-simulator-aws | nba-mcp-synthesis |
|--------|------------------|-------------------|
| **Purpose** | Temporal panel data system for NBA simulation | Local betting model development |
| **Infrastructure** | AWS (S3 + RDS) | Local PostgreSQL |
| **hoopR Data** | Phase 1 (parquet) + 152-endpoint collection | Phase 1 (parquet) only |
| **Database Size** | 13.9 GB (ESPN + hoopR) | 13.95M rows (hoopR only) |
| **Data Sources** | ESPN, hoopR, NBA API, BBRef, Kaggle | hoopR only |
| **Cost** | ~$2.74/month (S3 only currently) | $0 (local only) |
| **Use Case** | ML training, simulation, research | Betting analysis, feature engineering |
| **Active Development** | Yes (daily autonomous collection) | Yes (betting models) |

---

## Shared Data: hoopR Phase 1

### What Data is Shared?

**Source:** `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/` (parquet backup)

**Contents:**
- 30,758 games (2002-2025)
- 13,074,829 play-by-play events
- 785,505 player box scores
- 59,670 team box scores

**Format:** 96 parquet files (24 seasons × 4 data types)

### Where This Data Lives:

**nba-simulator-aws:**
1. **S3:** `s3://nba-sim-raw-data-lake/hoopr_parquet/` (531 MB compressed)
2. **RDS:** 4 tables in `nba_simulator` database (6.7 GB)
   - `hoopr_play_by_play`
   - `hoopr_player_box`
   - `hoopr_team_box`
   - `hoopr_schedule`
3. **Local backup:** `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/` (6.2 GB parquet)

**nba-mcp-synthesis:**
1. **Local PostgreSQL:** `hoopr_raw.*` schema in `nba_mcp_synthesis` database
   - `hoopr_raw.nba_play_by_play` (13.1M rows)
   - `hoopr_raw.nba_player_box` (785K rows)
   - `hoopr_raw.nba_team_box` (59K rows)
   - `hoopr_raw.nba_schedule` (30K rows)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Original Collection: NBA Stats API → hoopR R Package            │
│ Location: /Users/ryanranft/Projects/hoopR-nba-raw (43 GB JSON)  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Converted to Parquet
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Parquet Backup (Shared Source)                                  │
│ Location: /Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/│
│ Size: 6.2 GB (96 parquet files)                                 │
│ Coverage: 2002-2025 (24 seasons)                                │
└────────────┬───────────────────────────┬────────────────────────┘
             │                           │
             │                           │
    ┌────────▼────────┐         ┌────────▼────────┐
    │ nba-simulator   │         │ nba-mcp-        │
    │ -aws            │         │ synthesis       │
    │ (Production)    │         │ (Betting)       │
    └────────┬────────┘         └────────┬────────┘
             │                           │
    ┌────────▼────────────────┐  ┌──────▼──────────────┐
    │ S3 (cloud storage)      │  │ PostgreSQL (local)  │
    │ 531 MB compressed       │  │ hoopr_raw schema    │
    │                         │  │ 13.95M rows         │
    └────────┬────────────────┘  └─────────────────────┘
             │
    ┌────────▼────────────────┐
    │ RDS (cloud database)    │
    │ 4 tables, 6.7 GB        │
    │ Indexed & optimized     │
    └─────────────────────────┘
```

---

## Why Two Projects?

### nba-simulator-aws (Production System)

**Focus:** Comprehensive NBA temporal panel data system

**Goals:**
- Query NBA statistics at any exact moment in history
- Enable millisecond-precision game simulation
- Support econometric causal inference research
- Provide foundation for ML model training

**Data Strategy:**
- Multi-source integration (ESPN, hoopR, NBA API, BBRef)
- Comprehensive collection (152 hoopR endpoints)
- Cloud-based for scalability
- Daily autonomous collection

**Use Cases:**
- Academic research
- Game simulation
- Temporal queries ("What were Kobe's stats at 7:02 PM on June 19, 2016?")
- ML model training with 500+ features

---

### nba-mcp-synthesis (Betting Analysis)

**Focus:** Local betting model development and analysis

**Goals:**
- Build profitable NBA betting models
- Analyze historical betting performance
- Generate game predictions
- Feature engineering for ML

**Data Strategy:**
- Single source (hoopR Phase 1 only)
- Local PostgreSQL (no cloud costs)
- Sufficient data for betting features
- No need for comprehensive 152-endpoint collection

**Use Cases:**
- Betting model training
- Game outcome prediction
- Feature extraction for ML
- Historical betting backtesting

---

## Why Not Share All Data?

### nba-simulator-aws Has More Data:

**Additional Sources:**
- **ESPN:** 44,826 games (1993-2025)
- **Basketball Reference:** 75 seasons (1950-2025)
- **NBA API:** Advanced metrics (planned)
- **Kaggle:** Validation dataset (2004-2020)

**Additional hoopR Data (152 Endpoints):**
- Player tracking (speed, distance, touches)
- Synergy play types
- Clutch performance splits
- Defensive impact metrics
- Hustle stats
- Shot charts
- Lineup combinations

**Why Not in nba-mcp-synthesis?**
- Betting models don't need 500+ features
- 152-endpoint data is ~500 GB (too large for local)
- Phase 1 data sufficient for betting analysis
- Focus on simplicity and speed

---

## Data Transfer: Do You Need It?

### Question: Should I copy data from nba-mcp-synthesis to nba-simulator-aws?

**Answer: No!** The data is already there.

**Explanation:**
1. Both projects loaded from the SAME parquet backup
2. nba-simulator-aws loaded parquet → S3 + RDS (October 9, 2025)
3. nba-mcp-synthesis loaded parquet → Local PostgreSQL (November 7, 2025)
4. The parquet files are a backup, not a separate data source

---

### Question: Should I copy 152-endpoint data to nba-mcp-synthesis?

**Answer: Probably not, unless you need advanced features.**

**Considerations:**

**Reasons NOT to:**
- ❌ 500 GB of data (vs 6.7 GB Phase 1 only)
- ❌ Betting models typically don't need 500+ features
- ❌ Local storage constraints
- ❌ Query performance (too much data for local PostgreSQL)

**Reasons TO (if applicable):**
- ✅ You need player tracking features
- ✅ You need synergy play types
- ✅ You want clutch performance splits
- ✅ You're willing to manage large local database

**Alternative:**
- Connect nba-mcp-synthesis to nba-simulator-aws RDS remotely
- Query only needed data (don't store locally)
- Use SQL views to filter to relevant features

---

## Local Development Workflow

### Option 1: Keep Separate (Recommended)

**nba-simulator-aws:**
- Production data collection and storage
- Comprehensive 152-endpoint hoopR collection
- Multi-source integration
- Cloud-based (S3 + RDS)

**nba-mcp-synthesis:**
- Local betting analysis
- Phase 1 hoopR data only
- Fast local queries
- No cloud costs

**Benefit:** Each project optimized for its use case

---

### Option 2: Shared RDS Connection

**Setup:**
1. Connect nba-mcp-synthesis to nba-simulator-aws RDS
2. Use SQL to filter needed data
3. Cache frequently-used data locally

**Code Example:**
```python
# In nba-mcp-synthesis
import psycopg2

# Connect to nba-simulator-aws RDS
conn = psycopg2.connect(
    host="<RDS_ENDPOINT>",
    database="nba_simulator",
    user="<USER>",
    password="<PASSWORD>"
)

# Query specific data
query = """
SELECT game_id, game_date, home_score, away_score
FROM hoopr_schedule
WHERE season >= 2020
"""

df = pd.read_sql(query, conn)
```

**Benefit:** Access all data without local storage

**Cost:** Network latency + potential RDS charges

---

### Option 3: Selective Feature Sync

**Setup:**
1. Identify specific 152-endpoint features needed for betting
2. Extract only those features from nba-simulator-aws
3. Load to nba-mcp-synthesis as CSV or parquet

**Example:**
```bash
# On nba-simulator-aws
psql -d nba_simulator -c "
COPY (
  SELECT game_id, player_id, clutch_points, clutch_assists
  FROM hoopr_player_clutch_stats
  WHERE season >= 2020
) TO '/tmp/clutch_features.csv' CSV HEADER;
"

# Copy to nba-mcp-synthesis
# Load into local PostgreSQL
```

**Benefit:** Get advanced features without full 152-endpoint collection

---

## Summary & Recommendations

### ✅ Current Setup is Optimal

Both projects have the hoopR Phase 1 data they need:
- nba-simulator-aws: In S3 + RDS (production)
- nba-mcp-synthesis: In local PostgreSQL (betting)

**No data transfer needed!**

---

### ✅ Maintain Independence

Keep projects separate:
- nba-simulator-aws: Comprehensive data collection
- nba-mcp-synthesis: Focused betting analysis

**Each optimized for its purpose.**

---

### 🔄 Optional Future Integration

If you need advanced features in nba-mcp-synthesis:
1. Start with RDS connection (no local storage)
2. Test which features improve betting models
3. Only then consider selective feature sync

**Don't copy all 152-endpoint data unless proven valuable.**

---

## File References

### Documentation

**In nba-simulator-aws:**
- `docs/HOOPR_DATA_SOURCES_EXPLAINED.md` - Complete hoopR data explanation
- `docs/DATA_CATALOG.md` - All data sources catalog
- `docs/phases/phase_0/0.0002_hoopr_data_collection/` - hoopR collection docs

**In nba-mcp-synthesis:**
- `reports/DATA_SOURCE_CLARIFICATION.md` - Source clarification
- `docs/plans/LOCAL_DATABASE_VALIDATION_PLAN.md` - Validation plan

### Scripts

**nba-simulator-aws:**
- `scripts/db/load_hoopr_to_rds.py` - RDS loading
- `scripts/etl/scrape_hoopr_all_152_endpoints.R` - Comprehensive scraper
- `scripts/autonomous/run_scheduled_hoopr_comprehensive.sh` - Daily collection

**nba-mcp-synthesis:**
- `scripts/load_parquet_to_postgres.py` - Parquet → PostgreSQL
- `scripts/reorganize_hoopr_schema.py` - Schema reorganization
- `scripts/validate_hoopr_data.py` - Data validation

---

## FAQ

**Q: Is the data in both projects identical?**
A: Yes, the Phase 1 hoopR data (parquet backup) is identical. nba-simulator-aws has additional data sources and 152-endpoint collection.

**Q: Why does nba-simulator-aws have more data?**
A: It's a comprehensive research platform with multi-source integration. nba-mcp-synthesis focuses only on betting.

**Q: Should I delete the parquet backup?**
A: No! Keep it as disaster recovery. It's only 6.2 GB.

**Q: Can I use nba-simulator-aws data for betting?**
A: Yes! Connect nba-mcp-synthesis to RDS or export specific features.

**Q: How much does it cost to run both?**
A: nba-simulator-aws: ~$2.74/month S3, nba-mcp-synthesis: $0 (local only)

---

**Last Updated:** November 9, 2025
**Projects:** nba-simulator-aws (production) + nba-mcp-synthesis (betting)
