#!/usr/bin/env python3
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
    TeamDashboardByGeneralSplits,
    TeamDashboardByShootingSplits,
    TeamDashLineups,
    TeamDashPtPass,
    TeamDashPtReb,
    TeamDashPtShots,
)
from nba_api.stats.static import teams

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NBAAPITeamDashboardsScraper:
    def __init__(self, output_dir="/tmp/nba_api_team_dashboards"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "x-nba-stats-origin": "stats",
                "x-nba-stats-token": "true",
            }
        )

        self.dashboard_endpoints = [
            ("general_splits", TeamDashboardByGeneralSplits),
            ("shooting_splits", TeamDashboardByShootingSplits),
            ("lineups", TeamDashLineups),
            ("pt_pass", TeamDashPtPass),
            ("pt_reb", TeamDashPtReb),
            ("pt_shots", TeamDashPtShots),
        ]

        logger.info("NBA API Team Dashboards Scraper initialized")

    def get_all_teams(self, season="2023-24"):
        """Get all teams (static list of 30 teams)"""
        try:
            all_teams = teams.get_teams()
            team_ids = [team['id'] for team in all_teams]
            logger.info(f"Retrieved {len(team_ids)} teams")
            return team_ids
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []

    def scrape_team_dashboards(self, team_id, season="2023-24"):
        """Scrape all dashboard endpoints for a team"""
        team_data = {}

        for endpoint_name, endpoint_class in self.dashboard_endpoints:
            try:
                logger.info(f"Scraping {endpoint_name} for team {team_id}")

                endpoint = endpoint_class(team_id=team_id, season=season)

                data_frames = endpoint.get_data_frames()
                if data_frames and len(data_frames) > 0:
                    team_data[endpoint_name] = data_frames[0].to_dict("records")
                    logger.info(f"✅ {endpoint_name}: {len(data_frames[0])} records")
                else:
                    logger.warning(f"⚠️ {endpoint_name}: No data")
                    team_data[endpoint_name] = []

                time.sleep(1.5)  # Rate limiting

            except Exception as e:
                logger.error(
                    f"❌ Error scraping {endpoint_name} for team {team_id}: {e}"
                )
                team_data[endpoint_name] = []

        return team_data

    def run(self, start_season="2020-21", end_season="2024-25"):
        """Run the scraper for multiple seasons"""
        seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

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
                with open(team_file, "w") as f:
                    json.dump(
                        {
                            "team_id": team_id,
                            "season": season,
                            "scraped_at": datetime.now().isoformat(),
                            "data": team_data,
                        },
                        f,
                        indent=2,
                    )

                logger.info(f"Saved team {team_id} data to {team_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape NBA API Team Dashboard endpoints"
    )
    parser.add_argument(
        "--start-season",
        type=str,
        default="2020-21",
        help="Start season (e.g., 2020-21)",
    )
    parser.add_argument(
        "--end-season", type=str, default="2024-25", help="End season (e.g., 2024-25)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/nba_api_team_dashboards",
        help="Output directory for scraped data",
    )

    args = parser.parse_args()

    logger.info(f"Starting NBA API Team Dashboards scraper")
    logger.info(f"  Seasons: {args.start_season} to {args.end_season}")
    logger.info(f"  Output: {args.output_dir}")

    scraper = NBAAPITeamDashboardsScraper(output_dir=args.output_dir)
    scraper.run(start_season=args.start_season, end_season=args.end_season)
