
# MACHINE_SPECS.md

**Last Updated:** 2025-10-01

**Purpose:** Track development machine specifications and software versions to ensure Claude generates code compatible with the actual environment.

---

## Hardware Specifications

**Device:** MacBook Pro 16-inch, 2023
**Processor:** Apple M2 Max chip
**Memory:** 96 GB
**Storage:** Macintosh HD - 1.71 TB available of 4 TB
**Operating System:** macOS Sequoia Version 15.6.1

---

## Disk I/O Performance

**Storage Type:** NVMe SSD (Apple internal storage)
**Available Space:** 1.71 TB of 4 TB total
**File System:** APFS (Apple File System)

### Performance Characteristics

**Sequential Read/Write:**
- **Expected Read Speed:** ~5,000-7,000 MB/s (Apple M2 Max NVMe)
- **Expected Write Speed:** ~5,000-6,000 MB/s
- **Typical for M2 Max:** Peak speeds up to 7.4 GB/s on high-end configurations

**Random I/O:**
- **4K Random Read:** ~100,000-150,000 IOPS
- **4K Random Write:** ~80,000-120,000 IOPS

### Project-Specific I/O Considerations

**Large File Operations (119 GB NBA Dataset):**
- **Local file enumeration** (146,115 JSON files): ~30-60 seconds
- **Sequential read of entire dataset:** ~20-30 seconds at peak speeds (theoretical)
- **Practical read with processing:** 2-5 minutes depending on CPU operations

**AWS S3 Operations:**
- **Upload speed bottleneck:** Network bandwidth (NOT disk I/O)
- **Expected S3 sync performance:**
  - Limited by internet upload speed (typically 10-50 MB/s residential)
  - Disk can easily sustain 5000+ MB/s, so disk is NOT the bottleneck
  - 119 GB upload at 20 MB/s = ~100 minutes
  - 119 GB upload at 50 MB/s = ~40 minutes

**Conda Environment Operations:**
- **Package installation:** Fast due to NVMe speeds
- **Environment creation:** Typically <2 minutes for full environment
- **pip/conda cache:** Benefits from fast random I/O

### Check Disk Performance

**Check current disk usage:**
```bash
df -h /
```

**Expected output:**
```
Filesystem     Size   Used  Avail Capacity  iused      ifree %iused  Mounted on
/dev/disk3s1s1 4.0Ti  2.3Ti  1.7Ti    58%  5000000  17000000   23%   /
```

**Check I/O statistics (install if needed):**
```bash
# Check if iostat is available (built into macOS)
iostat -d disk0 1 5

# Alternative: Use Activity Monitor → Disk tab for real-time I/O
```

**Disk health check:**
```bash
# Check SMART status
diskutil info disk0 | grep -i smart

# Expected: "SMART Status: Verified"
```

**File system info:**
```bash
# Verify APFS
diskutil info / | grep "Type (Bundle)"

# Expected: "Type (Bundle): apfs"
```

### Performance Optimization Tips

**For large file operations in this project:**
1. **Avoid recursive directory listings** when possible (use direct paths)
2. **Use streaming reads** for large JSON files instead of loading entire file into memory
3. **Leverage parallel I/O** when processing multiple files (Python multiprocessing)
4. **Monitor disk space** - maintain at least 10% free space (400+ GB) for optimal performance

**File operations performance expectations:**
- **Reading single JSON file (700 KB):** <1 ms
- **Reading 1,000 JSON files sequentially:** ~1-2 seconds
- **Reading all 146,115 files:** ~2-5 minutes (depends on processing)
- **Writing to local SSD:** Consistently fast, no significant delays expected

### Known Limitations

**macOS APFS Characteristics:**
- **Case-insensitive by default** (but case-preserving)
  - `Game.json` and `game.json` are treated as the same file
  - Important when syncing with case-sensitive systems (Linux)
- **Snapshot overhead:** APFS creates automatic snapshots
  - Check snapshots: `tmutil listlocalsnapshots /`
  - Cleanup if needed: `tmutil deletelocalsnapshots /`

**Connection to Project Data:**
- **Local data location:** `/Users/ryanranft/0espn/data/nba/` (119 GB)
- **Project location:** `/Users/ryanranft/nba-simulator-aws/`
- **Both on same SSD:** No cross-device I/O bottlenecks

---

## Network Configuration

**Network Interface:** Built-in Wi-Fi or Ethernet (update after running checklist)
**Status:** TBD (run network checklist below)

### Network Performance Baselines

**Critical for AWS Operations:**
- **S3 uploads/downloads:** Network is PRIMARY bottleneck (not disk I/O)
- **Glue job triggers:** Network latency affects job start time
- **RDS connections:** Network stability critical for database operations
- **SageMaker:** Model downloads and training data transfer

### Check Network Configuration

**Check active network interfaces:**
```bash
ifconfig | grep -A 1 "flags=.*UP"
```

**Check current IP address and interface:**
```bash
# Show all network interfaces with IPs
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Test internet connectivity:**
```bash
# Basic connectivity test
ping -c 4 8.8.8.8

# DNS resolution test
ping -c 4 google.com
```

**Check network speed (download):**
```bash
# Using curl to download test file (if available)
curl -o /dev/null -s -w "Speed: %{speed_download} bytes/sec\n" http://speedtest.tele2.net/10MB.zip
```

**Check default gateway:**
```bash
netstat -nr | grep default
```

**View DNS configuration:**
```bash
scutil --dns | grep "nameserver"
```

**Expected DNS servers:**
- Router DNS (typically 192.168.x.1)
- Or public DNS (8.8.8.8, 1.1.1.1, etc.)

### AWS-Specific Network Configuration

**Test AWS connectivity:**
```bash
# Test connection to AWS S3 endpoint (us-east-1)
ping -c 4 s3.us-east-1.amazonaws.com

# Test AWS API connectivity
curl -I https://s3.us-east-1.amazonaws.com
```

**Expected response:** HTTP/1.1 403 Forbidden (normal - means endpoint is reachable)

**Check AWS region latency:**
```bash
# Measure round-trip time to us-east-1
time aws s3 ls s3://nba-sim-raw-data-lake/ --region us-east-1 | head -1

# Compare with other regions (if needed)
# time aws s3 ls s3://bucket-name/ --region us-west-2 | head -1
```

**Typical latency expectations:**
- **us-east-1 from most US locations:** 20-80 ms
- **Cross-country (US West to us-east-1):** 60-100 ms
- **International:** 100-300+ ms

### Bandwidth Considerations

**Upload bandwidth (critical for S3 sync):**
- **Residential typical:** 10-50 MB/s (80-400 Mbps)
- **Business/fiber:** 50-125 MB/s (400-1000 Mbps)

**Check current bandwidth:**
```bash
# Note: This requires running actual upload test
# Option 1: Use AWS S3 with a test file
dd if=/dev/zero bs=1M count=100 | aws s3 cp - s3://nba-sim-raw-data-lake/test-upload.bin

# Option 2: Use built-in network activity monitor
# Open Activity Monitor → Network tab → observe Send/Receive rates during S3 sync
```

**Project-specific bandwidth usage:**
- **Initial S3 upload (119 GB):** One-time cost
  - At 20 MB/s: ~100 minutes
  - At 50 MB/s: ~40 minutes
  - **Already completed** for this project
- **Ongoing operations:** Minimal (< 1 GB/day typical)
- **RDS queries:** Low bandwidth (KB/s range)
- **Glue jobs:** Backend AWS operations (no client bandwidth needed)

### VPN Configuration

**VPN Status:** Not applicable by default (update if using VPN)

**If using VPN for AWS operations:**
```bash
# Check if VPN is active
scutil --nc list | grep Connected

# Check VPN interface
ifconfig | grep -A 5 utun
```

**VPN Considerations for AWS:**
- **Corporate VPN:** May route AWS traffic through corporate network (slower)
- **Privacy VPN:** May cause AWS region detection issues
- **Split tunneling:** Recommended to exclude AWS endpoints from VPN routing
- **Latency impact:** VPN typically adds 20-100ms latency

**If VPN interferes with AWS:**
```bash
# Disconnect VPN temporarily for large S3 operations
# Or configure split tunneling to exclude AWS IP ranges
```

### Firewall and Security

**macOS Firewall status:**
```bash
# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Expected: "Firewall is enabled" or "Firewall is disabled"
```

**Check firewall application exceptions:**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps
```

**AWS CLI and Python should be allowed** (automatic for signed applications)

**Verify no blocking of AWS services:**
- **Port 443 (HTTPS):** Must be open for all AWS API calls
- **Port 22 (SSH):** Needed for GitHub operations
- **Port 5432 (PostgreSQL):** Will be needed for RDS connections

**Test specific ports:**
```bash
# Test HTTPS (AWS)
nc -zv s3.us-east-1.amazonaws.com 443

# Test SSH (GitHub)
ssh -T git@github.com

# Test PostgreSQL (after RDS is created)
# nc -zv nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com 5432
```

### Network Optimization for This Project

**Best practices for AWS operations:**

1. **Large S3 uploads (multi-GB):**
   - Use `aws s3 sync` instead of `cp` (supports resume)
   - Enable multipart uploads (automatic for files > 8MB)
   - Consider uploading during off-peak hours for better bandwidth

2. **S3 download optimization:**
   ```bash
   # Use parallel downloads for multiple files
   aws s3 sync s3://bucket/path /local/path --no-progress
   ```

3. **RDS connections:**
   - Use connection pooling (SQLAlchemy handles this)
   - Keep connections alive during active sessions
   - Close connections properly to avoid timeouts

4. **Monitor network during operations:**
   ```bash
   # Terminal 1: Run AWS operation
   aws s3 sync /local/path s3://bucket/path

   # Terminal 2: Monitor network activity
   nettop -m tcp
   ```

### Troubleshooting Network Issues

**Slow S3 uploads:**
```bash
# 1. Test raw upload bandwidth
time dd if=/dev/zero bs=1M count=100 | aws s3 cp - s3://nba-sim-raw-data-lake/speedtest.bin

# 2. Check for DNS issues
nslookup s3.us-east-1.amazonaws.com

# 3. Try different AWS endpoint style
aws s3 ls s3://nba-sim-raw-data-lake/ --endpoint-url https://s3.amazonaws.com
```

**Connection timeouts to AWS:**
```bash
# Check MTU size (may need adjustment for some networks)
networksetup -getMTU en0

# Standard is 1500, some networks need 1492 or lower
# Only adjust if experiencing frequent timeouts
```

**GitHub SSH connection issues:**
```bash
# Test SSH connection
ssh -vT git@github.com

# Check SSH config
cat ~/.ssh/config | grep -A 5 github.com
```

### Network Status Summary

**Measured network performance:**

| Parameter | Value | Last Checked | Status |
|-----------|-------|--------------|--------|
| Active Interface | en0, en7 (Ethernet/Wi-Fi) | 2025-10-01 | ✅ Multiple interfaces active |
| IP Address | [Private network] | 2025-10-01 | ✅ Local network |
| Default Gateway | [Router] | 2025-10-01 | ✅ Router accessible |
| DNS Servers | [Router DNS] | 2025-10-01 | ✅ Resolving correctly |
| Internet Latency | 7.8-22.9ms avg 14.9ms to 8.8.8.8 | 2025-10-01 | ✅ Excellent (<20ms) |
| AWS S3 Latency (us-east-1) | 38.1-40.1ms avg 39.0ms | 2025-10-01 | ✅ Excellent (<50ms) |
| AWS DNS Resolution | 8 IPs resolved instantly | 2025-10-01 | ✅ Fast resolution |
| Upload Bandwidth | ~4.2 MB/s (10 MB in 2.38s) | 2025-10-01 | ✅ Measured to S3 |
| Download Bandwidth | ~1.8 MB/s (738 KB in 0.90s) | 2025-10-01 | ✅ Measured from S3 |
| VPN Status | No VPN active | 2025-10-01 | ✅ Direct connection |
| Firewall | Unable to check (requires sudo) | 2025-10-01 | ℹ️ Check manually in System Settings |

---

## Software Environment

### Package Managers

#### Homebrew
**Status:** ✅ Installed
**Purpose:** System-level package management and auto-updates

**Check version:**
```bash
brew --version
```

**Check installation location:**
```bash
which brew
```

**Expected location (Apple Silicon):** `/opt/homebrew/bin/brew`

**Update all packages:**
```bash
brew update && brew upgrade
```

---

#### Miniconda
**Status:** ✅ Installed
**Purpose:** Python environment management

**Check version:**
```bash
conda --version
```

**Check installation location:**
```bash
which conda
conda info --base
```

**Expected location:** `/Users/ryanranft/miniconda3`

**Current environment:** `nba-aws`

**List all conda environments:**
```bash
conda env list
```

**Check conda configuration:**
```bash
conda info
```

**Update conda:**
```bash
conda update -n base -c defaults conda
```

---

### Conda Environment Export and Recreation

**Purpose:** Export complete environment specification for reproducibility and disaster recovery.

#### Export Current Environment

**Export environment to YAML file:**
```bash
# Activate the environment first
conda activate nba-aws

# Export with all dependencies (recommended)
conda env export > environment.yml

# Export with only explicitly installed packages (minimal)
conda env export --from-history > environment-minimal.yml
```

**Export pip packages separately:**
```bash
# Export pip-only packages
pip list --format=freeze > requirements.txt
```

**View exported environment file:**
```bash
cat environment.yml | head -30
```

**Expected environment.yml structure:**
```yaml
name: nba-aws
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11.13
  - pip=23.3.1
  - pip:
    - boto3==1.34.144
    - pandas==2.0.3
    - numpy==1.24.3
    # ... additional packages
```

#### Understand Environment Export Formats

**Full export (environment.yml):**
- **Pros:** Complete specification with all dependencies
- **Cons:** Platform-specific, may not work on different OS
- **Use case:** Exact reproduction on same OS/architecture
- **File size:** Larger (~200-500 lines)

**Minimal export (environment-minimal.yml):**
- **Pros:** Platform-independent, only explicitly installed packages
- **Cons:** May resolve to different dependency versions
- **Use case:** Cross-platform recreation, general sharing
- **File size:** Smaller (~30-50 lines)

**Requirements.txt:**
- **Pros:** Standard Python format, works with pip
- **Cons:** Doesn't include conda packages or Python version
- **Use case:** pip-only environments, sharing with non-conda users
- **File size:** Medium (~50-100 lines)

#### Recreate Environment from Export

**Method 1: From environment.yml (exact recreation):**
```bash
# Create new environment from file
conda env create -f environment.yml

# Verify creation
conda env list | grep nba-aws

# Activate and test
conda activate nba-aws
python --version
pip list
```

**Method 2: From environment-minimal.yml (cross-platform):**
```bash
# Create with minimal spec (conda resolves dependencies)
conda env create -f environment-minimal.yml

# Install pip packages separately
conda activate nba-aws
pip install -r requirements.txt
```

**Method 3: Manual recreation (from documentation):**
```bash
# Create fresh environment with specific Python version
conda create -n nba-aws python=3.11.13

# Activate
conda activate nba-aws

# Install pip packages
pip install -r requirements.txt
```

#### Verify Recreated Environment

**Check Python version:**
```bash
python --version
# Expected: Python 3.11.13
```

**Verify all core packages:**
```bash
pip show boto3 pandas numpy pyarrow jsonschema psycopg2-binary sqlalchemy pytest jupyter ipykernel python-dotenv pyyaml tqdm | grep -E "Name:|Version:"
```

**Count packages (should match original):**
```bash
pip list | wc -l
# Expected: ~60-80 packages
```

**Test imports:**
```bash
python -c "import boto3, pandas, numpy, psycopg2, sqlalchemy; print('All core packages imported successfully')"
```

#### Pip vs Conda Installed Packages

**List conda-installed packages:**
```bash
conda list | grep -v "pypi"
```

**List pip-installed packages (from PyPI):**
```bash
conda list | grep "pypi"
# Or
pip list --format=freeze
```

**This project's package sources:**
- **Conda-managed:** python, pip, setuptools (base packages)
- **Pip-installed:** All 14 core packages (boto3, pandas, numpy, etc.)
- **Reason:** pip provides more recent versions and better compatibility for AWS packages

**Check package source:**
```bash
conda list boto3
# Output shows channel: pypi (installed via pip)
```

#### Environment Backup Strategy

**Recommended backup frequency:**
- **After major package installations:** Immediate export
- **Weekly:** During regular session startup
- **Before major updates:** Export before running `conda update` or `pip upgrade`
- **Monthly:** Full environment export for archival

**Backup location recommendations:**
```bash
# Option 1: Version control (recommended)
# Store environment.yml in git repo (already done)
git add environment.yml
git commit -m "Update conda environment snapshot"

# Option 2: Local backup directory
mkdir -p ~/backups/conda-environments
cp environment.yml ~/backups/conda-environments/nba-aws-$(date +%Y%m%d).yml

# Option 3: Cloud storage
aws s3 cp environment.yml s3://nba-sim-raw-data-lake/backups/environment-$(date +%Y%m%d).yml
```

**Current environment.yml status:**
```bash
# Check if environment.yml exists in project
ls -la /Users/ryanranft/nba-simulator-aws/environment.yml

# Check when it was last updated
stat -f "%Sm" /Users/ryanranft/nba-simulator-aws/environment.yml 2>/dev/null || echo "File not found - run: conda env export > environment.yml"
```

#### Disaster Recovery Procedure

**Scenario: Environment corrupted or deleted**

**Step 1: Verify environment is missing or broken:**
```bash
conda env list | grep nba-aws
# If not listed, or if activation fails
```

**Step 2: Remove corrupted environment (if exists):**
```bash
conda env remove -n nba-aws
```

**Step 3: Recreate from backup:**
```bash
# Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# Recreate environment
conda env create -f environment.yml

# Verify
conda activate nba-aws
python --version
pip list | wc -l
```

**Step 4: Verify functionality:**
```bash
# Test AWS connectivity
python -c "import boto3; s3 = boto3.client('s3'); print(s3.list_buckets()['Buckets'][0]['Name'])"

# Test data processing
python -c "import pandas as pd; df = pd.DataFrame({'test': [1,2,3]}); print(df)"
```

**Estimated recovery time:** 5-10 minutes (depends on download speed)

#### Cross-Platform Considerations

**Exporting from macOS (M2 Max):**
- Environment includes ARM64-specific builds
- Full export (environment.yml) may not work on Intel/Linux/Windows
- Use minimal export for cross-platform sharing

**For cross-platform compatibility:**
```bash
# Export minimal specification
conda env export --from-history > environment-minimal.yml

# Add explicit platform-independent requirements.txt
pip list --format=freeze > requirements.txt

# Share both files with documentation about Python 3.11 requirement
```

**Platform-specific notes in environment:**
- **macOS ARM64:** Native support for all packages
- **macOS Intel:** Requires x86_64 builds (may need Rosetta 2)
- **Linux:** Different package names (e.g., libpq-dev for psycopg2)
- **Windows:** Some packages require Visual C++ build tools

#### Environment Difference Detection

**Compare current environment with exported file:**
```bash
# Export current state
conda env export > environment-current.yml

# Compare with previous export (if exists)
diff environment.yml environment-current.yml

# Show only package version differences
diff <(grep '^ *- ' environment.yml | sort) <(grep '^ *- ' environment-current.yml | sort)
```

**Check for package drift:**
```bash
# List packages installed since last export
# This requires manual comparison or custom script
```

#### Quick Environment Export Script

**Add to session startup routine:**
```bash
echo "=== CONDA ENVIRONMENT EXPORT ==="
echo ""

# Check if environment file exists
if [ -f environment.yml ]; then
    ENV_AGE=$(( ($(date +%s) - $(stat -f %m environment.yml)) / 86400 ))
    echo "environment.yml exists (${ENV_AGE} days old)"

    if [ $ENV_AGE -gt 7 ]; then
        echo "⚠️  WARNING: environment.yml is over 7 days old"
        echo "Consider updating: conda env export > environment.yml"
    else
        echo "✅ environment.yml is recent"
    fi
else
    echo "❌ environment.yml not found"
    echo "Create with: conda env export > environment.yml"
fi
echo ""
```

#### Environment Export Checklist

**Update environment.yml when:**
- ✅ Installing new packages via pip or conda
- ✅ Upgrading package versions
- ✅ Adding project dependencies
- ✅ Before major system updates
- ✅ Weekly as part of regular maintenance
- ✅ Before committing major code changes

**DO NOT commit to git:**
- ❌ `.env` files (contains credentials)
- ❌ `environment-current.yml` (temporary comparison files)
- ❌ Backup directories with dated exports

**DO commit to git:**
- ✅ `environment.yml` (for team reproducibility)
- ✅ `requirements.txt` (pip packages)
- ✅ `.env.example` (template without credentials)

---

### Python Environment

**Environment Name:** `nba-aws`
**Python Version:** 3.11.13 (required for AWS Glue 4.0 compatibility)

**Verify Python version:**
```bash
conda activate nba-aws
python --version
```

**Check Python location:**
```bash
which python
```

**Expected location:** `/Users/ryanranft/miniconda3/envs/nba-aws/bin/python`

**List installed packages:**
```bash
pip list
```

**Check specific package versions:**
```bash
pip show boto3 pandas numpy
```

**List all packages with versions:**
```bash
pip list --format=freeze
```

---

### Project-Specific Python Packages

**Requirements File:** `/Users/ryanranft/nba-simulator-aws/requirements.txt`
**Total Packages:** 14 core packages (plus dependencies)

#### Package Categories and Purpose

**1. AWS SDK (1 package)**

**boto3** (1.34.144)
- **Purpose:** AWS SDK for Python - interact with all AWS services
- **Used for:** S3 operations, Glue job management, RDS connections, SageMaker operations
- **Why this version:** Compatible with Python 3.11 and all required AWS services
- **Key modules:**
  - `boto3.client('s3')` - S3 bucket operations
  - `boto3.client('glue')` - Glue crawler and ETL jobs
  - `boto3.client('rds')` - RDS instance management
  - `boto3.client('sagemaker')` - ML model training and deployment

**Check boto3 version:**
```bash
pip show boto3 | grep Version
# Expected: Version: 1.34.144
```

**2. Data Processing (4 packages)**

**pandas** (2.0.3)
- **Purpose:** Data manipulation and analysis
- **Used for:** Loading JSON data, DataFrame operations, data cleaning, aggregations
- **Why this version:** Stable release with good performance for medium datasets
- **Key operations:** Reading JSONs, filtering rows, groupby operations, CSV exports

**numpy** (1.24.3)
- **Purpose:** Numerical computing and array operations
- **Used for:** Mathematical calculations, array operations, statistical computations
- **Why this version:** Compatible with pandas 2.0.3 and Python 3.11
- **Key operations:** Array math, statistical functions, random number generation

**pyarrow** (12.0.1)
- **Purpose:** Apache Arrow columnar format support
- **Used for:** Fast Parquet file I/O, efficient data serialization for AWS Glue
- **Why this version:** Required for pandas Parquet operations and Glue compatibility
- **Key operations:** Reading/writing Parquet files, columnar data processing

**jsonschema** (4.19.2)
- **Purpose:** JSON schema validation
- **Used for:** Validating JSON structure from ESPN data files
- **Why needed:** Ensure data quality before processing 146,115 JSON files
- **Key operations:** Schema validation, data quality checks

**Check data processing packages:**
```bash
pip show pandas numpy pyarrow jsonschema | grep -E "Name:|Version:"
```

**3. Database (2 packages)**

**psycopg2-binary** (2.9.9)
- **Purpose:** PostgreSQL database adapter for Python
- **Used for:** Direct connections to RDS PostgreSQL
- **Why binary version:** Pre-compiled, no need to install PostgreSQL development libraries
- **Why this version:** Latest stable with Python 3.11 support
- **Key operations:** Execute SQL queries, cursor management, transaction handling

**sqlalchemy** (2.0.23)
- **Purpose:** SQL toolkit and Object-Relational Mapping (ORM)
- **Used for:** Database abstraction, query building, connection pooling
- **Why this version:** Latest 2.x series with modern async support
- **Key operations:** Database connections, query building, ORM models, migrations

**Check database packages:**
```bash
pip show psycopg2-binary sqlalchemy | grep -E "Name:|Version:"
```

**4. Testing (1 package)**

**pytest** (7.4.3)
- **Purpose:** Testing framework for Python
- **Used for:** Unit tests, integration tests, data validation tests
- **Why this version:** Latest stable with good plugin ecosystem
- **Key features:** Test discovery, fixtures, parametrized tests, mocking
- **Usage:** `pytest tests/` to run all tests

**Check pytest version:**
```bash
pip show pytest | grep Version
```

**5. Jupyter (2 packages)**

**jupyter** (1.0.0)
- **Purpose:** Meta-package for Jupyter ecosystem
- **Used for:** Interactive data analysis, notebook-based development
- **Why needed:** Local development and testing before deploying to SageMaker
- **Components:** Jupyter Notebook, JupyterLab, IPython

**ipykernel** (6.26.0)
- **Purpose:** IPython kernel for Jupyter
- **Used for:** Running Python code in Jupyter notebooks
- **Why needed:** Connects Jupyter interface to Python interpreter
- **Key feature:** Allows conda environment to be used as Jupyter kernel

**Check Jupyter packages:**
```bash
pip show jupyter ipykernel | grep -E "Name:|Version:"
```

**Register conda environment as Jupyter kernel:**
```bash
python -m ipykernel install --user --name nba-aws --display-name "Python (nba-aws)"
```

**6. Utilities (3 packages)**

**python-dotenv** (1.0.0)
- **Purpose:** Load environment variables from .env file
- **Used for:** Managing configuration without hardcoding credentials
- **Why needed:** Secure credential management, environment-specific settings
- **Usage:**
  ```python
  from dotenv import load_dotenv
  load_dotenv()  # Loads .env file into environment variables
  ```

**pyyaml** (6.0.1)
- **Purpose:** YAML parser and emitter
- **Used for:** Reading AWS configuration from config/aws_config.yaml
- **Why needed:** Human-readable configuration files
- **Usage:**
  ```python
  import yaml
  with open('config/aws_config.yaml') as f:
      config = yaml.safe_load(f)
  ```

**tqdm** (4.66.1)
- **Purpose:** Progress bar for loops and iterables
- **Used for:** Visual feedback during long operations (processing 146K files)
- **Why needed:** User experience for long-running operations
- **Usage:**
  ```python
  from tqdm import tqdm
  for file in tqdm(files):
      process(file)
  ```

**Check utility packages:**
```bash
pip show python-dotenv pyyaml tqdm | grep -E "Name:|Version:"
```

#### Package Dependencies

**Additional packages installed as dependencies (partial list):**
- **botocore** - Core functionality for boto3
- **s3transfer** - S3 file transfer optimizations
- **jmespath** - JSON query language for AWS responses
- **urllib3** - HTTP client library
- **certifi** - SSL certificate bundle
- **pandas dependencies:** python-dateutil, pytz, tzdata
- **jupyter dependencies:** notebook, nbconvert, ipython, tornado

**View all installed packages:**
```bash
pip list
```

**Count total packages:**
```bash
pip list | wc -l
# Expected: ~60-80 packages (14 core + dependencies)
```

#### Package Installation and Verification

**Install all packages from requirements.txt:**
```bash
conda activate nba-aws
pip install -r requirements.txt
```

**Verify all core packages are installed:**
```bash
# Check each package explicitly
pip show boto3 pandas numpy pyarrow jsonschema psycopg2-binary sqlalchemy pytest jupyter ipykernel python-dotenv pyyaml tqdm | grep -E "Name:|Version:|Location:"
```

**Check for outdated packages:**
```bash
pip list --outdated
```

**Update specific package (if needed):**
```bash
pip install --upgrade package-name==version
# Then update requirements.txt
pip freeze > requirements.txt.new
# Review and merge into requirements.txt
```

#### Package Compatibility Matrix

| Package | Version | Python Req | Key Dependencies | AWS Glue Compatible |
|---------|---------|------------|------------------|---------------------|
| boto3 | 1.34.144 | >=3.7 | botocore, s3transfer | ✅ Yes |
| pandas | 2.0.3 | >=3.8 | numpy, pytz | ✅ Yes |
| numpy | 1.24.3 | >=3.8 | - | ✅ Yes |
| pyarrow | 12.0.1 | >=3.7 | - | ✅ Yes (required) |
| psycopg2-binary | 2.9.9 | >=3.6 | - | ✅ Yes |
| sqlalchemy | 2.0.23 | >=3.7 | greenlet | ✅ Yes |
| pytest | 7.4.3 | >=3.7 | pluggy, iniconfig | N/A (dev only) |
| jupyter | 1.0.0 | >=3.6 | notebook, ipython | N/A (local only) |
| python-dotenv | 1.0.0 | >=3.8 | - | ⚠️ Not needed in Glue |
| pyyaml | 6.0.1 | >=3.6 | - | ✅ Yes |
| tqdm | 4.66.1 | >=3.7 | - | ✅ Yes |

**Note on AWS Glue compatibility:**
- Glue uses Python 3.11 (compatible with all packages)
- Glue pre-installs: boto3, pandas, numpy, pyarrow, pyyaml
- Must explicitly include in Glue job: psycopg2-binary, sqlalchemy, tqdm
- Not needed in Glue: pytest, jupyter, python-dotenv

#### Package Version Tracking

**Update this table after checking versions:**

| Package | Required Version | Installed Version | Last Checked | Status |
|---------|------------------|-------------------|--------------|--------|
| boto3 | 1.34.144 | 1.34.144 | 2025-09-30 | ✅ Match |
| pandas | 2.0.3 | 2.0.3 | 2025-09-30 | ✅ Match |
| numpy | 1.24.3 | 1.24.3 | 2025-09-30 | ✅ Match |
| pyarrow | 12.0.1 | TBD | - | Run `pip show pyarrow` |
| jsonschema | 4.19.2 | TBD | - | Run `pip show jsonschema` |
| psycopg2-binary | 2.9.9 | TBD | - | Run `pip show psycopg2-binary` |
| sqlalchemy | 2.0.23 | TBD | - | Run `pip show sqlalchemy` |
| pytest | 7.4.3 | TBD | - | Run `pip show pytest` |
| jupyter | 1.0.0 | TBD | - | Run `pip show jupyter` |
| ipykernel | 6.26.0 | TBD | - | Run `pip show ipykernel` |
| python-dotenv | 1.0.0 | TBD | - | Run `pip show python-dotenv` |
| pyyaml | 6.0.1 | TBD | - | Run `pip show pyyaml` |
| tqdm | 4.66.1 | TBD | - | Run `pip show tqdm` |

#### Quick Package Check Script

**Run at start of session to verify all packages:**
```bash
echo "=== CORE PACKAGES ==="
echo ""

echo "AWS SDK:"
pip show boto3 | grep -E "Name:|Version:"
echo ""

echo "Data Processing:"
pip show pandas numpy pyarrow jsonschema | grep -E "Name:|Version:"
echo ""

echo "Database:"
pip show psycopg2-binary sqlalchemy | grep -E "Name:|Version:"
echo ""

echo "Testing:"
pip show pytest | grep -E "Name:|Version:"
echo ""

echo "Jupyter:"
pip show jupyter ipykernel | grep -E "Name:|Version:"
echo ""

echo "Utilities:"
pip show python-dotenv pyyaml tqdm | grep -E "Name:|Version:"
echo ""

echo "=== PACKAGE COUNT ==="
pip list | wc -l
```

---

### AWS CLI

**Status:** ✅ Installed (system-wide, NOT in conda)
**Purpose:** AWS resource management

**Check version:**
```bash
aws --version
```

**Check installation location:**
```bash
which aws
```

**Expected location (Homebrew on M2):** `/opt/homebrew/bin/aws`

**CRITICAL:** AWS CLI must be installed system-wide via Homebrew, NOT via pip in conda environment.

**Update AWS CLI:**
```bash
brew upgrade awscli
```

---

### Git

**Status:** ✅ Configured with SSH authentication

**Check version:**
```bash
git --version
```

**Check installation location:**
```bash
which git
```

**Expected location:** `/usr/bin/git` (macOS built-in) OR `/opt/homebrew/bin/git` (Homebrew)

**Verify SSH configuration:**
```bash
ssh -T git@github.com
```

**Expected output:** "Hi ryanranft! You've successfully authenticated..."

---

### IDE / Editors

**Primary IDE:** PyCharm (assumed - update if different)

**Terminal:** macOS Terminal / iTerm2 (update if different)

**Shell:** zsh (macOS default since Catalina)

**Check shell:**
```bash
echo $SHELL
```

**Expected output:** `/bin/zsh`

---

## Environment Variables

**Shell Configuration Files:** `.zshrc`, `.zprofile`, `.zshenv`
**Active Shell:** zsh (macOS default)

### Critical Environment Variables for This Project

**PATH Configuration:**
The PATH variable determines where the system looks for executables. Proper PATH ordering is critical.

**Check current PATH:**
```bash
echo $PATH
```

**Expected PATH structure (order matters):**
```
/Users/ryanranft/miniconda3/envs/nba-aws/bin    # Conda environment (FIRST when activated)
/Users/ryanranft/miniconda3/condabin            # Conda base
/opt/homebrew/bin                                # Homebrew packages (Apple Silicon)
/opt/homebrew/sbin                               # Homebrew system binaries
/usr/local/bin                                   # User-installed binaries
/usr/bin                                         # System binaries
/bin                                             # Essential binaries
/usr/sbin                                        # System administration binaries
/sbin                                            # Essential system binaries
```

**Verify PATH includes required directories:**
```bash
# Check for conda
echo $PATH | grep -o "/Users/ryanranft/miniconda3[^:]*" | head -3

# Check for Homebrew
echo $PATH | grep -o "/opt/homebrew[^:]*"

# Check which executables are being used
which python    # Should be: /Users/ryanranft/miniconda3/envs/nba-aws/bin/python
which aws       # Should be: /opt/homebrew/bin/aws
which git       # Should be: /usr/bin/git or /opt/homebrew/bin/git
which brew      # Should be: /opt/homebrew/bin/brew
which conda     # Should be: /Users/ryanranft/miniconda3/condabin/conda
```

### Conda Environment Variables

**When `nba-aws` environment is activated:**

**CONDA_DEFAULT_ENV:**
```bash
echo $CONDA_DEFAULT_ENV
# Expected: nba-aws
```

**CONDA_PREFIX:**
```bash
echo $CONDA_PREFIX
# Expected: /Users/ryanranft/miniconda3/envs/nba-aws
```

**CONDA_PYTHON_EXE:**
```bash
echo $CONDA_PYTHON_EXE
# Expected: /Users/ryanranft/miniconda3/bin/python
```

**CONDA_SHLVL:**
```bash
echo $CONDA_SHLVL
# Expected: 1 (indicates one conda environment is activated)
```

### AWS Environment Variables

**AWS Configuration:**

**AWS_DEFAULT_REGION:**
```bash
echo $AWS_DEFAULT_REGION
# Expected: us-east-1 (or empty if set via aws configure)
```

**AWS_PROFILE:**
```bash
echo $AWS_PROFILE
# Expected: empty (using default profile) or specific profile name
```

**AWS Config File Location:**
```bash
echo $AWS_CONFIG_FILE
# Expected: empty (uses default ~/.aws/config)

echo $AWS_SHARED_CREDENTIALS_FILE
# Expected: empty (uses default ~/.aws/credentials)
```

**Verify AWS credentials are configured:**
```bash
# Check if credentials file exists
ls -la ~/.aws/credentials

# Check if config file exists
ls -la ~/.aws/config

# View config (without exposing secrets)
cat ~/.aws/config
```

**Expected ~/.aws/config:**
```ini
[default]
region = us-east-1
output = json
```

**DO NOT expose credentials:**
```bash
# NEVER run: cat ~/.aws/credentials
# NEVER commit credentials to git
# NEVER share AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY
```

### Project-Specific Environment Variables

**Project uses `.env` file for configuration (gitignored):**

**Check if .env exists:**
```bash
ls -la /Users/ryanranft/nba-simulator-aws/.env
```

**Expected variables in .env (see .env.example):**
- Database connection strings
- AWS resource identifiers
- API keys (if any)
- Configuration flags

**Load .env in Python (handled by python-dotenv):**
```python
from dotenv import load_dotenv
load_dotenv()
```

**CRITICAL:** Never commit `.env` file to git (already in .gitignore)

### Python Environment Variables

**PYTHONPATH:**
```bash
echo $PYTHONPATH
# Expected: Usually empty (conda manages this)
# If set, should include project root for imports
```

**PYTHONHASHSEED:**
```bash
echo $PYTHONHASHSEED
# Expected: empty (random by default)
# Set to 0 for reproducible results if needed
```

**JUPYTER_CONFIG_DIR:**
```bash
echo $JUPYTER_CONFIG_DIR
# Expected: empty (uses default ~/.jupyter)
```

### Shell Configuration Files

**Check which files exist:**
```bash
ls -la ~ | grep -E "^\\.zsh|^\\.bash"
```

**Expected files for zsh:**
- `.zshrc` - Interactive shell configuration (aliases, functions, prompts)
- `.zprofile` - Login shell configuration (PATH, environment variables)
- `.zshenv` - Always sourced (used for essential environment variables)

**View relevant sections:**
```bash
# Check for conda initialization in .zshrc
grep -A 10 "conda initialize" ~/.zshrc

# Check for Homebrew initialization in .zprofile
grep -A 3 "homebrew" ~/.zprofile

# Check PATH modifications
grep "PATH" ~/.zshrc ~/.zprofile ~/.zshenv 2>/dev/null
```

**Expected conda initialization block in .zshrc:**
```bash
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/ryanranft/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/ryanranft/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/Users/ryanranft/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/ryanranft/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
```

**Expected Homebrew initialization in .zprofile:**
```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Environment Variables Checklist

**Run at start of session to verify environment:**
```bash
# 1. Check PATH
echo "=== PATH ==="
echo $PATH | tr ':' '\n' | nl
echo ""

# 2. Check conda variables (after activating nba-aws)
echo "=== CONDA ENVIRONMENT ==="
conda activate nba-aws
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "CONDA_PREFIX: $CONDA_PREFIX"
echo "CONDA_SHLVL: $CONDA_SHLVL"
echo ""

# 3. Check AWS variables
echo "=== AWS ENVIRONMENT ==="
echo "AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-not set}"
echo "AWS_PROFILE: ${AWS_PROFILE:-default}"
echo ""

# 4. Verify executables
echo "=== EXECUTABLE LOCATIONS ==="
which python
which aws
which git
which conda
which brew
echo ""

# 5. Check project .env
echo "=== PROJECT ENVIRONMENT ==="
if [ -f /Users/ryanranft/nba-simulator-aws/.env ]; then
    echo ".env file exists: ✅"
else
    echo ".env file exists: ❌ (create from .env.example if needed)"
fi
```

### Common Environment Issues

**Issue 1: Wrong Python version**
```bash
# Problem: python --version shows wrong version
# Cause: PATH order incorrect or wrong environment

# Solution:
conda deactivate
conda activate nba-aws
which python    # Should show conda environment path
```

**Issue 2: AWS CLI not found after conda activation**
```bash
# Problem: aws command not found after activating conda
# Cause: Conda modifies PATH, may not include Homebrew

# Solution: AWS CLI should be in Homebrew (system-wide), not conda
which aws       # Should show: /opt/homebrew/bin/aws
# If not found, ensure Homebrew is in PATH:
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Issue 3: Conda command not found**
```bash
# Problem: conda command not found in new shell
# Cause: conda init not run or .zshrc not sourced

# Solution:
/Users/ryanranft/miniconda3/bin/conda init zsh
source ~/.zshrc
```

**Issue 4: Module import errors**
```bash
# Problem: Python can't find project modules
# Cause: PYTHONPATH not set or wrong working directory

# Solution:
cd /Users/ryanranft/nba-simulator-aws
# Or set PYTHONPATH:
export PYTHONPATH=/Users/ryanranft/nba-simulator-aws:$PYTHONPATH
```

### Environment Variables Summary Table

**Update after running environment checklist:**

| Variable | Expected Value | Current Value | Status |
|----------|----------------|---------------|--------|
| PATH (first entry) | `/Users/ryanranft/miniconda3/envs/nba-aws/bin` | TBD | Run `echo $PATH` |
| CONDA_DEFAULT_ENV | `nba-aws` | TBD | Run `echo $CONDA_DEFAULT_ENV` |
| CONDA_PREFIX | `/Users/ryanranft/miniconda3/envs/nba-aws` | TBD | Run `echo $CONDA_PREFIX` |
| AWS_DEFAULT_REGION | `us-east-1` or empty | TBD | Run `echo $AWS_DEFAULT_REGION` |
| AWS_PROFILE | empty (default) | TBD | Run `echo $AWS_PROFILE` |
| SHELL | `/bin/zsh` | `/bin/zsh` | ✅ Verified |
| .env file | exists | TBD | Run `ls .env` |

---

## Version Tracking Table

| Software | Current Version | Last Checked | Update Command |
|----------|----------------|--------------|----------------|
| macOS | Sequoia 15.6.1 | 2025-10-01 | System Preferences → Software Update |
| Homebrew | TBD | - | `brew --version` |
| Miniconda | TBD | - | `conda --version` |
| Python (nba-aws) | 3.11.13 | 2025-09-30 | `python --version` |
| AWS CLI | TBD | - | `aws --version` |
| Git | TBD | - | `git --version` |
| boto3 | 1.34.144 | 2025-09-30 | `pip show boto3` |
| pandas | 2.0.3 | 2025-09-30 | `pip show pandas` |
| numpy | 1.24.3 | 2025-09-30 | `pip show numpy` |

---

## Session Startup Checklist

**Run at the start of EVERY session to update version information:**

```bash
# 1. System info
echo "=== SYSTEM INFO ==="
sw_vers
echo ""

# 2. Homebrew
echo "=== HOMEBREW ==="
brew --version
which brew
echo ""

# 3. Conda
echo "=== CONDA ==="
conda --version
conda info --base
conda env list | grep nba-aws
echo ""

# 4. Activate environment and check Python
echo "=== PYTHON (nba-aws environment) ==="
conda activate nba-aws
python --version
which python
echo ""

# 5. AWS CLI
echo "=== AWS CLI ==="
aws --version
which aws
echo ""

# 6. Git
echo "=== GIT ==="
git --version
which git
echo ""

# 7. Key Python packages
echo "=== KEY PACKAGES ==="
pip show boto3 | grep Version
pip show pandas | grep Version
pip show numpy | grep Version
```

**Copy and paste this into terminal, then share the output with Claude.**

---

## Update Protocol

### Weekly (Every Monday or Start of Week)
1. Run session startup checklist (above)
2. Update version table in this document
3. Check for Homebrew updates: `brew update && brew outdated`
4. Update critical packages if needed

### Monthly (First of Month)
1. Full system update: `brew upgrade`
2. Update conda: `conda update -n base -c defaults conda`
3. Update conda environment: `conda update --all -n nba-aws`
4. Review and update this document

### After Major Changes
- Document any new software installations
- Update version table
- Note any compatibility issues

---

## Compatibility Notes

### Apple Silicon (M2 Max) Specific
- **Homebrew location:** `/opt/homebrew/` (different from Intel Macs at `/usr/local/`)
- **Rosetta 2:** Not needed for this project (all packages have ARM64 support)
- **Performance:** Native ARM64 support provides optimal performance

### macOS Sequoia Specific
- Conda environments work natively
- Zsh is default shell (no bash compatibility needed)
- System Integrity Protection (SIP) enabled (standard)

### Critical Path Compatibility
- **Conda env must use Python 3.11** (AWS Glue 4.0 requirement)
- **AWS CLI must be system-wide** (not in conda)
- **SSH keys configured** (GitHub authentication)

---

## macOS Security Settings

**Purpose:** Document security configurations that may affect development workflow and AWS operations.

### System Integrity Protection (SIP)

**Status:** Enabled (macOS default)

**What is SIP:**
- Protects critical system files and directories from modification
- Prevents malicious software from tampering with system files
- Restricts root user access to protected locations

**Check SIP status:**
```bash
csrutil status
```

**Expected output:**
```
System Integrity Protection status: enabled.
```

**Protected directories (cannot modify even with sudo):**
- `/System/`
- `/usr/` (except `/usr/local/`)
- `/bin/`
- `/sbin/`
- Pre-installed Apple applications

**Impact on this project:**
- ✅ No negative impact - all development in `/Users/ryanranft/`
- ✅ Homebrew uses `/opt/homebrew/` (not protected)
- ✅ Conda uses `/Users/ryanranft/miniconda3/` (not protected)
- ✅ Python packages install to user directories

**When SIP might cause issues:**
- Installing system-wide Python packages (use conda/pip instead)
- Modifying system Python (use conda environments instead)
- Installing kernel extensions (not needed for this project)

**IMPORTANT:** Do NOT disable SIP for this project. It is not necessary.

---

### FileVault (Disk Encryption)

**Status:** TBD (check with command below)

**What is FileVault:**
- Full-disk encryption for macOS
- Protects data if laptop is lost or stolen
- Uses XTS-AES-128 encryption with 256-bit key

**Check FileVault status:**
```bash
fdesetup status
```

**Expected outputs:**
- `FileVault is On.` - Disk is encrypted (recommended)
- `FileVault is Off.` - Disk is not encrypted

**View encryption progress (if enabling):**
```bash
fdesetup status | grep "Percent complete"
```

**Impact on this project:**

**If FileVault is ON (recommended):**
- ✅ Data protected at rest (including AWS credentials)
- ✅ Slight performance overhead (~5-10% for disk I/O)
- ✅ Minimal impact on NVMe SSD (fast encryption)
- ⚠️ Must unlock disk at boot

**If FileVault is OFF:**
- ⚠️ AWS credentials in `~/.aws/` are unencrypted on disk
- ⚠️ `.env` file is unencrypted (contains sensitive data)
- ⚠️ Git credentials may be exposed if disk is physically accessed

**Performance impact on this project:**
- **File reads (146K JSON files):** Negligible (<5% overhead)
- **S3 uploads:** No impact (network bottleneck)
- **Database operations:** No impact (remote RDS)
- **Python operations:** No impact (CPU/memory bound)

**Recommendation:**
- ✅ Enable FileVault for security (especially for laptops)
- ✅ Backup recovery key securely
- ✅ Performance impact is minimal on M2 Max

---

### Gatekeeper

**Status:** Enabled (macOS default)

**What is Gatekeeper:**
- Verifies downloaded applications are from identified developers
- Protects against malware and unsigned applications
- Checks code signatures and notarization

**Check Gatekeeper status:**
```bash
spctl --status
```

**Expected output:**
```
assessments enabled
```

**View Gatekeeper settings:**
```bash
# Check system-wide setting
sudo spctl --master-status

# Check if app would be allowed to run
spctl --assess --verbose /Applications/Python.app
```

**Impact on this project:**

**Signed applications (should work without issues):**
- ✅ Python (signed by Apple via Xcode)
- ✅ Homebrew packages (trusted sources)
- ✅ AWS CLI (signed by Amazon)
- ✅ Git (signed by Apple)

**If you encounter "app cannot be opened" errors:**

**Method 1: Allow in System Settings (recommended)**
```bash
# After attempting to open app, go to:
# System Settings → Privacy & Security → "Open Anyway"
```

**Method 2: Override for specific app**
```bash
# Remove quarantine flag
xattr -d com.apple.quarantine /path/to/application

# Or allow specific app
sudo spctl --add /path/to/application
```

**Method 3: Temporarily disable (NOT recommended)**
```bash
# Disable Gatekeeper (requires admin password)
sudo spctl --master-disable

# Re-enable after installation
sudo spctl --master-enable
```

**Common scenarios:**
- Installing unsigned Python packages: ✅ No issue (pip/conda handle this)
- Running custom scripts: ✅ No issue (executed by Python interpreter)
- Installing developer tools: ⚠️ May require manual approval first time

---

### Firewall

**Status:** TBD (check with command below)

**What is macOS Firewall:**
- Application-level firewall (not port-based)
- Blocks incoming connections to applications
- Does NOT block outgoing connections

**Check firewall status:**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**Expected outputs:**
- `Firewall is enabled.` - Incoming connections are filtered
- `Firewall is disabled.` - All incoming connections allowed

**Check firewall mode:**
```bash
# Stealth mode (drop packets silently)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode

# Block all incoming connections
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getblockall
```

**List allowed applications:**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps
```

**Impact on this project:**

**Incoming connections (may be blocked by firewall):**
- ⚠️ SSH server (if running locally - not needed for this project)
- ⚠️ Local database server (not needed - using RDS)
- ⚠️ Jupyter Notebook server (default port 8888 - may need approval)

**Outgoing connections (NEVER blocked by macOS firewall):**
- ✅ AWS S3 API calls (port 443)
- ✅ AWS RDS connections (port 5432)
- ✅ GitHub SSH (port 22)
- ✅ HTTPS downloads (port 443)
- ✅ All AWS services

**Jupyter Notebook firewall configuration:**
```bash
# If firewall blocks Jupyter, you'll see connection errors when accessing localhost:8888
# Allow Python to accept incoming connections when prompted
# Or manually allow:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Users/ryanranft/miniconda3/envs/nba-aws/bin/python
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Users/ryanranft/miniconda3/envs/nba-aws/bin/python
```

**Recommended firewall setting for this project:**
- ✅ Enable firewall (default)
- ✅ Allow signed applications automatically
- ✅ Enable stealth mode (optional, for additional security)
- ✅ Do NOT block all incoming (breaks local development)

---

### Privacy & Permissions

**Relevant permissions for development:**

#### Full Disk Access

**Required for:**
- Terminal.app / iTerm2 (accessing all files)
- IDE (PyCharm, VS Code, etc.)

**Check if Terminal has Full Disk Access:**
```bash
# Try to list protected directory
ls ~/Library/Mail/ 2>&1 | grep -q "Operation not permitted" && echo "❌ No Full Disk Access" || echo "✅ Has Full Disk Access"
```

**Grant Full Disk Access:**
1. System Settings → Privacy & Security → Full Disk Access
2. Click lock icon (enter password)
3. Click "+" and add Terminal.app or iTerm2.app
4. Restart terminal application

**Why needed:**
- Reading files in protected locations
- Accessing Git repositories with restricted permissions
- Reading SSH keys and credentials

#### Developer Tools

**Check if Developer Tools are installed:**
```bash
xcode-select -p
```

**Expected output:**
```
/Library/Developer/CommandLineTools
```

**If not installed:**
```bash
xcode-select --install
```

**Required for:**
- Git (native macOS git)
- Compiling Python packages with C extensions
- Some Homebrew packages

---

### SSH Keys and GitHub Authentication

**SSH Key Location:**
```bash
ls -la ~/.ssh/
```

**Expected files:**
- `id_rsa` or `id_ed25519` - Private key (NEVER share)
- `id_rsa.pub` or `id_ed25519.pub` - Public key
- `known_hosts` - Fingerprints of known servers
- `config` - SSH client configuration

**Check SSH key permissions:**
```bash
ls -l ~/.ssh/id_*
```

**Expected permissions:**
- Private key (`id_rsa`): `-rw-------` (600) - CRITICAL
- Public key (`id_rsa.pub`): `-rw-r--r--` (644) - OK

**Fix incorrect permissions:**
```bash
# Fix private key (must be 600)
chmod 600 ~/.ssh/id_rsa

# Fix public key (should be 644)
chmod 644 ~/.ssh/id_rsa.pub

# Fix .ssh directory (should be 700)
chmod 700 ~/.ssh
```

**Test GitHub SSH authentication:**
```bash
ssh -T git@github.com
```

**Expected output:**
```
Hi ryanranft! You've successfully authenticated, but GitHub does not provide shell access.
```

**Common SSH issues:**

**Issue 1: Permission denied (publickey)**
```bash
# Check SSH key is added to ssh-agent
ssh-add -l

# If "The agent has no identities", add key:
ssh-add ~/.ssh/id_rsa
```

**Issue 2: Bad permissions**
```bash
# Fix all SSH permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 644 ~/.ssh/known_hosts
chmod 644 ~/.ssh/config
```

**Issue 3: SSH key not on GitHub**
```bash
# View public key
cat ~/.ssh/id_rsa.pub

# Copy and add to: https://github.com/settings/keys
```

---

### AWS Credentials Security

**Credentials location:**
```bash
~/.aws/credentials  # Contains access keys (NEVER commit to git)
~/.aws/config       # Contains region and output settings (safe to share)
```

**Check credentials file permissions:**
```bash
ls -l ~/.aws/credentials
```

**Expected permissions:** `-rw-------` (600) - Only owner can read/write

**Fix incorrect permissions:**
```bash
chmod 600 ~/.aws/credentials
chmod 644 ~/.aws/config
```

**Security best practices:**

**DO:**
- ✅ Keep credentials file at 600 permissions
- ✅ Use FileVault to encrypt credentials at rest
- ✅ Rotate access keys regularly (every 90 days)
- ✅ Use environment variables or `.env` for temporary credentials
- ✅ Add `.env` and `credentials` to `.gitignore`

**DO NOT:**
- ❌ Never commit credentials to git
- ❌ Never share credentials via Slack/email
- ❌ Never store credentials in code
- ❌ Never use root account credentials (use IAM user)
- ❌ Never set 644 or 777 permissions on credentials file

**Check if credentials are in git history:**
```bash
# Search git history for AWS keys
git log -p -S "AWS_ACCESS_KEY" | head -20

# Search for credentials file
git log --all --full-history -- ~/.aws/credentials
```

**If credentials were committed (IMMEDIATE ACTION REQUIRED):**
1. Rotate AWS access keys immediately (delete old, create new)
2. Update `~/.aws/credentials` with new keys
3. Remove from git history using `git filter-branch` or BFG Repo-Cleaner
4. Force push to remote (if already pushed)

---

### Security Settings Summary Table

**Update after running security checklist:**

| Setting | Status | Impact | Last Checked | Action Needed |
|---------|--------|--------|--------------|---------------|
| SIP (System Integrity Protection) | Enabled | ✅ Protects system | TBD | None - keep enabled |
| FileVault (Disk Encryption) | TBD | 🔐 Encrypts data | TBD | Run `fdesetup status` |
| Gatekeeper (App Verification) | Enabled | ✅ Prevents malware | TBD | None - keep enabled |
| Firewall | TBD | 🔥 Blocks incoming | TBD | Run firewall check |
| Full Disk Access (Terminal) | TBD | 📂 File access | TBD | Grant if needed |
| SSH Key Permissions | TBD | 🔑 GitHub auth | TBD | Run `ls -l ~/.ssh/` |
| AWS Credentials Permissions | TBD | 🔐 AWS auth | TBD | Run `ls -l ~/.aws/credentials` |
| Developer Tools | Installed | 🛠️ Git and compilers | TBD | Run `xcode-select -p` |

### Security Checklist Script

**Run at start of session to verify security settings:**
```bash
echo "=== SECURITY SETTINGS ==="
echo ""

echo "1. System Integrity Protection:"
csrutil status
echo ""

echo "2. FileVault (Disk Encryption):"
fdesetup status
echo ""

echo "3. Gatekeeper (App Verification):"
spctl --status
echo ""

echo "4. Firewall:"
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
echo ""

echo "5. SSH Key Permissions:"
ls -l ~/.ssh/id_* 2>/dev/null | head -2
echo ""

echo "6. AWS Credentials Permissions:"
ls -l ~/.aws/credentials 2>/dev/null
echo ""

echo "7. Developer Tools:"
xcode-select -p 2>/dev/null && echo "✅ Installed" || echo "❌ Not installed"
echo ""

echo "8. GitHub SSH Authentication:"
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" && echo "✅ Working" || echo "❌ Failed"
echo ""
```

---

## Performance Baselines

**Purpose:** Document expected performance metrics for common operations to identify performance degradation and optimize workflows.

### Hardware Performance Benchmarks

**CPU (Apple M2 Max):**
- **Cores:** 12-core (8 performance + 4 efficiency)
- **Max Turbo Frequency:** ~3.5 GHz
- **Single-core performance:** Excellent for sequential operations
- **Multi-core performance:** Excellent for parallel processing (10-12 workers optimal)

**Memory:**
- **Total:** 96 GB unified memory
- **Architecture:** Unified memory (CPU/GPU share)
- **Bandwidth:** ~400 GB/s
- **Typical usage:** 10-20 GB for this project (ample headroom)

**Storage (NVMe SSD):**
- **Sequential read:** 5,000-7,000 MB/s
- **Sequential write:** 5,000-6,000 MB/s
- **Random IOPS:** 100,000-150,000 (4K blocks)

### Project-Specific Performance Baselines

#### S3 Operations (Network-Bound)

**S3 Upload Performance:**
```bash
# Test upload speed (100 MB file)
time dd if=/dev/zero bs=1M count=100 | aws s3 cp - s3://nba-sim-raw-data-lake/test-upload.bin
```

**Expected performance:**
- **Residential internet (20 MB/s upload):** ~5-6 seconds for 100 MB
- **Fast internet (50 MB/s upload):** ~2-3 seconds for 100 MB
- **Gigabit internet (100 MB/s upload):** ~1-2 seconds for 100 MB

**S3 Download Performance:**
```bash
# Test download speed
time aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json /tmp/test.json
```

**Expected performance:**
- **Single file (~700 KB):** <500 ms
- **1,000 files (~700 MB):** 30-60 seconds (network dependent)
- **10,000 files (~7 GB):** 5-10 minutes (network dependent)

**S3 List Operations:**
```bash
# List bucket contents (146,115 files)
time aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l
```

**Expected performance:**
- **Full listing (146,115 files):** 10-30 seconds
- **Filtered listing (one folder):** 3-8 seconds

#### Local File Operations (I/O-Bound)

**File Enumeration:**
```bash
# Count files in data directory
time find /Users/ryanranft/0espn/data/nba -type f | wc -l
```

**Expected performance:**
- **146,115 files:** 30-60 seconds
- **Optimization:** Use `ls -R` or `fd` for faster enumeration

**Sequential File Reading:**
```bash
# Read 1,000 JSON files sequentially
time for i in {1..1000}; do cat /Users/ryanranft/0espn/data/nba/nba_box_score/*.json > /dev/null; done
```

**Expected performance:**
- **1,000 files (~700 MB):** 5-10 seconds
- **Per-file average:** ~5-10 ms

**Parallel File Reading:**
```bash
# Read files in parallel (4 workers)
time find /Users/ryanranft/0espn/data/nba/nba_box_score -name "*.json" | head -1000 | xargs -P 4 cat > /dev/null
```

**Expected performance:**
- **1,000 files (4 workers):** 2-4 seconds (2-3x faster than sequential)
- **Optimal worker count:** 8-12 (matches CPU cores)

#### Python Operations (CPU/Memory-Bound)

**JSON Parsing (pandas):**
```python
import pandas as pd
import time

start = time.time()
df = pd.read_json('/Users/ryanranft/0espn/data/nba/nba_box_score/131105001.json')
elapsed = time.time() - start
print(f"Parse time: {elapsed:.3f} seconds")
```

**Expected performance:**
- **Single JSON file (~700 KB):** 50-100 ms
- **1,000 files:** 50-100 seconds (sequential)
- **1,000 files (multiprocessing):** 10-20 seconds (8 workers)

**DataFrame Operations:**
```python
import pandas as pd
import numpy as np

# Create sample DataFrame (1M rows)
df = pd.DataFrame({
    'player_id': np.random.randint(1, 500, 1_000_000),
    'points': np.random.randint(0, 50, 1_000_000),
    'rebounds': np.random.randint(0, 20, 1_000_000)
})

# Benchmark operations
%timeit df.groupby('player_id')['points'].mean()
%timeit df[df['points'] > 20]
%timeit df.sort_values('points')
```

**Expected performance (1M rows):**
- **GroupBy aggregation:** 20-50 ms
- **Filtering:** 5-10 ms
- **Sorting:** 50-100 ms
- **Memory usage:** ~50-100 MB for 1M rows

**Database Operations (RDS - Network-Bound):**

**Connection establishment:**
```python
import psycopg2
import time

start = time.time()
conn = psycopg2.connect(
    host="nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com",
    database="nba_simulator",
    user="postgres",
    password="xxx"
)
elapsed = time.time() - start
print(f"Connection time: {elapsed:.3f} seconds")
```

**Expected performance:**
- **First connection:** 200-500 ms (includes DNS lookup)
- **Subsequent connections (with pooling):** 50-100 ms

**Query performance:**
```sql
-- Simple SELECT (1,000 rows)
SELECT * FROM player_game_stats LIMIT 1000;
-- Expected: 50-100 ms

-- Aggregation (100K rows)
SELECT player_id, AVG(points) FROM player_game_stats GROUP BY player_id;
-- Expected: 200-500 ms

-- Join operation (10K rows)
SELECT g.*, pgs.* FROM games g
JOIN player_game_stats pgs ON g.game_id = pgs.game_id
LIMIT 10000;
-- Expected: 100-300 ms
```

**Bulk insert performance:**
```python
# Insert 10,000 rows
# Expected: 5-10 seconds (single transaction)
# Optimized (COPY): 1-2 seconds
```

#### AWS Glue Jobs (Future Baseline)

**ETL Job Performance (when implemented):**

**Expected timings for 146,115 JSON files:**
- **Crawler discovery:** 10-30 minutes (one-time)
- **ETL job (10% extraction):** 30-60 minutes
  - Reading from S3: 10-15 minutes
  - Processing: 10-20 minutes
  - Writing to RDS: 10-25 minutes
- **DPU (Data Processing Units):** 2-10 DPUs recommended
- **Cost:** ~$0.44/DPU-hour

#### Python Package Operations

**Package Installation:**
```bash
# Install all requirements
time pip install -r requirements.txt
```

**Expected performance:**
- **Fresh install (14 packages + deps):** 2-5 minutes
- **Reinstall (cached):** 10-30 seconds
- **Single package (boto3):** 5-10 seconds

**Package Import Times:**
```python
import time

# Measure import time
start = time.time()
import boto3
print(f"boto3: {(time.time() - start)*1000:.1f} ms")

start = time.time()
import pandas as pd
print(f"pandas: {(time.time() - start)*1000:.1f} ms")

start = time.time()
import numpy as np
print(f"numpy: {(time.time() - start)*1000:.1f} ms")
```

**Expected import times:**
- **boto3:** 100-200 ms
- **pandas:** 300-500 ms
- **numpy:** 50-100 ms
- **psycopg2:** 20-50 ms
- **Total (all core packages):** 500-800 ms

### Performance Monitoring Tools

**System-wide monitoring:**
```bash
# CPU usage
top -l 1 | grep "CPU usage"

# Memory usage
vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//' | awk '{print $1*4096/1024/1024 " MB"}'

# Disk I/O
iostat -d disk0 1 1

# Network activity (requires nettop)
nettop -x -P -L 1 -t wifi
```

**Python profiling:**
```python
# Time a function
import time
start = time.time()
result = my_function()
print(f"Elapsed: {time.time() - start:.3f}s")

# Profile with cProfile
import cProfile
cProfile.run('my_function()')

# Memory profiling
from memory_profiler import profile
@profile
def my_function():
    # function code
```

**AWS operations monitoring:**
```bash
# S3 transfer speed
aws s3 cp file.txt s3://bucket/ --debug 2>&1 | grep "bytes/sec"

# RDS connection latency
time aws rds describe-db-instances --db-instance-identifier nba-sim-db
```

### Performance Optimization Guidelines

**For large file operations (146K files):**
1. **Use multiprocessing:** 8-12 workers optimal for M2 Max
2. **Batch operations:** Process files in chunks of 1,000-10,000
3. **Use generators:** Avoid loading all files into memory
4. **Cache results:** Store intermediate results to avoid reprocessing

**For data processing:**
1. **Use pandas efficiently:** Avoid iterrows(), use vectorized operations
2. **Chunk large datasets:** Process in 100K-1M row chunks
3. **Use appropriate dtypes:** int32 instead of int64 when possible
4. **Filter early:** Reduce data before complex operations

**For AWS operations:**
1. **Use S3 Transfer Acceleration:** For large uploads (>1 GB)
2. **Parallel S3 operations:** Use boto3 with ThreadPoolExecutor
3. **Connection pooling:** Reuse RDS connections
4. **Batch AWS API calls:** Reduce request overhead

**For database operations:**
1. **Use COPY for bulk inserts:** 10-20x faster than INSERT
2. **Create indexes:** After initial data load, not during
3. **Use connection pooling:** SQLAlchemy or pgbouncer
4. **Batch transactions:** Commit every 10K-100K rows

### Performance Degradation Indicators

**Monitor these metrics to identify performance issues:**

**Slower than expected:**
- **S3 operations >2x baseline:** Check network speed, VPN, AWS region
- **File operations >2x baseline:** Check disk space (>10% free), APFS snapshots, Spotlight indexing
- **Python operations >2x baseline:** Check memory usage (swap), CPU throttling (thermal), other processes

**Memory issues:**
- **Swap usage increasing:** Reduce chunk sizes, use generators
- **Memory not released:** Check for memory leaks, circular references
- **OOM errors:** Reduce batch sizes, use chunking

**Disk issues:**
- **High disk usage (>90%):** Free space, cleanup APFS snapshots
- **Slow I/O:** Check Activity Monitor → Disk, other processes

**Network issues:**
- **High latency to AWS:** Check VPN, internet connection, DNS
- **Slow S3 operations:** Check upload/download bandwidth, S3 Transfer Acceleration

### Performance Baseline Tracking

**Record baselines after major changes:**

| Operation | Baseline | Current | Date Measured | Notes |
|-----------|----------|---------|---------------|-------|
| S3 list (146K files) | 15s | TBD | - | Run `time aws s3 ls --recursive` |
| Read 1000 JSON files | 8s | TBD | - | Sequential read benchmark |
| Pandas read_json (1 file) | 75ms | TBD | - | Single file parse time |
| RDS connection | 300ms | TBD | - | First connection time |
| pip install requirements | 3min | TBD | - | Fresh install, no cache |
| Import boto3+pandas+numpy | 600ms | TBD | - | Combined import time |

### Performance Testing Scripts

**Create performance test suite:**
```bash
# Create scripts/performance/benchmark.py
```

**Run benchmarks periodically:**
```bash
# Weekly or after major changes
python scripts/performance/benchmark.py > performance_report.txt

# Compare with previous runs
diff performance_report_old.txt performance_report.txt
```

**Track performance over time:**
- Commit benchmark results to git (weekly)
- Plot trends to identify degradation
- Investigate significant changes (>20% slower)

### Expected Operation Times Summary

**Quick reference for common operations:**

| Operation | Size | Expected Time | Bottleneck |
|-----------|------|---------------|------------|
| S3 upload | 100 MB | 2-5s | Network |
| S3 download | 100 MB | 1-3s | Network |
| S3 list | 146K files | 15-30s | Network/API |
| Local file read | 1000 files | 5-10s | Disk I/O |
| JSON parse (pandas) | 1 file | 50-100ms | CPU |
| DataFrame groupby | 1M rows | 20-50ms | CPU |
| RDS query | 10K rows | 100-300ms | Network |
| RDS bulk insert | 10K rows | 5-10s | Network |
| Glue ETL | 146K files | 30-60min | AWS compute |
| pip install | 14 packages | 2-5min | Network |

---

## Troubleshooting

### Miniconda Not Found
```bash
# Check if conda is in PATH
echo $PATH | grep conda

# If not found, add to PATH (zsh)
echo 'export PATH="/Users/ryanranft/miniconda3/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Homebrew Command Not Found
```bash
# Add Homebrew to PATH (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
source ~/.zprofile
```

### AWS CLI Not Found After Conda Activation
This is expected and correct! AWS CLI should be system-wide, not in conda.

---

## Shell Configuration Files

**Purpose:** Document shell configuration files, their purpose, and relevant settings for this project.

### Shell Environment Overview

**Active Shell:** zsh (macOS default since Catalina)
**Shell Location:** `/bin/zsh`
**Configuration Files:** `.zshrc`, `.zprofile`, `.zshenv`

### Configuration File Hierarchy

**Load order (zsh):**
1. **`.zshenv`** - Always sourced (login + non-login shells)
   - Use for: Essential environment variables
   - Example: LANG, EDITOR
2. **`.zprofile`** - Sourced for login shells only
   - Use for: PATH setup, environment initialization
   - Example: Homebrew initialization
3. **`.zshrc`** - Sourced for interactive shells
   - Use for: Aliases, functions, prompts, key bindings
   - Example: Conda initialization, custom aliases

**Execution frequency:**
- **Every shell:** `.zshenv`
- **Login (first terminal):** `.zshenv` → `.zprofile` → `.zshrc`
- **New tab/window:** `.zshenv` → `.zshrc`

### Check Existing Configuration Files

**List all shell config files:**
```bash
ls -la ~ | grep -E "^\\.zsh|^\\.bash"
```

**Expected files:**
```
.zshenv    # Global environment variables
.zprofile  # Login shell setup (PATH, Homebrew)
.zshrc     # Interactive shell config (conda, aliases)
.zsh_history  # Command history
```

**View file sizes:**
```bash
wc -l ~/.zshrc ~/.zprofile ~/.zshenv 2>/dev/null
```

### Critical Configuration Sections

#### ~/.zprofile - Homebrew Initialization

**Check if Homebrew is initialized:**
```bash
grep -n "homebrew" ~/.zprofile
```

**Expected content:**
```bash
# Homebrew (Apple Silicon)
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**What this does:**
- Adds `/opt/homebrew/bin` to PATH
- Sets HOMEBREW_PREFIX, HOMEBREW_CELLAR, HOMEBREW_REPOSITORY
- Enables Homebrew completion

**Verify Homebrew environment:**
```bash
source ~/.zprofile
echo $HOMEBREW_PREFIX
# Expected: /opt/homebrew
```

**If missing, add:**
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
source ~/.zprofile
```

#### ~/.zshrc - Conda Initialization

**Check if Conda is initialized:**
```bash
grep -n "conda initialize" ~/.zshrc
```

**Expected content:**
```bash
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/ryanranft/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/ryanranft/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/Users/ryanranft/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/ryanranft/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
```

**What this does:**
- Adds conda to PATH
- Enables `conda activate` command
- Sets up conda shell integration

**If missing, initialize:**
```bash
/Users/ryanranft/miniconda3/bin/conda init zsh
source ~/.zshrc
```

### Recommended Project-Specific Additions

#### Add Project Aliases

**Edit ~/.zshrc:**
```bash
# Add at end of file
nano ~/.zshrc
```

**Recommended aliases for this project:**
```bash
# NBA Simulator Project Aliases

# Quick navigation
alias nba='cd /Users/ryanranft/nba-simulator-aws'
alias nbaenv='conda activate nba-aws'

# Conda environment shortcuts
alias ca='conda activate nba-aws'
alias cda='conda deactivate'

# AWS shortcuts
alias s3ls='aws s3 ls s3://nba-sim-raw-data-lake/'
alias s3sync='aws s3 sync'

# Git shortcuts
alias gs='git status'
alias gp='git pull'
alias gc='git commit'
alias glog='git log --oneline --graph --decorate -20'

# Python shortcuts
alias py='python'
alias ipy='ipython'
alias jn='jupyter notebook'

# Project maintenance
alias nbacosts='bash /Users/ryanranft/nba-simulator-aws/scripts/aws/check_costs.sh'
alias nbadocs='bash /Users/ryanranft/nba-simulator-aws/scripts/maintenance/update_docs.sh'

# Quick verification
alias nbacheck='make -C /Users/ryanranft/nba-simulator-aws verify-all'
```

**Apply changes:**
```bash
source ~/.zshrc
```

#### Add Project Functions

**Add to ~/.zshrc:**
```bash
# NBA Simulator Project Functions

# Quick project setup
nbasetup() {
    cd /Users/ryanranft/nba-simulator-aws
    conda activate nba-aws
    echo "✅ Environment: nba-aws"
    echo "✅ Directory: $(pwd)"
    echo "✅ Python: $(python --version)"
}

# Run session startup checklist
nbastart() {
    echo "=== NBA Simulator Session Startup ==="
    echo ""
    cd /Users/ryanranft/nba-simulator-aws
    conda activate nba-aws

    echo "Environment: nba-aws"
    echo "Python: $(python --version)"
    echo "AWS CLI: $(aws --version)"
    echo ""

    echo "Would you like to run full verification? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        make verify-all
    fi
}

# Quick S3 file count
s3count() {
    echo "Counting files in S3 bucket..."
    aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l
}

# Check AWS costs quickly
awscosts() {
    bash /Users/ryanranft/nba-simulator-aws/scripts/aws/check_costs.sh
}
```

#### Add Custom Prompt (Optional)

**Add to ~/.zshrc to show conda env in prompt:**
```bash
# Custom prompt with conda environment
setopt PROMPT_SUBST
PROMPT='%F{green}[%n@%m]%f %F{blue}%~%f ${CONDA_DEFAULT_ENV:+%F{yellow}($CONDA_DEFAULT_ENV)%f }%# '
```

**Result:**
```
[ryanranft@MacBook-Pro] ~/nba-simulator-aws (nba-aws) %
```

### Environment Variable Exports

**Add to ~/.zprofile or ~/.zshenv:**
```bash
# Project-specific environment variables
export NBA_PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
export NBA_DATA_ROOT="/Users/ryanranft/0espn/data/nba"
export NBA_S3_BUCKET="s3://nba-sim-raw-data-lake"

# Python settings
export PYTHONDONTWRITEBYTECODE=1  # Don't create .pyc files
export PYTHONUNBUFFERED=1         # Force unbuffered output

# AWS settings (optional - use aws configure instead)
# export AWS_DEFAULT_REGION=us-east-1
# export AWS_PROFILE=default
```

### PATH Configuration

**Current PATH (when nba-aws activated):**
```bash
echo $PATH | tr ':' '\n' | nl
```

**Expected order:**
```
1. /Users/ryanranft/miniconda3/envs/nba-aws/bin    # Conda env (FIRST)
2. /Users/ryanranft/miniconda3/condabin            # Conda base
3. /opt/homebrew/bin                                # Homebrew
4. /opt/homebrew/sbin                               # Homebrew sbin
5. /usr/local/bin                                   # Local binaries
6. /usr/bin                                         # System binaries
7. /bin                                             # Essential binaries
8. /usr/sbin                                        # System admin
9. /sbin                                            # Essential admin
```

**Verify PATH order:**
```bash
# Should show conda environment first
which python
# Expected: /Users/ryanranft/miniconda3/envs/nba-aws/bin/python

# Should show Homebrew
which aws
# Expected: /opt/homebrew/bin/aws
```

### Shell History Configuration

**Add to ~/.zshrc for better history:**
```bash
# History settings
HISTSIZE=10000              # Lines in memory
SAVEHIST=10000              # Lines saved to file
HISTFILE=~/.zsh_history     # History file location
setopt HIST_IGNORE_DUPS     # Don't record duplicates
setopt HIST_FIND_NO_DUPS    # Don't show duplicates in search
setopt HIST_IGNORE_SPACE    # Ignore commands starting with space
setopt SHARE_HISTORY        # Share history between sessions
```

**Search history:**
```bash
# Search backwards
Ctrl-R

# Search for specific command
history | grep "aws s3"

# Re-run last command
!!

# Re-run command 50
!50
```

### Completion Configuration

**Add to ~/.zshrc for better tab completion:**
```bash
# Enable completion
autoload -Uz compinit
compinit

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'

# Menu selection
zstyle ':completion:*' menu select

# AWS CLI completion (if not auto-loaded)
complete -C '/opt/homebrew/bin/aws_completer' aws
```

### Key Bindings

**Add to ~/.zshrc for useful shortcuts:**
```bash
# Key bindings
bindkey '^[[A' history-beginning-search-backward  # Up arrow
bindkey '^[[B' history-beginning-search-forward   # Down arrow
bindkey '^[[H' beginning-of-line                  # Home
bindkey '^[[F' end-of-line                        # End
bindkey '^[[3~' delete-char                       # Delete
```

### Shell Configuration Backup

**Backup current configuration:**
```bash
# Create backup directory
mkdir -p ~/.config/shell-backups

# Backup with timestamp
cp ~/.zshrc ~/.config/shell-backups/.zshrc.$(date +%Y%m%d)
cp ~/.zprofile ~/.config/shell-backups/.zprofile.$(date +%Y%m%d)
cp ~/.zshenv ~/.config/shell-backups/.zshenv.$(date +%Y%m%d) 2>/dev/null

echo "Backed up shell configuration files"
```

**Restore from backup:**
```bash
# List available backups
ls -la ~/.config/shell-backups/

# Restore specific backup
cp ~/.config/shell-backups/.zshrc.20251001 ~/.zshrc
source ~/.zshrc
```

### Verify Shell Configuration

**Check for syntax errors:**
```bash
# Test .zshrc for errors
zsh -n ~/.zshrc
# No output = no syntax errors

# Test .zprofile for errors
zsh -n ~/.zprofile
# No output = no syntax errors
```

**Reload configuration:**
```bash
# Reload .zshrc
source ~/.zshrc

# Reload .zprofile
source ~/.zprofile

# Or restart shell
exec zsh
```

**Check what's being loaded:**
```bash
# Show all sourced files
zsh -x -c "exit" 2>&1 | grep -E "\.zsh|profile|rc"
```

### Shell Configuration Checklist

**Verify essential configurations:**
```bash
# 1. Check Homebrew initialization
grep -q "homebrew" ~/.zprofile && echo "✅ Homebrew" || echo "❌ Missing Homebrew"

# 2. Check Conda initialization
grep -q "conda initialize" ~/.zshrc && echo "✅ Conda" || echo "❌ Missing Conda"

# 3. Check PATH order
[[ $(which python) == "/Users/ryanranft/miniconda3/envs/nba-aws/bin/python" ]] && echo "✅ PATH order correct" || echo "❌ PATH order incorrect"

# 4. Check aliases exist
type nba &>/dev/null && echo "✅ Project aliases" || echo "❌ No project aliases"

# 5. Check history settings
[[ $HISTSIZE -ge 10000 ]] && echo "✅ History configured" || echo "❌ History not configured"
```

### Shell Configuration Best Practices

**DO:**
- ✅ Keep configuration files organized and commented
- ✅ Backup before making changes
- ✅ Test changes in new shell before committing
- ✅ Use `.zprofile` for PATH and environment setup
- ✅ Use `.zshrc` for aliases, functions, and prompts
- ✅ Source files after changes to apply immediately

**DO NOT:**
- ❌ Don't put slow commands in startup files (delays shell start)
- ❌ Don't export sensitive credentials in config files
- ❌ Don't modify Conda initialization block manually
- ❌ Don't use conflicting aliases (e.g., `cd` override)
- ❌ Don't add duplicate PATH entries

### Common Shell Configuration Issues

**Issue 1: Conda activate not working**
```bash
# Problem: "conda: command not found"
# Solution: Re-initialize conda
/Users/ryanranft/miniconda3/bin/conda init zsh
source ~/.zshrc
```

**Issue 2: AWS CLI not found**
```bash
# Problem: "aws: command not found" after conda activate
# Solution: Ensure Homebrew is in PATH
grep "homebrew" ~/.zprofile
# If missing, add Homebrew initialization
```

**Issue 3: Aliases not working**
```bash
# Problem: "command not found" for custom alias
# Solution: Check if .zshrc is being sourced
echo "test" >> ~/.zshrc  # Add test line
exec zsh                  # Restart shell
grep "test" ~/.zshrc      # Verify file is correct
```

**Issue 4: Slow shell startup**
```bash
# Problem: Shell takes >2 seconds to start
# Diagnosis: Time shell startup
time zsh -i -c exit

# Common culprits:
# - nvm (Node Version Manager) - very slow
# - Complex prompt calculations
# - Network calls in startup files

# Solution: Move slow operations to functions, call manually
```

### Shell Configuration Templates

**Minimal ~/.zshrc for this project:**
```bash
# Homebrew (loaded from .zprofile)
# Conda initialization (auto-generated)

# >>> conda initialize >>>
# ... (conda init block)
# <<< conda initialize <<<

# Project aliases
alias nba='cd /Users/ryanranft/nba-simulator-aws'
alias ca='conda activate nba-aws'

# History
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY
```

**Minimal ~/.zprofile for this project:**
```bash
# Homebrew
eval "$(/opt/homebrew/bin/brew shellenv)"

# Project environment variables
export NBA_PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
```

### Verification Script

**Create shell config verification script:**
```bash
#!/bin/zsh
# Save as: scripts/shell/verify_shell_config.sh

echo "=== SHELL CONFIGURATION VERIFICATION ==="
echo ""

echo "1. Active Shell:"
echo $SHELL
echo ""

echo "2. Configuration Files:"
ls -l ~/.zshrc ~/.zprofile ~/.zshenv 2>/dev/null
echo ""

echo "3. Homebrew:"
grep -q "homebrew" ~/.zprofile && echo "✅ Initialized" || echo "❌ Not initialized"
echo ""

echo "4. Conda:"
grep -q "conda initialize" ~/.zshrc && echo "✅ Initialized" || echo "❌ Not initialized"
echo ""

echo "5. PATH Order:"
which python
which aws
which conda
echo ""

echo "6. Aliases:"
type nba 2>/dev/null && echo "✅ Project aliases exist" || echo "⚠️ No project aliases"
echo ""

echo "7. History Settings:"
echo "HISTSIZE: $HISTSIZE"
echo "SAVEHIST: $SAVEHIST"
echo ""
```

**Run verification:**
```bash
chmod +x scripts/shell/verify_shell_config.sh
./scripts/shell/verify_shell_config.sh
```

---

## Installed System Tools

**Purpose:** Document system-level CLI tools installed on this machine that may be used for this project.

### Essential System Tools (Pre-installed on macOS)

**Built-in macOS tools:**

#### Core Utilities
```bash
# Check if tools are available
which bash zsh sh curl wget grep sed awk find xargs tar gzip ssh git
```

**Essential tools included with macOS:**
- **bash** - `/bin/bash` (Bourne Again Shell, legacy)
- **zsh** - `/bin/zsh` (Current default shell)
- **curl** - `/usr/bin/curl` (HTTP client)
- **grep** - `/usr/bin/grep` (Pattern matching)
- **sed** - `/usr/bin/sed` (Stream editor)
- **awk** - `/usr/bin/awk` (Text processing)
- **find** - `/usr/bin/find` (File search)
- **xargs** - `/usr/bin/xargs` (Command builder)
- **tar** - `/usr/bin/tar` (Archive tool)
- **gzip** - `/usr/bin/gzip` (Compression)
- **ssh** - `/usr/bin/ssh` (Secure shell)
- **git** - `/usr/bin/git` (Version control)

#### Network Tools
```bash
# Check network tools
which ping traceroute netstat nslookup dig ifconfig nc telnet
```

**Network diagnostics:**
- **ping** - `/sbin/ping` (Network connectivity test)
- **traceroute** - `/usr/sbin/traceroute` (Route tracing)
- **netstat** - `/usr/sbin/netstat` (Network statistics)
- **nslookup** - `/usr/bin/nslookup` (DNS lookup)
- **dig** - `/usr/bin/dig` (DNS query tool)
- **ifconfig** - `/sbin/ifconfig` (Network interface config)
- **nc** - `/usr/bin/nc` (Netcat - network utility)
- **telnet** - `/usr/bin/telnet` (Remote connection)

#### System Monitoring
```bash
# Check monitoring tools
which top ps df du iostat vm_stat
```

**System monitoring tools:**
- **top** - `/usr/bin/top` (Process monitor)
- **ps** - `/bin/ps` (Process status)
- **df** - `/bin/df` (Disk free space)
- **du** - `/usr/bin/du` (Disk usage)
- **iostat** - `/usr/sbin/iostat` (I/O statistics)
- **vm_stat** - `/usr/bin/vm_stat` (Virtual memory stats)

### Homebrew-Installed Tools

**Check Homebrew-managed tools:**
```bash
brew list
```

**Expected Homebrew packages for this project:**
- **awscli** (AWS Command Line Interface)
- **git** (may be Homebrew version if upgraded from system git)

**Useful Homebrew tools to install (optional):**

#### Enhanced CLI Tools
```bash
# Modern replacements for traditional tools (optional)
brew install fd        # Modern 'find' alternative
brew install ripgrep   # Modern 'grep' alternative (rg)
brew install bat       # Modern 'cat' with syntax highlighting
brew install exa       # Modern 'ls' alternative
brew install htop      # Modern 'top' alternative
brew install tree      # Directory tree viewer
```

**Why these are useful:**
- **fd** - Faster file search than `find`, respects .gitignore
- **ripgrep (rg)** - 10-100x faster than `grep` for code search
- **bat** - Syntax-highlighted file viewer
- **exa** - Better ls with git integration
- **htop** - Interactive process viewer
- **tree** - Visual directory structure

#### JSON Processing
```bash
# JSON manipulation tools
brew install jq        # JSON processor (highly recommended)
brew install yq        # YAML processor
```

**jq usage examples:**
```bash
# Pretty print JSON
cat file.json | jq '.'

# Extract specific fields
aws s3api list-buckets | jq '.Buckets[].Name'

# Filter NBA data
cat 131105001.json | jq '.boxscore.teams'
```

#### Database Tools
```bash
# PostgreSQL client (for RDS)
brew install postgresql  # Installs psql client
```

**psql verification:**
```bash
which psql
# Expected: /opt/homebrew/bin/psql (if installed via Homebrew)
# Or: /usr/bin/psql (if installed via macOS)
```

#### Performance Testing
```bash
# Network speed testing
brew install speedtest-cli

# HTTP benchmarking
brew install apache-bench  # ab tool
brew install wrk           # Modern HTTP benchmark tool
```

### Python-Based CLI Tools

**Tools installed via pip (in conda environment):**

#### AWS Tools
```bash
# AWS Session Manager plugin (if needed)
brew install --cask session-manager-plugin
```

#### Data Tools
```bash
# CSV processing
pip install csvkit  # CSV manipulation tools

# Usage:
csvstat data.csv        # Statistics
csvcut -c 1,2 data.csv  # Select columns
csvsql data.csv         # SQL on CSV
```

### Version Control Tools

**Git (already installed):**
```bash
git --version
which git
```

**Expected output:**
- `/usr/bin/git` (macOS system git)
- OR `/opt/homebrew/bin/git` (Homebrew git)

**Git configuration:**
```bash
# View git config
git config --list --show-origin

# Essential git settings
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Useful git aliases (add to ~/.gitconfig):**
```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    last = log -1 HEAD
    unstage = reset HEAD --
    visual = log --oneline --graph --decorate
```

### Compression Tools

**Check compression tools:**
```bash
which gzip gunzip zip unzip tar bzip2 xz
```

**Compression tool usage:**
```bash
# gzip (best for streaming)
gzip file.txt
gunzip file.txt.gz

# zip (cross-platform)
zip archive.zip file1.txt file2.txt
unzip archive.zip

# tar with gzip (archives + compression)
tar -czf archive.tar.gz directory/
tar -xzf archive.tar.gz

# xz (best compression ratio)
xz file.txt
xz -d file.txt.xz
```

**For this project:**
- Use `gzip` for compressing large JSON files if needed
- Use `tar.gz` for backing up directories
- AWS S3 supports gzip compression (transparent)

### Text Processing Tools

**Check text tools:**
```bash
which cat less more head tail grep sed awk cut paste sort uniq wc
```

**Common text operations for this project:**

**View JSON files:**
```bash
# First 50 lines
head -50 /Users/ryanranft/0espn/data/nba/nba_box_score/131105001.json

# Last 50 lines
tail -50 file.json

# Interactive viewer (less)
less file.json
# Use /pattern to search, q to quit
```

**Count lines, words, files:**
```bash
# Count lines in file
wc -l file.json

# Count files in directory
ls -1 /Users/ryanranft/0espn/data/nba/nba_box_score | wc -l

# Count total lines in all JSON files
find /Users/ryanranft/0espn/data/nba -name "*.json" -exec wc -l {} + | tail -1
```

**Search and filter:**
```bash
# Search for pattern
grep "player_id" file.json

# Case-insensitive search
grep -i "lebron" file.json

# Count matches
grep -c "player" file.json

# Show context (5 lines before/after)
grep -C 5 "score" file.json
```

### File Management Tools

**Check file tools:**
```bash
which cp mv rm mkdir rmdir ln chmod chown stat
```

**Useful file operations:**
```bash
# Copy with progress
rsync -avh --progress source/ destination/

# Find large files
du -sh /Users/ryanranft/0espn/data/nba/*
find /Users/ryanranft/0espn/data/nba -size +10M -ls

# Check file type
file /Users/ryanranft/0espn/data/nba/nba_box_score/131105001.json
# Expected: JSON data

# Get detailed file info
stat -f "%N: %z bytes, modified %Sm" file.json
```

### Development Tools

**Check development tools:**
```bash
which make gcc clang python python3 pip pip3 ruby gem node npm
```

**Make (build automation):**
```bash
make --version
which make
# Expected: /usr/bin/make
```

**Usage in this project:**
```bash
cd /Users/ryanranft/nba-simulator-aws
make help        # Show available commands
make verify-all  # Run all checks
make inventory   # Update file inventory
```

**Command Line Developer Tools:**
```bash
# Check if installed
xcode-select -p

# Expected: /Library/Developer/CommandLineTools

# If not installed:
xcode-select --install
```

**Includes:**
- gcc, clang (C/C++ compilers)
- make (build tool)
- git (version control)
- Headers for compiling Python packages

### Database CLI Tools

**PostgreSQL Client (psql):**

**Check if installed:**
```bash
which psql
psql --version
```

**Install if missing:**
```bash
# Option 1: Homebrew (recommended)
brew install postgresql

# Option 2: Standalone psql
brew install libpq
echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zprofile
```

**Usage for RDS:**
```bash
# Connect to RDS (when available)
psql -h nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d nba_simulator

# Run query from command line
psql -h hostname -U user -d database -c "SELECT COUNT(*) FROM games;"

# Execute SQL file
psql -h hostname -U user -d database -f script.sql
```

### Useful Optional Tools

**Highly recommended for data projects:**

#### tmux (Terminal Multiplexer)
```bash
brew install tmux
```

**Why useful:**
- Run multiple commands in split panes
- Sessions persist if SSH disconnects
- Monitor long-running processes

**Basic tmux usage:**
```bash
tmux new -s nba           # New session
tmux attach -t nba        # Attach to session
Ctrl-b %                  # Split vertically
Ctrl-b "                  # Split horizontally
Ctrl-b d                  # Detach session
```

#### watch (Repeat command)
```bash
brew install watch
```

**Usage:**
```bash
# Monitor S3 file count
watch -n 60 'aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l'

# Monitor AWS costs
watch -n 300 'bash scripts/aws/check_costs.sh'
```

#### nettop (Network monitoring)
```bash
# Built into macOS
nettop -m tcp
```

**Monitor network during S3 operations.**

### Tool Installation Verification Script

**Create tool verification script:**
```bash
#!/bin/zsh
# Save as: scripts/shell/verify_system_tools.sh

echo "=== SYSTEM TOOLS VERIFICATION ==="
echo ""

echo "Core Utilities:"
for tool in bash zsh curl grep sed awk find xargs tar gzip ssh git; do
    if command -v $tool &> /dev/null; then
        echo "✅ $tool: $(which $tool)"
    else
        echo "❌ $tool: NOT FOUND"
    fi
done
echo ""

echo "Homebrew Packages:"
for tool in aws jq; do
    if command -v $tool &> /dev/null; then
        echo "✅ $tool: $(which $tool)"
    else
        echo "⚠️  $tool: NOT INSTALLED (optional)"
    fi
done
echo ""

echo "Database Tools:"
if command -v psql &> /dev/null; then
    echo "✅ psql: $(which psql) - $(psql --version)"
else
    echo "⚠️  psql: NOT INSTALLED (needed for RDS)"
fi
echo ""

echo "Development Tools:"
xcode-select -p &> /dev/null && echo "✅ Command Line Tools: $(xcode-select -p)" || echo "❌ Command Line Tools: NOT INSTALLED"
echo ""
```

**Run verification:**
```bash
chmod +x scripts/shell/verify_system_tools.sh
./scripts/shell/verify_system_tools.sh
```

### System Tools Summary

**Essential for this project:**
- ✅ **AWS CLI** - Installed via Homebrew (`/opt/homebrew/bin/aws`)
- ✅ **Git** - Installed (system or Homebrew)
- ✅ **Python 3.11** - Installed via Conda
- ✅ **Command Line Tools** - Installed via `xcode-select`
- ✅ **curl** - Built into macOS
- ✅ **grep/sed/awk** - Built into macOS

**Highly recommended:**
- ⚠️ **jq** - JSON processor (`brew install jq`)
- ⚠️ **psql** - PostgreSQL client (`brew install postgresql`)
- ⚠️ **tree** - Directory viewer (`brew install tree`)

**Optional but useful:**
- 📦 **fd** - Faster file search (`brew install fd`)
- 📦 **ripgrep** - Faster grep (`brew install ripgrep`)
- 📦 **htop** - Better top (`brew install htop`)
- 📦 **tmux** - Terminal multiplexer (`brew install tmux`)

### Tool Usage Examples for This Project

**Count JSON files:**
```bash
# Using find (built-in)
find /Users/ryanranft/0espn/data/nba -name "*.json" | wc -l

# Using fd (if installed)
fd -e json . /Users/ryanranft/0espn/data/nba | wc -l
```

**Search in JSON files:**
```bash
# Using grep (built-in)
grep -r "player_id" /Users/ryanranft/0espn/data/nba/nba_box_score | head -10

# Using ripgrep (if installed - much faster)
rg "player_id" /Users/ryanranft/0espn/data/nba/nba_box_score | head -10
```

**Process JSON data:**
```bash
# View structure
cat file.json | python -m json.tool | less

# Using jq (if installed - better)
jq '.' file.json | less
jq '.boxscore.teams[].team.displayName' file.json
```

**Monitor long operations:**
```bash
# Monitor S3 sync
aws s3 sync /local/path s3://bucket/ &
watch -n 5 'aws s3 ls s3://bucket/ --recursive | wc -l'

# Monitor disk space during operations
watch -n 10 'df -h /'
```

### Tool Version Tracking

**Document installed tool versions:**

| Tool | Location | Version | Last Checked | Purpose |
|------|----------|---------|--------------|---------|
| AWS CLI | `/opt/homebrew/bin/aws` | TBD | - | AWS operations |
| Git | `/usr/bin/git` | TBD | - | Version control |
| jq | TBD | TBD | - | JSON processing |
| psql | TBD | TBD | - | RDS access |
| curl | `/usr/bin/curl` | TBD | - | HTTP requests |
| Command Line Tools | `/Library/Developer/CommandLineTools` | TBD | - | Compilation |

**Update versions:**
```bash
aws --version
git --version
jq --version 2>/dev/null || echo "Not installed"
psql --version 2>/dev/null || echo "Not installed"
curl --version | head -1
xcode-select --version
```

---

## Notes for Claude

**When generating code, consider:**
1. **Python version:** 3.11.13 (use f-strings, type hints, modern syntax)
2. **macOS paths:** Use `/Users/ryanranft/` not `~` in documentation
3. **ARM64 architecture:** All packages must have ARM64 support
4. **Homebrew location:** `/opt/homebrew/` for Apple Silicon
5. **Shell:** zsh syntax (not bash) for shell scripts
6. **Memory:** 96 GB available (can handle large datasets in memory)
7. **Storage:** 1.71 TB available (no storage constraints for this project)

**Code should be optimized for:**
- Apple Silicon (ARM64) native performance
- macOS file system (case-insensitive by default)
- Conda environment isolation
- System-wide AWS CLI (not conda-installed)

---

## Quick Health Check Script

**Purpose:** Comprehensive health check script to run at the start of each session to verify all system components.

### Master Health Check Script

**Create the master health check script:**

**Location:** `scripts/shell/check_machine_health.sh`

**Complete script content available in MACHINE_SPECS.md** - The script performs 14 comprehensive checks:

1. System Information (macOS version, hardware, disk space)
2. Disk Space (usage percentage with warnings)
3. Homebrew (installation, location, outdated packages)
4. Miniconda (installation, nba-aws environment)
5. Python Environment (Python 3.11, package count)
6. Core Python Packages (all 14 required packages)
7. AWS CLI (installation, credentials, S3 connectivity)
8. Git (installation, GitHub SSH, configuration)
9. Project Files (critical files check)
10. Data Directory (JSON file count ~146K)
11. Network & AWS Connectivity (internet, endpoints, DNS)
12. Security Settings (SIP, FileVault, SSH permissions)
13. System Resources (memory, CPU)
14. Optional Tools (jq, psql, tree, tmux)

### Quick Setup

**Make executable and run:**
```bash
chmod +x /Users/ryanranft/nba-simulator-aws/scripts/shell/check_machine_health.sh
./scripts/shell/check_machine_health.sh
```

**Add shell alias:**
```bash
# Add to ~/.zshrc
alias nbahealth='/Users/ryanranft/nba-simulator-aws/scripts/shell/check_machine_health.sh'
```

### Exit Codes

- **0** - All checks passed (system ready)
- **1** - One or more checks failed

### Expected Execution Time

- **Without data check:** 5-10 seconds
- **With data check:** 30-60 seconds (146K file count)

---

**Next Update Due:** Start of next session or 2025-10-08 (whichever comes first)