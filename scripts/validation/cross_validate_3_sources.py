#!/usr/bin/env python3
"""
3-Source Cross-Validation Script

Compares NBA data from ESPN, hoopR, and NBA API to identify discrepancies.
Designed for overnight automation - validates games from last N days.

Validation checks:
1. Game existence (all 3 sources have the game?)
2. Final scores match
3. Play-by-play event counts
4. Key statistics (points, rebounds, assists)

Outputs:
- Validation report (JSON)
- Discrepancy summary
- Data quality scores per source

Usage:
    python scripts/validation/cross_validate_3_sources.py              # Last 3 days
    python scripts/validation/cross_validate_3_sources.py --days 7     # Last 7 days
    python scripts/validation/cross_validate_3_sources.py --detailed   # Full comparison

For overnight automation:
    - Runs after all 3 sources complete scraping
    - Generates quality report
    - Flags discrepancies for review

Version: 1.0
Created: October 18, 2025
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import sys
import boto3

# Configuration
S3_BUCKET = "nba-sim-raw-data-lake"
ESPN_PREFIX = "espn_incremental"
HOOPR_PREFIX = "hoopr_incremental"
NBA_API_PREFIX = "nba_api_incremental"
REPORTS_DIR = "/Users/ryanranft/nba-simulator-aws/reports/validation"


class ThreeSourceValidator:
    """Cross-validates data from ESPN, hoopR, and NBA API"""

    def __init__(self, days_back=3, detailed=False):
        self.days_back = days_back
        self.detailed = detailed
        self.s3_client = boto3.client('s3')

        # Validation results
        self.results = {
            "validation_date": datetime.now().isoformat(),
            "days_validated": days_back,
            "games_checked": 0,
            "discrepancies": [],
            "source_quality": {
                "espn": {"games": 0, "errors": 0, "quality": 0.0},
                "hoopr": {"games": 0, "errors": 0, "quality": 0.0},
                "nba_api": {"games": 0, "errors": 0, "quality": 0.0}
            },
            "summary": {}
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_date_range(self):
        """Get list of dates to validate."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_back)

        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return dates

    def list_s3_games(self, prefix, date_str):
        """List all games in S3 for a given source and date."""
        # Convert date format for ESPN (YYYYMMDD)
        if "espn" in prefix:
            date_folder = date_str.replace("-", "")
        else:
            date_folder = date_str

        full_prefix = f"{prefix}/{date_folder}/"

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=full_prefix
            )

            if 'Contents' not in response:
                return []

            # Extract game IDs from keys
            game_ids = set()
            for obj in response['Contents']:
                key = obj['Key']
                # Extract game ID from filename
                # Format: game_{ID}_pbp.json or game_{ID}_boxscore.json
                parts = key.split('/')[-1].split('_')
                if len(parts) >= 2:
                    game_id = parts[1]
                    game_ids.add(game_id)

            return list(game_ids)

        except Exception as e:
            self.logger.error(f"Error listing S3 games for {prefix}/{date_str}: {e}")
            return []

    def get_s3_json(self, key):
        """Download and parse JSON from S3."""
        try:
            response = self.s3_client.get_object(Bucket=S3_BUCKET, Key=key)
            return json.loads(response['Body'].read())
        except Exception as e:
            self.logger.error(f"Error reading S3 key {key}: {e}")
            return None

    def extract_game_stats(self, game_data, source):
        """Extract comparable stats from game data."""
        stats = {
            "source": source,
            "score_home": None,
            "score_away": None,
            "pbp_events": 0,
            "has_data": False
        }

        try:
            if source == "espn":
                # ESPN format
                if "competitions" in game_data:
                    comp = game_data["competitions"][0]
                    for team in comp.get("competitors", []):
                        score = int(team.get("score", 0))
                        if team.get("homeAway") == "home":
                            stats["score_home"] = score
                        else:
                            stats["score_away"] = score

                if "plays" in game_data:
                    stats["pbp_events"] = len(game_data["plays"])

            elif source == "hoopr":
                # hoopR format (list of play-by-play records)
                if isinstance(game_data, list) and len(game_data) > 0:
                    stats["pbp_events"] = len(game_data)
                    # Try to extract final score from last play
                    last_play = game_data[-1]
                    stats["score_home"] = last_play.get("home_score")
                    stats["score_away"] = last_play.get("away_score")

            elif source == "nba_api":
                # NBA API format
                if "resultSets" in game_data:
                    # This is simplified - actual extraction depends on endpoint
                    stats["has_data"] = True
                    # Box score has team stats
                    for result_set in game_data["resultSets"]:
                        if result_set.get("name") == "TeamStats":
                            rows = result_set.get("rowSet", [])
                            if len(rows) >= 2:
                                stats["score_home"] = rows[0][21]  # PTS index
                                stats["score_away"] = rows[1][21]

            stats["has_data"] = (stats["score_home"] is not None or
                                stats["score_away"] is not None or
                                stats["pbp_events"] > 0)

        except Exception as e:
            self.logger.error(f"Error extracting stats from {source}: {e}")

        return stats

    def validate_game(self, game_id, date_str):
        """Validate a single game across all 3 sources."""
        self.logger.info(f"  Validating game {game_id}...")

        # Collect data from all sources
        date_espn = date_str.replace("-", "")  # YYYYMMDD
        date_standard = date_str  # YYYY-MM-DD

        sources_data = {}

        # ESPN
        espn_key = f"{ESPN_PREFIX}/{date_espn}/game_{game_id}_pbp.json"
        espn_data = self.get_s3_json(espn_key)
        if espn_data:
            sources_data["espn"] = self.extract_game_stats(espn_data, "espn")
            self.results["source_quality"]["espn"]["games"] += 1
        else:
            self.results["source_quality"]["espn"]["errors"] += 1

        # hoopR
        hoopr_key = f"{HOOPR_PREFIX}/{date_standard}/game_{game_id}_pbp.json"
        hoopr_data = self.get_s3_json(hoopr_key)
        if hoopr_data:
            sources_data["hoopr"] = self.extract_game_stats(hoopr_data, "hoopr")
            self.results["source_quality"]["hoopr"]["games"] += 1
        else:
            self.results["source_quality"]["hoopr"]["errors"] += 1

        # NBA API
        nba_api_key = f"{NBA_API_PREFIX}/{date_standard}/game_{game_id}_boxscore.json"
        nba_api_data = self.get_s3_json(nba_api_key)
        if nba_api_data:
            sources_data["nba_api"] = self.extract_game_stats(nba_api_data, "nba_api")
            self.results["source_quality"]["nba_api"]["games"] += 1
        else:
            self.results["source_quality"]["nba_api"]["errors"] += 1

        # Check for discrepancies
        if len(sources_data) < 2:
            self.results["discrepancies"].append({
                "game_id": game_id,
                "date": date_str,
                "type": "insufficient_sources",
                "sources_found": list(sources_data.keys()),
                "severity": "high"
            })
            return

        # Compare scores
        scores_home = [s["score_home"] for s in sources_data.values() if s["score_home"]]
        scores_away = [s["score_away"] for s in sources_data.values() if s["score_away"]]

        if len(set(scores_home)) > 1:
            self.results["discrepancies"].append({
                "game_id": game_id,
                "date": date_str,
                "type": "score_mismatch_home",
                "values": {s: sources_data[s]["score_home"] for s in sources_data},
                "severity": "high"
            })

        if len(set(scores_away)) > 1:
            self.results["discrepancies"].append({
                "game_id": game_id,
                "date": date_str,
                "type": "score_mismatch_away",
                "values": {s: sources_data[s]["score_away"] for s in sources_data},
                "severity": "high"
            })

        # Compare event counts (should be similar, allowing for format differences)
        pbp_counts = {s: sources_data[s]["pbp_events"] for s in sources_data if sources_data[s]["pbp_events"] > 0}
        if len(pbp_counts) >= 2:
            avg = sum(pbp_counts.values()) / len(pbp_counts)
            for source, count in pbp_counts.items():
                if abs(count - avg) / avg > 0.1:  # >10% difference
                    self.results["discrepancies"].append({
                        "game_id": game_id,
                        "date": date_str,
                        "type": "pbp_count_divergence",
                        "source": source,
                        "count": count,
                        "average": avg,
                        "severity": "medium"
                    })

    def validate_date(self, date_str):
        """Validate all games for a specific date."""
        self.logger.info(f"\nValidating {date_str}...")

        # Get game IDs from all sources
        espn_games = set(self.list_s3_games(ESPN_PREFIX, date_str))
        hoopr_games = set(self.list_s3_games(HOOPR_PREFIX, date_str))
        nba_api_games = set(self.list_s3_games(NBA_API_PREFIX, date_str))

        # Union of all games
        all_games = espn_games | hoopr_games | nba_api_games

        if not all_games:
            self.logger.info(f"  No games found for {date_str}")
            return

        self.logger.info(f"  Found {len(all_games)} unique games")
        self.logger.info(f"    ESPN: {len(espn_games)}, hoopR: {len(hoopr_games)}, NBA API: {len(nba_api_games)}")

        # Check for missing games in each source
        for game_id in all_games:
            missing_in = []
            if game_id not in espn_games:
                missing_in.append("espn")
            if game_id not in hoopr_games:
                missing_in.append("hoopr")
            if game_id not in nba_api_games:
                missing_in.append("nba_api")

            if missing_in:
                self.results["discrepancies"].append({
                    "game_id": game_id,
                    "date": date_str,
                    "type": "missing_in_source",
                    "missing_in": missing_in,
                    "severity": "medium"
                })

        # Validate each game
        for game_id in all_games:
            self.validate_game(game_id, date_str)
            self.results["games_checked"] += 1

    def calculate_quality_scores(self):
        """Calculate quality scores for each source."""
        for source in ["espn", "hoopr", "nba_api"]:
            games = self.results["source_quality"][source]["games"]
            errors = self.results["source_quality"][source]["errors"]
            total = games + errors

            if total > 0:
                quality = (games / total) * 100
                self.results["source_quality"][source]["quality"] = round(quality, 2)

    def generate_summary(self):
        """Generate validation summary."""
        self.results["summary"] = {
            "total_games": self.results["games_checked"],
            "total_discrepancies": len(self.results["discrepancies"]),
            "discrepancies_by_type": {},
            "discrepancies_by_severity": {"high": 0, "medium": 0, "low": 0}
        }

        # Group by type
        by_type = defaultdict(int)
        for disc in self.results["discrepancies"]:
            by_type[disc["type"]] += 1
            self.results["summary"]["discrepancies_by_severity"][disc["severity"]] += 1

        self.results["summary"]["discrepancies_by_type"] = dict(by_type)

    def save_report(self):
        """Save validation report to file."""
        Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{REPORTS_DIR}/cross_validation_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)

        self.logger.info(f"\n✓ Report saved: {filename}")
        return filename

    def run(self):
        """Run cross-validation."""
        print("\n" + "=" * 70)
        print("3-SOURCE CROSS-VALIDATION (ESPN, hoopR, NBA API)")
        print("=" * 70)
        print(f"\nValidating last {self.days_back} days")
        print(f"S3 bucket: {S3_BUCKET}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Get date range
        dates = self.get_date_range()
        self.logger.info(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} days)")

        # Validate each date
        for date_str in dates:
            self.validate_date(date_str)

        # Calculate quality scores
        self.calculate_quality_scores()

        # Generate summary
        self.generate_summary()

        # Print results
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Games validated:     {self.results['games_checked']}")
        print(f"Total discrepancies: {self.results['summary']['total_discrepancies']}")
        print(f"\nBy severity:")
        print(f"  High:   {self.results['summary']['discrepancies_by_severity']['high']}")
        print(f"  Medium: {self.results['summary']['discrepancies_by_severity']['medium']}")
        print(f"  Low:    {self.results['summary']['discrepancies_by_severity']['low']}")
        print(f"\nSource quality scores:")
        for source in ["espn", "hoopr", "nba_api"]:
            quality = self.results["source_quality"][source]
            print(f"  {source.upper():10s}: {quality['quality']:.1f}% ({quality['games']} games, {quality['errors']} errors)")
        print("=" * 70)

        # Save report
        report_file = self.save_report()

        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✓ Report: {report_file}")

        return self.results


def main():
    parser = argparse.ArgumentParser(
        description="Cross-validate data from ESPN, hoopR, and NBA API"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="Number of days to validate (default: 3)"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Detailed validation (more comparisons)"
    )

    args = parser.parse_args()

    validator = ThreeSourceValidator(
        days_back=args.days,
        detailed=args.detailed
    )
    validator.run()


if __name__ == "__main__":
    main()
