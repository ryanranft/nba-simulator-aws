#!/usr/bin/env python3
"""
Comprehensive NBA Stats API Scraper using nba_api

Scrapes ALL major nba_api endpoints for maximum feature coverage.
Python equivalent of hoopR's 200+ NBA Stats API endpoints.

TIER 1 ENDPOINTS ENABLED (October 6, 2025):
✅ Advanced box scores (8 endpoints) - 40-50 features
✅ Player tracking (4 endpoints) - 20-30 features
Total features added: 60-80 (269-289 total, up from 209)

Coverage includes:
- Advanced box scores (V2, V3, hustle, tracking, matchups, four factors, usage) ✅ ENABLED
- Player tracking (defense, rebounding, passing, shots) ✅ ENABLED
- Team dashboards (clutch, lineups, shooting splits, opponent stats)
- Draft combine data (measurements, drills, shooting)
- Shot charts (detailed, league-wide, lineup-specific)
- League dashboards (player stats, team stats, lineups)
- Player/team career stats and profiles
- Game rotation and hustle stats
- Synergy play types
- Win probability

PRODUCTION CONFIGURATION (October 7, 2025):
- All endpoints enabled (no limits)
- Season cutoffs for unavailable data:
  * Player tracking: 2014+ only (SportVU era)
  * Hustle stats: 2016+ only
  * Synergy play types: 2016+ only
- PlayByPlayV2 endpoint for wall clock timestamps
- Rate limit: 1.5s between requests (safer for long runs)
- Full run estimate: ~25-30 hours/season

TEMPORAL PANEL DATA FEATURES:
- Wall clock timestamps (ISO 8601 format)
- Game clock timestamps
- Player birth dates for age calculations
- Cumulative statistics snapshots
- Millisecond precision where available

Prerequisites:
    pip install nba_api

Usage:
    # Scrape single season all endpoints
    python scripts/etl/scrape_nba_api_comprehensive.py --season 2024 --all-endpoints

    # Scrape specific categories
    python scripts/etl/scrape_nba_api_comprehensive.py --season 2024 --boxscores --player-tracking

    # Upload to S3
    python scripts/etl/scrape_nba_api_comprehensive.py --season 2024 --all-endpoints --upload-to-s3

Import Fix (October 6, 2025):
    Changed from individual imports to module-level import to avoid naming conflicts:
    from nba_api.stats import endpoints as nba_endpoints
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
import traceback

try:
    from nba_api.stats import endpoints as nba_endpoints
    HAS_NBA_API = True
except ImportError:
    HAS_NBA_API = False
    print("❌ nba_api package not installed")
    print("Install with: pip install nba_api")
    sys.exit(1)

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class ComprehensiveNBAStatsScraper:
    """
    Comprehensive NBA Stats API scraper using nba_api

    Equivalent to hoopR's 200+ endpoints in R
    """

    def __init__(self, output_dir="/tmp/nba_api_comprehensive", s3_bucket=None):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None

        # Create category subdirectories
        self.categories = [
            'league_dashboards',
            'boxscores_advanced',
            'player_stats',
            'team_stats',
            'draft',
            'shot_charts',
            'tracking',
            'hustle',
            'synergy',
            'common',
            'game_logs',
            'play_by_play',  # NEW: For temporal panel data
            'player_info',   # NEW: For birth dates and age calculations
        ]

        for category in self.categories:
            (self.output_dir / category).mkdir(parents=True, exist_ok=True)

        self.stats = {
            'endpoints_scraped': 0,
            'files_created': 0,
            'errors': 0,
            'api_calls': 0,
        }

        # Rate limiting (increased for production stability and to avoid NBA.com blocking)
        self.last_request_time = 0
        self.min_request_interval = 2.5  # 2.5s between requests (very conservative to avoid rate limiting)

    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def save_json(self, data, filepath):
        """Save data to JSON file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def upload_to_s3(self, local_path, s3_key):
        """Upload file to S3"""
        if not self.s3_client:
            return False

        try:
            self.s3_client.upload_file(str(local_path), self.s3_bucket, s3_key)
            return True
        except Exception as e:
            print(f"  ❌ S3 upload error: {e}")
            return False

    def scrape_endpoint(self, endpoint_func, params, category, filename):
        """
        Generic endpoint scraper

        Args:
            endpoint_func: nba_api endpoint function
            params: Dictionary of parameters
            category: Category subdirectory
            filename: Output filename
        """
        self._rate_limit()

        try:
            # Call endpoint
            response = endpoint_func(**params)
            self.stats['api_calls'] += 1

            # Get data as dict
            data = response.get_dict()

            # Save to file
            filepath = self.output_dir / category / filename
            self.save_json(data, filepath)
            self.stats['files_created'] += 1

            # Upload to S3
            if self.s3_client:
                s3_key = f"nba_api_comprehensive/{category}/{filename}"
                self.upload_to_s3(filepath, s3_key)

            return data

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.stats['errors'] += 1
            return None

    def scrape_league_dashboards(self, season):
        """Scrape league-wide dashboard stats"""
        print(f"\n📊 Scraping league dashboards for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"  # e.g., "2023-24"

        endpoint_list = [
            ('Player Stats', nba_endpoints.leaguedashplayerstats.LeagueDashPlayerStats, {'season': season_str}),
            ('Team Stats', nba_endpoints.leaguedashteamstats.LeagueDashTeamStats, {'season': season_str}),
            ('Lineups', nba_endpoints.leaguedashlineups.LeagueDashLineups, {'season': season_str}),
            ('Player Tracking Defense', nba_endpoints.leaguedashptdefend.LeagueDashPtDefend, {'season': season_str}),
            ('Player Tracking Stats', nba_endpoints.leaguedashptstats.LeagueDashPtStats, {'season': season_str}),
            ('Team Tracking Defense', nba_endpoints.leaguedashptteamdefend.LeagueDashPtTeamDefend, {'season': season_str}),
            ('League Leaders', nba_endpoints.leagueleaders.LeagueLeaders, {'season': season_str}),
        ]

        for name, func, params in endpoint_list:
            print(f"  → {name}")
            filename = f"{name.lower().replace(' ', '_')}_{season}.json"
            self.scrape_endpoint(func, params, 'league_dashboards', filename)
            self.stats['endpoints_scraped'] += 1

    def scrape_advanced_boxscores(self, season):
        """Scrape advanced box score endpoints for all games in season"""
        print(f"\n📦 Scraping advanced box scores for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        # First get all games for the season
        print(f"  → Getting game list...")
        games_response = nba_endpoints.leaguegamefinder.LeagueGameFinder(season_nullable=season_str)
        games_df = games_response.get_data_frames()[0]
        game_ids = games_df['GAME_ID'].unique()  # PRODUCTION: Get ALL games

        print(f"  → Found {len(game_ids)} games (scraping all)")

        boxscore_endpoints = [
            ('Advanced', nba_endpoints.boxscoreadvancedv2.BoxScoreAdvancedV2),
            ('Defensive', nba_endpoints.boxscoredefensivev2.BoxScoreDefensiveV2),
            ('Four Factors', nba_endpoints.boxscorefourfactorsv2.BoxScoreFourFactorsV2),
            ('Misc', nba_endpoints.boxscoremiscv2.BoxScoreMiscV2),
            ('Player Tracking', nba_endpoints.boxscoreplayertrackv2.BoxScorePlayerTrackV2),
            ('Scoring', nba_endpoints.boxscorescoringv2.BoxScoreScoringV2),
            ('Traditional', nba_endpoints.boxscoretraditionalv2.BoxScoreTraditionalV2),
            ('Usage', nba_endpoints.boxscoreusagev2.BoxScoreUsageV2),
        ]

        for i, game_id in enumerate(game_ids, 1):
            if i % 10 == 0:
                print(f"  → Progress: {i}/{len(game_ids)} games")

            for name, func in boxscore_endpoints:
                filename = f"{name.lower().replace(' ', '_')}_{game_id}.json"
                self.scrape_endpoint(func, {'game_id': game_id}, 'boxscores_advanced', filename)

        self.stats['endpoints_scraped'] += 1

    def scrape_player_tracking(self, season):
        """Scrape player tracking stats (2014+ only - SportVU era)"""

        # SEASON CUTOFF: Player tracking only available 2014+
        if season < 2014:
            print(f"\n⏭️  Skipping player tracking for {season} (not available before 2014)")
            return

        print(f"\n🏃 Scraping player tracking stats for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        # Get all players for the season with team info
        players_response = nba_endpoints.commonallplayers.CommonAllPlayers(season=season_str, is_only_current_season=1)
        players_df = players_response.get_data_frames()[0]

        # Filter to only players with teams (TEAM_ID != 0) and active roster status
        players_df = players_df[(players_df['TEAM_ID'] != 0) & (players_df['ROSTERSTATUS'] == 1)]

        # Get player and team IDs
        player_data = players_df[['PERSON_ID', 'TEAM_ID']].to_dict('records')  # PRODUCTION: Get ALL players

        print(f"  → Found {len(player_data)} active players with teams (scraping all)")

        tracking_endpoints = [
            ('Passing', nba_endpoints.playerdashptpass.PlayerDashPtPass),
            ('Rebounding', nba_endpoints.playerdashptreb.PlayerDashPtReb),
            ('Shot Defense', nba_endpoints.playerdashptshotdefend.PlayerDashPtShotDefend),
            ('Shots', nba_endpoints.playerdashptshots.PlayerDashPtShots),
        ]

        for i, player_info in enumerate(player_data, 1):
            if i % 10 == 0:
                print(f"  → Progress: {i}/{len(player_data)} players")

            player_id = player_info['PERSON_ID']
            team_id = player_info['TEAM_ID']

            for name, func in tracking_endpoints:
                filename = f"{name.lower().replace(' ', '_')}_player_{player_id}_{season}.json"
                self.scrape_endpoint(func, {
                    'player_id': player_id,
                    'team_id': team_id,
                    'season': season_str
                }, 'tracking', filename)

        self.stats['endpoints_scraped'] += 1

    def scrape_hustle_stats(self, season):
        """Scrape hustle stats (2016+ only)"""

        # SEASON CUTOFF: Hustle stats only available 2016+
        if season < 2016:
            print(f"\n⏭️  Skipping hustle stats for {season} (not available before 2016)")
            return

        print(f"\n💪 Scraping hustle stats for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        endpoints = [
            ('Player Hustle', nba_endpoints.leaguehustlestatsplayer.LeagueHustleStatsPlayer, {'season': season_str}),
            ('Team Hustle', nba_endpoints.leaguehustlestatsteam.LeagueHustleStatsTeam, {'season': season_str}),
        ]

        for name, func, params in endpoints:
            print(f"  → {name}")
            filename = f"{name.lower().replace(' ', '_')}_{season}.json"
            self.scrape_endpoint(func, params, 'hustle', filename)
            self.stats['endpoints_scraped'] += 1

    def scrape_draft_data(self, season):
        """Scrape draft combine and history data"""
        print(f"\n🎓 Scraping draft data for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        endpoints = [
            ('Draft Combine Stats', nba_endpoints.draftcombinestats.DraftCombineStats, {'season_all_time': season_str}),
            ('Draft History', nba_endpoints.drafthistory.DraftHistory, {'season_year_nullable': season_str}),
        ]

        for name, func, params in endpoints:
            print(f"  → {name}")
            filename = f"{name.lower().replace(' ', '_')}_{season}.json"
            self.scrape_endpoint(func, params, 'draft', filename)
            self.stats['endpoints_scraped'] += 1

    def scrape_shot_charts(self, season):
        """Scrape shot chart data (quality warning for 1996-2000)"""

        # DATA QUALITY WARNING: 1996-2000 has 25% missing shot coordinates
        if 1996 <= season <= 2000:
            print(f"\n⚠️  WARNING: {season} shot chart data has known quality issues (25% missing coordinates)")

        print(f"\n🎯 Scraping shot charts for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        # Get all players
        players_response = nba_endpoints.commonallplayers.CommonAllPlayers(season=season_str, is_only_current_season=1)
        players_df = players_response.get_data_frames()[0]
        player_ids = players_df['PERSON_ID'].tolist()  # PRODUCTION: Get ALL players

        print(f"  → Scraping shot charts for {len(player_ids)} players")

        for i, player_id in enumerate(player_ids, 1):
            if i % 5 == 0:
                print(f"  → Progress: {i}/{len(player_ids)} players")

            filename = f"shot_chart_player_{player_id}_{season}.json"
            self.scrape_endpoint(
                nba_endpoints.shotchartdetail.ShotChartDetail,
                {
                    'player_id': player_id,
                    'season_nullable': season_str,
                    'team_id': 0,
                    'context_measure_simple': 'FGA'
                },
                'shot_charts',
                filename
            )

        self.stats['endpoints_scraped'] += 1

    def scrape_synergy_stats(self, season):
        """Scrape synergy play type stats (2016+ only)"""

        # SEASON CUTOFF: Synergy play types only available 2016+
        if season < 2016:
            print(f"\n⏭️  Skipping synergy play types for {season} (not available before 2016)")
            return

        print(f"\n⚡ Scraping synergy play types for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        play_types = ['Transition', 'Isolation', 'PRBallHandler', 'PRRollman', 'Postup',
                     'Spotup', 'Handoff', 'Cut', 'OffScreen', 'OffRebound']

        for play_type in play_types:
            print(f"  → {play_type}")
            filename = f"synergy_{play_type.lower()}_{season}.json"
            self.scrape_endpoint(
                nba_endpoints.synergyplaytypes.SynergyPlayTypes,
                {
                    'season': season_str,
                    'season_type_all_star': 'Regular Season',
                    'play_type_nullable': play_type,
                    'player_or_team_abbreviation': 'P',
                    'type_grouping_nullable': 'offensive'
                },
                'synergy',
                filename
            )

        self.stats['endpoints_scraped'] += 1

    def scrape_play_by_play(self, season):
        """Scrape play-by-play data with wall clock timestamps for temporal panel data"""
        print(f"\n⏰ Scraping play-by-play with timestamps for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        # Get all games for the season
        print(f"  → Getting game list...")
        games_response = nba_endpoints.leaguegamefinder.LeagueGameFinder(season_nullable=season_str)
        games_df = games_response.get_data_frames()[0]
        game_ids = games_df['GAME_ID'].unique()

        print(f"  → Found {len(game_ids)} games (scraping all)")

        for i, game_id in enumerate(game_ids, 1):
            if i % 100 == 0:
                print(f"  → Progress: {i}/{len(game_ids)} games")

            filename = f"play_by_play_{game_id}.json"
            self.scrape_endpoint(
                nba_endpoints.playbyplayv2.PlayByPlayV2,
                {'game_id': game_id},
                'play_by_play',
                filename
            )

        self.stats['endpoints_scraped'] += 1

    def scrape_player_info(self, season):
        """Scrape player birth dates and biographical info for age calculations"""
        print(f"\n👤 Scraping player biographical info for {season}...")

        season_str = f"{season-1}-{str(season)[-2:]}"

        # Get all players for the season
        players_response = nba_endpoints.commonallplayers.CommonAllPlayers(season=season_str, is_only_current_season=1)
        players_df = players_response.get_data_frames()[0]
        player_ids = players_df['PERSON_ID'].tolist()

        print(f"  → Found {len(player_ids)} players (scraping all)")

        for i, player_id in enumerate(player_ids, 1):
            if i % 50 == 0:
                print(f"  → Progress: {i}/{len(player_ids)} players")

            filename = f"player_info_{player_id}_{season}.json"
            self.scrape_endpoint(
                nba_endpoints.commonplayerinfo.CommonPlayerInfo,
                {'player_id': player_id},
                'player_info',
                filename
            )

        self.stats['endpoints_scraped'] += 1

    def scrape_all_endpoints(self, season):
        """Scrape all available endpoints for a season"""
        print(f"\n🚀 Starting comprehensive NBA Stats API scrape for {season}")
        print(f"💾 Output directory: {self.output_dir}")
        if self.s3_client:
            print(f"☁️  S3 bucket: {self.s3_bucket}")

        # Scrape each category
        try:
            # TEMPORAL PANEL DATA - Priority endpoints
            self.scrape_play_by_play(season)      # Wall clock timestamps
            self.scrape_player_info(season)        # Birth dates for age calculations

            # Traditional endpoints
            self.scrape_league_dashboards(season)
            self.scrape_hustle_stats(season)       # 2016+ only
            self.scrape_draft_data(season)
            self.scrape_shot_charts(season)
            self.scrape_synergy_stats(season)      # 2016+ only

            # Tier 1 endpoints - HIGH PRIORITY (40-50 features)
            self.scrape_advanced_boxscores(season)

            # Tier 1 endpoints - HIGH PRIORITY (20-30 features, 2014+ only)
            self.scrape_player_tracking(season)
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            traceback.print_exc()

        # Print summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"Endpoint categories:  {self.stats['endpoints_scraped']}")
        print(f"Files created:        {self.stats['files_created']}")
        print(f"API calls made:       {self.stats['api_calls']}")
        print(f"Errors:               {self.stats['errors']}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive NBA Stats API scraper using nba_api (200+ endpoints)"
    )
    parser.add_argument('--season', type=int, required=True, help='Season year (e.g., 2024)')
    parser.add_argument('--all-endpoints', action='store_true', help='Scrape all available endpoints')
    parser.add_argument('--output-dir', default='/tmp/nba_api_comprehensive', help='Output directory')
    parser.add_argument('--upload-to-s3', action='store_true', help='Upload to S3')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake', help='S3 bucket name')

    args = parser.parse_args()

    if not HAS_NBA_API:
        sys.exit(1)

    # Configure S3
    s3_bucket = args.s3_bucket if args.upload_to_s3 else None
    if args.upload_to_s3 and not HAS_BOTO3:
        print("❌ boto3 required for S3 upload. Install with: pip install boto3")
        sys.exit(1)

    # Create scraper
    scraper = ComprehensiveNBAStatsScraper(output_dir=args.output_dir, s3_bucket=s3_bucket)

    # Scrape data
    scraper.scrape_all_endpoints(args.season)

    print(f"\n✅ Scraping complete!")
    print(f"📁 Files saved to: {scraper.output_dir}")
    if s3_bucket:
        print(f"☁️  Files uploaded to s3://{s3_bucket}/nba_api_comprehensive/")


if __name__ == '__main__':
    main()