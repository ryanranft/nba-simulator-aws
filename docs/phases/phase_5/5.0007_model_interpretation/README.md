# Phase 5.0002: Model Interpretation

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/model_interpretation.py` (619 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #15

---

## Overview

Comprehensive model interpretation framework implementing multiple explanation techniques:
- **SHAP values** - Additive feature attribution
- **Feature importance** - Permutation and gain-based importance
- **Decision paths** - Tree-based model path analysis
- **Feature interactions** - Pairwise interaction detection
- **Contribution analysis** - Instance-level feature contributions

Designed for interpretable ML on NBA temporal panel data.

---

## When to Use

### Use This Framework When:
- ✅ **Model deployed to production** - Need to explain predictions to stakeholders
- ✅ **Debugging model behavior** - Understanding why predictions fail
- ✅ **Feature engineering validation** - Verify features contribute as expected
- ✅ **Regulatory requirements** - Need interpretable models for compliance
- ✅ **Building trust** - Explaining model decisions to users

### Do NOT Use When:
- ❌ **Model still in early development** - Focus on performance first
- ❌ **Black-box model required** - Some use cases prioritize accuracy over interpretability
- ❌ **Insufficient samples** - Need 100+ samples for stable interpretations

---

## How to Use

### Quick Start - Feature Importance

```python
from scripts.ml.model_interpretation import ModelInterpreter
import pandas as pd

# Load trained model and data
model = load_model('models/nba_win_predictor_rf.pkl')
X_test = pd.read_csv('data/test_features.csv')
y_test = pd.read_csv('data/test_targets.csv')

# Initialize interpreter
interpreter = ModelInterpreter(
    model=model,
    X=X_test,
    y=y_test,
    feature_names=X_test.columns.tolist()
)

# Get permutation importance
importance = interpreter.permutation_importance(
    X_test=X_test,
    y_test=y_test,
    n_repeats=10
)

print("Top 10 most important features:")
for feature, score in list(importance.feature_importance.items())[:10]:
    print(f"  {feature}: {score:.4f}")
```

### SHAP Values for Instance Explanation

```python
# Explain specific prediction
instance_idx = 42
instance = X_test.iloc[instance_idx]

shap_explanation = interpreter.explain_with_shap(
    instance=instance,
    instance_id=instance_idx,
    background_samples=100  # Use subset for efficiency
)

print(f"Prediction: {shap_explanation.prediction:.4f}")
print(f"Base value: {shap_explanation.base_value:.4f}")
print("\nTop feature contributions:")
for feature, contrib in list(shap_explanation.shap_values.items())[:5]:
    print(f"  {feature}: {contrib:+.4f}")
```

### Decision Path Analysis (Tree Models)

```python
# Analyze decision path for tree-based models
if hasattr(model, 'estimators_'):  # RandomForest/GradientBoosting
    path = interpreter.analyze_decision_path(
        instance=instance,
        tree_index=0  # First tree
    )

    print("Decision path:")
    for i, node in enumerate(path.path_nodes):
        print(f"  Step {i+1}: {node['feature']} {node['comparison']} {node['threshold']:.4f}")
        print(f"    → Branch: {node['direction']}")
```

### Feature Interactions

```python
# Detect pairwise feature interactions
interactions = interpreter.detect_interactions(
    X_test=X_test,
    y_test=y_test,
    top_k=10  # Top 10 interactions
)

print("Top feature interactions:")
for interaction in interactions:
    print(f"  {interaction.feature_1} × {interaction.feature_2}: "
          f"strength={interaction.interaction_strength:.4f}")
```

---

## Integration with NBA Panel Data

```python
# Example: Interpret win prediction model
panel_df = pd.read_parquet('data/panel_data/game_level_panel.parquet')

# Select recent games for interpretation
recent_mask = panel_df['game_date'] >= '2024-10-01'
X_recent = panel_df.loc[recent_mask, feature_cols]
y_recent = panel_df.loc[recent_mask, 'win']

# Initialize interpreter
interpreter = ModelInterpreter(
    model=win_prediction_model,
    X=X_recent,
    y=y_recent,
    feature_names=feature_cols
)

# Get feature importance
importance = interpreter.permutation_importance(X_recent, y_recent)

# Export for documentation
interpreter.export_results(
    output_path='models/interpretation/win_prediction_importance.json',
    feature_importance=importance
)
```

---

## Workflow References

- **Workflow #13** - Model Testing
- **Workflow #41** - Testing Framework
- **Phase 5.0011** - Error Analysis (combine with interpretation for debugging)
- **Phase 5.0012** - Model Explainability (advanced explanation techniques)

---

## Integration Points

1. **Model Interpretation (5.2)** → **Error Analysis (5.11)**
   - Use interpretation to understand systematic errors
   - Identify features causing misclassifications

2. **Feature Selection (5.5)** → **Model Interpretation (5.2)**
   - Validate selected features have high importance
   - Remove low-importance features

3. **Model Interpretation (5.2)** → **Model Explainability (5.12)**
   - Basic interpretation first (this framework)
   - Advanced explainability second (LIME, counterfactuals)

---

## Common Patterns

### Pattern 1: Debug Poor Predictions

```python
# Find misclassified instances
misclassified = y_test != model.predict(X_test)
misclassified_idx = np.where(misclassified)[0]

# Explain first 5 misclassifications
for idx in misclassified_idx[:5]:
    explanation = interpreter.explain_with_shap(
        instance=X_test.iloc[idx],
        instance_id=idx
    )
    print(f"\nMisclassified instance {idx}:")
    print(f"  Predicted: {explanation.prediction:.2f}")
    print(f"  Actual: {y_test.iloc[idx]}")
    print(f"  Top contributors: {list(explanation.shap_values.items())[:3]}")
```

### Pattern 2: Validate Feature Engineering

```python
# Check if new features are important
new_features = ['cumulative_plus_minus', 'recent_win_rate', 'fatigue_index']

importance = interpreter.permutation_importance(X_test, y_test)

print("New feature importance:")
for feature in new_features:
    score = importance.feature_importance.get(feature, 0.0)
    print(f"  {feature}: {score:.4f}")
    if score < 0.01:
        print(f"    ⚠️ Low importance - consider removing")
```

---

## Troubleshooting

### Issue: SHAP values take too long to compute

**Solutions:**
- Reduce background_samples (from 100 to 50)
- Use TreeExplainer for tree models (faster than KernelExplainer)
- Compute SHAP for subset of instances, not all

### Issue: Feature importance values are unstable

**Solutions:**
- Increase n_repeats in permutation_importance (from 10 to 30)
- Use larger test set (need at least 500 samples)
- Average importance across multiple CV folds

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
- **Phase 5.0011** - Error Analysis
- **Phase 5.0012** - Model Explainability
- **Phase 5.0013** - Performance Profiling
