#!/usr/bin/env python3
"""
Fetch Upcoming NBA Games from ESPN API

Purpose:
- Fetch scheduled NBA games for the next N days
- Parse ESPN scoreboard API response
- Return structured DataFrame with game info
- Save to parquet for downstream prediction pipeline

Usage:
    python scripts/ml/fetch_upcoming_games.py --days 7
    python scripts/ml/fetch_upcoming_games.py --days 14 --output /tmp/upcoming_games.parquet

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import requests


class UpcomingGamesFetcher:
    """Fetches upcoming NBA games from ESPN API"""

    def __init__(
        self,
        base_url: str = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    ):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    def fetch_games_for_date(self, date: datetime) -> List[Dict]:
        """
        Fetch games for a specific date from ESPN API

        Args:
            date: Date to fetch games for

        Returns:
            List of game dictionaries
        """
        date_str = date.strftime("%Y%m%d")

        try:
            response = self.session.get(
                self.base_url, params={"dates": date_str}, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            games = []
            if "events" in data:
                for event in data["events"]:
                    game_info = self._parse_game_event(event, date)
                    if game_info:
                        games.append(game_info)

            return games

        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Error fetching games for {date_str}: {e}")
            return []
        except (KeyError, json.JSONDecodeError) as e:
            print(f"  ⚠️  Error parsing response for {date_str}: {e}")
            return []

    def _parse_game_event(self, event: Dict, date: datetime) -> Optional[Dict]:
        """
        Parse a single game event from ESPN API response

        Args:
            event: Event dictionary from ESPN API
            date: Date of the game

        Returns:
            Parsed game dictionary or None if not a scheduled game
        """
        try:
            # Check game status - we only want scheduled games
            status_type = event.get("status", {}).get("type", {}).get("name", "")

            # STATUS_SCHEDULED = not yet played
            # STATUS_IN_PROGRESS = currently playing
            # STATUS_FINAL = completed
            if status_type not in ["STATUS_SCHEDULED", "STATUS_IN_PROGRESS"]:
                return None

            # Extract basic game info
            game_id = event.get("id")
            game_date = event.get("date")  # ISO format: 2025-10-22T23:00Z
            game_name = event.get("name", "")  # e.g., "Lakers @ Warriors"

            # Extract competition info
            competitions = event.get("competitions", [])
            if not competitions:
                return None

            competition = competitions[0]
            competitors = competition.get("competitors", [])

            if len(competitors) != 2:
                return None

            # Identify home and away teams
            # ESPN format: competitors[0] is usually home, competitors[1] is away
            # But check the 'homeAway' field to be sure
            home_team = None
            away_team = None

            for competitor in competitors:
                team_info = competitor.get("team", {})
                home_away = competitor.get("homeAway", "")

                team_data = {
                    "id": team_info.get("id"),
                    "name": team_info.get("displayName", ""),
                    "abbreviation": team_info.get("abbreviation", ""),
                    "location": team_info.get("location", ""),
                }

                if home_away == "home":
                    home_team = team_data
                else:
                    away_team = team_data

            if not home_team or not away_team:
                return None

            # Extract venue info
            venue = competition.get("venue", {})
            venue_name = venue.get("fullName", "")
            venue_city = venue.get("address", {}).get("city", "")
            venue_state = venue.get("address", {}).get("state", "")

            # Extract broadcast info
            broadcasts = competition.get("broadcasts", [])
            broadcast_networks = [
                b.get("names", [""])[0] for b in broadcasts if b.get("names")
            ]

            # Status detail (e.g., "7:00 PM ET", "Final", "3rd Qtr")
            status_detail = event.get("status", {}).get("type", {}).get("detail", "")

            return {
                "game_id": game_id,
                "game_date": game_date,
                "game_date_local": date.strftime("%Y-%m-%d"),
                "status": status_type,
                "status_detail": status_detail,
                "game_name": game_name,
                "home_team_id": home_team["id"],
                "home_team_name": home_team["name"],
                "home_team_abbr": home_team["abbreviation"],
                "home_team_location": home_team["location"],
                "away_team_id": away_team["id"],
                "away_team_name": away_team["name"],
                "away_team_abbr": away_team["abbreviation"],
                "away_team_location": away_team["location"],
                "venue_name": venue_name,
                "venue_city": venue_city,
                "venue_state": venue_state,
                "broadcast_networks": (
                    ", ".join(broadcast_networks) if broadcast_networks else None
                ),
                "espn_url": f"https://www.espn.com/nba/game/_/gameId/{game_id}",
            }

        except (KeyError, IndexError, TypeError) as e:
            print(f"  ⚠️  Error parsing game event: {e}")
            return None

    def fetch_upcoming_games(self, days_ahead: int = 7) -> pd.DataFrame:
        """
        Fetch upcoming NBA games for the next N days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            DataFrame with upcoming games
        """
        print(f"\n{'='*80}")
        print(f"FETCHING UPCOMING NBA GAMES")
        print(f"{'='*80}")
        print(
            f"Date range: {datetime.now().strftime('%Y-%m-%d')} to "
            f"{(datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')}"
        )
        print(f"Days ahead: {days_ahead}")
        print()

        all_games = []

        for day_offset in range(days_ahead + 1):  # +1 to include today
            date = datetime.now() + timedelta(days=day_offset)
            print(f"Fetching games for {date.strftime('%Y-%m-%d')}...", end=" ")

            games = self.fetch_games_for_date(date)

            if games:
                print(f"✓ Found {len(games)} scheduled game(s)")
                all_games.extend(games)
            else:
                print("No scheduled games")

        if not all_games:
            print("\n⚠️  No upcoming games found")
            return pd.DataFrame()

        df = pd.DataFrame(all_games)

        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total upcoming games: {len(df)}")
        print(
            f"Date range: {df['game_date_local'].min()} to {df['game_date_local'].max()}"
        )
        print(
            f"Unique teams: {len(set(df['home_team_name'].tolist() + df['away_team_name'].tolist()))}"
        )
        print()

        return df


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Fetch upcoming NBA games from ESPN API"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to look ahead (default: 7)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/upcoming_games.parquet",
        help="Output parquet file path (default: /tmp/upcoming_games.parquet)",
    )
    parser.add_argument(
        "--csv", action="store_true", help="Also save as CSV for easy viewing"
    )
    parser.add_argument(
        "--display", action="store_true", help="Display games in terminal"
    )

    args = parser.parse_args()

    # Fetch games
    fetcher = UpcomingGamesFetcher()
    df = fetcher.fetch_upcoming_games(days_ahead=args.days)

    if df.empty:
        print("No games to save.")
        sys.exit(0)

    # Save to parquet
    df.to_parquet(args.output, index=False)
    print(f"✓ Saved to: {args.output}")

    # Optionally save as CSV
    if args.csv:
        csv_path = args.output.replace(".parquet", ".csv")
        df.to_csv(csv_path, index=False)
        print(f"✓ Saved CSV to: {csv_path}")

    # Optionally display games
    if args.display:
        print(f"\n{'='*80}")
        print("UPCOMING GAMES")
        print(f"{'='*80}\n")

        for _, game in df.iterrows():
            print(f"Game ID: {game['game_id']}")
            print(f"Date: {game['game_date_local']} ({game['status_detail']})")
            print(f"Matchup: {game['away_team_name']} @ {game['home_team_name']}")
            print(
                f"Venue: {game['venue_name']}, {game['venue_city']}, {game['venue_state']}"
            )
            if game["broadcast_networks"]:
                print(f"Broadcast: {game['broadcast_networks']}")
            print(f"URL: {game['espn_url']}")
            print()

    print(f"\n✓ Successfully fetched {len(df)} upcoming games")
    print(f"✓ Ready for feature extraction (Step 2)")


if __name__ == "__main__":
    main()
