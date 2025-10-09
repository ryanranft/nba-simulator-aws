#!/bin/bash
#
# NBA Simulator - Master Data Collection Pipeline
#
# Purpose: Integrated workflow combining data inventory, gap analysis,
#          scraper management, and quality validation
#
# Created: October 9, 2025
# Integrates: Workflows #45, #46, #47, #40, #42
#
# Usage:
#   bash scripts/monitoring/data_pipeline_manager.sh [MODE]
#
# Modes:
#   status     - Check current data state (inventory + gaps)
#   plan       - Generate data collection plan
#   collect    - Execute scraper(s) to fill gaps
#   validate   - Verify data quality after collection
#   full       - Complete pipeline (status → plan → collect → validate)
#

set -e

# ==============================================================================
# Configuration
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Credentials
CREDENTIALS_FILE="/Users/ryanranft/nba-sim-credentials.env"

# Output directories
REPORTS_DIR="$PROJECT_ROOT/reports/data_pipeline"
mkdir -p "$REPORTS_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORTS_DIR/pipeline_report_$TIMESTAMP.md"

# ==============================================================================
# Helper Functions
# ==============================================================================

log_section() {
    echo ""
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC}  $1"
}

check_prerequisites() {
    log_section "Checking Prerequisites"

    local all_ok=true

    # Check conda environment
    if conda info --envs | grep -q "nba-aws.*\*"; then
        log_success "Conda environment 'nba-aws' is active"
    else
        log_error "Conda environment 'nba-aws' is NOT active"
        echo "  Run: conda activate nba-aws"
        all_ok=false
    fi

    # Check AWS credentials
    if aws sts get-caller-identity &>/dev/null; then
        log_success "AWS credentials are configured"
    else
        log_error "AWS credentials are NOT configured"
        echo "  Run: aws configure"
        all_ok=false
    fi

    # Check database credentials
    if [ -f "$CREDENTIALS_FILE" ]; then
        log_success "Database credentials file exists"
    else
        log_warning "Database credentials file not found (optional)"
    fi

    # Check disk space
    available_space=$(df -h /tmp | awk 'NR==2 {print $4}')
    log_info "Disk space available in /tmp: $available_space"

    if [ "$all_ok" = false ]; then
        log_error "Prerequisites check FAILED"
        exit 1
    fi

    log_success "All prerequisites satisfied"
}

# ==============================================================================
# Phase 1: Data Inventory
# ==============================================================================

run_data_inventory() {
    log_section "Phase 1: Data Inventory (Workflows #45, #47)"

    log_info "Running local data inventory..."
    if [ -f "$SCRIPT_DIR/inventory_local_data.sh" ]; then
        bash "$SCRIPT_DIR/inventory_local_data.sh" --quick 2>&1 | tee -a "$REPORT_FILE"
    else
        log_warning "Local inventory script not found - skipping"
        log_info "Expected: $SCRIPT_DIR/inventory_local_data.sh"
    fi

    echo ""
    log_info "Running AWS data inventory..."
    if [ -f "$SCRIPT_DIR/inventory_aws.sh" ]; then
        bash "$SCRIPT_DIR/inventory_aws.sh" --quick 2>&1 | tee -a "$REPORT_FILE"
    else
        log_warning "AWS inventory script not found - skipping"
        log_info "Expected: $SCRIPT_DIR/inventory_aws.sh"
    fi

    log_success "Data inventory complete"
}

# ==============================================================================
# Phase 2: Gap Analysis
# ==============================================================================

run_gap_analysis() {
    log_section "Phase 2: Data Gap Analysis (Workflow #46)"

    log_info "Analyzing data gaps..."

    # Load database credentials if available
    if [ -f "$CREDENTIALS_FILE" ]; then
        source "$CREDENTIALS_FILE"

        # Check missing games by season
        log_info "Checking missing games by season..."
        psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF 2>&1 | tee -a "$REPORT_FILE"
WITH expected AS (
    SELECT season, CASE
        WHEN season = 2019 THEN 971   -- COVID shortened
        WHEN season = 2020 THEN 1095  -- COVID shortened
        ELSE 1230                     -- Normal season
    END AS expected_games
    FROM generate_series(2016, 2024) AS season
),
actual AS (
    SELECT
        season,
        COUNT(*) AS actual_games,
        COUNT(CASE WHEN completed = true THEN 1 END) AS completed_games
    FROM games
    GROUP BY season
)
SELECT
    e.season,
    e.expected_games,
    COALESCE(a.actual_games, 0) AS actual_games,
    COALESCE(a.completed_games, 0) AS completed_games,
    e.expected_games - COALESCE(a.actual_games, 0) AS missing_games,
    ROUND(100.0 * COALESCE(a.actual_games, 0) / e.expected_games, 1) AS coverage_pct
FROM expected e
LEFT JOIN actual a ON e.season = a.season
ORDER BY e.season DESC;
EOF
    else
        log_warning "Database credentials not available - skipping database gap analysis"
    fi

    # Check S3 vs local sync status
    log_info "Checking S3 sync status..."

    # ESPN Play-by-Play
    if [ -d "$PROJECT_ROOT/data/nba_pbp" ]; then
        local_pbp_count=$(find "$PROJECT_ROOT/data/nba_pbp" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    else
        local_pbp_count=0
    fi

    s3_pbp_count=$(aws s3 ls s3://nba-sim-raw-data-lake/pbp/ --recursive 2>/dev/null | wc -l | tr -d ' ')

    echo "" | tee -a "$REPORT_FILE"
    echo "ESPN Play-by-Play Sync Status:" | tee -a "$REPORT_FILE"
    echo "  Local files:  $local_pbp_count" | tee -a "$REPORT_FILE"
    echo "  S3 files:     $s3_pbp_count" | tee -a "$REPORT_FILE"

    gap=$((local_pbp_count - s3_pbp_count))
    if [ "$gap" -gt 0 ]; then
        log_warning "$gap files NOT uploaded to S3" | tee -a "$REPORT_FILE"
    elif [ "$gap" -lt 0 ]; then
        log_info "$((gap * -1)) files in S3 but not local" | tee -a "$REPORT_FILE"
    else
        log_success "Local and S3 are in sync" | tee -a "$REPORT_FILE"
    fi

    log_success "Gap analysis complete"
}

# ==============================================================================
# Phase 3: Generate Collection Plan
# ==============================================================================

generate_collection_plan() {
    log_section "Phase 3: Data Collection Plan"

    log_info "Generating data collection plan based on gaps..."

    PLAN_FILE="$REPORTS_DIR/collection_plan_$TIMESTAMP.md"

    cat > "$PLAN_FILE" <<'PLANEOF'
# NBA Simulator - Data Collection Plan

**Generated:** $(date)
**Report:** Based on inventory and gap analysis

---

## Identified Gaps

### Critical Gaps (Block Analysis)
PLANEOF

    # Add database gap analysis if available
    if [ -f "$CREDENTIALS_FILE" ]; then
        source "$CREDENTIALS_FILE"

        echo "" >> "$PLAN_FILE"
        echo "**Missing Games by Season:**" >> "$PLAN_FILE"
        echo '```' >> "$PLAN_FILE"
        psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
            WITH expected AS (
                SELECT season, CASE
                    WHEN season = 2019 THEN 971
                    WHEN season = 2020 THEN 1095
                    ELSE 1230
                END AS expected_games
                FROM generate_series(2016, 2024) AS season
            ),
            actual AS (
                SELECT season, COUNT(*) AS actual_games
                FROM games
                GROUP BY season
            )
            SELECT
                e.season,
                e.expected_games - COALESCE(a.actual_games, 0) AS missing_games
            FROM expected e
            LEFT JOIN actual a ON e.season = a.season
            WHERE e.expected_games - COALESCE(a.actual_games, 0) > 0
            ORDER BY missing_games DESC;
        " 2>/dev/null >> "$PLAN_FILE" || echo "No database gaps found" >> "$PLAN_FILE"
        echo '```' >> "$PLAN_FILE"
    fi

    # Add recommended scrapers
    cat >> "$PLAN_FILE" <<'PLANEOF2'

---

## Recommended Actions

### Priority 1: Fill Critical Gaps

**If missing recent games (2020-2025):**
```bash
# Run Basketball Reference incremental scraper (2-3 hours)
bash scripts/etl/scrape_bbref_incremental.sh 2020 2025
```

**If missing advanced stats:**
```bash
# Run hoopR Phase 1B scraper (30-60 minutes)
bash scripts/etl/run_hoopr_phase1b.sh
```

### Priority 2: Historical Data

**If missing historical data (pre-2020):**
```bash
# Run Basketball Reference for older seasons (5-7 hours)
bash scripts/etl/scrape_bbref_incremental.sh 2010 2019
```

### Priority 3: S3 Sync

**If local files not in S3:**
```bash
# Sync ESPN data to S3
aws s3 sync data/nba_pbp/ s3://nba-sim-raw-data-lake/pbp/
aws s3 sync data/nba_box_score/ s3://nba-sim-raw-data-lake/box_scores/
aws s3 sync data/nba_team_stats/ s3://nba-sim-raw-data-lake/team_stats/
```

---

## Execution Commands

**Launch recommended scraper(s):**
```bash
# Interactive launcher (recommended)
bash scripts/monitoring/launch_scraper.sh

# Or use this pipeline manager
bash scripts/monitoring/data_pipeline_manager.sh collect
```

**Monitor progress:**
```bash
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10
```

---

## Next Steps

1. Review this plan
2. Choose which gaps to fill first
3. Execute scraper(s) via pipeline manager or manually
4. Validate results with: `bash scripts/monitoring/data_pipeline_manager.sh validate`

PLANEOF2

    log_success "Collection plan generated: $PLAN_FILE"

    # Display plan summary
    echo ""
    log_info "Plan Summary:"
    cat "$PLAN_FILE"
}

# ==============================================================================
# Phase 4: Execute Scrapers
# ==============================================================================

run_scraper_collection() {
    log_section "Phase 4: Execute Data Collection (Workflows #40, #42)"

    log_info "Available scrapers:"
    echo "  1. Basketball Reference (Recent: 2020-2025, ~2-3 hours)"
    echo "  2. Basketball Reference (Historical: 2010-2019, ~5-7 hours)"
    echo "  3. hoopR Phase 1B (2002-2025, ~30-60 minutes)"
    echo "  4. NBA API Comprehensive (1996-2025, ~5-6 hours)"
    echo "  5. Skip and use launch_scraper.sh manually"
    echo ""

    read -p "Select scraper to run (1-5): " scraper_choice

    case $scraper_choice in
        1)
            log_info "Launching Basketball Reference (Recent)..."
            nohup bash "$PROJECT_ROOT/scripts/etl/scrape_bbref_incremental.sh" 2020 2025 > /tmp/bbref_recent.log 2>&1 &
            SCRAPER_PID=$!
            log_success "Started Basketball Reference scraper (PID: $SCRAPER_PID)"
            log_info "Monitor: tail -f /tmp/bbref_recent.log"
            ;;
        2)
            log_info "Launching Basketball Reference (Historical)..."
            nohup bash "$PROJECT_ROOT/scripts/etl/scrape_bbref_incremental.sh" 2010 2019 > /tmp/bbref_historical.log 2>&1 &
            SCRAPER_PID=$!
            log_success "Started Basketball Reference scraper (PID: $SCRAPER_PID)"
            log_info "Monitor: tail -f /tmp/bbref_historical.log"
            ;;
        3)
            log_info "Launching hoopR Phase 1B..."
            nohup bash "$PROJECT_ROOT/scripts/etl/run_hoopr_phase1b.sh" > /tmp/hoopr_phase1b.log 2>&1 &
            SCRAPER_PID=$!
            log_success "Started hoopR scraper (PID: $SCRAPER_PID)"
            log_info "Monitor: tail -f /tmp/hoopr_phase1b.log"
            ;;
        4)
            log_info "Launching NBA API Comprehensive..."
            log_warning "Note: NBA API scraper has known error rate issues"
            read -p "Continue? (y/n): " confirm
            if [ "$confirm" = "y" ]; then
                nohup bash "$PROJECT_ROOT/scripts/etl/overnight_nba_api_comprehensive.sh" > /tmp/nba_api.log 2>&1 &
                SCRAPER_PID=$!
                log_success "Started NBA API scraper (PID: $SCRAPER_PID)"
                log_info "Monitor: tail -f /tmp/nba_api.log"
            else
                log_info "Skipped NBA API scraper"
            fi
            ;;
        5)
            log_info "Skipping automatic scraper launch"
            log_info "You can launch manually with: bash scripts/monitoring/launch_scraper.sh"
            return
            ;;
        *)
            log_error "Invalid selection"
            return 1
            ;;
    esac

    echo ""
    log_info "Scraper launched in background"
    log_info "Monitor progress with: bash scripts/monitoring/monitor_scrapers_inline.sh"
    log_info "Check status next session with: Workflow #38 (Overnight Scraper Handoff)"
}

# ==============================================================================
# Phase 5: Validation
# ==============================================================================

run_validation() {
    log_section "Phase 5: Data Quality Validation (Workflow #41)"

    log_info "Running data quality checks..."

    # Check scraper output exists
    log_info "Checking for scraper output directories..."

    output_dirs=(
        "/tmp/basketball_reference_incremental"
        "/tmp/hoopr_phase1"
        "/tmp/hoopr_phase1b"
        "/tmp/nba_api_comprehensive"
    )

    found_output=false
    for dir in "${output_dirs[@]}"; do
        if [ -d "$dir" ]; then
            file_count=$(find "$dir" -type f | wc -l | tr -d ' ')
            if [ "$file_count" -gt 0 ]; then
                log_success "Found $file_count files in $dir"
                found_output=true

                # Validate sample files
                log_info "Validating sample files from $(basename $dir)..."
                sample_files=$(find "$dir" -type f -name "*.json" | head -3)

                valid_count=0
                for file in $sample_files; do
                    if python -m json.tool "$file" > /dev/null 2>&1; then
                        ((valid_count++))
                    fi
                done

                log_success "$valid_count/3 sample files are valid JSON"
            fi
        fi
    done

    if [ "$found_output" = false ]; then
        log_warning "No scraper output found - may not have completed yet"
    fi

    # Run feature engineering readiness test
    log_info "Running feature engineering readiness test..."
    if [ -f "$PROJECT_ROOT/notebooks/test_feature_engineering.py" ]; then
        python "$PROJECT_ROOT/notebooks/test_feature_engineering.py" 2>&1 | tee -a "$REPORT_FILE"
    else
        log_warning "Feature engineering test not found - skipping"
    fi

    log_success "Validation complete"
}

# ==============================================================================
# Main Pipeline Orchestration
# ==============================================================================

run_full_pipeline() {
    log_section "NBA Simulator - Data Collection Pipeline"
    echo "Generated: $(date)" | tee "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"

    check_prerequisites
    run_data_inventory
    run_gap_analysis
    generate_collection_plan

    echo ""
    log_info "Inventory and gap analysis complete"
    log_info "Collection plan generated: see reports/data_pipeline/"
    echo ""
    read -p "Proceed with data collection? (y/n): " proceed

    if [ "$proceed" = "y" ]; then
        run_scraper_collection

        echo ""
        log_info "Scraper launched. Validation can be run after completion."
        log_info "Run validation with: bash scripts/monitoring/data_pipeline_manager.sh validate"
    else
        log_info "Skipping data collection. You can run manually later."
    fi

    log_success "Pipeline complete"
}

# ==============================================================================
# Main Entry Point
# ==============================================================================

MODE="${1:-full}"

case $MODE in
    status)
        check_prerequisites
        run_data_inventory
        run_gap_analysis
        ;;
    plan)
        check_prerequisites
        run_data_inventory
        run_gap_analysis
        generate_collection_plan
        ;;
    collect)
        check_prerequisites
        run_scraper_collection
        ;;
    validate)
        check_prerequisites
        run_validation
        ;;
    full)
        run_full_pipeline
        ;;
    *)
        echo "Usage: $0 [MODE]"
        echo ""
        echo "Modes:"
        echo "  status     - Check current data state (inventory + gaps)"
        echo "  plan       - Generate data collection plan"
        echo "  collect    - Execute scraper(s) to fill gaps"
        echo "  validate   - Verify data quality after collection"
        echo "  full       - Complete pipeline (default)"
        exit 1
        ;;
esac
