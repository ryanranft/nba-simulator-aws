#!/usr/bin/env python3
"""
Model Interpretability Tools

Implements rec_13: Comprehensive model interpretability toolkit for NBA prediction models.

Features:
1. SHAP (SHapley Additive exPlanations) values
2. Feature importance analysis (multiple methods)
3. Partial dependence plots (PDP)
4. Individual conditional expectation (ICE) plots
5. Feature interaction analysis
6. Model-agnostic explanations
7. Integration with MLflow

Source Books: Hands-On ML, Stats 601, Elements of Statistical Learning
Created: October 2025
Status: rec_13 implementation
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ML libraries
from sklearn.inspection import partial_dependence, permutation_importance
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import joblib

# SHAP for model-agnostic interpretability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with: pip install shap")

# MLflow integration
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logging.warning("MLflow not available for logging interpretability artifacts")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelInterpretabilityTools:
    """
    Comprehensive model interpretability toolkit.

    Provides multiple methods for understanding model predictions:
    - Feature importance (multiple methods)
    - SHAP values and plots
    - Partial dependence analysis
    - Individual prediction explanations
    - Feature interaction analysis
    """

    def __init__(
        self,
        model: Any,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: Optional[pd.Series] = None,
        y_test: Optional[pd.Series] = None,
        feature_names: Optional[List[str]] = None,
        output_dir: str = "/tmp/model_interpretability"
    ):
        """
        Initialize interpretability toolkit.

        Args:
            model: Trained model (scikit-learn compatible)
            X_train: Training features
            X_test: Test features
            y_train: Training labels (optional, needed for some methods)
            y_test: Test labels (optional, needed for permutation importance)
            feature_names: Feature names (extracted from X_train if not provided)
            output_dir: Directory for saving plots and reports
        """
        self.model = model
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

        # Extract feature names
        if feature_names is None:
            if isinstance(X_train, pd.DataFrame):
                self.feature_names = X_train.columns.tolist()
            else:
                self.feature_names = [f"feature_{i}" for i in range(X_train.shape[1])]
        else:
            self.feature_names = feature_names

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Storage for computed interpretability results
        self.results = {
            'feature_importance': {},
            'shap_values': None,
            'pdp_results': {},
            'ice_results': {},
            'permutation_importance': None,
            'metadata': {
                'model_type': type(model).__name__,
                'n_features': len(self.feature_names),
                'n_train_samples': len(X_train),
                'n_test_samples': len(X_test),
                'timestamp': datetime.now().isoformat()
            }
        }

        logger.info(f"Initialized ModelInterpretabilityTools for {type(model).__name__}")
        logger.info(f"Features: {len(self.feature_names)}, Output: {self.output_dir}")

    def compute_feature_importance(
        self,
        methods: List[str] = ['tree', 'permutation', 'shap']
    ) -> Dict[str, pd.DataFrame]:
        """
        Compute feature importance using multiple methods.

        Args:
            methods: List of methods to use
                - 'tree': Tree-based feature importance (for tree models)
                - 'permutation': Permutation importance
                - 'shap': SHAP-based importance

        Returns:
            Dictionary of feature importance DataFrames by method
        """
        logger.info("Computing feature importance...")
        importance_results = {}

        # Method 1: Tree-based feature importance
        if 'tree' in methods and hasattr(self.model, 'feature_importances_'):
            logger.info("Computing tree-based feature importance...")
            importances = self.model.feature_importances_
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)

            importance_results['tree'] = importance_df
            self.results['feature_importance']['tree'] = importance_df

            # Plot
            self._plot_feature_importance(
                importance_df,
                title='Tree-based Feature Importance',
                filename='feature_importance_tree.png'
            )

        # Method 2: Permutation importance
        if 'permutation' in methods and self.y_test is not None:
            logger.info("Computing permutation importance...")
            perm_importance = permutation_importance(
                self.model,
                self.X_test,
                self.y_test,
                n_repeats=10,
                random_state=42,
                n_jobs=-1
            )

            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': perm_importance.importances_mean,
                'std': perm_importance.importances_std
            }).sort_values('importance', ascending=False)

            importance_results['permutation'] = importance_df
            self.results['feature_importance']['permutation'] = importance_df
            self.results['permutation_importance'] = perm_importance

            # Plot
            self._plot_feature_importance(
                importance_df,
                title='Permutation Feature Importance',
                filename='feature_importance_permutation.png',
                with_std=True
            )

        # Method 3: SHAP-based importance
        if 'shap' in methods and SHAP_AVAILABLE:
            logger.info("Computing SHAP-based feature importance...")
            shap_values = self.compute_shap_values()

            if shap_values is not None:
                # Mean absolute SHAP value per feature
                if isinstance(shap_values, list):
                    # Multi-class classification
                    shap_importance = np.abs(shap_values[1]).mean(0)
                else:
                    shap_importance = np.abs(shap_values).mean(0)

                importance_df = pd.DataFrame({
                    'feature': self.feature_names,
                    'importance': shap_importance
                }).sort_values('importance', ascending=False)

                importance_results['shap'] = importance_df
                self.results['feature_importance']['shap'] = importance_df

                # Plot
                self._plot_feature_importance(
                    importance_df,
                    title='SHAP-based Feature Importance',
                    filename='feature_importance_shap.png'
                )

        logger.info(f"Computed feature importance using {len(importance_results)} methods")
        return importance_results

    def compute_shap_values(
        self,
        sample_size: int = 100,
        force_recompute: bool = False
    ) -> Optional[np.ndarray]:
        """
        Compute SHAP values for model predictions.

        Args:
            sample_size: Number of samples to use for SHAP computation
            force_recompute: Recompute even if already cached

        Returns:
            SHAP values array or None if SHAP unavailable
        """
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available - skipping SHAP analysis")
            return None

        if self.results['shap_values'] is not None and not force_recompute:
            logger.info("Using cached SHAP values")
            return self.results['shap_values']

        logger.info("Computing SHAP values...")

        # Sample data for SHAP (can be expensive for large datasets)
        X_sample = self.X_test.sample(n=min(sample_size, len(self.X_test)), random_state=42)

        # Choose explainer based on model type
        model_type = type(self.model).__name__

        if 'Tree' in model_type or 'Forest' in model_type or 'Boost' in model_type:
            # Tree-based explainer (faster)
            logger.info(f"Using TreeExplainer for {model_type}")
            explainer = shap.TreeExplainer(self.model)
        else:
            # Model-agnostic explainer
            logger.info(f"Using KernelExplainer for {model_type}")
            background = shap.sample(self.X_train, 100)
            explainer = shap.KernelExplainer(self.model.predict_proba, background)

        shap_values = explainer.shap_values(X_sample)

        self.results['shap_values'] = shap_values
        self.results['shap_explainer'] = explainer
        self.results['shap_sample'] = X_sample

        # Generate SHAP plots
        self._plot_shap_summary(shap_values, X_sample)
        self._plot_shap_waterfall(shap_values, X_sample, explainer)

        logger.info("SHAP values computed successfully")
        return shap_values

    def compute_partial_dependence(
        self,
        features: Optional[List[Union[int, str]]] = None,
        n_top_features: int = 10
    ) -> Dict[str, Any]:
        """
        Compute partial dependence plots for top features.

        Args:
            features: Specific features to analyze (indices or names)
            n_top_features: Number of top features to analyze if features not specified

        Returns:
            Partial dependence results
        """
        logger.info("Computing partial dependence...")

        # Determine features to analyze
        if features is None:
            # Use top N features by importance
            if 'tree' in self.results['feature_importance']:
                top_features = self.results['feature_importance']['tree'].head(n_top_features)['feature'].tolist()
            elif 'permutation' in self.results['feature_importance']:
                top_features = self.results['feature_importance']['permutation'].head(n_top_features)['feature'].tolist()
            else:
                # Default to first N features
                top_features = self.feature_names[:n_top_features]

            feature_indices = [self.feature_names.index(f) for f in top_features]
        else:
            # Convert feature names to indices if needed
            feature_indices = []
            for f in features:
                if isinstance(f, str):
                    feature_indices.append(self.feature_names.index(f))
                else:
                    feature_indices.append(f)

        # Compute partial dependence
        logger.info(f"Computing PDP for {len(feature_indices)} features...")

        pdp_results = {}
        for idx in feature_indices:
            feature_name = self.feature_names[idx]

            # Compute PDP
            pd_result = partial_dependence(
                self.model,
                self.X_test,
                features=[idx],
                kind='average',
                grid_resolution=50
            )

            # Handle different scikit-learn versions
            if 'values' in pd_result:
                grid_values = pd_result['values'][0]
                pd_values = pd_result['average'][0]
            elif 'grid_values' in pd_result:
                grid_values = pd_result['grid_values'][0]
                pd_values = pd_result['average'][0]
            else:
                # Very old version - unpack tuple
                grid_values = pd_result[1][0]
                pd_values = pd_result[0][0]

            pdp_results[feature_name] = {
                'grid_values': grid_values,
                'pd_values': pd_values
            }

            # Plot
            self._plot_partial_dependence(
                grid_values,
                pd_values,
                feature_name
            )

        self.results['pdp_results'] = pdp_results
        logger.info(f"Computed partial dependence for {len(pdp_results)} features")
        return pdp_results

    def explain_prediction(
        self,
        sample_idx: int = 0,
        use_shap: bool = True
    ) -> Dict[str, Any]:
        """
        Explain a single prediction in detail.

        Args:
            sample_idx: Index of sample to explain from X_test
            use_shap: Use SHAP for explanation (otherwise use feature values)

        Returns:
            Explanation dictionary
        """
        logger.info(f"Explaining prediction for sample {sample_idx}...")

        # Get sample
        if isinstance(self.X_test, pd.DataFrame):
            sample = self.X_test.iloc[sample_idx:sample_idx+1]
        else:
            sample = self.X_test[sample_idx:sample_idx+1]

        # Get prediction
        prediction = self.model.predict(sample)[0]

        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(sample)[0]
        else:
            proba = None

        explanation = {
            'sample_idx': sample_idx,
            'prediction': prediction,
            'probability': proba.tolist() if proba is not None else None,
            'feature_values': {}
        }

        # Add feature values
        for i, feature_name in enumerate(self.feature_names):
            if isinstance(self.X_test, pd.DataFrame):
                value = sample.iloc[0, i]
            else:
                value = sample[0, i]
            explanation['feature_values'][feature_name] = float(value)

        # SHAP explanation if available
        if use_shap and SHAP_AVAILABLE:
            shap_values = self.compute_shap_values()
            if shap_values is not None:
                # Find sample in SHAP sample
                if sample_idx < len(self.results['shap_sample']):
                    if isinstance(shap_values, list):
                        sample_shap = shap_values[1][sample_idx]
                    else:
                        sample_shap = shap_values[sample_idx]

                    explanation['shap_values'] = {
                        self.feature_names[i]: float(sample_shap[i])
                        for i in range(len(self.feature_names))
                    }

        logger.info(f"Prediction: {prediction}, Probability: {proba}")
        return explanation

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate comprehensive interpretability report.

        Args:
            output_file: Path to save report (default: output_dir/report.json)

        Returns:
            Path to generated report
        """
        logger.info("Generating interpretability report...")

        if output_file is None:
            output_file = self.output_dir / "interpretability_report.json"

        # Compile report
        report = {
            'metadata': self.results['metadata'],
            'feature_importance': {},
            'shap_available': SHAP_AVAILABLE and self.results['shap_values'] is not None,
            'pdp_available': len(self.results['pdp_results']) > 0,
            'top_features': []
        }

        # Add feature importance from all methods
        for method, importance_df in self.results['feature_importance'].items():
            report['feature_importance'][method] = importance_df.head(20).to_dict('records')

        # Identify top features across methods
        if self.results['feature_importance']:
            # Combine rankings from all methods
            all_features = set()
            for method_df in self.results['feature_importance'].values():
                all_features.update(method_df.head(10)['feature'].tolist())
            report['top_features'] = list(all_features)

        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {output_file}")

        # Log to MLflow if available
        if MLFLOW_AVAILABLE:
            try:
                mlflow.log_artifact(str(output_file))
                mlflow.log_dict(report, "interpretability_report.json")
                logger.info("Report logged to MLflow")
            except Exception as e:
                logger.warning(f"Could not log to MLflow: {e}")

        return str(output_file)

    # ============ PLOTTING METHODS ============

    def _plot_feature_importance(
        self,
        importance_df: pd.DataFrame,
        title: str,
        filename: str,
        n_features: int = 20,
        with_std: bool = False
    ):
        """Plot feature importance bar chart."""
        plt.figure(figsize=(10, 8))

        # Get top N features
        top_features = importance_df.head(n_features)

        if with_std and 'std' in top_features.columns:
            plt.barh(
                range(len(top_features)),
                top_features['importance'],
                xerr=top_features['std'],
                alpha=0.7
            )
        else:
            plt.barh(range(len(top_features)), top_features['importance'], alpha=0.7)

        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance')
        plt.title(title)
        plt.tight_layout()

        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved feature importance plot to {save_path}")

    def _plot_shap_summary(self, shap_values: np.ndarray, X_sample: pd.DataFrame):
        """Generate SHAP summary plot."""
        if not SHAP_AVAILABLE:
            return

        plt.figure(figsize=(10, 8))

        # Handle multi-class
        if isinstance(shap_values, list):
            shap_values_to_plot = shap_values[1]
        else:
            shap_values_to_plot = shap_values

        shap.summary_plot(
            shap_values_to_plot,
            X_sample,
            feature_names=self.feature_names,
            show=False,
            max_display=20
        )

        save_path = self.output_dir / "shap_summary.png"
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved SHAP summary plot to {save_path}")

    def _plot_shap_waterfall(
        self,
        shap_values: np.ndarray,
        X_sample: pd.DataFrame,
        explainer: Any,
        sample_idx: int = 0
    ):
        """Generate SHAP waterfall plot for a single prediction."""
        if not SHAP_AVAILABLE:
            return

        try:
            # Handle multi-class
            if isinstance(shap_values, list):
                shap_values_to_plot = shap_values[1][sample_idx]
            else:
                shap_values_to_plot = shap_values[sample_idx]

            plt.figure(figsize=(10, 8))
            shap.waterfall_plot(
                shap.Explanation(
                    values=shap_values_to_plot,
                    base_values=explainer.expected_value if not isinstance(explainer.expected_value, list) else explainer.expected_value[1],
                    data=X_sample.iloc[sample_idx].values,
                    feature_names=self.feature_names
                ),
                show=False
            )

            save_path = self.output_dir / "shap_waterfall_sample0.png"
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved SHAP waterfall plot to {save_path}")
        except Exception as e:
            logger.warning(f"Could not create waterfall plot: {e}")

    def _plot_partial_dependence(
        self,
        grid_values: np.ndarray,
        pd_values: np.ndarray,
        feature_name: str
    ):
        """Plot partial dependence for a single feature."""
        plt.figure(figsize=(8, 6))
        plt.plot(grid_values, pd_values, linewidth=2)
        plt.xlabel(feature_name)
        plt.ylabel('Partial Dependence')
        plt.title(f'Partial Dependence Plot: {feature_name}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        safe_name = feature_name.replace('/', '_').replace(' ', '_')
        save_path = self.output_dir / f"pdp_{safe_name}.png"
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved PDP plot to {save_path}")


def main():
    """
    Demo: Load a model and generate interpretability analysis.
    """
    logger.info("=" * 80)
    logger.info("Model Interpretability Tools - Demo")
    logger.info("=" * 80)

    # Check if model exists
    model_path = "/tmp/nba_models/game_outcome_model.pkl"

    if not os.path.exists(model_path):
        logger.warning(f"No model found at {model_path}")
        logger.info("Training a simple model for demo...")

        # Create synthetic NBA data for demo
        np.random.seed(42)
        n_samples = 1000

        feature_names = [
            'home_fg_pct', 'away_fg_pct', 'home_3p_pct', 'away_3p_pct',
            'home_ft_pct', 'away_ft_pct', 'home_rebounds', 'away_rebounds',
            'home_assists', 'away_assists', 'home_turnovers', 'away_turnovers',
            'home_steals', 'away_steals', 'home_blocks', 'away_blocks',
            'home_fouls', 'away_fouls', 'home_rest_days', 'away_rest_days'
        ]

        # Generate features
        X = np.random.randn(n_samples, len(feature_names))

        # Generate target: home team wins if they have better stats
        y = (X[:, 0] - X[:, 1] +
             0.5 * (X[:, 2] - X[:, 3]) +
             0.3 * (X[:, 6] - X[:, 7]) > 0).astype(int)

        # Convert to DataFrame
        X_df = pd.DataFrame(X, columns=feature_names)
        y_series = pd.Series(y, name='home_win')

        # Split
        split_idx = int(0.8 * n_samples)
        X_train, X_test = X_df[:split_idx], X_df[split_idx:]
        y_train, y_test = y_series[:split_idx], y_series[split_idx:]

        # Train model
        logger.info("Training Random Forest model...")
        model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X_train, y_train)

        # Save model
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")
    else:
        logger.info(f"Loading model from {model_path}")
        model = joblib.load(model_path)

        # Note: In production, load actual training/test data
        logger.warning("Using synthetic data for demo - replace with actual data in production")

        np.random.seed(42)
        n_samples = 1000

        feature_names = [
            'home_fg_pct', 'away_fg_pct', 'home_3p_pct', 'away_3p_pct',
            'home_ft_pct', 'away_ft_pct', 'home_rebounds', 'away_rebounds',
            'home_assists', 'away_assists', 'home_turnovers', 'away_turnovers',
            'home_steals', 'away_steals', 'home_blocks', 'away_blocks',
            'home_fouls', 'away_fouls', 'home_rest_days', 'away_rest_days'
        ]

        X = np.random.randn(n_samples, len(feature_names))
        y = (X[:, 0] - X[:, 1] + 0.5 * (X[:, 2] - X[:, 3]) + 0.3 * (X[:, 6] - X[:, 7]) > 0).astype(int)

        X_df = pd.DataFrame(X, columns=feature_names)
        y_series = pd.Series(y, name='home_win')

        split_idx = int(0.8 * n_samples)
        X_train, X_test = X_df[:split_idx], X_df[split_idx:]
        y_train, y_test = y_series[:split_idx], y_series[split_idx:]

    # Initialize interpretability tools
    interp = ModelInterpretabilityTools(
        model=model,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        feature_names=feature_names,
        output_dir="/tmp/model_interpretability"
    )

    # Compute feature importance
    logger.info("\n" + "=" * 80)
    logger.info("Computing Feature Importance")
    logger.info("=" * 80)
    importance_results = interp.compute_feature_importance(methods=['tree', 'permutation', 'shap'])

    for method, importance_df in importance_results.items():
        logger.info(f"\n{method.upper()} - Top 10 Features:")
        logger.info(importance_df.head(10).to_string())

    # Compute partial dependence
    logger.info("\n" + "=" * 80)
    logger.info("Computing Partial Dependence")
    logger.info("=" * 80)
    pdp_results = interp.compute_partial_dependence(n_top_features=5)
    logger.info(f"Computed PDP for {len(pdp_results)} features")

    # Explain a prediction
    logger.info("\n" + "=" * 80)
    logger.info("Explaining Individual Prediction")
    logger.info("=" * 80)
    explanation = interp.explain_prediction(sample_idx=0, use_shap=True)
    logger.info(f"Sample 0 Prediction: {explanation['prediction']}")
    logger.info(f"Probability: {explanation['probability']}")

    # Generate report
    logger.info("\n" + "=" * 80)
    logger.info("Generating Report")
    logger.info("=" * 80)
    report_path = interp.generate_report()
    logger.info(f"Report saved to: {report_path}")

    logger.info("\n" + "=" * 80)
    logger.info("Interpretability Analysis Complete!")
    logger.info("=" * 80)
    logger.info(f"Output directory: {interp.output_dir}")
    logger.info("Generated files:")
    for file in sorted(interp.output_dir.iterdir()):
        logger.info(f"  - {file.name}")


if __name__ == "__main__":
    main()
