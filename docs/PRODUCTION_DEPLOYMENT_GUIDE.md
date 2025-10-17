# NBA Game Predictor - Production Deployment Guide

**Date:** October 17, 2025
**Model Version:** 1.0
**Status:** ✅ Ready for Production

---

## Table of Contents

1. [Overview](#overview)
2. [Model Specifications](#model-specifications)
3. [Deployment Architecture](#deployment-architecture)
4. [Quick Start](#quick-start)
5. [API Reference](#api-reference)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

---

## Overview

This guide provides complete instructions for deploying the NBA game prediction model to production. The model achieved **84% accuracy** on the 2021 test set with validated performance across multiple years (84.9% ± 0.9% cross-validation).

### What's Deployed

- **Model:** Logistic Regression with 300 historical features
- **API:** Flask REST API for predictions
- **Monitoring:** Performance tracking and drift detection
- **Artifacts:** All preprocessing pipelines and metadata

### Performance Expectations

- **Accuracy:** 84-86% (based on validation)
- **Latency:** <100ms per prediction
- **Throughput:** ~100 predictions/second (single instance)

---

## Model Specifications

### Model Details

```python
Model: LogisticRegression
Parameters:
  - C: 1.0 (regularization strength)
  - penalty: 'l2'
  - max_iter: 1000
  - solver: 'lbfgs'
  - random_state: 42

Features: 300 historical panel features
  - Lag variables (1, 2, 3, 5, 10 games back)
  - Rolling windows (3, 5, 10, 20 games)
  - Statistics: points, rebounds, assists, FG%, 3P%, FT%,
               steals, blocks, turnovers, minutes

Training Data: 2017-2020 seasons (3,837 games)
Test Data: 2021 season (1,099 games)
```

### Performance Metrics

| Metric | Value |
|--------|-------|
| Test Accuracy | 84.0% |
| Test AUC | 0.918 |
| Train/Test Gap | 7.6% |
| CV Accuracy | 84.9% ± 0.9% |
| Precision (Win) | 80% |
| Recall (Win) | 84% |

### MLflow Registry

```
Model Name: nba_game_predictor
Version: 1
Run ID: 1a2725dca5304ec9ad9602756296153e
Location: mlruns/
```

---

## Deployment Architecture

### Local Development Setup

```
┌─────────────────────────────────────────┐
│         Client Application              │
└────────────┬────────────────────────────┘
             │ HTTP POST /predict
             ▼
┌─────────────────────────────────────────┐
│      Flask Prediction API (Port 5001)   │
│  - Load Model from MLflow               │
│  - Preprocessing Pipeline               │
│  - Return Predictions                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      MLflow Model Registry              │
│  - Model: nba_game_predictor v1         │
│  - Artifacts: scaler, features, stats   │
└─────────────────────────────────────────┘
```

### Production Setup (Optional)

For production at scale, consider:

```
┌─────────────┐
│ Load Balancer│
└──────┬───────┘
       │
   ┌───┴────┬────────┐
   ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐
│ API  │ │ API  │ │ API  │  (Multiple instances)
│ Pod 1│ │ Pod 2│ │ Pod 3│
└──┬───┘ └──┬───┘ └──┬───┘
   │        │        │
   └────────┼────────┘
            ▼
     ┌──────────────┐
     │ MLflow Server│
     │ (S3 backend) │
     └──────────────┘
            │
            ▼
     ┌──────────────┐
     │ PostgreSQL   │
     │ (Predictions)│
     └──────────────┘
```

---

## Quick Start

### 1. Start the Prediction API

```bash
# Activate environment
conda activate nba-aws

# Navigate to project directory
cd /Users/ryanranft/nba-simulator-aws

# Start API server
python scripts/ml/prediction_api.py
```

The API will start on `http://localhost:5001`

### 2. Test the API

In another terminal:

```bash
python scripts/ml/test_prediction_api.py
```

Expected output:
```
[1/4] Health Check...
  ✓ API is healthy

[2/4] Model Info...
  Model: nba_game_predictor v1
  Accuracy: 84.0%

[3/4] Single Game Prediction...
  Prediction: win
  Probability: 85.2%
  ✓ Correct!

[4/4] Batch Prediction...
  Predicted 3 games
  Accuracy: 3/3 (100%)
```

### 3. Run Monitoring

```bash
python scripts/ml/monitoring_dashboard.py
```

This will:
- Evaluate current performance
- Check for feature drift
- Generate monitoring report
- Save metrics to CSV files

---

## API Reference

### Base URL

```
http://localhost:5001
```

### Endpoints

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-10-17T13:42:00Z"
}
```

#### Model Info

```http
GET /model_info
```

**Response:**
```json
{
  "model_name": "nba_game_predictor",
  "model_version": "1",
  "run_id": "1a2725dca5304ec9ad9602756296153e",
  "n_features": 300,
  "test_accuracy": 0.840,
  "test_auc": 0.918,
  "trained_on": "2017-2020 seasons",
  "last_updated": "2025-10-17T13:42:00Z"
}
```

#### Predict Single Game

```http
POST /predict
Content-Type: application/json
```

**Request Body:**
```json
{
  "features": {
    "home_points_rolling_3_mean_sum": 310.5,
    "away_points_rolling_3_mean_sum": 295.0,
    "matchup_points_rolling_3_mean_diff": 15.5,
    ...  // All 300 features
  }
}
```

**Response:**
```json
{
  "prediction": "win",
  "probability": 0.852,
  "probabilities": {
    "loss": 0.148,
    "win": 0.852
  },
  "confidence": "high",
  "timestamp": "2025-10-17T13:42:00Z"
}
```

**Confidence Levels:**
- `high`: probability > 75%
- `medium`: probability 60-75%
- `low`: probability < 60%

#### Predict Batch

```http
POST /predict_batch
Content-Type: application/json
```

**Request Body:**
```json
{
  "games": [
    {
      "game_id": "game_123",
      "features": {...}
    },
    {
      "game_id": "game_456",
      "features": {...}
    }
  ]
}
```

**Response:**
```json
{
  "predictions": [
    {
      "game_id": "game_123",
      "prediction": "win",
      "probability": 0.852,
      "confidence": "high"
    },
    {
      "game_id": "game_456",
      "prediction": "loss",
      "probability": 0.621,
      "confidence": "medium"
    }
  ],
  "count": 2,
  "timestamp": "2025-10-17T13:42:00Z"
}
```

### Error Responses

```json
{
  "error": "Missing required features",
  "missing_features": ["home_points_lag1_sum", ...]
}
```

Status codes:
- `200`: Success
- `400`: Bad request (missing features, invalid format)
- `500`: Server error

---

## Monitoring

### Performance Tracking

The monitoring dashboard tracks:

1. **Prediction Accuracy**
   - Current vs baseline
   - Alert if drops >5%

2. **AUC Score**
   - Discrimination ability
   - Alert if drops significantly

3. **Feature Drift**
   - Distribution changes
   - Alert if >10 features drift >2 std

### Running Monitoring

```bash
# Manual monitoring
python scripts/ml/monitoring_dashboard.py

# Scheduled monitoring (cron example)
# Run every day at 2 AM
0 2 * * * cd /Users/ryanranft/nba-simulator-aws && python scripts/ml/monitoring_dashboard.py
```

### Monitoring Outputs

**Performance History:**
```csv
/tmp/monitoring_performance.csv
```

Contains:
- Period name
- Accuracy, AUC
- Sample size
- Timestamp

**Drift Report:**
```csv
/tmp/monitoring_drift.csv
```

Contains:
- Feature name
- Baseline mean
- Current mean
- Drift magnitude
- Is drifted flag

### Alert Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Accuracy | < 80% | Retrain immediately |
| Accuracy | < 82% | Investigate |
| AUC | < 0.90 | Investigate |
| Drifted Features | > 10 | Retrain soon |
| Drifted Features | > 20 | Retrain immediately |

---

## Troubleshooting

### API Won't Start

**Problem:** `Model artifacts not found`

**Solution:**
```bash
# Re-run MLflow setup
python scripts/ml/mlflow_setup.py

# Verify artifacts exist
ls -la /tmp/scaler.pkl
ls -la /tmp/feature_list.txt
ls -la /tmp/train_stats.csv
```

### Low Accuracy

**Problem:** Predictions worse than expected

**Checks:**
1. Are you using the correct feature list? (300 features)
2. Are features computed correctly? (lag + rolling windows)
3. Is data from the same distribution? (2017-2021 NBA seasons)
4. Run monitoring: `python scripts/ml/monitoring_dashboard.py`

### Missing Features Error

**Problem:** API returns "Missing required features"

**Solution:**
```python
# Get feature list
import json
with open('/tmp/feature_list.txt', 'r') as f:
    required_features = [line.strip() for line in f]

# Check what you have
your_features = set(your_data.columns)
missing = set(required_features) - your_features
print(f"Missing {len(missing)} features:")
print(list(missing)[:10])  # First 10
```

### High Latency

**Problem:** Predictions taking too long

**Solutions:**
- Batch predictions instead of single
- Cache preprocessed features
- Use multiple API instances with load balancer

---

## Maintenance

### Regular Tasks

**Daily:**
- [ ] Check API health (`GET /health`)
- [ ] Review prediction logs

**Weekly:**
- [ ] Run monitoring dashboard
- [ ] Review drift reports
- [ ] Check accuracy trends

**Monthly:**
- [ ] Full model evaluation on new data
- [ ] Update training data if needed
- [ ] Retrain if accuracy drops

### Retraining Procedure

When to retrain:
- Accuracy drops below 80%
- >10 features show significant drift
- New season starts (different meta)
- Major NBA rule changes

**Retrain Steps:**

1. **Collect new data**
```bash
# Ensure latest game data is available
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_parquet/player_box/
```

2. **Re-run feature engineering**
```bash
python scripts/ml/fix_data_leakage_aggregation.py
python scripts/ml/feature_selection.py
```

3. **Train new model**
```bash
python scripts/ml/mlflow_setup.py
```

4. **Validate performance**
```bash
python scripts/ml/temporal_cross_validation.py
python scripts/ml/final_model_validation.py
```

5. **Deploy if better**
- Update run_id in `prediction_api.py`
- Restart API server
- Run monitoring to confirm

### Backup & Recovery

**Backup artifacts:**
```bash
# Backup MLflow runs
tar -czf mlflow_backup_$(date +%Y%m%d).tar.gz mlruns/

# Backup model artifacts
tar -czf artifacts_backup_$(date +%Y%m%d).tar.gz /tmp/scaler.pkl /tmp/feature_list.txt /tmp/train_stats.csv
```

**Restore from backup:**
```bash
# Restore MLflow runs
tar -xzf mlflow_backup_YYYYMMDD.tar.gz

# Restore artifacts
tar -xzf artifacts_backup_YYYYMMDD.tar.gz -C /
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Model trained and validated (84%+ accuracy)
- [ ] MLflow artifacts registered
- [ ] API tested locally
- [ ] Monitoring dashboard configured
- [ ] Documentation reviewed

### Production Deployment

- [ ] Environment configured (conda/pip)
- [ ] API server running
- [ ] Health check passes
- [ ] Test predictions working
- [ ] Monitoring enabled
- [ ] Alerting configured

### Post-Deployment

- [ ] Monitor accuracy for first week
- [ ] Check feature drift
- [ ] Review prediction logs
- [ ] User feedback collected
- [ ] Performance documented

---

## Cost Estimates

### Local Development
**Cost:** $0/month (runs on your machine)

### Production (AWS)

**Option 1: Single EC2 Instance**
- t3.medium instance: ~$30/month
- Total: **~$30/month**

**Option 2: Full Stack**
- EC2 instances (2x t3.medium): ~$60/month
- RDS PostgreSQL (db.t3.micro): ~$15/month
- S3 storage (MLflow): ~$5/month
- Load Balancer: ~$20/month
- Total: **~$100/month**

**Option 3: Serverless (AWS Lambda)**
- Lambda invocations: $0.20 per 1M requests
- API Gateway: $3.50 per 1M requests
- Total: **~$10-50/month** (depends on traffic)

---

## Support & Resources

### Documentation

- Model development: `docs/MODEL_IMPROVEMENT_FINAL_SUMMARY.md`
- Data leakage fix: `docs/CORRECTED_VALIDATION_SUMMARY.md`
- Original validation: `docs/FINAL_VALIDATION_SUMMARY.md`

### Scripts

- MLflow setup: `scripts/ml/mlflow_setup.py`
- Prediction API: `scripts/ml/prediction_api.py`
- Monitoring: `scripts/ml/monitoring_dashboard.py`
- Testing: `scripts/ml/test_prediction_api.py`

### Contact

- **Project:** NBA Simulator AWS
- **Location:** `/Users/ryanranft/nba-simulator-aws`
- **MLflow UI:** `http://localhost:5000` (after running `mlflow ui`)
- **API:** `http://localhost:5001`

---

## Conclusion

The NBA game prediction model is production-ready with:

✅ **Validated Performance** (84% accuracy)
✅ **Complete API** (Flask REST endpoints)
✅ **Monitoring System** (drift detection, alerts)
✅ **Documentation** (this guide + technical docs)
✅ **MLflow Integration** (model versioning, tracking)

The model is ready to deploy and start providing predictions!

---

**Version:** 1.0
**Last Updated:** October 17, 2025
**Status:** ✅ Production Ready
