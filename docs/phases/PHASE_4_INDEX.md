# Phase 4: Simulation Engine

**Status:** ✅ COMPLETE (basic) | 🔄 READY FOR ENHANCEMENT (📚 1 enhancement recommendation available)
**Priority:** MEDIUM-HIGH
**Prerequisites:** Phase 0-3 complete (database operational)
**Estimated Time:** 8-10 hours (basic) | 20-30 hours (advanced)
**Cost Impact:** $5-15/month (EC2 for simulations)
**Started:** October 3, 2025
**Completed:** October 3, 2025 (basic implementation)

---

## Overview

Build game simulation engine with temporal state reconstruction. This phase creates the Monte Carlo simulation system that can replay games from any moment in time and simulate alternative outcomes.

**This phase delivers:**
- Monte Carlo simulation engine
- Temporal state reconstruction (query game state at any moment)
- Win probability calculation
- Alternative outcome simulation
- 1,000-iteration Monte Carlo runs
- Simulation API and CLI tools

**Why simulation matters:**
- Answer "what-if" questions about historical games
- Calculate win probability at any moment
- Test betting strategies against historical data
- Validate ML models with backtest simulations

**Enhancement planned:**
- Advanced econometric models (ARIMA, VAR, state-space)
- Real-time betting strategy simulation
- Multi-game portfolio optimization

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | File |
|-----------|------|--------|------|------|
| **4.0** | Basic Simulation Engine | ✅ COMPLETE ✓ | 8-10h | Oct 23, 2025 |

---

## Sub-Phase 4.0: Basic Simulation Engine

**Status:** ✅ COMPLETE (October 3, 2025)

**What was completed:**
- Monte Carlo simulation framework
- Temporal state reconstruction queries
- Win probability calculator
- Simulation engine CLI
- 1,000-iteration test runs
- Documentation of simulation methodology

**Key Features:**
1. **Temporal State Queries:** Reconstruct game state at any timestamp
2. **Monte Carlo Simulation:** Run 1,000+ alternative scenarios
3. **Win Probability:** Calculate P(win) at any moment
4. **What-If Analysis:** Simulate alternative plays/decisions
5. **Backtesting:** Test strategies against historical data

**Simulation Accuracy:** ~63% (basic model, room for improvement with ML)

**See:** [Sub-Phase 4.0 Details](phase_4/4.0000_simulation_engine.md)

---

## Success Criteria

### Basic Implementation (Sub-Phase 4.0)
- [x] Monte Carlo framework operational
- [x] Temporal queries working (any timestamp)
- [x] Win probability calculator functional
- [x] 1,000-iteration simulations tested
- [x] CLI tools working
- [x] Documentation complete
- [x] Simulation accuracy baseline established (~63%)

### Advanced Enhancement (Planned)
- [ ] ARIMA time-series models integrated
- [ ] VAR (Vector Autoregression) models implemented
- [ ] State-space models for dynamic estimation
- [ ] Real-time betting strategy backtesting
- [ ] Simulation accuracy > 75%

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| EC2 (optional) | t3.medium for intensive sims | $30/month | Can run locally for free |
| Local computation | Free | $0 | Sufficient for development |
| **Total Phase Cost** | | **$0-30/month** | Depends on simulation volume |

**Cost Optimization:**
- Run simulations locally for development
- Use EC2 only for large batch simulations
- Consider Lambda for event-driven simulations

---

## Prerequisites

**Before starting Phase 4:**
- [x] Phase 0-3 complete (database with temporal data)
- [x] RDS accessible with cumulative stats
- [ ] Python simulation libraries (NumPy, SciPy)
- [ ] Understanding of Monte Carlo methods

---

## Key Architecture Decisions

**ADRs created in Phase 4:**
- Monte Carlo over deterministic simulation
- 1,000 iterations as default (balance of speed/accuracy)
- Temporal reconstruction using event_time indexes

**See:** `docs/adr/README.md`

---

## Advanced Simulation Framework (Planned Enhancement)

**Document:** `docs/ADVANCED_SIMULATION_FRAMEWORK.md`

**Econometric models planned:**
1. **ARIMA:** Time-series forecasting for momentum/streaks
2. **VAR:** Multi-variable regression for player interactions
3. **State-Space Models:** Dynamic parameter estimation
4. **Kalman Filters:** Real-time probability updates

**Expected accuracy boost:** 63% → 75-80%

**Timeline:** 20-30 hours additional work

---

## Multi-Sport Replication

**When adding a new sport (NFL, MLB, NHL, Soccer):**

This phase is **mostly sport-agnostic** - core Monte Carlo framework is reusable:

**Reusable components:**
- Monte Carlo simulation framework
- Temporal state reconstruction pattern
- Win probability calculation logic

**Sport-specific adaptations:**
- Scoring models (touchdowns vs points)
- Game flow parameters (quarters vs innings)
- Win probability curves (sport-specific)

**Example for NFL:**
```python
# Adapt scoring model
def simulate_nfl_drive(field_position, down, distance):
    # NFL-specific drive simulation
    return touchdown, field_goal, punt, turnover

# Win probability for NFL
def nfl_win_prob(score_diff, time_remaining, possessing_team):
    # NFL-specific win probability curve
    return probability
```

---

## Key Workflows

**For Sub-Phase 4.0:**
- Workflow #5: Task Execution
- Workflow #13: Testing Framework
- Workflow #2: Command Logging

---

## Troubleshooting

**Common issues:**

1. **Simulations too slow**
   - Solution: Reduce iteration count (1000 → 100 for testing)
   - Or: Parallelize simulations across cores
   - Or: Use NumPy vectorized operations

2. **Temporal queries slow**
   - Solution: Ensure event_time indexed
   - Use materialized views for common queries
   - Cache game states in memory

3. **Inaccurate win probabilities**
   - Solution: Calibrate against historical outcomes
   - Increase training data volume
   - Consider advanced ML models (Phase 5)

4. **Memory errors with large simulations**
   - Solution: Process in batches
   - Use generators instead of lists
   - Run on EC2 with more RAM

---

## Next Steps

**After Phase 4 complete:**
- ✅ Basic simulation engine operational
- → Proceed to [Phase 5: Machine Learning](PHASE_5_INDEX.md)
- → Optional: Implement advanced econometric models

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md)
**Previous Phase:** [Phase 3: Database Infrastructure](PHASE_3_INDEX.md)
**Next Phase:** [Phase 5: Machine Learning](PHASE_5_INDEX.md)
**Workflow Index:** [CLAUDE_WORKFLOW_ORDER.md](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related Documentation:**
- [Advanced Simulation Framework](../ADVANCED_SIMULATION_FRAMEWORK.md) (planned enhancement)
- [Temporal Query Guide](../TEMPORAL_QUERY_GUIDE.md)
- [Simulation Methodology](../SIMULATION_METHODOLOGY.md)

---

*For Claude Code: This phase has a single sub-phase (basic implementation complete). Advanced enhancements planned but not yet implemented.*

---

**Last Updated:** October 11, 2025
**Phase Owner:** Simulation Team
**Total Sub-Phases:** 1
**Status:** 100% complete (basic) | 0% complete (advanced enhancement)


## How Phase 4 Enables the Simulation Vision

This phase provides [data/infrastructure/capability] that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference
From this phase's outputs, we can:
- [Specific econometric technique enabled]
- [Example: PPP estimation using panel data regression]

### 2. Nonparametric Event Modeling
From this phase's data, we build:
- [Specific nonparametric technique enabled]
- [Example: Kernel density estimation for technical fouls]

### 3. Context-Adaptive Simulations
Using this phase's data, simulations can adapt to:
- [Game situation context]
- [Player/team specific factors]

**See [main README](../../README.md) for complete methodology.**
