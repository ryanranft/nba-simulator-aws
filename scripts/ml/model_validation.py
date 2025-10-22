"""
Model Validation and Testing Framework

Comprehensive framework for validating ML models:
- Cross-validation with multiple strategies
- Performance metrics calculation and tracking
- Residual analysis and diagnostics
- Model stability testing
- Out-of-time validation for temporal data
- Statistical significance testing

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
class ValidationResult:
    """Store validation results for a model."""
    model_name: str
    metrics: Dict[str, float]
    cv_scores: Optional[List[float]] = None
    cv_mean: Optional[float] = None
    cv_std: Optional[float] = None
    residual_stats: Optional[Dict[str, float]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'model_name': self.model_name,
            'metrics': {k: float(v) for k, v in self.metrics.items()},
            'cv_scores': [float(x) for x in self.cv_scores] if self.cv_scores else None,
            'cv_mean': float(self.cv_mean) if self.cv_mean is not None else None,
            'cv_std': float(self.cv_std) if self.cv_std is not None else None,
            'residual_stats': {k: float(v) for k, v in self.residual_stats.items()} if self.residual_stats else None,
            'timestamp': self.timestamp.isoformat()
        }


class ModelValidator:
    """
    Comprehensive model validation framework for ML models.
    """

    def __init__(self, task_type: str = 'regression'):
        """
        Initialize model validator.

        Args:
            task_type: 'regression' or 'classification'
        """
        self.task_type = task_type
        logger.info(f"Initialized ModelValidator for {task_type}")

    def validate_model(self, model: Any, X_train: pd.DataFrame, y_train: pd.Series,
                      X_test: pd.DataFrame, y_test: pd.Series,
                      model_name: str = "model",
                      cv_folds: int = 5) -> ValidationResult:
        """
        Comprehensive model validation.

        Args:
            model: Trained ML model
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            model_name: Name for the model
            cv_folds: Number of cross-validation folds

        Returns:
            ValidationResult object
        """
        logger.info(f"Validating model: {model_name}")

        # Calculate metrics
        metrics = self._calculate_metrics(model, X_train, y_train, X_test, y_test)

        # Perform cross-validation on training data
        cv_scores = self._cross_validate(model, X_train, y_train, cv_folds)
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))

        # Residual analysis
        residual_stats = self._analyze_residuals(model, X_test, y_test)

        result = ValidationResult(
            model_name=model_name,
            metrics=metrics,
            cv_scores=cv_scores,
            cv_mean=cv_mean,
            cv_std=cv_std,
            residual_stats=residual_stats
        )

        logger.info(f"Validation complete for {model_name}")
        logger.info(f"  Test R²: {metrics.get('test_r2', 'N/A'):.4f}")
        logger.info(f"  CV Mean: {cv_mean:.4f} ± {cv_std:.4f}")

        return result

    def out_of_time_validation(self, model: Any, X: pd.DataFrame, y: pd.Series,
                               time_column: str, train_end_date: Any,
                               model_name: str = "model") -> ValidationResult:
        """
        Validate model using out-of-time split (temporal validation).

        Args:
            model: ML model to validate
            X: Feature matrix with time column
            y: Target variable
            time_column: Name of time column
            train_end_date: Cutoff date for train/test split
            model_name: Name for the model

        Returns:
            ValidationResult object
        """
        logger.info(f"Performing out-of-time validation for {model_name}")

        # Split by time
        train_mask = X[time_column] <= train_end_date
        test_mask = X[time_column] > train_end_date

        X_train = X[train_mask].drop(columns=[time_column])
        y_train = y[train_mask]
        X_test = X[test_mask].drop(columns=[time_column])
        y_test = y[test_mask]

        logger.info(f"  Train period: {X_train.shape[0]} samples")
        logger.info(f"  Test period: {X_test.shape[0]} samples")

        # Train and validate
        model.fit(X_train, y_train)
        return self.validate_model(model, X_train, y_train, X_test, y_test, model_name)

    def stability_test(self, model_class: type, X: pd.DataFrame, y: pd.Series,
                      n_iterations: int = 10, test_size: float = 0.2,
                      random_state: int = 42) -> Dict[str, Any]:
        """
        Test model stability across multiple train/test splits.

        Args:
            model_class: Model class to instantiate
            X: Feature matrix
            y: Target variable
            n_iterations: Number of random splits
            test_size: Proportion of data for testing
            random_state: Random seed

        Returns:
            Dictionary with stability metrics
        """
        logger.info(f"Running stability test with {n_iterations} iterations...")

        np.random.seed(random_state)
        scores = []

        for i in range(n_iterations):
            # Random split
            indices = np.random.permutation(len(X))
            split_point = int(len(X) * (1 - test_size))
            train_idx = indices[:split_point]
            test_idx = indices[split_point:]

            X_train = X.iloc[train_idx]
            y_train = y.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_test = y.iloc[test_idx]

            # Train and score
            model = model_class()
            model.fit(X_train, y_train)
            score = self._score(model, X_test, y_test)
            scores.append(score)

        return {
            'scores': [float(x) for x in scores],
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'stability_ratio': float(np.std(scores) / np.mean(scores)) if np.mean(scores) != 0 else float('inf')
        }

    def compare_models(self, models: Dict[str, Any], X_train: pd.DataFrame,
                      y_train: pd.Series, X_test: pd.DataFrame,
                      y_test: pd.Series) -> pd.DataFrame:
        """
        Compare multiple models on the same dataset.

        Args:
            models: Dictionary of {model_name: model_instance}
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target

        Returns:
            DataFrame with comparison results
        """
        logger.info(f"Comparing {len(models)} models...")

        results = []
        for name, model in models.items():
            validation_result = self.validate_model(
                model, X_train, y_train, X_test, y_test, name
            )

            result_dict = {
                'model': name,
                'test_r2': validation_result.metrics.get('test_r2'),
                'test_rmse': validation_result.metrics.get('test_rmse'),
                'test_mae': validation_result.metrics.get('test_mae'),
                'cv_mean': validation_result.cv_mean,
                'cv_std': validation_result.cv_std
            }
            results.append(result_dict)

        comparison_df = pd.DataFrame(results)
        comparison_df = comparison_df.sort_values('test_r2', ascending=False)

        logger.info("\nModel Comparison:")
        logger.info(comparison_df.to_string(index=False))

        return comparison_df

    def statistical_significance_test(self, scores1: List[float], scores2: List[float],
                                     alpha: float = 0.05) -> Dict[str, Any]:
        """
        Test if difference between two models is statistically significant.

        Uses paired t-test for cross-validation scores.

        Args:
            scores1: CV scores for model 1
            scores2: CV scores for model 2
            alpha: Significance level

        Returns:
            Dictionary with test results
        """
        from scipy import stats

        if len(scores1) != len(scores2):
            raise ValueError("Score lists must have same length")

        # Paired t-test
        t_stat, p_value = stats.ttest_rel(scores1, scores2)

        is_significant = p_value < alpha
        mean_diff = float(np.mean(scores1) - np.mean(scores2))

        logger.info(f"Statistical significance test:")
        logger.info(f"  Mean difference: {mean_diff:.4f}")
        logger.info(f"  t-statistic: {t_stat:.4f}")
        logger.info(f"  p-value: {p_value:.4f}")
        logger.info(f"  Significant at α={alpha}: {is_significant}")

        return {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'mean_difference': mean_diff,
            'is_significant': bool(is_significant),
            'alpha': alpha
        }

    def _calculate_metrics(self, model: Any, X_train: pd.DataFrame,
                          y_train: pd.Series, X_test: pd.DataFrame,
                          y_test: pd.Series) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        metrics = {}

        # Training metrics
        y_train_pred = model.predict(X_train)
        train_r2 = self._r2_score(y_train, y_train_pred)
        train_rmse = float(np.sqrt(np.mean((y_train - y_train_pred) ** 2)))
        train_mae = float(np.mean(np.abs(y_train - y_train_pred)))

        # Test metrics
        y_test_pred = model.predict(X_test)
        test_r2 = self._r2_score(y_test, y_test_pred)
        test_rmse = float(np.sqrt(np.mean((y_test - y_test_pred) ** 2)))
        test_mae = float(np.mean(np.abs(y_test - y_test_pred)))

        metrics['train_r2'] = train_r2
        metrics['train_rmse'] = train_rmse
        metrics['train_mae'] = train_mae
        metrics['test_r2'] = test_r2
        metrics['test_rmse'] = test_rmse
        metrics['test_mae'] = test_mae
        metrics['overfitting_gap'] = train_r2 - test_r2

        return metrics

    def _cross_validate(self, model: Any, X: pd.DataFrame, y: pd.Series,
                       n_folds: int = 5) -> List[float]:
        """Perform k-fold cross-validation."""
        from sklearn.model_selection import KFold

        kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
        scores = []

        for train_idx, val_idx in kf.split(X):
            X_train_fold = X.iloc[train_idx]
            y_train_fold = y.iloc[train_idx]
            X_val_fold = X.iloc[val_idx]
            y_val_fold = y.iloc[val_idx]

            # Clone and train model
            from sklearn.base import clone
            model_fold = clone(model)
            model_fold.fit(X_train_fold, y_train_fold)

            # Score
            score = self._score(model_fold, X_val_fold, y_val_fold)
            scores.append(score)

        return scores

    def _analyze_residuals(self, model: Any, X: pd.DataFrame,
                          y: pd.Series) -> Dict[str, float]:
        """Analyze prediction residuals."""
        y_pred = model.predict(X)
        residuals = y - y_pred

        stats = {
            'mean': float(np.mean(residuals)),
            'std': float(np.std(residuals)),
            'min': float(np.min(residuals)),
            'max': float(np.max(residuals)),
            'median': float(np.median(residuals)),
            'q25': float(np.percentile(residuals, 25)),
            'q75': float(np.percentile(residuals, 75)),
            'skewness': float(self._skewness(residuals)),
            'kurtosis': float(self._kurtosis(residuals))
        }

        # Test for normality (Shapiro-Wilk test)
        from scipy import stats as scipy_stats
        if len(residuals) < 5000:  # Shapiro-Wilk works best for smaller samples
            _, normality_p = scipy_stats.shapiro(residuals[:5000])
            stats['normality_p_value'] = float(normality_p)
            stats['is_normal'] = bool(normality_p > 0.05)

        return stats

    def _score(self, model: Any, X: pd.DataFrame, y: pd.Series) -> float:
        """Calculate model score (R² for regression)."""
        y_pred = model.predict(X)
        return self._r2_score(y, y_pred)

    def _r2_score(self, y_true, y_pred) -> float:
        """Calculate R² score."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return float(1 - (ss_res / ss_tot))

    def _skewness(self, x: np.ndarray) -> float:
        """Calculate skewness."""
        mean = np.mean(x)
        std = np.std(x)
        return float(np.mean(((x - mean) / std) ** 3))

    def _kurtosis(self, x: np.ndarray) -> float:
        """Calculate kurtosis."""
        mean = np.mean(x)
        std = np.std(x)
        return float(np.mean(((x - mean) / std) ** 4) - 3)

    def export_results(self, output_path: str, results: Dict[str, Any]):
        """Export validation results to JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_model_validation():
    """Demonstrate model validation with synthetic data."""
    logger.info("Starting model validation demo...")

    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000

    # Generate features
    X = pd.DataFrame({
        'feature1': np.random.normal(0, 1, n_samples),
        'feature2': np.random.normal(0, 1, n_samples),
        'feature3': np.random.normal(0, 1, n_samples),
        'feature4': np.random.normal(0, 1, n_samples),
        'feature5': np.random.normal(0, 1, n_samples)
    })

    # Generate target with known relationship
    y = (
        2 * X['feature1'] +
        1.5 * X['feature2'] +
        X['feature3'] +
        0.5 * X['feature4'] +
        np.random.normal(0, 1, n_samples)
    )

    # Add time column for temporal validation
    X['time'] = pd.date_range('2020-01-01', periods=n_samples, freq='D')

    logger.info(f"Created dataset: {X.shape[0]} samples, {X.shape[1]-1} features")

    # Split data
    split_point = int(0.8 * n_samples)
    X_train = X.iloc[:split_point].drop(columns=['time'])
    y_train = y.iloc[:split_point]
    X_test = X.iloc[split_point:].drop(columns=['time'])
    y_test = y.iloc[split_point:]

    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Initialize validator
    validator = ModelValidator(task_type='regression')

    # Test 1: Single Model Validation
    logger.info("\n=== Test 1: Single Model Validation ===")
    from sklearn.linear_model import Ridge

    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    result = validator.validate_model(
        model, X_train, y_train, X_test, y_test,
        model_name="Ridge_alpha1.0"
    )

    logger.info(f"Validation metrics:")
    for metric, value in result.metrics.items():
        logger.info(f"  {metric}: {value:.4f}")

    # Test 2: Out-of-Time Validation
    logger.info("\n=== Test 2: Out-of-Time Validation ===")
    train_end_date = X['time'].iloc[split_point]

    oot_model = Ridge(alpha=1.0)
    oot_result = validator.out_of_time_validation(
        oot_model, X, y, 'time', train_end_date,
        model_name="Ridge_OOT"
    )

    logger.info(f"Out-of-time R²: {oot_result.metrics['test_r2']:.4f}")

    # Test 3: Stability Test
    logger.info("\n=== Test 3: Stability Test ===")
    X_no_time = X.drop(columns=['time'])

    stability_results = validator.stability_test(
        Ridge, X_no_time, y, n_iterations=10
    )

    logger.info(f"Stability metrics:")
    logger.info(f"  Mean R²: {stability_results['mean']:.4f}")
    logger.info(f"  Std R²: {stability_results['std']:.4f}")
    logger.info(f"  Range: [{stability_results['min']:.4f}, {stability_results['max']:.4f}]")
    logger.info(f"  Stability ratio: {stability_results['stability_ratio']:.4f}")

    # Test 4: Model Comparison
    logger.info("\n=== Test 4: Model Comparison ===")
    from sklearn.linear_model import Ridge, Lasso, ElasticNet

    models = {
        'Ridge_alpha0.1': Ridge(alpha=0.1),
        'Ridge_alpha1.0': Ridge(alpha=1.0),
        'Ridge_alpha10.0': Ridge(alpha=10.0),
        'Lasso_alpha0.1': Lasso(alpha=0.1, max_iter=5000),
        'ElasticNet': ElasticNet(alpha=0.1, max_iter=5000)
    }

    # Train all models
    for model in models.values():
        model.fit(X_train, y_train)

    comparison_df = validator.compare_models(models, X_train, y_train, X_test, y_test)

    # Test 5: Statistical Significance
    logger.info("\n=== Test 5: Statistical Significance Test ===")
    model1 = Ridge(alpha=1.0)
    model2 = Ridge(alpha=10.0)

    # Train models first
    model1.fit(X_train, y_train)
    model2.fit(X_train, y_train)

    # Get CV scores
    result1 = validator.validate_model(model1, X_train, y_train, X_test, y_test, "Model1")
    result2 = validator.validate_model(model2, X_train, y_train, X_test, y_test, "Model2")

    sig_test = validator.statistical_significance_test(
        result1.cv_scores, result2.cv_scores
    )

    # Export results
    output_dir = Path("/tmp/model_validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'n_samples': len(X),
            'n_features': len(X.columns) - 1,
            'task_type': 'regression'
        },
        'single_validation': result.to_dict(),
        'oot_validation': oot_result.to_dict(),
        'stability_test': stability_results,
        'model_comparison': comparison_df.to_dict('records'),
        'significance_test': sig_test
    }

    validator.export_results(str(output_dir / "validation_results.json"), results)

    logger.info(f"\n✅ Model validation demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_model_validation()
