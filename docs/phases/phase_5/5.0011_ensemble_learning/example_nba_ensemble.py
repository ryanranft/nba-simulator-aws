#!/usr/bin/env python3
"""NBA Ensemble Learning Example - MCP Recommendation #19"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.ensemble_learning import EnsembleBuilder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

# Create ensemble of multiple models
models = {
    "rf": RandomForestClassifier(n_estimators=100),
    "gb": GradientBoostingClassifier(n_estimators=100),
    "lr": LogisticRegression(),
}

ensemble = EnsembleBuilder(models)
print("✅ Ensemble created with 3 base models: RF, GB, LR")
print("Ready for voting/stacking/bagging strategies")
