#!/bin/bash
# Deploy Lambda function for NBA prediction API

set -e

LAMBDA_NAME="nba-prediction-api"
LAMBDA_DIR="lambda/prediction_api"
DEPLOY_DIR="/tmp/lambda_deploy_${LAMBDA_NAME}"
ZIP_FILE="/tmp/${LAMBDA_NAME}.zip"
ROLE_NAME="nba-lambda-execution-role"
REGION="us-east-1"

echo "========================================"
echo "NBA PREDICTION API - LAMBDA DEPLOYMENT"
echo "========================================"
echo ""

# Step 1: Create deployment directory
echo "Step 1: Creating deployment package..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy Lambda function
cp "$LAMBDA_DIR/lambda_function.py" "$DEPLOY_DIR/"

# Install dependencies
echo "  Installing Python dependencies..."
pip install -r "$LAMBDA_DIR/requirements.txt" -t "$DEPLOY_DIR" --quiet

# Create ZIP
cd "$DEPLOY_DIR"
zip -r "$ZIP_FILE" . > /dev/null
cd - > /dev/null

echo "  ✓ Deployment package created: $(du -h $ZIP_FILE | cut -f1)"

# Step 2: Create IAM role if it doesn't exist
echo ""
echo "Step 2: Checking IAM role..."
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "  Creating IAM role: $ROLE_NAME"

    # Trust policy
    cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    ROLE_ARN=$(aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        --query 'Role.Arn' \
        --output text)

    # Attach policies
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

    echo "  ✓ IAM role created: $ROLE_ARN"
    echo "  Waiting 10 seconds for IAM role to propagate..."
    sleep 10
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
        --memory-size 512 \
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
        --output text

    echo "  ✓ Lambda function updated"
fi

# Step 4: Create API Gateway
echo ""
echo "Step 4: Setting up API Gateway..."

API_NAME="nba-prediction-api"
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='$API_NAME'].ApiId" --output text 2>/dev/null || echo "")

if [ -z "$API_ID" ]; then
    echo "  Creating HTTP API: $API_NAME"

    API_ID=$(aws apigatewayv2 create-api \
        --name "$API_NAME" \
        --protocol-type HTTP \
        --target "arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$LAMBDA_NAME" \
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
    --region "$REGION" \
    2>/dev/null || echo "  (Permission may already exist)"

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
echo "API Endpoint: $API_ENDPOINT"
echo "Lambda Function: $LAMBDA_NAME"
echo "Region: $REGION"
echo ""
echo "Test with:"
echo "curl -X POST $API_ENDPOINT \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"home_team\": \"LAL\","
echo "    \"away_team\": \"BOS\","
echo "    \"features\": {"
echo "      \"home_rolling_win_pct\": 0.65,"
echo "      \"home_rolling_ppg\": 110.5,"
echo "      \"home_rolling_papg\": 105.2,"
echo "      \"home_rolling_margin\": 5.3,"
echo "      \"home_rest_days\": 2,"
echo "      \"home_back_to_back\": 0,"
echo "      \"away_rolling_win_pct\": 0.58,"
echo "      \"away_rolling_ppg\": 108.3,"
echo "      \"away_rolling_papg\": 107.1,"
echo "      \"away_rolling_margin\": 1.2,"
echo "      \"away_rest_days\": 1,"
echo "      \"away_back_to_back\": 0,"
echo "      \"month\": 11,"
echo "      \"day_of_week\": 3,"
echo "      \"is_weekend\": 0,"
echo "      \"season_phase\": 0"
echo "    }"
echo "  }'"
echo ""
echo "Estimated cost: \$0-3/month (first 1M requests free, then \$1 per million)"
echo "========================================"