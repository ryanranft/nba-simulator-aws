#!/bin/bash
# Generate SHA mapping after git-filter-repo
# This script compares commit messages before/after to create a mapping

set -e

echo "🔍 Generating SHA mapping (Old → New)..."
echo ""

# Check if we're in the right directory
if [ ! -f "SHA_MAPPING.md" ]; then
    echo "❌ Error: SHA_MAPPING.md not found. Run from project root."
    exit 1
fi

# Create temporary files for comparison
TEMP_DIR=$(mktemp -d)
OLD_FILE="${TEMP_DIR}/old_commits.txt"
NEW_FILE="${TEMP_DIR}/new_commits.txt"
MAPPING_FILE="${TEMP_DIR}/sha_mapping.txt"

# Extract old commit list from SHA_MAPPING.md (between the markers)
echo "📋 Extracting old commit list from SHA_MAPPING.md..."
awk '/^```$/,/^```$/' SHA_MAPPING.md | grep -E "^[a-f0-9]{7}" | awk '{print $1, $2, substr($0, index($0,$4))}' > "$OLD_FILE"

# Get current (new) commit list
echo "📋 Getting current commit list from git..."
git log --all --format="%h %H %s" > "$NEW_FILE"

# Create mapping by matching commit messages
echo "🔗 Matching commits by message..."
echo ""
echo "Old SHA → New SHA : Commit Message"
echo "============================================"

declare -A SHA_MAP

while IFS= read -r old_line; do
    old_short=$(echo "$old_line" | awk '{print $1}')
    old_full=$(echo "$old_line" | awk '{print $2}')
    # Get everything after the second field (commit message)
    old_msg=$(echo "$old_line" | cut -d' ' -f3-)

    # Find matching commit in new list by message
    new_line=$(grep -F "$old_msg" "$NEW_FILE" || echo "")

    if [ -n "$new_line" ]; then
        new_short=$(echo "$new_line" | awk '{print $1}')
        new_full=$(echo "$new_line" | awk '{print $2}')

        echo "${old_short} → ${new_short} : ${old_msg}"

        # Store in associative array for later use
        SHA_MAP[$old_short]=$new_short

        # Save to mapping file
        echo "${old_short}:${new_short}:${old_full}:${new_full}:${old_msg}" >> "$MAPPING_FILE"
    else
        echo "${old_short} → ??????? : ${old_msg} (NOT FOUND - may have been squashed or deleted)"
    fi
done < "$OLD_FILE"

echo ""
echo "✅ Mapping generated"
echo ""

# Ask if user wants to update files
echo "📝 Files that need SHA updates:"
echo "  1. HISTORY_REWRITE_GUIDE.md"
echo "  2. SECURITY_AUDIT_REPORT.md"
echo "  3. docs/adr/005-git-ssh-authentication.md"
echo "  4. COMMAND_LOG.md"
echo ""

read -p "Update these files automatically? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔧 Updating files..."

    # Read mapping file and perform replacements
    while IFS=: read -r old_short new_short old_full new_full msg; do
        echo "  Replacing ${old_short} with ${new_short}..."

        # Update all files (macOS compatible sed)
        if [ -f "HISTORY_REWRITE_GUIDE.md" ]; then
            sed -i '' "s/${old_short}/${new_short}/g" HISTORY_REWRITE_GUIDE.md
        fi

        if [ -f "SECURITY_AUDIT_REPORT.md" ]; then
            sed -i '' "s/${old_short}/${new_short}/g" SECURITY_AUDIT_REPORT.md
        fi

        if [ -f "docs/adr/005-git-ssh-authentication.md" ]; then
            sed -i '' "s/${old_short}/${new_short}/g" docs/adr/005-git-ssh-authentication.md
        fi

        if [ -f "COMMAND_LOG.md" ]; then
            sed -i '' "s/${old_short}/${new_short}/g" COMMAND_LOG.md
        fi
    done < "$MAPPING_FILE"

    echo ""
    echo "✅ Files updated!"
    echo ""
    echo "📋 Verification:"
    echo "  Run: git diff"
    echo "  Check that old SHAs have been replaced with new ones"
else
    echo "⏭️  Skipping automatic update"
    echo ""
    echo "📄 Mapping saved to: ${MAPPING_FILE}"
    echo "  Use this file to manually update documentation"
fi

# Update SHA_MAPPING.md with the actual mapping
echo ""
read -p "Update SHA_MAPPING.md with the new mapping table? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📝 Updating SHA_MAPPING.md..."

    # Create new mapping section
    MAPPING_TABLE="## SHA Mapping Table (Generated $(date +%Y-%m-%d))\n\n"
    MAPPING_TABLE+="| Old Short SHA | New Short SHA | Old Full SHA | New Full SHA | Commit Message |\n"
    MAPPING_TABLE+="|---------------|---------------|--------------|--------------|----------------|\n"

    while IFS=: read -r old_short new_short old_full new_full msg; do
        # Truncate full SHAs for display
        old_full_short="${old_full:0:12}..."
        new_full_short="${new_full:0:12}..."
        MAPPING_TABLE+="| ${old_short} | ${new_short} | ${old_full_short} | ${new_full_short} | ${msg} |\n"
    done < "$MAPPING_FILE"

    # Replace the placeholder table in SHA_MAPPING.md
    # This is a simplified approach - you might want to do this manually
    echo ""
    echo "✅ Mapping table generated"
    echo "   Copy the content below to SHA_MAPPING.md:"
    echo ""
    echo -e "$MAPPING_TABLE"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 Done!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Verify no old SHAs remain: grep -r \"b6dac89\\|e315e48\\|2134b36\" ."
echo "  3. Commit updated documentation: git add . && git commit -m \"Update SHA references after git-filter-repo\""
