#!/bin/bash
# Validate 4-digit phase numbering compliance (ADR-010)
#
# This pre-commit hook ensures all phase-related files use the 4-digit
# zero-padded sub-phase numbering format (N.MMMM) instead of the old
# variable-length format (N.M).
#
# Related: docs/adr/010-four-digit-subphase-numbering.md

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Track violations
VIOLATIONS=0

echo "🔍 Validating 4-digit phase numbering format (ADR-010)..."

# Check phase directories for old format
echo "   Checking phase directories..."
OLD_DIRS=$(find docs/phases/phase_* -maxdepth 1 -type d -name "[0-9].[0-9]_*" -o -name "[0-9].[0-9][0-9]_*" 2>/dev/null | grep -v "0\.0[0-9][0-9][0-9]_\|5\.0[0-9][0-9][0-9]_" || true)

if [ -n "$OLD_DIRS" ]; then
    echo -e "${RED}✗ Found directories using old format:${NC}"
    echo "$OLD_DIRS" | sed 's/^/    /'
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}   ✓ All directories use 4-digit format${NC}"
fi

# Check test files for old format in Phase 0 and 5 (migrated phases)
echo "   Checking test file names (Phase 0 & 5)..."
OLD_TESTS=$(find tests/phases/phase_0 tests/phases/phase_5 -type f \( -name "test_0_[0-9].py" -o -name "test_0_[0-9][0-9].py" -o -name "test_5_[0-9].py" -o -name "test_5_[0-9][0-9].py" -o -name "test_5_[0-9][0-9][0-9].py" \) 2>/dev/null | grep -v "test_[0-9]_0[0-9][0-9][0-9]\.py" || true)

if [ -n "$OLD_TESTS" ]; then
    echo -e "${RED}✗ Found test files using old format:${NC}"
    echo "$OLD_TESTS" | sed 's/^/    /'
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}   ✓ All test files use 4-digit format${NC}"
fi

# Check validator files for old format in Phase 0 and 5 (migrated phases)
echo "   Checking validator file names (Phase 0 & 5)..."
OLD_VALIDATORS=$(find validators/phases/phase_0 validators/phases/phase_5 -type f \( -name "validate_0_[0-9].py" -o -name "validate_0_[0-9][0-9].py" -o -name "validate_5_[0-9].py" -o -name "validate_5_[0-9][0-9].py" -o -name "validate_5_[0-9][0-9][0-9].py" \) 2>/dev/null | grep -v "validate_[0-9]_0[0-9][0-9][0-9]\.py" || true)

if [ -n "$OLD_VALIDATORS" ]; then
    echo -e "${RED}✗ Found validator files using old format:${NC}"
    echo "$OLD_VALIDATORS" | sed 's/^/    /'
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}   ✓ All validator files use 4-digit format${NC}"
fi

# Check key documentation files for old format references in file paths
echo "   Checking documentation file path references..."
KEY_DOCS="CLAUDE.md QUICKSTART.md scripts/automation/validate_phase.py"
for doc in $KEY_DOCS; do
    if [ -f "$doc" ]; then
        # Look for path patterns like "phase_0/0.1_" or "5.19_" but not "0.0001_" or "5.0019_"
        OLD_REFS=$(grep -n "phase_[0-9]/[0-9]\.[0-9]_\|phase_[0-9]/[0-9]\.[0-9][0-9]_" "$doc" 2>/dev/null | grep -v "/[0-9]\.0[0-9][0-9][0-9]_" || true)

        if [ -n "$OLD_REFS" ]; then
            echo -e "${RED}✗ Found old format path references in $doc:${NC}"
            echo "$OLD_REFS" | sed 's/^/    /'
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
done

if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✓ All phase numbering compliant with ADR-010${NC}"
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}✗ Phase numbering validation FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}ADR-010 requires 4-digit zero-padded format:${NC}"
    echo "   OLD: 0.1_name, 0.10_name, 5.19_name"
    echo "   NEW: 0.0001_name, 0.0010_name, 5.0019_name"
    echo ""
    echo -e "${YELLOW}See: docs/adr/010-four-digit-subphase-numbering.md${NC}"
    echo ""
    exit 1
fi

exit 0
