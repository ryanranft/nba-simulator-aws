#!/bin/bash
# Archive .gitignored documentation files with git SHA

set -e

# Configuration - Auto-detect sport from directory name
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Extract sport name from project directory (e.g., nba-simulator-aws -> nba)
SPORT=$(echo "$PROJECT_NAME" | sed -E 's/^([a-z]+)-simulator.*/\1/')

# Archive base with sport-specific subfolder (configurable via environment variable)
ARCHIVE_BASE="${ARCHIVE_BASE:-$HOME/sports-simulator-archives/$SPORT}"

# Get current git info
cd "$PROJECT_DIR"
CURRENT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT_DATE=$(git log -1 --format=%ci)
COMMIT_MSG=$(git log -1 --format=%s)

# Create archive directory structure
ARCHIVE_DIR="$ARCHIVE_BASE/$CURRENT_SHA"
mkdir -p "$ARCHIVE_DIR"

echo "📦 Archiving .gitignored files for commit: $SHORT_SHA"
echo "📁 Archive location: $ARCHIVE_DIR"

# Create git metadata file
cat > "$ARCHIVE_DIR/git-info.txt" << EOF
=================================================================
GIT SNAPSHOT METADATA
=================================================================

Full SHA:     $CURRENT_SHA
Short SHA:    $SHORT_SHA
Branch:       $BRANCH
Commit Date:  $COMMIT_DATE
Commit Msg:   $COMMIT_MSG

=================================================================
ARCHIVED FILES
=================================================================

EOF

# Files to archive (from .gitignore)
FILES=(
    "COMMIT_VERIFICATION.md"
    "EXTRACTION_PROGRESS_SNAPSHOT.md"
    "EXTRACTION_STATUS.md"
    "OVERNIGHT_AUTOMATION_STATUS_old.md"
    "OVERNIGHT_EXTRACTION_STATUS.md"
    "PYCHARM_DATABASE_SETUP.md"
    "OVERNIGHT_AUTOMATION_STATUS.md"
    "OVERNIGHT_STATUS.md"
    "COMMAND_LOG.md"
)

# Additional files that might exist
OPTIONAL_FILES=(
    "*.pid"
    "*_STATUS.md"
    "*_PROGRESS.md"
)

# Archive each file if it exists
COUNT=0
for file in "${FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        cp "$PROJECT_DIR/$file" "$ARCHIVE_DIR/" || true
        echo "✅ $file" >> "$ARCHIVE_DIR/git-info.txt"
        echo "  ✓ Archived: $file"
        COUNT=$((COUNT + 1))
    fi
done

# Archive log files (but not extract logs which are huge)
if ls "$PROJECT_DIR"/*.log 1> /dev/null 2>&1; then
    mkdir -p "$ARCHIVE_DIR/logs"
    for logfile in "$PROJECT_DIR"/*.log; do
        filename=$(basename "$logfile")
        # Skip massive extract logs
        if [[ ! "$filename" =~ ^extract.*\.log$ ]]; then
            cp "$logfile" "$ARCHIVE_DIR/logs/"
            echo "✅ logs/$filename" >> "$ARCHIVE_DIR/git-info.txt"
            echo "  ✓ Archived: logs/$filename"
            ((COUNT++))
        fi
    done
fi

# Footer in git-info.txt
cat >> "$ARCHIVE_DIR/git-info.txt" << EOF

=================================================================
Total files archived: $COUNT
Archive created: $(date)
=================================================================
EOF

# Update master index
INDEX_FILE="$ARCHIVE_BASE/README.md"
if [ ! -f "$INDEX_FILE" ]; then
    cat > "$INDEX_FILE" << EOF
# ${SPORT^^} Simulator Archive - Gitignored Files

This archive contains \`.gitignored\` documentation files organized by git commit SHA.

Each folder corresponds to a specific git commit and contains:
- `git-info.txt` - Git metadata (SHA, date, message)
- Documentation files that were excluded from GitHub
- Log files (excluding massive extraction logs)

## How to Use

1. Find the git commit SHA from your project history
2. Navigate to the corresponding folder
3. All gitignored documentation files from that commit are preserved

## Folders

EOF
fi

# Add entry to index if not already present
if ! grep -q "$CURRENT_SHA" "$INDEX_FILE"; then
    echo "- **$SHORT_SHA** - $BRANCH - $(date +%Y-%m-%d) - $COMMIT_MSG ($COUNT files)" >> "$INDEX_FILE"
    echo "  📝 Updated archive index"
fi

echo ""
echo "✅ Archive complete!"
echo "📂 Location: $ARCHIVE_DIR"
echo "📊 Files archived: $COUNT"
echo ""
echo "To view later: ls $ARCHIVE_DIR"
echo "To see all archives: cat $INDEX_FILE"