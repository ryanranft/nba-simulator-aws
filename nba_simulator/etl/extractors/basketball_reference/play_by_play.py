"""
Basketball Reference Play-by-Play Extractor

Extracts play-by-play data from Basketball Reference.

Historical data source for comprehensive coverage.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class BasketballReferencePlayByPlayExtractor(BaseExtractor):
    """
    Basketball Reference play-by-play data extractor.
    
    Historical data source with comprehensive coverage.
    
    Supports multiple extraction modes:
    - async - Fast parallel extraction
    - incremental - New games only
    - comprehensive - Complete historical extraction
    - daily - Daily incremental updates
    - backfill - Fill historical gaps
    - discovery - Discover available games
    
    Usage:
        extractor = BasketballReferencePlayByPlayExtractor()
        result = extractor.extract(season="2024", mode="incremental")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Basketball Reference play-by-play extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent
        
        self.legacy_scripts = {
            'async': project_root / "scripts/etl/basketball_reference_async_scraper.py",
            'incremental': project_root / "scripts/etl/basketball_reference_incremental_scraper.py",
            'comprehensive': project_root / "scripts/etl/basketball_reference_comprehensive_scraper.py",
            'daily': project_root / "scripts/etl/basketball_reference_daily_pbp.py",
            'backfill': project_root / "scripts/etl/basketball_reference_pbp_backfill.py",
            'discovery': project_root / "scripts/etl/basketball_reference_pbp_discovery.py",
        }
        
        # Default to incremental
        legacy_script = self.legacy_scripts.get('incremental')
        
        super().__init__(
            name="basketball_reference_play_by_play",
            legacy_script=str(legacy_script) if legacy_script else None,
            config=config,
            max_retries=3,
            rate_limit_delay=3.0  # BBRef needs slower rate limiting
        )
    
    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False,
        mode: str = "incremental"
    ) -> Dict[str, Any]:
        """
        Extract play-by-play data from Basketball Reference.
        
        Args:
            season: NBA season (e.g., "2024")
            game_id: Specific game ID to extract
            force: Force re-extraction
            mode: Extraction mode ('async', 'incremental', 'comprehensive', 
                  'daily', 'backfill', 'discovery')
        
        Returns:
            Dictionary with extraction results
        """
        self.logger.info(
            f"Extracting Basketball Reference PBP data (season={season}, "
            f"game_id={game_id}, force={force}, mode={mode})"
        )
        
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
                timeout=10800  # 3 hour timeout (BBRef is slow)
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
            self.logger.error(f"Basketball Reference PBP extraction failed: {e}")
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
        health['data_source'] = 'Basketball Reference'
        health['purpose'] = 'Historical data and comprehensive coverage'
        health['rate_limit_note'] = 'Slower rate limiting (3s) to respect BBRef'
        
        return health

