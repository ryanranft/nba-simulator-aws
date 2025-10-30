#!/bin/bash

###############################################################################
# Database Backup Script
#
# Purpose: Create PostgreSQL backup and upload to S3
# Usage: bash scripts/backup/create_db_backup.sh
# Author: Claude Code (NBA Simulator Project)
# Date: October 30, 2025
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
CREDENTIALS_FILE="/Users/ryanranft/nba-sim-credentials.env"
BACKUP_DIR="/Users/ryanranft/nba-simulator-aws/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="nba_simulator_backup_${TIMESTAMP}.dump"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"
S3_BACKUP_BUCKET="nba-sim-raw-data-lake"
S3_BACKUP_PREFIX="backups/database"
S3_BACKUP_PATH="s3://${S3_BACKUP_BUCKET}/${S3_BACKUP_PREFIX}/${BACKUP_FILENAME}"
CHECKSUM_FILE="${BACKUP_PATH}.sha256"

###############################################################################
# Pre-flight Checks
###############################################################################

log_info "Starting database backup process..."

# Check if credentials file exists
if [[ ! -f "$CREDENTIALS_FILE" ]]; then
    log_error "Credentials file not found: $CREDENTIALS_FILE"
    exit 1
fi

# Create backup directory if it doesn't exist
if [[ ! -d "$BACKUP_DIR" ]]; then
    log_info "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Load credentials
log_info "Loading database credentials..."
source "$CREDENTIALS_FILE"

# Verify required environment variables
if [[ -z "${RDS_HOST:-}" ]] || [[ -z "${RDS_USERNAME:-}" ]] || [[ -z "${RDS_PASSWORD:-}" ]] || [[ -z "${RDS_DATABASE:-}" ]]; then
    log_error "Missing required credentials. Please check $CREDENTIALS_FILE"
    log_error "Required: RDS_HOST, RDS_USERNAME, RDS_PASSWORD, RDS_DATABASE"
    exit 1
fi

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    log_error "pg_dump not found. Please install PostgreSQL client tools."
    exit 1
fi

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

log_success "Pre-flight checks passed"

###############################################################################
# Database Backup
###############################################################################

log_info "Creating PostgreSQL backup..."
log_info "Database: $RDS_DATABASE on $RDS_HOST"
log_info "Backup file: $BACKUP_PATH"

# Create backup using pg_dump
# -F c: Custom format (compressed)
# -v: Verbose
# -h: Host
# -U: Username
# -d: Database
# --no-password: Use PGPASSWORD environment variable
export PGPASSWORD="$RDS_PASSWORD"

if pg_dump -F c -v \
    -h "$RDS_HOST" \
    -U "$RDS_USERNAME" \
    -d "$RDS_DATABASE" \
    -f "$BACKUP_PATH"; then

    log_success "Database backup created successfully"
else
    log_error "Database backup failed"
    exit 1
fi

# Unset password from environment
unset PGPASSWORD

###############################################################################
# Backup Verification
###############################################################################

log_info "Verifying backup integrity..."

# Check file size
BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
BACKUP_SIZE_BYTES=$(stat -f%z "$BACKUP_PATH" 2>/dev/null || stat -c%s "$BACKUP_PATH")

if [[ $BACKUP_SIZE_BYTES -eq 0 ]]; then
    log_error "Backup file is empty"
    exit 1
fi

log_success "Backup size: $BACKUP_SIZE"

# Generate SHA256 checksum
log_info "Generating checksum..."
if command -v shasum &> /dev/null; then
    shasum -a 256 "$BACKUP_PATH" > "$CHECKSUM_FILE"
elif command -v sha256sum &> /dev/null; then
    sha256sum "$BACKUP_PATH" > "$CHECKSUM_FILE"
else
    log_warning "Neither shasum nor sha256sum found, skipping checksum"
fi

if [[ -f "$CHECKSUM_FILE" ]]; then
    CHECKSUM=$(cut -d' ' -f1 "$CHECKSUM_FILE")
    log_success "Checksum: $CHECKSUM"
fi

###############################################################################
# Upload to S3
###############################################################################

log_info "Uploading backup to S3..."
log_info "S3 location: $S3_BACKUP_PATH"

if aws s3 cp "$BACKUP_PATH" "$S3_BACKUP_PATH" --storage-class STANDARD_IA; then
    log_success "Backup uploaded to S3"
else
    log_error "S3 upload failed"
    exit 1
fi

# Upload checksum file if it exists
if [[ -f "$CHECKSUM_FILE" ]]; then
    log_info "Uploading checksum file..."
    aws s3 cp "$CHECKSUM_FILE" "${S3_BACKUP_PATH}.sha256" --storage-class STANDARD_IA
    log_success "Checksum uploaded to S3"
fi

###############################################################################
# Verify S3 Upload
###############################################################################

log_info "Verifying S3 upload..."

# Get S3 file size
S3_SIZE=$(aws s3 ls "$S3_BACKUP_PATH" | awk '{print $3}')

if [[ "$S3_SIZE" -eq "$BACKUP_SIZE_BYTES" ]]; then
    log_success "S3 upload verified (size matches)"
else
    log_warning "Size mismatch: Local=$BACKUP_SIZE_BYTES, S3=$S3_SIZE"
fi

###############################################################################
# Database Statistics
###############################################################################

log_info "Gathering database statistics..."

# Connect to database and get table counts
export PGPASSWORD="$RDS_PASSWORD"

STATS_OUTPUT="${BACKUP_DIR}/db_stats_${TIMESTAMP}.txt"

cat > "${STATS_OUTPUT}" << 'EOF'
################################################################################
# Database Statistics
# Timestamp: TIMESTAMP_PLACEHOLDER
# Database: DATABASE_PLACEHOLDER
# Backup File: BACKUP_FILE_PLACEHOLDER
################################################################################

EOF

# Replace placeholders
sed -i.bak "s/TIMESTAMP_PLACEHOLDER/$(date '+%Y-%m-%d %H:%M:%S')/g" "${STATS_OUTPUT}"
sed -i.bak "s/DATABASE_PLACEHOLDER/$RDS_DATABASE/g" "${STATS_OUTPUT}"
sed -i.bak "s|BACKUP_FILE_PLACEHOLDER|$BACKUP_PATH|g" "${STATS_OUTPUT}"
rm -f "${STATS_OUTPUT}.bak"

# Get table list and row counts
psql -h "$RDS_HOST" -U "$RDS_USERNAME" -d "$RDS_DATABASE" \
    -c "\dt" \
    -c "SELECT schemaname, tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 20;" \
    >> "${STATS_OUTPUT}" 2>/dev/null || log_warning "Could not retrieve detailed statistics"

unset PGPASSWORD

log_success "Statistics saved to: $STATS_OUTPUT"

###############################################################################
# Summary Report
###############################################################################

cat << EOF

################################################################################
# BACKUP SUMMARY
################################################################################

Timestamp:        $(date '+%Y-%m-%d %H:%M:%S')
Database:         $RDS_DATABASE
Host:             $RDS_HOST
Backup File:      $BACKUP_PATH
Backup Size:      $BACKUP_SIZE ($BACKUP_SIZE_BYTES bytes)
Checksum:         ${CHECKSUM:-N/A}
S3 Location:      $S3_BACKUP_PATH
Statistics File:  $STATS_OUTPUT

Local Files Created:
- $BACKUP_PATH
- $CHECKSUM_FILE (if created)
- $STATS_OUTPUT

S3 Files Uploaded:
- $S3_BACKUP_PATH
- ${S3_BACKUP_PATH}.sha256 (if created)

Storage Class:    STANDARD_IA (Infrequent Access)

################################################################################
# RESTORE INSTRUCTIONS
################################################################################

To restore this backup:

1. Download from S3:
   aws s3 cp $S3_BACKUP_PATH ./restore_backup.dump

2. Restore to database:
   pg_restore -h <HOST> -U <USERNAME> -d <DATABASE> -v restore_backup.dump

3. Verify restoration:
   psql -h <HOST> -U <USERNAME> -d <DATABASE> -c "\dt"

For more details, see: docs/claude_workflows/workflow_descriptions/19_backup_recovery.md

################################################################################

EOF

log_success "Database backup completed successfully!"
log_info "Local backup: $BACKUP_PATH"
log_info "S3 backup: $S3_BACKUP_PATH"

exit 0
