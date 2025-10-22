#!/usr/bin/env python3
"""
Implementation Script: Data Drift Detection

Recommendation ID: ml_systems_2
Priority: CRITICAL
Source Book: Designing Machine Learning Systems, Econometric Analysis
Generated: 2025-10-15T21:01:26.113762
Implemented: 2025-10-15

Description:
From ML Systems book: Ch 8
- Detect distribution shifts in input features
- Alert when data drift exceeds thresholds
- Multiple statistical tests (KS, Chi-squared, PSI)
- Distance metrics (KL divergence, Wasserstein)
- Integration with MLflow for tracking

Expected Impact: HIGH - Detect distribution shifts, prevent model degradation
Time Estimate: 2 days

Prerequisites:
- pip install scipy numpy pandas
- Reference dataset for baseline comparison
- MLflow for metric tracking (optional)
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path
import warnings

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Scientific computing imports (with graceful degradation)
try:
    import numpy as np
    import pandas as pd
    from scipy import stats
    from scipy.spatial.distance import jensenshannon

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning(
        "scipy/numpy/pandas not installed. Run: pip install scipy numpy pandas"
    )

# MLflow import (optional)
try:
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


class DataDriftDetection:
    """
    Implementation of: Data Drift Detection

    Implements data drift detection system as described in
    "Designing Machine Learning Systems" (Ch 8: Data Distribution Shifts)

    Features:
    - Multiple drift detection methods:
      * Kolmogorov-Smirnov test (numerical features)
      * Chi-squared test (categorical features)
      * Population Stability Index (PSI)
      * Jensen-Shannon divergence
      * Wasserstein distance
    - Reference dataset management
    - Configurable alert thresholds
    - MLflow integration for tracking
    - Per-feature and aggregate drift scores

    Architecture:
    - Reference data: Baseline distribution (training data)
    - Current data: Recent production data
    - Comparison: Statistical tests + distance metrics
    - Alerts: Threshold-based notifications
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DataDriftDetection.

        Args:
            config: Configuration dictionary with:
                - reference_data: Path to reference dataset or DataFrame
                - alert_threshold_psi: PSI threshold for drift alert (default: 0.2)
                - alert_threshold_ks: KS statistic threshold (default: 0.1)
                - alert_threshold_chi2: Chi-squared p-value threshold (default: 0.05)
                - features_to_monitor: List of feature names (optional, monitors all if not specified)
                - mlflow_tracking: Enable MLflow tracking (default: False)
        """
        self.config = config or {}
        self.setup_complete = False
        self.reference_data = None
        self.feature_stats = {}
        self.drift_results = {}

        # Thresholds for drift detection
        self.psi_threshold = self.config.get("alert_threshold_psi", 0.2)
        self.ks_threshold = self.config.get("alert_threshold_ks", 0.1)
        self.chi2_pvalue_threshold = self.config.get("alert_threshold_chi2", 0.05)

        logger.info(f"Initializing DataDriftDetection...")
        logger.info(f"  PSI Threshold: {self.psi_threshold}")
        logger.info(f"  KS Threshold: {self.ks_threshold}")
        logger.info(f"  Chi-squared p-value threshold: {self.chi2_pvalue_threshold}")

    def setup(self) -> bool:
        """
        Set up data drift detection infrastructure.

        Sets up:
        1. Load reference dataset
        2. Calculate reference statistics
        3. Identify feature types (numerical/categorical)
        4. Initialize MLflow tracking (if enabled)

        Returns:
            bool: True if setup successful
        """
        try:
            logger.info("Setting up DataDriftDetection...")

            if not SCIPY_AVAILABLE:
                logger.error("scipy/numpy/pandas not installed")
                return False

            # 1. Load reference data
            reference_data_config = self.config.get("reference_data")
            if reference_data_config is None:
                logger.warning(
                    "No reference data provided, will generate synthetic data for demo"
                )
                # Generate synthetic reference data for demonstration
                self.reference_data = self._generate_demo_data(1000, seed=42)
            elif isinstance(reference_data_config, str):
                # Load from file
                if reference_data_config.endswith(".csv"):
                    self.reference_data = pd.read_csv(reference_data_config)
                elif reference_data_config.endswith(".parquet"):
                    self.reference_data = pd.read_parquet(reference_data_config)
                else:
                    logger.error(f"Unsupported file format: {reference_data_config}")
                    return False
                logger.info(f"  Loaded reference data from {reference_data_config}")
            elif isinstance(reference_data_config, pd.DataFrame):
                self.reference_data = reference_data_config
                logger.info("  Using provided DataFrame as reference data")
            else:
                logger.error("Invalid reference_data configuration")
                return False

            logger.info(f"  Reference data shape: {self.reference_data.shape}")

            # 2. Identify feature types and calculate statistics
            self.features_to_monitor = self.config.get("features_to_monitor")
            if self.features_to_monitor is None:
                self.features_to_monitor = list(self.reference_data.columns)

            logger.info(f"  Monitoring {len(self.features_to_monitor)} features")

            # Calculate reference statistics for each feature
            for feature in self.features_to_monitor:
                if feature not in self.reference_data.columns:
                    logger.warning(
                        f"Feature '{feature}' not in reference data, skipping"
                    )
                    continue

                feature_data = self.reference_data[feature]

                # Determine if numerical or categorical
                if pd.api.types.is_numeric_dtype(feature_data):
                    feature_type = "numerical"
                    stats = {
                        "mean": float(feature_data.mean()),
                        "std": float(feature_data.std()),
                        "min": float(feature_data.min()),
                        "max": float(feature_data.max()),
                        "quantiles": feature_data.quantile([0.25, 0.5, 0.75]).to_dict(),
                    }
                else:
                    feature_type = "categorical"
                    value_counts = feature_data.value_counts(normalize=True)
                    stats = {
                        "categories": value_counts.index.tolist(),
                        "frequencies": value_counts.values.tolist(),
                    }

                self.feature_stats[feature] = {"type": feature_type, "stats": stats}

            logger.info(
                f"  Calculated statistics for {len(self.feature_stats)} features"
            )

            # 3. Initialize MLflow tracking if enabled
            if self.config.get("mlflow_tracking", False) and MLFLOW_AVAILABLE:
                mlflow.set_experiment(
                    self.config.get("experiment_name", "data-drift-monitoring")
                )
                logger.info("  MLflow tracking enabled")

            self.setup_complete = True
            logger.info("✅ Data drift detection setup complete")
            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def validate_prerequisites(self) -> bool:
        """
        Validate that all prerequisites are met.

        Checks:
        1. scipy/numpy/pandas installed
        2. Reference data available (or can generate demo data)
        3. Python version compatibility

        Returns:
            bool: True if all prerequisites met
        """
        logger.info("Validating prerequisites...")

        all_valid = True

        # 1. Check scipy/numpy/pandas
        if not SCIPY_AVAILABLE:
            logger.error("❌ scipy/numpy/pandas not installed")
            logger.error("   Install: pip install scipy numpy pandas")
            all_valid = False
        else:
            logger.info("✅ scipy/numpy/pandas installed")

        # 2. Check Python version
        import sys

        if sys.version_info >= (3, 7):
            logger.info(
                f"✅ Python {sys.version_info.major}.{sys.version_info.minor} (compatible)"
            )
        else:
            logger.warning(
                f"⚠️  Python {sys.version_info.major}.{sys.version_info.minor} (recommend 3.7+)"
            )

        # 3. Check MLflow if tracking enabled
        if self.config.get("mlflow_tracking", False):
            if MLFLOW_AVAILABLE:
                logger.info("✅ MLflow available for tracking")
            else:
                logger.warning("⚠️  MLflow not available (tracking disabled)")

        if all_valid:
            logger.info("✅ All prerequisites validated")
        else:
            logger.error("❌ Some prerequisites not met")

        return all_valid

    def _generate_demo_data(self, n_samples: int, seed: int = 42) -> pd.DataFrame:
        """
        Generate synthetic demo data for testing.

        Args:
            n_samples: Number of samples to generate
            seed: Random seed for reproducibility

        Returns:
            DataFrame with synthetic features
        """
        np.random.seed(seed)

        data = {
            "team_score": np.random.normal(110, 15, n_samples),
            "opponent_score": np.random.normal(108, 15, n_samples),
            "field_goal_pct": np.random.uniform(0.40, 0.55, n_samples),
            "three_point_pct": np.random.uniform(0.30, 0.45, n_samples),
            "free_throw_pct": np.random.uniform(0.70, 0.85, n_samples),
            "rebounds": np.random.poisson(45, n_samples),
            "assists": np.random.poisson(25, n_samples),
            "home_away": np.random.choice(["home", "away"], n_samples),
            "day_of_week": np.random.choice(
                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], n_samples
            ),
        }

        return pd.DataFrame(data)

    def calculate_psi(
        self, reference: np.ndarray, current: np.ndarray, bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI).

        PSI measures the shift in distribution between reference and current data.
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change (alert)

        Args:
            reference: Reference data array
            current: Current data array
            bins: Number of bins for discretization

        Returns:
            float: PSI score
        """
        # Create bins based on reference data
        bin_edges = np.histogram_bin_edges(reference, bins=bins)

        # Calculate frequencies for reference and current
        ref_freq, _ = np.histogram(reference, bins=bin_edges)
        cur_freq, _ = np.histogram(current, bins=bin_edges)

        # Convert to proportions (add small epsilon to avoid division by zero)
        epsilon = 1e-10
        ref_prop = (ref_freq + epsilon) / (len(reference) + epsilon * bins)
        cur_prop = (cur_freq + epsilon) / (len(current) + epsilon * bins)

        # Calculate PSI
        psi = np.sum((cur_prop - ref_prop) * np.log(cur_prop / ref_prop))

        return float(psi)

    def calculate_ks_test(
        self, reference: np.ndarray, current: np.ndarray
    ) -> Tuple[float, float]:
        """
        Perform Kolmogorov-Smirnov test.

        Tests whether two samples come from the same distribution.

        Args:
            reference: Reference data array
            current: Current data array

        Returns:
            tuple: (KS statistic, p-value)
        """
        statistic, pvalue = stats.ks_2samp(reference, current)
        return float(statistic), float(pvalue)

    def calculate_chi_squared(
        self, reference: pd.Series, current: pd.Series
    ) -> Tuple[float, float]:
        """
        Perform Chi-squared test for categorical features.

        Args:
            reference: Reference categorical data
            current: Current categorical data

        Returns:
            tuple: (Chi-squared statistic, p-value)
        """
        # Get all unique categories
        all_categories = list(set(reference.unique()) | set(current.unique()))

        # Count frequencies
        ref_counts = reference.value_counts().reindex(all_categories, fill_value=0)
        cur_counts = current.value_counts().reindex(all_categories, fill_value=0)

        # Perform chi-squared test
        chi2, pvalue, _, _ = stats.chi2_contingency([ref_counts, cur_counts])

        return float(chi2), float(pvalue)

    def calculate_wasserstein_distance(
        self, reference: np.ndarray, current: np.ndarray
    ) -> float:
        """
        Calculate Wasserstein distance (Earth Mover's Distance).

        Measures the minimum cost to transform one distribution into another.

        Args:
            reference: Reference data array
            current: Current data array

        Returns:
            float: Wasserstein distance
        """
        distance = stats.wasserstein_distance(reference, current)
        return float(distance)

    def calculate_jensen_shannon_divergence(
        self, reference: np.ndarray, current: np.ndarray, bins: int = 10
    ) -> float:
        """
        Calculate Jensen-Shannon divergence.

        Symmetric measure of similarity between two probability distributions.

        Args:
            reference: Reference data array
            current: Current data array
            bins: Number of bins for discretization

        Returns:
            float: Jensen-Shannon divergence
        """
        # Create bins and calculate histograms
        bin_edges = np.histogram_bin_edges(reference, bins=bins)
        ref_hist, _ = np.histogram(reference, bins=bin_edges)
        cur_hist, _ = np.histogram(current, bins=bin_edges)

        # Normalize to probabilities
        ref_prob = ref_hist / ref_hist.sum()
        cur_prob = cur_hist / cur_hist.sum()

        # Calculate JS divergence
        js_div = jensenshannon(ref_prob, cur_prob)

        return float(js_div)

    def detect_drift(self, current_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect data drift by comparing current data to reference data.

        Performs multiple statistical tests for each feature:
        - Numerical: KS test, PSI, Wasserstein distance, Jensen-Shannon divergence
        - Categorical: Chi-squared test

        Args:
            current_data: DataFrame with current/production data

        Returns:
            dict: Drift detection results with per-feature and aggregate scores
        """
        if not self.setup_complete:
            raise RuntimeError("Setup must be completed before drift detection")

        logger.info(f"Detecting drift for {len(self.features_to_monitor)} features...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "features": {},
            "alerts": [],
            "summary": {},
        }

        features_with_drift = 0
        total_features_checked = 0

        for feature in self.features_to_monitor:
            if feature not in self.feature_stats:
                continue

            if feature not in current_data.columns:
                logger.warning(f"Feature '{feature}' not in current data, skipping")
                continue

            feature_type = self.feature_stats[feature]["type"]
            ref_data = self.reference_data[feature]
            cur_data = current_data[feature]

            total_features_checked += 1
            feature_result = {"type": feature_type}

            if feature_type == "numerical":
                # Remove NaN values
                ref_clean = ref_data.dropna().values
                cur_clean = cur_data.dropna().values

                # PSI
                psi = self.calculate_psi(ref_clean, cur_clean)
                feature_result["psi"] = psi

                # KS test
                ks_stat, ks_pvalue = self.calculate_ks_test(ref_clean, cur_clean)
                feature_result["ks_statistic"] = ks_stat
                feature_result["ks_pvalue"] = ks_pvalue

                # Wasserstein distance
                wasserstein = self.calculate_wasserstein_distance(ref_clean, cur_clean)
                feature_result["wasserstein_distance"] = wasserstein

                # Jensen-Shannon divergence
                js_div = self.calculate_jensen_shannon_divergence(ref_clean, cur_clean)
                feature_result["jensen_shannon_divergence"] = js_div

                # Check thresholds
                drift_detected = (
                    psi >= self.psi_threshold or ks_stat >= self.ks_threshold
                )
                feature_result["drift_detected"] = drift_detected

                if drift_detected:
                    features_with_drift += 1
                    alert_msg = f"Drift detected in '{feature}': PSI={psi:.3f}, KS={ks_stat:.3f}"
                    results["alerts"].append(alert_msg)
                    logger.warning(f"  ⚠️  {alert_msg}")

            elif feature_type == "categorical":
                # Chi-squared test
                chi2, pvalue = self.calculate_chi_squared(ref_data, cur_data)
                feature_result["chi2_statistic"] = chi2
                feature_result["chi2_pvalue"] = pvalue

                # Check threshold
                drift_detected = pvalue < self.chi2_pvalue_threshold
                feature_result["drift_detected"] = drift_detected

                if drift_detected:
                    features_with_drift += 1
                    alert_msg = f"Drift detected in '{feature}': Chi²={chi2:.3f}, p={pvalue:.4f}"
                    results["alerts"].append(alert_msg)
                    logger.warning(f"  ⚠️  {alert_msg}")

            results["features"][feature] = feature_result

        # Summary statistics
        results["summary"] = {
            "total_features_checked": total_features_checked,
            "features_with_drift": features_with_drift,
            "drift_percentage": (
                (features_with_drift / total_features_checked * 100)
                if total_features_checked > 0
                else 0
            ),
            "overall_drift_detected": features_with_drift > 0,
        }

        logger.info(
            f"  Drift detected in {features_with_drift}/{total_features_checked} features ({results['summary']['drift_percentage']:.1f}%)"
        )

        return results

    def execute(self) -> Dict[str, Any]:
        """
        Execute data drift detection demonstration.

        Demonstrates:
        1. Setup with reference data
        2. Generate current data with intentional drift
        3. Detect drift using multiple methods
        4. Log results to MLflow (if enabled)
        5. Generate drift report

        Returns:
            dict: Execution results and metrics
        """
        if not self.setup_complete:
            raise RuntimeError("Setup must be completed before execution")

        logger.info("Executing DataDriftDetection demonstration...")
        start_time = datetime.now()

        try:
            # Generate current data with intentional drift for demonstration
            logger.info("  Generating current data with drift...")
            current_data = self._generate_demo_data(500, seed=99)

            # Introduce drift in some features
            current_data["team_score"] = current_data["team_score"] + 5  # Mean shift
            current_data["field_goal_pct"] = (
                current_data["field_goal_pct"] * 1.1
            )  # Scale change
            # Change distribution for categorical
            current_data["home_away"] = np.random.choice(
                ["home", "away"], 500, p=[0.7, 0.3]
            )

            logger.info("  Detecting drift...")
            drift_results = self.detect_drift(current_data)

            # Log to MLflow if enabled
            if self.config.get("mlflow_tracking", False) and MLFLOW_AVAILABLE:
                with mlflow.start_run(run_name="drift-detection"):
                    mlflow.log_metrics(
                        {
                            "features_with_drift": drift_results["summary"][
                                "features_with_drift"
                            ],
                            "drift_percentage": drift_results["summary"][
                                "drift_percentage"
                            ],
                        }
                    )
                    mlflow.log_dict(drift_results, "drift_report.json")
                    logger.info("  Logged results to MLflow")

            execution_time = (datetime.now() - start_time).total_seconds()

            results = {
                "success": True,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "drift_results": drift_results,
                "reference_data_shape": self.reference_data.shape,
                "current_data_shape": current_data.shape,
                "features_monitored": len(self.features_to_monitor),
            }

            logger.info(f"✅ Execution completed in {execution_time:.2f}s")
            if drift_results["summary"]["overall_drift_detected"]:
                logger.warning(
                    f"   ⚠️  DRIFT DETECTED in {drift_results['summary']['features_with_drift']} features"
                )
            else:
                logger.info("   ✅ No significant drift detected")

            return results

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    def cleanup(self):
        """
        Clean up resources and log final statistics.

        Logs:
        - Total drift detection runs
        - Final statistics summary
        - Resource cleanup status
        """
        logger.info("Cleaning up resources...")

        try:
            # Log drift detection statistics if available
            if self.drift_results:
                logger.info("  Drift Detection Summary:")
                logger.info(
                    f"    Total features monitored: {len(self.features_to_monitor)}"
                )
                logger.info(
                    f"    Reference data samples: {len(self.reference_data) if self.reference_data is not None else 0}"
                )
                logger.info(f"    Feature types tracked: {len(self.feature_stats)}")

                # Log threshold configuration
                logger.info("  Thresholds:")
                logger.info(f"    PSI: {self.psi_threshold}")
                logger.info(f"    KS: {self.ks_threshold}")
                logger.info(f"    Chi-squared p-value: {self.chi2_pvalue_threshold}")

            # Clear large data structures to free memory
            if self.reference_data is not None:
                logger.info("  Clearing reference data from memory")
                self.reference_data = None

            if self.feature_stats:
                logger.info(
                    f"  Clearing feature statistics ({len(self.feature_stats)} features)"
                )
                self.feature_stats.clear()

            if self.drift_results:
                logger.info("  Clearing drift results")
                self.drift_results.clear()

            logger.info("✅ Cleanup complete")

        except Exception as e:
            logger.warning(f"Cleanup encountered error (non-fatal): {e}")


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info(f"Starting: Data Drift Detection")
    logger.info("=" * 80)

    # Load configuration
    config_file = os.path.join(os.path.dirname(__file__), "config.json")

    config = {}
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)

    # Initialize and execute
    implementation = DataDriftDetection(config)

    # Validate prerequisites
    if not implementation.validate_prerequisites():
        logger.error("Prerequisites not met. Exiting.")
        sys.exit(1)

    # Setup
    if not implementation.setup():
        logger.error("Setup failed. Exiting.")
        sys.exit(1)

    # Execute
    results = implementation.execute()

    # Cleanup
    implementation.cleanup()

    # Report results
    logger.info("=" * 80)
    logger.info("Results:")
    logger.info(json.dumps(results, indent=2))
    logger.info("=" * 80)

    if results.get("success"):
        logger.info("✅ Implementation completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Implementation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
