"""
hoopR Play-by-Play Extractor

Extracts play-by-play data from hoopR (primary data source).

Current: 13,586,471 records in database
Critical: Must maintain temporal_events integration
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class HooprPlayByPlayExtractor(BaseExtractor):
    """
    hoopR play-by-play data extractor.
    
    PRIMARY DATA SOURCE: 13.6M records = 47.5% of database
    
    Current implementation wraps legacy scripts for safety.
    Future versions will implement direct hoopR API access.
    
    Usage:
        extractor = HooprPlayByPlayExtractor()
        result = extractor.extract(season="2024")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize hoopR play-by-play extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        # Identify available legacy scripts
        project_root = Path(__file__).parent.parent.parent.parent.parent
        
        legacy_scripts = {
            'async': project_root / "scripts/etl/hoopr_async_scraper.py",
            'incremental': project_root / "scripts/etl/hoopr_incremental_scraper.py",
            'pbp': project_root / "scripts/etl/hoopr_pbp_scraper.py",
        }
        
        # Use incremental scraper as default (safest for production)
        legacy_script = legacy_scripts.get('incremental')
        
        super().__init__(
            name="hoopr_play_by_play",
            legacy_script=str(legacy_script) if legacy_script else None,
            config=config,
            max_retries=3,
            rate_limit_delay=2.0  # hoopR rate limiting
        )
        
        self.legacy_scripts = legacy_scripts
    
    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False,
        mode: str = "incremental"
    ) -> Dict[str, Any]:
        """
        Extract play-by-play data from hoopR.
        
        Args:
            season: NBA season (e.g., "2024")
            game_id: Specific game ID to extract
            force: Force re-extraction even if data exists
            mode: Extraction mode ('async', 'incremental', 'pbp')
        
        Returns:
            Dictionary with extraction results
        """
        self.logger.info(
            f"Extracting hoopR PBP data (season={season}, "
            f"game_id={game_id}, force={force}, mode={mode})"
        )
        
        # Build arguments for legacy script
        args = []
        if season:
            args.extend(["--season", season])
        if game_id:
            args.extend(["--game-id", game_id])
        if force:
            args.append("--force")
        
        # Select appropriate legacy script
        if mode in self.legacy_scripts:
            self.legacy_script = self.legacy_scripts[mode]
        
        # Call legacy script with retry
        try:
            result = self.run_with_retry(
                self.call_legacy_script,
                args=args,
                timeout=7200  # 2 hour timeout for large extractions
            )
            
            return {
                'status': 'success',
                'mode': mode,
                'season': season,
                'game_id': game_id,
                'stdout': result.stdout[:500],  # First 500 chars
                'exit_code': result.returncode
            }
        
        except Exception as e:
            self.logger.error(f"hoopR PBP extraction failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate extraction results.
        
        Args:
            data: Extraction results dictionary
        
        Returns:
            True if extraction succeeded
        """
        if not isinstance(data, dict):
            return False
        
        return data.get('status') == 'success'
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if hoopR extractor is operational.
        
        Returns:
            Health check results
        """
        health = super().health_check()
        
        # Check if legacy scripts exist
        scripts_available = {}
        for name, path in self.legacy_scripts.items():
            scripts_available[name] = path.exists()
        
        health['legacy_scripts'] = scripts_available
        health['primary_data_source'] = True
        health['expected_records'] = '13.6M PBP records'
        
        return health

