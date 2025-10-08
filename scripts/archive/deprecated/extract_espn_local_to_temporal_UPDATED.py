"""
⚠️ DEPRECATED - DO NOT USE ⚠️

This script has been superseded by extract_espn_local_to_temporal_v2.py

DEPRECATED ON: October 8, 2025
REASON: Intermediate version replaced by v2 with superior architecture
ACTIVE VERSION: scripts/etl/extract_espn_local_to_temporal_v2.py

---

Extract Local ESPN Data to Temporal Format - UPDATED PATHS

Uses the correct data paths in the project directory:
- /Users/ryanranft/nba-simulator-aws/data/nba_pbp
- /Users/ryanranft/nba-simulator-aws/data/nba_box_score

Usage:
    python scripts/etl/extract_espn_local_to_temporal_UPDATED.py --limit 1000  # Test with 1000 games
    python scripts/etl/extract_espn_local_to_temporal_UPDATED.py  # Process all 146K games
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse

# ESPN data directories (CORRECTED PATHS)
PROJECT_DIR = Path("/Users/ryanranft/nba-simulator-aws")
DATA_DIR = PROJECT_DIR / "data"
PBP_DIR = DATA_DIR / "nba_pbp"
BOX_SCORE_DIR = DATA_DIR / "nba_box_score"

# Output directory
OUTPUT_DIR = Path("/tmp/temporal_data_espn")


def parse_espn_pbp_file(filepath: Path) -> tuple[List[Dict], Optional[str], Optional[datetime]]:
    """
    Parse ESPN play-by-play JSON file and extract temporal events.

    Returns:
        (events, game_id, game_date)
    """
    events = []
    game_id = None
    game_date = None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Navigate to gamepackage
        if 'page' not in data or 'content' not in data['page']:
            return events, game_id, game_date

        content = data['page']['content']
        if 'gamepackage' not in content:
            return events, game_id, game_date

        gp = content['gamepackage']

        # Extract game ID and date
        if 'gmStrp' in gp:
            game_id = str(gp['gmStrp'].get('gid'))
            date_str = gp['gmStrp'].get('dt')
            if date_str:
                game_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # Extract plays from playGrps (list of lists)
        if 'pbp' in gp and 'playGrps' in gp['pbp']:
            play_groups = gp['pbp']['playGrps']

            # Flatten playGrps (nested lists by period)
            for period_group in play_groups:
                if not isinstance(period_group, list):
                    continue

                for play in period_group:
                    if not isinstance(play, dict):
                        continue

                    # Extract event details
                    event = {
                        'game_id': game_id,
                        'play_id': play.get('id'),
                        'text': play.get('text'),
                        'period': play.get('period', {}).get('number') if isinstance(play.get('period'), dict) else None,

                        # Clock (game time)
                        'game_clock_display': play.get('clock', {}).get('displayValue') if isinstance(play.get('clock'), dict) else None,

                        # Scores
                        'home_score': play.get('homeScore'),
                        'away_score': play.get('awayScore'),

                        # Will reconstruct wall clock from game date
                        'wall_clock_utc': game_date,  # Base date, need to adjust based on period/clock

                        # Event metadata (store everything in JSONB)
                        'event_data': play
                    }

                    events.append(event)

    except Exception as e:
        print(f"Error processing {filepath.name}: {e}")

    return events, game_id, game_date


def extract_players_from_box_score(filepath: Path) -> List[Dict]:
    """
    Extract player roster from ESPN box score.
    """
    players = []

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Navigate to gamepackage
        if 'page' not in data or 'content' not in data['page']:
            return players

        content = data['page']['content']
        if 'gamepackage' not in content:
            return players

        gp = content['gamepackage']

        # Extract players from box score
        if 'bxscr' in gp:
            bxscr = gp['bxscr']

            # Box score may have teams > plrs (players)
            if 'tms' in bxscr:
                for team in bxscr['tms']:
                    team_id = team.get('id')
                    team_name = team.get('displayName')

                    # Extract players
                    if 'plrs' in team:
                        for player_section in team['plrs']:
                            if 'stats' in player_section:
                                for player_data in player_section['stats']:
                                    athlete = player_data.get('athlete', {})

                                    player = {
                                        'player_id': athlete.get('id'),
                                        'name': athlete.get('displayName'),
                                        'short_name': athlete.get('shortName'),
                                        'jersey': athlete.get('jersey'),
                                        'position': athlete.get('position', {}).get('abbreviation') if isinstance(athlete.get('position'), dict) else None,
                                        'team_id': team_id,
                                        'team_name': team_name
                                    }

                                    if player['player_id']:
                                        players.append(player)

    except Exception as e:
        print(f"Error extracting players from {filepath.name}: {e}")

    return players


def process_all_espn_data(limit: Optional[int] = None):
    """
    Process all ESPN play-by-play files and extract to temporal format.
    """
    print("="*80)
    print("ESPN Local Data → Temporal Format Extraction (UPDATED PATHS)")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Data directory: {DATA_DIR}")
    print(f"PBP directory: {PBP_DIR}")
    print(f"Box score directory: {BOX_SCORE_DIR}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get all play-by-play files
    pbp_files = sorted(list(PBP_DIR.glob("*.json")))
    total_files = len(pbp_files)

    if limit:
        pbp_files = pbp_files[:limit]
        print(f"Processing {len(pbp_files):,} of {total_files:,} games (test mode)")
    else:
        print(f"Processing all {total_files:,} games")

    print()

    # Process play-by-play files
    all_events = []
    all_players = {}
    processed_count = 0
    error_count = 0
    games_with_plays = 0

    for i, pbp_file in enumerate(pbp_files):
        if (i + 1) % 5000 == 0:
            print(f"Progress: {i+1:,}/{len(pbp_files):,} games ({(i+1)/len(pbp_files)*100:.1f}%)...")

        try:
            # Extract temporal events
            events, game_id, game_date = parse_espn_pbp_file(pbp_file)

            if events:
                all_events.extend(events)
                games_with_plays += 1

            # Extract players from corresponding box score
            if game_id:
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
            if error_count <= 10:
                print(f"Error processing {pbp_file.name}: {e}")

    print()
    print(f"Processed {processed_count:,} games")
    print(f"Games with plays: {games_with_plays:,} ({games_with_plays/processed_count*100:.1f}%)")
    print(f"Errors: {error_count:,}")
    print(f"Total events extracted: {len(all_events):,}")
    print(f"Unique players found: {len(all_players):,}")
    print()

    # Convert to DataFrames and save
    print("="*80)
    print("Saving CSV files...")
    print("="*80)

    # Save temporal events
    if all_events:
        events_df = pd.DataFrame(all_events)

        # Create simplified event_data JSONB column (full play data)
        events_df['event_data_json'] = events_df['event_data'].apply(lambda x: json.dumps(x))

        # Select columns for temporal_events table
        events_output = events_df[[
            'game_id', 'wall_clock_utc', 'period', 'event_data_json'
        ]].copy()

        events_output.columns = ['game_id', 'wall_clock_utc', 'period', 'event_data']
        events_output['player_id'] = None  # Extract from event_data after load
        events_output['team_id'] = None
        events_output['game_clock_seconds'] = None  # Parse from display value
        events_output['precision_level'] = 'minute'
        events_output['event_type'] = 'play'
        events_output['data_source'] = 'espn'
        events_output['quarter'] = events_output['period']

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
    print("="*80)
    print("Extraction Complete!")
    print("="*80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps:")
    print("1. Load events to local PostgreSQL: python scripts/db/load_espn_to_local_postgres.py")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description="Extract local ESPN data to temporal format (UPDATED)")
    parser.add_argument('--limit', type=int, help='Limit number of games to process (for testing)')

    args = parser.parse_args()

    # Validate directories exist
    if not PBP_DIR.exists():
        print(f"ERROR: Play-by-play directory not found: {PBP_DIR}")
        print(f"Expected: {PBP_DIR}")
        return

    if not BOX_SCORE_DIR.exists():
        print(f"ERROR: Box score directory not found: {BOX_SCORE_DIR}")
        print(f"Expected: {BOX_SCORE_DIR}")
        return

    process_all_espn_data(limit=args.limit)


if __name__ == '__main__':
    main()
