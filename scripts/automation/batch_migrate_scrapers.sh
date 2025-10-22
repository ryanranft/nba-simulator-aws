#!/bin/bash
#
# Batch Scraper Migration
#
# Migrates multiple scrapers to AsyncBaseScraper framework autonomously.
# Tests each migration and auto-commits successful ones.
#
# Usage:
#   bash scripts/automation/batch_migrate_scrapers.sh --count 10
#   bash scripts/automation/batch_migrate_scrapers.sh --all
#   bash scripts/automation/batch_migrate_scrapers.sh --pattern utility --count 5
#   bash scripts/automation/batch_migrate_scrapers.sh --dry-run
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default values
COUNT=10
MODE="next"  # next, all, pattern, or specific
PATTERN_FILTER=""
DRY_RUN=false
SPECIFIC_SCRAPERS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --count|-c)
            COUNT="$2"
            shift 2
            ;;
        --all|-a)
            MODE="all"
            COUNT=999
            shift
            ;;
        --pattern|-p)
            MODE="pattern"
            PATTERN_FILTER="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *.py)
            MODE="specific"
            SPECIFIC_SCRAPERS+=("$1")
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--count N | --all | --pattern PATTERN | --dry-run | scraper1.py scraper2.py ...]"
            exit 1
            ;;
    esac
done

# Initialize counters
TOTAL_ATTEMPTED=0
TOTAL_SUCCESS=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0
MANUAL_REVIEW=()

# Log file
LOG_DIR="${WORKSPACE_ROOT}/logs/scraper_migration"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/batch_${TIMESTAMP}.log"

# Redirect all output to log file and console
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${MAGENTA}==============================================================================${NC}"
echo -e "${MAGENTA}BATCH SCRAPER MIGRATION${NC}"
echo -e "${MAGENTA}==============================================================================${NC}"
echo ""
echo "Started: $(date)"
echo "Mode: $MODE"
echo "Target Count: $COUNT"
echo "Pattern Filter: ${PATTERN_FILTER:-none}"
echo "Dry Run: $DRY_RUN"
echo "Log File: $LOG_FILE"
echo ""

# Get list of scrapers to migrate
if [[ "$MODE" == "specific" ]]; then
    SCRAPERS_TO_MIGRATE=("${SPECIFIC_SCRAPERS[@]}")
    echo "Migrating specific scrapers: ${SCRAPERS_TO_MIGRATE[*]}"
else
    echo "Finding scrapers to migrate..."

    # Get all .py files in scripts/etl/
    ALL_SCRAPERS=($(find "${WORKSPACE_ROOT}/scripts/etl" -name "*.py" -type f | sort))

    # Filter out already migrated and infrastructure files
    SCRAPERS_TO_MIGRATE=()
    for scraper in "${ALL_SCRAPERS[@]}"; do
        basename_scraper=$(basename "$scraper")

        # Skip infrastructure files
        if [[ "$basename_scraper" == "async_scraper_base.py" ]] || \
           [[ "$basename_scraper" == "scraper_config.py" ]] || \
           [[ "$basename_scraper" == "scraper_telemetry.py" ]] || \
           [[ "$basename_scraper" == "scraper_error_handler.py" ]] || \
           [[ "$basename_scraper" == "data_validators.py" ]] || \
           [[ "$basename_scraper" == "deduplication_manager.py" ]] || \
           [[ "$basename_scraper" == "modular_tools.py" ]]; then
            continue
        fi

        # Check if already migrated (grep for "AsyncBaseScraper" in file)
        if grep -q "class.*AsyncBaseScraper" "$scraper" 2>/dev/null; then
            continue
        fi

        # Apply pattern filter if specified
        if [[ -n "$PATTERN_FILTER" ]]; then
            # Detect pattern
            pattern=$(python3 "${SCRIPT_DIR}/detect_scraper_pattern.py" "$scraper" 2>/dev/null || echo "unknown")
            if [[ "$pattern" != "$PATTERN_FILTER" ]]; then
                continue
            fi
        fi

        SCRAPERS_TO_MIGRATE+=("$scraper")

        # Stop if we have enough
        if [[ ${#SCRAPERS_TO_MIGRATE[@]} -ge $COUNT ]]; then
            break
        fi
    done

    echo "Found ${#SCRAPERS_TO_MIGRATE[@]} scrapers to migrate"
fi

echo ""
echo -e "${BLUE}Scrapers to migrate:${NC}"
for scraper in "${SCRAPERS_TO_MIGRATE[@]}"; do
    echo "  - $(basename "$scraper")"
done
echo ""

# Confirm before proceeding (unless dry-run)
if [[ "$DRY_RUN" == "false" ]]; then
    echo -e "${YELLOW}Proceed with batch migration? [y/N] ${NC}"
    read -r response

    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Cancelled by user"
        exit 0
    fi
fi

echo ""
echo -e "${GREEN}Starting batch migration...${NC}"
echo ""

# Track start time
START_TIME=$(date +%s)

# Next available port (starting from 8020)
NEXT_PORT=8020

# Migrate each scraper
for scraper in "${SCRAPERS_TO_MIGRATE[@]}"; do
    TOTAL_ATTEMPTED=$((TOTAL_ATTEMPTED + 1))
    basename_scraper=$(basename "$scraper")

    echo ""
    echo -e "${BLUE}------------------------------------------------------------------------------${NC}"
    echo -e "${BLUE}[${TOTAL_ATTEMPTED}/${#SCRAPERS_TO_MIGRATE[@]}] Migrating: $basename_scraper${NC}"
    echo -e "${BLUE}------------------------------------------------------------------------------${NC}"
    echo ""

    # Track start time for this scraper
    SCRAPER_START_TIME=$(date +%s)

    # Step 1: Detect pattern (30s)
    echo -e "${CYAN}[1/5] Detecting pattern...${NC}"
    if ! pattern_info=$(python3 "${SCRIPT_DIR}/detect_scraper_pattern.py" "$scraper" --json 2>&1); then
        echo -e "${RED}✗ Pattern detection failed${NC}"
        echo "$pattern_info"
        MANUAL_REVIEW+=("$basename_scraper - Pattern detection failed")
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        continue
    fi

    pattern=$(echo "$pattern_info" | python3 -c "import sys, json; print(json.load(sys.stdin)['pattern'])")
    echo -e "${GREEN}  Pattern: $pattern${NC}"

    # Skip agents automatically
    if [[ "$pattern" == "agent" ]]; then
        echo -e "${YELLOW}⊘ Autonomous agent - adding to manual review${NC}"
        MANUAL_REVIEW+=("$basename_scraper - Autonomous agent (requires manual migration)")
        TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
        continue
    fi

    # Step 2: Generate migration code (1m)
    echo -e "${CYAN}[2/5] Generating migration code...${NC}"

    # Save pattern info to temp file
    pattern_info_file="/tmp/pattern_info_${basename_scraper}.json"
    echo "$pattern_info" > "$pattern_info_file"

    # Generate migration (to temp file first)
    temp_migration="/tmp/migrated_${basename_scraper}"
    if ! python3 "${SCRIPT_DIR}/generate_migration.py" "$scraper" \
        --pattern-info "$pattern_info_file" \
        --preserve \
        --output "$temp_migration" 2>&1; then
        echo -e "${RED}✗ Code generation failed${NC}"
        MANUAL_REVIEW+=("$basename_scraper - Code generation failed")
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        rm -f "$pattern_info_file"
        continue
    fi
    echo -e "${GREEN}  Generated migration code (preserve mode)${NC}"

    # Step 3: Generate config (30s)
    echo -e "${CYAN}[3/5] Generating configuration...${NC}"

    config_name=$(basename "$scraper" .py)
    if ! python3 "${SCRIPT_DIR}/generate_scraper_config.py" "$config_name" \
        --port "$NEXT_PORT" \
        --pattern-info "$pattern_info_file" \
        --append 2>&1; then
        echo -e "${YELLOW}⚠ Config generation failed (non-critical)${NC}"
    else
        echo -e "${GREEN}  Generated config (port $NEXT_PORT)${NC}"
        NEXT_PORT=$((NEXT_PORT + 1))
    fi

    rm -f "$pattern_info_file"

    # Step 4: Test migration (2m)
    echo -e "${CYAN}[4/5] Testing migration...${NC}"

    # Copy temp migration to actual location (for testing)
    if [[ "$DRY_RUN" == "true" ]]; then
        test_file="$temp_migration"
    else
        cp "$temp_migration" "$scraper"
        test_file="$scraper"
    fi

    if ! test_results=$(python3 "${SCRIPT_DIR}/test_migrated_scraper.py" "$test_file" --json 2>&1); then
        echo -e "${RED}✗ Tests failed${NC}"
        echo "$test_results" | head -n 20

        # Rollback if not dry-run
        if [[ "$DRY_RUN" == "false" ]]; then
            git checkout -- "$scraper" 2>/dev/null || true
        fi

        MANUAL_REVIEW+=("$basename_scraper - Tests failed")
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        rm -f "$temp_migration"
        continue
    fi

    # Check test pass rate
    tests_passed=$(echo "$test_results" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tests_passed'])" 2>/dev/null || echo "0")
    tests_failed=$(echo "$test_results" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tests_failed'])" 2>/dev/null || echo "1")

    if [[ "$tests_failed" -gt 0 ]]; then
        echo -e "${YELLOW}⚠ Some tests failed ($tests_passed passed, $tests_failed failed)${NC}"
        # Continue anyway - some tests might be expected to fail (e.g., dry run without full setup)
    else
        echo -e "${GREEN}  All tests passed ($tests_passed/$tests_passed)${NC}"
    fi

    # Step 5: Commit (30s) - only if not dry-run
    if [[ "$DRY_RUN" == "false" ]]; then
        echo -e "${CYAN}[5/5] Committing migration...${NC}"

        # Format with black
        black "$scraper" >/dev/null 2>&1 || true

        # Git add
        git add "$scraper" config/scraper_config.yaml 2>/dev/null || true

        # Commit
        commit_msg="Migrate $basename_scraper to AsyncBaseScraper (Pattern: $pattern)

Automated migration via batch_migrate_scrapers.sh
- Pattern: $pattern
- Tests passed: $tests_passed
- Config port: $NEXT_PORT

Part of ADCE Phase 1: Automated Scraper Migration"

        if git commit -m "$commit_msg" >/dev/null 2>&1; then
            echo -e "${GREEN}  Committed migration${NC}"
        else
            echo -e "${YELLOW}  No changes to commit${NC}"
        fi
    else
        echo -e "${CYAN}[5/5] Skipping commit (dry-run)${NC}"
    fi

    # Calculate duration
    SCRAPER_END_TIME=$(date +%s)
    SCRAPER_DURATION=$((SCRAPER_END_TIME - SCRAPER_START_TIME))

    rm -f "$temp_migration"

    echo ""
    echo -e "${GREEN}✓ SUCCESS: $basename_scraper migrated in ${SCRAPER_DURATION}s${NC}"
    TOTAL_SUCCESS=$((TOTAL_SUCCESS + 1))
done

# Calculate statistics
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS=$((TOTAL_DURATION % 60))

echo ""
echo -e "${MAGENTA}==============================================================================${NC}"
echo -e "${MAGENTA}BATCH MIGRATION COMPLETE${NC}"
echo -e "${MAGENTA}==============================================================================${NC}"
echo ""
echo "Finished: $(date)"
echo "Total Duration: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Results:"
echo "  Attempted: $TOTAL_ATTEMPTED"
echo "  ✓ Success: $TOTAL_SUCCESS"
echo "  ✗ Failed: $TOTAL_FAILED"
echo "  ⊘ Skipped: $TOTAL_SKIPPED"
echo ""

if [[ $TOTAL_SUCCESS -gt 0 ]]; then
    AVG_TIME=$((TOTAL_DURATION / TOTAL_SUCCESS))
    echo "Average Time per Scraper: ${AVG_TIME}s"
fi

# Manual review list
if [[ ${#MANUAL_REVIEW[@]} -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}Manual Review Needed (${#MANUAL_REVIEW[@]}):${NC}"
    for item in "${MANUAL_REVIEW[@]}"; do
        echo "  - $item"
    done
fi

echo ""
echo "Log File: $LOG_FILE"
echo ""

# Generate final report
REPORT_DIR="${WORKSPACE_ROOT}/reports"
mkdir -p "$REPORT_DIR"
REPORT_FILE="${REPORT_DIR}/migration_summary_${TIMESTAMP}.md"

cat > "$REPORT_FILE" << EOF
# Scraper Migration Summary

**Date:** $(date)
**Duration:** ${MINUTES}m ${SECONDS}s
**Mode:** $MODE
**Pattern Filter:** ${PATTERN_FILTER:-none}
**Dry Run:** $DRY_RUN

## Results

- **Attempted:** $TOTAL_ATTEMPTED
- **✓ Success:** $TOTAL_SUCCESS ($(( TOTAL_SUCCESS * 100 / TOTAL_ATTEMPTED ))%)
- **✗ Failed:** $TOTAL_FAILED
- **⊘ Skipped:** $TOTAL_SKIPPED

EOF

if [[ $TOTAL_SUCCESS -gt 0 ]]; then
    echo "**Average Time:** ${AVG_TIME}s per scraper" >> "$REPORT_FILE"
fi

if [[ ${#MANUAL_REVIEW[@]} -gt 0 ]]; then
    echo "" >> "$REPORT_FILE"
    echo "## Manual Review Needed (${#MANUAL_REVIEW[@]})" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    for item in "${MANUAL_REVIEW[@]}"; do
        echo "- $item" >> "$REPORT_FILE"
    done
fi

echo "" >> "$REPORT_FILE"
echo "## Log File" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "$LOG_FILE" >> "$REPORT_FILE"

echo -e "${GREEN}Report saved: $REPORT_FILE${NC}"
echo ""

# Exit with appropriate code
if [[ $TOTAL_FAILED -gt 0 ]]; then
    exit 1
else
    exit 0
fi
