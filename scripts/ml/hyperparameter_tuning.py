"""
Grid Search and Random Search Hyperparameter Tuning Framework

Implements recommendation #14 (consolidated_consolidated_consolidated_rec_101_3020):
- Systematic hyperparameter optimization
- Cross-validated model selection
- MLflow integration for experiment tracking
- Parallel execution support
- Automated model selection

Author: NBA Simulator Project
Created: 2025-10-18
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from itertools import product
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
import json
import numpy as np
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Optional MLflow integration
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logging.warning("MLflow not available - experiment tracking will be limited")

# Scikit-learn for cross-validation
try:
    from sklearn.model_selection import KFold, StratifiedKFold, TimeSeriesSplit
    from sklearn.metrics import (
        mean_squared_error, mean_absolute_error, r2_score,
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - using fallback implementations")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class HyperparameterSpace:
    """Define hyperparameter search space."""
    name: str
    param_type: str  # 'continuous', 'discrete', 'categorical'
    values: Union[List[Any], Tuple[float, float]]  # List for discrete/categorical, tuple for continuous
    log_scale: bool = False  # Use log scale for continuous parameters

    def sample_random(self) -> Any:
        """Sample a random value from the space."""
        if self.param_type == 'categorical':
            return np.random.choice(self.values)
        elif self.param_type == 'discrete':
            return np.random.choice(self.values)
        elif self.param_type == 'continuous':
            low, high = self.values
            if self.log_scale:
                log_low, log_high = np.log10(low), np.log10(high)
                return float(10 ** np.random.uniform(log_low, log_high))
            else:
                return float(np.random.uniform(low, high))
        else:
            raise ValueError(f"Unknown parameter type: {self.param_type}")


@dataclass
class TrialResult:
    """Store results from a single hyperparameter trial."""
    trial_id: int
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    cv_scores: List[float]
    mean_score: float
    std_score: float
    fit_time: float
    score_time: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        def convert_value(v):
            """Convert numpy types to Python types."""
            if isinstance(v, (np.integer, np.int64, np.int32)):
                return int(v)
            elif isinstance(v, (np.floating, np.float64, np.float32)):
                return float(v)
            elif isinstance(v, (np.bool_, bool)):
                return bool(v)
            else:
                return v

        return {
            'trial_id': int(self.trial_id),
            'parameters': {k: convert_value(v) for k, v in self.parameters.items()},
            'metrics': {k: float(v) for k, v in self.metrics.items()},
            'cv_scores': [float(x) for x in self.cv_scores],
            'mean_score': float(self.mean_score),
            'std_score': float(self.std_score),
            'fit_time': float(self.fit_time),
            'score_time': float(self.score_time),
            'timestamp': self.timestamp.isoformat()
        }


class CrossValidationStrategy:
    """Cross-validation strategies for different data types."""

    def __init__(self, strategy: str = 'kfold', n_splits: int = 5, **kwargs):
        """
        Initialize cross-validation strategy.

        Args:
            strategy: 'kfold', 'stratified', 'timeseries', 'blocked_timeseries'
            n_splits: Number of folds
            **kwargs: Additional arguments for specific strategies
        """
        self.strategy = strategy
        self.n_splits = n_splits
        self.kwargs = kwargs

        if strategy == 'kfold':
            if SKLEARN_AVAILABLE:
                self.cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
            else:
                self.cv = None
        elif strategy == 'stratified':
            if SKLEARN_AVAILABLE:
                self.cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            else:
                self.cv = None
        elif strategy == 'timeseries':
            if SKLEARN_AVAILABLE:
                self.cv = TimeSeriesSplit(n_splits=n_splits)
            else:
                self.cv = None
        elif strategy == 'blocked_timeseries':
            # Custom implementation for panel data
            self.cv = None
            self.block_size = kwargs.get('block_size', 30)  # Days per block
        else:
            raise ValueError(f"Unknown CV strategy: {strategy}")

    def split(self, X: pd.DataFrame, y: pd.Series = None,
              groups: pd.Series = None) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate train/test splits.

        Returns:
            List of (train_indices, test_indices) tuples
        """
        if self.cv is not None and SKLEARN_AVAILABLE:
            if self.strategy == 'stratified':
                return list(self.cv.split(X, y))
            else:
                return list(self.cv.split(X))
        else:
            # Fallback implementation for blocked time series
            return self._blocked_timeseries_split(X, groups)

    def _blocked_timeseries_split(self, X: pd.DataFrame,
                                  groups: pd.Series) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Custom blocked time series split for panel data."""
        if groups is None:
            # Simple time-based split
            n = len(X)
            block_size = n // (self.n_splits + 1)
            splits = []
            for i in range(self.n_splits):
                train_end = (i + 1) * block_size
                test_start = train_end
                test_end = test_start + block_size
                train_idx = np.arange(0, train_end)
                test_idx = np.arange(test_start, min(test_end, n))
                if len(test_idx) > 0:
                    splits.append((train_idx, test_idx))
            return splits
        else:
            # Panel data: split by time within each group
            unique_groups = groups.unique()
            splits = []
            for i in range(self.n_splits):
                train_idx_list = []
                test_idx_list = []
                for group in unique_groups:
                    group_indices = np.where(groups == group)[0]
                    n_group = len(group_indices)
                    block_size = n_group // (self.n_splits + 1)
                    train_end = (i + 1) * block_size
                    test_start = train_end
                    test_end = test_start + block_size
                    train_idx_list.extend(group_indices[:train_end])
                    test_idx_list.extend(group_indices[test_start:min(test_end, n_group)])
                if len(test_idx_list) > 0:
                    splits.append((np.array(train_idx_list), np.array(test_idx_list)))
            return splits


class HyperparameterTuner:
    """
    Comprehensive hyperparameter tuning framework with grid search and random search.
    """

    def __init__(self, estimator: Any, param_space: Dict[str, HyperparameterSpace],
                 cv_strategy: CrossValidationStrategy,
                 scoring: Union[str, Callable] = 'neg_mean_squared_error',
                 n_jobs: int = 1,
                 verbose: int = 1,
                 mlflow_tracking: bool = True):
        """
        Initialize hyperparameter tuner.

        Args:
            estimator: ML model to tune (must have fit/predict methods)
            param_space: Dictionary mapping parameter names to HyperparameterSpace objects
            cv_strategy: Cross-validation strategy
            scoring: Scoring metric ('neg_mean_squared_error', 'r2', 'accuracy', etc.)
            n_jobs: Number of parallel jobs (-1 for all cores)
            verbose: Verbosity level (0=silent, 1=progress, 2=detailed)
            mlflow_tracking: Enable MLflow experiment tracking
        """
        self.estimator = estimator
        self.param_space = param_space
        self.cv_strategy = cv_strategy
        self.scoring = scoring
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.mlflow_tracking = mlflow_tracking and MLFLOW_AVAILABLE

        # Results storage
        self.results_: List[TrialResult] = []
        self.best_params_: Optional[Dict[str, Any]] = None
        self.best_score_: Optional[float] = None
        self.best_estimator_: Optional[Any] = None

        logger.info(f"Initialized HyperparameterTuner with {len(param_space)} parameters")
        logger.info(f"CV strategy: {cv_strategy.strategy} with {cv_strategy.n_splits} splits")
        logger.info(f"Scoring metric: {scoring}")

    def grid_search(self, X: pd.DataFrame, y: pd.Series,
                   groups: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Perform exhaustive grid search over all parameter combinations.

        Args:
            X: Feature matrix
            y: Target variable
            groups: Group labels for panel data (optional)

        Returns:
            Dictionary with best parameters, scores, and full results
        """
        logger.info("Starting grid search...")
        start_time = time.time()

        # Generate all parameter combinations
        param_grid = self._generate_grid()
        n_combinations = len(param_grid)
        logger.info(f"Testing {n_combinations} parameter combinations")

        if self.mlflow_tracking:
            mlflow.set_experiment("hyperparameter_tuning")
            mlflow.start_run(run_name=f"grid_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            mlflow.log_param("search_type", "grid_search")
            mlflow.log_param("n_combinations", n_combinations)

        # Evaluate each combination
        if self.n_jobs == 1:
            # Sequential execution
            for trial_id, params in enumerate(param_grid):
                result = self._evaluate_parameters(trial_id, params, X, y, groups)
                self.results_.append(result)
                if self.verbose >= 1:
                    logger.info(f"Trial {trial_id + 1}/{n_combinations} - "
                              f"Score: {result.mean_score:.4f} ± {result.std_score:.4f}")
        else:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = {
                    executor.submit(self._evaluate_parameters, trial_id, params, X, y, groups): trial_id
                    for trial_id, params in enumerate(param_grid)
                }
                for future in as_completed(futures):
                    result = future.result()
                    self.results_.append(result)
                    if self.verbose >= 1:
                        logger.info(f"Trial {result.trial_id + 1}/{n_combinations} - "
                                  f"Score: {result.mean_score:.4f} ± {result.std_score:.4f}")

        # Find best parameters
        self._update_best_results()

        elapsed_time = time.time() - start_time
        logger.info(f"Grid search complete in {elapsed_time:.2f}s")
        logger.info(f"Best score: {self.best_score_:.4f}")
        logger.info(f"Best parameters: {self.best_params_}")

        if self.mlflow_tracking:
            mlflow.log_metric("best_score", self.best_score_)
            mlflow.log_params(self.best_params_)
            mlflow.log_metric("search_time", elapsed_time)
            mlflow.end_run()

        return {
            'best_params': self.best_params_,
            'best_score': float(self.best_score_),
            'n_trials': len(self.results_),
            'elapsed_time': float(elapsed_time),
            'all_results': [r.to_dict() for r in self.results_]
        }

    def random_search(self, X: pd.DataFrame, y: pd.Series,
                     n_iter: int = 100,
                     groups: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Perform random search over parameter space.

        Args:
            X: Feature matrix
            y: Target variable
            n_iter: Number of random samples to try
            groups: Group labels for panel data (optional)

        Returns:
            Dictionary with best parameters, scores, and full results
        """
        logger.info("Starting random search...")
        start_time = time.time()
        logger.info(f"Testing {n_iter} random parameter combinations")

        if self.mlflow_tracking:
            mlflow.set_experiment("hyperparameter_tuning")
            mlflow.start_run(run_name=f"random_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            mlflow.log_param("search_type", "random_search")
            mlflow.log_param("n_iter", n_iter)

        # Generate random parameter combinations
        param_samples = self._generate_random_samples(n_iter)

        # Evaluate each combination
        if self.n_jobs == 1:
            # Sequential execution
            for trial_id, params in enumerate(param_samples):
                result = self._evaluate_parameters(trial_id, params, X, y, groups)
                self.results_.append(result)
                if self.verbose >= 1:
                    logger.info(f"Trial {trial_id + 1}/{n_iter} - "
                              f"Score: {result.mean_score:.4f} ± {result.std_score:.4f}")
        else:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = {
                    executor.submit(self._evaluate_parameters, trial_id, params, X, y, groups): trial_id
                    for trial_id, params in enumerate(param_samples)
                }
                for future in as_completed(futures):
                    result = future.result()
                    self.results_.append(result)
                    if self.verbose >= 1:
                        logger.info(f"Trial {result.trial_id + 1}/{n_iter} - "
                                  f"Score: {result.mean_score:.4f} ± {result.std_score:.4f}")

        # Find best parameters
        self._update_best_results()

        elapsed_time = time.time() - start_time
        logger.info(f"Random search complete in {elapsed_time:.2f}s")
        logger.info(f"Best score: {self.best_score_:.4f}")
        logger.info(f"Best parameters: {self.best_params_}")

        if self.mlflow_tracking:
            mlflow.log_metric("best_score", self.best_score_)
            mlflow.log_params(self.best_params_)
            mlflow.log_metric("search_time", elapsed_time)
            mlflow.end_run()

        return {
            'best_params': self.best_params_,
            'best_score': float(self.best_score_),
            'n_trials': len(self.results_),
            'elapsed_time': float(elapsed_time),
            'all_results': [r.to_dict() for r in self.results_]
        }

    def _generate_grid(self) -> List[Dict[str, Any]]:
        """Generate all combinations for grid search."""
        param_names = list(self.param_space.keys())
        param_values = []

        for name in param_names:
            space = self.param_space[name]
            if space.param_type in ['categorical', 'discrete']:
                param_values.append(space.values)
            elif space.param_type == 'continuous':
                # For continuous, create discrete grid
                low, high = space.values
                if space.log_scale:
                    values = np.logspace(np.log10(low), np.log10(high), num=5)
                else:
                    values = np.linspace(low, high, num=5)
                param_values.append(values.tolist())
            else:
                raise ValueError(f"Unknown parameter type: {space.param_type}")

        # Generate all combinations
        param_grid = []
        for combination in product(*param_values):
            param_dict = dict(zip(param_names, combination))
            param_grid.append(param_dict)

        return param_grid

    def _generate_random_samples(self, n_iter: int) -> List[Dict[str, Any]]:
        """Generate random samples from parameter space."""
        samples = []
        for _ in range(n_iter):
            sample = {}
            for name, space in self.param_space.items():
                sample[name] = space.sample_random()
            samples.append(sample)
        return samples

    def _evaluate_parameters(self, trial_id: int, params: Dict[str, Any],
                            X: pd.DataFrame, y: pd.Series,
                            groups: Optional[pd.Series] = None) -> TrialResult:
        """
        Evaluate a single parameter combination using cross-validation.

        Args:
            trial_id: Unique trial identifier
            params: Parameter dictionary
            X: Feature matrix
            y: Target variable
            groups: Group labels (optional)

        Returns:
            TrialResult object
        """
        if self.verbose >= 2:
            logger.info(f"Evaluating trial {trial_id}: {params}")

        # Set parameters
        for param_name, param_value in params.items():
            setattr(self.estimator, param_name, param_value)

        # Perform cross-validation
        cv_scores = []
        fit_times = []
        score_times = []

        splits = self.cv_strategy.split(X, y, groups)

        for train_idx, test_idx in splits:
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # Fit model
            fit_start = time.time()
            self.estimator.fit(X_train, y_train)
            fit_times.append(time.time() - fit_start)

            # Score model
            score_start = time.time()
            y_pred = self.estimator.predict(X_test)
            score = self._compute_score(y_test, y_pred)
            score_times.append(time.time() - score_start)
            cv_scores.append(score)

        # Compute metrics
        mean_score = float(np.mean(cv_scores))
        std_score = float(np.std(cv_scores))

        # Additional metrics on final fold
        metrics = self._compute_all_metrics(y_test, y_pred)

        result = TrialResult(
            trial_id=trial_id,
            parameters=params.copy(),
            metrics=metrics,
            cv_scores=cv_scores,
            mean_score=mean_score,
            std_score=std_score,
            fit_time=float(np.mean(fit_times)),
            score_time=float(np.mean(score_times))
        )

        if self.mlflow_tracking:
            with mlflow.start_run(nested=True):
                mlflow.log_params(params)
                mlflow.log_metric("mean_cv_score", mean_score)
                mlflow.log_metric("std_cv_score", std_score)
                for k, v in metrics.items():
                    mlflow.log_metric(k, v)

        return result

    def _compute_score(self, y_true: pd.Series, y_pred: np.ndarray) -> float:
        """Compute score based on scoring metric."""
        if callable(self.scoring):
            return float(self.scoring(y_true, y_pred))

        if SKLEARN_AVAILABLE:
            if self.scoring == 'neg_mean_squared_error':
                return float(-mean_squared_error(y_true, y_pred))
            elif self.scoring == 'neg_mean_absolute_error':
                return float(-mean_absolute_error(y_true, y_pred))
            elif self.scoring == 'r2':
                return float(r2_score(y_true, y_pred))
            elif self.scoring == 'accuracy':
                return float(accuracy_score(y_true, y_pred))
            else:
                raise ValueError(f"Unknown scoring metric: {self.scoring}")
        else:
            # Fallback implementations
            if self.scoring == 'neg_mean_squared_error':
                return float(-np.mean((y_true - y_pred) ** 2))
            elif self.scoring == 'neg_mean_absolute_error':
                return float(-np.mean(np.abs(y_true - y_pred)))
            elif self.scoring == 'r2':
                ss_res = np.sum((y_true - y_pred) ** 2)
                ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
                return float(1 - (ss_res / ss_tot))
            else:
                raise ValueError(f"Unknown scoring metric: {self.scoring}")

    def _compute_all_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """Compute multiple evaluation metrics."""
        metrics = {}

        if SKLEARN_AVAILABLE:
            # Regression metrics
            try:
                metrics['mse'] = float(mean_squared_error(y_true, y_pred))
                metrics['rmse'] = float(np.sqrt(metrics['mse']))
                metrics['mae'] = float(mean_absolute_error(y_true, y_pred))
                metrics['r2'] = float(r2_score(y_true, y_pred))
            except:
                pass
        else:
            # Fallback
            metrics['mse'] = float(np.mean((y_true - y_pred) ** 2))
            metrics['rmse'] = float(np.sqrt(metrics['mse']))
            metrics['mae'] = float(np.mean(np.abs(y_true - y_pred)))
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            metrics['r2'] = float(1 - (ss_res / ss_tot))

        return metrics

    def _update_best_results(self):
        """Update best parameters and score from all trials."""
        if not self.results_:
            return

        # Find best trial (highest mean score)
        best_trial = max(self.results_, key=lambda x: x.mean_score)

        self.best_params_ = best_trial.parameters
        self.best_score_ = best_trial.mean_score

        # Refit estimator with best parameters
        for param_name, param_value in self.best_params_.items():
            setattr(self.estimator, param_name, param_value)
        self.best_estimator_ = self.estimator

    def export_results(self, output_path: str):
        """Export all results to JSON file."""
        def convert_value(v):
            """Convert numpy types to Python types."""
            if isinstance(v, (np.integer, np.int64, np.int32)):
                return int(v)
            elif isinstance(v, (np.floating, np.float64, np.float32)):
                return float(v)
            elif isinstance(v, (np.bool_, bool)):
                return bool(v)
            else:
                return v

        results_dict = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'n_trials': len(self.results_),
                'scoring': self.scoring,
                'cv_strategy': self.cv_strategy.strategy,
                'n_splits': self.cv_strategy.n_splits
            },
            'best_results': {
                'best_params': {k: convert_value(v) for k, v in self.best_params_.items()} if self.best_params_ else None,
                'best_score': float(self.best_score_) if self.best_score_ is not None else None
            },
            'all_trials': [r.to_dict() for r in self.results_]
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2)

        logger.info(f"Results exported to {output_path}")


# Demo function
def demo_hyperparameter_tuning():
    """Demonstrate hyperparameter tuning with synthetic panel data."""
    logger.info("Starting hyperparameter tuning demo...")

    # Create synthetic panel data
    np.random.seed(42)
    n_players = 50
    n_games = 100

    data = []
    for player_id in range(n_players):
        player_skill = np.random.normal(20, 5)
        for game_id in range(n_games):
            # Simulate points with some noise
            points = player_skill + np.random.normal(0, 3)
            # Features: recent form, minutes played, team strength
            recent_form = np.random.uniform(0.8, 1.2)
            minutes = np.random.uniform(20, 40)
            team_strength = np.random.uniform(0.9, 1.1)

            data.append({
                'player_id': player_id,
                'game_id': game_id,
                'points': points,
                'recent_form': recent_form,
                'minutes': minutes,
                'team_strength': team_strength
            })

    df = pd.DataFrame(data)
    logger.info(f"Created synthetic dataset: {len(df)} observations, {n_players} players")

    # Prepare features and target
    X = df[['recent_form', 'minutes', 'team_strength']]
    y = df['points']
    groups = df['player_id']

    # Use sklearn's Ridge regression for stability
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    # Standardize features for stable optimization
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)

    # Define hyperparameter space for Ridge regression
    param_space = {
        'alpha': HyperparameterSpace(
            name='alpha',
            param_type='continuous',
            values=(0.1, 10.0),  # Regularization strength
            log_scale=True
        ),
        'fit_intercept': HyperparameterSpace(
            name='fit_intercept',
            param_type='categorical',
            values=[True, False]
        ),
        'solver': HyperparameterSpace(
            name='solver',
            param_type='categorical',
            values=['auto', 'svd', 'cholesky']
        )
    }

    # Test 1: Grid Search
    logger.info("\n=== Test 1: Grid Search ===")
    estimator = Ridge()
    cv_strategy = CrossValidationStrategy(strategy='kfold', n_splits=5)
    tuner = HyperparameterTuner(
        estimator=estimator,
        param_space=param_space,
        cv_strategy=cv_strategy,
        scoring='neg_mean_squared_error',
        n_jobs=1,
        verbose=1,
        mlflow_tracking=False  # Disable for demo
    )

    grid_results = tuner.grid_search(X_scaled, y)
    logger.info(f"Grid search complete: {grid_results['n_trials']} trials in {grid_results['elapsed_time']:.2f}s")
    logger.info(f"Best score: {grid_results['best_score']:.4f}")
    logger.info(f"Best params: {grid_results['best_params']}")

    # Test 2: Random Search
    logger.info("\n=== Test 2: Random Search ===")
    estimator2 = Ridge()
    tuner2 = HyperparameterTuner(
        estimator=estimator2,
        param_space=param_space,
        cv_strategy=cv_strategy,
        scoring='neg_mean_squared_error',
        n_jobs=1,
        verbose=1,
        mlflow_tracking=False
    )

    random_results = tuner2.random_search(X_scaled, y, n_iter=20)  # Reduced from 50
    logger.info(f"Random search complete: {random_results['n_trials']} trials in {random_results['elapsed_time']:.2f}s")
    logger.info(f"Best score: {random_results['best_score']:.4f}")
    logger.info(f"Best params: {random_results['best_params']}")

    # Test 3: Time Series CV for Panel Data
    logger.info("\n=== Test 3: Time Series CV ===")
    cv_ts = CrossValidationStrategy(strategy='blocked_timeseries', n_splits=3, block_size=30)
    estimator3 = Ridge()
    tuner3 = HyperparameterTuner(
        estimator=estimator3,
        param_space=param_space,
        cv_strategy=cv_ts,
        scoring='r2',
        n_jobs=1,
        verbose=1,
        mlflow_tracking=False
    )

    ts_results = tuner3.random_search(X_scaled, y, n_iter=10, groups=groups)  # Reduced from 20
    logger.info(f"Time series CV complete: {ts_results['n_trials']} trials in {ts_results['elapsed_time']:.2f}s")
    logger.info(f"Best score: {ts_results['best_score']:.4f}")
    logger.info(f"Best params: {ts_results['best_params']}")

    # Export results
    output_dir = Path("/tmp/hyperparameter_tuning")
    output_dir.mkdir(parents=True, exist_ok=True)

    tuner.export_results(str(output_dir / "grid_search_results.json"))
    tuner2.export_results(str(output_dir / "random_search_results.json"))
    tuner3.export_results(str(output_dir / "timeseries_cv_results.json"))

    logger.info(f"\n✅ Hyperparameter tuning demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return {
        'grid_search': grid_results,
        'random_search': random_results,
        'timeseries_cv': ts_results
    }


if __name__ == '__main__':
    demo_hyperparameter_tuning()
