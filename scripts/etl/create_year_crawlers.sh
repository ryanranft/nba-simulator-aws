#!/bin/bash
#
# Create Year-Based Glue Crawlers
#
# Creates separate Glue Crawlers for each year of data, allowing processing
# of manageable chunks instead of all 146K files at once.
#
# Usage:
#   ./scripts/etl/create_year_crawlers.sh --data-type schedule --years 1997-2021
#   ./scripts/etl/create_year_crawlers.sh --data-type pbp --years 2015-2021
#   ./scripts/etl/create_year_crawlers.sh --all
#
# Author: Ryan Ranft
# Date: 2025-10-01
# Phase: 2.1 - Year-Based Glue Crawler Approach

set -e

# Configuration
BUCKET="nba-sim-raw-data-lake"
DATABASE="nba_raw_data"
ROLE="AWSGlueServiceRole-NBASimulator"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
DATA_TYPE=""
START_YEAR=""
END_YEAR=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --data-type)
      DATA_TYPE="$2"
      shift 2
      ;;
    --years)
      if [[ $2 =~ ^([0-9]{4})-([0-9]{4})$ ]]; then
        START_YEAR="${BASH_REMATCH[1]}"
        END_YEAR="${BASH_REMATCH[2]}"
      else
        echo -e "${RED}Error: --years must be in format YYYY-YYYY (e.g., 1997-2021)${NC}"
        exit 1
      fi
      shift 2
      ;;
    --all)
      # Create crawlers for all data types and all years
      DATA_TYPE="all"
      START_YEAR=1997
      END_YEAR=2021
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --data-type TYPE    Data type: schedule, pbp, box_scores, team_stats"
      echo "  --years YYYY-YYYY   Year range (e.g., 1997-2021)"
      echo "  --all               Create crawlers for all data types and years"
      echo "  --dry-run           Show what would be created without creating"
      echo "  --help              Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0 --data-type schedule --years 1997-2021"
      echo "  $0 --data-type pbp --years 2015-2021 --dry-run"
      echo "  $0 --all"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Validate inputs
if [[ -z "$DATA_TYPE" ]]; then
  echo -e "${RED}Error: --data-type or --all is required${NC}"
  exit 1
fi

if [[ -z "$START_YEAR" || -z "$END_YEAR" ]]; then
  echo -e "${RED}Error: --years or --all is required${NC}"
  exit 1
fi

# Function to create a single crawler
create_crawler() {
  local data_type=$1
  local year=$2

  local crawler_name="nba-${data_type}-${year}-crawler"
  local s3_path="s3://${BUCKET}/${data_type}/year=${year}/"
  local description="Crawler for NBA ${data_type} data - Year ${year}"

  if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}[DRY RUN]${NC} Would create crawler: ${crawler_name}"
    echo "          S3 Path: ${s3_path}"
    return
  fi

  # Check if crawler already exists
  if aws glue get-crawler --name "$crawler_name" &>/dev/null; then
    echo -e "${YELLOW}⚠${NC}  Crawler already exists: ${crawler_name}"
    return
  fi

  # Create the crawler
  echo -e "${GREEN}✓${NC} Creating crawler: ${crawler_name}"

  aws glue create-crawler \
    --name "$crawler_name" \
    --targets "{\"S3Targets\":[{\"Path\":\"${s3_path}\"}]}" \
    --database-name "$DATABASE" \
    --role "$ROLE" \
    --description "$description" \
    --output text > /dev/null

  echo "    S3 Path: ${s3_path}"
}

# Function to create crawlers for a data type
create_crawlers_for_type() {
  local data_type=$1

  echo ""
  echo "================================================================"
  echo "Creating crawlers for: $(echo ${data_type} | tr '[:lower:]' '[:upper:]')"
  echo "Years: ${START_YEAR} to ${END_YEAR}"
  echo "================================================================"

  local count=0
  for year in $(seq $START_YEAR $END_YEAR); do
    create_crawler "$data_type" "$year"
    ((count++))
  done

  echo ""
  if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}[DRY RUN]${NC} Would create ${count} crawlers for ${data_type}"
  else
    echo -e "${GREEN}✓${NC} Created ${count} crawlers for ${data_type}"
  fi
}

# Main execution
echo "================================================================"
echo "Year-Based Glue Crawler Creation"
echo "================================================================"
echo "Bucket: ${BUCKET}"
echo "Database: ${DATABASE}"
echo "Role: ${ROLE}"
echo "Years: ${START_YEAR}-${END_YEAR}"

if [[ "$DRY_RUN" == true ]]; then
  echo -e "Mode: ${YELLOW}DRY RUN${NC} (no crawlers will be created)"
else
  echo -e "Mode: ${GREEN}EXECUTE${NC} (crawlers will be created)"
fi

# Create crawlers
if [[ "$DATA_TYPE" == "all" ]]; then
  for type in schedule pbp box_scores team_stats; do
    create_crawlers_for_type "$type"
  done
else
  create_crawlers_for_type "$DATA_TYPE"
fi

# Summary
echo ""
echo "================================================================"
echo "SUMMARY"
echo "================================================================"

if [[ "$DRY_RUN" == true ]]; then
  echo -e "${YELLOW}DRY RUN COMPLETE${NC}"
  echo "Run without --dry-run to actually create crawlers"
else
  echo -e "${GREEN}CRAWLERS CREATED SUCCESSFULLY${NC}"
  echo ""
  echo "Next steps:"
  echo "1. List all crawlers:"
  echo "   aws glue list-crawlers --query 'CrawlerNames' --output table"
  echo ""
  echo "2. Start a specific crawler:"
  echo "   aws glue start-crawler --name nba-schedule-1997-crawler"
  echo ""
  echo "3. Start all crawlers for a year (e.g., 1997):"
  echo "   for crawler in \$(aws glue list-crawlers --query 'CrawlerNames[?contains(@, \`1997\`)]' --output text); do"
  echo "     aws glue start-crawler --name \$crawler"
  echo "   done"
  echo ""
  echo "4. Monitor crawler status:"
  echo "   aws glue get-crawler --name nba-schedule-1997-crawler"
fi

echo ""