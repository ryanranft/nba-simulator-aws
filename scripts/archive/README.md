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
| `overnight_hoopr_comprehensive.sh` | `run_hoopr_comprehensive_overnight.sh` | `scripts/etl/` |
| `overnight_hoopr_all_152.sh` | `run_hoopr_comprehensive_overnight.sh` | `scripts/etl/` |
| `overnight_nba_api_comprehensive.sh` | Still active (no replacement) | `scripts/etl/` |

### Python Scripts

| Archived Script | Replacement | Location |
|----------------|-------------|----------|
| `scrape_hoopr_comprehensive.py` | `scrape_hoopr_nba_stats.py` | `scripts/etl/` |
| `scrape_nba_api_playbyplay_only.py` | `scrape_nba_api_comprehensive.py` | `scripts/etl/` |
| `scrape_sportsdataverse.py` | Direct Python API usage | Use sportsdataverse library directly |

## Directory Structure

```
scripts/archive/
├── README.md (this file)
└── deprecated/
    ├── overnight_hoopr_comprehensive.sh
    ├── overnight_hoopr_all_152.sh
    ├── overnight_nba_api_comprehensive.sh (ACTIVE - needs review)
    ├── scrape_hoopr_comprehensive.py
    ├── scrape_nba_api_playbyplay_only.py
    ├── scrape_sportsdataverse.py
    └── scrape_hoopr_nba_stats.py (ACTIVE - needs review)
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
- Commit: ff6bbb5 (`refactor(etl): archive deprecated scripts and consolidate documentation`)

---

*For active scraper documentation, see `scripts/etl/README.md`*
