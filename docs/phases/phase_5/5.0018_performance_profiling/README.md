# Phase 5.0013: Performance Profiling

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/performance_profiling.py` (589 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #25

---

## Overview

Comprehensive performance profiling framework providing:
- **Memory profiling** - Peak usage, allocations, GC analysis
- **Execution time analysis** - Total time, per-sample time
- **Throughput measurement** - Predictions per second
- **Resource utilization** - CPU, memory, disk usage
- **Bottleneck identification** - Identify performance bottlenecks
- **Optimization recommendations** - Actionable improvement suggestions

Designed for optimizing NBA ML pipelines.

---

## When to Use

### Use This Framework When:
- ✅ **Production deployment planned** - Optimize before deployment
- ✅ **Latency requirements** - Need fast inference times
- ✅ **Large-scale predictions** - Batch prediction optimization
- ✅ **Memory constraints** - Limited RAM available
- ✅ **Cost optimization** - Reduce compute costs

### Do NOT Use When:
- ❌ **Model still in development** - Premature optimization
- ❌ **Performance already acceptable** - No optimization needed
- ❌ **Prototype/one-off predictions** - Overhead not justified

---

## How to Use

### Quick Start - Profile Function

```python
from scripts.ml.performance_profiling import PerformanceProfiler

# Initialize profiler
profiler = PerformanceProfiler()

# Define workload to profile
def prediction_workload():
    # Load data
    X = load_test_data()
    # Make predictions
    y_pred = model.predict(X)
    return y_pred

# Profile both memory and time
result, memory_profile, time_profile = profiler.profile_comprehensive(
    func=prediction_workload,
    n_samples=10000  # Number of predictions
)

print("Memory Profile:")
print(f"  Baseline: {memory_profile.baseline_memory_mb:.1f} MB")
print(f"  Peak: {memory_profile.peak_memory_mb:.1f} MB")
print(f"  Increase: {memory_profile.memory_increase_mb:.1f} MB")

print("\nTime Profile:")
print(f"  Total time: {time_profile.total_time:.4f} seconds")
print(f"  Throughput: {time_profile.throughput_samples_per_sec:.1f} predictions/sec")
print(f"  Avg time per prediction: {time_profile.avg_time_per_sample*1000:.4f} ms")
```

### Generate Performance Report

```python
# Create comprehensive report with bottlenecks and recommendations
report = profiler.create_report(
    memory_profile=memory_profile,
    time_profile=time_profile
)

print("\nSystem Stats:")
for key, value in report.system_stats.items():
    print(f"  {key}: {value:.2f}")

if report.bottlenecks:
    print("\nBottlenecks Detected:")
    for i, bottleneck in enumerate(report.bottlenecks, 1):
        print(f"  {i}. {bottleneck}")

print("\nOptimization Recommendations:")
for i, rec in enumerate(report.recommendations, 1):
    print(f"  {i}. {rec}")

# Export report
profiler.export_report(
    output_path='models/profiling/performance_report.json',
    report=report
)
```

### Profile Specific Components

```python
# Profile individual pipeline components
components = {
    'data_loading': lambda: load_data(),
    'feature_extraction': lambda: extract_features(raw_data),
    'prediction': lambda: model.predict(features),
    'postprocessing': lambda: postprocess_predictions(predictions)
}

for name, func in components.items():
    _, memory_prof, time_prof = profiler.profile_comprehensive(
        func=func,
        n_samples=1000
    )

    print(f"\n{name}:")
    print(f"  Memory: {memory_prof.memory_increase_mb:.1f} MB")
    print(f"  Time: {time_prof.total_time:.4f} s")
    print(f"  Throughput: {time_prof.throughput_samples_per_sec:.1f} samples/sec")
```

---

## Integration with NBA Panel Data

```python
# Example: Profile win prediction pipeline
def nba_prediction_pipeline():
    # Load game data
    games_df = pd.read_parquet('data/panel_data/recent_games.parquet')

    # Extract features
    X = games_df[feature_cols]

    # Make predictions
    win_proba = win_prediction_model.predict_proba(X)

    # Generate betting recommendations
    recommendations = generate_betting_recommendations(win_proba)

    return recommendations

# Profile entire pipeline
profiler = PerformanceProfiler()

result, memory_prof, time_prof = profiler.profile_comprehensive(
    func=nba_prediction_pipeline,
    n_samples=len(games_df)
)

report = profiler.create_report(memory_prof, time_prof)

# Check if meets production requirements
LATENCY_REQUIREMENT_MS = 100  # 100ms per prediction
avg_latency_ms = time_prof.avg_time_per_sample * 1000

if avg_latency_ms > LATENCY_REQUIREMENT_MS:
    print(f"⚠️ Latency requirement not met:")
    print(f"   Current: {avg_latency_ms:.2f} ms")
    print(f"   Required: {LATENCY_REQUIREMENT_MS} ms")
    print(f"\nOptimization needed!")
    print("Recommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")
else:
    print(f"✅ Latency requirement met: {avg_latency_ms:.2f} ms")
```

---

## Workflow References

- **Workflow #13** - Model Testing
- **Workflow #41** - Testing Framework
- **Phase 5.0011** - Error Analysis (profile error analysis speed)
- **Phase 5.0012** - Model Explainability (profile explanation speed)

---

## Integration Points

1. **Performance Profiling (5.13)** → **Model Selection**
   - Profile candidate models
   - Consider latency/throughput in model selection

2. **Performance Profiling (5.13)** → **Feature Selection (5.5)**
   - Identify expensive features
   - Remove features with high compute cost and low importance

3. **Performance Profiling (5.13)** → **Production Deployment**
   - Validate performance requirements met
   - Estimate infrastructure costs

---

## Common Patterns

### Pattern 1: Compare Model Performance

```python
# Profile different models
models = {
    'logistic_regression': lr_model,
    'random_forest': rf_model,
    'gradient_boosting': gb_model
}

results = []

for name, model in models.items():
    def predict_func():
        return model.predict(X_test)

    _, mem_prof, time_prof = profiler.profile_comprehensive(
        func=predict_func,
        n_samples=len(X_test)
    )

    results.append({
        'model': name,
        'memory_mb': mem_prof.memory_increase_mb,
        'time_s': time_prof.total_time,
        'throughput': time_prof.throughput_samples_per_sec
    })

# Display results
results_df = pd.DataFrame(results)
print(results_df.sort_values('throughput', ascending=False))
```

### Pattern 2: Identify Memory Leaks

```python
# Profile repeated predictions
memory_usage_over_time = []

for i in range(10):
    def predict_batch():
        return model.predict(X_test)

    _, mem_prof, _ = profiler.profile_comprehensive(
        func=predict_batch,
        n_samples=len(X_test)
    )

    memory_usage_over_time.append(mem_prof.memory_increase_mb)

# Check for memory leak
if any(mem > memory_usage_over_time[0] * 1.5 for mem in memory_usage_over_time[1:]):
    print("⚠️ Potential memory leak detected!")
    print(f"   Memory usage: {memory_usage_over_time}")
else:
    print("✅ No memory leak detected")
```

### Pattern 3: Production Readiness Check

```python
# Define production requirements
REQUIREMENTS = {
    'max_latency_ms': 100,
    'min_throughput': 100,  # predictions/sec
    'max_memory_mb': 1000
}

# Profile production workload
def production_workload():
    return model.predict(X_test)

_, mem_prof, time_prof = profiler.profile_comprehensive(
    func=production_workload,
    n_samples=len(X_test)
)

# Check requirements
checks = {
    'Latency': time_prof.avg_time_per_sample * 1000 <= REQUIREMENTS['max_latency_ms'],
    'Throughput': time_prof.throughput_samples_per_sec >= REQUIREMENTS['min_throughput'],
    'Memory': mem_prof.memory_increase_mb <= REQUIREMENTS['max_memory_mb']
}

print("Production Readiness:")
for check_name, passed in checks.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {check_name}: {status}")

if all(checks.values()):
    print("\n✅ Model ready for production!")
else:
    print("\n⚠️ Model NOT ready - optimization needed")
```

---

## Optimization Strategies

### Memory Optimization

| Issue | Solution | Expected Improvement |
|-------|----------|---------------------|
| High memory allocation | Batch processing | 50-80% reduction |
| Large model size | Model compression (pruning, quantization) | 50-90% reduction |
| Excessive GC | Object pooling | 20-40% reduction |
| Large intermediate arrays | In-place operations | 30-60% reduction |

### Speed Optimization

| Issue | Solution | Expected Improvement |
|-------|----------|---------------------|
| Slow predictions | Model simplification | 2-10x faster |
| Sequential processing | Vectorization | 10-100x faster |
| CPU-bound | Multi-threading | 2-4x faster |
| I/O-bound | Async I/O, caching | 5-50x faster |

---

## Troubleshooting

### Issue: High memory usage

**Solutions:**
- Use batch processing (smaller batches)
- Convert to sparse matrices if applicable
- Use float32 instead of float64
- Remove intermediate copies

### Issue: Low throughput

**Solutions:**
- Vectorize operations (use NumPy/pandas)
- Use compiled models (ONNX, TensorRT)
- Enable multi-threading
- Cache frequently used data

### Issue: Profiling overhead too high

**Solutions:**
- Profile on subset of data first
- Use sampling-based profiling
- Profile offline, not in production

---

## Performance Benchmarks

### Typical NBA Prediction Pipeline

| Component | Time (ms) | Memory (MB) | Throughput (pred/sec) |
|-----------|-----------|-------------|----------------------|
| Data loading | 5-20 | 50-200 | N/A |
| Feature extraction | 10-50 | 100-500 | 200-1000 |
| Model prediction | 1-100 | 50-500 | 100-10000 |
| Postprocessing | 1-10 | 10-50 | 1000-10000 |

**Total pipeline**: 17-180 ms, 210-1250 MB, ~100-1000 predictions/sec

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
- **Phase 5.0011** - Error Analysis (profile analysis speed)
- **Phase 5.0012** - Model Explainability (profile explanation speed)
- **Production Deployment Documentation** - Deploy optimized models
