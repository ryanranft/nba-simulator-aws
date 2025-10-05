#!/usr/bin/env python3
"""
Lightweight AWS Lambda function for NBA game predictions
Uses JSON model coefficients (no scikit-learn required)
"""

import json
import boto3
import math
from datetime import datetime

# S3 configuration
S3_BUCKET = 'nba-sim-raw-data-lake'
S3_MODELS_PREFIX = 'ml-models'

# Global variables for model caching
model_coefficients = None
model_loaded_at = None

def load_model_coefficients():
    """Load model coefficients from S3 (cached for 5 minutes)"""
    global model_coefficients, model_loaded_at

    # Cache for 5 minutes
    if model_coefficients is not None and model_loaded_at is not None:
        age_seconds = (datetime.now() - model_loaded_at).total_seconds()
        if age_seconds < 300:
            return model_coefficients

    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=S3_BUCKET, Key=f'{S3_MODELS_PREFIX}/model_coefficients.json')
    model_coefficients = json.loads(obj['Body'].read().decode('utf-8'))
    model_loaded_at = datetime.now()

    return model_coefficients

def sigmoid(z):
    """Sigmoid activation function"""
    return 1 / (1 + math.exp(-z))

def predict_logistic_regression(features_dict):
    """
    Manual logistic regression prediction (no sklearn needed)
    P(y=1) = sigmoid(X * coef + intercept)
    """
    # Load model parameters
    model = load_model_coefficients()

    # Validate features
    missing = [f for f in model['feature_names'] if f not in features_dict]
    if missing:
        raise ValueError(f"Missing required features: {', '.join(missing)}")

    # Convert features to array (in correct order)
    features = [features_dict[name] for name in model['feature_names']]

    # Standardize features (z-score scaling)
    features_scaled = [
        (x - mean) / scale
        for x, mean, scale in zip(features, model['scaler_mean'], model['scaler_scale'])
    ]

    # Compute logit: z = X * coef + intercept
    logit = sum(x * coef for x, coef in zip(features_scaled, model['coefficients']))
    logit += model['intercept']

    # Apply sigmoid to get probability
    probability = sigmoid(logit)

    # Prediction: 1 if P(y=1) >= 0.5, else 0
    prediction = 1 if probability >= 0.5 else 0

    return {
        'home_win_probability': float(probability),
        'away_win_probability': float(1 - probability),
        'predicted_winner': 'home' if prediction == 1 else 'away',
        'confidence': float(max(probability, 1 - probability)),
        'model_used': model['model_type'],
        'model_accuracy': model['accuracy'],
        'model_auc': model['auc'],
        'prediction_timestamp': datetime.now().isoformat()
    }

def lambda_handler(event, context):
    """
    AWS Lambda handler for API Gateway requests

    Expected input (POST /predict):
    {
        "home_team": "LAL",
        "away_team": "BOS",
        "features": {
            "home_rolling_win_pct": 0.65,
            ... (all 16 features)
        }
    }
    """

    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        # Validate request
        if 'features' not in body:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required field: features',
                    'required_features': [
                        'home_rolling_win_pct', 'home_rolling_ppg', 'home_rolling_papg',
                        'home_rolling_margin', 'home_rest_days', 'home_back_to_back',
                        'away_rolling_win_pct', 'away_rolling_ppg', 'away_rolling_papg',
                        'away_rolling_margin', 'away_rest_days', 'away_back_to_back',
                        'month', 'day_of_week', 'is_weekend', 'season_phase'
                    ],
                    'example': {
                        'home_team': 'LAL',
                        'away_team': 'BOS',
                        'features': {
                            'home_rolling_win_pct': 0.65,
                            'home_rolling_ppg': 110.5,
                            'home_rolling_papg': 105.2,
                            'home_rolling_margin': 5.3,
                            'home_rest_days': 2,
                            'home_back_to_back': 0,
                            'away_rolling_win_pct': 0.58,
                            'away_rolling_ppg': 108.3,
                            'away_rolling_papg': 107.1,
                            'away_rolling_margin': 1.2,
                            'away_rest_days': 1,
                            'away_back_to_back': 0,
                            'month': 11,
                            'day_of_week': 3,
                            'is_weekend': 0,
                            'season_phase': 0
                        }
                    }
                })
            }

        # Generate prediction
        prediction_result = predict_logistic_regression(body['features'])

        # Add metadata
        prediction_result['home_team'] = body.get('home_team', 'Unknown')
        prediction_result['away_team'] = body.get('away_team', 'Unknown')

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(prediction_result)
        }

    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

    except Exception as e:
        print(f"Error: {str(e)}")  # CloudWatch logs
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'home_team': 'LAL',
        'away_team': 'BOS',
        'features': {
            'home_rolling_win_pct': 0.65,
            'home_rolling_ppg': 110.5,
            'home_rolling_papg': 105.2,
            'home_rolling_margin': 5.3,
            'home_rest_days': 2,
            'home_back_to_back': 0,
            'away_rolling_win_pct': 0.58,
            'away_rolling_ppg': 108.3,
            'away_rolling_papg': 107.1,
            'away_rolling_margin': 1.2,
            'away_rest_days': 1,
            'away_back_to_back': 0,
            'month': 11,
            'day_of_week': 3,
            'is_weekend': 0,
            'season_phase': 0
        }
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))