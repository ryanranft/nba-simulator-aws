#!/usr/bin/env python3
"""NBA Feature Store Example - MCP Recommendation #16"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")

import pandas as pd
from scripts.ml.feature_store import FeatureStore

# Initialize feature store
store = FeatureStore(storage_path="models/feature_store/")

# Register NBA features
features = {
    "team_rolling_stats": ["points_last_5", "rebounds_last_5", "assists_last_5"],
    "opponent_stats": ["opp_points_last_5", "opp_fg_pct_last_5"],
    "contextual": ["home_away", "rest_days", "back_to_back"],
}

for group_name, feature_list in features.items():
    store.register_feature_group(name=group_name, features=feature_list, version="v1.0")

print("✅ Feature Store Example: 3 feature groups registered")
print(f"Total features: {sum(len(f) for f in features.values())}")
