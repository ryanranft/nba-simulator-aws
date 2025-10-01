#!/bin/bash
# scripts/shell/verify_setup.sh
# Verify NBA Simulator AWS environment setup

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NBA Simulator AWS - Environment Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to check command exists
check_command() {
    if command -v "$1" &> /dev/null; then
        echo "✅ $1 installed"
        return 0
    else
        echo "❌ $1 NOT installed"
        return 1
    fi
}

# Function to check version
check_version() {
    local cmd=$1
    local version=$($2 2>&1)
    echo "   Version: $version"
}

# 1. System tools
echo "1. System Tools:"
check_command git && check_version git "git --version"
check_command conda && check_version conda "conda --version"
check_command aws && check_version aws "aws --version"
echo ""

# 2. Python environment
echo "2. Python Environment:"
if [[ "$CONDA_DEFAULT_ENV" == "nba-aws" ]]; then
    echo "✅ Conda environment 'nba-aws' activated"
    python_version=$(python --version 2>&1)
    echo "   Python: $python_version"
    if [[ "$python_version" == *"3.11"* ]]; then
        echo "   ✅ Python 3.11 confirmed"
    else
        echo "   ⚠️  Warning: Expected Python 3.11, got $python_version"
    fi
else
    echo "❌ Conda environment 'nba-aws' NOT activated"
    echo "   Run: conda activate nba-aws"
fi
echo ""

# 3. Python packages
echo "3. Python Packages:"
packages=("boto3" "pandas" "numpy" "psycopg2")
for pkg in "${packages[@]}"; do
    if python -c "import $pkg" 2>/dev/null; then
        version=$(python -c "import $pkg; print($pkg.__version__)" 2>/dev/null)
        echo "✅ $pkg ($version)"
    else
        echo "❌ $pkg NOT installed"
    fi
done
echo ""

# 4. AWS configuration
echo "4. AWS Configuration:"
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS credentials configured"
    account=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    user=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null)
    echo "   Account: $account"
    echo "   User: $user"
    echo "   Region: $(aws configure get region)"
else
    echo "❌ AWS credentials NOT configured"
    echo "   Run: aws configure"
fi
echo ""

# 5. S3 access
echo "5. S3 Bucket Access:"
if aws s3 ls s3://nba-sim-raw-data-lake/ &>/dev/null; then
    echo "✅ Can access s3://nba-sim-raw-data-lake/"
    object_count=$(aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize 2>/dev/null | grep "Total Objects" | awk '{print $3}')
    if [[ -n "$object_count" ]]; then
        echo "   Total objects: $object_count"
    fi
else
    echo "⚠️  Cannot access s3://nba-sim-raw-data-lake/"
    echo "   (This is okay if bucket isn't created yet)"
fi
echo ""

# 6. Git configuration
echo "6. Git Configuration:"
if git remote -v 2>/dev/null | grep -q "git@github.com"; then
    echo "✅ Git remote configured (SSH)"
    git remote -v | head -2
elif git remote -v 2>/dev/null | grep -q "github.com"; then
    echo "⚠️  Git remote configured but using HTTPS"
    echo "   Consider switching to SSH (see CLAUDE.md)"
else
    echo "❌ Git remote not configured"
fi
echo ""

# 7. GitHub SSH
echo "7. GitHub SSH Access:"
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ GitHub SSH authentication working"
else
    echo "❌ GitHub SSH authentication NOT working"
    echo "   Run: ssh -T git@github.com"
    echo "   See: docs/adr/005-git-ssh-authentication.md"
fi
echo ""

# 8. Project structure
echo "8. Project Structure:"
required_dirs=("scripts" "sql" "docs" "config")
for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "✅ $dir/ directory exists"
    else
        echo "⚠️  $dir/ directory missing (may not be created yet)"
    fi
done
echo ""

# 9. Disk space
echo "9. Disk Space:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    free_space=$(df -h . | awk 'NR==2 {print $4}')
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    free_space=$(df -h . | awk 'NR==2 {print $4}')
else
    free_space="Unknown"
fi
echo "   Free space: $free_space"
echo "   Required: ~130 GB for full local data copy"
echo ""

# 10. Documentation files
echo "10. Documentation Files:"
doc_files=("CLAUDE.md" "PROGRESS.md" "COMMAND_LOG.md" "docs/STYLE_GUIDE.md")
for file in "${doc_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file exists"
    else
        echo "⚠️  $file missing"
    fi
done
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verification complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ = Pass | ❌ = Fail | ⚠️  = Warning"
echo ""
echo "If all critical checks pass ✅, your environment is ready!"
echo "If any checks fail ❌, see docs/TROUBLESHOOTING.md"
echo ""
echo "Next steps:"
echo "  1. Review PROGRESS.md for current project status"
echo "  2. Review CLAUDE.md for LLM usage guidelines"
echo "  3. Start with Phase 2.1 (AWS Glue Crawler setup)"
