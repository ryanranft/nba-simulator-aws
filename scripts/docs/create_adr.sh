#!/bin/bash
#
# Create a new Architecture Decision Record (ADR)
#
# Usage:
#   bash scripts/docs/create_adr.sh "decision-title"
#
# Example:
#   bash scripts/docs/create_adr.sh "switch-to-postgresql-jsonb"
#   Creates: docs/adr/011-switch-to-postgresql-jsonb.md
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if title provided
if [ -z "$1" ]; then
    print_error "Error: ADR title required"
    echo ""
    echo "Usage: bash scripts/docs/create_adr.sh \"decision-title\""
    echo ""
    echo "Examples:"
    echo "  bash scripts/docs/create_adr.sh \"switch-to-postgresql-jsonb\""
    echo "  bash scripts/docs/create_adr.sh \"adopt-cloudwatch-monitoring\""
    echo "  bash scripts/docs/create_adr.sh \"use-semantic-versioning\""
    exit 1
fi

ADR_TITLE="$1"

# Calculate next ADR number
# Count existing ADRs (files matching pattern NNN-*.md where NNN is 3 digits)
EXISTING_ADRS=$(ls docs/adr/ | grep -E '^[0-9]{3}-.*\.md$' | wc -l | tr -d ' ')
ADR_NUMBER=$((EXISTING_ADRS + 1))

# Zero-pad to 3 digits
ADR_NUMBER=$(printf "%03d" $ADR_NUMBER)

# Create filename
ADR_FILE="docs/adr/${ADR_NUMBER}-${ADR_TITLE}.md"

# Check if template exists
if [ ! -f "docs/adr/_TEMPLATE.md" ]; then
    print_error "Template not found: docs/adr/_TEMPLATE.md"
    exit 1
fi

# Check if ADR already exists
if [ -f "$ADR_FILE" ]; then
    print_warning "ADR already exists: $ADR_FILE"
    read -p "Overwrite? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        print_info "Cancelled"
        exit 0
    fi
fi

print_info "Creating ADR-${ADR_NUMBER}: ${ADR_TITLE}"

# Copy template
cp docs/adr/_TEMPLATE.md "$ADR_FILE"

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Replace placeholders
# macOS uses BSD sed, Linux uses GNU sed - handle both
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/ADR-XXX/ADR-${ADR_NUMBER}/g" "$ADR_FILE"
    sed -i '' "s/\[Decision Title\]/${ADR_TITLE}/g" "$ADR_FILE"
    sed -i '' "s/YYYY-MM-DD/${CURRENT_DATE}/g" "$ADR_FILE"
    sed -i '' "s/\[Team\/Individual\]/Ryan Ranft + Claude Code/g" "$ADR_FILE"
else
    # Linux
    sed -i "s/ADR-XXX/ADR-${ADR_NUMBER}/g" "$ADR_FILE"
    sed -i "s/\[Decision Title\]/${ADR_TITLE}/g" "$ADR_FILE"
    sed -i "s/YYYY-MM-DD/${CURRENT_DATE}/g" "$ADR_FILE"
    sed -i "s/\[Team\/Individual\]/Ryan Ranft + Claude Code/g" "$ADR_FILE"
fi

print_success "Created: $ADR_FILE"

# Show file structure
echo ""
print_info "ADR file structure:"
head -10 "$ADR_FILE"
echo "..."

# Update ADR README index
echo ""
print_info "Don't forget to update docs/adr/README.md with the new ADR!"

# Open in editor (if EDITOR set, otherwise try common editors)
echo ""
if [ -n "$EDITOR" ]; then
    print_info "Opening in \$EDITOR: $EDITOR"
    $EDITOR "$ADR_FILE"
elif command -v code &> /dev/null; then
    print_info "Opening in VS Code"
    code "$ADR_FILE"
elif command -v nano &> /dev/null; then
    print_info "Opening in nano"
    nano "$ADR_FILE"
else
    print_warning "No editor found. Please open manually: $ADR_FILE"
fi

print_success "ADR-${ADR_NUMBER} ready for editing!"
