#!/usr/bin/env python3
"""NBA Model Explainability Example - MCP Recommendation #25"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.model_explainability import ModelExplainer

print("✅ Model Explainability: Detailed instance-level explanations")
print("Methods: Permutation importance, LIME, interactions, partial dependence")
