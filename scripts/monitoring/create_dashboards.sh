#!/bin/bash
#
# Create CloudWatch Dashboards
# Part of Phase 0.0020 (Monitoring & Observability)
#
# Usage:
#   bash scripts/monitoring/create_dashboards.sh
#   bash scripts/monitoring/create_dashboards.sh --dashboard data-collection
#   bash scripts/monitoring/create_dashboards.sh --dashboard performance
#   bash scripts/monitoring/create_dashboards.sh --dashboard adce-health
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DASHBOARDS_DIR="${PROJECT_ROOT}/dashboards"

# AWS region
REGION="${AWS_REGION:-us-east-1}"

# Function to create a dashboard
create_dashboard() {
    local dashboard_name="$1"
    local dashboard_file="$2"

    if [ ! -f "$dashboard_file" ]; then
        echo -e "${RED}❌ Dashboard file not found: $dashboard_file${NC}"
        return 1
    fi

    echo -e "${YELLOW}📊 Creating dashboard: $dashboard_name${NC}"

    aws cloudwatch put-dashboard \
        --dashboard-name "$dashboard_name" \
        --dashboard-body "file://${dashboard_file}" \
        --region "$REGION"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dashboard created: $dashboard_name${NC}"
        echo -e "   View at: https://console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=${dashboard_name}"
        return 0
    else
        echo -e "${RED}❌ Failed to create dashboard: $dashboard_name${NC}"
        return 1
    fi
}

# Function to list existing dashboards
list_dashboards() {
    echo -e "${YELLOW}📋 Existing CloudWatch Dashboards:${NC}"
    aws cloudwatch list-dashboards --region "$REGION" | \
        jq -r '.DashboardEntries[] | "  - \(.DashboardName)"'
}

# Main execution
main() {
    echo "NBA Simulator - CloudWatch Dashboard Setup"
    echo "=========================================="
    echo ""

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not installed${NC}"
        exit 1
    fi

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}⚠️  jq not installed (optional for listing dashboards)${NC}"
    fi

    # Parse arguments
    if [ "$1" == "--dashboard" ] && [ -n "$2" ]; then
        case "$2" in
            data-collection)
                create_dashboard "NBA-Simulator-DataCollection" \
                    "${DASHBOARDS_DIR}/data_collection_dashboard.json"
                ;;
            performance)
                create_dashboard "NBA-Simulator-Performance" \
                    "${DASHBOARDS_DIR}/performance_dashboard.json"
                ;;
            adce-health)
                create_dashboard "NBA-Simulator-ADCE-Health" \
                    "${DASHBOARDS_DIR}/adce_health_dashboard.json"
                ;;
            *)
                echo -e "${RED}❌ Unknown dashboard: $2${NC}"
                echo "Available dashboards: data-collection, performance, adce-health"
                exit 1
                ;;
        esac
    else
        # Create all dashboards
        echo "Creating all dashboards..."
        echo ""

        create_dashboard "NBA-Simulator-DataCollection" \
            "${DASHBOARDS_DIR}/data_collection_dashboard.json"
        echo ""

        create_dashboard "NBA-Simulator-Performance" \
            "${DASHBOARDS_DIR}/performance_dashboard.json"
        echo ""

        create_dashboard "NBA-Simulator-ADCE-Health" \
            "${DASHBOARDS_DIR}/adce_health_dashboard.json"
        echo ""
    fi

    echo ""
    list_dashboards

    echo ""
    echo -e "${GREEN}✅ Dashboard setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Set up SNS topic: bash scripts/monitoring/setup_sns.sh"
    echo "  2. Create alarms: python scripts/monitoring/create_alarms.py"
    echo "  3. Publish metrics: python scripts/monitoring/publish_collection_metrics.py --all"
}

main "$@"
