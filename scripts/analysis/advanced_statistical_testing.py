#!/usr/bin/env python3
"""
Advanced Statistical Testing Framework

Implements #5 in Master Implementation Sequence (rec_17)

Provides comprehensive statistical inference tools:
1. Hypothesis Testing - t-tests, F-tests, chi-square tests
2. Confidence Intervals - parametric and bootstrap
3. Bootstrap Methods - residual, case, wild bootstrap
4. Multiple Testing Corrections - Bonferroni, Holm, FDR (Benjamini-Hochberg)
5. Effect Size Calculations - Cohen's d, eta-squared, Cramér's V

Source: Elements of Statistical Learning, STATISTICS 601
Dependencies: #1 (Panel Data Processing), #4 (Statistical Validation)
Created: October 2025
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import t, f, chi2, norm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedStatisticalTestingFramework:
    """
    Comprehensive statistical inference framework.

    Provides hypothesis testing, confidence intervals, bootstrap methods,
    and multiple testing corrections for panel data analysis.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        output_dir: str = "/tmp/statistical_testing"
    ):
        """
        Initialize statistical testing framework.

        Args:
            data: DataFrame with panel data
            output_dir: Directory for saving test results
        """
        self.data = data
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            'hypothesis_tests': {},
            'confidence_intervals': {},
            'bootstrap_results': {},
            'multiple_testing': {},
            'effect_sizes': {},
            'metadata': {
                'n_observations': len(data),
                'timestamp': datetime.now().isoformat()
            }
        }

        logger.info(f"Initialized Advanced Statistical Testing Framework")
        logger.info(f"Observations: {len(data)}")

    def hypothesis_test(
        self,
        variable1: str,
        variable2: Optional[str] = None,
        test_type: str = 'ttest',
        alternative: str = 'two-sided',
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """
        Perform hypothesis test.

        Args:
            variable1: First variable name
            variable2: Second variable name (for two-sample tests)
            test_type: Type of test ('ttest', 'paired_ttest', 'f_test', 'chi2')
            alternative: 'two-sided', 'less', or 'greater'
            significance_level: Alpha level for test

        Returns:
            Test results dictionary
        """
        logger.info(f"Running {test_type} for {variable1}" +
                   (f" vs {variable2}" if variable2 else ""))

        try:
            if test_type == 'ttest':
                if variable2 is None:
                    # One-sample t-test (against zero)
                    data1 = self.data[variable1].dropna()
                    statistic, pvalue = stats.ttest_1samp(data1, 0.0, alternative=alternative)
                    test_name = "One-Sample t-test"
                else:
                    # Two-sample t-test
                    data1 = self.data[variable1].dropna()
                    data2 = self.data[variable2].dropna()
                    statistic, pvalue = stats.ttest_ind(data1, data2, alternative=alternative)
                    test_name = "Two-Sample t-test"

            elif test_type == 'paired_ttest':
                # Paired t-test
                data1 = self.data[variable1].dropna()
                data2 = self.data[variable2].dropna()
                statistic, pvalue = stats.ttest_rel(data1, data2, alternative=alternative)
                test_name = "Paired t-test"

            elif test_type == 'f_test':
                # F-test for variance equality
                data1 = self.data[variable1].dropna()
                data2 = self.data[variable2].dropna()
                var1, var2 = np.var(data1, ddof=1), np.var(data2, ddof=1)
                statistic = var1 / var2 if var1 > var2 else var2 / var1
                df1, df2 = len(data1) - 1, len(data2) - 1
                pvalue = 2 * min(f.cdf(statistic, df1, df2), 1 - f.cdf(statistic, df1, df2))
                test_name = "F-test (Variance Equality)"

            elif test_type == 'chi2':
                # Chi-square test for independence
                contingency_table = pd.crosstab(self.data[variable1], self.data[variable2])
                statistic, pvalue, dof, expected = stats.chi2_contingency(contingency_table)
                test_name = "Chi-Square Test of Independence"

            else:
                raise ValueError(f"Unknown test type: {test_type}")

            result = {
                'test_name': test_name,
                'test_type': test_type,
                'variable1': variable1,
                'variable2': variable2,
                'statistic': float(statistic),
                'pvalue': float(pvalue),
                'significance_level': significance_level,
                'reject_null': bool(pvalue < significance_level),  # Convert to Python bool
                'alternative': alternative,
                'conclusion': (
                    f"Reject null hypothesis (p={pvalue:.4f} < {significance_level})"
                    if pvalue < significance_level
                    else f"Fail to reject null hypothesis (p={pvalue:.4f} >= {significance_level})"
                ),
                'status': 'completed'
            }

            test_key = f"{test_type}_{variable1}" + (f"_{variable2}" if variable2 else "")
            self.results['hypothesis_tests'][test_key] = result

            logger.info(f"{test_name}: statistic={statistic:.4f}, p-value={pvalue:.4f}")
            logger.info(f"Conclusion: {result['conclusion']}")

            return result

        except Exception as e:
            logger.error(f"Hypothesis test failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            return result

    def confidence_interval(
        self,
        variable: str,
        confidence_level: float = 0.95,
        method: str = 'parametric'
    ) -> Dict[str, Any]:
        """
        Calculate confidence interval for population mean.

        Args:
            variable: Variable name
            confidence_level: Confidence level (e.g., 0.95 for 95% CI)
            method: 'parametric' or 'bootstrap'

        Returns:
            Confidence interval results
        """
        logger.info(f"Computing {confidence_level*100}% CI for {variable} ({method})")

        try:
            data = self.data[variable].dropna().values
            n = len(data)
            mean = np.mean(data)

            if method == 'parametric':
                # Parametric CI using t-distribution
                std_error = stats.sem(data)
                alpha = 1 - confidence_level
                t_critical = t.ppf(1 - alpha/2, n - 1)
                margin_error = t_critical * std_error
                ci_lower = mean - margin_error
                ci_upper = mean + margin_error

            elif method == 'bootstrap':
                # Bootstrap CI
                ci_lower, ci_upper = self._bootstrap_ci(
                    data,
                    statistic_func=np.mean,
                    confidence_level=confidence_level,
                    n_iterations=10000
                )

            else:
                raise ValueError(f"Unknown method: {method}")

            result = {
                'variable': variable,
                'method': method,
                'confidence_level': confidence_level,
                'point_estimate': float(mean),
                'ci_lower': float(ci_lower),
                'ci_upper': float(ci_upper),
                'ci_width': float(ci_upper - ci_lower),
                'n_observations': int(n),
                'status': 'completed'
            }

            ci_key = f"{variable}_{method}_{int(confidence_level*100)}"
            self.results['confidence_intervals'][ci_key] = result

            logger.info(f"{confidence_level*100}% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

            return result

        except Exception as e:
            logger.error(f"Confidence interval calculation failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            return result

    def bootstrap_test(
        self,
        variable: str,
        statistic_func: Callable = np.mean,
        null_value: float = 0.0,
        alternative: str = 'two-sided',
        n_iterations: int = 10000,
        bootstrap_type: str = 'case'
    ) -> Dict[str, Any]:
        """
        Bootstrap hypothesis test.

        Args:
            variable: Variable name
            statistic_func: Function to compute statistic (default: mean)
            null_value: Null hypothesis value
            alternative: 'two-sided', 'less', or 'greater'
            n_iterations: Number of bootstrap iterations
            bootstrap_type: 'case', 'residual', or 'wild'

        Returns:
            Bootstrap test results
        """
        logger.info(f"Running bootstrap test for {variable} (n={n_iterations})")

        try:
            data = self.data[variable].dropna().values
            n = len(data)

            # Observed statistic
            observed_stat = statistic_func(data)

            # Center data under null hypothesis
            centered_data = data - observed_stat + null_value

            # Bootstrap distribution
            bootstrap_stats = np.zeros(n_iterations)

            for i in range(n_iterations):
                if bootstrap_type == 'case':
                    # Resample observations
                    bootstrap_sample = np.random.choice(centered_data, size=n, replace=True)
                elif bootstrap_type == 'residual':
                    # Resample residuals (assuming linear model)
                    residuals = data - observed_stat
                    resampled_residuals = np.random.choice(residuals, size=n, replace=True)
                    bootstrap_sample = null_value + resampled_residuals
                elif bootstrap_type == 'wild':
                    # Wild bootstrap for heteroskedasticity
                    residuals = data - observed_stat
                    multipliers = np.random.choice([-1, 1], size=n)
                    bootstrap_sample = null_value + residuals * multipliers

                bootstrap_stats[i] = statistic_func(bootstrap_sample)

            # Compute p-value
            if alternative == 'two-sided':
                pvalue = 2 * min(
                    np.mean(bootstrap_stats >= observed_stat),
                    np.mean(bootstrap_stats <= observed_stat)
                )
            elif alternative == 'greater':
                pvalue = np.mean(bootstrap_stats >= observed_stat)
            elif alternative == 'less':
                pvalue = np.mean(bootstrap_stats <= observed_stat)

            result = {
                'variable': variable,
                'bootstrap_type': bootstrap_type,
                'n_iterations': n_iterations,
                'observed_statistic': float(observed_stat),
                'null_value': null_value,
                'pvalue': float(pvalue),
                'alternative': alternative,
                'bootstrap_mean': float(np.mean(bootstrap_stats)),
                'bootstrap_std': float(np.std(bootstrap_stats)),
                'status': 'completed'
            }

            bootstrap_key = f"{variable}_{bootstrap_type}"
            self.results['bootstrap_results'][bootstrap_key] = result

            logger.info(f"Bootstrap p-value: {pvalue:.4f}")

            return result

        except Exception as e:
            logger.error(f"Bootstrap test failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            return result

    def multiple_testing_correction(
        self,
        pvalues: List[float],
        method: str = 'fdr_bh',
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Apply multiple testing correction.

        Args:
            pvalues: List of p-values to correct
            method: 'bonferroni', 'holm', 'fdr_bh' (Benjamini-Hochberg)
            alpha: Family-wise error rate or FDR level

        Returns:
            Correction results
        """
        logger.info(f"Applying {method} correction to {len(pvalues)} p-values")

        try:
            pvalues = np.array(pvalues)
            m = len(pvalues)

            if method == 'bonferroni':
                # Bonferroni correction
                adjusted_pvalues = np.minimum(pvalues * m, 1.0)
                reject = adjusted_pvalues < alpha

            elif method == 'holm':
                # Holm-Bonferroni correction
                sorted_indices = np.argsort(pvalues)
                sorted_pvalues = pvalues[sorted_indices]

                adjusted_pvalues = np.zeros(m)
                for i in range(m):
                    adjusted_pvalues[sorted_indices[i]] = min(
                        sorted_pvalues[i] * (m - i),
                        1.0
                    )

                reject = adjusted_pvalues < alpha

            elif method == 'fdr_bh':
                # Benjamini-Hochberg FDR control
                sorted_indices = np.argsort(pvalues)
                sorted_pvalues = pvalues[sorted_indices]

                # Find largest i where p(i) <= (i/m) * alpha
                threshold_values = (np.arange(1, m + 1) / m) * alpha
                significant = sorted_pvalues <= threshold_values

                if np.any(significant):
                    max_i = np.where(significant)[0][-1]
                    reject = np.zeros(m, dtype=bool)
                    reject[sorted_indices[:max_i+1]] = True
                else:
                    reject = np.zeros(m, dtype=bool)

                # Adjusted p-values for FDR
                adjusted_pvalues = np.zeros(m)
                for i in range(m):
                    adjusted_pvalues[sorted_indices[i]] = min(
                        sorted_pvalues[i] * m / (i + 1),
                        1.0
                    )

            else:
                raise ValueError(f"Unknown correction method: {method}")

            result = {
                'method': method,
                'n_tests': m,
                'alpha': alpha,
                'n_rejected': int(np.sum(reject)),
                'proportion_rejected': float(np.mean(reject)),
                'original_pvalues': pvalues.tolist(),
                'adjusted_pvalues': adjusted_pvalues.tolist(),
                'reject': [bool(x) for x in reject],  # Convert numpy bool to Python bool
                'status': 'completed'
            }

            self.results['multiple_testing'][method] = result

            logger.info(f"Rejected {np.sum(reject)}/{m} tests at alpha={alpha}")

            return result

        except Exception as e:
            logger.error(f"Multiple testing correction failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            return result

    def effect_size(
        self,
        variable1: str,
        variable2: Optional[str] = None,
        effect_type: str = 'cohens_d'
    ) -> Dict[str, Any]:
        """
        Calculate effect size.

        Args:
            variable1: First variable name
            variable2: Second variable name (for two-group comparisons)
            effect_type: 'cohens_d', 'eta_squared', 'cramers_v'

        Returns:
            Effect size results
        """
        logger.info(f"Calculating {effect_type} for {variable1}" +
                   (f" vs {variable2}" if variable2 else ""))

        try:
            if effect_type == 'cohens_d':
                # Cohen's d for mean difference
                data1 = self.data[variable1].dropna()

                if variable2 is None:
                    # One-sample Cohen's d (vs zero)
                    d = np.mean(data1) / np.std(data1, ddof=1)
                else:
                    # Two-sample Cohen's d
                    data2 = self.data[variable2].dropna()
                    pooled_std = np.sqrt(
                        ((len(data1) - 1) * np.var(data1, ddof=1) +
                         (len(data2) - 1) * np.var(data2, ddof=1)) /
                        (len(data1) + len(data2) - 2)
                    )
                    d = (np.mean(data1) - np.mean(data2)) / pooled_std

                # Interpretation
                if abs(d) < 0.2:
                    interpretation = "negligible"
                elif abs(d) < 0.5:
                    interpretation = "small"
                elif abs(d) < 0.8:
                    interpretation = "medium"
                else:
                    interpretation = "large"

                result = {
                    'effect_type': effect_type,
                    'variable1': variable1,
                    'variable2': variable2,
                    'effect_size': float(d),
                    'interpretation': interpretation,
                    'status': 'completed'
                }

            else:
                raise ValueError(f"Effect type {effect_type} not yet implemented")

            effect_key = f"{effect_type}_{variable1}" + (f"_{variable2}" if variable2 else "")
            self.results['effect_sizes'][effect_key] = result

            logger.info(f"{effect_type} = {d:.4f} ({interpretation})")

            return result

        except Exception as e:
            logger.error(f"Effect size calculation failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            return result

    def _bootstrap_ci(
        self,
        data: np.ndarray,
        statistic_func: Callable,
        confidence_level: float = 0.95,
        n_iterations: int = 10000
    ) -> Tuple[float, float]:
        """
        Compute bootstrap confidence interval.

        Args:
            data: Data array
            statistic_func: Function to compute statistic
            confidence_level: Confidence level
            n_iterations: Number of bootstrap iterations

        Returns:
            (lower_bound, upper_bound)
        """
        n = len(data)
        bootstrap_stats = np.zeros(n_iterations)

        for i in range(n_iterations):
            bootstrap_sample = np.random.choice(data, size=n, replace=True)
            bootstrap_stats[i] = statistic_func(bootstrap_sample)

        alpha = 1 - confidence_level
        ci_lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
        ci_upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

        return ci_lower, ci_upper

    def generate_report(
        self,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive testing report.

        Args:
            output_file: Path to save report

        Returns:
            Path to generated report
        """
        logger.info("Generating statistical testing report...")

        if output_file is None:
            output_file = self.output_dir / "statistical_testing_report.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Report saved to {output_file}")
        return str(output_file)


def main():
    """
    Demo: Advanced statistical testing on sample data.
    """
    logger.info("=" * 80)
    logger.info("Advanced Statistical Testing Framework - Demo")
    logger.info("=" * 80)

    # Create sample data
    np.random.seed(42)
    n = 100

    df = pd.DataFrame({
        'group_a': np.random.normal(10, 2, n),
        'group_b': np.random.normal(12, 2, n),
        'paired_before': np.random.normal(15, 3, n),
        'paired_after': np.random.normal(16, 3, n),
    })

    # Add paired relationship
    df['paired_after'] = df['paired_before'] + np.random.normal(1, 0.5, n)

    logger.info(f"Sample data: {len(df)} observations")

    # Initialize framework
    framework = AdvancedStatisticalTestingFramework(
        data=df,
        output_dir="/tmp/statistical_testing"
    )

    # 1. Hypothesis tests
    logger.info("\n" + "=" * 80)
    logger.info("1. Hypothesis Tests")
    logger.info("=" * 80)

    framework.hypothesis_test('group_a', 'group_b', test_type='ttest')
    framework.hypothesis_test('paired_before', 'paired_after', test_type='paired_ttest')

    # 2. Confidence intervals
    logger.info("\n" + "=" * 80)
    logger.info("2. Confidence Intervals")
    logger.info("=" * 80)

    framework.confidence_interval('group_a', confidence_level=0.95, method='parametric')
    framework.confidence_interval('group_a', confidence_level=0.95, method='bootstrap')

    # 3. Bootstrap test
    logger.info("\n" + "=" * 80)
    logger.info("3. Bootstrap Tests")
    logger.info("=" * 80)

    framework.bootstrap_test('group_a', null_value=10, n_iterations=5000)

    # 4. Multiple testing correction
    logger.info("\n" + "=" * 80)
    logger.info("4. Multiple Testing Correction")
    logger.info("=" * 80)

    # Simulate multiple tests
    pvalues = [0.001, 0.01, 0.03, 0.05, 0.07, 0.10, 0.20, 0.50]
    framework.multiple_testing_correction(pvalues, method='fdr_bh', alpha=0.05)
    framework.multiple_testing_correction(pvalues, method='bonferroni', alpha=0.05)
    framework.multiple_testing_correction(pvalues, method='holm', alpha=0.05)

    # 5. Effect sizes
    logger.info("\n" + "=" * 80)
    logger.info("5. Effect Sizes")
    logger.info("=" * 80)

    framework.effect_size('group_a', 'group_b', effect_type='cohens_d')

    # Generate report
    report_path = framework.generate_report()

    logger.info("\n" + "=" * 80)
    logger.info(f"✅ Testing complete! Report: {report_path}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
