#!/bin/bash
# NBA MCP Synthesis - Security Scanning Setup Script
# Sets up git-secrets, trufflehog, and pre-commit hooks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

echo ""
echo "======================================"
echo "Security Scanning Setup"
echo "NBA MCP Synthesis Project"
echo "======================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    HAS_BREW=true
    if ! command -v brew &> /dev/null; then
        log_warn "Homebrew not found. Some tools may need manual installation."
        HAS_BREW=false
    fi
else
    HAS_BREW=false
    log_info "Not running on macOS. Will use alternative installation methods."
fi

# Step 1: Install git-secrets
log "Installing git-secrets..."
if command -v git-secrets &> /dev/null; then
    log_info "git-secrets already installed: $(git secrets --version)"
else
    if [[ "$HAS_BREW" == true ]]; then
        brew install git-secrets
        log "✅ git-secrets installed via Homebrew"
    else
        # Install from source on Linux
        log_info "Installing git-secrets from source..."
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        git clone https://github.com/awslabs/git-secrets.git
        cd git-secrets
        sudo make install
        cd -
        rm -rf "$TEMP_DIR"
        log "✅ git-secrets installed from source"
    fi
fi

# Step 2: Install trufflehog
log "Installing trufflehog..."
if command -v trufflehog &> /dev/null; then
    log_info "trufflehog already installed: $(trufflehog --version)"
else
    if [[ "$HAS_BREW" == true ]]; then
        brew install trufflehog
        log "✅ trufflehog installed via Homebrew"
    else
        # Install using go on Linux
        log_info "Installing trufflehog using go..."
        if command -v go &> /dev/null; then
            go install github.com/trufflesecurity/trufflehog/v3@latest
            log "✅ trufflehog installed via go"
        else
            log_warn "go not found. Please install trufflehog manually:"
            log_warn "  https://github.com/trufflesecurity/trufflehog#installation"
        fi
    fi
fi

# Step 3: Install Python packages
log "Installing Python packages..."
if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    if ! command -v pip3 &> /dev/null; then
        PIP_CMD="pip"
    fi

    $PIP_CMD install pre-commit detect-secrets --upgrade
    log "✅ Python packages installed (pre-commit, detect-secrets)"
else
    log_error "pip not found. Please install Python packages manually:"
    log_error "  pip install pre-commit detect-secrets"
    exit 1
fi

# Step 4: Setup git-secrets for this repo
log "Configuring git-secrets for this repository..."
cd "$(git rev-parse --show-toplevel)" || exit 1

# Install git-secrets hooks
git secrets --install --force || log_warn "git-secrets hooks may already be installed"

# Register AWS patterns
git secrets --register-aws || log_info "AWS patterns already registered"

# Add custom patterns from .git-secrets-patterns file
if [[ -f ".git-secrets-patterns" ]]; then
    log "Adding custom secret patterns..."
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
            git secrets --add "$line" || log_info "Pattern may already exist: $line"
        fi
    done < .git-secrets-patterns
    log "✅ Custom patterns added"
else
    log_warn ".git-secrets-patterns file not found. Skipping custom patterns."
fi

# Step 5: Initialize detect-secrets baseline
log "Initializing detect-secrets baseline..."
if [[ -f ".secrets.baseline" ]]; then
    log_info "Baseline file already exists. Updating..."
    detect-secrets scan --baseline .secrets.baseline --exclude-files '\.secrets\.baseline' || log_warn "Baseline update may have issues"
else
    detect-secrets scan > .secrets.baseline
    log "✅ Baseline file created"
fi

# Step 6: Install pre-commit hooks
log "Installing pre-commit hooks..."
if [[ -f ".pre-commit-config.yaml" ]]; then
    pre-commit install
    pre-commit install --hook-type commit-msg
    log "✅ Pre-commit hooks installed"

    # Run pre-commit on all files (optional, can be slow)
    read -p "Run pre-commit on all files now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Running pre-commit on all files..."
        pre-commit run --all-files || log_warn "Some checks may have failed. Review output above."
    fi
else
    log_warn ".pre-commit-config.yaml not found. Skipping pre-commit installation."
fi

# Step 7: Verify installation
echo ""
log "Verifying installation..."
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# Check git-secrets
if command -v git-secrets &> /dev/null; then
    echo -e "${GREEN}✓${NC} git-secrets: $(git secrets --version)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}✗${NC} git-secrets: Not found"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check trufflehog
if command -v trufflehog &> /dev/null; then
    echo -e "${GREEN}✓${NC} trufflehog: $(trufflehog --version)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${YELLOW}⚠${NC} trufflehog: Not found (optional for local use)"
fi

# Check pre-commit
if command -v pre-commit &> /dev/null; then
    echo -e "${GREEN}✓${NC} pre-commit: $(pre-commit --version)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}✗${NC} pre-commit: Not found"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check detect-secrets
if command -v detect-secrets &> /dev/null; then
    echo -e "${GREEN}✓${NC} detect-secrets: $(detect-secrets --version)"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}✗${NC} detect-secrets: Not found"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check baseline file
if [[ -f ".secrets.baseline" ]]; then
    echo -e "${GREEN}✓${NC} .secrets.baseline: Exists"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}✗${NC} .secrets.baseline: Not found"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check pre-commit config
if [[ -f ".pre-commit-config.yaml" ]]; then
    echo -e "${GREEN}✓${NC} .pre-commit-config.yaml: Exists"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${YELLOW}⚠${NC} .pre-commit-config.yaml: Not found"
fi

echo ""
echo "======================================"
echo "Installation Summary"
echo "======================================"
echo ""
echo -e "Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks failed: ${RED}$CHECKS_FAILED${NC}"
echo ""

if [[ $CHECKS_FAILED -eq 0 ]]; then
    log "✅ Security scanning tools successfully installed!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review .secrets.baseline for any false positives"
    echo "  2. Test with: pre-commit run --all-files"
    echo "  3. Make a commit to verify hooks are working"
    echo "  4. See docs/SECURITY_SCANNING_GUIDE.md for details"
    echo ""
    exit 0
else
    log_error "❌ Some tools failed to install. Please review errors above."
    echo ""
    log_info "Manual installation instructions:"
    echo "  - git-secrets: https://github.com/awslabs/git-secrets#installing-git-secrets"
    echo "  - trufflehog: https://github.com/trufflesecurity/trufflehog#installation"
    echo "  - pre-commit: pip install pre-commit"
    echo "  - detect-secrets: pip install detect-secrets"
    echo ""
    exit 1
fi

