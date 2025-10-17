# Security Scanning Guide

## Overview

NBA MCP Synthesis implements a comprehensive, multi-layered security approach to prevent secrets from being committed to the repository. This guide covers setup, usage, and troubleshooting of our security scanning tools.

## Security Layers

### Layer 1: Pre-commit Hooks (Local Protection)

Pre-commit hooks run automatically before each commit to catch secrets before they reach your local repository.

**Tools**:
- `detect-secrets`: Scans for common secret patterns
- `git-secrets`: AWS and custom pattern detection
- `bandit`: Python security linting
- `black`: Code formatting (ensures consistency)
- Custom file validation: Size checks, naming conventions

### Layer 2: CI/CD Pipeline (GitHub Actions)

Automated scanning runs on every push and pull request to catch issues that slip through local checks.

**Tools**:
- `bandit`: Python security vulnerabilities
- `Trivy`: Container and dependency vulnerabilities
- `trufflehog`: Comprehensive secret scanning with git history
- `git-secrets`: Pattern-based secret detection

### Layer 3: Secrets Management

Hierarchical secrets management system prevents secrets from being in the codebase entirely.

**Components**:
- `unified_secrets_manager.py`: Centralized secret loading
- Hierarchical directory structure: Secrets stored outside project
- Permission auditing: Automated permission verification
- Health monitoring: Secret availability checks

### Layer 4: S3 Public Access Validation (NEW)

Automated validation ensures S3 buckets containing sensitive data (books, datasets) are not publicly accessible.

**What it checks**:
- **Bucket-level**: PublicAccessBlock configuration, bucket ACLs, bucket policies
- **Object-level**: Individual object ACLs for all books/data files
- **Environment discovery**: Automatically finds buckets from env vars

**Tools**:
- `validate_s3_public_access.py`: Comprehensive S3 security scanner
- GitHub Actions: Automated checks on every push/PR
- Boto3 AWS SDK: Programmatic access to S3 APIs

## Quick Start

### 1. Install Security Tools

```bash
# Run the installation script
./scripts/setup_security_scanning.sh

# This installs:
# - git-secrets
# - trufflehog
# - pre-commit
# - detect-secrets
# - boto3 (for S3 validation)
```

### 2. Verify Installation

```bash
# Test that all tools work
python scripts/test_security_scanning.py
```

### 3. Run Pre-commit on All Files

```bash
# Check existing files
pre-commit run --all-files
```

### 4. Make Your First Protected Commit

```bash
# Stage your changes
git add .

# Commit (hooks will run automatically)
git commit -m "feat: your changes"

# If secrets are detected, the commit will be blocked
```

## Configuration Files

### `.pre-commit-config.yaml`

Defines which hooks run and their configuration:

```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### `.git-secrets-patterns`

Custom patterns for your naming convention:

```
# API Keys
(GOOGLE|ANTHROPIC|OPENAI|DEEPSEEK)_API_KEY_[A-Z_]+_(WORKFLOW|DEVELOPMENT|TEST)

# AWS Credentials
AKIA[0-9A-Z]{16}

# Generic patterns
sk-[a-zA-Z0-9]{20,}
```

### `.secrets.baseline`

Known false positives that are safe to commit:

```json
{
  "version": "1.4.0",
  "results": {
    "docs/example.md": [...]
  }
}
```

## Usage

### Daily Development Workflow

1. **Make changes** to your code
2. **Stage changes**: `git add .`
3. **Commit**: `git commit -m "your message"`
4. **Hooks run automatically**:
   - detect-secrets scans
   - bandit checks security
   - black formats code
   - File validation runs
5. **If passed**: Commit succeeds ✅
6. **If failed**: Fix issues and retry ❌

### Running Scans Manually

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run detect-secrets --all-files

# Scan for hardcoded secrets
python scripts/validate_secrets_security.py

# Scan for hardcoded secrets AND S3 public access
python scripts/validate_secrets_security.py --check-s3

# Check S3 public access only
python scripts/validate_s3_public_access.py --fail-on-public

# Test security tools
python scripts/test_security_scanning.py

# Audit file permissions
./scripts/audit_secret_permissions.sh
```

### Updating Hooks

```bash
# Update to latest versions
pre-commit autoupdate

# Re-install hooks
pre-commit install --install-hooks
```

## What to Do When Scans Fail

### Pre-commit Blocked Your Commit

#### 1. Check the Error Message

```bash
detect-secrets: Failed
- hook id: detect-secrets
- exit code: 1

Potential secrets found in:
  - mcp_server/config.py:42
```

#### 2. Investigate the Finding

```bash
# View the file and line
cat mcp_server/config.py | sed -n '42p'
```

#### 3. Choose Your Action

**If it's a real secret** (most common):
```bash
# Remove the secret from code
# Use unified_secrets_manager instead
from mcp_server.unified_secrets_manager import get_secret
api_key = get_secret('GOOGLE_API_KEY')

# Re-stage and commit
git add mcp_server/config.py
git commit -m "fix: use unified_secrets_manager"
```

**If it's a false positive**:
```bash
# Add to baseline
detect-secrets scan --baseline .secrets.baseline

# Re-commit
git commit -m "your message"
```

### CI/CD Pipeline Failed

#### 1. Check GitHub Actions Logs

1. Go to your PR or commit
2. Click "Details" next to failed check
3. Review the logs

#### 2. Common Failures

**trufflehog found a secret**:
```bash
# The secret is in git history
# You must:
# 1. Revoke the exposed secret immediately
# 2. Remove from history:
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/file' \
  --prune-empty --tag-name-filter cat -- --all
```

**git-secrets found a pattern**:
```bash
# Fix the file locally
# Push the fix
git add .
git commit -m "fix: remove secret"
git push
```

### Validation Script Reports Issues

```bash
# Run the validation
python scripts/validate_secrets_security.py

# Review the report
cat security_audit_report.md
```

**Issue Types**:

1. **Hardcoded secrets**: Remove and use unified_secrets_manager
2. **Direct os.getenv()**: Import unified_secrets_manager
3. **load_dotenv()**: Replace with load_secrets_hierarchical()
4. **Orphaned .env files**: Move to hierarchical structure

## Emergency: Secret Leaked to GitHub

If a real secret is committed and pushed to GitHub:

### Immediate Actions (< 5 minutes)

1. **Revoke the secret immediately**
   ```bash
   # For AWS
   aws iam delete-access-key --access-key-id AKIAXXXXXXXX

   # For other services
   # Revoke through the service's console/API
   ```

2. **Generate new credentials**
   ```bash
   # Generate replacement
   # Update in hierarchical secrets directory
   ```

3. **Notify team**
   ```bash
   # Post to Slack channel
   # Alert security team if applicable
   ```

### Cleanup (< 30 minutes)

4. **Remove from git history**
   ```bash
   # Use BFG Repo-Cleaner (fastest)
   brew install bfg
   bfg --replace-text passwords.txt my-repo.git

   # Or git filter-branch (slower)
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch path/to/secret-file' \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (WARNING: coordinate with team)
   git push origin --force --all
   ```

5. **Verify removal**
   ```bash
   # Scan history
   trufflehog git file://. --only-verified

   # Check GitHub
   # Review all branches and tags
   ```

### Prevention (< 1 hour)

6. **Run security audit**
   ```bash
   python scripts/validate_secrets_security.py
   ./scripts/audit_secret_permissions.sh
   ```

7. **Update documentation**
   ```bash
   # Document the incident
   # Update team procedures
   # Add new patterns to .git-secrets-patterns
   ```

## Best Practices

### DO ✅

1. **Run pre-commit on all files** before your first commit
   ```bash
   pre-commit run --all-files
   ```

2. **Use `.env.example`** for documentation
   ```bash
   cp .env.example .env.local
   # Edit .env.local with real values
   # Never commit .env.local
   ```

3. **Import unified_secrets_manager** in all code
   ```python
   from mcp_server.unified_secrets_manager import get_secret
   api_key = get_secret('GOOGLE_API_KEY')
   ```

4. **Audit permissions** regularly
   ```bash
   ./scripts/audit_secret_permissions.sh
   ```

5. **Review .secrets.baseline** periodically
   ```bash
   # Remove outdated entries
   # Verify false positives are still valid
   ```

### DON'T ❌

1. **Never commit with `--no-verify`**
   ```bash
   git commit --no-verify  # ❌ Bypasses security hooks
   ```

2. **Never hardcode secrets**
   ```python
   api_key = "sk-1234..."  # ❌ Will be detected
   ```

3. **Never use `load_dotenv()`**
   ```python
   from dotenv import load_dotenv  # ❌ Use unified_secrets_manager
   load_dotenv()  # ❌
   ```

4. **Never store secrets in project directory**
   ```bash
   # ❌ Don't do this
   echo "API_KEY=secret" > .env

   # ✅ Do this instead
   # Use hierarchical structure outside project
   ```

5. **Never force push without coordination**
   ```bash
   git push --force  # ❌ Can cause issues for team
   ```

## Troubleshooting

### Pre-commit Hooks Not Running

```bash
# Check if hooks are installed
ls -la .git/hooks/pre-commit

# Reinstall hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### detect-secrets Taking Too Long

```bash
# Update baseline to exclude large files
detect-secrets scan --baseline .secrets.baseline \
  --exclude-files 'large_file.txt'
```

### False Positives

```bash
# Add to baseline
detect-secrets scan --baseline .secrets.baseline

# Or add inline pragma
secret = "not-really-a-secret"  # pragma: allowlist secret
```

### Git-secrets Not Finding Patterns

```bash
# Verify patterns are loaded
git secrets --list

# Re-add patterns
git secrets --install --force
git secrets --register-aws
cat .git-secrets-patterns | while read line; do
  [[ ! "$line" =~ ^# ]] && git secrets --add "$line"
done
```

## Integration with Existing Workflow

### With Claude Desktop

Pre-commit hooks run automatically when you commit through:
- VS Code
- Command line
- Any Git client

### With CI/CD

GitHub Actions automatically run on:
- Every push to main/develop
- Every pull request
- Scheduled scans (nightly)

### With Unified Secrets Manager

All secrets should be:
1. Stored in hierarchical structure
2. Loaded via unified_secrets_manager
3. Never hardcoded in code
4. Managed with proper permissions

## S3 Security Best Practices

### Why Books Must Be Private

Books and datasets in S3 buckets contain:
- Copyrighted material (textbooks, research papers)
- Proprietary analysis and algorithms
- Sensitive training data
- Expensive purchased content

Making these public could:
- Violate copyright and licensing agreements
- Expose proprietary IP
- Incur legal liability
- Cost tens of thousands in damages

### How S3 Validation Works

**Bucket-level checks**:
1. **PublicAccessBlock**: Ensures all 4 settings are enabled
   - BlockPublicAcls
   - IgnorePublicAcls
   - BlockPublicPolicy
   - RestrictPublicBuckets

2. **Bucket ACL**: No grants to AllUsers or AuthenticatedUsers

3. **Bucket Policy**: No wildcard (*) principals with Allow

**Object-level checks**:
1. Lists all objects under `books/` prefix
2. Checks ACL for each object
3. Ensures no public READ grants
4. Samples up to 1000 objects per bucket

### Fixing Public S3 Access

**Enable Block Public Access (recommended)**:
```bash
# Apply to specific bucket
aws s3api put-public-access-block \
  --bucket nba-mcp-books-20251011 \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Apply to all buckets in account
aws s3control put-public-access-block \
  --account-id YOUR_ACCOUNT_ID \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

**Remove public ACL grants**:
```bash
# Remove from bucket
aws s3api put-bucket-acl \
  --bucket nba-mcp-books-20251011 \
  --acl private

# Remove from specific object
aws s3api put-object-acl \
  --bucket nba-mcp-books-20251011 \
  --key books/Basketball_Analytics.pdf \
  --acl private
```

**Secure bucket policy example**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::nba-mcp-books-20251011",
        "arn:aws:s3:::nba-mcp-books-20251011/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### S3 Validation in CI/CD

The GitHub Actions workflows automatically check S3 on every push:

```yaml
- name: Validate S3 Public Access
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    python scripts/validate_s3_public_access.py --fail-on-public
```

**Important**: Set AWS credentials in GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (optional, defaults to us-east-1)

## Advanced Topics

### Custom Patterns

Add project-specific patterns to `.git-secrets-patterns`:

```
# Custom API key format
MY_SERVICE_API_[A-Z0-9]{32}

# Custom token format
token_[a-f0-9]{64}
```

### CI/CD Customization

Modify `.github/workflows/secrets-scan.yml`:

```yaml
- name: Custom validation
  run: |
    python scripts/my_custom_check.py
```

### Performance Optimization

```bash
# Skip slow hooks for quick commits
SKIP=detect-secrets git commit -m "quick fix"

# Note: Use sparingly, only for urgent fixes
```

## Additional Resources

- [detect-secrets Documentation](https://github.com/Yelp/detect-secrets)
- [git-secrets Documentation](https://github.com/awslabs/git-secrets)
- [trufflehog Documentation](https://github.com/trufflesecurity/trufflehog)
- [pre-commit Documentation](https://pre-commit.com/)
- [Unified Secrets Manager Guide](./SECRETS_MANAGEMENT_GUIDE.md)

## Support

For issues or questions:

1. **Check this guide first**
2. **Run diagnostics**: `python scripts/test_security_scanning.py`
3. **Review audit report**: `python scripts/validate_secrets_security.py`
4. **Check permissions**: `./scripts/audit_secret_permissions.sh`
5. **Contact team**: Post in #security Slack channel

---

**Remember**: Security is everyone's responsibility. When in doubt, ask!

