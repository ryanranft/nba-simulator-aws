# Phase 5.3: Feature Store

**Status:** ✅ COMPLETE
**Implementation:** `scripts/ml/feature_store.py` (588 lines)
**Created:** 2025-10-18
**MCP Book Recommendation:** #16

---

## Overview

Centralized feature management system with:
- Feature registration and metadata tracking
- Version control for feature definitions
- Training/serving consistency
- Feature lineage tracking
- Temporal feature caching

Designed for NBA temporal panel data with time-aware feature management.

---

## When to Use

### Use This Framework When:
- ✅ **Multiple models share features** - Centralize feature definitions
- ✅ **Training/serving skew issues** - Ensure consistency across environments
- ✅ **Feature engineering proliferation** - Need organized feature catalog
- ✅ **Team collaboration** - Share features across data scientists
- ✅ **Production deployment** - Need feature versioning and lineage

### Do NOT Use When:
- ❌ **Single model prototype** - Overhead not justified
- ❌ **Exploratory analysis** - Too rigid for experimentation
- ❌ **Simple feature set** (<10 features) - Manual management sufficient

---

## How to Use

```python
from scripts.ml.feature_store import FeatureStore

# Initialize store
store = FeatureStore(storage_path='data/feature_store/')

# Register feature
store.register_feature(
    name='cumulative_points',
    description='Player cumulative points at game time',
    feature_type='numeric',
    source_table='panel_data.player_games',
    computation_logic='SUM(points) OVER (PARTITION BY player_id ORDER BY game_datetime)',
    version='1.0.0'
)

# Compute and store features
features = store.compute_features(
    feature_names=['cumulative_points', 'win_rate_l10'],
    entity_df=games_df,
    timestamp_column='game_datetime'
)

# Load for training
X_train = store.load_features(
    feature_names=['cumulative_points', 'win_rate_l10', 'rest_days'],
    start_date='2023-01-01',
    end_date='2024-01-01'
)
```

---

## Workflow References

- **Workflow #41** - Testing Framework
- **Phase 5.5** - Feature Selection (use store for feature retrieval)
- **Phase 5.4** - Automated Retraining (feature versioning)

---

## Common Patterns

### Pattern 1: Register Panel Data Features

```python
# Register temporal cumulative features
temporal_features = [
    {
        'name': 'career_ppg',
        'description': 'Career points per game at game time',
        'feature_type': 'numeric',
        'source': 'panel_data.player_game_snapshots'
    },
    {
        'name': 'team_win_pct',
        'description': 'Team win percentage at game time',
        'feature_type': 'numeric',
        'source': 'panel_data.team_snapshots'
    }
]

for feature in temporal_features:
    store.register_feature(**feature)
```

### Pattern 2: Version Control

```python
# Update feature definition (new version)
store.update_feature(
    name='cumulative_points',
    version='1.1.0',
    computation_logic='SUM(points) OVER (PARTITION BY player_id, season ORDER BY game_datetime)',
    changelog='Added season partitioning for per-season cumulative stats'
)

# Load specific version
features_v1_0 = store.load_features(
    feature_names=['cumulative_points'],
    version='1.0.0'
)
```

---

## See Also

- **USAGE_GUIDE.md** - Detailed API reference
- **Phase 5.4** - Automated Retraining
- **Phase 5.5** - Feature Selection
