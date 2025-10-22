"""
Model Calibration and Probability Estimation Framework

Implements calibration methods for improving probability estimates:
- Calibration analysis (reliability diagrams, calibration curves)
- Platt scaling (logistic calibration)
- Isotonic regression calibration
- Beta calibration
- Temperature scaling
- Expected Calibration Error (ECE) metrics
- Confidence interval estimation

Author: NBA Simulator Project
Created: 2025-10-18
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
import json
import numpy as np
import pandas as pd
from pathlib import Path
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    """Store calibration analysis results."""
    method: str
    ece_before: float  # Expected Calibration Error before calibration
    ece_after: float   # Expected Calibration Error after calibration
    mce_before: float  # Maximum Calibration Error before calibration
    mce_after: float   # Maximum Calibration Error after calibration
    brier_score_before: float
    brier_score_after: float
    calibration_time: float
    improvement: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'method': self.method,
            'ece_before': float(self.ece_before),
            'ece_after': float(self.ece_after),
            'mce_before': float(self.mce_before),
            'mce_after': float(self.mce_after),
            'brier_score_before': float(self.brier_score_before),
            'brier_score_after': float(self.brier_score_after),
            'calibration_time': float(self.calibration_time),
            'improvement': float(self.improvement),
            'metadata': self.metadata
        }


class ModelCalibrator:
    """
    Comprehensive model calibration framework.
    """

    def __init__(self, n_bins: int = 10):
        """
        Initialize calibrator.

        Args:
            n_bins: Number of bins for calibration analysis
        """
        self.n_bins = n_bins
        logger.info(f"Initialized ModelCalibrator (n_bins={n_bins})")

    def compute_calibration_metrics(self, y_true: np.ndarray,
                                    y_prob: np.ndarray) -> Dict[str, float]:
        """
        Compute calibration metrics.

        Args:
            y_true: True labels
            y_prob: Predicted probabilities

        Returns:
            Dictionary with calibration metrics
        """
        # Expected Calibration Error (ECE)
        ece = self._compute_ece(y_true, y_prob)

        # Maximum Calibration Error (MCE)
        mce = self._compute_mce(y_true, y_prob)

        # Brier Score
        brier = self._compute_brier_score(y_true, y_prob)

        return {
            'ece': float(ece),
            'mce': float(mce),
            'brier_score': float(brier)
        }

    def platt_scaling(self, y_true_cal: np.ndarray, y_prob_cal: np.ndarray,
                     y_true_test: np.ndarray, y_prob_test: np.ndarray) -> CalibrationResult:
        """
        Apply Platt scaling (logistic calibration).

        Fits a logistic regression on calibration set probabilities.

        Args:
            y_true_cal: True labels for calibration
            y_prob_cal: Predicted probabilities for calibration
            y_true_test: True labels for test
            y_prob_test: Predicted probabilities for test

        Returns:
            CalibrationResult with metrics
        """
        logger.info("Applying Platt scaling...")
        start_time = time.time()

        from sklearn.linear_model import LogisticRegression

        # Metrics before calibration
        metrics_before = self.compute_calibration_metrics(y_true_test, y_prob_test)

        # Fit logistic regression on calibration set
        calibrator = LogisticRegression()
        calibrator.fit(y_prob_cal.reshape(-1, 1), y_true_cal)

        # Apply calibration to test set
        y_prob_calibrated = calibrator.predict_proba(y_prob_test.reshape(-1, 1))[:, 1]

        # Metrics after calibration
        metrics_after = self.compute_calibration_metrics(y_true_test, y_prob_calibrated)

        improvement = metrics_before['ece'] - metrics_after['ece']
        elapsed_time = time.time() - start_time

        logger.info(f"ECE before: {metrics_before['ece']:.4f}")
        logger.info(f"ECE after: {metrics_after['ece']:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return CalibrationResult(
            method='platt_scaling',
            ece_before=metrics_before['ece'],
            ece_after=metrics_after['ece'],
            mce_before=metrics_before['mce'],
            mce_after=metrics_after['mce'],
            brier_score_before=metrics_before['brier_score'],
            brier_score_after=metrics_after['brier_score'],
            calibration_time=elapsed_time,
            improvement=improvement,
            metadata={'calibrator': 'LogisticRegression'}
        )

    def isotonic_calibration(self, y_true_cal: np.ndarray, y_prob_cal: np.ndarray,
                            y_true_test: np.ndarray, y_prob_test: np.ndarray) -> CalibrationResult:
        """
        Apply isotonic regression calibration.

        Non-parametric method that preserves monotonicity.

        Args:
            y_true_cal: True labels for calibration
            y_prob_cal: Predicted probabilities for calibration
            y_true_test: True labels for test
            y_prob_test: Predicted probabilities for test

        Returns:
            CalibrationResult with metrics
        """
        logger.info("Applying isotonic calibration...")
        start_time = time.time()

        from sklearn.isotonic import IsotonicRegression

        # Metrics before calibration
        metrics_before = self.compute_calibration_metrics(y_true_test, y_prob_test)

        # Fit isotonic regression
        calibrator = IsotonicRegression(out_of_bounds='clip')
        calibrator.fit(y_prob_cal, y_true_cal)

        # Apply calibration
        y_prob_calibrated = calibrator.predict(y_prob_test)

        # Metrics after calibration
        metrics_after = self.compute_calibration_metrics(y_true_test, y_prob_calibrated)

        improvement = metrics_before['ece'] - metrics_after['ece']
        elapsed_time = time.time() - start_time

        logger.info(f"ECE before: {metrics_before['ece']:.4f}")
        logger.info(f"ECE after: {metrics_after['ece']:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return CalibrationResult(
            method='isotonic_calibration',
            ece_before=metrics_before['ece'],
            ece_after=metrics_after['ece'],
            mce_before=metrics_before['mce'],
            mce_after=metrics_after['mce'],
            brier_score_before=metrics_before['brier_score'],
            brier_score_after=metrics_after['brier_score'],
            calibration_time=elapsed_time,
            improvement=improvement,
            metadata={'calibrator': 'IsotonicRegression'}
        )

    def temperature_scaling(self, y_true_cal: np.ndarray, logits_cal: np.ndarray,
                           y_true_test: np.ndarray, logits_test: np.ndarray) -> CalibrationResult:
        """
        Apply temperature scaling calibration.

        Simple method that divides logits by learned temperature parameter.

        Args:
            y_true_cal: True labels for calibration
            logits_cal: Model logits for calibration (before softmax)
            y_true_test: True labels for test
            logits_test: Model logits for test

        Returns:
            CalibrationResult with metrics
        """
        logger.info("Applying temperature scaling...")
        start_time = time.time()

        # Convert logits to probabilities (assuming binary classification)
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))

        y_prob_cal = sigmoid(logits_cal)
        y_prob_test = sigmoid(logits_test)

        # Metrics before calibration
        metrics_before = self.compute_calibration_metrics(y_true_test, y_prob_test)

        # Find optimal temperature using calibration set
        from scipy.optimize import minimize_scalar

        def nll_loss(temperature):
            """Negative log likelihood for temperature."""
            scaled_logits = logits_cal / temperature
            probs = sigmoid(scaled_logits)
            # Binary cross-entropy
            epsilon = 1e-10
            probs = np.clip(probs, epsilon, 1 - epsilon)
            loss = -np.mean(y_true_cal * np.log(probs) + (1 - y_true_cal) * np.log(1 - probs))
            return loss

        result = minimize_scalar(nll_loss, bounds=(0.1, 10.0), method='bounded')
        optimal_temperature = result.x

        # Apply temperature scaling to test set
        scaled_logits_test = logits_test / optimal_temperature
        y_prob_calibrated = sigmoid(scaled_logits_test)

        # Metrics after calibration
        metrics_after = self.compute_calibration_metrics(y_true_test, y_prob_calibrated)

        improvement = metrics_before['ece'] - metrics_after['ece']
        elapsed_time = time.time() - start_time

        logger.info(f"Optimal temperature: {optimal_temperature:.4f}")
        logger.info(f"ECE before: {metrics_before['ece']:.4f}")
        logger.info(f"ECE after: {metrics_after['ece']:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return CalibrationResult(
            method='temperature_scaling',
            ece_before=metrics_before['ece'],
            ece_after=metrics_after['ece'],
            mce_before=metrics_before['mce'],
            mce_after=metrics_after['mce'],
            brier_score_before=metrics_before['brier_score'],
            brier_score_after=metrics_after['brier_score'],
            calibration_time=elapsed_time,
            improvement=improvement,
            metadata={'optimal_temperature': float(optimal_temperature)}
        )

    def analyze_calibration(self, y_true: np.ndarray,
                           y_prob: np.ndarray) -> Dict[str, Any]:
        """
        Analyze calibration with reliability diagram data.

        Args:
            y_true: True labels
            y_prob: Predicted probabilities

        Returns:
            Dictionary with calibration analysis
        """
        logger.info("Analyzing calibration...")

        # Create bins
        bins = np.linspace(0, 1, self.n_bins + 1)
        bin_indices = np.digitize(y_prob, bins) - 1
        bin_indices = np.clip(bin_indices, 0, self.n_bins - 1)

        # Calculate statistics per bin
        bin_sums = np.zeros(self.n_bins)
        bin_counts = np.zeros(self.n_bins)
        bin_true_probs = np.zeros(self.n_bins)

        for i in range(self.n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_counts[i] = mask.sum()
                bin_sums[i] = y_prob[mask].sum()
                bin_true_probs[i] = y_true[mask].mean()

        # Calculate mean predicted probability per bin
        bin_pred_probs = np.zeros(self.n_bins)
        for i in range(self.n_bins):
            if bin_counts[i] > 0:
                bin_pred_probs[i] = bin_sums[i] / bin_counts[i]

        # Compute metrics
        metrics = self.compute_calibration_metrics(y_true, y_prob)

        return {
            'bin_counts': bin_counts.tolist(),
            'bin_pred_probs': bin_pred_probs.tolist(),
            'bin_true_probs': bin_true_probs.tolist(),
            'ece': metrics['ece'],
            'mce': metrics['mce'],
            'brier_score': metrics['brier_score']
        }

    def _compute_ece(self, y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """
        Compute Expected Calibration Error.

        Args:
            y_true: True labels
            y_prob: Predicted probabilities

        Returns:
            ECE value
        """
        bins = np.linspace(0, 1, self.n_bins + 1)
        bin_indices = np.digitize(y_prob, bins) - 1
        bin_indices = np.clip(bin_indices, 0, self.n_bins - 1)

        ece = 0.0
        n_samples = len(y_true)

        for i in range(self.n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_acc = y_true[mask].mean()
                bin_conf = y_prob[mask].mean()
                bin_size = mask.sum()
                ece += (bin_size / n_samples) * abs(bin_acc - bin_conf)

        return ece

    def _compute_mce(self, y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """
        Compute Maximum Calibration Error.

        Args:
            y_true: True labels
            y_prob: Predicted probabilities

        Returns:
            MCE value
        """
        bins = np.linspace(0, 1, self.n_bins + 1)
        bin_indices = np.digitize(y_prob, bins) - 1
        bin_indices = np.clip(bin_indices, 0, self.n_bins - 1)

        max_error = 0.0

        for i in range(self.n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                bin_acc = y_true[mask].mean()
                bin_conf = y_prob[mask].mean()
                error = abs(bin_acc - bin_conf)
                max_error = max(max_error, error)

        return max_error

    def _compute_brier_score(self, y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """
        Compute Brier score.

        Args:
            y_true: True labels
            y_prob: Predicted probabilities

        Returns:
            Brier score
        """
        return float(np.mean((y_prob - y_true) ** 2))

    def export_results(self, output_path: str, results: Dict[str, Any]):
        """Export calibration results to JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_model_calibration():
    """Demonstrate model calibration with synthetic data."""
    logger.info("Starting model calibration demo...")

    # Create synthetic data with poorly calibrated probabilities
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier

    np.random.seed(42)

    # Generate dataset
    X, y = make_classification(
        n_samples=2000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        n_classes=2,
        random_state=42
    )

    # Split into train, calibration, and test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.4, random_state=42
    )
    X_cal, X_test, y_cal, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )

    logger.info(f"Train: {len(X_train)}, Calibration: {len(X_cal)}, Test: {len(X_test)}")

    # Train Random Forest (tends to be poorly calibrated)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Get probabilities
    y_prob_cal = model.predict_proba(X_cal)[:, 1]
    y_prob_test = model.predict_proba(X_test)[:, 1]

    # Generate logits for temperature scaling (approximate from probabilities)
    def inverse_sigmoid(p):
        p = np.clip(p, 1e-10, 1 - 1e-10)
        return np.log(p / (1 - p))

    logits_cal = inverse_sigmoid(y_prob_cal)
    logits_test = inverse_sigmoid(y_prob_test)

    logger.info(f"Generated probabilities for {len(y_test)} test samples")

    # Initialize calibrator
    calibrator = ModelCalibrator(n_bins=10)

    # Test 1: Analyze baseline calibration
    logger.info("\n=== Test 1: Baseline Calibration Analysis ===")
    baseline_analysis = calibrator.analyze_calibration(y_test, y_prob_test)
    logger.info(f"Baseline ECE: {baseline_analysis['ece']:.4f}")
    logger.info(f"Baseline MCE: {baseline_analysis['mce']:.4f}")
    logger.info(f"Baseline Brier Score: {baseline_analysis['brier_score']:.4f}")

    # Test 2: Platt Scaling
    logger.info("\n=== Test 2: Platt Scaling ===")
    platt_result = calibrator.platt_scaling(y_cal, y_prob_cal, y_test, y_prob_test)

    # Test 3: Isotonic Calibration
    logger.info("\n=== Test 3: Isotonic Calibration ===")
    isotonic_result = calibrator.isotonic_calibration(y_cal, y_prob_cal, y_test, y_prob_test)

    # Test 4: Temperature Scaling
    logger.info("\n=== Test 4: Temperature Scaling ===")
    temp_result = calibrator.temperature_scaling(y_cal, logits_cal, y_test, logits_test)

    # Export results
    output_dir = Path("/tmp/model_calibration")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'n_train': len(X_train),
            'n_calibration': len(X_cal),
            'n_test': len(X_test),
            'model': 'RandomForestClassifier'
        },
        'baseline_analysis': baseline_analysis,
        'platt_scaling': platt_result.to_dict(),
        'isotonic_calibration': isotonic_result.to_dict(),
        'temperature_scaling': temp_result.to_dict()
    }

    calibrator.export_results(str(output_dir / "calibration_results.json"), results)

    # Summary
    logger.info("\n=== Calibration Results Summary ===")
    logger.info(f"Baseline ECE: {baseline_analysis['ece']:.4f}")
    logger.info("")
    
    for name, result in [
        ('Platt Scaling', platt_result),
        ('Isotonic Calibration', isotonic_result),
        ('Temperature Scaling', temp_result)
    ]:
        logger.info(f"{name}:")
        logger.info(f"  ECE After: {result.ece_after:.4f}")
        logger.info(f"  Improvement: {result.improvement:+.4f}")
        logger.info(f"  Brier After: {result.brier_score_after:.4f}")

    # Find best method
    best_method = min(
        [platt_result, isotonic_result, temp_result],
        key=lambda x: x.ece_after
    )
    logger.info(f"\nBest Calibration Method: {best_method.method}")
    logger.info(f"  Final ECE: {best_method.ece_after:.4f}")

    logger.info(f"\n✅ Model calibration demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_model_calibration()
