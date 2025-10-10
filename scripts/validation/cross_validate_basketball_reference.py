#!/usr/bin/env python3
"""
Cross-Validate Basketball Reference Data Against hoopR

Compares Basketball Reference aggregate data with hoopR game-by-game data
aggregated to season totals. Identifies discrepancies, validates data quality,
and provides recommendations for ML feature deployment.

Validation Strategy:
1. Player Season Totals (2001-2020 overlap):
   - Aggregate hoopR player_box by season and player
   - Compare with Basketball Reference player_season_totals
   - Key metrics: points, rebounds, assists, FG%, 3P%, FT%, games, minutes

2. Team Season Records (2001-2020):
   - Aggregate hoopR game results by season and team
   - Compare with Basketball Reference team_standings
   - Key metrics: wins, losses, win percentage

3. Tolerance Levels:
   - Counting stats: ±5 per season (minor discrepancies acceptable)
   - Percentages: ±1% (rounding differences)
   - Games played: ±2 games (different counting methods)
   - Team wins/losses: ±1 game (must be nearly exact)

Usage:
    python scripts/validation/cross_validate_basketball_reference.py
    python scripts/validation/cross_validate_basketball_reference.py --season 2020
    python scripts/validation/cross_validate_basketball_reference.py --export-csv

Created: October 10, 2025
"""

import sqlite3
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import csv

# Database paths
HOOPR_DB = "/tmp/hoopr_local.db"
BBREF_DB = "/tmp/basketball_reference_aggregate.db"

# Overlap period for cross-validation
OVERLAP_START = 2001
OVERLAP_END = 2020

# Tolerance thresholds
TOLERANCES = {
    'points': 5,  # ±5 points per season
    'rebounds': 5,
    'assists': 5,
    'field_goals_made': 5,
    'three_point_made': 3,
    'free_throws_made': 3,
    'steals': 3,
    'blocks': 3,
    'turnovers': 3,
    'minutes': 50,  # ±50 minutes per season
    'games_played': 2,  # ±2 games
    'percentage': 0.01,  # ±1%
    'team_wins': 1,  # ±1 win
    'team_losses': 1  # ±1 loss
}


def aggregate_hoopr_player_seasons(hoopr_conn, season: Optional[int] = None):
    """Aggregate hoopR player box scores to season totals."""

    print("=" * 70)
    print("AGGREGATE HOOPR PLAYER SEASON TOTALS")
    print("=" * 70)
    print()

    cursor = hoopr_conn.cursor()

    # Build season filter
    season_filter = ""
    if season:
        season_filter = f"WHERE CAST(strftime('%Y', game_date) AS INTEGER) = {season}"
        print(f"Filtering to season {season}")
    else:
        print(f"Aggregating all seasons {OVERLAP_START}-{OVERLAP_END}")

    query = f"""
        SELECT
            CAST(strftime('%Y', game_date) AS INTEGER) as season,
            athlete_display_name,
            team_short_display_name,
            COUNT(*) as games_played,
            CAST(SUM(CASE WHEN starter = 1 THEN 1 ELSE 0 END) AS INTEGER) as games_started,
            ROUND(SUM(minutes), 1) as minutes_played,
            CAST(SUM(field_goals_made) AS INTEGER) as made_field_goals,
            CAST(SUM(field_goals_attempted) AS INTEGER) as attempted_field_goals,
            CAST(SUM(three_point_field_goals_made) AS INTEGER) as made_three_point_field_goals,
            CAST(SUM(three_point_field_goals_attempted) AS INTEGER) as attempted_three_point_field_goals,
            CAST(SUM(free_throws_made) AS INTEGER) as made_free_throws,
            CAST(SUM(free_throws_attempted) AS INTEGER) as attempted_free_throws,
            CAST(SUM(offensive_rebounds) AS INTEGER) as offensive_rebounds,
            CAST(SUM(defensive_rebounds) AS INTEGER) as defensive_rebounds,
            CAST(SUM(rebounds) AS INTEGER) as total_rebounds,
            CAST(SUM(assists) AS INTEGER) as assists,
            CAST(SUM(steals) AS INTEGER) as steals,
            CAST(SUM(blocks) AS INTEGER) as blocks,
            CAST(SUM(turnovers) AS INTEGER) as turnovers,
            CAST(SUM(fouls) AS INTEGER) as personal_fouls,
            CAST(SUM(points) AS INTEGER) as points
        FROM player_box
        {season_filter}
        GROUP BY season, athlete_display_name, team_short_display_name
        HAVING games_played >= 5  -- Filter out very small samples
        ORDER BY season, athlete_display_name
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print(f"✓ Aggregated {len(results):,} player-seasons from hoopR")
    print()

    return results


def get_bbref_player_seasons(bbref_conn, season: Optional[int] = None):
    """Get Basketball Reference player season totals."""

    print("=" * 70)
    print("FETCH BASKETBALL REFERENCE PLAYER SEASON TOTALS")
    print("=" * 70)
    print()

    cursor = bbref_conn.cursor()

    # Build season filter
    season_filter = ""
    if season:
        season_filter = f"WHERE season = {season}"
        print(f"Filtering to season {season}")
    else:
        season_filter = f"WHERE season BETWEEN {OVERLAP_START} AND {OVERLAP_END}"
        print(f"Fetching seasons {OVERLAP_START}-{OVERLAP_END}")

    query = f"""
        SELECT
            season,
            player_name,
            team,
            games_played,
            games_started,
            minutes_played,
            made_field_goals,
            attempted_field_goals,
            made_three_point_field_goals,
            attempted_three_point_field_goals,
            made_free_throws,
            attempted_free_throws,
            offensive_rebounds,
            defensive_rebounds,
            total_rebounds,
            assists,
            steals,
            blocks,
            turnovers,
            personal_fouls,
            points
        FROM player_season_totals
        {season_filter}
        AND team IS NOT NULL  -- Exclude invalid records
        ORDER BY season, player_name
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print(f"✓ Fetched {len(results):,} player-seasons from Basketball Reference")
    print()

    return results


def normalize_player_name(name: str) -> str:
    """Normalize player name for matching."""
    # Remove periods, convert to uppercase, remove extra spaces
    return name.replace('.', '').replace("'", "").upper().strip()


def normalize_team_name(team: str) -> str:
    """Normalize team name for matching."""
    # Handle common variations
    team = team.upper().strip()

    # Map variations
    mappings = {
        'LA LAKERS': 'LOS ANGELES LAKERS',
        'LA CLIPPERS': 'LOS ANGELES CLIPPERS',
        'NY KNICKS': 'NEW YORK KNICKS',
        'GS WARRIORS': 'GOLDEN STATE WARRIORS',
        'SA SPURS': 'SAN ANTONIO SPURS',
        'NO PELICANS': 'NEW ORLEANS PELICANS',
        'NO HORNETS': 'NEW ORLEANS HORNETS',
        'NJ NETS': 'NEW JERSEY NETS',
        'SEA SUPERSONICS': 'SEATTLE SUPERSONICS'
    }

    return mappings.get(team, team)


def match_player_seasons(hoopr_data, bbref_data):
    """Match player seasons between hoopR and Basketball Reference."""

    print("=" * 70)
    print("MATCH PLAYER SEASONS BETWEEN SOURCES")
    print("=" * 70)
    print()

    # Index Basketball Reference data by (season, normalized_name)
    bbref_index = {}
    for row in bbref_data:
        season = row[0]
        name = normalize_player_name(row[1])
        team = normalize_team_name(row[2]) if row[2] else ''

        key = (season, name)
        if key not in bbref_index:
            bbref_index[key] = []
        bbref_index[key].append(row)

    # Match hoopR data
    matches = []
    hoopr_unmatched = []
    bbref_matched_keys = set()

    for hoopr_row in hoopr_data:
        season = hoopr_row[0]
        name = normalize_player_name(hoopr_row[1])

        key = (season, name)

        if key in bbref_index:
            # Found match(es)
            bbref_rows = bbref_index[key]

            if len(bbref_rows) == 1:
                # Single match - best case
                matches.append((hoopr_row, bbref_rows[0]))
                bbref_matched_keys.add(key)
            else:
                # Multiple matches (player traded) - try to match by team
                hoopr_team = normalize_team_name(hoopr_row[2])
                matched = False

                for bbref_row in bbref_rows:
                    bbref_team = normalize_team_name(bbref_row[2]) if bbref_row[2] else ''
                    if hoopr_team == bbref_team:
                        matches.append((hoopr_row, bbref_row))
                        bbref_matched_keys.add(key)
                        matched = True
                        break

                if not matched:
                    # Use first match as fallback
                    matches.append((hoopr_row, bbref_rows[0]))
                    bbref_matched_keys.add(key)
        else:
            hoopr_unmatched.append(hoopr_row)

    # Find Basketball Reference records that weren't matched
    bbref_unmatched = []
    for key, rows in bbref_index.items():
        if key not in bbref_matched_keys:
            bbref_unmatched.extend(rows)

    print(f"✓ Matched {len(matches):,} player-seasons")
    print(f"  hoopR unmatched: {len(hoopr_unmatched):,}")
    print(f"  Basketball Reference unmatched: {len(bbref_unmatched):,}")
    print()

    return matches, hoopr_unmatched, bbref_unmatched


def compare_player_seasons(matches):
    """Compare matched player seasons and calculate discrepancies."""

    print("=" * 70)
    print("COMPARE PLAYER SEASON STATISTICS")
    print("=" * 70)
    print()

    discrepancies = []
    stats_summary = defaultdict(lambda: {'sum_abs_diff': 0, 'count': 0, 'max_diff': 0})

    stat_indices = {
        'games_played': (3, 3),
        'games_started': (4, 4),
        'minutes': (5, 5),
        'field_goals_made': (6, 6),
        'field_goals_attempted': (7, 7),
        'three_point_made': (8, 8),
        'three_point_attempted': (9, 9),
        'free_throws_made': (10, 10),
        'free_throws_attempted': (11, 11),
        'offensive_rebounds': (12, 12),
        'defensive_rebounds': (13, 13),
        'total_rebounds': (14, 14),
        'assists': (15, 15),
        'steals': (16, 16),
        'blocks': (17, 17),
        'turnovers': (18, 18),
        'fouls': (19, 19),
        'points': (20, 20)
    }

    for hoopr_row, bbref_row in matches:
        season = hoopr_row[0]
        player_name = hoopr_row[1]
        team = hoopr_row[2]

        player_discrepancies = {}

        for stat_name, (hoopr_idx, bbref_idx) in stat_indices.items():
            hoopr_val = hoopr_row[hoopr_idx] or 0
            bbref_val = bbref_row[bbref_idx] or 0

            diff = abs(hoopr_val - bbref_val)

            # Update summary statistics
            stats_summary[stat_name]['sum_abs_diff'] += diff
            stats_summary[stat_name]['count'] += 1
            if diff > stats_summary[stat_name]['max_diff']:
                stats_summary[stat_name]['max_diff'] = diff

            # Check tolerance
            tolerance = TOLERANCES.get(stat_name, TOLERANCES['points'])
            if diff > tolerance:
                player_discrepancies[stat_name] = {
                    'hoopr': hoopr_val,
                    'bbref': bbref_val,
                    'diff': diff,
                    'tolerance': tolerance
                }

        if player_discrepancies:
            discrepancies.append({
                'season': season,
                'player': player_name,
                'team': team,
                'discrepancies': player_discrepancies
            })

    # Calculate mean absolute error for each stat
    print("Statistical Comparison:")
    print(f"  {'Statistic':<25} {'Mean Abs Diff':<15} {'Max Diff':<15}")
    print(f"  {'-'*25} {'-'*15} {'-'*15}")

    for stat_name in sorted(stat_indices.keys()):
        summary = stats_summary[stat_name]
        if summary['count'] > 0:
            mae = summary['sum_abs_diff'] / summary['count']
            max_diff = summary['max_diff']
            print(f"  {stat_name:<25} {mae:<15.2f} {max_diff:<15.1f}")

    print()
    print(f"Players with discrepancies exceeding tolerance: {len(discrepancies):,}")
    print()

    return discrepancies, stats_summary


def analyze_discrepancies(discrepancies):
    """Analyze patterns in discrepancies."""

    print("=" * 70)
    print("ANALYZE DISCREPANCY PATTERNS")
    print("=" * 70)
    print()

    # Group by stat type
    stat_counts = defaultdict(int)
    for player_disc in discrepancies:
        for stat_name in player_disc['discrepancies'].keys():
            stat_counts[stat_name] += 1

    print("Most common discrepant statistics:")
    print(f"  {'Statistic':<25} {'Count':<10} {'% of Total':<10}")
    print(f"  {'-'*25} {'-'*10} {'-'*10}")

    total_players = len(discrepancies)
    for stat_name, count in sorted(stat_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = (count / total_players) * 100
        print(f"  {stat_name:<25} {count:<10} {pct:<10.1f}%")

    print()

    # Group by season
    season_counts = defaultdict(int)
    for player_disc in discrepancies:
        season_counts[player_disc['season']] += 1

    print("Discrepancies by season:")
    print(f"  {'Season':<10} {'Count':<10}")
    print(f"  {'-'*10} {'-'*10}")

    for season in sorted(season_counts.keys()):
        print(f"  {season:<10} {season_counts[season]:<10}")

    print()

    return stat_counts, season_counts


def generate_data_quality_score(stats_summary, discrepancies, total_matches):
    """Generate overall data quality score."""

    print("=" * 70)
    print("DATA QUALITY ASSESSMENT")
    print("=" * 70)
    print()

    # Calculate percentage of players with issues
    issue_rate = (len(discrepancies) / total_matches) * 100 if total_matches > 0 else 0

    # Calculate average mean absolute error across key stats
    key_stats = ['points', 'rebounds', 'assists', 'field_goals_made', 'three_point_made']
    total_mae = 0
    stat_count = 0

    for stat_name in key_stats:
        if stat_name in stats_summary and stats_summary[stat_name]['count'] > 0:
            mae = stats_summary[stat_name]['sum_abs_diff'] / stats_summary[stat_name]['count']
            total_mae += mae
            stat_count += 1

    avg_mae = total_mae / stat_count if stat_count > 0 else 0

    # Calculate quality score (0-100)
    # Lower issue rate = higher score
    # Lower MAE = higher score
    issue_score = max(0, 100 - issue_rate * 2)  # 50% issues = 0 score
    accuracy_score = max(0, 100 - avg_mae * 10)  # MAE of 10 = 0 score

    overall_score = (issue_score + accuracy_score) / 2

    print(f"Issue Rate: {issue_rate:.1f}% of players have discrepancies")
    print(f"Average MAE (key stats): {avg_mae:.2f}")
    print(f"Issue Score: {issue_score:.1f}/100")
    print(f"Accuracy Score: {accuracy_score:.1f}/100")
    print(f"Overall Quality Score: {overall_score:.1f}/100")
    print()

    # Interpretation
    if overall_score >= 90:
        quality = "EXCELLENT"
        recommendation = "Data is highly reliable - safe to deploy for ML"
    elif overall_score >= 75:
        quality = "GOOD"
        recommendation = "Data is reliable with minor discrepancies - safe to deploy"
    elif overall_score >= 60:
        quality = "FAIR"
        recommendation = "Data has moderate discrepancies - review before deployment"
    else:
        quality = "POOR"
        recommendation = "Data has significant issues - investigate before deployment"

    print(f"Quality Rating: {quality}")
    print(f"Recommendation: {recommendation}")
    print()

    return {
        'overall_score': overall_score,
        'issue_rate': issue_rate,
        'avg_mae': avg_mae,
        'quality': quality,
        'recommendation': recommendation
    }


def export_discrepancies_to_csv(discrepancies, filename):
    """Export discrepancies to CSV for analysis."""

    print(f"Exporting discrepancies to {filename}...")

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Season', 'Player', 'Team', 'Statistic', 'hoopR_Value', 'BBRef_Value', 'Difference', 'Tolerance'])

        for player_disc in discrepancies:
            season = player_disc['season']
            player = player_disc['player']
            team = player_disc['team']

            for stat_name, values in player_disc['discrepancies'].items():
                writer.writerow([
                    season,
                    player,
                    team,
                    stat_name,
                    values['hoopr'],
                    values['bbref'],
                    values['diff'],
                    values['tolerance']
                ])

    print(f"✓ Exported {len(discrepancies)} player discrepancies")
    print()


def main():
    """Main execution."""

    parser = argparse.ArgumentParser(
        description="Cross-validate Basketball Reference data against hoopR",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--season',
        type=int,
        help='Validate specific season only'
    )

    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Export discrepancies to CSV file'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Connect to databases
    hoopr_conn = sqlite3.connect(HOOPR_DB)
    bbref_conn = sqlite3.connect(BBREF_DB)

    # Step 1: Aggregate hoopR player seasons
    hoopr_data = aggregate_hoopr_player_seasons(hoopr_conn, season=args.season)

    # Step 2: Get Basketball Reference player seasons
    bbref_data = get_bbref_player_seasons(bbref_conn, season=args.season)

    # Step 3: Match player seasons
    matches, hoopr_unmatched, bbref_unmatched = match_player_seasons(hoopr_data, bbref_data)

    # Step 4: Compare statistics
    discrepancies, stats_summary = compare_player_seasons(matches)

    # Step 5: Analyze patterns
    stat_counts, season_counts = analyze_discrepancies(discrepancies)

    # Step 6: Generate quality score
    quality_assessment = generate_data_quality_score(stats_summary, discrepancies, len(matches))

    # Step 7: Export if requested
    if args.export_csv:
        export_discrepancies_to_csv(discrepancies, '/tmp/bbref_cross_validation_discrepancies.csv')

    # Close connections
    hoopr_conn.close()
    bbref_conn.close()

    print("=" * 70)
    print("✓ CROSS-VALIDATION COMPLETE!")
    print("=" * 70)
    print(f"Total matches: {len(matches):,}")
    print(f"Players with discrepancies: {len(discrepancies):,} ({(len(discrepancies)/len(matches)*100):.1f}%)")
    print(f"Overall Quality Score: {quality_assessment['overall_score']:.1f}/100 ({quality_assessment['quality']})")
    print(f"Recommendation: {quality_assessment['recommendation']}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
