#!/usr/bin/env python3
"""
AWS Lambda function for NBA game predictions
Loads model from S3 and returns predictions via API Gateway
"""

import json
import boto3
import pickle
import numpy as np
from io import BytesIO
from datetime import datetime

# S3 configuration
S3_BUCKET = 'nba-sim-raw-data-lake'
S3_MODELS_PREFIX = 'ml-models'

# Global variables for model caching (Lambda keeps these between invocations)
model = None
scaler = None
model_loaded_at = None

def load_model_from_s3():
    """Load trained model and scaler from S3 (with caching)"""
    global model, scaler, model_loaded_at

    # Cache model for 5 minutes to reduce S3 calls
    if model is not None and model_loaded_at is not None:
        age_seconds = (datetime.now() - model_loaded_at).total_seconds()
        if age_seconds < 300:  # 5 minutes
            return model, scaler

    s3 = boto3.client('s3')

    # Load best model (Logistic Regression - 63% accuracy)
    model_key = f'{S3_MODELS_PREFIX}/logistic_regression.pkl'
    model_obj = s3.get_object(Bucket=S3_BUCKET, Key=model_key)
    model = pickle.load(BytesIO(model_obj['Body'].read()))

    # Load scaler
    scaler_key = f'{S3_MODELS_PREFIX}/scaler.pkl'
    scaler_obj = s3.get_object(Bucket=S3_BUCKET, Key=scaler_key)
    scaler = pickle.load(BytesIO(scaler_obj['Body'].read()))

    model_loaded_at = datetime.now()

    return model, scaler

def validate_features(features):
    """Validate that all required features are present"""
    required_features = [
        'home_rolling_win_pct', 'home_rolling_ppg', 'home_rolling_papg',
        'home_rolling_margin', 'home_rest_days', 'home_back_to_back',
        'away_rolling_win_pct', 'away_rolling_ppg', 'away_rolling_papg',
        'away_rolling_margin', 'away_rest_days', 'away_back_to_back',
        'month', 'day_of_week', 'is_weekend', 'season_phase'
    ]

    missing = [f for f in required_features if f not in features]
    if missing:
        return False, f"Missing required features: {', '.join(missing)}"

    return True, None

def predict(features_dict):
    """Generate prediction from feature dictionary"""
    # Load model
    model, scaler = load_model_from_s3()

    # Validate features
    valid, error = validate_features(features_dict)
    if not valid:
        raise ValueError(error)

    # Convert to numpy array (preserve feature order)
    feature_names = [
        'home_rolling_win_pct', 'home_rolling_ppg', 'home_rolling_papg',
        'home_rolling_margin', 'home_rest_days', 'home_back_to_back',
        'away_rolling_win_pct', 'away_rolling_ppg', 'away_rolling_papg',
        'away_rolling_margin', 'away_rest_days', 'away_back_to_back',
        'month', 'day_of_week', 'is_weekend', 'season_phase'
    ]

    features_array = np.array([[features_dict[f] for f in feature_names]])

    # Scale and predict
    features_scaled = scaler.transform(features_array)
    probability = model.predict_proba(features_scaled)[0, 1]  # Probability home wins
    prediction = model.predict(features_scaled)[0]

    return {
        'home_win_probability': float(probability),
        'away_win_probability': float(1 - probability),
        'predicted_winner': 'home' if prediction == 1 else 'away',
        'confidence': float(max(probability, 1 - probability)),
        'model_used': 'logistic_regression',
        'model_accuracy': 0.630,
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
            "home_rolling_ppg": 110.5,
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

        # Extract features
        if 'features' not in body:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required field: features',
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
        prediction_result = predict(body['features'])

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
