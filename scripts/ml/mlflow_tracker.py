"""
MLflow Integration for NBA Simulator
Provides easy-to-use interface for experiment tracking and model registry
"""

import mlflow
import mlflow.sklearn
import mlflow.xgboost
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MLflowTracker:
    """Wrapper for MLflow tracking in NBA Simulator"""

    def __init__(self, experiment_name: str = "nba_simulator"):
        """Initialize MLflow tracker"""
        self.experiment_name = experiment_name
        self.setup()

    def setup(self):
        """Set up MLflow tracking"""
        # Set tracking URI to local directory
        tracking_uri = "file://./mlruns"
        mlflow.set_tracking_uri(tracking_uri)

        # Set experiment
        try:
            mlflow.set_experiment(self.experiment_name)
            logger.info(f"MLflow experiment: {self.experiment_name}")
        except Exception as e:
            logger.error(f"Failed to set experiment: {e}")

    def start_run(self, run_name: str, tags: Optional[Dict[str, str]] = None):
        """Start MLflow run"""
        return mlflow.start_run(run_name=run_name, tags=tags or {})

    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics"""
        mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log artifact"""
        mlflow.log_artifact(local_path, artifact_path=artifact_path)

    def log_model(self, model, artifact_path: str, **kwargs):
        """Log model"""
        if hasattr(model, "get_params"):  # Sklearn-style
            mlflow.sklearn.log_model(model, artifact_path, **kwargs)
        else:
            logger.warning(f"Unsupported model type: {type(model)}")

    def register_model(self, model_uri: str, name: str):
        """Register model in model registry"""
        try:
            result = mlflow.register_model(model_uri, name)
            logger.info(f"Registered model: {name} (version {result.version})")
            return result
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            return None

    def load_model(self, model_name: str, version: Optional[int] = None):
        """Load model from registry"""
        try:
            if version:
                model_uri = f"models:/{model_name}/{version}"
            else:
                model_uri = f"models:/{model_name}/latest"

            model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"Loaded model: {model_uri}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None


# Example usage
if __name__ == "__main__":
    tracker = MLflowTracker("nba_simulator_test")

    with tracker.start_run("test_run"):
        tracker.log_params({"test_param": "value"})
        tracker.log_metrics({"test_metric": 0.95})
        print("✓ MLflow tracking test successful!")
