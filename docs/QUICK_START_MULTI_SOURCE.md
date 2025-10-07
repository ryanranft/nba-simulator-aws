# Quick Start: Multi-Source Data Integration

**Created:** October 6, 2025
**Purpose:** Fast reference for implementing 209-feature ML dataset
**Status:** Ready to implement

---

## 🎯 What We're Building

**Goal:** Extract 209 ML features from 5 data sources for SageMaker training

**Current state:** 58 features (ESPN only)
**Target state:** 209 features (all sources)
**Time required:** 28 hours (4 weeks)
**Cost:** ~$5-8/month

---

## 📊 Feature Breakdown

| Source | Features | Priority | Status |
|--------|----------|----------|--------|
| **ESPN** | 58 | ✅ Have | Already in S3 |
| **Basketball Reference** | 47 | 🔴 CRITICAL | Week 1 |
| **NBA.com Stats** | 92 | 🔴 CRITICAL | Week 1 |
| **Kaggle** | 12 | 🟡 Important | Week 2 |
| **Derived** | 20+ | 🟢 Optimization | Week 3 |
| **TOTAL** | **209** | | 4 weeks |

---

## 🚀 Implementation Order

### Week 1: Critical Advanced Features (12 hours)

**Day 1-2: Basketball Reference (8 hours)**
```bash
# Create scraper
python scripts/etl/scrape_basketball_reference.py

# What it gets:
# - True Shooting % (TS%)
# - Player Efficiency Rating (PER)
# - Box Plus/Minus (BPM)
# - Win Shares
# - Usage Rate
# - Four Factors
# ... 41 more advanced stats

# Output: 47 features per game
```

**Day 3-4: NBA.com Stats ALL Endpoints (4 hours)**
```bash
# Expand existing scraper
python scripts/etl/expand_nba_stats_scraper.py

# What it gets:
# - Player tracking (distance, speed, touches)
# - Shot quality (defender distance, shot clock)
# - Hustle stats (deflections, charges, screens)
# - Defensive matchups
# ... 88 more tracking features

# Output: 92 features per game
```

### Week 2: Historical & Storage (8 hours)

**Day 5-6: Kaggle Historical (4 hours)**
```bash
# Download and extract
python scripts/etl/extract_kaggle_historical.py

# What it gets:
# - Pre-1999 games (fill 1946-1998 gap)
# - 12 historical features

# Output: 50,000+ historical games
```

**Day 7-8: Multi-Source Storage (4 hours)**
```sql
-- Create new tables (DON'T merge sources)
CREATE TABLE player_advanced_stats (...);
CREATE TABLE player_tracking_stats (...);
CREATE TABLE games_multi_source (...);

-- Store all sources separately
-- Add confidence scores as features
```

### Week 3: Feature Engineering (6 hours)

**Day 9-10: Feature Engineering (4 hours)**
```python
# Create unified feature vectors
python scripts/ml/engineer_features.py

# Combines all sources:
# ESPN (58) + BRef (47) + NBA.com (92) + Kaggle (12) + Derived (20+)

# Output: 209-feature vectors for SageMaker
```

**Day 11: Quality Dashboard (2 hours)**
```bash
# Monitor feature completeness
python scripts/analytics/generate_quality_dashboard.py

# Shows:
# - Feature availability by era
# - NULL rates per feature
# - Source coverage
```

### Week 4: Validation (4 hours)

**Day 12-13: SageMaker Validation (2 hours)**
```python
# Validate for SageMaker
python scripts/ml/validate_for_sagemaker.py

# Checks:
# - No NULLs (or handled properly)
# - Data types correct
# - No infinite values
# - Label balance
```

**Day 14: Optional Cross-Validation (2 hours)**
```bash
# SportsDataverse (optional)
python scripts/etl/scrape_sportsdataverse.py
```

---

## 📚 Key Documents

**Planning & Strategy:**
1. 📖 [ML_FEATURE_CATALOG.md](ML_FEATURE_CATALOG.md) - Complete 209-feature list ⭐
2. 📋 [PHASE_1_MULTI_SOURCE_PLAN.md](phases/PHASE_1_MULTI_SOURCE_PLAN.md) - Detailed roadmap
3. 📊 [SESSION_SUMMARY_2025_10_06.md](SESSION_SUMMARY_2025_10_06.md) - Session recap

**Technical Reference:**
4. 🔗 [DATA_SOURCE_MAPPING.md](DATA_SOURCE_MAPPING.md) - ID conversion strategies
5. ⚙️ [FIELD_MAPPING_SCHEMA.md](FIELD_MAPPING_SCHEMA.md) - Field transformations
6. 🔀 [DATA_DEDUPLICATION_RULES.md](DATA_DEDUPLICATION_RULES.md) - Keep-all-sources strategy

---

## 🗄️ Database Schema

### New Tables to Create

```sql
-- Basketball Reference advanced stats
CREATE TABLE player_advanced_stats (
    player_id INTEGER,
    game_id VARCHAR(50),
    true_shooting_pct DECIMAL(4,3),
    effective_fg_pct DECIMAL(4,3),
    usage_rate DECIMAL(4,3),
    player_efficiency_rating DECIMAL(5,2),
    box_plus_minus DECIMAL(5,2),
    value_over_replacement DECIMAL(5,2),
    win_shares DECIMAL(5,3),
    -- ... 40 more fields
    data_source VARCHAR(20) DEFAULT 'bref',
    PRIMARY KEY (player_id, game_id)
);

-- NBA.com Stats tracking
CREATE TABLE player_tracking_stats (
    player_id INTEGER,
    game_id VARCHAR(50),
    dist_feet DECIMAL(7,1),
    dist_miles DECIMAL(4,2),
    avg_speed DECIMAL(4,2),
    touches INTEGER,
    drives INTEGER,
    deflections INTEGER,
    contested_shots INTEGER,
    contested_fg_pct DECIMAL(4,3),
    -- ... 82 more fields
    data_source VARCHAR(20) DEFAULT 'nba_stats',
    PRIMARY KEY (player_id, game_id)
);

-- Multi-source storage (keep all, don't merge)
CREATE TABLE games_multi_source (
    composite_key VARCHAR(100) PRIMARY KEY,
    game_date DATE,
    home_team_abbr VARCHAR(3),
    away_team_abbr VARCHAR(3),

    -- ESPN data
    espn_game_id VARCHAR(50),
    espn_home_score INTEGER,
    espn_data JSONB,

    -- NBA.com data
    nba_game_id VARCHAR(50),
    nba_home_score INTEGER,
    nba_data JSONB,

    -- Basketball Reference data
    bref_slug VARCHAR(50),
    bref_home_score INTEGER,
    bref_data JSONB,

    -- Derived best estimates
    final_home_score INTEGER,
    final_away_score INTEGER,
    confidence_score DECIMAL(3,2),

    -- Meta
    sources_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎯 Success Criteria

### Data Quality
- [ ] ≥90% feature completeness for 2016-present
- [ ] ≥80% historical coverage for 1946-1999
- [ ] ≤15% NULL rate per feature
- [ ] ≥0.80 average confidence score

### ML Performance (After Implementation)
- [ ] Game outcome accuracy: ≥75% (current: 63%)
- [ ] Player points MAE: ≤8 (current: 12)
- [ ] New capability: Defensive rating prediction
- [ ] New capability: Playoff probability (AUC ≥0.80)

---

## 🚨 Critical Reminders

### Basketball Reference Compliance
- ⚠️ Rate limit: **1 request per 3 seconds** (strict)
- ⚠️ User-Agent: Identify as bot ("NBA-Simulator-Bot/1.0")
- ⚠️ TOS: Academic/personal use OK, commercial requires permission
- ⚠️ Respect robots.txt

### NBA.com Stats API
- ℹ️ No API key needed (but requires User-Agent header)
- ℹ️ Rate limit: ~10-20 requests/minute (unofficial)
- ℹ️ Use exponential backoff on failures
- ℹ️ 11 endpoints to implement (not just 1)

### Data Strategy
- ✅ Keep all sources (don't merge)
- ✅ Store confidence scores as ML features
- ✅ Track source per field (JSONB metadata)
- ✅ Handle NULLs with `-1` or `_missing` flags

---

## 💡 Quick Wins

**You can start TODAY with:**

### Option 1: Basketball Reference (8 hours)
```bash
# Implement the MOST CRITICAL source first
# Gets 47 advanced features ESPN doesn't have

cd /Users/ryanranft/nba-simulator-aws
python scripts/etl/scrape_basketball_reference.py --start-date 2024-01-01 --end-date 2024-01-31

# Test on January 2024 (one month)
# Validate TOS compliance
# Then scale to full dataset
```

### Option 2: NBA.com Stats Expansion (4 hours)
```bash
# Expand existing NBA.com Stats scraper
# Add 10 more endpoints

python scripts/etl/expand_nba_stats_scraper.py --endpoints all --sample-size 100

# Test on 100 games first
# Verify rate limits
# Then scale up
```

### Option 3: Feature Engineering Test (2 hours)
```bash
# Test feature engineering on existing ESPN data
# Add derived features

python scripts/ml/engineer_features.py --source espn-only --output test_features.csv

# Creates:
# - pts_per_touch
# - efficiency_score
# - momentum features
# ... 20+ derived features
```

---

## 📈 Expected Outcomes

### After Week 1 (Basketball Ref + NBA.com Stats)
- **Features available:** 197 (58 ESPN + 47 BRef + 92 NBA.com)
- **Coverage:** 2016-present (full feature set)
- **ML accuracy improvement:** +15-20% (estimated)

### After Week 2 (+ Kaggle historical)
- **Features available:** 209 (all sources)
- **Coverage:** 1946-present (historical backfill)
- **Historical modeling:** Enabled

### After Week 3 (+ Feature engineering)
- **ML-ready dataset:** Complete
- **SageMaker export:** Parquet format in S3
- **Model training:** Ready to begin

### After Week 4 (+ Validation)
- **Data quality:** Verified
- **Production ready:** YES
- **Continuous updates:** Automated

---

## 🔗 Next Steps

**Right now:**
1. Review [ML_FEATURE_CATALOG.md](ML_FEATURE_CATALOG.md) - See all 209 features
2. Choose: Start with Basketball Reference OR NBA.com Stats
3. Create database tables (see schema above)
4. Run first scraper (test on small sample first)

**This week:**
1. Implement both Basketball Reference and NBA.com Stats
2. Store in new database tables
3. Run validation on sample games

**Next week:**
1. Add Kaggle historical data
2. Build feature engineering pipeline
3. Export to SageMaker format

**Final week:**
1. Validate for SageMaker
2. Train initial models with 209 features
3. Compare performance vs ESPN-only (58 features)

---

## 💰 Cost Tracking

### One-Time Costs
- Development time: 28 hours @ your hourly rate
- Kaggle download: $0 (one-time, 2-5GB)

### Monthly Ongoing Costs
- S3 storage: $3-5/month (50GB additional)
- API calls: $1-2/month (rate-limited, free APIs)
- Compute: $0 (local processing)
- **Total: $5-8/month**

### ROI
- **Feature increase:** 260% (58 → 209)
- **Cost increase:** $3-6/month
- **ML accuracy improvement:** +15-25% (estimated)
- **Verdict:** EXCELLENT ROI

---

## 📞 Help & Support

**If you get stuck:**
1. Check [PHASE_1_MULTI_SOURCE_PLAN.md](phases/PHASE_1_MULTI_SOURCE_PLAN.md) - Detailed steps
2. Review [DATA_SOURCE_MAPPING.md](DATA_SOURCE_MAPPING.md) - ID conversions
3. See [SESSION_SUMMARY_2025_10_06.md](SESSION_SUMMARY_2025_10_06.md) - Full context

**Common issues:**
- **Basketball Reference scraper fails:** Check rate limit (1 req/3 sec)
- **NBA.com Stats timeout:** Add exponential backoff
- **ID mapping fails:** Use composite key (date + teams)
- **Features missing:** Check data availability matrix in ML_FEATURE_CATALOG.md

---

**Ready to start?** Choose Week 1 task (Basketball Reference or NBA.com Stats) and begin! 🚀

---

*Last updated: October 6, 2025*
*Quick start for 209-feature ML dataset implementation*
