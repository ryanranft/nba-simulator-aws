#!/bin/bash

###############################################################################
# S3 Data Lake Manifest Generator
#
# Purpose: Generate comprehensive manifest of all S3 objects
# Usage: bash scripts/backup/generate_s3_manifest.sh
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
S3_BUCKET="nba-sim-raw-data-lake"
BACKUP_DIR="/Users/ryanranft/nba-simulator-aws/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MANIFEST_FILE="${BACKUP_DIR}/s3_manifest_${TIMESTAMP}.txt"
MANIFEST_JSON="${BACKUP_DIR}/s3_manifest_${TIMESTAMP}.json"
MANIFEST_SUMMARY="${BACKUP_DIR}/s3_manifest_summary_${TIMESTAMP}.txt"
TEMP_DIR="${BACKUP_DIR}/temp_manifest"

###############################################################################
# Pre-flight Checks
###############################################################################

log_info "Starting S3 manifest generation..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$TEMP_DIR"

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

log_success "Pre-flight checks passed"

###############################################################################
# Generate Full S3 Object List
###############################################################################

log_info "Fetching S3 object list from s3://${S3_BUCKET}..."
log_info "This may take several minutes for 146,115+ objects..."

# Get complete object list with metadata
aws s3api list-objects-v2 \
    --bucket "$S3_BUCKET" \
    --output json \
    --query 'Contents[].{Key:Key,Size:Size,LastModified:LastModified,ETag:ETag}' \
    > "$MANIFEST_JSON"

if [[ $? -ne 0 ]]; then
    log_error "Failed to fetch S3 object list"
    exit 1
fi

log_success "S3 object list retrieved"

###############################################################################
# Generate Human-Readable Manifest
###############################################################################

log_info "Generating human-readable manifest..."

# Create header
cat > "$MANIFEST_FILE" << 'EOF'
################################################################################
# S3 Data Lake Manifest
# NBA Simulator AWS Project
# Timestamp: TIMESTAMP_PLACEHOLDER
# Bucket: BUCKET_PLACEHOLDER
################################################################################

EOF

# Replace placeholders
sed -i.bak "s/TIMESTAMP_PLACEHOLDER/$(date '+%Y-%m-%d %H:%M:%S')/g" "$MANIFEST_FILE"
sed -i.bak "s/BUCKET_PLACEHOLDER/$S3_BUCKET/g" "$MANIFEST_FILE"
rm -f "${MANIFEST_FILE}.bak"

# Parse JSON and create formatted list
python3 << 'PYTHON_SCRIPT' >> "$MANIFEST_FILE"
import json
import sys
from datetime import datetime
from collections import defaultdict

# Read JSON manifest
with open('MANIFEST_JSON_PATH', 'r') as f:
    objects = json.load(f)

# Group by top-level directory
directories = defaultdict(list)
total_size = 0
total_count = 0

for obj in objects:
    key = obj['Key']
    size = obj['Size']
    last_modified = obj['LastModified']
    etag = obj['ETag']

    # Get top-level directory
    parts = key.split('/')
    top_dir = parts[0] if len(parts) > 1 else '(root)'

    directories[top_dir].append({
        'key': key,
        'size': size,
        'last_modified': last_modified,
        'etag': etag
    })

    total_size += size
    total_count += 1

# Print summary by directory
print("=" * 80)
print("SUMMARY BY DIRECTORY")
print("=" * 80)
print()

for dir_name in sorted(directories.keys()):
    dir_objects = directories[dir_name]
    dir_size = sum(obj['size'] for obj in dir_objects)
    dir_count = len(dir_objects)

    # Convert size to human-readable format
    if dir_size >= 1024**3:
        size_str = f"{dir_size / 1024**3:.2f} GB"
    elif dir_size >= 1024**2:
        size_str = f"{dir_size / 1024**2:.2f} MB"
    elif dir_size >= 1024:
        size_str = f"{dir_size / 1024:.2f} KB"
    else:
        size_str = f"{dir_size} bytes"

    print(f"{dir_name}/")
    print(f"  Files: {dir_count:,}")
    print(f"  Size: {size_str} ({dir_size:,} bytes)")
    print()

# Print overall totals
print("=" * 80)
print("OVERALL TOTALS")
print("=" * 80)
print()
if total_size >= 1024**3:
    total_size_str = f"{total_size / 1024**3:.2f} GB"
elif total_size >= 1024**2:
    total_size_str = f"{total_size / 1024**2:.2f} MB"
else:
    total_size_str = f"{total_size / 1024:.2f} KB"

print(f"Total Files: {total_count:,}")
print(f"Total Size: {total_size_str} ({total_size:,} bytes)")
print()

# Print detailed file list by directory
print("=" * 80)
print("DETAILED FILE LIST")
print("=" * 80)
print()

for dir_name in sorted(directories.keys()):
    dir_objects = directories[dir_name]

    print(f"\n### {dir_name}/ ({len(dir_objects):,} files)")
    print()

    # Sort by last modified (newest first)
    sorted_objects = sorted(dir_objects, key=lambda x: x['last_modified'], reverse=True)

    # Print first 10 and last 10 files to keep manifest manageable
    display_count = min(20, len(sorted_objects))

    for i, obj in enumerate(sorted_objects[:display_count]):
        size = obj['size']
        if size >= 1024**2:
            size_str = f"{size / 1024**2:.2f} MB"
        elif size >= 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size} B"

        # Parse timestamp
        ts = obj['last_modified']

        print(f"  {obj['key']}")
        print(f"    Size: {size_str:>12}  Modified: {ts}  ETag: {obj['etag'][:16]}...")

    if len(sorted_objects) > display_count:
        print(f"  ... and {len(sorted_objects) - display_count:,} more files")

    print()

PYTHON_SCRIPT

# Replace placeholder in Python script
sed -i.bak "s|MANIFEST_JSON_PATH|$MANIFEST_JSON|g" "$MANIFEST_FILE"
rm -f "${MANIFEST_FILE}.bak"

# Actually run the Python script (recreate with proper path)
python3 << PYTHON_SCRIPT >> "$MANIFEST_FILE"
import json
from collections import defaultdict

# Read JSON manifest
with open('$MANIFEST_JSON', 'r') as f:
    objects = json.load(f)

# Group by top-level directory
directories = defaultdict(list)
total_size = 0
total_count = 0

for obj in objects:
    key = obj['Key']
    size = obj['Size']
    last_modified = obj['LastModified']
    etag = obj['ETag']

    # Get top-level directory
    parts = key.split('/')
    top_dir = parts[0] if len(parts) > 1 else '(root)'

    directories[top_dir].append({
        'key': key,
        'size': size,
        'last_modified': last_modified,
        'etag': etag
    })

    total_size += size
    total_count += 1

# Print summary by directory
print("=" * 80)
print("SUMMARY BY DIRECTORY")
print("=" * 80)
print()

for dir_name in sorted(directories.keys()):
    dir_objects = directories[dir_name]
    dir_size = sum(obj['size'] for obj in dir_objects)
    dir_count = len(dir_objects)

    # Convert size to human-readable format
    if dir_size >= 1024**3:
        size_str = f"{dir_size / 1024**3:.2f} GB"
    elif dir_size >= 1024**2:
        size_str = f"{dir_size / 1024**2:.2f} MB"
    elif dir_size >= 1024:
        size_str = f"{dir_size / 1024:.2f} KB"
    else:
        size_str = f"{dir_size} bytes"

    print(f"{dir_name}/")
    print(f"  Files: {dir_count:,}")
    print(f"  Size: {size_str} ({dir_size:,} bytes)")
    print()

# Print overall totals
print("=" * 80)
print("OVERALL TOTALS")
print("=" * 80)
print()
if total_size >= 1024**3:
    total_size_str = f"{total_size / 1024**3:.2f} GB"
elif total_size >= 1024**2:
    total_size_str = f"{total_size / 1024**2:.2f} MB"
else:
    total_size_str = f"{total_size / 1024:.2f} KB"

print(f"Total Files: {total_count:,}")
print(f"Total Size: {total_size_str} ({total_size:,} bytes)")
print()

PYTHON_SCRIPT

log_success "Human-readable manifest created"

###############################################################################
# Upload to S3
###############################################################################

log_info "Uploading manifest files to S3..."

S3_MANIFEST_PREFIX="backups/manifests"

# Upload JSON manifest
aws s3 cp "$MANIFEST_JSON" \
    "s3://${S3_BUCKET}/${S3_MANIFEST_PREFIX}/s3_manifest_${TIMESTAMP}.json" \
    --storage-class STANDARD_IA

# Upload text manifest
aws s3 cp "$MANIFEST_FILE" \
    "s3://${S3_BUCKET}/${S3_MANIFEST_PREFIX}/s3_manifest_${TIMESTAMP}.txt" \
    --storage-class STANDARD_IA

log_success "Manifest files uploaded to S3"

###############################################################################
# Generate Checksum
###############################################################################

log_info "Generating checksums..."

if command -v shasum &> /dev/null; then
    shasum -a 256 "$MANIFEST_FILE" > "${MANIFEST_FILE}.sha256"
    shasum -a 256 "$MANIFEST_JSON" > "${MANIFEST_JSON}.sha256"
elif command -v sha256sum &> /dev/null; then
    sha256sum "$MANIFEST_FILE" > "${MANIFEST_FILE}.sha256"
    sha256sum "$MANIFEST_JSON" > "${MANIFEST_JSON}.sha256"
fi

log_success "Checksums generated"

###############################################################################
# Summary Report
###############################################################################

MANIFEST_SIZE=$(du -h "$MANIFEST_FILE" | cut -f1)
JSON_SIZE=$(du -h "$MANIFEST_JSON" | cut -f1)

cat << EOF

################################################################################
# S3 MANIFEST GENERATION COMPLETE
################################################################################

Timestamp:        $(date '+%Y-%m-%d %H:%M:%S')
S3 Bucket:        s3://${S3_BUCKET}

Local Files Created:
- Text Manifest:  $MANIFEST_FILE ($MANIFEST_SIZE)
- JSON Manifest:  $MANIFEST_JSON ($JSON_SIZE)
- Checksums:      ${MANIFEST_FILE}.sha256
                  ${MANIFEST_JSON}.sha256

S3 Files Uploaded:
- s3://${S3_BUCKET}/${S3_MANIFEST_PREFIX}/s3_manifest_${TIMESTAMP}.txt
- s3://${S3_BUCKET}/${S3_MANIFEST_PREFIX}/s3_manifest_${TIMESTAMP}.json

Storage Class:    STANDARD_IA (Infrequent Access)

################################################################################

EOF

log_success "S3 manifest generation completed successfully!"
log_info "Text manifest: $MANIFEST_FILE"
log_info "JSON manifest: $MANIFEST_JSON"

# Cleanup temp directory
rm -rf "$TEMP_DIR"

exit 0
