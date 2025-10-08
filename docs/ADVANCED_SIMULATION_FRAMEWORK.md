# Advanced Multi-Level Simulation Framework

> **⚠️ LARGE FILE WARNING (903 lines)**
>
> **For Claude Code:** Only read this file when:
> - Implementing advanced simulation features
> - Working on Monte Carlo simulation system
> - Developing multi-level simulation architecture
>
> **DO NOT read at session start** - this file is a detailed implementation guide, not initialization documentation.

**Created:** October 6, 2025
**Purpose:** Econometric simulation architecture for NBA game forecasting
**Status:** Planning document - Post-infrastructure backbone completion

---

## 🎯 Vision Statement

**Goal:** Build sophisticated multi-level simulation models using econometric techniques (panel data, cluster equations, non-linear dynamics) to forecast **every statistic** about NBA games with high accuracy.

**Current state:** Simple Monte Carlo simulation (proof-of-concept)
**Target state:** Multi-level econometric simulation engine with hierarchical modeling

---

## 📊 Problem Statement

### Why Simple Monte Carlo Isn't Enough

**Current Monte Carlo limitations:**
- Assumes independence between events (not true in basketball)
- Linear probability distributions (real game dynamics are non-linear)
- No temporal dependencies (momentum, fatigue, strategy shifts)
- No player interactions (defensive matchups, chemistry)
- No contextual effects (home court, back-to-back games, playoff pressure)

**Example of what Monte Carlo misses:**
```python
# Simple Monte Carlo (current):
pts_scored = np.random.normal(team_avg_pts, team_std_pts)

# Reality (what we need to capture):
pts_scored = f(
    team_offensive_efficiency,
    opponent_defensive_rating,
    pace_of_game,
    player_matchups,
    fatigue_level,
    home_court_advantage,
    recent_performance_trend,
    strategic_adjustments,
    time_of_season,
    playoff_pressure,
    ... 50+ interacting variables
)
```

---

## 🏗️ Architecture Overview

### Multi-Level Simulation Hierarchy

```
Level 1: League-Wide Dynamics
  ├─ Season context (playoff race, tanking incentives)
  ├─ Conference/division effects
  └─ Schedule strength and fatigue patterns

Level 2: Team-Level Models
  ├─ Offensive system (pace, shot selection, ball movement)
  ├─ Defensive scheme (man-to-man, zone, switching)
  ├─ Roster composition (star load, depth, chemistry)
  └─ Coaching strategy (timeout usage, rotations)

Level 3: Player-Level Models
  ├─ Individual performance (shooting, playmaking, defense)
  ├─ Matchup dependencies (vs specific defenders)
  ├─ Usage patterns (high/low usage, role consistency)
  └─ Fatigue and injury effects

Level 4: Possession-Level Dynamics
  ├─ Shot quality (defender distance, shot clock, location)
  ├─ Turnover probability (defensive pressure, ball-handler skill)
  ├─ Rebounding outcomes (positioning, size advantages)
  └─ Free throw generation (driving frequency, foul calls)

Level 5: Micro-Events (Shot-by-Shot)
  ├─ Shot location selection (based on defense)
  ├─ Make/miss probability (contested vs open)
  ├─ Rebound outcomes (ORB vs DRB)
  └─ Transition opportunities
```

### Econometric Techniques to Apply

**1. Panel Data Models**
```
y_it = α_i + β*X_it + γ*Z_t + ε_it

Where:
- y_it = outcome for team i at time t
- α_i = team fixed effects (inherent quality)
- X_it = team-specific time-varying covariates
- Z_t = league-wide time effects (rule changes, era)
- ε_it = idiosyncratic error
```

**2. Cluster Equations (Simultaneous System)**
```
Offensive_Efficiency = f(Pace, Shot_Selection, Turnovers, ORB%)
Defensive_Efficiency = g(Opponent_Shot_Quality, DRB%, Steals, Blocks)
Pace = h(Team_Style, Opponent_Style, Game_Context)
Shot_Selection = j(Defense_Type, Player_Skills, Shot_Clock)

Solve simultaneously (3SLS or GMM)
```

**3. Non-Linear Dynamics**
```
# Momentum effects (non-linear)
P(next_basket) = logit(β0 + β1*recent_scoring_run + β2*run^2 + β3*run^3)

# Fatigue (exponential decay)
Performance_t = Performance_0 * exp(-λ * minutes_played)

# Interaction effects (multiplicative)
Shot_Quality = Shooter_Skill * (1 - Defender_Quality) * (1 + Open_Space_Factor)
```

**4. Hierarchical Bayesian Models**
```
# Player performance nested within team systems
Player_i ~ N(Team_Mean_j, Player_Variance)
Team_Mean_j ~ N(League_Mean, Team_Variance)
League_Mean ~ N(Prior_Mean, Prior_Variance)

# Allows borrowing strength across hierarchy
```

**5. Regime-Switching Models**
```
# Different dynamics in different game states
if score_margin > 15:
    use_garbage_time_model()
elif time_remaining < 2_minutes:
    use_clutch_model()
else:
    use_normal_game_model()
```

---

## 📋 Implementation Phases

### Phase 4.5: Advanced Simulation Architecture (NEW)

**Prerequisites:**
- ✅ Phase 0-6 complete (infrastructure backbone)
- ✅ 209-feature dataset available (multi-source integration)
- ✅ RDS with 6.7M plays + advanced stats
- ✅ SageMaker notebook operational

**Timeline:** 6-8 weeks
**Estimated cost:** +$20-30/month (compute for model estimation)

---

### Sub-Phase 4.5.1: Panel Data Model Estimation (Week 1-2)

**Objective:** Estimate team-level panel data models with fixed effects

**Implementation:**

**1. Data Preparation (3 hours)**
```python
# scripts/simulation/prepare_panel_data.py

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

class PanelDataPrep:
    """
    Prepare panel data structure for econometric estimation

    Panel structure:
    - Cross-sectional units: 30 NBA teams
    - Time dimension: Games (T = ~82 per season)
    - Balanced panel: Same number of observations per team
    """

    def create_panel(self, start_season: int, end_season: int):
        """
        Create panel dataset with team-game observations
        """
        # Query all games
        query = """
        SELECT
            g.game_id,
            g.game_date,
            g.season,
            g.home_team_abbr as team,
            g.home_score as points,
            g.away_score as opponent_points,
            -- Add all 209 features here
            pa.offensive_rating,
            pa.defensive_rating,
            pa.pace,
            pa.true_shooting_pct,
            pt.touches,
            pt.drives,
            pt.deflections
        FROM games g
        LEFT JOIN player_advanced_stats pa ON g.game_id = pa.game_id
        LEFT JOIN player_tracking_stats pt ON g.game_id = pt.game_id
        WHERE g.season BETWEEN %s AND %s
        """

        df = pd.read_sql(query, engine, params=[start_season, end_season])

        # Set multi-index (team, game)
        df = df.set_index(['team', 'game_id'])

        # Create lagged variables (t-1, t-5, t-10 game moving averages)
        for col in ['offensive_rating', 'defensive_rating', 'pace']:
            df[f'{col}_lag1'] = df.groupby('team')[col].shift(1)
            df[f'{col}_ma5'] = df.groupby('team')[col].rolling(5).mean()

        # Add time-invariant team characteristics
        df['team_quality'] = df.groupby('team')['points'].transform('mean')

        return df
```

**2. Fixed Effects Estimation (4 hours)**
```python
# scripts/simulation/estimate_panel_models.py

from linearmodels.panel import PanelOLS, RandomEffects
import statsmodels.api as sm

class PanelModelEstimator:
    """
    Estimate panel data models for team performance
    """

    def estimate_offensive_efficiency(self, panel_df):
        """
        Model: OffRtg_it = α_i + β*Pace_it + γ*TS%_it + δ*TOV%_it + ε_it

        α_i = team fixed effects (captures inherent offensive talent)
        """
        # Entity (team) fixed effects
        model = PanelOLS(
            dependent=panel_df['offensive_rating'],
            exog=panel_df[['pace', 'true_shooting_pct', 'turnover_pct',
                          'offensive_rebound_pct', 'free_throw_rate']],
            entity_effects=True,  # Team fixed effects
            time_effects=True     # Season fixed effects
        )

        results = model.fit(cov_type='clustered', cluster_entity=True)

        return results

    def estimate_interactive_model(self, panel_df):
        """
        Model with interaction effects:
        Points_it = α_i + β1*OffRtg + β2*DefRtg_opponent +
                    β3*(OffRtg × Pace) + β4*(Home) + ε_it
        """
        # Create interaction term
        panel_df['offrtg_pace'] = panel_df['offensive_rating'] * panel_df['pace']

        model = PanelOLS(
            dependent=panel_df['points'],
            exog=panel_df[['offensive_rating', 'opponent_defensive_rating',
                          'offrtg_pace', 'home_indicator']],
            entity_effects=True
        )

        return model.fit(cov_type='robust')
```

**3. Store Estimated Parameters (1 hour)**
```python
# Store model coefficients for simulation
coefficients = {
    'team_fixed_effects': results.estimated_effects,
    'pace_coef': results.params['pace'],
    'ts_pct_coef': results.params['true_shooting_pct'],
    # ... all coefficients
}

# Save to database
import json
with open('data/panel_model_params.json', 'w') as f:
    json.dump(coefficients, f)
```

**Validation:**
- [ ] R-squared ≥ 0.80 (within-team variation)
- [ ] All coefficients statistically significant (p < 0.05)
- [ ] Hausman test confirms fixed effects preferred over random effects
- [ ] Residuals show no autocorrelation (Durbin-Watson ~ 2)

---

### Sub-Phase 4.5.2: Cluster Equation System (Week 3-4)

**Objective:** Estimate simultaneous equation system for interconnected stats

**Implementation:**

**1. Define System of Equations (2 hours)**
```python
# scripts/simulation/cluster_equations.py

from statsmodels.sandbox.regression.gmm import IV2SLS
from linearmodels.system import SUR, IV3SLS

class ClusterEquationSystem:
    """
    Simultaneous equation system:

    Equation 1 (Offensive): OffRtg = f(Pace, Shot_Quality, Turnovers)
    Equation 2 (Defensive): DefRtg = g(Opp_Shot_Quality, Rebounding, Steals)
    Equation 3 (Pace): Pace = h(Team_Style, Opp_Style, Score_Margin)
    Equation 4 (Shot_Quality): ShotQual = j(Spacing, Ball_Movement, Defense)

    All equations estimated jointly (3SLS or GMM)
    """

    def define_equations(self):
        """
        Define structural equations with endogeneity
        """
        equations = {
            'offensive_rating': {
                'dependent': 'offensive_rating',
                'exog': ['pace', 'true_shooting_pct', 'turnover_pct'],
                'endog': ['shot_quality'],  # Endogenous
                'instruments': ['spacing_rating', 'ball_movement_index']
            },
            'defensive_rating': {
                'dependent': 'defensive_rating',
                'exog': ['opponent_pace', 'defensive_rebound_pct', 'steal_pct'],
                'endog': ['opponent_shot_quality'],
                'instruments': ['defensive_scheme_index', 'rim_protection']
            },
            'pace': {
                'dependent': 'pace',
                'exog': ['team_pace_preference', 'opponent_pace_preference'],
                'endog': ['score_margin'],
                'instruments': ['starting_lineup_speed', 'bench_speed']
            }
        }
        return equations

    def estimate_3sls(self, data, equations):
        """
        Three-Stage Least Squares estimation
        """
        # Stage 1: Estimate reduced form for endogenous variables
        # Stage 2: Predict endogenous variables
        # Stage 3: Estimate structural equations with GLS

        model = IV3SLS.from_formula(
            equations,
            data=data
        )

        results = model.fit()
        return results
```

**2. Solve System Simultaneously (3 hours)**
```python
def solve_system(self, params, exog_values):
    """
    Given exogenous variables, solve for equilibrium values

    System:
    OffRtg = β0 + β1*Pace + β2*ShotQual + ε1
    Pace = γ0 + γ1*OffRtg + γ2*DefRtg + ε2
    ShotQual = δ0 + δ1*OffRtg + δ2*Defense + ε3

    Solve for (OffRtg, Pace, ShotQual) given Defense (exogenous)
    """
    from scipy.optimize import fsolve

    def equations(vars):
        offrtg, pace, shot_qual = vars

        eq1 = offrtg - (params['β0'] + params['β1']*pace + params['β2']*shot_qual)
        eq2 = pace - (params['γ0'] + params['γ1']*offrtg + params['γ2']*exog_values['defrtg'])
        eq3 = shot_qual - (params['δ0'] + params['δ1']*offrtg + params['δ2']*exog_values['defense'])

        return [eq1, eq2, eq3]

    # Solve system
    initial_guess = [110, 100, 0.55]  # (OffRtg, Pace, ShotQual)
    solution = fsolve(equations, initial_guess)

    return {
        'offensive_rating': solution[0],
        'pace': solution[1],
        'shot_quality': solution[2]
    }
```

**Validation:**
- [ ] System identification verified (order/rank conditions)
- [ ] Overidentification test (Sargan test p > 0.05)
- [ ] Instrument relevance (F-stat > 10)
- [ ] Convergence of iterative solver (< 50 iterations)

---

### Sub-Phase 4.5.3: Non-Linear Dynamics (Week 5)

**Objective:** Capture non-linearities (momentum, fatigue, regime-switching)

**Implementation:**

**1. Momentum Effects (Non-Linear) (2 hours)**
```python
# scripts/simulation/non_linear_models.py

from sklearn.preprocessing import PolynomialFeatures
from statsmodels.discrete.discrete_model import Logit

class NonLinearDynamics:
    """
    Capture non-linear game dynamics
    """

    def estimate_momentum_model(self, data):
        """
        Momentum effect on next basket probability

        Model: P(next_basket) = logit(β0 + β1*run + β2*run^2 + β3*run^3)

        run = point differential in last 5 minutes
        """
        # Create polynomial features
        poly = PolynomialFeatures(degree=3)
        X_poly = poly.fit_transform(data[['scoring_run']])

        # Logistic regression
        model = Logit(data['next_basket'], X_poly)
        results = model.fit()

        return results

    def estimate_fatigue_curve(self, data):
        """
        Fatigue effect: Performance = f(minutes) with exponential decay

        Model: Performance_t = β0 * exp(-λ * minutes_played)
        """
        from scipy.optimize import curve_fit

        def fatigue_func(minutes, beta0, lambda_):
            return beta0 * np.exp(-lambda_ * minutes)

        popt, pcov = curve_fit(
            fatigue_func,
            data['minutes_played'],
            data['performance_index']
        )

        return {'beta0': popt[0], 'lambda': popt[1]}
```

**2. Regime-Switching Models (3 hours)**
```python
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

class RegimeSwitchingModel:
    """
    Different dynamics in different game states
    """

    def estimate_markov_switching(self, data):
        """
        Markov-switching model with 3 regimes:
        - Regime 0: Normal play
        - Regime 1: Clutch time (last 2 minutes, close game)
        - Regime 2: Garbage time (blowout)
        """
        model = MarkovRegression(
            endog=data['points_scored'],
            k_regimes=3,
            exog=data[['offensive_rating', 'pace', 'time_remaining']],
            switching_variance=True
        )

        results = model.fit()

        return results

    def classify_regime(self, score_margin, time_remaining):
        """
        Determine which regime we're in
        """
        if time_remaining < 120 and abs(score_margin) < 10:
            return 'clutch'  # Regime 1
        elif abs(score_margin) > 20:
            return 'garbage'  # Regime 2
        else:
            return 'normal'   # Regime 0
```

**Validation:**
- [ ] Momentum polynomial terms significant (p < 0.05)
- [ ] Fatigue decay rate λ in realistic range (0.01-0.05)
- [ ] Regime transitions follow expected patterns
- [ ] Out-of-sample prediction improves vs linear model

---

### Sub-Phase 4.5.4: Hierarchical Bayesian Models (Week 6)

**Objective:** Multi-level player/team/league structure with partial pooling

**Implementation:**

**1. Define Hierarchical Structure (2 hours)**
```python
# scripts/simulation/hierarchical_models.py

import pymc as pm
import arviz as az

class HierarchicalBayesianModel:
    """
    Hierarchical model: Players nested within teams within league
    """

    def build_player_performance_model(self, data):
        """
        Three-level hierarchy:
        Level 1 (League): Overall NBA scoring distribution
        Level 2 (Team): Team offensive system effects
        Level 3 (Player): Individual player skill

        Player_Points_ijk ~ N(μ_ijk, σ_player)
        μ_ijk = α + β_team[j] + γ_player[k]
        β_team ~ N(0, σ_team)
        γ_player ~ N(Team_Mean[j], σ_within_team)
        """
        with pm.Model() as model:
            # Hyperpriors (league level)
            league_mean = pm.Normal('league_mean', mu=15, sigma=5)

            # Team-level random effects
            team_sigma = pm.HalfNormal('team_sigma', sigma=5)
            team_effects = pm.Normal('team_effects', mu=0, sigma=team_sigma,
                                     shape=30)  # 30 teams

            # Player-level random effects (nested within team)
            player_sigma = pm.HalfNormal('player_sigma', sigma=3)
            player_effects = pm.Normal('player_effects',
                                       mu=team_effects[data['team_id']],
                                       sigma=player_sigma,
                                       shape=len(data))

            # Likelihood
            mu = league_mean + player_effects
            points = pm.Normal('points', mu=mu, sigma=2, observed=data['points'])

            # Sample posterior
            trace = pm.sample(2000, tune=1000, return_inferencedata=True)

        return trace
```

**2. Partial Pooling Benefits (1 hour)**
```python
def demonstrate_partial_pooling(self, trace):
    """
    Show how hierarchical model borrows strength

    - Players with few games: Pull toward team mean
    - Players with many games: Stay close to individual mean
    - Teams with weak players: Pull toward league mean
    """
    # Extract posterior means
    player_means = trace.posterior['player_effects'].mean(dim=['chain', 'draw'])
    team_means = trace.posterior['team_effects'].mean(dim=['chain', 'draw'])

    # Compare with no-pooling (individual estimates)
    individual_means = data.groupby('player_id')['points'].mean()

    # Shrinkage factor (how much pulled toward group mean)
    shrinkage = 1 - (player_means.var() / individual_means.var())

    print(f"Shrinkage: {shrinkage:.2%}")  # Typically 20-40%
```

**Validation:**
- [ ] MCMC convergence (Rhat < 1.01)
- [ ] Effective sample size > 1000
- [ ] Posterior predictive checks pass (observed data in 95% CI)
- [ ] Hierarchical structure improves prediction vs pooled model

---

### Sub-Phase 4.5.5: Integrated Simulation Engine (Week 7-8)

**Objective:** Combine all models into unified simulation framework

**Implementation:**

**1. Master Simulation Class (4 hours)**
```python
# scripts/simulation/integrated_simulator.py

class AdvancedGameSimulator:
    """
    Multi-level econometric simulation engine

    Combines:
    - Panel data models (team effects)
    - Cluster equations (simultaneous dynamics)
    - Non-linear models (momentum, fatigue)
    - Hierarchical Bayes (player performance)
    - Regime-switching (game states)
    """

    def __init__(self):
        self.panel_model = PanelModelEstimator()
        self.cluster_system = ClusterEquationSystem()
        self.nonlinear_model = NonLinearDynamics()
        self.hierarchical_model = HierarchicalBayesianModel()
        self.regime_model = RegimeSwitchingModel()

    def simulate_game(self, home_team: str, away_team: str,
                     n_simulations: int = 10000):
        """
        Simulate full game using multi-level approach

        Steps:
        1. Estimate team-level expected performance (panel model)
        2. Solve for equilibrium pace/efficiency (cluster equations)
        3. Simulate possession-by-possession with momentum (non-linear)
        4. Draw player performances (hierarchical Bayes)
        5. Switch regimes as game state changes (Markov switching)
        """
        results = []

        for sim in range(n_simulations):
            # Level 1: Team-level expectations
            home_offrtg = self.panel_model.predict(home_team, 'offensive')
            away_defrtg = self.panel_model.predict(away_team, 'defensive')

            # Level 2: Solve cluster system
            equilibrium = self.cluster_system.solve_system({
                'home_offrtg': home_offrtg,
                'away_defrtg': away_defrtg
            })

            pace = equilibrium['pace']
            possessions = int(pace * 48 / 48)  # ~100 possessions

            # Level 3: Possession-by-possession simulation
            home_score = 0
            away_score = 0
            momentum = 0

            for poss in range(possessions):
                # Determine regime
                time_left = 48 - (poss / possessions * 48)
                margin = home_score - away_score
                regime = self.regime_model.classify_regime(margin, time_left)

                # Possession outcome (with momentum effect)
                if poss % 2 == 0:  # Home possession
                    # Level 4: Player performance draw
                    shooter_id = self.select_shooter(home_team, poss)
                    shot_prob = self.hierarchical_model.predict_make_prob(
                        shooter_id, momentum, regime
                    )

                    # Non-linear momentum effect
                    shot_prob_adj = self.nonlinear_model.apply_momentum(
                        shot_prob, momentum
                    )

                    # Outcome
                    if np.random.random() < shot_prob_adj:
                        points = np.random.choice([2, 3], p=[0.6, 0.4])
                        home_score += points
                        momentum += points  # Positive momentum
                    else:
                        momentum -= 1  # Negative momentum
                else:  # Away possession
                    # Similar for away team
                    pass

            results.append({
                'home_score': home_score,
                'away_score': away_score,
                'regime_switches': count_regime_switches(),
                'max_momentum': max_momentum
            })

        return pd.DataFrame(results)
```

**2. Validation Framework (2 hours)**
```python
def validate_simulations(self, simulated_games, actual_games):
    """
    Compare simulated vs actual distributions
    """
    # 1. Score accuracy
    sim_scores = simulated_games['home_score'].mean()
    actual_scores = actual_games['home_score'].mean()
    score_mae = abs(sim_scores - actual_scores)

    # 2. Variance calibration
    sim_variance = simulated_games['home_score'].var()
    actual_variance = actual_games['home_score'].var()
    variance_ratio = sim_variance / actual_variance

    # 3. Distribution fit (Kolmogorov-Smirnov test)
    from scipy.stats import ks_2samp
    ks_stat, ks_pvalue = ks_2samp(
        simulated_games['home_score'],
        actual_games['home_score']
    )

    # 4. Extreme event probability
    sim_blowouts = (simulated_games['margin'] > 20).mean()
    actual_blowouts = (actual_games['margin'] > 20).mean()

    print(f"Score MAE: {score_mae:.2f}")
    print(f"Variance ratio: {variance_ratio:.2f} (target: 1.0)")
    print(f"KS test p-value: {ks_pvalue:.3f} (want > 0.05)")
    print(f"Blowout rate: Sim {sim_blowouts:.1%} vs Actual {actual_blowouts:.1%}")
```

**Validation:**
- [ ] Score MAE < 5 points
- [ ] Variance ratio 0.9-1.1
- [ ] KS test p-value > 0.05 (distributions match)
- [ ] Extreme event rates match (within 2%)

---

## 📊 Forecasting Every Statistic

### Comprehensive Statistic Forecasting

**Once integrated simulation is working, extend to forecast ALL stats:**

```python
class ComprehensiveStatForecaster:
    """
    Forecast every possible game/player statistic
    """

    def forecast_game_stats(self, home_team, away_team):
        """
        Forecast all 209 features + derived stats
        """
        sims = self.simulator.simulate_game(home_team, away_team, n=10000)

        forecasts = {
            # Scoring
            'total_points': sims['total_points'].mean(),
            'total_points_ci': np.percentile(sims['total_points'], [2.5, 97.5]),

            # Pace
            'pace': sims['pace'].mean(),
            'pace_ci': np.percentile(sims['pace'], [2.5, 97.5]),

            # Efficiency
            'offensive_rating': sims['offensive_rating'].mean(),
            'defensive_rating': sims['defensive_rating'].mean(),

            # Advanced
            'four_factors': self.calculate_four_factors(sims),
            'player_matchups': self.simulate_matchups(sims),

            # All 209 features
            **{f: sims[f].mean() for f in self.features}
        }

        return forecasts

    def create_forecast_distribution(self, forecasts):
        """
        Full probability distribution for each stat
        """
        import matplotlib.pyplot as plt

        for stat in ['points', 'rebounds', 'assists', 'turnovers']:
            plt.hist(forecasts[stat], bins=50, density=True)
            plt.title(f"{stat} distribution")
            plt.xlabel(stat)
            plt.ylabel("Probability")
            plt.show()
```

---

## 🚀 Implementation Roadmap

### Timeline Summary

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1-2 | Panel data models | Team fixed effects estimated |
| 3-4 | Cluster equations | Simultaneous system solved |
| 5 | Non-linear dynamics | Momentum/fatigue/regime models |
| 6 | Hierarchical Bayes | Player performance distributions |
| 7-8 | Integration | Unified simulation engine |

**Total: 6-8 weeks**

### Success Criteria

**Model Performance:**
- [ ] Score prediction MAE < 5 points (vs current Monte Carlo ~12)
- [ ] Win probability accuracy > 75% (vs current ~63%)
- [ ] Variance calibration ratio 0.9-1.1
- [ ] All 209 statistics forecasted with confidence intervals

**Technical Validation:**
- [ ] Panel model R² > 0.80
- [ ] Cluster system convergence < 50 iterations
- [ ] MCMC diagnostics pass (Rhat < 1.01)
- [ ] Out-of-sample validation RMSE < training RMSE * 1.1

---

## 💰 Cost & Resource Requirements

### Compute Requirements

**Model Estimation (One-time):**
- Panel models: ~2 hours on laptop (free)
- Cluster equations: ~4 hours on laptop (free)
- Bayesian MCMC: ~8 hours on EC2 c5.2xlarge ($0.34/hr = $2.72)
- **Total one-time: ~$3**

**Ongoing Simulation:**
- 10,000 sims/game: ~30 seconds on EC2 t3.medium
- Daily forecasts (15 games): ~7.5 minutes = $0.01/day
- **Monthly: ~$0.30**

### Software Requirements

```bash
# Additional Python packages
pip install linearmodels  # Panel data models
pip install pymc          # Bayesian inference
pip install arviz         # Bayesian diagnostics
pip install statsmodels   # Time series, regime-switching
pip install scikit-learn  # Polynomial features
```

**Total additional cost: ~$5-10/month**

---

## 📚 References & Literature

### Econometric Methods
- Wooldridge, J. (2010). *Econometric Analysis of Cross Section and Panel Data*
- Greene, W. (2018). *Econometric Analysis* (8th ed.)
- Cameron & Trivedi (2005). *Microeconometrics: Methods and Applications*

### Sports Analytics
- Albert, J. & Koning, R. (2007). *Statistical Thinking in Sports*
- Carlin, B. et al. (2005). "Hierarchical Bayesian NBA Prediction"
- Deshpande & Jensen (2016). "Estimating an NBA player's impact on his team's chances of winning"

### Non-Linear Dynamics
- Hamilton, J. (1994). *Time Series Analysis* (Regime-switching models)
- Tong, H. (1990). *Non-linear Time Series* (Threshold models)

---

## 🎯 Next Steps

**Immediate (Next Session):**
1. Review this framework with user
2. Confirm priorities (which models to build first?)
3. Set up additional Python packages
4. Begin Sub-Phase 4.5.1 (Panel data preparation)

**This Week:**
1. Prepare panel data structure (team-game observations)
2. Estimate first panel model (offensive efficiency)
3. Validate model fit (R², residual diagnostics)

**This Month:**
1. Complete all 5 sub-phases
2. Build integrated simulation engine
3. Validate against 2024-25 season (out-of-sample)
4. Deploy to EC2 for production forecasting

---

*Last updated: October 6, 2025*
*From simple Monte Carlo to sophisticated econometric simulation*
