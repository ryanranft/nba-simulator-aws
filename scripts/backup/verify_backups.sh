#!/bin/bash

###############################################################################
# Backup Verification Script
#
# Purpose: Verify integrity of all backup files and S3 uploads
# Usage: bash scripts/backup/verify_backups.sh
# Author: Claude Code (NBA Simulator Project)
# Date: October 30, 2025
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
BACKUP_DIR="/Users/ryanranft/nba-simulator-aws/backups"
S3_BUCKET="nba-sim-raw-data-lake"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

###############################################################################
# Verification Functions
###############################################################################

verify_local_file() {
    local file="$1"
    local description="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ -f "$file" ]]; then
        local size=$(du -h "$file" | cut -f1)
        log_success "$description exists ($size)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$description NOT FOUND"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

verify_checksum() {
    local file="$1"
    local checksum_file="$2"
    local description="$3"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ ! -f "$checksum_file" ]]; then
        log_warning "$description checksum file not found"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi

    if shasum -a 256 -c "$checksum_file" > /dev/null 2>&1; then
        log_success "$description checksum verified"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$description checksum FAILED"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

verify_s3_object() {
    local s3_path="$1"
    local description="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if aws s3 ls "$s3_path" > /dev/null 2>&1; then
        local size=$(aws s3 ls "$s3_path" | awk '{print $3}')
        log_success "$description exists in S3 ($size bytes)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$description NOT FOUND in S3"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

verify_git_tag() {
    local tag="$1"
    local description="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if git tag -l "$tag" | grep -q "$tag"; then
        local commit=$(git rev-list -n 1 "$tag" | cut -c1-8)
        log_success "$description exists (commit: $commit)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$description NOT FOUND"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

###############################################################################
# Main Verification
###############################################################################

log_info "Starting backup verification..."
echo ""

###############################################################################
# 1. Database Backup
###############################################################################

echo "=" * 80
log_info "Verifying Database Backup..."
echo ""

DB_BACKUP="${BACKUP_DIR}/nba_simulator_backup_20251030_145942.dump"
DB_CHECKSUM="${DB_BACKUP}.sha256"
S3_DB_PATH="s3://${S3_BUCKET}/backups/database/nba_simulator_backup_20251030_145942.dump"

verify_local_file "$DB_BACKUP" "Database backup"
verify_checksum "$DB_BACKUP" "$DB_CHECKSUM" "Database backup"
verify_s3_object "$S3_DB_PATH" "Database backup"

# Verify database statistics
DB_STATS="${BACKUP_DIR}/db_stats_20251030_145942.txt"
verify_local_file "$DB_STATS" "Database statistics"

echo ""

###############################################################################
# 2. S3 Manifest
###############################################################################

echo "=" * 80
log_info "Verifying S3 Manifest..."
echo ""

S3_MANIFEST_JSON="${BACKUP_DIR}/s3_manifest_20251030_150706.json"
S3_MANIFEST_TXT="${BACKUP_DIR}/s3_manifest_20251030_150706.txt"
S3_MANIFEST_JSON_CHECKSUM="${S3_MANIFEST_JSON}.sha256"
S3_MANIFEST_TXT_CHECKSUM="${S3_MANIFEST_TXT}.sha256"
S3_JSON_PATH="s3://${S3_BUCKET}/backups/manifests/s3_manifest_20251030_150706.json"
S3_TXT_PATH="s3://${S3_BUCKET}/backups/manifests/s3_manifest_20251030_150706.txt"

verify_local_file "$S3_MANIFEST_JSON" "S3 manifest (JSON)"
verify_local_file "$S3_MANIFEST_TXT" "S3 manifest (Text)"
verify_checksum "$S3_MANIFEST_JSON" "$S3_MANIFEST_JSON_CHECKSUM" "S3 manifest (JSON)"
verify_checksum "$S3_MANIFEST_TXT" "$S3_MANIFEST_TXT_CHECKSUM" "S3 manifest (Text)"
verify_s3_object "$S3_JSON_PATH" "S3 manifest (JSON)"
verify_s3_object "$S3_TXT_PATH" "S3 manifest (Text)"

echo ""

###############################################################################
# 3. Code Repository
###############################################################################

echo "=" * 80
log_info "Verifying Code Repository Snapshot..."
echo ""

CODE_ARCHIVE="${BACKUP_DIR}/nba_simulator_pre_refactor_20251030.tar.gz"
S3_CODE_PATH="s3://${S3_BUCKET}/backups/code/nba_simulator_pre_refactor_20251030.tar.gz"

verify_local_file "$CODE_ARCHIVE" "Code archive"
verify_s3_object "$S3_CODE_PATH" "Code archive"
verify_git_tag "pre-refactor-v1.0" "Git tag"

# Verify archive contents
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if tar -tzf "$CODE_ARCHIVE" > /dev/null 2>&1; then
    file_count=$(tar -tzf "$CODE_ARCHIVE" | wc -l | tr -d ' ')
    log_success "Code archive is valid ($file_count files)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Code archive is corrupted"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

###############################################################################
# 4. Configuration Backup
###############################################################################

echo "=" * 80
log_info "Verifying Configuration Backup..."
echo ""

CONFIG_ARCHIVE="${BACKUP_DIR}/config_backup_20251030_152145.tar.gz"
CONFIG_CHECKSUM="${CONFIG_ARCHIVE}.sha256"
S3_CONFIG_PATH="s3://${S3_BUCKET}/backups/config/config_backup_20251030_152145.tar.gz"

verify_local_file "$CONFIG_ARCHIVE" "Configuration archive"
verify_checksum "$CONFIG_ARCHIVE" "$CONFIG_CHECKSUM" "Configuration archive"
verify_s3_object "$S3_CONFIG_PATH" "Configuration archive"

# Verify AWS state documentation
CONFIG_DIR="${BACKUP_DIR}/config_20251030_152145"
AWS_STATE="${CONFIG_DIR}/aws_state.txt"
verify_local_file "$AWS_STATE" "AWS state documentation"

# Verify archive contents
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if tar -tzf "$CONFIG_ARCHIVE" > /dev/null 2>&1; then
    file_count=$(tar -tzf "$CONFIG_ARCHIVE" | wc -l | tr -d ' ')
    log_success "Configuration archive is valid ($file_count files)"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "Configuration archive is corrupted"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

###############################################################################
# 5. System State Snapshot
###############################################################################

echo "=" * 80
log_info "Verifying System State Snapshot..."
echo ""

SNAPSHOT="${BACKUP_DIR}/system_state_snapshot_20251030_152505.json"
SNAPSHOT_CHECKSUM="${SNAPSHOT}.sha256"
S3_SNAPSHOT_PATH="s3://${S3_BUCKET}/backups/snapshots/system_state_snapshot_20251030_152505.json"

verify_local_file "$SNAPSHOT" "System state snapshot"
verify_checksum "$SNAPSHOT" "$SNAPSHOT_CHECKSUM" "System state snapshot"
verify_s3_object "$S3_SNAPSHOT_PATH" "System state snapshot"

# Verify JSON format
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if python3 -c "import json; json.load(open('$SNAPSHOT'))" > /dev/null 2>&1; then
    log_success "System state snapshot JSON is valid"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "System state snapshot JSON is invalid"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

###############################################################################
# 6. Documentation
###############################################################################

echo "=" * 80
log_info "Verifying Documentation..."
echo ""

PHASE0_DOC="/Users/ryanranft/nba-simulator-aws/PHASE_0_DISCOVERY_COMPLETE.md"
BACKUP_MANIFEST="/Users/ryanranft/nba-simulator-aws/BACKUP_MANIFEST.md"

verify_local_file "$PHASE0_DOC" "Phase 0 discovery documentation"
verify_local_file "$BACKUP_MANIFEST" "Backup manifest"

echo ""

###############################################################################
# Summary Report
###############################################################################

echo "=" * 80
echo "=" * 80
echo ""
echo "BACKUP VERIFICATION SUMMARY"
echo ""
echo "=" * 80
echo "=" * 80
echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo "Passed:       $PASSED_CHECKS"
echo "Failed:       $FAILED_CHECKS"
echo ""

if [[ $FAILED_CHECKS -eq 0 ]]; then
    echo -e "${GREEN}✅ ALL VERIFICATIONS PASSED${NC}"
    echo ""
    echo "All backups are intact and verified. System is ready for Phase 1 refactoring."
    echo ""
else
    echo -e "${RED}❌ VERIFICATION FAILED${NC}"
    echo ""
    echo "Some backups could not be verified. Please review errors above."
    echo ""
fi

echo "=" * 80
echo ""

# Exit with appropriate code
if [[ $FAILED_CHECKS -eq 0 ]]; then
    exit 0
else
    exit 1
fi
