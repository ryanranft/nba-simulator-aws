"""
ESPN Box Scores Extractor

Extracts box score data from ESPN.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class ESPNBoxScoresExtractor(BaseExtractor):
    """
    ESPN box scores extractor.
    
    Extracts box score data from local ESPN files or API.
    
    Usage:
        extractor = ESPNBoxScoresExtractor()
        result = extractor.extract(season="2024")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ESPN box scores extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent
        legacy_script = project_root / "scripts/etl/extract_boxscores_local.py"
        
        super().__init__(
            name="espn_box_scores",
            legacy_script=str(legacy_script),
            config=config,
            max_retries=3,
            rate_limit_delay=1.0
        )
    
    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Extract box scores from ESPN.
        
        Args:
            season: NBA season
            game_id: Specific game ID
            force: Force re-extraction
        
        Returns:
            Extraction results
        """
        self.logger.info(f"Extracting ESPN box scores (season={season})")
        
        args = []
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
                'stdout': result.stdout[:500],
                'exit_code': result.returncode
            }
        
        except Exception as e:
            self.logger.error(f"ESPN box scores extraction failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extraction results"""
        if not isinstance(data, dict):
            return False
        return data.get('status') == 'success'

