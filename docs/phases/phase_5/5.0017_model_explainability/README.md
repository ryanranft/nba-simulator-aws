# 5.0012: Model Explainability

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/model_explainability.py` (541 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #24

---

## Overview

Advanced explainability framework providing:
- **Global explanations** - Permutation importance across all predictions
- **Local explanations** - LIME-style instance-level explanations
- **Feature interactions** - Detect non-additive feature effects
- **Partial dependence** - Feature effect visualization
- **Individual Conditional Expectation (ICE)** - Per-instance feature effects

Designed for interpretable ML on NBA temporal panel data.

---

## When to Use

### Use This Framework When:
- ✅ **Stakeholder buy-in needed** - Explain model decisions to non-technical users
- ✅ **Regulatory compliance** - Interpretability requirements (GDPR, etc.)
- ✅ **Model debugging** - Understand surprising predictions
- ✅ **Feature validation** - Verify features work as expected
- ✅ **Trust building** - Demonstrate model reasonableness

### Do NOT Use When:
- ❌ **Model still in development** - Focus on performance first (use 5.2 Model Interpretation instead)
- ❌ **Black-box acceptable** - No interpretability requirement
- ❌ **Computational constraints** - Explanations computationally expensive

---

## How to Use

### Quick Start - Permutation Importance

```python
from scripts.ml.model_explainability import ModelExplainer

# Initialize explainer
explainer = ModelExplainer(
    model=trained_model,
    X=X_train,  # Reference dataset
    y=y_train
)

# Calculate global feature importance
global_explanation = explainer.permutation_importance(
    X_test=X_test,
    y_test=y_test,
    n_repeats=10
)

print("Top 10 most important features:")
for i, (feature, importance) in enumerate(list(global_explanation.feature_importance.items())[:10], 1):
    print(f"  {i}. {feature}: {importance:.4f}")

# Export for documentation
explainer.export_explanations(
    output_path='models/explainability/global_importance.json',
    global_explanation=global_explanation
)
```

### Local Instance Explanation

```python
# Explain specific prediction
instance_idx = 42
instance = X_test.iloc[instance_idx]

local_explanation = explainer.explain_instance(
    instance=instance,
    instance_id=instance_idx,
    n_samples=1000,  # Perturbation samples
    actual=y_test.iloc[instance_idx]
)

print(f"Instance {instance_idx}:")
print(f"  Prediction: {local_explanation.prediction:.4f}")
print(f"  Actual: {local_explanation.actual}")
print(f"  Base value: {local_explanation.base_value:.4f}")

print("\nTop 5 feature contributions:")
for i, (feature, contribution) in enumerate(list(local_explanation.feature_contributions.items())[:5], 1):
    direction = "↑" if contribution > 0 else "↓"
    print(f"  {i}. {feature}: {contribution:+.4f} {direction}")
```

### Feature Interactions

```python
# Detect pairwise interactions
interactions = explainer.detect_interactions(
    X_test=X_test,
    y_test=y_test,
    top_k=10
)

print("Top 10 feature interactions:")
for i, interaction in enumerate(interactions, 1):
    print(f"  {i}. {interaction.feature_1} × {interaction.feature_2}")
    print(f"      Interaction strength: {interaction.interaction_strength:.4f}")
```

### Partial Dependence

```python
# Show how prediction changes with feature value
pd_result = explainer.partial_dependence(
    feature='cumulative_points',
    num_points=20
)

print(f"Partial dependence for {pd_result['feature']}:")
for value, pd_val in zip(pd_result['grid_values'][:10], pd_result['pd_values'][:10]):
    print(f"  {pd_result['feature']} = {value:.2f} → prediction = {pd_val:.4f}")
```

---

## Integration with NBA Panel Data

```python
# Example: Explain win prediction for specific game
panel_df = pd.read_parquet('data/panel_data/game_level_panel.parquet')

# Select game to explain
game_idx = 1234
game_features = panel_df.loc[game_idx, feature_cols]

# Initialize explainer
explainer = ModelExplainer(
    model=win_prediction_model,
    X=X_train,
    y=y_train
)

# Get explanation
explanation = explainer.explain_instance(
    instance=game_features,
    instance_id=game_idx,
    n_samples=1000,
    actual=panel_df.loc[game_idx, 'win']
)

print(f"Game {game_idx} explanation:")
print(f"  Team: {panel_df.loc[game_idx, 'team']}")
print(f"  Opponent: {panel_df.loc[game_idx, 'opponent']}")
print(f"  Win probability: {explanation.prediction:.2%}")
print(f"  Actual outcome: {'Win' if explanation.actual == 1 else 'Loss'}")

print("\nKey factors driving prediction:")
for i, (feature, contrib) in enumerate(list(explanation.feature_contributions.items())[:5], 1):
    direction = "increases" if contrib > 0 else "decreases"
    print(f"  {i}. {feature} {direction} win probability by {abs(contrib):.3f}")
```

---

## Workflow References

- **Workflow #13** - Model Testing
- **Workflow #41** - Testing Framework
- **5.0002** - Model Interpretation (basic interpretation, use first)
- **5.0011** - Error Analysis (combine with explainability for debugging)

---

## Integration Points

1. **Model Interpretation (5.2)** → **Model Explainability (5.12)**
   - Use 5.2 for quick feature importance
   - Use 5.12 for detailed stakeholder explanations

2. **Error Analysis (5.11)** + **Model Explainability (5.12)**
   - Identify errors with error analysis
   - Explain why errors occurred with explainability

3. **Model Explainability (5.12)** → **Feature Engineering**
   - Discover unexpected feature effects
   - Create interaction features based on detected interactions

---

## Common Patterns

### Pattern 1: Explain Model to Stakeholders

```python
# Generate report for non-technical stakeholders
global_exp = explainer.permutation_importance(X_test, y_test)

print("=== Model Explanation Report ===\n")
print("The model makes predictions using these key factors:\n")

for i, (feature, importance) in enumerate(list(global_exp.feature_importance.items())[:5], 1):
    # Translate technical feature names to business terms
    business_name = feature_name_to_business_term(feature)
    print(f"{i}. {business_name}")
    print(f"   Impact on predictions: {importance:.2%}\n")
```

### Pattern 2: Debug Unexpected Prediction

```python
# Model predicted loss but team won - why?
unexpected_idx = find_unexpected_prediction(y_test, y_pred)

explanation = explainer.explain_instance(
    instance=X_test.iloc[unexpected_idx],
    instance_id=unexpected_idx,
    actual=y_test.iloc[unexpected_idx]
)

print("Why did model predict incorrectly?")
print(f"  Predicted: {explanation.prediction:.2%} win probability")
print(f"  Actual: Win\n")

print("Factors that led to wrong prediction:")
for feature, contrib in list(explanation.feature_contributions.items())[:5]:
    if contrib < 0:  # Features that decreased win probability
        print(f"  - {feature} decreased probability by {abs(contrib):.3f}")
        print(f"    Value: {X_test.loc[unexpected_idx, feature]:.2f}")
```

### Pattern 3: Validate Feature Engineering

```python
# Check if new features behave as expected
new_features = ['fatigue_index', 'momentum_score', 'clutch_performance']

global_exp = explainer.permutation_importance(X_test, y_test)

print("New feature validation:")
for feature in new_features:
    importance = global_exp.feature_importance.get(feature, 0.0)
    print(f"  {feature}: {importance:.4f}")

    if importance > 0.05:
        print(f"    ✅ High importance - feature is valuable")

        # Check partial dependence
        pd_result = explainer.partial_dependence(feature)
        print(f"    Relationship: {'Positive' if is_monotonic_increasing(pd_result['pd_values']) else 'Non-monotonic'}")
    else:
        print(f"    ⚠️ Low importance - consider removing")
```

---

## Troubleshooting

### Issue: Local explanations unstable (different each time)

**Solutions:**
- Increase n_samples (from 1000 to 5000)
- Set random seed for reproducibility
- Use more stable methods (tree SHAP for tree models)

### Issue: Explanations contradict domain knowledge

**Causes:**
- Data quality issues
- Feature leakage
- Model overfitting

**Solutions:**
- Investigate data pipeline
- Check for leakage (future information in features)
- Regularize model more

### Issue: Partial dependence plots look strange

**Causes:**
- Feature correlations
- Extrapolation to unrealistic values
- Non-linear interactions

**Solutions:**
- Check feature correlations
- Restrict grid to realistic value ranges
- Use ICE plots to see individual variation

---

## Performance Considerations

- **Permutation importance**: O(f × n × m) where f = features, n = samples, m = repeats (~slow)
- **Local explanation**: O(k × n) where k = perturbations, n = samples (~medium, 1-5 seconds per instance)
- **Interactions**: O(f² × n) (~very slow for many features)
- **Partial dependence**: O(g × n) where g = grid points (~medium)

**Memory usage**: ~100-500 MB for typical NBA dataset

**Tip**: Use background data sampling to speed up LIME-style explanations

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference and advanced examples
- **5.0002** - Model Interpretation (lighter-weight alternative)
- **5.0011** - Error Analysis (find what to explain)
- **5.0013** - Performance Profiling (optimize explanation speed)
