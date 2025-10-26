#!/usr/bin/env python3
"""NBA Automated Retraining Example - MCP Recommendation #17"""
import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")
from scripts.ml.automated_retraining import AutomatedRetrainingPipeline

# Initialize retraining pipeline
pipeline = AutomatedRetrainingPipeline(
    model_path="models/win_prediction/", monitoring_window_days=30, drift_threshold=0.05
)

# Configure retraining triggers
pipeline.configure_triggers(
    performance_drop_threshold=0.03,  # Retrain if AUC drops > 3%
    data_drift_threshold=0.05,  # Retrain if feature drift > 5%
    schedule="weekly",  # Or 'daily', 'monthly'
)

print("✅ Automated Retraining: Configured for NBA win prediction model")
print(f"Monitoring: {pipeline.monitoring_window_days} days")
print(f"Drift threshold: {pipeline.drift_threshold}")
