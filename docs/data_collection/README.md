# Data Collection Documentation

**Location:** `docs/data_collection/`
**Status:** Active data collection operations
**Last Updated:** October 21, 2025

---

## Overview

This directory contains documentation for all data collection systems, scrapers, and data acquisition strategies for the NBA Temporal Panel Data System.

---

## Subdirectories

### [scrapers/](scrapers/)
**Scraper Systems & Autonomous Data Collection**

Complete documentation for scraper systems including:
- ESPN scraper implementation
- NBA API scraper optimization
- Basketball Reference scraper (see 0.0001)
- Management and monitoring systems
- Autonomous overnight deployment
- Test results and validation

---

## Data Sources

**Primary Sources:**
1. **ESPN** - Play-by-play, box scores, schedules (70,522 files in S3)
2. **NBA API** - Advanced stats, player tracking, shot charts
3. **Basketball Reference** - Historical data, advanced metrics, biographical info
4. **Kaggle** - Historical game data (pre-2020)
5. **hoopR** - R package integration for statistical analysis

**See also:**
- [Data Source Baselines](../DATA_SOURCE_BASELINES.md)
- [Data Catalog](../DATA_CATALOG.md)
- [Data Structure Guide](../DATA_STRUCTURE_GUIDE.md)

---

## Related Documentation

**Phase Documentation:**
- [Phase 0: Data Collection](../phases/phase_0/PHASE_0_INDEX.md)
- [0.0001: Basketball Reference](../phases/phase_0/0.0001_basketball_reference/)
- [Phase 1: Data Quality](../phases/PHASE_1_INDEX.md)

**Workflows:**
- [Workflow #38: Overnight Scraper Handoff](../claude_workflows/workflow_descriptions/38_overnight_scraper_handoff.md)
- [Workflow #39: Monitoring Automation](../claude_workflows/workflow_descriptions/39_monitoring_automation.md)
- [Workflow #40: Complete Scraper Operations](../claude_workflows/workflow_descriptions/40_complete_scraper_operations.md)

---

## Navigation

**Return to:** [Main Documentation Index](../README.md)
**Related:** [Scraper Systems](scrapers/)

---

**Last Updated:** October 21, 2025
