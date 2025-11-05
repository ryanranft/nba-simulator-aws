#!/bin/bash
################################################################################
# Overnight Multi-Source Unified Database Workflow
#
# Complete automation for nightly data collection, quality tracking, and
# unified database maintenance.
#
# Strategy:
# 1. Scrape from each source independently (maintains data purity)
#    - ESPN: Last 14 days of games (play-by-play)
#    - hoopR: Last 7 days of games (play-by-play)
#    - Basketball Reference: Current season aggregate stats (season totals + advanced)
# 2. Update source databases (ESPN, hoopR, Basketball Reference remain pure)
# 3. Extract/update game ID mappings
# 4. Rebuild unified database with quality scores
# 5. Run discrepancy detection
# 6. Export ML-ready quality dataset
# 7. Generate quality reports
# 8. Send completion notification
#
# Schedule: Daily at 3:00 AM (games are final, web traffic is low)
# Cron: 0 3 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/workflows/overnight_multi_source_unified.sh
#
# Version: 1.1
# Created: October 9, 2025
# Updated: October 10, 2025 - Added Basketball Reference incremental scraping
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/overnight"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/overnight_unified_$TIMESTAMP.log"

# Database paths
ESPN_DB="/tmp/espn_local.db"
HOOPR_DB="/tmp/hoopr_local.db"
UNIFIED_DB="/tmp/unified_nba.db"

# Output paths
REPORTS_DIR="$PROJECT_DIR/reports"
ML_QUALITY_DIR="$PROJECT_DIR/data/ml_quality"

# Email settings (optional)
SEND_EMAIL=false
EMAIL_RECIPIENT="your-email@example.com"

################################################################################
# Logging Functions
################################################################################

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "========================================================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "========================================================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

################################################################################
# Setup
################################################################################

setup() {
    log_section "OVERNIGHT MULTI-SOURCE UNIFIED WORKFLOW"

    # Create log directory
    mkdir -p "$LOG_DIR"
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$ML_QUALITY_DIR"

    log "Log file: $LOG_FILE"
    log "Project directory: $PROJECT_DIR"
    log ""

    # Change to project directory
    cd "$PROJECT_DIR"

    # Activate conda environment
    log "Activating conda environment: nba-aws"
    eval "$(conda shell.bash hook)"
    conda activate nba-aws

    # Load credentials
    log "Loading credentials..."
    source /Users/ryanranft/nba-sim-credentials.env

    log "✓ Setup complete"
}

################################################################################
# Step 1: Scrape ESPN Data
################################################################################

scrape_espn() {
    log_section "STEP 1: SCRAPE ESPN DATA (INCREMENTAL)"

    # Use incremental scraper (only recent games, NOT all 27 seasons)
    if [ -f "$PROJECT_DIR/scripts/etl/espn_incremental_scraper.py" ]; then
        log "Running ESPN incremental scraper (last 14 days)..."

        if python scripts/etl/espn_incremental_scraper.py >> "$LOG_FILE" 2>&1; then
            log "✓ ESPN incremental scraping complete"
        else
            log_error "ESPN scraping failed (non-fatal, continuing)"
        fi
    else
        log "⚠️  ESPN incremental scraper not found, skipping"
    fi
}

################################################################################
# Step 2: Scrape hoopR Data
################################################################################

scrape_hoopr() {
    log_section "STEP 2: SCRAPE HOOPR DATA (INCREMENTAL)"

    # Use incremental scraper (only recent games, NOT all seasons)
    if [ -f "$PROJECT_DIR/scripts/etl/hoopr_incremental_scraper.py" ]; then
        log "Running hoopR incremental scraper (last 7 days)..."

        if python scripts/etl/hoopr_incremental_scraper.py >> "$LOG_FILE" 2>&1; then
            log "✓ hoopR incremental scraping complete"
        else
            log_error "hoopR scraping failed (non-fatal, continuing)"
        fi
    else
        log "⚠️  hoopR incremental scraper not found, skipping"
    fi
}

################################################################################
# Step 2.5: Scrape Basketball Reference Aggregate Data
################################################################################

scrape_basketball_reference() {
    log_section "STEP 2.5: SCRAPE BASKETBALL REFERENCE AGGREGATE DATA"

    # Scrape current season aggregate stats (season totals + advanced stats)
    if [ -f "$PROJECT_DIR/scripts/etl/basketball_reference_incremental_scraper.py" ]; then
        log "Running Basketball Reference incremental scraper (current season)..."

        if python scripts/etl/basketball_reference_incremental_scraper.py --upload-to-s3 >> "$LOG_FILE" 2>&1; then
            log "✓ Basketball Reference scraping complete"

            # Re-integrate into local database
            log "Re-integrating Basketball Reference aggregate data..."
            if python scripts/etl/integrate_basketball_reference_aggregate.py >> "$LOG_FILE" 2>&1; then
                log "✓ Basketball Reference database updated"
            else
                log_error "Basketball Reference integration failed (non-fatal, continuing)"
            fi
        else
            log_error "Basketball Reference scraping failed (non-fatal, continuing)"
        fi
    else
        log "⚠️  Basketball Reference incremental scraper not found, skipping"
    fi
}

################################################################################
# Step 3: Update Game ID Mappings
################################################################################

update_mappings() {
    log_section "STEP 3: UPDATE GAME ID MAPPINGS"

    log "Extracting ESPN-hoopR game ID mappings..."

    if python scripts/mapping/extract_espn_hoopr_game_mapping.py >> "$LOG_FILE" 2>&1; then
        log "✓ Game ID mappings updated"

        # Log mapping count
        mapping_count=$(python -c "import json; data = json.load(open('scripts/mapping/espn_hoopr_game_mapping.json')); print(data['metadata']['total_mappings'])")
        log "  Total mappings: $mapping_count"
    else
        log_error "Mapping extraction failed"
        return 1
    fi
}

################################################################################
# Step 4: Rebuild Unified Database
################################################################################

rebuild_unified() {
    log_section "STEP 4: REBUILD UNIFIED DATABASE"

    log "Rebuilding unified database from source databases..."

    if python scripts/etl/build_unified_database.py >> "$LOG_FILE" 2>&1; then
        log "✓ Unified database rebuilt"

        # Log game count
        game_count=$(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM source_coverage;")
        log "  Total games in unified DB: $game_count"
    else
        log_error "Unified database rebuild failed"
        return 1
    fi
}

################################################################################
# Step 5: Detect Discrepancies
################################################################################

detect_discrepancies() {
    log_section "STEP 5: DETECT DATA DISCREPANCIES"

    log "Running discrepancy detection on dual-source games..."

    # Clear existing discrepancies (will be rebuilt)
    sqlite3 "$UNIFIED_DB" "DELETE FROM data_quality_discrepancies;"
    log "  Cleared existing discrepancies"

    if python scripts/validation/detect_data_discrepancies.py >> "$LOG_FILE" 2>&1; then
        log "✓ Discrepancy detection complete"

        # Log discrepancy count
        disc_count=$(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM data_quality_discrepancies;")
        games_with_disc=$(sqlite3 "$UNIFIED_DB" "SELECT COUNT(DISTINCT game_id) FROM data_quality_discrepancies;")
        log "  Total discrepancies: $disc_count"
        log "  Games with discrepancies: $games_with_disc"
    else
        log_error "Discrepancy detection failed"
        return 1
    fi
}

################################################################################
# Step 6: Export ML Quality Dataset
################################################################################

export_ml_dataset() {
    log_section "STEP 6: EXPORT ML QUALITY DATASET"

    log "Exporting ML-ready quality dataset..."

    if python scripts/validation/export_ml_quality_dataset.py >> "$LOG_FILE" 2>&1; then
        log "✓ ML quality dataset exported"

        # Log file sizes
        json_file=$(ls -t "$ML_QUALITY_DIR"/ml_quality_dataset_*.json 2>/dev/null | head -1)
        csv_file=$(ls -t "$ML_QUALITY_DIR"/ml_quality_dataset_*.csv 2>/dev/null | head -1)

        if [ -f "$json_file" ]; then
            json_size=$(du -h "$json_file" | cut -f1)
            log "  JSON: $json_size"
        fi

        if [ -f "$csv_file" ]; then
            csv_size=$(du -h "$csv_file" | cut -f1)
            log "  CSV: $csv_size"
        fi
    else
        log_error "ML dataset export failed"
        return 1
    fi
}

################################################################################
# Step 7: Generate Quality Reports
################################################################################

generate_reports() {
    log_section "STEP 7: GENERATE QUALITY REPORTS"

    log "Generating quality report..."

    # Create daily quality report
    report_file="$REPORTS_DIR/daily_quality_report_$(date +%Y%m%d).md"

    cat > "$report_file" <<EOF
# Daily Data Quality Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')

## Database Statistics

### Source Databases
- **ESPN:** $(sqlite3 "$ESPN_DB" "SELECT COUNT(*) FROM games WHERE has_pbp = 1;" 2>/dev/null || echo "N/A") games
- **hoopR:** $(sqlite3 "$HOOPR_DB" "SELECT COUNT(DISTINCT game_id) FROM play_by_play;" 2>/dev/null || echo "N/A") games

### Unified Database
- **Total games:** $(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM source_coverage;")
- **Dual-source games:** $(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 1 AND has_hoopr = 1;")
- **Games with discrepancies:** $(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM source_coverage WHERE has_discrepancies = 1;")

## Quality Distribution

\`\`\`
$(sqlite3 "$UNIFIED_DB" "SELECT
    CASE
        WHEN quality_score >= 90 THEN 'High (90-100)'
        WHEN quality_score >= 70 THEN 'Medium (70-89)'
        ELSE 'Low (<70)'
    END as quality,
    COUNT(*) as games,
    ROUND(AVG(quality_score), 1) as avg_score
FROM quality_scores
GROUP BY quality
ORDER BY avg_score DESC;")
\`\`\`

## Recent Discrepancies

\`\`\`
$(sqlite3 "$UNIFIED_DB" "SELECT
    field_name,
    COUNT(*) as count,
    severity
FROM data_quality_discrepancies
WHERE detected_at > datetime('now', '-1 day')
GROUP BY field_name, severity
ORDER BY count DESC
LIMIT 10;")
\`\`\`

## Source Recommendations

\`\`\`
$(sqlite3 "$UNIFIED_DB" "SELECT
    recommended_source,
    COUNT(*) as games
FROM quality_scores
GROUP BY recommended_source
ORDER BY games DESC;")
\`\`\`

---

**Next Steps:**
- Review discrepancies in high-severity games
- Monitor quality score trends
- Validate new data additions

**Log File:** $LOG_FILE
EOF

    log "✓ Quality report generated: $report_file"
}

################################################################################
# Step 8: Database Backup
################################################################################

backup_databases() {
    log_section "STEP 8: BACKUP DATABASES"

    backup_dir="$PROJECT_DIR/backups/$(date +%Y%m%d)"
    mkdir -p "$backup_dir"

    log "Backing up databases to: $backup_dir"

    # Backup unified database
    if [ -f "$UNIFIED_DB" ]; then
        cp "$UNIFIED_DB" "$backup_dir/unified_nba.db"
        log "✓ Unified database backed up"
    fi

    # Optional: Backup source databases (large files)
    # cp "$ESPN_DB" "$backup_dir/espn_local.db"
    # cp "$HOOPR_DB" "$backup_dir/hoopr_local.db"

    # Keep only last 7 days of backups
    find "$PROJECT_DIR/backups" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    log "✓ Old backups cleaned (kept last 7 days)"
}

################################################################################
# Step 9: Send Notification (Optional)
################################################################################

send_notification() {
    log_section "STEP 9: SEND NOTIFICATION"

    if [ "$SEND_EMAIL" = true ]; then
        log "Sending email notification to: $EMAIL_RECIPIENT"

        # Create email body
        email_subject="NBA Simulator: Overnight Workflow Complete - $(date +%Y-%m-%d)"
        email_body="Overnight multi-source unified database workflow completed successfully.

Log file: $LOG_FILE
Report: $REPORTS_DIR/daily_quality_report_$(date +%Y%m%d).md

Summary:
- Total games: $(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM source_coverage;")
- Dual-source: $(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 1 AND has_hoopr = 1;")
- Discrepancies: $(sqlite3 "$UNIFIED_DB" "SELECT COUNT(DISTINCT game_id) FROM data_quality_discrepancies;")

Completed: $(date '+%Y-%m-%d %H:%M:%S')
"

        # Send email using mail command (macOS)
        echo "$email_body" | mail -s "$email_subject" "$EMAIL_RECIPIENT" 2>&1 | tee -a "$LOG_FILE"

        log "✓ Email sent"
    else
        log "Email notification disabled (set SEND_EMAIL=true to enable)"
    fi
}

################################################################################
# Cleanup
################################################################################

cleanup() {
    log_section "CLEANUP"

    # Vacuum databases to reclaim space
    log "Vacuuming databases..."
    sqlite3 "$UNIFIED_DB" "VACUUM;" 2>&1 | tee -a "$LOG_FILE"

    # Clean old log files (keep last 30 days)
    find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    log "✓ Old logs cleaned (kept last 30 days)"
}

################################################################################
# Error Handler
################################################################################

error_handler() {
    log_error "Workflow failed at step: $1"
    log "Check log file for details: $LOG_FILE"

    if [ "$SEND_EMAIL" = true ]; then
        echo "Overnight workflow FAILED at step: $1. Check log: $LOG_FILE" | \
            mail -s "NBA Simulator: Overnight Workflow FAILED" "$EMAIL_RECIPIENT"
    fi

    exit 1
}

################################################################################
# Main Execution
################################################################################

main() {
    # Setup
    setup || error_handler "Setup"

    # Step 1: Scrape ESPN
    scrape_espn || log "⚠️  ESPN scraping skipped or failed (non-fatal)"

    # Step 2: Scrape hoopR
    scrape_hoopr || log "⚠️  hoopR scraping skipped or failed (non-fatal)"

    # Step 2.5: Scrape Basketball Reference
    scrape_basketball_reference || log "⚠️  Basketball Reference scraping skipped or failed (non-fatal)"

    # Step 3: Update mappings
    update_mappings || error_handler "Update Mappings"

    # Step 4: Rebuild unified database
    rebuild_unified || error_handler "Rebuild Unified Database"

    # Step 5: Detect discrepancies
    detect_discrepancies || error_handler "Detect Discrepancies"

    # Step 6: Export ML dataset
    export_ml_dataset || error_handler "Export ML Dataset"

    # Step 7: Generate reports
    generate_reports || error_handler "Generate Reports"

    # Step 8: Backup databases
    backup_databases || log "⚠️  Backup failed (non-fatal)"

    # Step 9: Send notification
    send_notification || log "⚠️  Notification failed (non-fatal)"

    # Cleanup
    cleanup || log "⚠️  Cleanup failed (non-fatal)"

    # Step 10: Check and recover long-running scrapers
    log_section "STEP 10: CHECK LONG-RUNNING SCRAPERS"

    if [ -f "$PROJECT_DIR/scripts/monitoring/check_and_recover_scrapers.sh" ]; then
        log "Checking health of Basketball Reference and NBA API scrapers..."

        if bash "$PROJECT_DIR/scripts/monitoring/check_and_recover_scrapers.sh" >> "$LOG_FILE" 2>&1; then
            log "✓ All long-running scrapers healthy or recovered"
        else
            log "⚠️  Some scraper recovery attempts failed (non-fatal)"
            log "  Check recovery log for details"
        fi
    else
        log "⚠️  Scraper health check script not found, skipping"
    fi

    # Success
    log_section "WORKFLOW COMPLETE"
    log "✓ All steps completed successfully!"
    log "Total duration: $(($(date +%s) - $(date -r "$LOG_FILE" +%s))) seconds"
    log "Log file: $LOG_FILE"
}

# Run main workflow
main
