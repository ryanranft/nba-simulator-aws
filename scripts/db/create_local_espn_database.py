"""
Create Local ESPN SQLite Database

Parses 44,826 ESPN play-by-play JSON files from data/nba_pbp/ and creates
a local SQLite database for fast querying without RDS costs.

Tables Created:
1. games - Game metadata (date, teams, scores, status)
2. pbp_events - Play-by-play events (text, period, clock, scores)
3. data_coverage - Coverage analysis by year

Usage:
    python scripts/db/create_local_espn_database.py
    python scripts/db/create_local_espn_database.py --output /custom/path/espn_local.db
    python scripts/db/create_local_espn_database.py --sample 1000  # Test with first 1000 files

Duration: 2-4 hours for 44,826 files
Output: SQLite database (~5-10GB)
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import argparse
import sys

# Paths
PROJECT_DIR = Path("/Users/ryanranft/nba-simulator-aws")
ESPN_DATA_DIR = PROJECT_DIR / "data" / "nba_pbp"
DEFAULT_OUTPUT = Path("/tmp/espn_local.db")


def create_schema(conn):
    """Create database schema with indexes"""
    cursor = conn.cursor()

    print("Creating database schema...")

    # Games table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            game_date TEXT NOT NULL,
            season INTEGER,
            game_type TEXT,
            status TEXT,
            home_team TEXT,
            away_team TEXT,
            home_score INTEGER,
            away_score INTEGER,
            quarters_played INTEGER,
            has_pbp BOOLEAN DEFAULT 0,
            pbp_event_count INTEGER DEFAULT 0,
            json_file_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Play-by-play events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pbp_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            period INTEGER,
            clock_display TEXT,
            event_text TEXT,
            home_score INTEGER,
            away_score INTEGER,
            team_possession TEXT,
            event_sequence INTEGER,
            FOREIGN KEY (game_id) REFERENCES games(game_id)
        )
    """)

    # Data coverage summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_coverage (
            year INTEGER PRIMARY KEY,
            games_total INTEGER,
            games_with_pbp INTEGER,
            pbp_coverage_pct REAL,
            avg_events_per_game REAL,
            earliest_game_date TEXT,
            latest_game_date TEXT
        )
    """)

    # Create indexes
    print("Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_season ON games(season)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pbp_game ON pbp_events(game_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pbp_period ON pbp_events(game_id, period)")

    conn.commit()
    print("✓ Schema created")


def extract_game_info(filepath: Path) -> dict:
    """
    Extract game information from ESPN JSON file

    Returns:
        dict with game metadata and play-by-play events
    """
    try:
        with open(filepath) as f:
            data = json.load(f)

        # Navigate to game package
        game = data.get('page', {}).get('content', {}).get('gamepackage', {})
        if not game:
            return None

        gmStrp = game.get('gmStrp', {})
        pbp = game.get('pbp', {})

        # Extract game metadata
        game_id = gmStrp.get('gid')
        if not game_id:
            return None

        date_str = gmStrp.get('dt')
        status = gmStrp.get('status', {}).get('desc', 'Unknown')

        # Extract teams and scores
        teams = gmStrp.get('tms', [])
        home_team = None
        away_team = None
        home_score = 0
        away_score = 0

        for team in teams:
            team_name = team.get('displayName', '')
            score = team.get('score', 0)
            is_home = team.get('homeAway') == 'home'

            if is_home:
                home_team = team_name
                home_score = score
            else:
                away_team = team_name
                away_score = score

        # Extract play-by-play data
        play_grps = pbp.get('playGrps', [])
        events = []

        for period_idx, grp in enumerate(play_grps):
            if not isinstance(grp, list):
                continue

            for seq, play in enumerate(grp):
                if not isinstance(play, dict):
                    continue

                events.append({
                    'period': period_idx + 1,
                    'sequence': seq,
                    'clock': play.get('clock', {}).get('displayValue'),
                    'text': play.get('text', ''),
                    'away_score': play.get('awayScore', 0),
                    'home_score': play.get('homeScore', 0),
                    'team': play.get('homeAway', '')
                })

        # Parse date to get season
        season = None
        game_date = None
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                game_date = dt.strftime('%Y-%m-%d')
                # NBA season spans calendar years (Oct-Jun)
                year = dt.year
                season = year if dt.month >= 10 else year - 1
            except:
                pass

        return {
            'game_id': str(game_id),
            'game_date': game_date,
            'season': season,
            'status': status,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': int(home_score) if home_score else 0,
            'away_score': int(away_score) if away_score else 0,
            'quarters_played': len(play_grps),
            'has_pbp': len(events) > 0,
            'pbp_event_count': len(events),
            'events': events,
            'json_file_path': str(filepath)
        }

    except Exception as e:
        # Return minimal info on error
        return None


def insert_game(cursor, game_info: dict):
    """Insert game and events into database"""
    # Insert game
    cursor.execute("""
        INSERT OR REPLACE INTO games (
            game_id, game_date, season, status, home_team, away_team,
            home_score, away_score, quarters_played, has_pbp,
            pbp_event_count, json_file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        game_info['game_id'],
        game_info['game_date'],
        game_info['season'],
        game_info['status'],
        game_info['home_team'],
        game_info['away_team'],
        game_info['home_score'],
        game_info['away_score'],
        game_info['quarters_played'],
        game_info['has_pbp'],
        game_info['pbp_event_count'],
        game_info['json_file_path']
    ))

    # Insert events
    if game_info['events']:
        for event in game_info['events']:
            cursor.execute("""
                INSERT INTO pbp_events (
                    game_id, period, clock_display, event_text,
                    home_score, away_score, team_possession, event_sequence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_info['game_id'],
                event['period'],
                event['clock'],
                event['text'],
                event['home_score'],
                event['away_score'],
                event['team'],
                event['sequence']
            ))


def calculate_coverage(conn):
    """Calculate coverage statistics by year"""
    cursor = conn.cursor()

    print("\nCalculating coverage statistics...")

    cursor.execute("""
        INSERT OR REPLACE INTO data_coverage (
            year, games_total, games_with_pbp, pbp_coverage_pct,
            avg_events_per_game, earliest_game_date, latest_game_date
        )
        SELECT
            season as year,
            COUNT(*) as games_total,
            SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) as games_with_pbp,
            ROUND(100.0 * SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as pbp_coverage_pct,
            ROUND(AVG(pbp_event_count), 0) as avg_events_per_game,
            MIN(game_date) as earliest_game_date,
            MAX(game_date) as latest_game_date
        FROM games
        WHERE season IS NOT NULL
        GROUP BY season
        ORDER BY season
    """)

    conn.commit()
    print("✓ Coverage statistics calculated")


def print_summary(conn):
    """Print database summary"""
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("ESPN LOCAL DATABASE SUMMARY")
    print("="*80)

    # Total games
    cursor.execute("SELECT COUNT(*) FROM games")
    total_games = cursor.fetchone()[0]
    print(f"\nTotal games: {total_games:,}")

    # Games with PBP
    cursor.execute("SELECT COUNT(*) FROM games WHERE has_pbp = 1")
    games_with_pbp = cursor.fetchone()[0]
    pbp_pct = (games_with_pbp / total_games * 100) if total_games > 0 else 0
    print(f"Games with play-by-play: {games_with_pbp:,} ({pbp_pct:.1f}%)")

    # Total events
    cursor.execute("SELECT COUNT(*) FROM pbp_events")
    total_events = cursor.fetchone()[0]
    avg_events = (total_events / games_with_pbp) if games_with_pbp > 0 else 0
    print(f"Total play-by-play events: {total_events:,}")
    print(f"Average events per game: {avg_events:.0f}")

    # Date range
    cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM games WHERE game_date IS NOT NULL")
    min_date, max_date = cursor.fetchone()
    print(f"Date range: {min_date} to {max_date}")

    # Coverage by era
    print("\nCoverage by Era:")
    print(f"{'Era':<20} {'Games':<10} {'With PBP':<12} {'Avg Events':<12} {'Coverage %'}")
    print("-"*70)

    cursor.execute("""
        SELECT
            CASE
                WHEN season < 2002 THEN '1993-2001 (Early)'
                WHEN season BETWEEN 2002 AND 2010 THEN '2002-2010 (Digital)'
                WHEN season >= 2011 THEN '2011-2025 (Modern)'
            END as era,
            COUNT(*) as games,
            SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) as with_pbp,
            ROUND(AVG(pbp_event_count), 0) as avg_events,
            ROUND(100.0 * SUM(CASE WHEN has_pbp = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as coverage
        FROM games
        WHERE season IS NOT NULL
        GROUP BY era
        ORDER BY MIN(season)
    """)

    for row in cursor.fetchall():
        era, games, with_pbp, avg_events, coverage = row
        print(f"{era:<20} {games:<10,} {with_pbp:<12,} {avg_events:<12.0f} {coverage:.1f}%")

    # Top 10 years by coverage
    print("\nTop 10 Years by Play-by-Play Coverage:")
    print(f"{'Year':<8} {'Games':<10} {'With PBP':<12} {'Coverage %':<12} {'Avg Events'}")
    print("-"*60)

    cursor.execute("""
        SELECT year, games_total, games_with_pbp, pbp_coverage_pct, avg_events_per_game
        FROM data_coverage
        ORDER BY pbp_coverage_pct DESC, avg_events_per_game DESC
        LIMIT 10
    """)

    for row in cursor.fetchall():
        year, total, with_pbp, pct, avg_events = row
        print(f"{year:<8} {total:<10,} {with_pbp:<12,} {pct:<12.1f} {avg_events:.0f}")

    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="Create local ESPN SQLite database")
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT), help='Output database path')
    parser.add_argument('--sample', type=int, help='Process only first N files (for testing)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    output_path = Path(args.output)

    print("="*80)
    print("CREATE LOCAL ESPN DATABASE")
    print("="*80)
    print(f"Input directory: {ESPN_DATA_DIR}")
    print(f"Output database: {output_path}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Validate input directory
    if not ESPN_DATA_DIR.exists():
        print(f"ERROR: ESPN data directory not found: {ESPN_DATA_DIR}")
        sys.exit(1)

    # Get all JSON files
    json_files = sorted(ESPN_DATA_DIR.glob("*.json"))
    total_files = len(json_files)

    if total_files == 0:
        print(f"ERROR: No JSON files found in {ESPN_DATA_DIR}")
        sys.exit(1)

    print(f"Found {total_files:,} JSON files")

    # Apply sample limit if specified
    if args.sample:
        json_files = json_files[:args.sample]
        print(f"TEST MODE: Processing first {len(json_files):,} files")

    print()

    # Remove existing database
    if output_path.exists():
        print(f"Removing existing database: {output_path}")
        output_path.unlink()

    # Create database connection
    conn = sqlite3.connect(str(output_path))

    # Create schema
    create_schema(conn)

    # Process files
    print(f"\nProcessing {len(json_files):,} files...")
    print()

    cursor = conn.cursor()
    processed = 0
    games_inserted = 0
    events_inserted = 0
    errors = 0

    for i, filepath in enumerate(json_files, 1):
        if args.verbose or i % 1000 == 0:
            pct = (i / len(json_files)) * 100
            print(f"Progress: {i:,}/{len(json_files):,} ({pct:.1f}%) - {games_inserted:,} games, {events_inserted:,} events")

        try:
            game_info = extract_game_info(filepath)

            if game_info:
                insert_game(cursor, game_info)
                games_inserted += 1
                events_inserted += game_info['pbp_event_count']
                processed += 1

            # Commit every 1000 files
            if i % 1000 == 0:
                conn.commit()

        except Exception as e:
            errors += 1
            if args.verbose:
                print(f"Error processing {filepath.name}: {e}")

    # Final commit
    conn.commit()

    print()
    print(f"✓ Processed {processed:,} games successfully")
    if errors > 0:
        print(f"⚠ Errors: {errors:,} files could not be processed")

    # Calculate coverage statistics
    calculate_coverage(conn)

    # Print summary
    print_summary(conn)

    # Close connection
    conn.close()

    # Show file size
    db_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\nDatabase size: {db_size_mb:.1f} MB")
    print(f"Saved to: {output_path}")
    print()
    print("="*80)
    print("COMPLETE")
    print("="*80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps:")
    print("1. Query database: sqlite3 /tmp/espn_local.db")
    print("2. Compare with RDS: python scripts/analysis/compare_espn_local_vs_rds.py")
    print("3. Generate reports: python scripts/analysis/generate_espn_coverage_report.py")
    print("="*80)


if __name__ == '__main__':
    main()
