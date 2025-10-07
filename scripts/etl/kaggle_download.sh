#!/bin/bash
#
# Kaggle Basketball Database Download
#
# Downloads the comprehensive Kaggle NBA database (Wyatt Walsh)
# - Source: https://www.kaggle.com/datasets/wyattowalsh/basketball
# - Coverage: 1946-2025 (65,000+ games, 13M+ play-by-play rows)
# - Format: SQLite database
# - Size: ~2-5 GB
#
# Prerequisites:
# - Kaggle account and API credentials configured
# - kaggle package installed: pip install kaggle
# - API token at ~/.kaggle/kaggle.json
#
# Estimated runtime: 5-15 minutes (depends on download speed)
#
# Output: SQLite database file ready to query or load into RDS

set -e  # Exit on error

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
DOWNLOAD_DIR="$PROJECT_DIR/data/kaggle"
LOG_DIR="$PROJECT_DIR/logs/kaggle_download_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$LOG_DIR"

echo "📦 Starting Kaggle Basketball Database Download"
echo "📁 Download directory: $DOWNLOAD_DIR"
echo "📁 Logs: $LOG_DIR"
echo "⏰ Started: $(date)"
echo ""

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

cd "$PROJECT_DIR"

#############################################
# Check Prerequisites
#############################################
echo "🔍 Checking prerequisites..."
echo ""

# Check if kaggle package is installed
if ! python -c "import kaggle" 2>/dev/null; then
    echo "❌ Kaggle package not installed"
    echo "Installing kaggle package..."
    pip install kaggle
fi

# Check if Kaggle API credentials exist
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo ""
    echo "❌ Kaggle API credentials not found!"
    echo ""
    echo "To set up Kaggle API:"
    echo "1. Go to https://www.kaggle.com/settings/account"
    echo "2. Scroll to 'API' section"
    echo "3. Click 'Create New Token'"
    echo "4. Save kaggle.json to ~/.kaggle/"
    echo "5. Run: chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    echo "Then re-run this script."
    exit 1
fi

echo "✅ Kaggle package installed"
echo "✅ Kaggle API credentials found"
echo ""

#############################################
# Download Database
#############################################
echo "================================================"
echo "Downloading Kaggle Basketball Database"
echo "================================================"
echo "📦 Dataset: wyattowalsh/basketball"
echo "💾 Size: ~2-5 GB (compressed)"
echo "⏱️  This may take 5-15 minutes..."
echo ""

KAGGLE_LOG="$LOG_DIR/kaggle_download.log"
KAGGLE_ERRORS="$LOG_DIR/kaggle_download_errors.log"

# Download dataset
kaggle datasets download -d wyattowalsh/basketball -p "$DOWNLOAD_DIR" \
    >> "$KAGGLE_LOG" 2>> "$KAGGLE_ERRORS"

if [ $? -eq 0 ]; then
    echo "✅ Download complete"
else
    echo "❌ Download failed (see $KAGGLE_ERRORS)"
    exit 1
fi

echo ""

#############################################
# Extract Database
#############################################
echo "================================================"
echo "Extracting Database Files"
echo "================================================"

# Find the downloaded zip file
ZIP_FILE=$(find "$DOWNLOAD_DIR" -name "*.zip" -type f | head -1)

if [ -z "$ZIP_FILE" ]; then
    echo "❌ No zip file found in $DOWNLOAD_DIR"
    exit 1
fi

echo "📦 Found: $(basename "$ZIP_FILE")"
echo "📂 Extracting..."

unzip -q "$ZIP_FILE" -d "$DOWNLOAD_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Extraction complete"
    # Remove zip file to save space
    rm "$ZIP_FILE"
    echo "🗑️  Removed zip file"
else
    echo "❌ Extraction failed"
    exit 1
fi

echo ""

#############################################
# Verify Database
#############################################
echo "================================================"
echo "Verifying SQLite Database"
echo "================================================"

# Find the SQLite database file
DB_FILE=$(find "$DOWNLOAD_DIR" -name "*.sqlite" -o -name "*.db" | head -1)

if [ -z "$DB_FILE" ]; then
    echo "❌ No SQLite database file found"
    exit 1
fi

echo "📊 Database: $(basename "$DB_FILE")"
echo "💾 Size: $(du -h "$DB_FILE" | cut -f1)"
echo ""

# Query database schema
echo "🔍 Database schema:"
sqlite3 "$DB_FILE" ".tables" | tee -a "$KAGGLE_LOG"
echo ""

# Count records in key tables
echo "📊 Record counts:"
sqlite3 "$DB_FILE" "SELECT 'Teams: ' || COUNT(*) FROM team;" 2>/dev/null || echo "  team table not found"
sqlite3 "$DB_FILE" "SELECT 'Players: ' || COUNT(*) FROM player;" 2>/dev/null || echo "  player table not found"
sqlite3 "$DB_FILE" "SELECT 'Games: ' || COUNT(*) FROM game;" 2>/dev/null || echo "  game table not found"

echo ""

#############################################
# Upload to S3 (Optional)
#############################################
echo "================================================"
echo "Upload to S3"
echo "================================================"

read -p "Upload database to S3? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    S3_KEY="kaggle/basketball_database/$(basename "$DB_FILE")"

    echo "☁️  Uploading to s3://nba-sim-raw-data-lake/$S3_KEY"
    aws s3 cp "$DB_FILE" "s3://nba-sim-raw-data-lake/$S3_KEY"

    if [ $? -eq 0 ]; then
        echo "✅ Upload complete"
    else
        echo "❌ Upload failed"
    fi
else
    echo "⏭️  Skipping S3 upload"
fi

echo ""

#############################################
# Summary
#############################################
echo "================================================"
echo "🎉 Kaggle Database Download Complete!"
echo "================================================"
echo "⏰ Finished: $(date)"
echo ""
echo "📊 Database Information:"
echo "  - Location: $DB_FILE"
echo "  - Size: $(du -h "$DB_FILE" | cut -f1)"
echo "  - Format: SQLite"
echo ""
echo "📝 Logs:"
echo "  - Download log: $KAGGLE_LOG"
echo "  - Error log: $KAGGLE_ERRORS"
echo ""
echo "🔍 Quick Query Examples:"
echo "  # Open database:"
echo "    sqlite3 $DB_FILE"
echo ""
echo "  # List tables:"
echo "    sqlite3 $DB_FILE '.tables'"
echo ""
echo "  # Count games:"
echo "    sqlite3 $DB_FILE 'SELECT COUNT(*) FROM game;'"
echo ""
echo "  # View schema:"
echo "    sqlite3 $DB_FILE '.schema game'"
echo ""
echo "📋 Next Steps:"
echo "  1. Explore database schema: sqlite3 $DB_FILE '.schema'"
echo "  2. Compare with your scraped data for validation"
echo "  3. Extract tables to CSV: sqlite3 $DB_FILE '.mode csv' '.output games.csv' 'SELECT * FROM game;'"
echo "  4. Load into RDS if needed (see scripts/db/load_kaggle_to_rds.py)"
echo ""
echo "💡 Use Cases:"
echo "  - Data validation (compare with ESPN/NBA Stats)"
echo "  - Fill gaps in your scraped data"
echo "  - Cross-reference player/team IDs"
echo "  - Historical data quality checks"
echo ""