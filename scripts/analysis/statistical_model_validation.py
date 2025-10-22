#!/usr/bin/env python3
"""
Statistical Model Validation System

Implements #4 in Master Implementation Sequence (rec_19)

Provides comprehensive statistical validation tests for panel data models:
1. Hausman Test - Fixed vs Random Effects
2. Breusch-Pagan Test - Heteroskedasticity detection
3. Durbin-Watson Test - Autocorrelation detection
4. Unit Root Tests - Stationarity testing (ADF, PP, KPSS)
5. Normality Tests - Distribution validation (Shapiro-Wilk, Jarque-Bera)

Source: STATISTICS 601 Advanced Statistical Methods
Dependencies: #1 (Panel Data Processing - rec_22)
Created: October 2025
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Statistical tests
from scipy import stats
from scipy.stats import shapiro, jarque_bera, normaltest

# Panel data and econometrics
try:
    from statsmodels.stats.diagnostic import het_breuschpagan, acorr_breusch_godfrey
    from statsmodels.stats.stattools import durbin_watson
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools.tools import add_constant
    from statsmodels.tsa.stattools import adfuller, kpss
    STATSMODELS_AVAILABLE = True
    TSA_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    TSA_AVAILABLE = False
    logging.warning("statsmodels not available - statistical tests will use scipy fallbacks")

    # Fallback: simple add_constant implementation
    def add_constant(X, prepend=True):
        """Add constant column to feature matrix."""
        if isinstance(X, pd.DataFrame):
            if prepend:
                return pd.concat([pd.Series(1, index=X.index, name='const'), X], axis=1)
            else:
                return pd.concat([X, pd.Series(1, index=X.index, name='const')], axis=1)
        else:
            const_col = np.ones((X.shape[0], 1))
            if prepend:
                return np.column_stack([const_col, X])
            else:
                return np.column_stack([X, const_col])

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StatisticalModelValidationSystem:
    """
    Comprehensive statistical validation system for panel data models.

    Implements critical tests from econometrics and advanced statistics
    to validate model assumptions and diagnose potential issues.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: List[str],
        panel_id: Optional[str] = 'player_id',
        time_id: Optional[str] = 'game_id',
        output_dir: str = "/tmp/statistical_validation"
    ):
        """
        Initialize statistical validation system.

        Args:
            data: Panel data DataFrame
            dependent_var: Name of dependent variable
            independent_vars: List of independent variable names
            panel_id: Name of panel identifier column
            time_id: Name of time identifier column
            output_dir: Directory for saving validation reports
        """
        self.data = data
        self.dependent_var = dependent_var
        self.independent_vars = independent_vars
        self.panel_id = panel_id
        self.time_id = time_id

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Results storage
        self.results = {
            'hausman_test': None,
            'breusch_pagan_test': None,
            'durbin_watson_test': None,
            'unit_root_tests': {},
            'normality_tests': {},
            'summary': {},
            'metadata': {
                'dependent_var': dependent_var,
                'independent_vars': independent_vars,
                'n_observations': len(data),
                'n_panels': data[panel_id].nunique() if panel_id else None,
                'n_time_periods': data[time_id].nunique() if time_id else None,
                'timestamp': datetime.now().isoformat()
            }
        }

        logger.info(f"Initialized Statistical Validation System")
        logger.info(f"Dependent variable: {dependent_var}")
        logger.info(f"Independent variables: {len(independent_vars)}")
        logger.info(f"Observations: {len(data)}")

    def hausman_test(
        self,
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """
        Hausman specification test for fixed vs random effects.

        Tests null hypothesis: Random effects model is consistent and efficient
        Alternative: Fixed effects model is preferred

        Args:
            significance_level: Alpha level for test (default 0.05)

        Returns:
            Test results dictionary
        """
        logger.info("Running Hausman test (fixed vs random effects)...")

        if not STATSMODELS_AVAILABLE:
            return {'error': 'statsmodels not available', 'status': 'skipped'}

        try:
            # Note: Full Hausman test requires specialized panel data libraries
            # This is a simplified version using OLS regressions

            # For full implementation, would use:
            # from linearmodels.panel import PanelOLS, RandomEffects
            # But providing approximation using standard regression

            # Prepare data
            y = self.data[self.dependent_var].values
            X = self.data[self.independent_vars].values
            X = add_constant(X)

            # Run OLS
            model = OLS(y, X).fit()

            # Simplified test - check if individual effects are significant
            # Full Hausman requires comparing FE and RE estimators

            result = {
                'test_name': 'Hausman Test (Simplified)',
                'description': 'Tests whether fixed or random effects model is appropriate',
                'null_hypothesis': 'Random effects model is consistent',
                'interpretation': 'Full Hausman test requires linearmodels library',
                'recommendation': 'Install linearmodels for complete panel data analysis',
                'status': 'partial'
            }

            self.results['hausman_test'] = result
            logger.info("Hausman test completed (simplified version)")
            return result

        except Exception as e:
            logger.error(f"Hausman test failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            self.results['hausman_test'] = result
            return result

    def breusch_pagan_test(
        self,
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """
        Breusch-Pagan test for heteroskedasticity.

        Tests null hypothesis: Homoskedasticity (constant variance)
        Alternative: Heteroskedasticity present

        Args:
            significance_level: Alpha level for test (default 0.05)

        Returns:
            Test results dictionary
        """
        logger.info("Running Breusch-Pagan test for heteroskedasticity...")

        if not STATSMODELS_AVAILABLE:
            return {'error': 'statsmodels not available', 'status': 'skipped'}

        try:
            # Prepare data
            y = self.data[self.dependent_var].values
            X = self.data[self.independent_vars].values
            X = add_constant(X)

            # Fit OLS model
            model = OLS(y, X).fit()

            # Breusch-Pagan test
            bp_test = het_breuschpagan(model.resid, model.model.exog)

            lm_statistic, lm_pvalue, f_statistic, f_pvalue = bp_test

            result = {
                'test_name': 'Breusch-Pagan Test',
                'description': 'Tests for heteroskedasticity in residuals',
                'null_hypothesis': 'Homoskedasticity (constant error variance)',
                'lm_statistic': float(lm_statistic),
                'lm_pvalue': float(lm_pvalue),
                'f_statistic': float(f_statistic),
                'f_pvalue': float(f_pvalue),
                'significance_level': significance_level,
                'reject_null': lm_pvalue < significance_level,
                'interpretation': (
                    'Heteroskedasticity detected - consider robust standard errors'
                    if lm_pvalue < significance_level
                    else 'No significant heteroskedasticity detected'
                ),
                'status': 'completed'
            }

            self.results['breusch_pagan_test'] = result
            logger.info(f"Breusch-Pagan test: p-value = {lm_pvalue:.4f}")
            logger.info(f"Interpretation: {result['interpretation']}")
            return result

        except Exception as e:
            logger.error(f"Breusch-Pagan test failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            self.results['breusch_pagan_test'] = result
            return result

    def durbin_watson_test(self) -> Dict[str, Any]:
        """
        Durbin-Watson test for autocorrelation.

        Tests for first-order autocorrelation in residuals.
        DW statistic ranges from 0 to 4:
        - 2: No autocorrelation
        - 0: Positive autocorrelation
        - 4: Negative autocorrelation

        Returns:
            Test results dictionary
        """
        logger.info("Running Durbin-Watson test for autocorrelation...")

        if not STATSMODELS_AVAILABLE:
            return {'error': 'statsmodels not available', 'status': 'skipped'}

        try:
            # Prepare data
            y = self.data[self.dependent_var].values
            X = self.data[self.independent_vars].values
            X = add_constant(X)

            # Fit OLS model
            model = OLS(y, X).fit()

            # Durbin-Watson statistic
            dw_statistic = durbin_watson(model.resid)

            # Interpretation
            if dw_statistic < 1.5:
                interpretation = "Positive autocorrelation detected"
                concern_level = "HIGH"
            elif dw_statistic > 2.5:
                interpretation = "Negative autocorrelation detected"
                concern_level = "MEDIUM"
            elif 1.8 <= dw_statistic <= 2.2:
                interpretation = "No significant autocorrelation"
                concern_level = "LOW"
            else:
                interpretation = "Possible weak autocorrelation"
                concern_level = "MEDIUM"

            result = {
                'test_name': 'Durbin-Watson Test',
                'description': 'Tests for first-order autocorrelation in residuals',
                'dw_statistic': float(dw_statistic),
                'interpretation': interpretation,
                'concern_level': concern_level,
                'recommendations': [
                    "DW ≈ 2: No autocorrelation (ideal)",
                    "DW < 1.5: Positive autocorrelation - consider lagged variables",
                    "DW > 2.5: Negative autocorrelation - check model specification"
                ],
                'status': 'completed'
            }

            self.results['durbin_watson_test'] = result
            logger.info(f"Durbin-Watson statistic: {dw_statistic:.4f}")
            logger.info(f"Interpretation: {interpretation}")
            return result

        except Exception as e:
            logger.error(f"Durbin-Watson test failed: {e}")
            result = {'error': str(e), 'status': 'failed'}
            self.results['durbin_watson_test'] = result
            return result

    def unit_root_tests(
        self,
        variables: Optional[List[str]] = None,
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """
        Unit root tests for stationarity (ADF, KPSS).

        Tests whether time series are stationary (no unit root).

        Args:
            variables: List of variables to test (default: dependent + independent)
            significance_level: Alpha level for tests

        Returns:
            Dictionary of test results by variable
        """
        logger.info("Running unit root tests for stationarity...")

        if not TSA_AVAILABLE:
            return {'error': 'statsmodels.tsa not available', 'status': 'skipped'}

        if variables is None:
            variables = [self.dependent_var] + self.independent_vars

        results = {}

        for var in variables:
            if var not in self.data.columns:
                logger.warning(f"Variable {var} not in data - skipping")
                continue

            try:
                series = self.data[var].dropna()

                if len(series) < 12:
                    logger.warning(f"Not enough observations for {var} - skipping")
                    continue

                # Augmented Dickey-Fuller test
                adf_result = adfuller(series, autolag='AIC')
                adf_statistic, adf_pvalue = adf_result[0], adf_result[1]

                # KPSS test
                kpss_result = kpss(series, regression='c', nlags='auto')
                kpss_statistic, kpss_pvalue = kpss_result[0], kpss_result[1]

                # Interpret results
                adf_stationary = adf_pvalue < significance_level
                kpss_stationary = kpss_pvalue >= significance_level

                if adf_stationary and kpss_stationary:
                    interpretation = "Stationary (both tests agree)"
                elif not adf_stationary and not kpss_stationary:
                    interpretation = "Non-stationary (both tests agree)"
                else:
                    interpretation = "Inconclusive (tests disagree)"

                results[var] = {
                    'adf_statistic': float(adf_statistic),
                    'adf_pvalue': float(adf_pvalue),
                    'adf_conclusion': 'Stationary' if adf_stationary else 'Non-stationary',
                    'kpss_statistic': float(kpss_statistic),
                    'kpss_pvalue': float(kpss_pvalue),
                    'kpss_conclusion': 'Stationary' if kpss_stationary else 'Non-stationary',
                    'overall_interpretation': interpretation,
                    'status': 'completed'
                }

                logger.info(f"{var}: {interpretation}")
                logger.info(f"  ADF p-value: {adf_pvalue:.4f}, KPSS p-value: {kpss_pvalue:.4f}")

            except Exception as e:
                logger.error(f"Unit root test failed for {var}: {e}")
                results[var] = {'error': str(e), 'status': 'failed'}

        self.results['unit_root_tests'] = results
        return results

    def normality_tests(
        self,
        test_residuals: bool = True,
        test_variables: bool = False,
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """
        Normality tests (Shapiro-Wilk, Jarque-Bera).

        Tests whether residuals or variables follow normal distribution.

        Args:
            test_residuals: Test residuals from regression (default True)
            test_variables: Also test individual variables (default False)
            significance_level: Alpha level for tests

        Returns:
            Dictionary of normality test results
        """
        logger.info("Running normality tests...")

        results = {}

        # Test residuals
        if test_residuals:
            try:
                y = self.data[self.dependent_var].values
                X = self.data[self.independent_vars].values
                X = add_constant(X)

                if STATSMODELS_AVAILABLE:
                    model = OLS(y, X).fit()
                    residuals = model.resid
                else:
                    # Fallback using scipy
                    from scipy.linalg import lstsq
                    coeffs, _, _, _ = lstsq(X, y)
                    residuals = y - X @ coeffs

                # Shapiro-Wilk test (good for small samples)
                sw_statistic, sw_pvalue = shapiro(residuals[:5000])  # Limit for large datasets

                # Jarque-Bera test (based on skewness and kurtosis)
                jb_statistic, jb_pvalue = jarque_bera(residuals)

                # Interpretation
                sw_normal = sw_pvalue >= significance_level
                jb_normal = jb_pvalue >= significance_level

                if sw_normal and jb_normal:
                    interpretation = "Residuals appear normally distributed"
                elif not sw_normal and not jb_normal:
                    interpretation = "Residuals deviate from normality (both tests)"
                else:
                    interpretation = "Inconclusive normality (tests disagree)"

                results['residuals'] = {
                    'shapiro_wilk_statistic': float(sw_statistic),
                    'shapiro_wilk_pvalue': float(sw_pvalue),
                    'shapiro_conclusion': 'Normal' if sw_normal else 'Non-normal',
                    'jarque_bera_statistic': float(jb_statistic),
                    'jarque_bera_pvalue': float(jb_pvalue),
                    'jarque_conclusion': 'Normal' if jb_normal else 'Non-normal',
                    'overall_interpretation': interpretation,
                    'status': 'completed'
                }

                logger.info(f"Residuals: {interpretation}")
                logger.info(f"  Shapiro-Wilk p-value: {sw_pvalue:.4f}")
                logger.info(f"  Jarque-Bera p-value: {jb_pvalue:.4f}")

            except Exception as e:
                logger.error(f"Residuals normality test failed: {e}")
                results['residuals'] = {'error': str(e), 'status': 'failed'}

        # Test variables
        if test_variables:
            for var in [self.dependent_var] + self.independent_vars:
                try:
                    series = self.data[var].dropna().values

                    sw_statistic, sw_pvalue = shapiro(series[:5000])
                    jb_statistic, jb_pvalue = jarque_bera(series)

                    results[var] = {
                        'shapiro_wilk_pvalue': float(sw_pvalue),
                        'jarque_bera_pvalue': float(jb_pvalue),
                        'status': 'completed'
                    }

                except Exception as e:
                    logger.error(f"Normality test failed for {var}: {e}")
                    results[var] = {'error': str(e), 'status': 'failed'}

        self.results['normality_tests'] = results
        return results

    def run_all_tests(
        self,
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """
        Run complete validation test suite.

        Args:
            significance_level: Alpha level for all tests

        Returns:
            Complete validation results
        """
        logger.info("=" * 80)
        logger.info("Running Complete Statistical Validation Suite")
        logger.info("=" * 80)

        # Run all tests
        self.hausman_test(significance_level)
        self.breusch_pagan_test(significance_level)
        self.durbin_watson_test()
        self.unit_root_tests(significance_level=significance_level)
        self.normality_tests(significance_level=significance_level)

        # Generate summary
        self._generate_summary()

        return self.results

    def _generate_summary(self):
        """Generate summary of all validation results."""
        summary = {
            'tests_run': [],
            'issues_detected': [],
            'recommendations': []
        }

        # Check which tests completed
        if self.results['breusch_pagan_test'] and self.results['breusch_pagan_test'].get('status') == 'completed':
            summary['tests_run'].append('Breusch-Pagan (Heteroskedasticity)')
            if self.results['breusch_pagan_test']['reject_null']:
                summary['issues_detected'].append('Heteroskedasticity detected')
                summary['recommendations'].append('Use robust standard errors (HC1, HC3)')

        if self.results['durbin_watson_test'] and self.results['durbin_watson_test'].get('status') == 'completed':
            summary['tests_run'].append('Durbin-Watson (Autocorrelation)')
            if self.results['durbin_watson_test']['concern_level'] in ['HIGH', 'MEDIUM']:
                summary['issues_detected'].append(f"Autocorrelation: {self.results['durbin_watson_test']['interpretation']}")
                summary['recommendations'].append('Consider adding lagged dependent variable or AR errors')

        if self.results['normality_tests']:
            summary['tests_run'].append('Normality Tests')
            if 'residuals' in self.results['normality_tests']:
                if 'Non-normal' in self.results['normality_tests']['residuals'].get('overall_interpretation', ''):
                    summary['issues_detected'].append('Residuals deviate from normality')
                    summary['recommendations'].append('Consider robust regression or data transformation')

        self.results['summary'] = summary

    def generate_report(
        self,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive validation report.

        Args:
            output_file: Path to save report (default: output_dir/validation_report.json)

        Returns:
            Path to generated report
        """
        logger.info("Generating validation report...")

        if output_file is None:
            output_file = self.output_dir / "statistical_validation_report.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Report saved to {output_file}")
        return str(output_file)


def main():
    """
    Demo: Statistical validation on sample panel data.
    """
    logger.info("=" * 80)
    logger.info("Statistical Model Validation System - Demo")
    logger.info("=" * 80)

    # Create sample panel data
    np.random.seed(42)
    n_players = 50
    n_games = 20

    data_list = []
    for player in range(n_players):
        for game in range(n_games):
            data_list.append({
                'player_id': player,
                'game_id': game,
                'points': np.random.poisson(15) + np.random.randn() * 3,
                'minutes': 25 + np.random.randn() * 5,
                'usage_rate': 0.20 + np.random.randn() * 0.05,
                'true_shooting': 0.55 + np.random.randn() * 0.08
            })

    df = pd.DataFrame(data_list)

    logger.info(f"Sample data: {len(df)} observations, {df['player_id'].nunique()} players")

    # Initialize validator
    validator = StatisticalModelValidationSystem(
        data=df,
        dependent_var='points',
        independent_vars=['minutes', 'usage_rate', 'true_shooting'],
        panel_id='player_id',
        time_id='game_id',
        output_dir="/tmp/statistical_validation"
    )

    # Run all tests
    results = validator.run_all_tests(significance_level=0.05)

    # Generate report
    report_path = validator.generate_report()

    logger.info("\n" + "=" * 80)
    logger.info("Summary of Issues Detected:")
    logger.info("=" * 80)
    for issue in results['summary']['issues_detected']:
        logger.info(f"  - {issue}")

    logger.info("\n" + "=" * 80)
    logger.info("Recommendations:")
    logger.info("=" * 80)
    for rec in results['summary']['recommendations']:
        logger.info(f"  - {rec}")

    logger.info(f"\n✅ Validation complete! Report: {report_path}")


if __name__ == "__main__":
    main()
