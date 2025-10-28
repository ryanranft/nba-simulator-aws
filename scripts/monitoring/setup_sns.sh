#!/bin/bash
#
# SNS Topic Setup for CloudWatch Alarms
# Part of Phase 0.0020 (Monitoring & Observability)
#
# Usage:
#   bash scripts/monitoring/setup_sns.sh --email your@email.com
#   bash scripts/monitoring/setup_sns.sh --email your@email.com --sms +1234567890
#   bash scripts/monitoring/setup_sns.sh --list
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# AWS region
REGION="${AWS_REGION:-us-east-1}"
TOPIC_NAME="nba-simulator-alerts"

# Function to create SNS topic
create_sns_topic() {
    echo -e "${YELLOW}📧 Creating SNS topic: $TOPIC_NAME${NC}"

    local topic_arn=$(aws sns create-topic \
        --name "$TOPIC_NAME" \
        --region "$REGION" \
        --query 'TopicArn' \
        --output text)

    if [ -n "$topic_arn" ]; then
        echo -e "${GREEN}✅ Topic created: $topic_arn${NC}"
        echo "$topic_arn"
        return 0
    else
        echo -e "${RED}❌ Failed to create topic${NC}"
        return 1
    fi
}

# Function to get existing topic ARN
get_topic_arn() {
    aws sns list-topics \
        --region "$REGION" \
        --query "Topics[?contains(TopicArn, '$TOPIC_NAME')].TopicArn" \
        --output text
}

# Function to subscribe email
subscribe_email() {
    local topic_arn="$1"
    local email="$2"

    echo -e "${YELLOW}📧 Subscribing email: $email${NC}"

    aws sns subscribe \
        --topic-arn "$topic_arn" \
        --protocol email \
        --notification-endpoint "$email" \
        --region "$REGION" > /dev/null

    echo -e "${GREEN}✅ Email subscription created${NC}"
    echo -e "   ${YELLOW}⚠️  Check your inbox and confirm the subscription!${NC}"
}

# Function to subscribe SMS
subscribe_sms() {
    local topic_arn="$1"
    local phone="$2"

    echo -e "${YELLOW}📱 Subscribing SMS: $phone${NC}"

    aws sns subscribe \
        --topic-arn "$topic_arn" \
        --protocol sms \
        --notification-endpoint "$phone" \
        --region "$REGION" > /dev/null

    echo -e "${GREEN}✅ SMS subscription created${NC}"
}

# Function to list subscriptions
list_subscriptions() {
    local topic_arn="$1"

    echo -e "${YELLOW}📋 Subscriptions for topic: $topic_arn${NC}"
    echo ""

    aws sns list-subscriptions-by-topic \
        --topic-arn "$topic_arn" \
        --region "$REGION" \
        --query 'Subscriptions[*].[Protocol,Endpoint,SubscriptionArn]' \
        --output table
}

# Function to test SNS topic
test_sns() {
    local topic_arn="$1"

    echo -e "${YELLOW}🧪 Sending test notification...${NC}"

    aws sns publish \
        --topic-arn "$topic_arn" \
        --subject "NBA Simulator - Test Alert" \
        --message "This is a test notification from the NBA Simulator monitoring system. If you received this, your SNS topic is configured correctly!" \
        --region "$REGION"

    echo -e "${GREEN}✅ Test message sent!${NC}"
    echo -e "   Check your email/SMS for the test notification"
}

# Main execution
main() {
    echo "NBA Simulator - SNS Setup"
    echo "========================="
    echo ""

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not installed${NC}"
        exit 1
    fi

    # Get or create topic ARN
    topic_arn=$(get_topic_arn)

    if [ -z "$topic_arn" ]; then
        topic_arn=$(create_sns_topic)
        echo ""
    else
        echo -e "${GREEN}✅ Topic already exists: $topic_arn${NC}"
        echo ""
    fi

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --email)
                subscribe_email "$topic_arn" "$2"
                echo ""
                shift 2
                ;;
            --sms)
                subscribe_sms "$topic_arn" "$2"
                echo ""
                shift 2
                ;;
            --list)
                list_subscriptions "$topic_arn"
                echo ""
                shift
                ;;
            --test)
                test_sns "$topic_arn"
                echo ""
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                shift
                ;;
        esac
    done

    # Show next steps
    echo ""
    echo -e "${GREEN}✅ SNS setup complete!${NC}"
    echo ""
    echo "Topic ARN:"
    echo "  $topic_arn"
    echo ""
    echo "Next steps:"
    echo "  1. Confirm email subscription (check your inbox)"
    echo "  2. Create alarms: python scripts/monitoring/create_alarms.py --sns-topic '$topic_arn' --all"
    echo "  3. Test notifications: bash scripts/monitoring/setup_sns.sh --test"
    echo ""
    echo "To view subscriptions:"
    echo "  bash scripts/monitoring/setup_sns.sh --list"
}

main "$@"
