"""
Model Interpretation and Explainability Framework

Implements model interpretation techniques for understanding ML model predictions:
- Feature importance (permutation, SHAP-like, tree-based)
- Partial dependence plots
- Individual prediction explanations
- Global model behavior analysis
- Feature interaction detection

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
class FeatureImportance:
    """Store feature importance results."""
    feature_name: str
    importance: float
    std_error: Optional[float] = None
    rank: Optional[int] = None
    method: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'feature_name': self.feature_name,
            'importance': float(self.importance),
            'std_error': float(self.std_error) if self.std_error is not None else None,
            'rank': int(self.rank) if self.rank is not None else None,
            'method': self.method
        }


@dataclass
class PredictionExplanation:
    """Store explanation for a single prediction."""
    prediction: float
    feature_contributions: Dict[str, float]
    baseline: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'prediction': float(self.prediction),
            'feature_contributions': {k: float(v) for k, v in self.feature_contributions.items()},
            'baseline': float(self.baseline),
            'timestamp': self.timestamp.isoformat()
        }


class ModelInterpreter:
    """
    Comprehensive model interpretation framework for understanding ML models.
    """

    def __init__(self, model: Any, feature_names: List[str],
                 task_type: str = 'regression'):
        """
        Initialize model interpreter.

        Args:
            model: Trained ML model with predict method
            feature_names: List of feature names
            task_type: 'regression' or 'classification'
        """
        self.model = model
        self.feature_names = feature_names
        self.task_type = task_type
        self.n_features = len(feature_names)

        logger.info(f"Initialized ModelInterpreter for {task_type} with {self.n_features} features")

    def permutation_importance(self, X: pd.DataFrame, y: pd.Series,
                               n_repeats: int = 10,
                               random_state: int = 42) -> List[FeatureImportance]:
        """
        Calculate permutation feature importance.

        Measures importance by randomly shuffling each feature and measuring
        the decrease in model performance.

        Args:
            X: Feature matrix
            y: Target variable
            n_repeats: Number of times to permute each feature
            random_state: Random seed

        Returns:
            List of FeatureImportance objects sorted by importance
        """
        logger.info("Computing permutation importance...")
        np.random.seed(random_state)

        # Get baseline score
        baseline_score = self._score(X, y)
        logger.info(f"Baseline score: {baseline_score:.4f}")

        importances = []

        for i, feature in enumerate(self.feature_names):
            scores = []
            X_permuted = X.copy()

            for _ in range(n_repeats):
                # Permute feature
                X_permuted[feature] = np.random.permutation(X_permuted[feature].values)

                # Score with permuted feature
                permuted_score = self._score(X_permuted, y)
                scores.append(baseline_score - permuted_score)

                # Restore original values
                X_permuted[feature] = X[feature]

            importance = float(np.mean(scores))
            std_error = float(np.std(scores))

            importances.append(FeatureImportance(
                feature_name=feature,
                importance=importance,
                std_error=std_error,
                method='permutation'
            ))

        # Sort by importance and assign ranks
        importances.sort(key=lambda x: abs(x.importance), reverse=True)
        for rank, imp in enumerate(importances, 1):
            imp.rank = rank

        logger.info(f"Top 5 important features: {[imp.feature_name for imp in importances[:5]]}")

        return importances

    def partial_dependence(self, X: pd.DataFrame, feature: str,
                          grid_resolution: int = 50,
                          percentiles: Tuple[float, float] = (0.05, 0.95)) -> Dict[str, Any]:
        """
        Calculate partial dependence of the model on a feature.

        Shows the marginal effect of a feature on predictions.

        Args:
            X: Feature matrix
            feature: Feature name to analyze
            grid_resolution: Number of points in the grid
            percentiles: Feature value range to analyze

        Returns:
            Dictionary with grid values and average predictions
        """
        logger.info(f"Computing partial dependence for {feature}...")

        if feature not in self.feature_names:
            raise ValueError(f"Feature {feature} not found in model")

        # Create grid of feature values
        feature_values = X[feature].values
        lower = np.percentile(feature_values, percentiles[0] * 100)
        upper = np.percentile(feature_values, percentiles[1] * 100)
        grid = np.linspace(lower, upper, grid_resolution)

        # Calculate average prediction for each grid point
        pd_values = []
        for value in grid:
            X_temp = X.copy()
            X_temp[feature] = value
            predictions = self.model.predict(X_temp)
            pd_values.append(float(np.mean(predictions)))

        return {
            'feature': feature,
            'grid_values': grid.tolist(),
            'pd_values': pd_values,
            'percentiles': percentiles
        }

    def feature_interaction(self, X: pd.DataFrame,
                           feature1: str, feature2: str,
                           grid_resolution: int = 20) -> Dict[str, Any]:
        """
        Calculate interaction effect between two features.

        Args:
            X: Feature matrix
            feature1: First feature name
            feature2: Second feature name
            grid_resolution: Number of points per dimension

        Returns:
            Dictionary with grid and interaction matrix
        """
        logger.info(f"Computing interaction between {feature1} and {feature2}...")

        # Create 2D grid
        f1_values = X[feature1].values
        f2_values = X[feature2].values

        f1_grid = np.linspace(
            np.percentile(f1_values, 5),
            np.percentile(f1_values, 95),
            grid_resolution
        )
        f2_grid = np.linspace(
            np.percentile(f2_values, 5),
            np.percentile(f2_values, 95),
            grid_resolution
        )

        # Calculate predictions for each grid point
        interaction_matrix = np.zeros((grid_resolution, grid_resolution))

        for i, f1_val in enumerate(f1_grid):
            for j, f2_val in enumerate(f2_grid):
                X_temp = X.copy()
                X_temp[feature1] = f1_val
                X_temp[feature2] = f2_val
                predictions = self.model.predict(X_temp)
                interaction_matrix[i, j] = float(np.mean(predictions))

        return {
            'feature1': feature1,
            'feature2': feature2,
            'f1_grid': f1_grid.tolist(),
            'f2_grid': f2_grid.tolist(),
            'interaction_matrix': interaction_matrix.tolist()
        }

    def explain_prediction(self, X_instance: pd.Series,
                          baseline: Optional[pd.Series] = None) -> PredictionExplanation:
        """
        Explain a single prediction using linear approximation.

        Approximates feature contributions to the prediction.

        Args:
            X_instance: Single instance to explain
            baseline: Baseline instance for comparison (default: feature means)

        Returns:
            PredictionExplanation object
        """
        # Get prediction for instance
        X_df = pd.DataFrame([X_instance], columns=self.feature_names)
        prediction = float(self.model.predict(X_df)[0])

        # Use feature means as baseline if not provided
        if baseline is None:
            baseline = X_instance.copy()
            for feature in self.feature_names:
                baseline[feature] = 0.0  # Assume standardized features

        baseline_df = pd.DataFrame([baseline], columns=self.feature_names)
        baseline_pred = float(self.model.predict(baseline_df)[0])

        # Calculate contributions by perturbing each feature
        contributions = {}
        for feature in self.feature_names:
            # Create instance with only this feature changed from baseline
            X_temp = baseline.copy()
            X_temp[feature] = X_instance[feature]
            X_temp_df = pd.DataFrame([X_temp], columns=self.feature_names)

            pred_with_feature = float(self.model.predict(X_temp_df)[0])
            contributions[feature] = pred_with_feature - baseline_pred

        return PredictionExplanation(
            prediction=prediction,
            feature_contributions=contributions,
            baseline=baseline_pred
        )

    def global_feature_importance(self, X: pd.DataFrame,
                                  method: str = 'variance') -> List[FeatureImportance]:
        """
        Calculate global feature importance based on prediction variance.

        Args:
            X: Feature matrix
            method: 'variance' or 'range'

        Returns:
            List of FeatureImportance objects
        """
        logger.info(f"Computing global importance using {method} method...")

        importances = []

        for feature in self.feature_names:
            # Get predictions at different feature values
            feature_values = X[feature].values
            lower = np.percentile(feature_values, 5)
            upper = np.percentile(feature_values, 95)

            # Predictions at lower percentile
            X_lower = X.copy()
            X_lower[feature] = lower
            preds_lower = self.model.predict(X_lower)

            # Predictions at upper percentile
            X_upper = X.copy()
            X_upper[feature] = upper
            preds_upper = self.model.predict(X_upper)

            if method == 'variance':
                # Measure variance in predictions
                importance = float(np.var(preds_upper - preds_lower))
            elif method == 'range':
                # Measure range in predictions
                importance = float(np.max(preds_upper - preds_lower) - np.min(preds_upper - preds_lower))
            else:
                raise ValueError(f"Unknown method: {method}")

            importances.append(FeatureImportance(
                feature_name=feature,
                importance=importance,
                method=f'global_{method}'
            ))

        # Sort and rank
        importances.sort(key=lambda x: abs(x.importance), reverse=True)
        for rank, imp in enumerate(importances, 1):
            imp.rank = rank

        return importances

    def _score(self, X: pd.DataFrame, y: pd.Series) -> float:
        """Calculate model score (R² for regression, accuracy for classification)."""
        predictions = self.model.predict(X)

        if self.task_type == 'regression':
            # R² score
            ss_res = np.sum((y - predictions) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            return float(1 - (ss_res / ss_tot))
        else:
            # Accuracy
            return float(np.mean(predictions == y))

    def export_results(self, output_path: str, results: Dict[str, Any]):
        """Export interpretation results to JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_model_interpretation():
    """Demonstrate model interpretation with synthetic data."""
    logger.info("Starting model interpretation demo...")

    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000

    # Generate features
    X = pd.DataFrame({
        'minutes': np.random.uniform(20, 40, n_samples),
        'usage_rate': np.random.uniform(15, 35, n_samples),
        'true_shooting': np.random.uniform(0.45, 0.65, n_samples),
        'assist_rate': np.random.uniform(10, 40, n_samples),
        'rebound_rate': np.random.uniform(5, 25, n_samples)
    })

    # Generate target (points) with known relationships
    y = (
        0.5 * X['minutes'] +
        0.3 * X['usage_rate'] +
        20 * X['true_shooting'] +
        0.1 * X['assist_rate'] +
        0.2 * X['rebound_rate'] +
        np.random.normal(0, 2, n_samples)
    )

    logger.info(f"Created dataset: {X.shape[0]} samples, {X.shape[1]} features")

    # Train simple model
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X),
        columns=X.columns,
        index=X.index
    )

    model = Ridge(alpha=1.0)
    model.fit(X_scaled, y)

    logger.info("Trained Ridge regression model")

    # Initialize interpreter
    interpreter = ModelInterpreter(
        model=model,
        feature_names=list(X.columns),
        task_type='regression'
    )

    # Test 1: Permutation Importance
    logger.info("\n=== Test 1: Permutation Importance ===")
    perm_importance = interpreter.permutation_importance(X_scaled, y, n_repeats=5)

    logger.info("Feature importance rankings:")
    for imp in perm_importance[:5]:
        logger.info(f"  {imp.rank}. {imp.feature_name}: {imp.importance:.4f} ± {imp.std_error:.4f}")

    # Test 2: Partial Dependence
    logger.info("\n=== Test 2: Partial Dependence ===")
    pd_result = interpreter.partial_dependence(X_scaled, 'minutes', grid_resolution=20)
    logger.info(f"Computed partial dependence for 'minutes'")
    logger.info(f"  PD range: [{min(pd_result['pd_values']):.2f}, {max(pd_result['pd_values']):.2f}]")

    # Test 3: Feature Interaction
    logger.info("\n=== Test 3: Feature Interaction ===")
    interaction = interpreter.feature_interaction(
        X_scaled, 'minutes', 'usage_rate', grid_resolution=10
    )
    logger.info(f"Computed interaction between 'minutes' and 'usage_rate'")
    interaction_matrix = np.array(interaction['interaction_matrix'])
    logger.info(f"  Interaction range: [{interaction_matrix.min():.2f}, {interaction_matrix.max():.2f}]")

    # Test 4: Explain Single Prediction
    logger.info("\n=== Test 4: Single Prediction Explanation ===")
    sample_instance = X_scaled.iloc[0]
    explanation = interpreter.explain_prediction(sample_instance)

    logger.info(f"Prediction: {explanation.prediction:.2f}")
    logger.info(f"Baseline: {explanation.baseline:.2f}")
    logger.info("Top feature contributions:")
    sorted_contribs = sorted(
        explanation.feature_contributions.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    for feature, contrib in sorted_contribs[:5]:
        logger.info(f"  {feature}: {contrib:+.2f}")

    # Test 5: Global Feature Importance
    logger.info("\n=== Test 5: Global Feature Importance ===")
    global_importance = interpreter.global_feature_importance(X_scaled, method='variance')

    logger.info("Global importance rankings:")
    for imp in global_importance[:5]:
        logger.info(f"  {imp.rank}. {imp.feature_name}: {imp.importance:.4f}")

    # Export results
    output_dir = Path("/tmp/model_interpretation")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'n_samples': len(X),
            'n_features': len(X.columns),
            'task_type': 'regression'
        },
        'permutation_importance': [imp.to_dict() for imp in perm_importance],
        'partial_dependence': pd_result,
        'feature_interaction': interaction,
        'sample_explanation': explanation.to_dict(),
        'global_importance': [imp.to_dict() for imp in global_importance]
    }

    interpreter.export_results(str(output_dir / "interpretation_results.json"), results)

    logger.info(f"\n✅ Model interpretation demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_model_interpretation()
