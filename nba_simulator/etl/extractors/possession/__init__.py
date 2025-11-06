"""
Phase 0.0005: Possession Extraction

Basketball possession extraction from temporal play-by-play events.
Uses Dean Oliver's "Basketball on Paper" methodology to identify
possession boundaries and calculate efficiency metrics.

Exports:
    - PossessionDetector: Core detection logic
    - PossessionExtractor: Database operations
    - DeanOliverValidator: Possession validation
    - PossessionConfig: Main configuration class
"""

from .detector import PossessionDetector, PossessionBoundary
from .extractor import PossessionExtractor
from .validator import DeanOliverValidator
from .config import (
    DatabaseConfig,
    PossessionDetectionConfig,
    ValidationConfig,
    ProcessingConfig,
    PossessionConfig,
    load_config,
)

__all__ = [
    "PossessionDetector",
    "PossessionBoundary",
    "PossessionExtractor",
    "DeanOliverValidator",
    "DatabaseConfig",
    "PossessionDetectionConfig",
    "ValidationConfig",
    "ProcessingConfig",
    "PossessionConfig",
    "load_config",
]
