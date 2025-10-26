#!/bin/bash
#
# Create New Phase - Auto-generator for ADR-010 compliance
#
# Purpose: Generate new phase structure with 4-digit sub-phase format
# Usage: ./create_new_phase.sh <phase_num> "<phase_name>"
# Example: ./create_new_phase.sh 6 "Model Deployment"
#
# Created: October 26, 2025
# ADR: 010 (4-digit sub-phase numbering)

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validate arguments
if [ $# -ne 2 ]; then
    echo -e "${RED}Error: Incorrect number of arguments${NC}"
    echo ""
    echo "Usage: $0 <phase_num> \"<phase_name>\""
    echo ""
    echo "Arguments:"
    echo "  phase_num   - Single digit (0-9)"
    echo "  phase_name  - Descriptive name (quoted)"
    echo ""
    echo "Example:"
    echo "  $0 6 \"Model Deployment\""
    exit 1
fi

PHASE_NUM=$1
PHASE_NAME=$2

# Validate phase number
if ! [[ "$PHASE_NUM" =~ ^[0-9]$ ]]; then
    echo -e "${RED}Error: Phase number must be single digit (0-9)${NC}"
    echo "Received: $PHASE_NUM"
    exit 1
fi

# Define paths
PHASE_INDEX="docs/phases/PHASE_${PHASE_NUM}_INDEX.md"
PHASE_DIR="docs/phases/phase_${PHASE_NUM}"
SUBPHASE_DIR="${PHASE_DIR}/${PHASE_NUM}.0001_initial_setup"
TEMPLATE="docs/templates/phase-index-template.md"

# Check if phase already exists
if [ -f "$PHASE_INDEX" ]; then
    echo -e "${RED}Error: Phase already exists${NC}"
    echo "File: $PHASE_INDEX"
    echo ""
    echo "To add a sub-phase to existing phase, use:"
    echo "  ./create_new_subphase.sh $PHASE_NUM \"<subphase_name>\""
    exit 1
fi

if [ -d "$PHASE_DIR" ]; then
    echo -e "${RED}Error: Phase directory already exists${NC}"
    echo "Directory: $PHASE_DIR"
    exit 1
fi

# Check template exists
if [ ! -f "$TEMPLATE" ]; then
    echo -e "${YELLOW}Warning: Template not found: $TEMPLATE${NC}"
    echo "Creating phase without template..."
    USE_TEMPLATE=false
else
    USE_TEMPLATE=true
fi

# Create phase index
echo -e "${GREEN}Creating Phase ${PHASE_NUM}: ${PHASE_NAME}${NC}"
echo ""

if [ "$USE_TEMPLATE" = true ]; then
    # Use template
    cp "$TEMPLATE" "$PHASE_INDEX"

    # Replace placeholders (macOS compatible)
    sed -i '' "s/PHASE_N/PHASE_${PHASE_NUM}/g" "$PHASE_INDEX"
    sed -i '' "s/Phase N:/Phase ${PHASE_NUM}:/g" "$PHASE_INDEX"
    sed -i '' "s/\[Phase Name\]/${PHASE_NAME}/g" "$PHASE_INDEX"
    sed -i '' "s/phase_N/phase_${PHASE_NUM}/g" "$PHASE_INDEX"

    echo "✅ Created: $PHASE_INDEX (from template)"
else
    # Create minimal phase index without template
    cat > "$PHASE_INDEX" <<EOF
# Phase ${PHASE_NUM}: ${PHASE_NAME}

**Status:** ⏸️ PENDING
**Priority:** TBD
**Estimated Time:** TBD

---

## Overview

${PHASE_NAME} implementation phase.

## Sub-Phases

| Sub-Phase | Name | Status | Est. Time | File |
|-----------|------|--------|-----------|------|
| **${PHASE_NUM}.0001** | Initial Setup | ⏸️ PENDING | 2-4h | [${PHASE_NUM}.0001_initial_setup](phase_${PHASE_NUM}/${PHASE_NUM}.0001_initial_setup/README.md) |

---

**Created:** $(date +%Y-%m-%d)
**Last Updated:** $(date +%Y-%m-%d)
EOF

    echo "✅ Created: $PHASE_INDEX (minimal)"
fi

# Create phase directory
mkdir -p "$PHASE_DIR"
echo "✅ Created: $PHASE_DIR/"

# Create first sub-phase (N.0001_initial_setup)
mkdir -p "$SUBPHASE_DIR"

# Create README for first sub-phase
cat > "$SUBPHASE_DIR/README.md" <<EOF
# Phase ${PHASE_NUM}.0001: Initial Setup

**Status:** ⏸️ PENDING
**Priority:** HIGH
**Estimated Time:** 2-4 hours
**Created:** $(date +%Y-%m-%d)

---

## Overview

Initial setup and planning for Phase ${PHASE_NUM}: ${PHASE_NAME}.

This sub-phase establishes the foundation for all subsequent work in this phase.

---

## Objectives

- [ ] Define phase scope and requirements
- [ ] Create implementation plan
- [ ] Set up necessary infrastructure
- [ ] Document architecture decisions

---

## Tasks

### 1. Requirements Gathering
- [ ] Review project goals
- [ ] Identify dependencies
- [ ] Document success criteria

### 2. Planning
- [ ] Break down into sub-phases
- [ ] Estimate time and resources
- [ ] Identify risks

### 3. Setup
- [ ] Create directory structure
- [ ] Set up testing framework
- [ ] Initialize documentation

---

## Success Criteria

- [ ] Phase objectives clearly defined
- [ ] Sub-phases planned and documented
- [ ] Infrastructure ready
- [ ] Team aligned on approach

---

## References

- **Phase Index:** [PHASE_${PHASE_NUM}_INDEX.md](../../PHASE_${PHASE_NUM}_INDEX.md)
- **ADR-010:** [4-Digit Sub-Phase Numbering](../../adr/010-four-digit-subphase-numbering.md)

---

**Next Steps:** Define subsequent sub-phases (${PHASE_NUM}.0002, ${PHASE_NUM}.0003, etc.)
EOF

echo "✅ Created: ${SUBPHASE_DIR}/"
echo "✅ Created: ${SUBPHASE_DIR}/README.md"

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Phase ${PHASE_NUM} Created Successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Phase: ${PHASE_NUM} - ${PHASE_NAME}"
echo ""
echo "Files created:"
echo "  - $PHASE_INDEX"
echo "  - $PHASE_DIR/"
echo "  - ${SUBPHASE_DIR}/"
echo "  - ${SUBPHASE_DIR}/README.md"
echo ""
echo "Next steps:"
echo "  1. Edit $PHASE_INDEX to add phase details"
echo "  2. Update PROGRESS.md to include new phase"
echo "  3. Add subsequent sub-phases:"
echo "     ./create_new_subphase.sh $PHASE_NUM \"<subphase_name>\""
echo ""
echo "Validation:"
echo "  bash scripts/maintenance/validate_phase_numbering.sh"
echo ""
