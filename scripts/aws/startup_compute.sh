#!/bin/bash
# Startup compute instances
# Companion to shutdown_compute.sh

set -e

echo "========================================="
echo "STARTUP COMPUTE INSTANCES"
echo "========================================="
echo ""

# Check current status
echo "Step 1: Checking stopped instances..."
echo ""

echo "EC2 Instances:"
EC2_STOPPED=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*nba*" "Name=instance-state-name,Values=stopped" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,Tags[?Key==`Name`].Value|[0]]' \
  --output text)

if [ -n "$EC2_STOPPED" ]; then
  echo "$EC2_STOPPED"
else
  echo "  No stopped EC2 instances"
fi

echo ""
echo "SageMaker Notebooks:"
SM_STOPPED=$(aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[?NotebookInstanceStatus==`Stopped`].[NotebookInstanceName,InstanceType]' \
  --output text)

if [ -n "$SM_STOPPED" ]; then
  echo "$SM_STOPPED"
else
  echo "  No stopped SageMaker notebooks"
fi

echo ""
echo "========================================="
echo "Step 2: Starting instances..."
echo ""

# Start EC2
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=nba-simulation-engine" "Name=instance-state-name,Values=stopped" \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text)

if [ -n "$INSTANCE_ID" ]; then
  echo "Starting EC2 instance: $INSTANCE_ID"
  aws ec2 start-instances --instance-ids $INSTANCE_ID --query 'StartingInstances[*].[InstanceId,CurrentState.Name]' --output table
  echo "✓ EC2 starting"
else
  echo "✓ No EC2 instances to start (may already be running)"
fi

echo ""

# Start SageMaker
NOTEBOOK_NAME=$(aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[?NotebookInstanceStatus==`Stopped`].NotebookInstanceName' \
  --output text | head -1)

if [ -n "$NOTEBOOK_NAME" ]; then
  echo "Starting SageMaker notebook: $NOTEBOOK_NAME"
  aws sagemaker start-notebook-instance --notebook-instance-name "$NOTEBOOK_NAME"
  echo "✓ SageMaker starting (takes 2-3 minutes)"
else
  echo "✓ No SageMaker notebooks to start (may already be running)"
fi

echo ""
echo "========================================="
echo "Step 3: Verification (waiting 30 seconds)..."
echo ""
sleep 30

echo "EC2 Status:"
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=nba-simulation-engine" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]' \
  --output table

echo ""
echo "SageMaker Status:"
aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[*].[NotebookInstanceName,NotebookInstanceStatus,Url]' \
  --output table

echo ""
echo "========================================="
echo "STARTUP COMPLETE"
echo "========================================="
echo ""
echo "Resources are starting up:"
echo "  - EC2: May take 1-2 minutes to be fully accessible"
echo "  - SageMaker: May take 2-3 minutes to be fully accessible"
echo ""
echo "To connect to EC2:"
echo "  ssh -i ~/.ssh/your-key.pem ec2-user@<public-ip>"
echo ""
echo "To access SageMaker:"
echo "  aws sagemaker create-presigned-notebook-instance-url --notebook-instance-name nba-ml-notebook"
echo ""
echo "To shutdown: bash scripts/aws/shutdown_compute.sh"
echo "========================================="