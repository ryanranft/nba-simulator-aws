"""
ESPN Data Extractors

Extractors for ESPN data sources.
Consolidates 12+ ESPN scripts into organized structure.

ESPN is a secondary data source (primarily for validation and gap-filling).
"""

from .play_by_play import ESPNPlayByPlayExtractor
from .box_scores import ESPNBoxScoresExtractor
from .schedule import ESPNScheduleExtractor

__all__ = [
    "ESPNPlayByPlayExtractor",
    "ESPNBoxScoresExtractor",
    "ESPNScheduleExtractor",
]
