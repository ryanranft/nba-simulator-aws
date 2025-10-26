#!/bin/bash
#
# Create New Sub-Phase - Auto-generator for ADR-010 compliance
#
# Purpose: Generate new sub-phase with automatic 4-digit numbering
# Usage: ./create_new_subphase.sh <phase_num> "<subphase_name>"
# Example: ./create_new_subphase.sh 5 "optimize_inference"
#
# Created: October 26, 2025
# ADR: 010 (4-digit sub-phase numbering)

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validate arguments
if [ $# -ne 2 ]; then
    echo -e "${RED}Error: Incorrect number of arguments${NC}"
    echo ""
    echo "Usage: $0 <phase_num> \"<subphase_name>\""
    echo ""
    echo "Arguments:"
    echo "  phase_num      - Single digit (0-9)"
    echo "  subphase_name  - Snake_case name (no spaces)"
    echo ""
    echo "Example:"
    echo "  $0 5 \"optimize_inference\""
    echo "  $0 0 \"data_validation\""
    exit 1
fi

PHASE_NUM=$1
SUBPHASE_NAME=$2

# Validate phase number
if ! [[ "$PHASE_NUM" =~ ^[0-9]$ ]]; then
    echo -e "${RED}Error: Phase number must be single digit (0-9)${NC}"
    echo "Received: $PHASE_NUM"
    exit 1
fi

# Validate subphase name (snake_case)
if [[ "$SUBPHASE_NAME" =~ [[:space:]] ]]; then
    echo -e "${RED}Error: Sub-phase name cannot contain spaces${NC}"
    echo "Use snake_case format: optimize_inference"
    echo "Received: $SUBPHASE_NAME"
    exit 1
fi

# Define paths
PHASE_INDEX="docs/phases/PHASE_${PHASE_NUM}_INDEX.md"
PHASE_DIR="docs/phases/phase_${PHASE_NUM}"

# Check if phase exists
if [ ! -f "$PHASE_INDEX" ]; then
    echo -e "${RED}Error: Phase ${PHASE_NUM} does not exist${NC}"
    echo "File not found: $PHASE_INDEX"
    echo ""
    echo "Create phase first:"
    echo "  ./create_new_phase.sh $PHASE_NUM \"<phase_name>\""
    exit 1
fi

if [ ! -d "$PHASE_DIR" ]; then
    echo -e "${RED}Error: Phase directory does not exist${NC}"
    echo "Directory not found: $PHASE_DIR"
    exit 1
fi

# Find next available sub-phase number
echo -e "${BLUE}Finding next available sub-phase number...${NC}"

# Extract all existing N.MMMM numbers from phase index
EXISTING_NUMS=$(grep -oE "${PHASE_NUM}\.[0-9]{4}" "$PHASE_INDEX" 2>/dev/null || echo "")

if [ -z "$EXISTING_NUMS" ]; then
    # No existing sub-phases found, start at 0001
    NEXT_NUM="0001"
    echo "No existing sub-phases found, starting at ${PHASE_NUM}.0001"
else
    # Find highest number and increment
    HIGHEST=$(echo "$EXISTING_NUMS" | sed "s/${PHASE_NUM}\.//" | sort -n | tail -1)
    NEXT_NUM=$(printf "%04d" $((10#$HIGHEST + 1)))
    echo "Found $(echo "$EXISTING_NUMS" | wc -l | tr -d ' ') existing sub-phases"
    echo "Highest: ${PHASE_NUM}.${HIGHEST}"
    echo "Next: ${PHASE_NUM}.${NEXT_NUM}"
fi

SUBPHASE_ID="${PHASE_NUM}.${NEXT_NUM}"
SUBPHASE_DIR="${PHASE_DIR}/${SUBPHASE_ID}_${SUBPHASE_NAME}"

# Check if sub-phase already exists
if [ -d "$SUBPHASE_DIR" ]; then
    echo -e "${RED}Error: Sub-phase directory already exists${NC}"
    echo "Directory: $SUBPHASE_DIR"
    exit 1
fi

# Create sub-phase directory
echo ""
echo -e "${GREEN}Creating Sub-Phase ${SUBPHASE_ID}: ${SUBPHASE_NAME}${NC}"
echo ""

mkdir -p "$SUBPHASE_DIR"
echo "✅ Created: $SUBPHASE_DIR/"

# Create README
cat > "$SUBPHASE_DIR/README.md" <<EOF
# Phase ${SUBPHASE_ID}: ${SUBPHASE_NAME}

**Status:** ⏸️ PENDING
**Priority:** TBD
**Estimated Time:** TBD
**Created:** $(date +%Y-%m-%d)

---

## Overview

[Brief description of what this sub-phase accomplishes]

---

## Objectives

- [ ] Objective 1
- [ ] Objective 2
- [ ] Objective 3

---

## Tasks

### 1. [Task Category 1]
- [ ] Task 1.1
- [ ] Task 1.2

### 2. [Task Category 2]
- [ ] Task 2.1
- [ ] Task 2.2

---

## Implementation

### Setup

\`\`\`bash
# Setup commands
\`\`\`

### Execution

\`\`\`bash
# Execution commands
\`\`\`

### Validation

\`\`\`bash
# Validation commands
\`\`\`

---

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All tests passing
- [ ] Documentation complete

---

## References

- **Phase Index:** [PHASE_${PHASE_NUM}_INDEX.md](../../PHASE_${PHASE_NUM}_INDEX.md)
- **ADR-010:** [4-Digit Sub-Phase Numbering](../../adr/010-four-digit-subphase-numbering.md)

---

**Dependencies:** [List any prerequisite sub-phases]
**Next Steps:** [What comes after this sub-phase]
EOF

echo "✅ Created: ${SUBPHASE_DIR}/README.md"

# Generate phase index update instructions
PHASE_INDEX_ROW="| **${SUBPHASE_ID}** | ${SUBPHASE_NAME} | ⏸️ PENDING | TBD | [${SUBPHASE_ID}_${SUBPHASE_NAME}](phase_${PHASE_NUM}/${SUBPHASE_ID}_${SUBPHASE_NAME}/README.md) |"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}MANUAL STEP REQUIRED${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Add this row to the sub-phases table in:"
echo "  $PHASE_INDEX"
echo ""
echo "Row to add:"
echo "$PHASE_INDEX_ROW"
echo ""
echo "Location: Insert in the sub-phases table in numerical order"
echo ""

# Summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Sub-Phase ${SUBPHASE_ID} Created Successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Sub-Phase: ${SUBPHASE_ID} - ${SUBPHASE_NAME}"
echo ""
echo "Files created:"
echo "  - ${SUBPHASE_DIR}/"
echo "  - ${SUBPHASE_DIR}/README.md"
echo ""
echo "Next steps:"
echo "  1. Add row to $PHASE_INDEX (see above)"
echo "  2. Edit ${SUBPHASE_DIR}/README.md with implementation details"
echo "  3. Create tests (optional):"
echo "     mkdir -p tests/phases/phase_${PHASE_NUM}"
echo "     touch tests/phases/phase_${PHASE_NUM}/test_${PHASE_NUM}_${NEXT_NUM}_${SUBPHASE_NAME}.py"
echo "  4. Create validators (optional):"
echo "     mkdir -p validators/phases/phase_${PHASE_NUM}"
echo "     touch validators/phases/phase_${PHASE_NUM}/validate_${PHASE_NUM}_${NEXT_NUM}_${SUBPHASE_NAME}.py"
echo ""
echo "Validation:"
echo "  bash scripts/maintenance/validate_phase_numbering.sh"
echo ""
