# Environment Setup Guide

**Project:** NBA Game Simulator & ML Platform
**Purpose:** Complete setup and verification checklist for new development environments

---

## Quick Start (Existing Environment)

If environment is already set up, verify it's working:

```bash
# Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# Activate conda environment
conda activate nba-aws

# Run verification script
./scripts/shell/verify_setup.sh
```

Expected output: All checks ✅ pass

---

## Complete Setup (New Machine/User)

### Prerequisites

**Required:**
- macOS, Linux, or Windows with WSL2
- 130+ GB free disk space (for local data copy)
- Internet connection
- GitHub account with SSH access

**Accounts:**
- AWS account with AdministratorAccess
- GitHub account (for repository access)

---

## Setup Steps

### 1. Install System Dependencies

#### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install git wget
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y git wget build-essential
```

#### Windows (WSL2)
```bash
# Inside WSL2 terminal
sudo apt-get update
sudo apt-get install -y git wget build-essential
```

**Verify:**
```bash
git --version          # Should show git version 2.x
wget --version         # Should show wget version
```

---

### 2. Install Miniconda

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -O miniconda.sh

# For Linux x86_64:
# wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh

# Install
bash miniconda.sh -b -p $HOME/miniconda3

# Initialize conda
~/miniconda3/bin/conda init bash
# or for zsh:
~/miniconda3/bin/conda init zsh

# Restart shell
exec $SHELL

# Verify
conda --version       # Should show conda 23.x or later
```

---

### 3. Install AWS CLI

#### macOS
```bash
# Download installer
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

# Install
sudo installer -pkg AWSCLIV2.pkg -target /
```

#### Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Verify:**
```bash
aws --version         # Should show aws-cli/2.x
which aws             # Should show /usr/local/bin/aws (NOT in conda)
```

**⚠️ CRITICAL:** AWS CLI must be system-wide, NOT in conda environment

---

### 4. Configure AWS Credentials

```bash
# Run AWS configure
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json
```

**Test AWS access:**
```bash
# Should list S3 buckets (or show empty if none exist)
aws s3 ls

# Check identity
aws sts get-caller-identity
# Should show your AWS account ID and user
```

**Files created:**
```
~/.aws/
├── config          # Region and output settings
└── credentials     # Access keys (NEVER commit to Git!)
```

---

### 5. Set Up SSH Keys for GitHub

#### Check for existing keys
```bash
ls -la ~/.ssh
# Look for: id_rsa, id_ed25519, id_ecdsa
```

#### Generate new key (if needed)
```bash
# Generate Ed25519 key (recommended)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Press Enter to accept default location
# Enter passphrase (optional but recommended)
```

#### Add key to ssh-agent
```bash
# Start ssh-agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# For macOS, persist across reboots:
cat >> ~/.ssh/config << 'EOF'
Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
EOF
```

#### Add public key to GitHub
```bash
# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub
# Copy the output

# Then:
# 1. Go to https://github.com/settings/keys
# 2. Click "New SSH key"
# 3. Paste the public key
# 4. Click "Add SSH key"
```

**Test GitHub SSH connection:**
```bash
ssh -T git@github.com
# Should output: "Hi [username]! You've successfully authenticated..."
# Exit code 1 is expected - this is normal for GitHub
```

---

### 6. Clone Repository

```bash
# Navigate to projects directory
cd ~  # Or your preferred location

# Clone via SSH
git clone git@github.com:ryanranft/nba-simulator-aws.git

# Navigate into project
cd nba-simulator-aws

# Verify
git remote -v
# Should show: git@github.com:ryanranft/nba-simulator-aws.git
```

---

### 7. Create Conda Environment

```bash
# Create environment with Python 3.11
conda create -n nba-aws python=3.11.13 -y

# Activate environment
conda activate nba-aws

# Verify Python version
python --version
# Should show: Python 3.11.13

# Verify environment location
which python
# Should show: ~/miniconda3/envs/nba-aws/bin/python
```

---

### 8. Install Python Dependencies

```bash
# Make sure environment is activated
conda activate nba-aws

# Install core dependencies
pip install boto3 pandas numpy psycopg2-binary sqlalchemy

# Install development dependencies (optional)
pip install pytest pytest-cov black isort flake8

# Verify installations
pip list | grep boto3      # Should show boto3 version
pip list | grep pandas     # Should show pandas version
pip list | grep numpy      # Should show numpy version
```

**Expected versions:**
- boto3: 1.34.x or later
- pandas: 2.0.x or later
- numpy: 1.24.x or later
- psycopg2-binary: 2.9.x or later

---

### 9. Configure Environment Variables (Optional)

**Create `.env` file:**
```bash
cat > .env << 'EOF'
# AWS
AWS_REGION=us-east-1
S3_BUCKET=nba-sim-raw-data-lake

# Database (update after RDS is created)
DB_HOST=nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=nba_simulator
DB_USER=postgres
DB_PASSWORD=your_password_here

# Glue (update after Glue is created)
GLUE_DATABASE=nba_raw_data
GLUE_ETL_JOB=nba-etl-job
EOF
```

**⚠️ IMPORTANT:** `.env` is already in `.gitignore` - never commit it!

---

### 10. Verify S3 Access

```bash
# List S3 buckets
aws s3 ls

# List NBA data bucket contents
aws s3 ls s3://nba-sim-raw-data-lake/

# Should show:
#   PRE box_scores/
#   PRE pbp/
#   PRE schedule/
#   PRE team_stats/

# Count objects (should be 146,115)
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | grep "Total Objects"
```

---

### 11. Set Up Command Logging (Optional)

```bash
# Make logging script executable
chmod +x scripts/shell/log_command.sh

# Add to shell profile for convenience
echo 'alias load_logging="source ~/path/to/nba-simulator-aws/scripts/shell/log_command.sh"' >> ~/.zshrc
# or for bash:
# echo 'alias load_logging="source ~/path/to/nba-simulator-aws/scripts/shell/log_command.sh"' >> ~/.bashrc

# Reload shell
source ~/.zshrc  # or source ~/.bashrc

# Load logging functions
load_logging

# Test
log_cmd git status
```

---

## Verification Checklist

Run this comprehensive verification:

```bash
#!/bin/bash
# scripts/shell/verify_setup.sh

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
    local version=$($2)
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
    python_version=$(python --version)
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
        version=$(python -c "import $pkg; print($pkg.__version__)")
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
    account=$(aws sts get-caller-identity --query Account --output text)
    user=$(aws sts get-caller-identity --query Arn --output text)
    echo "   Account: $account"
    echo "   User: $user"
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
    echo "   Total objects: $object_count"
else
    echo "❌ Cannot access s3://nba-sim-raw-data-lake/"
fi
echo ""

# 6. Git configuration
echo "6. Git Configuration:"
if git remote -v | grep -q "git@github.com"; then
    echo "✅ Git remote configured (SSH)"
    git remote -v | head -2
else
    echo "⚠️  Git remote not using SSH"
fi
echo ""

# 7. GitHub SSH
echo "7. GitHub SSH Access:"
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ GitHub SSH authentication working"
else
    echo "❌ GitHub SSH authentication NOT working"
    echo "   Run: ssh -T git@github.com"
fi
echo ""

# 8. Project structure
echo "8. Project Structure:"
required_dirs=("scripts" "sql" "docs" "tests" "config")
for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "✅ $dir/ directory exists"
    else
        echo "❌ $dir/ directory missing"
    fi
done
echo ""

# 9. Disk space
echo "9. Disk Space:"
free_space=$(df -h . | awk 'NR==2 {print $4}')
echo "   Free space: $free_space"
echo "   Required: ~130 GB for full local data copy"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verification complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "If all checks pass ✅, your environment is ready!"
echo "If any checks fail ❌, see docs/TROUBLESHOOTING.md"
