"""
Modular Tool Components - Reusable Scraper Tools

This package provides modular, reusable components for NBA data scrapers:

- FetchTool: HTTP request handling with rate limiting and retry logic
- ParseTool: Content parsing with intelligent extraction strategies
- StoreTool: Data persistence to local filesystem and S3
- CheckpointTool: Progress tracking and recovery
- ToolComposer: Composition patterns for complex scraping workflows

Usage:
    from nba_simulator.etl.tools import (
        FetchTool,
        ParseTool,
        StoreTool,
        CheckpointTool,
        ToolComposer,
        ToolConfig,
        BaseTool
    )

    # Initialize composer with scraped configuration
    composer = ToolComposer(config, error_handler, telemetry)

    # Use composed operations
    success = await composer.fetch_and_store(url, filename)

    # Or use tools individually
    fetch_tool = FetchTool(tool_config)
    async with fetch_tool:
        response = await fetch_tool.fetch_url(url)

Version: 2.0 (Package migration)
Created: November 6, 2025
"""

from nba_simulator.etl.tools.modular import (
    BaseTool,
    FetchTool,
    ParseTool,
    StoreTool,
    CheckpointTool,
    ToolComposer,
    ToolConfig,
)

__all__ = [
    # Abstract base
    "BaseTool",
    # Tool implementations
    "FetchTool",
    "ParseTool",
    "StoreTool",
    "CheckpointTool",
    # Composition
    "ToolComposer",
    # Configuration
    "ToolConfig",
]

__version__ = "2.0.0"
