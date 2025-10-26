# 5.0006: Ensemble Learning

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/ensemble_learning.py` (619 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #19

---

## Overview

Comprehensive ensemble framework implementing 5 strategies:
1. **Voting** - Simple or weighted majority voting
2. **Averaging** - Weighted prediction averaging
3. **Stacking** - Meta-model learns to combine predictions
4. **Bagging** - Bootstrap aggregating with diverse models
5. **Boosting** - Sequential error correction

Designed for NBA temporal panel data with time-aware ensemble construction.

---

## When to Use

### Use This Framework When:
- ✅ **Multiple strong models available** - Combine complementary models
- ✅ **Prediction stability needed** - Reduce variance through ensemble
- ✅ **Model performance plateau** - Single models not improving
- ✅ **Production deployment** - Ensembles often outperform single models
- ✅ **Diverse feature sets** - Different models trained on different features

### Do NOT Use When:
- ❌ **Single model sufficient** - Ensemble adds complexity
- ❌ **Latency constraints** - Ensembles slower than single models
- ❌ **Limited training data** - Need sufficient data for multiple models

---

## How to Use

```python
from scripts.ml.ensemble_learning import EnsembleLearner
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

# Train base models
rf_model = RandomForestClassifier(n_estimators=100)
gb_model = GradientBoostingClassifier(n_estimators=100)
lr_model = LogisticRegression()

rf_model.fit(X_train, y_train)
gb_model.fit(X_train, y_train)
lr_model.fit(X_train, y_train)

# Create ensemble
ensemble = EnsembleLearner(
    models={'rf': rf_model, 'gb': gb_model, 'lr': lr_model},
    ensemble_method='voting',
    voting_type='soft'  # Probability-based voting
)

# Predict
y_pred_ensemble = ensemble.predict(X_test)
y_proba_ensemble = ensemble.predict_proba(X_test)

# Evaluate
from sklearn.metrics import accuracy_score, roc_auc_score
acc = accuracy_score(y_test, y_pred_ensemble)
auc = roc_auc_score(y_test, y_proba_ensemble[:, 1])
print(f"Ensemble Accuracy: {acc:.4f}")
print(f"Ensemble AUC: {auc:.4f}")
```

---

## Ensemble Strategy Selection

| Strategy | Best For | Complexity | Training Time | Prediction Time |
|----------|----------|------------|---------------|----------------|
| Voting | Quick ensemble | Low | Fast | Fast |
| Averaging | Regression | Low | Fast | Fast |
| Stacking | Maximum performance | High | Slow | Medium |
| Bagging | Variance reduction | Medium | Medium | Medium |
| Boosting | Bias reduction | High | Slow | Fast |

---

## Workflow References

- **5.0001** - Hyperparameter Optimization (optimize base models first)
- **5.0010** - Model Comparison (compare ensemble vs base models)

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
- **5.0001** - Hyperparameter Optimization
- **5.0010** - Model Comparison
