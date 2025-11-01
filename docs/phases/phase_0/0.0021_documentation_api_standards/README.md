# 0.0021: Documentation & API Standards

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ✅ COMPLETE
**Priority:** 🟡 MEDIUM
**Completion Date:** November 1, 2025
**Timeline:** Completed in 1 session (~2 hours)
**Cost Impact:** $0 (documentation tools free)

---

## Overview

Establish comprehensive documentation standards and API specifications to enable team collaboration, external integrations, and long-term maintainability. This transforms ad-hoc documentation into a systematic knowledge base.

**This sub-phase delivers:**
- Swagger/OpenAPI specifications for all APIs
- Developer onboarding guides and runbooks
- Architecture Decision Records (ADR) system
- Code documentation standards (docstrings, comments)
- API versioning and deprecation policies
- Auto-generated API reference documentation

**Why this is foundational, not optional:**
- Enables API consumers (future web app, mobile apps)
- Reduces onboarding time for new developers
- Documents architectural decisions for future reference
- Prevents knowledge loss as system evolves
- Supports external integrations and partnerships

---

## Current Documentation State

**Existing Documentation (from 0.0001-0.18):**
- 1,720 markdown files (251 MB)
- PROGRESS.md - Master project status
- CLAUDE.md - AI assistant instructions
- 66 workflows in `docs/claude_workflows/`
- Phase indexes and sub-phase READMEs
- DATA_CATALOG.md, DATA_STRUCTURE_GUIDE.md, etc.
- ADR-010: Four-Digit Sub-Phase Numbering

**Gaps to Address:**
- No Swagger/OpenAPI API specifications
- No formal developer onboarding guide
- ADR system exists but not standardized
- Inconsistent docstring coverage
- No API versioning strategy
- No auto-generated reference docs

---

## Sub-Phase Components

### 1. Swagger/OpenAPI Specifications

**Goal:** Machine-readable API documentation for all endpoints

**API Categories to Document:**

#### A. Data Collection APIs
```yaml
# api_specs/data_collection.yaml
openapi: 3.0.0
info:
  title: NBA Simulator Data Collection API
  version: 1.0.0
  description: APIs for autonomous data collection and S3 management

paths:
  /api/v1/collection/trigger:
    post:
      summary: Trigger data collection task
      tags: [Data Collection]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                source:
                  type: string
                  enum: [espn, hoopr, nba_api, basketball_reference]
                  example: "espn"
                date_range:
                  type: object
                  properties:
                    start: {type: string, format: date, example: "2025-10-01"}
                    end: {type: string, format: date, example: "2025-10-25"}
                priority:
                  type: string
                  enum: [low, medium, high, critical]
                  default: "medium"
      responses:
        '202':
          description: Task queued successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  task_id: {type: string, example: "task_123456"}
                  status: {type: string, example: "queued"}
                  estimated_duration: {type: integer, example: 300}

  /api/v1/collection/status/{task_id}:
    get:
      summary: Check collection task status
      tags: [Data Collection]
      parameters:
        - name: task_id
          in: path
          required: true
          schema: {type: string}
      responses:
        '200':
          description: Task status retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  task_id: {type: string}
                  status: {type: string, enum: [queued, running, completed, failed]}
                  progress: {type: number, minimum: 0, maximum: 100}
                  files_collected: {type: integer}
                  errors: {type: array, items: {type: string}}
```

#### B. Temporal Query APIs
```yaml
# api_specs/temporal_queries.yaml
openapi: 3.0.0
info:
  title: NBA Temporal Query API
  version: 1.0.0
  description: Query NBA statistics at any point in time

paths:
  /api/v1/query/player-stats:
    get:
      summary: Get player statistics at specific timestamp
      tags: [Temporal Queries]
      parameters:
        - name: player_id
          in: query
          required: true
          schema: {type: integer, example: 1628369}
          description: NBA player ID
        - name: timestamp
          in: query
          required: true
          schema: {type: string, format: date-time, example: "2016-06-19T19:02:34.560000-05:00"}
          description: Exact moment to query (ISO 8601)
        - name: scope
          in: query
          schema: {type: string, enum: [career, season, game], default: "career"}
      responses:
        '200':
          description: Player stats at timestamp
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PlayerStats'

components:
  schemas:
    PlayerStats:
      type: object
      properties:
        player_id: {type: integer}
        player_name: {type: string}
        timestamp: {type: string, format: date-time}
        stats:
          type: object
          properties:
            points: {type: integer}
            rebounds: {type: integer}
            assists: {type: integer}
            games_played: {type: integer}
            # ... all stats ...
```

#### C. ADCE Management APIs
```yaml
# api_specs/adce_management.yaml
openapi: 3.0.0
info:
  title: ADCE Management API
  version: 1.0.0
  description: Autonomous Data Collection Ecosystem control

paths:
  /api/v1/adce/health:
    get:
      summary: Get ADCE system health
      tags: [ADCE]
      responses:
        '200':
          description: System health status
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: {type: string, enum: [healthy, degraded, unhealthy]}
                  uptime_seconds: {type: integer}
                  tasks_completed_24h: {type: integer}
                  queue_depth: {type: integer}
                  success_rate: {type: number, minimum: 0, maximum: 100}

  /api/v1/adce/queue:
    get:
      summary: Get current task queue
      tags: [ADCE]
      responses:
        '200':
          description: Task queue contents
          content:
            application/json:
              schema:
                type: object
                properties:
                  queue_depth: {type: integer}
                  tasks:
                    type: array
                    items:
                      type: object
                      properties:
                        task_id: {type: string}
                        source: {type: string}
                        priority: {type: string}
                        queued_at: {type: string, format: date-time}
```

**Generate Documentation:**
```bash
# Install redoc for HTML rendering
npm install -g redoc-cli

# Generate HTML docs
redoc-cli bundle api_specs/data_collection.yaml -o docs/api/data_collection.html
redoc-cli bundle api_specs/temporal_queries.yaml -o docs/api/temporal_queries.html
redoc-cli bundle api_specs/adce_management.yaml -o docs/api/adce_management.html
```

### 2. Developer Onboarding Guide

**Goal:** New developers productive within 2 hours

**Create:** `docs/DEVELOPER_ONBOARDING.md`

```markdown
# NBA Simulator - Developer Onboarding

**Estimated Time:** 2 hours
**Prerequisites:** MacBook Pro, AWS credentials, GitHub access

---

## Hour 1: Environment Setup

### Step 1: Clone Repository (5 min)
\`\`\`bash
git clone git@github.com:your-org/nba-simulator-aws.git
cd nba-simulator-aws
\`\`\`

### Step 2: Install Dependencies (15 min)
\`\`\`bash
# Create conda environment
conda create -n nba-aws python=3.11
conda activate nba-aws

# Install Python packages
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
\`\`\`

### Step 3: Configure AWS (10 min)
\`\`\`bash
# Copy environment template
cp .env.example .env

# Edit with your AWS credentials
nano .env

# Test connection
aws s3 ls s3://nba-sim-raw-data-lake/ --profile nba-simulator
\`\`\`

### Step 4: Verify Setup (10 min)
\`\`\`bash
# Run test suite
pytest tests/ -v

# Verify DIMS
python scripts/monitoring/dims_cli.py verify --category s3_storage

# Check documentation
open docs/README.md
\`\`\`

### Step 5: Explore Codebase (20 min)
\`\`\`bash
# Read project overview
cat PROGRESS.md

# Understand workflows
ls docs/claude_workflows/workflow_descriptions/

# Browse data structure
cat docs/DATA_STRUCTURE_GUIDE.md
\`\`\`

---

## Hour 2: First Contribution

### Step 1: Pick a Task (10 min)
- Browse `PROGRESS.md` for ⏸️ PENDING tasks
- Check GitHub Issues for good first issues
- Ask team lead for recommendations

### Step 2: Create Feature Branch (5 min)
\`\`\`bash
git checkout -b feature/your-feature-name
\`\`\`

### Step 3: Make Changes (30 min)
- Follow code standards in `docs/STYLE_GUIDE.md`
- Write tests for new functionality
- Update documentation if needed

### Step 4: Commit and Push (15 min)
\`\`\`bash
# Pre-commit hooks will run automatically
git add .
git commit -m "feat: Your commit message"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request
gh pr create --title "Your PR title" --body "Description"
\`\`\`

---

## Common Gotchas

1. **AWS credentials not found:** Ensure `.env` file exists with correct keys
2. **Pre-commit hook fails:** Run `pre-commit run --all-files` to see errors
3. **Tests fail locally:** Check you're using Python 3.11, not 3.9 or 3.12
4. **S3 access denied:** Verify IAM role has correct permissions

---

## Next Steps

After onboarding:
- Join team Slack channel
- Review ADRs in `docs/adr/`
- Attend weekly standup
- Pair program with senior developer
\`\`\`

### 3. Architecture Decision Records (ADR) System

**Goal:** Standardized decision documentation

**ADR Template:** `docs/adr/_TEMPLATE.md`

```markdown
# ADR-XXX: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Decision Maker:** [Name | Team]

---

## Context

What is the issue we're addressing? What constraints exist?

## Decision

What decision are we making? What is the chosen approach?

## Rationale

Why did we choose this approach? What are the key benefits?

## Alternatives Considered

### Alternative 1: [Name]
- **Pros:** ...
- **Cons:** ...
- **Why rejected:** ...

### Alternative 2: [Name]
- **Pros:** ...
- **Cons:** ...
- **Why rejected:** ...

## Consequences

### Positive
✅ Benefit 1
✅ Benefit 2

### Negative
⚠️ Cost 1
⚠️ Risk 1

### Mitigation
- How we address negative consequences

## Implementation

- Step-by-step plan
- Timeline
- Success metrics

## Review Date

When should we revisit this decision?

## References

- Links to related documentation
- Related ADRs
- External resources

---

**Related ADRs:** [ADR-XXX], [ADR-YYY]
**Supersedes:** None | [ADR-XXX]
**Superseded By:** None | [ADR-XXX]
```

**ADR Management Script:**
```bash
#!/bin/bash
# scripts/docs/create_adr.sh

ADR_NUMBER=$(ls docs/adr/ | grep -E '^[0-9]{3}' | wc -l | awk '{print $1+1}')
ADR_NUMBER=$(printf "%03d" $ADR_NUMBER)

ADR_TITLE="$1"
ADR_FILE="docs/adr/${ADR_NUMBER}-${ADR_TITLE}.md"

cp docs/adr/_TEMPLATE.md "$ADR_FILE"
sed -i '' "s/ADR-XXX/ADR-${ADR_NUMBER}/g" "$ADR_FILE"
sed -i '' "s/\[Decision Title\]/${ADR_TITLE}/g" "$ADR_FILE"
sed -i '' "s/YYYY-MM-DD/$(date +%Y-%m-%d)/g" "$ADR_FILE"

echo "Created: $ADR_FILE"
open "$ADR_FILE"
```

**Usage:**
```bash
bash scripts/docs/create_adr.sh "Switch to PostgreSQL JSONB"
# Creates: docs/adr/011-switch-to-postgresql-jsonb.md
```

### 4. Code Documentation Standards

**Goal:** Consistent, comprehensive docstrings

**Python Docstring Standard (Google Style):**
```python
def extract_game_data(game_id: int, source: str = "espn") -> dict:
    """Extract raw game data from specified source.

    Retrieves complete game data including play-by-play, box scores,
    and metadata. Supports multiple data sources with automatic
    fallback if primary source fails.

    Args:
        game_id: NBA game ID (e.g., 401584866)
        source: Data source name. Options: 'espn', 'nba_api', 'hoopr'
            Default: 'espn'

    Returns:
        Dictionary containing:
            - 'game_id': int - Game identifier
            - 'date': datetime - Game date/time
            - 'home_team': str - Home team abbreviation
            - 'away_team': str - Away team abbreviation
            - 'play_by_play': list[dict] - All game events
            - 'box_score': dict - Final box score

    Raises:
        ValueError: If game_id is invalid or source is unknown
        requests.HTTPError: If API request fails
        DataQualityError: If extracted data fails validation

    Examples:
        >>> game_data = extract_game_data(401584866, source='espn')
        >>> print(game_data['home_team'])
        'LAL'

        >>> game_data = extract_game_data(401584866, source='nba_api')
        >>> len(game_data['play_by_play'])
        342

    Notes:
        - Automatically caches results to reduce API calls
        - Retries up to 3 times on transient failures
        - Falls back to alternate source if primary fails

    See Also:
        - validate_game_data(): Validates extracted data
        - upload_to_s3(): Uploads extracted data to S3
    """
    pass
```

**Enforce with linter:**
```bash
# Install pydocstyle
pip install pydocstyle

# Check docstring coverage
pydocstyle scripts/ notebooks/ --count

# Add to pre-commit hooks
# .pre-commit-config.yaml
- repo: https://github.com/PyCQA/pydocstyle
  rev: 6.3.0
  hooks:
    - id: pydocstyle
      args: ['--ignore=D100,D104']  # Allow missing module/package docstrings
```

### 5. API Versioning Strategy

**Goal:** Backwards compatibility and graceful deprecation

**Versioning Policy:**
```markdown
# API Versioning Policy

## Version Format
- **URL-based versioning:** `/api/v1/`, `/api/v2/`
- **Semantic versioning** for breaking changes

## Version Lifecycle

1. **Active Support (v1)**
   - All features available
   - Bug fixes and security updates
   - New features may be added

2. **Deprecated (v0)**
   - Still functional but discouraged
   - Security updates only
   - Deprecation warnings in responses
   - 6-month sunset notice

3. **Sunset (removed)**
   - No longer available
   - Returns 410 Gone with migration guide

## Breaking Changes

Require new major version:
- Removing endpoints
- Changing request/response schema (incompatible)
- Changing authentication method
- Changing rate limits (more restrictive)

Don't require new version:
- Adding new endpoints
- Adding optional fields to requests
- Adding fields to responses
- Bug fixes

## Deprecation Process

1. Announce deprecation 6 months in advance
2. Add `Deprecation` header to responses
3. Document migration path in API docs
4. Sunset old version after grace period
```

**Deprecation Header Example:**
```python
from flask import Response

@app.route('/api/v1/old-endpoint')
def old_endpoint():
    response = Response(...)
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = 'Wed, 01 Apr 2026 00:00:00 GMT'
    response.headers['Link'] = '</api/v2/new-endpoint>; rel="successor-version"'
    return response
```

### 6. Auto-Generated Reference Documentation

**Goal:** Always up-to-date API reference

**Using Sphinx for Python:**
```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Initialize Sphinx
mkdir docs/reference
cd docs/reference
sphinx-quickstart

# Configure conf.py
echo "
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # Google-style docstrings
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

html_theme = 'sphinx_rtd_theme'
" >> conf.py

# Generate reference docs
sphinx-apidoc -o source/ ../../scripts/ ../../notebooks/

# Build HTML
make html
open _build/html/index.html
```

**Auto-rebuild on changes:**
```bash
# Install sphinx-autobuild
pip install sphinx-autobuild

# Watch for changes
sphinx-autobuild docs/reference/source docs/reference/_build/html
```

---

## Success Criteria

**Minimum Viable Product (MVP):**
- ✅ Swagger specs for 3 core APIs
- ✅ Developer onboarding guide
- ✅ ADR template and 10 existing ADRs documented
- ✅ Docstring standards enforced via pre-commit
- ✅ API versioning policy documented

**Full Success:**
- ✅ All APIs documented with Swagger
- ✅ Auto-generated reference docs (Sphinx)
- ✅ API versioning implemented
- ✅ Comprehensive runbooks for common operations
- ✅ Documentation site deployed (GitHub Pages)

---

## Implementation Plan

### Week 1: API Documentation
**Days 1-2:**
- Create Swagger specs for Data Collection API
- Create Swagger specs for Temporal Query API
- Create Swagger specs for ADCE Management API

**Days 3-4:**
- Generate HTML documentation with Redoc
- Create developer onboarding guide
- Test onboarding with new team member

**Day 5:**
- Create ADR template
- Document existing architectural decisions
- Standardize ADR creation process

### Week 2: Code Standards & Automation
**Days 1-2:**
- Define docstring standards (Google style)
- Add pydocstyle to pre-commit hooks
- Audit existing code for docstring coverage

**Days 3-4:**
- Set up Sphinx for auto-generated docs
- Configure sphinx-autobuild
- Deploy documentation site (GitHub Pages)

**Day 5:**
- Create API versioning policy
- Implement deprecation headers
- End-to-end validation

---

## Cost Breakdown

| Component | Configuration | Monthly Cost | Notes |
|-----------|--------------|--------------|-------|
| GitHub Pages | Documentation hosting | $0 | Free for public repos |
| Redoc/Swagger | API documentation | $0 | Open source tools |
| Sphinx | Reference docs | $0 | Open source tool |
| **Total** | | **$0/month** | Zero cost |

**Development Time:** 2 weeks (80 hours)

---

## Prerequisites

**Before starting 0.0021:**
- [x] Existing documentation (1,720 markdown files)
- [x] ADR system initiated (ADR-010 exists)
- [ ] APIs to document (may be minimal until Phase 3/4)
- [ ] GitHub Pages enabled (or alternative hosting)

---

## Integration with Existing Systems

### Phase Documentation
- Standardize phase README templates
- Ensure all sub-phases follow power directory structure
- Auto-generate phase navigation

### DIMS (Data Inventory Management System)
- Document DIMS CLI in Swagger
- Create DIMS developer guide
- Auto-generate DIMS metric reference

### ADCE (Autonomous Data Collection Ecosystem)
- Document ADCE APIs (health, queue, tasks)
- Create ADCE operator runbook
- Standardize ADCE error codes

---

## Files to Create

**API Specifications:**
```
api_specs/data_collection.yaml          # Data collection APIs
api_specs/temporal_queries.yaml         # Temporal query APIs
api_specs/adce_management.yaml          # ADCE control APIs
api_specs/dims_metrics.yaml             # DIMS APIs
```

**Guides:**
```
docs/DEVELOPER_ONBOARDING.md            # New developer guide
docs/API_VERSIONING_POLICY.md           # Versioning standards
docs/DOCSTRING_STANDARDS.md             # Code documentation guide
docs/RUNBOOK_TEMPLATE.md                # Operational runbooks
```

**Templates:**
```
docs/adr/_TEMPLATE.md                   # ADR template
scripts/docs/create_adr.sh              # ADR creation script
```

**Generated Docs:**
```
docs/api/data_collection.html           # Redoc HTML (auto-generated)
docs/api/temporal_queries.html          # Redoc HTML
docs/reference/_build/html/             # Sphinx output (auto-generated)
```

---

## Common Issues & Solutions

### Issue 1: Swagger specs out of sync with code
**Cause:** Manual editing, no validation
**Solution:**
- Use code-first approach (generate specs from code)
- Add swagger-cli validation to pre-commit hooks
- Auto-generate specs from Flask/FastAPI decorators

### Issue 2: Developers don't read documentation
**Cause:** Documentation hard to find or outdated
**Solution:**
- Link docs prominently in README
- Keep docs short and actionable
- Add "Last Updated" timestamps
- Make docs searchable (Algolia DocSearch)

### Issue 3: Docstrings incomplete or incorrect
**Cause:** No enforcement, unclear standards
**Solution:**
- Enforce with pydocstyle in pre-commit hooks
- Use automated coverage reports
- Code review checklist includes docstring check

### Issue 4: ADRs not created for decisions
**Cause:** Process friction, unclear when to create
**Solution:**
- Make ADR creation effortless (shell script)
- Define clear triggers (architectural changes, cost impact >$10/mo)
- Review ADRs in retrospectives

---

## Workflows Referenced

- **Workflow #6:** File Creation - Creating documentation files
- **Workflow #2:** Command Logging - Documenting commands
- **Workflow #57:** Phase-README Alignment - Validating documentation

---

## Related Documentation

**Documentation System:**
- [DOCUMENTATION_SYSTEM.md](../../../DOCUMENTATION_SYSTEM.md) - Current system
- [CONTEXT_MANAGEMENT_GUIDE.md](../../../CONTEXT_MANAGEMENT_GUIDE.md) - File size guidelines

**ADRs:**
- [ADR-010](../../adr/010-four-digit-subphase-numbering.md) - Four-Digit Sub-Phase Numbering

**Workflows:**
- [Workflow #57: Phase-README Alignment](../../../claude_workflows/workflow_descriptions/57_phase_readme_alignment.md)

---

## Navigation

**Return to:** [Phase 0 Index](../PHASE_0_INDEX.md)

**Prerequisites:** None (foundational)

**Integrates with:**
- 0.0019: Testing Infrastructure - Test documentation
- 0.0020: Monitoring & Observability - Monitoring runbooks
- All phases - READMEs and documentation

---

## How This Enables the Simulation Vision

This sub-phase provides **documentation infrastructure** that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this sub-phase enables:**

### 1. Econometric Causal Inference
From this sub-phase's documentation, we can:
- **Understand methodologies** via clear API docs (which panel data endpoints exist)
- **Reproduce results** with documented parameters and configurations
- **Validate assumptions** recorded in ADRs

### 2. Nonparametric Event Modeling
From this sub-phase's standards, we build:
- **Well-documented event APIs** (play-by-play access patterns)
- **Reproducible kernel density estimation** (parameters documented)
- **Versioned simulation configs** (API versioning ensures compatibility)

### 3. Context-Adaptive Simulations
Using this sub-phase's guides, simulations can:
- **Onboard new developers** quickly (faster iteration)
- **Integrate external systems** via Swagger specs
- **Maintain long-term** via ADRs and runbooks

**See [main README](../../../README.md) for complete methodology.**

---

**Last Updated:** October 25, 2025 (Migrated from 6.0002)
**Status:** ⏸️ PENDING - Ready for implementation
**Migrated By:** Comprehensive Phase Reorganization (ADR-010)

---

## Implementation Summary

**Completion Date:** November 1, 2025
**Status:** ✅ COMPLETE

### Deliverables

#### 1. Swagger/OpenAPI Specifications ✅

**Location:** `api_specs/`

- **adce_data_collection_api.yaml** (600+ lines)
  - ADCE health monitoring endpoints
  - Task queue management
  - Reconciliation operations
  - Scraper management

- **monitoring_observability_api.yaml** (350+ lines)
  - DIMS metrics API
  - CloudWatch integration
  - Health monitoring endpoints

- **temporal_query_api.yaml** (150+ lines)
  - Player statistics queries
  - Team statistics queries
  - Game state queries

**Features:**
- OpenAPI 3.0.3 specification
- Comprehensive endpoint documentation
- Request/response schemas
- Example payloads
- Error responses

#### 2. Developer Documentation ✅

**Previously Completed:**

- **docs/DEVELOPER_ONBOARDING.md** (430 lines)
  - Environment setup
  - Development workflow
  - Coding standards
  - Testing procedures
  - Contribution guidelines

- **docs/API_VERSIONING_POLICY.md** (550 lines)
  - Semantic versioning strategy
  - Deprecation policy
  - Backward compatibility
  - Version migration guides

- **docs/DOCSTRING_STANDARDS.md** (680 lines)
  - Google-style docstring format
  - Napoleon extension usage
  - Type hints
  - Examples and best practices

#### 3. Sphinx Auto-Documentation ✅

**Location:** `docs/sphinx/`

**Files Created:**
- `conf.py` - Sphinx configuration with autodoc, napoleon, viewcode
- `index.rst` - Main documentation index
- `Makefile` - Build automation
- `api/monitoring.rst` - Monitoring API reference
- `api/autonomous.rst` - ADCE API reference
- `api/database.rst` - Database API reference
- `api/utils.rst` - Utilities API reference
- `README.md` - Build instructions

**Features:**
- Auto-generation from Python docstrings
- Google/NumPy docstring support (Napoleon)
- Source code links (viewcode)
- Intersphinx linking to external docs
- HTML output with Alabaster theme

**Build Commands:**
```bash
cd docs/sphinx
make html
make serve  # View at http://localhost:8000
```

### What's Complete

- [x] Swagger/OpenAPI API specifications
- [x] Developer onboarding guide
- [x] API versioning policy
- [x] Docstring standards
- [x] ADR (Architecture Decision Records) system
- [x] Sphinx auto-documentation framework
- [x] API reference generation

### Usage Examples

#### Viewing Swagger Specs

```bash
# Install Swagger UI (optional)
npm install -g swagger-ui

# Serve API specs
swagger-ui serve api_specs/adce_data_collection_api.yaml
```

Or use online viewer:
```
https://editor.swagger.io/
# Paste content from api_specs/*.yaml
```

#### Building Sphinx Docs

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Build HTML documentation
cd docs/sphinx
make html

# View documentation
open _build/html/index.html
```

### Integration with Existing Systems

The documentation framework integrates with:

- **Phase 0.0020** - CloudWatch monitoring APIs documented
- **Phase 0.0018** - ADCE endpoints documented
- **Phase 0.0019** - DIMS APIs documented

### Benefits

1. **API Consumers:** Machine-readable API specifications enable automated client generation
2. **Developer Onboarding:** Comprehensive guides reduce onboarding time from days to hours
3. **Code Quality:** Docstring standards ensure consistent, well-documented code
4. **Knowledge Preservation:** ADR system documents architectural decisions
5. **External Integrations:** Swagger specs enable easy API integration
6. **Auto-Generated Docs:** Sphinx reduces documentation maintenance burden

---

**Phase 0.0021 Complete** ✅
**Files Created:** 10+ files
**Lines of Documentation:** ~3,000+ lines
**Time Investment:** ~2 hours
**Cost:** $0

