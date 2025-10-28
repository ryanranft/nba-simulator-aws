"""
hoopR Player Box Score Extractor

Extracts player box score data from hoopR.

Current: 813,245 records in database
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class HooprPlayerBoxExtractor(BaseExtractor):
    """
    hoopR player box score extractor.
    
    Current: 813K records in database
    
    Wraps legacy scripts for backward compatibility.
    
    Usage:
        extractor = HooprPlayerBoxExtractor()
        result = extractor.extract(season="2024")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize hoopR player box extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent
        
        # hoopR player box is part of the main scraper
        legacy_script = project_root / "scripts/etl/hoopr_async_scraper.py"
        
        super().__init__(
            name="hoopr_player_box",
            legacy_script=str(legacy_script),
            config=config,
            max_retries=3,
            rate_limit_delay=2.0
        )
    
    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Extract player box score data from hoopR.
        
        Args:
            season: NBA season (e.g., "2024")
            game_id: Specific game ID to extract
            force: Force re-extraction
        
        Returns:
            Dictionary with extraction results
        """
        self.logger.info(
            f"Extracting hoopR player box scores "
            f"(season={season}, game_id={game_id})"
        )
        
        args = ["--data-type", "player_box"]
        if season:
            args.extend(["--season", season])
        if game_id:
            args.extend(["--game-id", game_id])
        if force:
            args.append("--force")
        
        try:
            result = self.run_with_retry(
                self.call_legacy_script,
                args=args,
                timeout=3600
            )
            
            return {
                'status': 'success',
                'season': season,
                'game_id': game_id,
                'stdout': result.stdout[:500],
                'exit_code': result.returncode
            }
        
        except Exception as e:
            self.logger.error(f"hoopR player box extraction failed: {e}")
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
        health['expected_records'] = '813K player box scores'
        return health

