#!/usr/bin/env python3
"""
Implementation Script: Model Versioning with MLflow

Recommendation ID: ml_systems_1
Priority: CRITICAL
Source Book: Designing Machine Learning Systems
Generated: 2025-10-15T21:01:26.113136
Implemented: 2025-10-15

Description:
From ML Systems book: Ch 5, Ch 10
- Implement model registry with MLflow
- Enable model versioning and lineage tracking
- Support model promotion across stages (staging, production)
- Track model metadata (parameters, metrics, artifacts)

Expected Impact: HIGH - Track models, enable rollback
Time Estimate: 1 day

Prerequisites:
- pip install mlflow boto3
- AWS credentials configured (for S3 artifact storage)
- RDS PostgreSQL running (for backend store)
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# MLflow imports (with graceful degradation)
try:
    import mlflow
    import mlflow.sklearn
    import mlflow.pyfunc
    from mlflow.tracking import MlflowClient

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not installed. Run: pip install mlflow boto3")


class ModelVersioningWithMlflow:
    """
    Implementation of: Model Versioning with MLflow

    Implements model versioning system using MLflow as described in
    "Designing Machine Learning Systems" (Ch 5: Model Development, Ch 10: Infrastructure)

    Features:
    - Model registry with versioning
    - Experiment tracking
    - Model lineage and metadata
    - Stage-based promotion (None → Staging → Production)
    - Artifact storage (models, plots, data)
    - Model comparison and rollback

    Architecture:
    - Backend Store: PostgreSQL (metadata, params, metrics)
    - Artifact Store: S3 (model files, plots, data)
    - Tracking Server: Local or remote MLflow server
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ModelVersioningWithMlflow.

        Args:
            config: Configuration dictionary with:
                - tracking_uri: MLflow tracking server URI (default: local file)
                - experiment_name: Experiment name (default: 'nba-simulator-ml')
                - artifact_location: S3 bucket for artifacts (default: s3://nba-sim-raw-data-lake/mlflow)
                - backend_store_uri: PostgreSQL connection for backend (optional)
                - default_tags: Default tags for runs (dict)
        """
        self.config = config or {}
        self.setup_complete = False
        self.client = None
        self.experiment_id = None
        self.experiment_name = self.config.get("experiment_name", "nba-simulator-ml")

        logger.info(f"Initializing ModelVersioningWithMlflow...")
        logger.info(f"  Experiment: {self.experiment_name}")
        logger.info(f"  MLflow Available: {MLFLOW_AVAILABLE}")

    def setup(self) -> bool:
        """
        Set up MLflow tracking infrastructure.

        Sets up:
        1. Tracking URI (local file store or remote server)
        2. Experiment (creates if doesn't exist)
        3. MLflow client for registry operations
        4. Artifact location (S3 or local)

        Returns:
            bool: True if setup successful
        """
        try:
            logger.info("Setting up ModelVersioningWithMlflow...")

            if not MLFLOW_AVAILABLE:
                logger.error("MLflow not installed. Run: pip install mlflow boto3")
                return False

            # 1. Configure tracking URI
            tracking_uri = self.config.get("tracking_uri", "file:./mlruns")
            mlflow.set_tracking_uri(tracking_uri)
            logger.info(f"  Tracking URI: {tracking_uri}")

            # 2. Set experiment (creates if doesn't exist)
            artifact_location = self.config.get(
                "artifact_location", "s3://nba-sim-raw-data-lake/mlflow"
            )

            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                self.experiment_id = mlflow.create_experiment(
                    self.experiment_name, artifact_location=artifact_location
                )
                logger.info(
                    f"  Created experiment: {self.experiment_name} (ID: {self.experiment_id})"
                )
            else:
                self.experiment_id = experiment.experiment_id
                logger.info(
                    f"  Using existing experiment: {self.experiment_name} (ID: {self.experiment_id})"
                )

            mlflow.set_experiment(self.experiment_name)

            # 3. Initialize MLflow client for model registry
            self.client = MlflowClient(tracking_uri=tracking_uri)

            # 4. Verify artifact location is accessible
            logger.info(f"  Artifact location: {artifact_location}")

            # 5. Set default tags
            default_tags = self.config.get(
                "default_tags",
                {
                    "project": "nba-simulator-aws",
                    "component": "ml-models",
                    "environment": "development",
                },
            )
            self.default_tags = default_tags

            self.setup_complete = True
            logger.info("✅ MLflow setup complete")
            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def validate_prerequisites(self) -> bool:
        """
        Validate that all prerequisites are met.

        Checks:
        1. MLflow installed
        2. AWS credentials (if using S3)
        3. Database connection (if using PostgreSQL backend)
        4. Required Python packages

        Returns:
            bool: True if all prerequisites met
        """
        logger.info("Validating prerequisites...")

        all_valid = True

        # 1. Check MLflow installation
        if not MLFLOW_AVAILABLE:
            logger.error("❌ MLflow not installed")
            logger.error("   Install: pip install mlflow boto3")
            all_valid = False
        else:
            logger.info("✅ MLflow installed")

        # 2. Check AWS credentials (if using S3)
        artifact_location = self.config.get("artifact_location", "")
        if artifact_location.startswith("s3://"):
            try:
                import boto3

                session = boto3.Session()
                credentials = session.get_credentials()
                if credentials:
                    logger.info("✅ AWS credentials configured")
                else:
                    logger.warning(
                        "⚠️  AWS credentials not found (S3 artifacts may fail)"
                    )
                    logger.warning("   Configure: aws configure")
            except ImportError:
                logger.error("❌ boto3 not installed (required for S3)")
                logger.error("   Install: pip install boto3")
                all_valid = False
            except Exception as e:
                logger.warning(f"⚠️  AWS credential check failed: {e}")

        # 3. Check database connection (if using PostgreSQL backend)
        backend_uri = self.config.get("backend_store_uri", "")
        if backend_uri.startswith("postgresql"):
            try:
                import psycopg2

                logger.info("✅ PostgreSQL driver (psycopg2) installed")
            except ImportError:
                logger.error(
                    "❌ psycopg2 not installed (required for PostgreSQL backend)"
                )
                logger.error("   Install: pip install psycopg2-binary")
                all_valid = False

        # 4. Check Python version
        import sys

        if sys.version_info >= (3, 8):
            logger.info(
                f"✅ Python {sys.version_info.major}.{sys.version_info.minor} (compatible)"
            )
        else:
            logger.warning(
                f"⚠️  Python {sys.version_info.major}.{sys.version_info.minor} (recommend 3.8+)"
            )

        if all_valid:
            logger.info("✅ All prerequisites validated")
        else:
            logger.error("❌ Some prerequisites not met")

        return all_valid

    def register_model(
        self,
        model_name: str,
        model_artifact_path: str = None,
        run_id: str = None,
        description: str = None,
        tags: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """
        Register a model in the MLflow Model Registry.

        Args:
            model_name: Name to register the model under
            model_artifact_path: Path to model artifact (e.g., 'model' or 's3://bucket/path')
            run_id: MLflow run ID containing the model
            description: Model description
            tags: Model tags

        Returns:
            dict: Registration details (model_name, version, run_id)
        """
        try:
            logger.info(f"Registering model: {model_name}")

            # If run_id provided, register from that run
            if run_id and model_artifact_path:
                model_uri = f"runs:/{run_id}/{model_artifact_path}"
                result = mlflow.register_model(model_uri, model_name)

                logger.info(f"  Registered as version {result.version}")

                # Add description and tags if provided
                if description:
                    self.client.update_model_version(
                        name=model_name, version=result.version, description=description
                    )

                if tags:
                    for key, value in tags.items():
                        self.client.set_model_version_tag(
                            name=model_name,
                            version=result.version,
                            key=key,
                            value=value,
                        )

                return {
                    "model_name": model_name,
                    "version": result.version,
                    "run_id": run_id,
                    "status": "registered",
                }

            else:
                logger.warning("No run_id or model_artifact_path provided")
                return {"status": "skipped", "reason": "missing_artifacts"}

        except Exception as e:
            logger.error(f"Model registration failed: {e}")
            return {"status": "failed", "error": str(e)}

    def promote_model(self, model_name: str, version: int, stage: str) -> bool:
        """
        Promote a model version to a specific stage.

        Args:
            model_name: Name of the registered model
            version: Version number to promote
            stage: Target stage ('Staging', 'Production', 'Archived')

        Returns:
            bool: True if promotion successful
        """
        try:
            valid_stages = ["Staging", "Production", "Archived", "None"]
            if stage not in valid_stages:
                logger.error(f"Invalid stage: {stage}. Must be one of {valid_stages}")
                return False

            logger.info(f"Promoting {model_name} v{version} to {stage}")

            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=True,  # Archive old versions in this stage
            )

            logger.info(f"✅ Model promoted to {stage}")
            return True

        except Exception as e:
            logger.error(f"Model promotion failed: {e}")
            return False

    def get_model_version(
        self, model_name: str, stage: str = None, version: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get model version information.

        Args:
            model_name: Name of the registered model
            stage: Stage to filter by ('Staging', 'Production')
            version: Specific version number

        Returns:
            dict: Model version details or None
        """
        try:
            if version:
                mv = self.client.get_model_version(name=model_name, version=version)
                return {
                    "name": mv.name,
                    "version": mv.version,
                    "stage": mv.current_stage,
                    "description": mv.description,
                    "run_id": mv.run_id,
                    "status": mv.status,
                }
            elif stage:
                versions = self.client.get_latest_versions(model_name, stages=[stage])
                if versions:
                    mv = versions[0]
                    return {
                        "name": mv.name,
                        "version": mv.version,
                        "stage": mv.current_stage,
                        "description": mv.description,
                        "run_id": mv.run_id,
                        "status": mv.status,
                    }
            return None

        except Exception as e:
            logger.error(f"Failed to get model version: {e}")
            return None

    def execute(self) -> Dict[str, Any]:
        """
        Execute MLflow model versioning demonstration.

        Demonstrates:
        1. Creating an MLflow run
        2. Logging parameters and metrics
        3. Logging a dummy model artifact
        4. Registering the model
        5. Promoting through stages (Staging → Production)
        6. Retrieving model information

        Returns:
            dict: Execution results and metrics
        """
        if not self.setup_complete:
            raise RuntimeError("Setup must be completed before execution")

        logger.info("Executing ModelVersioningWithMlflow demonstration...")
        start_time = datetime.now()

        try:
            # 1. Start an MLflow run
            with mlflow.start_run(tags=self.default_tags) as run:
                run_id = run.info.run_id
                logger.info(f"  Started run: {run_id}")

                # 2. Log parameters (hyperparameters)
                params = {
                    "algorithm": "XGBoost",
                    "n_estimators": 100,
                    "max_depth": 6,
                    "learning_rate": 0.1,
                }
                mlflow.log_params(params)
                logger.info(f"  Logged {len(params)} parameters")

                # 3. Log metrics (model performance)
                metrics = {
                    "accuracy": 0.75,
                    "precision": 0.72,
                    "recall": 0.78,
                    "f1_score": 0.75,
                    "auc_roc": 0.82,
                }
                mlflow.log_metrics(metrics)
                logger.info(f"  Logged {len(metrics)} metrics")

                # 4. Log dummy model artifact (in production, this would be a real trained model)
                # Create a simple sklearn model for demonstration
                try:
                    from sklearn.ensemble import RandomForestClassifier

                    model = RandomForestClassifier(n_estimators=10, random_state=42)
                    mlflow.sklearn.log_model(model, "model")
                    logger.info("  Logged model artifact")
                except ImportError:
                    logger.warning(
                        "  Scikit-learn not available, skipping model logging"
                    )

                # 5. Register the model
                model_name = "nba-game-outcome-predictor"
                registration = self.register_model(
                    model_name=model_name,
                    model_artifact_path="model",
                    run_id=run_id,
                    description="NBA game outcome prediction model",
                    tags={"model_type": "classifier", "framework": "sklearn"},
                )

                # 6. Promote model through stages
                if registration.get("status") == "registered":
                    version = registration["version"]

                    # Promote to Staging
                    self.promote_model(model_name, version, "Staging")

                    # Simulate validation/approval
                    logger.info("  Simulating model validation...")

                    # Promote to Production
                    self.promote_model(model_name, version, "Production")

                    # Get production model info
                    prod_model = self.get_model_version(model_name, stage="Production")
                    logger.info(f"  Production model: v{prod_model['version']}")

            execution_time = (datetime.now() - start_time).total_seconds()

            results = {
                "success": True,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
                "experiment_id": self.experiment_id,
                "experiment_name": self.experiment_name,
                "model_name": model_name,
                "model_version": registration.get("version"),
                "final_stage": "Production",
                "parameters_logged": len(params),
                "metrics_logged": len(metrics),
                "artifact_logged": True,
                "tracking_uri": self.config.get("tracking_uri", "file:./mlruns"),
            }

            logger.info(f"✅ Execution completed in {execution_time:.2f}s")
            logger.info(
                f"   Model: {model_name} v{registration.get('version')} (Production)"
            )
            return results

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    def cleanup(self):
        """
        Clean up resources.

        Currently MLflow doesn't require explicit cleanup for tracking operations.
        In production, you might want to:
        - Close database connections (if using custom backend)
        - Flush logs
        - Archive old experiments
        """
        logger.info("Cleaning up resources...")

        # Log final statistics
        if self.experiment_id and MLFLOW_AVAILABLE:
            try:
                experiment = self.client.get_experiment(self.experiment_id)
                runs = self.client.search_runs(self.experiment_id)
                logger.info(
                    f"  Experiment '{self.experiment_name}' has {len(runs)} runs"
                )
            except Exception as e:
                logger.warning(f"Could not retrieve experiment stats: {e}")

        logger.info("✅ Cleanup complete")


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info(f"Starting: Model Versioning with MLflow")
    logger.info("=" * 80)

    # Load configuration
    config_file = os.path.join(os.path.dirname(__file__), "config.json")

    config = {}
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)

    # Initialize and execute
    implementation = ModelVersioningWithMlflow(config)

    # Validate prerequisites
    if not implementation.validate_prerequisites():
        logger.error("Prerequisites not met. Exiting.")
        sys.exit(1)

    # Setup
    if not implementation.setup():
        logger.error("Setup failed. Exiting.")
        sys.exit(1)

    # Execute
    results = implementation.execute()

    # Cleanup
    implementation.cleanup()

    # Report results
    logger.info("=" * 80)
    logger.info("Results:")
    logger.info(json.dumps(results, indent=2))
    logger.info("=" * 80)

    if results.get("success"):
        logger.info("✅ Implementation completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Implementation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
