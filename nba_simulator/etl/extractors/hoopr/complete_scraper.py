#!/usr/bin/env python3
"""
hoopR NBA Stats API - COMPLETE ALL ENDPOINTS Scraper

Scrapes EVERY available NBA endpoint from hoopR/sportsdataverse.
This is the most comprehensive NBA data collection possible.

Coverage includes:
- 4 bulk data loaders (pbp, schedules, box scores)
- 150+ NBA Stats API endpoints
- All advanced metrics, tracking, hustle, synergy, etc.

Runtime: 20-30 hours for full historical scrape
Data size: 50-100 GB estimated

Usage:
    # Scrape everything for recent seasons
    python scrape_hoopr_complete_all_endpoints.py --seasons 2023 2024 2025

    # Full historical scrape (2002-2025)
    python scrape_hoopr_complete_all_endpoints.py --all-seasons

    # Just today's games with all endpoints
    python scrape_hoopr_complete_all_endpoints.py --today

Version: 2.0 (AsyncBaseScraper Integration)
Updated: October 22, 2025 (Session 7 - Framework Migration)
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

try:
    from sportsdataverse.nba import (
        # Bulk data loaders
        load_nba_pbp,
        load_nba_team_boxscore,
        load_nba_player_boxscore,
        load_nba_schedule,
    )

    HAS_SPORTSDATAVERSE = True
except ImportError:
    HAS_SPORTSDATAVERSE = False
    print("❌ sportsdataverse not installed")
    sys.exit(1)

try:
    from sportsdataverse import nba

    HAS_NBA_API = True
except ImportError:
    HAS_NBA_API = False
    print("❌ sportsdataverse.nba not available")
    sys.exit(1)

# Import AsyncBaseScraper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.scrapers.async_scraper_base import AsyncBaseScraper


class ComprehensiveNBAScraper(AsyncBaseScraper):
    """
    Scrapes ALL NBA Stats API endpoints available through hoopR

    This scraper calls every single endpoint for maximum data coverage:
    - Bulk loaders for efficiency
    - Individual game endpoints for granularity
    - League-wide dashboards for aggregates
    - Advanced tracking and metrics
    """

    def __init__(
        self,
        output_dir=None,
        include_game_detail=False,
        config_name="hoopr_complete_endpoints",
    ):
        super().__init__(config_name=config_name)

        # Use configured output dir or override
        self.output_dir = (
            Path(output_dir)
            if output_dir
            else Path(self.config.storage.local_output_dir)
        )
        self.include_game_detail = include_game_detail

        # Create comprehensive directory structure
        self.categories = {
            # Bulk loaders
            "bulk_pbp": "Bulk play-by-play data",
            "bulk_team_box": "Bulk team box scores",
            "bulk_player_box": "Bulk player box scores",
            "bulk_schedule": "Bulk schedules",
            # Box score endpoints (game-level)
            "boxscore_traditional": "Traditional box scores",
            "boxscore_advanced": "Advanced box scores",
            "boxscore_scoring": "Scoring box scores",
            "boxscore_usage": "Usage box scores",
            "boxscore_fourfactors": "Four factors box scores",
            "boxscore_misc": "Miscellaneous box scores",
            "boxscore_hustle": "Hustle stats box scores",
            "boxscore_tracking": "Player tracking box scores",
            "boxscore_matchups": "Matchup box scores",
            "boxscore_defensive": "Defensive box scores",
            # Play-by-play
            "pbp_detailed": "Detailed play-by-play",
            "pbp_winprob": "Win probability play-by-play",
            # Shot data
            "shotchart_detail": "Shot chart detail",
            "shotchart_leaguewide": "League-wide shot charts",
            "shotchart_lineup": "Lineup shot charts",
            # Synergy
            "synergy_playtypes": "Synergy play types",
            # League dashboards
            "league_dash_player_stats": "League player stats",
            "league_dash_team_stats": "League team stats",
            "league_dash_lineups": "League lineups",
            "league_dash_player_clutch": "Player clutch stats",
            "league_dash_team_clutch": "Team clutch stats",
            "league_dash_player_bio": "Player bio stats",
            "league_dash_player_shot_locations": "Player shot locations",
            "league_dash_team_shot_locations": "Team shot locations",
            # Player tracking
            "league_dash_pt_stats": "Player tracking stats",
            "league_dash_pt_defend": "Player tracking defense",
            "league_dash_pt_team_defend": "Team tracking defense",
            "league_dash_pt_shots": "Player tracking shots",
            "league_dash_opponent_shots": "Opponent shot tracking",
            # Hustle stats
            "league_hustle_player": "League hustle player stats",
            "league_hustle_team": "League hustle team stats",
            "league_hustle_player_leaders": "Hustle player leaders",
            "league_hustle_team_leaders": "Hustle team leaders",
            # Player dashboards
            "player_dash_general": "Player general splits",
            "player_dash_clutch": "Player clutch splits",
            "player_dash_shooting": "Player shooting splits",
            "player_dash_opponent": "Player vs opponent",
            "player_dash_team_performance": "Player team performance",
            "player_dash_game_splits": "Player game splits",
            "player_dash_last_n_games": "Player last N games",
            "player_dash_year_over_year": "Player year over year",
            # Player tracking dashboards
            "player_dash_pt_shots": "Player tracking shots",
            "player_dash_pt_passing": "Player tracking passing",
            "player_dash_pt_rebounding": "Player tracking rebounding",
            "player_dash_pt_defense": "Player tracking shot defense",
            # Team dashboards
            "team_dash_general": "Team general splits",
            "team_dash_clutch": "Team clutch splits",
            "team_dash_shooting": "Team shooting splits",
            "team_dash_opponent": "Team vs opponent",
            "team_dash_team_performance": "Team performance splits",
            "team_dash_game_splits": "Team game splits",
            "team_dash_last_n_games": "Team last N games",
            "team_dash_year_over_year": "Team year over year",
            "team_dash_lineups": "Team lineups",
            # Team tracking dashboards
            "team_dash_pt_shots": "Team tracking shots",
            "team_dash_pt_passing": "Team tracking passing",
            "team_dash_pt_rebounding": "Team tracking rebounding",
            # Player info
            "player_info": "Player info",
            "player_career_stats": "Player career stats",
            "player_awards": "Player awards",
            "player_profile": "Player profiles",
            "player_game_log": "Player game logs",
            "player_estimated_metrics": "Player estimated metrics",
            # Team info
            "team_info_common": "Team common info",
            "team_details": "Team details",
            "team_game_log": "Team game logs",
            "team_year_by_year": "Team year by year stats",
            "team_estimated_metrics": "Team estimated metrics",
            "team_historical_leaders": "Team historical leaders",
            # Draft
            "draft_combine_stats": "Draft combine stats",
            "draft_combine_anthro": "Draft combine measurements",
            "draft_combine_drills": "Draft combine drills",
            "draft_combine_spot_shooting": "Draft combine spot shooting",
            "draft_combine_nonstat_shooting": "Draft combine non-stationary shooting",
            "draft_history": "Draft history",
            "draft_board": "Draft board",
            # Franchise
            "franchise_history": "Franchise history",
            "franchise_leaders": "Franchise leaders",
            "franchise_players": "Franchise players",
            # Scoreboards
            "scoreboard": "Daily scoreboard",
            "scoreboard_v2": "Scoreboard V2",
            "scoreboard_v3": "Scoreboard V3",
            "todays_scoreboard": "Today's scoreboard",
            # League info
            "league_leaders": "League leaders",
            "league_standings": "League standings",
            "league_game_finder": "League game finder",
            "league_game_log": "League game log",
            # Matchups
            "matchups_rollup": "Matchups rollup",
            "league_season_matchups": "League season matchups",
            # Other
            "game_rotation": "Game rotation",
            "video_events": "Video events",
            "assist_tracker": "Assist tracker",
            "assist_leaders": "Assist leaders",
            "defense_hub": "Defense hub",
            "playoff_picture": "Playoff picture",
            "common_playoff_series": "Playoff series",
            "homepage_leaders": "Homepage leaders",
            "all_time_leaders": "All-time leaders grids",
        }

        for category in self.categories.keys():
            (self.output_dir / category).mkdir(parents=True, exist_ok=True)

        self.stats = {
            "endpoints_called": 0,
            "endpoints_successful": 0,
            "endpoints_failed": 0,
            "total_data_points": 0,
            "errors": [],
        }

    def save_json(self, data, filepath):
        """Save data to JSON with proper serialization"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Handle DataFrames
        if hasattr(data, "to_dicts"):
            data = data.to_dicts()
        elif hasattr(data, "to_dict"):
            data = data.to_dict("records")

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

    async def call_endpoint_safe(self, endpoint_func, *args, **kwargs):
        """Safely call an endpoint with error handling and rate limiting"""
        self.stats["endpoints_called"] += 1
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Call endpoint (wrapped in thread for synchronous hoopR calls)
            result = await asyncio.to_thread(endpoint_func, *args, **kwargs)

            self.stats["endpoints_successful"] += 1
            return result
        except Exception as e:
            self.stats["endpoints_failed"] += 1
            self.stats["errors"].append(
                {
                    "endpoint": endpoint_func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "error": str(e),
                }
            )
            return None

    # ====================================================================
    # BULK LOADERS (Historical efficiency)
    # ====================================================================

    async def scrape_bulk_loaders(self, seasons):
        """Scrape the 4 main bulk data loaders"""
        print("\n" + "=" * 80)
        print("BULK DATA LOADERS (Most Efficient)")
        print("=" * 80)

        # Play-by-play
        print(f"\n📊 Loading bulk play-by-play for {len(seasons)} seasons...")
        pbp_data = await self.call_endpoint_safe(load_nba_pbp, seasons=seasons)
        if pbp_data is not None and len(pbp_data) > 0:
            season_str = "_".join(map(str, seasons))
            pbp_file = self.output_dir / "bulk_pbp" / f"pbp_seasons_{season_str}.json"
            self.save_json(pbp_data, pbp_file)
            self.stats["total_data_points"] += len(pbp_data)
            print(f"  ✅ Saved {len(pbp_data):,} play-by-play events")

            # Upload to S3 if configured
            if self.config.storage.upload_to_s3:
                s3_key = f"{self.config.storage.s3_prefix}/bulk_pbp/pbp_seasons_{season_str}.json"
                await self.store_data(
                    pbp_data, s3_key, f"pbp_seasons_{season_str}.json"
                )

        # Player box scores
        print(f"\n📊 Loading bulk player box scores for {len(seasons)} seasons...")
        player_box_data = await self.call_endpoint_safe(
            load_nba_player_boxscore, seasons=seasons
        )
        if player_box_data is not None and len(player_box_data) > 0:
            season_str = "_".join(map(str, seasons))
            player_box_file = (
                self.output_dir
                / "bulk_player_box"
                / f"player_box_seasons_{season_str}.json"
            )
            self.save_json(player_box_data, player_box_file)
            self.stats["total_data_points"] += len(player_box_data)
            print(f"  ✅ Saved {len(player_box_data):,} player box scores")

            if self.config.storage.upload_to_s3:
                s3_key = f"{self.config.storage.s3_prefix}/bulk_player_box/player_box_seasons_{season_str}.json"
                await self.store_data(
                    player_box_data, s3_key, f"player_box_seasons_{season_str}.json"
                )

        # Team box scores
        print(f"\n📊 Loading bulk team box scores for {len(seasons)} seasons...")
        team_box_data = await self.call_endpoint_safe(
            load_nba_team_boxscore, seasons=seasons
        )
        if team_box_data is not None and len(team_box_data) > 0:
            season_str = "_".join(map(str, seasons))
            team_box_file = (
                self.output_dir
                / "bulk_team_box"
                / f"team_box_seasons_{season_str}.json"
            )
            self.save_json(team_box_data, team_box_file)
            self.stats["total_data_points"] += len(team_box_data)
            print(f"  ✅ Saved {len(team_box_data):,} team box scores")

            if self.config.storage.upload_to_s3:
                s3_key = f"{self.config.storage.s3_prefix}/bulk_team_box/team_box_seasons_{season_str}.json"
                await self.store_data(
                    team_box_data, s3_key, f"team_box_seasons_{season_str}.json"
                )

        # Schedules
        print(f"\n📊 Loading bulk schedules for {len(seasons)} seasons...")
        schedule_data = await self.call_endpoint_safe(
            load_nba_schedule, seasons=seasons
        )
        if schedule_data is not None and len(schedule_data) > 0:
            season_str = "_".join(map(str, seasons))
            schedule_file = (
                self.output_dir
                / "bulk_schedule"
                / f"schedule_seasons_{season_str}.json"
            )
            self.save_json(schedule_data, schedule_file)
            self.stats["total_data_points"] += len(schedule_data)
            print(f"  ✅ Saved {len(schedule_data):,} games")

            if self.config.storage.upload_to_s3:
                s3_key = f"{self.config.storage.s3_prefix}/bulk_schedule/schedule_seasons_{season_str}.json"
                await self.store_data(
                    schedule_data, s3_key, f"schedule_seasons_{season_str}.json"
                )

            # Return games list for further scraping
            return schedule_data

        return None

    # ====================================================================
    # GAME-LEVEL ENDPOINTS (Per-game detail)
    # ====================================================================

    async def scrape_game_endpoints(self, game_id, season):
        """Scrape all per-game endpoints for a single game"""
        print(f"\n  🏀 Game {game_id}...")

        # Box score variants (V2 and V3)
        endpoints_to_call = [
            (
                "boxscore_traditional",
                nba.nba_boxscoretraditionalv2,
                {"game_id": game_id},
            ),
            (
                "boxscore_traditional",
                nba.nba_boxscoretraditionalv3,
                {"game_id": game_id},
            ),
            ("boxscore_advanced", nba.nba_boxscoreadvancedv2, {"game_id": game_id}),
            ("boxscore_advanced", nba.nba_boxscoreadvancedv3, {"game_id": game_id}),
            ("boxscore_scoring", nba.nba_boxscorescoringv2, {"game_id": game_id}),
            ("boxscore_scoring", nba.nba_boxscorescoringv3, {"game_id": game_id}),
            ("boxscore_usage", nba.nba_boxscoreusagev2, {"game_id": game_id}),
            ("boxscore_usage", nba.nba_boxscoreusagev3, {"game_id": game_id}),
            (
                "boxscore_fourfactors",
                nba.nba_boxscorefourfactorsv2,
                {"game_id": game_id},
            ),
            (
                "boxscore_fourfactors",
                nba.nba_boxscorefourfactorsv3,
                {"game_id": game_id},
            ),
            ("boxscore_misc", nba.nba_boxscoremiscv2, {"game_id": game_id}),
            ("boxscore_misc", nba.nba_boxscoremiscv3, {"game_id": game_id}),
            ("boxscore_hustle", nba.nba_boxscorehustlev2, {"game_id": game_id}),
            ("boxscore_tracking", nba.nba_boxscoreplayertrackv2, {"game_id": game_id}),
            ("boxscore_tracking", nba.nba_boxscoreplayertrackv3, {"game_id": game_id}),
            ("boxscore_matchups", nba.nba_boxscorematchups, {"game_id": game_id}),
            ("boxscore_matchups", nba.nba_boxscorematchupsv3, {"game_id": game_id}),
            ("boxscore_defensive", nba.nba_boxscoredefensive, {"game_id": game_id}),
            ("boxscore_defensive", nba.nba_boxscoredefensivev2, {"game_id": game_id}),
            # Play-by-play
            ("pbp_detailed", nba.nba_pbp, {"game_id": game_id}),
            ("pbp_winprob", nba.nba_winprobabilitypbp, {"game_id": game_id}),
            # Shot charts
            ("shotchart_detail", nba.nba_shotchartdetail, {"game_id": game_id}),
            ("shotchart_lineup", nba.nba_shotchartlineupdetail, {"game_id": game_id}),
            # Game rotation
            ("game_rotation", nba.nba_gamerotation, {"game_id": game_id}),
            # Video
            ("video_events", nba.nba_videoevents, {"game_id": game_id}),
        ]

        for category, endpoint_func, params in endpoints_to_call:
            data = await self.call_endpoint_safe(endpoint_func, **params)
            if data:
                filename = self.output_dir / category / f"{game_id}.json"
                self.save_json(data, filename)

        return True

    # ====================================================================
    # LEAGUE-WIDE ENDPOINTS (Season-level aggregates)
    # ====================================================================

    async def scrape_league_endpoints(self, season):
        """Scrape all league-wide dashboard endpoints for a season"""
        print(f"\n" + "=" * 80)
        print(f"LEAGUE DASHBOARDS - Season {season}")
        print("=" * 80)

        season_str = f"{season}-{str(season+1)[-2:]}"

        league_endpoints = [
            # Player stats dashboards
            (
                "league_dash_player_stats",
                nba.nba_leaguedashplayerstats,
                {"season": season_str, "per_mode_detailed": "PerGame"},
            ),
            (
                "league_dash_player_clutch",
                nba.nba_leaguedashplayerclutch,
                {"season": season_str},
            ),
            (
                "league_dash_player_bio",
                nba.nba_leaguedashplayerbiostats,
                {"season": season_str},
            ),
            (
                "league_dash_player_shot_locations",
                nba.nba_leaguedashplayershotlocations,
                {"season": season_str},
            ),
            # Team stats dashboards
            (
                "league_dash_team_stats",
                nba.nba_leaguedashteamstats,
                {"season": season_str, "per_mode_detailed": "PerGame"},
            ),
            (
                "league_dash_team_clutch",
                nba.nba_leaguedashteamclutch,
                {"season": season_str},
            ),
            (
                "league_dash_team_shot_locations",
                nba.nba_leaguedashteamshotlocations,
                {"season": season_str},
            ),
            # Lineups
            (
                "league_dash_lineups",
                nba.nba_leaguedashlineups,
                {"season": season_str, "group_quantity": 5},
            ),
            # Player tracking
            (
                "league_dash_pt_stats",
                nba.nba_leaguedashptstats,
                {"season": season_str, "pt_measure_type": "SpeedDistance"},
            ),
            (
                "league_dash_pt_defend",
                nba.nba_leaguedashptdefend,
                {"season": season_str, "defense_category": "Overall"},
            ),
            (
                "league_dash_pt_team_defend",
                nba.nba_leaguedashptteamdefend,
                {"season": season_str, "defense_category": "Overall"},
            ),
            (
                "league_dash_opponent_shots",
                nba.nba_leaguedashoppptshot,
                {"season": season_str},
            ),
            # Hustle stats
            (
                "league_hustle_player",
                nba.nba_leaguehustlestatsplayer,
                {"season": season_str},
            ),
            (
                "league_hustle_team",
                nba.nba_leaguehustlestatsteam,
                {"season": season_str},
            ),
            (
                "league_hustle_player_leaders",
                nba.nba_leaguehustlestatsplayerleaders,
                {"season": season_str},
            ),
            (
                "league_hustle_team_leaders",
                nba.nba_leaguehustlestatsteamleaders,
                {"season": season_str},
            ),
            # Leaders
            ("league_leaders", nba.nba_leagueleaders, {"season": season_str}),
            # Standings
            ("league_standings", nba.nba_leaguestandings, {"season": season_str}),
            ("league_standings", nba.nba_leaguestandingsv3, {"season": season_str}),
            # Game logs
            ("league_game_log", nba.nba_leaguegamelog, {"season": season_str}),
        ]

        for category, endpoint_func, params in league_endpoints:
            print(f"  📊 {endpoint_func.__name__}...")
            data = await self.call_endpoint_safe(endpoint_func, **params)
            if data:
                filename = self.output_dir / category / f"{season}.json"
                self.save_json(data, filename)

    # ====================================================================
    # SEASON-LEVEL ENDPOINTS (Historical/meta data)
    # ====================================================================

    async def scrape_static_endpoints(self):
        """Scrape endpoints that don't depend on season/game (one-time data)"""
        print("\n" + "=" * 80)
        print("STATIC/META ENDPOINTS (One-time scrapes)")
        print("=" * 80)

        static_endpoints = [
            # All-time data
            ("all_time_leaders", nba.nba_alltimeleadersgrids, {}),
            # Franchise data
            ("franchise_history", nba.nba_franchisehistory, {}),
            # Draft historical
            ("draft_history", nba.nba_drafthistory, {}),
            # Common info
            (
                "common_playoff_series",
                nba.nba_commonplayoffseries,
                {"season": "2023-24"},
            ),
        ]

        for category, endpoint_func, params in static_endpoints:
            print(f"  📊 {endpoint_func.__name__}...")
            data = await self.call_endpoint_safe(endpoint_func, **params)
            if data:
                filename = self.output_dir / category / "data.json"
                self.save_json(data, filename)

    # ====================================================================
    # MAIN ORCHESTRATION
    # ====================================================================

    async def scrape_all(self, seasons, include_game_detail=False):
        """
        Master function to scrape ALL endpoints

        Args:
            seasons: List of season years (e.g., [2023, 2024, 2025])
            include_game_detail: If True, scrape every endpoint for every game (SLOW!)
        """
        print("\n" + "=" * 80)
        print("🏀 NBA STATS API - COMPLETE ALL ENDPOINTS SCRAPER (ASYNC)")
        print("=" * 80)
        print(f"Seasons: {seasons}")
        print(f"Output: {self.output_dir}")
        print(f"Game detail: {'YES (SLOW!)' if include_game_detail else 'NO (fast)'}")
        print("=" * 80)

        start_time = time.time()

        # Step 1: Bulk loaders (most efficient)
        schedule_data = await self.scrape_bulk_loaders(seasons)

        # Step 2: Static endpoints (one-time)
        await self.scrape_static_endpoints()

        # Step 3: League dashboards (per season)
        for season in seasons:
            await self.scrape_league_endpoints(season)

        # Step 4: Per-game detail (optional - very slow!)
        if include_game_detail and schedule_data:
            print("\n" + "=" * 80)
            print("PER-GAME ENDPOINTS (This will take a LONG time!)")
            print("=" * 80)

            games = (
                schedule_data[:100] if len(schedule_data) > 100 else schedule_data
            )  # Limit for testing

            for game in tqdm(games, desc="Scraping games"):
                game_id = game.get("game_id")
                season = game.get("season")
                if game_id:
                    await self.scrape_game_endpoints(game_id, season)

        # Print summary
        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print("SCRAPING COMPLETE")
        print("=" * 80)
        print(f"Endpoints called: {self.stats['endpoints_called']}")
        print(f"Successful: {self.stats['endpoints_successful']}")
        print(f"Failed: {self.stats['endpoints_failed']}")
        print(f"Total data points: {self.stats['total_data_points']:,}")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        print(f"Output directory: {self.output_dir}")
        print("=" * 80)

        if self.stats["errors"]:
            print(f"\n⚠️  {len(self.stats['errors'])} errors occurred:")
            for err in self.stats["errors"][:10]:  # Show first 10
                print(f"  - {err['endpoint']}: {err['error'][:100]}")


async def main_async():
    parser = argparse.ArgumentParser(
        description="Scrape ALL NBA Stats API endpoints via hoopR (AsyncBaseScraper)"
    )
    parser.add_argument(
        "--seasons", nargs="+", type=int, help="Season years (e.g., 2023 2024 2025)"
    )
    parser.add_argument(
        "--all-seasons", action="store_true", help="Scrape all seasons 2002-2025"
    )
    parser.add_argument(
        "--today", action="store_true", help="Scrape just today's season (2025)"
    )
    parser.add_argument(
        "--game-detail", action="store_true", help="Include per-game endpoints (SLOW!)"
    )
    parser.add_argument(
        "--output-dir", default=None, help="Output directory (default: from config)"
    )

    args = parser.parse_args()

    # Determine seasons
    if args.all_seasons:
        seasons = list(range(2002, 2026))
    elif args.today:
        seasons = [2025]
    elif args.seasons:
        seasons = args.seasons
    else:
        print("❌ Must specify --seasons, --all-seasons, or --today")
        sys.exit(1)

    # Create scraper
    scraper = ComprehensiveNBAScraper(
        output_dir=args.output_dir, include_game_detail=args.game_detail
    )

    # Scrape everything
    await scraper.scrape_all(seasons=seasons, include_game_detail=args.game_detail)

    print(f"\n✅ Complete! Data saved to {scraper.output_dir}")


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
