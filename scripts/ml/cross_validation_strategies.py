"""
Cross-Validation Strategies Framework

Implements advanced cross-validation techniques for panel data and time series:
- Time series cross-validation (expanding/sliding windows)
- Blocked time series CV (respecting temporal ordering)
- Group K-Fold (for panel data with entities)
- Stratified K-Fold (maintaining class distributions)
- Leave-One-Group-Out (LOGO)
- Custom CV splitters for panel data
- CV strategy selection and comparison

Author: NBA Simulator Project
Created: 2025-10-18
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Iterator
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
class CVResult:
    """Store cross-validation results."""
    strategy_name: str
    n_splits: int
    scores: List[float]
    mean_score: float
    std_score: float
    min_score: float
    max_score: float
    cv_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'strategy_name': self.strategy_name,
            'n_splits': int(self.n_splits),
            'scores': [float(x) for x in self.scores],
            'mean_score': float(self.mean_score),
            'std_score': float(self.std_score),
            'min_score': float(self.min_score),
            'max_score': float(self.max_score),
            'cv_time': float(self.cv_time),
            'metadata': self.metadata
        }


class CrossValidationStrategies:
    """
    Advanced cross-validation strategies for panel data and time series.
    """

    def __init__(self, scoring: str = 'accuracy'):
        """
        Initialize CV strategies.

        Args:
            scoring: Scoring metric
        """
        self.scoring = scoring
        logger.info(f"Initialized CrossValidationStrategies (scoring={scoring})")

    def time_series_cv(self, model: Any, X: pd.DataFrame, y: pd.Series,
                       n_splits: int = 5,
                       test_size: Optional[int] = None,
                       gap: int = 0) -> CVResult:
        """
        Time series cross-validation with expanding window.

        Maintains temporal ordering - training always before test.

        Args:
            model: ML model
            X: Feature matrix
            y: Target variable
            n_splits: Number of splits
            test_size: Size of test set
            gap: Gap between train and test (to avoid leakage)

        Returns:
            CVResult with scores
        """
        logger.info(f"Running time series CV (n_splits={n_splits}, gap={gap})...")
        start_time = time.time()

        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.metrics import get_scorer

        # Create splitter
        tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size, gap=gap)

        # Perform CV
        scorer = get_scorer(self.scoring)
        scores = []

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model.fit(X_train, y_train)
            score = scorer(model, X_test, y_test)
            scores.append(score)

            logger.info(f"  Fold {fold}/{n_splits}: Score = {score:.4f}, "
                       f"Train size = {len(train_idx)}, Test size = {len(test_idx)}")

        elapsed_time = time.time() - start_time

        return CVResult(
            strategy_name='time_series_cv',
            n_splits=n_splits,
            scores=scores,
            mean_score=float(np.mean(scores)),
            std_score=float(np.std(scores)),
            min_score=float(np.min(scores)),
            max_score=float(np.max(scores)),
            cv_time=elapsed_time,
            metadata={'gap': gap, 'test_size': test_size}
        )

    def blocked_time_series_cv(self, model: Any, X: pd.DataFrame, y: pd.Series,
                               groups: pd.Series,
                               n_splits: int = 5) -> CVResult:
        """
        Blocked time series CV for panel data.

        Respects both entity structure and temporal ordering.

        Args:
            model: ML model
            X: Feature matrix
            y: Target variable
            groups: Entity/group identifiers
            n_splits: Number of splits

        Returns:
            CVResult with scores
        """
        logger.info(f"Running blocked time series CV (n_splits={n_splits})...")
        start_time = time.time()

        from sklearn.metrics import get_scorer

        # Create time-based splits
        n_samples = len(X)
        split_size = n_samples // (n_splits + 1)

        scorer = get_scorer(self.scoring)
        scores = []

        for fold in range(1, n_splits + 1):
            # Expanding window: train on [0, fold*split_size], test on [fold*split_size, (fold+1)*split_size]
            train_end = fold * split_size
            test_start = train_end
            test_end = min(test_start + split_size, n_samples)

            train_idx = np.arange(0, train_end)
            test_idx = np.arange(test_start, test_end)

            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model.fit(X_train, y_train)
            score = scorer(model, X_test, y_test)
            scores.append(score)

            # Count unique groups
            train_groups = groups.iloc[train_idx].nunique()
            test_groups = groups.iloc[test_idx].nunique()

            logger.info(f"  Fold {fold}/{n_splits}: Score = {score:.4f}, "
                       f"Train groups = {train_groups}, Test groups = {test_groups}")

        elapsed_time = time.time() - start_time

        return CVResult(
            strategy_name='blocked_time_series_cv',
            n_splits=n_splits,
            scores=scores,
            mean_score=float(np.mean(scores)),
            std_score=float(np.std(scores)),
            min_score=float(np.min(scores)),
            max_score=float(np.max(scores)),
            cv_time=elapsed_time,
            metadata={'unique_groups': int(groups.nunique())}
        )

    def group_kfold_cv(self, model: Any, X: pd.DataFrame, y: pd.Series,
                       groups: pd.Series,
                       n_splits: int = 5) -> CVResult:
        """
        Group K-Fold cross-validation.

        Ensures same group doesn't appear in both train and test.

        Args:
            model: ML model
            X: Feature matrix
            y: Target variable
            groups: Group identifiers
            n_splits: Number of splits

        Returns:
            CVResult with scores
        """
        logger.info(f"Running Group K-Fold CV (n_splits={n_splits})...")
        start_time = time.time()

        from sklearn.model_selection import GroupKFold
        from sklearn.metrics import get_scorer

        # Create splitter
        gkf = GroupKFold(n_splits=n_splits)

        # Perform CV
        scorer = get_scorer(self.scoring)
        scores = []

        for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups), 1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model.fit(X_train, y_train)
            score = scorer(model, X_test, y_test)
            scores.append(score)

            # Count unique groups
            train_groups = groups.iloc[train_idx].nunique()
            test_groups = groups.iloc[test_idx].nunique()

            logger.info(f"  Fold {fold}/{n_splits}: Score = {score:.4f}, "
                       f"Train groups = {train_groups}, Test groups = {test_groups}")

        elapsed_time = time.time() - start_time

        return CVResult(
            strategy_name='group_kfold_cv',
            n_splits=n_splits,
            scores=scores,
            mean_score=float(np.mean(scores)),
            std_score=float(np.std(scores)),
            min_score=float(np.min(scores)),
            max_score=float(np.max(scores)),
            cv_time=elapsed_time,
            metadata={'unique_groups': int(groups.nunique())}
        )

    def stratified_kfold_cv(self, model: Any, X: pd.DataFrame, y: pd.Series,
                           n_splits: int = 5) -> CVResult:
        """
        Stratified K-Fold cross-validation.

        Maintains class distribution in each fold.

        Args:
            model: ML model
            X: Feature matrix
            y: Target variable
            n_splits: Number of splits

        Returns:
            CVResult with scores
        """
        logger.info(f"Running Stratified K-Fold CV (n_splits={n_splits})...")
        start_time = time.time()

        from sklearn.model_selection import StratifiedKFold
        from sklearn.metrics import get_scorer

        # Create splitter
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        # Perform CV
        scorer = get_scorer(self.scoring)
        scores = []

        for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model.fit(X_train, y_train)
            score = scorer(model, X_test, y_test)
            scores.append(score)

            # Check class distribution
            train_dist = y_train.value_counts(normalize=True).to_dict()
            test_dist = y_test.value_counts(normalize=True).to_dict()

            logger.info(f"  Fold {fold}/{n_splits}: Score = {score:.4f}")

        elapsed_time = time.time() - start_time

        return CVResult(
            strategy_name='stratified_kfold_cv',
            n_splits=n_splits,
            scores=scores,
            mean_score=float(np.mean(scores)),
            std_score=float(np.std(scores)),
            min_score=float(np.min(scores)),
            max_score=float(np.max(scores)),
            cv_time=elapsed_time,
            metadata={'class_distribution': y.value_counts(normalize=True).to_dict()}
        )

    def leave_one_group_out_cv(self, model: Any, X: pd.DataFrame, y: pd.Series,
                               groups: pd.Series) -> CVResult:
        """
        Leave-One-Group-Out cross-validation.

        Each group is used as test set once.

        Args:
            model: ML model
            X: Feature matrix
            y: Target variable
            groups: Group identifiers

        Returns:
            CVResult with scores
        """
        logger.info("Running Leave-One-Group-Out CV...")
        start_time = time.time()

        from sklearn.model_selection import LeaveOneGroupOut
        from sklearn.metrics import get_scorer

        # Create splitter
        logo = LeaveOneGroupOut()

        # Perform CV
        scorer = get_scorer(self.scoring)
        scores = []

        n_groups = groups.nunique()
        for fold, (train_idx, test_idx) in enumerate(logo.split(X, y, groups), 1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model.fit(X_train, y_train)
            score = scorer(model, X_test, y_test)
            scores.append(score)

            test_group = groups.iloc[test_idx].iloc[0]
            
            if fold % max(1, n_groups // 10) == 0:  # Log every 10%
                logger.info(f"  Fold {fold}/{n_groups}: Score = {score:.4f}, "
                           f"Test group = {test_group}")

        elapsed_time = time.time() - start_time

        logger.info(f"Completed {len(scores)} folds in {elapsed_time:.2f}s")

        return CVResult(
            strategy_name='leave_one_group_out_cv',
            n_splits=len(scores),
            scores=scores,
            mean_score=float(np.mean(scores)),
            std_score=float(np.std(scores)),
            min_score=float(np.min(scores)),
            max_score=float(np.max(scores)),
            cv_time=elapsed_time,
            metadata={'n_groups': int(n_groups)}
        )

    def compare_strategies(self, model: Any, X: pd.DataFrame, y: pd.Series,
                          groups: Optional[pd.Series] = None,
                          strategies: Optional[List[str]] = None) -> Dict[str, CVResult]:
        """
        Compare multiple CV strategies.

        Args:
            model: ML model
            X: Feature matrix
            y: Target variable
            groups: Group identifiers (optional, needed for group-based CV)
            strategies: List of strategies to compare

        Returns:
            Dictionary of CVResult objects
        """
        logger.info("Comparing CV strategies...")

        if strategies is None:
            strategies = ['time_series', 'stratified_kfold']
            if groups is not None:
                strategies.extend(['group_kfold', 'blocked_time_series'])

        results = {}

        for strategy in strategies:
            logger.info(f"\n=== Testing {strategy} ===")
            
            if strategy == 'time_series':
                result = self.time_series_cv(model, X, y, n_splits=5)
            elif strategy == 'stratified_kfold':
                result = self.stratified_kfold_cv(model, X, y, n_splits=5)
            elif strategy == 'group_kfold' and groups is not None:
                result = self.group_kfold_cv(model, X, y, groups, n_splits=5)
            elif strategy == 'blocked_time_series' and groups is not None:
                result = self.blocked_time_series_cv(model, X, y, groups, n_splits=5)
            else:
                logger.warning(f"Strategy {strategy} not available or missing groups")
                continue

            results[strategy] = result

        return results

    def export_results(self, output_path: str, results: Dict[str, Any]):
        """Export CV results to JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_cv_strategies():
    """Demonstrate cross-validation strategies with synthetic data."""
    logger.info("Starting CV strategies demo...")

    # Create synthetic panel data
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression

    np.random.seed(42)

    # Generate data with groups (entities)
    n_groups = 20
    n_per_group = 100
    n_samples = n_groups * n_per_group

    # Generate features and target
    X, y = make_classification(
        n_samples=n_samples,
        n_features=20,
        n_informative=15,
        n_classes=2,
        random_state=42
    )

    # Create groups (entities) - each entity has multiple observations
    groups = np.repeat(np.arange(n_groups), n_per_group)

    # Convert to DataFrame/Series
    X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(20)])
    y = pd.Series(y)
    groups = pd.Series(groups, name='entity_id')

    logger.info(f"Created panel dataset:")
    logger.info(f"  Total samples: {n_samples}")
    logger.info(f"  Unique entities: {n_groups}")
    logger.info(f"  Observations per entity: {n_per_group}")

    # Initialize CV strategies
    cv_strategies = CrossValidationStrategies(scoring='accuracy')

    # Create model
    model = LogisticRegression(random_state=42, max_iter=1000)

    # Test 1: Time Series CV
    logger.info("\n=== Test 1: Time Series CV ===")
    ts_result = cv_strategies.time_series_cv(model, X, y, n_splits=5, gap=10)

    # Test 2: Blocked Time Series CV
    logger.info("\n=== Test 2: Blocked Time Series CV ===")
    blocked_result = cv_strategies.blocked_time_series_cv(model, X, y, groups, n_splits=5)

    # Test 3: Group K-Fold CV
    logger.info("\n=== Test 3: Group K-Fold CV ===")
    group_result = cv_strategies.group_kfold_cv(model, X, y, groups, n_splits=5)

    # Test 4: Stratified K-Fold CV
    logger.info("\n=== Test 4: Stratified K-Fold CV ===")
    stratified_result = cv_strategies.stratified_kfold_cv(model, X, y, n_splits=5)

    # Test 5: Leave-One-Group-Out CV (on subset)
    logger.info("\n=== Test 5: Leave-One-Group-Out CV (subset) ===")
    # Use only first 5 groups for LOGO (faster demo)
    subset_mask = groups < 5
    X_subset = X[subset_mask]
    y_subset = y[subset_mask]
    groups_subset = groups[subset_mask]
    
    logo_result = cv_strategies.leave_one_group_out_cv(
        model, X_subset, y_subset, groups_subset
    )

    # Export results
    output_dir = Path("/tmp/cv_strategies")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'n_samples': n_samples,
            'n_groups': n_groups,
            'n_features': X.shape[1]
        },
        'time_series_cv': ts_result.to_dict(),
        'blocked_time_series_cv': blocked_result.to_dict(),
        'group_kfold_cv': group_result.to_dict(),
        'stratified_kfold_cv': stratified_result.to_dict(),
        'leave_one_group_out_cv': logo_result.to_dict()
    }

    cv_strategies.export_results(str(output_dir / "cv_results.json"), results)

    # Summary
    logger.info("\n=== CV Strategy Comparison ===")
    for name, result in [
        ('Time Series CV', ts_result),
        ('Blocked Time Series CV', blocked_result),
        ('Group K-Fold CV', group_result),
        ('Stratified K-Fold CV', stratified_result),
        ('Leave-One-Group-Out CV', logo_result)
    ]:
        logger.info(f"{name:30s}: Mean = {result.mean_score:.4f}, "
                   f"Std = {result.std_score:.4f}, "
                   f"Splits = {result.n_splits}")

    # Find most stable strategy (lowest std)
    all_results = [ts_result, blocked_result, group_result, stratified_result, logo_result]
    most_stable = min(all_results, key=lambda x: x.std_score)
    logger.info(f"\nMost stable strategy: {most_stable.strategy_name}")
    logger.info(f"  Mean score: {most_stable.mean_score:.4f}")
    logger.info(f"  Std score: {most_stable.std_score:.4f}")

    logger.info(f"\n✅ CV strategies demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_cv_strategies()
