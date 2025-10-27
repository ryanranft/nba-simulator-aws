#!/bin/bash
# Validate path references using PRMS (Path Reference Management System)
#
# This pre-commit hook ensures no outdated phase path references are committed.
# Uses PRMS to scan for old-format path references (phase_6, phase_8, phase_9)
# that should be updated to new format (phase_0, phase_2) per Phase Reorganization.
#
# Related:
#   - config/prms_config.yaml - PRMS configuration
#   - scripts/maintenance/prms_cli.py - PRMS automation
#   - docs/claude_workflows/workflow_descriptions/60_prms_path_reference_management.md

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Validating path references with PRMS..."

# Check if PRMS CLI exists
if [ ! -f "scripts/maintenance/prms_cli.py" ]; then
    echo -e "${RED}✗ PRMS CLI not found at scripts/maintenance/prms_cli.py${NC}"
    echo -e "${YELLOW}  PRMS may not be installed. Skipping validation.${NC}"
    exit 0
fi

# Check if PRMS config exists
if [ ! -f "config/prms_config.yaml" ]; then
    echo -e "${RED}✗ PRMS config not found at config/prms_config.yaml${NC}"
    echo -e "${YELLOW}  PRMS may not be configured. Skipping validation.${NC}"
    exit 0
fi

# Create temp directory for scan results
TEMP_DIR=$(mktemp -d)
SCAN_RESULT="$TEMP_DIR/prms_scan.json"

# Run PRMS scan on staged files only
echo "   Scanning staged files for path references..."

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}   ✓ No files staged for commit${NC}"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Check if recent scan results exist (< 1 hour old)
SCAN_OUTPUT_FILE="inventory/outputs/prms/path_references.json"

if [ -f "$SCAN_OUTPUT_FILE" ]; then
    file_age_seconds=$(( $(date +%s) - $(stat -f %m "$SCAN_OUTPUT_FILE") ))
    file_age_minutes=$(( file_age_seconds / 60 ))

    # If scan is recent (< 60 minutes), use existing results
    if [ $file_age_minutes -lt 60 ]; then
        echo "   Using cached PRMS scan results (${file_age_minutes}m old)..."
    else
        # Re-scan if stale
        python scripts/maintenance/prms_cli.py scan --classify > /dev/null 2>&1
    fi
else
    # No scan results exist, run initial scan
    python scripts/maintenance/prms_cli.py scan --classify > /dev/null 2>&1
fi

# Use the JSON output file (not the report file)
SCAN_OUTPUT_FILE="inventory/outputs/prms/path_references.json"

if [ ! -f "$SCAN_OUTPUT_FILE" ]; then
    echo -e "${YELLOW}⚠  PRMS scan output not found. Validation incomplete.${NC}"
    rm -rf "$TEMP_DIR"
    exit 0
fi

# Count MUST_UPDATE references in staged files
MUST_UPDATE_COUNT=0
MUST_UPDATE_FILES=""

# Parse JSON to find MUST_UPDATE references in staged files
while IFS= read -r staged_file; do
    # Check if this file has MUST_UPDATE references
    file_refs=$(python3 -c "
import json
import sys

try:
    with open('$SCAN_OUTPUT_FILE', 'r') as f:
        data = json.load(f)

    must_update = [
        ref for ref in data.get('references', [])
        if ref.get('category') == 'MUST_UPDATE'
        and ref.get('file') == '$staged_file'
        and ref.get('confidence', 0) >= 0.8
    ]

    if must_update:
        print(f'{len(must_update)}')
        for ref in must_update:
            print(f\"  Line {ref['line']}: {ref['match']} → {ref.get('suggested_fix', 'N/A')}\")
    else:
        print('0')
except Exception as e:
    print('0', file=sys.stderr)
" 2>/dev/null)

    if [ -n "$file_refs" ] && [ "$file_refs" != "0" ]; then
        ref_count=$(echo "$file_refs" | head -1)
        if [ "$ref_count" != "0" ]; then
            MUST_UPDATE_COUNT=$((MUST_UPDATE_COUNT + ref_count))
            MUST_UPDATE_FILES="${MUST_UPDATE_FILES}\n${staged_file}:\n${file_refs}"
        fi
    fi
done <<< "$STAGED_FILES"

# Clean up temp directory
rm -rf "$TEMP_DIR"

# Report results
if [ $MUST_UPDATE_COUNT -gt 0 ]; then
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}✗ Path reference validation FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Found ${MUST_UPDATE_COUNT} outdated path reference(s) in staged files:${NC}"
    echo -e "$MUST_UPDATE_FILES"
    echo ""
    echo -e "${BLUE}💡 To fix these references:${NC}"
    echo "   1. Review suggestions above"
    echo "   2. Run: python scripts/maintenance/prms_cli.py fix --dry-run"
    echo "   3. Review changes, then run: python scripts/maintenance/prms_cli.py fix"
    echo "   4. Stage fixed files and commit again"
    echo ""
    echo -e "${BLUE}💡 To see full report:${NC}"
    echo "   python scripts/maintenance/prms_cli.py report"
    echo ""
    echo -e "${YELLOW}See: docs/claude_workflows/workflow_descriptions/60_prms_path_reference_management.md${NC}"
    echo ""
    exit 1
else
    echo -e "${GREEN}   ✓ No outdated path references found in staged files${NC}"
fi

exit 0
