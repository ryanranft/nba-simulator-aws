# 5.0001: Hyperparameter Optimization

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/hyperparameter_tuning.py` (623 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #14

---

## Overview

Comprehensive hyperparameter optimization framework implementing three search strategies:
1. **Grid Search** - Exhaustive search over parameter grid
2. **Random Search** - Random sampling for efficient exploration
3. **Bayesian Optimization** - Intelligent search using Gaussian processes

Designed specifically for NBA temporal panel data models with time-aware validation.

---

## When to Use

### Use This Framework When:
- ✅ **Initial model development** - Finding optimal hyperparameters for new models
- ✅ **Model performance plateau** - Current model not improving with feature engineering
- ✅ **After feature changes** - New features added, need hyperparameter retuning
- ✅ **Cross-validation shows high variance** - Model sensitive to hyperparameters
- ✅ **Before production deployment** - Final optimization before deployment

### Do NOT Use When:
- ❌ **Insufficient training data** - Need at least 500+ samples for reliable optimization
- ❌ **Model already near theoretical maximum** - Accuracy >95%, diminishing returns
- ❌ **Time constraints** - Bayesian optimization can take hours on large parameter spaces
- ❌ **Preliminary exploration** - Use default parameters first, then optimize

---

## How to Use

### Quick Start

```python
from scripts.ml.hyperparameter_tuning import HyperparameterOptimizer
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load panel data
X_train = pd.read_csv('data/features_train.csv')
y_train = pd.read_csv('data/targets_train.csv')

# Initialize optimizer
optimizer = HyperparameterOptimizer(
    model_type='random_forest',
    X_train=X_train,
    y_train=y_train,
    cv_strategy='time_series',  # Critical for temporal data
    n_splits=5,
    scoring='roc_auc'
)

# Define parameter space
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 20, 30, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

# Run grid search
result = optimizer.grid_search(param_grid)
print(f"Best parameters: {result.best_params}")
print(f"Best score: {result.best_score:.4f}")

# Train final model with best params
model = RandomForestClassifier(**result.best_params)
model.fit(X_train, y_train)
```

### Advanced: Bayesian Optimization

```python
# For large parameter spaces, use Bayesian optimization
param_space = {
    'n_estimators': (50, 500),  # Range instead of list
    'max_depth': (5, 50),
    'min_samples_split': (2, 20),
    'min_samples_leaf': (1, 10),
    'max_features': (0.1, 1.0)  # Continuous parameters
}

result = optimizer.bayesian_optimization(
    param_space=param_space,
    n_iterations=50,  # More iterations = better convergence
    n_initial_points=10  # Random exploration before optimization
)

# Export results for tracking
optimizer.export_results(
    output_path='models/hyperparameter_results/rf_optimization.json',
    result=result
)
```

### Integration with Panel Data

```python
# Example: Optimize for temporal NBA panel data
# Load game-level panel data with cumulative stats
panel_df = pd.read_parquet('data/panel_data/game_level_panel.parquet')

# Split by date (respect temporal structure)
train_mask = panel_df['game_date'] < '2024-01-01'
val_mask = (panel_df['game_date'] >= '2024-01-01') & (panel_df['game_date'] < '2024-03-01')

X_train = panel_df.loc[train_mask, feature_cols]
y_train = panel_df.loc[train_mask, 'target']

# Initialize with time-series CV
optimizer = HyperparameterOptimizer(
    model_type='gradient_boosting',
    X_train=X_train,
    y_train=y_train,
    cv_strategy='time_series',  # Respects temporal order
    n_splits=5,
    scoring='f1'  # Or 'roc_auc', 'precision', 'recall'
)

# Optimize
param_grid = {
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 5, 7],
    'subsample': [0.8, 0.9, 1.0]
}

result = optimizer.grid_search(param_grid)
```

---

## Parameter Space Recommendations

### Random Forest (NBA Win Prediction)
```python
{
    'n_estimators': [100, 200, 300, 500],
    'max_depth': [10, 20, 30, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4, 8],
    'max_features': ['sqrt', 'log2', 0.5, 0.8],
    'class_weight': ['balanced', 'balanced_subsample', None]
}
```

### Gradient Boosting (Point Spread Prediction)
```python
{
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'n_estimators': [100, 200, 300, 500],
    'max_depth': [3, 5, 7, 10],
    'min_samples_split': [5, 10, 20],
    'subsample': [0.8, 0.9, 1.0],
    'max_features': [0.5, 0.7, 0.9, 1.0]
}
```

### Logistic Regression (Binary Outcome)
```python
{
    'C': [0.001, 0.01, 0.1, 1, 10, 100],
    'penalty': ['l1', 'l2', 'elasticnet'],
    'solver': ['liblinear', 'saga'],
    'class_weight': ['balanced', None],
    'max_iter': [100, 500, 1000]
}
```

---

## Optimization Strategies

### Strategy Selection Matrix

| Scenario | Parameter Count | Sample Size | Recommended Strategy | Estimated Time |
|----------|----------------|-------------|---------------------|---------------|
| Quick exploration | <20 combinations | Any | Grid Search | 5-30 min |
| Medium complexity | 20-100 combos | >1000 samples | Random Search | 15-60 min |
| Large parameter space | >100 combos | >5000 samples | Bayesian Optimization | 1-4 hours |
| Production tuning | Any | >10000 samples | Bayesian (50+ iters) | 2-8 hours |

### Best Practices

1. **Start broad, then narrow**
   ```python
   # Phase 1: Coarse grid search
   coarse_grid = {
       'n_estimators': [50, 200, 500],
       'max_depth': [5, 20, None]
   }

   # Phase 2: Fine-tune around best region
   fine_grid = {
       'n_estimators': [180, 200, 220],  # Narrow around 200
       'max_depth': [18, 20, 22]
   }
   ```

2. **Use appropriate CV for temporal data**
   ```python
   # ALWAYS use time_series CV for NBA panel data
   optimizer = HyperparameterOptimizer(
       cv_strategy='time_series',  # NOT 'k_fold'
       n_splits=5
   )
   ```

3. **Monitor for overfitting**
   ```python
   # Check train vs validation scores
   if result.train_score - result.best_score > 0.1:
       print("Warning: Model may be overfitting")
       # Regularize: increase min_samples_split, reduce max_depth
   ```

4. **Export and version results**
   ```python
   # Always save results for comparison
   optimizer.export_results(
       output_path=f'models/optimization/{model_name}_{timestamp}.json',
       result=result
   )
   ```

---

## Workflow References

- **Workflow #13** - Model Testing (test hyperparameter optimization)
- **Workflow #41** - Testing Framework (comprehensive testing)
- **5.0009** - Cross-Validation Strategies (CV selection guidance)
- **5.0010** - Model Comparison (compare optimized vs baseline)

---

## Integration Points

### With Other Frameworks

1. **Feature Selection (5.5)** → **Hyperparameter Optimization (5.1)**
   - Run feature selection first to reduce dimensionality
   - Then optimize hyperparameters on selected features

2. **Hyperparameter Optimization (5.1)** → **Model Calibration (5.8)**
   - Optimize first for best discrimination
   - Then calibrate for probability accuracy

3. **Cross-Validation (5.9)** → **Hyperparameter Optimization (5.1)**
   - Use appropriate CV strategy from 5.9
   - Pass to optimizer for consistent evaluation

4. **Hyperparameter Optimization (5.1)** → **Model Comparison (5.10)**
   - Compare optimized model to baseline
   - Validate improvement is statistically significant

---

## Common Patterns

### Pattern 1: Quick Win Prediction Optimization

```python
# Optimize RandomForest for NBA win prediction
from scripts.ml.hyperparameter_tuning import HyperparameterOptimizer

optimizer = HyperparameterOptimizer(
    model_type='random_forest',
    X_train=X_train,
    y_train=y_train_win,  # Binary: 1=win, 0=loss
    cv_strategy='time_series',
    scoring='roc_auc'
)

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, None],
    'min_samples_split': [5, 10, 20]
}

result = optimizer.random_search(param_grid, n_iterations=30)
```

### Pattern 2: Point Spread Regression

```python
# Optimize for point spread prediction (regression)
optimizer = HyperparameterOptimizer(
    model_type='gradient_boosting',
    X_train=X_train,
    y_train=y_train_spread,  # Continuous: point differential
    cv_strategy='time_series',
    scoring='neg_mean_squared_error'
)

param_space = {
    'learning_rate': (0.01, 0.2),
    'n_estimators': (100, 500),
    'max_depth': (3, 10)
}

result = optimizer.bayesian_optimization(param_space, n_iterations=50)
```

### Pattern 3: Multi-Metric Optimization

```python
# Optimize considering multiple metrics
import pandas as pd

results = []
for metric in ['roc_auc', 'f1', 'precision', 'recall']:
    optimizer = HyperparameterOptimizer(
        model_type='random_forest',
        X_train=X_train,
        y_train=y_train,
        cv_strategy='time_series',
        scoring=metric
    )

    result = optimizer.grid_search(param_grid)
    results.append({
        'metric': metric,
        'best_score': result.best_score,
        'best_params': result.best_params
    })

# Compare results
results_df = pd.DataFrame(results)
print(results_df)
```

---

## Troubleshooting

### Issue: Optimization takes too long

**Solutions:**
- Reduce parameter grid size (fewer values per parameter)
- Use Random Search instead of Grid Search
- Reduce n_splits in CV (from 5 to 3)
- Use smaller n_iterations for Bayesian optimization

### Issue: All parameter combinations perform similarly

**Causes:**
- Model already at performance ceiling
- Features are weak (optimize features, not hyperparameters)
- Insufficient variance in data

**Solutions:**
- Try different model type
- Focus on feature engineering (5.0005)
- Collect more data

### Issue: Overfitting detected (high train score, low validation)

**Solutions:**
- Add regularization parameters to search space
- Increase min_samples_split, min_samples_leaf
- Reduce max_depth
- Add more training data

---

## Performance Considerations

- **Grid Search**: O(n_params^n_dimensions × n_folds × n_samples)
- **Random Search**: O(n_iterations × n_folds × n_samples)
- **Bayesian Optimization**: O(n_iterations × n_folds × n_samples) + GP overhead

**Memory usage**: ~100-500 MB for typical NBA dataset (10K samples, 100 features)

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
- **5.0000** - Initial ML model development
- **5.0005** - Feature selection (run before optimization)
- **5.0009** - Cross-validation strategies
- **5.0010** - Model comparison framework
