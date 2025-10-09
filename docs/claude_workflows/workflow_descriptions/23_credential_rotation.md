## 🔐 Credential Rotation Workflow

**Follow 90-day rotation schedule for security**

### Rotation Schedule

| Credential Type | Frequency | Next Rotation | Priority |
|-----------------|-----------|---------------|----------|
| AWS Access Keys | 90 days | Check IAM | 🔴 High |
| AWS Secret Keys | 90 days | Check IAM | 🔴 High |
| SSH Keys | 365 days | Check GitHub | 🟡 Medium |
| RDS Passwords | 90 days | After RDS created | 🔴 High |
| API Tokens | 90 days | Service-specific | 🟡 Medium |

### AWS Credential Rotation Procedure

1. **Check current key age:**
   ```bash
   aws iam get-credential-report
   # Look for "access_key_1_last_rotated"
   ```

2. **Generate new key:**
   - AWS Console → IAM → Users → Security Credentials
   - Click "Create access key"
   - Save new key securely (DO NOT commit)

3. **Update local credentials:**
   ```bash
   # Edit ~/.aws/credentials
   [default]
   aws_access_key_id = <NEW_KEY>
   aws_secret_access_key = <NEW_SECRET>
   ```

4. **Test new credentials:**
   ```bash
   aws sts get-caller-identity
   aws s3 ls  # Verify S3 access
   ```

5. **Deactivate old key:**
   - AWS Console → IAM → Users → Security Credentials
   - Click "Make inactive" on old key

6. **Wait 24 hours** (verify no issues)

7. **Delete old key:**
   - AWS Console → IAM → Users → Security Credentials
   - Click "Delete" on inactive key

8. **Document rotation:**
   ```bash
   echo "AWS credentials rotated on $(date)" >> COMMAND_LOG.md
   # Or create calendar reminder for next rotation (90 days)
   ```

### Emergency Rotation (If Compromised)

**If credentials exposed (committed to GitHub, logged, etc.):**

1. **IMMEDIATELY deactivate compromised credential**
2. **Generate new credential**
3. **Update all systems using old credential**
4. **Delete compromised credential**
5. **Review CloudTrail logs** for unauthorized access:
   ```bash
   aws cloudtrail lookup-events --max-results 50
   ```
6. **Document incident** in TROUBLESHOOTING.md
7. **Run security audit:**
   ```bash
   bash scripts/shell/security_scan.sh
   ```

**Set calendar reminders:** 85 days after each rotation

---

