#!/bin/bash

##############################################################################
# Audit Diff Reporter
##############################################################################
#
# Purpose: Show exactly what files changed between audits
# Output: Detailed diff report with file lists
# Cost: $0 (local analysis only)
#
# Usage:
#   bash scripts/audit/audit_diff.sh [--verbose]
#
# Options:
#   --verbose    Show all added/removed files (not just samples)
#
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
SNAPSHOT_DIR="$PROJECT_ROOT/logs/audit/snapshots"
CURRENT_DATE=$(date +%Y-%m-%d\ %H:%M:%S)

# Parse arguments
VERBOSE=false
if [ "$1" == "--verbose" ]; then
    VERBOSE=true
fi

# Create snapshot directory
mkdir -p "$SNAPSHOT_DIR"

##############################################################################
# Create Current Snapshot
##############################################################################

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Audit Diff Report${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$PROJECT_ROOT"

echo "Creating current file snapshot..."

# Create current snapshots (sorted for comparison)
find data/nba_pbp -name "*.json" 2>/dev/null | sort > "$SNAPSHOT_DIR/current_pbp.txt"
find data/nba_box_score -name "*.json" 2>/dev/null | sort > "$SNAPSHOT_DIR/current_box.txt"
find data/nba_team_stats -name "*.json" 2>/dev/null | sort > "$SNAPSHOT_DIR/current_team.txt"
find data/nba_schedule_json -name "*.json" 2>/dev/null | sort > "$SNAPSHOT_DIR/current_sched.txt"

# Count current files
CURRENT_PBP=$(wc -l < "$SNAPSHOT_DIR/current_pbp.txt" | tr -d ' ')
CURRENT_BOX=$(wc -l < "$SNAPSHOT_DIR/current_box.txt" | tr -d ' ')
CURRENT_TEAM=$(wc -l < "$SNAPSHOT_DIR/current_team.txt" | tr -d ' ')
CURRENT_SCHED=$(wc -l < "$SNAPSHOT_DIR/current_sched.txt" | tr -d ' ')
CURRENT_TOTAL=$((CURRENT_PBP + CURRENT_BOX + CURRENT_TEAM + CURRENT_SCHED))

##############################################################################
# Compare to Last Snapshot
##############################################################################

# Check if last snapshot exists
if [ ! -f "$SNAPSHOT_DIR/last_pbp.txt" ]; then
    echo -e "${YELLOW}⚠️  No previous snapshot found${NC}"
    echo ""
    echo "This is the first diff run. Current state saved as baseline."
    echo ""
    echo "Current file counts:"
    echo -e "  Play-by-Play: ${GREEN}$CURRENT_PBP${NC} files"
    echo -e "  Box Scores: ${GREEN}$CURRENT_BOX${NC} files"
    echo -e "  Team Stats: ${GREEN}$CURRENT_TEAM${NC} files"
    echo -e "  Schedule: ${GREEN}$CURRENT_SCHED${NC} files"
    echo -e "  ${CYAN}Total: $CURRENT_TOTAL files${NC}"
    echo ""

    # Save as last for next run
    cp "$SNAPSHOT_DIR/current_pbp.txt" "$SNAPSHOT_DIR/last_pbp.txt"
    cp "$SNAPSHOT_DIR/current_box.txt" "$SNAPSHOT_DIR/last_box.txt"
    cp "$SNAPSHOT_DIR/current_team.txt" "$SNAPSHOT_DIR/last_team.txt"
    cp "$SNAPSHOT_DIR/current_sched.txt" "$SNAPSHOT_DIR/last_sched.txt"

    exit 0
fi

# Get last audit date from history
if [ -f "$PROJECT_ROOT/logs/audit/audit_history.csv" ]; then
    LAST_AUDIT=$(tail -2 "$PROJECT_ROOT/logs/audit/audit_history.csv" | head -1 | cut -d',' -f1)
    echo -e "Comparing to last audit: ${BLUE}$LAST_AUDIT${NC}"
else
    echo -e "Comparing to previous snapshot"
fi
echo ""

##############################################################################
# Analyze Changes
##############################################################################

TOTAL_ADDED=0
TOTAL_REMOVED=0

# Function to analyze data type
analyze_data_type() {
    local type_name="$1"
    local current_file="$2"
    local last_file="$3"

    echo -e "${CYAN}$type_name:${NC}"

    # Files added (in current but not in last)
    comm -13 "$last_file" "$current_file" > "$SNAPSHOT_DIR/temp_added.txt"
    local added=$(wc -l < "$SNAPSHOT_DIR/temp_added.txt" | tr -d ' ')

    # Files removed (in last but not in current)
    comm -23 "$last_file" "$current_file" > "$SNAPSHOT_DIR/temp_removed.txt"
    local removed=$(wc -l < "$SNAPSHOT_DIR/temp_removed.txt" | tr -d ' ')

    # Net change
    local net=$((added - removed))

    TOTAL_ADDED=$((TOTAL_ADDED + added))
    TOTAL_REMOVED=$((TOTAL_REMOVED + removed))

    # Display results
    if [ $added -eq 0 ] && [ $removed -eq 0 ]; then
        echo -e "  ${YELLOW}No changes${NC}"
    else
        if [ $added -gt 0 ]; then
            echo -e "  ${GREEN}Added: $added files${NC}"

            # Show sample or all
            if [ "$VERBOSE" = true ]; then
                cat "$SNAPSHOT_DIR/temp_added.txt" | xargs -I{} basename {} | sed 's/^/    + /'
            else
                # Show first 5
                head -5 "$SNAPSHOT_DIR/temp_added.txt" | xargs -I{} basename {} | sed 's/^/    + /'
                if [ $added -gt 5 ]; then
                    echo "    ... and $((added - 5)) more"
                fi
            fi
        fi

        if [ $removed -gt 0 ]; then
            echo -e "  ${RED}Removed: $removed files${NC}"

            # Show sample or all
            if [ "$VERBOSE" = true ]; then
                cat "$SNAPSHOT_DIR/temp_removed.txt" | xargs -I{} basename {} | sed 's/^/    - /'
            else
                # Show first 5
                head -5 "$SNAPSHOT_DIR/temp_removed.txt" | xargs -I{} basename {} | sed 's/^/    - /'
                if [ $removed -gt 5 ]; then
                    echo "    ... and $((removed - 5)) more"
                fi
            fi
        fi

        # Net change
        if [ $net -gt 0 ]; then
            echo -e "  ${GREEN}Net: +$net files${NC}"
        elif [ $net -lt 0 ]; then
            echo -e "  ${RED}Net: $net files${NC}"
        else
            echo -e "  ${YELLOW}Net: 0 files (equal adds/removes)${NC}"
        fi
    fi

    echo ""
}

# Analyze each data type
analyze_data_type "Play-by-Play" "$SNAPSHOT_DIR/current_pbp.txt" "$SNAPSHOT_DIR/last_pbp.txt"
analyze_data_type "Box Scores" "$SNAPSHOT_DIR/current_box.txt" "$SNAPSHOT_DIR/last_box.txt"
analyze_data_type "Team Stats" "$SNAPSHOT_DIR/current_team.txt" "$SNAPSHOT_DIR/last_team.txt"
analyze_data_type "Schedule" "$SNAPSHOT_DIR/current_sched.txt" "$SNAPSHOT_DIR/last_sched.txt"

##############################################################################
# Summary
##############################################################################

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

NET_CHANGE=$((TOTAL_ADDED - TOTAL_REMOVED))

echo -e "Total files added: ${GREEN}$TOTAL_ADDED${NC}"
echo -e "Total files removed: ${RED}$TOTAL_REMOVED${NC}"

if [ $NET_CHANGE -gt 0 ]; then
    echo -e "Net change: ${GREEN}+$NET_CHANGE${NC} files"
elif [ $NET_CHANGE -lt 0 ]; then
    echo -e "Net change: ${RED}$NET_CHANGE${NC} files"
else
    echo -e "Net change: ${YELLOW}0${NC} files"
fi

echo ""
echo "Current total: $CURRENT_TOTAL files"

if [ "$VERBOSE" = false ] && [ $((TOTAL_ADDED + TOTAL_REMOVED)) -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Tip: Run with --verbose to see all files${NC}"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

##############################################################################
# Save Current as Last for Next Diff
##############################################################################

cp "$SNAPSHOT_DIR/current_pbp.txt" "$SNAPSHOT_DIR/last_pbp.txt"
cp "$SNAPSHOT_DIR/current_box.txt" "$SNAPSHOT_DIR/last_box.txt"
cp "$SNAPSHOT_DIR/current_team.txt" "$SNAPSHOT_DIR/last_team.txt"
cp "$SNAPSHOT_DIR/current_sched.txt" "$SNAPSHOT_DIR/last_sched.txt"

# Clean up temp files
rm -f "$SNAPSHOT_DIR/temp_added.txt" "$SNAPSHOT_DIR/temp_removed.txt"

exit 0
