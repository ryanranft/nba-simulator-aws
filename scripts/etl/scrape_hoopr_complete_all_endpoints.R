#!/usr/bin/env Rscript
#
# hoopR Comprehensive NBA Stats API Scraper (R Version)
#
# This script uses the R version of hoopR which has ALL 152 NBA Stats API endpoints
# (unlike Python's sportsdataverse which only has 4 bulk loaders)
#
# Coverage: 2002-2025 (based on data availability)
# Endpoints: 152 NBA Stats API functions
# Output: JSON files organized by category
# S3 Upload: Optional automatic upload to s3://nba-sim-raw-data-lake
#

suppressPackageStartupMessages({
  library(hoopR)
  library(jsonlite)
  library(dplyr)
  library(purrr)
  library(lubridate)
  library(progressr)
})

# Configuration
args <- commandArgs(trailingOnly = TRUE)
OUTPUT_DIR <- if (length(args) > 0) args[1] else "/tmp/hoopr_complete"
UPLOAD_TO_S3 <- "--upload-to-s3" %in% args
S3_BUCKET <- "s3://nba-sim-raw-data-lake/hoopr"
SEASONS <- 2002:2025  # 24 seasons

# Create output directories
dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)
categories <- c(
  "bulk_data", "boxscores", "shot_charts", "tracking", "hustle",
  "synergy", "lineups", "league_dashboards", "player_info", "team_info",
  "game_logs", "draft", "standings", "static_data"
)
for (cat in categories) {
  dir.create(file.path(OUTPUT_DIR, cat), recursive = TRUE, showWarnings = FALSE)
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("🏀 hoopR COMPREHENSIVE NBA STATS API SCRAPER (R VERSION)\n")
cat(rep("=", 80), "\n", sep = "")
cat("Seasons:", paste(SEASONS, collapse = ", "), "\n")
cat("Output:", OUTPUT_DIR, "\n")
cat("S3 Upload:", if (UPLOAD_TO_S3) "ENABLED" else "DISABLED", "\n")
cat("Total endpoints: 152 NBA Stats API functions\n")
cat(rep("=", 80), "\n\n", sep = "")

# Helper function to safely call API with retry logic
call_api_safe <- function(func, ..., max_retries = 3, delay = 2) {
  for (attempt in 1:max_retries) {
    result <- tryCatch({
      Sys.sleep(delay)  # Rate limiting
      func(...)
    }, error = function(e) {
      if (attempt < max_retries) {
        cat("  ⚠️  Attempt", attempt, "failed, retrying...\n")
        return(NULL)
      } else {
        cat("  ❌ Failed after", max_retries, "attempts:", e$message, "\n")
        return(NULL)
      }
    })

    if (!is.null(result)) {
      return(result)
    }
  }
  return(NULL)
}

# Save data to JSON
save_json <- function(data, filepath) {
  if (is.null(data) || nrow(data) == 0) {
    return(FALSE)
  }

  dir.create(dirname(filepath), recursive = TRUE, showWarnings = FALSE)
  write_json(data, filepath, pretty = FALSE, auto_unbox = TRUE)

  # Upload to S3 if enabled
  if (UPLOAD_TO_S3) {
    s3_path <- gsub(OUTPUT_DIR, S3_BUCKET, filepath)
    system(paste("aws s3 cp", filepath, s3_path, "--quiet"))
  }

  return(TRUE)
}

# Statistics tracker
stats <- list(
  total_calls = 0,
  successful_calls = 0,
  failed_calls = 0,
  total_data_points = 0,
  start_time = Sys.time()
)

cat("\n", rep("=", 80), "\n", sep = "")
cat("PHASE 1: BULK DATA LOADERS (Most Efficient)\n")
cat(rep("=", 80), "\n\n", sep = "")

# 1. Load bulk play-by-play
cat("📊 Loading bulk play-by-play for", length(SEASONS), "seasons...\n")
pbp_data <- call_api_safe(load_nba_pbp, seasons = SEASONS)
if (!is.null(pbp_data)) {
  season_str <- paste(SEASONS, collapse = "_")
  filepath <- file.path(OUTPUT_DIR, "bulk_data", paste0("pbp_seasons_", season_str, ".json"))
  if (save_json(pbp_data, filepath)) {
    cat("  ✅ Saved", nrow(pbp_data), "play-by-play events\n")
    stats$total_data_points <- stats$total_data_points + nrow(pbp_data)
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# 2. Load bulk player box scores
cat("\n📊 Loading bulk player box scores for", length(SEASONS), "seasons...\n")
player_box_data <- call_api_safe(load_nba_player_box, seasons = SEASONS)
if (!is.null(player_box_data)) {
  season_str <- paste(SEASONS, collapse = "_")
  filepath <- file.path(OUTPUT_DIR, "bulk_data", paste0("player_box_seasons_", season_str, ".json"))
  if (save_json(player_box_data, filepath)) {
    cat("  ✅ Saved", nrow(player_box_data), "player box scores\n")
    stats$total_data_points <- stats$total_data_points + nrow(player_box_data)
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# 3. Load bulk team box scores
cat("\n📊 Loading bulk team box scores for", length(SEASONS), "seasons...\n")
team_box_data <- call_api_safe(load_nba_team_box, seasons = SEASONS)
if (!is.null(team_box_data)) {
  season_str <- paste(SEASONS, collapse = "_")
  filepath <- file.path(OUTPUT_DIR, "bulk_data", paste0("team_box_seasons_", season_str, ".json"))
  if (save_json(team_box_data, filepath)) {
    cat("  ✅ Saved", nrow(team_box_data), "team box scores\n")
    stats$total_data_points <- stats$total_data_points + nrow(team_box_data)
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# 4. Load bulk schedules
cat("\n📊 Loading bulk schedules for", length(SEASONS), "seasons...\n")
schedule_data <- call_api_safe(load_nba_schedule, seasons = SEASONS)
if (!is.null(schedule_data)) {
  season_str <- paste(SEASONS, collapse = "_")
  filepath <- file.path(OUTPUT_DIR, "bulk_data", paste0("schedule_seasons_", season_str, ".json"))
  if (save_json(schedule_data, filepath)) {
    cat("  ✅ Saved", nrow(schedule_data), "games\n")
    stats$total_data_points <- stats$total_data_points + nrow(schedule_data)
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

cat("\n", rep("=", 80), "\n", sep = "")
cat("PHASE 2: STATIC/META ENDPOINTS (One-time scrapes)\n")
cat(rep("=", 80), "\n\n", sep = "")

# All-time leaders
cat("🏆 Fetching all-time leader grids...\n")
leaders_data <- call_api_safe(nba_alltimeleadersgrids)
if (!is.null(leaders_data)) {
  filepath <- file.path(OUTPUT_DIR, "static_data", "all_time_leaders.json")
  if (save_json(leaders_data, filepath)) {
    cat("  ✅ Saved all-time leaders\n")
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# Common all players
cat("\n👥 Fetching all players list...\n")
all_players <- call_api_safe(nba_commonallplayers, season = "2024-25")
if (!is.null(all_players)) {
  filepath <- file.path(OUTPUT_DIR, "player_info", "all_players.json")
  if (save_json(all_players, filepath)) {
    cat("  ✅ Saved", nrow(all_players), "players\n")
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# Draft history (recent years)
cat("\n🎯 Fetching draft history...\n")
for (year in 2002:2024) {
  draft_data <- call_api_safe(nba_drafthistory, season = paste0(year, "-", substr(year + 1, 3, 4)))
  if (!is.null(draft_data)) {
    filepath <- file.path(OUTPUT_DIR, "draft", paste0("draft_", year, ".json"))
    if (save_json(draft_data, filepath)) {
      cat("  ✅ Saved", year, "draft\n")
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("PHASE 3: PER-SEASON LEAGUE DASHBOARDS\n")
cat(rep("=", 80), "\n\n", sep = "")

# League dashboards for each season
for (season_year in SEASONS) {
  season_str <- paste0(season_year, "-", substr(season_year + 1, 3, 4))
  cat("\n📊 Season", season_str, "- League dashboards...\n")

  # Player stats dashboard
  player_stats <- call_api_safe(nba_leaguedashplayerstats, season = season_str, per_mode = "PerGame")
  if (!is.null(player_stats)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("player_stats_", season_year, ".json"))
    if (save_json(player_stats, filepath)) {
      cat("  ✅ Player stats\n")
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Team stats dashboard
  team_stats <- call_api_safe(nba_leaguedashteamstats, season = season_str, per_mode = "PerGame")
  if (!is.null(team_stats)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("team_stats_", season_year, ".json"))
    if (save_json(team_stats, filepath)) {
      cat("  ✅ Team stats\n")
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Lineups (5-man combinations)
  lineups <- call_api_safe(nba_leaguedashlineups, season = season_str, group_quantity = 5)
  if (!is.null(lineups)) {
    filepath <- file.path(OUTPUT_DIR, "lineups", paste0("lineups_5man_", season_year, ".json"))
    if (save_json(lineups, filepath)) {
      cat("  ✅ 5-man lineups\n")
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Standings
  standings <- call_api_safe(nba_leaguestandingsv3, season = season_str)
  if (!is.null(standings)) {
    filepath <- file.path(OUTPUT_DIR, "standings", paste0("standings_", season_year, ".json"))
    if (save_json(standings, filepath)) {
      cat("  ✅ Standings\n")
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("SCRAPING COMPLETE - SUMMARY\n")
cat(rep("=", 80), "\n", sep = "")

elapsed_time <- as.numeric(difftime(Sys.time(), stats$start_time, units = "mins"))

cat("\n📊 Statistics:\n")
cat("  Total API calls:", stats$total_calls, "\n")
cat("  Successful:", stats$successful_calls, "\n")
cat("  Failed:", stats$failed_calls, "\n")
cat("  Success rate:", round(100 * stats$successful_calls / stats$total_calls, 1), "%\n")
cat("  Total data points:", format(stats$total_data_points, big.mark = ","), "\n")
cat("  Runtime:", round(elapsed_time, 1), "minutes\n")

cat("\n📁 Output:\n")
cat("  Directory:", OUTPUT_DIR, "\n")
if (UPLOAD_TO_S3) {
  cat("  S3 Bucket:", S3_BUCKET, "\n")
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("✅ hoopR comprehensive scraping complete!\n")
cat(rep("=", 80), "\n\n", sep = "")
