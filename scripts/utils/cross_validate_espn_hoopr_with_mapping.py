#!/usr/bin/env python3
"""
ESPN vs hoopR Cross-Validation with Game ID Mapping

Uses the extracted ESPN-to-hoopR game ID mapping to properly identify:
1. Games in ESPN but missing from hoopR
2. Games in hoopR but missing from ESPN
3. Games in both with event count discrepancies

This enables targeted gap-filling strategies.

Usage:
    python scripts/utils/cross_validate_espn_hoopr_with_mapping.py
    python scripts/utils/cross_validate_espn_hoopr_with_mapping.py --export-gaps
    python scripts/utils/cross_validate_espn_hoopr_with_mapping.py --detailed

Output:
    - Console summary statistics
    - /tmp/missing_from_hoopr.csv - Games to scrape for hoopR
    - /tmp/missing_from_espn.csv - Games to scrape for ESPN
    - /tmp/event_discrepancies.csv - Games with different event counts
"""

import sqlite3
import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import argparse

# Database paths
ESPN_DB = "/tmp/espn_local.db"
HOOPR_DB = "/tmp/hoopr_local.db"
MAPPING_FILE = Path(__file__).parent.parent / "mapping" / "espn_hoopr_game_mapping.json"

# Output paths
MISSING_FROM_HOOPR = "/tmp/missing_from_hoopr.csv"
MISSING_FROM_ESPN = "/tmp/missing_from_espn.csv"
EVENT_DISCREPANCIES = "/tmp/event_discrepancies.csv"


def load_mapping():
    """Load ESPN-to-hoopR game ID mapping."""

    print("=" * 70)
    print("CROSS-VALIDATION WITH GAME ID MAPPING")
    print("=" * 70)
    print()

    if not MAPPING_FILE.exists():
        raise FileNotFoundError(
            f"Mapping file not found: {MAPPING_FILE}\n"
            f"Run: python scripts/mapping/extract_espn_hoopr_game_mapping.py --output-format json"
        )

    print(f"📂 Loading mapping: {MAPPING_FILE}")
    with open(MAPPING_FILE) as f:
        data = json.load(f)

    espn_to_hoopr = data['espn_to_hoopr']
    hoopr_to_espn = data['hoopr_to_espn']

    print(f"✓ Loaded {data['metadata']['total_mappings']:,} game ID mappings")
    print()

    return espn_to_hoopr, hoopr_to_espn


def get_espn_games():
    """Get all ESPN games with play-by-play."""

    print("📊 Loading ESPN games...")
    conn = sqlite3.connect(ESPN_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            game_id,
            game_date,
            home_team,
            away_team,
            pbp_event_count
        FROM games
        WHERE has_pbp = 1
          AND game_date >= '2001-10-30'  -- hoopR start date
        ORDER BY game_date;
    """)

    games = {}
    for row in cursor.fetchall():
        game_id, game_date, home_team, away_team, event_count = row
        games[game_id] = {
            'game_id': game_id,
            'game_date': game_date,
            'home_team': home_team or 'Unknown',
            'away_team': away_team or 'Unknown',
            'event_count': event_count or 0
        }

    cursor.close()
    conn.close()

    print(f"✓ Loaded {len(games):,} ESPN games with PBP")
    return games


def get_hoopr_games():
    """Get all hoopR games with play-by-play."""

    print("📊 Loading hoopR games...")
    conn = sqlite3.connect(HOOPR_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.game_id,
            s.game_date,
            s.home_display_name,
            s.away_display_name,
            COUNT(pbp.id) as event_count
        FROM schedule s
        LEFT JOIN play_by_play pbp ON s.game_id = pbp.game_id
        GROUP BY s.game_id, s.game_date, s.home_display_name, s.away_display_name
        HAVING event_count > 0
        ORDER BY s.game_date;
    """)

    games = {}
    for row in cursor.fetchall():
        game_id, game_date, home_team, away_team, event_count = row
        games[str(game_id)] = {
            'game_id': str(game_id),
            'game_date': game_date,
            'home_team': home_team or 'Unknown',
            'away_team': away_team or 'Unknown',
            'event_count': event_count or 0
        }

    cursor.close()
    conn.close()

    print(f"✓ Loaded {len(games):,} hoopR games with PBP")
    print()
    return games


def identify_gaps(espn_games, hoopr_games, espn_to_hoopr, hoopr_to_espn):
    """Identify missing games in each source."""

    print("=" * 70)
    print("GAP ANALYSIS")
    print("=" * 70)
    print()

    # Games in ESPN but missing from hoopR
    missing_from_hoopr = []
    for espn_id, espn_game in espn_games.items():
        hoopr_id = espn_to_hoopr.get(espn_id)

        if not hoopr_id:
            # No mapping exists - hoopR doesn't have this game
            missing_from_hoopr.append({
                'espn_game_id': espn_id,
                'game_date': espn_game['game_date'],
                'home_team': espn_game['home_team'],
                'away_team': espn_game['away_team'],
                'espn_events': espn_game['event_count'],
                'reason': 'No hoopR mapping'
            })
        elif hoopr_id not in hoopr_games:
            # Mapping exists but no PBP in hoopR
            missing_from_hoopr.append({
                'espn_game_id': espn_id,
                'hoopr_game_id': hoopr_id,
                'game_date': espn_game['game_date'],
                'home_team': espn_game['home_team'],
                'away_team': espn_game['away_team'],
                'espn_events': espn_game['event_count'],
                'reason': 'hoopR has no PBP'
            })

    # Games in hoopR but missing from ESPN
    missing_from_espn = []
    for hoopr_id, hoopr_game in hoopr_games.items():
        espn_id = hoopr_to_espn.get(hoopr_id)

        if not espn_id:
            # No mapping exists - ESPN doesn't have this game
            missing_from_espn.append({
                'hoopr_game_id': hoopr_id,
                'game_date': hoopr_game['game_date'],
                'home_team': hoopr_game['home_team'],
                'away_team': hoopr_game['away_team'],
                'hoopr_events': hoopr_game['event_count'],
                'reason': 'No ESPN mapping'
            })
        elif espn_id not in espn_games:
            # Mapping exists but no PBP in ESPN
            missing_from_espn.append({
                'hoopr_game_id': hoopr_id,
                'espn_game_id': espn_id,
                'game_date': hoopr_game['game_date'],
                'home_team': hoopr_game['home_team'],
                'away_team': hoopr_game['away_team'],
                'hoopr_events': hoopr_game['event_count'],
                'reason': 'ESPN has no PBP'
            })

    print(f"Missing from hoopR: {len(missing_from_hoopr):,} games")
    print(f"Missing from ESPN:  {len(missing_from_espn):,} games")
    print()

    return missing_from_hoopr, missing_from_espn


def identify_discrepancies(espn_games, hoopr_games, espn_to_hoopr, threshold=50):
    """Identify games with event count discrepancies."""

    print("=" * 70)
    print("EVENT COUNT DISCREPANCY ANALYSIS")
    print("=" * 70)
    print()

    discrepancies = []

    for espn_id, espn_game in espn_games.items():
        hoopr_id = espn_to_hoopr.get(espn_id)

        if hoopr_id and hoopr_id in hoopr_games:
            hoopr_game = hoopr_games[hoopr_id]

            espn_count = espn_game['event_count']
            hoopr_count = hoopr_game['event_count']
            diff = abs(espn_count - hoopr_count)

            if diff > threshold:
                discrepancies.append({
                    'espn_game_id': espn_id,
                    'hoopr_game_id': hoopr_id,
                    'game_date': espn_game['game_date'],
                    'matchup': f"{espn_game['away_team']} @ {espn_game['home_team']}",
                    'espn_events': espn_count,
                    'hoopr_events': hoopr_count,
                    'difference': diff,
                    'pct_diff': (diff / max(espn_count, hoopr_count) * 100) if max(espn_count, hoopr_count) > 0 else 0
                })

    # Sort by difference descending
    discrepancies.sort(key=lambda x: x['difference'], reverse=True)

    print(f"Games with event count differences >{threshold}: {len(discrepancies):,}")
    print()

    # Show top 10
    if discrepancies:
        print("Top 10 discrepancies:")
        print(f"{'Date':<12} {'ESPN Events':<12} {'hoopR Events':<13} {'Diff':<8} {'% Diff':<8} {'Matchup':<40}")
        print("-" * 95)
        for disc in discrepancies[:10]:
            print(f"{disc['game_date']:<12} {disc['espn_events']:<12,} {disc['hoopr_events']:<13,} "
                  f"{disc['difference']:<8,} {disc['pct_diff']:<7.1f}% {disc['matchup']:<40}")
        print()

    return discrepancies


def export_gaps(missing_from_hoopr, missing_from_espn, discrepancies):
    """Export gap analysis to CSV files."""

    print("=" * 70)
    print("EXPORTING GAP REPORTS")
    print("=" * 70)
    print()

    # Missing from hoopR
    print(f"💾 Exporting: {MISSING_FROM_HOOPR}")
    with open(MISSING_FROM_HOOPR, 'w', newline='') as f:
        if missing_from_hoopr:
            fieldnames = list(missing_from_hoopr[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(missing_from_hoopr)
    print(f"✓ {len(missing_from_hoopr):,} games exported")

    # Missing from ESPN
    print(f"💾 Exporting: {MISSING_FROM_ESPN}")
    with open(MISSING_FROM_ESPN, 'w', newline='') as f:
        if missing_from_espn:
            fieldnames = list(missing_from_espn[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(missing_from_espn)
    print(f"✓ {len(missing_from_espn):,} games exported")

    # Event discrepancies
    print(f"💾 Exporting: {EVENT_DISCREPANCIES}")
    with open(EVENT_DISCREPANCIES, 'w', newline='') as f:
        if discrepancies:
            fieldnames = list(discrepancies[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(discrepancies)
    print(f"✓ {len(discrepancies):,} discrepancies exported")
    print()


def print_summary(espn_games, hoopr_games, missing_from_hoopr, missing_from_espn, discrepancies):
    """Print summary statistics."""

    print("=" * 70)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 70)
    print()

    total_unique_games = len(set(espn_games.keys()) | set(hoopr_games.keys()))
    games_in_both = len(set(espn_games.keys()) & set(hoopr_games.keys()))

    print(f"Total unique games:      {total_unique_games:,}")
    print(f"Games in both sources:   {games_in_both:,}")
    print(f"Games only in ESPN:      {len(missing_from_hoopr):,}")
    print(f"Games only in hoopR:     {len(missing_from_espn):,}")
    print(f"Event count mismatches:  {len(discrepancies):,}")
    print()

    # Coverage percentages
    espn_coverage = (len(espn_games) / total_unique_games * 100) if total_unique_games > 0 else 0
    hoopr_coverage = (len(hoopr_games) / total_unique_games * 100) if total_unique_games > 0 else 0

    print(f"ESPN coverage:   {espn_coverage:.1f}%")
    print(f"hoopR coverage:  {hoopr_coverage:.1f}%")
    print()

    print("=" * 70)
    print("RECOMMENDED ACTIONS")
    print("=" * 70)
    print()

    if missing_from_hoopr:
        print(f"1. Fill {len(missing_from_hoopr):,} gaps in hoopR:")
        print(f"   - Target ESPN games: {MISSING_FROM_HOOPR}")
        print(f"   - Use: python scripts/etl/fill_hoopr_gaps_from_espn.py")
        print()

    if missing_from_espn:
        print(f"2. Fill {len(missing_from_espn):,} gaps in ESPN:")
        print(f"   - Target hoopR games: {MISSING_FROM_ESPN}")
        print(f"   - Use: python scripts/etl/fill_espn_gaps_from_hoopr.py")
        print()

    if discrepancies:
        print(f"3. Investigate {len(discrepancies):,} event count discrepancies:")
        print(f"   - Review: {EVENT_DISCREPANCIES}")
        print(f"   - Determine which source is more reliable per game")
        print()

    print("=" * 70)


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Cross-validate ESPN and hoopR using game ID mapping",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--export-gaps',
        action='store_true',
        help='Export gap analysis to CSV files'
    )

    parser.add_argument(
        '--discrepancy-threshold',
        type=int,
        default=50,
        help='Event count difference threshold for discrepancies (default: 50)'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load mapping
    espn_to_hoopr, hoopr_to_espn = load_mapping()

    # Load games
    espn_games = get_espn_games()
    hoopr_games = get_hoopr_games()

    # Identify gaps
    missing_from_hoopr, missing_from_espn = identify_gaps(
        espn_games, hoopr_games, espn_to_hoopr, hoopr_to_espn
    )

    # Identify discrepancies
    discrepancies = identify_discrepancies(
        espn_games, hoopr_games, espn_to_hoopr,
        threshold=args.discrepancy_threshold
    )

    # Export if requested
    if args.export_gaps:
        export_gaps(missing_from_hoopr, missing_from_espn, discrepancies)

    # Print summary
    print_summary(espn_games, hoopr_games, missing_from_hoopr,
                  missing_from_espn, discrepancies)

    print(f"✓ Cross-validation complete!")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
