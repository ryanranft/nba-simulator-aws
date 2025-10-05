#!/bin/bash
# Shutdown compute instances to save costs
# Workflow #37

set -e

echo "========================================="
echo "SHUTDOWN COMPUTE INSTANCES"
echo "========================================="
echo ""

# Check current status
echo "Step 1: Checking running instances..."
echo ""

echo "EC2 Instances:"
EC2_RUNNING=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*nba*" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,Tags[?Key==`Name`].Value|[0]]' \
  --output text)

if [ -n "$EC2_RUNNING" ]; then
  echo "$EC2_RUNNING"
else
  echo "  No running EC2 instances"
fi

echo ""
echo "SageMaker Notebooks:"
SM_RUNNING=$(aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[?NotebookInstanceStatus==`InService`].[NotebookInstanceName,InstanceType]' \
  --output text)

if [ -n "$SM_RUNNING" ]; then
  echo "$SM_RUNNING"
else
  echo "  No running SageMaker notebooks"
fi

echo ""
echo "========================================="
echo "Step 2: Stopping instances..."
echo ""

# Stop EC2
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=nba-simulation-engine" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text)

if [ -n "$INSTANCE_ID" ]; then
  echo "Stopping EC2 instance: $INSTANCE_ID"
  aws ec2 stop-instances --instance-ids $INSTANCE_ID --query 'StoppingInstances[*].[InstanceId,CurrentState.Name]' --output table
  echo "✓ EC2 stopping (saves ~\$6.59/month)"
else
  echo "✓ No EC2 instances to stop"
fi

echo ""

# Stop SageMaker
NOTEBOOK_NAME=$(aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[?NotebookInstanceStatus==`InService`].NotebookInstanceName' \
  --output text | head -1)

if [ -n "$NOTEBOOK_NAME" ]; then
  echo "Stopping SageMaker notebook: $NOTEBOOK_NAME"
  aws sagemaker stop-notebook-instance --notebook-instance-name "$NOTEBOOK_NAME"
  echo "✓ SageMaker stopping (saves ~\$50/month if running 24/7)"
else
  echo "✓ No SageMaker notebooks to stop"
fi

echo ""
echo "========================================="
echo "Step 3: Verification (waiting 30 seconds)..."
echo ""
sleep 30

echo "EC2 Status:"
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=nba-simulation-engine" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' \
  --output table

echo ""
echo "SageMaker Status:"
aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[*].[NotebookInstanceName,NotebookInstanceStatus]' \
  --output table

echo ""
echo "========================================="
echo "SHUTDOWN COMPLETE"
echo "========================================="
echo ""
echo "Cost savings: ~\$6-56/month depending on usage"
echo ""
echo "Still running:"
echo "  - S3 Storage: \$2.74/month"
echo "  - RDS Database: \$29/month"
echo "  - Lambda/API: ~\$0.20/month"
echo ""
echo "To restart: bash scripts/aws/startup_compute.sh"
echo "========================================="