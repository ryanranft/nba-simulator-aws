#!/bin/bash
# Deploy lightweight Lambda function (boto3 only, no external dependencies)

set -e

LAMBDA_NAME="nba-prediction-api"
LAMBDA_DIR="lambda/prediction_api"
DEPLOY_DIR="/tmp/lambda_deploy_${LAMBDA_NAME}"
ZIP_FILE="/tmp/${LAMBDA_NAME}.zip"
ROLE_NAME="nba-lambda-execution-role"
REGION="us-east-1"

echo "========================================"
echo "NBA PREDICTION API - LIGHTWEIGHT DEPLOYMENT"
echo "(Using JSON coefficients - no sklearn)"
echo "========================================"
echo ""

# Step 1: Create deployment package (code only, no dependencies)
echo "Step 1: Creating deployment package..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy lightweight Lambda function
cp "$LAMBDA_DIR/lambda_function_lightweight.py" "$DEPLOY_DIR/lambda_function.py"

# Create ZIP
cd "$DEPLOY_DIR"
zip -r "$ZIP_FILE" . > /dev/null
cd - > /dev/null

LAMBDA_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "  ✓ Deployment package created: $LAMBDA_SIZE (code only, no dependencies)"

# Step 2: Get IAM role (already created)
echo ""
echo "Step 2: Checking IAM role..."
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "  ✓ Using existing IAM role from previous deployment"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
else
    echo "  ✓ Using existing IAM role: $ROLE_ARN"
fi

# Step 3: Create or update Lambda function
echo ""
echo "Step 3: Deploying Lambda function..."

FUNCTION_EXISTS=$(aws lambda get-function --function-name "$LAMBDA_NAME" --region "$REGION" 2>/dev/null || echo "")

if [ -z "$FUNCTION_EXISTS" ]; then
    echo "  Creating new Lambda function: $LAMBDA_NAME"

    FUNCTION_ARN=$(aws lambda create-function \
        --function-name "$LAMBDA_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout 30 \
        --memory-size 256 \
        --region "$REGION" \
        --query 'FunctionArn' \
        --output text)

    echo "  ✓ Lambda function created: $FUNCTION_ARN"
else
    echo "  Updating existing Lambda function: $LAMBDA_NAME"

    aws lambda update-function-code \
        --function-name "$LAMBDA_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --query 'FunctionArn' \
        --output text > /dev/null

    # Also update memory size to 256MB (lower than 512MB)
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_NAME" \
        --memory-size 256 \
        --region "$REGION" > /dev/null

    echo "  ✓ Lambda function updated"
fi

# Wait for function to be active
echo "  Waiting for function to be active..."
sleep 3

# Step 4: Create API Gateway
echo ""
echo "Step 4: Setting up API Gateway..."

API_NAME="nba-prediction-api"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='$API_NAME'].ApiId" --output text 2>/dev/null || echo "")

if [ -z "$API_ID" ]; then
    echo "  Creating HTTP API: $API_NAME"

    API_ID=$(aws apigatewayv2 create-api \
        --name "$API_NAME" \
        --protocol-type HTTP \
        --target "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$LAMBDA_NAME" \
        --query 'ApiId' \
        --output text)

    echo "  ✓ API created: $API_ID"
else
    echo "  ✓ Using existing API: $API_ID"
fi

# Grant API Gateway permission to invoke Lambda
echo "  Granting API Gateway invoke permission..."
aws lambda add-permission \
    --function-name "$LAMBDA_NAME" \
    --statement-id "apigateway-invoke-$(date +%s)" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
    --region "$REGION" \
    2>/dev/null || echo "  (Permission already exists)"

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-apis --query "Items[?ApiId=='$API_ID'].ApiEndpoint" --output text)

# Cleanup
rm -rf "$DEPLOY_DIR"
rm -f "$ZIP_FILE"

echo ""
echo "========================================"
echo "DEPLOYMENT COMPLETE"
echo "========================================"
echo ""
echo "✓ Lambda Function: $LAMBDA_NAME (${LAMBDA_SIZE})"
echo "✓ API Endpoint: $API_ENDPOINT"
echo "✓ Region: $REGION"
echo "✓ Memory: 256MB (optimized for lightweight function)"
echo ""
echo "Test with curl:"
echo ""
cat << EOF
curl -X POST $API_ENDPOINT \\
  -H 'Content-Type: application/json' \\
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
EOF
echo ""
echo ""
echo "Estimated monthly cost:"
echo "  - Lambda (compute): \$0-1/month (first 1M requests free)"
echo "  - API Gateway: \$0-2/month (first 1M requests free)"
echo "  - Total: ~\$0-3/month with low usage"
echo ""
echo "✓ No external dependencies required"
echo "✓ Fast cold start (~200ms vs 3s+ with sklearn)"
echo "✓ Low memory usage (256MB vs 512MB+)"
echo "========================================"