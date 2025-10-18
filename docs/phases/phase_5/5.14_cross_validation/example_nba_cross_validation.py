#!/usr/bin/env python3
"""NBA Cross-Validation Example - MCP Recommendation #22"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.cross_validation_strategies import CVStrategySelector

# CRITICAL for NBA temporal data: use time series CV
cv_strategy = CVStrategySelector().get_strategy(strategy_type="time_series", n_splits=5)

print("✅ Time Series CV: Respects temporal ordering of NBA games")
print("NEVER use standard K-Fold for temporal panel data!")
