#!/usr/bin/env python3
"""NBA Feature Selection Example - MCP Recommendation #18"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
import pandas as pd, numpy as np
from scripts.ml.feature_selection import FeatureSelector

# Sample NBA features
np.random.seed(42)
X = pd.DataFrame({f"feature_{i}": np.random.randn(1000) for i in range(50)})
y = np.random.choice([0, 1], 1000)

# Initialize selector
selector = FeatureSelector()

# Run multiple selection methods
methods = ["variance", "correlation", "mutual_info", "lasso", "tree"]
selected_features = {}

for method in methods:
    features = selector.select_features(X, y, method=method, k=15)
    selected_features[method] = features
    print(f"✅ {method.upper()}: Selected {len(features)} features")

# Consensus features (selected by >3 methods)
from collections import Counter

all_features = [f for features in selected_features.values() for f in features]
consensus = [f for f, count in Counter(all_features).items() if count >= 3]
print(f"\n✅ Consensus features (≥3 methods): {len(consensus)}")
