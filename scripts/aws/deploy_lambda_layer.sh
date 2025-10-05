#!/bin/bash
# Deploy Lambda function with separate layer for dependencies

set -e

LAMBDA_NAME="nba-prediction-api"
LAYER_NAME="nba-ml-dependencies"
LAMBDA_DIR="lambda/prediction_api"
LAYER_DIR="/tmp/lambda_layer_${LAYER_NAME}"
DEPLOY_DIR="/tmp/lambda_deploy_${LAMBDA_NAME}"
LAYER_ZIP="/tmp/${LAYER_NAME}.zip"
LAMBDA_ZIP="/tmp/${LAMBDA_NAME}.zip"
ROLE_NAME="nba-lambda-execution-role"
REGION="us-east-1"

echo "========================================"
echo "NBA PREDICTION API - LAMBDA DEPLOYMENT"
echo "(Using Lambda Layers for dependencies)"
echo "========================================"
echo ""

# Step 1: Create Lambda Layer with dependencies
echo "Step 1: Creating Lambda Layer with dependencies..."
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR/python"

# Install dependencies to layer
echo "  Installing numpy and scikit-learn..."
pip install numpy==1.24.3 scikit-learn==1.3.0 -t "$LAYER_DIR/python" --quiet --no-deps

# Add minimal scipy dependencies (scikit-learn needs these)
pip install scipy joblib threadpoolctl -t "$LAYER_DIR/python" --quiet --no-deps

# Create layer ZIP
cd "$LAYER_DIR"
zip -r "$LAYER_ZIP" . > /dev/null
cd - > /dev/null

LAYER_SIZE=$(du -h "$LAYER_ZIP" | cut -f1)
echo "  ✓ Layer package created: $LAYER_SIZE"

# Publish or update layer
echo "  Publishing Lambda Layer..."
LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --zip-file "fileb://$LAYER_ZIP" \
    --compatible-runtimes python3.11 \
    --region "$REGION" \
    --query 'LayerVersionArn' \
    --output text)

echo "  ✓ Layer published: $LAYER_VERSION_ARN"

# Step 2: Create minimal Lambda function package (code only)
echo ""
echo "Step 2: Creating Lambda function package..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy only Lambda function code (no dependencies)
cp "$LAMBDA_DIR/lambda_function.py" "$DEPLOY_DIR/"

# Create ZIP
cd "$DEPLOY_DIR"
zip -r "$LAMBDA_ZIP" . > /dev/null
cd - > /dev/null

LAMBDA_SIZE=$(du -h "$LAMBDA_ZIP" | cut -f1)
echo "  ✓ Function package created: $LAMBDA_SIZE (code only)"

# Step 3: Get or create IAM role
echo ""
echo "Step 3: Checking IAM role..."
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "  Using existing IAM role from previous deployment"
    ROLE_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/$ROLE_NAME"
else
    echo "  ✓ Using existing IAM role: $ROLE_ARN"
fi

# Step 4: Create or update Lambda function
echo ""
echo "Step 4: Deploying Lambda function..."

FUNCTION_EXISTS=$(aws lambda get-function --function-name "$LAMBDA_NAME" --region "$REGION" 2>/dev/null || echo "")

if [ -z "$FUNCTION_EXISTS" ]; then
    echo "  Creating new Lambda function: $LAMBDA_NAME"

    FUNCTION_ARN=$(aws lambda create-function \
        --function-name "$LAMBDA_NAME" \
        --runtime python3.11 \
        --role "$ROLE_ARN" \
        --handler lambda_function.lambda_handler \
        --zip-file "fileb://$LAMBDA_ZIP" \
        --timeout 30 \
        --memory-size 512 \
        --layers "$LAYER_VERSION_ARN" \
        --region "$REGION" \
        --query 'FunctionArn' \
        --output text)

    echo "  ✓ Lambda function created: $FUNCTION_ARN"
else
    echo "  Updating existing Lambda function: $LAMBDA_NAME"

    aws lambda update-function-code \
        --function-name "$LAMBDA_NAME" \
        --zip-file "fileb://$LAMBDA_ZIP" \
        --region "$REGION" \
        --query 'FunctionArn' \
        --output text > /dev/null

    # Update layer
    aws lambda update-function-configuration \
        --function-name "$LAMBDA_NAME" \
        --layers "$LAYER_VERSION_ARN" \
        --region "$REGION" > /dev/null

    echo "  ✓ Lambda function updated"
fi

# Step 5: Create API Gateway
echo ""
echo "Step 5: Setting up API Gateway..."

API_NAME="nba-prediction-api"
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='$API_NAME'].ApiId" --output text 2>/dev/null || echo "")

if [ -z "$API_ID" ]; then
    echo "  Creating HTTP API: $API_NAME"

    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
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
    --region "$REGION" \
    2>/dev/null || echo "  (Permission already exists)"

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-apis --query "Items[?ApiId=='$API_ID'].ApiEndpoint" --output text)

# Cleanup
rm -rf "$DEPLOY_DIR" "$LAYER_DIR"
rm -f "$LAMBDA_ZIP" "$LAYER_ZIP"

echo ""
echo "========================================"
echo "DEPLOYMENT COMPLETE"
echo "========================================"
echo ""
echo "✓ Lambda Layer: $LAYER_NAME ($LAYER_SIZE)"
echo "✓ Lambda Function: $LAMBDA_NAME ($LAMBDA_SIZE)"
echo "✓ API Endpoint: $API_ENDPOINT"
echo "✓ Region: $REGION"
echo ""
echo "Test with curl:"
echo ""
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
echo "Estimated monthly cost:"
echo "  - Lambda: \$0-1/month (first 1M requests free)"
echo "  - API Gateway: \$0-2/month (first 1M requests free)"
echo "  - Total: ~\$0-3/month with low usage"
echo ""
echo "========================================"