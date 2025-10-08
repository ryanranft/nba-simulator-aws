# Archived ETL Scripts

**Last Updated:** October 8, 2025

This directory contains deprecated scraper scripts that have been replaced by improved versions.

## Deprecation Policy

Files moved here are:
1. **Documented** - Deprecation notice added to file header
2. **Replaced** - Active alternative documented
3. **Preserved** - Available for reference but not for active use

## Active Alternatives

Use the following current scripts instead of archived versions:

### Shell Wrappers (Overnight Jobs)

| Archived Script | Replacement | Location |
|----------------|-------------|----------|
| `overnight_hoopr_comprehensive.sh` | `run_hoopr_phase1b.sh` | `scripts/etl/` |
| `overnight_scrape.sh` | `scrape_bbref_incremental.sh` | `scripts/etl/` |
| `run_sportsdataverse_overnight.sh` | `run_hoopr_phase1b.sh` | `scripts/etl/` |

### Python Scripts

| Archived Script | Replacement | Location |
|----------------|-------------|----------|
| `scrape_sportsdataverse.py` | Use hoopR Phase 1B instead | `scripts/etl/run_hoopr_phase1b.sh` |
| `download_kaggle_database.py` | `download_kaggle_basketball.py` | `scripts/etl/` |
| `extract_espn_local_to_temporal.py` | No longer needed | N/A |
| `extract_espn_local_to_temporal_UPDATED.py` | No longer needed | N/A |

## Directory Structure

```
scripts/archive/
├── README.md (this file)
└── deprecated/
    ├── download_kaggle_database.py
    ├── extract_espn_local_to_temporal.py
    ├── extract_espn_local_to_temporal_UPDATED.py
    ├── overnight_hoopr_comprehensive.sh
    ├── overnight_scrape.sh
    ├── run_sportsdataverse_overnight.sh
    └── scrape_sportsdataverse.py
```

## How to Use This Archive

**Before using any script from this archive:**

1. Check if it's marked as `⚠️ DEPRECATED` in the file header
2. Read the deprecation notice for the replacement script
3. Use the active alternative from `scripts/etl/` instead

**Restoration process (if needed):**

```bash
# 1. Check deprecation notice in archived file
head -20 scripts/archive/deprecated/<script_name>

# 2. If truly needed, copy to active directory
cp scripts/archive/deprecated/<script_name> scripts/etl/

# 3. Remove deprecation notice
# Edit file and remove ⚠️ DEPRECATED header

# 4. Update documentation to reflect restoration
```

## Archive History

**October 8, 2025 - Initial archival:**
- Moved 7 files (4 Python, 3 shell scripts)
- Reason: Consolidation and deduplication
- Scripts archived:
  - Python: `download_kaggle_database.py`, `extract_espn_local_to_temporal.py`, `extract_espn_local_to_temporal_UPDATED.py`, `scrape_sportsdataverse.py`
  - Shell: `overnight_hoopr_comprehensive.sh`, `overnight_scrape.sh`, `run_sportsdataverse_overnight.sh`
- Commit: ff6bbb5 (`refactor(etl): archive deprecated scripts and consolidate documentation`)

---

*For active scraper documentation, see `scripts/etl/README.md`*
