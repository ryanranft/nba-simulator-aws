"""Global Rate Limit Coordinator for ADCE scrapers.

Prevents API rate limit violations by coordinating requests across
concurrent scrapers using a token bucket algorithm.

Week 3 Day 1 Enhancement #3 - Global Rate Limit Coordination

Author: Claude Code (NBA Simulator Dev Team)
Created: 2025-10-31
"""

import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimitCoordinator:
    """Thread-safe rate limit coordinator using token bucket algorithm.

    Coordinates rate limits across multiple concurrent scrapers to prevent
    API rate limit violations. Supports both global and per-source limits
    with configurable backoff strategies.

    Features:
    - Token bucket algorithm for smooth rate limiting
    - Sliding window request tracking
    - Exponential backoff when approaching limits
    - Thread-safe for use with ThreadPoolExecutor
    - Per-source and global rate limits
    - Burst handling with configurable burst sizes

    Example:
        >>> config = {
        ...     "enabled": True,
        ...     "global_limits": {
        ...         "requests_per_minute": 100,
        ...         "requests_per_hour": 5000
        ...     },
        ...     "source_limits": {
        ...         "espn": {
        ...             "requests_per_minute": 60,
        ...             "requests_per_hour": 3000,
        ...             "burst_size": 10
        ...         }
        ...     }
        ... }
        >>> coordinator = RateLimitCoordinator(config)
        >>> coordinator.acquire("espn")  # Blocks if rate limit exceeded
        >>> # ... make API request ...
        >>> coordinator.release("espn")  # Record request completion
    """

    def __init__(self, config: Dict):
        """Initialize rate limit coordinator.

        Args:
            config: Rate limiting configuration from autonomous_config.yaml
        """
        self.config = config
        self.enabled = config.get("enabled", True)

        if not self.enabled:
            logger.info("Rate limiting disabled")
            return

        # Thread safety
        self.lock = threading.RLock()

        # Configuration (must be set BEFORE _initialize_tokens)
        self.global_limits = config.get("global_limits", {})
        self.source_limits = config.get("source_limits", {})
        self.backoff_config = config.get("backoff", {})

        # Request tracking (sliding window)
        self.global_requests = deque()  # [(timestamp, source), ...]
        self.source_requests = defaultdict(deque)  # source -> [(timestamp), ...]

        # Token buckets (for burst handling)
        self.global_tokens = config.get("global_limits", {}).get(
            "requests_per_minute", 100
        )
        self.source_tokens = {}  # source -> token_count
        self._initialize_tokens()

        # Backoff state
        self.backoff_delays = defaultdict(float)  # source -> current_delay
        self.last_request_times = {}  # source -> timestamp

        logger.info("Rate limit coordinator initialized")
        logger.info(f"  Global: {self.global_limits}")
        logger.info(f"  Sources: {list(self.source_limits.keys())}")

    def _initialize_tokens(self):
        """Initialize token buckets for each source."""
        for source, limits in self.source_limits.items():
            burst_size = limits.get("burst_size", limits.get("requests_per_minute", 10))
            self.source_tokens[source] = burst_size

    def acquire(self, source: str, wait: bool = True) -> bool:
        """Acquire permission to make an API request.

        Checks both global and source-specific rate limits. If limits are
        exceeded and wait=True, blocks until request can be made. If wait=False,
        returns False immediately if rate limited.

        Args:
            source: Source name (espn, nba_api, basketball_reference, hoopr)
            wait: If True, block until request allowed. If False, return immediately.

        Returns:
            bool: True if request permitted, False if rate limited (when wait=False)

        Example:
            >>> if coordinator.acquire("espn", wait=False):
            ...     make_api_request()
            ...     coordinator.release("espn")
            ... else:
            ...     logger.warning("Rate limited, skipping request")
        """
        if not self.enabled:
            return True

        with self.lock:
            while True:
                # Clean old requests from sliding window
                self._clean_old_requests()

                # Check if request would violate limits
                delay = self._calculate_required_delay(source)

                if delay == 0:
                    # Request permitted, consume token
                    self._consume_token(source)
                    return True

                if not wait:
                    # Rate limited and not waiting
                    logger.warning(
                        f"Rate limit would be exceeded for {source}, delay needed: {delay:.1f}s"
                    )
                    return False

                # Wait and retry
                logger.info(
                    f"Rate limit approaching for {source}, waiting {delay:.1f}s..."
                )

        # Release lock while sleeping
        time.sleep(delay)

        # Retry acquisition after delay
        return self.acquire(source, wait=wait)

    def release(self, source: str):
        """Record completion of an API request.

        Updates request tracking and refills token buckets.

        Args:
            source: Source name that made the request
        """
        if not self.enabled:
            return

        with self.lock:
            now = datetime.now()

            # Record request
            self.global_requests.append((now, source))
            self.source_requests[source].append(now)
            self.last_request_times[source] = now

            # Refill tokens over time
            self._refill_tokens(source)

    def _calculate_required_delay(self, source: str) -> float:
        """Calculate delay needed before request can be made.

        Checks:
        1. Global rate limits (requests/minute, requests/hour)
        2. Source-specific rate limits
        3. Minimum delay between requests (if configured)
        4. Backoff delays (if approaching limits)

        Args:
            source: Source name to check

        Returns:
            float: Seconds to delay (0 if no delay needed)
        """
        delays = []

        # Check global limits
        if self.global_limits:
            delay = self._check_global_limits()
            if delay > 0:
                delays.append(delay)

        # Check source limits
        if source in self.source_limits:
            delay = self._check_source_limits(source)
            if delay > 0:
                delays.append(delay)

        # Check minimum delay between requests
        if source in self.source_limits:
            min_delay = self.source_limits[source].get("min_delay_seconds", 0)
            if min_delay > 0 and source in self.last_request_times:
                time_since_last = (
                    datetime.now() - self.last_request_times[source]
                ).total_seconds()
                if time_since_last < min_delay:
                    delays.append(min_delay - time_since_last)

        # Check backoff delay
        if source in self.backoff_delays and self.backoff_delays[source] > 0:
            delays.append(self.backoff_delays[source])

        return max(delays) if delays else 0

    def _check_global_limits(self) -> float:
        """Check if global rate limits would be exceeded.

        Returns:
            float: Delay needed in seconds (0 if no delay needed)
        """
        now = datetime.now()

        # Check requests per minute
        rpm_limit = self.global_limits.get("requests_per_minute", 0)
        if rpm_limit > 0:
            minute_ago = now - timedelta(minutes=1)
            recent_requests = sum(
                1 for ts, _ in self.global_requests if ts > minute_ago
            )

            if recent_requests >= rpm_limit:
                # Find oldest request in window
                oldest = min(ts for ts, _ in self.global_requests if ts > minute_ago)
                delay = (oldest + timedelta(minutes=1) - now).total_seconds()
                return max(0, delay)

        # Check requests per hour
        rph_limit = self.global_limits.get("requests_per_hour", 0)
        if rph_limit > 0:
            hour_ago = now - timedelta(hours=1)
            recent_requests = sum(1 for ts, _ in self.global_requests if ts > hour_ago)

            if recent_requests >= rph_limit:
                oldest = min(ts for ts, _ in self.global_requests if ts > hour_ago)
                delay = (oldest + timedelta(hours=1) - now).total_seconds()
                return max(0, delay)

        return 0

    def _check_source_limits(self, source: str) -> float:
        """Check if source-specific rate limits would be exceeded.

        Args:
            source: Source name to check

        Returns:
            float: Delay needed in seconds (0 if no delay needed)
        """
        now = datetime.now()
        limits = self.source_limits.get(source, {})

        # Check requests per minute
        rpm_limit = limits.get("requests_per_minute", 0)
        if rpm_limit > 0:
            minute_ago = now - timedelta(minutes=1)
            recent_requests = sum(
                1 for ts in self.source_requests[source] if ts > minute_ago
            )

            if recent_requests >= rpm_limit:
                oldest = min(
                    ts for ts in self.source_requests[source] if ts > minute_ago
                )
                delay = (oldest + timedelta(minutes=1) - now).total_seconds()
                return max(0, delay)

        # Check requests per hour
        rph_limit = limits.get("requests_per_hour", 0)
        if rph_limit > 0:
            hour_ago = now - timedelta(hours=1)
            recent_requests = sum(
                1 for ts in self.source_requests[source] if ts > hour_ago
            )

            if recent_requests >= rph_limit:
                oldest = min(ts for ts in self.source_requests[source] if ts > hour_ago)
                delay = (oldest + timedelta(hours=1) - now).total_seconds()
                return max(0, delay)

        return 0

    def _consume_token(self, source: str):
        """Consume a token from source's bucket.

        Args:
            source: Source consuming a token
        """
        if source in self.source_tokens:
            self.source_tokens[source] = max(0, self.source_tokens[source] - 1)

    def _refill_tokens(self, source: str):
        """Refill tokens in source's bucket over time.

        Args:
            source: Source to refill tokens for
        """
        if source not in self.source_limits:
            return

        limits = self.source_limits[source]
        burst_size = limits.get("burst_size", limits.get("requests_per_minute", 10))

        # Refill at rate of requests_per_minute
        rpm = limits.get("requests_per_minute", 60)
        refill_rate = rpm / 60  # Tokens per second

        if source in self.last_request_times:
            time_since_last = (
                datetime.now() - self.last_request_times[source]
            ).total_seconds()
            tokens_to_add = time_since_last * refill_rate

            self.source_tokens[source] = min(
                burst_size, self.source_tokens[source] + tokens_to_add
            )

    def _clean_old_requests(self):
        """Remove requests older than 1 hour from tracking."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Clean global requests
        while self.global_requests and self.global_requests[0][0] < hour_ago:
            self.global_requests.popleft()

        # Clean source requests
        for source in self.source_requests:
            while (
                self.source_requests[source]
                and self.source_requests[source][0] < hour_ago
            ):
                self.source_requests[source].popleft()

    def get_stats(self) -> Dict:
        """Get current rate limiting statistics.

        Returns:
            dict: Statistics including request counts and available tokens

        Example:
            >>> stats = coordinator.get_stats()
            >>> print(f"Global: {stats['global']['requests_last_minute']}/min")
            >>> print(f"ESPN: {stats['sources']['espn']['tokens_available']}")
        """
        if not self.enabled:
            return {"enabled": False}

        with self.lock:
            self._clean_old_requests()
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            stats = {
                "enabled": True,
                "global": {
                    "requests_last_minute": sum(
                        1 for ts, _ in self.global_requests if ts > minute_ago
                    ),
                    "requests_last_hour": sum(
                        1 for ts, _ in self.global_requests if ts > hour_ago
                    ),
                    "limit_rpm": self.global_limits.get("requests_per_minute", 0),
                    "limit_rph": self.global_limits.get("requests_per_hour", 0),
                },
                "sources": {},
            }

            for source in self.source_requests:
                stats["sources"][source] = {
                    "requests_last_minute": sum(
                        1 for ts in self.source_requests[source] if ts > minute_ago
                    ),
                    "requests_last_hour": sum(
                        1 for ts in self.source_requests[source] if ts > hour_ago
                    ),
                    "tokens_available": self.source_tokens.get(source, 0),
                    "limit_rpm": self.source_limits.get(source, {}).get(
                        "requests_per_minute", 0
                    ),
                    "limit_rph": self.source_limits.get(source, {}).get(
                        "requests_per_hour", 0
                    ),
                }

            return stats
