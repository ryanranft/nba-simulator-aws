"""
Learning Curves and Model Complexity Analysis Framework

Implements tools for analyzing model learning behavior:
- Learning curves (performance vs training set size)
- Validation curves (performance vs hyperparameter values)
- Complexity curves (performance vs model complexity)
- Bias-variance decomposition
- Training set size recommendations
- Overfitting/underfitting diagnosis

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
class LearningCurveResult:
    """Store learning curve analysis results."""
    train_sizes: List[int]
    train_scores_mean: List[float]
    train_scores_std: List[float]
    test_scores_mean: List[float]
    test_scores_std: List[float]
    analysis_time: float
    diagnosis: str
    recommended_action: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'train_sizes': [int(x) for x in self.train_sizes],
            'train_scores_mean': [float(x) for x in self.train_scores_mean],
            'train_scores_std': [float(x) for x in self.train_scores_std],
            'test_scores_mean': [float(x) for x in self.test_scores_mean],
            'test_scores_std': [float(x) for x in self.test_scores_std],
            'analysis_time': float(self.analysis_time),
            'diagnosis': self.diagnosis,
            'recommended_action': self.recommended_action,
            'metadata': self.metadata
        }


@dataclass
class ValidationCurveResult:
    """Store validation curve results."""
    param_name: str
    param_range: List[float]
    train_scores_mean: List[float]
    train_scores_std: List[float]
    test_scores_mean: List[float]
    test_scores_std: List[float]
    best_param_value: float
    best_test_score: float
    analysis_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'param_name': self.param_name,
            'param_range': [float(x) for x in self.param_range],
            'train_scores_mean': [float(x) for x in self.train_scores_mean],
            'train_scores_std': [float(x) for x in self.train_scores_std],
            'test_scores_mean': [float(x) for x in self.test_scores_mean],
            'test_scores_std': [float(x) for x in self.test_scores_std],
            'best_param_value': float(self.best_param_value),
            'best_test_score': float(self.best_test_score),
            'analysis_time': float(self.analysis_time),
            'metadata': self.metadata
        }


class LearningCurveAnalyzer:
    """
    Comprehensive learning curve and model complexity analysis.
    """

    def __init__(self, scoring: str = 'accuracy', cv: int = 5):
        """
        Initialize analyzer.

        Args:
            scoring: Scoring metric ('accuracy', 'r2', 'neg_mean_squared_error', etc.)
            cv: Number of cross-validation folds
        """
        self.scoring = scoring
        self.cv = cv
        logger.info(f"Initialized LearningCurveAnalyzer (scoring={scoring}, cv={cv})")

    def compute_learning_curve(self, model: Any, X: pd.DataFrame, y: pd.Series,
                               train_sizes: Optional[List[float]] = None) -> LearningCurveResult:
        """
        Compute learning curve showing performance vs training set size.

        Args:
            model: ML model to analyze
            X: Feature matrix
            y: Target variable
            train_sizes: Fractions of training data to use

        Returns:
            LearningCurveResult with curves and diagnosis
        """
        logger.info("Computing learning curve...")
        start_time = time.time()

        from sklearn.model_selection import learning_curve

        # Default training sizes
        if train_sizes is None:
            train_sizes = np.linspace(0.1, 1.0, 10)

        # Compute learning curve
        train_sizes_abs, train_scores, test_scores = learning_curve(
            model, X, y,
            train_sizes=train_sizes,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=-1,
            random_state=42
        )

        # Calculate means and standard deviations
        train_scores_mean = np.mean(train_scores, axis=1)
        train_scores_std = np.std(train_scores, axis=1)
        test_scores_mean = np.mean(test_scores, axis=1)
        test_scores_std = np.std(test_scores, axis=1)

        # Diagnose learning behavior
        diagnosis, recommended_action = self._diagnose_learning_curve(
            train_scores_mean, test_scores_mean
        )

        elapsed_time = time.time() - start_time

        logger.info(f"Learning curve computed in {elapsed_time:.2f}s")
        logger.info(f"Diagnosis: {diagnosis}")
        logger.info(f"Recommendation: {recommended_action}")

        return LearningCurveResult(
            train_sizes=train_sizes_abs.tolist(),
            train_scores_mean=train_scores_mean.tolist(),
            train_scores_std=train_scores_std.tolist(),
            test_scores_mean=test_scores_mean.tolist(),
            test_scores_std=test_scores_std.tolist(),
            analysis_time=elapsed_time,
            diagnosis=diagnosis,
            recommended_action=recommended_action,
            metadata={
                'final_train_score': float(train_scores_mean[-1]),
                'final_test_score': float(test_scores_mean[-1]),
                'train_test_gap': float(train_scores_mean[-1] - test_scores_mean[-1])
            }
        )

    def compute_validation_curve(self, model: Any, X: pd.DataFrame, y: pd.Series,
                                 param_name: str,
                                 param_range: List[float]) -> ValidationCurveResult:
        """
        Compute validation curve showing performance vs hyperparameter values.

        Args:
            model: ML model to analyze
            X: Feature matrix
            y: Target variable
            param_name: Name of hyperparameter to vary
            param_range: Range of parameter values to test

        Returns:
            ValidationCurveResult with optimal parameter
        """
        logger.info(f"Computing validation curve for {param_name}...")
        start_time = time.time()

        from sklearn.model_selection import validation_curve

        # Compute validation curve
        train_scores, test_scores = validation_curve(
            model, X, y,
            param_name=param_name,
            param_range=param_range,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=-1
        )

        # Calculate means and standard deviations
        train_scores_mean = np.mean(train_scores, axis=1)
        train_scores_std = np.std(train_scores, axis=1)
        test_scores_mean = np.mean(test_scores, axis=1)
        test_scores_std = np.std(test_scores, axis=1)

        # Find best parameter
        best_idx = np.argmax(test_scores_mean)
        best_param_value = param_range[best_idx]
        best_test_score = test_scores_mean[best_idx]

        elapsed_time = time.time() - start_time

        logger.info(f"Validation curve computed in {elapsed_time:.2f}s")
        logger.info(f"Best {param_name}: {best_param_value}")
        logger.info(f"Best test score: {best_test_score:.4f}")

        return ValidationCurveResult(
            param_name=param_name,
            param_range=param_range,
            train_scores_mean=train_scores_mean.tolist(),
            train_scores_std=train_scores_std.tolist(),
            test_scores_mean=test_scores_mean.tolist(),
            test_scores_std=test_scores_std.tolist(),
            best_param_value=best_param_value,
            best_test_score=best_test_score,
            analysis_time=elapsed_time,
            metadata={
                'param_range_min': float(min(param_range)),
                'param_range_max': float(max(param_range)),
                'n_params_tested': len(param_range)
            }
        )

    def analyze_model_complexity(self, X: pd.DataFrame, y: pd.Series,
                                 max_depth_range: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Analyze model complexity using decision trees of varying depth.

        Args:
            X: Feature matrix
            y: Target variable
            max_depth_range: Range of tree depths to test

        Returns:
            Dictionary with complexity analysis results
        """
        logger.info("Analyzing model complexity...")
        start_time = time.time()

        from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
        from sklearn.model_selection import cross_val_score

        # Default depth range
        if max_depth_range is None:
            max_depth_range = list(range(1, 21))

        # Determine task type
        is_classification = len(np.unique(y)) < 20

        # Test different complexities
        train_scores = []
        test_scores = []

        for depth in max_depth_range:
            if is_classification:
                model = DecisionTreeClassifier(max_depth=depth, random_state=42)
            else:
                model = DecisionTreeRegressor(max_depth=depth, random_state=42)

            # Cross-validated test scores
            cv_scores = cross_val_score(model, X, y, cv=self.cv, scoring=self.scoring)
            test_scores.append(np.mean(cv_scores))

            # Training score
            model.fit(X, y)
            train_scores.append(model.score(X, y))

            if (depth) % 5 == 0:
                logger.info(f"  Depth {depth}: Train={train_scores[-1]:.4f}, "
                           f"Test={test_scores[-1]:.4f}")

        # Find optimal complexity
        best_idx = np.argmax(test_scores)
        optimal_depth = max_depth_range[best_idx]
        best_test_score = test_scores[best_idx]

        elapsed_time = time.time() - start_time

        logger.info(f"Optimal tree depth: {optimal_depth}")
        logger.info(f"Best test score: {best_test_score:.4f}")

        return {
            'max_depth_range': max_depth_range,
            'train_scores': train_scores,
            'test_scores': test_scores,
            'optimal_depth': optimal_depth,
            'best_test_score': best_test_score,
            'analysis_time': elapsed_time
        }

    def estimate_sample_size_requirement(self, model: Any, X: pd.DataFrame, y: pd.Series,
                                        target_score: float = 0.9,
                                        max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Estimate training set size needed to reach target performance.

        Args:
            model: ML model
            X: Feature matrix
            y: Target variable
            target_score: Target test score to reach
            max_size: Maximum training size to test

        Returns:
            Dictionary with size recommendations
        """
        logger.info(f"Estimating sample size for target score {target_score:.2f}...")
        start_time = time.time()

        from sklearn.model_selection import learning_curve

        # Use up to max_size or all data
        if max_size is None:
            max_size = len(X)

        # Compute learning curve
        train_sizes = np.linspace(0.1, 1.0, 10)
        train_sizes_abs, _, test_scores = learning_curve(
            model, X, y,
            train_sizes=train_sizes,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=-1,
            random_state=42
        )

        test_scores_mean = np.mean(test_scores, axis=1)

        # Check if target is reachable
        max_achieved_score = np.max(test_scores_mean)

        if max_achieved_score >= target_score:
            # Find minimum size that reaches target
            reaching_indices = np.where(test_scores_mean >= target_score)[0]
            min_reaching_idx = reaching_indices[0]
            recommended_size = int(train_sizes_abs[min_reaching_idx])
            status = 'reachable'
        else:
            # Target not reached, extrapolate
            recommended_size = int(len(X) * 1.5)  # Suggest 50% more data
            status = 'needs_more_data'

        elapsed_time = time.time() - start_time

        logger.info(f"Recommended training size: {recommended_size}")
        logger.info(f"Status: {status}")

        return {
            'target_score': target_score,
            'max_achieved_score': float(max_achieved_score),
            'recommended_size': recommended_size,
            'current_size': len(X),
            'status': status,
            'train_sizes': train_sizes_abs.tolist(),
            'test_scores': test_scores_mean.tolist(),
            'analysis_time': elapsed_time
        }

    def _diagnose_learning_curve(self, train_scores: np.ndarray,
                                 test_scores: np.ndarray) -> Tuple[str, str]:
        """
        Diagnose learning behavior from curves.

        Args:
            train_scores: Training scores
            test_scores: Test scores

        Returns:
            (diagnosis, recommended_action) tuple
        """
        # Calculate key metrics
        final_train = train_scores[-1]
        final_test = test_scores[-1]
        gap = final_train - final_test

        # Check if scores are converging
        score_diff = test_scores[-1] - test_scores[-2] if len(test_scores) > 1 else 0

        # Diagnose
        if gap > 0.15:  # Large gap
            if final_test < 0.7:  # Poor performance
                diagnosis = "High variance (overfitting) with poor performance"
                action = "Reduce model complexity, add regularization, or collect more data"
            else:
                diagnosis = "Moderate overfitting"
                action = "Add more training data or reduce model complexity"
        elif gap > 0.05:  # Moderate gap
            diagnosis = "Slight overfitting"
            action = "Monitor performance; consider light regularization"
        elif final_test < 0.7:  # Small gap but poor performance
            diagnosis = "High bias (underfitting)"
            action = "Increase model complexity or add more features"
        elif abs(score_diff) < 0.01:  # Converged
            diagnosis = "Good fit - learning has plateaued"
            action = "Model is well-tuned; more data unlikely to help significantly"
        else:  # Still improving
            diagnosis = "Good fit - still improving"
            action = "Consider adding more data for potential improvement"

        return diagnosis, action

    def export_results(self, output_path: str, results: Dict[str, Any]):
        """Export analysis results to JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_learning_curves():
    """Demonstrate learning curve analysis with synthetic data."""
    logger.info("Starting learning curve analysis demo...")

    # Create synthetic data
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier

    np.random.seed(42)

    # Generate dataset
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        n_classes=2,
        random_state=42
    )

    X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(20)])
    y = pd.Series(y)

    logger.info(f"Created dataset: {len(X)} samples, {len(X.columns)} features")

    # Initialize analyzer
    analyzer = LearningCurveAnalyzer(scoring='accuracy', cv=5)

    # Test 1: Learning Curve for Logistic Regression
    logger.info("\n=== Test 1: Learning Curve (Logistic Regression) ===")
    model_lr = LogisticRegression(random_state=42, max_iter=1000)
    lc_lr = analyzer.compute_learning_curve(model_lr, X, y)

    # Test 2: Learning Curve for Random Forest
    logger.info("\n=== Test 2: Learning Curve (Random Forest) ===")
    model_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    lc_rf = analyzer.compute_learning_curve(model_rf, X, y)

    # Test 3: Validation Curve for Random Forest n_estimators
    logger.info("\n=== Test 3: Validation Curve (n_estimators) ===")
    model_rf_base = RandomForestClassifier(random_state=42)
    vc_result = analyzer.compute_validation_curve(
        model_rf_base, X, y,
        param_name='n_estimators',
        param_range=[10, 25, 50, 75, 100, 150, 200]
    )

    # Test 4: Model Complexity Analysis
    logger.info("\n=== Test 4: Model Complexity Analysis ===")
    complexity_result = analyzer.analyze_model_complexity(X, y, max_depth_range=list(range(1, 16)))

    # Test 5: Sample Size Estimation
    logger.info("\n=== Test 5: Sample Size Estimation ===")
    size_result = analyzer.estimate_sample_size_requirement(
        model_lr, X, y, target_score=0.85
    )

    # Export results
    output_dir = Path("/tmp/learning_curves")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'n_samples': len(X),
            'n_features': len(X.columns),
            'scoring': analyzer.scoring
        },
        'learning_curve_logistic': lc_lr.to_dict(),
        'learning_curve_random_forest': lc_rf.to_dict(),
        'validation_curve_n_estimators': vc_result.to_dict(),
        'complexity_analysis': complexity_result,
        'sample_size_estimation': size_result
    }

    analyzer.export_results(str(output_dir / "learning_curve_results.json"), results)

    # Summary
    logger.info("\n=== Learning Curve Analysis Summary ===")
    logger.info(f"Logistic Regression:")
    logger.info(f"  Final Train Score: {lc_lr.metadata['final_train_score']:.4f}")
    logger.info(f"  Final Test Score: {lc_lr.metadata['final_test_score']:.4f}")
    logger.info(f"  Diagnosis: {lc_lr.diagnosis}")

    logger.info(f"\nRandom Forest:")
    logger.info(f"  Final Train Score: {lc_rf.metadata['final_train_score']:.4f}")
    logger.info(f"  Final Test Score: {lc_rf.metadata['final_test_score']:.4f}")
    logger.info(f"  Diagnosis: {lc_rf.diagnosis}")

    logger.info(f"\nValidation Curve:")
    logger.info(f"  Best n_estimators: {vc_result.best_param_value}")
    logger.info(f"  Best Test Score: {vc_result.best_test_score:.4f}")

    logger.info(f"\nComplexity Analysis:")
    logger.info(f"  Optimal Depth: {complexity_result['optimal_depth']}")
    logger.info(f"  Best Test Score: {complexity_result['best_test_score']:.4f}")

    logger.info(f"\nSample Size Estimation:")
    logger.info(f"  Recommended Size: {size_result['recommended_size']}")
    logger.info(f"  Status: {size_result['status']}")

    logger.info(f"\n✅ Learning curve analysis demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_learning_curves()
