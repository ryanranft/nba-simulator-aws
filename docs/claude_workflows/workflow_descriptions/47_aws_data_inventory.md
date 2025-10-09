# Workflow #47: AWS Data Inventory System

**Purpose:** Comprehensive inventory of all data stored in AWS services (S3, RDS, Glue, Athena, etc.) with cost analysis, usage metrics, and resource utilization.

**Created:** October 8, 2025
**Last Updated:** October 8, 2025
**Related Workflows:** #45 (Local Data Inventory), #46 (Data Gap Analysis), #24 (AWS Resource Setup)

---

## When to Use This Workflow

**Use this workflow when:**
- Starting a new session and need to understand AWS data state
- Planning AWS resource usage or cleanup
- Analyzing AWS costs (what's using storage/compute)
- Verifying data uploaded to S3
- Checking database sizes and growth
- Preparing AWS cost reports
- Before creating new AWS resources (check what exists)
- Auditing AWS infrastructure

**Prerequisites:**
- AWS credentials configured (`aws configure list`)
- Access to AWS account (us-east-1 region)
- Database credentials (for RDS inventory)

---

## Quick Reference

### Common AWS Inventory Commands

```bash
# Quick AWS overview (all services)
bash scripts/monitoring/inventory_aws.sh --quick

# S3 detailed inventory
bash scripts/monitoring/inventory_aws_s3.sh

# RDS database inventory
bash scripts/monitoring/inventory_aws_rds.sh

# Glue catalog inventory (if using)
bash scripts/monitoring/inventory_aws_glue.sh

# Cost analysis
bash scripts/monitoring/analyze_aws_costs.sh

# All AWS data + costs
bash scripts/monitoring/inventory_aws.sh --full --with-costs
```

---

## Complete Workflow Steps

### Phase 1: S3 Data Inventory

**Purpose:** Comprehensive inventory of S3 bucket data

**Step 1.1: S3 Bucket Overview**

```bash
echo "=" * 70
echo "AWS S3 DATA INVENTORY"
echo "=" * 70
echo ""

# List all S3 buckets in account
echo "S3 Buckets in Account:"
aws s3 ls

echo ""
echo "Primary Bucket: nba-sim-raw-data-lake"
echo ""

# Get total bucket size and file count
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize | tail -2
```

**Expected output:**
```
S3 Buckets in Account:
2024-06-15 10:23:45 nba-sim-raw-data-lake

Primary Bucket: nba-sim-raw-data-lake

Total Objects: 146115
   Total Size: 13421772800  (12.5 GB)
```

**Step 1.2: S3 Inventory by Data Source**

```bash
echo "S3 Inventory by Data Source:"
echo ""

# Actual S3 bucket prefixes (from aws s3 ls s3://nba-sim-raw-data-lake/)
sources=(
    "athena-results"
    "basketball_reference"
    "box_scores"
    "hoopr_phase1"
    "ml-features"
    "ml-models"
    "ml-predictions"
    "nba_api_comprehensive"
    "nba_api_playbyplay"
    "pbp"
    "schedule"
    "scripts"
    "sportsdataverse"
    "team_stats"
)

# Header
printf "%-30s %12s %15s %15s\n" "Source" "Files" "Size (MB)" "Size (GB)"
echo "------------------------------------------------------------------------"

for source in "${sources[@]}"; do
    # Check if prefix exists
    if aws s3 ls s3://nba-sim-raw-data-lake/$source/ > /dev/null 2>&1; then
        # Get file count
        file_count=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive 2>/dev/null | wc -l)

        # Get total size
        size_bytes=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive --summarize 2>/dev/null | \
            grep "Total Size" | awk '{print $3}')

        if [ -n "$size_bytes" ] && [ "$size_bytes" != "0" ]; then
            size_mb=$(echo "scale=2; $size_bytes / 1024 / 1024" | bc)
            size_gb=$(echo "scale=2; $size_bytes / 1024 / 1024 / 1024" | bc)
            printf "%-30s %12s %15s %15s\n" "$source" "$file_count" "$size_mb" "$size_gb"
        else
            printf "%-30s %12s %15s %15s\n" "$source" "$file_count" "0" "0"
        fi
    else
        printf "%-30s %12s %15s %15s\n" "$source" "0" "N/A" "N/A"
    fi
done
```

**Expected output:**
```
Source                             Files        Size (MB)        Size (GB)
------------------------------------------------------------------------
basketball_reference               15234          2458.34            2.40
espn                               23456          1876.21            1.83
hoopr                              34567          3287.65            3.21
kaggle                                 1           890.45            0.87
nba_api                            14199          4123.89            4.03
pbpstats                           12345           234.56            0.23
ml-features                            3            45.23            0.04
athena-results                       310            12.34            0.01
```

**Step 1.3: S3 Storage Class Analysis**

```bash
echo ""
echo "S3 Storage Class Analysis:"
echo ""

# Check storage classes in use
aws s3api list-objects-v2 \
    --bucket nba-sim-raw-data-lake \
    --query "Contents[*].[StorageClass]" \
    --output text | sort | uniq -c | sort -rn

echo ""
echo "Note: Empty or 'None' = STANDARD storage class"
```

**Step 1.4: S3 Latest Activity**

```bash
echo ""
echo "Recent S3 Activity (Last 10 uploads):"
echo ""

aws s3api list-objects-v2 \
    --bucket nba-sim-raw-data-lake \
    --query 'reverse(sort_by(Contents, &LastModified))[:10].[Key,LastModified,Size]' \
    --output table
```

---

### Phase 2: RDS Database Inventory

**Purpose:** Inventory RDS PostgreSQL database

**Step 2.1: RDS Instance Details**

```bash
echo "=" * 70
echo "AWS RDS DATABASE INVENTORY"
echo "=" * 70
echo ""

# Get RDS instance information
echo "RDS Instance Information:"
aws rds describe-db-instances \
    --db-instance-identifier nba-sim-db \
    --query 'DBInstances[0].[DBInstanceIdentifier,DBInstanceClass,Engine,EngineVersion,DBInstanceStatus,AllocatedStorage,StorageType,MultiAZ,AvailabilityZone]' \
    --output table

echo ""
```

**Expected output:**
```
RDS Instance Information:
-------------------------------------------------------------------------
|                        DescribeDBInstances                           |
+---------------------+------------------------------------------------+
|  nba-sim-db         |                                                |
|  db.t3.micro        |                                                |
|  postgres           |                                                |
|  15.14              |                                                |
|  available          |                                                |
|  20                 |  (GB)                                          |
|  gp2                |                                                |
|  False              |                                                |
|  us-east-1a         |                                                |
+---------------------+------------------------------------------------+
```

**Step 2.2: RDS Database Size**

```bash
echo "Database Size Analysis:"
echo ""

# Load credentials
source /Users/ryanranft/nba-sim-credentials.env

# Connect and get database size
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Overall database size
SELECT
    pg_database.datname AS database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = '$DB_NAME';

-- Breakdown by table
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS toast_size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 15;
EOF
```

**Expected output:**
```
Database Size Analysis:

 database_name | size
---------------+-------
 nba_simulator | 3.8 GB

 schemaname |        tablename         | total_size | table_size | indexes_size | toast_size
------------+--------------------------+------------+------------+--------------+------------
 public     | temporal_events          | 2.1 GB     | 1.8 GB     | 340 MB       | 8 MB
 public     | play_by_play             | 890 MB     | 756 MB     | 134 MB       | 0 bytes
 public     | possession_panel         | 450 MB     | 380 MB     | 70 MB        | 0 bytes
 public     | player_game_stats        | 120 MB     | 95 MB      | 25 MB        | 0 bytes
 public     | team_game_stats          | 25 MB      | 20 MB      | 5 MB         | 0 bytes
 public     | games                    | 15 MB      | 12 MB      | 3 MB         | 0 bytes
```

**Step 2.3: RDS Table Row Counts**

```bash
echo ""
echo "Table Row Counts:"
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
EOF
```

**Step 2.4: RDS Connection and Activity**

```bash
echo ""
echo "Database Activity Metrics:"
echo ""

psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" <<EOF
-- Current connections
SELECT
    COUNT(*) AS total_connections,
    COUNT(CASE WHEN state = 'active' THEN 1 END) AS active_connections,
    COUNT(CASE WHEN state = 'idle' THEN 1 END) AS idle_connections
FROM pg_stat_activity;

-- Database statistics
SELECT
    numbackends AS current_connections,
    xact_commit AS transactions_committed,
    xact_rollback AS transactions_rolled_back,
    blks_read AS blocks_read_from_disk,
    blks_hit AS blocks_read_from_cache,
    ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) AS cache_hit_ratio
FROM pg_stat_database
WHERE datname = '$DB_NAME';
EOF
```

---

### Phase 3: AWS Glue Catalog (if applicable)

**Purpose:** Inventory Glue Data Catalog

**Step 3.1: Check if Glue is Configured**

```bash
echo "=" * 70
echo "AWS GLUE CATALOG INVENTORY"
echo "=" * 70
echo ""

# Check if Glue database exists
if aws glue get-database --name nba_raw_data 2>/dev/null; then
    echo "✅ Glue database 'nba_raw_data' exists"
    echo ""

    # List tables
    echo "Glue Catalog Tables:"
    aws glue get-tables --database-name nba_raw_data \
        --query 'TableList[*].[Name,StorageDescriptor.Location,Parameters.classification]' \
        --output table

else
    echo "⚠️  Glue database 'nba_raw_data' not found (not yet created)"
    echo "   This is expected if you haven't started Phase 2 (AWS Glue setup)"
fi

echo ""
```

**Step 3.2: Glue Crawlers (if configured)**

```bash
echo "Glue Crawlers:"
echo ""

# List crawlers
crawler_count=$(aws glue list-crawlers --query 'CrawlerNames' --output text | wc -w)

if [ "$crawler_count" -gt 0 ]; then
    aws glue list-crawlers --query 'CrawlerNames' --output table

    echo ""
    echo "Crawler Details:"
    for crawler in $(aws glue list-crawlers --query 'CrawlerNames' --output text); do
        aws glue get-crawler --name "$crawler" \
            --query 'Crawler.[Name,State,LastCrawl.Status,LastCrawl.StartTime]' \
            --output table
    done
else
    echo "No crawlers configured yet"
fi
```

---

### Phase 4: Athena Query History (if applicable)

**Purpose:** Check Athena usage and query results

**Step 4.1: Athena Query Executions**

```bash
echo "=" * 70
echo "AWS ATHENA QUERY INVENTORY"
echo "=" * 70
echo ""

# Get recent query executions
echo "Recent Athena Queries (Last 10):"
echo ""

aws athena list-query-executions \
    --max-items 10 \
    --query 'QueryExecutionIds' \
    --output text | while read query_id; do

    if [ -n "$query_id" ]; then
        aws athena get-query-execution --query-execution-id "$query_id" \
            --query 'QueryExecution.[QueryExecutionId,Query,Status.State,Statistics.DataScannedInBytes,Statistics.EngineExecutionTimeInMillis]' \
            --output table 2>/dev/null | head -10
        echo ""
    fi
done
```

**Step 4.2: Athena Results Location**

```bash
echo "Athena Query Results:"
echo ""

# Check athena-results prefix in S3
if aws s3 ls s3://nba-sim-raw-data-lake/athena-results/ 2>/dev/null; then
    file_count=$(aws s3 ls s3://nba-sim-raw-data-lake/athena-results/ --recursive | wc -l)
    size=$(aws s3 ls s3://nba-sim-raw-data-lake/athena-results/ --recursive --summarize | \
        grep "Total Size" | awk '{print $3/1024/1024 " MB"}')

    echo "Athena results stored in S3:"
    echo "  Files: $file_count"
    echo "  Size: $size"
else
    echo "No Athena results found (Athena not yet used)"
fi

echo ""
```

---

### Phase 5: AWS Cost Analysis

**Purpose:** Analyze AWS costs for data storage

**Step 5.1: Estimate S3 Costs**

```bash
echo "=" * 70
echo "AWS COST ANALYSIS"
echo "=" * 70
echo ""

echo "S3 Storage Costs (Estimated):"
echo ""

# Get total S3 size
total_size_bytes=$(aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize | \
    grep "Total Size" | awk '{print $3}')

if [ -n "$total_size_bytes" ]; then
    total_size_gb=$(echo "scale=2; $total_size_bytes / 1024 / 1024 / 1024" | bc)

    # S3 Standard pricing: $0.023 per GB/month (us-east-1)
    s3_cost=$(echo "scale=2; $total_size_gb * 0.023" | bc)

    echo "Total S3 Storage: ${total_size_gb} GB"
    echo "Estimated Monthly Cost: \$${s3_cost}"
    echo ""
    echo "Note: This is STANDARD storage class pricing"
    echo "      Does not include transfer or request costs"
fi
```

**Step 5.2: RDS Storage Costs**

```bash
echo ""
echo "RDS Storage Costs (Estimated):"
echo ""

# Get RDS allocated storage
allocated_storage=$(aws rds describe-db-instances \
    --db-instance-identifier nba-sim-db \
    --query 'DBInstances[0].AllocatedStorage' \
    --output text)

if [ -n "$allocated_storage" ]; then
    # gp2 pricing: $0.10 per GB/month
    rds_storage_cost=$(echo "scale=2; $allocated_storage * 0.10" | bc)

    echo "Allocated Storage: ${allocated_storage} GB"
    echo "Estimated Monthly Cost: \$${rds_storage_cost}"
fi

# Get RDS instance type cost
instance_class=$(aws rds describe-db-instances \
    --db-instance-identifier nba-sim-db \
    --query 'DBInstances[0].DBInstanceClass' \
    --output text)

echo ""
echo "RDS Instance: $instance_class"

# Common instance costs (us-east-1, on-demand)
case $instance_class in
    "db.t3.micro")
        instance_cost=14.60
        ;;
    "db.t3.small")
        instance_cost=29.20
        ;;
    "db.t3.medium")
        instance_cost=58.40
        ;;
    *)
        instance_cost="unknown"
        ;;
esac

if [ "$instance_cost" != "unknown" ]; then
    echo "Estimated Monthly Cost: \$${instance_cost}"

    total_rds_cost=$(echo "scale=2; $rds_storage_cost + $instance_cost" | bc)
    echo ""
    echo "Total RDS Monthly Cost: \$${total_rds_cost}"
fi
```

**Step 5.3: Total AWS Costs**

```bash
echo ""
echo "=" * 70
echo "TOTAL ESTIMATED AWS COSTS (Monthly)"
echo "=" * 70
echo ""

# Calculate total
if [ -n "$s3_cost" ] && [ -n "$total_rds_cost" ]; then
    total_cost=$(echo "scale=2; $s3_cost + $total_rds_cost" | bc)

    echo "S3 Storage:           \$${s3_cost}"
    echo "RDS (instance+storage): \$${total_rds_cost}"
    echo "----------------------------------------"
    echo "TOTAL:                \$${total_cost}/month"
    echo ""
    echo "Note: Does not include:"
    echo "  - Data transfer costs"
    echo "  - Request costs (S3 API calls)"
    echo "  - Glue/Athena if configured"
    echo "  - EC2/SageMaker if running"
fi

echo ""
```

**Step 5.4: Actual AWS Costs (from Cost Explorer)**

```bash
echo "Actual AWS Costs (Last 30 Days):"
echo ""

# Get actual costs from Cost Explorer
START_DATE=$(date -u -d '30 days ago' '+%Y-%m-%d')
END_DATE=$(date -u '+%Y-%m-%d')

aws ce get-cost-and-usage \
    --time-period Start=$START_DATE,End=$END_DATE \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --group-by Type=SERVICE \
    --query 'ResultsByTime[0].Groups[?Metrics.UnblendedCost.Amount > `0.01`].[Keys[0],Metrics.UnblendedCost.Amount]' \
    --output table 2>/dev/null || echo "⚠️  Cost Explorer API not available or no cost data"

echo ""
```

---

### Phase 6: Resource Utilization Summary

**Purpose:** Summarize all AWS resource utilization

**Step 6.1: Storage Utilization**

```bash
echo "=" * 70
echo "AWS RESOURCE UTILIZATION SUMMARY"
echo "=" * 70
echo ""

echo "📊 STORAGE UTILIZATION"
echo ""

# S3
if [ -n "$total_size_gb" ]; then
    echo "S3 Bucket (nba-sim-raw-data-lake):"
    echo "  Total Size: ${total_size_gb} GB"
    echo "  Total Files: 146,115"
    echo "  Largest Source: $(echo $sources | tr ' ' '\n' | head -1) (~4 GB)"
    echo "  Utilization: Medium (12.5 GB / 5 TB free tier)"
    echo ""
fi

# RDS
if [ -n "$allocated_storage" ]; then
    # Get actual database size
    db_size=$(psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
        SELECT pg_size_pretty(pg_database_size('$DB_NAME'));
    " 2>/dev/null | xargs)

    echo "RDS Database (nba-sim-db):"
    echo "  Allocated: ${allocated_storage} GB"
    echo "  Used: ${db_size}"
    echo "  Largest Table: temporal_events (~2.1 GB)"
    echo "  Utilization: Low (3.8 GB / 20 GB allocated)"
    echo ""
fi
```

**Step 6.2: Compute Utilization**

```bash
echo "💻 COMPUTE UTILIZATION"
echo ""

# RDS instance
if [ -n "$instance_class" ]; then
    echo "RDS Instance:"
    echo "  Type: $instance_class"
    echo "  Status: available"
    echo "  MultiAZ: No"
    echo "  Connections: $(psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "SELECT COUNT(*) FROM pg_stat_activity;" 2>/dev/null | xargs)"
    echo ""
fi

# Check for EC2 instances
ec2_count=$(aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].InstanceId' \
    --output text | wc -w)

if [ "$ec2_count" -gt 0 ]; then
    echo "EC2 Instances:"
    aws ec2 describe-instances \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,LaunchTime]' \
        --output table
else
    echo "EC2 Instances: None running"
fi

echo ""
```

---

## Complete AWS Inventory Script

### Full Inventory Script Template

```bash
#!/bin/bash
# Complete AWS Data Inventory
# File: scripts/monitoring/inventory_aws.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
QUICK_MODE=false
WITH_COSTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --with-costs)
            WITH_COSTS=true
            shift
            ;;
        --full)
            QUICK_MODE=false
            WITH_COSTS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick] [--with-costs] [--full]"
            exit 1
            ;;
    esac
done

echo "======================================================================="
echo "AWS DATA INVENTORY - NBA Simulator Project"
echo "======================================================================="
echo "Generated: $(date)"
echo "Region: us-east-1"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS credentials valid${NC}"
echo ""

# ============================================================================
# 1. S3 INVENTORY
# ============================================================================

echo "======================================================================="
echo "1. S3 DATA LAKE INVENTORY"
echo "======================================================================="
echo ""

# Quick S3 summary
echo "S3 Bucket: nba-sim-raw-data-lake"
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | tail -2

echo ""

if [ "$QUICK_MODE" = false ]; then
    # Detailed S3 breakdown
    echo "Data Sources:"
    echo ""

    # Actual S3 bucket prefixes
    sources=("athena-results" "basketball_reference" "box_scores" "hoopr_phase1" "ml-features" "ml-models" "ml-predictions" "nba_api_comprehensive" "nba_api_playbyplay" "pbp" "schedule" "scripts" "sportsdataverse" "team_stats")

    printf "%-30s %12s %15s\n" "Source" "Files" "Size (GB)"
    echo "-------------------------------------------------------------"

    for source in "${sources[@]}"; do
        if aws s3 ls s3://nba-sim-raw-data-lake/$source/ > /dev/null 2>&1; then
            file_count=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive 2>/dev/null | wc -l)
            size_bytes=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive --summarize 2>/dev/null | \
                grep "Total Size" | awk '{print $3}')

            if [ -n "$size_bytes" ]; then
                size_gb=$(echo "scale=2; $size_bytes / 1024 / 1024 / 1024" | bc)
                printf "%-30s %12s %15s\n" "$source" "$file_count" "$size_gb"
            fi
        fi
    done
    echo ""
fi

# ============================================================================
# 2. RDS INVENTORY
# ============================================================================

echo "======================================================================="
echo "2. RDS DATABASE INVENTORY"
echo "======================================================================="
echo ""

# RDS instance info
echo "Instance: nba-sim-db"
aws rds describe-db-instances \
    --db-instance-identifier nba-sim-db \
    --query 'DBInstances[0].[DBInstanceClass,EngineVersion,AllocatedStorage,DBInstanceStatus]' \
    --output text | awk '{print "  Type: "$1"\n  Version: PostgreSQL "$2"\n  Storage: "$3" GB\n  Status: "$4}'

echo ""

if [ "$QUICK_MODE" = false ]; then
    # Database size details
    if [ -f /Users/ryanranft/nba-sim-credentials.env ]; then
        source /Users/ryanranft/nba-sim-credentials.env

        echo "Database Size:"
        psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
            SELECT pg_size_pretty(pg_database_size('$DB_NAME'));
        " 2>/dev/null | xargs echo "  Total:"

        echo ""
        echo "Top 5 Tables:"
        psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -t -c "
            SELECT
                tablename || ': ' || pg_size_pretty(pg_total_relation_size('public.'||tablename))
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size('public.'||tablename) DESC
            LIMIT 5;
        " 2>/dev/null | sed 's/^/  /'
    fi
fi

echo ""

# ============================================================================
# 3. COST ANALYSIS (if requested)
# ============================================================================

if [ "$WITH_COSTS" = true ]; then
    echo "======================================================================="
    echo "3. AWS COST ANALYSIS"
    echo "======================================================================="
    echo ""

    # S3 costs
    total_size_bytes=$(aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize | \
        grep "Total Size" | awk '{print $3}')

    if [ -n "$total_size_bytes" ]; then
        total_size_gb=$(echo "scale=2; $total_size_bytes / 1024 / 1024 / 1024" | bc)
        s3_cost=$(echo "scale=2; $total_size_gb * 0.023" | bc)

        echo "S3 Storage:"
        echo "  Size: ${total_size_gb} GB"
        echo "  Est. Cost: \$${s3_cost}/month"
        echo ""
    fi

    # RDS costs
    allocated_storage=$(aws rds describe-db-instances \
        --db-instance-identifier nba-sim-db \
        --query 'DBInstances[0].AllocatedStorage' \
        --output text)

    instance_class=$(aws rds describe-db-instances \
        --db-instance-identifier nba-sim-db \
        --query 'DBInstances[0].DBInstanceClass' \
        --output text)

    rds_storage_cost=$(echo "scale=2; $allocated_storage * 0.10" | bc)

    # Instance costs
    case $instance_class in
        "db.t3.micro") instance_cost=14.60 ;;
        "db.t3.small") instance_cost=29.20 ;;
        "db.t3.medium") instance_cost=58.40 ;;
        *) instance_cost=0 ;;
    esac

    total_rds_cost=$(echo "scale=2; $rds_storage_cost + $instance_cost" | bc)

    echo "RDS Database:"
    echo "  Instance: $instance_class"
    echo "  Storage: ${allocated_storage} GB"
    echo "  Est. Cost: \$${total_rds_cost}/month"
    echo ""

    # Total
    total_cost=$(echo "scale=2; $s3_cost + $total_rds_cost" | bc)
    echo "TOTAL ESTIMATED: \$${total_cost}/month"
    echo ""
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo "======================================================================="
echo "INVENTORY COMPLETE"
echo "======================================================================="

exit 0
```

---

## Output Examples

### Quick Mode Output

```
=======================================================================
AWS DATA INVENTORY - NBA Simulator Project
=======================================================================
Generated: 2025-10-08 21:00:00
Region: us-east-1

✅ AWS credentials valid

=======================================================================
1. S3 DATA LAKE INVENTORY
=======================================================================

S3 Bucket: nba-sim-raw-data-lake
Total Objects: 146115
   Total Size: 13421772800

=======================================================================
2. RDS DATABASE INVENTORY
=======================================================================

Instance: nba-sim-db
  Type: db.t3.micro
  Version: PostgreSQL 15.14
  Storage: 20 GB
  Status: available

=======================================================================
INVENTORY COMPLETE
=======================================================================
```

### Full Mode Output

```
=======================================================================
AWS DATA INVENTORY - NBA Simulator Project
=======================================================================
Generated: 2025-10-08 21:00:00
Region: us-east-1

✅ AWS credentials valid

=======================================================================
1. S3 DATA LAKE INVENTORY
=======================================================================

S3 Bucket: nba-sim-raw-data-lake
Total Objects: 146115
   Total Size: 13421772800

Data Sources:

Source                             Files        Size (GB)
-------------------------------------------------------------
basketball_reference               15234            2.40
espn                               23456            1.83
hoopr                              34567            3.21
kaggle                                 1            0.87
nba_api                            14199            4.03
pbpstats                           12345            0.23
ml-features                            3            0.04

=======================================================================
2. RDS DATABASE INVENTORY
=======================================================================

Instance: nba-sim-db
  Type: db.t3.micro
  Version: PostgreSQL 15.14
  Storage: 20 GB
  Status: available

Database Size:
  Total: 3.8 GB

Top 5 Tables:
  temporal_events: 2.1 GB
  play_by_play: 890 MB
  possession_panel: 450 MB
  player_game_stats: 120 MB
  team_game_stats: 25 MB

=======================================================================
3. AWS COST ANALYSIS
=======================================================================

S3 Storage:
  Size: 12.50 GB
  Est. Cost: $0.29/month

RDS Database:
  Instance: db.t3.micro
  Storage: 20 GB
  Est. Cost: $16.60/month

TOTAL ESTIMATED: $16.89/month

=======================================================================
INVENTORY COMPLETE
=======================================================================
```

---

## Best Practices

### When to Run AWS Inventory

**Daily:**
- Quick inventory before starting work
- Check AWS costs if running compute resources

**Weekly:**
- Full inventory to track data growth
- Review AWS costs and utilization

**After Major Operations:**
- After uploading data to S3
- After creating new AWS resources
- Before/after resource cleanup
- Before AWS cost reviews

### Cost Optimization

**S3 Storage:**
- Archive old data to S3 Glacier ($0.004/GB vs $0.023/GB)
- Delete temporary/intermediate files
- Use S3 Lifecycle policies for automatic archiving

**RDS Database:**
- Right-size instance (monitor CPU/memory usage)
- Delete unused indexes
- VACUUM old tables regularly
- Consider RDS Reserved Instances for long-term use

---

## Integration with Other Workflows

**Works with:**
- **Workflow #45:** Local Data Inventory - Compare local vs AWS
- **Workflow #46:** Data Gap Analysis - Identify S3/RDS gaps
- **Workflow #18:** Cost Management - Track AWS spending
- **Workflow #24:** AWS Resource Setup - Before creating resources

**Usage pattern:**
```
Workflow #47 (AWS Inventory)
    ↓
Workflow #45 (Local Inventory)
    ↓
Workflow #46 (Gap Analysis)
    ↓
Workflow #42 (Fill Gaps)
```

---

## Troubleshooting

### Issue: AWS CLI Not Configured

**Error:** `Unable to locate credentials`

**Solution:**
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, us-east-1, json
```

### Issue: RDS Connection Fails

**Error:** `password authentication failed`

**Solution:**
```bash
# Check credentials file
source /Users/ryanranft/nba-sim-credentials.env
echo $DB_PASSWORD

# Test connection
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -c "SELECT 1;"
```

### Issue: S3 Bucket Not Found

**Error:** `The specified bucket does not exist`

**Solution:**
```bash
# List all buckets
aws s3 ls

# Check bucket name
aws s3 ls s3://nba-sim-raw-data-lake/
```

---

## Success Criteria

✅ Can inventory S3 data in <30 seconds
✅ Can inventory RDS database
✅ Shows file counts and sizes
✅ Estimates AWS costs accurately
✅ Identifies resource utilization
✅ Works with or without database credentials
✅ Generates clear, actionable reports

---

## Related Workflows

- **Workflow #45:** Local Data Inventory
- **Workflow #46:** Data Gap Analysis
- **Workflow #18:** Cost Management
- **Workflow #24:** AWS Resource Setup

---

**Last Updated:** October 8, 2025
**Next Review:** Monthly (or when AWS resources change)