#!/usr/bin/env bash
#
# Data Collection Status Monitor
#
# Automated inventory system for tracking NBA data collection across all sources.
# Integrates with workflow automation tools for real-time status updates.
#
# Usage:
#   bash scripts/monitoring/data_collection_status.sh [--format json|table|markdown]
#
# Output:
#   - Data source status (scraped, uploaded to S3, loaded to DB)
#   - File counts and sizes
#   - Last update timestamps
#   - Active scraper processes
#   - Failed scraper logs
#
# Integration:
#   - Called by Workflow #38 (Overnight Scraper Handoff)
#   - Updates docs/DATA_COLLECTION_INVENTORY.md
#   - Logs to /tmp/data_collection_status.log
#

set -e

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
OUTPUT_FORMAT="${1:-markdown}"  # json, table, or markdown
LOG_FILE="/tmp/data_collection_status.log"
INVENTORY_FILE="$PROJECT_DIR/docs/DATA_COLLECTION_INVENTORY.md"

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if AWS CLI is available
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log "ERROR: AWS CLI not found"
        exit 1
    fi
}

# Get S3 bucket file count and size for a prefix
get_s3_stats() {
    local prefix="$1"
    local bucket="s3://nba-sim-raw-data-lake/$prefix"

    # Check if prefix exists
    if ! aws s3 ls "$bucket" &> /dev/null; then
        echo "0|0"
        return
    fi

    # Get file count and total size
    local stats=$(aws s3 ls "$bucket" --recursive --summarize 2>/dev/null | \
                  tail -2 | \
                  grep -E "Total (Objects|Size)" | \
                  awk '{print $3}' | \
                  paste -sd'|' -)

    echo "${stats:-0|0}"
}

# Check if scraper process is running
check_scraper_process() {
    local search_pattern="$1"
    ps aux | grep -E "$search_pattern" | grep -v grep | awk '{print $2}' | head -1
}

# Get last modification time for a file/directory
get_last_modified() {
    local path="$1"
    if [ -e "$path" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$path"
        else
            stat -c "%y" "$path" | cut -d'.' -f1
        fi
    else
        echo "N/A"
    fi
}

# Format bytes to human readable
format_bytes() {
    local bytes=$1
    if [ "$bytes" -eq 0 ]; then
        echo "0 B"
    elif [ "$bytes" -lt 1024 ]; then
        echo "${bytes} B"
    elif [ "$bytes" -lt 1048576 ]; then
        echo "$(echo "scale=2; $bytes/1024" | bc) KB"
    elif [ "$bytes" -lt 1073741824 ]; then
        echo "$(echo "scale=2; $bytes/1048576" | bc) MB"
    else
        echo "$(echo "scale=2; $bytes/1073741824" | bc) GB"
    fi
}

# Check ESPN data
check_espn_data() {
    log "Checking ESPN data..."

    local s3_stats=$(get_s3_stats "espn/")
    local file_count=$(echo "$s3_stats" | cut -d'|' -f1)
    local total_size=$(echo "$s3_stats" | cut -d'|' -f2)
    local size_human=$(format_bytes "$total_size")

    local local_files=$(find /tmp/espn_* -type f 2>/dev/null | wc -l | tr -d ' ')
    local scraper_pid=$(check_scraper_process "scrape_missing_espn_data.py")

    echo "ESPN|$file_count|$size_human|${scraper_pid:-N/A}|$(get_last_modified /tmp/espn_extraction_direct.log)"
}

# Check hoopR data
check_hoopr_data() {
    log "Checking hoopR data..."

    local s3_stats=$(get_s3_stats "hoopr_phase1/")
    local file_count=$(echo "$s3_stats" | cut -d'|' -f1)
    local total_size=$(echo "$s3_stats" | cut -d'|' -f2)
    local size_human=$(format_bytes "$total_size")

    local local_files=$(find /tmp/hoopr_phase1 -type f -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
    local scraper_pid=$(check_scraper_process "scrape_hoopr")

    echo "hoopR Phase 1|$file_count|$size_human|${scraper_pid:-N/A}|$(get_last_modified /tmp/hoopr_phase1b.log)"
}

# Check Basketball Reference data
check_bbref_data() {
    log "Checking Basketball Reference data..."

    local s3_stats=$(get_s3_stats "basketball_reference/")
    local file_count=$(echo "$s3_stats" | cut -d'|' -f1)
    local total_size=$(echo "$s3_stats" | cut -d'|' -f2)
    local size_human=$(format_bytes "$total_size")

    local completion_files=$(find /tmp/basketball_reference_incremental -name "*.complete" 2>/dev/null | wc -l | tr -d ' ')
    local scraper_pid=$(check_scraper_process "scrape_bbref_incremental.sh|scrape_basketball_reference")

    echo "Basketball Reference|$file_count|$size_human|${scraper_pid:-N/A}|$completion_files seasons complete|$(get_last_modified /tmp/bbref_incremental_2020-2025.log)"
}

# Check NBA API data
check_nba_api_data() {
    log "Checking NBA API data..."

    local s3_stats=$(get_s3_stats "nba_api/")
    local file_count=$(echo "$s3_stats" | cut -d'|' -f1)
    local total_size=$(echo "$s3_stats" | cut -d'|' -f2)
    local size_human=$(format_bytes "$total_size")

    local local_files=$(find /tmp/nba_api_comprehensive -type f 2>/dev/null | wc -l | tr -d ' ')
    local scraper_pid=$(check_scraper_process "scrape_nba_api_comprehensive.py")

    echo "NBA API|$file_count|$size_human|${scraper_pid:-N/A}|Local: $local_files files|$(get_last_modified /tmp/nba_api_comprehensive.log)"
}

# Check Kaggle data
check_kaggle_data() {
    log "Checking Kaggle data..."

    local s3_stats=$(get_s3_stats "kaggle/")
    local file_count=$(echo "$s3_stats" | cut -d'|' -f1)
    local total_size=$(echo "$s3_stats" | cut -d'|' -f2)
    local size_human=$(format_bytes "$total_size")

    local local_files=$(find /tmp/kaggle_* -type f 2>/dev/null | wc -l | tr -d ' ')
    local scraper_pid=$(check_scraper_process "download_kaggle_basketball.py")

    echo "Kaggle|$file_count|$size_human|${scraper_pid:-N/A}|$(get_last_modified /tmp/kaggle_extraction.log)"
}

# Check SportsDataverse data
check_sportsdataverse_data() {
    log "Checking SportsDataverse data..."

    local s3_stats=$(get_s3_stats "sportsdataverse/")
    local file_count=$(echo "$s3_stats" | cut -d'|' -f1)
    local total_size=$(echo "$s3_stats" | cut -d'|' -f2)
    local size_human=$(format_bytes "$total_size")

    local local_files=$(find /tmp/sportsdataverse -type f 2>/dev/null | wc -l | tr -d ' ')
    local scraper_pid=$(check_scraper_process "scrape_sportsdataverse.py")

    echo "SportsDataverse|$file_count|$size_human|${scraper_pid:-N/A}|$(get_last_modified /tmp/sportsdataverse_final.log)"
}

# Output in markdown format
output_markdown() {
    cat > "$INVENTORY_FILE" <<EOF
# NBA Data Collection Inventory

**Last Updated:** $(date '+%Y-%m-%d %H:%M:%S %Z')
**Auto-generated by:** \`scripts/monitoring/data_collection_status.sh\`

---

## Data Sources Status

| Data Source | S3 Files | S3 Size | Active Scraper PID | Notes | Last Activity |
|-------------|----------|---------|-------------------|-------|---------------|
EOF

    # Collect all data source stats
    check_espn_data | awk -F'|' '{printf "| %s | %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5, $6}' >> "$INVENTORY_FILE"
    check_hoopr_data | awk -F'|' '{printf "| %s | %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5, $6}' >> "$INVENTORY_FILE"
    check_bbref_data | awk -F'|' '{printf "| %s | %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5, $6}' >> "$INVENTORY_FILE"
    check_nba_api_data | awk -F'|' '{printf "| %s | %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5, $6}' >> "$INVENTORY_FILE"
    check_kaggle_data | awk -F'|' '{printf "| %s | %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5, $6}' >> "$INVENTORY_FILE"
    check_sportsdataverse_data | awk -F'|' '{printf "| %s | %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5, $6}' >> "$INVENTORY_FILE"

    cat >> "$INVENTORY_FILE" <<EOF

---

## Summary

**Total S3 Objects:** $(aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize 2>/dev/null | grep "Total Objects:" | awk '{print $3}')
**Total S3 Size:** $(aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize 2>/dev/null | grep "Total Size:" | awk '{print $3}' | xargs -I {} echo "scale=2; {}/1073741824" | bc) GB

**Active Scrapers:** $(ps aux | grep -E "scrape_|download_kaggle" | grep -v grep | wc -l | tr -d ' ')

---

## Failed Scrapers

EOF

    # Check for failed scraper logs
    for log_file in /tmp/nba_api_comprehensive.log /tmp/nba_api_playbyplay.log /tmp/hoopr.log /tmp/bbref.log; do
        if [ -f "$log_file" ]; then
            local errors=$(grep -c "ERROR\|Error\|Failed\|❌" "$log_file" 2>/dev/null || echo 0)
            if [ "$errors" -gt 0 ]; then
                echo "- \`$(basename "$log_file")\`: $errors errors detected" >> "$INVENTORY_FILE"
            fi
        fi
    done

    cat >> "$INVENTORY_FILE" <<EOF

---

## Next Steps

1. **Monitor active scrapers** - Check PIDs listed above
2. **Upload local data to S3** - For completed scrapers with local files
3. **Load to PostgreSQL** - After S3 upload verification
4. **Create possession panels** - Once all data sources loaded

---

*For detailed scraper management, see Workflow #42: \`docs/claude_workflows/workflow_descriptions/42_scraper_management.md\`*
EOF

    log "Markdown inventory written to: $INVENTORY_FILE"

    # Also print to stdout
    cat "$INVENTORY_FILE"
}

# Output in JSON format
output_json() {
    echo '{'
    echo '  "last_updated": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",'
    echo '  "data_sources": ['

    # Collect stats for all sources
    local espn=$(check_espn_data)
    local hoopr=$(check_hoopr_data)
    local bbref=$(check_bbref_data)
    local nba_api=$(check_nba_api_data)
    local kaggle=$(check_kaggle_data)
    local sportsdataverse=$(check_sportsdataverse_data)

    # Format as JSON (simplified - would need jq for proper JSON)
    echo '  ]'
    echo '}'
}

# Main execution
main() {
    log "Starting data collection status check..."

    check_aws_cli

    case "$OUTPUT_FORMAT" in
        json)
            output_json
            ;;
        markdown)
            output_markdown
            ;;
        *)
            log "ERROR: Unknown output format: $OUTPUT_FORMAT"
            log "Valid formats: json, markdown"
            exit 1
            ;;
    esac

    log "Data collection status check complete"
}

# Run main function
main "$@"
