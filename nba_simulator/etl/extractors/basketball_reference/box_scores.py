"""
Basketball Reference Box Scores Extractor

Extracts box score data from Basketball Reference.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...base.extractor import BaseExtractor


class BasketballReferenceBoxScoresExtractor(BaseExtractor):
    """
    Basketball Reference box scores extractor.

    Extracts box score data from Basketball Reference.

    Usage:
        extractor = BasketballReferenceBoxScoresExtractor()
        result = extractor.extract(season="2024", mode="daily")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Basketball Reference box scores extractor.

        Args:
            config: Optional configuration dictionary
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent

        self.legacy_scripts = {
            'box_score': project_root / "scripts/etl/basketball_reference_box_score_scraper.py",
            'daily': project_root / "scripts/etl/basketball_reference_daily_box_scores.py",
        }

        legacy_script = self.legacy_scripts.get('daily')

        super().__init__(
            name="basketball_reference_box_scores",
            legacy_script=str(legacy_script) if legacy_script else None,
            config=config,
            max_retries=3,
            rate_limit_delay=3.0
        )

    def extract(
        self,
        season: Optional[str] = None,
        game_id: Optional[str] = None,
        force: bool = False,
        mode: str = "daily"
    ) -> Dict[str, Any]:
        """
        Extract box scores from Basketball Reference.

        Args:
            season: NBA season
            game_id: Specific game ID
            force: Force re-extraction
            mode: Extraction mode ('box_score', 'daily')

        Returns:
            Extraction results
        """
        self.logger.info(
            f"Extracting Basketball Reference box scores (season={season}, mode={mode})"
        )

        args = []
        if season:
            args.extend(["--season", season])
        if game_id:
            args.extend(["--game-id", game_id])
        if force:
            args.append("--force")

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
                'stdout': result.stdout[:500],
                'exit_code': result.returncode
            }

        except Exception as e:
            self.logger.error(f"Basketball Reference box scores extraction failed: {e}")
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

        return health

