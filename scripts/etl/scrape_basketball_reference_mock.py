#!/usr/bin/env python3
"""
Basketball Reference Mock Scraper
Creates comprehensive mock Basketball Reference data for testing and development.

Since the Basketball Reference API is currently blocked (403 Forbidden),
this scraper creates realistic mock data that matches the expected schema.

Features created:
- True Shooting % (TS%)
- Player Efficiency Rating (PER)
- Box Plus/Minus (BPM)
- Win Shares (WS)
- Four Factors (eFG%, TOV%, ORB%, FTr)
- Advanced metrics for 2016-2025
"""

import argparse
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import random
import sys
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BasketballReferenceMockScraper:
    def __init__(
        self, output_dir: str = "/tmp/bbref_mock", rate_limit_delay: float = 0.1
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_delay = rate_limit_delay
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        self.start_time = time.time()

        # Create subdirectories
        self.player_logs_dir = self.output_dir / "player_game_logs"
        self.advanced_stats_dir = self.output_dir / "advanced_stats"
        self.four_factors_dir = self.output_dir / "four_factors"

        for dir_path in [
            self.player_logs_dir,
            self.advanced_stats_dir,
            self.four_factors_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Basketball Reference Mock Scraper initialized")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Rate limit delay: {self.rate_limit_delay}s")

    def _create_realistic_player_logs(self, season_end_year: int) -> List[Dict]:
        """Create realistic player game logs for a season"""
        # Realistic player names from different eras
        player_names = [
            "LeBron James",
            "Stephen Curry",
            "Kevin Durant",
            "Giannis Antetokounmpo",
            "Luka Doncic",
            "Jayson Tatum",
            "Joel Embiid",
            "Nikola Jokic",
            "Kawhi Leonard",
            "Jimmy Butler",
            "Damian Lillard",
            "Russell Westbrook",
            "Chris Paul",
            "Paul George",
            "Klay Thompson",
            "Draymond Green",
            "Anthony Davis",
            "Kyrie Irving",
            "James Harden",
            "Blake Griffin",
            "Kemba Walker",
            "Bradley Beal",
            "Devin Booker",
            "Donovan Mitchell",
            "Jrue Holiday",
            "Khris Middleton",
            "Pascal Siakam",
            "Kyle Lowry",
            "Al Horford",
            "Gordon Hayward",
            "Tobias Harris",
            "Ben Simmons",
        ]

        team_names = [
            "LAL",
            "GSW",
            "BKN",
            "MIL",
            "DAL",
            "BOS",
            "PHI",
            "DEN",
            "LAC",
            "MIA",
            "POR",
            "LAL",
            "PHX",
            "IND",
            "GSW",
            "GSW",
            "LAL",
            "BKN",
            "PHI",
            "DET",
            "BOS",
            "WAS",
            "PHX",
            "UTA",
            "MIL",
            "MIL",
            "TOR",
            "TOR",
            "BOS",
            "CHA",
            "PHI",
            "PHI",
        ]

        game_logs = []
        games_per_season = 82

        for game_num in range(1, games_per_season + 1):
            # Create 10 players per game (5 per team)
            for i in range(10):
                player_idx = i % len(player_names)
                team_idx = i % len(team_names)

                # Generate realistic stats based on player position/type
                if i < 5:  # Starters
                    minutes = random.uniform(28, 38)
                    points = random.uniform(12, 28)
                    rebounds = random.uniform(4, 12)
                    assists = random.uniform(3, 9)
                else:  # Bench players
                    minutes = random.uniform(8, 22)
                    points = random.uniform(4, 16)
                    rebounds = random.uniform(2, 8)
                    assists = random.uniform(1, 5)

                # Calculate derived stats
                fgm = int(points * random.uniform(0.35, 0.55))
                fga = int(fgm / random.uniform(0.40, 0.60))
                ftm = int(points * random.uniform(0.15, 0.35))
                fta = int(ftm / random.uniform(0.70, 0.90))

                # Advanced stats
                ts_percentage = random.uniform(0.50, 0.65)
                per = random.uniform(12, 28)
                bpm = random.uniform(-2, 8)
                ws = random.uniform(0.5, 12)

                game_log = {
                    "player_id": f"{season_end_year}_{player_idx:03d}",
                    "player_name": player_names[player_idx],
                    "team": team_names[team_idx],
                    "opponent": team_names[(team_idx + 1) % len(team_names)],
                    "date": f"{season_end_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                    "game_number": game_num,
                    "minutes": round(minutes, 1),
                    "points": int(points),
                    "rebounds": int(rebounds),
                    "assists": int(assists),
                    "steals": random.randint(0, 4),
                    "blocks": random.randint(0, 3),
                    "turnovers": random.randint(1, 6),
                    "field_goals_made": fgm,
                    "field_goals_attempted": fga,
                    "field_goal_percentage": round(fgm / fga, 3) if fga > 0 else 0,
                    "three_pointers_made": random.randint(0, 6),
                    "three_pointers_attempted": random.randint(0, 8),
                    "three_point_percentage": random.uniform(0.30, 0.45),
                    "free_throws_made": ftm,
                    "free_throws_attempted": fta,
                    "free_throw_percentage": round(ftm / fta, 3) if fta > 0 else 0,
                    "true_shooting_percentage": round(ts_percentage, 3),
                    "player_efficiency_rating": round(per, 1),
                    "box_plus_minus": round(bpm, 1),
                    "win_shares": round(ws, 2),
                    "season": season_end_year,
                    "data_source": "basketball_reference_mock",
                }

                game_logs.append(game_log)

        return game_logs

    def _create_realistic_advanced_stats(self, season_end_year: int) -> List[Dict]:
        """Create realistic advanced statistics for a season"""
        player_names = [
            "LeBron James",
            "Stephen Curry",
            "Kevin Durant",
            "Giannis Antetokounmpo",
            "Luka Doncic",
            "Jayson Tatum",
            "Joel Embiid",
            "Nikola Jokic",
            "Kawhi Leonard",
            "Jimmy Butler",
            "Damian Lillard",
            "Russell Westbrook",
            "Chris Paul",
            "Paul George",
            "Klay Thompson",
            "Draymond Green",
            "Anthony Davis",
            "Kyrie Irving",
            "James Harden",
            "Blake Griffin",
        ]

        advanced_stats = []

        for i, player_name in enumerate(player_names):
            # Generate realistic advanced stats
            ts_percentage = random.uniform(0.52, 0.68)
            per = random.uniform(15, 30)
            bpm = random.uniform(0, 10)
            ws = random.uniform(2, 15)
            ws_per_48 = random.uniform(0.10, 0.25)
            ortg = random.uniform(105, 125)
            drtg = random.uniform(105, 120)
            net_rating = ortg - drtg
            usage_pct = random.uniform(18, 35)
            pace = random.uniform(95, 105)

            advanced_stat = {
                "player_id": f"{season_end_year}_{i:03d}",
                "player_name": player_name,
                "season": season_end_year,
                "true_shooting_percentage": round(ts_percentage, 3),
                "player_efficiency_rating": round(per, 1),
                "box_plus_minus": round(bpm, 1),
                "win_shares": round(ws, 2),
                "win_shares_per_48": round(ws_per_48, 3),
                "offensive_rating": round(ortg, 1),
                "defensive_rating": round(drtg, 1),
                "net_rating": round(net_rating, 1),
                "usage_percentage": round(usage_pct, 1),
                "pace": round(pace, 1),
                "data_source": "basketball_reference_mock",
            }

            advanced_stats.append(advanced_stat)

        return advanced_stats

    def _create_realistic_four_factors(self, season_end_year: int) -> List[Dict]:
        """Create realistic four factors data for a season"""
        team_names = [
            "LAL",
            "GSW",
            "BKN",
            "MIL",
            "DAL",
            "BOS",
            "PHI",
            "DEN",
            "LAC",
            "MIA",
            "POR",
            "PHX",
            "IND",
            "UTA",
            "TOR",
            "ATL",
            "CHI",
            "CLE",
            "DET",
            "CHA",
            "ORL",
            "WAS",
            "NYK",
            "MEM",
            "SAS",
            "HOU",
            "OKC",
            "MIN",
            "SAC",
            "NOP",
        ]

        four_factors = []

        for i, team_name in enumerate(team_names):
            # Generate realistic four factors
            efg_pct = random.uniform(0.48, 0.58)
            tov_pct = random.uniform(0.12, 0.18)
            orb_pct = random.uniform(0.22, 0.32)
            ftr = random.uniform(0.18, 0.28)

            # Team performance metrics
            wins = random.randint(25, 60)
            losses = 82 - wins
            win_pct = wins / 82

            four_factor = {
                "team_id": f"{season_end_year}_{i:02d}",
                "team_name": team_name,
                "season": season_end_year,
                "wins": wins,
                "losses": losses,
                "win_percentage": round(win_pct, 3),
                "effective_field_goal_percentage": round(efg_pct, 3),
                "turnover_percentage": round(tov_pct, 3),
                "offensive_rebound_percentage": round(orb_pct, 3),
                "free_throw_rate": round(ftr, 3),
                "defensive_rating": round(random.uniform(105, 120), 1),
                "offensive_rating": round(random.uniform(105, 125), 1),
                "net_rating": round(random.uniform(-5, 15), 1),
                "data_source": "basketball_reference_mock",
            }

            four_factors.append(four_factor)

        return four_factors

    def _scrape_season(self, season_end_year: int) -> bool:
        """Create mock data for a single season"""
        logger.info(
            f"Creating mock Basketball Reference data for season {season_end_year}"
        )

        success_count = 0

        # Create player game logs
        try:
            player_logs = self._create_realistic_player_logs(season_end_year)
            output_file = (
                self.player_logs_dir / f"player_game_logs_{season_end_year}.json"
            )
            with open(output_file, "w") as f:
                json.dump(player_logs, f, indent=2)
            logger.info(
                f"✅ Created {len(player_logs)} player game logs for {season_end_year}"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"❌ Error creating player logs for {season_end_year}: {e}")
            self.failed_scrapes += 1

        time.sleep(self.rate_limit_delay)

        # Create advanced stats
        try:
            advanced_stats = self._create_realistic_advanced_stats(season_end_year)
            output_file = (
                self.advanced_stats_dir / f"advanced_stats_{season_end_year}.json"
            )
            with open(output_file, "w") as f:
                json.dump(advanced_stats, f, indent=2)
            logger.info(
                f"✅ Created {len(advanced_stats)} advanced stats records for {season_end_year}"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"❌ Error creating advanced stats for {season_end_year}: {e}")
            self.failed_scrapes += 1

        time.sleep(self.rate_limit_delay)

        # Create four factors
        try:
            four_factors = self._create_realistic_four_factors(season_end_year)
            output_file = self.four_factors_dir / f"four_factors_{season_end_year}.json"
            with open(output_file, "w") as f:
                json.dump(four_factors, f, indent=2)
            logger.info(
                f"✅ Created {len(four_factors)} four factors records for {season_end_year}"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"❌ Error creating four factors for {season_end_year}: {e}")
            self.failed_scrapes += 1

        time.sleep(self.rate_limit_delay)

        logger.info(
            f"Season {season_end_year}: {success_count}/3 data types created successfully"
        )
        return success_count > 0

    def scrape_date_range(self, start_year: int, end_year: int) -> Dict:
        """Create mock data for a range of seasons"""
        logger.info(
            f"Starting Basketball Reference mock data creation from {start_year} to {end_year}"
        )

        seasons_to_scrape = list(range(start_year, end_year + 1))
        successful_seasons = []
        failed_seasons = []

        for season in seasons_to_scrape:
            logger.info(f"Processing season {season} ({len(seasons_to_scrape)} total)")

            if self._scrape_season(season):
                successful_seasons.append(season)
                logger.info(f"✅ Season {season} completed successfully")
            else:
                failed_seasons.append(season)
                logger.error(f"❌ Season {season} failed")

            # Progress update
            completed = len(successful_seasons) + len(failed_seasons)
            remaining = len(seasons_to_scrape) - completed
            logger.info(
                f"Progress: {completed}/{len(seasons_to_scrape)} seasons completed, {remaining} remaining"
            )

        # Generate summary report
        end_time = time.time()
        duration = end_time - self.start_time

        summary = {
            "scrape_summary": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(end_time).isoformat(),
                "duration_seconds": duration,
                "duration_minutes": duration / 60,
                "total_seasons": len(seasons_to_scrape),
                "successful_seasons": len(successful_seasons),
                "failed_seasons": len(failed_seasons),
                "success_rate": (
                    len(successful_seasons) / len(seasons_to_scrape)
                    if seasons_to_scrape
                    else 0
                ),
            },
            "successful_seasons": successful_seasons,
            "failed_seasons": failed_seasons,
            "data_types_created": [
                "player_game_logs",
                "advanced_stats",
                "four_factors",
            ],
            "features_created": [
                "True Shooting % (TS%)",
                "Player Efficiency Rating (PER)",
                "Box Plus/Minus (BPM)",
                "Win Shares (WS)",
                "Four Factors (eFG%, TOV%, ORB%, FTr)",
                "Offensive/Defensive Ratings",
                "Usage Percentage",
                "Pace",
            ],
            "output_directory": str(self.output_dir),
            "rate_limit_delay": self.rate_limit_delay,
            "note": "Mock data created due to Basketball Reference API blocking (403 Forbidden)",
        }

        # Save summary report
        summary_file = self.output_dir / "scrape_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("=" * 60)
        logger.info("BASKETBALL REFERENCE MOCK DATA CREATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total seasons: {len(seasons_to_scrape)}")
        logger.info(f"Successful: {len(successful_seasons)}")
        logger.info(f"Failed: {len(failed_seasons)}")
        logger.info(
            f"Success rate: {len(successful_seasons)/len(seasons_to_scrape)*100:.1f}%"
        )
        logger.info(f"Duration: {duration/60:.1f} minutes")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Summary report: {summary_file}")

        return summary


def main():
    parser = argparse.ArgumentParser(description="Basketball Reference Mock Scraper")
    parser.add_argument(
        "--start-year",
        type=int,
        default=2016,
        help="Start year for mock data creation (default: 2016)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2025,
        help="End year for mock data creation (default: 2025)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/bbref_mock",
        help="Output directory (default: /tmp/bbref_mock)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.1,
        help="Rate limit delay in seconds (default: 0.1)",
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="Test mode: only create 2024 season"
    )

    args = parser.parse_args()

    if args.test_mode:
        logger.info("🧪 TEST MODE: Only creating 2024 season")
        args.start_year = 2024
        args.end_year = 2024

    scraper = BasketballReferenceMockScraper(
        output_dir=args.output_dir, rate_limit_delay=args.rate_limit
    )

    summary = scraper.scrape_date_range(args.start_year, args.end_year)

    if summary["scrape_summary"]["success_rate"] > 0.8:
        logger.info("✅ Mock data creation completed successfully!")
        return 0
    else:
        logger.error("❌ Mock data creation had significant failures")
        return 1


if __name__ == "__main__":
    exit(main())
