#!/bin/bash
# scripts/aws/check_costs.sh
# Check current AWS costs and usage

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "AWS Cost Report - NBA Simulator Project"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get current month dates
START_DATE=$(date -u -v1d +%Y-%m-01 2>/dev/null || date -u -d "$(date +%Y-%m-01)" +%Y-%m-01)
END_DATE=$(date -u +%Y-%m-%d)

echo "📅 Period: $START_DATE to $END_DATE (month-to-date)"
echo ""

# Function to format currency
format_currency() {
    printf "$%.2f" "$1"
}

# Get total cost for current month
echo "💰 Total Cost (Month-to-Date):"
TOTAL_COST=$(aws ce get-cost-and-usage \
    --time-period Start="$START_DATE",End="$END_DATE" \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
    --output text 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$TOTAL_COST" ]; then
    echo "   $(format_currency "$TOTAL_COST") USD"
else
    echo "   ⚠️  Unable to retrieve cost data"
    TOTAL_COST=0
fi
echo ""

# Get cost by service
echo "📊 Cost by Service:"
aws ce get-cost-and-usage \
    --time-period Start="$START_DATE",End="$END_DATE" \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE \
    --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.BlendedCost.Amount]' \
    --output text 2>/dev/null | \
    sort -t$'\t' -k2 -rn | \
    head -10 | \
    while IFS=$'\t' read -r service cost; do
        if [ -n "$service" ] && [ -n "$cost" ]; then
            printf "   %-30s %8.2f USD\n" "$service" "$cost"
        fi
    done
echo ""

# Check S3 storage
echo "🗄️  S3 Storage:"
S3_SIZE=$(aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | \
    grep "Total Size" | awk '{print $3}')

if [ -n "$S3_SIZE" ]; then
    S3_GB=$(echo "scale=2; $S3_SIZE / 1024 / 1024 / 1024" | bc)
    S3_COST=$(echo "scale=2; $S3_GB * 0.023" | bc)
    echo "   Size: ${S3_GB} GB"
    echo "   Estimated monthly cost: \$${S3_COST}"
else
    echo "   ⚠️  Unable to retrieve S3 size"
fi
echo ""

# Check RDS status
echo "🗃️  RDS Status:"
RDS_STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier nba-sim-db \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null)

if [ $? -eq 0 ] && [ "$RDS_STATUS" != "None" ]; then
    RDS_CLASS=$(aws rds describe-db-instances \
        --db-instance-identifier nba-sim-db \
        --query 'DBInstances[0].DBInstanceClass' \
        --output text 2>/dev/null)
    echo "   Status: $RDS_STATUS"
    echo "   Instance: $RDS_CLASS"

    # Rough cost estimate
    if [[ "$RDS_CLASS" == *"t3.small"* ]]; then
        echo "   Estimated cost: ~\$29/month"
    elif [[ "$RDS_CLASS" == *"t3.medium"* ]]; then
        echo "   Estimated cost: ~\$60/month"
    fi
else
    echo "   Status: Not created yet (⏸️ Pending)"
fi
echo ""

# Check EC2 instances
echo "🖥️  EC2 Instances:"
EC2_COUNT=$(aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=nba-simulator" \
    --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType]' \
    --output text 2>/dev/null | wc -l)

if [ "$EC2_COUNT" -gt 0 ]; then
    aws ec2 describe-instances \
        --filters "Name=tag:Project,Values=nba-simulator" \
        --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType]' \
        --output text 2>/dev/null | \
        while read -r instance_id state instance_type; do
            echo "   $instance_id: $state ($instance_type)"
        done
else
    echo "   No EC2 instances found (or not tagged)"
fi
echo ""

# Check Glue jobs
echo "⚙️  Glue Jobs:"
GLUE_JOBS=$(aws glue get-jobs --query 'Jobs[*].Name' --output text 2>/dev/null)

if [ -n "$GLUE_JOBS" ]; then
    echo "   Jobs: $GLUE_JOBS"
else
    echo "   Status: Not created yet (⏸️ Pending)"
fi
echo ""

# Monthly forecast
echo "📈 Cost Forecast:"
FORECAST=$(aws ce get-cost-forecast \
    --time-period Start="$END_DATE",End=$(date -u -v+1m -v1d -v-1d +%Y-%m-%d 2>/dev/null || date -u -d "$(date +%Y-%m-01) +1 month -1 day" +%Y-%m-%d) \
    --metric BLENDED_COST \
    --granularity MONTHLY \
    --query 'Total.Amount' \
    --output text 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$FORECAST" ]; then
    echo "   Projected month-end total: $(format_currency "$FORECAST") USD"
else
    echo "   ⚠️  Unable to retrieve forecast"
fi
echo ""

# Budget alert
BUDGET_THRESHOLD=150
if (( $(echo "$TOTAL_COST > $BUDGET_THRESHOLD" | bc -l) )); then
    echo "⚠️  WARNING: Month-to-date costs exceed budget threshold of \$$BUDGET_THRESHOLD"
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Current month: $(format_currency "$TOTAL_COST") USD"
echo "Budget: \$150.00 USD/month (recommended)"
echo ""

# Recommendations
if (( $(echo "$TOTAL_COST < 10" | bc -l) )); then
    echo "✅ Costs are low (Phase 1: S3 only)"
elif (( $(echo "$TOTAL_COST < 50" | bc -l) )); then
    echo "✅ Costs are within expected range (S3 + minimal services)"
elif (( $(echo "$TOTAL_COST < 100" | bc -l) )); then
    echo "⚠️  Costs are moderate - monitor RDS/EC2 usage"
else
    echo "⚠️  Costs are high - review running services"
    echo "   Consider stopping unused RDS/EC2 instances"
fi
echo ""

echo "💡 Cost Optimization Tips:"
echo "   1. Stop RDS when not in use (saves ~\$29-60/month)"
echo "   2. Stop EC2 when not in use (saves ~\$5-15/month)"
echo "   3. Use Spot Instances for non-critical workloads"
echo "   4. Run Glue ETL monthly instead of daily"
echo "   5. Monitor with: aws ce get-cost-and-usage --help"
echo ""

echo "📝 For detailed breakdown, visit:"
echo "   https://console.aws.amazon.com/cost-management/home#/cost-explorer"
