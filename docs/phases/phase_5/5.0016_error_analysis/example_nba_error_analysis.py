#!/usr/bin/env python3
"""NBA Error Analysis Example - MCP Recommendation #24"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.error_analysis import ErrorAnalyzer

analyzer = ErrorAnalyzer(X=None, y_true=None, y_pred=None, y_proba=None)
print("✅ Error Analysis: Identify systematic prediction errors")
print("Features: Pattern detection, error segmentation, recommendations")
