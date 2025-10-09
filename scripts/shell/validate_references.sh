#!/bin/bash

################################################################################
# Reference Path Validator
#
# Automatically detects moved, renamed, or deleted files and finds all
# references to those files in the codebase. Optionally updates references.
#
# Usage:
#   bash scripts/shell/validate_references.sh [OPTIONS] [COMMIT_SHA]
#
# Options:
#   --fix              Auto-fix references with confirmation
#   --dry-run          Show what would be updated without making changes
#   --check-only       Exit 0 if valid, 1 if broken references found
#   --staged           Check staged changes (default if no commit specified)
#   --auto-commit      Automatically commit reference updates
#   --no-confirm       Skip confirmation prompts (use with --fix)
#   --verbose          Show detailed output
#
# Examples:
#   # Check staged changes
#   bash scripts/shell/validate_references.sh
#
#   # Check specific commit
#   bash scripts/shell/validate_references.sh c363ed5
#
#   # Check and auto-fix
#   bash scripts/shell/validate_references.sh --fix
#
#   # Dry run
#   bash scripts/shell/validate_references.sh --dry-run
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
MODE="report"  # report, dry-run, fix, check-only
TARGET="staged"  # staged or commit SHA
AUTO_COMMIT=false
CONFIRM=true
VERBOSE=false
COMMIT_SHA=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --fix)
      MODE="fix"
      shift
      ;;
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --check-only)
      MODE="check-only"
      shift
      ;;
    --staged)
      TARGET="staged"
      shift
      ;;
    --auto-commit)
      AUTO_COMMIT=true
      shift
      ;;
    --no-confirm)
      CONFIRM=false
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      head -n 33 "$0" | tail -n 30
      exit 0
      ;;
    *)
      # Assume it's a commit SHA
      COMMIT_SHA="$1"
      TARGET="commit"
      shift
      ;;
  esac
done

# Temporary files
TEMP_DIR=$(mktemp -d)
CHANGED_FILES="$TEMP_DIR/changed_files.txt"
MOVED_FILES="$TEMP_DIR/moved_files.txt"
DELETED_FILES="$TEMP_DIR/deleted_files.txt"
RENAMED_FILES="$TEMP_DIR/renamed_files.txt"
REFERENCE_REPORT="$TEMP_DIR/reference_report.txt"

# Cleanup on exit
trap 'rm -rf "$TEMP_DIR"' EXIT

################################################################################
# Helper Functions
################################################################################

log_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
  echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
  echo -e "${RED}❌${NC} $1"
}

log_verbose() {
  if [ "$VERBOSE" = true ]; then
    echo -e "${BLUE}[VERBOSE]${NC} $1"
  fi
}

################################################################################
# Step 1: Detect Changed Files
################################################################################

detect_changes() {
  log_info "Detecting changed files..."

  if [ "$TARGET" = "staged" ]; then
    log_verbose "Checking staged changes"

    # Get staged file changes
    git diff --cached --name-status > "$CHANGED_FILES"

    # Parse different change types
    grep '^D' "$CHANGED_FILES" | awk '{print $2}' > "$DELETED_FILES" || true
    grep '^R' "$CHANGED_FILES" | awk '{print $2 " → " $3}' > "$RENAMED_FILES" || true
    grep '^R' "$CHANGED_FILES" | awk '{print $2}' >> "$DELETED_FILES" || true  # Old name is "deleted"

  elif [ "$TARGET" = "commit" ]; then
    log_verbose "Checking commit: $COMMIT_SHA"

    # Get changes from specific commit
    git diff --name-status "${COMMIT_SHA}~1" "$COMMIT_SHA" > "$CHANGED_FILES"

    # Parse different change types
    grep '^D' "$CHANGED_FILES" | awk '{print $2}' > "$DELETED_FILES" || true
    grep '^R' "$CHANGED_FILES" | awk '{print $2 " → " $3}' > "$RENAMED_FILES" || true
    grep '^R' "$CHANGED_FILES" | awk '{print $2}' >> "$DELETED_FILES" || true
  fi

  # Count changes
  local total_changes=$(wc -l < "$CHANGED_FILES" | tr -d ' ')
  local deleted_count=$(wc -l < "$DELETED_FILES" | tr -d ' ')
  local renamed_count=$(wc -l < "$RENAMED_FILES" | tr -d ' ')

  log_verbose "Total changes: $total_changes"
  log_verbose "Deleted/moved: $deleted_count"
  log_verbose "Renamed: $renamed_count"

  if [ "$deleted_count" -eq 0 ] && [ "$renamed_count" -eq 0 ]; then
    log_success "No files moved, renamed, or deleted"
    return 1
  fi

  return 0
}

################################################################################
# Step 2: Search for References
################################################################################

search_references() {
  local file_to_search="$1"
  local basename_only=$(basename "$file_to_search")

  log_verbose "Searching for references to: $basename_only"

  # Search in documentation files
  local md_refs=$(grep -r "$basename_only" . \
    --include="*.md" \
    --exclude-dir=".git" \
    --exclude-dir="node_modules" \
    --exclude-dir="__pycache__" \
    --exclude-dir="venv" \
    --exclude-dir=".venv" \
    -l 2>/dev/null || true)

  # Search in Python files
  local py_refs=$(grep -r "$basename_only" . \
    --include="*.py" \
    --exclude-dir=".git" \
    --exclude-dir="__pycache__" \
    --exclude-dir="venv" \
    -l 2>/dev/null || true)

  # Search in shell scripts
  local sh_refs=$(grep -r "$basename_only" . \
    --include="*.sh" \
    --exclude-dir=".git" \
    -l 2>/dev/null || true)

  # Search in R scripts
  local r_refs=$(grep -r "$basename_only" . \
    --include="*.R" \
    --exclude-dir=".git" \
    -l 2>/dev/null || true)

  # Combine and deduplicate
  echo -e "$md_refs\n$py_refs\n$sh_refs\n$r_refs" | grep -v '^$' | sort -u || true
}

################################################################################
# Step 3: Generate Reference Report
################################################################################

generate_report() {
  log_info "Generating reference report..."

  echo "# Reference Path Validation Report" > "$REFERENCE_REPORT"
  echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$REFERENCE_REPORT"
  echo "**Target:** $TARGET" >> "$REFERENCE_REPORT"
  if [ "$TARGET" = "commit" ]; then
    echo "**Commit:** $COMMIT_SHA" >> "$REFERENCE_REPORT"
  fi
  echo "" >> "$REFERENCE_REPORT"

  # Summary section
  local deleted_count=$(wc -l < "$DELETED_FILES" | tr -d ' ')
  local renamed_count=$(wc -l < "$RENAMED_FILES" | tr -d ' ')

  echo "## Summary" >> "$REFERENCE_REPORT"
  echo "- Files deleted/moved: $deleted_count" >> "$REFERENCE_REPORT"
  echo "- Files renamed: $renamed_count" >> "$REFERENCE_REPORT"
  echo "" >> "$REFERENCE_REPORT"

  local total_refs=0
  local files_with_refs=0

  # Check deleted/moved files
  if [ -s "$DELETED_FILES" ]; then
    echo "## Deleted/Moved Files" >> "$REFERENCE_REPORT"
    echo "" >> "$REFERENCE_REPORT"

    while IFS= read -r file; do
      [ -z "$file" ] && continue

      echo "### File: $file" >> "$REFERENCE_REPORT"

      # Search for references
      local refs=$(search_references "$file")

      if [ -n "$refs" ]; then
        local ref_count=$(echo "$refs" | wc -l | tr -d ' ')
        total_refs=$((total_refs + ref_count))
        files_with_refs=$((files_with_refs + 1))

        echo "**References found:** $ref_count files" >> "$REFERENCE_REPORT"
        echo '```' >> "$REFERENCE_REPORT"
        echo "$refs" >> "$REFERENCE_REPORT"
        echo '```' >> "$REFERENCE_REPORT"
      else
        echo "**References found:** None" >> "$REFERENCE_REPORT"
      fi

      echo "" >> "$REFERENCE_REPORT"
    done < "$DELETED_FILES"
  fi

  # Check renamed files
  if [ -s "$RENAMED_FILES" ]; then
    echo "## Renamed Files" >> "$REFERENCE_REPORT"
    echo "" >> "$REFERENCE_REPORT"

    while IFS= read -r rename_pair; do
      [ -z "$rename_pair" ] && continue

      local old_name=$(echo "$rename_pair" | cut -d '→' -f 1 | xargs)
      local new_name=$(echo "$rename_pair" | cut -d '→' -f 2 | xargs)

      echo "### $old_name → $new_name" >> "$REFERENCE_REPORT"

      # Search for references to old name
      local refs=$(search_references "$old_name")

      if [ -n "$refs" ]; then
        local ref_count=$(echo "$refs" | wc -l | tr -d ' ')
        total_refs=$((total_refs + ref_count))

        echo "**References to old name:** $ref_count files" >> "$REFERENCE_REPORT"
        echo '```' >> "$REFERENCE_REPORT"
        echo "$refs" >> "$REFERENCE_REPORT"
        echo '```' >> "$REFERENCE_REPORT"
      else
        echo "**References to old name:** None" >> "$REFERENCE_REPORT"
      fi

      echo "" >> "$REFERENCE_REPORT"
    done < "$RENAMED_FILES"
  fi

  # Final summary
  echo "## Final Summary" >> "$REFERENCE_REPORT"
  echo "- **Total references found:** $total_refs" >> "$REFERENCE_REPORT"
  echo "- **Files with broken references:** $files_with_refs" >> "$REFERENCE_REPORT"
  echo "" >> "$REFERENCE_REPORT"

  if [ $total_refs -eq 0 ]; then
    echo "✅ **No broken references detected**" >> "$REFERENCE_REPORT"
    return 0
  else
    echo "⚠️  **Broken references detected - update needed**" >> "$REFERENCE_REPORT"
    return 1
  fi
}

################################################################################
# Step 4: Display Report
################################################################################

display_report() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  cat "$REFERENCE_REPORT"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
}

################################################################################
# Step 5: Fix References (if requested)
################################################################################

fix_references() {
  log_info "Preparing to fix broken references..."

  if [ "$CONFIRM" = true ]; then
    echo ""
    read -p "Update all references automatically? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      log_warning "Fix cancelled by user"
      return 1
    fi
  fi

  # Parse renamed files and update references
  if [ -s "$RENAMED_FILES" ]; then
    while IFS= read -r rename_pair; do
      [ -z "$rename_pair" ] && continue

      local old_name=$(echo "$rename_pair" | cut -d '→' -f 1 | xargs)
      local new_name=$(echo "$rename_pair" | cut -d '→' -f 2 | xargs)
      local old_basename=$(basename "$old_name")
      local new_basename=$(basename "$new_name")

      log_info "Updating references: $old_basename → $new_basename"

      # Find files with references
      local refs=$(search_references "$old_name")

      if [ -n "$refs" ]; then
        while IFS= read -r ref_file; do
          [ -z "$ref_file" ] && continue

          log_verbose "  Updating: $ref_file"

          # Create backup
          cp "$ref_file" "${ref_file}.bak"

          # Update references (escape special characters in paths)
          local old_escaped=$(echo "$old_name" | sed 's/[\/&]/\\&/g')
          local new_escaped=$(echo "$new_name" | sed 's/[\/&]/\\&/g')

          sed -i '' "s|$old_escaped|$new_escaped|g" "$ref_file"

          # Also update just the basename (for partial references)
          sed -i '' "s|$old_basename|$new_basename|g" "$ref_file"

          log_success "  ✅ Updated: $ref_file"
        done <<< "$refs"
      fi
    done < "$RENAMED_FILES"
  fi

  log_success "Reference updates complete"

  # Show git diff
  if git diff --quiet; then
    log_warning "No changes made (references may already be correct)"
  else
    log_info "Changes made - review with: git diff"
  fi
}

################################################################################
# Step 6: Auto-commit (if requested)
################################################################################

auto_commit_changes() {
  if [ "$AUTO_COMMIT" = false ]; then
    return 0
  fi

  # Check if there are changes to commit
  if git diff --quiet; then
    log_info "No changes to commit"
    return 0
  fi

  log_info "Auto-committing reference updates..."

  git add .

  local commit_msg="docs(refs): auto-update broken references

Updated references to renamed/moved files.
Generated by: scripts/shell/validate_references.sh

$(git diff --cached --name-only | sed 's/^/- /')"

  git commit -m "$commit_msg"

  log_success "Reference updates committed"
}

################################################################################
# Main Execution
################################################################################

main() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Reference Path Validator"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Detect changes
  if ! detect_changes; then
    log_success "Validation passed - no files moved/renamed/deleted"
    exit 0
  fi

  # Generate report
  local report_status=0
  generate_report || report_status=$?

  # Display report
  if [ "$MODE" != "check-only" ]; then
    display_report
  fi

  # Handle different modes
  case $MODE in
    report)
      if [ $report_status -ne 0 ]; then
        log_warning "Broken references detected"
        log_info "Run with --fix to auto-update references"
        exit 1
      else
        log_success "No broken references detected"
        exit 0
      fi
      ;;

    dry-run)
      log_info "Dry run mode - no changes made"
      if [ $report_status -ne 0 ]; then
        log_info "Run with --fix to update these references"
        exit 1
      else
        exit 0
      fi
      ;;

    fix)
      if [ $report_status -ne 0 ]; then
        fix_references
        auto_commit_changes
        exit 0
      else
        log_success "No fixes needed"
        exit 0
      fi
      ;;

    check-only)
      if [ $report_status -ne 0 ]; then
        log_error "Broken references detected"
        exit 1
      else
        log_success "All references valid"
        exit 0
      fi
      ;;
  esac
}

# Run main function
main "$@"
