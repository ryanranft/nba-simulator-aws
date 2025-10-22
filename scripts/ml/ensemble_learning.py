"""
Ensemble Learning and Model Stacking Framework

Implements multiple ensemble strategies for combining models:
- Voting ensembles (hard and soft voting)
- Averaging ensembles (simple and weighted averaging)
- Stacking (meta-learning from base model predictions)
- Blending (holdout-based stacking)
- Boosting ensembles (gradient boosting, AdaBoost)
- Bagging ensembles (bootstrap aggregating)

Author: NBA Simulator Project
Created: 2025-10-18
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
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
class EnsembleResult:
    """Store ensemble learning results."""
    ensemble_type: str
    n_base_models: int
    base_model_scores: Dict[str, float]
    ensemble_score: float
    improvement: float
    training_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ensemble_type': self.ensemble_type,
            'n_base_models': int(self.n_base_models),
            'base_model_scores': {k: float(v) for k, v in self.base_model_scores.items()},
            'ensemble_score': float(self.ensemble_score),
            'improvement': float(self.improvement),
            'training_time': float(self.training_time),
            'metadata': self.metadata
        }


class EnsembleLearner:
    """
    Comprehensive ensemble learning framework.
    """

    def __init__(self, task_type: str = 'classification'):
        """
        Initialize ensemble learner.

        Args:
            task_type: 'classification' or 'regression'
        """
        self.task_type = task_type
        logger.info(f"Initialized EnsembleLearner (task_type={task_type})")

    def voting_ensemble(self, X_train: pd.DataFrame, y_train: pd.Series,
                       X_test: pd.DataFrame, y_test: pd.Series,
                       voting: str = 'soft') -> EnsembleResult:
        """
        Create voting ensemble from multiple base models.

        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            voting: 'hard' or 'soft' voting

        Returns:
            EnsembleResult with scores
        """
        logger.info(f"Creating voting ensemble ({voting} voting)...")
        start_time = time.time()

        from sklearn.ensemble import VotingClassifier, VotingRegressor
        from sklearn.linear_model import LogisticRegression, Ridge
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

        # Create base models
        if self.task_type == 'classification':
            base_models = [
                ('logistic', LogisticRegression(random_state=42, max_iter=1000)),
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42))
            ]
            voting_ensemble = VotingClassifier(estimators=base_models, voting=voting)
        else:
            base_models = [
                ('ridge', Ridge(random_state=42)),
                ('rf', RandomForestRegressor(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingRegressor(n_estimators=100, random_state=42))
            ]
            voting_ensemble = VotingRegressor(estimators=base_models)

        # Train base models individually to get their scores
        base_scores = {}
        for name, model in base_models:
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            base_scores[name] = score
            logger.info(f"  {name}: {score:.4f}")

        # Train ensemble
        voting_ensemble.fit(X_train, y_train)
        ensemble_score = voting_ensemble.score(X_test, y_test)

        best_base_score = max(base_scores.values())
        improvement = ensemble_score - best_base_score

        elapsed_time = time.time() - start_time
        logger.info(f"Voting ensemble score: {ensemble_score:.4f}")
        logger.info(f"Best base model score: {best_base_score:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return EnsembleResult(
            ensemble_type=f'voting_{voting}',
            n_base_models=len(base_models),
            base_model_scores=base_scores,
            ensemble_score=ensemble_score,
            improvement=improvement,
            training_time=elapsed_time,
            metadata={'voting': voting}
        )

    def weighted_average_ensemble(self, X_train: pd.DataFrame, y_train: pd.Series,
                                  X_test: pd.DataFrame, y_test: pd.Series,
                                  weights: Optional[List[float]] = None) -> EnsembleResult:
        """
        Create weighted average ensemble.

        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            weights: Model weights (None = equal weights)

        Returns:
            EnsembleResult with scores
        """
        logger.info("Creating weighted average ensemble...")
        start_time = time.time()

        from sklearn.linear_model import Ridge, Lasso, ElasticNet
        from sklearn.metrics import r2_score, accuracy_score

        # Create base models
        if self.task_type == 'classification':
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

            base_models = {
                'logistic': LogisticRegression(random_state=42, max_iter=1000),
                'rf': RandomForestClassifier(n_estimators=100, random_state=42),
                'gb': GradientBoostingClassifier(n_estimators=100, random_state=42)
            }
        else:
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

            base_models = {
                'ridge': Ridge(alpha=1.0, random_state=42),
                'lasso': Lasso(alpha=1.0, random_state=42),
                'rf': RandomForestRegressor(n_estimators=100, random_state=42)
            }

        # Train base models and get predictions
        base_scores = {}
        predictions = {}

        for name, model in base_models.items():
            model.fit(X_train, y_train)

            if self.task_type == 'classification':
                pred = model.predict_proba(X_test)[:, 1]  # Probability of positive class
                score = accuracy_score(y_test, (pred > 0.5).astype(int))
            else:
                pred = model.predict(X_test)
                score = r2_score(y_test, pred)

            predictions[name] = pred
            base_scores[name] = score
            logger.info(f"  {name}: {score:.4f}")

        # Create weighted ensemble
        if weights is None:
            weights = [1.0 / len(base_models)] * len(base_models)

        # Normalize weights
        weights = np.array(weights)
        weights = weights / weights.sum()

        # Combine predictions
        pred_matrix = np.column_stack([predictions[name] for name in base_models.keys()])
        ensemble_pred = np.average(pred_matrix, axis=1, weights=weights)

        # Calculate ensemble score
        if self.task_type == 'classification':
            ensemble_score = accuracy_score(y_test, (ensemble_pred > 0.5).astype(int))
        else:
            ensemble_score = r2_score(y_test, ensemble_pred)

        best_base_score = max(base_scores.values())
        improvement = ensemble_score - best_base_score

        elapsed_time = time.time() - start_time
        logger.info(f"Weighted average ensemble score: {ensemble_score:.4f}")
        logger.info(f"Best base model score: {best_base_score:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return EnsembleResult(
            ensemble_type='weighted_average',
            n_base_models=len(base_models),
            base_model_scores=base_scores,
            ensemble_score=ensemble_score,
            improvement=improvement,
            training_time=elapsed_time,
            metadata={'weights': weights.tolist()}
        )

    def stacking_ensemble(self, X_train: pd.DataFrame, y_train: pd.Series,
                         X_test: pd.DataFrame, y_test: pd.Series,
                         cv_folds: int = 5) -> EnsembleResult:
        """
        Create stacking ensemble with meta-learner.

        Base models make predictions, meta-learner combines them.

        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            cv_folds: Number of CV folds for stacking

        Returns:
            EnsembleResult with scores
        """
        logger.info(f"Creating stacking ensemble (cv_folds={cv_folds})...")
        start_time = time.time()

        from sklearn.ensemble import StackingClassifier, StackingRegressor
        from sklearn.linear_model import LogisticRegression, Ridge
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

        # Create base models
        if self.task_type == 'classification':
            base_models = [
                ('logistic', LogisticRegression(random_state=42, max_iter=1000)),
                ('rf', RandomForestClassifier(n_estimators=50, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=50, random_state=42))
            ]
            meta_learner = LogisticRegression(random_state=42)
            stacking_model = StackingClassifier(
                estimators=base_models,
                final_estimator=meta_learner,
                cv=cv_folds
            )
        else:
            base_models = [
                ('ridge', Ridge(alpha=1.0, random_state=42)),
                ('rf', RandomForestRegressor(n_estimators=50, random_state=42)),
                ('gb', GradientBoostingRegressor(n_estimators=50, random_state=42))
            ]
            meta_learner = Ridge(alpha=1.0, random_state=42)
            stacking_model = StackingRegressor(
                estimators=base_models,
                final_estimator=meta_learner,
                cv=cv_folds
            )

        # Train base models individually to get their scores
        base_scores = {}
        for name, model in base_models:
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            base_scores[name] = score
            logger.info(f"  {name}: {score:.4f}")

        # Train stacking ensemble
        stacking_model.fit(X_train, y_train)
        ensemble_score = stacking_model.score(X_test, y_test)

        best_base_score = max(base_scores.values())
        improvement = ensemble_score - best_base_score

        elapsed_time = time.time() - start_time
        logger.info(f"Stacking ensemble score: {ensemble_score:.4f}")
        logger.info(f"Best base model score: {best_base_score:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return EnsembleResult(
            ensemble_type='stacking',
            n_base_models=len(base_models),
            base_model_scores=base_scores,
            ensemble_score=ensemble_score,
            improvement=improvement,
            training_time=elapsed_time,
            metadata={'cv_folds': cv_folds, 'meta_learner': type(meta_learner).__name__}
        )

    def bagging_ensemble(self, X_train: pd.DataFrame, y_train: pd.Series,
                        X_test: pd.DataFrame, y_test: pd.Series,
                        n_estimators: int = 100) -> EnsembleResult:
        """
        Create bagging ensemble (bootstrap aggregating).

        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            n_estimators: Number of base estimators

        Returns:
            EnsembleResult with scores
        """
        logger.info(f"Creating bagging ensemble (n_estimators={n_estimators})...")
        start_time = time.time()

        from sklearn.ensemble import BaggingClassifier, BaggingRegressor
        from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

        # Create base estimator
        if self.task_type == 'classification':
            base_estimator = DecisionTreeClassifier(random_state=42)
            bagging_model = BaggingClassifier(
                estimator=base_estimator,  # Changed from base_estimator to estimator
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1
            )
        else:
            base_estimator = DecisionTreeRegressor(random_state=42)
            bagging_model = BaggingRegressor(
                estimator=base_estimator,  # Changed from base_estimator to estimator
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1
            )

        # Train single base estimator for comparison
        base_estimator.fit(X_train, y_train)
        base_score = base_estimator.score(X_test, y_test)
        logger.info(f"  Single decision tree: {base_score:.4f}")

        # Train bagging ensemble
        bagging_model.fit(X_train, y_train)
        ensemble_score = bagging_model.score(X_test, y_test)

        improvement = ensemble_score - base_score

        elapsed_time = time.time() - start_time
        logger.info(f"Bagging ensemble score: {ensemble_score:.4f}")
        logger.info(f"Base model score: {base_score:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return EnsembleResult(
            ensemble_type='bagging',
            n_base_models=n_estimators,
            base_model_scores={'decision_tree': base_score},
            ensemble_score=ensemble_score,
            improvement=improvement,
            training_time=elapsed_time,
            metadata={'n_estimators': n_estimators}
        )

    def boosting_ensemble(self, X_train: pd.DataFrame, y_train: pd.Series,
                         X_test: pd.DataFrame, y_test: pd.Series,
                         n_estimators: int = 100) -> EnsembleResult:
        """
        Create gradient boosting ensemble.

        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            n_estimators: Number of boosting stages

        Returns:
            EnsembleResult with scores
        """
        logger.info(f"Creating boosting ensemble (n_estimators={n_estimators})...")
        start_time = time.time()

        from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
        from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

        # Create base estimator for comparison
        if self.task_type == 'classification':
            base_estimator = DecisionTreeClassifier(random_state=42)
            boosting_model = GradientBoostingClassifier(
                n_estimators=n_estimators,
                random_state=42
            )
        else:
            base_estimator = DecisionTreeRegressor(random_state=42)
            boosting_model = GradientBoostingRegressor(
                n_estimators=n_estimators,
                random_state=42
            )

        # Train single base estimator for comparison
        base_estimator.fit(X_train, y_train)
        base_score = base_estimator.score(X_test, y_test)
        logger.info(f"  Single decision tree: {base_score:.4f}")

        # Train boosting ensemble
        boosting_model.fit(X_train, y_train)
        ensemble_score = boosting_model.score(X_test, y_test)

        improvement = ensemble_score - base_score

        elapsed_time = time.time() - start_time
        logger.info(f"Boosting ensemble score: {ensemble_score:.4f}")
        logger.info(f"Base model score: {base_score:.4f}")
        logger.info(f"Improvement: {improvement:+.4f}")

        return EnsembleResult(
            ensemble_type='boosting',
            n_base_models=n_estimators,
            base_model_scores={'decision_tree': base_score},
            ensemble_score=ensemble_score,
            improvement=improvement,
            training_time=elapsed_time,
            metadata={'n_estimators': n_estimators}
        )

    def export_results(self, output_path: str, results: Dict[str, Any]):
        """Export ensemble results to JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_ensemble_learning():
    """Demonstrate ensemble learning with synthetic data."""
    logger.info("Starting ensemble learning demo...")

    # Create synthetic classification data
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

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

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    logger.info(f"Created dataset: {len(X_train)} train, {len(X_test)} test samples")
    logger.info(f"Class distribution: {y.value_counts().to_dict()}")

    # Initialize learner
    learner = EnsembleLearner(task_type='classification')

    # Test 1: Soft Voting Ensemble
    logger.info("\n=== Test 1: Soft Voting Ensemble ===")
    voting_result = learner.voting_ensemble(X_train, y_train, X_test, y_test, voting='soft')

    # Test 2: Weighted Average Ensemble
    logger.info("\n=== Test 2: Weighted Average Ensemble ===")
    weighted_result = learner.weighted_average_ensemble(X_train, y_train, X_test, y_test)

    # Test 3: Stacking Ensemble
    logger.info("\n=== Test 3: Stacking Ensemble ===")
    stacking_result = learner.stacking_ensemble(X_train, y_train, X_test, y_test, cv_folds=5)

    # Test 4: Bagging Ensemble
    logger.info("\n=== Test 4: Bagging Ensemble ===")
    bagging_result = learner.bagging_ensemble(X_train, y_train, X_test, y_test, n_estimators=100)

    # Test 5: Boosting Ensemble
    logger.info("\n=== Test 5: Boosting Ensemble ===")
    boosting_result = learner.boosting_ensemble(X_train, y_train, X_test, y_test, n_estimators=100)

    # Export results
    output_dir = Path("/tmp/ensemble_learning")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'n_features': len(X.columns),
            'task_type': 'classification'
        },
        'voting_soft': voting_result.to_dict(),
        'weighted_average': weighted_result.to_dict(),
        'stacking': stacking_result.to_dict(),
        'bagging': bagging_result.to_dict(),
        'boosting': boosting_result.to_dict()
    }

    learner.export_results(str(output_dir / "ensemble_results.json"), results)

    # Summary
    logger.info("\n=== Ensemble Learning Results Summary ===")
    for name, result in [
        ('Soft Voting', voting_result),
        ('Weighted Average', weighted_result),
        ('Stacking', stacking_result),
        ('Bagging', bagging_result),
        ('Boosting', boosting_result)
    ]:
        logger.info(f"{name:20s}: Score={result.ensemble_score:.4f}, "
                   f"Improvement={result.improvement:+.4f}, "
                   f"Time={result.training_time:.2f}s")

    logger.info(f"\n✅ Ensemble learning demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_ensemble_learning()
