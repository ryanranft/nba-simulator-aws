# Workflow #28: ADR (Architecture Decision Record) Creation

**Category:** Documentation
**Priority:** High
**When to Use:** After making significant architectural decisions
**Related Workflows:** #12 (Documentation Triggers), #5 (Task Execution)

---

## Overview

Architecture Decision Records (ADRs) document important technical decisions that have long-term impact on the project. This workflow defines when and how to create ADRs.

**Purpose:** Preserve context for why decisions were made, not just what was decided.

---

## What is an ADR?

An ADR is a document that captures:
- **Context:** What was the situation/problem?
- **Decision:** What did we decide to do?
- **Consequences:** What are the trade-offs?
- **Alternatives:** What else did we consider?

**Format:** Markdown file following template at `docs/adr/template.md`

**Location:** `docs/adr/XXX-short-title.md`

---

## When to Create an ADR

### ✅ CREATE ADR For:

#### 1. Significant Architectural Decisions
```markdown
Examples:
- Choosing RDS over DynamoDB for data storage
- Selecting Python 3.11 for Glue compatibility
- Excluding Redshift to save costs
- Using S3 for raw data lake instead of database
```

**Trigger:** Decision affects multiple components or is hard to reverse

#### 2. Technology Choices with Long-Term Impact
```markdown
Examples:
- Choosing PostgreSQL over MySQL
- Selecting Conda over venv for environment management
- Using boto3 for AWS SDK
- Choosing pytest over unittest
```

**Trigger:** Choice locks in dependencies or affects team workflow

#### 3. Major Trade-Offs
```markdown
Examples:
- Cost vs performance (extracting 10% of data instead of 100%)
- Simplicity vs scalability (starting with single RDS vs sharding)
- Storage vs compute (pre-aggregating vs real-time calculations)
```

**Trigger:** Decision has clear pros and cons that future developers need to understand

#### 4. Decisions Affecting Multiple Parts of System
```markdown
Examples:
- Authentication method (affects API, database, frontend)
- Logging strategy (affects all services)
- Error handling approach (affects all code)
- Data validation rules (affects ETL, API, simulation)
```

**Trigger:** Change would require modifying 3+ different components

#### 5. Rejecting Common Approaches
```markdown
Examples:
- Why NOT using Redshift (ADR-001)
- Why NOT extracting all data (ADR-002)
- Why NOT using GitHub push initially (ADR-004, superseded)
- Why NOT using Lambda for ETL
```

**Trigger:** Future developers might wonder "Why didn't they just use X?"

#### 6. Development Workflow Changes
```markdown
Examples:
- Adopting Git without remote push (ADR-004)
- Switching to SSH authentication (ADR-005)
- Automating session initialization (ADR-006)
- Implementing documentation trigger system (ADR-007)
```

**Trigger:** Change affects how team works on daily basis

---

### ❌ DON'T CREATE ADR For:

#### 1. Small Implementation Details
```markdown
Examples:
- Variable naming conventions (use STYLE_GUIDE.md instead)
- File organization within a module
- Code formatting preferences
- Comment style
```

**Reason:** Too low-level, belongs in style guide

#### 2. Temporary Workarounds
```markdown
Examples:
- Quick fix for a bug
- Temporary patch until proper solution
- Hotfix for production issue
```

**Reason:** Not a long-term decision, will be replaced

#### 3. Obvious Choices with No Alternatives
```markdown
Examples:
- Using JSON for API responses
- Using Git for version control
- Using Python for data science
- Using SQL for relational queries
```

**Reason:** Industry standard, no decision was made

#### 4. Easily Reversible Decisions
```markdown
Examples:
- UI colors or themes
- Log message format
- Temporary feature flags
- Development shortcuts
```

**Reason:** Can be changed without consequences

---

## ADR Creation Workflow

### Step 1: Identify Decision Trigger

Ask yourself:
- [ ] Is this decision significant and long-term?
- [ ] Will future developers wonder why we did this?
- [ ] Are there trade-offs that need explanation?
- [ ] Does this reject a common/obvious alternative?

If **YES to 2 or more**, create an ADR.

---

### Step 2: Read the Template

```bash
# Review ADR template
cat docs/adr/template.md
```

**Template sections:**
1. **Status:** Proposed / Accepted / Deprecated / Superseded
2. **Context:** What problem are we solving?
3. **Decision:** What did we decide?
4. **Consequences:** What are the trade-offs?
5. **Alternatives Considered:** What else did we evaluate?

---

### Step 3: Determine ADR Number

```bash
# List existing ADRs
ls -1 docs/adr/*.md | grep -E '^[0-9]{3}-'

# Current ADRs:
# 001-redshift-exclusion.md
# 002-data-extraction-strategy.md
# 003-python-version.md
# 004-git-without-github-push.md (superseded)
# 005-git-ssh-authentication.md
# 006-session-initialization-automation.md
# 007-documentation-trigger-system.md

# Next number: 008
```

**Numbering:**
- Use 3 digits with leading zeros (001, 002, 003...)
- Sequential (no gaps)
- Never reuse numbers

---

### Step 4: Create ADR File

```bash
# Copy template
cp docs/adr/template.md docs/adr/008-short-descriptive-title.md

# Edit in text editor
nano docs/adr/008-short-descriptive-title.md
```

**Filename format:**
- `XXX-short-title.md`
- Use dashes, not underscores
- Lowercase
- Descriptive but concise

**Examples:**
- ✅ `003-python-version.md`
- ✅ `005-git-ssh-authentication.md`
- ❌ `003-Python Version Decision.md` (spaces, capitals)
- ❌ `005_git_ssh.md` (underscores)

---

### Step 5: Fill in ADR Content

#### Section 1: Status
```markdown
**Status:** Accepted
**Date:** 2025-10-02
**Deciders:** Ryan Ranft, Claude Code
```

**Statuses:**
- **Proposed:** Under consideration
- **Accepted:** Decision made and implemented
- **Deprecated:** No longer recommended
- **Superseded by ADR-XXX:** Replaced by newer decision

#### Section 2: Context
```markdown
## Context

Describe the situation that led to this decision:
- What problem are we solving?
- What constraints exist?
- What are the requirements?
- What triggered this decision?

Be specific with data:
- Cost estimates
- Performance requirements
- Timeline constraints
- Technical limitations
```

**Example:**
```markdown
## Context

AWS Redshift costs $200-600/month for even small clusters. Our NBA
simulator is a learning project with a budget target of $150/month total.

We need to store 146,115 JSON files (119 GB) and query them for:
- Game simulation (historical data lookup)
- ML training (feature extraction)
- Analytics (aggregations, player stats)

S3 storage costs $0.023/GB/month ($2.74 for our data).
```

#### Section 3: Decision
```markdown
## Decision

We will [clear statement of decision].

Specific approach:
1. First component/action
2. Second component/action
3. Third component/action
```

**Example:**
```markdown
## Decision

We will exclude AWS Redshift from the architecture and use S3 + Athena
for analytics queries instead.

Architecture:
1. Store raw JSON in S3 ($2.74/month)
2. Load structured data into RDS PostgreSQL ($29/month)
3. Use Athena for ad-hoc queries on S3 ($5/TB scanned)
4. Use RDS for simulation and ML feature queries
```

#### Section 4: Consequences

```markdown
## Consequences

### Positive
- Benefit 1
- Benefit 2
- Benefit 3

### Negative
- Drawback 1
- Drawback 2
- Mitigation strategy for each

### Neutral
- Other impacts
```

**Example:**
```markdown
## Consequences

### Positive
- **Cost savings:** $200-600/month saved (Redshift excluded)
- **Simplicity:** One less AWS service to manage
- **Budget compliance:** Stays within $150/month target

### Negative
- **Query performance:** Athena slower than Redshift for complex queries
  - Mitigation: Pre-aggregate data in RDS for common queries
- **Learning opportunity:** Won't learn Redshift architecture
  - Mitigation: Can add Redshift later if needed

### Neutral
- S3 + Athena pattern common in industry (good learning)
```

#### Section 5: Alternatives Considered
```markdown
## Alternatives Considered

### Option 1: [Alternative Name]
**Pros:**
- Benefit 1
- Benefit 2

**Cons:**
- Drawback 1
- Drawback 2

**Why rejected:** [Clear reason]

### Option 2: [Alternative Name]
[Same structure]
```

---

### Step 6: Update ADR Index

```bash
# Edit docs/adr/README.md
nano docs/adr/README.md
```

**Add entry:**
```markdown
## ADRs

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [ADR-008](008-short-title.md) | Short Title | Accepted | 2025-10-02 |
```

---

### Step 7: Commit ADR

```bash
# Stage ADR
git add docs/adr/008-short-title.md docs/adr/README.md

# Commit
git commit -m "Add ADR-008: [Short Title]

Document decision to [what was decided] instead of [alternative].

Key trade-offs:
- Pro: [main benefit]
- Con: [main drawback]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## ADR Lifecycle

### When to Update an ADR

**If decision changes:**
1. **Minor update:** Edit ADR, add note at bottom
2. **Major change:** Create new ADR that supersedes old one

**Example minor update:**
```markdown
---
**Update 2025-10-15:** Added Athena query optimization strategy.
```

**Example superseding:**
```markdown
# ADR-004: Git Without GitHub Push

**Status:** Superseded by ADR-005
**Date:** 2025-10-01
```

Then create ADR-005 with new decision.

### When to Deprecate an ADR

```markdown
**Status:** Deprecated
**Date:** 2025-11-01
**Reason:** Feature removed from project scope
```

**Keep the ADR** - provides historical context.

---

## ADR Quality Checklist

Before committing ADR:
- [ ] Number is sequential and unique
- [ ] Filename follows convention (XXX-short-title.md)
- [ ] Status is clear (Proposed/Accepted/Deprecated/Superseded)
- [ ] Context explains WHY decision was needed
- [ ] Decision is clear and specific
- [ ] Consequences list both pros and cons
- [ ] Alternatives section shows what was considered
- [ ] Updated docs/adr/README.md index
- [ ] Committed to git

---

## Example ADRs in This Project

### ADR-001: Redshift Exclusion
- **Context:** Budget constraints ($150/month)
- **Decision:** Use S3 + Athena instead of Redshift
- **Consequence:** Saves $200-600/month

### ADR-002: Data Extraction Strategy
- **Context:** 146,115 files = 119 GB
- **Decision:** Extract 10% of data (12 GB)
- **Consequence:** Reduces costs, sufficient for learning

### ADR-003: Python Version
- **Context:** AWS Glue requires Python 3.11
- **Decision:** Use Python 3.11.13
- **Consequence:** Compatibility with Glue, stable ecosystem

### ADR-005: Git SSH Authentication
- **Context:** HTTPS authentication deprecated by GitHub
- **Decision:** Use SSH keys for git operations
- **Consequence:** More secure, no password prompts

---

## Common ADR Mistakes

### ❌ Mistake 1: Too Vague
```markdown
## Decision
We will use a database.
```

**✅ Better:**
```markdown
## Decision
We will use PostgreSQL 15 on AWS RDS (db.t3.micro instance) for storing
structured NBA game data extracted from S3.
```

### ❌ Mistake 2: No Context
```markdown
## Decision
We chose Python 3.11.
```

**✅ Better:**
```markdown
## Context
AWS Glue requires Python 3.11 for compatibility. Python 3.12 is not yet
supported. Python 3.10 would work but lacks performance improvements.

## Decision
We will use Python 3.11.13 (latest 3.11.x release).
```

### ❌ Mistake 3: Missing Trade-Offs
```markdown
## Consequences
This is the best solution!
```

**✅ Better:**
```markdown
## Consequences

### Positive
- Compatible with AWS Glue
- Stable ecosystem

### Negative
- Can't use Python 3.12 features (e.g., improved error messages)
- Will need to upgrade when Glue supports 3.12
```

---

## Integration with Other Workflows

**After creating ADR:**
1. Run `make inventory` to update FILE_INVENTORY.md (workflow #13)
2. Commit ADR (workflow #8)
3. If changing project approach, update PROGRESS.md (workflow #4)

**Reference ADRs in:**
- PROGRESS.md (link to ADR for context)
- README.md (mention key architectural decisions)
- Code comments (explain why code follows ADR decision)

---

## Resources

**Templates and Examples:**
- `docs/adr/template.md` - ADR template
- `docs/adr/README.md` - Index of all ADRs
- `docs/adr/001-redshift-exclusion.md` - Example ADR

**References:**
- [ADR GitHub](https://adr.github.io/)
- [Joel Parker Henderson's ADR templates](https://github.com/joelparkerhenderson/architecture-decision-record)

---

**Last Updated:** 2025-10-02
**Source:** docs/SESSION_INITIALIZATION.md (lines 123-140)
