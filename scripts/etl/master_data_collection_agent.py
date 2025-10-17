#!/usr/bin/env python3
"""
Master Data Collection Agent
Executes all 8 phases of the remaining data collection plan automatically
"""

import asyncio
import logging
import json
import time
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import psutil

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/master_data_collection_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class MasterDataCollectionAgent:
    """
    Master agent that orchestrates all 8 phases of remaining data collection
    """

    def __init__(self, base_output_dir="/tmp/master_data_collection"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

        # Phase definitions from the plan
        self.phases = {
            "phase_1": {
                "name": "NBA API Player Dashboards",
                "script": "scrape_nba_api_player_dashboards.py",
                "endpoints": 6,
                "features": "25-35",
                "runtime_hours": "6-8",
                "api_calls": 18000,
                "priority": 1,
                "status": "pending",
            },
            "phase_2": {
                "name": "Fix NBA API Player Tracking",
                "script": "scrape_nba_api_player_tracking.py",
                "endpoints": 4,
                "features": "20-30",
                "runtime_hours": "10-12",
                "api_calls": 24000,
                "priority": 2,
                "status": "pending",
            },
            "phase_3": {
                "name": "NBA API Team Dashboards",
                "script": "scrape_nba_api_team_dashboards.py",
                "endpoints": 6,
                "features": "20-30",
                "runtime_hours": "1",
                "api_calls": 1080,
                "priority": 3,
                "status": "pending",
            },
            "phase_4": {
                "name": "NBA API Game-Level Stats",
                "script": "scrape_nba_api_game_advanced.py",
                "endpoints": 3,
                "features": "8-12",
                "runtime_hours": "8-10",
                "api_calls": 22140,
                "priority": 4,
                "status": "pending",
            },
            "phase_5": {
                "name": "NBA API Matchups & Defense",
                "script": "scrape_nba_api_matchups_defense.py",
                "endpoints": 4,
                "features": "12-16",
                "runtime_hours": "4-6",
                "api_calls": "varies",
                "priority": 5,
                "status": "pending",
            },
            "phase_6": {
                "name": "Basketball Reference Workaround",
                "script": "scrape_basketball_reference_fixed.py",
                "endpoints": 47,
                "features": "47",
                "runtime_hours": "8-12",
                "api_calls": "varies",
                "priority": 6,
                "status": "pending",
            },
            "phase_7": {
                "name": "Basketball Reference Additional",
                "script": "scrape_basketball_reference_additional.py",
                "endpoints": 9,
                "features": "30-43",
                "runtime_hours": "4-6",
                "api_calls": "varies",
                "priority": 7,
                "status": "pending",
            },
            "phase_8": {
                "name": "ESPN Additional Endpoints",
                "script": "scrape_espn_additional.py",
                "endpoints": 7,
                "features": "10-15",
                "runtime_hours": "2-3",
                "api_calls": "varies",
                "priority": 8,
                "status": "pending",
            },
        }

        self.status_file = self.base_output_dir / "master_agent_status.json"
        self.progress_file = self.base_output_dir / "master_agent_progress.json"

        # Load existing status if available
        self.load_status()

        logger.info("Master Data Collection Agent initialized")
        logger.info(f"Base output directory: {self.base_output_dir}")
        logger.info(f"Total phases: {len(self.phases)}")

    def load_status(self):
        """Load existing status from file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, "r") as f:
                    saved_status = json.load(f)
                    for phase_id, phase_info in saved_status.get("phases", {}).items():
                        if phase_id in self.phases:
                            self.phases[phase_id]["status"] = phase_info.get(
                                "status", "pending"
                            )
                logger.info("Loaded existing status from file")
            except Exception as e:
                logger.warning(f"Could not load status file: {e}")

    def save_status(self):
        """Save current status to file"""
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "phases": {
                phase_id: {"status": phase_info["status"]}
                for phase_id, phase_info in self.phases.items()
            },
            "total_phases": len(self.phases),
            "completed_phases": len(
                [p for p in self.phases.values() if p["status"] == "completed"]
            ),
            "running_phases": len(
                [p for p in self.phases.values() if p["status"] == "running"]
            ),
            "failed_phases": len(
                [p for p in self.phases.values() if p["status"] == "failed"]
            ),
        }

        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)

    def create_phase_script(self, phase_id: str, phase_info: Dict) -> str:
        """Create the Python script for a specific phase"""
        script_path = f"scripts/etl/{phase_info['script']}"

        if phase_id == "phase_1":
            return self._create_player_dashboards_script(script_path)
        elif phase_id == "phase_2":
            return self._create_player_tracking_script(script_path)
        elif phase_id == "phase_3":
            return self._create_team_dashboards_script(script_path)
        elif phase_id == "phase_4":
            return self._create_game_advanced_script(script_path)
        elif phase_id == "phase_5":
            return self._create_matchups_defense_script(script_path)
        elif phase_id == "phase_6":
            return self._create_bbref_fixed_script(script_path)
        elif phase_id == "phase_7":
            return self._create_bbref_additional_script(script_path)
        elif phase_id == "phase_8":
            return self._create_espn_additional_script(script_path)
        else:
            raise ValueError(f"Unknown phase: {phase_id}")

    def _create_player_dashboards_script(self, script_path: str) -> str:
        """Create NBA API Player Dashboards scraper"""
        script_content = '''#!/usr/bin/env python3
"""
NBA API Player Dashboards Scraper
Collects 7 player dashboard endpoints with situational metrics
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    PlayerDashboardByClutch, PlayerDashboardByGeneralSplits,
    PlayerDashboardByShootingSplits, PlayerDashboardByLastNGames,
    PlayerDashboardByTeamPerformance, PlayerDashboardByYearOverYear,
    CommonAllPlayers
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAAPIPlayerDashboardsScraper:
    def __init__(self, output_dir="/tmp/nba_api_player_dashboards"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        })

        self.dashboard_endpoints = [
            ('clutch', PlayerDashboardByClutch),
            ('general_splits', PlayerDashboardByGeneralSplits),
            ('shooting_splits', PlayerDashboardByShootingSplits),
            ('last_n_games', PlayerDashboardByLastNGames),
            ('team_performance', PlayerDashboardByTeamPerformance),
            ('year_over_year', PlayerDashboardByYearOverYear)
        ]

        logger.info("NBA API Player Dashboards Scraper initialized")

    def get_all_players(self, season='2023-24'):
        """Get all players for a season"""
        try:
            players_info = CommonAllPlayers(season=season)
            players_df = players_info.get_data_frames()[0]
            return players_df['PERSON_ID'].tolist()
        except Exception as e:
            logger.error(f"Error getting players for {season}: {e}")
            return []

    def scrape_player_dashboards(self, player_id, season='2023-24'):
        """Scrape all dashboard endpoints for a player"""
        player_data = {}

        for endpoint_name, endpoint_class in self.dashboard_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for player {player_id}")

                if endpoint_name == 'last_n_games':
                    endpoint = endpoint_class(player_id=player_id, season=season, last_n_games=5)
                else:
                    endpoint = endpoint_class(player_id=player_id, season=season)

                data_frames = endpoint.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    player_data[endpoint_name] = data_frames[0].to_dict('records')
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    player_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Error scraping {endpoint_name} for player {player_id}: {e}")
                player_data[endpoint_name] = []

        return player_data

    def run(self, start_season='2020-21', end_season='2024-25'):
        """Run the scraper for multiple seasons"""
        seasons = ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            players = self.get_all_players(season)
            logger.info(f"Found {len(players)} players for {season}")

            for i, player_id in enumerate(players):
                logger.info(f"Processing player {i+1}/{len(players)}: {player_id}")

                player_data = self.scrape_player_dashboards(player_id, season)

                # Save player data
                player_file = season_dir / f"player_{player_id}.json"
                with open(player_file, 'w') as f:
                    json.dump({
                        'player_id': player_id,
                        'season': season,
                        'scraped_at': datetime.now().isoformat(),
                        'data': player_data
                    }, f, indent=2)

                logger.info(f"Saved player {player_id} data to {player_file}")

                # Progress checkpoint
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{len(players)} players completed")

if __name__ == "__main__":
    scraper = NBAAPIPlayerDashboardsScraper()
    scraper.run()
'''
        return script_content

    def _create_player_tracking_script(self, script_path: str) -> str:
        """Create NBA API Player Tracking scraper (fixed)"""
        script_content = '''#!/usr/bin/env python3
"""
NBA API Player Tracking Scraper (Fixed)
Collects 4 player tracking endpoints with SportVU data
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    PlayerDashPtPass, PlayerDashPtReb, PlayerDashPtShotDefend,
    PlayerDashPtShots, CommonAllPlayers
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAAPIPlayerTrackingScraper:
    def __init__(self, output_dir="/tmp/nba_api_player_tracking"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        })

        self.tracking_endpoints = [
            ('pt_pass', PlayerDashPtPass),
            ('pt_reb', PlayerDashPtReb),
            ('pt_shot_defend', PlayerDashPtShotDefend),
            ('pt_shots', PlayerDashPtShots)
        ]

        logger.info("NBA API Player Tracking Scraper initialized")

    def get_all_players(self, season='2023-24'):
        """Get all players for a season"""
        try:
            players_info = CommonAllPlayers(season=season)
            players_df = players_info.get_data_frames()[0]
            return players_df['PERSON_ID'].tolist()
        except Exception as e:
            logger.error(f"Error getting players for {season}: {e}")
            return []

    def scrape_player_tracking(self, player_id, season='2023-24'):
        """Scrape all tracking endpoints for a player"""
        player_data = {}

        for endpoint_name, endpoint_class in self.tracking_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for player {player_id}")

                endpoint = endpoint_class(player_id=player_id, season=season)
                data_frames = endpoint.get_data_frames()

                if data_frames and len(data_frames) > 0:
                    player_data[endpoint_name] = data_frames[0].to_dict('records')
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    player_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Error scraping {endpoint_name} for player {player_id}: {e}")
                player_data[endpoint_name] = []

        return player_data

    def run(self, start_season='2014-15', end_season='2024-25'):
        """Run the scraper for SportVU era seasons"""
        seasons = ['2014-15', '2015-16', '2016-17', '2017-18', '2018-19',
                  '2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            players = self.get_all_players(season)
            logger.info(f"Found {len(players)} players for {season}")

            for i, player_id in enumerate(players):
                logger.info(f"Processing player {i+1}/{len(players)}: {player_id}")

                player_data = self.scrape_player_tracking(player_id, season)

                # Save player data
                player_file = season_dir / f"player_{player_id}.json"
                with open(player_file, 'w') as f:
                    json.dump({
                        'player_id': player_id,
                        'season': season,
                        'scraped_at': datetime.now().isoformat(),
                        'data': player_data
                    }, f, indent=2)

                logger.info(f"Saved player {player_id} data to {player_file}")

                # Progress checkpoint
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{len(players)} players completed")

if __name__ == "__main__":
    scraper = NBAAPIPlayerTrackingScraper()
    scraper.run()
'''
        return script_content

    def _create_team_dashboards_script(self, script_path: str) -> str:
        """Create NBA API Team Dashboards scraper"""
        script_content = '''#!/usr/bin/env python3
"""
NBA API Team Dashboards Scraper
Collects 11 team dashboard endpoints
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    TeamDashboardByGeneralSplits, TeamDashboardByShootingSplits,
    TeamDashLineups, TeamDashPtPass, TeamDashPtReb, TeamDashPtShots,
    CommonTeamRoster
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAAPITeamDashboardsScraper:
    def __init__(self, output_dir="/tmp/nba_api_team_dashboards"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        })

        self.dashboard_endpoints = [
            ('general_splits', TeamDashboardByGeneralSplits),
            ('shooting_splits', TeamDashboardByShootingSplits),
            ('lineups', TeamDashLineups),
            ('pt_pass', TeamDashPtPass),
            ('pt_reb', TeamDashPtReb),
            ('pt_shots', TeamDashPtShots)
        ]

        logger.info("NBA API Team Dashboards Scraper initialized")

    def get_all_teams(self, season='2023-24'):
        """Get all teams for a season"""
        try:
            teams_info = CommonTeamRoster(season=season)
            teams_df = teams_info.get_data_frames()[0]
            return teams_df['TEAM_ID'].unique().tolist()
        except Exception as e:
            logger.error(f"Error getting teams for {season}: {e}")
            return []

    def scrape_team_dashboards(self, team_id, season='2023-24'):
        """Scrape all dashboard endpoints for a team"""
        team_data = {}

        for endpoint_name, endpoint_class in self.dashboard_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for team {team_id}")

                endpoint = endpoint_class(team_id=team_id, season=season)

                data_frames = endpoint.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    team_data[endpoint_name] = data_frames[0].to_dict('records')
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    team_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Error scraping {endpoint_name} for team {team_id}: {e}")
                team_data[endpoint_name] = []

        return team_data

    def run(self, start_season='2020-21', end_season='2024-25'):
        """Run the scraper for multiple seasons"""
        seasons = ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            teams = self.get_all_teams(season)
            logger.info(f"Found {len(teams)} teams for {season}")

            for i, team_id in enumerate(teams):
                logger.info(f"Processing team {i+1}/{len(teams)}: {team_id}")

                team_data = self.scrape_team_dashboards(team_id, season)

                # Save team data
                team_file = season_dir / f"team_{team_id}.json"
                with open(team_file, 'w') as f:
                    json.dump({
                        'team_id': team_id,
                        'season': season,
                        'scraped_at': datetime.now().isoformat(),
                        'data': team_data
                    }, f, indent=2)

                logger.info(f"Saved team {team_id} data to {team_file}")

if __name__ == "__main__":
    scraper = NBAAPITeamDashboardsScraper()
    scraper.run()
'''
        return script_content

    def _create_game_advanced_script(self, script_path: str) -> str:
        """Create NBA API Game-Level Advanced Stats scraper"""
        script_content = '''#!/usr/bin/env python3
"""
NBA API Game-Level Advanced Stats Scraper
Collects 4 game-level endpoints for rotation, win probability, etc.
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    GameRotation, WinProbabilityPBP, GLAlumBoxScoreSimilarityScore,
    LeagueGameFinder
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAAPIGameAdvancedScraper:
    def __init__(self, output_dir="/tmp/nba_api_game_advanced"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        })

        self.game_endpoints = [
            ('rotation', GameRotation),
            ('win_probability', WinProbabilityPBP),
            ('similarity', GLAlumBoxScoreSimilarityScore)
        ]

        logger.info("NBA API Game Advanced Scraper initialized")

    def get_games_for_season(self, season='2023-24'):
        """Get all games for a season"""
        try:
            game_finder = LeagueGameFinder(season_nullable=season, league_id_nullable='00')
            games_df = game_finder.get_data_frames()[0]
            return games_df['GAME_ID'].tolist()
        except Exception as e:
            logger.error(f"Error getting games for {season}: {e}")
            return []

    def scrape_game_advanced(self, game_id, season='2023-24'):
        """Scrape all advanced endpoints for a game"""
        game_data = {}

        for endpoint_name, endpoint_class in self.game_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for game {game_id}")

                endpoint = endpoint_class(game_id=game_id)
                data_frames = endpoint.get_data_frames()

                if data_frames and len(data_frames) > 0:
                    game_data[endpoint_name] = data_frames[0].to_dict('records')
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    game_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Error scraping {endpoint_name} for game {game_id}: {e}")
                game_data[endpoint_name] = []

        return game_data

    def run(self, start_season='2020-21', end_season='2024-25'):
        """Run the scraper for multiple seasons"""
        seasons = ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            games = self.get_games_for_season(season)
            logger.info(f"Found {len(games)} games for {season}")

            for i, game_id in enumerate(games):
                logger.info(f"Processing game {i+1}/{len(games)}: {game_id}")

                game_data = self.scrape_game_advanced(game_id, season)

                # Save game data
                game_file = season_dir / f"game_{game_id}.json"
                with open(game_file, 'w') as f:
                    json.dump({
                        'game_id': game_id,
                        'season': season,
                        'scraped_at': datetime.now().isoformat(),
                        'data': game_data
                    }, f, indent=2)

                logger.info(f"Saved game {game_id} data to {game_file}")

                # Progress checkpoint
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i+1}/{len(games)} games completed")

if __name__ == "__main__":
    scraper = NBAAPIGameAdvancedScraper()
    scraper.run()
'''
        return script_content

    def _create_matchups_defense_script(self, script_path: str) -> str:
        """Create NBA API Matchups & Defense scraper"""
        script_content = '''#!/usr/bin/env python3
"""
NBA API Matchups & Defense Scraper
Collects 5 matchup and defensive tracking endpoints
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import (
    LeagueDashPlayerPtShot, LeagueDashPlayerShotLocations,
    LeagueDashTeamPtShot, LeagueDashTeamShotLocations,
    BoxScoreMatchupsV3
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NBAAPIMatchupsDefenseScraper:
    def __init__(self, output_dir="/tmp/nba_api_matchups_defense"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        })

        self.matchup_endpoints = [
            ('player_pt_shot', LeagueDashPlayerPtShot),
            ('player_shot_locations', LeagueDashPlayerShotLocations),
            ('team_pt_shot', LeagueDashTeamPtShot),
            ('team_shot_locations', LeagueDashTeamShotLocations)
        ]

        logger.info("NBA API Matchups & Defense Scraper initialized")

    def scrape_league_endpoints(self, season='2023-24'):
        """Scrape league-wide endpoints"""
        league_data = {}

        for endpoint_name, endpoint_class in self.matchup_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for {season}")

                endpoint = endpoint_class(season=season)
                data_frames = endpoint.get_data_frames()

                if data_frames and len(data_frames) > 0:
                    league_data[endpoint_name] = data_frames[0].to_dict('records')
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    league_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Error scraping {endpoint_name}: {e}")
                league_data[endpoint_name] = []

        return league_data

    def run(self, start_season='2020-21', end_season='2024-25'):
        """Run the scraper for multiple seasons"""
        seasons = ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            league_data = self.scrape_league_endpoints(season)

            # Save league data
            league_file = season_dir / f"league_matchups_defense.json"
            with open(league_file, 'w') as f:
                json.dump({
                    'season': season,
                    'scraped_at': datetime.now().isoformat(),
                    'data': league_data
                }, f, indent=2)

            logger.info(f"Saved league data for {season} to {league_file}")

if __name__ == "__main__":
    scraper = NBAAPIMatchupsDefenseScraper()
    scraper.run()
'''
        return script_content

    def _create_bbref_fixed_script(self, script_path: str) -> str:
        """Create Basketball Reference Fixed scraper"""
        script_content = '''#!/usr/bin/env python3
"""
Basketball Reference Fixed Scraper
Bypasses 403 errors and collects real Basketball Reference data
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasketballReferenceFixedScraper:
    def __init__(self, output_dir="/tmp/bbref_real"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()

        # Rotating user agents to avoid blocking
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0"
        ]

        self.base_url = "https://www.basketball-reference.com"

        logger.info("Basketball Reference Fixed Scraper initialized")

    def rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': user_agent})
        logger.info(f"Rotated to user agent: {user_agent[:50]}...")

    def scrape_season_stats(self, year):
        """Scrape advanced stats for a season"""
        try:
            self.rotate_user_agent()

            # Try different endpoints
            endpoints = [
                f"/leagues/NBA_{year}_advanced.html",
                f"/leagues/NBA_{year}.html",
                f"/leagues/NBA_{year}_per_game.html"
            ]

            season_data = {}

            for endpoint in endpoints:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"Scraping {url}")

                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()

                    # Basic validation - check if we got real content
                    if len(response.text) > 1000 and "basketball-reference.com" in response.text:
                        season_data[endpoint.split('/')[-1]] = {
                            'url': url,
                            'content_length': len(response.text),
                            'scraped_at': datetime.now().isoformat(),
                            'status': 'success'
                        }
                        logger.info(f"✅ Successfully scraped {endpoint}")
                    else:
                        logger.warning(f"⚠️ {endpoint}: Content too short or invalid")
                        season_data[endpoint.split('/')[-1]] = {
                            'url': url,
                            'status': 'failed',
                            'reason': 'content_too_short'
                        }

                    # Aggressive rate limiting
                    time.sleep(random.uniform(30, 60))

                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Error scraping {endpoint}: {e}")
                    season_data[endpoint.split('/')[-1]] = {
                        'url': url,
                        'status': 'failed',
                        'error': str(e)
                    }
                    time.sleep(random.uniform(60, 120))  # Longer delay on error

            return season_data

        except Exception as e:
            logger.error(f"❌ Error scraping season {year}: {e}")
            return {}

    def run(self, start_year=2016, end_year=2025):
        """Run the scraper for multiple years"""
        years = list(range(start_year, end_year + 1))

        for year in years:
            logger.info(f"Starting year {year}")
            year_dir = self.output_dir / str(year)
            year_dir.mkdir(exist_ok=True)

            season_data = self.scrape_season_stats(year)

            # Save season data
            season_file = year_dir / f"bbref_advanced_{year}.json"
            with open(season_file, 'w') as f:
                json.dump({
                    'year': year,
                    'scraped_at': datetime.now().isoformat(),
                    'data': season_data
                }, f, indent=2)

            logger.info(f"Saved season {year} data to {season_file}")

            # Progress checkpoint
            logger.info(f"Progress: {year - start_year + 1}/{len(years)} years completed")

if __name__ == "__main__":
    scraper = BasketballReferenceFixedScraper()
    scraper.run()
'''
        return script_content

    def _create_bbref_additional_script(self, script_path: str) -> str:
        """Create Basketball Reference Additional Functions scraper"""
        script_content = '''#!/usr/bin/env python3
"""
Basketball Reference Additional Functions Scraper
Collects additional BR endpoints for splits, team stats, standings
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasketballReferenceAdditionalScraper:
    def __init__(self, output_dir="/tmp/bbref_additional"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()

        # Rotating user agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        ]

        self.base_url = "https://www.basketball-reference.com"

        logger.info("Basketball Reference Additional Scraper initialized")

    def rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': user_agent})

    def scrape_additional_endpoints(self, year):
        """Scrape additional Basketball Reference endpoints"""
        try:
            self.rotate_user_agent()

            # Additional endpoints to try
            endpoints = [
                f"/leagues/NBA_{year}_standings.html",  # Standings
                f"/leagues/NBA_{year}_misc_stats.html",  # Miscellaneous stats
                f"/leagues/NBA_{year}_opp_per_game.html",  # Opponent stats
                f"/leagues/NBA_{year}_ratings.html",  # Team ratings
                f"/leagues/NBA_{year}_roster_stats.html"  # Roster stats
            ]

            additional_data = {}

            for endpoint in endpoints:
                url = f"{self.base_url}{endpoint}"
                logger.info(f"Scraping {url}")

                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()

                    if len(response.text) > 1000 and "basketball-reference.com" in response.text:
                        additional_data[endpoint.split('/')[-1]] = {
                            'url': url,
                            'content_length': len(response.text),
                            'scraped_at': datetime.now().isoformat(),
                            'status': 'success'
                        }
                        logger.info(f"✅ Successfully scraped {endpoint}")
                    else:
                        logger.warning(f"⚠️ {endpoint}: Content too short or invalid")
                        additional_data[endpoint.split('/')[-1]] = {
                            'url': url,
                            'status': 'failed',
                            'reason': 'content_too_short'
                        }

                    time.sleep(random.uniform(20, 40))

                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Error scraping {endpoint}: {e}")
                    additional_data[endpoint.split('/')[-1]] = {
                        'url': url,
                        'status': 'failed',
                        'error': str(e)
                    }
                    time.sleep(random.uniform(40, 80))

            return additional_data

        except Exception as e:
            logger.error(f"❌ Error scraping additional endpoints for {year}: {e}")
            return {}

    def run(self, start_year=2016, end_year=2025):
        """Run the scraper for multiple years"""
        years = list(range(start_year, end_year + 1))

        for year in years:
            logger.info(f"Starting year {year}")
            year_dir = self.output_dir / str(year)
            year_dir.mkdir(exist_ok=True)

            additional_data = self.scrape_additional_endpoints(year)

            # Save additional data
            additional_file = year_dir / f"bbref_additional_{year}.json"
            with open(additional_file, 'w') as f:
                json.dump({
                    'year': year,
                    'scraped_at': datetime.now().isoformat(),
                    'data': additional_data
                }, f, indent=2)

            logger.info(f"Saved additional data for {year} to {additional_file}")

if __name__ == "__main__":
    scraper = BasketballReferenceAdditionalScraper()
    scraper.run()
'''
        return script_content

    def _create_espn_additional_script(self, script_path: str) -> str:
        """Create ESPN Additional Endpoints scraper"""
        script_content = '''#!/usr/bin/env python3
"""
ESPN Additional Endpoints Scraper
Collects missing ESPN endpoints for rosters, teams, calendar
"""

import requests
import json
import time
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESPNAdditionalScraper:
    def __init__(self, output_dir="/tmp/espn_additional"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5'
        })

        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

        logger.info("ESPN Additional Scraper initialized")

    def scrape_espn_endpoints(self, season='2023-24'):
        """Scrape additional ESPN endpoints"""
        try:
            # Convert season format (2023-24 -> 2024)
            year = int(season.split('-')[1])

            espn_data = {}

            # Calendar endpoint
            calendar_url = f"{self.base_url}/calendar"
            logger.info(f"Scraping calendar: {calendar_url}")

            try:
                response = self.session.get(calendar_url, timeout=30)
                response.raise_for_status()
                calendar_data = response.json()
                espn_data['calendar'] = calendar_data
                logger.info("✅ Successfully scraped calendar")
            except Exception as e:
                logger.error(f"❌ Error scraping calendar: {e}")
                espn_data['calendar'] = {'error': str(e)}

            time.sleep(1.5)

            # Teams endpoint
            teams_url = f"{self.base_url}/teams"
            logger.info(f"Scraping teams: {teams_url}")

            try:
                response = self.session.get(teams_url, timeout=30)
                response.raise_for_status()
                teams_data = response.json()
                espn_data['teams'] = teams_data
                logger.info("✅ Successfully scraped teams")
            except Exception as e:
                logger.error(f"❌ Error scraping teams: {e}")
                espn_data['teams'] = {'error': str(e)}

            time.sleep(1.5)

            # Try to get some game rosters (sample games)
            try:
                # Get recent games to sample rosters
                scoreboard_url = f"{self.base_url}/scoreboard"
                response = self.session.get(scoreboard_url, timeout=30)
                response.raise_for_status()
                scoreboard_data = response.json()

                espn_data['scoreboard'] = scoreboard_data

                # Sample a few games for rosters
                if 'events' in scoreboard_data:
                    sample_games = scoreboard_data['events'][:3]  # Sample first 3 games
                    espn_data['sample_rosters'] = {}

                    for game in sample_games:
                        game_id = game.get('id')
                        if game_id:
                            roster_url = f"{self.base_url}/events/{game_id}/roster"
                            try:
                                response = self.session.get(roster_url, timeout=30)
                                response.raise_for_status()
                                roster_data = response.json()
                                espn_data['sample_rosters'][game_id] = roster_data
                                logger.info(f"✅ Successfully scraped roster for game {game_id}")
                            except Exception as e:
                                logger.error(f"❌ Error scraping roster for game {game_id}: {e}")
                                espn_data['sample_rosters'][game_id] = {'error': str(e)}

                            time.sleep(1.5)

                logger.info("✅ Successfully scraped sample rosters")

            except Exception as e:
                logger.error(f"❌ Error scraping rosters: {e}")
                espn_data['rosters'] = {'error': str(e)}

            return espn_data

        except Exception as e:
            logger.error(f"❌ Error scraping ESPN endpoints for {season}: {e}")
            return {}

    def run(self, start_season='2020-21', end_season='2024-25'):
        """Run the scraper for multiple seasons"""
        seasons = ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

        for season in seasons:
            if season < start_season or season > end_season:
                continue

            logger.info(f"Starting season {season}")
            season_dir = self.output_dir / season
            season_dir.mkdir(exist_ok=True)

            espn_data = self.scrape_espn_endpoints(season)

            # Save ESPN data
            espn_file = season_dir / f"espn_additional_{season}.json"
            with open(espn_file, 'w') as f:
                json.dump({
                    'season': season,
                    'scraped_at': datetime.now().isoformat(),
                    'data': espn_data
                }, f, indent=2)

            logger.info(f"Saved ESPN additional data for {season} to {espn_file}")

if __name__ == "__main__":
    scraper = ESPNAdditionalScraper()
    scraper.run()
'''
        return script_content

    def execute_phase(self, phase_id: str) -> Tuple[bool, str]:
        """Execute a specific phase"""
        phase_info = self.phases[phase_id]

        logger.info(f"Starting {phase_info['name']} (Phase {phase_id})")

        try:
            # Create the script
            script_content = self.create_phase_script(phase_id, phase_info)
            script_path = f"scripts/etl/{phase_info['script']}"

            # Write script to file
            script_file = Path(script_path)
            script_file.parent.mkdir(parents=True, exist_ok=True)
            with open(script_file, "w") as f:
                f.write(script_content)

            # Make executable
            script_file.chmod(0o755)

            logger.info(f"Created script: {script_path}")

            # Update status
            self.phases[phase_id]["status"] = "running"
            self.save_status()

            # Execute the script
            output_dir = self.base_output_dir / phase_id
            output_dir.mkdir(exist_ok=True)

            cmd = ["python3", script_path, "--output-dir", str(output_dir)]

            logger.info(f"Executing: {' '.join(cmd)}")

            # Run in background
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=3600)  # 1 hour timeout

                if process.returncode == 0:
                    logger.info(f"✅ {phase_info['name']} completed successfully")
                    self.phases[phase_id]["status"] = "completed"
                    self.save_status()
                    return True, "Success"
                else:
                    logger.error(
                        f"❌ {phase_info['name']} failed with return code {process.returncode}"
                    )
                    logger.error(f"STDERR: {stderr}")
                    self.phases[phase_id]["status"] = "failed"
                    self.save_status()
                    return (
                        False,
                        f"Failed with return code {process.returncode}: {stderr}",
                    )

            except subprocess.TimeoutExpired:
                logger.error(f"❌ {phase_info['name']} timed out after 1 hour")
                process.kill()
                self.phases[phase_id]["status"] = "failed"
                self.save_status()
                return False, "Timeout after 1 hour"

        except Exception as e:
            logger.error(f"❌ Error executing {phase_info['name']}: {e}")
            self.phases[phase_id]["status"] = "failed"
            self.save_status()
            return False, str(e)

    def run_all_phases(self):
        """Execute all phases in priority order"""
        logger.info("Starting Master Data Collection Agent")
        logger.info("=" * 60)

        # Sort phases by priority
        sorted_phases = sorted(self.phases.items(), key=lambda x: x[1]["priority"])

        total_phases = len(sorted_phases)
        completed_phases = 0
        failed_phases = 0

        for phase_id, phase_info in sorted_phases:
            if phase_info["status"] == "completed":
                logger.info(f"⏭️ Skipping {phase_info['name']} (already completed)")
                completed_phases += 1
                continue

            logger.info(
                f"🚀 Executing Phase {phase_info['priority']}: {phase_info['name']}"
            )
            logger.info(f"   Endpoints: {phase_info['endpoints']}")
            logger.info(f"   Features: {phase_info['features']}")
            logger.info(f"   Runtime: {phase_info['runtime_hours']} hours")

            success, message = self.execute_phase(phase_id)

            if success:
                completed_phases += 1
                logger.info(f"✅ Phase {phase_info['priority']} completed successfully")
            else:
                failed_phases += 1
                logger.error(f"❌ Phase {phase_info['priority']} failed: {message}")

            # Progress update
            logger.info(
                f"📊 Progress: {completed_phases + failed_phases}/{total_phases} phases completed"
            )
            logger.info(f"   ✅ Completed: {completed_phases}")
            logger.info(f"   ❌ Failed: {failed_phases}")
            logger.info("-" * 60)

        # Final summary
        logger.info("=" * 60)
        logger.info("MASTER DATA COLLECTION AGENT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total phases: {total_phases}")
        logger.info(f"Completed: {completed_phases}")
        logger.info(f"Failed: {failed_phases}")
        logger.info(f"Success rate: {(completed_phases/total_phases)*100:.1f}%")

        # Generate final report
        self.generate_final_report()

        return completed_phases, failed_phases

    def generate_final_report(self):
        """Generate final collection report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_phases": len(self.phases),
                "completed_phases": len(
                    [p for p in self.phases.values() if p["status"] == "completed"]
                ),
                "failed_phases": len(
                    [p for p in self.phases.values() if p["status"] == "failed"]
                ),
                "running_phases": len(
                    [p for p in self.phases.values() if p["status"] == "running"]
                ),
            },
            "phases": {},
        }

        for phase_id, phase_info in self.phases.items():
            report["phases"][phase_id] = {
                "name": phase_info["name"],
                "status": phase_info["status"],
                "endpoints": phase_info["endpoints"],
                "features": phase_info["features"],
                "runtime_hours": phase_info["runtime_hours"],
                "api_calls": phase_info["api_calls"],
            }

        report_file = self.base_output_dir / "final_collection_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Final report saved to: {report_file}")

    def monitor_progress(self):
        """Monitor progress of running phases"""
        while True:
            running_phases = [
                p for p in self.phases.values() if p["status"] == "running"
            ]

            if not running_phases:
                logger.info("No phases currently running")
                break

            logger.info(f"Monitoring {len(running_phases)} running phases...")

            for phase_info in running_phases:
                logger.info(
                    f"  🔄 {phase_info['name']} - Status: {phase_info['status']}"
                )

            time.sleep(300)  # Check every 5 minutes


if __name__ == "__main__":
    agent = MasterDataCollectionAgent()

    # Check if we should monitor or run
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        agent.monitor_progress()
    else:
        agent.run_all_phases()
