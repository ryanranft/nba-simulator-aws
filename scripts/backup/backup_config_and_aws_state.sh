#!/bin/bash

###############################################################################
# Configuration and AWS State Backup Script
#
# Purpose: Backup configuration files and document AWS infrastructure state
# Usage: bash scripts/backup/backup_config_and_aws_state.sh
# Author: Claude Code (NBA Simulator Project)
# Date: October 30, 2025
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
BACKUP_DIR="/Users/ryanranft/nba-simulator-aws/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONFIG_BACKUP_DIR="${BACKUP_DIR}/config_${TIMESTAMP}"
AWS_STATE_FILE="${CONFIG_BACKUP_DIR}/aws_state.txt"
S3_BUCKET="nba-sim-raw-data-lake"

###############################################################################
# Pre-flight Checks
###############################################################################

log_info "Starting configuration and AWS state backup..."

# Create backup directories
mkdir -p "$CONFIG_BACKUP_DIR"

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

log_success "Pre-flight checks passed"

###############################################################################
# Backup Configuration Files
###############################################################################

log_info "Backing up configuration files..."

# Copy .env.example (actual .env is not in repo, as it should be)
if [[ -f ".env.example" ]]; then
    cp .env.example "${CONFIG_BACKUP_DIR}/.env.example"
    log_success "Copied .env.example"
fi

# Copy configuration YAML files
if [[ -d "config" ]]; then
    cp -r config "${CONFIG_BACKUP_DIR}/config"
    log_success "Copied config/ directory"
fi

# Copy inventory files
if [[ -d "inventory" ]]; then
    cp -r inventory "${CONFIG_BACKUP_DIR}/inventory"
    log_success "Copied inventory/ directory"
fi

# Copy pyproject.toml
if [[ -f "pyproject.toml" ]]; then
    cp pyproject.toml "${CONFIG_BACKUP_DIR}/pyproject.toml"
    log_success "Copied pyproject.toml"
fi

# Copy requirements files
if [[ -f "requirements.txt" ]]; then
    cp requirements.txt "${CONFIG_BACKUP_DIR}/requirements.txt"
    log_success "Copied requirements.txt"
fi

if [[ -f "requirements-dev.txt" ]]; then
    cp requirements-dev.txt "${CONFIG_BACKUP_DIR}/requirements-dev.txt"
    log_success "Copied requirements-dev.txt"
fi

# Copy Makefile
if [[ -f "Makefile" ]]; then
    cp Makefile "${CONFIG_BACKUP_DIR}/Makefile"
    log_success "Copied Makefile"
fi

# Copy .gitignore
if [[ -f ".gitignore" ]]; then
    cp .gitignore "${CONFIG_BACKUP_DIR}/.gitignore"
    log_success "Copied .gitignore"
fi

# Copy pre-commit configuration
if [[ -f ".pre-commit-config.yaml" ]]; then
    cp .pre-commit-config.yaml "${CONFIG_BACKUP_DIR}/.pre-commit-config.yaml"
    log_success "Copied .pre-commit-config.yaml"
fi

log_success "Configuration files backed up"

###############################################################################
# Document AWS State
###############################################################################

log_info "Documenting AWS infrastructure state..."

cat > "$AWS_STATE_FILE" << 'EOF'
################################################################################
# AWS Infrastructure State Snapshot
# NBA Simulator AWS Project
# Timestamp: TIMESTAMP_PLACEHOLDER
################################################################################

EOF

# Replace timestamp
sed -i.bak "s/TIMESTAMP_PLACEHOLDER/$(date '+%Y-%m-%d %H:%M:%S')/g" "$AWS_STATE_FILE"
rm -f "${AWS_STATE_FILE}.bak"

# Get AWS account ID and region
log_info "Getting AWS account info..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "N/A")
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

cat >> "$AWS_STATE_FILE" << EOF
## AWS Account Information
- Account ID: $AWS_ACCOUNT_ID
- Region: $AWS_REGION

EOF

# S3 Buckets
log_info "Documenting S3 buckets..."
cat >> "$AWS_STATE_FILE" << 'EOF'
## S3 Buckets

EOF

aws s3 ls | while read -r line; do
    bucket_name=$(echo "$line" | awk '{print $3}')
    if [[ "$bucket_name" == *"nba"* ]] || [[ "$bucket_name" == *"sim"* ]]; then
        bucket_size=$(aws s3 ls "s3://${bucket_name}" --recursive --summarize 2>/dev/null | grep "Total Size" | awk '{print $3}' || echo "0")
        bucket_files=$(aws s3 ls "s3://${bucket_name}" --recursive --summarize 2>/dev/null | grep "Total Objects" | awk '{print $3}' || echo "0")

        # Convert size to human readable
        if [[ $bucket_size -gt 0 ]]; then
            size_gb=$(echo "scale=2; $bucket_size / 1024 / 1024 / 1024" | bc)
        else
            size_gb="0"
        fi

        echo "### $bucket_name" >> "$AWS_STATE_FILE"
        echo "- Files: $bucket_files" >> "$AWS_STATE_FILE"
        echo "- Size: ${size_gb} GB" >> "$AWS_STATE_FILE"
        echo "" >> "$AWS_STATE_FILE"
    fi
done

# RDS Instances
log_info "Documenting RDS instances..."
cat >> "$AWS_STATE_FILE" << 'EOF'
## RDS Database Instances

EOF

aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceClass,Engine,EngineVersion,DBInstanceStatus,Endpoint.Address,Endpoint.Port,AllocatedStorage]' --output text 2>/dev/null | while read -r line; do
    echo "### Database Instance" >> "$AWS_STATE_FILE"
    echo "$line" | awk '{
        print "- Identifier: " $1
        print "- Class: " $2
        print "- Engine: " $3 " " $4
        print "- Status: " $5
        print "- Endpoint: " $6 ":" $7
        print "- Storage: " $8 " GB"
        print ""
    }' >> "$AWS_STATE_FILE"
done || echo "No RDS instances found or unable to describe" >> "$AWS_STATE_FILE"

# EC2 Instances
log_info "Documenting EC2 instances..."
cat >> "$AWS_STATE_FILE" << 'EOF'

## EC2 Instances

EOF

aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,PublicDnsName,Tags[?Key==`Name`].Value|[0]]' --output text 2>/dev/null | while read -r line; do
    if [[ ! -z "$line" ]]; then
        echo "### EC2 Instance" >> "$AWS_STATE_FILE"
        echo "$line" | awk '{
            print "- Instance ID: " $1
            print "- Type: " $2
            print "- State: " $3
            print "- Public DNS: " $4
            print "- Name: " $5
            print ""
        }' >> "$AWS_STATE_FILE"
    fi
done

instance_count=$(aws ec2 describe-instances --query 'Reservations[*].Instances[*]' --output text 2>/dev/null | wc -l)
if [[ $instance_count -eq 0 ]]; then
    echo "No EC2 instances found" >> "$AWS_STATE_FILE"
    echo "" >> "$AWS_STATE_FILE"
fi

# Lambda Functions
log_info "Documenting Lambda functions..."
cat >> "$AWS_STATE_FILE" << 'EOF'

## Lambda Functions

EOF

aws lambda list-functions --query 'Functions[*].[FunctionName,Runtime,MemorySize,Timeout,LastModified]' --output text 2>/dev/null | while read -r line; do
    echo "### Lambda Function" >> "$AWS_STATE_FILE"
    echo "$line" | awk '{
        print "- Name: " $1
        print "- Runtime: " $2
        print "- Memory: " $3 " MB"
        print "- Timeout: " $4 " seconds"
        print "- Last Modified: " $5
        print ""
    }' >> "$AWS_STATE_FILE"
done || echo "No Lambda functions found" >> "$AWS_STATE_FILE"

# Glue Databases and Crawlers
log_info "Documenting Glue resources..."
cat >> "$AWS_STATE_FILE" << 'EOF'

## AWS Glue Resources

### Glue Databases
EOF

aws glue get-databases --query 'DatabaseList[*].[Name,Description,CreateTime]' --output text 2>/dev/null | while read -r line; do
    echo "$line" | awk '{
        print "- " $1 " (Created: " $3 ")"
    }' >> "$AWS_STATE_FILE"
done || echo "No Glue databases found" >> "$AWS_STATE_FILE"

cat >> "$AWS_STATE_FILE" << 'EOF'

### Glue Crawlers
EOF

aws glue get-crawlers --query 'Crawlers[*].[Name,State,LastCrawl.Status]' --output text 2>/dev/null | while read -r line; do
    echo "$line" | awk '{
        print "- " $1 " (State: " $2 ", Last Status: " $3 ")"
    }' >> "$AWS_STATE_FILE"
done || echo "No Glue crawlers found" >> "$AWS_STATE_FILE"

# CloudWatch Alarms
log_info "Documenting CloudWatch alarms..."
cat >> "$AWS_STATE_FILE" << 'EOF'

## CloudWatch Alarms

EOF

aws cloudwatch describe-alarms --query 'MetricAlarms[*].[AlarmName,StateValue,MetricName]' --output text 2>/dev/null | while read -r line; do
    echo "$line" | awk '{
        print "- " $1 " (State: " $2 ", Metric: " $3 ")"
    }' >> "$AWS_STATE_FILE"
done || echo "No CloudWatch alarms found" >> "$AWS_STATE_FILE"

# SageMaker Resources
log_info "Documenting SageMaker resources..."
cat >> "$AWS_STATE_FILE" << 'EOF'

## SageMaker Resources

### Notebook Instances
EOF

aws sagemaker list-notebook-instances --query 'NotebookInstances[*].[NotebookInstanceName,InstanceType,NotebookInstanceStatus]' --output text 2>/dev/null | while read -r line; do
    echo "$line" | awk '{
        print "- " $1 " (Type: " $2 ", Status: " $3 ")"
    }' >> "$AWS_STATE_FILE"
done || echo "No SageMaker notebook instances found" >> "$AWS_STATE_FILE"

cat >> "$AWS_STATE_FILE" << 'EOF'

### Training Jobs (Last 10)
EOF

aws sagemaker list-training-jobs --max-results 10 --query 'TrainingJobSummaries[*].[TrainingJobName,TrainingJobStatus,CreationTime]' --output text 2>/dev/null | while read -r line; do
    echo "$line" | awk '{
        print "- " $1 " (Status: " $2 ", Created: " $3 ")"
    }' >> "$AWS_STATE_FILE"
done || echo "No SageMaker training jobs found" >> "$AWS_STATE_FILE"

# Cost Information
log_info "Getting cost information..."
cat >> "$AWS_STATE_FILE" << 'EOF'

## Cost Information

### Current Month (Estimated)
EOF

# Get current month costs
START_DATE=$(date -u +"%Y-%m-01")
END_DATE=$(date -u +"%Y-%m-%d")

aws ce get-cost-and-usage \
    --time-period Start=${START_DATE},End=${END_DATE} \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --query 'ResultsByTime[*].[TimePeriod.Start,Groups[*].[Keys[0],Metrics.UnblendedCost.Amount]]' \
    --output text 2>/dev/null >> "$AWS_STATE_FILE" || echo "Unable to retrieve cost information" >> "$AWS_STATE_FILE"

log_success "AWS state documented"

###############################################################################
# Create Archive
###############################################################################

log_info "Creating configuration archive..."

CONFIG_ARCHIVE="${BACKUP_DIR}/config_backup_${TIMESTAMP}.tar.gz"
tar -czf "$CONFIG_ARCHIVE" -C "$BACKUP_DIR" "config_${TIMESTAMP}"

CONFIG_SIZE=$(du -h "$CONFIG_ARCHIVE" | cut -f1)
log_success "Configuration archive created: $CONFIG_SIZE"

###############################################################################
# Upload to S3
###############################################################################

log_info "Uploading configuration backup to S3..."

aws s3 cp "$CONFIG_ARCHIVE" \
    "s3://${S3_BUCKET}/backups/config/config_backup_${TIMESTAMP}.tar.gz" \
    --storage-class STANDARD_IA

log_success "Configuration backup uploaded to S3"

###############################################################################
# Generate Checksum
###############################################################################

log_info "Generating checksum..."

if command -v shasum &> /dev/null; then
    shasum -a 256 "$CONFIG_ARCHIVE" > "${CONFIG_ARCHIVE}.sha256"
elif command -v sha256sum &> /dev/null; then
    sha256sum "$CONFIG_ARCHIVE" > "${CONFIG_ARCHIVE}.sha256"
fi

log_success "Checksum generated"

###############################################################################
# Summary
###############################################################################

cat << EOF

################################################################################
# CONFIGURATION BACKUP COMPLETE
################################################################################

Timestamp:        $(date '+%Y-%m-%d %H:%M:%S')

Local Files Created:
- Config Directory: $CONFIG_BACKUP_DIR
- AWS State Doc:    $AWS_STATE_FILE
- Archive:          $CONFIG_ARCHIVE ($CONFIG_SIZE)
- Checksum:         ${CONFIG_ARCHIVE}.sha256

S3 Files Uploaded:
- s3://${S3_BUCKET}/backups/config/config_backup_${TIMESTAMP}.tar.gz

Files Backed Up:
- .env.example
- config/ directory
- inventory/ directory
- pyproject.toml
- requirements.txt
- requirements-dev.txt
- Makefile
- .gitignore
- .pre-commit-config.yaml

AWS Resources Documented:
- S3 Buckets
- RDS Instances
- EC2 Instances
- Lambda Functions
- Glue Resources
- CloudWatch Alarms
- SageMaker Resources
- Cost Information

################################################################################

EOF

log_success "Configuration and AWS state backup completed successfully!"
log_info "AWS state document: $AWS_STATE_FILE"
log_info "Configuration archive: $CONFIG_ARCHIVE"

exit 0
