#!/bin/bash
#
# SNS Topics Setup Script
#
# Creates and configures SNS topics for NBA Simulator CloudWatch alerts.
# Subscribes email endpoints for notifications.
#
# Phase 0.0020: Monitoring & Observability
#
# Usage:
#   bash scripts/monitoring/cloudwatch/setup_sns_topics.sh create
#   bash scripts/monitoring/cloudwatch/setup_sns_topics.sh delete
#   bash scripts/monitoring/cloudwatch/setup_sns_topics.sh list
#

set -e  # Exit on error

# Configuration
TOPIC_NAME="nba-simulator-alerts"
REGION="us-east-1"
CONFIG_FILE="config/cloudwatch_config.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Extract email from config (if using Python to parse YAML)
get_email_from_config() {
    # Simple extraction - assumes format: - email@example.com
    grep -A 1 "email_endpoints:" "$CONFIG_FILE" | grep -E "^\s+-\s+" | sed 's/.*- //' | head -1
}

# Create SNS topic
create_topic() {
    log_info "Creating SNS topic: $TOPIC_NAME"

    # Create topic
    TOPIC_ARN=$(aws sns create-topic \
        --name "$TOPIC_NAME" \
        --region "$REGION" \
        --output text \
        --query 'TopicArn' 2>/dev/null)

    if [ $? -eq 0 ]; then
        log_info "SNS topic created successfully"
        log_info "Topic ARN: $TOPIC_ARN"
    else
        log_error "Failed to create SNS topic"
        exit 1
    fi

    # Extract email from config
    EMAIL=$(get_email_from_config)

    if [ -z "$EMAIL" ] || [ "$EMAIL" == "ryanranft@example.com" ]; then
        log_warn "No valid email configured in $CONFIG_FILE"
        echo ""
        read -p "Enter email address for alerts: " EMAIL
    fi

    if [ -n "$EMAIL" ]; then
        log_info "Subscribing email: $EMAIL"

        # Subscribe email
        SUBSCRIPTION_ARN=$(aws sns subscribe \
            --topic-arn "$TOPIC_ARN" \
            --protocol email \
            --notification-endpoint "$EMAIL" \
            --region "$REGION" \
            --output text \
            --query 'SubscriptionArn' 2>/dev/null)

        if [ $? -eq 0 ]; then
            log_info "Email subscription created"
            log_warn "Check your email ($EMAIL) to confirm the subscription"
        else
            log_error "Failed to subscribe email"
        fi
    fi

    echo ""
    log_info "SNS topic setup complete!"
    log_info "Topic ARN: $TOPIC_ARN"
    echo ""
    echo "Next steps:"
    echo "  1. Check your email and confirm the subscription"
    echo "  2. Run: python scripts/monitoring/cloudwatch/create_alarms.py --create --sns-topic-arn \"$TOPIC_ARN\""
    echo "  3. Test alarms to verify notifications work"
}

# Delete SNS topic
delete_topic() {
    log_info "Finding SNS topic: $TOPIC_NAME"

    # Find topic ARN
    TOPIC_ARN=$(aws sns list-topics \
        --region "$REGION" \
        --output text \
        --query "Topics[?contains(TopicArn, '$TOPIC_NAME')].TopicArn" 2>/dev/null | head -1)

    if [ -z "$TOPIC_ARN" ]; then
        log_warn "Topic not found: $TOPIC_NAME"
        exit 0
    fi

    log_info "Found topic: $TOPIC_ARN"

    # Confirm deletion
    read -p "Delete topic $TOPIC_NAME? (y/N): " CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        log_info "Deletion cancelled"
        exit 0
    fi

    # Delete topic
    aws sns delete-topic \
        --topic-arn "$TOPIC_ARN" \
        --region "$REGION" 2>/dev/null

    if [ $? -eq 0 ]; then
        log_info "Topic deleted successfully"
    else
        log_error "Failed to delete topic"
        exit 1
    fi
}

# List SNS topics
list_topics() {
    log_info "Listing NBA Simulator SNS topics..."
    echo ""

    # List all topics
    aws sns list-topics \
        --region "$REGION" \
        --output table \
        --query "Topics[?contains(TopicArn, 'nba-simulator')]" 2>/dev/null

    if [ $? -ne 0 ]; then
        log_error "Failed to list topics"
        exit 1
    fi

    echo ""

    # Show subscriptions for each topic
    TOPIC_ARNS=$(aws sns list-topics \
        --region "$REGION" \
        --output text \
        --query "Topics[?contains(TopicArn, 'nba-simulator')].TopicArn" 2>/dev/null)

    for TOPIC_ARN in $TOPIC_ARNS; do
        log_info "Subscriptions for: $TOPIC_ARN"

        aws sns list-subscriptions-by-topic \
            --topic-arn "$TOPIC_ARN" \
            --region "$REGION" \
            --output table \
            --query 'Subscriptions[*].[Protocol,Endpoint,SubscriptionArn]' 2>/dev/null

        echo ""
    done
}

# Main
main() {
    case "$1" in
        create)
            create_topic
            ;;
        delete)
            delete_topic
            ;;
        list)
            list_topics
            ;;
        *)
            echo "Usage: $0 {create|delete|list}"
            echo ""
            echo "Commands:"
            echo "  create  - Create SNS topic and subscribe email"
            echo "  delete  - Delete SNS topic"
            echo "  list    - List SNS topics and subscriptions"
            exit 1
            ;;
    esac
}

main "$@"
