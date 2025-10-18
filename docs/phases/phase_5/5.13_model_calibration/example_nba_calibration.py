#!/usr/bin/env python3
"""NBA Model Calibration Example - MCP Recommendation #21"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.model_calibration import ModelCalibrator

calibrator = ModelCalibrator()
print("✅ Model Calibration: Ensures predicted probabilities match actual outcomes")
print("Methods: Platt scaling, Isotonic regression, Temperature scaling")
