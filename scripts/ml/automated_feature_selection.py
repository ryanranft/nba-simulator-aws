"""
Automated Feature Selection Framework

Implements multiple feature selection strategies for panel data and ML models:
- Filter methods (correlation, variance, mutual information)
- Wrapper methods (recursive feature elimination, sequential selection)
- Embedded methods (Lasso, tree-based importance, regularization paths)
- Stability analysis (selection consistency across samples)
- Panel-specific selection (within/between entity variance)

Author: NBA Simulator Project
Created: 2025-10-18
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
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
class FeatureScore:
    """Store feature selection scores."""
    feature_name: str
    score: float
    rank: int
    method: str
    p_value: Optional[float] = None
    selected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'feature_name': self.feature_name,
            'score': float(self.score),
            'rank': int(self.rank),
            'method': self.method,
            'p_value': float(self.p_value) if self.p_value is not None else None,
            'selected': bool(self.selected)
        }


@dataclass
class SelectionResult:
    """Store feature selection results."""
    method: str
    n_features_selected: int
    selected_features: List[str]
    feature_scores: List[FeatureScore]
    selection_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'method': self.method,
            'n_features_selected': int(self.n_features_selected),
            'selected_features': self.selected_features,
            'feature_scores': [fs.to_dict() for fs in self.feature_scores],
            'selection_time': float(self.selection_time),
            'metadata': self.metadata
        }


class FeatureSelector:
    """
    Comprehensive feature selection framework with multiple strategies.
    """

    def __init__(self, n_features_to_select: Optional[int] = None,
                 selection_threshold: float = 0.05):
        """
        Initialize feature selector.

        Args:
            n_features_to_select: Number of features to select (None = auto)
            selection_threshold: P-value threshold for statistical methods
        """
        self.n_features_to_select = n_features_to_select
        self.selection_threshold = selection_threshold

        logger.info(f"Initialized FeatureSelector (n_features={n_features_to_select}, "
                   f"threshold={selection_threshold})")

    def variance_threshold_selection(self, X: pd.DataFrame,
                                     threshold: float = 0.01) -> SelectionResult:
        """
        Select features with variance above threshold.

        Removes features with low variance (near-constant features).

        Args:
            X: Feature matrix
            threshold: Minimum variance threshold

        Returns:
            SelectionResult with selected features
        """
        logger.info(f"Running variance threshold selection (threshold={threshold})...")
        start_time = time.time()

        # Calculate variance for each feature
        variances = X.var()

        # Select features above threshold
        selected_mask = variances > threshold
        selected_features = variances[selected_mask].index.tolist()

        # Create feature scores
        feature_scores = []
        for rank, (feature, variance) in enumerate(
            variances.sort_values(ascending=False).items(), 1
        ):
            feature_scores.append(FeatureScore(
                feature_name=feature,
                score=float(variance),
                rank=rank,
                method='variance_threshold',
                selected=feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='variance_threshold',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={'threshold': threshold}
        )

    def correlation_selection(self, X: pd.DataFrame, y: pd.Series,
                             threshold: float = 0.1) -> SelectionResult:
        """
        Select features based on correlation with target.

        Args:
            X: Feature matrix
            y: Target variable
            threshold: Minimum absolute correlation

        Returns:
            SelectionResult with selected features
        """
        logger.info(f"Running correlation selection (threshold={threshold})...")
        start_time = time.time()

        # Calculate correlations with target
        correlations = pd.Series({
            col: X[col].corr(y) for col in X.columns
        })

        # Select features above threshold
        selected_mask = correlations.abs() > threshold
        selected_features = correlations[selected_mask].index.tolist()

        # Create feature scores
        feature_scores = []
        for rank, (feature, corr) in enumerate(
            correlations.abs().sort_values(ascending=False).items(), 1
        ):
            feature_scores.append(FeatureScore(
                feature_name=feature,
                score=float(abs(corr)),
                rank=rank,
                method='correlation',
                selected=feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='correlation',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={'threshold': threshold}
        )

    def mutual_information_selection(self, X: pd.DataFrame, y: pd.Series,
                                     k: Optional[int] = None) -> SelectionResult:
        """
        Select features based on mutual information with target.

        Measures how much information each feature provides about the target.

        Args:
            X: Feature matrix
            y: Target variable
            k: Number of features to select (None = use n_features_to_select)

        Returns:
            SelectionResult with selected features
        """
        logger.info("Running mutual information selection...")
        start_time = time.time()

        from sklearn.feature_selection import mutual_info_regression, mutual_info_classif

        # Determine if regression or classification
        is_classification = len(np.unique(y)) < 20

        # Calculate mutual information
        if is_classification:
            mi_scores = mutual_info_classif(X, y, random_state=42)
        else:
            mi_scores = mutual_info_regression(X, y, random_state=42)

        # Create DataFrame for sorting
        mi_df = pd.DataFrame({
            'feature': X.columns,
            'mi_score': mi_scores
        }).sort_values('mi_score', ascending=False)

        # Select top k features
        k = k or self.n_features_to_select or len(X.columns) // 2
        selected_features = mi_df.head(k)['feature'].tolist()

        # Create feature scores
        feature_scores = []
        for rank, row in enumerate(mi_df.itertuples(), 1):
            feature_scores.append(FeatureScore(
                feature_name=row.feature,
                score=float(row.mi_score),
                rank=rank,
                method='mutual_information',
                selected=row.feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='mutual_information',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={'k': k, 'is_classification': is_classification}
        )

    def lasso_selection(self, X: pd.DataFrame, y: pd.Series,
                       alpha: float = 1.0) -> SelectionResult:
        """
        Select features using Lasso (L1 regularization).

        Lasso drives coefficients of unimportant features to exactly zero.

        Args:
            X: Feature matrix
            y: Target variable
            alpha: Regularization strength

        Returns:
            SelectionResult with selected features
        """
        logger.info(f"Running Lasso selection (alpha={alpha})...")
        start_time = time.time()

        from sklearn.linear_model import Lasso
        from sklearn.preprocessing import StandardScaler

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Fit Lasso
        lasso = Lasso(alpha=alpha, random_state=42)
        lasso.fit(X_scaled, y)

        # Get non-zero coefficients
        non_zero_mask = lasso.coef_ != 0
        selected_features = X.columns[non_zero_mask].tolist()

        # Create feature scores (absolute coefficients)
        coef_df = pd.DataFrame({
            'feature': X.columns,
            'coefficient': np.abs(lasso.coef_)
        }).sort_values('coefficient', ascending=False)

        feature_scores = []
        for rank, row in enumerate(coef_df.itertuples(), 1):
            feature_scores.append(FeatureScore(
                feature_name=row.feature,
                score=float(row.coefficient),
                rank=rank,
                method='lasso',
                selected=row.feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='lasso',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={'alpha': alpha, 'n_non_zero': int(non_zero_mask.sum())}
        )

    def tree_based_selection(self, X: pd.DataFrame, y: pd.Series,
                            k: Optional[int] = None) -> SelectionResult:
        """
        Select features using tree-based feature importance.

        Uses Random Forest to rank feature importance.

        Args:
            X: Feature matrix
            y: Target variable
            k: Number of features to select

        Returns:
            SelectionResult with selected features
        """
        logger.info("Running tree-based selection...")
        start_time = time.time()

        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

        # Determine if regression or classification
        is_classification = len(np.unique(y)) < 20

        # Train Random Forest
        if is_classification:
            model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

        model.fit(X, y)

        # Get feature importances
        importance_df = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        # Select top k features
        k = k or self.n_features_to_select or len(X.columns) // 2
        selected_features = importance_df.head(k)['feature'].tolist()

        # Create feature scores
        feature_scores = []
        for rank, row in enumerate(importance_df.itertuples(), 1):
            feature_scores.append(FeatureScore(
                feature_name=row.feature,
                score=float(row.importance),
                rank=rank,
                method='tree_based',
                selected=row.feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='tree_based',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={'k': k, 'is_classification': is_classification}
        )

    def recursive_feature_elimination(self, X: pd.DataFrame, y: pd.Series,
                                     k: Optional[int] = None,
                                     step: int = 1) -> SelectionResult:
        """
        Select features using Recursive Feature Elimination (RFE).

        Recursively removes least important features.

        Args:
            X: Feature matrix
            y: Target variable
            k: Number of features to select
            step: Number of features to remove at each iteration

        Returns:
            SelectionResult with selected features
        """
        logger.info(f"Running RFE (k={k}, step={step})...")
        start_time = time.time()

        from sklearn.feature_selection import RFE
        from sklearn.linear_model import Ridge

        # Determine k
        k = k or self.n_features_to_select or len(X.columns) // 2

        # Create estimator
        estimator = Ridge(alpha=1.0)

        # Run RFE
        rfe = RFE(estimator=estimator, n_features_to_select=k, step=step)
        rfe.fit(X, y)

        # Get selected features
        selected_features = X.columns[rfe.support_].tolist()

        # Create feature scores (inverse of ranking)
        ranking_df = pd.DataFrame({
            'feature': X.columns,
            'ranking': rfe.ranking_
        }).sort_values('ranking')

        feature_scores = []
        for row in ranking_df.itertuples():
            # Convert ranking to score (lower rank = higher score)
            score = 1.0 / row.ranking
            feature_scores.append(FeatureScore(
                feature_name=row.feature,
                score=float(score),
                rank=int(row.ranking),
                method='rfe',
                selected=row.feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='rfe',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={'k': k, 'step': step}
        )

    def stability_selection(self, X: pd.DataFrame, y: pd.Series,
                           n_iterations: int = 100,
                           threshold: float = 0.6) -> SelectionResult:
        """
        Select features using stability selection.

        Features selected consistently across bootstrap samples are chosen.

        Args:
            X: Feature matrix
            y: Target variable
            n_iterations: Number of bootstrap iterations
            threshold: Minimum selection frequency

        Returns:
            SelectionResult with selected features
        """
        logger.info(f"Running stability selection (n_iter={n_iterations}, "
                   f"threshold={threshold})...")
        start_time = time.time()

        from sklearn.linear_model import Lasso
        from sklearn.preprocessing import StandardScaler

        # Track selection frequency
        selection_counts = pd.Series(0, index=X.columns)

        # Bootstrap sampling
        n_samples = len(X)
        scaler = StandardScaler()

        for i in range(n_iterations):
            # Bootstrap sample
            indices = np.random.choice(n_samples, n_samples, replace=True)
            X_boot = X.iloc[indices]
            y_boot = y.iloc[indices]

            # Standardize
            X_scaled = pd.DataFrame(
                scaler.fit_transform(X_boot),
                columns=X_boot.columns
            )

            # Fit Lasso
            lasso = Lasso(alpha=0.01, random_state=42)
            lasso.fit(X_scaled, y_boot)

            # Count non-zero coefficients
            selected = X_boot.columns[lasso.coef_ != 0]
            selection_counts[selected] += 1

            if (i + 1) % 20 == 0:
                logger.info(f"  Completed {i + 1}/{n_iterations} iterations")

        # Calculate selection frequencies
        selection_freq = selection_counts / n_iterations

        # Select features above threshold
        selected_features = selection_freq[selection_freq >= threshold].index.tolist()

        # Create feature scores
        freq_df = selection_freq.sort_values(ascending=False)
        feature_scores = []
        for rank, (feature, freq) in enumerate(freq_df.items(), 1):
            feature_scores.append(FeatureScore(
                feature_name=feature,
                score=float(freq),
                rank=rank,
                method='stability',
                selected=feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='stability',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={
                'n_iterations': n_iterations,
                'threshold': threshold
            }
        )

    def consensus_selection(self, X: pd.DataFrame, y: pd.Series,
                           methods: Optional[List[str]] = None,
                           min_votes: int = 3) -> SelectionResult:
        """
        Select features using consensus across multiple methods.

        Features selected by multiple methods are chosen.

        Args:
            X: Feature matrix
            y: Target variable
            methods: List of methods to use (None = all)
            min_votes: Minimum number of methods that must select feature

        Returns:
            SelectionResult with selected features
        """
        logger.info(f"Running consensus selection (min_votes={min_votes})...")
        start_time = time.time()

        # Default methods
        if methods is None:
            methods = ['correlation', 'mutual_information', 'lasso',
                      'tree_based', 'rfe']

        # Run each method
        results = {}
        for method in methods:
            logger.info(f"  Running {method}...")
            if method == 'correlation':
                result = self.correlation_selection(X, y, threshold=0.05)
            elif method == 'mutual_information':
                result = self.mutual_information_selection(X, y)
            elif method == 'lasso':
                result = self.lasso_selection(X, y, alpha=0.1)
            elif method == 'tree_based':
                result = self.tree_based_selection(X, y)
            elif method == 'rfe':
                result = self.recursive_feature_elimination(X, y)
            else:
                logger.warning(f"Unknown method: {method}, skipping")
                continue

            results[method] = set(result.selected_features)

        # Count votes for each feature
        vote_counts = pd.Series(0, index=X.columns)
        for feature_set in results.values():
            for feature in feature_set:
                vote_counts[feature] += 1

        # Select features with enough votes
        selected_features = vote_counts[vote_counts >= min_votes].index.tolist()

        # Create feature scores
        vote_df = vote_counts.sort_values(ascending=False)
        feature_scores = []
        for rank, (feature, votes) in enumerate(vote_df.items(), 1):
            feature_scores.append(FeatureScore(
                feature_name=feature,
                score=float(votes),
                rank=rank,
                method='consensus',
                selected=feature in selected_features
            ))

        elapsed_time = time.time() - start_time
        logger.info(f"Selected {len(selected_features)}/{len(X.columns)} features "
                   f"in {elapsed_time:.2f}s")

        return SelectionResult(
            method='consensus',
            n_features_selected=len(selected_features),
            selected_features=selected_features,
            feature_scores=feature_scores,
            selection_time=elapsed_time,
            metadata={
                'methods': methods,
                'min_votes': min_votes,
                'method_counts': {m: len(s) for m, s in results.items()}
            }
        )

    def export_results(self, output_path: str, results: Dict[str, Any]):
        """Export selection results to JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_feature_selection():
    """Demonstrate feature selection with synthetic data."""
    logger.info("Starting feature selection demo...")

    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 50

    # Generate features
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )

    # Create target with known dependencies
    # Only first 10 features are relevant
    y = (
        2.0 * X['feature_0'] +
        1.5 * X['feature_1'] +
        1.0 * X['feature_2'] +
        0.8 * X['feature_3'] +
        0.6 * X['feature_4'] +
        0.4 * X['feature_5'] +
        0.3 * X['feature_6'] +
        0.2 * X['feature_7'] +
        0.15 * X['feature_8'] +
        0.1 * X['feature_9'] +
        np.random.normal(0, 1, n_samples)
    )

    logger.info(f"Created dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"True relevant features: feature_0 through feature_9 (10 features)")

    # Initialize selector
    selector = FeatureSelector(n_features_to_select=15, selection_threshold=0.05)

    # Test 1: Variance Threshold
    logger.info("\n=== Test 1: Variance Threshold Selection ===")
    variance_result = selector.variance_threshold_selection(X, threshold=0.5)
    logger.info(f"Selected {variance_result.n_features_selected} features")
    logger.info(f"Top 5: {variance_result.selected_features[:5]}")

    # Test 2: Correlation Selection
    logger.info("\n=== Test 2: Correlation Selection ===")
    corr_result = selector.correlation_selection(X, y, threshold=0.1)
    logger.info(f"Selected {corr_result.n_features_selected} features")
    logger.info(f"Top 5: {corr_result.selected_features[:5]}")

    # Test 3: Mutual Information
    logger.info("\n=== Test 3: Mutual Information Selection ===")
    mi_result = selector.mutual_information_selection(X, y, k=15)
    logger.info(f"Selected {mi_result.n_features_selected} features")
    logger.info(f"Top 5: {mi_result.selected_features[:5]}")

    # Test 4: Lasso Selection
    logger.info("\n=== Test 4: Lasso Selection ===")
    lasso_result = selector.lasso_selection(X, y, alpha=0.1)
    logger.info(f"Selected {lasso_result.n_features_selected} features")
    logger.info(f"Selected: {sorted(lasso_result.selected_features)}")

    # Test 5: Tree-based Selection
    logger.info("\n=== Test 5: Tree-based Selection ===")
    tree_result = selector.tree_based_selection(X, y, k=15)
    logger.info(f"Selected {tree_result.n_features_selected} features")
    logger.info(f"Top 5: {tree_result.selected_features[:5]}")

    # Test 6: RFE
    logger.info("\n=== Test 6: Recursive Feature Elimination ===")
    rfe_result = selector.recursive_feature_elimination(X, y, k=15, step=5)
    logger.info(f"Selected {rfe_result.n_features_selected} features")
    logger.info(f"Selected: {sorted(rfe_result.selected_features)}")

    # Test 7: Stability Selection
    logger.info("\n=== Test 7: Stability Selection ===")
    stability_result = selector.stability_selection(X, y, n_iterations=50, threshold=0.6)
    logger.info(f"Selected {stability_result.n_features_selected} features")
    logger.info(f"Selected: {sorted(stability_result.selected_features)}")

    # Test 8: Consensus Selection
    logger.info("\n=== Test 8: Consensus Selection ===")
    consensus_result = selector.consensus_selection(
        X, y,
        methods=['correlation', 'mutual_information', 'lasso', 'tree_based', 'rfe'],
        min_votes=3
    )
    logger.info(f"Selected {consensus_result.n_features_selected} features")
    logger.info(f"Selected: {sorted(consensus_result.selected_features)}")
    logger.info(f"Method vote counts: {consensus_result.metadata['method_counts']}")

    # Export results
    output_dir = Path("/tmp/feature_selection")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'n_samples': len(X),
            'n_features': len(X.columns),
            'true_relevant_features': 10,
            'n_features_to_select': selector.n_features_to_select
        },
        'variance_threshold': variance_result.to_dict(),
        'correlation': corr_result.to_dict(),
        'mutual_information': mi_result.to_dict(),
        'lasso': lasso_result.to_dict(),
        'tree_based': tree_result.to_dict(),
        'rfe': rfe_result.to_dict(),
        'stability': stability_result.to_dict(),
        'consensus': consensus_result.to_dict()
    }

    selector.export_results(str(output_dir / "selection_results.json"), results)

    # Evaluate accuracy (how many true features were found)
    true_features = {f'feature_{i}' for i in range(10)}

    logger.info("\n=== Evaluation: True Positive Rate ===")
    for method_name, result in [
        ('Correlation', corr_result),
        ('Mutual Information', mi_result),
        ('Lasso', lasso_result),
        ('Tree-based', tree_result),
        ('RFE', rfe_result),
        ('Stability', stability_result),
        ('Consensus', consensus_result)
    ]:
        selected_set = set(result.selected_features)
        true_positives = len(true_features & selected_set)
        precision = true_positives / len(selected_set) if selected_set else 0
        recall = true_positives / len(true_features)
        logger.info(f"{method_name:20s}: TP={true_positives}/10, "
                   f"Precision={precision:.2%}, Recall={recall:.2%}")

    logger.info(f"\n✅ Feature selection demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_feature_selection()
