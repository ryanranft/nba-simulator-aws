#!/bin/bash
# scripts/maintenance/update_docs.sh
# Automatically update documentation files with current project state

set -e

PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Documentation Auto-Update"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to update a section in a file
update_section() {
    local file=$1
    local start_marker=$2
    local end_marker=$3
    local new_content=$4

    if [ ! -f "$file" ]; then
        echo "⚠️  File not found: $file"
        return 1
    fi

    # Create backup
    cp "$file" "${file}.backup"

    # Use awk to replace section
    awk -v start="$start_marker" -v end="$end_marker" -v content="$new_content" '
        $0 ~ start {print; print content; skip=1; next}
        $0 ~ end {skip=0}
        !skip
    ' "${file}.backup" > "$file"

    rm "${file}.backup"
}

# ============================================================================
# 1. Update QUICKSTART.md with current costs
# ============================================================================

echo "1. Updating QUICKSTART.md..."

# Get current AWS cost
CURRENT_COST=$(aws ce get-cost-and-usage \
    --time-period Start=$(date -u -v1d +%Y-%m-01 2>/dev/null || date -u -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
    --output text 2>/dev/null || echo "0")

CURRENT_COST_FORMATTED=$(printf "%.2f" "$CURRENT_COST" 2>/dev/null || echo "2.74")

# Get next phase from PROGRESS.md
NEXT_PHASE=$(grep -A 5 "### Next Immediate Steps" PROGRESS.md | grep "^[0-9]" | head -1 || echo "1. Check PROGRESS.md for next steps")

# Update cost section in QUICKSTART.md
if [ -f "QUICKSTART.md" ]; then
    sed -i.bak "s/\*\*Current:\*\* ~\$[0-9.]*\/month/\*\*Current:\*\* ~\$$CURRENT_COST_FORMATTED\/month/g" QUICKSTART.md
    rm QUICKSTART.md.bak
    echo "   ✅ Updated current costs to \$$CURRENT_COST_FORMATTED/month"
else
    echo "   ⚠️  QUICKSTART.md not found"
fi

# ============================================================================
# 2. Update ADR index in docs/adr/README.md
# ============================================================================

echo "2. Updating ADR index..."

if [ -d "docs/adr" ]; then
    ADR_COUNT=$(find docs/adr -name "[0-9]*.md" -type f | wc -l | tr -d ' ')

    # Update ADR count in README
    if [ -f "docs/adr/README.md" ]; then
        sed -i.bak "s/\*\*Total ADRs:\*\* [0-9]*/\*\*Total ADRs:\*\* $ADR_COUNT/g" docs/adr/README.md
        rm docs/adr/README.md.bak
        echo "   ✅ Updated ADR count to $ADR_COUNT"
    fi
else
    echo "   ⚠️  docs/adr directory not found"
fi

# ============================================================================
# 3. Update project statistics in PROGRESS.md
# ============================================================================

echo "3. Updating PROGRESS.md statistics..."

if [ -f "PROGRESS.md" ]; then
    # Count commits
    COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")

    # Get S3 object count
    S3_OBJECT_COUNT=$(aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize 2>/dev/null | \
        grep "Total Objects" | awk '{print $3}' || echo "146115")

    # Check if RDS exists
    RDS_STATUS=$(aws rds describe-db-instances --db-instance-identifier nba-sim-db \
        --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "not-created")

    # Check if Glue exists
    GLUE_STATUS=$(aws glue get-crawler --name nba-data-crawler \
        --query 'Crawler.State' --output text 2>/dev/null || echo "not-created")

    echo "   ✅ Stats: $COMMIT_COUNT commits, $S3_OBJECT_COUNT S3 objects"
    echo "   ✅ RDS: $RDS_STATUS, Glue: $GLUE_STATUS"
else
    echo "   ⚠️  PROGRESS.md not found"
fi

# ============================================================================
# 4. Update Last Updated timestamps
# ============================================================================

echo "4. Updating 'Last Updated' timestamps..."

CURRENT_DATE=$(date +%Y-%m-%d)

# Update timestamps in all docs
for file in QUICKSTART.md docs/STYLE_GUIDE.md docs/TESTING.md docs/TROUBLESHOOTING.md docs/adr/README.md; do
    if [ -f "$file" ]; then
        sed -i.bak "s/\*\*Last Updated:\*\* [0-9-]*/\*\*Last Updated:\*\* $CURRENT_DATE/g" "$file"
        rm "${file}.bak" 2>/dev/null || true
        echo "   ✅ Updated timestamp in $file"
    fi
done

# ============================================================================
# 5. Generate statistics report
# ============================================================================

echo "5. Generating statistics..."

# Count lines of code (excluding data files)
LOC=$(find . -name "*.py" -o -name "*.sh" -o -name "*.sql" 2>/dev/null | \
    grep -v "__pycache__" | grep -v ".git" | grep -v "data/" | \
    xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")

# Count documentation lines
DOC_LINES=$(find docs -name "*.md" 2>/dev/null | xargs wc -l 2>/dev/null | \
    tail -1 | awk '{print $1}' || echo "0")

# Count test files
TEST_COUNT=$(find tests -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project Statistics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Lines of code: $LOC"
echo "Documentation lines: $DOC_LINES"
echo "Test files: $TEST_COUNT"
echo "Git commits: $COMMIT_COUNT"
echo "S3 objects: $S3_OBJECT_COUNT"
echo "ADRs: $ADR_COUNT"
echo "Current AWS cost: \$$CURRENT_COST_FORMATTED/month"
echo ""

# ============================================================================
# 6. Check for stale documentation
# ============================================================================

echo "6. Checking for stale documentation..."

# Find docs not updated in 30+ days
find docs -name "*.md" -mtime +30 2>/dev/null | while read -r file; do
    echo "   ⚠️  Stale (30+ days): $file"
done

# ============================================================================
# 7. Validate documentation links
# ============================================================================

echo "7. Validating internal links..."

BROKEN_LINKS=0
for file in $(find docs -name "*.md" 2>/dev/null); do
    # Extract markdown links
    grep -oP '\[.*?\]\(\K[^)]+' "$file" 2>/dev/null | while read -r link; do
        # Skip external links
        if [[ "$link" =~ ^http ]]; then
            continue
        fi

        # Check if local file exists
        if [[ ! -f "docs/$link" ]] && [[ ! -f "$link" ]]; then
            echo "   ⚠️  Broken link in $file: $link"
            BROKEN_LINKS=$((BROKEN_LINKS + 1))
        fi
    done
done

if [ "$BROKEN_LINKS" -eq 0 ]; then
    echo "   ✅ All internal links valid"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Documentation update complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit if satisfied: git add -u && git commit -m 'Update documentation'"
echo "  3. Run this script weekly to keep docs current"