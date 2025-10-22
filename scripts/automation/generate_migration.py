#!/usr/bin/env python3
"""
Scraper Migration Code Generator

Generates AsyncBaseScraper-compatible code based on detected pattern.

Supports 5 migration patterns:
1. Primary Async - Full async migration
2. Incremental - Add state tracking
3. Specialized Task - Simple task scraper
4. Autonomous Agent - Manual review notice
5. Utility Script - Config adoption only

Usage:
    python scripts/automation/generate_migration.py scripts/etl/analyze_data_coverage.py --pattern utility

Version: 1.0
Created: October 22, 2025
"""

import argparse
import sys
from pathlib import Path
from typing import Dict
import re


class MigrationCodeGenerator:
    """Generate migration code based on pattern"""

    def __init__(self, file_path: str, pattern_info: Dict, preserve: bool = False):
        self.file_path = Path(file_path)
        self.pattern_info = pattern_info
        self.pattern = pattern_info["pattern"]
        self.file_name = self.file_path.name
        self.scraper_name = self.file_name.replace(".py", "")
        self.config_name = self._generate_config_name()
        self.preserve = preserve

        # Read original content
        self.original_content = self.file_path.read_text()
        self.original_lines = self.original_content.split("\n")

    def _generate_config_name(self) -> str:
        """Generate config name for scraper_config.yaml"""
        # Remove common prefixes/suffixes
        name = self.scraper_name
        name = name.replace("scraper", "").replace("_scraper", "")
        name = name.replace("script", "").replace("_script", "")
        name = name.strip("_")
        return name

    def _extract_class_name(self) -> str:
        """Extract or generate class name"""
        if self.pattern_info.get("classes"):
            return self.pattern_info["classes"][0]

        # Generate from file name
        parts = self.scraper_name.split("_")
        return "".join(word.capitalize() for word in parts)

    def _extract_docstring(self) -> str:
        """Extract module docstring from original file"""
        # Find first triple-quoted string
        match = re.search(r'"""([^"]*)"""', self.original_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return f"{self.scraper_name} - Migrated to AsyncBaseScraper"

    def generate(self) -> str:
        """Generate migration code based on pattern"""
        # Use preserve mode if requested
        if self.preserve:
            return self._generate_preserve_migration()

        generators = {
            "async": self._generate_async_migration,
            "incremental": self._generate_incremental_migration,
            "specialized": self._generate_specialized_migration,
            "agent": self._generate_agent_migration,
            "utility": self._generate_utility_migration,
        }

        generator = generators.get(self.pattern)
        if not generator:
            raise ValueError(f"Unknown pattern: {self.pattern}")

        return generator()

    def _generate_preserve_migration(self) -> str:
        """
        Generate migration that preserves original code

        Adds AsyncBaseScraper integration without destroying original logic
        """
        lines = self.original_lines.copy()

        # Skip if utility (utilities don't need migration)
        if self.pattern == "utility":
            return self.original_content

        # Skip if agent (too complex)
        if self.pattern == "agent":
            return self.original_content

        # Find docstring end
        docstring_end = self._find_docstring_end(lines)

        # Add migration note to docstring
        if docstring_end > 0:
            lines.insert(docstring_end, "")
            lines.insert(docstring_end + 1, "Migrated to AsyncBaseScraper framework.")
            lines.insert(
                docstring_end + 2,
                f"Version: 2.0 (AsyncBaseScraper Integration - Preserve Mode)",
            )
            lines.insert(docstring_end + 3, f"Migrated: {self._get_date()}")

        # Find first import line
        first_import = self._find_first_import(lines)

        # Add AsyncBaseScraper imports after docstring, before first import
        insert_pos = max(docstring_end + 5, first_import)
        lines.insert(insert_pos, "")
        lines.insert(insert_pos + 1, "# TODO: AsyncBaseScraper Integration")
        lines.insert(
            insert_pos + 2, "# 1. Make your main class inherit from AsyncBaseScraper"
        )
        lines.insert(insert_pos + 3, "# 2. Add config_name parameter to __init__")
        lines.insert(
            insert_pos + 4, "# 3. Call super().__init__(config_name=config_name)"
        )
        lines.insert(
            insert_pos + 5, "# 4. Wrap synchronous HTTP calls in asyncio.to_thread()"
        )
        lines.insert(
            insert_pos + 6, "# 5. Use self.rate_limiter.acquire() before requests"
        )
        lines.insert(insert_pos + 7, "# 6. Use self.store_data() for S3 uploads")
        lines.insert(insert_pos + 8, "#")
        lines.insert(insert_pos + 9, "# Uncomment these imports when ready:")
        lines.insert(insert_pos + 10, "# import sys")
        lines.insert(insert_pos + 11, "# from pathlib import Path")
        lines.insert(
            insert_pos + 12,
            "# sys.path.insert(0, str(Path(__file__).parent.parent.parent))",
        )
        lines.insert(
            insert_pos + 13,
            "# from scripts.etl.async_scraper_base import AsyncBaseScraper",
        )
        lines.insert(insert_pos + 14, "")

        # Find main class (if exists)
        class_line = self._find_main_class(lines)
        if class_line >= 0:
            lines.insert(class_line + 1, "")
            lines.insert(
                class_line + 2, "    # TODO: After inheriting from AsyncBaseScraper:"
            )
            lines.insert(
                class_line + 3, "    # - Add config_name parameter to __init__"
            )
            lines.insert(
                class_line + 4,
                "    # - Call super().__init__(config_name='{}')".format(
                    self.config_name
                ),
            )
            lines.insert(class_line + 5, "")

        return "\n".join(lines)

    def _find_docstring_end(self, lines) -> int:
        """Find the line number where module docstring ends"""
        in_docstring = False
        quote_count = 0

        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                quote_count += line.count('"""') + line.count("'''")
                if quote_count >= 2:
                    return i
        return 0

    def _find_first_import(self, lines) -> int:
        """Find the first import statement"""
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                return i
        return 0

    def _find_main_class(self, lines) -> int:
        """Find the main class definition"""
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("class "):
                # Skip if it's AsyncBaseScraper itself or config manager
                if "AsyncBaseScraper" in stripped or "ConfigManager" in stripped:
                    continue
                return i
        return -1

    def _generate_async_migration(self) -> str:
        """Generate primary async migration"""
        class_name = self._extract_class_name()
        docstring = self._extract_docstring()

        return f'''#!/usr/bin/env python3
"""
{docstring}

Migrated to AsyncBaseScraper framework.

Version: 2.0 (AsyncBaseScraper Integration)
Migrated: {self._get_date()}
"""

import asyncio
import sys
from pathlib import Path

# Import AsyncBaseScraper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager


class {class_name}(AsyncBaseScraper):
    """Migrated {self.scraper_name}"""

    def __init__(self, config_name="{self.config_name}"):
        """Initialize scraper"""
        super().__init__(config_name=config_name)

        # TODO: Add custom initialization from original scraper

    async def scrape(self):
        """Main scraping method"""
        # TODO: Migrate original scraping logic here
        # Use self.fetch_url() for HTTP requests
        # Use self.rate_limiter.acquire() before each request
        # Use self.store_data() for S3 uploads
        pass


async def main():
    """Main entry point"""
    async with {class_name}() as scraper:
        await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())
'''

    def _generate_incremental_migration(self) -> str:  # nosec B608
        """Generate incremental migration"""
        class_name = self._extract_class_name()
        docstring = self._extract_docstring()
        db_path = self.pattern_info.get("db_path", "data/scraper_state.db")

        # Template contains SQL examples for educational purposes only
        return f'''#!/usr/bin/env python3  # nosec B608
"""
{docstring}

Incremental scraper - Migrated to AsyncBaseScraper framework.

Version: 2.0 (AsyncBaseScraper Integration)
Migrated: {self._get_date()}
"""

import asyncio
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import AsyncBaseScraper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper


class {class_name}(AsyncBaseScraper):
    """Incremental scraper - Migrated"""

    def __init__(self, days_back=7, config_name="{self.config_name}"):
        """Initialize incremental scraper"""
        super().__init__(config_name=config_name)
        self.days_back = days_back
        self.db_path = "{db_path}"

    async def get_last_run_date(self):
        """Get last successful run date from database"""
        return await asyncio.to_thread(self._get_last_run_date_sync)

    def _get_last_run_date_sync(self):
        """Synchronous database query"""
        # TODO: Migrate database query from original scraper
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Example: cursor.execute("SELECT MAX(game_date) FROM games")  # nosec B608
        # result = cursor.fetchone()[0]
        conn.close()
        return None  # TODO: Return actual result

    async def scrape(self):
        """Main scraping method"""
        # Get last run date
        last_date = await self.get_last_run_date()

        # TODO: Migrate scraping logic here
        # Scrape data since last_date
        # Use self.fetch_url() for HTTP requests
        # Use self.rate_limiter.acquire() before each request
        # Use self.store_data() for S3 uploads
        pass


async def main():
    """Main entry point"""
    async with {class_name}() as scraper:
        await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())
'''

    def _generate_specialized_migration(self) -> str:
        """Generate specialized task migration"""
        class_name = self._extract_class_name()
        docstring = self._extract_docstring()

        return f'''#!/usr/bin/env python3
"""
{docstring}

Specialized task scraper - Migrated to AsyncBaseScraper framework.

Version: 2.0 (AsyncBaseScraper Integration)
Migrated: {self._get_date()}
"""

import asyncio
import requests
import sys
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

# Import AsyncBaseScraper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper


class {class_name}(AsyncBaseScraper):
    """Specialized task scraper - Migrated"""

    def __init__(self, config_name="{self.config_name}"):
        """Initialize scraper"""
        super().__init__(config_name=config_name)

    async def scrape(self):
        """Main scraping method"""
        # Use base class rate limiter
        await self.rate_limiter.acquire()

        # TODO: Migrate HTTP request logic
        # Wrap synchronous requests in asyncio.to_thread
        # Example:
        # response = await asyncio.to_thread(
        #     requests.get,
        #     "URL_HERE",
        #     headers={{'User-Agent': 'NBA Simulator'}}
        # )

        # TODO: Migrate parsing logic
        # soup = await asyncio.to_thread(BeautifulSoup, response.text, 'html.parser')

        # TODO: Parse and store data
        # data = self._parse_data(soup)
        # await self.store_data(data, f"output_{{datetime.now().strftime('%Y%m%d')}}.json")
        pass

    def _parse_data(self, soup):
        """Parse data from soup (synchronous)"""
        # TODO: Migrate parsing logic from original scraper
        return {{}}


async def main():
    """Main entry point"""
    async with {class_name}() as scraper:
        await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())
'''

    def _generate_agent_migration(self) -> str:
        """Generate agent migration notice"""
        class_name = self._extract_class_name()
        docstring = self._extract_docstring()
        phases = self.pattern_info.get("phases", [])

        phases_str = "\n".join(f"- {phase}" for phase in phases)
        if not phases_str:
            phases_str = "- (Phases not automatically detected)"

        return f'''#!/usr/bin/env python3
"""
{docstring}

⚠️ REQUIRES MANUAL REVIEW ⚠️

This autonomous agent has complex multi-phase workflows that need careful migration.

Consider:
1. Extending AsyncBaseScraper as base for HTTP/storage
2. Keeping custom state management
3. Using shared rate limiting
4. Preserving checkpoint recovery logic

Detected Phases:
{phases_str}

Original file: {self.file_path}

Version: 2.0 (Migration Pending)
Flagged: {self._get_date()}
"""

# TODO: Manual migration needed
# This agent has complex orchestration that requires human review

# Suggested approach:
# 1. Inherit from AsyncBaseScraper for HTTP/storage
# 2. Keep custom state management
# 3. Use shared config for rate limits
# 4. Preserve checkpoint recovery
# 5. Test thoroughly with dry runs

# Example skeleton:
"""
from scripts.etl.async_scraper_base import AsyncBaseScraper

class {class_name}(AsyncBaseScraper):
    def __init__(self):
        super().__init__(config_name="{self.config_name}")
        # Custom state management
        self.checkpoint_file = "checkpoints/{self.scraper_name}.json"

    async def run_phase_1(self):
        # Migrate Phase 1 logic
        pass

    async def run_all_phases(self):
        # Orchestrate all phases
        pass
"""
'''

    def _generate_utility_migration(self) -> str:
        """Generate utility script migration (config adoption only)"""
        docstring = self._extract_docstring()

        return f'''#!/usr/bin/env python3
"""
{docstring}

Utility script - Config adoption only (no AsyncBaseScraper inheritance needed).

Version: 2.0 (Config Integration)
Migrated: {self._get_date()}
"""

import sys
from pathlib import Path

# Import config manager
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.etl.scraper_config import ScraperConfigManager


def main():
    """Main entry point"""
    # Load config instead of hardcoded values
    config_manager = ScraperConfigManager()
    config = config_manager.get_scraper_config("{self.config_name}")

    # TODO: Migrate original logic here
    # Use config values instead of hardcoded settings
    # Example:
    # - config.storage.s3_bucket
    # - config.storage.local_output_dir
    # - config.monitoring.log_level

    print(f"Loaded config for: {self.config_name}")
    print(f"Config: {{config}}")


if __name__ == "__main__":
    main()
'''

    def _get_date(self) -> str:
        """Get current date string"""
        from datetime import datetime

        return datetime.now().strftime("%B %d, %Y")


def main():
    parser = argparse.ArgumentParser(
        description="Generate migration code for NBA scraper"
    )
    parser.add_argument("file_path", help="Path to scraper file")
    parser.add_argument(
        "--pattern",
        choices=["async", "incremental", "specialized", "agent", "utility"],
        help="Override detected pattern",
    )
    parser.add_argument("--pattern-info", help="Path to JSON file with pattern info")
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: overwrite original)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print to stdout instead of file"
    )
    parser.add_argument(
        "--preserve",
        action="store_true",
        help="Preserve original code (add TODOs, don't replace)",
    )

    args = parser.parse_args()

    # Check file exists
    if not Path(args.file_path).exists():
        print(f"ERROR: File not found: {args.file_path}", file=sys.stderr)
        sys.exit(1)

    # Get pattern info
    if args.pattern_info:
        import json

        with open(args.pattern_info) as f:
            pattern_info = json.load(f)
    else:
        # Detect pattern
        from detect_scraper_pattern import ScraperPatternDetector

        detector = ScraperPatternDetector(args.file_path)
        pattern_info = detector.get_pattern_info()

    # Override pattern if specified
    if args.pattern:
        pattern_info["pattern"] = args.pattern

    # Generate migration code
    generator = MigrationCodeGenerator(
        args.file_path, pattern_info, preserve=args.preserve
    )
    migrated_code = generator.generate()

    # Output
    if args.dry_run:
        print(migrated_code)
    else:
        output_path = Path(args.output) if args.output else Path(args.file_path)
        output_path.write_text(migrated_code)
        print(f"Generated migration: {output_path}")


if __name__ == "__main__":
    main()
