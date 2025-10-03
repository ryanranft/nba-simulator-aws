# Workflow #32: RDS PostgreSQL Connection

**Category:** AWS Operations
**Priority:** High
**When to Use:** When connecting to RDS for development, debugging, or data operations
**Related Workflows:** #25 (Database Migration), #24 (AWS Resource Setup)

---

## Overview

This workflow provides step-by-step procedures for connecting to RDS PostgreSQL from various tools and languages. Use this when you need to query data, verify schema, or debug database issues.

**Purpose:** Establish secure connections to RDS from different environments.

---

## When to Use This Workflow

✅ **USE when:**
- First-time RDS connection setup
- IP address changes (home/office/travel)
- Debugging connection issues
- Setting up new development machine
- Testing ETL data loads
- Running manual queries
- Verifying schema migrations

❌ **DON'T USE when:**
- RDS not yet created (see workflow #24 first)
- Just need to view data (use AWS Console RDS Query Editor)
- Automated ETL connections (use environment variables in code)

---

## Connection Information

**Instance Details:**
- **Instance Identifier:** `nba-sim-db`
- **Engine:** PostgreSQL 15.14
- **Instance Class:** db.t3.small (2 vCPUs, 2 GB RAM)
- **Region:** us-east-1
- **Endpoint:** `nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com`
- **Port:** 5432
- **Database Name:** `nba_simulator`
- **Master Username:** `postgres`

**Get your endpoint:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier nba-sim-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

---

## Connection Method 1: psql (Command Line)

**Best for:** Quick queries, schema inspection, manual data fixes

### Step 1: Install psql

**macOS:**
```bash
brew install postgresql@15
```

**Verify installation:**
```bash
psql --version
# Expected: psql (PostgreSQL) 15.x
```

### Step 2: Set Environment Variables

**Option A: Export for current session**
```bash
export PGPASSWORD='<your-password>'
export PGHOST='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'
export PGDATABASE='nba_simulator'
export PGUSER='postgres'
export PGPORT='5432'
```

**Option B: Use .pgpass file (more secure)**
```bash
# Create .pgpass file
cat > ~/.pgpass << EOF
nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com:5432:nba_simulator:postgres:<your-password>
EOF

# Set permissions (required)
chmod 600 ~/.pgpass

# Verify permissions
ls -l ~/.pgpass
# Expected: -rw------- (600)
```

### Step 3: Connect

**Using environment variables:**
```bash
psql
```

**Using command-line arguments:**
```bash
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d nba_simulator \
     -p 5432
```

**Expected output:**
```
psql (15.4)
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
Type "help" for help.

nba_simulator=>
```

### Step 4: Verify Connection

```sql
-- Check database version
SELECT version();

-- List all tables
\dt

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Sample data from a table
SELECT * FROM games LIMIT 5;

-- Exit
\q
```

---

## Connection Method 2: Python (psycopg2)

**Best for:** ETL scripts, data analysis, automation

### Step 1: Install psycopg2

```bash
conda activate nba-aws
pip install psycopg2-binary
```

### Step 2: Create Connection Script

**Basic connection:**
```python
import psycopg2
import os

# Option 1: Hardcoded (development only)
conn = psycopg2.connect(
    host='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com',
    port=5432,
    database='nba_simulator',
    user='postgres',
    password='<your-password>'
)

# Option 2: Environment variables (recommended)
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT', 5432),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

# Test connection
cursor = conn.cursor()
cursor.execute('SELECT version();')
version = cursor.fetchone()
print(f"Connected to: {version[0]}")

cursor.close()
conn.close()
```

### Step 3: Query Example

```python
import psycopg2
import os

def get_game_count():
    """Get total number of games in database."""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM games')
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count

# Usage
print(f"Total games: {get_game_count()}")
```

### Step 4: Batch Insert Example

```python
import psycopg2
from psycopg2.extras import execute_batch

def insert_games(games_data):
    """Insert multiple games using batch insert.

    Args:
        games_data: List of tuples (game_id, season, game_date, home_team, away_team)
    """
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    cursor = conn.cursor()

    insert_query = """
        INSERT INTO games (game_id, season, game_date, home_team, away_team)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (game_id) DO NOTHING
    """

    # Batch insert (faster than individual inserts)
    execute_batch(cursor, insert_query, games_data, page_size=1000)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Inserted {len(games_data)} games")

# Usage
games = [
    ('401584893', 2024, '2024-01-15', 'LAL', 'GSW'),
    ('401584894', 2024, '2024-01-15', 'BOS', 'MIA'),
]
insert_games(games)
```

---

## Connection Method 3: Python (SQLAlchemy ORM)

**Best for:** Complex queries, ORM-based applications, pandas integration

### Step 1: Install SQLAlchemy

```bash
pip install sqlalchemy pandas
```

### Step 2: Create Engine

```python
from sqlalchemy import create_engine
import os

# Build connection string
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"

# Create engine
engine = create_engine(DATABASE_URL)

# Test connection
with engine.connect() as conn:
    result = conn.execute("SELECT version();")
    version = result.fetchone()[0]
    print(f"Connected via SQLAlchemy: {version}")
```

### Step 3: Query with Pandas

```python
import pandas as pd
from sqlalchemy import create_engine
import os

# Create engine
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)

# Read SQL query into DataFrame
query = """
    SELECT season, COUNT(*) as game_count
    FROM games
    GROUP BY season
    ORDER BY season DESC
"""
df = pd.read_sql(query, engine)

print(df.head())

# Write DataFrame to database
new_data = pd.DataFrame({
    'team_id': [1, 2, 3],
    'team_name': ['Lakers', 'Warriors', 'Celtics']
})
new_data.to_sql('teams', engine, if_exists='append', index=False)
```

---

## Connection Method 4: Environment Variables Setup

**Best for:** Keeping credentials secure and out of code

### Step 1: Create Credentials File

```bash
# Create credentials file (NOT in git repo)
cat > /Users/ryanranft/nba-sim-credentials.env << 'EOF'
# RDS PostgreSQL Connection
export DB_HOST='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com'
export DB_PORT='5432'
export DB_NAME='nba_simulator'
export DB_USER='postgres'
export DB_PASSWORD='<your-password-here>'
export DB_SSLMODE='require'  # Optional: enforce SSL
EOF

# Set permissions
chmod 600 /Users/ryanranft/nba-sim-credentials.env
```

### Step 2: Load Credentials

```bash
# Load for current session
source /Users/ryanranft/nba-sim-credentials.env

# Verify loaded
echo $DB_HOST
# Expected: nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com
```

### Step 3: Auto-Load (Optional)

**Add to ~/.zshrc or ~/.bashrc:**
```bash
# Auto-load NBA simulator credentials
if [ -f /Users/ryanranft/nba-sim-credentials.env ]; then
    source /Users/ryanranft/nba-sim-credentials.env
fi
```

**Or use in Python with python-dotenv:**
```python
from dotenv import load_dotenv
import os

# Load from .env file
load_dotenv('/Users/ryanranft/nba-sim-credentials.env')

# Access variables
db_host = os.getenv('DB_HOST')
db_password = os.getenv('DB_PASSWORD')
```

---

## Security Setup

### Update Security Group for Your IP

**When to run:** IP address changes, new location, connection refused errors

### Step 1: Get Your Current IP

```bash
MY_IP=$(curl -s https://checkip.amazonaws.com)
echo "Your IP: $MY_IP"
```

### Step 2: Get Security Group ID

```bash
# Get security group from RDS instance
SG_ID=$(aws rds describe-db-instances \
  --db-instance-identifier nba-sim-db \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
  --output text)

echo "Security Group ID: $SG_ID"
```

### Step 3: Add Your IP to Security Group

```bash
# Add your IP (port 5432 for PostgreSQL)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32

# Verify rule added
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --query 'SecurityGroups[0].IpPermissions'
```

**Expected output:**
```json
[
  {
    "FromPort": 5432,
    "IpProtocol": "tcp",
    "IpRanges": [
      {
        "CidrIp": "174.62.194.89/32",
        "Description": "Home IP"
      }
    ],
    "ToPort": 5432
  }
]
```

### Step 4: Remove Old IP (Optional)

```bash
# Remove previous IP when it changes
OLD_IP="<old-ip-address>"

aws ec2 revoke-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5432 \
  --cidr $OLD_IP/32
```

---

## Database Schema Reference

**View schema:**
```sql
-- List all tables
\dt

-- Describe specific table
\d games

-- Detailed table info
\d+ player_game_stats

-- List all indexes
\di

-- Table sizes
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;
```

**Expected tables:**
- `teams` - NBA teams (~30 rows)
- `players` - NBA players (~5,000 rows)
- `games` - Game metadata (~120,000 rows)
- `player_game_stats` - Player box scores (~2.4M rows)
- `plays` - Play-by-play events (~15M rows)
- `team_game_stats` - Team box scores (~240,000 rows)

---

## Troubleshooting

### Error: "connection refused"

**Cause:** Security group doesn't allow your IP

**Solution:**
```bash
# Add your IP to security group (see Security Setup above)
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
  --group-id <security-group-id> \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32
```

### Error: "password authentication failed"

**Cause:** Wrong password or username

**Solution:**
```bash
# Reset RDS password via AWS Console or CLI
aws rds modify-db-instance \
  --db-instance-identifier nba-sim-db \
  --master-user-password '<new-password>' \
  --apply-immediately

# Wait for modification to complete
aws rds wait db-instance-available --db-instance-identifier nba-sim-db
```

### Error: "SSL connection required"

**Cause:** RDS requires SSL, client not using it

**Solution:**
```bash
# Download RDS CA certificate
wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

# Connect with SSL
psql "host=nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
      dbname=nba_simulator \
      user=postgres \
      sslmode=require \
      sslrootcert=global-bundle.pem"
```

**Or in Python:**
```python
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    sslmode='require',
    sslrootcert='global-bundle.pem'
)
```

### Error: "database does not exist"

**Cause:** Database name wrong or not created

**Solution:**
```bash
# Connect to default postgres database
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d postgres

# Create database
CREATE DATABASE nba_simulator;

# Verify
\l
```

### Error: "too many connections"

**Cause:** Connection pool exhausted (RDS limits based on instance class)

**Solution:**
```sql
-- Check current connections
SELECT COUNT(*) FROM pg_stat_activity;

-- Check max connections allowed
SHOW max_connections;
-- db.t3.small allows 112 connections

-- Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '10 minutes';
```

**Or increase instance size:**
```bash
# Upgrade to larger instance (more connections)
aws rds modify-db-instance \
  --db-instance-identifier nba-sim-db \
  --db-instance-class db.t3.medium \
  --apply-immediately
```

---

## Connection Checklist

**Before connecting:**
- [ ] RDS instance status = "available"
- [ ] Security group allows your IP (port 5432)
- [ ] Have correct endpoint, database name, username, password
- [ ] psql or Python psycopg2 installed

**After connecting:**
- [ ] Can run SELECT version()
- [ ] Can list tables (\dt or SELECT * FROM pg_tables)
- [ ] Can query sample data
- [ ] Connection closes properly (no lingering connections)

---

## Integration with Other Workflows

**After RDS creation (workflow #24):**
1. Get endpoint and credentials
2. Set up security group (this workflow, Security Setup)
3. Test connection (this workflow, Method 1)
4. Run schema migration (workflow #25)

**During ETL development:**
1. Load credentials (this workflow, Method 4)
2. Connect from Python (this workflow, Method 2)
3. Test data insert (this workflow, Method 2, Step 4)
4. Verify data loaded (this workflow, Method 1, Step 4)

**For daily queries:**
1. Load credentials (this workflow, Method 4, Step 2)
2. Connect via psql (this workflow, Method 1)
3. Run ad-hoc queries
4. Disconnect

---

## Best Practices

1. **Always use environment variables for passwords** (never hardcode)
2. **Use .pgpass or credentials file** (not command-line args with passwords)
3. **Close connections when done** (prevents connection pool exhaustion)
4. **Use connection pooling** for production apps (e.g., SQLAlchemy pool)
5. **Enable SSL/TLS** for production (sslmode=require)
6. **Rotate passwords every 90 days** (see workflow #23)
7. **Limit security group to specific IPs** (not 0.0.0.0/0)
8. **Monitor active connections** (pg_stat_activity)

---

**Last Updated:** 2025-10-02
**Source:** docs/RDS_CONNECTION.md
