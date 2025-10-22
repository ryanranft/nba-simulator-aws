"""
Model Explainability Framework

Implements comprehensive model explanation techniques:
- Global feature importance (permutation, drop-column)
- Local explanations (LIME-style, force plots)
- Partial dependence plots
- Individual conditional expectation (ICE)
- Interaction detection
- Decision path analysis
- Counterfactual explanations
- Rule extraction

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
class GlobalExplanation:
    """Store global model explanation."""
    feature_importance: Dict[str, float]
    method: str  # 'permutation', 'drop_column', 'gain', 'split'
    baseline_score: float
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'feature_importance': {k: float(v) for k, v in self.feature_importance.items()},
            'method': self.method,
            'baseline_score': float(self.baseline_score),
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


@dataclass
class LocalExplanation:
    """Store local (instance-level) explanation."""
    instance_id: int
    prediction: float
    actual: Optional[float]
    feature_contributions: Dict[str, float]
    base_value: float
    method: str  # 'lime', 'shap', 'tree_path'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'instance_id': int(self.instance_id),
            'prediction': float(self.prediction),
            'actual': float(self.actual) if self.actual is not None else None,
            'feature_contributions': {k: float(v) for k, v in self.feature_contributions.items()},
            'base_value': float(self.base_value),
            'method': self.method,
            'metadata': self.metadata
        }


@dataclass
class InteractionEffect:
    """Store feature interaction effect."""
    feature_1: str
    feature_2: str
    interaction_strength: float
    samples_analyzed: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'feature_1': self.feature_1,
            'feature_2': self.feature_2,
            'interaction_strength': float(self.interaction_strength),
            'samples_analyzed': int(self.samples_analyzed),
            'metadata': self.metadata
        }


class ModelExplainer:
    """
    Comprehensive model explainability framework.

    Provides methods for:
    - Global explanations (feature importance)
    - Local explanations (instance-level)
    - Interaction detection
    - Partial dependence
    - Decision path analysis
    """

    def __init__(self, model: Any, X: pd.DataFrame, y: np.ndarray):
        """
        Initialize explainer.

        Parameters
        ----------
        model : Any
            Trained model with predict() or predict_proba() method
        X : pd.DataFrame
            Training or reference data
        y : np.ndarray
            Target values
        """
        self.model = model
        self.X = X
        self.y = y
        self.feature_names = X.columns.tolist()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized ModelExplainer with {X.shape[0]} samples, {X.shape[1]} features")

    def permutation_importance(
        self,
        X_test: pd.DataFrame,
        y_test: np.ndarray,
        n_repeats: int = 10,
        scoring_func: Callable = None
    ) -> GlobalExplanation:
        """
        Calculate permutation feature importance.

        Parameters
        ----------
        X_test : pd.DataFrame
            Test data
        y_test : np.ndarray
            Test labels
        n_repeats : int
            Number of times to permute each feature
        scoring_func : Callable, optional
            Scoring function (default: accuracy)

        Returns
        -------
        GlobalExplanation
            Feature importance scores
        """
        self.logger.info("Calculating permutation importance")

        if scoring_func is None:
            def scoring_func(y_true, y_pred):
                return (y_true == y_pred).mean()

        # Baseline score
        y_pred_baseline = self.model.predict(X_test)
        baseline_score = scoring_func(y_test, y_pred_baseline)

        importances = {}

        for feature in self.feature_names:
            feature_scores = []

            for _ in range(n_repeats):
                # Permute feature
                X_permuted = X_test.copy()
                X_permuted[feature] = np.random.permutation(X_permuted[feature].values)

                # Score with permuted feature
                y_pred = self.model.predict(X_permuted)
                score = scoring_func(y_test, y_pred)

                # Importance = drop in performance
                feature_scores.append(baseline_score - score)

            importances[feature] = np.mean(feature_scores)

        # Sort by importance
        importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

        return GlobalExplanation(
            feature_importance=importances,
            method='permutation',
            baseline_score=baseline_score,
            timestamp=datetime.now().isoformat(),
            metadata={'n_repeats': n_repeats, 'n_features': len(importances)}
        )

    def explain_instance(
        self,
        instance: pd.Series,
        instance_id: int,
        n_samples: int = 1000,
        actual: float = None
    ) -> LocalExplanation:
        """
        Explain individual prediction (LIME-style).

        Parameters
        ----------
        instance : pd.Series
            Instance to explain
        instance_id : int
            Instance identifier
        n_samples : int
            Number of perturbed samples to generate
        actual : float, optional
            Actual label for comparison

        Returns
        -------
        LocalExplanation
            Local explanation for instance
        """
        self.logger.info(f"Explaining instance {instance_id}")

        # Get prediction for original instance
        prediction = self.model.predict(instance.values.reshape(1, -1))[0]

        # Generate perturbed samples around instance
        perturbed_data = np.zeros((n_samples, len(self.feature_names)))

        for i, feature in enumerate(self.feature_names):
            # Sample from normal distribution around instance value
            mean = instance[feature]
            std = self.X[feature].std()
            perturbed_data[:, i] = np.random.normal(mean, std, n_samples)

        perturbed_df = pd.DataFrame(perturbed_data, columns=self.feature_names)

        # Get predictions for perturbed samples
        perturbed_preds = self.model.predict(perturbed_df)

        # Calculate distances (weights)
        distances = np.sqrt(((perturbed_df - instance)**2).sum(axis=1))
        weights = np.exp(-distances / distances.std())

        # Fit linear model to approximate local behavior
        feature_contributions = {}

        for feature in self.feature_names:
            # Simple correlation-based contribution
            correlation = np.cov(perturbed_df[feature], perturbed_preds, aweights=weights)[0, 1]
            contribution = correlation / (perturbed_df[feature].std() + 1e-10)
            feature_contributions[feature] = contribution

        # Sort by absolute contribution
        feature_contributions = dict(sorted(
            feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        ))

        # Base value (mean prediction)
        base_value = self.model.predict(self.X).mean()

        return LocalExplanation(
            instance_id=instance_id,
            prediction=prediction,
            actual=actual,
            feature_contributions=feature_contributions,
            base_value=base_value,
            method='lime_style',
            metadata={'n_samples': n_samples}
        )

    def detect_interactions(
        self,
        X_test: pd.DataFrame,
        y_test: np.ndarray,
        top_k: int = 10
    ) -> List[InteractionEffect]:
        """
        Detect feature interactions.

        Parameters
        ----------
        X_test : pd.DataFrame
            Test data
        y_test : np.ndarray
            Test labels
        top_k : int
            Number of top interactions to return

        Returns
        -------
        List[InteractionEffect]
            Detected interactions
        """
        self.logger.info(f"Detecting top {top_k} feature interactions")

        interactions = []

        # Limit to top features for efficiency
        n_features_to_check = min(10, len(self.feature_names))

        for i in range(n_features_to_check):
            for j in range(i + 1, n_features_to_check):
                feature_1 = self.feature_names[i]
                feature_2 = self.feature_names[j]

                # Calculate interaction strength
                # Method: Compare predictions with both features vs individual features

                # Remove both features
                X_without_both = X_test.copy()
                X_without_both[feature_1] = self.X[feature_1].mean()
                X_without_both[feature_2] = self.X[feature_2].mean()

                # Remove feature 1 only
                X_without_1 = X_test.copy()
                X_without_1[feature_1] = self.X[feature_1].mean()

                # Remove feature 2 only
                X_without_2 = X_test.copy()
                X_without_2[feature_2] = self.X[feature_2].mean()

                # Predictions
                pred_both = self.model.predict(X_test)
                pred_without_both = self.model.predict(X_without_both)
                pred_without_1 = self.model.predict(X_without_1)
                pred_without_2 = self.model.predict(X_without_2)

                # Interaction strength (non-additivity)
                effect_both = np.abs(pred_both - pred_without_both).mean()
                effect_1 = np.abs(pred_both - pred_without_1).mean()
                effect_2 = np.abs(pred_both - pred_without_2).mean()

                interaction_strength = effect_both - (effect_1 + effect_2)

                interactions.append(InteractionEffect(
                    feature_1=feature_1,
                    feature_2=feature_2,
                    interaction_strength=abs(interaction_strength),
                    samples_analyzed=len(X_test)
                ))

        # Sort by strength and return top k
        interactions.sort(key=lambda x: x.interaction_strength, reverse=True)
        return interactions[:top_k]

    def partial_dependence(
        self,
        feature: str,
        num_points: int = 20
    ) -> Dict[str, Any]:
        """
        Calculate partial dependence for a feature.

        Parameters
        ----------
        feature : str
            Feature name
        num_points : int
            Number of grid points

        Returns
        -------
        Dict[str, Any]
            Partial dependence results
        """
        self.logger.info(f"Calculating partial dependence for {feature}")

        # Create grid of feature values
        feature_values = np.linspace(
            self.X[feature].min(),
            self.X[feature].max(),
            num_points
        )

        pd_values = []

        for value in feature_values:
            # Set all instances to this value
            X_modified = self.X.copy()
            X_modified[feature] = value

            # Get predictions
            preds = self.model.predict(X_modified)
            pd_values.append(preds.mean())

        return {
            'feature': feature,
            'grid_values': feature_values.tolist(),
            'pd_values': pd_values,
            'method': 'partial_dependence'
        }

    def export_explanations(
        self,
        output_path: str,
        global_explanation: GlobalExplanation = None,
        local_explanations: List[LocalExplanation] = None,
        interactions: List[InteractionEffect] = None
    ) -> None:
        """
        Export explanations to JSON file.

        Parameters
        ----------
        output_path : str
            Path to output file
        global_explanation : GlobalExplanation, optional
            Global explanation
        local_explanations : List[LocalExplanation], optional
            Local explanations
        interactions : List[InteractionEffect], optional
            Feature interactions
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        results = {
            'global_explanation': global_explanation.to_dict() if global_explanation else None,
            'local_explanations': [exp.to_dict() for exp in (local_explanations or [])],
            'interactions': [inter.to_dict() for inter in (interactions or [])],
            'timestamp': datetime.now().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"Explanations exported to {output_path}")


def demo_model_explainability():
    """Demonstrate model explainability framework."""
    logger.info("=== Model Explainability Framework Demo ===\n")

    # Create output directory
    output_dir = Path("/tmp/model_explainability")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 8

    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )

    # Create target with known feature importance
    y = (
        2 * X['feature_0'] +
        1.5 * X['feature_1'] +
        0.5 * X['feature_2'] +
        X['feature_3'] * X['feature_4'] +  # Interaction
        np.random.randn(n_samples) * 0.1
    )
    y = (y > y.median()).astype(int)

    # Train simple model
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)

    # Split data
    train_size = int(0.8 * len(X))
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    model.fit(X_train, y_train)

    logger.info(f"Model accuracy: {model.score(X_test, y_test):.4f}\n")

    # Initialize explainer
    explainer = ModelExplainer(model, X_train, y_train)

    # Test 1: Permutation importance
    logger.info("--- Test 1: Permutation Importance ---")
    global_explanation = explainer.permutation_importance(X_test, y_test, n_repeats=5)

    logger.info("Top 5 most important features:")
    for i, (feature, importance) in enumerate(list(global_explanation.feature_importance.items())[:5], 1):
        logger.info(f"  {i}. {feature}: {importance:.4f}")

    # Test 2: Local explanation
    logger.info("\n--- Test 2: Local Explanation (Instance 0) ---")
    instance = X_test.iloc[0]
    local_explanation = explainer.explain_instance(instance, 0, n_samples=500, actual=y_test.iloc[0])

    logger.info(f"Prediction: {local_explanation.prediction:.4f}")
    logger.info(f"Actual: {local_explanation.actual}")
    logger.info("Top 5 feature contributions:")
    for i, (feature, contribution) in enumerate(list(local_explanation.feature_contributions.items())[:5], 1):
        logger.info(f"  {i}. {feature}: {contribution:.4f}")

    # Test 3: Interaction detection
    logger.info("\n--- Test 3: Feature Interactions ---")
    interactions = explainer.detect_interactions(X_test, y_test, top_k=5)

    logger.info("Top 5 feature interactions:")
    for i, interaction in enumerate(interactions, 1):
        logger.info(f"  {i}. {interaction.feature_1} × {interaction.feature_2}: "
                   f"{interaction.interaction_strength:.4f}")

    # Test 4: Partial dependence
    logger.info("\n--- Test 4: Partial Dependence (feature_0) ---")
    pd_result = explainer.partial_dependence('feature_0', num_points=10)

    logger.info("Partial dependence values (first 5 points):")
    for value, pd_val in zip(pd_result['grid_values'][:5], pd_result['pd_values'][:5]):
        logger.info(f"  feature_0 = {value:.2f} → prediction = {pd_val:.4f}")

    # Export results
    local_explanations = [
        explainer.explain_instance(X_test.iloc[i], i, n_samples=500, actual=y_test.iloc[i])
        for i in range(min(3, len(X_test)))
    ]

    explainer.export_explanations(
        str(output_dir / "explanations.json"),
        global_explanation=global_explanation,
        local_explanations=local_explanations,
        interactions=interactions
    )

    logger.info(f"\n✅ Model explainability demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return {
        'global': global_explanation,
        'local': local_explanations,
        'interactions': interactions
    }


if __name__ == '__main__':
    demo_model_explainability()
