# Phase 5.0009: Cross-Validation Strategies

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/cross_validation_strategies.py` (557 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #22

---

## Overview

Comprehensive CV framework implementing 5 strategies:
1. **Time Series CV** - Respects temporal order (CRITICAL for NBA data)
2. **Blocked Time Series CV** - Fixed-size temporal blocks
3. **Group K-Fold** - Group-aware splitting (e.g., by team)
4. **Stratified K-Fold** - Maintains class distribution
5. **Leave-One-Group-Out** - Holdout specific groups

Designed specifically for NBA temporal panel data.

---

## When to Use

### CV Strategy Selection

| Strategy | Use When | Example NBA Use Case |
|----------|----------|---------------------|
| Time Series CV | **Always for temporal data** | Game predictions (respect chronology) |
| Blocked Time Series | Fixed evaluation periods | Season-by-season validation |
| Group K-Fold | Group structure matters | Player-specific models |
| Stratified K-Fold | Imbalanced classes | Rare event prediction (injuries) |
| LOGO | Generalization testing | Leave-one-team-out validation |

**⚠️ CRITICAL**: Always use Time Series CV for NBA panel data. Standard K-Fold causes data leakage.

---

## How to Use

```python
from scripts.ml.cross_validation_strategies import CrossValidator

# Initialize with time series CV
cv = CrossValidator(
    cv_strategy='time_series',
    n_splits=5,
    time_column='game_datetime'  # REQUIRED for temporal CV
)

# Perform cross-validation
cv_results = cv.cross_validate(
    model=model,
    X=X_train,
    y=y_train,
    scoring=['roc_auc', 'accuracy', 'f1']
)

print(f"Mean AUC: {cv_results['test_roc_auc'].mean():.4f} ± {cv_results['test_roc_auc'].std():.4f}")
print(f"Mean Accuracy: {cv_results['test_accuracy'].mean():.4f}")
```

---

## Workflow References

- **Phase 5.0001** - Hyperparameter Optimization (use appropriate CV)
- **Phase 5.0007** - Learning Curves (CV for robust estimates)

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
