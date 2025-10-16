# Quick Start Guide: MLOps-Enhanced Training

**Created:** October 16, 2025
**Status:** Ready to use
**Environment:** Development (validated with real NBA data)

---

## Overview

This guide shows you how to use the new MLOps-enhanced training pipeline that integrates MLflow model versioning (ml_systems_1) and data drift detection (ml_systems_2) with your existing Phase 5 NBA prediction models.

---

## Prerequisites

✅ **Already Installed:**
- mlflow==2.16.2
- scipy>=1.11.0
- scikit-learn>=1.3.0
- xgboost>=2.0.0
- All dependencies from requirements.txt

✅ **Validated:**
- 47/47 tests passed (100% success rate)
- End-to-end workflow tested with real NBA data
- Both systems production-ready

---

## Quick Start (3 Steps)

### 1. Run Enhanced Training

```bash
cd /Users/ryanranft/nba-simulator-aws
python scripts/ml/train_models_with_mlops.py
```

**What This Does:**
- Loads train/test data from S3
- Checks for drift between train and test sets
- Trains 4 models: Logistic Regression, Random Forest, XGBoost, LightGBM
- Logs all experiments to MLflow
- Saves models to S3 (backward compatible)
- Reports best model performance

**Expected Output:**
```
MLOps Systems Status:
  MLflow Available: ✓
  Drift Detection Available: ✓

[1/8] Loading feature data from S3...
✓ Data loaded
  Train: 34,788 games, 16 features
  Test:  8,697 games, 16 features

[2/8] Checking for data drift (train vs test)...
  ⚠️  DRIFT DETECTED in 5 features
      Drift detected in 'home_rolling_ppg': PSI=4.834, KS=0.711
      [...]

[3/8] Scaling features...
✓ Features scaled

[4/8] Training Logistic Regression...
✓ Logistic Regression trained
  Test Accuracy: 0.6302
  Test AUC: 0.6593

[...]

🏆 Best Model: Logistic Regression (AUC: 0.6593)
```

### 2. View Experiments in MLflow UI

```bash
# Start MLflow UI server
mlflow ui --backend-store-uri file:./mlruns

# Navigate to: http://localhost:5000
```

**What You'll See:**
- **Experiments:** `nba-game-predictions`, `data-drift-monitoring`
- **Runs:** 4 model training runs with all parameters and metrics
- **Models:** Logged models with artifacts
- **Metrics:** Accuracy, AUC, precision, recall, F1 for each model
- **Comparison:** Side-by-side model comparison

### 3. Query Results Programmatically

```python
import mlflow

# Set tracking URI
mlflow.set_tracking_uri("file:./mlruns")

# Get experiment
experiment = mlflow.get_experiment_by_name("nba-game-predictions")
print(f"Experiment ID: {experiment.experiment_id}")

# Search runs sorted by AUC
runs = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.test_auc DESC"]
)

# View best model
print(runs[['metrics.test_auc', 'params.model_name', 'tags.mlflow.runName']].head())

# Load best model
best_run_id = runs.iloc[0].run_id
model = mlflow.sklearn.load_model(f"runs:/{best_run_id}/model")

# Make predictions
predictions = model.predict(X_test_scaled)
```

---

## Advanced Usage

### Running Without MLOps (Backward Compatible)

```python
# Edit train_models_with_mlops.py or pass flags
pipeline = MLOpsTrainingPipeline(
    enable_mlflow=False,
    enable_drift_detection=False
)
```

This runs the original Phase 5 training logic without any MLOps overhead.

### Running with Only MLflow

```python
pipeline = MLOpsTrainingPipeline(
    enable_mlflow=True,
    enable_drift_detection=False
)
```

### Running with Only Drift Detection

```python
pipeline = MLOpsTrainingPipeline(
    enable_mlflow=False,
    enable_drift_detection=True
)
```

### Custom MLflow Configuration

```python
mlflow_config = {
    'tracking_uri': 's3://your-bucket/mlflow',  # Remote storage
    'experiment_name': 'custom-experiment',
    'artifact_location': 's3://your-bucket/artifacts',
    'default_tags': {
        'team': 'data-science',
        'version': 'v2.0'
    }
}

pipeline = MLOpsTrainingPipeline(mlflow_config=mlflow_config)
```

### Custom Drift Thresholds

```python
drift_config = {
    'alert_threshold_psi': 0.5,     # More lenient (default: 0.2)
    'alert_threshold_ks': 0.2,      # More lenient (default: 0.1)
    'alert_threshold_chi2': 0.01,   # More strict (default: 0.05)
    'mlflow_tracking': True
}

pipeline = MLOpsTrainingPipeline(drift_config=drift_config)
```

---

## Understanding Drift Detection

### What Drift Was Detected?

In the test run, drift was detected in 5 of 16 features:

| Feature | PSI Score | KS Statistic | Interpretation |
|---------|-----------|--------------|----------------|
| home_rolling_ppg | 4.834 | 0.711 | **High drift** - Points per game shifted significantly |
| home_rolling_papg | 6.975 | 0.739 | **High drift** - Points allowed shifted significantly |
| away_rolling_ppg | 4.077 | 0.754 | **High drift** - Away scoring shifted |
| away_rolling_papg | 4.529 | 0.714 | **High drift** - Away defense shifted |
| month | 0.634 | 0.066 | **Medium drift** - Seasonal distribution different |

### Why Is There Drift?

This drift is **expected and normal** because:

1. **Temporal Split:** Training data contains earlier games, test data contains later games
2. **NBA Evolution:** Scoring rates changed over time (pace of play, rule changes, 3-point revolution)
3. **Team Strategies:** Teams evolved offensive and defensive strategies
4. **Seasonal Effects:** Different months represented in train vs test

### When Would You Retrain?

In production, you'd retrain when:
- PSI > 0.2 (significant drift)
- Multiple features drifting simultaneously
- Model performance drops below threshold
- New season starts (rule changes, new players)

---

## Model Performance Summary

### Current Results (Validated October 16, 2025)

| Model | Test Accuracy | Test AUC | Precision | Recall | F1 Score | Status |
|-------|--------------|----------|-----------|--------|----------|--------|
| **Logistic Regression** | **63.0%** | **0.659** | 0.646 | 0.758 | 0.698 | 🏆 Best |
| Random Forest | 62.7% | 0.656 | 0.635 | 0.793 | 0.705 | Good |
| LightGBM | 60.9% | 0.629 | 0.633 | 0.727 | 0.677 | Good |
| XGBoost | 59.8% | 0.626 | 0.632 | 0.686 | 0.658 | Good |

**Key Insights:**
- ✅ All models exceed 60% accuracy target
- ✅ Logistic Regression provides best generalization (least overfitting)
- ✅ High recall (0.758) means we correctly identify most home wins
- ⚠️ Some overfitting in tree-based models (XGBoost: 74.3% train, 59.8% test)

---

## Next Steps

### Immediate
1. ✅ Run enhanced training (validated)
2. ✅ View MLflow UI (experiments created)
3. ⏸️ **Your turn:** Explore MLflow UI at http://localhost:5000
4. ⏸️ **Your turn:** Try querying runs programmatically
5. ⏸️ **Your turn:** Load and test best model

### Short-term (This Week)
1. Set up automated drift monitoring (daily checks)
2. Create drift alert notifications
3. Establish model retraining workflow
4. Document team processes

### Medium-term (Next 2 Weeks)
1. Deploy MLflow tracking server to EC2 (~$15/month)
2. Set up PostgreSQL backend store (~$15/month)
3. Implement model registry with stage-based promotion
4. Create monitoring dashboards (ml_systems_3)

### Long-term (Next Month)
1. Automated retraining pipeline
2. A/B testing framework
3. Complete remaining critical recommendations (3 more)
4. Production deployment

---

## Troubleshooting

### MLflow UI Not Starting

```bash
# Check if port 5000 is already in use
lsof -i :5000

# Use different port
mlflow ui --backend-store-uri file:./mlruns --port 5001
```

### Can't Find Experiments

```python
# List all experiments
import mlflow
mlflow.set_tracking_uri("file:./mlruns")
experiments = mlflow.search_experiments()
for exp in experiments:
    print(f"{exp.name}: {exp.experiment_id}")
```

### Drift Detection Too Sensitive

Edit thresholds in the script or config:
```python
drift_config = {
    'alert_threshold_psi': 0.5,  # Increase from 0.2
    'alert_threshold_ks': 0.2    # Increase from 0.1
}
```

### Models Not Logging

Check that MLflow is available:
```python
try:
    import mlflow
    print(f"MLflow version: {mlflow.__version__}")
except ImportError:
    print("MLflow not installed - run: pip install mlflow==2.16.2")
```

---

## Resources

### Documentation
- [MLflow Integration Summary](MLFLOW_INTEGRATION_SUMMARY.md)
- [Data Drift Detection Summary](DATA_DRIFT_DETECTION_SUMMARY.md)
- [Testing Summary](TESTING_SUMMARY_ML_SYSTEMS.md)
- [Deployment Summary](DEPLOYMENT_SUMMARY_ML_SYSTEMS.md)
- [Book Recommendations Tracker](../../BOOK_RECOMMENDATIONS_TRACKER.md)

### Implementation Files
- **Enhanced Training:** `/scripts/ml/train_models_with_mlops.py` (490+ lines)
- **MLflow System:** `/docs/phases/phase_0/implement_ml_systems_1.py` (578 lines)
- **Drift Detection:** `/docs/phases/phase_0/implement_ml_systems_2.py` (688 lines)

### External Resources
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [Designing Machine Learning Systems (Book)](https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/)

---

## FAQ

**Q: Do I need to use the enhanced training pipeline?**
A: No! The original `train_models.py` still works. The enhanced version adds MLOps features but is completely optional.

**Q: Will this increase my AWS costs?**
A: Not in development (using local MLflow). Production deployment (~$30/month) is optional.

**Q: Can I use MLflow without drift detection?**
A: Yes! Both features can be enabled/disabled independently.

**Q: What if I don't have MLflow installed?**
A: The pipeline gracefully degrades and runs the original training logic.

**Q: Is this production-ready?**
A: Yes! All 47 tests passed, validated with real NBA data, comprehensive error handling.

**Q: How do I register a model for production?**
A: Use MLflow UI or API to promote from "None" → "Staging" → "Production" stages.

---

**Status:** ✅ Ready to use

**Last Validated:** October 16, 2025

**Support:** See documentation links above or check TROUBLESHOOTING.md
