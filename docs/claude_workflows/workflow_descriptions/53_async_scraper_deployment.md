# Workflow #53: Async Scraper Deployment

**Purpose:** Deploy the new async scraping infrastructure to production with comprehensive testing, monitoring, and rollback procedures.

**When to Use:** After completing the async infrastructure implementation and before running production scrapers.

**Estimated Time:** 75-110 minutes

**Prerequisites:**
- Async infrastructure completed (Workflow #52)
- Docker and Docker Compose installed
- AWS credentials configured
- Test suite passing

---

## 1. Prerequisites Checklist

### Environment Setup
- [ ] **Docker Installed**: `docker --version` (20.10+)
- [ ] **Docker Compose Installed**: `docker-compose --version` (2.0+)
- [ ] **Python Environment**: `python3 --version` (3.11+)
- [ ] **AWS CLI Configured**: `aws sts get-caller-identity`
- [ ] **S3 Access**: `aws s3 ls s3://nba-sim-raw-data-lake`

### Configuration Files
- [ ] **Environment Variables**: `.env` file created with required variables
- [ ] **Scraper Config**: `config/scraper_config.yaml` validated
- [ ] **Docker Compose**: `docker-compose.yml` present and configured
- [ ] **Requirements**: `requirements.txt` includes async dependencies

### Data Safety
- [ ] **Backup Completed**: Current data backed up to `~/sports-simulator-archives/nba/`
- [ ] **S3 Bucket Accessible**: Can read/write to `nba-sim-raw-data-lake`
- [ ] **Database Access**: RDS PostgreSQL connection tested

---

## 2. Pre-Deployment Testing

### Run Test Suite
```bash
# Navigate to project directory
cd /Users/ryanranft/nba-simulator-aws

# Run comprehensive test suite
python3 -m pytest tests/test_new_scraper_components.py -v

# Run integration tests
python3 -m pytest tests/test_async_scrapers.py -v

# Check test coverage
python3 -m pytest tests/ --cov=scripts/etl --cov-report=html
```

**Expected Results:**
- All tests pass (100% success rate)
- No critical errors in test output
- Coverage report generated in `htmlcov/`

### Validate Configurations
```bash
# Test scraper configuration loading
python3 -c "from scripts.etl.scraper_config import ScraperConfig; print('Config loaded successfully')"

# Test Docker Compose syntax
docker-compose config

# Validate environment variables
python3 -c "import os; print('AWS_ACCESS_KEY_ID:', bool(os.getenv('AWS_ACCESS_KEY_ID')))"
```

---

## 3. Local Deployment

### Build and Start Services
```bash
# Build all Docker images
docker-compose build

# Start services in detached mode
docker-compose up -d

# Check service status
docker-compose ps
```

**Expected Output:**
```
Name                     Command               State           Ports
--------------------------------------------------------------------
nba-data-validator       python -c ...         Up
nba-espn-scraper         python scripts/etl/espn_async_scraper.py  Up
nba-health-dashboard     python scripts/monitoring/scraper_health_monitor.py  Up  0.0.0.0:8080->8080/tcp
nba-nba-api-scraper      python scripts/etl/nba_api_async_scraper.py  Up
nba-ref-scraper          python scripts/etl/basketball_reference_async_scraper.py  Up
```

### Verify Health Endpoints
```bash
# Check health dashboard
curl http://localhost:8080/health

# Check individual service health
curl http://localhost:8080/health/espn
curl http://localhost:8080/health/basketball-reference
curl http://localhost:8080/health/nba-api
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-13T10:30:00Z",
  "services": {
    "espn": "healthy",
    "basketball-reference": "healthy",
    "nba-api": "healthy"
  }
}
```

---

## 4. Production Deployment

### EC2 Deployment (Recommended)
```bash
# SSH to EC2 instance
ssh -i ~/.ssh/nba-sim-key.pem ec2-user@your-ec2-instance

# Clone repository
git clone https://github.com/your-username/nba-simulator-aws.git
cd nba-simulator-aws

# Install Docker (if not already installed)
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure environment
cp .env.example .env
# Edit .env with production values

# Deploy
docker-compose up -d
```

### ECS Deployment (Alternative)
```bash
# Build and push images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

docker build -t nba-scrapers .
docker tag nba-scrapers:latest your-account.dkr.ecr.us-east-1.amazonaws.com/nba-scrapers:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/nba-scrapers:latest

# Update ECS service
aws ecs update-service --cluster nba-scrapers --service nba-scrapers-service --force-new-deployment
```

---

## 5. Health Monitoring Setup

### Configure Alerts
```bash
# Test alert system
python3 -c "
from scripts.monitoring.alert_manager import AlertManager
alert_manager = AlertManager()
alert_manager.send_test_alert('Deployment test alert')
"
```

### Verify Monitoring Dashboard
1. **Access Dashboard**: Navigate to `http://your-server:8080`
2. **Check Metrics**: Verify Prometheus metrics are being collected
3. **Test Alerts**: Trigger test alerts to verify notification channels
4. **Review Logs**: Check structured logging output

### Set Up Log Rotation
```bash
# Configure logrotate for scraper logs
sudo tee /etc/logrotate.d/nba-scrapers << EOF
/Users/ryanranft/nba-simulator-aws/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ryanranft staff
}
EOF
```

---

## 6. Post-Deployment Verification

### Automated Validation
```bash
# Run deployment validation script
bash scripts/deployment/docker_deploy.sh validate

# Check all services are healthy
curl -s http://localhost:8080/health | jq '.status' | grep -q "healthy"
```

### Manual Verification Steps
1. **Service Status**: All containers running without restarts
2. **Health Endpoints**: All services responding with "healthy" status
3. **Log Analysis**: No ERROR or CRITICAL messages in last 10 minutes
4. **S3 Connectivity**: Test upload/download to S3 bucket
5. **Data Validation**: Run sample data collection and validation

### Performance Verification
```bash
# Test scraper performance
python3 -c "
import asyncio
from scripts.etl.espn_async_scraper import ESPNAsyncScraper

async def test_performance():
    scraper = ESPNAsyncScraper()
    start_time = time.time()
    await scraper.scrape_recent_games(days=1)
    duration = time.time() - start_time
    print(f'Scraping completed in {duration:.2f} seconds')

asyncio.run(test_performance())
"
```

**Expected Performance:**
- ESPN scraper: < 30 seconds for 1 day of data
- Basketball Reference: < 60 seconds for current season stats
- NBA API: < 45 seconds for player stats

---

## 7. Rollback Procedures

### Quick Rollback (Local)
```bash
# Stop new services
docker-compose down

# Start old scrapers
python3 scripts/etl/espn_incremental_scraper.py
python3 scripts/etl/basketball_reference_incremental_scraper.py
```

### Complete Rollback (Production)
```bash
# Stop all services
docker-compose down

# Remove new images
docker rmi $(docker images -q nba-scrapers)

# Restore from backup
aws s3 sync s3://nba-sim-raw-data-lake-backup/ s3://nba-sim-raw-data-lake/

# Start old infrastructure
python3 scripts/monitoring/launch_scraper.sh
```

### Data Rollback
```bash
# Restore S3 data from backup
aws s3 sync s3://nba-sim-raw-data-lake-backup/ s3://nba-sim-raw-data-lake/ --delete

# Restore database from snapshot (if applicable)
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier nba-sim-restored \
    --db-snapshot-identifier nba-sim-pre-deployment-snapshot
```

---

## 8. Troubleshooting Guide

### Common Issues

#### Services Won't Start
```bash
# Check Docker logs
docker-compose logs [service-name]

# Common fixes:
# 1. Port conflicts: Change ports in docker-compose.yml
# 2. Memory issues: Increase Docker memory allocation
# 3. Permission issues: Check file permissions
```

#### Health Checks Failing
```bash
# Check individual service health
curl -v http://localhost:8080/health/[service-name]

# Common fixes:
# 1. Service not ready: Wait 30 seconds for startup
# 2. Network issues: Check Docker network configuration
# 3. Dependencies missing: Verify all required packages installed
```

#### S3 Connection Issues
```bash
# Test AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://nba-sim-raw-data-lake

# Common fixes:
# 1. Credentials expired: Refresh AWS credentials
# 2. Permissions: Check IAM policy for S3 access
# 3. Region mismatch: Verify AWS region configuration
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor logs for bottlenecks
docker-compose logs -f | grep -E "(ERROR|WARNING|slow)"

# Common fixes:
# 1. Rate limiting: Adjust rate limits in config
# 2. Memory leaks: Restart services periodically
# 3. Network latency: Check internet connection
```

### Emergency Contacts
- **AWS Support**: [Your AWS Support Plan]
- **Docker Support**: [Docker Hub Support]
- **Project Lead**: [Your Contact Information]

---

## 9. Success Criteria

### Deployment Success
- [ ] All services running without errors
- [ ] Health dashboard accessible and showing green status
- [ ] Test data collection successful
- [ ] Performance metrics within expected ranges
- [ ] Alert system functional
- [ ] Logs showing normal operation

### Performance Benchmarks
- [ ] ESPN scraper: < 30 seconds for 1 day of data
- [ ] Basketball Reference: < 60 seconds for current season
- [ ] NBA API: < 45 seconds for player stats
- [ ] Error rate: < 1% for all scrapers
- [ ] Uptime: > 99% for all services

### Monitoring Success
- [ ] Prometheus metrics being collected
- [ ] Health checks passing consistently
- [ ] Alerts configured and tested
- [ ] Log rotation configured
- [ ] Dashboard accessible and functional

---

## 10. Next Steps

After successful deployment:

1. **Monitor for 24 hours**: Watch for any issues or performance degradation
2. **Update documentation**: Record any deployment-specific notes
3. **Schedule maintenance**: Set up regular health checks and updates
4. **Train team**: Ensure team members understand new infrastructure
5. **Plan migration**: Gradually migrate old scrapers to new infrastructure

---

## Related Workflows

- **Workflow #35**: Pre-Deployment Testing
- **Workflow #40**: Scraper Operations Complete
- **Workflow #41**: Testing Framework
- **Workflow #42**: Scraper Management

---

## References

- [README_ASYNC_INFRASTRUCTURE.md](../README_ASYNC_INFRASTRUCTURE.md)
- [SCRAPER_MANAGEMENT.md](../SCRAPER_MANAGEMENT.md)
- [ASYNC_DEPLOYMENT_CHECKLIST.md](../ASYNC_DEPLOYMENT_CHECKLIST.md)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)

