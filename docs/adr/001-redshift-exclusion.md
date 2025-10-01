# ADR-001: Redshift Exclusion for Initial Development

**Date:** September 29, 2025
**Status:** Accepted
**Decision Maker:** Project team based on cost-benefit analysis

## Context

The original architecture plan (v4) included Amazon Redshift as a data warehouse for analytical queries and ML feature engineering. Redshift offers columnar storage, massive parallel processing, and is optimized for OLAP workloads.

The project involves:
- 146,115 JSON files (119 GB raw data)
- ~12 GB after 10% field extraction
- Primary use cases: game simulations and ML predictions
- Learning-focused project, not production analytics platform

## Decision

**Exclude Redshift from initial implementation.** Use RDS PostgreSQL for both OLTP and OLAP workloads during development and learning phases.

## Rationale

### 1. Cost Optimization

**Redshift Costs:**
- Serverless: $270-660/month (16-32 RPUs)
- Provisioned: $180-783/month minimum

**RDS PostgreSQL Costs:**
- db.t3.small: $29/month
- db.t3.medium: $60/month

**Savings:** $200-600/month during development

### 2. Data Size

- Extracted data: ~12 GB (after 10% field extraction)
- RDS handles this size efficiently with acceptable query performance
- Redshift benefits only materialize at 50+ GB with complex analytical queries
- Our dataset is well within RDS's optimal range

### 3. Learning Objectives

- Primary goal: Learning AWS architecture patterns
- RDS provides sufficient functionality to understand ETL and database design
- Can add Redshift later when/if needed
- Simpler architecture = easier to understand and debug

### 4. Query Complexity

- **Initial use case:** Simulation queries (single-game lookups)
  - RDS excels at OLTP workloads like this
- **Analytical queries:** Occasional, not real-time
  - RDS provides acceptable performance (2-5 seconds)
- **User concurrency:** Single developer, not multiple analysts
  - No need for massive parallel processing

## Alternatives Considered

### Alternative 1: Redshift Serverless
- **Pros:** Automatic scaling, pay-per-query, no cluster management
- **Cons:** $270-660/month minimum cost, overkill for 12 GB dataset
- **Why rejected:** Cost not justified for learning project with small dataset

### Alternative 2: Redshift Provisioned (dc2.large)
- **Pros:** Predictable performance, lower cost than serverless
- **Cons:** Still $180+/month, requires cluster management, always-on billing
- **Why rejected:** Still expensive for the dataset size and use case

### Alternative 3: AWS Athena Only (No Database)
- **Pros:** $5/TB scanned, serverless, query S3 directly
- **Cons:** Not suitable for OLTP (simulation queries), slow for repeated queries
- **Why rejected:** Simulations need fast repeated lookups, not ad-hoc analytics

## Consequences

### Positive
- **Lower monthly costs:** Save $200-600/month during development
- **Simpler architecture:** Fewer services to manage and debug
- **Faster setup:** RDS provisions in 10-20 minutes vs learning Redshift
- **Easier local development:** Can run PostgreSQL locally for testing

### Negative
- **Slower analytical queries:** 2-5 seconds vs 0.5-1 second on Redshift
- **Limited to single-node:** Cannot leverage distributed processing
- **No columnar storage:** Less efficient for wide analytical queries
- **Scaling ceiling:** Will need migration if dataset grows to 100+ GB

### Mitigation
- Use AWS Athena ($5/TB scanned) for ad-hoc complex queries if RDS becomes bottleneck
- Add read replicas if query load increases
- Implement query result caching for repeated analytical queries
- Monitor query performance; if consistently >30 seconds, revisit decision

## Implementation

Already implemented:
- ✅ Architecture documentation updated
- ✅ Cost estimates revised
- ✅ RDS selected as primary database

Pending:
- ⏸️ Provision RDS PostgreSQL instance (Phase 3.1)
- ⏸️ Create database schema
- ⏸️ Monitor query performance during development

## Success Metrics

This decision is successful if:
- ✅ Monthly AWS costs stay under $100 during development
- ✅ Simulation queries execute in <1 second
- ✅ Analytical queries execute in <30 seconds
- ✅ Database storage stays under 20 GB
- ✅ No need to add Redshift within first 6 months

## Migration Path

If future requirements demand Redshift:

1. Keep RDS for OLTP (simulation queries remain fast)
2. Add Redshift Serverless for OLAP (analytics only)
3. Use AWS Glue to replicate RDS → Redshift nightly
4. Point analytical queries to Redshift
5. Estimated migration time: 2-4 hours
6. Cost increase: +$270-660/month

**Migration triggers:**
- Analytical queries consistently >30 seconds
- Dataset grows beyond 50 GB
- Multiple concurrent analysts need parallel queries
- Advanced analytics features needed (window functions, materialized views)

## Review Date

**Review after:** 3 months of usage OR when analytical query latency exceeds 30 seconds

**Review criteria:**
- Average query performance
- Dataset size growth rate
- Types of queries being run
- User pain points

## References

- PROGRESS.md: ADR-001 (original detailed version)
- AWS Pricing Calculator: Cost estimates
- PostgreSQL documentation: Performance characteristics
- Redshift documentation: Use case recommendations

## Notes

- This decision optimizes for learning and cost efficiency
- Production deployments may have different requirements
- Easy to add Redshift later without major rework
- S3 data lake preserves all raw data for future reprocessing

---

**Related ADRs:**
- ADR-002: 10% Data Extraction Strategy (related data size decision)
- ADR-003: Python 3.11 for Development (impacts database driver compatibility)

**Supersedes:** None

**Superseded By:** None
