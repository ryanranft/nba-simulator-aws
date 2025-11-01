# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the NBA Game Simulator & ML Platform project.

## What are ADRs?

Architecture Decision Records document significant architectural and technical decisions made during project development. They provide context for future developers (including LLMs) to understand:

- **Why** decisions were made
- **What** alternatives were considered
- **What** consequences resulted from the decision

## Purpose

ADRs help:
- ✅ Prevent revisiting settled questions
- ✅ Provide context for new team members
- ✅ Document rationale for technical choices
- ✅ Track evolution of project architecture
- ✅ Help LLMs (like Claude Code) understand project decisions

## ADR Index

### Active ADRs

| ID | Title | Date | Status | Summary |
|----|-------|------|--------|---------|
| [001](001-redshift-exclusion.md) | Redshift Exclusion | 2025-09-29 | Accepted | Use RDS PostgreSQL instead of Redshift to save $200-600/month during development |
| [002](002-data-extraction-strategy.md) | 10% Data Extraction | 2025-09-29 | Accepted | Extract only 10% of JSON fields to reduce storage from 119 GB → 12 GB |
| [003](003-python-version.md) | Python 3.11 | 2025-09-29 | Accepted | Use Python 3.11 for AWS Glue compatibility and performance |
| [005](005-git-ssh-authentication.md) | Git SSH Auth | 2025-09-30 | Resolved | Use SSH instead of HTTPS for GitHub authentication |
| [006](006-session-initialization-automation.md) | Session Init Automation | 2025-10-01 | Accepted | Automated session startup and post-commit version tracking |
| [007](007-documentation-trigger-system.md) | Documentation Trigger System | 2025-10-01 | Accepted | HTML comment triggers + central registry for automatic documentation updates |
| [008](008-phase-reorganization.md) | Phase Reorganization | 2025-10-08 | Accepted | Redistribute 214 book recommendations into focused phases |
| [009](009-temporal-panel-data-architecture.md) | Temporal Panel Data Architecture | 2025-10-08 | Accepted | Econometric + nonparametric hybrid simulation framework |
| [010](010-four-digit-subphase-numbering.md) | Four-Digit Sub-Phase Numbering | 2025-10-25 | Implemented | Zero-padded 4-digit format (N.MMMM) for sub-phases |

### Superseded ADRs

| ID | Title | Status | Superseded By |
|----|-------|--------|---------------|
| 004 | Git Without GitHub Push | Complete | [ADR-005](005-git-ssh-authentication.md) |

## Quick Reference

### Cost Optimization Decisions
- **ADR-001:** Exclude Redshift (save $200-600/month)
- **ADR-002:** Extract 10% of data (save $9/month storage)

### Technical Compatibility Decisions
- **ADR-003:** Python 3.11 (AWS Glue compatibility)
- **ADR-005:** SSH authentication (security and convenience)

### Data Architecture Decisions
- **ADR-002:** 10% extraction strategy (119 GB → 12 GB)
- **ADR-001:** RDS for OLTP + OLAP (not Redshift)

## How to Use ADRs

### For Humans

1. **Starting work?** Read ADRs related to your area
2. **Making a decision?** Check if already documented
3. **Proposing change?** Reference relevant ADRs
4. **Need context?** ADRs explain "why" not just "what"

### For LLMs (like Claude Code)

When working on this project:
1. **Read `README.md` first** for ADR index
2. **Reference relevant ADRs** when making technical decisions
3. **Don't propose alternatives** already rejected in ADRs
4. **Update ADRs** if decisions change
5. **Create new ADRs** for significant new decisions

## Creating a New ADR

### Automated Method (Recommended)

Use the ADR creation script for automatic numbering and templating:

```bash
# Create new ADR with automatic numbering
bash scripts/docs/create_adr.sh "your-decision-title"

# Example:
bash scripts/docs/create_adr.sh "adopt-cloudwatch-monitoring"
# Creates: docs/adr/011-adopt-cloudwatch-monitoring.md
```

The script will:
- ✅ Calculate the next ADR number automatically
- ✅ Copy from `_TEMPLATE.md`
- ✅ Fill in date and placeholders
- ✅ Open in your default editor
- ✅ Remind you to update this README

### Manual Method

If you prefer to create ADRs manually:

1. **Copy the template:**
   ```bash
   cp docs/adr/_TEMPLATE.md docs/adr/011-your-decision.md
   ```

2. **Fill out all sections:**
   - **Context:** What problem are we solving?
   - **Decision:** What are we doing?
   - **Rationale:** Why this approach?
   - **Alternatives:** What else did we consider?
   - **Consequences:** What are the trade-offs?
   - **Implementation:** How will we do it?
   - **Success Metrics:** How do we measure success?

3. **Number sequentially:**
   - Next ADR: 011
   - Use format: `0XX-brief-title.md` (3 digits, zero-padded)

4. **Update this README:**
   - Add entry to index table above
   - Update "Total ADRs" count at bottom
   - Update "Next ADR Number" at bottom

## ADR Status Values

- **Proposed:** Decision suggested, not yet approved
- **Accepted:** Decision approved and active
- **Deprecated:** No longer recommended, but not replaced
- **Superseded:** Replaced by newer decision (link to new ADR)

## Decision Categories

### Infrastructure
- ADR-001: Redshift Exclusion
- ADR-003: Python 3.11
- ADR-005: Git SSH Authentication

### Data Architecture
- ADR-002: 10% Data Extraction Strategy

### Development Workflow
- ADR-006: Session Initialization Automation
- ADR-007: Documentation Trigger System

### Process
- ADR-004: Git Without GitHub Push (superseded)
- ADR-005: Git SSH Authentication

## Reviewing ADRs

Some ADRs have scheduled review dates:

| ADR | Review Trigger | Expected Date |
|-----|---------------|---------------|
| 001 | Query latency >30s OR 3 months usage | 2026-01-01 |
| 002 | After initial ETL completion | TBD |
| 003 | AWS Glue adds Python 3.12 support | ~2026 |
| 005 | No review needed | N/A |
| 006 | Session startup slow or credential issues | 2025-04-01 |
| 007 | Documentation maintenance becomes burdensome | 2026-01-01 |

## Related Documentation

- **PROGRESS.md:** Original ADR content (detailed version)
- **CLAUDE.md:** Quick reference for LLMs
- **docs/COMMAND_LOG_SANITIZATION.md:** Implementation details

## Best Practices

### When to Create an ADR

✅ **DO create ADR for:**
- Significant architectural decisions
- Technology choices (databases, languages, services)
- Major trade-offs (cost vs performance, simplicity vs scalability)
- Decisions that affect multiple parts of the system

❌ **DON'T create ADR for:**
- Small implementation details
- Temporary workarounds
- Obvious choices with no alternatives
- Reversible decisions with no consequences

### Writing Good ADRs

**Good ADR:**
- Explains context and constraints
- Lists alternatives considered
- Documents trade-offs clearly
- Provides rationale, not just decision
- Includes success metrics

**Bad ADR:**
- Only states the decision
- No explanation of "why"
- Missing alternatives
- No consideration of consequences
- Vague or unclear

## Template Overview

See [_TEMPLATE.md](_TEMPLATE.md) for the full template structure:

```markdown
# ADR-XXX: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed | Accepted | Deprecated | Superseded]

## Context
## Decision
## Rationale
## Alternatives Considered
## Consequences
## Implementation
## Success Metrics
## Review Date
## References
```

## Questions?

- See [_TEMPLATE.md](_TEMPLATE.md) for detailed structure
- Use `bash scripts/docs/create_adr.sh "title"` to create new ADRs
- Reference existing ADRs for examples
- Check PROGRESS.md for original detailed versions
- Ask in project discussions

---

**Last Updated:** 2025-10-31
**Total ADRs:** 10 (9 active, 1 superseded)
**Next ADR Number:** 011
**ADR Creation Script:** `scripts/docs/create_adr.sh`