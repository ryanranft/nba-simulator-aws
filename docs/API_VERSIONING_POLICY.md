# API Versioning Policy

**Version:** 1.0.0
**Last Updated:** October 31, 2025
**Status:** Active
**Owner:** NBA Simulator Dev Team

---

## Table of Contents

- [Overview](#overview)
- [Versioning Strategy](#versioning-strategy)
- [Version Lifecycle](#version-lifecycle)
- [Breaking vs Non-Breaking Changes](#breaking-vs-non-breaking-changes)
- [Deprecation Process](#deprecation-process)
- [Version Headers](#version-headers)
- [Client Compatibility](#client-compatibility)
- [Examples](#examples)
- [Migration Guide](#migration-guide)

---

## Overview

This document defines the API versioning strategy for the NBA Simulator system. Our goal is to:

- ✅ **Maintain backward compatibility** for existing clients
- ✅ **Enable evolution** of APIs over time
- ✅ **Provide clear migration paths** when breaking changes are necessary
- ✅ **Give adequate notice** before removing deprecated features
- ✅ **Support multiple versions** during transition periods

**Applies to:**
- REST APIs (Data Collection, Temporal Queries, ADCE Management)
- Database schemas (table structures, column definitions)
- Python package APIs (`nba_simulator` package)
- MCP server APIs (nba-mcp-server)

**Does NOT apply to:**
- Internal scripts (can change freely)
- Development/test environments
- Experimental features clearly marked as unstable

---

## Versioning Strategy

### URL-Based Versioning (REST APIs)

**Format:** `/api/{version}/{resource}`

**Examples:**
```
/api/v1/collection/trigger
/api/v2/query/player-stats
/api/v1/adce/health
```

**Why URL-based?**
- ✅ Explicit and visible in requests
- ✅ Easy to route in proxies/load balancers
- ✅ Supports multiple versions simultaneously
- ✅ Clear from logs which version was used

**Rejected Alternatives:**
- ❌ **Header-based versioning** (`Accept: application/vnd.nba-simulator.v1+json`)
  - Less visible, harder to debug
- ❌ **Query parameter versioning** (`/api/data?version=1`)
  - Can conflict with resource query params
- ❌ **Hostname versioning** (`v1.api.nba-simulator.com`)
  - Requires separate DNS, SSL certificates

### Semantic Versioning (Python Packages)

**Format:** `MAJOR.MINOR.PATCH`

**Example:** `nba_simulator==2.1.3`

- **MAJOR:** Breaking changes (incompatible API changes)
- **MINOR:** New features (backward-compatible additions)
- **PATCH:** Bug fixes (backward-compatible fixes)

**Pre-release versions:**
- `2.0.0-alpha` - Early testing, unstable
- `2.0.0-beta` - Feature complete, stabilizing
- `2.0.0-rc1` - Release candidate, final testing

---

## Version Lifecycle

### Phase 1: Active Support

**Duration:** Indefinite (until superseded)
**Support Level:** Full

- ✅ All features available
- ✅ Bug fixes and security updates
- ✅ Performance improvements
- ✅ New features may be added (non-breaking)
- ✅ Documentation actively maintained

**Example:** v1 API released 2025-10-01, still in active support

### Phase 2: Deprecated

**Duration:** Minimum 6 months
**Support Level:** Limited

- ⚠️ Still functional but discouraged
- ✅ Security updates only (no new features)
- ⚠️ Deprecation warnings in responses
- ⚠️ Documentation marked as deprecated
- ℹ️ Migration guide provided

**Triggers for deprecation:**
- New major version released (v2 replaces v1)
- Security concerns with architecture
- Cost or performance issues
- Better alternatives available

**Example:** v1 API deprecated 2026-04-01 when v2 released

### Phase 3: Sunset (End of Life)

**Duration:** 6 months notice minimum
**Support Level:** None

- ❌ No longer available
- ❌ Returns `410 Gone` HTTP status
- ℹ️ Response includes migration guide URL
- ℹ️ Logs track failed requests for monitoring

**Example:** v1 API sunset 2026-10-01 (6 months after deprecation)

**Sunset response:**
```json
{
  "error": "version_sunset",
  "message": "API version v1 has been sunset as of 2026-10-01",
  "sunset_date": "2026-10-01",
  "current_version": "v2",
  "migration_guide": "https://docs.nba-simulator.com/api/v1-to-v2-migration",
  "support_contact": "support@nba-simulator.com"
}
```

---

## Breaking vs Non-Breaking Changes

### Breaking Changes (Require New Major Version)

**API Changes:**
- ❌ Removing endpoints
- ❌ Removing request/response fields
- ❌ Changing field types (string → integer)
- ❌ Changing authentication method
- ❌ Changing error response formats
- ❌ Renaming fields
- ❌ Making optional fields required
- ❌ Changing URL structure
- ❌ Restricting rate limits significantly

**Database Changes:**
- ❌ Dropping tables
- ❌ Dropping columns
- ❌ Changing column types (incompatible)
- ❌ Removing indexes that queries depend on
- ❌ Changing primary key structure

**Package Changes:**
- ❌ Removing public functions/classes
- ❌ Changing function signatures (incompatible)
- ❌ Removing required parameters
- ❌ Changing return types

### Non-Breaking Changes (Backward Compatible)

**API Changes:**
- ✅ Adding new endpoints
- ✅ Adding optional request parameters
- ✅ Adding new fields to responses
- ✅ Adding new optional headers
- ✅ Improving error messages (without changing structure)
- ✅ Performance optimizations
- ✅ Bug fixes
- ✅ Relaxing validation rules
- ✅ Increasing rate limits

**Database Changes:**
- ✅ Adding new tables
- ✅ Adding new columns (nullable or with defaults)
- ✅ Adding indexes for performance
- ✅ Adding constraints (non-breaking)

**Package Changes:**
- ✅ Adding new functions/classes
- ✅ Adding optional parameters (with defaults)
- ✅ Adding new return fields (if returning dict)
- ✅ Deprecating (but not removing) functions

---

## Deprecation Process

### Step 1: Announce Deprecation (T-0)

**Actions:**
- 📣 Post announcement in docs and changelog
- 📣 Send email to API consumers
- 📣 Add deprecation notice to API docs
- 📣 Update response headers (see below)

**Timeline:** Minimum 6 months before sunset

**Example Announcement:**
```markdown
## Deprecation Notice: v1 API

**Effective Date:** 2026-04-01
**Sunset Date:** 2026-10-01 (6 months)
**Replacement:** v2 API

The v1 API will be sunset on 2026-10-01. All clients should migrate
to v2 before this date. See migration guide: [link]

**What's Changing:**
- Authentication moved from query params to headers
- Timestamps now use ISO 8601 format
- Error responses follow RFC 7807 format

**Migration Support:**
- Migration guide: [link]
- Support email: support@nba-simulator.com
- Office hours: Tuesdays 2-4pm CT
```

### Step 2: Add Deprecation Headers (T-0)

**HTTP Response Headers:**
```http
Deprecation: true
Sunset: Wed, 01 Oct 2026 00:00:00 GMT
Link: </api/v2/resource>; rel="successor-version"
Warning: 299 - "API v1 is deprecated and will be removed on 2026-10-01. Migrate to v2."
```

**Implementation:**
```python
from flask import Response
from datetime import datetime

def add_deprecation_headers(response: Response, sunset_date: str, successor: str):
    """Add deprecation headers to response."""
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = sunset_date  # HTTP date format
    response.headers['Link'] = f'<{successor}>; rel="successor-version"'
    response.headers['Warning'] = (
        f'299 - "This API version is deprecated. '
        f'Sunset date: {sunset_date}. Migrate to {successor}."'
    )
    return response

@app.route('/api/v1/data')
def get_data_v1():
    data = {"result": "data"}
    response = jsonify(data)
    return add_deprecation_headers(
        response,
        sunset_date='Wed, 01 Oct 2026 00:00:00 GMT',
        successor='/api/v2/data'
    )
```

### Step 3: Monitor Usage (T+1 month to T+5 months)

**Tracking:**
- Log all requests to deprecated endpoints
- Track unique clients using deprecated version
- Monitor error rates during migration
- Measure adoption of new version

**Metrics:**
```python
# CloudWatch metrics
cloudwatch.put_metric_data(
    Namespace='ADCE/API',
    MetricData=[
        {
            'MetricName': 'DeprecatedAPIUsage',
            'Value': request_count,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Version', 'Value': 'v1'},
                {'Name': 'Endpoint', 'Value': endpoint_path}
            ]
        }
    ]
)
```

**Proactive outreach:**
- Email high-volume API consumers directly
- Offer migration assistance
- Provide timeline updates

### Step 4: Sunset (T+6 months)

**Actions:**
- 🔒 Remove deprecated endpoints
- 🔒 Return `410 Gone` with migration info
- 📊 Monitor for broken clients
- 📞 Support remaining stragglers

**Sunset Implementation:**
```python
@app.route('/api/v1/<path:path>')
def v1_sunset_handler(path):
    """Return 410 Gone for all v1 endpoints."""
    return jsonify({
        'error': 'version_sunset',
        'message': 'API version v1 was sunset on 2026-10-01',
        'sunset_date': '2026-10-01',
        'current_version': 'v2',
        'migration_guide': 'https://docs.nba-simulator.com/api/v1-to-v2-migration',
        'requested_path': path
    }), 410
```

---

## Version Headers

### Request Headers (Optional)

Clients can specify version preferences:

```http
Accept: application/json
API-Version: v2
```

**Behavior:**
- If header present and valid: Use specified version
- If header invalid: Return `400 Bad Request`
- If header absent: Use URL version (recommended approach)

### Response Headers (Required)

All API responses include version information:

```http
API-Version: v2
Vary: API-Version
```

**Rationale:**
- Clients know which version handled request
- Caching proxies vary by version
- Debugging easier (version in logs)

---

## Client Compatibility

### Graceful Degradation

Clients should handle API evolution:

**Best Practices:**
- ✅ Ignore unknown fields in responses (forward compatibility)
- ✅ Check for required fields before use
- ✅ Handle new error codes gracefully
- ✅ Set explicit version in requests
- ✅ Monitor deprecation headers
- ✅ Test against new versions before migration

**Example (Python client):**
```python
import requests

response = requests.get('https://api.nba-simulator.com/api/v1/data')

# Check for deprecation
if 'Deprecation' in response.headers:
    print(f"⚠️ WARNING: This API is deprecated!")
    print(f"Sunset date: {response.headers.get('Sunset')}")
    print(f"Migrate to: {response.headers.get('Link')}")

# Handle response (ignore unknown fields)
data = response.json()
required_fields = ['game_id', 'date', 'score']

if all(field in data for field in required_fields):
    process_data(data)
else:
    handle_missing_fields(data, required_fields)
```

### Version Negotiation

If client specifies unsupported version:

```http
GET /api/v5/data HTTP/1.1
API-Version: v5
```

**Response:**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "unsupported_version",
  "message": "API version v5 is not supported",
  "supported_versions": ["v1", "v2"],
  "recommended_version": "v2"
}
```

---

## Examples

### Example 1: Adding New Field (Non-Breaking)

**v1 Response:**
```json
{
  "game_id": 401584866,
  "date": "2024-06-19",
  "home_team": "BOS",
  "away_team": "DAL",
  "score": {"home": 106, "away": 88}
}
```

**v1 Response (after enhancement):**
```json
{
  "game_id": 401584866,
  "date": "2024-06-19",
  "home_team": "BOS",
  "away_team": "DAL",
  "score": {"home": 106, "away": 88},
  "attendance": 19156  // ✅ New optional field
}
```

**Impact:** None - old clients ignore new field

### Example 2: Changing Field Type (Breaking)

**v1 Response:**
```json
{
  "game_id": "401584866",  // string
  "date": "2024-06-19"
}
```

**v2 Response:**
```json
{
  "game_id": 401584866,  // ❌ now integer (breaking!)
  "date": "2024-06-19T20:30:00Z"  // ❌ ISO 8601 (breaking!)
}
```

**Impact:** Breaking - requires new version (v2)

### Example 3: Renaming Field (Breaking)

**v1 Response:**
```json
{
  "player_name": "Jayson Tatum"
}
```

**v2 Response (bad approach):**
```json
{
  "name": "Jayson Tatum"  // ❌ Field renamed (breaking!)
}
```

**v2 Response (good approach):**
```json
{
  "player_name": "Jayson Tatum",  // ✅ Keep old field
  "name": "Jayson Tatum"           // ✅ Add new field
  // Deprecate player_name in docs, remove in v3
}
```

### Example 4: Adding Required Parameter (Breaking)

**v1 Request:**
```http
POST /api/v1/collection/trigger
Content-Type: application/json

{
  "source": "espn",
  "date_range": {"start": "2025-01-01", "end": "2025-01-31"}
}
```

**v2 Request:**
```http
POST /api/v2/collection/trigger
Content-Type: application/json

{
  "source": "espn",
  "date_range": {"start": "2025-01-01", "end": "2025-01-31"},
  "priority": "medium"  // ❌ Now required (breaking!)
}
```

**Better approach (v2):**
```http
POST /api/v2/collection/trigger
Content-Type: application/json

{
  "source": "espn",
  "date_range": {"start": "2025-01-01", "end": "2025-01-31"},
  "priority": "medium"  // ✅ Optional with default="medium"
}
```

---

## Migration Guide

### Migrating from v1 to v2 (Example)

**Step 1: Review Changes**

Read the changelog: `https://docs.nba-simulator.com/api/v2-changelog`

**Key Changes:**
- Authentication moved to headers
- Timestamps use ISO 8601
- Error responses follow RFC 7807

**Step 2: Update Client Code**

**Before (v1):**
```python
import requests

response = requests.get(
    'https://api.nba-simulator.com/api/v1/data',
    params={'api_key': 'your_key'}  # Auth in query params
)
```

**After (v2):**
```python
import requests

response = requests.get(
    'https://api.nba-simulator.com/api/v2/data',
    headers={'Authorization': f'Bearer your_token'}  # Auth in headers
)
```

**Step 3: Test Against v2**

```bash
# Test in staging first
export API_BASE_URL=https://staging-api.nba-simulator.com/api/v2

pytest tests/integration/test_api_client.py
```

**Step 4: Gradual Rollout**

```python
# Feature flag approach
USE_API_V2 = os.getenv('USE_API_V2', 'false') == 'true'

if USE_API_V2:
    api_client = APIV2Client()
else:
    api_client = APIV1Client()
```

**Step 5: Monitor & Validate**

- Check error rates
- Validate response data
- Monitor latency changes
- Track deprecation warnings

---

## Governance

### Version Approval Process

**Minor version (v1.1, v1.2):**
- Technical lead approval
- Documentation update
- Changelog entry

**Major version (v2.0, v3.0):**
- Team discussion and approval
- ADR creation (Architecture Decision Record)
- 6-month deprecation notice
- Migration guide required
- Customer communication plan

### Review Schedule

**Quarterly Review:**
- Review deprecated versions
- Check adoption metrics
- Plan sunset dates
- Update migration guides

---

## References

**Standards:**
- [RFC 7231 - HTTP Status Codes](https://tools.ietf.org/html/rfc7231)
- [RFC 8594 - Sunset Header](https://tools.ietf.org/html/rfc8594)
- [RFC 7807 - Problem Details](https://tools.ietf.org/html/rfc7807)
- [Semantic Versioning 2.0.0](https://semver.org/)

**Related Documentation:**
- [API Documentation](docs/api/) - API reference
- [DEVELOPER_ONBOARDING.md](DEVELOPER_ONBOARDING.md) - Getting started
- [ADR Template](docs/adr/_TEMPLATE.md) - Architecture decisions

---

**Version History:**
- **1.0.0** (2025-10-31) - Initial policy document

**Last Updated:** October 31, 2025
**Owner:** NBA Simulator Dev Team
**Review Date:** January 31, 2026
