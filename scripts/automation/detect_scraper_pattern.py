#!/usr/bin/env python3
"""
Scraper Pattern Detection Analyzer

Analyzes NBA scraper source code to determine the appropriate migration pattern.

Patterns:
1. Primary Async - Full async HTTP scraping (aiohttp, asyncio)
2. Incremental - Delta updates since last run (state tracking)
3. Specialized Task - Specific endpoint/task scraper
4. Autonomous Agent - Multi-phase workflow with checkpoints
5. Utility Script - Data processing/analysis (no HTTP scraping)

Usage:
    python scripts/automation/detect_scraper_pattern.py scripts/etl/analyze_data_coverage.py

Version: 1.0
Created: October 22, 2025
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


class ScraperPatternDetector:
    """Detect scraper migration pattern from source code"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = self.file_path.read_text()
        self.lines = self.content.split("\n")
        self.imports = self._extract_imports()
        self.classes = self._extract_classes()
        self.functions = self._extract_functions()
        self.keywords = self._extract_keywords()

    def _extract_imports(self) -> Set[str]:
        """Extract all import statements"""
        imports = set()
        for line in self.lines:
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                # Extract module name
                if line.startswith("import "):
                    module = line.split()[1].split(".")[0]
                else:
                    module = line.split()[1].split(".")[0]
                imports.add(module)
        return imports

    def _extract_classes(self) -> List[str]:
        """Extract class names"""
        classes = []
        for line in self.lines:
            line = line.strip()
            if line.startswith("class "):
                match = re.match(r"class\s+(\w+)", line)
                if match:
                    classes.append(match.group(1))
        return classes

    def _extract_functions(self) -> List[str]:
        """Extract function/method names"""
        functions = []
        for line in self.lines:
            line = line.strip()
            if line.startswith("def ") or line.startswith("async def "):
                match = re.match(r"(?:async\s+)?def\s+(\w+)", line)
                if match:
                    functions.append(match.group(1))
        return functions

    def _extract_keywords(self) -> Set[str]:
        """Extract key terms from content (lowercase)"""
        # Remove comments and strings
        content_lower = self.content.lower()
        keywords = set(re.findall(r"\b\w+\b", content_lower))
        return keywords

    def detect_pattern(self) -> str:
        """
        Detect the scraper pattern

        Returns:
            Pattern name: 'async', 'incremental', 'specialized', 'agent', or 'utility'
        """
        # Check each pattern in order of specificity

        # Pattern 4: Autonomous Agent (most specific)
        if self._is_agent():
            return "agent"

        # Pattern 1: Primary Async
        if self._is_primary_async():
            return "async"

        # Pattern 2: Incremental
        if self._is_incremental():
            return "incremental"

        # Pattern 3: Specialized Task
        if self._is_specialized():
            return "specialized"

        # Pattern 5: Utility (fallback)
        return "utility"

    def _is_primary_async(self) -> bool:
        """Check if primary async scraper"""
        has_async = "async def" in self.content
        has_http = "aiohttp" in self.imports or "asyncio" in self.imports
        has_class = len(self.classes) > 0
        has_scrape = "scrape" in self.keywords

        return has_async and has_http and has_class and has_scrape

    def _is_incremental(self) -> bool:
        """Check if incremental scraper"""
        # Look for state tracking patterns
        state_patterns = [
            "last_run",
            "last_updated",
            "since",
            "delta",
            "checkpoint",
        ]
        has_state = any(pattern in self.keywords for pattern in state_patterns)

        # Look for database queries for "latest"
        has_max_query = (
            "select max" in self.content.lower() or "order by" in self.content.lower()
        )

        # Look for date/time tracking
        has_datetime = "datetime" in self.imports or "date" in self.keywords

        return has_state and (has_max_query or has_datetime)

    def _is_specialized(self) -> bool:
        """Check if specialized task scraper"""
        # Uses synchronous HTTP libraries
        has_requests = "requests" in self.imports
        has_parsing = "BeautifulSoup" in self.content or "json" in self.imports

        # Focused scope (fewer functions)
        is_focused = len(self.functions) < 15

        # Has scraping functionality
        has_scrape = "scrape" in self.keywords

        return has_requests and has_parsing and is_focused and has_scrape

    def _is_agent(self) -> bool:
        """Check if autonomous agent"""
        # Multi-phase workflow
        has_phases = "phase" in self.keywords or "stage" in self.keywords

        # State persistence
        has_state = "checkpoint" in self.keywords or "resume" in self.keywords

        # Complex orchestration (multiple classes)
        is_complex = len(self.classes) > 2

        return has_phases and has_state and is_complex

    def get_pattern_info(self) -> Dict:
        """
        Get detailed pattern information

        Returns:
            Dict with pattern name and extracted components
        """
        pattern = self.detect_pattern()

        info = {
            "pattern": pattern,
            "file_path": str(self.file_path),
            "file_name": self.file_path.name,
            "imports": list(self.imports),
            "classes": self.classes,
            "functions": self.functions[:20],  # Limit to first 20
            "line_count": len(self.lines),
            "has_async": "async def" in self.content,
            "has_requests": "requests" in self.imports,
            "has_aiohttp": "aiohttp" in self.imports,
            "has_database": "sqlite3" in self.imports or "psycopg2" in self.imports,
            "has_s3": "boto3" in self.imports,
        }

        # Extract scraper-specific info
        if pattern == "async":
            info["rate_limit"] = self._extract_rate_limit()
            info["base_url"] = self._extract_base_url()

        elif pattern == "incremental":
            info["rate_limit"] = self._extract_rate_limit()
            info["base_url"] = self._extract_base_url()
            info["db_path"] = self._extract_db_path()

        elif pattern == "specialized":
            info["rate_limit"] = self._extract_rate_limit()
            info["base_url"] = self._extract_base_url()

        elif pattern == "agent":
            info["phases"] = self._extract_phases()

        return info

    def _extract_rate_limit(self) -> Optional[float]:
        """Extract rate limit from code (seconds between requests)"""
        # Look for sleep() calls
        sleep_pattern = r"(?:time\.sleep|asyncio\.sleep)\((\d+(?:\.\d+)?)\)"
        matches = re.findall(sleep_pattern, self.content)
        if matches:
            return float(matches[0])

        # Look for rate_limit variables
        rate_pattern = r"rate_limit\s*=\s*(\d+(?:\.\d+)?)"
        matches = re.findall(rate_pattern, self.content)
        if matches:
            return float(matches[0])

        return None

    def _extract_base_url(self) -> Optional[str]:
        """Extract base URL from code"""
        # Look for URL patterns
        url_pattern = r'["\']https?://[^"\']+["\']'
        matches = re.findall(url_pattern, self.content)
        if matches:
            # Return first URL (likely base URL)
            return matches[0].strip('"').strip("'")
        return None

    def _extract_db_path(self) -> Optional[str]:
        """Extract database path"""
        db_pattern = r'["\']([^"\']*\.(?:db|sqlite3?))["\']'
        matches = re.findall(db_pattern, self.content)
        if matches:
            return matches[0]
        return None

    def _extract_phases(self) -> List[str]:
        """Extract phase names from agent code"""
        phases = []

        # Look for phase comments
        phase_pattern = r"#\s*(?:Phase|PHASE)\s*(\d+):?\s*([^\n]+)"
        matches = re.findall(phase_pattern, self.content)
        for num, desc in matches:
            phases.append(f"Phase {num}: {desc.strip()}")

        return phases


def main():
    parser = argparse.ArgumentParser(
        description="Detect scraper migration pattern from source code"
    )
    parser.add_argument("file_path", help="Path to scraper file")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed info"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Check file exists
    if not Path(args.file_path).exists():
        print(f"ERROR: File not found: {args.file_path}", file=sys.stderr)
        sys.exit(1)

    # Detect pattern
    detector = ScraperPatternDetector(args.file_path)
    info = detector.get_pattern_info()

    # Output
    if args.json:
        import json

        print(json.dumps(info, indent=2))
    elif args.verbose:
        print(f"File: {info['file_name']}")
        print(f"Pattern: {info['pattern']}")
        print(f"Line Count: {info['line_count']}")
        print(f"\nClasses ({len(info['classes'])}):")
        for cls in info["classes"]:
            print(f"  - {cls}")
        print(f"\nImports ({len(info['imports'])}):")
        for imp in sorted(info["imports"])[:10]:
            print(f"  - {imp}")
        print(f"\nFunctions ({len(info['functions'])}):")
        for func in info["functions"][:10]:
            print(f"  - {func}")
        if info.get("rate_limit"):
            print(f"\nRate Limit: {info['rate_limit']}s")
        if info.get("base_url"):
            print(f"Base URL: {info['base_url']}")
    else:
        # Simple output
        print(info["pattern"])


if __name__ == "__main__":
    main()
