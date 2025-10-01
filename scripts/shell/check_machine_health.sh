#!/bin/zsh
# Master health check script for NBA Simulator AWS project
# Purpose: Verify all system components at session start
# Usage: ./scripts/shell/check_machine_health.sh
# Version: 1.0.0
# Last Updated: 2025-10-01

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  NBA Simulator AWS - Machine Health Check                     ║"
echo "║  Date: $(date +%Y-%m-%d' '%H:%M:%S)                                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Exit codes
EXIT_CODE=0

# Helper functions
check_pass() {
    echo "✅ $1"
}

check_fail() {
    echo "❌ $1"
    EXIT_CODE=1
}

check_warn() {
    echo "⚠️  $1"
}

check_info() {
    echo "ℹ️  $1"
}

separator() {
    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo ""
}

# 1. SYSTEM INFORMATION
echo "1️⃣  SYSTEM INFORMATION"
echo "─────────────────────────────────────"
sw_vers | sed 's/^/    /'
echo ""
echo "    Device: MacBook Pro 16-inch, 2023"
echo "    Processor: Apple M2 Max"
echo "    Memory: 96 GB"
echo "    Storage: $(df -h / | awk 'NR==2 {print $4}') available of $(df -h / | awk 'NR==2 {print $2}')"
separator

# 2. DISK SPACE
echo "2️⃣  DISK SPACE"
echo "─────────────────────────────────────"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h / | awk 'NR==2 {print $4}')
echo "    Available: $DISK_AVAIL"
echo "    Usage: ${DISK_USAGE}%"

if [ $DISK_USAGE -gt 90 ]; then
    check_fail "Disk usage critical (>90%)"
elif [ $DISK_USAGE -gt 80 ]; then
    check_warn "Disk usage high (>80%)"
else
    check_pass "Disk space OK"
fi
separator

# 3. HOMEBREW
echo "3️⃣  HOMEBREW"
echo "─────────────────────────────────────"
if command -v brew &> /dev/null; then
    BREW_VERSION=$(brew --version | head -1)
    BREW_LOCATION=$(which brew)
    echo "    Version: $BREW_VERSION"
    echo "    Location: $BREW_LOCATION"

    if [[ "$BREW_LOCATION" == "/opt/homebrew/bin/brew" ]]; then
        check_pass "Homebrew installed correctly (Apple Silicon)"
    else
        check_warn "Homebrew location unexpected: $BREW_LOCATION"
    fi

    # Check for outdated packages
    OUTDATED_COUNT=$(brew outdated | wc -l | tr -d ' ')
    if [ $OUTDATED_COUNT -gt 0 ]; then
        check_info "$OUTDATED_COUNT outdated packages (run 'brew upgrade')"
    fi
else
    check_fail "Homebrew not found"
fi
separator

# 4. MINICONDA
echo "4️⃣  MINICONDA"
echo "─────────────────────────────────────"
if command -v conda &> /dev/null; then
    CONDA_VERSION=$(conda --version)
    CONDA_BASE=$(conda info --base)
    echo "    Version: $CONDA_VERSION"
    echo "    Base: $CONDA_BASE"
    check_pass "Conda installed"

    # Check if nba-aws environment exists
    if conda env list | grep -q "nba-aws"; then
        check_pass "nba-aws environment exists"
    else
        check_fail "nba-aws environment not found"
    fi
else
    check_fail "Conda not found"
fi
separator

# 5. PYTHON ENVIRONMENT
echo "5️⃣  PYTHON ENVIRONMENT (nba-aws)"
echo "─────────────────────────────────────"

# Activate conda environment
eval "$(conda shell.zsh hook 2> /dev/null)"
conda activate nba-aws 2>/dev/null

if [[ "$CONDA_DEFAULT_ENV" == "nba-aws" ]]; then
    PYTHON_VERSION=$(python --version 2>&1)
    PYTHON_LOCATION=$(which python)
    echo "    Version: $PYTHON_VERSION"
    echo "    Location: $PYTHON_LOCATION"

    if [[ "$PYTHON_VERSION" == *"3.11"* ]]; then
        check_pass "Python 3.11 (required for AWS Glue 4.0)"
    else
        check_fail "Python version not 3.11: $PYTHON_VERSION"
    fi

    # Check package count
    PACKAGE_COUNT=$(pip list | wc -l | tr -d ' ')
    echo "    Packages installed: $PACKAGE_COUNT"

    if [ $PACKAGE_COUNT -lt 50 ]; then
        check_warn "Low package count, may need to reinstall requirements"
    else
        check_pass "Packages installed"
    fi
else
    check_fail "Could not activate nba-aws environment"
fi
separator

# 6. CORE PYTHON PACKAGES
echo "6️⃣  CORE PYTHON PACKAGES"
echo "─────────────────────────────────────"
REQUIRED_PACKAGES=("boto3" "pandas" "numpy" "psycopg2-binary" "sqlalchemy" "pytest" "jupyter" "python-dotenv" "pyyaml" "tqdm")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if pip show "$package" &>/dev/null; then
        VERSION=$(pip show "$package" | grep "Version:" | awk '{print $2}')
        echo "    ✅ $package ($VERSION)"
    else
        echo "    ❌ $package (NOT INSTALLED)"
        EXIT_CODE=1
    fi
done
separator

# 7. AWS CLI
echo "7️⃣  AWS CLI"
echo "─────────────────────────────────────"
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1)
    AWS_LOCATION=$(which aws)
    echo "    Version: $AWS_VERSION"
    echo "    Location: $AWS_LOCATION"

    if [[ "$AWS_LOCATION" == "/opt/homebrew/bin/aws" ]]; then
        check_pass "AWS CLI installed system-wide (Homebrew)"
    else
        check_warn "AWS CLI location unexpected: $AWS_LOCATION"
    fi

    # Check AWS credentials
    if [ -f ~/.aws/credentials ]; then
        CREDS_PERMS=$(stat -f "%Lp" ~/.aws/credentials)
        if [[ "$CREDS_PERMS" == "600" ]]; then
            check_pass "AWS credentials file exists with correct permissions (600)"
        else
            check_warn "AWS credentials permissions: $CREDS_PERMS (should be 600)"
        fi
    else
        check_fail "AWS credentials file not found"
    fi

    # Test AWS connectivity
    if aws s3 ls s3://nba-sim-raw-data-lake/ --max-items 1 &>/dev/null; then
        check_pass "AWS S3 connectivity verified"
    else
        check_warn "Could not connect to S3 bucket (check credentials/network)"
    fi
else
    check_fail "AWS CLI not found"
fi
separator

# 8. GIT
echo "8️⃣  GIT"
echo "─────────────────────────────────────"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    GIT_LOCATION=$(which git)
    echo "    Version: $GIT_VERSION"
    echo "    Location: $GIT_LOCATION"
    check_pass "Git installed"

    # Check SSH authentication
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        check_pass "GitHub SSH authentication working"
    else
        check_warn "GitHub SSH authentication may not be configured"
    fi

    # Check git config
    GIT_USER=$(git config --global user.name)
    GIT_EMAIL=$(git config --global user.email)
    if [[ -n "$GIT_USER" && -n "$GIT_EMAIL" ]]; then
        echo "    User: $GIT_USER <$GIT_EMAIL>"
        check_pass "Git configured"
    else
        check_warn "Git user/email not configured globally"
    fi
else
    check_fail "Git not found"
fi
separator

# 9. PROJECT FILES
echo "9️⃣  PROJECT FILES"
echo "─────────────────────────────────────"
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
if [ -d "$PROJECT_ROOT" ]; then
    echo "    Project root: $PROJECT_ROOT"
    check_pass "Project directory exists"

    # Check critical files
    CRITICAL_FILES=("requirements.txt" "Makefile" "CLAUDE.md" "PROGRESS.md" "README.md" "COMMAND_LOG.md")
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            echo "    ✅ $file"
        else
            echo "    ❌ $file (missing)"
            EXIT_CODE=1
        fi
    done

    # Check documentation files
    DOC_FILES=("docs/STYLE_GUIDE.md" "docs/TROUBLESHOOTING.md" "docs/SETUP.md")
    for file in "${DOC_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            echo "    ✅ $file"
        else
            echo "    ⚠️  $file (missing)"
        fi
    done

    # Check project directories
    REQUIRED_DIRS=("scripts" "sql" "docs" "config")
    echo ""
    echo "    Project directories:"
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            echo "    ✅ $dir/"
        else
            echo "    ⚠️  $dir/ (missing, may not be created yet)"
        fi
    done

    # Check .env file
    echo ""
    if [ -f "$PROJECT_ROOT/.env" ]; then
        check_pass ".env file exists"
    else
        check_warn ".env file not found (create from .env.example if needed)"
    fi
else
    check_fail "Project directory not found: $PROJECT_ROOT"
fi
separator

# 10. DATA DIRECTORY
echo "🔟 DATA DIRECTORY"
echo "─────────────────────────────────────"
DATA_ROOT="/Users/ryanranft/0espn/data/nba"
if [ -d "$DATA_ROOT" ]; then
    echo "    Data root: $DATA_ROOT"
    check_pass "Data directory exists"

    # Count JSON files (this may take time for 146K files)
    echo "    Counting JSON files (this may take a moment)..."
    JSON_COUNT=$(find "$DATA_ROOT" -name "*.json" -type f | wc -l | tr -d ' ')
    echo "    JSON files: $JSON_COUNT"

    if [ $JSON_COUNT -gt 140000 ]; then
        check_pass "All data files present (~146K expected)"
    elif [ $JSON_COUNT -gt 100000 ]; then
        check_warn "Some data files may be missing (found $JSON_COUNT, expected ~146K)"
    else
        check_fail "Many data files missing (found $JSON_COUNT, expected ~146K)"
    fi
else
    check_warn "Data directory not found: $DATA_ROOT (okay if data already in S3)"
fi
separator

# 11. NETWORK & AWS CONNECTIVITY
echo "1️⃣1️⃣  NETWORK & AWS CONNECTIVITY"
echo "─────────────────────────────────────"

# Check internet connectivity
if ping -c 1 8.8.8.8 &> /dev/null; then
    check_pass "Internet connectivity OK"
else
    check_fail "No internet connectivity"
fi

# Check AWS S3 endpoint reachability
if ping -c 1 s3.us-east-1.amazonaws.com &> /dev/null; then
    check_pass "AWS S3 endpoint reachable"
else
    check_warn "AWS S3 endpoint not reachable via ping (may be blocked)"
fi

# Check DNS resolution
if nslookup s3.us-east-1.amazonaws.com &> /dev/null; then
    check_pass "DNS resolution working"
else
    check_warn "DNS resolution issues detected"
fi
separator

# 12. SECURITY SETTINGS
echo "1️⃣2️⃣  SECURITY SETTINGS"
echo "─────────────────────────────────────"

# Check SIP
SIP_STATUS=$(csrutil status 2>&1)
if echo "$SIP_STATUS" | grep -q "enabled"; then
    check_pass "System Integrity Protection enabled"
else
    check_warn "System Integrity Protection status: $SIP_STATUS"
fi

# Check FileVault
FILEVAULT_STATUS=$(fdesetup status 2>&1)
if echo "$FILEVAULT_STATUS" | grep -q "FileVault is On"; then
    check_pass "FileVault disk encryption enabled"
else
    check_warn "FileVault status: $FILEVAULT_STATUS"
fi

# Check SSH key permissions
if [ -f ~/.ssh/id_rsa ]; then
    SSH_PERMS=$(stat -f "%Lp" ~/.ssh/id_rsa)
    if [[ "$SSH_PERMS" == "600" ]]; then
        check_pass "SSH private key permissions correct (600)"
    else
        check_fail "SSH private key permissions: $SSH_PERMS (should be 600)"
    fi
elif [ -f ~/.ssh/id_ed25519 ]; then
    SSH_PERMS=$(stat -f "%Lp" ~/.ssh/id_ed25519)
    if [[ "$SSH_PERMS" == "600" ]]; then
        check_pass "SSH private key permissions correct (600)"
    else
        check_fail "SSH private key permissions: $SSH_PERMS (should be 600)"
    fi
else
    check_info "SSH private key not found (may use different key name)"
fi
separator

# 13. SYSTEM RESOURCES
echo "1️⃣3️⃣  SYSTEM RESOURCES"
echo "─────────────────────────────────────"

# Memory
FREE_MEM=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
FREE_MEM_MB=$((FREE_MEM * 4096 / 1024 / 1024))
echo "    Free Memory: ~${FREE_MEM_MB} MB"

if [ $FREE_MEM_MB -lt 1000 ]; then
    check_warn "Low free memory (<1 GB)"
else
    check_pass "Sufficient free memory"
fi

# CPU usage
CPU_IDLE=$(top -l 1 | grep "CPU usage" | awk '{print $7}' | sed 's/%//')
if [ -z "$CPU_IDLE" ]; then
    CPU_IDLE="0"
fi
echo "    CPU idle: ${CPU_IDLE}%"

separator

# 14. OPTIONAL TOOLS
echo "1️⃣4️⃣  OPTIONAL TOOLS"
echo "─────────────────────────────────────"

OPTIONAL_TOOLS=("jq:JSON processor" "psql:PostgreSQL client" "tree:Directory viewer" "tmux:Terminal multiplexer")

for tool_desc in "${OPTIONAL_TOOLS[@]}"; do
    tool="${tool_desc%%:*}"
    desc="${tool_desc##*:}"
    if command -v "$tool" &> /dev/null; then
        echo "    ✅ $tool - $desc"
    else
        echo "    ⚠️  $tool - $desc (not installed, optional)"
    fi
done

separator

# SUMMARY
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  HEALTH CHECK SUMMARY                                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - System ready for development"
    echo ""
    echo "Next steps:"
    echo "  1. Run: cd /Users/ryanranft/nba-simulator-aws"
    echo "  2. Run: conda activate nba-aws"
    echo "  3. Run: make verify-all (for additional checks)"
else
    echo "⚠️  SOME CHECKS FAILED - Review errors above"
    echo ""
    echo "Common fixes:"
    echo "  - Missing packages: pip install -r requirements.txt"
    echo "  - AWS credentials: aws configure"
    echo "  - Git config: git config --global user.name/email"
fi

echo ""
echo "Health check completed at $(date +%Y-%m-%d' '%H:%M:%S)"
echo ""

exit $EXIT_CODE