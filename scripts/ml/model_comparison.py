"""
Model Comparison & Benchmarking Framework

Implements comprehensive model comparison and benchmarking:
- Statistical comparison tests (paired t-test, Wilcoxon, McNemar)
- Performance metric comparison across models
- Cross-model evaluation consistency
- Benchmark against baseline models
- Model ranking and selection
- Statistical significance testing
- Performance visualization and reporting

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
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class ModelPerformance:
    """Store model performance metrics."""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    log_loss: float
    training_time: float
    prediction_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'model_name': self.model_name,
            'accuracy': float(self.accuracy),
            'precision': float(self.precision),
            'recall': float(self.recall),
            'f1_score': float(self.f1_score),
            'auc_roc': float(self.auc_roc),
            'log_loss': float(self.log_loss),
            'training_time': float(self.training_time),
            'prediction_time': float(self.prediction_time),
            'metadata': self.metadata
        }


@dataclass
class ComparisonResult:
    """Store model comparison results."""
    comparison_type: str
    model_a: str
    model_b: str
    statistic: float
    p_value: float
    significant: bool
    winner: Optional[str]
    effect_size: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'comparison_type': self.comparison_type,
            'model_a': self.model_a,
            'model_b': self.model_b,
            'statistic': float(self.statistic),
            'p_value': float(self.p_value),
            'significant': self.significant,
            'winner': self.winner,
            'effect_size': float(self.effect_size),
            'metadata': self.metadata
        }


@dataclass
class BenchmarkResult:
    """Store benchmarking results."""
    models: List[ModelPerformance]
    comparisons: List[ComparisonResult]
    rankings: Dict[str, List[Tuple[str, float]]]
    best_model: str
    baseline_model: str
    baseline_improvement: Dict[str, float]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Convert baseline_improvement (nested dict) to serializable format
        baseline_improvement_serializable = {}
        for model_name, improvements in self.baseline_improvement.items():
            baseline_improvement_serializable[model_name] = {
                metric: float(value) for metric, value in improvements.items()
            }

        return {
            'models': [m.to_dict() for m in self.models],
            'comparisons': [c.to_dict() for c in self.comparisons],
            'rankings': self.rankings,
            'best_model': self.best_model,
            'baseline_model': self.baseline_model,
            'baseline_improvement': baseline_improvement_serializable,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class ModelComparator:
    """
    Comprehensive model comparison and benchmarking framework.

    Provides methods for:
    - Statistical comparison between models
    - Performance metric benchmarking
    - Model ranking and selection
    - Baseline comparison
    - Significance testing
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize model comparator.

        Parameters
        ----------
        alpha : float
            Significance level for statistical tests (default: 0.05)
        """
        self.alpha = alpha
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized ModelComparator with alpha={alpha}")

    def paired_ttest(
        self,
        model_a_scores: np.ndarray,
        model_b_scores: np.ndarray,
        model_a_name: str = "Model A",
        model_b_name: str = "Model B"
    ) -> ComparisonResult:
        """
        Perform paired t-test to compare two models.

        Parameters
        ----------
        model_a_scores : np.ndarray
            Performance scores for model A (e.g., accuracy on each fold)
        model_b_scores : np.ndarray
            Performance scores for model B
        model_a_name : str
            Name of model A
        model_b_name : str
            Name of model B

        Returns
        -------
        ComparisonResult
            Test results including statistic, p-value, and winner
        """
        self.logger.info(f"Performing paired t-test: {model_a_name} vs {model_b_name}")

        # Perform paired t-test
        statistic, p_value = stats.ttest_rel(model_a_scores, model_b_scores)

        # Determine significance
        significant = p_value < self.alpha

        # Determine winner
        mean_a = np.mean(model_a_scores)
        mean_b = np.mean(model_b_scores)
        if significant:
            winner = model_a_name if mean_a > mean_b else model_b_name
        else:
            winner = None  # No significant difference

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((np.var(model_a_scores) + np.var(model_b_scores)) / 2)
        effect_size = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0

        result = ComparisonResult(
            comparison_type='paired_ttest',
            model_a=model_a_name,
            model_b=model_b_name,
            statistic=statistic,
            p_value=p_value,
            significant=significant,
            winner=winner,
            effect_size=effect_size,
            metadata={'mean_a': mean_a, 'mean_b': mean_b}
        )

        self.logger.info(f"  Statistic: {statistic:.4f}, p-value: {p_value:.4f}")
        if winner:
            self.logger.info(f"  Winner: {winner} (significant)")
        else:
            self.logger.info(f"  No significant difference")

        return result

    def wilcoxon_test(
        self,
        model_a_scores: np.ndarray,
        model_b_scores: np.ndarray,
        model_a_name: str = "Model A",
        model_b_name: str = "Model B"
    ) -> ComparisonResult:
        """
        Perform Wilcoxon signed-rank test (non-parametric alternative to t-test).

        Parameters
        ----------
        model_a_scores : np.ndarray
            Performance scores for model A
        model_b_scores : np.ndarray
            Performance scores for model B
        model_a_name : str
            Name of model A
        model_b_name : str
            Name of model B

        Returns
        -------
        ComparisonResult
            Test results
        """
        self.logger.info(f"Performing Wilcoxon test: {model_a_name} vs {model_b_name}")

        # Perform Wilcoxon signed-rank test
        statistic, p_value = stats.wilcoxon(model_a_scores, model_b_scores)

        # Determine significance and winner
        significant = p_value < self.alpha
        mean_a = np.mean(model_a_scores)
        mean_b = np.mean(model_b_scores)
        winner = model_a_name if (significant and mean_a > mean_b) else (
            model_b_name if (significant and mean_b > mean_a) else None
        )

        # Effect size (r = Z / sqrt(N))
        n = len(model_a_scores)
        z_score = (statistic - n*(n+1)/4) / np.sqrt(n*(n+1)*(2*n+1)/24)
        effect_size = abs(z_score) / np.sqrt(n)

        result = ComparisonResult(
            comparison_type='wilcoxon',
            model_a=model_a_name,
            model_b=model_b_name,
            statistic=statistic,
            p_value=p_value,
            significant=significant,
            winner=winner,
            effect_size=effect_size,
            metadata={'mean_a': mean_a, 'mean_b': mean_b}
        )

        self.logger.info(f"  Statistic: {statistic:.4f}, p-value: {p_value:.4f}")
        if winner:
            self.logger.info(f"  Winner: {winner}")

        return result

    def mcnemar_test(
        self,
        model_a_predictions: np.ndarray,
        model_b_predictions: np.ndarray,
        y_true: np.ndarray,
        model_a_name: str = "Model A",
        model_b_name: str = "Model B"
    ) -> ComparisonResult:
        """
        Perform McNemar's test for comparing classifiers on binary outcomes.

        Parameters
        ----------
        model_a_predictions : np.ndarray
            Binary predictions from model A
        model_b_predictions : np.ndarray
            Binary predictions from model B
        y_true : np.ndarray
            True labels
        model_a_name : str
            Name of model A
        model_b_name : str
            Name of model B

        Returns
        -------
        ComparisonResult
            Test results
        """
        self.logger.info(f"Performing McNemar's test: {model_a_name} vs {model_b_name}")

        # Create contingency table
        # n01: A wrong, B correct
        # n10: A correct, B wrong
        a_correct = (model_a_predictions == y_true)
        b_correct = (model_b_predictions == y_true)

        n01 = np.sum(~a_correct & b_correct)
        n10 = np.sum(a_correct & ~b_correct)

        # McNemar's test statistic with continuity correction
        statistic = (abs(n01 - n10) - 1)**2 / (n01 + n10) if (n01 + n10) > 0 else 0
        p_value = 1 - stats.chi2.cdf(statistic, 1)

        # Determine significance and winner
        significant = p_value < self.alpha
        if significant:
            winner = model_b_name if n01 > n10 else model_a_name
        else:
            winner = None

        # Effect size (odds ratio)
        effect_size = n01 / n10 if n10 > 0 else float('inf')

        result = ComparisonResult(
            comparison_type='mcnemar',
            model_a=model_a_name,
            model_b=model_b_name,
            statistic=statistic,
            p_value=p_value,
            significant=significant,
            winner=winner,
            effect_size=effect_size,
            metadata={'n01': int(n01), 'n10': int(n10)}
        )

        self.logger.info(f"  Statistic: {statistic:.4f}, p-value: {p_value:.4f}")
        if winner:
            self.logger.info(f"  Winner: {winner}")

        return result

    def rank_models(
        self,
        performances: List[ModelPerformance],
        metrics: List[str] = None
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Rank models by different performance metrics.

        Parameters
        ----------
        performances : List[ModelPerformance]
            List of model performance results
        metrics : List[str], optional
            Metrics to rank by (default: all available metrics)

        Returns
        -------
        Dict[str, List[Tuple[str, float]]]
            Rankings for each metric (metric_name -> [(model_name, score), ...])
        """
        if metrics is None:
            metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc']

        rankings = {}

        for metric in metrics:
            # Get scores for this metric
            scores = [(p.model_name, getattr(p, metric)) for p in performances]

            # Sort descending (higher is better) except for log_loss
            if metric == 'log_loss':
                scores.sort(key=lambda x: x[1])  # Lower is better
            else:
                scores.sort(key=lambda x: x[1], reverse=True)  # Higher is better

            rankings[metric] = scores

        return rankings

    def compare_to_baseline(
        self,
        performances: List[ModelPerformance],
        baseline_name: str,
        metrics: List[str] = None
    ) -> Dict[str, float]:
        """
        Compare all models to a baseline model.

        Parameters
        ----------
        performances : List[ModelPerformance]
            List of model performances
        baseline_name : str
            Name of baseline model
        metrics : List[str], optional
            Metrics to compare

        Returns
        -------
        Dict[str, float]
            Improvements over baseline for each model
        """
        if metrics is None:
            metrics = ['accuracy', 'f1_score', 'auc_roc']

        # Find baseline
        baseline = next((p for p in performances if p.model_name == baseline_name), None)
        if baseline is None:
            raise ValueError(f"Baseline model '{baseline_name}' not found")

        improvements = {}

        for perf in performances:
            if perf.model_name == baseline_name:
                continue

            model_improvements = {}
            for metric in metrics:
                baseline_score = getattr(baseline, metric)
                model_score = getattr(perf, metric)

                # Calculate percentage improvement
                if baseline_score != 0:
                    improvement = ((model_score - baseline_score) / abs(baseline_score)) * 100
                else:
                    improvement = 0.0

                model_improvements[metric] = improvement

            improvements[perf.model_name] = model_improvements

        return improvements

    def benchmark_models(
        self,
        performances: List[ModelPerformance],
        baseline_name: str = None,
        metrics: List[str] = None
    ) -> BenchmarkResult:
        """
        Comprehensive benchmarking of multiple models.

        Parameters
        ----------
        performances : List[ModelPerformance]
            List of model performances
        baseline_name : str, optional
            Name of baseline model (defaults to first model)
        metrics : List[str], optional
            Metrics to benchmark

        Returns
        -------
        BenchmarkResult
            Complete benchmarking results
        """
        if not performances:
            raise ValueError("No model performances provided")

        if baseline_name is None:
            baseline_name = performances[0].model_name

        if metrics is None:
            metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc']

        self.logger.info(f"Benchmarking {len(performances)} models")
        self.logger.info(f"Baseline: {baseline_name}")

        # Rank models
        rankings = self.rank_models(performances, metrics)

        # Compare to baseline
        baseline_improvement = self.compare_to_baseline(performances, baseline_name, metrics)

        # Find best model (by primary metric - accuracy)
        best_model = rankings['accuracy'][0][0]

        # Perform pairwise comparisons (for demonstration, compare top 2)
        comparisons = []
        if len(performances) >= 2:
            # This would typically use cross-validation scores
            # For demo, we'll skip pairwise comparisons
            pass

        result = BenchmarkResult(
            models=performances,
            comparisons=comparisons,
            rankings=rankings,
            best_model=best_model,
            baseline_model=baseline_name,
            baseline_improvement=baseline_improvement,
            timestamp=datetime.now().isoformat(),
            metadata={'n_models': len(performances), 'metrics': metrics}
        )

        return result

    def export_results(self, output_path: str, results: BenchmarkResult) -> None:
        """
        Export benchmark results to JSON file.

        Parameters
        ----------
        output_path : str
            Path to output JSON file
        results : BenchmarkResult
            Results to export
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)

        self.logger.info(f"Results exported to {output_path}")


def demo_model_comparison():
    """Demonstrate model comparison framework with synthetic data."""
    logger.info("=== Model Comparison & Benchmarking Demo ===\n")

    # Create output directory
    output_dir = Path("/tmp/model_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize comparator
    comparator = ModelComparator(alpha=0.05)

    # Simulate model performances
    np.random.seed(42)

    # Create synthetic performance data for 4 models
    models = ['Logistic Regression', 'Random Forest', 'XGBoost', 'LightGBM']
    performances = []

    for i, model_name in enumerate(models):
        # Simulate increasing performance for better models
        base_accuracy = 0.60 + i * 0.05
        performance = ModelPerformance(
            model_name=model_name,
            accuracy=base_accuracy + np.random.normal(0, 0.02),
            precision=base_accuracy + np.random.normal(0, 0.03),
            recall=base_accuracy + np.random.normal(0, 0.03),
            f1_score=base_accuracy + np.random.normal(0, 0.02),
            auc_roc=base_accuracy + 0.1 + np.random.normal(0, 0.02),
            log_loss=0.7 - i * 0.05 + np.random.normal(0, 0.03),
            training_time=10.0 + i * 5.0 + np.random.normal(0, 2.0),
            prediction_time=0.5 + i * 0.2 + np.random.normal(0, 0.1),
            metadata={'cv_folds': 5, 'dataset_size': 10000}
        )
        performances.append(performance)

    # Test 1: Paired t-test
    logger.info("\n--- Test 1: Paired T-Test ---")
    # Simulate 5-fold CV scores
    lr_scores = np.array([0.60, 0.62, 0.61, 0.63, 0.60])
    rf_scores = np.array([0.65, 0.67, 0.66, 0.68, 0.65])

    ttest_result = comparator.paired_ttest(
        lr_scores, rf_scores,
        "Logistic Regression", "Random Forest"
    )
    logger.info(f"Result: {ttest_result.winner or 'No significant difference'}")
    logger.info(f"Effect size (Cohen's d): {ttest_result.effect_size:.4f}")

    # Test 2: Wilcoxon test
    logger.info("\n--- Test 2: Wilcoxon Signed-Rank Test ---")
    wilcoxon_result = comparator.wilcoxon_test(
        lr_scores, rf_scores,
        "Logistic Regression", "Random Forest"
    )
    logger.info(f"Result: {wilcoxon_result.winner or 'No significant difference'}")

    # Test 3: McNemar's test
    logger.info("\n--- Test 3: McNemar's Test ---")
    # Simulate predictions
    n_samples = 1000
    y_true = np.random.randint(0, 2, n_samples)
    lr_preds = (np.random.random(n_samples) > 0.4).astype(int)  # 60% accuracy
    rf_preds = (np.random.random(n_samples) > 0.35).astype(int)  # 65% accuracy

    mcnemar_result = comparator.mcnemar_test(
        lr_preds, rf_preds, y_true,
        "Logistic Regression", "Random Forest"
    )
    logger.info(f"Result: {mcnemar_result.winner or 'No significant difference'}")
    logger.info(f"Contingency: A wrong/B correct={mcnemar_result.metadata['n01']}, "
               f"A correct/B wrong={mcnemar_result.metadata['n10']}")

    # Test 4: Model ranking
    logger.info("\n--- Test 4: Model Rankings ---")
    rankings = comparator.rank_models(performances)
    for metric, ranked_models in rankings.items():
        logger.info(f"\n{metric.upper()} rankings:")
        for rank, (model_name, score) in enumerate(ranked_models, 1):
            logger.info(f"  {rank}. {model_name:20s}: {score:.4f}")

    # Test 5: Baseline comparison
    logger.info("\n--- Test 5: Baseline Comparison ---")
    baseline_improvements = comparator.compare_to_baseline(
        performances,
        baseline_name="Logistic Regression"
    )
    for model_name, improvements in baseline_improvements.items():
        logger.info(f"\n{model_name} vs Logistic Regression:")
        for metric, improvement in improvements.items():
            logger.info(f"  {metric}: {improvement:+.2f}%")

    # Test 6: Complete benchmark
    logger.info("\n--- Test 6: Complete Benchmark ---")
    benchmark_result = comparator.benchmark_models(
        performances,
        baseline_name="Logistic Regression"
    )

    logger.info(f"\nBest model: {benchmark_result.best_model}")
    logger.info(f"Baseline model: {benchmark_result.baseline_model}")
    logger.info(f"Number of models: {len(benchmark_result.models)}")

    # Export results
    comparator.export_results(
        str(output_dir / "benchmark_results.json"),
        benchmark_result
    )

    logger.info(f"\n✅ Model comparison demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return benchmark_result


if __name__ == '__main__':
    demo_model_comparison()
