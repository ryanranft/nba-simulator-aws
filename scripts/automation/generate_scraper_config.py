#!/usr/bin/env python3
"""
Scraper Configuration Generator

Generates scraper_config.yaml entries for migrated scrapers.

Determines appropriate rate limits, timeouts, and settings based on data source.

Usage:
    python scripts/automation/generate_scraper_config.py analyze_data_coverage --source utility --port 8020

Version: 1.0
Created: October 22, 2025
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional
import yaml


class ScraperConfigGenerator:
    """Generate scraper configuration"""

    # Default rate limits per source (requests per second)
    SOURCE_RATE_LIMITS = {
        "espn": 0.5,  # 2s between requests
        "basketball_reference": 0.083,  # 12s between requests
        "nba_api": 0.67,  # 1.5s between requests
        "hoopr": 1.67,  # 0.6s between requests
        "utility": 0.0,  # No rate limit for utilities
    }

    # Base URLs per source
    SOURCE_BASE_URLS = {
        "espn": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
        "basketball_reference": "https://www.basketball-reference.com",
        "nba_api": "https://stats.nba.com",
        "hoopr": "https://api.collegefootballdata.com",  # hoopR uses multiple APIs
        "utility": "",
    }

    # Timeouts per source (seconds)
    SOURCE_TIMEOUTS = {
        "espn": 30,
        "basketball_reference": 45,
        "nba_api": 20,
        "hoopr": 30,
        "utility": 60,
    }

    def __init__(
        self,
        config_name: str,
        source: str,
        port: int,
        pattern_info: Optional[Dict] = None,
    ):
        self.config_name = config_name
        self.source = source
        self.port = port
        self.pattern_info = pattern_info or {}

    def _detect_source(self, file_name: str) -> str:
        """Detect data source from file name"""
        file_lower = file_name.lower()
        if "espn" in file_lower:
            return "espn"
        elif "basketball_reference" in file_lower or "bref" in file_lower:
            return "basketball_reference"
        elif "nba_api" in file_lower:
            return "nba_api"
        elif "hoopr" in file_lower:
            return "hoopr"
        else:
            return "utility"

    def generate(self) -> Dict:
        """Generate configuration dictionary"""
        # Get source defaults
        rate_limit = self.SOURCE_RATE_LIMITS.get(self.source, 1.0)
        base_url = self.SOURCE_BASE_URLS.get(self.source, "")
        timeout = self.SOURCE_TIMEOUTS.get(self.source, 30)

        # Override from pattern info if available
        if self.pattern_info.get("rate_limit"):
            rate_limit = self.pattern_info["rate_limit"]
        if self.pattern_info.get("base_url"):
            base_url = self.pattern_info["base_url"]

        # Build config
        config = {
            "base_url": base_url,
            "rate_limit": {
                "requests_per_second": rate_limit,
                "burst_size": max(5, int(rate_limit * 10)),
                "adaptive": True,
                "retry_after_header": True,
            },
            "retry": {
                "max_attempts": 5 if self.source == "basketball_reference" else 3,
                "base_delay": 2.0 if self.source == "basketball_reference" else 1.0,
                "max_delay": 120.0 if self.source == "basketball_reference" else 60.0,
                "exponential_backoff": True,
                "jitter": True,
            },
            "timeout": timeout,
            "user_agent": "NBA-Simulator-Scraper/1.0",
            "max_concurrent": self._get_max_concurrent(),
            "storage": {
                "s3_bucket": "nba-sim-raw-data-lake",
                "local_output_dir": f"/tmp/scraper_output/{self.config_name}",  # nosec B108 - config template only, actual dir created by scraper
                "upload_to_s3": True,
                "compression": False,
                "deduplication": True,
            },
            "monitoring": {
                "enable_telemetry": True,
                "log_level": "INFO",
                "log_file": None,
                "metrics_port": self.port,
                "health_check_interval": 60,
                "alert_thresholds": {},
            },
            "custom_settings": {},
        }

        return config

    def _get_max_concurrent(self) -> int:
        """Get max concurrent requests based on source"""
        concurrent_map = {
            "espn": 10,
            "basketball_reference": 1,  # Very conservative
            "nba_api": 15,
            "hoopr": 5,
            "utility": 1,
        }
        return concurrent_map.get(self.source, 5)

    def generate_yaml(self) -> str:
        """Generate YAML string"""
        config = self.generate()

        # Create wrapper dict with config name
        wrapper = {self.config_name: config}

        # Generate YAML
        yaml_str = yaml.dump(wrapper, default_flow_style=False, sort_keys=False)

        return yaml_str

    def append_to_config_file(self, config_file: Path) -> bool:
        """
        Append configuration to existing scraper_config.yaml

        Returns:
            True if successful, False if config name already exists
        """
        # Read existing config
        if config_file.exists():
            with open(config_file) as f:
                existing_config = yaml.safe_load(f) or {}
        else:
            existing_config = {"scrapers": {}}

        # Check if config name already exists
        if "scrapers" in existing_config:
            if self.config_name in existing_config["scrapers"]:
                print(
                    f"Warning: Config '{self.config_name}' already exists",
                    file=sys.stderr,
                )
                return False

        # Add new config
        if "scrapers" not in existing_config:
            existing_config["scrapers"] = {}

        existing_config["scrapers"][self.config_name] = self.generate()

        # Write back
        with open(config_file, "w") as f:
            yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate scraper configuration for scraper_config.yaml"
    )
    parser.add_argument(
        "config_name", help="Configuration name (e.g., 'analyze_data_coverage')"
    )
    parser.add_argument(
        "--source",
        choices=["espn", "basketball_reference", "nba_api", "hoopr", "utility"],
        help="Data source (auto-detected if not specified)",
    )
    parser.add_argument(
        "--port", type=int, default=8020, help="Telemetry port (default: 8020)"
    )
    parser.add_argument("--pattern-info", help="Path to JSON file with pattern info")
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: print to stdout)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to config/scraper_config.yaml",
    )

    args = parser.parse_args()

    # Load pattern info if provided
    pattern_info = None
    if args.pattern_info:
        import json

        with open(args.pattern_info) as f:
            pattern_info = json.load(f)

    # Auto-detect source if not specified
    source = args.source
    if not source:
        generator = ScraperConfigGenerator("dummy", "utility", 8000)
        source = generator._detect_source(args.config_name)
        print(f"Auto-detected source: {source}", file=sys.stderr)

    # Generate config
    generator = ScraperConfigGenerator(
        args.config_name, source, args.port, pattern_info
    )

    # Output
    if args.append:
        config_file = Path("config/scraper_config.yaml")
        if generator.append_to_config_file(config_file):
            print(f"Appended config '{args.config_name}' to {config_file}")
        else:
            print(f"Failed to append config '{args.config_name}'", file=sys.stderr)
            sys.exit(1)
    elif args.output:
        yaml_str = generator.generate_yaml()
        Path(args.output).write_text(yaml_str)
        print(f"Generated config: {args.output}")
    else:
        # Print to stdout
        yaml_str = generator.generate_yaml()
        print(yaml_str)


if __name__ == "__main__":
    main()
