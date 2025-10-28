"""
NBA API Play-by-Play Extractor

Extracts play-by-play data from official NBA API.

Official NBA statistics source.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class NBAAPIPlayByPlayExtractor(BaseExtractor):
    """
    NBA API play-by-play data extractor.

    Official NBA statistics source.

    Supports:
    - async - Fast parallel extraction
    - incremental - New games only (simple mode)

    Usage:
        extractor = NBAAPIPlayByPlayExtractor()
        result = extractor.extract(season="2024", mode="incremental")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NBA API play-by-play extractor.

        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent

        self.legacy_scripts = {
            'async': project_root / "scripts/etl/nba_api_async_scraper.py",
            'incremental': project_root / "scripts/etl/nba_api_incremental_simple.py",
        }

        # Default to incremental
        legacy_script = self.legacy_scripts.get('incremental')

        super().__init__(
            name="nba_api_play_by_play",
            legacy_script=str(legacy_script) if legacy_script else None,
            config=config,
            max_retries=3,
            rate_limit_delay=1.5  # NBA API rate limiting
        )

    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False,
        mode: str = "incremental"
    ) -> Dict[str, Any]:
        """
        Extract play-by-play data from NBA API.

        Args:
            season: NBA season (e.g., "2024")
            game_id: Specific game ID to extract
            force: Force re-extraction
            mode: Extraction mode ('async', 'incremental')

        Returns:
            Dictionary with extraction results
        """
        self.logger.info(
            f"Extracting NBA API PBP data (season={season}, "
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
            self.logger.error(f"NBA API PBP extraction failed: {e}")
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
        health['data_source'] = 'NBA Official API'
        health['purpose'] = 'Official statistics'

        return health

