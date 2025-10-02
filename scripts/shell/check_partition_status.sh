#!/bin/bash
#
# Check Overnight Partitioning Status
#
# Quick status check script to see if partitioning completed successfully
# and how many year folders were created.
#
# Usage: ./scripts/shell/check_partition_status.sh

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "S3 PARTITIONING STATUS CHECK"
echo "================================================================================"
echo ""

# Check if processes are still running
if ps aux | grep -q "[p]artition_by_year.py"; then
    echo -e "${YELLOW}⏳ Partitioning is STILL RUNNING${NC}"
    echo ""
    echo "Active processes:"
    ps aux | grep "[p]artition" | grep -v grep
    echo ""
    echo "To monitor progress:"
    echo "  tail -f partition_overnight.log"
    echo ""
else
    echo -e "${GREEN}✅ Partitioning processes have COMPLETED${NC}"
    echo ""
fi

# Check S3 year folders created
echo "-------------------------------------------------------------------------------"
echo "Year Folders Created in S3"
echo "-------------------------------------------------------------------------------"
echo ""

for data_type in schedule pbp box_scores team_stats; do
    count=$(aws s3 ls s3://nba-sim-raw-data-lake/${data_type}/ 2>/dev/null | grep "year=" | wc -l | tr -d ' ')

    if [ "$count" -eq 33 ]; then
        echo -e "${GREEN}✅${NC} ${data_type}: ${count} year folders (COMPLETE)"
    elif [ "$count" -gt 0 ]; then
        echo -e "${YELLOW}⏳${NC} ${data_type}: ${count} year folders (IN PROGRESS)"
    else
        echo -e "${RED}⏸️${NC}  ${data_type}: ${count} year folders (NOT STARTED)"
    fi
done

echo ""

# Check log file for completion message
echo "-------------------------------------------------------------------------------"
echo "Log File Status"
echo "-------------------------------------------------------------------------------"
echo ""

if [ -f partition_overnight.log ]; then
    if grep -q "ALL PARTITIONING COMPLETE" partition_overnight.log; then
        echo -e "${GREEN}✅ Log shows: ALL PARTITIONING COMPLETE${NC}"
    elif grep -q "FAILED" partition_overnight.log; then
        echo -e "${RED}❌ Log shows: Some partitioning FAILED${NC}"
        echo ""
        echo "Failed sections:"
        grep "FAILED" partition_overnight.log
    else
        echo -e "${YELLOW}⏳ Partitioning in progress${NC}"
        echo ""
        echo "Last 5 lines:"
        tail -5 partition_overnight.log
    fi

    echo ""
    echo "Full log: partition_overnight.log ($(wc -l < partition_overnight.log | tr -d ' ') lines)"
else
    echo -e "${RED}⚠️  Log file not found: partition_overnight.log${NC}"
fi

echo ""

# Summary
echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo ""

schedule_count=$(aws s3 ls s3://nba-sim-raw-data-lake/schedule/ 2>/dev/null | grep "year=" | wc -l | tr -d ' ')
pbp_count=$(aws s3 ls s3://nba-sim-raw-data-lake/pbp/ 2>/dev/null | grep "year=" | wc -l | tr -d ' ')
box_count=$(aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ 2>/dev/null | grep "year=" | wc -l | tr -d ' ')
team_count=$(aws s3 ls s3://nba-sim-raw-data-lake/team_stats/ 2>/dev/null | grep "year=" | wc -l | tr -d ' ')

total=$((schedule_count + pbp_count + box_count + team_count))
expected=132  # 33 years × 4 data types

echo "Total year folders created: ${total}/132"
echo ""

if [ "$total" -eq 132 ]; then
    echo -e "${GREEN}🎉 PARTITIONING 100% COMPLETE!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Create year-based crawlers:"
    echo "     ./scripts/etl/create_year_crawlers.sh --all"
    echo ""
    echo "  2. Test one crawler:"
    echo "     aws glue start-crawler --name nba-schedule-1997-crawler"
    echo ""
elif [ "$total" -gt 0 ]; then
    percent=$((total * 100 / expected))
    echo -e "${YELLOW}⏳ PARTITIONING ${percent}% COMPLETE${NC}"
    echo ""
    echo "Monitor progress:"
    echo "  tail -f partition_overnight.log"
    echo ""
else
    echo -e "${RED}⚠️  PARTITIONING NOT STARTED${NC}"
    echo ""
    echo "Start partitioning:"
    echo "  nohup ./scripts/etl/partition_all_overnight.sh > partition_overnight.log 2>&1 &"
    echo ""
fi

echo ""