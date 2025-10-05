#!/bin/bash
# Deploy Lambda function using container image (no size limits)

set -e

LAMBDA_NAME="nba-prediction-api"
LAMBDA_DIR="lambda/prediction_api"
ROLE_NAME="nba-lambda-execution-role"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="nba-prediction-api"
IMAGE_TAG="latest"

echo "========================================"
echo "NBA PREDICTION API - CONTAINER DEPLOYMENT"
echo "(Using Lambda Container Images - no size limit)"
echo "========================================"
echo ""

# Step 1: Create ECR repository if it doesn't exist
echo "Step 1: Setting up ECR repository..."
ECR_REPO_URI=$(aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$REGION" --query 'repositories[0].repositoryUri' --output text 2>/dev/null || echo "")

if [ -z "$ECR_REPO_URI" ]; then
    echo "  Creating ECR repository: $ECR_REPO_NAME"
    ECR_REPO_URI=$(aws ecr create-repository \
        --repository-name "$ECR_REPO_NAME" \
        --region "$REGION" \
        --query 'repository.repositoryUri' \
        --output text)
    echo "  ✓ ECR repository created: $ECR_REPO_URI"
else
    echo "  ✓ Using existing ECR repository: $ECR_REPO_URI"
fi

# Step 2: Build Docker image
echo ""
echo "Step 2: Building Docker image..."
cd "$LAMBDA_DIR"
docker build --platform linux/amd64 -t "${ECR_REPO_NAME}:${IMAGE_TAG}" .
cd - > /dev/null
echo "  ✓ Docker image built"

# Step 3: Tag and push to ECR
echo ""
echo "Step 3: Pushing image to ECR..."
echo "  Logging into ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "  Tagging image..."
docker tag "${ECR_REPO_NAME}:${IMAGE_TAG}" "${ECR_REPO_URI}:${IMAGE_TAG}"

echo "  Pushing image to ECR (this may take a few minutes)..."
docker push "${ECR_REPO_URI}:${IMAGE_TAG}"
echo "  ✓ Image pushed to ECR"

# Step 4: Get or create IAM role
echo ""
echo "Step 4: Checking IAM role..."
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ROLE_ARN" ]; then
    echo "  Using IAM role from previous deployment"
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
else
    echo "  ✓ Using existing IAM role: $ROLE_ARN"
fi

# Step 5: Create or update Lambda function
echo ""
echo "Step 5: Deploying Lambda function..."

FUNCTION_EXISTS=$(aws lambda get-function --function-name "$LAMBDA_NAME" --region "$REGION" 2>/dev/null || echo "")

if [ -z "$FUNCTION_EXISTS" ]; then
    echo "  Creating new Lambda function: $LAMBDA_NAME"

    FUNCTION_ARN=$(aws lambda create-function \
        --function-name "$LAMBDA_NAME" \
        --package-type Image \
        --code ImageUri="${ECR_REPO_URI}:${IMAGE_TAG}" \
        --role "$ROLE_ARN" \
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
        --image-uri "${ECR_REPO_URI}:${IMAGE_TAG}" \
        --region "$REGION" \
        --query 'FunctionArn' \
        --output text > /dev/null

    echo "  ✓ Lambda function updated"
fi

# Wait for function to be active
echo "  Waiting for function to be active..."
aws lambda wait function-updated --function-name "$LAMBDA_NAME" --region "$REGION"

# Step 6: Create API Gateway
echo ""
echo "Step 6: Setting up API Gateway..."

API_NAME="nba-prediction-api"
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

echo ""
echo "========================================"
echo "DEPLOYMENT COMPLETE"
echo "========================================"
echo ""
echo "✓ ECR Repository: $ECR_REPO_URI"
echo "✓ Lambda Function: $LAMBDA_NAME"
echo "✓ API Endpoint: $API_ENDPOINT"
echo "✓ Region: $REGION"
echo ""
echo "Test with curl:"
echo ""
cat << 'EOF'
curl -X POST $API_ENDPOINT \
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
EOF
echo ""
echo ""
echo "Estimated monthly cost:"
echo "  - Lambda (compute): \$0-1/month (first 1M requests free)"
echo "  - API Gateway: \$0-2/month (first 1M requests free)"
echo "  - ECR storage: \$0.10/month per GB (~\$0.20/month)"
echo "  - Total: ~\$0.20-3/month with low usage"
echo ""
echo "========================================"