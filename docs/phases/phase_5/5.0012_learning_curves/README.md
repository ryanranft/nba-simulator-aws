# 5.0007: Learning Curves

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/learning_curves.py` (580 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #20

---

## Overview

Learning curve analysis framework providing:
- Train/validation score curves
- Bias/variance diagnostic analysis
- Sample size estimation
- Model complexity analysis
- Convergence detection

Designed for NBA temporal panel data with time-aware sampling.

---

## When to Use

### Use This Framework When:
- ✅ **Diagnosing model issues** - Identify overfitting/underfitting
- ✅ **Data collection planning** - Estimate data needs for target performance
- ✅ **Model selection** - Compare model complexity requirements
- ✅ **Training optimization** - Determine optimal training set size
- ✅ **Budget planning** - Estimate labeling costs

### Do NOT Use When:
- ❌ **Model already performing well** - Analysis unnecessary
- ❌ **Time constraints** - Learning curves computationally expensive
- ❌ **Very small datasets** - Need at least 500 samples

---

## How to Use

```python
from scripts.ml.learning_curves import LearningCurveAnalyzer

# Initialize analyzer
analyzer = LearningCurveAnalyzer(
    model=model,
    X=X_train,
    y=y_train,
    cv_strategy='time_series',
    scoring='roc_auc'
)

# Generate learning curve
result = analyzer.generate_learning_curve(
    train_sizes=np.linspace(0.1, 1.0, 10)  # 10%, 20%, ..., 100%
)

# Diagnose model issues
diagnosis = analyzer.diagnose_model_fit(result)
print(f"Model status: {diagnosis.status}")  # 'overfitting', 'underfitting', 'good_fit'
print(f"Recommendation: {diagnosis.recommendation}")

# Estimate sample size needed
target_score = 0.85
estimated_samples = analyzer.estimate_sample_size(
    result=result,
    target_score=target_score
)
print(f"Estimated samples needed for {target_score:.2f} score: {estimated_samples}")
```

---

## Workflow References

- **5.0001** - Hyperparameter Optimization
- **5.0010** - Model Comparison

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
