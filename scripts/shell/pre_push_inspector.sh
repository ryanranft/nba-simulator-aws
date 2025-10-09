#!/bin/bash

# pre_push_inspector.sh - Interactive Pre-Push Inspection Workflow
# Automates repository cleanup before pushing to GitHub
# Implements 7-step workflow from docs/SECURITY_PROTOCOLS.md

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCHIVE_BASE="$HOME/sports-simulator-archives"

# Security patterns (from security_scan.sh)
SECURITY_PATTERNS=(
    "AKIA[A-Z0-9]{16}"                              # AWS Access Keys
    "aws_secret_access_key.*[A-Za-z0-9/+=]{40}"    # AWS Secret Keys
    "BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY"       # Private Keys
    "gh[psor]_[A-Za-z0-9]{36}"                     # GitHub Tokens
    "postgresql://[^:]+:[^@]{8,}@"                 # DB connection strings
    "(192\.168\.|10\.)[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"  # Private IPs
)

# File categorization patterns
declare -A FILE_CATEGORIES

# High priority - operational/runtime files
FILE_CATEGORIES[operational]="*_STATUS.md *_PROGRESS.md *_SUMMARY.md *_VERIFICATION.md"

# High priority - command logs
FILE_CATEGORIES[logs]="COMMAND_LOG.md COMMAND_HISTORY.md *_LOG.md *.log"

# Medium priority - temporary documentation
FILE_CATEGORIES[temp_docs]="COMMIT_VERIFICATION.md EXTRACTION_*.md TEST_*.md WORKFLOW_*_COMPARISON.md"

# Medium priority - configuration with paths
FILE_CATEGORIES[config]="*.env .aws/credentials"

# Low priority - data files
FILE_CATEGORIES[data]="*.csv *.json *.parquet data/*.json"

# Files to ALWAYS keep
KEEP_PATTERNS=(
    "CLAUDE.md"
    "PROGRESS.md"
    "README.md"
    "QUICKSTART.md"
    "MACHINE_SPECS.md"
    "FILE_INVENTORY.md"
    "TROUBLESHOOTING.md"
    "WORKFLOW_CONSOLIDATION_LOG.md"
    "docs/*.md"
    "scripts/**/*.sh"
    "scripts/**/*.py"
    "config/*.yaml"
    "*.example"
    ".gitignore"
    "requirements.txt"
    "Makefile"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITY FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

show_usage() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║       Pre-Push Inspection Workflow - Interactive Tool       ║
╚══════════════════════════════════════════════════════════════╝

USAGE: bash scripts/shell/pre_push_inspector.sh <mode>

MODES:
  security-scan        Run comprehensive 15-point security audit
  inspect-repo         Scan for local-only files (categorized by risk)
  recommend            Show recommendations with priority levels
  archive-cleanup      Archive flagged files before deletion
  cleanup-repo         Remove files from tracking (git rm --cached)
  validate-references  Check for broken references to moved/archived files
  full                 Complete workflow (all steps, interactive)
  status               Preview what would be flagged (dry-run)
  help                 Show this help message

EXAMPLES:
  # Full pre-push workflow (recommended before git push)
  bash scripts/shell/pre_push_inspector.sh full

  # Individual steps
  bash scripts/shell/pre_push_inspector.sh security-scan
  bash scripts/shell/pre_push_inspector.sh inspect-repo
  bash scripts/shell/pre_push_inspector.sh status

WORKFLOW STEPS (full mode):
  Step 1: Security Scan
  Step 2: Repository Inspection
  Step 3: Present Recommendations
  Step 4: User Confirmation
  Step 5: Archive Before Deletion
  Step 6: Remove from Repository
  Step 7: Reference Path Validation
  Step 8: Final Push Approval

See docs/SECURITY_PROTOCOLS.md for complete documentation.
EOF
}

# Check if file should be kept (matches KEEP_PATTERNS)
should_keep_file() {
    local file="$1"
    local pattern

    for pattern in "${KEEP_PATTERNS[@]}"; do
        # Convert glob to regex
        if [[ "$pattern" == *"*"* ]]; then
            # Handle ** and * wildcards
            local regex_pattern="${pattern//\*\*/.*}"
            regex_pattern="${regex_pattern//\*/[^/]*}"
            if [[ "$file" =~ $regex_pattern ]]; then
                return 0  # Keep this file
            fi
        else
            # Exact match
            if [[ "$file" == "$pattern" ]]; then
                return 0  # Keep this file
            fi
        fi
    done

    return 1  # Don't keep
}

# Categorize file by risk level
categorize_file() {
    local file="$1"
    local category
    local pattern

    # Check each category
    for category in operational logs temp_docs config data; do
        for pattern in ${FILE_CATEGORIES[$category]}; do
            if [[ "$file" == $pattern ]] || [[ "$(basename "$file")" == $pattern ]]; then
                echo "$category"
                return
            fi
        done
    done

    echo "unknown"
}

# Get priority level for category
get_priority() {
    local category="$1"

    case "$category" in
        operational|logs)
            echo "HIGH"
            ;;
        temp_docs|config)
            echo "MEDIUM"
            ;;
        data)
            echo "LOW"
            ;;
        *)
            echo "LOW"
            ;;
    esac
}

# Get priority emoji
get_priority_emoji() {
    local priority="$1"

    case "$priority" in
        HIGH)
            echo "🔴"
            ;;
        MEDIUM)
            echo "🟡"
            ;;
        LOW)
            echo "🟢"
            ;;
        *)
            echo "⚪"
            ;;
    esac
}

# Get reason for flagging file
get_flagging_reason() {
    local file="$1"
    local category="$2"

    case "$category" in
        operational)
            echo "Contains operational/runtime status data"
            ;;
        logs)
            echo "Contains command outputs with potential credentials"
            ;;
        temp_docs)
            echo "Temporary documentation from debugging/testing"
            ;;
        config)
            echo "Configuration with local absolute paths"
            ;;
        data)
            echo "Large data file (should be in data/ directory)"
            ;;
        *)
            echo "File pattern matches local-only criteria"
            ;;
    esac
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: security-scan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_security_scan() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     COMPREHENSIVE SECURITY SCAN - Git History & Files      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Check if security_scan.sh exists
    if [ -f "$PROJECT_DIR/scripts/shell/security_scan.sh" ]; then
        echo "Running existing security_scan.sh..."
        echo ""
        bash "$PROJECT_DIR/scripts/shell/security_scan.sh"
        return $?
    fi

    # Fallback: simplified inline scan
    echo "⚠️  Warning: security_scan.sh not found, running simplified scan"
    echo ""

    local ISSUES_FOUND=0

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SECURITY SCAN - Tracked Files"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check for AWS keys
    echo -n "1. AWS Access Keys (AKIA)........................ "
    COUNT=$(git ls-files | xargs grep -E "AKIA[A-Z0-9]{16}" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓ PASS (0 found)${NC}"
    else
        echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
    fi

    # Check for private keys
    echo -n "2. Private SSH/RSA Keys.......................... "
    COUNT=$(git ls-files | xargs grep -E "BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓ PASS (0 found)${NC}"
    else
        echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
    fi

    # Check for .env files
    echo -n "3. .env files.................................... "
    COUNT=$(git ls-files | grep "\.env$" | grep -v "\.env\.example" | wc -l | tr -d ' ')
    if [ "$COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓ PASS (0 found)${NC}"
    else
        echo -e "${RED}✗ FAIL ($COUNT found)${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + COUNT))
    fi

    echo ""

    if [ "$ISSUES_FOUND" -eq 0 ]; then
        echo -e "${GREEN}✓ SECURITY SCAN PASSED - NO CRITICAL ISSUES FOUND${NC}"
        return 0
    else
        echo -e "${RED}✗ SECURITY SCAN FAILED - $ISSUES_FOUND ISSUES FOUND${NC}"
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: inspect-repo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_inspect_repo() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           Repository Inspection - Local-Only Files        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    cd "$PROJECT_DIR" || exit 1

    # Get all tracked files with specific extensions
    local tracked_files
    tracked_files=$(git ls-files | grep -E "\.(md|log|txt|json|csv)$")

    if [ -z "$tracked_files" ]; then
        echo "No tracked files with inspectable extensions found."
        return 0
    fi

    # Arrays to hold categorized files
    declare -A flagged_files
    declare -A keep_files

    local total_flagged=0
    local total_keep=0

    echo "Scanning tracked files..."
    echo ""

    # Categorize each file
    while IFS= read -r file; do
        if should_keep_file "$file"; then
            keep_files["$file"]=1
            ((total_keep++))
        else
            local category=$(categorize_file "$file")
            if [ "$category" != "unknown" ]; then
                flagged_files["$file"]="$category"
                ((total_flagged++))
            else
                keep_files["$file"]=1
                ((total_keep++))
            fi
        fi
    done <<< "$tracked_files"

    # Display results
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "INSPECTION RESULTS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}📋 Files Flagged for Review: $total_flagged${NC}"
    echo -e "${GREEN}✅ Files to Keep: $total_keep${NC}"
    echo ""

    if [ "$total_flagged" -eq 0 ]; then
        echo "✓ No local-only files detected"
        echo "✓ Repository appears clean for push"
        return 0
    fi

    # Show flagged files by category
    echo "Flagged files by category:"
    echo ""

    for file in "${!flagged_files[@]}"; do
        local category="${flagged_files[$file]}"
        local priority=$(get_priority "$category")
        local emoji=$(get_priority_emoji "$priority")
        echo "$emoji $priority - $file ($category)"
    done | sort

    echo ""
    echo "Run 'recommend' mode to see detailed recommendations."

    return 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: recommend
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_recommend() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║      Pre-Push Recommendations - Files to Archive/Delete   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    cd "$PROJECT_DIR" || exit 1

    # Get flagged files
    local tracked_files
    tracked_files=$(git ls-files | grep -E "\.(md|log|txt|json|csv)$")

    declare -A flagged_high
    declare -A flagged_medium
    declare -A flagged_low
    declare -a keep_list

    local count_high=0
    local count_medium=0
    local count_low=0

    # Categorize files
    while IFS= read -r file; do
        if should_keep_file "$file"; then
            keep_list+=("$file")
        else
            local category=$(categorize_file "$file")
            if [ "$category" != "unknown" ]; then
                local priority=$(get_priority "$category")
                local reason=$(get_flagging_reason "$file" "$category")

                case "$priority" in
                    HIGH)
                        flagged_high["$file"]="$reason"
                        ((count_high++))
                        ;;
                    MEDIUM)
                        flagged_medium["$file"]="$reason"
                        ((count_medium++))
                        ;;
                    LOW)
                        flagged_low["$file"]="$reason"
                        ((count_low++))
                        ;;
                esac
            else
                keep_list+=("$file")
            fi
        fi
    done <<< "$tracked_files"

    # Display recommendations
    echo "📋 Pre-Push Inspection Results:"
    echo ""

    local total_flagged=$((count_high + count_medium + count_low))

    if [ "$total_flagged" -eq 0 ]; then
        echo -e "${GREEN}✓ No files recommended for deletion${NC}"
        echo -e "${GREEN}✓ Repository is clean and ready to push${NC}"
        return 0
    fi

    echo "Files Recommended for Deletion (Archive First):"
    echo ""

    # High priority
    if [ "$count_high" -gt 0 ]; then
        echo -e "${RED}🔴 HIGH PRIORITY (likely contains sensitive/operational data):${NC}"
        for file in "${!flagged_high[@]}"; do
            echo "  - $file"
            echo "    Reason: ${flagged_high[$file]}"
        done
        echo ""
    fi

    # Medium priority
    if [ "$count_medium" -gt 0 ]; then
        echo -e "${YELLOW}🟡 MEDIUM PRIORITY (operational data, no immediate risk):${NC}"
        for file in "${!flagged_medium[@]}"; do
            echo "  - $file"
            echo "    Reason: ${flagged_medium[$file]}"
        done
        echo ""
    fi

    # Low priority
    if [ "$count_low" -gt 0 ]; then
        echo -e "${GREEN}🟢 LOW PRIORITY (consider for cleanup):${NC}"
        for file in "${!flagged_low[@]}"; do
            echo "  - $file"
            echo "    Reason: ${flagged_low[$file]}"
        done
        echo ""
    fi

    # Files to keep
    echo "Files to KEEP on GitHub:"
    for file in "${keep_list[@]:0:10}"; do
        echo "  ✅ $file"
    done
    if [ "${#keep_list[@]}" -gt 10 ]; then
        echo "  ... and $((${#keep_list[@]} - 10)) more"
    fi
    echo ""

    # Save flagged files to temp file for other modes
    local temp_file="/tmp/pre_push_inspector_flagged.txt"
    {
        for file in "${!flagged_high[@]}"; do echo "$file"; done
        for file in "${!flagged_medium[@]}"; do echo "$file"; done
        for file in "${!flagged_low[@]}"; do echo "$file"; done
    } > "$temp_file"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Next steps:"
    echo "  1. Review flagged files above"
    echo "  2. Run 'archive-cleanup' mode to archive them"
    echo "  3. Run 'cleanup-repo' mode to remove from tracking"
    echo "  4. Or run 'full' mode for complete interactive workflow"

    return 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: archive-cleanup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_archive_cleanup() {
    local files_to_archive=("$@")

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         Archive Cleanup - Pre-Push File Archiving         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # If no files provided, read from temp file
    if [ "${#files_to_archive[@]}" -eq 0 ]; then
        local temp_file="/tmp/pre_push_inspector_flagged.txt"
        if [ -f "$temp_file" ]; then
            mapfile -t files_to_archive < "$temp_file"
        else
            echo "❌ No files specified and no flagged files found."
            echo "Run 'recommend' mode first to identify files."
            return 1
        fi
    fi

    if [ "${#files_to_archive[@]}" -eq 0 ]; then
        echo "✓ No files to archive"
        return 0
    fi

    # Detect sport (from directory name)
    local sport=$(basename "$PROJECT_DIR" | sed 's/-simulator-aws//')

    # Create archive directory
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local archive_dir="$ARCHIVE_BASE/$sport/pre-push-cleanup-$timestamp"

    mkdir -p "$archive_dir"

    echo "Creating pre-push cleanup archive..."
    echo "Archive: $archive_dir"
    echo ""

    # Copy files to archive
    local count=0
    cd "$PROJECT_DIR" || exit 1

    for file in "${files_to_archive[@]}"; do
        if [ -f "$file" ]; then
            # Create subdirectories if needed
            local file_dir=$(dirname "$file")
            mkdir -p "$archive_dir/$file_dir"

            # Copy file
            cp "$file" "$archive_dir/$file"
            echo "  ✓ Archived: $file"
            ((count++))
        fi
    done

    echo ""
    echo "📊 Files archived: $count"
    echo ""

    # Create CLEANUP_RECORD.md
    cat > "$archive_dir/CLEANUP_RECORD.md" << EOF
# Pre-Push Cleanup Record

**Date:** $(date)
**Trigger:** Pre-push inspection
**Reason:** Files identified as local-only during GitHub push review

## Files Removed:

EOF

    for file in "${files_to_archive[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            local category=$(categorize_file "$file")
            local reason=$(get_flagging_reason "$file" "$category")
            echo "- \`$file\` - $reason" >> "$archive_dir/CLEANUP_RECORD.md"
        fi
    done

    cat >> "$archive_dir/CLEANUP_RECORD.md" << EOF

## How to Access:

- **Pre-push archive:** $archive_dir
- **Git history:** \`git show <commit>:FILENAME\`
- **Archive git repo:** \`git -C $ARCHIVE_BASE/$sport log --all\`

## Context:

These files were flagged during automated pre-push inspection and confirmed
for deletion by user before pushing to GitHub.

All files have been safely archived and can be restored if needed.
EOF

    echo "✅ CLEANUP_RECORD.md created"
    echo ""

    # Commit to archive git repo
    if [ -d "$ARCHIVE_BASE/$sport/.git" ]; then
        echo "Committing to archive git repository..."
        cd "$ARCHIVE_BASE/$sport" || exit 1
        git add "pre-push-cleanup-$timestamp/"
        git commit -m "Pre-push cleanup - archive files before GitHub push ($count files)" -q
        echo "✅ Committed to archive git repo"
        cd "$PROJECT_DIR" || exit 1
    else
        echo "⚠️  No git repo in archive directory (skipping commit)"
    fi

    echo ""
    echo "Archive location: $archive_dir"

    return 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: cleanup-repo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_cleanup_repo() {
    local files_to_remove=("$@")

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║      Repository Cleanup - Remove from Git Tracking        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # If no files provided, read from temp file
    if [ "${#files_to_remove[@]}" -eq 0 ]; then
        local temp_file="/tmp/pre_push_inspector_flagged.txt"
        if [ -f "$temp_file" ]; then
            mapfile -t files_to_remove < "$temp_file"
        else
            echo "❌ No files specified and no flagged files found."
            echo "Run 'recommend' mode first to identify files."
            return 1
        fi
    fi

    if [ "${#files_to_remove[@]}" -eq 0 ]; then
        echo "✓ No files to remove from tracking"
        return 0
    fi

    cd "$PROJECT_DIR" || exit 1

    echo "Removing files from git tracking..."
    echo ""

    local count=0
    local gitignore_additions=()

    for file in "${files_to_remove[@]}"; do
        if git ls-files --error-unmatch "$file" &>/dev/null; then
            # Remove from tracking (but keep local file)
            git rm --cached "$file" -q 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "  ✓ Removed from tracking: $file"
                ((count++))

                # Add to gitignore if not already there
                if ! grep -qF "$file" .gitignore 2>/dev/null; then
                    gitignore_additions+=("$file")
                fi
            fi
        fi
    done

    echo ""
    echo "📊 Files removed from tracking: $count"

    # Update .gitignore
    if [ "${#gitignore_additions[@]}" -gt 0 ]; then
        echo ""
        echo "Updating .gitignore..."

        # Add section header if .gitignore exists
        if [ -f .gitignore ]; then
            echo "" >> .gitignore
            echo "# Pre-push cleanup - removed $(date +%Y-%m-%d)" >> .gitignore
        fi

        for file in "${gitignore_additions[@]}"; do
            echo "$file" >> .gitignore
            echo "  ✓ Added to .gitignore: $file"
        done

        echo ""
        echo "✅ .gitignore updated"
    fi

    # Create cleanup commit
    if [ "$count" -gt 0 ]; then
        echo ""
        echo "Creating cleanup commit..."

        git add .gitignore

        git commit -m "$(cat <<EOF
Remove local-only files identified in pre-push inspection

Files removed from tracking:
$(for file in "${files_to_remove[@]}"; do echo "- $file"; done)

Files have been archived before removal and can be restored from:
~/sports-simulator-archives/$(basename "$PROJECT_DIR" | sed 's/-simulator-aws//')/pre-push-cleanup-*

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" -q

        echo "✅ Cleanup commit created"
        echo ""
        echo "Run 'git log -1' to see commit details"
    fi

    return 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: validate-references
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_validate_references() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║      Reference Path Validation - Check Broken Links       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Check if validate_references.sh exists
    if [ ! -f "$PROJECT_DIR/scripts/shell/validate_references.sh" ]; then
        echo "❌ validate_references.sh not found"
        echo "Expected location: $PROJECT_DIR/scripts/shell/validate_references.sh"
        return 1
    fi

    # Run reference validator in check-only mode
    bash "$PROJECT_DIR/scripts/shell/validate_references.sh" --check-only

    local result=$?

    echo ""

    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED: All file references valid${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: Broken documentation references detected${NC}"
        echo ""
        echo "To see details, run:"
        echo "  bash scripts/shell/validate_references.sh"
        echo ""
        echo "To auto-fix, run:"
        echo "  bash scripts/shell/validate_references.sh --fix"
        echo ""
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_status() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         Pre-Push Status - Dry Run (No Changes Made)       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    cd "$PROJECT_DIR" || exit 1

    # Count files by category
    local tracked_files
    tracked_files=$(git ls-files | grep -E "\.(md|log|txt|json|csv)$")

    declare -A category_counts
    category_counts[operational]=0
    category_counts[logs]=0
    category_counts[temp_docs]=0
    category_counts[config]=0
    category_counts[data]=0
    local keep_count=0
    local flagged_count=0

    while IFS= read -r file; do
        if should_keep_file "$file"; then
            ((keep_count++))
        else
            local category=$(categorize_file "$file")
            if [ "$category" != "unknown" ]; then
                ((category_counts[$category]++))
                ((flagged_count++))
            else
                ((keep_count++))
            fi
        fi
    done <<< "$tracked_files"

    # Display status
    echo "Repository Status Summary:"
    echo ""
    echo -e "${YELLOW}📋 Files flagged for review: $flagged_count${NC}"
    echo ""

    if [ "$flagged_count" -eq 0 ]; then
        echo -e "${GREEN}✓ No local-only files detected${NC}"
        echo -e "${GREEN}✓ Repository is clean and ready to push${NC}"
    else
        echo "Breakdown by category:"
        for category in operational logs temp_docs config data; do
            local count=${category_counts[$category]}
            if [ "$count" -gt 0 ]; then
                local priority=$(get_priority "$category")
                local emoji=$(get_priority_emoji "$priority")
                echo "  $emoji $priority - $category: $count file(s)"
            fi
        done
    fi

    echo ""
    echo -e "${GREEN}✅ Files to keep on GitHub: $keep_count${NC}"
    echo ""

    if [ "$flagged_count" -gt 0 ]; then
        echo "Next steps:"
        echo "  • Run 'recommend' mode to see detailed list"
        echo "  • Run 'full' mode for interactive cleanup workflow"
    fi

    return 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE: full
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mode_full() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║    Complete Pre-Push Workflow - Interactive Inspection    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "This will guide you through the complete 7-step pre-push workflow:"
    echo "  1. Security Scan"
    echo "  2. Repository Inspection"
    echo "  3. Present Recommendations"
    echo "  4. User Confirmation"
    echo "  5. Archive Before Deletion"
    echo "  6. Remove from Repository"
    echo "  7. Final Push Approval"
    echo ""

    read -p "Continue? [y/N] " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Workflow cancelled."
        return 0
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 1: Security Scan"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    mode_security_scan
    local security_result=$?

    if [ "$security_result" -ne 0 ]; then
        echo ""
        echo "❌ Security scan failed. Fix security issues before proceeding."
        return 1
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 2: Repository Inspection"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    mode_inspect_repo

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 3: Present Recommendations"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    mode_recommend

    # Check if any files were flagged
    local temp_file="/tmp/pre_push_inspector_flagged.txt"
    if [ ! -f "$temp_file" ] || [ ! -s "$temp_file" ]; then
        echo ""
        echo -e "${GREEN}✓ No files to clean up. Repository is ready to push!${NC}"
        echo ""
        read -p "Ready to push to GitHub? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "You can now run: git push"
        fi
        return 0
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 4: User Confirmation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Would you like to archive and delete the flagged files?"
    echo ""
    echo "Options:"
    echo "  YES     - Archive and delete all flagged files"
    echo "  NO      - Skip deletion, proceed with push anyway"
    echo "  <files> - Only delete specific files (space-separated)"
    echo ""
    read -p "Your choice [YES/NO/<files>]: " user_response

    case "$user_response" in
        YES|yes|Y|y)
            echo ""
            echo "Proceeding with archive and deletion of all flagged files..."
            ;;
        NO|no|N|n)
            echo ""
            echo "Skipping cleanup. You can proceed with push."
            echo ""
            read -p "Ready to push to GitHub? [y/N] " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "You can now run: git push"
            fi
            return 0
            ;;
        *)
            echo ""
            echo "Processing specific files: $user_response"
            # Create temporary file with only specified files
            echo "$user_response" | tr ' ' '\n' > "$temp_file"
            ;;
    esac

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 5: Archive Before Deletion"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    mode_archive_cleanup

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 6: Remove from Repository"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    mode_cleanup_repo

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 7: Reference Path Validation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    mode_validate_references
    local validation_result=$?

    if [ "$validation_result" -ne 0 ]; then
        echo ""
        echo "⚠️  Warning: Broken documentation references detected"
        echo ""
        read -p "Fix references now? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash "$PROJECT_DIR/scripts/shell/validate_references.sh" --fix
            echo ""
            echo "✅ References fixed"
        else
            echo "⚠️  Proceeding with broken references (may cause 404s)"
        fi
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 8: Final Push Approval"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "✅ Cleanup complete!"
    echo ""
    echo "Summary:"
    echo "  • Files archived to: ~/sports-simulator-archives/"
    echo "  • Files removed from tracking"
    echo "  • .gitignore updated"
    echo "  • Cleanup commit created"
    echo ""

    read -p "Ready to push to GitHub? [y/N] " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "You can now run: git push"
        echo ""
        echo "Note: If pre-push hook blocks with security violations:"
        echo "  1. Review the flagged lines"
        echo "  2. Confirm they are safe (e.g., documentation patterns)"
        echo "  3. Use --no-verify only if absolutely necessary"
    else
        echo ""
        echo "Push cancelled. You can push later with: git push"
    fi

    return 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN EXECUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODE="${1:-help}"

case "$MODE" in
    security-scan)
        mode_security_scan
        ;;
    inspect-repo)
        mode_inspect_repo
        ;;
    recommend)
        mode_recommend
        ;;
    archive-cleanup)
        shift  # Remove mode argument
        mode_archive_cleanup "$@"
        ;;
    cleanup-repo)
        shift  # Remove mode argument
        mode_cleanup_repo "$@"
        ;;
    validate-references)
        mode_validate_references
        ;;
    full)
        mode_full
        ;;
    status)
        mode_status
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo ""
        show_usage
        exit 1
        ;;
esac

exit $?