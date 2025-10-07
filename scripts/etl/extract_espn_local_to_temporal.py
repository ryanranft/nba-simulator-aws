"""
Extract Local ESPN Data to Temporal Format

Processes existing ESPN JSON files from /Users/ryanranft/0espn/data/nba/
and extracts temporal data for loading into RDS.

Extracts:
1. Play-by-play events with timestamps (wall clock + game clock)
2. Player rosters from box scores
3. Shot locations and advanced event data
4. All event metadata (scores, player involvement, etc.)

Usage:
    python scripts/etl/extract_espn_local_to_temporal.py --limit 1000  # Test with 1000 games
    python scripts/etl/extract_espn_local_to_temporal.py  # Process all games

Output: CSV files ready for load_kaggle_to_rds.py
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional
import argparse

# ESPN data directories
ESPN_DATA_DIR = Path("/Users/ryanranft/0espn/data/nba")
PBP_DIR = ESPN_DATA_DIR / "nba_pbp"
BOX_SCORE_DIR = ESPN_DATA_DIR / "nba_box_score"
SCHEDULE_DIR = ESPN_DATA_DIR / "nba_schedule_json"

# Output directory
OUTPUT_DIR = Path("/tmp/temporal_data_espn")

# Cache for game dates
GAME_DATE_INDEX_FILE = Path("/tmp/espn_game_dates_index.json")


def build_game_date_index() -> Dict[str, datetime]:
    """
    Pre-build game_id → date mapping from play-by-play files.

    Extracts dates directly from pbp files since schedule files don't
    have the right structure. This is a one-time process.

    Returns:
        Dictionary mapping game_id to datetime
    """
    print("="*60)
    print("Building Game Date Index")
    print("="*60)
    print(f"Scanning {PBP_DIR}...")
    print()

    game_dates = {}
    pbp_files = list(PBP_DIR.glob("*.json"))

    print(f"Found {len(pbp_files):,} play-by-play files")
    print("Extracting game dates from pbp files...")

    for i, pbp_file in enumerate(pbp_files):
        if (i + 1) % 5000 == 0:
            print(f"  Progress: {i+1:,}/{len(pbp_files):,} files...")

        try:
            with open(pbp_file, 'r') as f:
                data = json.load(f)

                # Navigate to gamepackage (not gamepackageJSON)
                if 'page' not in data or 'content' not in data['page']:
                    continue

                content = data['page']['content']
                if 'gamepackage' not in content:
                    continue

                game_data = content['gamepackage']
                game_id = game_data.get('gmId')

                # Get date from game info
                if not game_id:
                    continue

                # Try to get date from game info
                game_info = game_data.get('gmInfo', {})
                date_str = game_info.get('dtTm')

                if date_str:
                    # Parse ESPN date format
                    try:
                        game_dates[str(game_id)] = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass

        except Exception as e:
            pass  # Skip malformed files

    print()
    print(f"✓ Indexed {len(game_dates):,} games")

    # Cache to file for future runs
    print(f"Caching to: {GAME_DATE_INDEX_FILE}")
    with open(GAME_DATE_INDEX_FILE, 'w') as f:
        json.dump({k: v.isoformat() for k, v in game_dates.items()}, f)

    print("✓ Index cached")
    print("="*60)
    print()

    return game_dates


def load_game_date_index() -> Dict[str, datetime]:
    """
    Load pre-built game date index from cache file.

    Returns:
        Dictionary mapping game_id to datetime
    """
    if GAME_DATE_INDEX_FILE.exists():
        print(f"Loading cached game date index from {GAME_DATE_INDEX_FILE}...")
        with open(GAME_DATE_INDEX_FILE, 'r') as f:
            data = json.load(f)
            game_dates = {k: datetime.fromisoformat(v) for k, v in data.items()}
        print(f"✓ Loaded {len(game_dates):,} game dates from cache")
        print()
        return game_dates
    else:
        print("No cached index found. Building new index...")
        return build_game_date_index()


def extract_game_date_from_schedule(game_id: str) -> Optional[datetime]:
    """
    Find game date from schedule files.

    Args:
        game_id: ESPN game ID

    Returns:
        datetime object or None
    """
    # Try to find in schedule files
    for schedule_file in SCHEDULE_DIR.glob("*.json"):
        try:
            with open(schedule_file, 'r') as f:
                data = json.load(f)
                if 'events' in data:
                    for event in data['events']:
                        if event.get('id') == game_id:
                            date_str = event.get('date')
                            if date_str:
                                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            continue

    return None


def parse_espn_pbp_file(filepath: Path, game_date: Optional[datetime] = None) -> List[Dict]:
    """
    Parse ESPN play-by-play JSON file and extract temporal events.

    Args:
        filepath: Path to ESPN play-by-play JSON file
        game_date: Optional game date (for timestamp reconstruction)

    Returns:
        List of event dictionaries
    """
    events = []

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Navigate to gamepackageJSON.plays
        if 'page' not in data or 'content' not in data['page']:
            return events

        content = data['page']['content']
        if 'gamepackage' not in content:
            return events

        game_data = content['gamepackage']

        # Extract game metadata
        game_id = game_data.get('gmId')
        if not game_id:
            return events

        # Get game date if not provided
        if not game_date:
            game_info = game_data.get('gmInfo', {})
            date_str = game_info.get('dtTm')
            if date_str:
                game_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # Extract plays
        plays = game_data.get('plays', [])
        if not plays:
            return events

        for play in plays:
            # Extract core fields
            event = {
                'game_id': game_id,
                'play_id': play.get('id'),
                'type_id': play.get('type', {}).get('id'),
                'type_text': play.get('type', {}).get('text'),
                'text': play.get('text'),
                'period': play.get('period', {}).get('number'),

                # Timestamps
                'wall_clock_display': play.get('wallclock'),  # e.g., "7:42 PM"
                'game_clock_display': play.get('clock', {}).get('displayValue'),  # e.g., "11:23"
                'game_clock_seconds': play.get('clock', {}).get('value'),  # Seconds remaining

                # Scoring
                'scoring_play': play.get('scoringPlay', False),
                'score_value': play.get('scoreValue'),
                'home_score': play.get('homeScore'),
                'away_score': play.get('awayScore'),

                # Shot details (if applicable)
                'shot_type': play.get('shotType'),
                'coordinate_x': play.get('coordinate', {}).get('x') if play.get('coordinate') else None,
                'coordinate_y': play.get('coordinate', {}).get('y') if play.get('coordinate') else None,

                # Participants (can have multiple players involved)
                'participants': []
            }

            # Extract participants (players involved in play)
            if 'participants' in play:
                for participant in play['participants']:
                    event['participants'].append({
                        'athlete_id': participant.get('athlete', {}).get('id'),
                        'athlete_name': participant.get('athlete', {}).get('displayName'),
                        'team_id': participant.get('team', {}).get('id'),
                    })

            # Reconstruct full wall clock timestamp
            if game_date and event['wall_clock_display']:
                try:
                    # Parse wall clock time (e.g., "7:42 PM")
                    time_str = event['wall_clock_display'].strip()

                    # Handle different formats
                    if 'PM' in time_str or 'AM' in time_str:
                        # Remove AM/PM and parse
                        time_part = time_str.replace('PM', '').replace('AM', '').strip()
                        hour, minute = map(int, time_part.split(':'))

                        # Convert to 24-hour
                        if 'PM' in time_str and hour != 12:
                            hour += 12
                        elif 'AM' in time_str and hour == 12:
                            hour = 0

                        # Combine with game date
                        wall_clock = game_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        event['wall_clock_utc'] = wall_clock
                except Exception as e:
                    event['wall_clock_utc'] = None

            events.append(event)

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

    return events


def extract_players_from_box_score(filepath: Path) -> List[Dict]:
    """
    Extract player roster and biographical data from ESPN box score.

    Args:
        filepath: Path to ESPN box score JSON file

    Returns:
        List of player dictionaries
    """
    players = []

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Navigate to boxscore data
        if 'page' not in data or 'content' not in data['page']:
            return players

        content = data['page']['content']
        if 'gamepackage' not in content:
            return players

        game_data = content['gamepackage']
        boxscore = game_data.get('bxscr', {})

        # Extract players from both teams
        teams_data = boxscore.get('players', [])
        for team in teams_data:
            team_id = team.get('team', {}).get('id')
            team_name = team.get('team', {}).get('displayName')

            # Get statistics definitions
            stat_labels = team.get('statistics', [{}])[0].get('labels', []) if team.get('statistics') else []

            for player_data in team.get('statistics', [{}])[0].get('athletes', []):
                athlete = player_data.get('athlete', {})

                player = {
                    'player_id': athlete.get('id'),
                    'name': athlete.get('displayName'),
                    'short_name': athlete.get('shortName'),
                    'jersey': athlete.get('jersey'),
                    'position': athlete.get('position', {}).get('abbreviation'),
                    'team_id': team_id,
                    'team_name': team_name,

                    # Stats (if available)
                    'stats': dict(zip(stat_labels, player_data.get('stats', [])))
                }

                players.append(player)

    except Exception as e:
        print(f"Error extracting players from {filepath}: {e}")

    return players


def process_all_espn_data(limit: Optional[int] = None):
    """
    Process all ESPN play-by-play files and extract to temporal format.

    Args:
        limit: Optional limit on number of games to process (for testing)
    """
    print("="*60)
    print("ESPN Local Data → Temporal Format Extraction")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Skip game date index - dates are in each pbp file already
    # (building index takes 5-10 min, not worth it for single extraction)

    # Get all play-by-play files
    pbp_files = list(PBP_DIR.glob("*.json"))
    total_files = len(pbp_files)

    if limit:
        pbp_files = pbp_files[:limit]
        print(f"Processing {len(pbp_files)} of {total_files:,} games (test mode)")
    else:
        print(f"Processing all {total_files:,} games")

    print()

    # Process play-by-play files
    all_events = []
    all_players = {}
    processed_count = 0
    error_count = 0

    for i, pbp_file in enumerate(pbp_files):
        if (i + 1) % 1000 == 0:
            print(f"Progress: {i+1:,}/{len(pbp_files):,} games...")

        try:
            # Extract game ID from filename
            game_id = pbp_file.stem

            # Date will be extracted from pbp file itself (None triggers fallback)
            game_date = None

            # Extract temporal events
            events = parse_espn_pbp_file(pbp_file, game_date)
            all_events.extend(events)

            # Extract players from corresponding box score
            box_score_file = BOX_SCORE_DIR / f"{game_id}.json"
            if box_score_file.exists():
                players = extract_players_from_box_score(box_score_file)
                for player in players:
                    player_id = player['player_id']
                    if player_id and player_id not in all_players:
                        all_players[player_id] = player

            processed_count += 1

        except Exception as e:
            error_count += 1
            if error_count <= 10:  # Only print first 10 errors
                print(f"Error processing {pbp_file.name}: {e}")

    print(f"\nProcessed {processed_count:,} games")
    print(f"Errors: {error_count:,}")
    print(f"Total events extracted: {len(all_events):,}")
    print(f"Unique players found: {len(all_players):,}")
    print()

    # Convert to DataFrames and save
    print("="*60)
    print("Saving CSV files...")
    print("="*60)

    # Save temporal events
    if all_events:
        # Flatten participants into separate columns
        events_df = pd.DataFrame(all_events)

        # Extract first participant as primary player
        events_df['player_id'] = events_df['participants'].apply(
            lambda x: x[0]['athlete_id'] if x and len(x) > 0 else None
        )
        events_df['team_id'] = events_df['participants'].apply(
            lambda x: x[0]['team_id'] if x and len(x) > 0 else None
        )

        # Create event_data JSONB column
        events_df['event_data'] = events_df.apply(lambda row: json.dumps({
            'text': row['text'],
            'type_text': row['type_text'],
            'scoring_play': row['scoring_play'],
            'score_value': row['score_value'],
            'home_score': row['home_score'],
            'away_score': row['away_score'],
            'shot_type': row['shot_type'],
            'coordinate_x': row['coordinate_x'],
            'coordinate_y': row['coordinate_y'],
            'participants': row['participants']
        }), axis=1)

        # Select columns for temporal_events table
        events_output = events_df[[
            'game_id', 'player_id', 'team_id', 'wall_clock_utc',
            'game_clock_seconds', 'period', 'event_data'
        ]].copy()

        events_output['precision_level'] = 'minute'  # ESPN provides minute-level precision
        events_output['event_type'] = events_df['type_text'].str.lower().str.replace(' ', '_')
        events_output['data_source'] = 'espn'
        events_output['quarter'] = events_df['period']

        # Save
        events_file = OUTPUT_DIR / "temporal_events_espn.csv"
        events_output.to_csv(events_file, index=False)
        print(f"✓ Saved temporal events: {events_file}")
        print(f"  Rows: {len(events_output):,}")
        print(f"  Size: {events_file.stat().st_size / 1024 / 1024:.1f} MB")

    # Save players
    if all_players:
        players_df = pd.DataFrame(all_players.values())
        players_file = OUTPUT_DIR / "players_espn.csv"
        players_df.to_csv(players_file, index=False)
        print(f"\n✓ Saved players: {players_file}")
        print(f"  Rows: {len(players_df):,}")
        print(f"  Size: {players_file.stat().st_size / 1024 / 1024:.1f} MB")

    print()
    print("="*60)
    print("Extraction Complete!")
    print("="*60)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps:")
    print("1. Load players to RDS: python scripts/db/load_espn_players.py")
    print("2. Load events to RDS: python scripts/db/load_espn_events.py")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Extract local ESPN data to temporal format")
    parser.add_argument('--limit', type=int, help='Limit number of games to process (for testing)')

    args = parser.parse_args()

    # Validate directories exist
    if not PBP_DIR.exists():
        print(f"ERROR: Play-by-play directory not found: {PBP_DIR}")
        return

    if not BOX_SCORE_DIR.exists():
        print(f"ERROR: Box score directory not found: {BOX_SCORE_DIR}")
        return

    process_all_espn_data(limit=args.limit)


if __name__ == '__main__':
    main()
