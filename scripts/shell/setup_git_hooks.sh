#!/bin/bash
# Setup Git Hooks for NBA Simulator AWS Project
# This script installs all Git hooks used by the project

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NBA Simulator AWS - Git Hooks Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get project root directory
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

if [ -z "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    echo "   Please run this script from within the nba-simulator-aws project"
    exit 1
fi

echo "Project root: $PROJECT_ROOT"
echo ""

# Ensure .git/hooks directory exists
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${RED}❌ Error: .git/hooks directory not found${NC}"
    exit 1
fi

# Function to create hook
create_hook() {
    local hook_name=$1
    local hook_path="$HOOKS_DIR/$hook_name"

    echo "Installing $hook_name hook..."

    case $hook_name in
        "post-commit")
            cat > "$hook_path" << 'EOF'
#!/bin/bash
# Post-commit hook: Automatically log session snapshot after every commit

# Change to project root directory
cd "$(git rev-parse --show-toplevel)"

# Append session snapshot to .session-history.md
bash scripts/shell/session_startup.sh >> .session-history.md

# Silent success
exit 0
EOF
            ;;
        *)
            echo -e "${RED}❌ Unknown hook: $hook_name${NC}"
            return 1
            ;;
    esac

    # Make hook executable
    chmod +x "$hook_path"

    # Verify hook was created
    if [ -x "$hook_path" ]; then
        echo -e "${GREEN}✅ $hook_name installed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to install $hook_name${NC}"
        return 1
    fi
}

# Install all hooks
echo "Installing Git hooks..."
echo ""

HOOKS_INSTALLED=0
HOOKS_FAILED=0

# Post-commit hook (session history logging)
if create_hook "post-commit"; then
    ((HOOKS_INSTALLED++))
else
    ((HOOKS_FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Hooks installed: $HOOKS_INSTALLED${NC}"

if [ $HOOKS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Hooks failed: $HOOKS_FAILED${NC}"
fi

echo ""

# List installed hooks
echo "Installed hooks in $HOOKS_DIR:"
ls -lh "$HOOKS_DIR" | grep -E "^-rwx" | awk '{print "  " $9}' || echo "  (none)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "What these hooks do:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "post-commit:"
echo "  - Automatically appends environment snapshot to .session-history.md"
echo "  - Logs: hardware, Python version, conda env, git status, packages"
echo "  - Enables correlation of commits with exact software versions"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To test the post-commit hook:"
echo "  1. Make a test commit:"
echo "     touch test.txt"
echo "     git add test.txt"
echo "     git commit -m \"Test post-commit hook\""
echo ""
echo "  2. Verify .session-history.md was updated:"
echo "     tail -20 .session-history.md"
echo ""
echo "  3. Clean up:"
echo "     git rm test.txt"
echo "     git commit -m \"Remove test file\""
echo ""

if [ $HOOKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All hooks installed successfully!${NC}"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠ Some hooks failed to install. Check errors above.${NC}"
    echo ""
    exit 1
fi