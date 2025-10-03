## 🔍 Systematic Troubleshooting Protocol

**When any operation fails or behaves unexpectedly:**

### Step 1: Run Health Check
```bash
source scripts/shell/session_manager.sh start
```
**Review output for:**
- Environment issues (conda, Python, packages)
- AWS credential issues
- Git state problems
- Disk space issues

### Step 2: Check Documentation
```bash
# Search TROUBLESHOOTING.md for keywords
grep -i "<error_keyword>" docs/TROUBLESHOOTING.md

# Search COMMAND_LOG.md for similar errors
grep -i "<error_keyword>" COMMAND_LOG.md
```

### Step 3: Enable Debug Logging
```python
# Add to Python scripts
import logging
logging.basicConfig(level=logging.DEBUG)

# For AWS operations
import boto3
boto3.set_stream_logger('boto3.resources', logging.DEBUG)
```

```bash
# For bash scripts
set -x  # Enable verbose output
```

### Step 4: Isolate the Problem
1. **Reproduce with minimal example**
2. **Test components individually**
3. **Check intermediate outputs**
4. **Verify assumptions** (file exists, network connectivity, permissions)

### Step 5: Document and Resolve
1. **Document in COMMAND_LOG.md:**
   - Error message (exact text)
   - Steps to reproduce
   - What you tried
   - What worked
2. **If took >10 min to solve:** Offer to add to TROUBLESHOOTING.md
3. **Use `log_solution` helper:**
   ```bash
   log_solution "Brief description of error and fix"
   ```

### Common Troubleshooting Commands

**Environment issues:**
```bash
conda info --envs
conda list boto3
which python
pip show psycopg2-binary
```

**AWS issues:**
```bash
aws sts get-caller-identity  # Verify credentials
aws s3 ls  # Test S3 access
aws rds describe-db-instances  # Check RDS status
```

**Git issues:**
```bash
git status
git log --oneline -5
git remote -v
git config --list | grep user
```

**Disk space issues:**
```bash
df -h  # Check disk usage
du -sh ~/sports-simulator-archives/nba/*  # Archive sizes
find . -type f -size +100M  # Large files
```

**See `docs/TROUBLESHOOTING.md` for complete error catalog**

---

