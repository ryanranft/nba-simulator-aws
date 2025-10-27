# NBA Temporal Panel Data System

**High-frequency panel data platform for millisecond-precision NBA historical analysis with econometric causal inference, nonparametric event modeling, cumulative advantage dynamics, and advanced machine learning**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![Phases](https://img.shields.io/badge/Core%20Phases-6%2F6%20Complete-brightgreen)]()
[![Temporal](https://img.shields.io/badge/Temporal-Enhanced-purple)]()
[![Precision](https://img.shields.io/badge/Precision-Millisecond-orange)]()
[![Tests](https://github.com/ryanranft/nba-simulator-aws/actions/workflows/test.yml/badge.svg)](https://github.com/ryanranft/nba-simulator-aws/actions/workflows/test.yml)
[![Security](https://github.com/ryanranft/nba-simulator-aws/actions/workflows/security.yml/badge.svg)](https://github.com/ryanranft/nba-simulator-aws/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/ryanranft/nba-simulator-aws/branch/main/graph/badge.svg)](https://codecov.io/gh/ryanranft/nba-simulator-aws)
[![Cost](https://img.shields.io/badge/Monthly%20Cost-$38.33--75-blue)]()
[![Data](https://img.shields.io/badge/Data-119%20GB%20(+215--330%20GB%20temporal)-blue)]()
[![Events](https://img.shields.io/badge/Temporal%20Events-500M%2B-green)]()
[![Snapshots](https://img.shields.io/badge/Player%20Snapshots-50M%2B-green)]()
[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.14-blue)]()
[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20RDS%20%7C%20EC2-orange)]()

---

## Project Vision

This project creates a **temporal panel data system** that enables snapshot queries of NBA history at exact timestamps with millisecond precision, powering **context-aware game simulations** that adapt to real-time game situations.

**Core capability:**
Query cumulative NBA statistics at any exact moment in time and simulate game outcomes using a comprehensive statistical framework: econometric causal inference for regular play, nonparametric methods for irregular events, Bayesian updating for in-game learning, regime-switching models, network effects, and model ensembling.

**Example queries:**
- *"What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"*
- *"What was the NBA's average pace at 11:23:45.678 PM on March 15, 2023?"*
- *"Show me the complete game state (score, possession, lineup) at 8:45:30 PM on May 1, 2024"*

**Advanced Simulation Vision:**

The temporal precision enables **context-adaptive simulations** using a hybrid model that combines econometric causal inference with nonparametric estimation of irregular events. This dual approach handles both:
1. **Regular outcomes** (shots, turnovers, rebounds) via econometric models with causal identification
2. **Irregular events** (injuries, ejections, momentum shifts) via distribution-free methods that make no parametric assumptions

The system models how teams and players behave differently based on:

- **Game situation:** Teams trailing by 40 points play differently than tied games in double-overtime of the NBA Finals
- **Player aging:** Career arcs captured at millisecond granularity - rookies vs. prime vs. declining performance
- **Temporal context:** First game of season (extensive game planning) vs. mid-season rhythm vs. playoff intensity
- **Fatigue states:** Back-to-back games, injury recovery timelines, minutes played, real-time stamina depletion
- **Strategic adaptation:** Coaches adjust offensive plays and defensive schemes based on opponent tendencies and matchup advantages
- **Irregular events:** Technical fouls, injuries, referee bias, momentum swings, flagrant fouls, coach's challenges

**Key Innovation: Econometric + Nonparametric Integration**

Each possession combines two modeling frameworks:

**Econometric component** (for regular basketball outcomes):
- **Panel data methods:** Fixed effects control for unobserved player/team heterogeneity; random effects model hierarchical structure
- **Endogeneity correction:** Instrumental variables address reverse causality (e.g., star players playing more minutes *because* game is close)
- **Selection bias adjustment:** Propensity score matching ensures comparable historical possessions for counterfactual inference
- **Heterogeneous effects:** Interaction terms capture how play effectiveness varies by defender quality, fatigue, game stakes
- **Structural estimation:** Discrete choice models reveal decision-making processes behind shot selection and defensive positioning

**Nonparametric component** (for irregular events - distribution-free):
- **Kernel density estimation:** Model rare event frequencies without assuming Poisson, exponential, or other parametric distributions
- **Bootstrap resampling:** Generate injury occurrences by resampling from observed historical events
- **Empirical CDFs:** Draw technical fouls, flagrant fouls, ejections directly from empirical cumulative distribution functions
- **Changepoint detection:** Identify momentum shifts using PELT/Binary Segmentation algorithms without assuming run length distributions
- **Quantile regression:** Model clutch performance with fat-tailed distributions in high-pressure situations
- **Empirical transition matrices:** Capture shooting streaks via observed transition probabilities, not geometric/Markov assumptions

The payoff matrix is constructed from **estimated causal effects**, not raw correlations:
- **Offense** chooses from play types (Attack Rim, Pick & Roll, Spot-up 3PT)
- **Defense** chooses from schemes (Protect Paint, Man-to-Man, Guard Perimeter)
- **Expected PPP** estimated via regression with robust inference, including confidence intervals
- **Nash equilibrium** computed from econometrically-justified payoff matrix with parameter uncertainty
- **Substitutions** optimized by comparing lineup effectiveness using estimated treatment effects of player matchups
- **Irregular events** injected at each possession by sampling from empirical distributions without parametric assumptions

**Simulation Methodology:**

The system employs a **hybrid econometric + nonparametric model** that combines rigorous causal inference with distribution-free estimation of irregular events:

1. **Temporal feature engineering:** Extract game context (score differential, time remaining, playoff stakes, days rest, stamina levels) at each play-by-play event

2. **Econometric PPP (Points Per Possession) estimation:**
   - Use panel data regression models (fixed effects, random effects) to estimate causal relationships between game context and outcomes
   - Employ instrumental variables (IV) estimation to address endogeneity (e.g., star players' minutes affected by score, which affects outcomes)
   - Apply propensity score matching to find comparable historical possessions controlling for selection bias
   - Model heterogeneous treatment effects: impact of "Attack Rim" differs by defender quality, fatigue level, score margin
   - Estimate non-linear effects using polynomial specifications or splines (e.g., stamina's diminishing marginal impact on shooting)
   - Build 3x3 payoff matrix with econometrically-estimated expected PPP for each (offensive play, defensive strategy) combination
   - Calculate robust standard errors clustered at game level to account for within-game correlation

3. **Nonparametric event modeling (distribution-free):**
   - **Technical fouls & ejections:** Use kernel density estimation on historical frequency without assuming parametric distribution
   - **Injury events:** Bootstrap resampling from observed in-game injury occurrences (no Poisson/exponential assumptions)
   - **Referee bias patterns:** Empirical distribution of foul calling rates by official, game context, and team (avoid normal distribution assumptions)
   - **Momentum shifts:** Identify scoring runs using changepoint detection algorithms (PELT, Binary Segmentation) without assuming run length distributions
   - **Unusual plays:** Flagrant fouls, technical fouls, coach's challenges, shot clock violations drawn from empirical CDFs
   - **Clutch performance deviations:** Allow for fat-tailed distributions in high-pressure situations using quantile regression
   - **Three-point variance:** Model shooting "hot/cold" streaks via empirical transition probabilities (not geometric/Markov chains with parametric assumptions)

4. **Game theory strategy optimization:**
   - Coaches select Nash equilibrium mixed strategies from econometrically-estimated payoff matrices
   - Offensive strategy adapts based on defensive tendencies estimated from panel regressions
   - Defensive strategy counters offensive play selection probabilities
   - Substitutions optimized using lineup effectiveness differentials (PPP_offense - PPP_defense) with confidence intervals

5. **Dynamic player state modeling:**
   - Stamina degradation modeled as time-varying coefficient in panel regression framework
   - Shooting percentages estimated with player fixed effects + time-varying fatigue interaction terms
   - Defense ratings incorporate opponent quality adjustments via control function approach
   - Usage rates estimated from structural discrete choice models of shot selection

6. **Model validation & out-of-sample testing:**
   - Cross-validation: Train on seasons t-3 to t-1, test prediction accuracy on season t
   - Compare predicted vs. actual possession outcomes using likelihood ratio tests
   - Assess model fit with R², adjusted R², and information criteria (AIC/BIC)
   - Test structural stability across different game contexts (regular season vs. playoffs)
   - Validate causal identification assumptions using falsification tests and placebo checks
   - **Nonparametric validation:** Kolmogorov-Smirnov tests to verify simulated event frequencies match empirical distributions without assuming functional form

7. **Monte Carlo generation with parameter uncertainty:**
   - Run 10,000+ simulations per game, incorporating econometric estimation uncertainty
   - Each simulation draws from posterior distributions of estimated coefficients
   - **Nonparametric event injection:** At each possession, sample from empirical distributions of irregular events (injuries, technicals, challenges)
   - Use inverse transform sampling from empirical CDFs to generate rare events without parametric assumptions
   - Possession outcomes resolved stochastically using estimated probabilities + confidence bands
   - Track both sampling variation (Monte Carlo) and parameter uncertainty (econometric estimation)

8. **Betting applications with rigorous inference:**
   - Aggregate outcomes accounting for both econometric uncertainty and nonparametric event variability
   - Calculate implied probabilities with econometrically-justified confidence intervals
   - Identify +EV opportunities where market odds fall outside model's prediction intervals
   - Quantify edge magnitude using estimated treatment effects and their standard errors
   - **Tail risk assessment:** Use empirical quantiles (not normal theory) to estimate probability of extreme outcomes

**Advanced Modeling Techniques:**

The simulation framework incorporates additional sophisticated methods to capture basketball's complex dynamics:

**1. Bayesian Updating for In-Game Learning:**
- **Sequential Bayesian updates:** After each possession, update posterior beliefs about opponent strategy distribution
- **Conjugate priors:** Use Dirichlet priors for categorical strategy distributions (computationally efficient, closed-form updates)
- **Particle filtering:** For non-conjugate models, use Sequential Monte Carlo to track posterior as game evolves
- **Adaptive Nash equilibrium:** Recompute optimal mixed strategies as observed opponent play frequencies deviate from priors
- **Prior specification:** Use historical data as informative priors (α = historical frequency × effective sample size), update with in-game observations
- **Convergence diagnostics:** Monitor effective sample size, potential scale reduction factor (R-hat) to ensure posterior has converged
- **Computational efficiency:** Use Kalman filtering for linear Gaussian state-space models, particle filters for nonlinear/non-Gaussian
- **Robustness checks:** Sensitivity analysis with different prior specifications (weak/strong, optimistic/pessimistic)
- **Example:** If Celtics run "Protect Paint" 70% in Q1 vs. 50% historical prior (α₀ = [50, 30, 20] with n₀=100 observations), posterior after 20 Q1 possessions: α₁ = [50+6, 30+14, 20+0] = [56, 44, 20], Lakers' updated belief is 56/120 = 47% Protect Paint → shift strategy toward perimeter shooting

**2. Regime-Switching Models:**
- **Markov regime-switching:** Detect transitions between latent states (normal play, desperation mode, garbage time, playoff intensity)
- **Hidden Markov Models (HMM):** Identify unobserved team states like "locked in defensively" or "coasting"
- **Estimation methods:** Expectation-Maximization (EM) algorithm for maximum likelihood, Viterbi algorithm for most likely state sequence
- **Regime identification:** Use Baum-Welch algorithm to estimate transition probabilities and emission distributions
- **Number of regimes:** Select optimal K using BIC, Akaike Information Criterion (AIC), or cross-validated likelihood
- **Regime-specific parameters:** Shot selection, pace, defensive intensity, foul rates all vary by regime (estimate via regime-conditional regressions)
- **Transition probabilities:** Model P(regime_t | regime_t-1, score_diff, time, timeouts) using multinomial logit
- **Smoothing:** Use forward-backward algorithm to compute filtered (current), predicted (future), and smoothed (past) regime probabilities
- **Non-homogeneous transitions:** Allow transition matrix to depend on game context (score, time) rather than assuming constant transitions
- **Durability constraints:** Add minimum regime duration constraints to prevent unrealistic rapid switching
- **Example:** Down 15 with 3 minutes left triggers "desperation regime" with posterior probability 0.89 (vs. 0.08 normal play, 0.03 garbage time), with higher 3PT attempt rate (+18%), faster pace (+6 possessions/48min), intentional fouling strategy (P(foul) = 0.34 vs. 0.12 baseline)

**3. Network Effects & Lineup Synergies:**
- **Graph-based modeling:** Represent lineups as complete graphs K₅ where edges capture player-pair chemistry
- **Adjacency matrix estimation:** Use Exponential Random Graph Models (ERGMs) or Stochastic Actor-Oriented Models (SAOMs)
- **Interaction terms:** Estimate synergy effects beyond individual player ratings via difference-in-differences on lineup changes
- **Identification strategy:** Use player injuries/trades as natural experiments to isolate network effects from individual effects
- **Two-way fixed effects:** Control for player-specific and game-specific unobservables when estimating pair interactions
- **LeBron-AD pick-and-roll multiplier:** Estimate as (PPP_LeBron+AD) - (PPP_LeBron_alone + PPP_AD_alone), controlling for opponent quality
- **Spatial interaction models:** Capture floor spacing effects using Voronoi tessellation and geometric entropy measures
- **Network centrality metrics:** Betweenness centrality identifies playmakers (pass network), eigenvector centrality identifies offensive hubs
- **Complementarity scores:** Use principal components analysis (PCA) on skill vectors, measure angular distance in skill space
- **Spectral clustering:** Identify natural lineup groupings based on graph Laplacian eigenvalues
- **Lineup optimization:** Solve maximum weight matching problem to find optimal 5-player subgraph given opponent matchup
- **Cross-validation:** Test synergy estimates on held-out lineup combinations to avoid overfitting to sample lineups

**4. Opponent-Specific Learning:**
- **Hierarchical Bayesian models:** Team-level parameters nested within opponent-specific random effects
- **Head-to-head adjustment factors:** Lakers vs. Celtics dynamics differ from Lakers vs. average opponent
- **Matchup history:** Weight recent head-to-head games more heavily than overall historical data
- **Player-specific defensive matchups:** Estimate how Draymond specifically guards LeBron vs. average defender
- **Coaching tendencies:** Account for how specific coaches adjust strategies against specific opponents

**5. Market Efficiency Feedback Loop (Betting Applications):**
- **Performance tracking:** Record predicted probabilities vs. actual outcomes for all bets with timestamps, odds, stake sizes
- **Calibration analysis:** Verify reliability using Brier score = (1/N)Σ(p_predicted - outcome)², log loss = -(1/N)Σ[y·log(p) + (1-y)·log(1-p)]
- **Calibration curves:** Bin predictions into deciles, plot observed frequency vs. predicted probability, test for deviation from 45° line
- **Discrimination metrics:** Area under ROC curve (AUC), precision-recall curves to measure model's ability to separate outcomes
- **Kelly Criterion position sizing:** Optimal bet fraction f* = (p·(b+1) - 1) / b where p = true probability, b = decimal odds - 1
- **Fractional Kelly:** Use f*/4 or f*/2 for robustness to estimation error (reduces volatility, sacrifices growth rate)
- **Bankroll management:** Track rolling Sharpe ratio, maximum drawdown, Value at Risk (VaR), Expected Shortfall (ES)
- **Market movement monitoring:** Track if closing lines move toward model's predictions using regression: ΔOdds = α + β·ModelEdge + ε
- **Closing line value (CLV):** Measure long-term profitability: CLV = Σ(ClosingOdds - OpeningOdds) × BetDirection, positive CLV → profitable long-term
- **Sharpe ratio tracking:** Annualized Sharpe = (E[returns] - risk_free_rate) / σ(returns), benchmark against random betting (Sharpe ≈ 0)
- **Win rate vs. ROI decomposition:** Distinguish between high win rate/low odds vs. low win rate/high odds strategies
- **Bet correlation analysis:** Estimate correlation between simultaneous bets (player props correlated with game totals), adjust position sizes
- **Statistical significance tests:** Use t-tests and bootstrapped confidence intervals to verify edge is statistically significant (not luck)
- **Stopping rules:** Pre-commit to sample size (N bets) before evaluating, avoid p-hacking by continuous monitoring

**6. Temporal Autocorrelation Structures:**
- **ARIMA models for scoring runs:** Use Box-Jenkins methodology to identify optimal (p,d,q) order via ACF/PACF plots
- **Model selection:** Compare AIC/BIC across candidate models, verify residuals are white noise via Ljung-Box test
- **Augmented Dickey-Fuller test:** Test for unit roots to determine integration order d
- **Forecasting:** Generate h-step ahead forecasts with prediction intervals based on innovation variance
- **Fatigue accumulation models:** Cumulative minutes over past 7 days with exponentially decaying weights: Fatigue_t = Σ_{k=1}^7 λ^k · Minutes_{t-k}
- **Optimal decay rate:** Estimate λ via grid search or nonlinear least squares to minimize out-of-sample forecast error
- **Injury risk time series:** Model as counting process with intensity function λ(t) = exp(β₀ + β₁·ConsecutiveGames + β₂·MinutesTrend + γ·AgeDummies)
- **Duration models:** Use Cox proportional hazards or Weibull accelerated failure time models for injury prediction
- **VAR (Vector Autoregression):** Model interdependencies: [Score_Home, Score_Away, Pace]_t = Φ₁·[...]_{t-1} + Φ₂·[...]_{t-2} + ε_t
- **Granger causality tests:** Test if lags of opponent scoring help predict own team's scoring (bidirectional feedback)
- **Impulse response functions:** Trace out dynamic effects of one-unit shock to pace on future scoring
- **GARCH models:** Capture time-varying volatility in shooting: r_t = μ + ε_t, ε_t ~ N(0, σ²_t), σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}
- **Volatility forecasting:** Use GARCH(1,1) for one-step ahead volatility predictions, EGARCH for asymmetric effects
- **Multivariate GARCH:** Model correlation between players' shooting volatilities using DCC-GARCH or BEKK models
- **Structural break tests:** Use Chow test, CUSUM, or Quandt-Andrews to detect parameter instability over time

**7. Counterfactual Simulation Validation:**
- **What-if scenario testing:** "What if LeBron sat Q3?" - compare simulation to actual games where he rested
- **Treatment effect estimation:** Use potential outcomes framework: τ = E[Y₁ - Y₀] where Y₁ = outcome if treated, Y₀ = outcome if control
- **Matching methods:** Propensity score matching, coarsened exact matching (CEM), Mahalanobis distance matching to find comparable games
- **Synthetic control methods:** Construct counterfactual games as weighted average of control games: Y₀_treated = Σ w_j · Y_control,j
- **Optimal weights:** Minimize pre-treatment RMSPE subject to w_j ≥ 0, Σw_j = 1, match on pre-treatment covariates
- **Inference for synthetic controls:** Use permutation tests (placebo synthetic controls for all units) or conformal inference
- **Difference-in-differences:** Parallel trends assumption: E[Y₀_{t=1} - Y₀_{t=0} | Treated] = E[Y₀_{t=1} - Y₀_{t=0} | Control]
- **Event study specifications:** Estimate lead/lag effects to test pre-trends and dynamic treatment effects
- **Robust standard errors:** Cluster at appropriate level (player, team, season) to account for serial correlation
- **Propensity score weighting:** Inverse probability of treatment weighting (IPTW) to balance covariates
- **Doubly robust estimation:** Combine outcome regression with propensity score weighting for robustness to model misspecification
- **Placebo tests:** Run model on games where outcome is known, verify predictions match reality within statistical error
- **Falsification tests:** Test for effects in periods where no effect should exist (pre-treatment periods)
- **Sensitivity analysis:** Rosenbaum bounds for hidden bias, assess how strong unmeasured confounder must be to invalidate results
- **Sharp vs. fuzzy designs:** Sharp RD when treatment assignment is deterministic, fuzzy RD for probabilistic assignment

**8. Model Ensembling:**
- **Multiple econometric specifications:** Combine fixed effects, random effects, pooled OLS, GMM, 2SLS estimators
- **Hausman test:** Compare FE vs. RE, if test rejects (p < 0.05) then FE is consistent, RE is not
- **Bayesian Model Averaging (BMA):** Weight models by posterior probability: P(M_k | Data) ∝ P(Data | M_k) · P(M_k)
- **Marginal likelihood computation:** Use Laplace approximation, harmonic mean estimator, or bridge sampling
- **Model prior specification:** Equal priors P(M_k) = 1/K or dilution priors that penalize complexity
- **AIC/BIC weighted averaging:** w_k = exp(-0.5·Δ_k) / Σ_j exp(-0.5·Δ_j) where Δ_k = IC_k - IC_min
- **Cross-validation stacking:** Train meta-learner (ridge, lasso, random forest) on K-fold CV predictions from base models
- **Optimal convex combination:** Minimize squared error subject to w ≥ 0, Σw = 1 using quadratic programming
- **Superlearner algorithm:** Ensemble that achieves oracle property (asymptotically performs as well as best model in library)
- **Forecast combination theorems:** Show simple average often outperforms individual models when forecast errors are uncorrelated
- **Arithmetic mean:** Equal weights w_k = 1/K, robust to outliers, theoretical justification when all models unbiased
- **Geometric mean:** Log-space averaging, better for ratio/multiplicative processes
- **Inverse variance weighting:** w_k ∝ 1/σ²_k, optimal when models have different precision but same bias
- **Shrinkage methods:** Ridge regression on model predictions, shrinks toward simpler models
- **Ensemble diversity:** Include models with different assumptions (parametric vs. nonparametric, Bayesian vs. frequentist) to reduce correlation of forecast errors
- **Bias-variance decomposition:** MSE = Bias² + Variance + Irreducible Error, ensembles primarily reduce variance
- **Out-of-bag error:** Use bootstrap aggregating (bagging) and evaluate on out-of-sample observations for variance reduction
- **Validation:** Test ensemble on held-out data, verify it outperforms individual models via Diebold-Mariano test

**Example:** Simulating Lakers vs. Celtics with LeBron at age 38 in Game 7 of Finals with 2 days rest:

**Econometric estimation approach (regular outcomes):**
- Run fixed effects panel regression on historical Finals games (Q4, close score) with Age 35+ stars
- Control for opponent defensive rating, days rest, home court advantage using covariate adjustment
- Use instrumental variables: player's career average usage rate as instrument for current game usage (addresses endogeneity of "clutch" situations)
- Estimate LeBron's Attack Rim success: **β₁ = 0.685** (baseline) **+ β₂ × RestDays = +0.037** (2 days rest effect) **+ β₃ × Finals = +0.015** (playoff intensity) = **73.7% estimated success rate**
- Standard error clustered at playoff series level: **SE = 0.042**, giving 95% CI: [65.3%, 82.1%]
- Propensity score matching identifies 127 comparable possessions from historical data
- Test for defensive scheme effects: Attack Rim vs. Man-to-Man shows **+4.3pp higher success** (p < 0.05) than vs. Protect Paint

**Nonparametric event injection (irregular outcomes - distribution-free):**
- Query empirical distribution of technical fouls in Finals Game 7, Q4, close score: **P(tech foul) ≈ 0.0023** per possession (observed in 11 of 4,782 historical possessions)
- Use kernel density estimation for referee bias: This officiating crew calls **1.18x more fouls** on visiting teams in playoff games (empirical ratio, no parametric assumption)
- Bootstrap resample from 89 observed Finals Game 7 injuries: **P(in-game injury) ≈ 0.0112** (1 injury per 89 player-games)
- Identify momentum changepoints using PELT algorithm: After 6-0 runs in Finals Q4, next possession efficiency changes by **+0.31 PPP** (empirical average across 213 runs)
- Flagrant foul probability via empirical CDF: **0.00087** per possession in high-intensity playoff games (no Poisson assumption)
- Sample from empirical transition matrix for shooting streaks: If LeBron made last 2 shots, P(make next) = **0.68** (observed frequency in 412 similar streaks)

**Payoff matrix construction:**
- Each cell contains econometrically-estimated expected PPP with confidence intervals
- Lakers' coach computes Nash equilibrium using point estimates: (40% Attack Rim, 35% Pick & Roll, 25% Spot-up 3PT)
- Sensitivity analysis: With 95% CI bounds, optimal strategy ranges from 35-45% Attack Rim (robust to estimation uncertainty)

**Dynamic adjustment with nonparametric events:**
- LeBron's stamina (85/100 after 36 minutes) modeled as time-varying coefficient: **ΔShootingPct = -0.12 × (100-Stamina)** = **-1.8pp**
- Estimated success rate for this specific possession: 73.7% - 1.8% = **71.9%** [CI: 63.5%, 80.3%]
- **Irregular event check:** Sample from empirical distributions → No technical foul (rand=0.8912 > 0.0023), no injury (rand=0.4521 > 0.0112)
- **Momentum check:** Lakers on 4-0 run (below 6-0 threshold), no changepoint detected
- **Referee bias adjustment:** Visiting team, multiply foul probability by 1.18x empirical ratio

This differs from November back-to-back game where:
- Estimated success rate drops to **61.2%** (fatigue + lower stakes effects)
- Defensive scheme effects are **+2.1pp weaker** (less game-planning intensity)
- Optimal strategy shifts to **52% Pick & Roll** (exploits tired big men rotating)
- **Irregular events more likely:** P(tech foul) = **0.0041** (less emotional control when fatigued, observed empirically)
- **Injury risk higher:** P(injury) = **0.0189** on back-to-backs (bootstrap from 47 observed B2B injuries)

**Future vision:**
Integration with video feeds to synchronize ball/player coordinates with temporal snapshots for computer vision analysis at 30fps (~33ms per frame).

---

## Research Opportunities: Modeling Cumulative Advantage & Causal Mechanisms

**For ML Systems & Research Extensions:**

This temporal panel data system creates unprecedented opportunities to study self-reinforcing causal mechanisms in basketball that mirror sociological phenomena like the Matthew effect. Machine learning systems, Model Context Protocols (MCPs), and researchers are encouraged to explore:

**1. The Matthew Effect in Basketball (Cumulative Advantage):**
The Matthew effect describes how initial advantages compound over time through positive feedback loops, where "the rich get richer". In basketball contexts:

- **Momentum cascades:** Early scoring runs create psychological advantages that amplify future scoring probability (success breeds success)
- **Star treatment by referees:** Established stars receive favorable foul calls, enabling them to play more aggressively → more scoring → more star power
- **Media attention feedback:** High-performing players receive more coverage → increased endorsements → better training resources → higher performance
- **Draft position effects:** Higher draft picks receive more playing time and developmental investment, creating self-fulfilling prophecies
- **Market size advantages:** Large-market teams attract better free agents → win more → attract even better players
- **Coaching reputation loops:** Winning coaches attract better assistants and players → continue winning → reputation grows

**Modeling Challenge:** Cumulative advantage is an intra-individual micro-level phenomenon, while the Matthew effect is an inter-individual macro-level phenomenon. Simulations should capture both:
- **Micro-level:** Individual player confidence, fatigue resistance, and skill development over career
- **Macro-level:** Between-player inequality dynamics, team resource allocation, league-wide competitive balance

**2. Path Dependence & Irreversible Causal Chains:**

Basketball outcomes exhibit strong path dependence where early events constrain future possibilities:

- **Injury cascades:** One player injury → increased minutes for backups → backup gets injured → team spiral
- **Timeout timing:** Early timeout breaks opponent momentum vs. saving for critical late-game situations (irreversible decision)
- **Foul trouble trajectories:** Star picks up 2 quick fouls → sits Q1 → team falls behind → harder to catch up later
- **Chemistry development:** Lineup combinations that play together early in season develop better coordination → coach uses them more → chemistry gap widens

**Modeling Approach:** Use **path-dependent stochastic processes** where transition probabilities depend on entire history, not just current state. Implement **hysteresis effects** where system doesn't return to equilibrium after shock.

**3. Tipping Points & Phase Transitions:**

Basketball games exhibit critical thresholds where small changes trigger large shifts:

- **Blowout threshold:** Once lead exceeds ~20 points in Q3, probability of comeback drops exponentially (garbage time regime)
- **Confidence collapse:** Team misses 5 straight shots → panic sets in → shot selection deteriorates → miss 10 more
- **Crowd energy:** Home team goes on 8-0 run → crowd roars → opposing team calls timeout (social feedback mechanism)
- **Playoff intensity shift:** Regular season → playoffs transition changes all parameters (pace, physicality, strategy)

**Modeling Approach:** Use **catastrophe theory** and **regime-switching models** with endogenous transition probabilities. Identify bifurcation points where system behavior qualitatively changes.

**4. Emergent Complexity from Simple Rules:**

Basketball exhibits emergent macro-patterns that aren't reducible to individual player actions:

- **Spacing dynamics:** Five players' positions create floor geometry that enables/constrains offensive possibilities
- **Defensive rotations:** Help defense creates cascading rotation patterns across all five defenders
- **Pace contagion:** One team plays fast → opponent forced to match pace → both teams score more (emergent property)
- **Tanking equilibria:** Multiple teams simultaneously tanking for draft picks creates Nash equilibrium with poor play

**Modeling Approach:** Use **agent-based models** where players follow simple rules but collective behavior is complex. Implement **cellular automata** for spatial positioning dynamics.

**5. Black Swan Events & Fat-Tailed Distributions:**

Basketball contains rare, high-impact events that standard models miss:

- **Historic performances:** Klay Thompson's 37-point quarter (exceeds any normal prediction interval)
- **Clutch gene vs. regression:** Do some players actually perform better in clutch, or is it survivorship bias?
- **Perfect games:** Team shoots 70% from three for entire game (probability ≈ 10⁻⁸ under independence assumption)
- **Career-ending injuries:** Occur with long right tails, small probabilities but massive impact

**Modeling Approach:** Use **power law distributions**, **Lévy processes**, and **extreme value theory** rather than Gaussian assumptions. Implement **fat-tailed priors** in Bayesian models.

**6. Reflexivity & Self-Fulfilling Prophecies:**

Basketball outcomes are influenced by predictions about outcomes:

- **Betting line movements:** Sharp money moves line → public follows → line moves further (reflexive feedback)
- **Tank expectations:** Team expected to tank → fans stop attending → revenue drops → ownership cuts payroll → team actually tanks
- **MVP narratives:** Media crowns MVP frontrunner → receives more attention → highlight plays get more coverage → voting reinforces narrative
- **Playoff seeding games:** Team clinches playoff spot → rests stars → loses games → gets worse matchup (self-fulfilling)

**Modeling Approach:** Use **reflexive equilibrium models** where agents' beliefs about outcomes affect the outcomes themselves. Implement **rational expectations** with learning.

**7. Measurement-Induced Effects (Observer Effects):**

The act of measuring/modeling basketball changes the game:

- **Analytics revolution:** Teams discover 3PT efficiency → entire league shifts strategy → 3PT defense improves → efficiency advantage disappears
- **Player tracking data:** Players become aware of being tracked → modify behavior → changes the data being collected
- **Advanced stats:** Players optimize for metrics (e.g., PER, WAR) rather than pure winning

**Modeling Approach:** Incorporate **quantum game theory** concepts where observation changes outcomes. Use **meta-learning** where models account for how their own predictions alter future data.

**Implementation Guidelines for ML Systems:**

- **Embrace nonlinearity:** Basketball is fundamentally nonlinear; don't force linear approximations
- **Model feedback loops explicitly:** Use structural equation models with bidirectional causation
- **Account for unobserved heterogeneity:** Some "clutch ability" may be real skill, some may be measurement error
- **Test for causality rigorously:** Use natural experiments, IV estimation, RDD to identify causal effects
- **Validate on out-of-distribution data:** Test model on unprecedented scenarios (new rule changes, COVID season, etc.)
- **Quantify epistemic uncertainty:** Separate "we don't know the parameters well" from "the process is inherently stochastic"
- **Build interpretable models:** Black-box predictions are less useful than understanding *why* outcomes occur

**Suggested Research Projects:**

1. Estimate the magnitude of Matthew effects in NBA careers using longitudinal data
2. Identify tipping points in individual games using changepoint detection
3. Test if momentum exists after controlling for opponent quality and regression to mean
4. Build agent-based model of defensive rotations and measure emergent properties
5. Estimate fat-tailed distributions for extreme individual performances
6. Model reflexive betting markets using game theory with beliefs as endogenous variables
7. Quantify how widespread analytics adoption has changed NBA strategy over time

This framework transforms the simulation system from a pure prediction tool into a **causal inference laboratory** for understanding complex, self-reinforcing dynamics in competitive sports.

---

## Overview

This platform ingests 25+ years of historical NBA data from multiple sources and builds a temporal database for high-frequency statistical analysis, game simulation, and machine learning.

**What it does:**
- Ingests 147,382+ historical NBA game files (119+ GB) from 5 data sources (ESPN, NBA Stats, hoopR, Basketball Reference, Kaggle)
- Captures wall clock timestamps and game clock times for temporal alignment
- Extracts player birth dates for precise age calculations at any moment in time
- Stores processed data in RDS PostgreSQL with temporal indexing
- Enables snapshot reconstruction of NBA state at exact timestamps
- Trains ML models using SageMaker with temporal feature engineering

**Data precision levels:**
- **2020-2025:** Millisecond precision (NBA Live API - future integration)
- **1993-2019:** Minute-level precision (NBA Stats PlayByPlayV2)
- **1946-1992:** Game-level aggregates (Basketball Reference)

**Current Status:**  Phase 0 Complete - S3 data lake operational with 119 GB uploaded

---

## Architecture

### 5-Phase Pipeline

```
Phase 0 (✓): S3 Data Lake
   147,382 JSON files collected (70,522 in S3, 119 GB total)
      box_scores/    (44,828 files) - player statistics per game
      pbp/           (44,826 files) - play-by-play sequences
      schedule/      (11,633 files) - game schedules by date
      team_stats/    (44,828 files) - team-level statistics

Phase 2 (⏳): AWS Glue ETL
   2.1: Crawler discovers JSON schema
   2.2: ETL job extracts 10% of fields (119 GB → 12 GB)

Phase 3 (⏳): RDS PostgreSQL
   Stores extracted data (~12 GB)
      games table
      player_game_stats table
      team_game_stats table

Phase 4 (⏳): EC2 Simulation Engine
   Runs game simulations using statistical models

Phase 5 (⏳): SageMaker ML Pipeline
   Jupyter notebooks for development
   Training jobs for prediction models
```

**Key Architectural Decision:** Extract only 10% of JSON fields during ETL to reduce costs and improve performance (119 GB → 12 GB).

---

## Data Coverage

- **Time Period:** 1999 - 2025 (25+ NBA seasons)
- **Total Games:** ~44,800 games
- **Data Sources:** ESPN.com web scraping
- **File Formats:** JSON (raw), Parquet (processed)
- **Storage:** S3 (raw), RDS PostgreSQL (processed)

---

## Cost Estimates

| Phase | Monthly Cost | One-Time Setup |
|-------|--------------|----------------|
| Phase 0 (S3) | $2.74 | Complete |
| Phase 2 (Glue) | +$13 | ~6-8 hours dev |
| Phase 3 (RDS) | +$29 | ~2-3 hours setup |
| Phase 4 (EC2) | +$5-15 | ~1 week dev |
| Phase 5 (SageMaker) | +$50 | ~2-3 weeks dev |
| **Total** | **$95-130/month** | **~1 month total dev** |

**Budget Target:** $150/month (includes buffer)

See `PROGRESS.md` for detailed phase-by-phase breakdown with time estimates.

---

## Quick Start

### Prerequisites

- **Hardware:** Apple Silicon (M2/M3) recommended, 16GB+ RAM
- **OS:** macOS Sequoia 15.6+ or Linux
- **Tools:** Miniconda, Homebrew, AWS CLI 2.x, Git

### Setup

```bash
# 1. Clone repository
git clone git@github.com:ryanranft/nba-simulator-aws.git
cd nba-simulator-aws

# 2. Create conda environment
conda env create -f environment.yml
conda activate nba-aws

# 3. Configure AWS credentials
aws configure
# Enter: access key, secret key, region (us-east-1), output format (json)

# 4. Verify setup
python -c "import boto3; print('✓ boto3 installed')"
aws s3 ls s3://nba-sim-raw-data-lake/ --max-items 5
```

See `docs/SETUP.md` for complete installation and verification procedures.

---

## Documentation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - One-page command reference
- **[docs/SETUP.md](docs/SETUP.md)** - Complete environment setup
- **[PROGRESS.md](PROGRESS.md)** - Phase-by-phase implementation plan

### Development
- **[CLAUDE.md](CLAUDE.md)** - Instructions for Claude Code AI assistant
- **[docs/DATA_STRUCTURE_GUIDE.md](docs/DATA_STRUCTURE_GUIDE.md)** - ESPN JSON data structure
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Security & Workflows
- **[docs/SECURITY_PROTOCOLS.md](docs/SECURITY_PROTOCOLS.md)** - Git security, credential rotation
- **[docs/ARCHIVE_PROTOCOLS.md](docs/ARCHIVE_PROTOCOLS.md)** - Conversation and file archiving
- **[docs/SESSION_INITIALIZATION.md](docs/SESSION_INITIALIZATION.md)** - Daily workflow setup

### Archives
- **[.archive-location](.archive-location)** - Location of gitignored files archive
- **Archive System:** Gitignored files (logs, status files, conversations) are auto-archived to `~/sports-simulator-archives/nba/` organized by commit SHA

### Reference
- **[FILE_INVENTORY.md](FILE_INVENTORY.md)** - Auto-generated file summaries
- **[docs/AWS_GLUE_DATA_CATALOG_STRATEGY.md](docs/AWS_GLUE_DATA_CATALOG_STRATEGY.md)** - Cloud-based data indexing strategy (planned)
- **Hardware/Software Specs** - Archived (see ~/sports-simulator-archives/nba/)

---

## Development Machine

**Hardware:**
- Model: MacBook Pro 16-inch, 2023
- Chip: Apple M2 Max (12-core CPU, 38-core GPU)
- Memory: 96 GB unified
- Storage: 1 TB SSD

**Software:**
- OS: macOS Sequoia 15.6.1
- Python: 3.11.13 (via Miniconda)
- AWS CLI: 2.x (system-wide, not in conda)
- Package Manager: Homebrew 4.6.15

Code is optimized for Apple Silicon (ARM64) architecture. See archived specs for complete compatibility notes.

---

## Key Technologies

### AWS Services
- **S3** - Raw data lake (146K files, 119 GB)
- **Glue** - Schema discovery and ETL (10% field extraction; Data Catalog planned for cloud-based metadata indexing)
- **RDS PostgreSQL** - Structured data storage (~12 GB)
- **EC2** - Simulation compute (t3.medium or similar)
- **SageMaker** - ML model training and deployment

### Python Stack
- **boto3** - AWS SDK
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **pyarrow** - Parquet file handling
- **psycopg2** - PostgreSQL connections
- **sqlalchemy** - ORM and database abstraction

### Statistical & Econometric Methods
- **statsmodels** - Panel data regression, IV estimation, time series (ARIMA, VAR, GARCH)
- **linearmodels** - Fixed effects, random effects, GMM estimators
- **scikit-learn** - Propensity score matching, cross-validation, ensemble methods
- **pymc** - Bayesian inference, MCMC sampling, posterior updates
- **hmmlearn** - Hidden Markov Models for regime detection
- **ruptures** - Changepoint detection (PELT, Binary Segmentation)
- **networkx** - Graph-based lineup synergy modeling
- **scipy.stats** - Kernel density estimation, empirical distributions, bootstrap

See `requirements.txt` for complete dependency list.

---

## Data Pipeline Workflow

```
1. Data Ingestion (Complete)
    146K JSON files → S3 bucket

2. Schema Discovery (Pending)
    AWS Glue Crawler → Data Catalog

3. ETL Processing (Pending)
    Glue ETL job → Extract 10% fields → Parquet

4. Data Loading (Pending)
    Parquet files → RDS PostgreSQL

5. Simulation (Pending)
    Python scripts on EC2 → Game outcomes

6. ML Training (Pending)
    SageMaker → Prediction models
```

---

## Project Structure

```
nba-simulator-aws/
 config/              # AWS resource configuration
 data/                # Local data cache (gitignored)
 docs/                # Documentation (23 files)
 scripts/
    aws/            # AWS utility scripts
    maintenance/    # Documentation and archive automation
    shell/          # Workflow automation (session, archive, security)
 CLAUDE.md           # AI assistant instructions
 PROGRESS.md         # Detailed implementation roadmap
 QUICKSTART.md       # One-page command reference
 requirements.txt    # Python dependencies
```

### Phase Organization

This project uses a **hierarchical phase organization** with 4-digit zero-padded sub-phase numbering (see [ADR-010](docs/adr/010-four-digit-subphase-numbering.md)):

**Format:** `N.MMMM_name` (4 digits, zero-padded, supports up to 9,999 sub-phases per phase)

**Active Phases:**
- **Phase 0:** `0.0001` - `0.0022` (Initial Data Collection & Security)
- **Phase 5:** `5.0001` - `5.0013` (Machine Learning Models & Frameworks)

**Examples:**
- `docs/phases/phase_0/0.0001_basketball_reference/`
- `docs/phases/phase_5/5.0121_implement_ab_testing/`

**Benefits:**
- Eliminates filesystem sorting ambiguity (0.0001, 0.0002, ... 0.0010, 0.0011)
- Future-proof scalability (supports growth to 9,999 sub-phases)
- Visual clarity and alignment in directory listings
- Pre-commit validation prevents old format usage

---

## Git & GitHub

- **Repository:** https://github.com/ryanranft/nba-simulator-aws
- **Authentication:** SSH (no passwords needed)
- **Branch:** `main` (tracks `origin/main`)
- **Commit Co-author:** Claude AI assistant

**Security:**
- Pre-commit hooks scan for AWS credentials, secrets, IPs
- Pre-push hooks scan last 5 commits for leaked secrets
- Automated conversation archiving (never committed to GitHub)
- See `docs/SECURITY_PROTOCOLS.md` for complete procedures

---

## Workflow Automation

**Three unified workflow managers:**

1. **`session_manager.sh`** - Session initialization and cleanup
   ```bash
   source scripts/shell/session_manager.sh start  # Begin session
   bash scripts/shell/session_manager.sh end      # End session
   ```

2. **`archive_manager.sh`** - Conversation and file archiving
   ```bash
   bash scripts/maintenance/archive_manager.sh full  # Archive everything
   ```

3. **`pre_push_inspector.sh`** - Pre-push security inspection
   ```bash
   bash scripts/shell/pre_push_inspector.sh full  # Complete inspection
   ```

See `QUICKSTART.md` for complete workflow commands.

---

## Next Steps

See `PROGRESS.md` for detailed implementation plan. Current priority:

1. **2.0001:** Set up AWS Glue Crawler (~45 min, adds $1/month)
2. **2.0002:** Create Glue ETL job (~6-8 hrs dev, adds $13/month)
3. **Phase 3:** Provision RDS PostgreSQL (~2-3 hrs, adds $29/month)

---

## Contributing

This is a personal learning project. Contributions are not currently accepted, but feel free to fork and adapt for your own use.

---

## License

**Data Source:** ESPN.com (scraped data for personal educational use)
**Code:** Personal project, not licensed for distribution

⚠️ **Important:** This project is for educational purposes. ESPN data is scraped from publicly available web pages and should not be used commercially without proper licensing.

---

## Acknowledgments

- **ESPN.com** - Data source for historical NBA games
- **Claude Code (Anthropic)** - AI pair programming assistant
- **AWS** - Cloud infrastructure platform

---

## Contact

**Developer:** Ryan Ranft
**GitHub:** https://github.com/ryanranft
**Project:** https://github.com/ryanranft/nba-simulator-aws

---

**Last Updated:** 2025-10-02
**Version:** Phase 0 Complete (S3 Data Lake operational)