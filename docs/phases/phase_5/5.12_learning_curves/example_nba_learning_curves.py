#!/usr/bin/env python3
"""NBA Learning Curves Example - MCP Recommendation #20"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.learning_curves import LearningCurveAnalyzer

analyzer = LearningCurveAnalyzer()
# Analyze if model needs more data or better features
print("✅ Learning Curve Analyzer ready")
print("Diagnoses: bias/variance, optimal sample size")
