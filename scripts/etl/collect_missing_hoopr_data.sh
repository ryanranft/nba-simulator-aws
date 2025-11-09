#!/bin/bash
# hoopR Missing Data Collection - Execution Plan
# Collects Dec 2, 2024 → Nov 9, 2025 data
#
# Runtime: ~2 hours
# Cost: ~$0.08/month
# Output: Parquet files ready for nba-mcp-synthesis

set -e  # Exit on error

echo "========================================"
echo "HOOPR MISSING DATA COLLECTION"
echo "========================================"
echo ""
echo "📅 Target Range: Dec 2, 2024 → Nov 9, 2025"
echo "📊 Seasons: 2024, 2025"
echo "⏱️  Estimated Time: ~2 hours"
echo ""

# Step 1: Navigate to nba-simulator-aws
echo "Step 1: Setting up environment..."
cd /Users/ryanranft/nba-simulator-aws

# Activate conda environment
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate nba-aws

# Verify R is available
if ! command -v Rscript &> /dev/null; then
    echo "❌ Rscript not found. Please install R."
    exit 1
fi

# Verify hoopR package is installed
echo "Checking hoopR package..."
Rscript -e "if (!require('hoopR')) { install.packages('hoopR', repos='https://cloud.r-project.org') }"

echo "✅ Environment ready"
echo ""

# Step 2: Create modified collection script
echo "Step 2: Creating modified collection script..."

cat > /tmp/collect_hoopr_2024_2025.R << 'EOF'
#!/usr/bin/env Rscript
# Collect hoopR data for 2024-2025 seasons only
# Fills gap: Dec 2, 2024 → Nov 9, 2025

library(hoopR)
library(dplyr)
library(arrow)

# Configuration
SEASONS <- c(2024, 2025)
OUTPUT_DIR <- "/tmp/hoopr_missing_data"
BACKUP_DIR <- "/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba"

# Create output directory
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)
dir.create(BACKUP_DIR, showWarnings = FALSE, recursive = TRUE)

cat("\n========================================\n")
cat("HOOPR DATA COLLECTION: 2024-2025\n")
cat("========================================\n\n")

# Function to collect and save data
collect_and_save <- function(load_func, func_name, seasons) {
  cat(sprintf("\n📊 Collecting %s...\n", func_name))

  for (season in seasons) {
    cat(sprintf("  Season %d-%d: ", season, season + 1))

    tryCatch({
      # Call the hoopR function
      data <- load_func(seasons = season)

      if (is.null(data) || nrow(data) == 0) {
        cat("⚠️  No data\n")
        next
      }

      # Save as CSV (temporary)
      csv_file <- file.path(OUTPUT_DIR, sprintf("%s_%d.csv", func_name, season))
      write.csv(data, csv_file, row.names = FALSE)

      # Save as Parquet (optimized)
      parquet_dir <- file.path(BACKUP_DIR, func_name, "parquet")
      dir.create(parquet_dir, showWarnings = FALSE, recursive = TRUE)
      parquet_file <- file.path(parquet_dir, sprintf("nba_data_%d.parquet", season))
      write_parquet(data, parquet_file)

      cat(sprintf("✅ %d rows → %s\n", nrow(data), parquet_file))

    }, error = function(e) {
      cat(sprintf("❌ Error: %s\n", e$message))
    })

    # Rate limiting (be nice to the API)
    Sys.sleep(2)
  }
}

# Collect Phase 1 data (4 datasets)
cat("\n🔄 Phase 1: Bulk Data Loaders\n")
cat("================================\n")

collect_and_save(load_nba_schedule, "load_nba_schedule", SEASONS)
collect_and_save(load_nba_team_box, "load_nba_team_box", SEASONS)
collect_and_save(load_nba_player_box, "load_nba_player_box", SEASONS)
collect_and_save(load_nba_pbp, "load_nba_pbp", SEASONS)

cat("\n========================================\n")
cat("✅ COLLECTION COMPLETE\n")
cat("========================================\n")
cat(sprintf("📁 CSV files: %s\n", OUTPUT_DIR))
cat(sprintf("📁 Parquet files: %s\n", BACKUP_DIR))
cat("\n")
EOF

chmod +x /tmp/collect_hoopr_2024_2025.R

echo "✅ Collection script created: /tmp/collect_hoopr_2024_2025.R"
echo ""

# Step 3: Run collection
echo "Step 3: Running hoopR collection..."
echo "⏱️  This will take ~30-45 minutes..."
echo ""

Rscript /tmp/collect_hoopr_2024_2025.R

# Step 4: Verify output
echo ""
echo "Step 4: Verifying output..."
echo ""

PARQUET_DIR="/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba"

echo "📁 Parquet files created:"
find "$PARQUET_DIR" -name "nba_data_2024.parquet" -o -name "nba_data_2025.parquet" | sort

echo ""
echo "📊 File sizes:"
find "$PARQUET_DIR" -name "nba_data_2024.parquet" -o -name "nba_data_2025.parquet" -exec ls -lh {} \; | awk '{print $9, $5}'

echo ""
echo "========================================"
echo "✅ DATA COLLECTION COMPLETE"
echo "========================================"
echo ""
echo "Next Steps:"
echo "  1. Switch to nba-mcp-synthesis project"
echo "  2. Run: python scripts/load_parquet_to_postgres.py --years 2024-2025"
echo "  3. Verify: python scripts/validate_hoopr_data.py"
echo ""
echo "Files ready at:"
echo "  $PARQUET_DIR"
echo ""
