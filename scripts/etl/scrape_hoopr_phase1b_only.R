#!/usr/bin/env Rscript
#
# hoopR Phase 1B Only: League Dashboards & Static Data
#
# Runs only Phase 1B since Phase 1A (bulk loaders) already completed
# Gets: League dashboards, standings, static/reference data, draft history
# Output: CSV files
# Coverage: 2002-2025 (24 seasons)
# Runtime: 30-60 minutes
#

suppressPackageStartupMessages({
  library(hoopR)
  library(dplyr)
  library(purrr)
  library(lubridate)
  library(readr)
})

# Configuration
args <- commandArgs(trailingOnly = TRUE)
OUTPUT_DIR <- if (length(args) > 0) args[1] else "/tmp/hoopr_phase1"
UPLOAD_TO_S3 <- "--upload-to-s3" %in% args
S3_BUCKET <- "s3://nba-sim-raw-data-lake/hoopr_phase1"
SEASONS <- 2002:2025

# Create output structure
categories <- c("league_dashboards", "static_reference", "draft", "standings")
for (cat in categories) {
  dir.create(file.path(OUTPUT_DIR, cat), recursive = TRUE, showWarnings = FALSE)
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("🏀 hoopR PHASE 1B: LEAGUE DASHBOARDS & STATIC DATA\n")
cat(rep("=", 80), "\n", sep = "")
cat("Seasons:", paste(SEASONS, collapse = ", "), "\n")
cat("Output:", OUTPUT_DIR, "\n")
cat("S3 Upload:", if (UPLOAD_TO_S3) "ENABLED" else "DISABLED", "\n")
cat(rep("=", 80), "\n\n", sep = "")

# Statistics tracker
stats <- list(
  total_calls = 0,
  successful_calls = 0,
  failed_calls = 0,
  total_rows = 0,
  start_time = Sys.time()
)

# Helper: Safe API call with retry
call_api_safe <- function(func, ..., max_retries = 3, delay = 2) {
  for (attempt in 1:max_retries) {
    result <- tryCatch({
      Sys.sleep(delay)
      func(...)
    }, error = function(e) {
      if (attempt < max_retries) {
        cat("  ⚠️  Attempt", attempt, "failed, retrying...\n")
        return(NULL)
      } else {
        cat("  ❌ Failed:", e$message, "\n")
        return(NULL)
      }
    })
    if (!is.null(result)) return(result)
  }
  return(NULL)
}

# Helper: Save CSV and upload to S3
save_csv <- function(data, filepath) {
  # Handle NULL or empty data
  if (is.null(data)) return(FALSE)

  # If data is a list (hoopR often returns lists), extract first data frame
  if (is.list(data) && !is.data.frame(data)) {
    # Find first non-null data frame in the list
    for (item in data) {
      if (is.data.frame(item) && nrow(item) > 0) {
        data <- item
        break
      }
    }
  }

  # Final check: must be a data frame with rows
  if (!is.data.frame(data)) return(FALSE)
  if (nrow(data) == 0) return(FALSE)

  dir.create(dirname(filepath), recursive = TRUE, showWarnings = FALSE)
  write_csv(data, filepath)

  if (UPLOAD_TO_S3) {
    s3_path <- gsub(OUTPUT_DIR, S3_BUCKET, filepath)
    system(paste("aws s3 cp", shQuote(filepath), s3_path, "--quiet"))
  }

  return(TRUE)
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("PHASE 1B: LEAGUE DASHBOARDS (Per-Season)\n")
cat(rep("=", 80), "\n\n", sep = "")

for (season in SEASONS) {
  season_str <- paste0(season, "-", substr(season + 1, 3, 4))
  cat("\n📅 Season", season_str, "\n")

  # Player stats
  cat("  📊 League player stats...")
  player_stats <- call_api_safe(nba_leaguedashplayerstats, season = season_str, per_mode = "PerGame")
  if (!is.null(player_stats)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("player_stats_", season, ".csv"))
    if (save_csv(player_stats, filepath)) {
      cat(" ✅", nrow(player_stats), "players\n")
      stats$total_rows <- stats$total_rows + nrow(player_stats)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Team stats
  cat("  📊 League team stats...")
  team_stats <- call_api_safe(nba_leaguedashteamstats, season = season_str, per_mode = "PerGame")
  if (!is.null(team_stats)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("team_stats_", season, ".csv"))
    if (save_csv(team_stats, filepath)) {
      cat(" ✅", nrow(team_stats), "teams\n")
      stats$total_rows <- stats$total_rows + nrow(team_stats)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # 5-man lineups
  cat("  📊 5-man lineups...")
  lineups <- call_api_safe(nba_leaguedashlineups, season = season_str, group_quantity = 5)
  if (!is.null(lineups)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("lineups_5man_", season, ".csv"))
    if (save_csv(lineups, filepath)) {
      cat(" ✅", nrow(lineups), "lineups\n")
      stats$total_rows <- stats$total_rows + nrow(lineups)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Player tracking stats
  cat("  📊 Player tracking stats...")
  pt_stats <- call_api_safe(nba_leaguedashptstats, season = season_str, pt_measure_type = "SpeedDistance")
  if (!is.null(pt_stats)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("player_tracking_", season, ".csv"))
    if (save_csv(pt_stats, filepath)) {
      cat(" ✅", nrow(pt_stats), "players\n")
      stats$total_rows <- stats$total_rows + nrow(pt_stats)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Hustle stats - player
  cat("  📊 Hustle stats (player)...")
  hustle_player <- call_api_safe(nba_leaguehustlestatsplayer, season = season_str)
  if (!is.null(hustle_player)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("hustle_player_", season, ".csv"))
    if (save_csv(hustle_player, filepath)) {
      cat(" ✅", nrow(hustle_player), "players\n")
      stats$total_rows <- stats$total_rows + nrow(hustle_player)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Hustle stats - team
  cat("  📊 Hustle stats (team)...")
  hustle_team <- call_api_safe(nba_leaguehustlestatsteam, season = season_str)
  if (!is.null(hustle_team)) {
    filepath <- file.path(OUTPUT_DIR, "league_dashboards", paste0("hustle_team_", season, ".csv"))
    if (save_csv(hustle_team, filepath)) {
      cat(" ✅", nrow(hustle_team), "teams\n")
      stats$total_rows <- stats$total_rows + nrow(hustle_team)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1

  # Standings
  cat("  📊 Standings...")
  standings <- call_api_safe(nba_leaguestandingsv3, season = season_str)
  if (!is.null(standings)) {
    filepath <- file.path(OUTPUT_DIR, "standings", paste0("standings_", season, ".csv"))
    if (save_csv(standings, filepath)) {
      cat(" ✅", nrow(standings), "teams\n")
      stats$total_rows <- stats$total_rows + nrow(standings)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1
}

cat("\n", rep("=", 80), "\n", sep = "")
cat("PHASE 1C: STATIC/REFERENCE DATA (One-Time)\n")
cat(rep("=", 80), "\n\n", sep = "")

# All-time leaders
cat("📊 All-time leaders...")
leaders <- call_api_safe(nba_alltimeleadersgrids)
if (!is.null(leaders)) {
  filepath <- file.path(OUTPUT_DIR, "static_reference", "alltime_leaders.csv")
  if (save_csv(leaders, filepath)) {
    cat(" ✅", nrow(leaders), "records\n")
    stats$total_rows <- stats$total_rows + nrow(leaders)
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# All players (current roster data)
cat("📊 All players (2024-25)...")
all_players <- call_api_safe(nba_commonallplayers, season = "2024-25")
if (!is.null(all_players)) {
  filepath <- file.path(OUTPUT_DIR, "static_reference", "all_players_2024.csv")
  if (save_csv(all_players, filepath)) {
    cat(" ✅", nrow(all_players), "players\n")
    stats$total_rows <- stats$total_rows + nrow(all_players)
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# All teams
cat("📊 All teams...")
all_teams <- call_api_safe(nba_teams)
if (!is.null(all_teams)) {
  filepath <- file.path(OUTPUT_DIR, "static_reference", "all_teams.csv")
  if (save_csv(all_teams, filepath)) {
    cat(" ✅", nrow(all_teams), "teams\n")
    stats$total_rows <- stats$total_rows + nrow(all_teams)
    stats$successful_calls <- stats$successful_calls + 1
  }
} else {
  stats$failed_calls <- stats$failed_calls + 1
}
stats$total_calls <- stats$total_calls + 1

# Draft history (per year)
cat("\n📊 Draft history by year:\n")
for (year in 2002:2024) {
  season_str <- paste0(year, "-", substr(year + 1, 3, 4))
  cat("  ", season_str, "...")

  draft <- call_api_safe(nba_drafthistory, season = season_str)
  if (!is.null(draft)) {
    filepath <- file.path(OUTPUT_DIR, "draft", paste0("draft_", year, ".csv"))
    if (save_csv(draft, filepath)) {
      cat(" ✅", nrow(draft), "picks\n")
      stats$total_rows <- stats$total_rows + nrow(draft)
      stats$successful_calls <- stats$successful_calls + 1
    }
  } else {
    cat(" ❌\n")
    stats$failed_calls <- stats$failed_calls + 1
  }
  stats$total_calls <- stats$total_calls + 1
}

# Final summary
cat("\n", rep("=", 80), "\n", sep = "")
cat("✅ PHASE 1B COMPLETE\n")
cat(rep("=", 80), "\n\n", sep = "")

elapsed <- difftime(Sys.time(), stats$start_time, units = "mins")
cat("📊 Final Statistics:\n")
cat("  Total API calls:", stats$total_calls, "\n")
cat("  Successful:", stats$successful_calls, "\n")
cat("  Failed:", stats$failed_calls, "\n")
cat("  Success rate:", round(100 * stats$successful_calls / stats$total_calls, 1), "%\n")
cat("  Total data rows:", format(stats$total_rows, big.mark = ","), "\n")
cat("  Runtime:", round(elapsed, 1), "minutes\n")
cat("\n")
