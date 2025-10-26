# Phase 5.8: Model Calibration

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/model_calibration.py` (607 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #21

---

## Overview

Comprehensive calibration framework implementing 3 methods:
1. **Platt Scaling** - Logistic calibration
2. **Isotonic Regression** - Non-parametric calibration
3. **Temperature Scaling** - Neural network calibration

Designed for NBA temporal panel data with time-aware calibration.

---

## When to Use

### Use This Framework When:
- ✅ **Probability estimates needed** - Not just classification
- ✅ **Betting applications** - Accurate probabilities critical
- ✅ **Risk assessment** - Confidence scores must be accurate
- ✅ **Decision thresholds matter** - Optimal threshold depends on calibration
- ✅ **Tree models** - Random Forests tend to be miscalibrated

### Do NOT Use When:
- ❌ **Only predictions needed** - Not probabilities
- ❌ **Model already well-calibrated** - Logistic regression often calibrated
- ❌ **Insufficient validation data** - Need at least 1000 samples

---

## How to Use

```python
from scripts.ml.model_calibration import ModelCalibrator

# Train initial model
model.fit(X_train, y_train)

# Initialize calibrator
calibrator = ModelCalibrator(
    model=model,
    X_val=X_val,
    y_val=y_val,
    method='isotonic'  # or 'platt', 'temperature'
)

# Calibrate model
calibrated_model = calibrator.calibrate()

# Compare before/after
y_proba_uncalibrated = model.predict_proba(X_test)[:, 1]
y_proba_calibrated = calibrated_model.predict_proba(X_test)[:, 1]

# Evaluate calibration
calibration_report = calibrator.evaluate_calibration(
    y_true=y_test,
    y_proba=y_proba_calibrated
)
print(f"Brier score: {calibration_report.brier_score:.4f}")
print(f"ECE: {calibration_report.expected_calibration_error:.4f}")
```

---

## Workflow References

- **Phase 5.1** - Hyperparameter Optimization (calibrate after optimization)
- **Phase 5.10** - Model Comparison

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
