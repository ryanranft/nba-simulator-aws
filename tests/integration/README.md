# Integration Tests

**Purpose:** Tests requiring AWS resources and external services

**Characteristics:**
- Require AWS credentials
- Access S3, RDS, or other AWS services
- May make network calls
- Slower execution (1s+)
- Require proper environment configuration

**Run Command:**
```bash
pytest -m integration
```

**Prerequisites:**
- AWS credentials configured
- RDS database accessible
- S3 bucket permissions

**Examples:**
- S3 file upload/download
- Database queries
- ETL pipeline tests
- ADCE autonomous system tests
