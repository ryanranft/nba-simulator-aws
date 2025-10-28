"""
Base Extractor Class

Specialized scraper for data extraction with legacy script wrapping capability.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, List
from .scraper import BaseScraper


class BaseExtractor(BaseScraper):
    """
    Base class for data extractors.
    
    Extends BaseScraper with legacy script wrapping capability.
    Allows new extractors to call existing scripts during migration.
    
    Usage:
        class HooprExtractor(BaseExtractor):
            def __init__(self):
                super().__init__(
                    "hoopr",
                    legacy_script="scripts/etl/hoopr_scraper.py"
                )
            
            def extract(self, season):
                return self.call_legacy_script(["--season", season])
    """
    
    def __init__(
        self,
        name: str,
        legacy_script: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize extractor.
        
        Args:
            name: Extractor name
            legacy_script: Path to legacy script (for gradual migration)
            **kwargs: Additional arguments for BaseScraper
        """
        self.legacy_script = Path(legacy_script) if legacy_script else None
        super().__init__(name, **kwargs)
    
    def call_legacy_script(
        self,
        args: Optional[List[str]] = None,
        timeout: int = 3600
    ) -> subprocess.CompletedProcess:
        """
        Call legacy script with arguments.
        
        Args:
            args: Command line arguments for script
            timeout: Timeout in seconds (default: 1 hour)
        
        Returns:
            CompletedProcess with script output
        
        Raises:
            FileNotFoundError: If legacy script doesn't exist
            RuntimeError: If script execution fails
        """
        if not self.legacy_script:
            raise ValueError(f"{self.name}: No legacy script configured")
        
        if not self.legacy_script.exists():
            raise FileNotFoundError(
                f"{self.name}: Legacy script not found: {self.legacy_script}"
            )
        
        cmd = [sys.executable, str(self.legacy_script)]
        if args:
            cmd.extend(args)
        
        self.logger.info(f"{self.name}: Calling legacy script: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise on non-zero exit
            )
            
            if result.returncode != 0:
                self.logger.error(
                    f"{self.name}: Legacy script failed (exit {result.returncode}): "
                    f"{result.stderr[:500]}"
                )
                raise RuntimeError(f"Legacy script failed: {result.stderr[:200]}")
            
            self.logger.info(f"{self.name}: Legacy script completed successfully")
            return result
        
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"{self.name}: Legacy script timed out after {timeout}s")
            raise RuntimeError(f"Legacy script timed out") from e
    
    def validate(self, data: Any) -> bool:
        """
        Default validation implementation.
        Override in subclasses for specific validation.
        
        Args:
            data: Data to validate
        
        Returns:
            True if data is not None/empty
        """
        if data is None:
            self.logger.warning(f"{self.name}: Validation failed - data is None")
            return False
        
        if isinstance(data, (list, dict, str)) and len(data) == 0:
            self.logger.warning(f"{self.name}: Validation failed - data is empty")
            return False
        
        return True

