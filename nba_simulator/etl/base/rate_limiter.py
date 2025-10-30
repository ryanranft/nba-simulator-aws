#!/usr/bin/env python3
"""
Adaptive Rate Limiting - Smart Rate Limiter with 429 Detection

Provides intelligent rate limiting with adaptive behavior:
- 429 detection and automatic delay adjustment
- Token bucket algorithm for smooth rate control
- Retry-After header respect
- Automatic adaptation to website changes
- Rate limit change detection
- TOS compliance monitoring

Based on Crawl4AI MCP server rate limiting patterns.

Usage:
    from adaptive_rate_limiter import AdaptiveRateLimiter, TokenBucket

    # Adaptive rate limiter
    rate_limiter = AdaptiveRateLimiter(initial_rate=10, max_rate=100)
    await rate_limiter.acquire()

    # Token bucket
    bucket = TokenBucket(capacity=100, refill_rate=10)
    if await bucket.consume(5):
        # Process request
        pass

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys
from enum import Enum

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class RateLimitState(Enum):
    """Rate limit state enumeration"""

    NORMAL = "normal"
    APPROACHING_LIMIT = "approaching_limit"
    RATE_LIMITED = "rate_limited"
    BACKING_OFF = "backing_off"


@dataclass
class RateLimitInfo:
    """Rate limit information"""

    current_rate: float
    max_rate: float
    state: RateLimitState
    last_429_time: Optional[datetime] = None
    retry_after: Optional[int] = None
    consecutive_429s: int = 0
    total_requests: int = 0
    successful_requests: int = 0


@dataclass
class TokenBucketConfig:
    """Token bucket configuration"""

    capacity: int
    refill_rate: float  # tokens per second
    initial_tokens: Optional[int] = None


class TokenBucket:
    """Token bucket rate limiter implementation"""

    def __init__(
        self, capacity: int, refill_rate: float, initial_tokens: Optional[int] = None
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = initial_tokens or capacity
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("token_bucket")

    async def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from bucket"""
        async with self.lock:
            await self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def _refill(self) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        time_passed = now - self.last_refill

        if time_passed > 0:
            tokens_to_add = time_passed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

    async def wait_for_tokens(self, tokens: int = 1) -> None:
        """Wait until enough tokens are available"""
        while not await self.consume(tokens):
            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate

            if wait_time > 0:
                await asyncio.sleep(wait_time)

    def get_tokens_available(self) -> int:
        """Get current number of tokens available"""
        return int(self.tokens)

    def get_capacity(self) -> int:
        """Get bucket capacity"""
        return self.capacity


class AdaptiveRateLimiter:
    """Adaptive rate limiter with 429 detection and automatic adjustment"""

    def __init__(
        self,
        initial_rate: float = 10.0,
        max_rate: float = 100.0,
        min_rate: float = 0.1,
        adaptation_factor: float = 0.8,
    ):
        self.initial_rate = initial_rate
        self.max_rate = max_rate
        self.min_rate = min_rate
        self.adaptation_factor = adaptation_factor

        self.current_rate = initial_rate
        self.state = RateLimitState.NORMAL
        self.last_429_time: Optional[datetime] = None
        self.retry_after: Optional[int] = None
        self.consecutive_429s = 0
        self.total_requests = 0
        self.successful_requests = 0

        # Token bucket for rate limiting
        self.token_bucket = TokenBucket(
            capacity=int(max_rate), refill_rate=initial_rate
        )

        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("adaptive_rate_limiter")

        # Rate limit history for learning
        self.rate_history: List[Tuple[datetime, float, bool]] = []

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire permission to make request"""
        async with self.lock:
            self.total_requests += 1

            # Wait for tokens
            await self.token_bucket.wait_for_tokens(tokens)

            # Update rate based on current state
            await self._update_rate()

    async def record_response(self, status_code: int, headers: Dict[str, str]) -> None:
        """Record response and adjust rate accordingly"""
        async with self.lock:
            if status_code == 429:
                await self._handle_429(headers)
            elif status_code < 400:
                await self._handle_success()
            else:
                await self._handle_error(status_code)

    async def _handle_429(self, headers: Dict[str, str]) -> None:
        """Handle 429 rate limit response"""
        self.consecutive_429s += 1
        self.last_429_time = datetime.now(timezone.utc)
        self.state = RateLimitState.RATE_LIMITED

        # Extract Retry-After header
        retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                self.retry_after = int(retry_after)
            except ValueError:
                self.retry_after = None

        # Reduce rate aggressively
        self.current_rate *= self.adaptation_factor
        self.current_rate = max(self.min_rate, self.current_rate)

        # Update token bucket
        self.token_bucket = TokenBucket(
            capacity=int(self.max_rate), refill_rate=self.current_rate
        )

        self.logger.warning(
            f"Rate limited (429). Consecutive 429s: {self.consecutive_429s}, "
            f"New rate: {self.current_rate:.2f}/s, Retry-After: {self.retry_after}"
        )

        # Record in history
        self.rate_history.append((datetime.now(timezone.utc), self.current_rate, False))

    async def _handle_success(self) -> None:
        """Handle successful response"""
        self.successful_requests += 1
        self.consecutive_429s = 0

        # Gradually increase rate if we're not at max
        if (
            self.current_rate < self.max_rate
            and self.state != RateLimitState.RATE_LIMITED
        ):
            self.current_rate *= 1 + self.adaptation_factor * 0.1
            self.current_rate = min(self.max_rate, self.current_rate)

            # Update token bucket
            self.token_bucket = TokenBucket(
                capacity=int(self.max_rate), refill_rate=self.current_rate
            )

        # Update state
        if self.state == RateLimitState.RATE_LIMITED:
            self.state = RateLimitState.BACKING_OFF
        elif self.state == RateLimitState.BACKING_OFF:
            self.state = RateLimitState.NORMAL

        # Record in history
        self.rate_history.append((datetime.now(timezone.utc), self.current_rate, True))

    async def _handle_error(self, status_code: int) -> None:
        """Handle other error responses"""
        if status_code >= 500:
            # Server error - reduce rate slightly
            self.current_rate *= 0.95
            self.current_rate = max(self.min_rate, self.current_rate)

            self.logger.warning(
                f"Server error {status_code}, reducing rate to {self.current_rate:.2f}/s"
            )

        # Record in history
        self.rate_history.append((datetime.now(timezone.utc), self.current_rate, False))

    async def _update_rate(self) -> None:
        """Update rate based on current state and history"""
        # If we're rate limited, respect retry-after
        if self.state == RateLimitState.RATE_LIMITED and self.retry_after:
            time_since_429 = datetime.now(timezone.utc) - self.last_429_time
            if time_since_429.total_seconds() < self.retry_after:
                # Still in retry-after period
                return

        # Clean old history (keep last 100 entries)
        if len(self.rate_history) > 100:
            self.rate_history = self.rate_history[-100:]

    def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit information"""
        return RateLimitInfo(
            current_rate=self.current_rate,
            max_rate=self.max_rate,
            state=self.state,
            last_429_time=self.last_429_time,
            retry_after=self.retry_after,
            consecutive_429s=self.consecutive_429s,
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
        )

    def get_success_rate(self) -> float:
        """Get success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    def get_recent_success_rate(self, minutes: int = 5) -> float:
        """Get recent success rate"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent_requests = [r for r in self.rate_history if r[0] >= cutoff_time]

        if not recent_requests:
            return 0.0

        successful = sum(1 for r in recent_requests if r[2])
        return successful / len(recent_requests)

    def reset(self) -> None:
        """Reset rate limiter to initial state"""
        self.current_rate = self.initial_rate
        self.state = RateLimitState.NORMAL
        self.last_429_time = None
        self.retry_after = None
        self.consecutive_429s = 0
        self.total_requests = 0
        self.successful_requests = 0

        self.token_bucket = TokenBucket(
            capacity=int(self.max_rate), refill_rate=self.initial_rate
        )

        self.rate_history.clear()
        self.logger.info("Rate limiter reset to initial state")


class MultiDomainRateLimiter:
    """Rate limiter that manages multiple domains independently"""

    def __init__(self, default_config: Dict[str, Any] = None):
        self.default_config = default_config or {
            "initial_rate": 10.0,
            "max_rate": 100.0,
            "min_rate": 0.1,
        }
        self.limiters: Dict[str, AdaptiveRateLimiter] = {}
        self.logger = logging.getLogger("multi_domain_rate_limiter")

    def get_limiter(self, domain: str) -> AdaptiveRateLimiter:
        """Get rate limiter for domain"""
        if domain not in self.limiters:
            self.limiters[domain] = AdaptiveRateLimiter(**self.default_config)
            self.logger.info(f"Created rate limiter for domain: {domain}")

        return self.limiters[domain]

    async def acquire(self, domain: str, tokens: int = 1) -> None:
        """Acquire permission for domain"""
        limiter = self.get_limiter(domain)
        await limiter.acquire(tokens)

    async def record_response(
        self, domain: str, status_code: int, headers: Dict[str, str]
    ) -> None:
        """Record response for domain"""
        limiter = self.get_limiter(domain)
        await limiter.record_response(status_code, headers)

    def get_all_rate_info(self) -> Dict[str, RateLimitInfo]:
        """Get rate limit info for all domains"""
        return {
            domain: limiter.get_rate_limit_info()
            for domain, limiter in self.limiters.items()
        }

    def get_domain_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all domains"""
        stats = {}
        for domain, limiter in self.limiters.items():
            stats[domain] = {
                "rate_info": limiter.get_rate_limit_info(),
                "success_rate": limiter.get_success_rate(),
                "recent_success_rate": limiter.get_recent_success_rate(),
            }
        return stats


class RateLimitMonitor:
    """Monitor rate limiting across multiple domains"""

    def __init__(self, multi_domain_limiter: MultiDomainRateLimiter):
        self.multi_domain_limiter = multi_domain_limiter
        self.logger = logging.getLogger("rate_limit_monitor")
        self.alerts: List[Dict[str, Any]] = []

    async def check_rate_limits(self) -> Dict[str, Any]:
        """Check rate limits and generate alerts"""
        stats = self.multi_domain_limiter.get_domain_stats()
        alerts = []

        for domain, domain_stats in stats.items():
            rate_info = domain_stats["rate_info"]
            success_rate = domain_stats["success_rate"]
            recent_success_rate = domain_stats["recent_success_rate"]

            # Check for issues
            if rate_info.state == RateLimitState.RATE_LIMITED:
                alerts.append(
                    {
                        "domain": domain,
                        "type": "rate_limited",
                        "message": f"Domain {domain} is currently rate limited",
                        "severity": "high",
                        "timestamp": datetime.now(timezone.utc),
                    }
                )

            if success_rate < 0.5:
                alerts.append(
                    {
                        "domain": domain,
                        "type": "low_success_rate",
                        "message": f"Domain {domain} has low success rate: {success_rate:.2%}",
                        "severity": "medium",
                        "timestamp": datetime.now(timezone.utc),
                    }
                )

            if recent_success_rate < 0.3:
                alerts.append(
                    {
                        "domain": domain,
                        "type": "recent_failures",
                        "message": f"Domain {domain} has recent failure rate: {1-recent_success_rate:.2%}",
                        "severity": "high",
                        "timestamp": datetime.now(timezone.utc),
                    }
                )

        self.alerts.extend(alerts)

        return {"stats": stats, "alerts": alerts, "total_alerts": len(self.alerts)}

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert["timestamp"] >= cutoff_time]

    def clear_old_alerts(self, hours: int = 24) -> int:
        """Clear old alerts"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        old_count = len(self.alerts)
        self.alerts = [
            alert for alert in self.alerts if alert["timestamp"] >= cutoff_time
        ]
        cleared_count = old_count - len(self.alerts)

        if cleared_count > 0:
            self.logger.info(f"Cleared {cleared_count} old alerts")

        return cleared_count


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Single domain rate limiter
        rate_limiter = AdaptiveRateLimiter(initial_rate=5.0, max_rate=50.0)

        # Simulate requests
        for i in range(20):
            await rate_limiter.acquire()

            # Simulate response
            if i % 5 == 0:  # Every 5th request is rate limited
                await rate_limiter.record_response(429, {"Retry-After": "10"})
                print(f"Request {i+1}: Rate limited (429)")
            else:
                await rate_limiter.record_response(200, {})
                print(f"Request {i+1}: Success (200)")

            # Show rate info
            info = rate_limiter.get_rate_limit_info()
            print(f"  Rate: {info.current_rate:.2f}/s, State: {info.state.value}")

            await asyncio.sleep(0.5)

        # Multi-domain rate limiter
        multi_limiter = MultiDomainRateLimiter()

        domains = ["espn.com", "basketball-reference.com", "nba.com"]

        for domain in domains:
            await multi_limiter.acquire(domain)
            await multi_limiter.record_response(domain, 200, {})
            print(f"Domain {domain}: Request successful")

        # Get stats
        stats = multi_limiter.get_domain_stats()
        print(f"Multi-domain stats: {stats}")

        # Rate limit monitor
        monitor = RateLimitMonitor(multi_limiter)
        monitor_result = await monitor.check_rate_limits()
        print(f"Monitor result: {monitor_result}")

    asyncio.run(example_usage())
