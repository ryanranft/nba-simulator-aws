# 5.0010: Model Comparison & Benchmarking

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/model_comparison.py` (646 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #22

---

## Overview

Statistical model comparison framework implementing:
- **Paired t-test** - Parametric comparison with effect size
- **Wilcoxon signed-rank** - Non-parametric comparison
- **McNemar's test** - Classification model comparison
- **Model ranking** - Multi-metric ranking
- **Benchmark baselines** - Compare to dummy/baseline models

Designed for rigorous statistical comparison of NBA prediction models.

---

## When to Use

### Use This Framework When:
- ✅ **Comparing model candidates** - Select best model for deployment
- ✅ **A/B testing models** - Statistically validate improvements
- ✅ **Hyperparameter optimization** - Compare optimized vs baseline
- ✅ **Feature engineering validation** - Prove feature improvements
- ✅ **Model updates** - Validate retraining improves performance

### Do NOT Use When:
- ❌ **Single model** - Need at least 2 models to compare
- ❌ **Different datasets** - Models must be evaluated on same test set
- ❌ **Very small test sets** - Need at least 100 samples for reliable tests

---

## How to Use

### Quick Start - Paired t-test

```python
from scripts.ml.model_comparison import ModelComparator

# Train two models
model_a.fit(X_train, y_train)
model_b.fit(X_train, y_train)

# Get predictions on same test set
y_pred_a = model_a.predict(X_test)
y_pred_b = model_b.predict(X_test)

# Compute scores (e.g., per-fold or per-sample)
scores_a = [accuracy_score(y_test_fold, y_pred_a_fold) for y_test_fold, y_pred_a_fold in cv_folds_a]
scores_b = [accuracy_score(y_test_fold, y_pred_b_fold) for y_test_fold, y_pred_b_fold in cv_folds_b]

# Initialize comparator
comparator = ModelComparator(alpha=0.05)

# Compare models
result = comparator.paired_ttest(
    model_a_scores=scores_a,
    model_b_scores=scores_b,
    model_a_name='RandomForest',
    model_b_name='GradientBoosting'
)

print(f"Winner: {result.winner if result.winner else 'No significant difference'}")
print(f"P-value: {result.p_value:.6f}")
print(f"Effect size: {result.effect_size:.4f}")
print(f"Significant: {result.significant}")
```

### Advanced - Benchmark Suite

```python
# Compare multiple models against baselines
models = {
    'dummy_most_frequent': DummyClassifier(strategy='most_frequent'),
    'dummy_stratified': DummyClassifier(strategy='stratified'),
    'logistic_regression': LogisticRegression(),
    'random_forest': RandomForestClassifier(n_estimators=100),
    'gradient_boosting': GradientBoostingClassifier(n_estimators=100),
    'ensemble': ensemble_model
}

benchmark_result = comparator.benchmark_models(
    models=models,
    X_test=X_test,
    y_test=y_test,
    metrics=['accuracy', 'roc_auc', 'f1', 'precision', 'recall']
)

print("Model Rankings:")
for i, (model_name, rank_score) in enumerate(benchmark_result.rankings.items(), 1):
    print(f"  {i}. {model_name}: {rank_score:.4f}")

print("\nBaseline Improvements:")
for model_name, improvements in benchmark_result.baseline_improvement.items():
    if 'dummy' not in model_name:
        print(f"  {model_name}:")
        for metric, improvement in improvements.items():
            print(f"    {metric}: +{improvement:.4f}")
```

### McNemar's Test for Classification

```python
# Compare two classifiers statistically
y_pred_model_a = model_a.predict(X_test)
y_pred_model_b = model_b.predict(X_test)

mcnemar_result = comparator.mcnemar_test(
    y_true=y_test,
    y_pred_a=y_pred_model_a,
    y_pred_b=y_pred_model_b,
    model_a_name='RandomForest',
    model_b_name='GradientBoosting'
)

print(f"McNemar statistic: {mcnemar_result.statistic:.4f}")
print(f"P-value: {mcnemar_result.p_value:.6f}")
print(f"Winner: {mcnemar_result.winner}")
```

---

## Integration with NBA Panel Data

```python
# Example: Compare win prediction models with temporal CV
from scripts.ml.cross_validation_strategies import CrossValidator

panel_df = pd.read_parquet('data/panel_data/game_level_panel.parquet')

# Split by date
train_mask = panel_df['game_date'] < '2024-01-01'
test_mask = panel_df['game_date'] >= '2024-01-01'

X_train = panel_df.loc[train_mask, feature_cols]
y_train = panel_df.loc[train_mask, 'win']
X_test = panel_df.loc[test_mask, feature_cols]
y_test = panel_df.loc[test_mask, 'win']

# Train models
rf_model = RandomForestClassifier(n_estimators=200, max_depth=20)
gb_model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1)

rf_model.fit(X_train, y_train)
gb_model.fit(X_train, y_train)

# Time series CV for fair comparison
cv = CrossValidator(cv_strategy='time_series', n_splits=5, time_column='game_date')

# Get CV scores
rf_scores = cv.cross_val_score(rf_model, X_test, y_test, scoring='roc_auc')
gb_scores = cv.cross_val_score(gb_model, X_test, y_test, scoring='roc_auc')

# Statistical comparison
comparator = ModelComparator(alpha=0.05)
result = comparator.paired_ttest(
    model_a_scores=rf_scores,
    model_b_scores=gb_scores,
    model_a_name='RandomForest',
    model_b_name='GradientBoosting'
)

if result.significant:
    print(f"✅ {result.winner} is significantly better (p={result.p_value:.4f}, effect size={result.effect_size:.4f})")
else:
    print(f"❌ No significant difference (p={result.p_value:.4f})")
```

---

## Workflow References

- **Workflow #13** - Model Testing
- **Workflow #41** - Testing Framework
- **5.0001** - Hyperparameter Optimization (compare optimized models)
- **5.0006** - Ensemble Learning (compare ensemble vs base models)
- **5.0009** - Cross-Validation Strategies (use appropriate CV)

---

## Integration Points

1. **Hyperparameter Optimization (5.1)** → **Model Comparison (5.10)**
   - Compare optimized model to baseline
   - Validate optimization improved performance significantly

2. **Ensemble Learning (5.6)** → **Model Comparison (5.10)**
   - Compare ensemble to individual base models
   - Quantify ensemble improvement

3. **Automated Retraining (5.4)** → **Model Comparison (5.10)**
   - Compare retrained model to previous version
   - Deploy only if statistically better

---

## Statistical Test Selection Guide

| Test | Use When | Assumptions | Best For |
|------|----------|-------------|----------|
| Paired t-test | Normal distribution | Normality, paired data | CV fold scores |
| Wilcoxon | Non-normal distribution | Paired data only | Robust alternative to t-test |
| McNemar's | Binary classifications | Paired predictions | Classification models |

---

## Common Patterns

### Pattern 1: Validate Feature Engineering

```python
# Before feature engineering
baseline_model = RandomForestClassifier(n_estimators=100)
baseline_model.fit(X_train_baseline, y_train)
baseline_scores = cv.cross_val_score(baseline_model, X_test_baseline, y_test)

# After feature engineering
improved_model = RandomForestClassifier(n_estimators=100)  # Same hyperparameters
improved_model.fit(X_train_with_new_features, y_train)
improved_scores = cv.cross_val_score(improved_model, X_test_with_new_features, y_test)

# Statistical test
result = comparator.paired_ttest(
    model_a_scores=baseline_scores,
    model_b_scores=improved_scores,
    model_a_name='Baseline',
    model_b_name='With_New_Features'
)

print(f"Feature engineering improvement: {result.mean_difference:+.4f}")
print(f"Statistically significant: {result.significant}")
```

### Pattern 2: Model Selection for Production

```python
# Train candidate models
models = {
    'lr': LogisticRegression(),
    'rf': RandomForestClassifier(n_estimators=100),
    'gb': GradientBoostingClassifier(n_estimators=100),
    'xgb': XGBClassifier(n_estimators=100),
    'ensemble': VotingClassifier([('rf', rf), ('gb', gb), ('xgb', xgb)])
}

# Benchmark
benchmark_result = comparator.benchmark_models(
    models=models,
    X_test=X_test,
    y_test=y_test,
    metrics=['roc_auc', 'accuracy', 'f1', 'training_time', 'prediction_time']
)

# Select best model considering performance AND latency
print("Top 3 models by ranking:")
for i, (model_name, rank) in enumerate(list(benchmark_result.rankings.items())[:3], 1):
    perf = benchmark_result.model_performances[model_name]
    print(f"  {i}. {model_name}: rank={rank:.4f}, auc={perf.scores['roc_auc']:.4f}, "
          f"train_time={perf.training_time:.2f}s, pred_time={perf.prediction_time:.4f}s")
```

### Pattern 3: Non-Parametric Comparison

```python
# When CV scores are not normally distributed, use Wilcoxon
model_a_scores = [0.82, 0.85, 0.81, 0.88, 0.79]  # Non-normal distribution
model_b_scores = [0.84, 0.86, 0.83, 0.89, 0.82]

result = comparator.wilcoxon_test(
    model_a_scores=model_a_scores,
    model_b_scores=model_b_scores,
    model_a_name='Model_A',
    model_b_name='Model_B'
)

print(f"Wilcoxon test result: {result.winner if result.winner else 'No difference'}")
print(f"P-value: {result.p_value:.6f}")
```

---

## Troubleshooting

### Issue: No significant difference detected but models clearly different

**Causes:**
- Too few CV folds (low statistical power)
- High variance in CV scores
- Small effect size

**Solutions:**
- Increase n_splits in CV (from 5 to 10)
- Use larger test set
- Collect more data to reduce variance
- Check if practical difference matters (even if not statistically significant)

### Issue: All models have similar performance

**Causes:**
- Models are learning same patterns
- Feature set limits performance ceiling
- Problem may be too easy or too hard

**Solutions:**
- Try more diverse model types (linear, tree-based, neural networks)
- Improve feature engineering (5.0005)
- Collect additional data sources

### Issue: Test selection unclear

**Guidance:**
- **Paired t-test**: Default choice for CV scores (usually normal)
- **Wilcoxon**: If normality assumption violated (check with Shapiro-Wilk test)
- **McNemar's**: For binary classification comparison on same test set

---

## Performance Considerations

- **Paired t-test**: O(n) where n = number of CV folds (~instant)
- **Wilcoxon**: O(n log n) (~instant)
- **McNemar's**: O(n) where n = test set size (~instant)
- **Benchmark suite**: O(k × m × n) where k = models, m = metrics, n = test samples

**Memory usage**: Minimal (~10-50 MB for typical NBA dataset)

---

## Export and Tracking

```python
# Export comparison results for MLOps tracking
comparator.export_results(
    output_path='models/comparison/model_comparison_20251018.json',
    comparison_result=result
)

# Export benchmark results
comparator.export_benchmark(
    output_path='models/benchmarks/model_benchmark_20251018.json',
    benchmark_result=benchmark_result
)

# These can be loaded into MLflow, Weights & Biases, or custom dashboards
```

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference and advanced examples
- **5.0001** - Hyperparameter Optimization (optimize before comparing)
- **5.0006** - Ensemble Learning (compare ensembles)
- **5.0009** - Cross-Validation Strategies (proper CV for fair comparison)
- **5.0011** - Error Analysis (understand why one model outperforms another)
