# Phase 5.11: Error Analysis

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/error_analysis.py` (700 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #23

---

## Overview

Comprehensive error analysis framework providing:
- **Error pattern detection** - Identify systematic misclassifications
- **Error segmentation** - Analyze errors by feature subgroups
- **Confusion analysis** - Detailed confusion matrix insights
- **Confidence analysis** - High-confidence errors detection
- **Actionable recommendations** - Data/feature/model improvement suggestions

Designed for NBA temporal panel data with basketball-specific error patterns.

---

## When to Use

### Use This Framework When:
- ✅ **Model deployed but underperforming** - Diagnose why predictions fail
- ✅ **Systematic errors detected** - Model consistently wrong on certain cases
- ✅ **Need improvement roadmap** - Prioritize what to fix next
- ✅ **Stakeholder questions** - Explain model failures
- ✅ **Feature engineering validation** - Identify weak feature coverage

### Do NOT Use When:
- ❌ **Model still in early development** - Focus on basic performance first
- ❌ **Random errors** - No systematic patterns to analyze
- ❌ **Insufficient test data** - Need at least 500 samples with errors

---

## How to Use

### Quick Start - Detect Error Patterns

```python
from scripts.ml.error_analysis import ErrorAnalyzer

# Get predictions
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

# Initialize analyzer
analyzer = ErrorAnalyzer(
    X=X_test,
    y_true=y_test,
    y_pred=y_pred,
    y_proba=y_proba,
    feature_names=X_test.columns.tolist()
)

# Detect systematic error patterns
patterns = analyzer.detect_error_patterns(y_test, y_pred, y_proba)

print(f"Detected {len(patterns)} error patterns:")
for pattern in patterns:
    print(f"  - {pattern.pattern_type}: {pattern.description}")
    print(f"    Frequency: {pattern.frequency} ({pattern.percentage:.2f}%)")
    print(f"    Severity: {pattern.severity}")
```

### Error Segmentation

```python
# Analyze errors by feature segments
segments = analyzer.segment_errors(
    X=X_test,
    y_true=y_test,
    y_pred=y_pred,
    segment_features=['home_away', 'rest_days_category', 'season_phase']
)

print("Error rates by segment:")
for segment in segments:
    print(f"  {segment.segment_name}: {segment.segment_size} samples")
    print(f"    Error rate: {segment.error_rate:.2%}")
    print(f"    Expected: {segment.expected_error_rate:.2%}")
    if segment.is_significant:
        print(f"    ⚠️ Significantly high error rate!")
```

### Comprehensive Error Analysis

```python
# Full analysis with recommendations
analysis_result = analyzer.analyze_errors(
    X=X_test,
    y_true=y_test,
    y_pred=y_pred,
    y_proba=y_proba
)

print(f"\nTotal errors: {analysis_result.total_errors} / {analysis_result.total_samples}")
print(f"Error rate: {analysis_result.error_rate:.2%}")

print("\nError patterns:")
for pattern in analysis_result.error_patterns:
    print(f"  - {pattern.description} ({pattern.severity})")

print("\nRecommendations:")
for i, rec in enumerate(analysis_result.recommendations, 1):
    print(f"  {i}. {rec}")

# Export for documentation
analyzer.export_results(
    output_path='models/error_analysis/error_report.json',
    result=analysis_result
)
```

---

## Integration with NBA Panel Data

```python
# Example: Analyze win prediction errors
panel_df = pd.read_parquet('data/panel_data/game_level_panel.parquet')

# Focus on recent games
recent_mask = panel_df['game_date'] >= '2024-10-01'
X_recent = panel_df.loc[recent_mask, feature_cols]
y_recent = panel_df.loc[recent_mask, 'win']

# Get predictions
y_pred_recent = win_prediction_model.predict(X_recent)
y_proba_recent = win_prediction_model.predict_proba(X_recent)

# Initialize analyzer
analyzer = ErrorAnalyzer(
    X=X_recent,
    y_true=y_recent,
    y_pred=y_pred_recent,
    y_proba=y_proba_recent,
    feature_names=feature_cols
)

# Analyze by basketball-specific segments
basketball_segments = [
    'home_away',  # Home vs away games
    'back_to_back',  # B2B vs rested
    'opponent_win_pct_bucket',  # Strong vs weak opponents
    'season_phase'  # Regular season vs playoffs
]

segments = analyzer.segment_errors(
    X=X_recent,
    y_true=y_recent,
    y_pred=y_pred_recent,
    segment_features=basketball_segments
)

# Identify problematic segments
for segment in segments:
    if segment.is_significant and segment.error_rate > 0.3:
        print(f"⚠️ High error rate for {segment.segment_name}:")
        print(f"   Error rate: {segment.error_rate:.2%}")
        print(f"   Sample size: {segment.segment_size}")
```

---

## Workflow References

- **Workflow #13** - Model Testing
- **Workflow #41** - Testing Framework
- **Phase 5.2** - Model Interpretation (combine with error analysis)
- **Phase 5.10** - Model Comparison (compare error patterns across models)
- **Phase 5.12** - Model Explainability (explain why specific errors occur)

---

## Integration Points

1. **Model Interpretation (5.2)** + **Error Analysis (5.11)**
   - Use interpretation to understand why errors occur
   - Focus interpretation on high-error segments

2. **Error Analysis (5.11)** → **Feature Engineering**
   - Identify feature gaps causing errors
   - Create features targeting error segments

3. **Model Comparison (5.10)** + **Error Analysis (5.11)**
   - Compare error patterns between models
   - Select model with better error distribution

4. **Error Analysis (5.11)** → **Model Explainability (5.12)**
   - Use explainability to understand specific error cases
   - Generate counterfactuals for misclassifications

---

## Common Patterns

### Pattern 1: Debug Specific Error Cases

```python
# Find high-confidence errors (most problematic)
errors = y_test != y_pred
high_confidence_errors = errors & (y_proba.max(axis=1) > 0.8)

print(f"High-confidence errors: {high_confidence_errors.sum()}")

# Analyze these specific cases
error_indices = np.where(high_confidence_errors)[0]
for idx in error_indices[:5]:  # First 5
    print(f"\nError case {idx}:")
    print(f"  True: {y_test.iloc[idx]}, Predicted: {y_pred[idx]} (confidence: {y_proba[idx].max():.2f})")
    print(f"  Features: {X_test.iloc[idx].to_dict()}")
```

### Pattern 2: Track Error Trends Over Time

```python
# Analyze error rates by game date
panel_df['error'] = (y_test != y_pred).astype(int)

error_by_date = panel_df.groupby('game_date').agg({
    'error': ['mean', 'sum', 'count']
}).reset_index()

print("Error rate trends:")
print(error_by_date.tail(10))

# Detect if error rate increasing
from scipy.stats import spearmanr
corr, p_value = spearmanr(range(len(error_by_date)), error_by_date['error']['mean'])
if corr > 0.3 and p_value < 0.05:
    print("⚠️ Warning: Error rate increasing over time - consider retraining")
```

### Pattern 3: Compare Error Patterns Before/After Changes

```python
# Before model update
analyzer_before = ErrorAnalyzer(X=X_test, y_true=y_test, y_pred=y_pred_before, y_proba=y_proba_before)
patterns_before = analyzer_before.detect_error_patterns(y_test, y_pred_before, y_proba_before)

# After model update
analyzer_after = ErrorAnalyzer(X=X_test, y_true=y_test, y_pred=y_pred_after, y_proba=y_proba_after)
patterns_after = analyzer_after.detect_error_patterns(y_test, y_pred_after, y_proba_after)

print("Pattern changes:")
for pattern_type in set([p.pattern_type for p in patterns_before + patterns_after]):
    freq_before = sum([p.frequency for p in patterns_before if p.pattern_type == pattern_type])
    freq_after = sum([p.frequency for p in patterns_after if p.pattern_type == pattern_type])
    change = freq_after - freq_before
    print(f"  {pattern_type}: {freq_before} → {freq_after} ({change:+d})")
```

---

## Troubleshooting

### Issue: No clear error patterns detected

**Causes:**
- Errors are random (good sign - model performing well)
- Test set too small
- Features don't capture error-causing factors

**Solutions:**
- Collect more test data
- Try different segmentation features
- Accept that some errors are unavoidable

### Issue: Too many error patterns detected

**Causes:**
- Model severely underfitting
- Poor feature engineering
- Data quality issues

**Solutions:**
- Focus on patterns with severity='critical' or 'high'
- Prioritize patterns with high frequency
- Check data quality first

### Issue: Recommendations too generic

**Causes:**
- Error patterns not specific enough
- Limited feature information

**Solutions:**
- Use domain knowledge to define better segments
- Add more contextual features for analysis
- Manually investigate high-error cases

---

## Performance Considerations

- **Pattern detection**: O(n) where n = test samples (~fast, <1 second for 10K samples)
- **Segmentation**: O(n × m) where m = segment features (~fast, <5 seconds)
- **Full analysis**: O(n × (m + k)) where k = pattern types (~moderate, 10-30 seconds)

**Memory usage**: ~50-200 MB for typical NBA dataset

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference and advanced examples
- **Phase 5.2** - Model Interpretation (understand model decisions)
- **Phase 5.10** - Model Comparison (compare error patterns)
- **Phase 5.12** - Model Explainability (explain specific errors)
- **Phase 5.13** - Performance Profiling (optimize error analysis speed)
