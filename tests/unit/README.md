# Unit Tests

**Purpose:** Fast, isolated tests with no external dependencies

**Characteristics:**
- No AWS resource access (S3, RDS, CloudWatch)
- No network calls
- Use mocked data and responses
- Run in <100ms each
- Can run offline

**Run Command:**
```bash
pytest -m unit
```

**Examples:**
- Data transformation logic
- Utility function tests
- Configuration parsing
- Data validation rules
