# NBA Prediction API Documentation

**Version:** 1.0
**Last Updated:** October 3, 2025
**Status:** Production

---

## Overview

The NBA Prediction API provides real-time game outcome predictions using a trained machine learning model (Logistic Regression with 63% accuracy). The API is serverless, cost-effective, and highly scalable.

**Architecture:**
- **Lambda Function:** Lightweight Python function (4KB, no external dependencies)
- **API Gateway:** HTTP API with automatic scaling
- **Model Storage:** JSON coefficients in S3 (no sklearn required)
- **Response Time:** ~200-500ms (including cold start)

---

## API Endpoint

```
POST https://emktactsx8.execute-api.us-east-1.amazonaws.com
```

**Region:** `us-east-1`
**Content-Type:** `application/json`
**Authentication:** None (public endpoint)

---

## Request Format

### POST /

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "home_team": "LAL",
  "away_team": "BOS",
  "features": {
    "home_rolling_win_pct": 0.65,
    "home_rolling_ppg": 110.5,
    "home_rolling_papg": 105.2,
    "home_rolling_margin": 5.3,
    "home_rest_days": 2,
    "home_back_to_back": 0,
    "away_rolling_win_pct": 0.58,
    "away_rolling_ppg": 108.3,
    "away_rolling_papg": 107.1,
    "away_rolling_margin": 1.2,
    "away_rest_days": 1,
    "away_back_to_back": 0,
    "month": 11,
    "day_of_week": 3,
    "is_weekend": 0,
    "season_phase": 0
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `home_team` | string | Home team abbreviation (e.g., "LAL", "BOS") |
| `away_team` | string | Away team abbreviation |
| `features` | object | Game feature dict ionary (see below) |

### Feature Fields (all required)

| Feature | Type | Range | Description |
|---------|------|-------|-------------|
| `home_rolling_win_pct` | float | 0.0-1.0 | Home team rolling win % (last N games) |
| `home_rolling_ppg` | float | 80-130 | Home team points per game |
| `home_rolling_papg` | float | 80-130 | Home team points allowed per game |
| `home_rolling_margin` | float | -20 to +20 | Home team point differential |
| `home_rest_days` | int | 0-7 | Days since home team's last game |
| `home_back_to_back` | int | 0 or 1 | 1 if home team on back-to-back |
| `away_rolling_win_pct` | float | 0.0-1.0 | Away team rolling win % |
| `away_rolling_ppg` | float | 80-130 | Away team points per game |
| `away_rolling_papg` | float | 80-130 | Away team points allowed per game |
| `away_rolling_margin` | float | -20 to +20 | Away team point differential |
| `away_rest_days` | int | 0-7 | Days since away team's last game |
| `away_back_to_back` | int | 0 or 1 | 1 if away team on back-to-back |
| `month` | int | 1-12 | Month of game (1=Jan, 12=Dec) |
| `day_of_week` | int | 0-6 | Day of week (0=Monday, 6=Sunday) |
| `is_weekend` | int | 0 or 1 | 1 if game on Saturday/Sunday |
| `season_phase` | int | 0-3 | 0=early, 1=mid, 2=late, 3=playoffs |

---

## Response Format

### Success Response (200 OK)

```json
{
  "home_win_probability": 0.5561209648530041,
  "away_win_probability": 0.4438790351469959,
  "predicted_winner": "home",
  "confidence": 0.5561209648530041,
  "model_used": "logistic_regression",
  "model_accuracy": 0.63,
  "model_auc": 0.659,
  "prediction_timestamp": "2025-10-03T16:46:45.000874",
  "home_team": "LAL",
  "away_team": "BOS"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `home_win_probability` | float | Probability home team wins (0.0-1.0) |
| `away_win_probability` | float | Probability away team wins (0.0-1.0) |
| `predicted_winner` | string | "home" or "away" |
| `confidence` | float | Confidence level (max of two probabilities) |
| `model_used` | string | Model type ("logistic_regression") |
| `model_accuracy` | float | Model test accuracy (0.63 = 63%) |
| `model_auc` | float | Model AUC score (0.659) |
| `prediction_timestamp` | string | ISO 8601 timestamp |
| `home_team` | string | Echo of home team from request |
| `away_team` | string | Echo of away team from request |

### Error Responses

**400 Bad Request** - Missing or invalid features
```json
{
  "error": "Missing required features: home_rest_days, away_rest_days",
  "required_features": ["home_rolling_win_pct", ...]
}
```

**500 Internal Server Error** - Server-side error
```json
{
  "error": "Internal server error",
  "message": "Error details..."
}
```

---

## Example Usage

### cURL

```bash
curl -X POST https://emktactsx8.execute-api.us-east-1.amazonaws.com \
  -H 'Content-Type: application/json' \
  -d '{
    "home_team": "LAL",
    "away_team": "BOS",
    "features": {
      "home_rolling_win_pct": 0.65,
      "home_rolling_ppg": 110.5,
      "home_rolling_papg": 105.2,
      "home_rolling_margin": 5.3,
      "home_rest_days": 2,
      "home_back_to_back": 0,
      "away_rolling_win_pct": 0.58,
      "away_rolling_ppg": 108.3,
      "away_rolling_papg": 107.1,
      "away_rolling_margin": 1.2,
      "away_rest_days": 1,
      "away_back_to_back": 0,
      "month": 11,
      "day_of_week": 3,
      "is_weekend": 0,
      "season_phase": 0
    }
  }'
```

### Python

```python
import requests
import json

url = "https://emktactsx8.execute-api.us-east-1.amazonaws.com"

payload = {
    "home_team": "LAL",
    "away_team": "BOS",
    "features": {
        "home_rolling_win_pct": 0.65,
        "home_rolling_ppg": 110.5,
        "home_rolling_papg": 105.2,
        "home_rolling_margin": 5.3,
        "home_rest_days": 2,
        "home_back_to_back": 0,
        "away_rolling_win_pct": 0.58,
        "away_rolling_ppg": 108.3,
        "away_rolling_papg": 107.1,
        "away_rolling_margin": 1.2,
        "away_rest_days": 1,
        "away_back_to_back": 0,
        "month": 11,
        "day_of_week": 3,
        "is_weekend": 0,
        "season_phase": 0
    }
}

response = requests.post(url, json=payload)
prediction = response.json()

print(f"Predicted winner: {prediction['predicted_winner']}")
print(f"Home win probability: {prediction['home_win_probability']:.1%}")
print(f"Confidence: {prediction['confidence']:.1%}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const url = 'https://emktactsx8.execute-api.us-east-1.amazonaws.com';

const payload = {
  home_team: 'LAL',
  away_team: 'BOS',
  features: {
    home_rolling_win_pct: 0.65,
    home_rolling_ppg: 110.5,
    home_rolling_papg: 105.2,
    home_rolling_margin: 5.3,
    home_rest_days: 2,
    home_back_to_back: 0,
    away_rolling_win_pct: 0.58,
    away_rolling_ppg: 108.3,
    away_rolling_papg: 107.1,
    away_rolling_margin: 1.2,
    away_rest_days: 1,
    away_back_to_back: 0,
    month: 11,
    day_of_week: 3,
    is_weekend: 0,
    season_phase: 0
  }
};

axios.post(url, payload)
  .then(response => {
    const prediction = response.data;
    console.log(`Predicted winner: ${prediction.predicted_winner}`);
    console.log(`Home win probability: ${(prediction.home_win_probability * 100).toFixed(1)}%`);
    console.log(`Confidence: ${(prediction.confidence * 100).toFixed(1)}%`);
  })
  .catch(error => {
    console.error('Error:', error.response ? error.response.data : error.message);
  });
```

---

## Cost & Performance

### Pricing

- **Lambda:** $0.20 per 1M requests (first 1M free monthly)
- **API Gateway:** $1.00 per 1M requests (first 1M free monthly)
- **Total:** ~$0-3/month for typical usage

### Performance

- **Cold start:** ~200-300ms (no dependencies to load)
- **Warm request:** ~50-150ms
- **Throughput:** 1,000 concurrent requests
- **Memory:** 256MB (optimized for cost)

### Rate Limits

- **Default:** 10,000 requests/second
- **Burst:** 5,000 requests
- **No authentication required** (public endpoint)

---

## Model Information

### Training Data

- **Source:** NBA games 1993-2018 (training), 2018-2024 (testing)
- **Training set:** 34,788 games
- **Test set:** 8,697 games
- **Features:** 16 engineered features (rolling stats, rest days, temporal)

### Model Performance

- **Algorithm:** Logistic Regression (L2 regularization)
- **Test Accuracy:** 63.0%
- **AUC:** 0.659
- **Precision:** 0.646
- **Recall:** 0.758
- **F1 Score:** 0.698
- **Baseline (home win rate):** 59.4%
- **Improvement over baseline:** +3.6%

### Model Deployment

- **Format:** JSON coefficients (no sklearn dependency)
- **Size:** ~2KB
- **Update frequency:** Can be updated without redeploying Lambda
- **Version control:** Stored in S3 (`s3://nba-sim-raw-data-lake/ml-models/model_coefficients.json`)

---

## Troubleshooting

### Common Issues

**1. Missing features error**
```json
{"error": "Missing required features: ..."}
```
**Solution:** Ensure all 16 feature fields are included in the request.

**2. Lambda cold start timeout**
**Symptom:** First request takes >1 second
**Solution:** This is normal. Subsequent requests will be faster (~50-150ms).

**3. 500 Internal Server Error**
**Possible causes:**
- Model coefficients not found in S3
- IAM permissions issue (Lambda can't read S3)
- Invalid feature values (e.g., negative probabilities)

**Debug:** Check CloudWatch logs for detailed error messages.

---

## AWS Resources

### Lambda Function

- **Name:** `nba-prediction-api`
- **Runtime:** Python 3.11
- **Memory:** 256MB
- **Timeout:** 30 seconds
- **Role:** `nba-lambda-execution-role`
- **ARN:** `arn:aws:lambda:us-east-1:575734508327:function:nba-prediction-api`

### API Gateway

- **Name:** `nba-prediction-api`
- **Type:** HTTP API
- **ID:** `emktactsx8`
- **Stage:** `$default` (auto-deploy)

### S3 Storage

- **Bucket:** `nba-sim-raw-data-lake`
- **Model coefficients:** `ml-models/model_coefficients.json`
- **Trained models:** `ml-models/*.pkl` (for reference)

---

## Deployment

### Redeploy Lambda Function

```bash
cd /Users/ryanranft/nba-simulator-aws
bash scripts/aws/deploy_lambda_lightweight.sh
```

### Update Model

To update the model without redeploying Lambda:

```bash
# 1. Retrain model
python scripts/ml/train_models.py

# 2. Export new coefficients
python scripts/ml/export_model_coefficients.py

# 3. Lambda will pick up new coefficients automatically (cached for 5 minutes)
```

### Delete Resources

```bash
# Delete Lambda function
aws lambda delete-function --function-name nba-prediction-api

# Delete API Gateway
aws apigatewayv2 delete-api --api-id emktactsx8

# Delete IAM role (optional, may be used by other resources)
aws iam delete-role --role-name nba-lambda-execution-role
```

---

## Security

- **Public endpoint:** No authentication required
- **IAM role:** Minimum permissions (S3 read-only)
- **CORS:** Enabled (`Access-Control-Allow-Origin: *`)
- **Encryption:** API Gateway uses TLS 1.2+
- **Rate limiting:** API Gateway throttling enabled

**Note:** For production use with sensitive data, consider adding API keys or AWS IAM authentication.

---

## Support

**Issues:** [GitHub Issues](https://github.com/your-repo/issues)
**Documentation:** See `docs/phases/PHASE_6_ENHANCEMENTS.md`
**Cost monitoring:** `make check-costs`

---

*Last updated: October 3, 2025*
*API Version: 1.0*
