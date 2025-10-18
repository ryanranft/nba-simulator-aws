# Data Drift Detection System

**Recommendation ID:** ml_systems_2
**Status:** ✅ **COMPLETE**
**Completed:** October 16, 2025
**Integration Type:** Infrastructure / MLOps

---

## Overview

Statistical monitoring system for detecting distribution shifts in production ML data. Uses 5 complementary methods to identify when model retraining is needed.

**Key Capabilities:**
- Population Stability Index (PSI)
- Kolmogorov-Smirnov Test
- Chi-Squared Test
- Wasserstein Distance
- Jensen-Shannon Divergence

---

## Quick Start

```python
from implement_ml_systems_2 import DataDriftDetection

# Initialize
drift_detector = DataDriftDetection({
    'alert_threshold_psi': 0.2,
    'mlflow_tracking': True
})

# Setup with training data as reference
drift_detector.setup()

# Detect drift in production data
production_data = load_production_features()
results = drift_detector.detect_drift(production_data)

# Check for drift
if results['summary']['overall_drift_detected']:
    print(f"⚠️ Drift in {results['summary']['features_with_drift']} features")
    # Trigger model retraining
else:
    print("✅ No significant drift")
```

---

## Statistical Methods

| Method | Type | Threshold | Use Case |
|--------|------|-----------|----------|
| **PSI** | Numerical | ≥ 0.2 | Overall distribution shift |
| **KS Test** | Numerical | ≥ 0.1 | Distribution comparison |
| **Chi-Squared** | Categorical | p < 0.05 | Category frequency shifts |
| **Wasserstein** | Numerical | Distance metric | Continuous distributions |
| **JS Divergence** | Both | 0 to 1 | General similarity |

---

## Integration with MLflow (ml_systems_1)

```python
# When drift detected → retrain → register new version
if drift_results['summary']['drift_percentage'] > 30:
    # Retrain model
    new_model = train_model(X_train, y_train)

    # Register new version with MLflow
    mlflow.register_model(
        f"runs:/{run_id}/model",
        "nba-game-predictor",
        tags={'reason': 'drift_detected', 'drift_pct': '35%'}
    )
```

---

## Implementation Details

**Development Time:** ~4 hours
**Test Coverage:** 25+ tests (100% pass rate)
**Lines of Code:** 1,189 total (688 implementation, 501 tests)
**Statistical Methods:** 5

---

## Related Documentation

- [STATUS.md](STATUS.md) - Implementation status
- [RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md) - Book sources
- [DATA_DRIFT_DETECTION_SUMMARY.md](../DATA_DRIFT_DETECTION_SUMMARY.md) - Complete summary

---

**Last Updated:** October 18, 2025
**Maintained By:** NBA Simulator AWS Team
