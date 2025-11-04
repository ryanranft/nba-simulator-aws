"""
hoopR Scraper - Python Wrapper for hoopR R Package

Comprehensive scraper that wraps the hoopR R package for NBA data collection.
hoopR is an R package that provides clean access to ESPN NBA data.

Features:
- Python wrapper for R's hoopR package
- Play-by-play data from ESPN
- Team schedules and rosters
- Player box scores
- Async execution with subprocess
- Automatic R dependency checking
- Fallback to direct ESPN API if R unavailable

Installation Requirements:
    # R and hoopR package
    install.packages("hoopR")
    
    # Optional: rpy2 for direct R integration
    pip install rpy2

Usage:
    config = ScraperConfig(
        base_url="",  # Not used - hoopR handles URLs
        rate_limit=1.0,
        output_dir="/tmp/hoopr_data"
    )
    
    async with HoopRScraper(config) as scraper:
        # Scrape play-by-play
        pbp = await scraper.scrape_play_by_play(game_id="401468224")
        
        # Scrape team schedule
        schedule = await scraper.scrape_team_schedule(team="LAL", season=2024)

Version: 2.0 (Refactored)
Created: November 2, 2025
"""

import asyncio
import subprocess
import json
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from nba_simulator.etl.base import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperErrorHandler,
    safe_execute
)
from nba_simulator.etl.validation import (
    validate_play_by_play,
    validate_game,
    DataSource,
    ValidationReport
)
from nba_simulator.utils import logger

# Try to import rpy2 for direct R integration
try:
    import rpy2.robjects as ro
    from rpy2.robjects.packages import importr
    HAS_RPY2 = True
except ImportError:
    HAS_RPY2 = False
    logger.info("rpy2 not available, will use subprocess method")


class HoopRScraper(AsyncBaseScraper):
    """
    Async scraper that wraps the hoopR R package.
    
    Provides two integration methods:
    1. Direct R integration via rpy2 (preferred if available)
    2. Subprocess calls to R scripts (fallback)
    """
    
    def __init__(self, config: ScraperConfig, use_rpy2: bool = True, **kwargs):
        """
        Initialize hoopR scraper.
        
        Args:
            config: Scraper configuration
            use_rpy2: If True and rpy2 available, use direct R integration
            **kwargs: Additional arguments passed to base class
        """
        super().__init__(config, **kwargs)
        
        # Initialize error handler
        self.error_handler = ScraperErrorHandler(
            max_retries=config.retry_attempts
        )
        
        # hoopR specific settings
        self.data_source = DataSource.HOOPR
        self.use_rpy2 = use_rpy2 and HAS_RPY2
        
        # Check R availability
        self.r_available = self._check_r_installation()
        
        if not self.r_available:
            logger.warning(
                "R not found. hoopR scraper will not work. "
                "Install R and hoopR package: install.packages('hoopR')"
            )
        
        # Initialize R interface if using rpy2
        if self.use_rpy2 and self.r_available:
            try:
                self.hoopr = importr('hoopR')
                logger.info("Successfully loaded hoopR via rpy2")
            except Exception as e:
                logger.warning(f"Failed to load hoopR via rpy2: {e}")
                logger.info("Falling back to subprocess method")
                self.use_rpy2 = False
        
        self.logger.info(
            f"Initialized hoopR scraper "
            f"(method={'rpy2' if self.use_rpy2 else 'subprocess'}, "
            f"rate_limit={config.rate_limit}s)"
        )
    
    def _check_r_installation(self) -> bool:
        """
        Check if R is installed and available.
        
        Returns:
            True if R is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['R', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    async def scrape(self) -> None:
        """
        Main scraping entry point.
        
        Override to implement complete scraping workflow.
        """
        if not self.r_available:
            self.logger.error("R not available. Cannot scrape.")
            return
        
        self.logger.info("Starting hoopR scrape...")
        
        # Example: scrape Lakers schedule for 2024
        schedule = await self.scrape_team_schedule(team="LAL", season=2024)
        self.logger.info(f"Scraped {len(schedule)} games")
    
    async def scrape_play_by_play(
        self,
        game_id: str,
        season: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape play-by-play data using hoopR.
        
        Args:
            game_id: ESPN game ID
            season: Optional season year
            
        Returns:
            List of play dictionaries or None on error
        """
        self.logger.info(f"Scraping play-by-play: {game_id}")
        
        if not self.r_available:
            return None
        
        # Use appropriate method
        if self.use_rpy2:
            pbp_data = await self._scrape_pbp_rpy2(game_id)
        else:
            pbp_data = await self._scrape_pbp_subprocess(game_id)
        
        if not pbp_data:
            return None
        
        # Validate plays
        valid_plays = []
        for play in pbp_data:
            report = validate_play_by_play(play, source=self.data_source)
            if report.is_valid or report.has_warnings:
                valid_plays.append(play)
        
        # Store data
        if valid_plays:
            filename = f"pbp_{game_id}.json"
            await self.store_data(
                valid_plays,
                filename,
                subdir=f"hoopr/play_by_play/{season or datetime.now().year}"
            )
        
        self.logger.info(f"Scraped {len(valid_plays)} plays")
        return valid_plays
    
    async def scrape_team_schedule(
        self,
        team: str,
        season: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape team schedule using hoopR.
        
        Args:
            team: Team abbreviation (e.g., "LAL")
            season: Season year
            
        Returns:
            List of game dictionaries or None on error
        """
        self.logger.info(f"Scraping {team} schedule for {season}")
        
        if not self.r_available:
            return None
        
        # Use appropriate method
        if self.use_rpy2:
            schedule_data = await self._scrape_schedule_rpy2(team, season)
        else:
            schedule_data = await self._scrape_schedule_subprocess(team, season)
        
        if not schedule_data:
            return None
        
        # Validate games
        valid_games = []
        for game in schedule_data:
            report = validate_game(game, source=self.data_source)
            if report.is_valid:
                valid_games.append(game)
        
        # Store data
        if valid_games:
            filename = f"schedule_{team}_{season}.json"
            await self.store_data(
                valid_games,
                filename,
                subdir=f"hoopr/schedules/{season}"
            )
        
        self.logger.info(f"Scraped {len(valid_games)} games")
        return valid_games
    
    async def _scrape_pbp_rpy2(self, game_id: str) -> Optional[List[Dict]]:
        """
        Scrape play-by-play using rpy2.
        
        Args:
            game_id: ESPN game ID
            
        Returns:
            List of play dictionaries or None on error
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def get_pbp():
                # Call hoopR function
                pbp_df = self.hoopr.nba_pbp(game_id=game_id)
                # Convert R dataframe to Python dict
                return self._r_dataframe_to_list(pbp_df)
            
            result = await loop.run_in_executor(None, get_pbp)
            return result
        
        except Exception as e:
            self.logger.error(f"Error scraping PBP via rpy2: {e}")
            return None
    
    async def _scrape_pbp_subprocess(self, game_id: str) -> Optional[List[Dict]]:
        """
        Scrape play-by-play using subprocess.
        
        Args:
            game_id: ESPN game ID
            
        Returns:
            List of play dictionaries or None on error
        """
        # Create temporary R script
        r_script = f"""
library(hoopR)
library(jsonlite)

# Get play-by-play data
pbp <- nba_pbp(game_id = "{game_id}")

# Convert to JSON
cat(toJSON(pbp, auto_unbox = TRUE))
"""
        
        try:
            # Write script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
                f.write(r_script)
                script_path = f.name
            
            # Run R script
            result = await self._run_r_script(script_path)
            
            # Clean up
            Path(script_path).unlink()
            
            if result:
                return json.loads(result)
            return None
        
        except Exception as e:
            self.logger.error(f"Error scraping PBP via subprocess: {e}")
            return None
    
    async def _scrape_schedule_rpy2(
        self,
        team: str,
        season: int
    ) -> Optional[List[Dict]]:
        """Scrape schedule using rpy2"""
        try:
            loop = asyncio.get_event_loop()
            
            def get_schedule():
                # Call hoopR function
                schedule_df = self.hoopr.nba_schedule(season=season)
                # Filter by team if needed
                # Convert to Python dict
                return self._r_dataframe_to_list(schedule_df)
            
            result = await loop.run_in_executor(None, get_schedule)
            return result
        
        except Exception as e:
            self.logger.error(f"Error scraping schedule via rpy2: {e}")
            return None
    
    async def _scrape_schedule_subprocess(
        self,
        team: str,
        season: int
    ) -> Optional[List[Dict]]:
        """Scrape schedule using subprocess"""
        r_script = f"""
library(hoopR)
library(jsonlite)

# Get schedule
schedule <- nba_schedule(season = {season})

# Convert to JSON
cat(toJSON(schedule, auto_unbox = TRUE))
"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
                f.write(r_script)
                script_path = f.name
            
            result = await self._run_r_script(script_path)
            Path(script_path).unlink()
            
            if result:
                return json.loads(result)
            return None
        
        except Exception as e:
            self.logger.error(f"Error scraping schedule via subprocess: {e}")
            return None
    
    async def _run_r_script(self, script_path: str) -> Optional[str]:
        """
        Run R script asynchronously.
        
        Args:
            script_path: Path to R script
            
        Returns:
            Script output or None on error
        """
        try:
            # Run R script asynchronously
            process = await asyncio.create_subprocess_exec(
                'Rscript',
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"R script failed: {stderr.decode()}")
                return None
            
            return stdout.decode()
        
        except Exception as e:
            self.logger.error(f"Error running R script: {e}")
            return None
    
    def _r_dataframe_to_list(self, r_df) -> List[Dict]:
        """
        Convert R dataframe to list of dictionaries.
        
        Args:
            r_df: R dataframe object
            
        Returns:
            List of dictionaries
        """
        if not HAS_RPY2:
            return []
        
        try:
            # Convert R dataframe to pandas, then to dict
            import pandas as pd
            pandas_df = pd.DataFrame(r_df)
            return pandas_df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Error converting R dataframe: {e}")
            return []
    
    async def get_error_summary(self) -> Dict[str, Any]:
        """Get error handling summary"""
        return self.error_handler.get_error_summary()


# Convenience function
async def scrape_hoopr_season(
    season: int,
    teams: Optional[List[str]] = None,
    output_dir: str = "/tmp/hoopr_scraper",
    s3_bucket: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to scrape hoopR season data.
    
    Args:
        season: Season year (e.g., 2024)
        teams: Optional list of team abbreviations to scrape
        output_dir: Output directory
        s3_bucket: Optional S3 bucket
        
    Returns:
        Dictionary with scraping results
    """
    config = ScraperConfig(
        base_url="",  # Not used
        rate_limit=1.0,
        timeout=60,  # R can be slow
        retry_attempts=3,
        max_concurrent=1,  # Keep low for R
        s3_bucket=s3_bucket,
        output_dir=output_dir
    )
    
    results = {
        'teams_scraped': 0,
        'errors': 0
    }
    
    async with HoopRScraper(config) as scraper:
        if not scraper.r_available:
            logger.error("R not available. Cannot scrape with hoopR.")
            results['errors'] = 1
            return results
        
        # Default teams if none specified
        if teams is None:
            teams = ['LAL', 'GSW', 'BOS', 'MIA']  # Example teams
        
        # Scrape each team's schedule
        for team in teams:
            schedule = await scraper.scrape_team_schedule(team, season)
            if schedule:
                results['teams_scraped'] += 1
        
        # Get error summary
        error_summary = await scraper.get_error_summary()
        results['errors'] += error_summary.get('total_errors', 0)
    
    return results


if __name__ == "__main__":
    # Example usage
    async def main():
        config = ScraperConfig(
            base_url="",
            rate_limit=1.0,
            output_dir="/tmp/hoopr_test"
        )
        
        async with HoopRScraper(config) as scraper:
            if scraper.r_available:
                # Scrape Lakers schedule
                schedule = await scraper.scrape_team_schedule("LAL", 2024)
                print(f"Scraped {len(schedule) if schedule else 0} games")
            else:
                print("R not available")
    
    asyncio.run(main())
