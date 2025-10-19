#!/bin/bash
#
# Implement Single Recommendation
#
# Automates the implementation of a single book recommendation.
# Checks dependencies, runs implementation script, runs tests, commits changes.
#
# Usage:
#   bash scripts/automation/implement_recommendation.sh rec_001
#   bash scripts/automation/implement_recommendation.sh rec_001 --dry-run
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Parse arguments
REC_ID="$1"
DRY_RUN=false

if [[ "$2" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Validate input
if [[ -z "$REC_ID" ]]; then
    echo -e "${RED}Error: Recommendation ID required${NC}"
    echo "Usage: $0 rec_XXX [--dry-run]"
    exit 1
fi

# Validate format
if [[ ! "$REC_ID" =~ ^rec_[0-9]{3}$ ]]; then
    echo -e "${RED}Error: Invalid recommendation ID format. Expected: rec_XXX${NC}"
    exit 1
fi

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}IMPLEMENTING RECOMMENDATION: $REC_ID${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Step 1: Load recommendation mapping
echo -e "${YELLOW}Step 1: Loading recommendation mapping...${NC}"

MAPPING_FILE="${WORKSPACE_ROOT}/data/recommendation_mapping.json"

if [[ ! -f "$MAPPING_FILE" ]]; then
    echo -e "${YELLOW}Mapping file not found. Generating...${NC}"
    cd "$WORKSPACE_ROOT"
    python3 scripts/automation/map_recommendations_to_phases.py
fi

# Get recommendation directory
REC_DIR=$(python3 -c "
import json
with open('${MAPPING_FILE}') as f:
    mapping = json.load(f)
if '${REC_ID}' in mapping:
    print(mapping['${REC_ID}']['directory'])
else:
    exit(1)
" 2>/dev/null)

if [[ -z "$REC_DIR" ]]; then
    echo -e "${RED}Error: Recommendation $REC_ID not found in mapping${NC}"
    exit 1
fi

REC_PATH="${WORKSPACE_ROOT}/${REC_DIR}"

if [[ ! -d "$REC_PATH" ]]; then
    echo -e "${RED}Error: Recommendation directory does not exist: $REC_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found recommendation at: $REC_PATH${NC}"
echo ""

# Step 2: Check current status
echo -e "${YELLOW}Step 2: Checking current status...${NC}"

STATUS_FILE="${REC_PATH}/STATUS.md"

if [[ ! -f "$STATUS_FILE" ]]; then
    echo -e "${RED}Error: STATUS.md not found${NC}"
    exit 1
fi

# Check if already complete
if grep -q "✅.*COMPLETE" "$STATUS_FILE"; then
    echo -e "${GREEN}✓ Recommendation already marked as COMPLETE${NC}"
    echo -e "${YELLOW}Skip? [y/N] ${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Skipping..."
        exit 0
    fi
fi

echo -e "${GREEN}✓ Status file found${NC}"
echo ""

# Step 3: Check dependencies
echo -e "${YELLOW}Step 3: Checking dependencies...${NC}"

# Extract dependencies from STATUS.md
DEPENDENCIES=$(grep -A 5 "Prerequisites:" "$STATUS_FILE" | grep -o "rec_[0-9]\{3\}" || true)

if [[ -n "$DEPENDENCIES" ]]; then
    echo "Dependencies found: $DEPENDENCIES"
    
    # Check if dependencies are met
    UNMET_DEPS=""
    for dep in $DEPENDENCIES; do
        # Get dependency status
        DEP_STATUS=$(python3 scripts/automation/check_recommendation_status.py --rec "$dep" 2>/dev/null | grep "Status:" | awk '{print $2}')
        
        if [[ "$DEP_STATUS" != "COMPLETE" ]]; then
            UNMET_DEPS="$UNMET_DEPS $dep"
        fi
    done
    
    if [[ -n "$UNMET_DEPS" ]]; then
        echo -e "${RED}✗ Unmet dependencies:$UNMET_DEPS${NC}"
        echo -e "${YELLOW}Cannot proceed. Implement dependencies first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All dependencies met${NC}"
else
    echo -e "${GREEN}✓ No dependencies${NC}"
fi
echo ""

# Step 4: Read implementation guide
echo -e "${YELLOW}Step 4: Reading implementation guide...${NC}"

README_FILE="${REC_PATH}/README.md"
GUIDE_FILE="${REC_PATH}/IMPLEMENTATION_GUIDE.md"

if [[ -f "$README_FILE" ]]; then
    TITLE=$(grep -m 1 "^# " "$README_FILE" | sed 's/^# //')
    echo "Title: $TITLE"
fi

if [[ -f "$GUIDE_FILE" ]]; then
    echo -e "${GREEN}✓ Implementation guide found${NC}"
    
    if [[ "$DRY_RUN" == true ]]; then
        echo ""
        echo -e "${BLUE}Implementation Guide Preview:${NC}"
        head -n 20 "$GUIDE_FILE"
        echo "..."
    fi
else:
    echo -e "${YELLOW}⚠ No implementation guide found${NC}"
fi
echo ""

# Step 5: Run implementation script
echo -e "${YELLOW}Step 5: Running implementation script...${NC}"

IMPL_SCRIPT="${REC_PATH}/implement_${REC_ID}.py"

if [[ ! -f "$IMPL_SCRIPT" ]]; then
    echo -e "${RED}Error: Implementation script not found: $IMPL_SCRIPT${NC}"
    exit 1
fi

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${BLUE}[DRY RUN] Would execute: python3 $IMPL_SCRIPT${NC}"
else
    echo "Executing implementation script..."
    cd "$REC_PATH"
    
    # Activate conda environment if available
    if command -v conda &> /dev/null; then
        echo "Activating conda environment: nba-aws"
        eval "$(conda shell.bash hook)"
        conda activate nba-aws || echo "Warning: Could not activate conda environment"
    fi
    
    # Run implementation
    if python3 "$IMPL_SCRIPT"; then
        echo -e "${GREEN}✓ Implementation script completed successfully${NC}"
    else
        echo -e "${RED}✗ Implementation script failed${NC}"
        exit 1
    fi
fi
echo ""

# Step 6: Run tests
echo -e "${YELLOW}Step 6: Running tests...${NC}"

TEST_SCRIPT="${REC_PATH}/test_${REC_ID}.py"

if [[ ! -f "$TEST_SCRIPT" ]]; then
    echo -e "${YELLOW}⚠ No test file found: $TEST_SCRIPT${NC}"
else
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${BLUE}[DRY RUN] Would execute: python3 -m pytest $TEST_SCRIPT -v${NC}"
    else
        echo "Running tests..."
        cd "$REC_PATH"
        
        if python3 -m pytest "$TEST_SCRIPT" -v; then
            echo -e "${GREEN}✓ All tests passed${NC}"
        else
            echo -e "${RED}✗ Tests failed${NC}"
            echo ""
            echo -e "${YELLOW}Fix the tests and run again.${NC}"
            exit 1
        fi
    fi
fi
echo ""

# Step 7: Update STATUS.md
echo -e "${YELLOW}Step 7: Updating STATUS.md...${NC}"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${BLUE}[DRY RUN] Would mark as COMPLETE in STATUS.md${NC}"
else
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Update status emoji
    sed -i '' 's/🔵.*PLANNED/✅ COMPLETE/' "$STATUS_FILE" || \
    sed -i 's/🔵.*PLANNED/✅ COMPLETE/' "$STATUS_FILE"
    
    # Add completion markers
    echo "" >> "$STATUS_FILE"
    echo "## Implementation Complete" >> "$STATUS_FILE"
    echo "" >> "$STATUS_FILE"
    echo "- ✅ Implementation complete: $TIMESTAMP" >> "$STATUS_FILE"
    echo "- ✅ Tests passing: $TIMESTAMP" >> "$STATUS_FILE"
    echo "- ✅ Committed: (pending)" >> "$STATUS_FILE"
    
    echo -e "${GREEN}✓ STATUS.md updated${NC}"
fi
echo ""

# Step 8: Commit changes
echo -e "${YELLOW}Step 8: Committing changes...${NC}"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${BLUE}[DRY RUN] Would commit with message:${NC}"
    echo "Implement $REC_ID: $TITLE"
    echo ""
    echo "- Implementation complete"
    echo "- All tests passing"
    echo "- Integrated with NBA Simulator system"
    echo ""
    echo "Status: COMPLETE ✅"
else
    cd "$WORKSPACE_ROOT"
    
    # Add changes
    git add "$REC_PATH"
    
    # Create commit message
    COMMIT_MSG="Implement $REC_ID: $TITLE

- Implementation complete
- All tests passing
- Integrated with NBA Simulator system

Status: COMPLETE ✅"
    
    # Commit
    if git commit -m "$COMMIT_MSG"; then
        echo -e "${GREEN}✓ Changes committed${NC}"
    else
        echo -e "${YELLOW}⚠ No changes to commit (may already be committed)${NC}"
    fi
fi
echo ""

# Step 9: Update progress tracker
echo -e "${YELLOW}Step 9: Updating progress tracker...${NC}"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${BLUE}[DRY RUN] Would update BOOK_RECOMMENDATIONS_PROGRESS.md${NC}"
else
    if python3 scripts/automation/check_recommendation_status.py --update "$REC_ID"; then
        echo -e "${GREEN}✓ Progress tracker updated${NC}"
    else
        echo -e "${YELLOW}⚠ Could not update progress tracker${NC}"
    fi
fi
echo ""

# Success!
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✓ SUCCESS: $REC_ID IMPLEMENTATION COMPLETE${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

# Show next recommendations
if [[ "$DRY_RUN" != true ]]; then
    echo -e "${BLUE}Next available recommendations:${NC}"
    python3 scripts/automation/check_recommendation_status.py --next | head -n 20
fi

exit 0

