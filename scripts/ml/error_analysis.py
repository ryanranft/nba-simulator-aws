"""
Error Analysis Framework

Implements comprehensive error analysis and failure mode detection:
- Error distribution analysis
- Misclassification pattern identification
- Feature-based error analysis
- Confusion matrix deep dive
- Error clustering and segmentation
- Prediction confidence analysis
- Failure case identification
- Systematic error detection

Author: NBA Simulator Project
Created: 2025-10-18
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class ErrorPattern:
    """Store detected error pattern."""
    pattern_type: str
    description: str
    frequency: int
    percentage: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    examples: List[int]  # Sample indices
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'pattern_type': self.pattern_type,
            'description': self.description,
            'frequency': int(self.frequency),
            'percentage': float(self.percentage),
            'severity': self.severity,
            'examples': [int(x) for x in self.examples],
            'metadata': self.metadata
        }


@dataclass
class ErrorSegment:
    """Store error segment (subgroup with high error rate)."""
    segment_name: str
    condition: str
    total_samples: int
    error_count: int
    error_rate: float
    avg_confidence: float
    feature_stats: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'segment_name': self.segment_name,
            'condition': self.condition,
            'total_samples': int(self.total_samples),
            'error_count': int(self.error_count),
            'error_rate': float(self.error_rate),
            'avg_confidence': float(self.avg_confidence),
            'feature_stats': {k: float(v) for k, v in self.feature_stats.items()},
            'metadata': self.metadata
        }


@dataclass
class ErrorAnalysisResult:
    """Store comprehensive error analysis results."""
    total_predictions: int
    total_errors: int
    error_rate: float
    patterns: List[ErrorPattern]
    segments: List[ErrorSegment]
    confusion_stats: Dict[str, Any]
    confidence_analysis: Dict[str, float]
    feature_importance: Dict[str, float]
    recommendations: List[str]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Convert confidence_analysis (may contain nested dicts)
        confidence_analysis_serializable = {}
        for k, v in self.confidence_analysis.items():
            if isinstance(v, dict):
                confidence_analysis_serializable[k] = {
                    k2: float(v2) for k2, v2 in v.items()
                }
            else:
                confidence_analysis_serializable[k] = float(v)

        return {
            'total_predictions': int(self.total_predictions),
            'total_errors': int(self.total_errors),
            'error_rate': float(self.error_rate),
            'patterns': [p.to_dict() for p in self.patterns],
            'segments': [s.to_dict() for s in self.segments],
            'confusion_stats': self.confusion_stats,
            'confidence_analysis': confidence_analysis_serializable,
            'feature_importance': {k: float(v) for k, v in self.feature_importance.items()},
            'recommendations': self.recommendations,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class ErrorAnalyzer:
    """
    Comprehensive error analysis framework.

    Provides methods for:
    - Error pattern detection
    - Misclassification analysis
    - Error segmentation
    - Confidence calibration check
    - Feature-based error analysis
    - Actionable recommendations
    """

    def __init__(self, class_names: List[str] = None):
        """
        Initialize error analyzer.

        Parameters
        ----------
        class_names : List[str], optional
            Class labels for classification tasks
        """
        self.class_names = class_names or ['Negative', 'Positive']
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized ErrorAnalyzer with {len(self.class_names)} classes")

    def analyze_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze confusion matrix in detail.

        Parameters
        ----------
        y_true : np.ndarray
            True labels
        y_pred : np.ndarray
            Predicted labels

        Returns
        -------
        Dict[str, Any]
            Confusion matrix statistics
        """
        self.logger.info("Analyzing confusion matrix")

        # Create confusion matrix
        n_classes = len(self.class_names)
        cm = np.zeros((n_classes, n_classes), dtype=int)

        for i in range(len(y_true)):
            cm[int(y_true[i]), int(y_pred[i])] += 1

        # Calculate per-class metrics
        class_stats = {}
        for i, class_name in enumerate(self.class_names):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            tn = cm.sum() - tp - fp - fn

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            class_stats[class_name] = {
                'true_positives': int(tp),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_negatives': int(tn),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1)
            }

        return {
            'confusion_matrix': cm.tolist(),
            'class_statistics': class_stats,
            'accuracy': float((y_true == y_pred).mean())
        }

    def detect_error_patterns(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray = None
    ) -> List[ErrorPattern]:
        """
        Detect systematic error patterns.

        Parameters
        ----------
        y_true : np.ndarray
            True labels
        y_pred : np.ndarray
            Predicted labels
        y_proba : np.ndarray, optional
            Prediction probabilities

        Returns
        -------
        List[ErrorPattern]
            Detected error patterns
        """
        self.logger.info("Detecting error patterns")
        patterns = []

        # Find errors
        errors = y_true != y_pred
        error_indices = np.where(errors)[0]
        n_errors = errors.sum()

        if n_errors == 0:
            return patterns

        # Pattern 1: High confidence errors (if probabilities available)
        if y_proba is not None:
            max_proba = y_proba.max(axis=1)
            high_conf_errors = errors & (max_proba > 0.8)
            n_high_conf_errors = high_conf_errors.sum()

            if n_high_conf_errors > 0:
                pattern = ErrorPattern(
                    pattern_type='high_confidence_errors',
                    description='Predictions with >80% confidence that are wrong',
                    frequency=n_high_conf_errors,
                    percentage=(n_high_conf_errors / n_errors) * 100,
                    severity='critical' if n_high_conf_errors / len(y_true) > 0.05 else 'high',
                    examples=np.where(high_conf_errors)[0][:5].tolist(),
                    metadata={'avg_confidence': float(max_proba[high_conf_errors].mean())}
                )
                patterns.append(pattern)

        # Pattern 2: Class-specific errors
        for i, class_name in enumerate(self.class_names):
            class_mask = y_true == i
            class_errors = errors & class_mask
            n_class_errors = class_errors.sum()
            n_class_total = class_mask.sum()

            if n_class_total > 0:
                error_rate = n_class_errors / n_class_total
                if error_rate > 0.3:  # More than 30% error rate
                    pattern = ErrorPattern(
                        pattern_type=f'class_{class_name}_errors',
                        description=f'{class_name} predictions have high error rate',
                        frequency=n_class_errors,
                        percentage=(n_class_errors / n_errors) * 100,
                        severity='high' if error_rate > 0.5 else 'medium',
                        examples=np.where(class_errors)[0][:5].tolist(),
                        metadata={'class_error_rate': float(error_rate)}
                    )
                    patterns.append(pattern)

        # Pattern 3: Systematic misclassification
        if len(self.class_names) == 2:
            # For binary classification, check if always predicting one class
            pred_distribution = Counter(y_pred[error_indices])
            most_common_pred = pred_distribution.most_common(1)[0]
            if most_common_pred[1] / n_errors > 0.8:  # 80%+ errors are one prediction
                pattern = ErrorPattern(
                    pattern_type='systematic_bias',
                    description=f'Model predominantly predicts {self.class_names[most_common_pred[0]]} when wrong',
                    frequency=most_common_pred[1],
                    percentage=(most_common_pred[1] / n_errors) * 100,
                    severity='high',
                    examples=error_indices[:5].tolist(),
                    metadata={'biased_class': self.class_names[most_common_pred[0]]}
                )
                patterns.append(pattern)

        return patterns

    def segment_errors(
        self,
        X: pd.DataFrame,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray = None,
        n_segments: int = 5
    ) -> List[ErrorSegment]:
        """
        Identify data segments with high error rates.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix
        y_true : np.ndarray
            True labels
        y_pred : np.ndarray
            Predicted labels
        y_proba : np.ndarray, optional
            Prediction probabilities
        n_segments : int
            Number of segments to identify

        Returns
        -------
        List[ErrorSegment]
            Error segments
        """
        self.logger.info(f"Segmenting errors into {n_segments} groups")
        segments = []

        errors = y_true != y_pred
        confidences = y_proba.max(axis=1) if y_proba is not None else np.ones(len(y_true))

        # Segment 1: By each feature (find features with high error correlation)
        for col in X.columns[:10]:  # Limit to first 10 features for demo
            try:
                # For numerical features, split by median
                if pd.api.types.is_numeric_dtype(X[col]):
                    median_val = X[col].median()
                    high_mask = X[col] > median_val
                    low_mask = X[col] <= median_val

                    for mask, label in [(high_mask, 'high'), (low_mask, 'low')]:
                        n_samples = mask.sum()
                        if n_samples < 10:  # Skip small segments
                            continue

                        n_errors = (errors & mask).sum()
                        error_rate = n_errors / n_samples if n_samples > 0 else 0

                        if error_rate > 0.4:  # High error rate threshold
                            segment = ErrorSegment(
                                segment_name=f'{col}_{label}',
                                condition=f'{col} {">" if label == "high" else "<="} {median_val:.2f}',
                                total_samples=int(n_samples),
                                error_count=int(n_errors),
                                error_rate=float(error_rate),
                                avg_confidence=float(confidences[mask].mean()),
                                feature_stats={
                                    'mean': float(X.loc[mask, col].mean()),
                                    'std': float(X.loc[mask, col].std())
                                }
                            )
                            segments.append(segment)
            except Exception as e:
                self.logger.warning(f"Error processing feature {col}: {e}")
                continue

        # Sort by error rate and return top segments
        segments.sort(key=lambda x: x.error_rate, reverse=True)
        return segments[:n_segments]

    def analyze_confidence(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray
    ) -> Dict[str, float]:
        """
        Analyze prediction confidence and calibration.

        Parameters
        ----------
        y_true : np.ndarray
            True labels
        y_proba : np.ndarray
            Prediction probabilities

        Returns
        -------
        Dict[str, float]
            Confidence analysis metrics
        """
        self.logger.info("Analyzing prediction confidence")

        max_proba = y_proba.max(axis=1)
        y_pred = y_proba.argmax(axis=1)
        correct = y_true == y_pred

        # Confidence for correct vs incorrect predictions
        correct_confidence = max_proba[correct].mean() if correct.any() else 0.0
        incorrect_confidence = max_proba[~correct].mean() if (~correct).any() else 0.0

        # Confidence bins
        bins = [0, 0.5, 0.7, 0.8, 0.9, 1.0]
        bin_labels = ['0-50%', '50-70%', '70-80%', '80-90%', '90-100%']
        bin_accuracies = {}

        for i in range(len(bins) - 1):
            mask = (max_proba >= bins[i]) & (max_proba < bins[i+1])
            if mask.sum() > 0:
                bin_acc = correct[mask].mean()
                bin_accuracies[bin_labels[i]] = float(bin_acc)

        return {
            'avg_confidence_correct': float(correct_confidence),
            'avg_confidence_incorrect': float(incorrect_confidence),
            'confidence_gap': float(correct_confidence - incorrect_confidence),
            'overall_avg_confidence': float(max_proba.mean()),
            'bin_accuracies': bin_accuracies
        }

    def generate_recommendations(
        self,
        patterns: List[ErrorPattern],
        segments: List[ErrorSegment],
        confusion_stats: Dict[str, Any]
    ) -> List[str]:
        """
        Generate actionable recommendations based on error analysis.

        Parameters
        ----------
        patterns : List[ErrorPattern]
            Detected error patterns
        segments : List[ErrorSegment]
            Error segments
        confusion_stats : Dict[str, Any]
            Confusion matrix statistics

        Returns
        -------
        List[str]
            Actionable recommendations
        """
        recommendations = []

        # Check for high confidence errors
        high_conf_pattern = next(
            (p for p in patterns if p.pattern_type == 'high_confidence_errors'),
            None
        )
        if high_conf_pattern and high_conf_pattern.frequency > 0:
            recommendations.append(
                f"⚠️ {high_conf_pattern.frequency} high-confidence errors detected "
                f"({high_conf_pattern.percentage:.1f}% of errors). "
                "Consider calibrating model probabilities or reviewing feature quality."
            )

        # Check for class imbalance issues
        class_stats = confusion_stats.get('class_statistics', {})
        for class_name, stats in class_stats.items():
            if stats['recall'] < 0.5:
                recommendations.append(
                    f"📉 Low recall ({stats['recall']:.2%}) for class '{class_name}'. "
                    "Consider collecting more training examples or using class weights."
                )

            if stats['precision'] < 0.5:
                recommendations.append(
                    f"📉 Low precision ({stats['precision']:.2%}) for class '{class_name}'. "
                    "Consider adding features that better distinguish this class."
                )

        # Check for high-error segments
        if segments:
            top_segment = segments[0]
            if top_segment.error_rate > 0.5:
                recommendations.append(
                    f"🎯 High error rate ({top_segment.error_rate:.1%}) in segment: {top_segment.condition}. "
                    "This subgroup may need specialized handling or additional features."
                )

        # General recommendations
        overall_accuracy = confusion_stats.get('accuracy', 0)
        if overall_accuracy < 0.7:
            recommendations.append(
                "💡 Overall accuracy is below 70%. Consider: "
                "(1) Feature engineering, (2) Model complexity adjustment, "
                "(3) Data quality review, (4) Ensemble methods."
            )

        return recommendations

    def analyze_errors(
        self,
        X: pd.DataFrame,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray = None,
        feature_importance: Dict[str, float] = None
    ) -> ErrorAnalysisResult:
        """
        Comprehensive error analysis.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix
        y_true : np.ndarray
            True labels
        y_pred : np.ndarray
            Predicted labels
        y_proba : np.ndarray, optional
            Prediction probabilities
        feature_importance : Dict[str, float], optional
            Feature importance scores

        Returns
        -------
        ErrorAnalysisResult
            Complete error analysis results
        """
        self.logger.info("Performing comprehensive error analysis")

        # Basic statistics
        total_predictions = len(y_true)
        errors = y_true != y_pred
        total_errors = errors.sum()
        error_rate = total_errors / total_predictions

        # Confusion matrix analysis
        confusion_stats = self.analyze_confusion_matrix(y_true, y_pred)

        # Detect error patterns
        patterns = self.detect_error_patterns(y_true, y_pred, y_proba)

        # Segment errors
        segments = self.segment_errors(X, y_true, y_pred, y_proba)

        # Confidence analysis
        if y_proba is not None:
            confidence_analysis = self.analyze_confidence(y_true, y_proba)
        else:
            confidence_analysis = {}

        # Generate recommendations
        recommendations = self.generate_recommendations(patterns, segments, confusion_stats)

        result = ErrorAnalysisResult(
            total_predictions=total_predictions,
            total_errors=total_errors,
            error_rate=error_rate,
            patterns=patterns,
            segments=segments,
            confusion_stats=confusion_stats,
            confidence_analysis=confidence_analysis,
            feature_importance=feature_importance or {},
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
            metadata={'n_features': X.shape[1], 'n_classes': len(self.class_names)}
        )

        return result

    def export_results(self, output_path: str, results: ErrorAnalysisResult) -> None:
        """
        Export error analysis results to JSON file.

        Parameters
        ----------
        output_path : str
            Path to output JSON file
        results : ErrorAnalysisResult
            Results to export
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)

        self.logger.info(f"Results exported to {output_path}")


def demo_error_analysis():
    """Demonstrate error analysis framework with synthetic data."""
    logger.info("=== Error Analysis Framework Demo ===\n")

    # Create output directory
    output_dir = Path("/tmp/error_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize analyzer
    analyzer = ErrorAnalyzer(class_names=['Loss', 'Win'])

    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10

    # Create features
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )

    # Add a problematic feature (high correlation with errors)
    X['problematic_feature'] = np.random.randn(n_samples)

    # Create true labels (60% wins)
    y_true = (np.random.random(n_samples) > 0.4).astype(int)

    # Create predictions with systematic errors
    y_pred = y_true.copy()
    # Introduce errors:
    # 1. High confidence errors (model very confident but wrong)
    high_conf_error_idx = np.random.choice(n_samples, 50, replace=False)
    y_pred[high_conf_error_idx] = 1 - y_pred[high_conf_error_idx]

    # 2. Errors correlated with problematic feature
    problematic_idx = X['problematic_feature'] > 1.5
    y_pred[problematic_idx] = 1 - y_true[problematic_idx]

    # 3. Class imbalance errors (predict Win more often)
    imbalance_idx = np.random.choice(np.where(y_true == 0)[0], 80, replace=False)
    y_pred[imbalance_idx] = 1

    # Create probabilities
    y_proba = np.zeros((n_samples, 2))
    for i in range(n_samples):
        if i in high_conf_error_idx:
            # High confidence errors
            y_proba[i, y_pred[i]] = 0.85 + np.random.random() * 0.14
        else:
            # Normal confidence
            y_proba[i, y_pred[i]] = 0.55 + np.random.random() * 0.3

        y_proba[i, 1 - y_pred[i]] = 1 - y_proba[i, y_pred[i]]

    # Feature importance (synthetic)
    feature_importance = {f'feature_{i}': np.random.random() for i in range(n_features)}
    feature_importance['problematic_feature'] = 0.25

    # Run comprehensive error analysis
    logger.info("\n--- Comprehensive Error Analysis ---")
    results = analyzer.analyze_errors(
        X, y_true, y_pred, y_proba, feature_importance
    )

    # Display results
    logger.info(f"\n📊 Overall Statistics:")
    logger.info(f"  Total predictions: {results.total_predictions}")
    logger.info(f"  Total errors: {results.total_errors}")
    logger.info(f"  Error rate: {results.error_rate:.2%}")

    logger.info(f"\n🔍 Detected Patterns ({len(results.patterns)}):")
    for pattern in results.patterns:
        logger.info(f"  - {pattern.pattern_type}: {pattern.description}")
        logger.info(f"    Frequency: {pattern.frequency} ({pattern.percentage:.1f}% of errors)")
        logger.info(f"    Severity: {pattern.severity.upper()}")

    logger.info(f"\n📍 Error Segments ({len(results.segments)}):")
    for segment in results.segments[:3]:  # Top 3
        logger.info(f"  - {segment.segment_name}: {segment.error_rate:.1%} error rate")
        logger.info(f"    Condition: {segment.condition}")
        logger.info(f"    Samples: {segment.error_count}/{segment.total_samples}")

    logger.info(f"\n🎯 Confusion Matrix:")
    cm = results.confusion_stats['confusion_matrix']
    logger.info(f"           Predicted Loss  Predicted Win")
    logger.info(f"True Loss:      {cm[0][0]:4d}          {cm[0][1]:4d}")
    logger.info(f"True Win:       {cm[1][0]:4d}          {cm[1][1]:4d}")

    logger.info(f"\n📈 Confidence Analysis:")
    for metric, value in results.confidence_analysis.items():
        if metric != 'bin_accuracies':
            logger.info(f"  {metric}: {value:.4f}")

    logger.info(f"\n💡 Recommendations ({len(results.recommendations)}):")
    for i, rec in enumerate(results.recommendations, 1):
        logger.info(f"  {i}. {rec}")

    # Export results
    analyzer.export_results(str(output_dir / "error_analysis_results.json"), results)

    logger.info(f"\n✅ Error analysis demo complete!")
    logger.info(f"Results exported to {output_dir}")

    return results


if __name__ == '__main__':
    demo_error_analysis()
