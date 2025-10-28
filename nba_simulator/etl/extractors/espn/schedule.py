"""
ESPN Schedule Extractor

Extracts schedule data from ESPN.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class ESPNScheduleExtractor(BaseExtractor):
    """
    ESPN schedule extractor.
    
    Extracts game schedule data from ESPN.
    
    Usage:
        extractor = ESPNScheduleExtractor()
        result = extractor.extract(season="2024")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ESPN schedule extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent
        legacy_script = project_root / "scripts/etl/extract_schedule_local.py"
        
        super().__init__(
            name="espn_schedule",
            legacy_script=str(legacy_script),
            config=config,
            max_retries=3,
            rate_limit_delay=1.0
        )
    
    def extract(
        self,
        season: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Extract schedule from ESPN.
        
        Args:
            season: NBA season
            force: Force re-extraction
        
        Returns:
            Extraction results
        """
        self.logger.info(f"Extracting ESPN schedule (season={season})")
        
        args = []
        if season:
            args.extend(["--season", season])
        if force:
            args.append("--force")
        
        try:
            result = self.run_with_retry(
                self.call_legacy_script,
                args=args,
                timeout=1800  # 30 min timeout
            )
            
            return {
                'status': 'success',
                'season': season,
                'stdout': result.stdout[:500],
                'exit_code': result.returncode
            }
        
        except Exception as e:
            self.logger.error(f"ESPN schedule extraction failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extraction results"""
        if not isinstance(data, dict):
            return False
        return data.get('status') == 'success'

