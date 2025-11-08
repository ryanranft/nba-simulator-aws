# Phase 0.0001 Repurposing & S3 Migration Plan

**Date:** November 6, 2025
**Status:** 🔄 IN PROGRESS
**Estimated Time:** 4-5 hours

---

## Overview

Transform Phase 0.0001 from a completed historical upload to an active data extraction and validation phase with ESPN-prefixed folder names.

## Key Changes

- **S3 Paths:** Rename folders with `espn_` prefix for source clarity:
  - `pbp/` → `espn_play_by_play/`
  - `box_scores/` → `espn_box_scores/`
  - `team_stats/` → `espn_team_stats/`
  - `schedule/` → `espn_schedules/`

- **Phase Status:** ✅ COMPLETE → 🔄 IN PROGRESS (active data collection)

- **Scope:** Comprehensive phase including:
  - Data extraction from external ESPN scraper
  - S3 upload and validation
  - Gap detection and analysis
  - Incremental data filling

- **Data Migration:** Move 146,115 existing files (119 GB) to new structure

---

## Implementation Steps

### ✅ Step 1: S3 Data Migration Script
**Status:** COMPLETE
**File:** `scripts/0_0001/migrate_espn_s3_paths.py`

Created comprehensive migration script with:
- S3 copy operations (no download/re-upload for cost efficiency)
- Dry-run capability for safe testing
- Source path verification (compares against expected baselines)
- Destination path collision detection
- Progress tracking every 1,000 files
- Post-migration verification
- Rollback capability (keeps old folders)

**Usage:**
```bash
# Preview migration (recommended first)
python scripts/0_0001/migrate_espn_s3_paths.py --dry-run

# Execute migration
python scripts/0_0001/migrate_espn_s3_paths.py

# Verify after migration
python scripts/0_0001/migrate_espn_s3_paths.py --verify
```

---

### 🔄 Step 2: Execute S3 Data Migration
**Status:** IN PROGRESS
**Files to migrate:** 146,115 (119 GB)

**Migration mapping:**
- `pbp/` (44,826 files) → `espn_play_by_play/`
- `box_scores/` (44,828 files) → `espn_box_scores/`
- `team_stats/` (44,828 files) → `espn_team_stats/`
- `schedule/` (11,633 files) → `espn_schedules/`

**Estimated time:** 1-2 hours

**Commands:**
```bash
# 1. Test with dry-run first
python scripts/0_0001/migrate_espn_s3_paths.py --dry-run

# 2. Execute migration
python scripts/0_0001/migrate_espn_s3_paths.py

# 3. Verify success
python scripts/0_0001/migrate_espn_s3_paths.py --verify
```

---

### ⏳ Step 3: Verify S3 Migration Success
**Status:** PENDING

**Verification checklist:**
- [ ] File counts match: 146,115 total
  - [ ] espn_play_by_play/: 44,826 files
  - [ ] espn_box_scores/: 44,828 files
  - [ ] espn_team_stats/: 44,828 files
  - [ ] espn_schedules/: 11,633 files
- [ ] Total size matches: ~119 GB
- [ ] Sample files from each folder are valid JSON
- [ ] Old folders still exist (rollback capability)

---

### ⏳ Step 4: Update Documentation (23+ occurrences)

#### Phase 0.0001 README
**File:** `docs/phases/phase_0/0.0001_initial_data_collection/README.md`

**Changes:**
- [ ] Update status: ✅ COMPLETE → 🔄 IN PROGRESS
- [ ] Rewrite purpose section:
  ```
  Active extraction and validation of ESPN data from external scraper.
  Handles initial data collection, gap detection, and incremental updates.
  ```
- [ ] Update all S3 paths (23 locations):
  - Lines 337-340: Data uploaded section
  - Lines 345-360: Upload commands
  - Line 396: Verification command
  - Lines 428-431: Data structure summary
  - Line 180: ADCE growth tracking
- [ ] Add new sections:
  - Gap Detection & Analysis
  - Data Quality Tracking
  - Incremental Update Workflow
  - Local ESPN Scraper Integration

#### DATA_STRUCTURE_GUIDE.md
**File:** `docs/DATA_STRUCTURE_GUIDE.md`

**Changes:**
- [ ] Update S3 folder structure (lines 30-33)
- [ ] Update table showing folder names (lines 46-49)
- [ ] Update section headings:
  - Line 64: "Play-by-Play Files" → "ESPN Play-by-Play Files (espn_play_by_play/)"
  - Line 234: "Team Stats Files" → "ESPN Team Stats Files (espn_team_stats/)"
  - Line 277: "Schedule Files" → "ESPN Schedule Files (espn_schedules/)"
- [ ] Update all code examples with new paths

#### DATA_CATALOG.md
**File:** `docs/DATA_CATALOG.md`

**Changes:**
- [ ] Update ESPN section (lines 89-166)
- [ ] Update S3 path references throughout
- [ ] Update file count statistics if different after migration

---

### ⏳ Step 5: Update Python Code (7+ scripts)

#### 5.1: s3_loader.py
**File:** `nba_simulator/etl/loaders/s3_loader.py`

**Changes:**
- [ ] Line 391: Update comment `s3://bucket/box_scores/` → `s3://bucket/espn_box_scores/`
- [ ] Line 400: Update variable `prefix="box_scores/"` → `prefix="espn_box_scores/"`

#### 5.2: extract_schedule_local.py
**File:** `scripts/etl/extract_schedule_local.py`

**Changes:**
- [ ] Line 8: Update comment `s3://bucket/schedule/` → `s3://bucket/espn_schedules/`
- [ ] Line 59: Update variable `prefix = "schedule/"` → `prefix = "espn_schedules/"`

#### 5.3: extract_boxscores_local.py
**File:** `scripts/etl/extract_boxscores_local.py`

**Changes:**
- [ ] Line 8: Update comment with new S3 path
- [ ] Line 364: Update `s3_key = f"box_scores/{game_id}.json"` → `f"espn_box_scores/{game_id}.json"`

#### 5.4: extract_pbp_local.py
**File:** `scripts/etl/extract_pbp_local.py`

**Changes:**
- [ ] Update S3 path references `pbp/` → `espn_play_by_play/`
- [ ] Update comments and variable assignments

#### 5.5: merge_all_sources.py
**File:** `scripts/etl/merge_all_sources.py`

**Changes:**
- [ ] Line 7: Update comment with new paths
- [ ] Line 86: Update `DataSourceConfig("espn", "pbp/", priority=2)` → `"espn_play_by_play/"`
- [ ] Line 229: Update `Prefix="pbp/"` → `Prefix="espn_play_by_play/"`
- [ ] Line 642: Update `Prefix="pbp/"` → `Prefix="espn_play_by_play/"`

#### 5.6: partition_by_year.py
**File:** `scripts/etl/partition_by_year.py`

**Changes:**
- [ ] Lines 10-13: Update ASCII art folder structure
- [ ] Lines 17+: Update comments about partitioning paths

#### 5.7: game_id_decoder.py
**File:** `scripts/etl/game_id_decoder.py`

**Changes:**
- [ ] Line 230: Update docstring example `"s3://bucket/pbp/"` → `"s3://bucket/espn_play_by_play/"`
- [ ] Line 239: Update docstring example similarly

---

### ⏳ Step 6: Implement Validator
**File:** `validators/phases/phase_0/validate_0_0001.py`

**Status:** PENDING - Needs complete implementation

**Required functionality:**
- [ ] S3 file count verification
  - Compare against baseline: 146,115 files, 119 GB
  - Per-folder counts (schedules, pbp, box_scores, team_stats)
- [ ] Folder structure validation
  - Verify all `espn_*` folders exist
  - Check for unexpected folders
- [ ] Sample JSON validation
  - Select random files from each folder
  - Validate JSON structure
  - Check for required fields
- [ ] DIMS integration
  - Read live metrics from `inventory/metrics.yaml`
  - Compare against expected values
  - Report growth since baseline
- [ ] Gap detection reporting
  - Identify missing games by date range
  - Report empty JSON files
  - Calculate coverage percentages
- [ ] Data quality metrics
  - Empty file percentages per folder
  - Size distribution analysis
  - Temporal coverage gaps

---

### ⏳ Step 7: Build Gap-Filling Infrastructure

#### 7.1: extract_espn_data.py
**File:** `scripts/0_0001/extract_espn_data.py`

**Purpose:** Extract ESPN data from local scraper repository

**Functionality:**
- [ ] Read from `/Users/ryanranft/0espn/data/nba/`
- [ ] Support selective extraction by:
  - Date range
  - Game IDs
  - Data type (schedules, pbp, box_scores, team_stats)
- [ ] Validate extracted files
- [ ] Output extraction summary

#### 7.2: detect_gaps.py
**File:** `scripts/0_0001/detect_gaps.py`

**Purpose:** Compare S3 contents vs expected coverage

**Functionality:**
- [ ] Query S3 for current file list
- [ ] Compare against:
  - Expected date range (1993-2025)
  - Schedule files (should have all dates)
  - Game IDs from schedule files
- [ ] Identify missing:
  - Schedule dates
  - Game PBP files
  - Box score files
  - Team stats files
- [ ] Generate gap report with priorities

#### 7.3: fill_gaps.py
**File:** `scripts/0_0001/fill_gaps.py`

**Purpose:** Upload missing files from local source to S3

**Functionality:**
- [ ] Read gap report from detect_gaps.py
- [ ] Check local scraper repository for missing files
- [ ] Upload found files to appropriate S3 paths
- [ ] Verify upload success
- [ ] Generate fill summary report
- [ ] Update DIMS metrics

#### 7.4: upload_espn_to_s3.py
**File:** `scripts/0_0001/upload_espn_to_s3.py`

**Purpose:** Wrapper for AWS sync operations

**Functionality:**
- [ ] Smart sync from local → S3
  - Skip existing files
  - Only upload new/modified
- [ ] Support for:
  - All data types
  - Selective upload (by type, date range)
- [ ] Progress tracking
- [ ] Validation after upload
- [ ] DIMS metrics update

---

### ⏳ Step 8: Update Configuration Files

**Files to check:**
- [ ] `nba_simulator/etl/config/` - Any path configurations
- [ ] `config/autonomous_config.yaml` - ADCE scraper paths
- [ ] Workflow definitions referencing old S3 paths

---

### ⏳ Step 9: Testing & Validation

#### 9.1: Run Phase 0.0001 Validator
```bash
python validators/phases/phase_0/validate_0_0001.py
```

**Expected output:**
- [ ] All file counts match expectations
- [ ] All folders use `espn_*` naming
- [ ] Sample JSON files are valid
- [ ] DIMS metrics are current
- [ ] Gap report is generated

#### 9.2: Test Extraction Scripts
```bash
# Test schedule extraction
python scripts/etl/extract_schedule_local.py --limit 10

# Test box score extraction
python scripts/etl/extract_boxscores_local.py --limit 10

# Test PBP extraction
python scripts/etl/extract_pbp_local.py --limit 10
```

**Verify:**
- [ ] Scripts read from new S3 paths without errors
- [ ] Data extraction still works correctly
- [ ] No broken path references

#### 9.3: Verify Downstream Phases
- [ ] Phase 0.0002 (hoopR) - Still operational
- [ ] Phase 0.0009 (Extraction) - Works with new paths
- [ ] Phase 0.0010 (PostgreSQL) - Loaders functional

#### 9.4: Run DIMS Verification
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

**Verify:**
- [ ] Total object count updated
- [ ] Total size GB updated
- [ ] ESPN-specific metrics correct
- [ ] No errors or warnings

---

### ⏳ Step 10: Update Project Documentation

#### PROGRESS.md
**File:** `PROGRESS.md`

**Changes:**
- [ ] Update Phase 0.0001 status: ✅ COMPLETE → 🔄 IN PROGRESS
- [ ] Add note about S3 migration completion
- [ ] Update "Current Session Context" with migration details

#### Phase 0 Index
**File:** `docs/phases/phase_0/PHASE_0_INDEX.md`

**Changes:**
- [ ] Update 0.0001 status and description
- [ ] Reflect new comprehensive scope

---

## Migration Safety Measures

### Rollback Capability
Original S3 folders are kept intact during migration:
- `pbp/` - 44,826 files (preserved)
- `box_scores/` - 44,828 files (preserved)
- `team_stats/` - 44,828 files (preserved)
- `schedule/` - 11,633 files (preserved)

**If rollback needed:**
1. Update all code back to original paths
2. Delete new `espn_*` folders
3. Continue using original folders

**After successful validation (1-2 weeks):**
```bash
# Remove old folders to save costs (will save ~$2.74/month)
aws s3 rm s3://nba-sim-raw-data-lake/pbp/ --recursive
aws s3 rm s3://nba-sim-raw-data-lake/box_scores/ --recursive
aws s3 rm s3://nba-sim-raw-data-lake/team_stats/ --recursive
aws s3 rm s3://nba-sim-raw-data-lake/schedule/ --recursive
```

### Testing Strategy
1. **Dry-run first** - Always test with --dry-run flag
2. **Verify at each step** - Check file counts before proceeding
3. **Test extraction scripts** - Ensure downstream systems work
4. **Monitor DIMS metrics** - Watch for unexpected changes
5. **Keep rollback window** - Don't delete old folders for 1-2 weeks

### Cost Impact
- **Migration cost:** ~$0 (S3 copy operations within same region)
- **Temporary doubling:** ~$5.48/month while both folder structures exist
- **Final state:** ~$2.74/month (same as before, after cleanup)

---

## Success Criteria

- [ ] All 146,115 files migrated to `espn_*` folders
- [ ] File counts match: 44,826 + 44,828 + 44,828 + 11,633 = 146,115
- [ ] Total size matches: ~119 GB
- [ ] All documentation updated with new paths (23+ locations)
- [ ] All Python scripts updated (7+ files)
- [ ] Validator implemented and passing
- [ ] Gap-filling scripts created and tested
- [ ] Extraction scripts work with new paths
- [ ] DIMS metrics updated and accurate
- [ ] No broken references in codebase
- [ ] Downstream phases (0.0002-0.0010) still functional

---

## Timeline

| Step | Estimated Time | Status |
|------|---------------|--------|
| 1. Create migration script | 30 mins | ✅ COMPLETE |
| 2. Execute S3 migration | 1-2 hours | 🔄 IN PROGRESS |
| 3. Verify migration | 15 mins | ⏳ PENDING |
| 4. Update documentation | 30 mins | ⏳ PENDING |
| 5. Update Python code | 1 hour | ⏳ PENDING |
| 6. Implement validator | 1 hour | ⏳ PENDING |
| 7. Create gap-filling tools | 1 hour | ⏳ PENDING |
| 8. Update config files | 15 mins | ⏳ PENDING |
| 9. Testing & validation | 1 hour | ⏳ PENDING |
| 10. Update project docs | 15 mins | ⏳ PENDING |
| **TOTAL** | **4-5 hours** | **~10% COMPLETE** |

---

## Notes

- This plan follows the user's requirements:
  - ✅ Rename folders with `espn_` prefix
  - ✅ Full migration (docs + code + S3)
  - ✅ Use `espn_play_by_play` (not `espn_pbp`)
  - ✅ Migrate existing 146,115 files
  - ✅ Include gap detection and filling in Phase 0.0001

- Original Phase 0.0001 was a "completed upload" phase
- New Phase 0.0001 is an "active data collection" phase
- This aligns better with the ADCE autonomous data collection system

---

**Last Updated:** November 6, 2025
**Session:** Phase 0.0001 Repurposing
**Next Step:** Execute S3 migration with dry-run test