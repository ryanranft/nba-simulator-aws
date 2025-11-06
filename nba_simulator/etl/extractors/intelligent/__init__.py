"""
Intelligent Content Extraction Strategies

This package provides intelligent extraction strategies for NBA data scrapers:

- **ExtractionResult:** Dataclass for extraction results with success status, data, confidence
- **BaseExtractionStrategy:** Abstract base class for extraction strategies
- **ESPNExtractionStrategy:** ESPN-specific JSON/HTML extraction
- **BasketballReferenceExtractionStrategy:** Basketball Reference HTML table parsing
- **LLMExtractionStrategy:** Google Gemini-based intelligent extraction
- **ExtractionManager:** Strategy manager with fallback support

Usage:
    from nba_simulator.etl.extractors.intelligent import (
        ExtractionManager,
        ESPNExtractionStrategy,
        BasketballReferenceExtractionStrategy
    )

    # Create manager with strategies
    manager = ExtractionManager()
    manager.add_strategy("espn", ESPNExtractionStrategy())
    manager.add_strategy("bref", BasketballReferenceExtractionStrategy())

    # Extract with fallback
    result = await manager.extract_with_fallback(
        content,
        content_type="json",
        preferred_strategy="espn"
    )

    if result.success:
        print(f"Extracted data: {result.data}")
        print(f"Confidence: {result.confidence}")

Version: 2.0 (Package migration)
Created: November 6, 2025
"""

from nba_simulator.etl.extractors.intelligent.strategies import (
    # Result dataclass
    ExtractionResult,
    # Base class
    BaseExtractionStrategy,
    # Concrete strategies
    ESPNExtractionStrategy,
    BasketballReferenceExtractionStrategy,
    LLMExtractionStrategy,
    # Manager
    ExtractionManager,
)

__all__ = [
    # Result dataclass
    "ExtractionResult",
    # Base class
    "BaseExtractionStrategy",
    # Concrete strategies
    "ESPNExtractionStrategy",
    "BasketballReferenceExtractionStrategy",
    "LLMExtractionStrategy",
    # Manager
    "ExtractionManager",
]

__version__ = "2.0.0"
