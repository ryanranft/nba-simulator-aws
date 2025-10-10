#!/bin/bash
################################################################################
# Test Overnight Workflow (Core Quality Tracking Only)
#
# Tests steps 3-9 of the overnight workflow without running time-consuming scrapers.
# Use this to verify the quality tracking pipeline works correctly.
################################################################################

set -e
cd /Users/ryanranft/nba-simulator-aws

echo "========================================================================"
echo "TEST: OVERNIGHT CORE WORKFLOW (SKIP SCRAPERS)"
echo "========================================================================"
echo ""

# Activate environment
eval "$(conda shell.bash hook)"
conda activate nba-aws
source /Users/ryanranft/nba-sim-credentials.env

echo "Step 3: Update Game ID Mappings"
python scripts/mapping/extract_espn_hoopr_game_mapping.py
echo ""

echo "Step 4: Rebuild Unified Database"
python scripts/etl/build_unified_database.py
echo ""

echo "Step 5: Detect Discrepancies (limit 100 for testing)"
python scripts/validation/detect_data_discrepancies.py --limit 100
echo ""

echo "Step 6: Export ML Quality Dataset"
python scripts/validation/export_ml_quality_dataset.py
echo ""

echo "Step 7: Generate Daily Report"
report_file="reports/daily_quality_report_$(date +%Y%m%d).md"
cat > "$report_file" <<EOF
# Daily Data Quality Report (TEST)

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')

## Database Statistics

### Unified Database
- **Total games:** $(sqlite3 /tmp/unified_nba.db "SELECT COUNT(*) FROM source_coverage;")
- **Dual-source games:** $(sqlite3 /tmp/unified_nba.db "SELECT COUNT(*) FROM source_coverage WHERE has_espn = 1 AND has_hoopr = 1;")
- **Games with discrepancies:** $(sqlite3 /tmp/unified_nba.db "SELECT COUNT(*) FROM source_coverage WHERE has_discrepancies = 1;")

## Quality Distribution

\`\`\`
$(sqlite3 /tmp/unified_nba.db "SELECT
    CASE
        WHEN quality_score >= 90 THEN 'High (90-100)'
        WHEN quality_score >= 70 THEN 'Medium (70-89)'
        ELSE 'Low (<70)'
    END as quality,
    COUNT(*) as games
FROM quality_scores
GROUP BY quality
ORDER BY quality DESC;")
\`\`\`
EOF
echo "✓ Report created: $report_file"
echo ""

echo "========================================================================"
echo "✅ TEST COMPLETE - CORE WORKFLOW WORKING"
echo "========================================================================"
echo ""
echo "Files created:"
ls -lh scripts/mapping/espn_hoopr_game_mapping.json
ls -lh data/ml_quality/ml_quality_dataset_*.json | tail -1
ls -lh data/ml_quality/ml_quality_dataset_*.csv | tail -1
ls -lh reports/daily_quality_report_*.md | tail -1
