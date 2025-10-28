"""
ESPN Play-by-Play Extractor

Extracts play-by-play data from ESPN API.

Secondary data source (used for validation and gap-filling).
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class ESPNPlayByPlayExtractor(BaseExtractor):
    """
    ESPN play-by-play data extractor.
    
    Secondary data source for validation and gap-filling.
    
    Supports multiple extraction modes:
    - Async (fast, parallel extraction)
    - Incremental (new games only)
    - Simple incremental (simplified logic)
    - Missing games (gap-filling)
    
    Usage:
        extractor = ESPNPlayByPlayExtractor()
        result = extractor.extract(season="2024", mode="incremental")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ESPN play-by-play extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent
        
        self.legacy_scripts = {
            'async': project_root / "scripts/etl/espn_async_scraper.py",
            'incremental': project_root / "scripts/etl/espn_incremental_scraper.py",
            'simple': project_root / "scripts/etl/espn_incremental_simple.py",
            'missing': project_root / "scripts/etl/espn_missing_pbp_scraper.py",
            'extract': project_root / "scripts/etl/extract_pbp_local.py",
        }
        
        # Default to incremental (safest)
        legacy_script = self.legacy_scripts.get('incremental')
        
        super().__init__(
            name="espn_play_by_play",
            legacy_script=str(legacy_script) if legacy_script else None,
            config=config,
            max_retries=3,
            rate_limit_delay=1.0  # ESPN rate limiting
        )
    
    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False,
        mode: str = "incremental"
    ) -> Dict[str, Any]:
        """
        Extract play-by-play data from ESPN.
        
        Args:
            season: NBA season (e.g., "2024")
            game_id: Specific game ID to extract
            force: Force re-extraction
            mode: Extraction mode ('async', 'incremental', 'simple', 'missing', 'extract')
        
        Returns:
            Dictionary with extraction results
        """
        self.logger.info(
            f"Extracting ESPN PBP data (season={season}, "
            f"game_id={game_id}, force={force}, mode={mode})"
        )
        
        # Build arguments
        args = []
        if season:
            args.extend(["--season", season])
        if game_id:
            args.extend(["--game-id", game_id])
        if force:
            args.append("--force")
        
        # Select script based on mode
        if mode in self.legacy_scripts:
            self.legacy_script = self.legacy_scripts[mode]
        
        try:
            result = self.run_with_retry(
                self.call_legacy_script,
                args=args,
                timeout=7200  # 2 hour timeout
            )
            
            return {
                'status': 'success',
                'mode': mode,
                'season': season,
                'game_id': game_id,
                'stdout': result.stdout[:500],
                'exit_code': result.returncode
            }
        
        except Exception as e:
            self.logger.error(f"ESPN PBP extraction failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extraction results"""
        if not isinstance(data, dict):
            return False
        return data.get('status') == 'success'
    
    def health_check(self) -> Dict[str, Any]:
        """Check extractor health"""
        health = super().health_check()
        
        scripts_available = {}
        for name, path in self.legacy_scripts.items():
            scripts_available[name] = path.exists()
        
        health['legacy_scripts'] = scripts_available
        health['data_source'] = 'ESPN API'
        health['purpose'] = 'Validation and gap-filling'
        
        return health

