# 5.0004: Automated Retraining

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/automated_retraining.py` (640 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #17

---

## Overview

Automated model retraining pipeline with drift detection:
- Data drift monitoring (distributional shifts)
- Concept drift detection (target distribution changes)
- Performance degradation detection
- Automated retraining triggers
- Version control and rollback

Designed for NBA temporal panel data with seasonality awareness.

---

## When to Use

### Use This Framework When:
- ✅ **Production deployment** - Models need continuous updates
- ✅ **Seasonal data** - NBA seasons have different characteristics
- ✅ **Player roster changes** - New players, trades affect predictions
- ✅ **Rule changes** - NBA rule changes impact game statistics
- ✅ **Performance degradation** - Model accuracy declining over time

### Do NOT Use When:
- ❌ **Development phase** - Manual retraining more flexible
- ❌ **Insufficient monitoring data** - Need 30+ days for drift detection
- ❌ **Static problem** - Historical data doesn't change

---

## How to Use

```python
from scripts.ml.automated_retraining import AutomatedRetrainingPipeline

# Initialize pipeline
pipeline = AutomatedRetrainingPipeline(
    model=current_model,
    X_reference=X_train_baseline,  # Reference distribution
    y_reference=y_train_baseline,
    drift_threshold=0.05,  # 5% drift triggers retraining
    performance_threshold=0.02  # 2% performance drop triggers retraining
)

# Monitor new data
new_data_batch = load_latest_games()
drift_detected = pipeline.detect_drift(
    X_new=new_data_batch[feature_cols],
    y_new=new_data_batch['target']
)

if drift_detected.should_retrain:
    print(f"Drift detected: {drift_detected.drift_type}")
    print(f"Magnitude: {drift_detected.drift_magnitude:.4f}")

    # Automatic retraining
    retrained_model = pipeline.retrain(
        X_new=new_data_batch[feature_cols],
        y_new=new_data_batch['target'],
        retrain_strategy='incremental'  # or 'full'
    )

    # Validate before deployment
    if retrained_model.performance > current_model.performance:
        print("Deploying retrained model")
        deploy_model(retrained_model)
    else:
        print("Rollback: New model underperforms")
```

---

## Workflow References

- **Workflow #13** - Model Testing
- **Workflow #41** - Testing Framework
- **5.0003** - Feature Store (versioned features)
- **5.0010** - Model Comparison (validate retraining)

---

## Common Patterns

### Pattern 1: Daily Monitoring

```python
# Run daily after games complete
daily_games = load_games_for_date(today)

drift_report = pipeline.check_drift_and_retrain(
    X_new=daily_games[features],
    y_new=daily_games['target'],
    auto_retrain=True
)

# Log to monitoring system
logger.info(f"Drift magnitude: {drift_report.drift_magnitude:.4f}")
logger.info(f"Should retrain: {drift_report.should_retrain}")
```

### Pattern 2: Season Boundary Retraining

```python
# Automatic retraining at season start
if is_new_season(today):
    print("New season detected - triggering full retraining")
    pipeline.retrain(
        X_new=load_season_data(current_season),
        y_new=load_season_targets(current_season),
        retrain_strategy='full',  # Full retrain for new season
        force=True  # Force retraining regardless of drift
    )
```

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
- **5.0003** - Feature Store
- **5.0010** - Model Comparison
