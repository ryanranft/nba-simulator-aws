# Phase 5.0005: Automated Feature Selection

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/feature_selection.py` (668 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #18

---

## Overview

Comprehensive feature selection framework implementing 8 methods:
1. **Variance Threshold** - Remove low-variance features
2. **Correlation Filter** - Remove highly correlated features
3. **Mutual Information** - Information-theoretic feature ranking
4. **L1 Regularization (Lasso)** - Sparse feature selection
5. **Tree-based** - Feature importance from tree models
6. **Recursive Feature Elimination (RFE)** - Backward elimination
7. **Stability Selection** - Robust selection across bootstrap samples
8. **Consensus Selection** - Combine multiple methods

Designed for NBA temporal panel data with high-dimensional feature spaces.

---

## When to Use

### Use This Framework When:
- ✅ **High-dimensional data** - >100 features, need dimensionality reduction
- ✅ **Multicollinearity issues** - Highly correlated features
- ✅ **Overfitting problems** - Model memorizing training data
- ✅ **Model interpretability needed** - Simplify model with fewer features
- ✅ **Computational constraints** - Reduce training time

### Do NOT Use When:
- ❌ **Low-dimensional data** - <20 features, selection unnecessary
- ❌ **All features are important** - Domain knowledge suggests keeping all
- ❌ **Non-linear relationships** - Some methods assume linearity

---

## How to Use

### Quick Start - Variance Threshold

```python
from scripts.ml.feature_selection import FeatureSelector
import pandas as pd

# Load panel data
X_train = pd.read_csv('data/train_features.csv')
y_train = pd.read_csv('data/train_targets.csv')

# Initialize selector
selector = FeatureSelector(X=X_train, y=y_train)

# Remove low-variance features
result = selector.variance_threshold(threshold=0.01)

print(f"Features removed: {len(result.removed_features)}")
print(f"Features selected: {len(result.selected_features)}")

# Get selected features
X_train_selected = X_train[result.selected_features]
```

### Advanced - Consensus Selection

```python
# Combine multiple methods for robust selection
methods = ['mutual_information', 'lasso', 'tree_based', 'rfe']

consensus_result = selector.consensus_selection(
    methods=methods,
    n_features_to_select=50,  # Target 50 features
    voting_threshold=0.5  # Feature must appear in 50% of methods
)

print("Selected features:")
for feature in consensus_result.selected_features:
    score = consensus_result.feature_scores.get(feature, 0)
    print(f"  {feature}: {score:.4f}")

# Export for documentation
selector.export_results(
    output_path='models/feature_selection/consensus_results.json',
    result=consensus_result
)
```

---

## Method Selection Guide

| Method | Best For | Speed | Stability | Handles Non-linear |
|--------|----------|-------|-----------|-------------------|
| Variance Threshold | Quick filtering | Fast | High | N/A |
| Correlation Filter | Multicollinearity | Fast | High | No |
| Mutual Information | Non-linear relationships | Medium | Medium | Yes |
| Lasso | Sparse linear models | Fast | Medium | No |
| Tree-based | Non-linear, interactions | Medium | High | Yes |
| RFE | Optimal subset | Slow | Low | Depends on estimator |
| Stability Selection | Robust selection | Very Slow | Very High | Depends on estimator |
| Consensus | Maximum robustness | Slow | Very High | Yes |

---

## Workflow References

- **Workflow #13** - Model Testing
- **Workflow #41** - Testing Framework
- **Phase 5.0001** - Hyperparameter Optimization (optimize after selection)
- **Phase 5.0002** - Model Interpretation (validate selections)

---

## Common Patterns

### Pattern 1: Progressive Feature Selection

```python
# Step 1: Remove low-variance features
result1 = selector.variance_threshold(threshold=0.01)
X_step1 = X_train[result1.selected_features]

# Step 2: Remove highly correlated features
selector2 = FeatureSelector(X=X_step1, y=y_train)
result2 = selector2.correlation_filter(correlation_threshold=0.95)
X_step2 = X_step1[result2.selected_features]

# Step 3: Select top features with tree-based importance
selector3 = FeatureSelector(X=X_step2, y=y_train)
result3 = selector3.tree_based_selection(n_features=50)
X_final = X_step2[result3.selected_features]

print(f"Features: {X_train.shape[1]} → {X_step1.shape[1]} → {X_step2.shape[1]} → {X_final.shape[1]}")
```

### Pattern 2: NBA-Specific Selection

```python
# Identify important features for win prediction
selector = FeatureSelector(X=X_train, y=y_train_win)

# Use tree-based for non-linear relationships
result = selector.tree_based_selection(
    n_features=30,
    estimator_type='random_forest',
    n_estimators=100
)

print("Top 10 features for win prediction:")
for i, feature in enumerate(result.selected_features[:10], 1):
    score = result.feature_scores[feature]
    print(f"  {i}. {feature}: {score:.4f}")
```

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
- **Phase 5.0001** - Hyperparameter Optimization
- **Phase 5.0002** - Model Interpretation
