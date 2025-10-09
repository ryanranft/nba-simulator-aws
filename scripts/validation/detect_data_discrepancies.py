#!/usr/bin/env python3
"""
Detect Data Quality Discrepancies Between Sources

Compares games available in multiple sources (ESPN, hoopR, etc.) to identify
where data disagrees. Logs discrepancies to unified database for ML quality tracking.

Strategy:
1. Load games that have both ESPN and hoopR data (28,777 games)
2. Compare:
   - Event counts (how many play-by-play events)
   - Final scores (home_score, away_score)
   - Game dates
   - Other metadata fields
3. Calculate severity based on discrepancy magnitude
4. Update unified database quality scores

Key Principles:
- Only compare games available in BOTH sources
- Source databases remain pure (read-only)
- All findings logged to unified database
- Quality scores updated based on discrepancy severity

Usage:
    python scripts/validation/detect_data_discrepancies.py
    python scripts/validation/detect_data_discrepancies.py --limit 100  # Test
    python scripts/validation/detect_data_discrepancies.py --verbose    # Detailed output
    python scripts/validation/detect_data_discrepancies.py --game-id 401584669  # Single game

Version: 1.0
Created: October 9, 2025
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
from collections import defaultdict

# Database paths
ESPN_DB = "/tmp/espn_local.db"
HOOPR_DB = "/tmp/hoopr_local.db"
UNIFIED_DB = "/tmp/unified_nba.db"

# Game ID mapping
MAPPING_FILE = Path(__file__).parent.parent / "mapping" / "espn_hoopr_game_mapping.json"

# Severity thresholds
SEVERITY_THRESHOLDS = {
    'event_count': {
        'LOW': 5.0,      # <5% difference
        'MEDIUM': 10.0,  # 5-10% difference
        'HIGH': 10.0     # >10% difference
    },
    'score': {
        'LOW': 2,        # ±1-2 points
        'MEDIUM': 5,     # ±3-5 points
        'HIGH': 5        # >5 points
    },
    'date': {
        'LOW': 0,        # Same date
        'MEDIUM': 1,     # 1 day off
        'HIGH': 1        # >1 day off
    }
}


def load_game_mapping() -> Tuple[Dict, Dict]:
    """Load ESPN-to-hoopR game ID mapping."""

    with open(MAPPING_FILE) as f:
        data = json.load(f)

    return data['espn_to_hoopr'], data['hoopr_to_espn']


def get_dual_source_games(unified_conn, limit: Optional[int] = None) -> List[Dict]:
    """Get games that have both ESPN and hoopR data."""

    print("=" * 70)
    print("LOAD DUAL-SOURCE GAMES")
    print("=" * 70)
    print()

    cursor = unified_conn.cursor()

    query = """
        SELECT game_id, game_date,
               espn_event_count, hoopr_event_count
        FROM source_coverage
        WHERE has_espn = 1 AND has_hoopr = 1
        ORDER BY game_date DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)

    games = []
    for row in cursor.fetchall():
        games.append({
            'game_id': row[0],
            'game_date': row[1],
            'espn_event_count': row[2],
            'hoopr_event_count': row[3]
        })

    print(f"✓ Loaded {len(games):,} dual-source games for comparison")
    print()

    cursor.close()
    return games


def get_espn_game_data(espn_conn, game_id: str) -> Optional[Dict]:
    """Get game data from ESPN database."""

    cursor = espn_conn.cursor()

    # Get schedule/game info
    cursor.execute("""
        SELECT game_id, game_date, home_team, away_team,
               home_score, away_score, pbp_event_count
        FROM games
        WHERE game_id = ?
    """, (game_id,))

    row = cursor.fetchone()
    cursor.close()

    if not row:
        return None

    return {
        'game_id': row[0],
        'game_date': row[1],
        'home_team': row[2],
        'away_team': row[3],
        'home_score': row[4],
        'away_score': row[5],
        'event_count': row[6]
    }


def get_hoopr_game_data(hoopr_conn, hoopr_game_id: str) -> Optional[Dict]:
    """Get game data from hoopR database."""

    cursor = hoopr_conn.cursor()

    # Get schedule info
    cursor.execute("""
        SELECT game_id, game_date,
               home_display_name, away_display_name,
               home_score, away_score
        FROM schedule
        WHERE game_id = ?
    """, (hoopr_game_id,))

    row = cursor.fetchone()

    if not row:
        cursor.close()
        return None

    # Get event count
    cursor.execute("""
        SELECT COUNT(*)
        FROM play_by_play
        WHERE game_id = ?
    """, (hoopr_game_id,))

    event_count = cursor.fetchone()[0]
    cursor.close()

    return {
        'game_id': row[0],
        'game_date': row[1],
        'home_team': row[2],
        'away_team': row[3],
        'home_score': row[4],
        'away_score': row[5],
        'event_count': event_count
    }


def calculate_severity(field_name: str, difference: float, pct_difference: float) -> str:
    """Calculate severity level based on field type and difference magnitude."""

    if field_name == 'event_count':
        thresholds = SEVERITY_THRESHOLDS['event_count']
        if pct_difference < thresholds['LOW']:
            return 'LOW'
        elif pct_difference < thresholds['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'HIGH'

    elif field_name in ['home_score', 'away_score']:
        thresholds = SEVERITY_THRESHOLDS['score']
        if abs(difference) <= thresholds['LOW']:
            return 'LOW'
        elif abs(difference) <= thresholds['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'HIGH'

    elif field_name == 'game_date':
        # Date difference in days (simplified)
        if difference == 0:
            return 'LOW'
        else:
            return 'HIGH'

    else:
        # Default severity
        if pct_difference < 5:
            return 'LOW'
        elif pct_difference < 10:
            return 'MEDIUM'
        else:
            return 'HIGH'


def detect_discrepancies(
    game_id: str,
    espn_data: Dict,
    hoopr_data: Dict,
    unified_conn,
    verbose: bool = False
) -> List[Dict]:
    """Detect all discrepancies between ESPN and hoopR for a single game."""

    discrepancies = []

    # Compare event counts
    if espn_data['event_count'] is not None and hoopr_data['event_count'] is not None:
        espn_count = espn_data['event_count']
        hoopr_count = hoopr_data['event_count']

        if espn_count != hoopr_count:
            difference = abs(espn_count - hoopr_count)
            avg = (espn_count + hoopr_count) / 2
            pct_diff = (difference / avg * 100) if avg > 0 else 0
            severity = calculate_severity('event_count', difference, pct_diff)

            # Recommend source with more events (usually more complete)
            recommended_source = 'ESPN' if espn_count > hoopr_count else 'hoopR'
            recommended_value = str(max(espn_count, hoopr_count))

            discrepancies.append({
                'game_id': game_id,
                'field_name': 'event_count',
                'espn_value': str(espn_count),
                'hoopr_value': str(hoopr_count),
                'difference': difference,
                'pct_difference': pct_diff,
                'severity': severity,
                'recommended_source': recommended_source,
                'recommended_value': recommended_value,
                'ml_impact_notes': f'Event count differs by {difference} ({pct_diff:.1f}%). {recommended_source} has more complete data.'
            })

            if verbose:
                print(f"  ⚠️  event_count: ESPN={espn_count}, hoopR={hoopr_count}, diff={difference} ({pct_diff:.1f}%), severity={severity}")

    # Compare home scores
    if espn_data['home_score'] is not None and hoopr_data['home_score'] is not None:
        espn_score = espn_data['home_score']
        hoopr_score = hoopr_data['home_score']

        if espn_score != hoopr_score:
            difference = abs(espn_score - hoopr_score)
            pct_diff = (difference / max(espn_score, hoopr_score) * 100) if max(espn_score, hoopr_score) > 0 else 0
            severity = calculate_severity('home_score', difference, pct_diff)

            discrepancies.append({
                'game_id': game_id,
                'field_name': 'home_score',
                'espn_value': str(espn_score),
                'hoopr_value': str(hoopr_score),
                'difference': difference,
                'pct_difference': pct_diff,
                'severity': severity,
                'recommended_source': 'ESPN',  # Default to ESPN for score discrepancies
                'recommended_value': str(espn_score),
                'ml_impact_notes': f'Home score differs by {difference} points. Manual verification needed.'
            })

            if verbose:
                print(f"  ⚠️  home_score: ESPN={espn_score}, hoopR={hoopr_score}, diff={difference}, severity={severity}")

    # Compare away scores
    if espn_data['away_score'] is not None and hoopr_data['away_score'] is not None:
        espn_score = espn_data['away_score']
        hoopr_score = hoopr_data['away_score']

        if espn_score != hoopr_score:
            difference = abs(espn_score - hoopr_score)
            pct_diff = (difference / max(espn_score, hoopr_score) * 100) if max(espn_score, hoopr_score) > 0 else 0
            severity = calculate_severity('away_score', difference, pct_diff)

            discrepancies.append({
                'game_id': game_id,
                'field_name': 'away_score',
                'espn_value': str(espn_score),
                'hoopr_value': str(hoopr_score),
                'difference': difference,
                'pct_difference': pct_diff,
                'severity': severity,
                'recommended_source': 'ESPN',
                'recommended_value': str(espn_score),
                'ml_impact_notes': f'Away score differs by {difference} points. Manual verification needed.'
            })

            if verbose:
                print(f"  ⚠️  away_score: ESPN={espn_score}, hoopR={hoopr_score}, diff={difference}, severity={severity}")

    # Compare game dates
    if espn_data['game_date'] != hoopr_data['game_date']:
        discrepancies.append({
            'game_id': game_id,
            'field_name': 'game_date',
            'espn_value': espn_data['game_date'],
            'hoopr_value': hoopr_data['game_date'],
            'difference': 1,  # Simplified (would need proper date diff)
            'pct_difference': None,
            'severity': 'HIGH',
            'recommended_source': 'ESPN',
            'recommended_value': espn_data['game_date'],
            'ml_impact_notes': 'Game date mismatch - critical data quality issue.'
        })

        if verbose:
            print(f"  ⚠️  game_date: ESPN={espn_data['game_date']}, hoopR={hoopr_data['game_date']}, severity=HIGH")

    return discrepancies


def log_discrepancy(unified_conn, discrepancy: Dict):
    """Log a discrepancy to the unified database."""

    cursor = unified_conn.cursor()

    cursor.execute("""
        INSERT INTO data_quality_discrepancies (
            game_id, field_name,
            espn_value, hoopr_value,
            difference, pct_difference, severity,
            recommended_source, recommended_value, ml_impact_notes,
            resolution_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DETECTED')
    """, (
        discrepancy['game_id'],
        discrepancy['field_name'],
        discrepancy['espn_value'],
        discrepancy['hoopr_value'],
        discrepancy['difference'],
        discrepancy['pct_difference'],
        discrepancy['severity'],
        discrepancy['recommended_source'],
        discrepancy['recommended_value'],
        discrepancy['ml_impact_notes']
    ))

    cursor.close()


def update_quality_scores(unified_conn, game_id: str, discrepancies: List[Dict]):
    """Update quality scores based on detected discrepancies."""

    cursor = unified_conn.cursor()

    # Check if game has discrepancies
    has_discrepancies = len(discrepancies) > 0

    # Count by field type
    has_event_count_issue = any(d['field_name'] == 'event_count' for d in discrepancies)
    has_score_issue = any(d['field_name'] in ['home_score', 'away_score'] for d in discrepancies)
    has_timing_issue = any(d['field_name'] == 'game_date' for d in discrepancies)

    # Calculate new quality score
    # Start with base score of 95 (dual-source)
    quality_score = 95

    # Deduct based on severity
    for disc in discrepancies:
        if disc['severity'] == 'HIGH':
            quality_score -= 10
        elif disc['severity'] == 'MEDIUM':
            quality_score -= 5
        elif disc['severity'] == 'LOW':
            quality_score -= 2

    # Floor at 50
    quality_score = max(quality_score, 50)

    # Determine uncertainty
    if quality_score >= 90:
        uncertainty = 'LOW'
    elif quality_score >= 70:
        uncertainty = 'MEDIUM'
    else:
        uncertainty = 'HIGH'

    # Update quality_scores table
    cursor.execute("""
        UPDATE quality_scores
        SET quality_score = ?,
            uncertainty = ?,
            has_event_count_issue = ?,
            has_score_issue = ?,
            has_timing_issue = ?,
            ml_notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE game_id = ?
    """, (
        quality_score,
        uncertainty,
        has_event_count_issue,
        has_score_issue,
        has_timing_issue,
        f'{len(discrepancies)} discrepancies detected. Quality reduced from 95 to {quality_score}.',
        game_id
    ))

    # Update source_coverage table
    cursor.execute("""
        UPDATE source_coverage
        SET has_discrepancies = ?,
            overall_quality_score = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE game_id = ?
    """, (has_discrepancies, quality_score, game_id))

    cursor.close()


def process_games(
    espn_conn,
    hoopr_conn,
    unified_conn,
    espn_to_hoopr: Dict,
    games: List[Dict],
    verbose: bool = False
):
    """Process all dual-source games and detect discrepancies."""

    print("=" * 70)
    print("DETECT DISCREPANCIES")
    print("=" * 70)
    print()

    total_games = len(games)
    games_with_discrepancies = 0
    total_discrepancies = 0

    discrepancy_types = defaultdict(int)
    severity_counts = defaultdict(int)

    print(f"Comparing {total_games:,} dual-source games...")
    print()

    for i, game in enumerate(games, 1):
        espn_game_id = game['game_id']
        hoopr_game_id = espn_to_hoopr.get(espn_game_id)

        if not hoopr_game_id:
            if verbose:
                print(f"[{i}/{total_games}] ⚠️  No hoopR mapping for {espn_game_id}")
            continue

        # Get data from both sources
        espn_data = get_espn_game_data(espn_conn, espn_game_id)
        hoopr_data = get_hoopr_game_data(hoopr_conn, hoopr_game_id)

        if not espn_data or not hoopr_data:
            if verbose:
                print(f"[{i}/{total_games}] ⚠️  Missing data for {espn_game_id}")
            continue

        # Detect discrepancies
        discrepancies = detect_discrepancies(
            espn_game_id,
            espn_data,
            hoopr_data,
            unified_conn,
            verbose=verbose
        )

        # Log discrepancies
        if discrepancies:
            games_with_discrepancies += 1
            total_discrepancies += len(discrepancies)

            for disc in discrepancies:
                log_discrepancy(unified_conn, disc)
                discrepancy_types[disc['field_name']] += 1
                severity_counts[disc['severity']] += 1

            if verbose or (i <= 10):
                print(f"[{i}/{total_games}] ⚠️  {espn_game_id}: {len(discrepancies)} discrepancies")
        else:
            if verbose and i <= 10:
                print(f"[{i}/{total_games}] ✓ {espn_game_id}: Perfect agreement")

        # Update quality scores
        update_quality_scores(unified_conn, espn_game_id, discrepancies)

        # Progress update
        if i % 1000 == 0:
            pct = i / total_games * 100
            print(f"  Progress: {i:,}/{total_games:,} ({pct:.1f}%) | "
                  f"Discrepancies: {games_with_discrepancies:,} games, "
                  f"{total_discrepancies:,} issues")

    # Commit all changes
    unified_conn.commit()

    print()
    print("=" * 70)
    print("DISCREPANCY DETECTION SUMMARY")
    print("=" * 70)
    print()
    print(f"Total games analyzed:        {total_games:,}")
    print(f"Games with discrepancies:    {games_with_discrepancies:,} ({games_with_discrepancies/total_games*100:.1f}%)")
    print(f"Games with perfect agreement: {total_games - games_with_discrepancies:,} ({(total_games - games_with_discrepancies)/total_games*100:.1f}%)")
    print(f"Total discrepancies found:   {total_discrepancies:,}")
    print()

    if discrepancy_types:
        print("Discrepancies by field:")
        for field, count in sorted(discrepancy_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field:20s} {count:,}")
        print()

    if severity_counts:
        print("Discrepancies by severity:")
        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            if severity in severity_counts:
                count = severity_counts[severity]
                print(f"  {severity:10s} {count:,} ({count/total_discrepancies*100:.1f}%)")
        print()


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Detect data quality discrepancies between ESPN and hoopR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect all discrepancies
  python scripts/validation/detect_data_discrepancies.py

  # Test on 100 games
  python scripts/validation/detect_data_discrepancies.py --limit 100

  # Verbose output
  python scripts/validation/detect_data_discrepancies.py --verbose

  # Single game analysis
  python scripts/validation/detect_data_discrepancies.py --game-id 401584669

Result:
  - Discrepancies logged to data_quality_discrepancies table
  - Quality scores updated based on severity
  - Source coverage marked with discrepancy flags
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of games to analyze (for testing)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output for each game'
    )

    parser.add_argument(
        '--game-id',
        type=str,
        help='Analyze single game by ESPN game ID'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load game mapping
    print("Loading game ID mappings...")
    espn_to_hoopr, hoopr_to_espn = load_game_mapping()
    print(f"✓ Loaded {len(espn_to_hoopr):,} mappings")
    print()

    # Connect to databases
    print("Connecting to databases...")
    espn_conn = sqlite3.connect(ESPN_DB)
    hoopr_conn = sqlite3.connect(HOOPR_DB)
    unified_conn = sqlite3.connect(UNIFIED_DB)
    print("✓ Connected to ESPN, hoopR, and Unified databases")
    print()

    # Get dual-source games
    if args.game_id:
        # Single game mode
        games = [{
            'game_id': args.game_id,
            'game_date': None,
            'espn_event_count': None,
            'hoopr_event_count': None
        }]
    else:
        games = get_dual_source_games(unified_conn, limit=args.limit)

    # Process games
    process_games(
        espn_conn,
        hoopr_conn,
        unified_conn,
        espn_to_hoopr,
        games,
        verbose=args.verbose
    )

    # Close connections
    espn_conn.close()
    hoopr_conn.close()
    unified_conn.close()

    print("=" * 70)
    print("✓ Discrepancy detection complete!")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
