# NBA Betting Analysis Scripts

**Created:** October 28, 2025
**Purpose:** Comprehensive betting analysis using ML predictions and Monte Carlo simulations

---

## Scripts Overview

### 1. `fetch_todays_odds.py`
Fetch all betting odds for a specific date from RDS PostgreSQL.

**Usage:**
```bash
python fetch_todays_odds.py --date 2025-10-28
```

**Output:** JSON file with games, markets, and odds from all bookmakers

---

### 2. `fetch_simulation_features.py`
Query team and player statistics to build feature matrices.

**Usage:**
```bash
python fetch_simulation_features.py --games-file data/betting/odds_2025-10-28.json
```

**Output:** JSON file with historical stats and derived features

---

### 3. `generate_ml_predictions.py`
Generate ML predictions with confidence intervals.

**Usage:**
```bash
python generate_ml_predictions.py --features-file data/betting/features_odds_2025-10-28.json
```

**Output:** JSON file with win probabilities, predicted scores, spreads, totals

---

### 4. `run_game_simulations.py`
Run possession-by-possession Monte Carlo simulations.

**Usage:**
```bash
python run_game_simulations.py --predictions-file data/betting/predictions_odds_2025-10-28.json --n-simulations 10000
```

**Output:** JSON file with simulation distributions for all betting markets

---

### 5. `simulate_player_props.py`
Simulate individual player performance for prop bets.

**Usage:**
```bash
python simulate_player_props.py --simulations-file data/betting/simulations_odds_2025-10-28.json --n-simulations 10000
```

**Output:** JSON file with player prop probabilities

---

### 6. `calculate_betting_edges.py`
Calculate expected value and Kelly Criterion for all markets.

**Usage:**
```bash
python calculate_betting_edges.py --props-file data/betting/props_odds_2025-10-28.json --min-edge 0.02
```

**Output:** JSON file with ranked betting opportunities

---

### 7. `generate_betting_report.py`
Generate comprehensive reports in multiple formats.

**Usage:**
```bash
python generate_betting_report.py --edges-file data/betting/edges_odds_2025-10-28.json
```

**Output:** Markdown, CSV, and JSON reports

---

### 8. `run_full_betting_analysis.py` ⭐
Master orchestrator - runs entire pipeline.

**Usage:**
```bash
# Standard analysis
python run_full_betting_analysis.py --date 2025-10-28

# Quick test (1K simulations)
python run_full_betting_analysis.py --date 2025-10-28 --n-simulations 1000

# High-confidence only
python run_full_betting_analysis.py --date 2025-10-28 --min-edge 0.05
```

**Output:** All intermediate files + comprehensive reports

---

## Quick Start

**One-line execution:**
```bash
python run_full_betting_analysis.py --date 2025-10-28
```

View results:
```bash
open reports/betting/betting_recommendations_2025-10-28.md
```

---

## Dependencies

- `psycopg2-binary` - PostgreSQL connection
- `numpy` - Numerical computations
- `scipy` - Statistical distributions
- `pandas` - Data manipulation
- `python-dotenv` - Environment variables

Install:
```bash
pip install psycopg2-binary numpy scipy pandas python-dotenv
```

---

## Architecture

```
Master Orchestrator
        ↓
1. Fetch Odds → 2. Features → 3. ML Predictions
                                      ↓
4. Monte Carlo Simulations ← ← ← ← ←
        ↓
5. Player Props → 6. Calculate Edges → 7. Reports
```

---

## Configuration

**Database credentials:** `/Users/ryanranft/nba-sim-credentials.env`

Required environment variables:
- `DB_HOST` - RDS endpoint
- `DB_NAME` - Database name
- `DB_USER` - Username
- `DB_PASSWORD` - Password
- `DB_PORT` - Port (default: 5432)

---

## Testing

Run unit tests:
```bash
pytest ../../tests/betting/test_betting_analysis.py -v
```

---

## Output Structure

```
data/betting/
├── odds_YYYY-MM-DD.json           # Raw odds data
├── features_odds_YYYY-MM-DD.json  # Feature matrix
├── predictions_odds_YYYY-MM-DD.json # ML predictions
├── simulations_odds_YYYY-MM-DD.json # Monte Carlo results
├── props_odds_YYYY-MM-DD.json     # Player props
└── edges_odds_YYYY-MM-DD.json     # Betting edges

reports/betting/
├── betting_recommendations_YYYY-MM-DD.md # Human-readable report
├── betting_edges_YYYY-MM-DD.csv          # Spreadsheet format
└── betting_analysis_YYYY-MM-DD.json      # Complete data
```

---

## Performance

**Pipeline runtime (12 games, 10K simulations):** ~10-12 minutes

**Breakdown:**
- Fetch odds: 10s
- Fetch features: 60s
- ML predictions: 15s
- Monte Carlo: 5-8min
- Player props: 3min
- Edges: 10s
- Reports: 5s

---

## Edge Calculation

### Expected Value (EV)
```
EV = (Model_Prob × Payout) - 1
```

### Kelly Criterion
```
Kelly% = (bp - q) / b
where:
  b = decimal odds - 1
  p = win probability
  q = 1 - p
```

**Conservative approach:** Use 1/4 Kelly for lower variance

---

## Confidence Levels

- **HIGH (⭐⭐⭐):** Edge ≥ 5%, Low variance
- **MEDIUM (⭐⭐):** Edge ≥ 3%, Moderate variance
- **LOW (⭐):** Edge ≥ 2%, High variance

---

## Troubleshooting

### No games found
- Check if odds-api scraper has run
- Verify date format (YYYY-MM-DD)
- Confirm database connection

### Simulation errors
- Ensure numpy/scipy installed
- Check feature data completeness
- Verify n_simulations > 0

### Report generation fails
- Check output directory permissions
- Verify edges file exists
- Ensure sufficient disk space

---

## Related Documentation

- **Setup Guide:** `/BETTING_ANALYSIS_SETUP.md`
- **Odds API Integration:** `docs/phases/phase_0/0.0007_odds_api_data/README.md`
- **Project Plan:** `/game-predictions-betting.plan.md`

---

**Branch:** `feature/game-predictions-2025-10-28`
**Status:** Production Ready
**Last Updated:** October 28, 2025

