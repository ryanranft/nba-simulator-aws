"""
NBA API Possession Panel Extractor

Creates possession panel data from NBA API play-by-play.

Transforms PBP data into possession-level panel data.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class NBAAPIPossessionPanelExtractor(BaseExtractor):
    """
    NBA API possession panel extractor.

    Creates possession-level panel data from NBA API play-by-play.
    Critical for temporal panel data analysis.

    Usage:
        extractor = NBAAPIPossessionPanelExtractor()
        result = extractor.extract(season="2024")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NBA API possession panel extractor.

        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent
        legacy_script = project_root / "scripts/etl/create_possession_panel_from_nba_api.py"

        super().__init__(
            name="nba_api_possession_panel",
            legacy_script=str(legacy_script),
            config=config,
            max_retries=3,
            rate_limit_delay=0.5  # Faster - works with local data
        )

    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Create possession panel from NBA API data.

        Args:
            season: NBA season
            game_id: Specific game ID
            force: Force re-creation

        Returns:
            Extraction results
        """
        self.logger.info(
            f"Creating possession panel from NBA API (season={season}, game_id={game_id})"
        )

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
                timeout=7200  # 2 hour timeout
            )

            return {
                'status': 'success',
                'season': season,
                'game_id': game_id,
                'stdout': result.stdout[:500],
                'exit_code': result.returncode
            }

        except Exception as e:
            self.logger.error(f"NBA API possession panel creation failed: {e}")
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
        health['data_type'] = 'Possession-level panel data'
        health['critical_for'] = 'Temporal analysis'
        return health

