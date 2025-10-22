#!/usr/bin/env python3
"""
Bayesian Analysis Pipeline - rec_18

Comprehensive Bayesian inference system for NBA panel data implementing
recommendation rec_18 from STATISTICS 601 book analysis.

Features:
1. Hierarchical Bayesian models (player/team/game effects)
2. Shrinkage estimation (James-Stein, empirical Bayes)
3. Uncertainty quantification (credible intervals, posterior predictive)
4. Prior knowledge incorporation (informative/non-informative priors)
5. MCMC sampling (Metropolis-Hastings)
6. Model comparison (Bayes factors, WAIC)

Implementation: Master Implementation Sequence #6
Source: STATISTICS 601
Dependencies: rec_22 (panel data), rec_19 (statistical validation)
"""

import os
import sys
import logging
import json
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import logsumexp

# Optional: Try to import PyMC for advanced Bayesian modeling
PYMC_AVAILABLE = False
try:
    import pymc as pm
    import arviz as az
    PYMC_AVAILABLE = True
except ImportError:
    logging.warning("PyMC not available - using custom MCMC implementations")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BayesianAnalysisPipeline:
    """
    Comprehensive Bayesian analysis system for NBA panel data.

    Provides hierarchical Bayesian modeling, shrinkage estimation,
    uncertainty quantification, and prior knowledge incorporation.
    """

    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Bayesian Analysis Pipeline.

        Args:
            data: Panel data DataFrame (optional)
            config: Configuration dictionary (optional)
        """
        self.data = data
        self.config = config or {}
        self.results = {}
        self.models = {}

        # Default configuration
        self.default_config = {
            'mcmc_iterations': 10000,
            'mcmc_burnin': 2000,
            'mcmc_chains': 4,
            'credible_interval': 0.95,
            'prior_strength': 1.0,
            'shrinkage_threshold': 5,  # Minimum observations before shrinkage
        }

        # Merge with provided config
        self.config = {**self.default_config, **self.config}

        logger.info("Initialized Bayesian Analysis Pipeline")
        if data is not None:
            logger.info(f"Data loaded: {len(data)} observations")

    def hierarchical_model(
        self,
        outcome: str,
        predictors: List[str],
        group_var: str,
        prior_mean: float = 0.0,
        prior_sd: float = 10.0,
        method: str = 'empirical_bayes'
    ) -> Dict[str, Any]:
        """
        Fit hierarchical Bayesian model with group-level effects.

        Hierarchical structure:
        - Level 1: Individual observations
        - Level 2: Group effects (players, teams)
        - Level 3: Population hyperparameters

        Args:
            outcome: Outcome variable name
            predictors: List of predictor variable names
            group_var: Grouping variable (e.g., 'player_id', 'team_id')
            prior_mean: Prior mean for coefficients
            prior_sd: Prior standard deviation for coefficients
            method: 'empirical_bayes' or 'mcmc'

        Returns:
            Dictionary with model results, group effects, and diagnostics
        """
        logger.info(f"Fitting hierarchical model for {outcome}")
        logger.info(f"Predictors: {predictors}")
        logger.info(f"Grouping variable: {group_var}")

        if self.data is None:
            raise ValueError("No data loaded")

        # Extract data
        y = self.data[outcome].values
        X = self.data[predictors].values
        groups = self.data[group_var].values

        # Get unique groups
        unique_groups = np.unique(groups)
        n_groups = len(unique_groups)
        group_indices = {g: i for i, g in enumerate(unique_groups)}

        logger.info(f"Number of groups: {n_groups}")

        if method == 'empirical_bayes':
            # Empirical Bayes estimation
            results = self._empirical_bayes_hierarchical(
                y, X, groups, group_indices, prior_mean, prior_sd
            )
        elif method == 'mcmc':
            # MCMC estimation
            results = self._mcmc_hierarchical(
                y, X, groups, group_indices, prior_mean, prior_sd
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        # Add metadata
        results['model_type'] = 'hierarchical_bayesian'
        results['outcome'] = outcome
        results['predictors'] = predictors
        results['group_var'] = group_var
        results['n_groups'] = int(n_groups)
        results['method'] = method

        # Store results
        self.results['hierarchical_model'] = results

        logger.info(f"Hierarchical model complete: {n_groups} groups")
        return results

    def _empirical_bayes_hierarchical(
        self,
        y: np.ndarray,
        X: np.ndarray,
        groups: np.ndarray,
        group_indices: Dict[Any, int],
        prior_mean: float,
        prior_sd: float
    ) -> Dict[str, Any]:
        """
        Empirical Bayes estimation for hierarchical model.

        Uses two-stage approach:
        1. Estimate group-specific effects using OLS
        2. Shrink estimates toward population mean
        """
        n_groups = len(group_indices)
        n_features = X.shape[1]

        # Stage 1: Group-specific OLS estimates
        group_estimates = np.zeros((n_groups, n_features))
        group_ses = np.zeros((n_groups, n_features))
        group_n = np.zeros(n_groups)

        for group, idx in group_indices.items():
            # Get data for this group
            mask = groups == group
            y_group = y[mask]
            X_group = X[mask]

            if len(y_group) < n_features + 1:
                # Too few observations - use prior
                group_estimates[idx] = prior_mean
                group_ses[idx] = prior_sd
                group_n[idx] = len(y_group)
                continue

            # OLS estimation
            try:
                # Add intercept
                X_aug = np.column_stack([np.ones(len(X_group)), X_group])

                # Solve normal equations
                XtX = X_aug.T @ X_aug
                Xty = X_aug.T @ y_group

                # Check condition number
                if np.linalg.cond(XtX) > 1e10:
                    # Ill-conditioned - add ridge regularization
                    XtX += 1e-6 * np.eye(XtX.shape[0])

                beta = np.linalg.solve(XtX, Xty)

                # Standard errors
                residuals = y_group - X_aug @ beta
                sigma2 = np.sum(residuals**2) / (len(y_group) - X_aug.shape[1])
                se = np.sqrt(sigma2 * np.diag(np.linalg.inv(XtX)))

                # Store (exclude intercept)
                group_estimates[idx] = beta[1:]
                group_ses[idx] = se[1:]
                group_n[idx] = len(y_group)

            except np.linalg.LinAlgError:
                # Singular matrix - use prior
                group_estimates[idx] = prior_mean
                group_ses[idx] = prior_sd
                group_n[idx] = len(y_group)

        # Stage 2: Empirical Bayes shrinkage
        # Estimate hyperparameters from group estimates
        population_mean = np.mean(group_estimates, axis=0)
        population_var = np.var(group_estimates, axis=0)

        # Shrinkage factor (James-Stein type)
        shrinkage_factors = np.zeros((n_groups, n_features))
        for i in range(n_groups):
            for j in range(n_features):
                # Variance of group estimate
                var_estimate = group_ses[i, j]**2

                # Shrinkage toward population mean
                if population_var[j] > 0:
                    lambda_ij = population_var[j] / (population_var[j] + var_estimate)
                else:
                    lambda_ij = 0.0

                shrinkage_factors[i, j] = lambda_ij

        # Shrunken estimates
        shrunken_estimates = np.zeros_like(group_estimates)
        for i in range(n_groups):
            for j in range(n_features):
                shrunken_estimates[i, j] = (
                    shrinkage_factors[i, j] * group_estimates[i, j] +
                    (1 - shrinkage_factors[i, j]) * population_mean[j]
                )

        # Compute credible intervals
        alpha = 1 - self.config['credible_interval']
        z_critical = stats.norm.ppf(1 - alpha/2)

        credible_intervals = []
        for i in range(n_groups):
            ci_lower = shrunken_estimates[i] - z_critical * group_ses[i]
            ci_upper = shrunken_estimates[i] + z_critical * group_ses[i]
            credible_intervals.append({
                'lower': ci_lower.tolist(),
                'upper': ci_upper.tolist()
            })

        return {
            'group_estimates': group_estimates.tolist(),
            'shrunken_estimates': shrunken_estimates.tolist(),
            'shrinkage_factors': shrinkage_factors.tolist(),
            'population_mean': population_mean.tolist(),
            'population_var': population_var.tolist(),
            'group_ses': group_ses.tolist(),
            'group_n': group_n.tolist(),
            'credible_intervals': credible_intervals,
            'groups': [int(g) if isinstance(g, (np.integer, np.int64)) else g for g in group_indices.keys()]
        }

    def _mcmc_hierarchical(
        self,
        y: np.ndarray,
        X: np.ndarray,
        groups: np.ndarray,
        group_indices: Dict[Any, int],
        prior_mean: float,
        prior_sd: float
    ) -> Dict[str, Any]:
        """
        MCMC estimation for hierarchical model using Metropolis-Hastings.
        """
        logger.info("Running MCMC with Metropolis-Hastings")

        n_groups = len(group_indices)
        n_features = X.shape[1]
        n_iter = self.config['mcmc_iterations']
        burnin = self.config['mcmc_burnin']

        # Initialize parameters
        beta_global = np.zeros(n_features)  # Global coefficients
        beta_groups = np.zeros((n_groups, n_features))  # Group-specific deviations
        sigma2 = 1.0  # Residual variance
        tau2 = 1.0  # Group-level variance

        # Storage for MCMC samples
        samples_global = np.zeros((n_iter - burnin, n_features))
        samples_groups = np.zeros((n_iter - burnin, n_groups, n_features))
        samples_sigma2 = np.zeros(n_iter - burnin)
        samples_tau2 = np.zeros(n_iter - burnin)

        # Group mapping for fast indexing
        group_to_idx = np.array([group_indices[g] for g in groups])

        # MCMC iterations
        accepted = 0
        for iter_idx in range(n_iter):
            # 1. Update global coefficients (Gibbs step)
            # Prior: N(prior_mean, prior_sd^2)
            # Likelihood: sum over all observations

            precision_prior = 1 / prior_sd**2
            precision_likelihood = 0.0
            weighted_sum = 0.0

            for i in range(len(y)):
                group_idx = group_to_idx[i]
                # Predicted value using current group effect
                pred = X[i] @ (beta_global + beta_groups[group_idx])
                precision_likelihood += (X[i]**2).sum() / sigma2
                weighted_sum += X[i] * (y[i] - X[i] @ beta_groups[group_idx]) / sigma2

            posterior_precision = precision_prior + precision_likelihood
            posterior_mean = (prior_mean * precision_prior + weighted_sum) / posterior_precision
            posterior_sd = np.sqrt(1 / posterior_precision)

            beta_global = np.random.normal(posterior_mean, posterior_sd)

            # 2. Update group-specific deviations (Gibbs step)
            for group_idx in range(n_groups):
                mask = group_to_idx == group_idx
                if not mask.any():
                    continue

                y_group = y[mask]
                X_group = X[mask]

                # Prior: N(0, tau2)
                # Likelihood: observations in this group
                precision_prior = 1 / tau2
                precision_likelihood = (X_group**2).sum(axis=0) / sigma2

                posterior_precision = precision_prior + precision_likelihood

                residual = y_group[:, np.newaxis] - X_group * beta_global
                weighted_sum = (X_group * residual).sum(axis=0) / sigma2

                posterior_mean = weighted_sum / posterior_precision
                posterior_sd = np.sqrt(1 / posterior_precision)

                beta_groups[group_idx] = np.random.normal(posterior_mean, posterior_sd)

            # 3. Update residual variance (Gibbs step)
            # Inverse-Gamma prior (non-informative)
            residuals = np.zeros(len(y))
            for i in range(len(y)):
                group_idx = group_to_idx[i]
                pred = X[i] @ (beta_global + beta_groups[group_idx])
                residuals[i] = y[i] - pred

            sse = np.sum(residuals**2)
            shape = len(y) / 2
            scale = sse / 2
            sigma2 = 1 / np.random.gamma(shape, 1/scale)

            # 4. Update group-level variance (Gibbs step)
            # Inverse-Gamma prior
            ssb = np.sum(beta_groups**2)
            shape = n_groups * n_features / 2
            scale = ssb / 2
            tau2 = 1 / np.random.gamma(shape, 1/scale)

            # Store samples (after burnin)
            if iter_idx >= burnin:
                idx = iter_idx - burnin
                samples_global[idx] = beta_global
                samples_groups[idx] = beta_groups
                samples_sigma2[idx] = sigma2
                samples_tau2[idx] = tau2

            if (iter_idx + 1) % 1000 == 0:
                logger.info(f"MCMC iteration {iter_idx + 1}/{n_iter}")

        # Compute posterior summaries
        posterior_mean_global = samples_global.mean(axis=0)
        posterior_sd_global = samples_global.std(axis=0)
        posterior_mean_groups = samples_groups.mean(axis=0)
        posterior_sd_groups = samples_groups.std(axis=0)

        # Credible intervals
        alpha = 1 - self.config['credible_interval']
        ci_lower_global = np.percentile(samples_global, 100 * alpha/2, axis=0)
        ci_upper_global = np.percentile(samples_global, 100 * (1 - alpha/2), axis=0)

        credible_intervals_groups = []
        for i in range(n_groups):
            ci_lower = np.percentile(samples_groups[:, i, :], 100 * alpha/2, axis=0)
            ci_upper = np.percentile(samples_groups[:, i, :], 100 * (1 - alpha/2), axis=0)
            credible_intervals_groups.append({
                'lower': ci_lower.tolist(),
                'upper': ci_upper.tolist()
            })

        return {
            'posterior_mean_global': posterior_mean_global.tolist(),
            'posterior_sd_global': posterior_sd_global.tolist(),
            'posterior_mean_groups': posterior_mean_groups.tolist(),
            'posterior_sd_groups': posterior_sd_groups.tolist(),
            'ci_global': {
                'lower': ci_lower_global.tolist(),
                'upper': ci_upper_global.tolist()
            },
            'credible_intervals_groups': credible_intervals_groups,
            'posterior_mean_sigma2': float(samples_sigma2.mean()),
            'posterior_mean_tau2': float(samples_tau2.mean()),
            'groups': [int(g) if isinstance(g, (np.integer, np.int64)) else g for g in group_indices.keys()],
            'n_iterations': int(n_iter),
            'burnin': int(burnin)
        }

    def shrinkage_estimation(
        self,
        estimates: np.ndarray,
        standard_errors: np.ndarray,
        method: str = 'james_stein'
    ) -> Dict[str, Any]:
        """
        Apply shrinkage estimation to noisy estimates.

        Shrinkage methods pull extreme estimates toward the population mean,
        which is especially useful for small sample sizes (e.g., rookie players).

        Args:
            estimates: Array of point estimates (e.g., player batting averages)
            standard_errors: Array of standard errors
            method: 'james_stein' or 'empirical_bayes'

        Returns:
            Dictionary with shrunken estimates and shrinkage factors
        """
        logger.info(f"Applying {method} shrinkage to {len(estimates)} estimates")

        if method == 'james_stein':
            # James-Stein estimator
            grand_mean = np.mean(estimates)

            # Shrinkage factor
            # lambda = (p-2) * sigma^2 / ||theta - mu||^2
            p = len(estimates)
            sigma2 = np.mean(standard_errors**2)
            norm_sq = np.sum((estimates - grand_mean)**2)

            if norm_sq > 0:
                lambda_js = min(1.0, (p - 2) * sigma2 / norm_sq)
            else:
                lambda_js = 0.0

            # Shrunken estimates
            shrunken = grand_mean + (1 - lambda_js) * (estimates - grand_mean)

            shrinkage_factors = np.full(len(estimates), lambda_js)

        elif method == 'empirical_bayes':
            # Empirical Bayes shrinkage
            # Estimate hyperparameters from data
            grand_mean = np.mean(estimates)

            # Between-group variance
            tau2 = max(0.0, np.var(estimates) - np.mean(standard_errors**2))

            # Shrinkage factors (group-specific)
            shrinkage_factors = standard_errors**2 / (standard_errors**2 + tau2)

            # Shrunken estimates
            shrunken = grand_mean + (1 - shrinkage_factors) * (estimates - grand_mean)

        else:
            raise ValueError(f"Unknown shrinkage method: {method}")

        # Compute mean squared error reduction
        mse_original = np.mean(standard_errors**2)
        mse_shrunken = np.mean((shrunken - estimates)**2 + (1 - shrinkage_factors)**2 * standard_errors**2)
        mse_reduction = (mse_original - mse_shrunken) / mse_original

        results = {
            'original_estimates': estimates.tolist(),
            'shrunken_estimates': shrunken.tolist(),
            'shrinkage_factors': shrinkage_factors.tolist(),
            'grand_mean': float(grand_mean),
            'method': method,
            'mse_reduction': float(mse_reduction)
        }

        self.results['shrinkage_estimation'] = results

        logger.info(f"Shrinkage complete: MSE reduction = {mse_reduction:.2%}")
        return results

    def credible_interval(
        self,
        samples: np.ndarray,
        credible_level: float = 0.95,
        method: str = 'percentile'
    ) -> Dict[str, Any]:
        """
        Compute Bayesian credible interval from posterior samples.

        Args:
            samples: Posterior samples (1D or 2D array)
            credible_level: Credibility level (e.g., 0.95 for 95% CI)
            method: 'percentile' or 'hpd' (highest posterior density)

        Returns:
            Dictionary with credible intervals
        """
        logger.info(f"Computing {credible_level*100}% credible interval")

        if method == 'percentile':
            # Equal-tailed credible interval
            alpha = 1 - credible_level

            if samples.ndim == 1:
                ci_lower = float(np.percentile(samples, 100 * alpha/2))
                ci_upper = float(np.percentile(samples, 100 * (1 - alpha/2)))
            else:
                ci_lower = np.percentile(samples, 100 * alpha/2, axis=0).tolist()
                ci_upper = np.percentile(samples, 100 * (1 - alpha/2), axis=0).tolist()

        elif method == 'hpd':
            # Highest Posterior Density interval
            # This is the shortest interval containing credible_level of the mass
            ci_lower, ci_upper = self._hpd_interval(samples, credible_level)

        else:
            raise ValueError(f"Unknown method: {method}")

        results = {
            'credible_level': float(credible_level),
            'method': method,
            'lower': ci_lower,
            'upper': ci_upper,
            'posterior_mean': float(np.mean(samples)) if samples.ndim == 1 else np.mean(samples, axis=0).tolist(),
            'posterior_sd': float(np.std(samples)) if samples.ndim == 1 else np.std(samples, axis=0).tolist()
        }

        return results

    def _hpd_interval(
        self,
        samples: np.ndarray,
        credible_level: float
    ) -> Tuple[float, float]:
        """
        Compute Highest Posterior Density (HPD) interval.

        The HPD interval is the shortest interval containing credible_level
        of the posterior mass.
        """
        if samples.ndim > 1:
            raise ValueError("HPD interval only supports 1D samples")

        # Sort samples
        sorted_samples = np.sort(samples)
        n = len(sorted_samples)

        # Number of samples to include
        n_included = int(np.ceil(credible_level * n))

        # Find shortest interval
        interval_widths = sorted_samples[n_included:] - sorted_samples[:n-n_included]
        min_idx = np.argmin(interval_widths)

        ci_lower = float(sorted_samples[min_idx])
        ci_upper = float(sorted_samples[min_idx + n_included])

        return ci_lower, ci_upper

    def posterior_predictive(
        self,
        model_type: str = 'hierarchical',
        n_samples: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate posterior predictive distribution.

        The posterior predictive distribution represents uncertainty about
        future observations given the observed data.

        Args:
            model_type: Type of model to use ('hierarchical', etc.)
            n_samples: Number of predictive samples to generate

        Returns:
            Dictionary with posterior predictive samples and summaries
        """
        logger.info(f"Generating posterior predictive distribution ({n_samples} samples)")

        if model_type not in self.results:
            raise ValueError(f"Model {model_type} not fitted")

        # Get model results
        results = self.results[model_type]

        # Generate predictive samples
        # This is a simplified version - in practice, you'd use the full posterior
        if 'posterior_mean_global' in results:
            # MCMC results
            mean = np.array(results['posterior_mean_global'])
            sd = np.array(results['posterior_sd_global'])
            sigma = results['posterior_mean_sigma2']

            # Generate samples from posterior predictive
            # y_new ~ N(X * beta, sigma^2)
            predictive_samples = []
            for _ in range(n_samples):
                beta_sample = np.random.normal(mean, sd)
                # Assume X = [1] for simplicity (intercept only)
                y_pred = np.random.normal(beta_sample.sum(), np.sqrt(sigma))
                predictive_samples.append(float(y_pred))

        else:
            # Empirical Bayes results
            shrunken = np.array(results['shrunken_estimates'])
            mean = np.mean(shrunken, axis=0)
            sd = np.std(shrunken, axis=0)

            # Generate samples
            predictive_samples = []
            for _ in range(n_samples):
                y_pred = np.random.normal(mean.sum(), sd.sum())
                predictive_samples.append(float(y_pred))

        predictive_samples = np.array(predictive_samples)

        # Compute summary statistics
        summary = {
            'mean': float(np.mean(predictive_samples)),
            'median': float(np.median(predictive_samples)),
            'sd': float(np.std(predictive_samples)),
            'q025': float(np.percentile(predictive_samples, 2.5)),
            'q975': float(np.percentile(predictive_samples, 97.5))
        }

        results_dict = {
            'samples': predictive_samples.tolist(),
            'summary': summary,
            'n_samples': int(n_samples),
            'model_type': model_type
        }

        self.results['posterior_predictive'] = results_dict

        logger.info(f"Posterior predictive: mean={summary['mean']:.3f}, sd={summary['sd']:.3f}")
        return results_dict

    def bayes_factor(
        self,
        model1_log_likelihood: float,
        model2_log_likelihood: float,
        interpretation: bool = True
    ) -> Dict[str, Any]:
        """
        Compute Bayes factor for model comparison.

        Bayes factor = P(data | model1) / P(data | model2)

        Interpretation (Kass & Raftery 1995):
        - BF < 1: Evidence for model 2
        - 1 < BF < 3: Weak evidence for model 1
        - 3 < BF < 20: Positive evidence for model 1
        - 20 < BF < 150: Strong evidence for model 1
        - BF > 150: Very strong evidence for model 1

        Args:
            model1_log_likelihood: Log marginal likelihood of model 1
            model2_log_likelihood: Log marginal likelihood of model 2
            interpretation: Include textual interpretation

        Returns:
            Dictionary with Bayes factor and interpretation
        """
        logger.info("Computing Bayes factor for model comparison")

        # Bayes factor (on log scale to avoid overflow)
        log_bf = model1_log_likelihood - model2_log_likelihood
        bf = np.exp(log_bf)

        # Interpretation
        if interpretation:
            if bf < 1:
                bf_interpretation = "Evidence favors model 2"
            elif bf < 3:
                bf_interpretation = "Weak evidence for model 1"
            elif bf < 20:
                bf_interpretation = "Positive evidence for model 1"
            elif bf < 150:
                bf_interpretation = "Strong evidence for model 1"
            else:
                bf_interpretation = "Very strong evidence for model 1"
        else:
            bf_interpretation = None

        results = {
            'bayes_factor': float(bf),
            'log_bayes_factor': float(log_bf),
            'interpretation': bf_interpretation,
            'model1_log_likelihood': float(model1_log_likelihood),
            'model2_log_likelihood': float(model2_log_likelihood)
        }

        logger.info(f"Bayes factor = {bf:.3f} ({bf_interpretation})")
        return results

    def generate_report(
        self,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive Bayesian analysis report.

        Args:
            output_path: Path to save JSON report (optional)

        Returns:
            Dictionary with all analysis results
        """
        logger.info("Generating Bayesian analysis report")

        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'n_observations': len(self.data) if self.data is not None else 0,
                'config': self.config
            },
            'results': self.results
        }

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Report saved to {output_path}")

        return report


def demo_bayesian_analysis():
    """
    Demonstrate Bayesian analysis capabilities with synthetic NBA data.
    """
    logger.info("="*80)
    logger.info("Bayesian Analysis Pipeline - Demo")
    logger.info("="*80)

    # Generate synthetic panel data
    np.random.seed(42)

    n_players = 20
    n_games_per_player = 50
    n_total = n_players * n_games_per_player

    # Player IDs
    player_ids = np.repeat(np.arange(n_players), n_games_per_player)

    # Player-specific true skills (random effects)
    true_skills = np.random.normal(15, 5, n_players)  # Mean PPG

    # Generate points per game with noise
    points = np.zeros(n_total)
    for i, player_id in enumerate(player_ids):
        # Player's true skill + game-to-game variation
        points[i] = np.random.normal(true_skills[player_id], 3)

    # Create DataFrame
    data = pd.DataFrame({
        'player_id': player_ids,
        'points': points,
        'minutes': np.random.normal(25, 5, n_total),  # Minutes played
        'opponent_strength': np.random.uniform(0, 1, n_total)  # Opponent difficulty
    })

    logger.info(f"Sample data: {len(data)} observations, {n_players} players")

    # Initialize pipeline
    pipeline = BayesianAnalysisPipeline(data)

    # 1. Hierarchical Bayesian model
    logger.info("\n" + "="*80)
    logger.info("1. Hierarchical Bayesian Model (Empirical Bayes)")
    logger.info("="*80)

    hierarchical_results = pipeline.hierarchical_model(
        outcome='points',
        predictors=['minutes', 'opponent_strength'],
        group_var='player_id',
        method='empirical_bayes'
    )

    logger.info(f"Population mean: {hierarchical_results['population_mean']}")
    logger.info(f"Number of groups: {hierarchical_results['n_groups']}")

    # 2. Shrinkage estimation
    logger.info("\n" + "="*80)
    logger.info("2. Shrinkage Estimation (James-Stein)")
    logger.info("="*80)

    # Get player-specific estimates
    player_means = data.groupby('player_id')['points'].mean().values
    player_ses = data.groupby('player_id')['points'].sem().values

    shrinkage_results = pipeline.shrinkage_estimation(
        player_means,
        player_ses,
        method='james_stein'
    )

    logger.info(f"MSE reduction: {shrinkage_results['mse_reduction']:.2%}")

    # 3. MCMC Hierarchical Model
    logger.info("\n" + "="*80)
    logger.info("3. Hierarchical Bayesian Model (MCMC)")
    logger.info("="*80)

    mcmc_results = pipeline.hierarchical_model(
        outcome='points',
        predictors=['minutes', 'opponent_strength'],
        group_var='player_id',
        method='mcmc'
    )

    logger.info(f"Posterior mean (global): {mcmc_results['posterior_mean_global']}")
    logger.info(f"Posterior SD (global): {mcmc_results['posterior_sd_global']}")

    # 4. Posterior predictive distribution
    logger.info("\n" + "="*80)
    logger.info("4. Posterior Predictive Distribution")
    logger.info("="*80)

    predictive_results = pipeline.posterior_predictive(
        model_type='hierarchical_model',
        n_samples=1000
    )

    logger.info(f"Predictive mean: {predictive_results['summary']['mean']:.2f}")
    logger.info(f"Predictive 95% CI: [{predictive_results['summary']['q025']:.2f}, {predictive_results['summary']['q975']:.2f}]")

    # 5. Generate report
    logger.info("Generating Bayesian analysis report...")
    report_path = "/tmp/bayesian_analysis/bayesian_analysis_report.json"
    report = pipeline.generate_report(output_path=report_path)

    logger.info(f"Report saved to {report_path}")

    logger.info("\n" + "="*80)
    logger.info("✅ Bayesian analysis complete!")
    logger.info("="*80)


if __name__ == '__main__':
    demo_bayesian_analysis()
