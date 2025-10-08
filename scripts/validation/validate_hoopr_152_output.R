#!/usr/bin/env Rscript
#
# hoopR 152 Endpoints Output Validator
#
# Validates output from scrape_hoopr_all_152_endpoints.R
# - Checks file counts per phase
# - Validates CSV structure
# - Compares to expected output
# - Generates validation report
#
# Usage:
#   Rscript scripts/validation/validate_hoopr_152_output.R /tmp/hoopr_all_152
#

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(purrr)
  library(stringr)
})

# Configuration
args <- commandArgs(trailingOnly = TRUE)
OUTPUT_DIR <- if (length(args) > 0) args[1] else "/tmp/hoopr_all_152"
SEASONS_START <- 2002
SEASONS_END <- 2025
NUM_SEASONS <- SEASONS_END - SEASONS_START + 1

cat("\n", rep("=", 80), "\n", sep = "")
cat("🔍 hoopR 152 ENDPOINTS - OUTPUT VALIDATOR\n")
cat(rep("=", 80), "\n", sep = "")
cat("Output Directory: ", OUTPUT_DIR, "\n", sep = "")
cat("Expected Seasons: ", SEASONS_START, "-", SEASONS_END, " (", NUM_SEASONS, " seasons)\n", sep = "")
cat(rep("=", 80), "\n\n", sep = "")

# Validation results
results <- list(
  phase1 = list(name = "Phase 1: Bulk Data Loaders", expected = 4 * NUM_SEASONS, actual = 0, status = "PENDING"),
  phase2 = list(name = "Phase 2: Static/Reference", expected = 50, actual = 0, status = "PENDING"),
  phase3 = list(name = "Phase 3: Per-Season Dashboards", expected = 40 * NUM_SEASONS, actual = 0, status = "PENDING"),
  phase4 = list(name = "Phase 4: Per-Game Boxscores", expected = NA, actual = 0, status = "PENDING"),
  total_size = 0,
  errors = c(),
  warnings = c()
)

# Helper functions
count_files <- function(pattern) {
  files <- list.files(OUTPUT_DIR, pattern = pattern, recursive = TRUE, full.names = TRUE)
  length(files)
}

check_csv_structure <- function(filepath, required_cols = NULL) {
  tryCatch({
    data <- read_csv(filepath, n_max = 10, show_col_types = FALSE)

    # Check if empty
    if (nrow(data) == 0) {
      return(list(valid = FALSE, message = "Empty file"))
    }

    # Check required columns
    if (!is.null(required_cols)) {
      missing <- setdiff(required_cols, names(data))
      if (length(missing) > 0) {
        return(list(valid = FALSE, message = paste("Missing columns:", paste(missing, collapse = ", "))))
      }
    }

    return(list(valid = TRUE, rows = nrow(data), cols = ncol(data)))
  }, error = function(e) {
    return(list(valid = FALSE, message = e$message))
  })
}

# ==============================================================================
# PHASE 1: BULK DATA LOADERS
# ==============================================================================

cat("📊 PHASE 1: Bulk Data Loaders\n")
cat(rep("-", 80), "\n", sep = "")

# Check play-by-play
pbp_dir <- file.path(OUTPUT_DIR, "bulk_pbp")
if (dir.exists(pbp_dir)) {
  pbp_files <- list.files(pbp_dir, pattern = "pbp_.*\\.csv", full.names = TRUE)
  results$phase1$actual <- results$phase1$actual + length(pbp_files)

  cat("  Play-by-play:          ", length(pbp_files), " files\n", sep = "")

  if (length(pbp_files) > 0) {
    # Sample first file
    sample_pbp <- check_csv_structure(pbp_files[1], c("game_id"))
    if (sample_pbp$valid) {
      cat("    ✓ Sample file valid: ", basename(pbp_files[1]), " (", sample_pbp$rows, " rows, ", sample_pbp$cols, " cols)\n", sep = "")
    } else {
      results$errors <- c(results$errors, paste("PBP validation failed:", sample_pbp$message))
      cat("    ✗ Sample file invalid: ", sample_pbp$message, "\n", sep = "")
    }
  }
} else {
  results$warnings <- c(results$warnings, "Play-by-play directory not found")
  cat("  Play-by-play:          ✗ Directory not found\n")
}

# Check player box scores
player_box_dir <- file.path(OUTPUT_DIR, "bulk_player_box")
if (dir.exists(player_box_dir)) {
  player_box_files <- list.files(player_box_dir, pattern = "player_box_.*\\.csv", full.names = TRUE)
  results$phase1$actual <- results$phase1$actual + length(player_box_files)

  cat("  Player box scores:     ", length(player_box_files), " files\n", sep = "")

  if (length(player_box_files) > 0) {
    sample_pbox <- check_csv_structure(player_box_files[1], c("game_id", "athlete_id"))
    if (sample_pbox$valid) {
      cat("    ✓ Sample file valid: ", basename(player_box_files[1]), " (", sample_pbox$rows, " rows)\n", sep = "")
    } else {
      results$warnings <- c(results$warnings, paste("Player box validation failed:", sample_pbox$message))
    }
  }
}

# Check team box scores
team_box_dir <- file.path(OUTPUT_DIR, "bulk_team_box")
if (dir.exists(team_box_dir)) {
  team_box_files <- list.files(team_box_dir, pattern = "team_box_.*\\.csv", full.names = TRUE)
  results$phase1$actual <- results$phase1$actual + length(team_box_files)

  cat("  Team box scores:       ", length(team_box_files), " files\n", sep = "")
}

# Check schedules
schedule_dir <- file.path(OUTPUT_DIR, "bulk_schedule")
if (dir.exists(schedule_dir)) {
  schedule_files <- list.files(schedule_dir, pattern = "schedule_.*\\.csv", full.names = TRUE)
  results$phase1$actual <- results$phase1$actual + length(schedule_files)

  cat("  Schedules:             ", length(schedule_files), " files\n", sep = "")
}

# Phase 1 status
results$phase1$status <- ifelse(
  results$phase1$actual >= results$phase1$expected * 0.9,
  "PASS",
  ifelse(results$phase1$actual > 0, "PARTIAL", "FAIL")
)
cat("  Status: ", results$phase1$status, " (", results$phase1$actual, "/", results$phase1$expected, " expected)\n\n", sep = "")

# ==============================================================================
# PHASE 2: STATIC/REFERENCE DATA
# ==============================================================================

cat("📊 PHASE 2: Static/Reference Data\n")
cat(rep("-", 80), "\n", sep = "")

# Count files in various static directories
static_dirs <- c(
  "static_data", "player_info", "team_info", "draft", "franchise",
  "all_time_leaders", "home_leaders", "leader_tiles", "scoreboard",
  "todays_scoreboard", "playoff_picture", "common_playoff_series", "defense_hub"
)

for (dir_name in static_dirs) {
  dir_path <- file.path(OUTPUT_DIR, dir_name)
  if (dir.exists(dir_path)) {
    files <- list.files(dir_path, pattern = "\\.csv$", full.names = TRUE)
    results$phase2$actual <- results$phase2$actual + length(files)
    if (length(files) > 0) {
      cat("  ", dir_name, ": ", length(files), " files\n", sep = "")
    }
  }
}

results$phase2$status <- ifelse(results$phase2$actual > 0, "PARTIAL", "FAIL")
cat("  Status: ", results$phase2$status, " (", results$phase2$actual, "/~", results$phase2$expected, " expected)\n\n", sep = "")

# ==============================================================================
# PHASE 3: PER-SEASON DASHBOARDS
# ==============================================================================

cat("📊 PHASE 3: Per-Season Dashboards\n")
cat(rep("-", 80), "\n", sep = "")

dashboard_dirs <- c("league_dashboards", "lineups", "standings")

for (dir_name in dashboard_dirs) {
  dir_path <- file.path(OUTPUT_DIR, dir_name)
  if (dir.exists(dir_path)) {
    files <- list.files(dir_path, pattern = "\\.csv$", full.names = TRUE)
    results$phase3$actual <- results$phase3$actual + length(files)
    if (length(files) > 0) {
      cat("  ", dir_name, ": ", length(files), " files\n", sep = "")
    }
  }
}

results$phase3$status <- ifelse(
  results$phase3$actual >= results$phase3$expected * 0.5,
  "PARTIAL",
  ifelse(results$phase3$actual > 0, "MINIMAL", "FAIL")
)
cat("  Status: ", results$phase3$status, " (", results$phase3$actual, "/", results$phase3$expected, " expected)\n\n", sep = "")

# ==============================================================================
# PHASE 4: PER-GAME BOXSCORES
# ==============================================================================

cat("📊 PHASE 4: Per-Game Boxscores\n")
cat(rep("-", 80), "\n", sep = "")

boxscore_dirs <- c(
  "boxscore_traditional", "boxscore_advanced", "boxscore_scoring",
  "boxscore_usage", "boxscore_fourfactors", "boxscore_misc",
  "boxscore_tracking", "boxscore_hustle", "boxscore_matchups",
  "boxscore_defensive"
)

for (dir_name in boxscore_dirs) {
  dir_path <- file.path(OUTPUT_DIR, dir_name)
  if (dir.exists(dir_path)) {
    files <- list.files(dir_path, pattern = "\\.csv$", full.names = TRUE)
    results$phase4$actual <- results$phase4$actual + length(files)
    if (length(files) > 0) {
      cat("  ", dir_name, ": ", length(files), " files\n", sep = "")
    }
  }
}

results$phase4$status <- ifelse(results$phase4$actual > 0, "PARTIAL", "NONE")
cat("  Status: ", results$phase4$status, " (", results$phase4$actual, " files - sample mode)\n\n", sep = "")

# ==============================================================================
# OVERALL STATISTICS
# ==============================================================================

cat("\n", rep("=", 80), "\n", sep = "")
cat("📈 OVERALL STATISTICS\n")
cat(rep("=", 80), "\n", sep = "")

# Total files
total_files <- list.files(OUTPUT_DIR, pattern = "\\.csv$", recursive = TRUE)
cat("  Total CSV files:       ", length(total_files), "\n", sep = "")

# Total size
all_files <- list.files(OUTPUT_DIR, recursive = TRUE, full.names = TRUE)
total_size <- sum(file.info(all_files[!file.info(all_files)$isdir])$size, na.rm = TRUE)
results$total_size <- total_size

cat("  Total size:            ", round(total_size / 1024^3, 2), " GB\n", sep = "")
cat("  Average file size:     ", round(total_size / length(total_files) / 1024^2, 2), " MB\n", sep = "")

# Log file analysis
log_files <- list.files(OUTPUT_DIR, pattern = "scraper_log_.*\\.txt", full.names = TRUE)
if (length(log_files) > 0) {
  log_file <- log_files[1]
  log_lines <- readLines(log_file)

  # Count errors and warnings
  errors <- sum(grepl("\\[ERROR\\]", log_lines))
  warnings <- sum(grepl("\\[WARN\\]", log_lines))

  cat("\n  Log Analysis:\n")
  cat("    Log file:            ", basename(log_file), "\n", sep = "")
  cat("    Total log lines:     ", length(log_lines), "\n", sep = "")
  cat("    Errors logged:       ", errors, "\n", sep = "")
  cat("    Warnings logged:     ", warnings, "\n", sep = "")

  # Extract runtime if available
  runtime_line <- log_lines[grepl("Runtime:", log_lines)]
  if (length(runtime_line) > 0) {
    cat("    ", runtime_line[1], "\n", sep = "")
  }
}

# ==============================================================================
# VALIDATION SUMMARY
# ==============================================================================

cat("\n", rep("=", 80), "\n", sep = "")
cat("✅ VALIDATION SUMMARY\n")
cat(rep("=", 80), "\n", sep = "")

cat("\nPhase Results:\n")
cat("  Phase 1: ", results$phase1$status, " (", results$phase1$actual, "/", results$phase1$expected, ")\n", sep = "")
cat("  Phase 2: ", results$phase2$status, " (", results$phase2$actual, "/~", results$phase2$expected, ")\n", sep = "")
cat("  Phase 3: ", results$phase3$status, " (", results$phase3$actual, "/", results$phase3$expected, ")\n", sep = "")
cat("  Phase 4: ", results$phase4$status, " (", results$phase4$actual, " files)\n", sep = "")

# Overall status
overall_status <- "FAIL"
if (results$phase1$status %in% c("PASS", "PARTIAL") &&
    results$phase2$status %in% c("PASS", "PARTIAL") &&
    results$phase3$status != "FAIL") {
  overall_status <- "PASS"
} else if (results$phase1$actual > 0 || results$phase2$actual > 0) {
  overall_status <- "PARTIAL"
}

cat("\nOverall Status: ", overall_status, "\n", sep = "")

# Errors and warnings
if (length(results$errors) > 0) {
  cat("\nErrors:\n")
  for (error in results$errors) {
    cat("  ✗ ", error, "\n", sep = "")
  }
}

if (length(results$warnings) > 0) {
  cat("\nWarnings:\n")
  for (warning in results$warnings) {
    cat("  ⚠️  ", warning, "\n", sep = "")
  }
}

# Recommendations
cat("\n", rep("=", 80), "\n", sep = "")
cat("📋 RECOMMENDATIONS\n")
cat(rep("=", 80), "\n", sep = "")

if (overall_status == "PASS") {
  cat("\n  ✓ Output validation passed!\n")
  cat("  ✓ Data ready for loading into PostgreSQL\n")
  cat("  ✓ Proceed with feature engineering pipeline\n")
} else if (overall_status == "PARTIAL") {
  cat("\n  ⚠️  Partial data collected\n")

  if (results$phase1$status != "PASS") {
    cat("  → Re-run Phase 1 for missing bulk data\n")
  }
  if (results$phase2$actual < 20) {
    cat("  → Re-run Phase 2 for static endpoints\n")
  }
  if (results$phase3$actual < results$phase3$expected * 0.5) {
    cat("  → Re-run Phase 3 for per-season dashboards\n")
  }
} else {
  cat("\n  ✗ Validation failed\n")
  cat("  → Check scraper logs for errors\n")
  cat("  → Verify API connectivity\n")
  cat("  → Re-run scraper with increased delay\n")
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("Validation complete!\n")
cat(rep("=", 80), "\n\n", sep = "")

# Exit with appropriate code
if (overall_status == "PASS") {
  quit(status = 0)
} else if (overall_status == "PARTIAL") {
  quit(status = 1)
} else {
  quit(status = 2)
}
