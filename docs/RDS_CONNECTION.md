# RDS PostgreSQL Connection Details

**Purpose:** Secure reference for RDS connection information
**Created:** 2025-10-01
**Phase:** 3.1 - RDS PostgreSQL Setup

---

## Connection Information

**Instance Identifier:** `nba-sim-db`
**Engine:** PostgreSQL 15.14
**Instance Class:** db.t3.small (2 vCPUs, 2 GB RAM)
**Region:** us-east-1
**Status:** Available ✅

**Endpoint:** `nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com`
**Port:** 5432
**Database Name:** `nba_simulator`
**Master Username:** `postgres`
**Master Password:** *See secure credential storage*

---

## Connection Methods

### 1. psql (Command Line)

```bash
# Set password environment variable
export PGPASSWORD='<your-password-here>'

# Connect
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d nba_simulator \
     -p 5432

# Or use .pgpass file (more secure)
# Create ~/.pgpass with: hostname:port:database:username:password
# chmod 600 ~/.pgpass
```

### 2. Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com',
    port=5432,
    database='nba_simulator',
    user='postgres',
    password='<your-password-here>'
)

cursor = conn.cursor()
cursor.execute('SELECT version();')
print(cursor.fetchone())
conn.close()
```

### 3. SQLAlchemy (ORM)

```python
from sqlalchemy import create_engine
import os

# Connection string (use environment variable for password)
DATABASE_URL = f"postgresql://postgres:{os.getenv('DB_PASSWORD')}@nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com:5432/nba_simulator"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute("SELECT COUNT(*) FROM teams")
    print(result.fetchone())
```

### 4. Environment Variables (Recommended)

```bash
# Add to ~/.env or project .env file
export DB_HOST='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'
export DB_PORT='5432'
export DB_NAME='nba_simulator'
export DB_USER='postgres'
export DB_PASSWORD='<your-password-here>'

# Then in Python:
import os
import psycopg2

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
```

---

## Database Schema

**Tables:** 6
**Indexes:** 33 (23 performance + 10 constraints)

| Table | Purpose | Row Count (est.) |
|-------|---------|------------------|
| `teams` | NBA teams | ~30 |
| `players` | NBA players | ~5,000 |
| `games` | Game metadata | ~120,000 |
| `player_game_stats` | Player box scores | ~2.4M |
| `plays` | Play-by-play events | ~15M |
| `team_game_stats` | Team box scores | ~240,000 |

**View Schema:**
```sql
\dt                  -- List all tables
\di                  -- List all indexes
\d teams             -- Describe teams table
\d+ player_game_stats -- Detailed table info
```

---

## Security

**Security Group:** `sg-079ed470e0caaca44`
**Allowed IPs:**
- Home IP: 174.62.194.89/32 (PostgreSQL port 5432)

**Public Accessibility:** Yes (for development)
**SSL/TLS:** Available (recommended for production)

**Update Security Group:**
```bash
# Get current IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Add your IP to security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-079ed470e0caaca44 \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32
```

---

## Backup & Recovery

**Automated Backups:** Enabled
**Retention Period:** 7 days
**Backup Window:** Automatic (AWS-managed)
**Maintenance Window:** Automatic (AWS-managed)

**Create Manual Snapshot:**
```bash
aws rds create-db-snapshot \
  --db-instance-identifier nba-sim-db \
  --db-snapshot-identifier nba-sim-manual-snapshot-$(date +%Y%m%d)
```

**Restore from Snapshot:**
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier nba-sim-db-restored \
  --db-snapshot-identifier nba-sim-manual-snapshot-20251001
```

---

## Cost Management

**Current Cost:** ~$29/month
**Breakdown:**
- Compute (db.t3.small): ~$25/month
- Storage (20 GB gp3): ~$2.30/month
- Backup storage (20 GB): ~$1.80/month

**Stop Instance (when not in use):**
```bash
# Stop (can stop for up to 7 days)
aws rds stop-db-instance --db-instance-identifier nba-sim-db

# Start
aws rds start-db-instance --db-instance-identifier nba-sim-db

# Check status
aws rds describe-db-instances \
  --db-instance-identifier nba-sim-db \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Note:** Stopping saves compute costs (~$25/month) but not storage (~$4/month)

---

## Monitoring

**CloudWatch Metrics:**
- CPU Utilization
- Database Connections
- Free Storage Space
- Read/Write IOPS

**View Metrics:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=nba-sim-db \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

---

## Common Queries

### Check Database Size
```sql
SELECT
    pg_size_pretty(pg_database_size('nba_simulator')) AS database_size;
```

### Check Table Sizes
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check Active Connections
```sql
SELECT
    datname,
    COUNT(*) AS connections
FROM pg_stat_activity
GROUP BY datname;
```

### Check Table Row Counts
```sql
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

---

## Troubleshooting

### Connection Timeout
**Problem:** Cannot connect to RDS
**Solutions:**
1. Check security group allows your IP
2. Verify RDS instance is in "available" status
3. Check VPC settings (default VPC should work)
4. Ping endpoint to test network: `ping nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com`

### Password Authentication Failed
**Problem:** `FATAL: password authentication failed`
**Solutions:**
1. Verify password in ~/.env or credential manager
2. Check no special characters cause shell escaping issues
3. Rotate password if compromised:
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier nba-sim-db \
     --master-user-password '<new-password>' \
     --apply-immediately
   ```

### Out of Connections
**Problem:** `too many connections`
**Solutions:**
1. Check max_connections: `SHOW max_connections;`
2. Close idle connections
3. Upgrade to larger instance class (more RAM = more connections)

---

## Useful Commands

**List all databases:**
```sql
\l
```

**Switch database:**
```sql
\c nba_simulator
```

**Show current user:**
```sql
SELECT current_user;
```

**Show all users:**
```sql
\du
```

**Exit psql:**
```sql
\q
```

---

## References

- **Database Schema:** `sql/create_tables.sql`
- **Indexes:** `sql/create_indexes.sql`
- **PROGRESS.md:** Phase 3.1 - RDS PostgreSQL Setup
- **AWS Console:** https://console.aws.amazon.com/rds/home?region=us-east-1

---

**⚠️ SECURITY WARNING:**

- **NEVER commit credentials to Git**
- **NEVER share passwords in chat logs or screenshots**
- Store password in:
  - Environment variables (`~/.env`)
  - AWS Secrets Manager (production)
  - Password manager (personal)
- Rotate password every 90 days
- Use SSL/TLS for production connections