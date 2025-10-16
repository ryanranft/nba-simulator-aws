# Phase 7: Betting Odds Integration

**Status:** ⏸️ PENDING (optional future enhancement)
**Priority:** LOW (optional)
**Prerequisites:** Phase 0-6 complete
**Estimated Time:** 12-15 hours
**Cost Impact:** $0-30/month (odds API fees)
**Started:** Not yet started
**Completion:** Future

---

## Overview

Integrate historical betting odds data and build betting strategy backtesting system. This phase adds sports betting analytics capabilities, allowing users to test betting strategies against historical odds and outcomes.

**This phase delivers:**
- Historical odds data integration (The Odds API or similar)
- Betting strategy framework
- Backtest engine for historical odds
- Kelly criterion calculator
- Portfolio optimization for multi-game bets
- ROI tracking and analysis

**Why betting odds integration matters:**
- Test betting strategies against historical data
- Calculate edge vs bookmaker odds
- Optimize bet sizing (Kelly criterion)
- Identify value betting opportunities
- Track long-term ROI performance

**⚠️ Note:** This phase is **entirely optional** and focused on sports betting analytics research.

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | File |
|-----------|------|--------|------|------|
| **7.0** | Betting Odds Integration | ⏸️ PENDING | 12-15h | [7.0_betting_odds_integration.md](phase_7/7.0_betting_odds_integration.md) |

---

## Sub-Phase 7.0: Betting Odds Integration

**Status:** ⏸️ PENDING (not yet started)

**What this sub-phase will include:**
- Historical odds data source selection
- Odds data ingestion pipeline
- Betting strategy framework
- Backtest engine implementation
- Kelly criterion optimizer
- Portfolio optimization logic
- ROI tracking dashboard

**Odds Data Sources:**
1. **The Odds API** - $0-30/mo (500-10K requests/mo)
2. **SportsOddsHistory.com** - Historical archive (scraping)
3. **Action Network** - API access (varies)
4. **Bookmaker archives** - Various sources

**Betting Strategies to Implement:**
- Flat betting (constant stake)
- Proportional betting (% of bankroll)
- Kelly criterion (optimal sizing)
- Modified Kelly (fractional Kelly)
- Arbitrage detection

**See:** [Sub-Phase 7.0 Details](phase_7/7.0_betting_odds_integration.md)

---

## Success Criteria

### Sub-Phase 7.0 (Betting Odds Integration)
- [ ] Historical odds data source chosen
- [ ] Odds data ingestion pipeline operational
- [ ] Odds database schema created
- [ ] Betting strategy framework implemented
- [ ] Backtest engine functional
- [ ] Kelly criterion calculator working
- [ ] Portfolio optimization logic implemented
- [ ] ROI tracking dashboard operational
- [ ] Strategy comparison analysis complete

---

## Cost Breakdown

### Odds Data Sources
| Source | Cost | Coverage | Notes |
|--------|------|----------|-------|
| **The Odds API** | $0-30/mo | 2010-present | 500 requests/mo free, $0.006/request after |
| **SportsOddsHistory** | $0 | 2005-present | Scraping required, may violate TOS |
| **Action Network** | Varies | 2015-present | API access varies by plan |
| **Manual collection** | $0 | Limited | Time-intensive |

### Infrastructure Costs
| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| S3 odds storage | ~1GB | ~$0.02/mo | Minimal |
| RDS (existing) | No change | $0 | Use existing database |
| Lambda (odds refresh) | Daily runs | ~$0.50/mo | Automated updates |
| **Total Phase Cost** | | **$0-30/month** | Depends on odds API choice |

**Cost Optimization:**
- Use free tier of The Odds API (500 requests/mo)
- Collect only essential odds types (moneyline, spread, total)
- Archive old odds to S3 Glacier

---

## Prerequisites

**Before starting Phase 7:**
- [x] Phase 0-6 complete (core system operational)
- [ ] Odds API key obtained (The Odds API or alternative)
- [ ] User has chosen betting strategy focus
- [ ] Understanding of betting mathematics (Kelly criterion, expected value)

**Note:** This phase is entirely optional - core project is complete without it.

---

## Key Architecture Decisions

**ADRs to create in Phase 7:**
- Odds API selection rationale
- Betting strategy framework design
- Backtest methodology

**See:** `docs/adr/README.md` (will be created during implementation)

---

## Betting Analytics Features

### 1. Historical Odds Integration
- **Moneyline odds:** Team win probabilities
- **Spread betting:** Point spread odds
- **Over/Under:** Total points odds
- **Player props:** Individual player performance bets

### 2. Betting Strategies
- **Flat betting:** Fixed stake per bet
- **Proportional:** % of bankroll
- **Kelly criterion:** Mathematically optimal sizing
- **Modified Kelly:** Fractional Kelly (risk management)

### 3. Backtesting
- **Historical simulation:** Test strategy on past games
- **ROI calculation:** Return on investment tracking
- **Drawdown analysis:** Maximum loss periods
- **Sharpe ratio:** Risk-adjusted returns

### 4. Value Betting
- **Edge calculation:** Model prob - bookmaker prob
- **Expected value:** EV = (prob × payout) - (1-prob × stake)
- **Value threshold:** Only bet when EV > threshold
- **Confidence intervals:** Uncertainty quantification

### 5. Portfolio Optimization
- **Multi-game betting:** Optimize across multiple games
- **Correlation analysis:** Account for related outcomes
- **Risk management:** Limit exposure per day/week
- **Bankroll management:** Kelly-optimal allocations

---

## Multi-Sport Replication

**When adding a new sport (NFL, MLB, NHL, Soccer):**

This phase is **mostly sport-agnostic** - betting framework is reusable:

**Reusable components:**
- Odds data ingestion pipeline
- Betting strategy framework
- Backtest engine
- Kelly criterion calculator
- ROI tracking

**Sport-specific adaptations:**
- Odds types (sport-specific markets)
- Betting rules (pushes, ties, overtimes)
- Correlation models (sport-specific dependencies)

**Example for NFL:**
```python
# NFL-specific odds types
odds_types = [
    'moneyline',  # Team win
    'spread',     # Point spread
    'total',      # Over/under total points
    'first_half', # First half markets
    'player_props' # Player performance props
]
```

---

## Key Workflows

**For Sub-Phase 7.0:**
- Workflow #18: Cost Management
- Workflow #5: Task Execution
- Workflow #13: Testing Framework

---

## Responsible Gambling Notice

**⚠️ IMPORTANT:** This phase is for **educational and research purposes only**.

- This system is NOT gambling advice
- Past performance does not guarantee future results
- Betting involves risk of loss
- Only bet what you can afford to lose
- Check local gambling laws and regulations

**Purpose of this phase:**
- Sports analytics research
- Mathematical modeling education
- Strategy testing and validation
- Historical data analysis

---

## Troubleshooting

**Common issues:**

1. **Odds API rate limiting**
   - Solution: Cache odds data locally
   - Reduce API call frequency
   - Upgrade to paid tier if needed

2. **Backtest shows positive ROI but real-world doesn't**
   - Solution: Check for lookahead bias
   - Account for juice/vig in calculations
   - Use out-of-sample testing

3. **Kelly criterion suggests huge bets**
   - Solution: Use fractional Kelly (0.25x or 0.5x)
   - Set max bet size limits
   - Verify edge calculation accuracy

4. **Missing historical odds data**
   - Solution: Accept incomplete coverage
   - Focus on recent years (2015+)
   - Consider commercial odds archives

---

## Next Steps

**After Phase 7 complete:**
- ✅ Betting analytics operational
- → System fully complete (all 7 phases done)
- → Begin Phase 0 expansion (Basketball Reference)
- → Or: Apply system to new sport (NFL, MLB, etc.)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md)
**Previous Phase:** [Phase 6: Optional Enhancements](PHASE_6_INDEX.md)
**Next Phase:** None (final phase)
**Workflow Index:** [CLAUDE_WORKFLOW_ORDER.md](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related Documentation:**
- [Betting Analytics Guide](../BETTING_ANALYTICS_GUIDE.md) (to be created)
- [Kelly Criterion Calculator](../KELLY_CRITERION.md) (to be created)
- [Backtest Methodology](../BACKTEST_METHODOLOGY.md) (to be created)

---

*For Claude Code: This phase is entirely optional. Core project (Phases 0-6) is complete without it. Only implement if user specifically requests betting analytics.*

---

**Last Updated:** October 11, 2025
**Phase Owner:** Analytics Team
**Total Sub-Phases:** 1
**Status:** 0% complete (pending - optional enhancement)


## Enhancement: Enhance distributed tracing coverage

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.599336
**Category:** important

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## New Item: Implement feature importance tracking

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.599664
**Category:** important
**Priority:** Important

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## Enhancement: Enhance distributed tracing coverage

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.918143
**Category:** important

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## New Item: Implement feature importance tracking

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.918338
**Category:** important
**Priority:** Important

### Description
No additional description provided.

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---
