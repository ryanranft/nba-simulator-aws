# Workflow #37: Credential Management

**Purpose:** Add new credentials to the credential file when creating AWS resources or generating new keys/passwords.

**When to run:** After creating any new AWS resource that generates credentials, keys, IPs, or connection strings (EC2, RDS, S3, SageMaker, etc.)

**Time:** 2-5 minutes

---

## Prerequisites

- New AWS resource has been created
- Credentials/connection details are available
- Credential file exists at `/Users/ryanranft/nba-sim-credentials.env`

---

## Steps

### 1. Identify New Credentials

**Check what credentials were generated:**
- EC2: Instance ID, Public IP, Key pair name/path, Security group ID
- RDS: Endpoint hostname, Database name, Username, Password
- S3: Bucket names
- SageMaker: Notebook instance name, Endpoint
- Security: API keys, Access keys, Secret keys

### 2. Read Current Credential File

```bash
cat /Users/ryanranft/nba-sim-credentials.env
```

**Purpose:** Understand current structure and avoid duplicates

### 3. Add New Credentials

**Use the Edit tool to add new section:**

```bash
# Template for new section:
# ============================================================================
# [Resource Type] Configuration (Phase X - [Purpose])
# ============================================================================
export [RESOURCE]_[ATTRIBUTE]="[value]"
export [RESOURCE]_[ATTRIBUTE]="[value]"
```

**Example for EC2:**
```bash
# ============================================================================
# EC2 Configuration (Phase 4 - Simulation Engine)
# ============================================================================
export EC2_INSTANCE_ID="i-0b8bbe4cdff7ae2d2"
export EC2_PUBLIC_IP="54.165.99.80"
export EC2_INSTANCE_TYPE="t3.small"
export EC2_KEY_NAME="nba-simulator-ec2-key"
export EC2_KEY_PATH="/Users/ryanranft/.ssh/nba-simulator-ec2-key.pem"
export EC2_SECURITY_GROUP_ID="sg-0b9ca09f4a041e1c8"
export EC2_SSH_USER="ec2-user"
```

### 4. Update Claude Instructions Section

**Add new variables to the "Instructions for Claude Code" section:**

```bash
# [Resource Type] (Phase X):
#   - $RESOURCE_ATTRIBUTE, $RESOURCE_ATTRIBUTE, etc.
```

### 5. Document SSH Keys/Certificates Separately

**If SSH keys or certificates were created:**

```bash
# Store private keys in ~/.ssh/ with permissions 400
chmod 400 ~/.ssh/[key-name].pem

# Document location in credential file
export [RESOURCE]_KEY_PATH="/Users/ryanranft/.ssh/[key-name].pem"
```

### 6. Verification

**Verify credentials are accessible:**

```bash
# Reload credential file
source /Users/ryanranft/nba-sim-credentials.env

# Test new variables
echo $EC2_INSTANCE_ID
echo $EC2_PUBLIC_IP
echo $DB_PASSWORD
```

**Expected:** All variables should print their values

### 7. Security Check

**Ensure credential file is NOT in Git:**

```bash
# Verify .gitignore excludes credential file
grep "nba-sim-credentials.env" .gitignore

# Check Git status (file should NOT appear)
git status | grep "nba-sim-credentials.env"
```

**Expected:** File should be ignored by Git

---

## Common Credential Types

### EC2 Credentials
```bash
export EC2_INSTANCE_ID="i-xxxxx"
export EC2_PUBLIC_IP="x.x.x.x"
export EC2_KEY_PATH="/Users/ryanranft/.ssh/key.pem"
export EC2_SECURITY_GROUP_ID="sg-xxxxx"
```

### RDS Credentials
```bash
export DB_HOST="db.xxxxx.rds.amazonaws.com"
export DB_PASSWORD="SecurePassword"
export DB_USER="postgres"
export DB_NAME="database_name"
export DB_PORT="5432"
```

### S3 Buckets
```bash
export S3_BUCKET_NAME="bucket-name"
export S3_BUCKET_ARN="arn:aws:s3:::bucket-name"
```

### SageMaker Credentials
```bash
export SAGEMAKER_NOTEBOOK_NAME="notebook-name"
export SAGEMAKER_ROLE_ARN="arn:aws:iam::xxxxx:role/SageMakerRole"
export SAGEMAKER_ENDPOINT="endpoint-name"
```

### API Keys
```bash
export API_KEY_NAME="key-value"
export API_SECRET="secret-value"
```

---

## Best Practices

### Security
1. ✅ **NEVER commit credential file to Git**
2. ✅ **Set restrictive permissions:** `chmod 600 /Users/ryanranft/nba-sim-credentials.env`
3. ✅ **Set SSH key permissions:** `chmod 400 ~/.ssh/*.pem`
4. ✅ **Use environment variables in code** (never hardcode)
5. ✅ **Document credential location in README** (but not values)

### Organization
1. ✅ **Group credentials by resource type**
2. ✅ **Add comments for context** (Phase number, purpose)
3. ✅ **Use consistent naming:** `RESOURCE_ATTRIBUTE` format
4. ✅ **Update Claude instructions section** when adding new variables

### Maintenance
1. ✅ **Update IP addresses** when EC2 instances restart
2. ✅ **Rotate passwords** periodically (see Workflow #23)
3. ✅ **Remove obsolete credentials** when resources are deleted
4. ✅ **Backup credential file** to secure location (Desktop/++)

---

## Troubleshooting

### Variables Not Loading

**Problem:** Environment variables are undefined

**Solution:**
```bash
# Reload credential file
source /Users/ryanranft/nba-sim-credentials.env

# Verify file syntax
bash -n /Users/ryanranft/nba-sim-credentials.env
```

### SSH Key Permission Denied

**Problem:** SSH connection fails with "permissions are too open"

**Solution:**
```bash
# Fix permissions
chmod 400 ~/.ssh/nba-simulator-ec2-key.pem

# Update credential file with correct path
export EC2_KEY_PATH="/Users/ryanranft/.ssh/nba-simulator-ec2-key.pem"
```

### Credential File Appears in Git Status

**Problem:** File shows up in `git status`

**Solution:**
```bash
# Add to .gitignore (if not already there)
echo "*credentials.env" >> .gitignore
echo "*.pem" >> .gitignore

# Remove from Git tracking (if accidentally added)
git rm --cached /Users/ryanranft/nba-sim-credentials.env
```

---

## Related Workflows

- **Workflow #23:** Credential Rotation (periodic password updates)
- **Workflow #2:** Command Logging (log credential creation commands)
- **Workflow #8:** Git Commit (security scan before commit)
- **Workflow #19:** Backup & Recovery (backup credential file)

---

## Success Criteria

- [ ] New credentials added to credential file
- [ ] Claude instructions section updated
- [ ] Environment variables load successfully
- [ ] SSH keys have correct permissions (400)
- [ ] Credential file excluded from Git
- [ ] Variables accessible via `$VARIABLE_NAME` syntax

---

*Last updated: 2025-10-03*
*Created: Phase 4 (EC2 deployment)*