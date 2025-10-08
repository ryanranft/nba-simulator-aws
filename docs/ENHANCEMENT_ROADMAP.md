# NBA Simulator Enhancement Roadmap

**Created:** October 6, 2025
**Status:** Two paths ready to implement
**Project State:** Core infrastructure complete ✅

---

## 🎯 Vision

Transform your NBA simulator from a basic Monte Carlo system into a sophisticated multi-level econometric forecasting platform powered by comprehensive multi-source data.

**Current capabilities:**
- 58 features (ESPN only)
- Simple Monte Carlo simulation
- 63% game outcome accuracy
- Basic win/loss prediction

**Target capabilities:**
- 209 features (5 data sources)
- Multi-level econometric simulation
- 75-80% game outcome accuracy
- Every statistic forecasted with confidence intervals

---

## 🗺️ Two Enhancement Paths

### Path 1: Multi-Source Data Integration 📊

**Goal:** Maximize ML granularity with 209 features from 5 sources

```
Week 1: Critical Advanced Features (12 hours)
├─ Basketball Reference scraper
│  ├─ TOS compliance (1 req/3 sec)
│  ├─ 47 advanced features
│  └─ TS%, PER, BPM, Win Shares
│
└─ NBA.com Stats expansion
   ├─ 11 API endpoints
   ├─ 92 tracking features
   └─ Movement, hustle, defense

Week 2: Historical & Storage (8 hours)
├─ Kaggle integration
│  ├─ 1946-1998 historical data
│  └─ 12 historical features
│
└─ Multi-source storage
   ├─ games_multi_source table
   ├─ Keep all sources (don't merge)
   └─ Confidence scores

Week 3: Feature Engineering (6 hours)
├─ ML pipeline
│  ├─ Combine 209 features
│  ├─ Handle NULLs
│  └─ Export to Parquet
│
└─ Quality dashboard
   ├─ Completeness tracking
   ├─ NULL rate monitoring
   └─ Validation metrics

Week 4: Validation (2 hours)
└─ SageMaker validation
   ├─ 209 features present
   ├─ NULL/infinite checks
   └─ File format validation

Total: 28 hours over 4 weeks
Cost: +$5-8/month
ML Boost: 63% → 75-80% accuracy
```

**Deliverables:**
- ✅ 209-feature ML dataset
- ✅ Historical coverage (1946-present)
- ✅ Advanced metrics (TS%, PER, BPM)
- ✅ Tracking data (movement, hustle)
- ✅ Defensive impact metrics
- ✅ Quality dashboard

---

### Path 2: Advanced Simulation Framework 🚀

**Goal:** Replace simple Monte Carlo with sophisticated econometric models

```
Weeks 1-2: Panel Data Models
├─ Team-game panel structure
├─ Fixed effects estimation
├─ Interactive effects (OffRtg × Pace)
└─ Store parameters for simulation

Weeks 3-4: Cluster Equations
├─ 4-equation simultaneous system
│  ├─ OffRtg = f(Pace, Shot_Quality, TO)
│  ├─ DefRtg = g(Opp_Shot_Qual, Reb, Steals)
│  ├─ Pace = h(Team_Style, Opp_Style, Margin)
│  └─ Shot_Qual = j(Spacing, Movement, Defense)
│
├─ 3SLS estimation
└─ Solve for equilibrium

Week 5: Non-Linear Dynamics
├─ Momentum effects
│  └─ P(basket) = logit(β0 + β1*run + β2*run² + β3*run³)
│
├─ Fatigue curves
│  └─ Performance = β0 * exp(-λ * minutes)
│
└─ Regime-switching
   ├─ Normal play
   ├─ Clutch time (last 2 min, close game)
   └─ Garbage time (blowout)

Week 6: Hierarchical Bayesian
├─ Multi-level structure
│  ├─ League → Team → Player
│  └─ Partial pooling (borrow strength)
│
├─ MCMC sampling (PyMC)
└─ Posterior distributions

Weeks 7-8: Integration
├─ Unified simulation engine
│  ├─ Combine all models
│  ├─ Possession-by-possession
│  └─ Forecast every statistic
│
└─ Validation framework
   ├─ Score MAE < 5 points
   ├─ Win prob accuracy > 75%
   └─ Variance calibration 0.9-1.1

Total: 6-8 weeks
Cost: +$5-10/month
Simulation Boost: 12 → <5 MAE (60% improvement)
```

**Deliverables:**
- ✅ Panel data models (team fixed effects)
- ✅ Cluster equation system (4 equations, 3SLS)
- ✅ Non-linear dynamics (momentum, fatigue, regimes)
- ✅ Hierarchical Bayesian (player/team/league)
- ✅ Integrated simulation engine
- ✅ Every statistic forecasted

---

## 📈 Sequential Implementation (Recommended)

**Total timeline: 10-12 weeks**

```
Weeks 1-4: Multi-Source Integration
├─ Week 1: Basketball Ref + NBA.com Stats
├─ Week 2: Kaggle + Multi-source storage
├─ Week 3: Feature engineering + Dashboard
└─ Week 4: SageMaker validation
   └─ ✅ 209 features available

         ↓ (Now simulation has richer data)

Weeks 5-12: Advanced Simulation
├─ Weeks 5-6: Panel data models
├─ Weeks 7-8: Cluster equations
├─ Week 9: Non-linear dynamics
├─ Week 10: Hierarchical Bayesian
└─ Weeks 11-12: Integration + Validation
   └─ ✅ Econometric simulation complete

Total Cost: +$10-18/month
Total Time: 10-12 weeks
Final State: 209 features + sophisticated simulation
```

**Why sequential?**
1. Shorter time to first results (4 weeks vs 8 weeks)
2. Econometric models benefit from 209 features
3. Panel data needs tracking data
4. Hierarchical Bayesian needs advanced metrics
5. Incremental value delivery

---

## 🎯 Capability Progression

### Current State (Today)

```
Data:
├─ ESPN only: 58 features
├─ Coverage: 1999-2025
└─ Quality: 89.9% complete

ML:
├─ Game outcome: 63% accuracy
├─ Player points MAE: 12
└─ Models: Logistic, RF, XGBoost, LightGBM

Simulation:
├─ Simple Monte Carlo
├─ Linear probabilities
└─ No temporal dependencies

Cost: $38.33/month
```

### After Multi-Source (Week 4)

```
Data:
├─ 5 sources: 209 features
│  ├─ ESPN: 58 features
│  ├─ Basketball Ref: 47 features (advanced)
│  ├─ NBA.com Stats: 92 features (tracking)
│  ├─ Kaggle: 12 features (historical)
│  └─ Derived: 20+ features (efficiency)
│
├─ Coverage: 1946-2025 (historical backfill)
└─ Quality: ≥90% complete (2016-present)

ML:
├─ Game outcome: 75-80% accuracy (+15-20%)
├─ Player points MAE: 8 (-33%)
├─ NEW: Defensive rating prediction
└─ NEW: Playoff probability (AUC ≥0.80)

Simulation:
└─ (Still simple Monte Carlo)

Cost: $43-46/month (+$5-8)
```

### After Advanced Simulation (Week 12)

```
Data:
└─ (Same as Week 4: 209 features)

ML:
├─ Game outcome: 75-80% accuracy
├─ Player points MAE: 8
├─ Defensive rating prediction
└─ Playoff probability (AUC ≥0.80)

Simulation:
├─ Multi-level econometric engine
│  ├─ Panel data (team fixed effects)
│  ├─ Cluster equations (simultaneous)
│  ├─ Non-linear dynamics (momentum, fatigue)
│  ├─ Hierarchical Bayesian (player/team/league)
│  └─ Regime-switching (normal/clutch/garbage)
│
├─ Score prediction MAE: <5 points (-60%)
├─ Win probability: >75% accuracy (+12%)
├─ Variance calibration: 0.9-1.1
└─ Every statistic forecasted with confidence intervals

Cost: $48-56/month (+$10-18 total)
```

**Final state: 63% under $150/month budget ✅**

---

## 💰 Cost Breakdown

### Current Monthly Costs

```
S3 Storage:           $2.74
RDS (db.t3.small):   $29.00
EC2 (t3.small):       $6.59
Monitoring:           $0.00
────────────────────────────
Total:               $38.33/month
```

### After Multi-Source Integration (Week 4)

```
S3 Storage:           $5-7    (+$3 for 50GB additional)
RDS (db.t3.small):   $29.00
EC2 (t3.small):       $6.59
API calls:            $1-2    (Basketball Ref, NBA.com - free but rate-limited)
Monitoring:           $0.00
────────────────────────────
Total:               $43-46/month (+$5-8)
```

### After Advanced Simulation (Week 12)

```
S3 Storage:           $5-7
RDS (db.t3.small):   $29.00
EC2 (simulation):    $10-15  (increased for econometric compute)
API calls:            $1-2
Monitoring:           $0.00
────────────────────────────
Total:               $48-56/month (+$10-18 from baseline)

Budget: $150/month target
Used: $48-56/month (63-68% under budget) ✅
```

---

## 📊 Feature Availability Matrix

**Which features are available in each state:**

| Feature Category | Current | After Multi-Source | After Adv Sim |
|------------------|---------|-------------------|---------------|
| **Basic box score** | ✅ 25 | ✅ 25 | ✅ 25 |
| **Advanced shooting** | ❌ 0 | ✅ 8 (TS%, eFG%) | ✅ 8 |
| **Impact metrics** | ❌ 0 | ✅ 10 (PER, BPM, WS) | ✅ 10 |
| **Usage/percentages** | ❌ 0 | ✅ 12 (USG%, REB%) | ✅ 12 |
| **Team ratings** | ❌ 0 | ✅ 7 (ORtg, DRtg, Pace) | ✅ 7 |
| **Four Factors** | ❌ 0 | ✅ 10 (eFG%, TOV%, ORB%, FTR) | ✅ 10 |
| **Player tracking** | ❌ 0 | ✅ 12 (distance, speed) | ✅ 12 |
| **Ball handling** | ❌ 0 | ✅ 15 (touches, drives) | ✅ 15 |
| **Shot quality** | ❌ 0 | ✅ 18 (defender dist, clock) | ✅ 18 |
| **Hustle stats** | ❌ 0 | ✅ 12 (deflections, charges) | ✅ 12 |
| **Defensive impact** | ❌ 0 | ✅ 15 (matchup FG%, rim protection) | ✅ 15 |
| **Historical (1946-1998)** | ❌ 0 | ✅ 12 | ✅ 12 |
| **Derived features** | ❌ 0 | ✅ 20+ (efficiency, momentum) | ✅ 20+ |
| **Econometric params** | ❌ 0 | ❌ 0 | ✅ 50+ (panel coefs, etc.) |
| **TOTAL** | **58** | **209** | **259+** |

---

## 🏆 Success Metrics

### Multi-Source Integration Success Criteria

**Data quality:**
- [ ] Feature completeness ≥90% (2016-present)
- [ ] Historical coverage ≥80% (1946-1999)
- [ ] NULL rate ≤15% per feature
- [ ] Confidence score ≥0.80 average

**ML performance:**
- [ ] Game outcome accuracy ≥75% (vs current 63%)
- [ ] Player points MAE ≤8 (vs current 12)
- [ ] Defensive rating prediction enabled
- [ ] Playoff probability AUC ≥0.80

**Technical:**
- [ ] All 5 sources integrated
- [ ] 209 features extracted per game
- [ ] SageMaker validation passed
- [ ] Quality dashboard operational

---

### Advanced Simulation Success Criteria

**Model performance:**
- [ ] Score prediction MAE <5 points (vs current 12)
- [ ] Win probability accuracy >75% (vs current 63%)
- [ ] Variance calibration 0.9-1.1
- [ ] All 209 statistics forecasted

**Technical validation:**
- [ ] Panel model R² >0.80
- [ ] Cluster system convergence <50 iterations
- [ ] MCMC diagnostics pass (Rhat <1.01)
- [ ] Out-of-sample RMSE < training RMSE * 1.1

**Simulation capabilities:**
- [ ] Possession-by-possession dynamics
- [ ] Momentum effects captured
- [ ] Fatigue curves estimated
- [ ] Regime-switching operational

---

## 📚 Documentation Quick Reference

### Multi-Source Integration Docs

1. **[ML_FEATURE_CATALOG.md](ML_FEATURE_CATALOG.md)** - All 209 features
2. **[IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)** - Week-by-week tasks
3. **[QUICK_START_MULTI_SOURCE.md](QUICK_START_MULTI_SOURCE.md)** - Quick reference
4. **[PHASE_1_MULTI_SOURCE_PLAN.md](PHASE_1_MULTI_SOURCE_PLAN.md)** - Detailed plan
5. **[DATA_SOURCE_MAPPING.md](DATA_SOURCE_MAPPING.md)** - ID conversion
6. **[DATA_DEDUPLICATION_RULES.md](DATA_DEDUPLICATION_RULES.md)** - Conflict resolution
7. **[FIELD_MAPPING_SCHEMA.md](FIELD_MAPPING_SCHEMA.md)** - Transformations

### Advanced Simulation Docs

1. **[ADVANCED_SIMULATION_FRAMEWORK.md](ADVANCED_SIMULATION_FRAMEWORK.md)** - Complete architecture
   - Multi-level simulation hierarchy
   - Econometric techniques (panel, cluster, non-linear, Bayesian)
   - Code examples
   - 6-8 week roadmap
   - Validation framework

### Decision Guides

1. **[NEXT_STEPS_OPTIONS.md](NEXT_STEPS_OPTIONS.md)** - Compare both paths
2. **[SESSION_SUMMARY_2025_10_06_CONTINUED.md](SESSION_SUMMARY_2025_10_06_CONTINUED.md)** - Planning recap
3. **[ENHANCEMENT_ROADMAP.md](ENHANCEMENT_ROADMAP.md)** - This document

---

## 🚀 Getting Started

### Option 1: Multi-Source Integration

**First command to run:**

```bash
cd /Users/ryanranft/nba-simulator-aws

# Test Basketball Reference scraper on one month
python scripts/etl/scrape_basketball_reference.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31

# Verify TOS compliance (1 req/3 sec)
# Check output for 47 features per game
```

**Documents to read first:**
1. `docs/archive/planning/IMPLEMENTATION_CHECKLIST.md` - Sub-Phase 1.10
2. `docs/ML_FEATURE_CATALOG.md` - Basketball Reference features

---

### Option 2: Advanced Simulation

**First command to run:**

```bash
# Install required packages
pip install linearmodels pymc arviz statsmodels

# Prepare panel data
python scripts/simulation/prepare_panel_data.py \
  --start-season 2020 \
  --end-season 2024

# Check output: team-game observations with lagged variables
```

**Documents to read first:**
1. `docs/ADVANCED_SIMULATION_FRAMEWORK.md` - Sub-Phase 4.5.1
2. Econometric literature references (Wooldridge, Greene)

---

### Option 3: Sequential (Recommended)

**Start with multi-source integration, then add advanced simulation.**

**Timeline:** 10-12 weeks total
**Cost:** +$10-18/month
**Outcome:** Maximum sophistication

---

## 🎯 Key Decisions

**You need to decide:**

1. **Which path to start with?**
   - Multi-source integration (4 weeks)
   - Advanced simulation (8 weeks)
   - Sequential (12 weeks total)

2. **When to start?**
   - Immediately (documentation ready)
   - After review (ask questions first)
   - Staged approach (one sub-phase at a time)

3. **Resource allocation?**
   - Development time availability
   - Budget comfort level ($10-18/month additional)
   - Priority: ML accuracy vs simulation sophistication

**All planning is complete. Ready to begin implementation immediately.**

---

## 💡 Final Recommendation

**Suggested approach: Sequential implementation**

**Week 1-4: Multi-Source Integration**
- Delivers immediate value (209 features)
- Shorter timeline to first results
- Enables better ML models
- Foundation for advanced simulation

**Week 5-12: Advanced Simulation**
- Benefits from richer 209-feature dataset
- Econometric models powered by tracking data
- Complete sophistication
- Every statistic forecasted

**Total investment:**
- Time: 10-12 weeks
- Cost: +$10-18/month
- ROI: 260% feature increase + 60% simulation improvement

**Budget status:** 63% under $150/month target ✅

---

**Ready to start?** Choose your path and let's begin implementation!

---

*Last updated: October 6, 2025*
*Roadmap version 1.0 - Two enhancement paths ready to implement*
