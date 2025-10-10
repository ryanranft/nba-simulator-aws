#!/bin/bash
# Quick scraper status check

echo "==================================================================="
echo "SCRAPER STATUS - $(date)"
echo "==================================================================="
echo ""

# Check Basketball Reference (Recent)
if ps aux | grep -q "[s]crape_bbref_incremental.sh 2020 2025"; then
    echo "🏀 Basketball Reference (2020-2025): ✅ RUNNING"
    echo "   Latest log (last 3 lines):"
    tail -3 /tmp/bbref_2020-2025.log | sed 's/^/     /'
else
    echo "🏀 Basketball Reference (2020-2025): ⏸️  NOT RUNNING"
fi

echo ""

# Check Basketball Reference (Historical)
if ps aux | grep -q "[s]crape_bbref_incremental.sh 1947 2019"; then
    echo "📚 Basketball Reference (1947-2019): ✅ RUNNING"
    echo "   Latest log (last 3 lines):"
    tail -3 /tmp/bbref_1947-2019.log | sed 's/^/     /'
else
    echo "📚 Basketball Reference (1947-2019): ⏸️  NOT RUNNING"
fi

echo ""
echo "📊 Total Basketball Reference progress:"
echo "   Completed operations: $(ls /tmp/basketball_reference_incremental/*.complete 2>/dev/null | wc -l | tr -d ' ')/553 total (79 seasons × 7 types)"

echo ""

# Check NBA API Comprehensive
if ps aux | grep -q "[o]vernight_nba_api_comprehensive"; then
    echo "📊 NBA API Comprehensive (1996-2025): ✅ RUNNING"
    echo "   Latest log (last 5 lines):"
    tail -5 /tmp/nba_api_comprehensive.log | sed 's/^/     /'
    echo "   Progress: $(grep -c '✅ Season .* complete' /tmp/nba_api_comprehensive.log 2>/dev/null || echo 0)/30 seasons"
else
    echo "📊 NBA API Comprehensive: ⏸️  NOT RUNNING"
fi

echo ""
echo "==================================================================="
echo "Monitor logs:"
echo "  Basketball Ref (Recent):     tail -f /tmp/bbref_2020-2025.log"
echo "  Basketball Ref (Historical): tail -f /tmp/bbref_1947-2019.log"
echo "  NBA API Comprehensive:       tail -f /tmp/nba_api_comprehensive.log"
echo "===================================================================" 
