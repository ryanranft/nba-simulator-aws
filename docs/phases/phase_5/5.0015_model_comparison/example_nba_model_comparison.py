#!/usr/bin/env python3
"""NBA Model Comparison Example - MCP Recommendation #23"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.model_comparison import ModelComparator

comparator = ModelComparator()
print("✅ Model Comparison: Statistical tests to compare model performance")
print("Tests: Paired t-test, Wilcoxon, McNemar, Friedman")
