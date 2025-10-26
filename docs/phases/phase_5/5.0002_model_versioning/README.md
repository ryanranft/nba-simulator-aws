# 5.2: MLflow Model Versioning System

**Sub-Phase:** 5.2 (Model Versioning & Registry)
**Parent Phase:** [Phase 5: Machine Learning Pipeline](../PHASE_5_INDEX.md)
**Status:** ✅ COMPLETE
**Priority:** ⭐ CRITICAL
**Implementation ID:** ml_systems_1
**Completed:** October 15, 2025

---

## Overview

Enterprise-grade ML model lifecycle management using MLflow. Provides versioning, stage-based promotion, experiment tracking, and artifact storage for all NBA simulator models.

**Key Capabilities:**
- Model versioning with automatic incrementing
- Stage-based workflow: None → Staging → Production → Archived
- Experiment tracking and comparison
- S3 artifact storage integration
- Model metadata and tagging

---

## Quick Start

```python
import mlflow

# Configure MLflow
mlflow.set_tracking_uri('s3://nba-sim-raw-data-lake/mlflow')
mlflow.set_experiment('nba-game-predictions')

# Train and log model
with mlflow.start_run():
    model = train_model(X_train, y_train)

    # Log parameters, metrics, model
    mlflow.log_params({'algorithm': 'XGBoost', 'n_estimators': 100})
    mlflow.log_metrics({'accuracy': 0.75, 'f1_score': 0.75})
    mlflow.sklearn.log_model(model, "model")

# Register model for production
mlflow.register_model(
    model_uri=f"runs:/{run_id}/model",
    name="nba-game-predictor"
)

# Promote to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="nba-game-predictor",
    version=1,
    stage="Production"
)
```

---

## Architecture

**Storage:**
- **Tracking Server**: S3 (`s3://nba-sim-raw-data-lake/mlflow`)
- **Backend Store**: PostgreSQL (optional, for metadata)
- **Artifact Store**: S3 (model binaries, plots, data)

**Integration Points:**
- **[5.20_panel_data](../5.20_panel_data/README.md) + [5.1_feature_engineering](../5.1_feature_engineering/README.md)**: Track feature engineering pipeline versions
- **Phase 5 Models (5.0)**: Version all XGBoost/ML models
- **[5.19_drift_detection](../5.19_drift_detection/README.md)**: Connect drift detection to model retraining
- **ml_systems_3**: Dashboard visualization of model performance

---

## Features Implemented

### 1. Model Registration ✅
```python
# Automatic versioning
mlflow.register_model("runs:/abc123/model", "my-model")  # v1
mlflow.register_model("runs:/def456/model", "my-model")  # v2
```

### 2. Stage Promotion ✅
```python
# Promote best model to production
client.transition_model_version_stage("my-model", version=2, stage="Production")
# Old production version automatically archived
```

### 3. Experiment Tracking ✅
```python
# Compare multiple runs
experiments = mlflow.search_runs(experiment_ids=['1'])
best_run = experiments.sort_values('metrics.f1_score', ascending=False).iloc[0]
```

### 4. Model Retrieval ✅
```python
# Load latest production model
model = mlflow.pyfunc.load_model("models:/nba-game-predictor/Production")
predictions = model.predict(X_test)
```

---

## Implementation Details

**Development Time:** ~3 hours (vs 1 day estimate)
**Test Coverage:** 15+ unit tests, 4+ integration tests
**Lines of Code:** 975 total (578 implementation, 397 tests)

**Prerequisites:**
```bash
pip install mlflow>=2.8.0 boto3 scikit-learn
aws configure  # For S3 access
```

---

## Usage Examples

### Training with MLflow

```python
import mlflow
import xgboost as xgb
from implement_rec_11 import AdvancedFeatureEngineeringPipeline

# Setup MLflow
mlflow.set_tracking_uri('s3://nba-sim-raw-data-lake/mlflow')
mlflow.set_experiment('nba-game-predictions')

# Engineer features
pipeline = AdvancedFeatureEngineeringPipeline()
pipeline.setup()
features = pipeline.execute(demo_data=df)

# Train model with tracking
with mlflow.start_run():
    # Log feature engineering config
    mlflow.log_params(pipeline.config)

    # Train model
    model = xgb.XGBClassifier(n_estimators=100, max_depth=6)
    model.fit(X_train, y_train)

    # Log model metrics
    y_pred = model.predict(X_test)
    accuracy = (y_pred == y_test).mean()
    mlflow.log_metric('accuracy', accuracy)

    # Log model
    mlflow.xgboost.log_model(model, "model")

    # Register model
    run_id = mlflow.active_run().info.run_id
    mlflow.register_model(
        f"runs:/{run_id}/model",
        "nba-game-predictor"
    )
```

### Model Comparison

```python
# Compare all runs in experiment
import pandas as pd

runs = mlflow.search_runs(experiment_names=['nba-game-predictions'])

# Sort by accuracy
best_runs = runs.sort_values('metrics.accuracy', ascending=False).head(5)

print("Top 5 models:")
print(best_runs[['run_id', 'metrics.accuracy', 'params.n_estimators', 'start_time']])
```

### Model Deployment

```python
# Load production model
import mlflow

model_uri = "models:/nba-game-predictor/Production"
model = mlflow.pyfunc.load_model(model_uri)

# Make predictions
predictions = model.predict(new_game_data)
```

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tracking_uri` | `file:./mlruns` | MLflow tracking server URI |
| `experiment_name` | `nba-simulator-ml` | Experiment name |
| `artifact_location` | `s3://nba-sim-raw-data-lake/mlflow` | S3 bucket for artifacts |
| `backend_store_uri` | (optional) | PostgreSQL for metadata |
| `default_tags` | `{'project': 'nba-simulator-aws'}` | Default run tags |

---

## Testing

```bash
# Run tests
cd /Users/ryanranft/nba-simulator-aws/docs/phases/phase_5/5.2_model_versioning
python -m pytest test_ml_systems_1.py -v

# Or check integration
python -c "import mlflow; print(mlflow.__version__)"
```

---

## Implementation Files

| File | Purpose |
|------|---------|
| **README.md** | This file - main documentation |
| **STATUS.md** | Implementation status and metrics |
| **RECOMMENDATIONS_FROM_BOOKS.md** | Book sources |
| Various `implement_*.py` | Implementation files from book recommendations |
| Various `test_*.py` | Test suites |

---

## Related Documentation

- **[STATUS.md](STATUS.md)** - Implementation status and metrics
- **[RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md)** - Book sources
- **[Phase 0: MLFLOW_INTEGRATION_SUMMARY.md](../../phase_0/MLFLOW_INTEGRATION_SUMMARY.md)** - Complete integration summary
- **[MLflow Docs](https://mlflow.org/docs/latest/index.html)** - Official MLflow documentation

---

## Navigation

**Return to:** [Phase 5: Machine Learning Pipeline](../PHASE_5_INDEX.md)
**Prerequisites:** [5.0: ML Model Pipeline](../5.0_machine_learning_models.md)
**Integrates with:** [5.1: Feature Engineering](../5.1_feature_engineering/README.md), [5.19: Drift Detection](../5.19_drift_detection/README.md)

---

**Last Updated:** October 18, 2025
**Maintained By:** NBA Simulator AWS Team
**Integration:** Complete and production-ready
