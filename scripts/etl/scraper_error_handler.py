"""
Scraper Error Handler - Minimal Stub

Temporary stub until full error handling framework is migrated.
"""

import logging

logger = logging.getLogger(__name__)


class ScraperErrorHandler:
    """Minimal error handler for scrapers"""

    def __init__(self):
        self.logger = logger

    async def handle_error(self, error):
        """Handle scraper errors by logging them"""
        self.logger.error(f"Scraper error: {error}")
        # Additional error handling logic can be added here
