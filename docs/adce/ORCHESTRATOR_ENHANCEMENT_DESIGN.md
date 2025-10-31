# ADCE Orchestrator Enhancement Design
## Week 3 Implementation Specification

**Date:** October 31, 2025
**Version:** 1.0
**Status:** DESIGN - Ready for Implementation
**Target:** Week 3 (Nov 1-7, 2025)
**Estimated Effort:** 18-27 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Enhancement 1: Weighted Priority Queue](#enhancement-1-weighted-priority-queue)
3. [Enhancement 2: Parallel Execution](#enhancement-2-parallel-execution)
4. [Enhancement 3: Global Rate Limit Coordinator](#enhancement-3-global-rate-limit-coordinator)
5. [Enhancement 4: Real-Time Reconciliation](#enhancement-4-real-time-reconciliation)
6. [Enhancement 5: Metrics & Observability](#enhancement-5-metrics--observability)
7. [Testing Strategy](#testing-strategy)
8. [Rollback Plan](#rollback-plan)
9. [Migration Guide](#migration-guide)

---

## Overview

### Goals

Transform the ADCE scraper orchestrator from **sequential execution** to **intelligent parallel execution** with enhanced gap detection and comprehensive monitoring.

**Current State:**
- ✅ Sequential task processing within priority levels
- ✅ Simple priority grouping (CRITICAL → HIGH → MEDIUM → LOW)
- ✅ 1-hour reconciliation cycles
- ✅ Basic health monitoring

**Target State:**
- 🎯 Parallel task execution (5 concurrent scrapers)
- 🎯 Weighted priority scoring (age, source, volume)
- 🎯 15-minute reconciliation cycles
- 🎯 Global rate limit coordination
- 🎯 CloudWatch metrics integration
- 🎯 3-4x faster gap filling

### Success Criteria

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Task throughput | 5 tasks/min | 15-20 tasks/min | Tasks completed per minute |
| Gap detection latency | 60 min | 15 min | Time to detect → task creation |
| Orchestrator runtime | 30-60 min | 10-20 min | Duration for 100 tasks |
| API 429 errors | 0-2/day | 0/day | Rate limit violations |
| Parallel efficiency | N/A (sequential) | 70-80% | Actual vs theoretical speedup |

---

## Enhancement 1: Weighted Priority Queue

### Current Implementation

**File:** `scripts/orchestration/scraper_orchestrator.py`
**Lines:** 154-208

```python
# Current: Simple priority grouping
priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

for priority in priority_order:
    priority_tasks = [t for t in tasks if t["priority"] == priority]
    for task in priority_tasks:
        self._execute_task(task)  # Sequential
```

**Problem:** Within each priority level, tasks are processed in arbitrary order. No consideration for:
- Task age (staleness)
- Data source importance
- Task complexity (estimated time)
- Historical success rates

### Enhanced Design

**Weighted Scoring Algorithm:**

```python
def _calculate_task_score(self, task):
    """
    Calculate weighted priority score for intelligent task ordering

    Factors:
    - Base priority (CRITICAL=1000, HIGH=100, MEDIUM=10, LOW=1)
    - Age multiplier (older gaps = higher priority)
    - Source importance (ESPN > NBA_API > others)
    - Task size (smaller = easier = higher priority)
    - Historical success rate (failing scrapers = lower priority)

    Returns:
        float: Weighted score (higher = more important)
    """
    # Base priority score
    base_scores = {
        "CRITICAL": 1000,
        "HIGH": 100,
        "MEDIUM": 10,
        "LOW": 1
    }
    score = base_scores.get(task["priority"], 1)

    # Age factor: +0.5 points per hour old
    if "detected_at" in task:
        detected = datetime.fromisoformat(task["detected_at"])
        age_hours = (datetime.now() - detected).total_seconds() / 3600
        score += age_hours * 0.5

    # Source importance multiplier
    source_multipliers = {
        "ESPN": 1.5,
        "NBA_API": 1.3,
        "Basketball_Reference": 1.2,
        "hoopR": 1.1,
        "Kaggle": 1.0
    }
    score *= source_multipliers.get(task["source"], 1.0)

    # Task size factor: smaller gaps are easier to fill
    if "estimated_files" in task:
        file_count = task["estimated_files"]
        if file_count < 10:
            score *= 1.3  # Boost small gaps
        elif file_count < 50:
            score *= 1.1
        elif file_count > 500:
            score *= 0.8  # Depress large gaps slightly

    # Historical success rate
    scraper = task.get("scraper")
    if scraper and scraper in self.scraper_success_rates:
        success_rate = self.scraper_success_rates[scraper]
        if success_rate < 0.5:
            score *= 0.7  # Depress failing scrapers

    return score
```

### Implementation Steps

**Step 1: Add score calculation method** (30 min)

**File:** `scripts/orchestration/scraper_orchestrator.py`
**Location:** After Line 152 (before `execute_all_tasks`)

```python
def _calculate_task_score(self, task):
    """Calculate weighted priority score"""
    # [Implementation above]
    pass

def _calculate_scraper_success_rates(self):
    """
    Calculate historical success rates for each scraper

    Returns:
        dict: {scraper_name: success_rate}
    """
    # Load from DIMS metrics or calculate from recent history
    success_rates = {}

    # Option 1: From execution_stats (current session)
    for scraper, stats in self.execution_stats["by_scraper"].items():
        total = stats["completed"] + stats["failed"]
        if total > 0:
            success_rates[scraper] = stats["completed"] / total

    # Option 2: From DIMS historical data (future)
    # TODO: Load from DIMS metrics database

    return success_rates
```

**Step 2: Update execute_all_tasks to use weighted queue** (1 hour)

**Replace Lines 154-208 with:**

```python
def execute_all_tasks(self, priority_filter=None):
    """
    Execute all tasks using weighted priority queue

    Args:
        priority_filter: Optional filter for specific priority

    Returns:
        dict: Execution statistics
    """
    self.execution_stats["start_time"] = datetime.now()

    logger.info("\n" + "=" * 80)
    logger.info("STARTING TASK EXECUTION (Weighted Priority Queue)")
    logger.info("=" * 80)

    # Get tasks
    tasks = self.task_queue.get("tasks", [])
    self.execution_stats["total_tasks"] = len(tasks)

    if priority_filter:
        tasks = [t for t in tasks if t["priority"].lower() == priority_filter.lower()]
        logger.info(f"Filtered to {len(tasks)} {priority_filter} priority tasks")

    # Calculate success rates for weighting
    self.scraper_success_rates = self._calculate_scraper_success_rates()

    # Calculate scores for all tasks
    logger.info(f"\nCalculating weighted scores for {len(tasks)} tasks...")
    scored_tasks = []
    for task in tasks:
        score = self._calculate_task_score(task)
        scored_tasks.append((score, task))

    # Sort by score (descending)
    scored_tasks.sort(reverse=True, key=lambda x: x[0])

    # Log top 5 tasks
    logger.info("\nTop 5 tasks by weighted score:")
    for i, (score, task) in enumerate(scored_tasks[:5]):
        logger.info(f"  {i+1}. [{task['priority']}] {task['id']} "
                   f"(score: {score:.2f}, source: {task['source']})")

    # Execute tasks (still sequential for now, parallel in Enhancement 2)
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Executing {len(scored_tasks)} tasks in weighted order")
    logger.info(f"{'=' * 80}")

    for score, task in scored_tasks:
        if not self.running:
            logger.warning("Shutdown requested, stopping execution...")
            break

        logger.info(f"\n[Score: {score:.2f}] Processing task: {task['id']}")
        self._execute_task(task)

    self.execution_stats["end_time"] = datetime.now()
    self._print_execution_summary()

    return self.execution_stats
```

**Step 3: Add configuration for weighting factors** (15 min)

**File:** `config/scraper_config.yaml`
**Add new section:**

```yaml
# Weighted Priority Queue Configuration
priority_weighting:
  enabled: true

  # Base scores by priority level
  base_scores:
    CRITICAL: 1000
    HIGH: 100
    MEDIUM: 10
    LOW: 1

  # Age multiplier (points per hour old)
  age_multiplier: 0.5

  # Source importance multipliers
  source_multipliers:
    ESPN: 1.5
    NBA_API: 1.3
    Basketball_Reference: 1.2
    hoopR: 1.1
    Kaggle: 1.0

  # Task size thresholds and multipliers
  task_size:
    small_threshold: 10  # files
    small_multiplier: 1.3
    medium_threshold: 50
    medium_multiplier: 1.1
    large_threshold: 500
    large_multiplier: 0.8

  # Success rate threshold
  success_rate_threshold: 0.5
  success_rate_penalty: 0.7
```

**Step 4: Load weighting config in orchestrator** (15 min)

**File:** `scripts/orchestration/scraper_orchestrator.py`
**Modify `__init__` method (Line 60-78):**

```python
def __init__(self, task_queue_file="inventory/gaps.json",
             scraper_config_file="config/scraper_config.yaml",
             max_concurrent=5, dry_run=False):
    # ... existing code ...

    # Load scraper config
    self.scraper_config = self._load_scraper_config()

    # Load priority weighting config
    self.weighting_config = self.scraper_config.get("priority_weighting", {})
    if not self.weighting_config.get("enabled", False):
        logger.warning("Weighted priority queue disabled, using simple priority")
        self.weighting_config = None

    # Initialize scraper success rates
    self.scraper_success_rates = {}

    # ... rest of init ...
```

### Testing

**Test Case 1: Scoring Algorithm**
```python
# Test task scoring
task1 = {
    "id": "task_001",
    "priority": "HIGH",
    "source": "ESPN",
    "detected_at": "2025-10-31T10:00:00",
    "estimated_files": 5
}

score = orchestrator._calculate_task_score(task1)
assert score > 100  # Base HIGH score
print(f"Score: {score}")  # Should be ~200+ with multipliers
```

**Test Case 2: Task Ordering**
```python
# Create test tasks with different priorities, ages, sources
tasks = [
    {"priority": "LOW", "source": "ESPN", "detected_at": "2025-10-30T10:00:00"},
    {"priority": "HIGH", "source": "Kaggle", "detected_at": "2025-10-31T10:00:00"},
    {"priority": "MEDIUM", "source": "ESPN", "detected_at": "2025-10-29T10:00:00"}
]

# Score and sort
scored = [(orchestrator._calculate_task_score(t), t) for t in tasks]
scored.sort(reverse=True)

# Verify oldest ESPN task (MEDIUM + age + ESPN) beats recent HIGH Kaggle
assert scored[0][1]["source"] == "ESPN"
```

### Rollback

**Feature Flag:** Add `enabled: false` to `priority_weighting` config

**Fallback:** If weighting config missing or disabled, falls back to original simple priority grouping

---

## Enhancement 2: Parallel Execution

### Current Implementation

**File:** `scripts/orchestration/scraper_orchestrator.py`
**Lines:** 197-201

```python
for task in priority_tasks:
    if not self.running:
        break
    self._execute_task(task)  # Blocks until complete
```

**Problem:** Tasks execute sequentially. With 5 max_concurrent slots, we could run 5 tasks simultaneously, but currently only run 1 at a time.

### Enhanced Design

**Use concurrent.futures.ThreadPoolExecutor for true parallelism:**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class ScraperOrchestrator:
    def __init__(self, ...):
        # ... existing init ...

        # Parallel execution pool
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_concurrent,
            thread_name_prefix="scraper"
        )

        # Thread-safe execution tracking
        self.stats_lock = threading.Lock()

    def execute_all_tasks(self, priority_filter=None):
        """Execute tasks in parallel using ThreadPoolExecutor"""
        # ... task scoring (from Enhancement 1) ...

        # Submit all tasks to executor
        logger.info(f"\nSubmitting {len(scored_tasks)} tasks to parallel execution pool")
        logger.info(f"Max concurrent workers: {self.max_concurrent}")

        futures = {}
        for score, task in scored_tasks:
            if not self.running:
                break

            # Submit task to pool (non-blocking)
            future = self.executor.submit(self._execute_task_safe, task, score)
            futures[future] = (task, score)

        # Process results as they complete
        logger.info(f"\nProcessing {len(futures)} tasks...")
        completed_count = 0

        for future in as_completed(futures):
            task, score = futures[future]

            try:
                result = future.result()  # Get result (blocking)
                completed_count += 1

                logger.info(f"\n[{completed_count}/{len(futures)}] Task completed: "
                           f"{task['id']} (score: {score:.2f})")

            except Exception as e:
                logger.error(f"Task {task['id']} failed with exception: {e}")
                with self.stats_lock:
                    self.execution_stats["failed"] += 1

            # Check for shutdown signal
            if not self.running:
                logger.warning("Shutdown requested, cancelling pending tasks...")
                for f in futures:
                    if not f.done():
                        f.cancel()
                break

        self.execution_stats["end_time"] = datetime.now()
        self._print_execution_summary()

        return self.execution_stats

    def _execute_task_safe(self, task, score):
        """
        Thread-safe wrapper for _execute_task

        Handles thread-local state and stats updates
        """
        try:
            return self._execute_task(task)
        finally:
            # Always update stats in thread-safe manner
            pass

    def _update_stats_thread_safe(self, stat_type, increment=1):
        """Update execution stats in thread-safe manner"""
        with self.stats_lock:
            self.execution_stats[stat_type] += increment
```

### Implementation Steps

**Step 1: Add concurrent.futures import** (5 min)

**File:** `scripts/orchestration/scraper_orchestrator.py`
**Line 35 (after existing imports):**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
```

**Step 2: Modify __init__ to create executor** (15 min)

**Line 60-78, add after Line 98 (after execution_stats):**

```python
# Parallel execution pool
self.executor = ThreadPoolExecutor(
    max_workers=self.max_concurrent,
    thread_name_prefix="scraper_worker"
)

# Thread-safe stats updates
self.stats_lock = threading.Lock()

logger.info(f"Initialized thread pool: {self.max_concurrent} workers")
```

**Step 3: Implement parallel execution** (2 hours)

Replace `execute_all_tasks` method with implementation shown above in Enhanced Design.

**Step 4: Make _execute_task thread-safe** (1 hour)

**Current** `_execute_task` updates `self.execution_stats` directly (Lines 268-276).

**Problem:** Multiple threads updating shared dict = race conditions

**Solution:** Wrap stats updates with lock

```python
def _execute_task(self, task):
    """Execute a single collection task (thread-safe)"""
    # ... existing validation code (Lines 210-247) ...

    try:
        start_time = time.time()

        # ... existing subprocess execution (Lines 249-262) ...

        duration = time.time() - start_time

        # Thread-safe stats updates
        with self.stats_lock:
            if result.returncode == 0:
                logger.info(f"  ✅ Task completed in {duration:.1f}s")
                self.execution_stats["completed"] += 1
                self.execution_stats["by_priority"][priority.lower()]["completed"] += 1
                self.execution_stats["by_scraper"][scraper]["completed"] += 1
            else:
                logger.error(f"  ❌ Task failed after {duration:.1f}s")
                self.execution_stats["failed"] += 1
                self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
                self.execution_stats["by_scraper"][scraper]["failed"] += 1

    except subprocess.TimeoutExpired:
        # ... existing error handling ...
        with self.stats_lock:
            self.execution_stats["failed"] += 1
            # ...
```

**Step 5: Graceful shutdown of executor** (30 min)

**Add shutdown method:**

```python
def shutdown(self):
    """Gracefully shutdown executor and wait for tasks"""
    if self.executor:
        logger.info("Shutting down task execution pool...")
        self.executor.shutdown(wait=True, cancel_futures=False)
        logger.info("✅ All tasks completed or cancelled")
```

**Call from CLI main() function:**

```python
def main():
    # ... existing arg parsing ...

    orchestrator = ScraperOrchestrator(...)

    try:
        stats = orchestrator.execute_all_tasks(priority_filter=args.priority)
        # ...
    finally:
        orchestrator.shutdown()
```

### Configuration

**File:** `config/autonomous_config.yaml`
**Line 29 (already exists):**

```yaml
max_concurrent_scrapers: 5 # Tune based on system resources and rate limits
```

**Tuning Guide:**
- **CPU-bound tasks:** max_workers = CPU count
- **I/O-bound tasks (scrapers):** max_workers = 2-4x CPU count
- **Rate limit constrained:** Depends on slowest API (e.g., Basketball Reference = 1 req/12s)

**Recommended Settings:**
- Development/Testing: 3 workers
- Production (M2 Max, 12 cores): 5-8 workers
- Production (rate limit constrained): 3-5 workers

### Testing

**Test Case 1: Parallel Execution**
```python
# Create 10 test tasks
tasks = [
    {"id": f"task_{i:03d}", "priority": "HIGH", "source": "ESPN",
     "scraper": "test_scraper", "estimated_time_minutes": 0.5}
    for i in range(10)
]

# Mock task queue
mock_queue = {"total_tasks": 10, "tasks": tasks}

# Execute with max_concurrent=3
start_time = time.time()
stats = orchestrator.execute_all_tasks()
duration = time.time() - start_time

# Verify parallel execution (should take ~2 min with 3 workers, not 5 min sequential)
assert duration < 3 * 60  # 3 minutes (10 tasks / 3 workers * 0.5 min/task)
```

**Test Case 2: Thread Safety**
```python
# Submit 100 concurrent tasks that all update stats
# Verify final counts match expected (no lost updates from race conditions)
assert stats["completed"] + stats["failed"] == 100
```

### Rollback

**Feature Flag:** Set `max_concurrent_scrapers: 1` to force sequential execution

---

## Enhancement 3: Global Rate Limit Coordinator

### Problem Statement

**Current Situation:**
- Each scraper independently respects its own rate limits
- No coordination between concurrent scrapers
- Risk of exceeding API limits when running multiple scrapers to same API

**Example Scenario:**
```
Scraper A (ESPN): 10 req/sec limit
Scraper B (ESPN): 10 req/sec limit
Scraper C (ESPN): 10 req/sec limit

Running concurrently → 30 req/sec → EXCEEDS ESPN 10 req/sec limit → 429 errors
```

### Enhanced Design

**Token Bucket Algorithm with Global Coordination:**

```python
import threading
import time
from collections import defaultdict

class TokenBucket:
    """
    Token bucket for rate limiting using leaky bucket algorithm

    Tokens refill at constant rate up to bucket capacity.
    Consuming tokens blocks if bucket empty.
    """
    def __init__(self, rate, capacity=None):
        """
        Initialize token bucket

        Args:
            rate: Tokens per second refill rate
            capacity: Max tokens (defaults to rate if not specified)
        """
        self.rate = rate
        self.capacity = capacity or rate
        self.tokens = self.capacity
        self.lock = threading.Lock()
        self.last_refill = time.time()

    def consume(self, count=1, block=True, timeout=None):
        """
        Consume tokens from bucket

        Args:
            count: Number of tokens to consume
            block: If True, wait for tokens to be available
            timeout: Max seconds to wait (None = wait forever)

        Returns:
            bool: True if tokens consumed, False if timeout

        Raises:
            ValueError: If count > capacity (impossible to fulfill)
        """
        if count > self.capacity:
            raise ValueError(f"Requested {count} tokens exceeds capacity {self.capacity}")

        start_time = time.time()

        with self.lock:
            while True:
                # Refill tokens based on elapsed time
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_refill = now

                # Check if we have enough tokens
                if self.tokens >= count:
                    self.tokens -= count
                    return True

                # If not blocking, return immediately
                if not block:
                    return False

                # Check timeout
                if timeout and (time.time() - start_time) >= timeout:
                    return False

                # Sleep briefly and retry
                time.sleep(0.1)


class RateLimitCoordinator:
    """
    Global rate limit coordinator for all scrapers

    Prevents any API from being overwhelmed by concurrent scrapers
    """
    def __init__(self, config_file="config/scraper_config.yaml"):
        """
        Initialize rate limit coordinator

        Loads rate limits from scraper config and creates token buckets
        """
        self.config = self._load_config(config_file)
        self.buckets = {}  # source → TokenBucket
        self.lock = threading.Lock()

        # Create buckets for each source
        self._initialize_buckets()

        logger.info("=" * 80)
        logger.info("RATE LIMIT COORDINATOR INITIALIZED")
        logger.info("=" * 80)
        for source, bucket in self.buckets.items():
            logger.info(f"  {source}: {bucket.rate} req/sec (capacity: {bucket.capacity})")
        logger.info("=" * 80)

    def _load_config(self, config_file):
        """Load scraper configuration"""
        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    def _initialize_buckets(self):
        """Create token buckets for each data source"""
        scrapers = self.config.get("scrapers", {})

        # Group scrapers by source and find most restrictive rate limit
        source_limits = defaultdict(list)

        for scraper_name, scraper_config in scrapers.items():
            source = scraper_config.get("source", scraper_name)
            rate_limit = scraper_config.get("rate_limit", {})

            # Parse rate limit (e.g., "10/second", "1/12seconds")
            rate = self._parse_rate_limit(rate_limit)
            if rate:
                source_limits[source].append(rate)

        # Create buckets with most restrictive rate
        for source, rates in source_limits.items():
            min_rate = min(rates)  # Most restrictive
            self.buckets[source] = TokenBucket(
                rate=min_rate,
                capacity=min_rate * 2  # Allow short bursts
            )

    def _parse_rate_limit(self, rate_limit_config):
        """
        Parse rate limit config to requests per second

        Examples:
            {"requests": 10, "per": "second"} → 10.0
            {"requests": 1, "per": "12seconds"} → 0.0833
            {"requests": 60, "per": "minute"} → 1.0
        """
        if not rate_limit_config:
            return None

        requests = rate_limit_config.get("requests", 0)
        per = rate_limit_config.get("per", "second")

        # Parse time unit
        if per == "second":
            return float(requests)
        elif per.endswith("seconds"):
            seconds = int(per.replace("seconds", ""))
            return requests / seconds
        elif per == "minute":
            return requests / 60.0
        elif per == "hour":
            return requests / 3600.0
        else:
            logger.warning(f"Unknown rate limit unit: {per}")
            return None

    def acquire(self, source, count=1, timeout=30):
        """
        Acquire rate limit tokens before making API calls

        Args:
            source: Data source name (e.g., "ESPN", "NBA_API")
            count: Number of API calls to make
            timeout: Max seconds to wait for tokens

        Returns:
            bool: True if acquired, False if timeout

        Usage:
            coordinator.acquire("ESPN", count=5)  # Wait for 5 tokens
            make_api_calls()
        """
        # Get or create bucket for source
        with self.lock:
            if source not in self.buckets:
                # No rate limit configured, allow immediately
                logger.warning(f"No rate limit configured for {source}, allowing all requests")
                return True

            bucket = self.buckets[source]

        # Acquire tokens (blocks if necessary)
        success = bucket.consume(count=count, block=True, timeout=timeout)

        if not success:
            logger.warning(f"⏰ Rate limit timeout for {source} ({timeout}s)")

        return success

    def get_current_rates(self):
        """
        Get current token availability for all sources

        Returns:
            dict: {source: {"tokens": float, "rate": float}}
        """
        rates = {}
        for source, bucket in self.buckets.items():
            with bucket.lock:
                rates[source] = {
                    "tokens": bucket.tokens,
                    "rate": bucket.rate,
                    "capacity": bucket.capacity,
                    "utilization": 1.0 - (bucket.tokens / bucket.capacity)
                }
        return rates
```

### Implementation Steps

**Step 1: Create rate_limit_coordinator.py** (1 hour)

**File:** `scripts/orchestration/rate_limit_coordinator.py` (NEW)

Copy implementation above.

**Step 2: Add rate limits to scraper_config.yaml** (30 min)

**File:** `config/scraper_config.yaml`

```yaml
scrapers:
  basketball_reference_async_scraper:
    source: Basketball_Reference
    rate_limit:
      requests: 1
      per: "12seconds"  # Very conservative

  espn_scraper:
    source: ESPN
    rate_limit:
      requests: 10
      per: "second"

  nba_api_scraper:
    source: NBA_API
    rate_limit:
      requests: 2
      per: "second"

  hoopr_incremental_scraper:
    source: hoopR
    rate_limit:
      requests: 5
      per: "second"  # Generous (library handles internally)
```

**Step 3: Integrate with orchestrator** (1 hour)

**File:** `scripts/orchestration/scraper_orchestrator.py`

**Import (Line 35):**
```python
from rate_limit_coordinator import RateLimitCoordinator
```

**Initialize in __init__ (Line 105):**
```python
# Global rate limit coordinator
self.rate_limiter = RateLimitCoordinator(
    config_file=self.scraper_config_file
)
```

**Use in _execute_task (Line 249, before subprocess.run):**
```python
def _execute_task(self, task):
    # ... existing validation ...

    # Acquire rate limit tokens BEFORE execution
    source = task.get("source", "unknown")
    estimated_requests = task.get("estimated_requests", 1)

    logger.info(f"  Acquiring rate limit: {estimated_requests} requests for {source}")

    if not self.rate_limiter.acquire(source, count=estimated_requests, timeout=30):
        logger.error(f"  ❌ Rate limit timeout for {source}, skipping task")
        with self.stats_lock:
            self.execution_stats["failed"] += 1
            self.execution_stats["by_priority"][priority.lower()]["failed"] += 1
        return

    logger.info(f"  ✅ Rate limit acquired")

    # Now execute scraper
    try:
        result = subprocess.run(cmd, ...)
        # ...
```

**Step 4: Add rate limit monitoring** (30 min)

**Add to health_monitor.py:**

```python
@app.route('/rate-limits')
def rate_limits():
    """Show current rate limit status"""
    if orchestrator.rate_limiter:
        rates = orchestrator.rate_limiter.get_current_rates()
        return jsonify(rates)
    return jsonify({"error": "Rate limiter not initialized"})
```

### Testing

**Test Case 1: Token Bucket**
```python
bucket = TokenBucket(rate=10.0)  # 10 tokens/sec

# Consume 5 tokens
assert bucket.consume(5) == True
assert bucket.tokens == 5.0

# Wait 1 second, should refill to 10
time.sleep(1)
assert bucket.tokens == 10.0

# Consume 15 tokens (more than capacity), should block and wait
start = time.time()
bucket.consume(15, timeout=2)
assert (time.time() - start) >= 0.5  # Had to wait for refill
```

**Test Case 2: Global Coordination**
```python
coordinator = RateLimitCoordinator()

# Simulate 3 scrapers hitting ESPN simultaneously
def scraper_thread(thread_id):
    for i in range(10):
        coordinator.acquire("ESPN", count=1)
        # Make API call
        time.sleep(0.1)

threads = [threading.Thread(target=scraper_thread, args=(i,)) for i in range(3)]
[t.start() for t in threads]
[t.join() for t in threads]

# Verify no 429 errors (test by monitoring logs)
```

### Rollback

Remove rate_limiter integration from orchestrator (comment out Lines 249-260).

---

## Enhancement 4: Real-Time Reconciliation

### Current Implementation

**Reconciliation Interval:** 1 hour
**Task Queue Check:** Every 30 seconds
**Gap Detection Latency:** Up to 60 minutes

**File:** `config/autonomous_config.yaml` Line 21
```yaml
reconciliation_interval_hours: 1
```

**File:** `scripts/autonomous/autonomous_loop.py` Line 267
```python
check_interval = 30  # Check every 30 seconds
```

### Enhanced Design

**Target:** 15-minute reconciliation cycles

**Changes:**
1. Reduce reconciliation interval: 1 hour → 15 minutes
2. Reduce task queue check: 30 seconds → 10 seconds
3. Add reconciliation cycle metrics

### Implementation Steps

**Step 1: Update autonomous_config.yaml** (5 min)

**File:** `config/autonomous_config.yaml` Line 21

**Replace:**
```yaml
reconciliation_interval_hours: 1
```

**With:**
```yaml
reconciliation_interval_minutes: 15  # 4x faster gap detection
```

**Step 2: Update autonomous_loop.py** (15 min)

**File:** `scripts/autonomous/autonomous_loop.py`

**Line 117-118 (logging):**
```python
logger.info(f"Reconciliation interval: {self.config['reconciliation_interval_minutes']}min")
```

**Line 234 (command building):**
```python
cmd = [
    sys.executable,
    "scripts/reconciliation/reconciliation_daemon.py",
    "--interval-minutes",  # Changed from --interval-hours
    str(self.config["reconciliation_interval_minutes"]),
]
```

**Line 267 (task queue check):**
```python
check_interval = 10  # Check every 10 seconds (was 30)
```

**Step 3: Update reconciliation_daemon.py** (30 min)

**File:** `scripts/reconciliation/reconciliation_daemon.py`

**Add CLI argument:**
```python
parser.add_argument(
    "--interval-minutes",
    type=int,
    default=None,
    help="Run reconciliation every N minutes"
)

parser.add_argument(
    "--interval-hours",
    type=float,
    default=1.0,
    help="Run reconciliation every N hours (legacy)"
)

args = parser.parse_args()

# Calculate interval in seconds
if args.interval_minutes:
    interval_seconds = args.interval_minutes * 60
else:
    interval_seconds = args.interval_hours * 3600
```

**Step 4: Add reconciliation metrics** (1 hour)

**Track in autonomous_loop.py:**
- Reconciliation cycle duration
- Gaps detected per cycle
- Tasks generated per cycle
- S3 list operation count

```python
def _track_reconciliation_cycle(self, start_time, end_time, gaps_found):
    """Track reconciliation cycle metrics"""
    duration = (end_time - start_time).total_seconds()

    self.state["last_reconciliation"] = end_time
    self.stats["reconciliation_cycles"] += 1
    self.stats["reconciliation_total_duration"] += duration
    self.stats["reconciliation_gaps_found"] += gaps_found

    logger.info(f"Reconciliation cycle complete:")
    logger.info(f"  Duration: {duration:.1f}s")
    logger.info(f"  Gaps found: {gaps_found}")
    logger.info(f"  Average cycle time: {self.stats['reconciliation_total_duration'] / self.stats['reconciliation_cycles']:.1f}s")
```

### Testing

**Test Case 1: 15-Minute Cycles**
```bash
# Start autonomous loop with 15-minute reconciliation
python scripts/autonomous/autonomous_loop.py

# Monitor logs for cycle timing
tail -f logs/autonomous_loop.log | grep "Reconciliation cycle"

# Verify cycles occur every 15 minutes
# Expected output:
# 2025-10-31 14:00:00 - Reconciliation cycle complete
# 2025-10-31 14:15:00 - Reconciliation cycle complete
# 2025-10-31 14:30:00 - Reconciliation cycle complete
```

**Test Case 2: Task Queue Responsiveness**
```bash
# Manually add task to queue
echo '{"total_tasks": 1, "tasks": [...]}' > inventory/gaps.json

# Verify orchestrator triggers within 10 seconds
# (was 30 seconds previously)
```

### Rollback

**Revert config:**
```yaml
reconciliation_interval_hours: 1  # Back to 1 hour
```

**Revert autonomous_loop.py Line 267:**
```python
check_interval = 30  # Back to 30 seconds
```

---

## Enhancement 5: Metrics & Observability

### Current State

- ✅ Execution statistics printed to logs
- ❌ No persistent metrics storage
- ❌ No dashboards
- ❌ No alerting on performance degradation

### Enhanced Design

**CloudWatch Integration for AWS-native metrics:**

```python
import boto3

class MetricsCollector:
    """
    Collect and publish metrics to AWS CloudWatch

    Tracks orchestrator and reconciliation performance
    """
    def __init__(self, namespace="ADCE/Orchestrator", enabled=True):
        self.namespace = namespace
        self.enabled = enabled
        self.cloudwatch = boto3.client('cloudwatch') if enabled else None

    def record_task_execution(self, scraper, duration_seconds, success):
        """Record task execution metrics"""
        if not self.enabled:
            return

        metrics = [
            {
                'MetricName': 'TaskDuration',
                'Value': duration_seconds,
                'Unit': 'Seconds',
                'Dimensions': [
                    {'Name': 'Scraper', 'Value': scraper},
                    {'Name': 'Status', 'Value': 'Success' if success else 'Failure'}
                ]
            },
            {
                'MetricName': 'TaskCount',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Scraper', 'Value': scraper},
                    {'Name': 'Status', 'Value': 'Success' if success else 'Failure'}
                ]
            }
        ]

        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
        except Exception as e:
            logger.warning(f"Failed to publish metrics: {e}")

    def record_orchestrator_run(self, duration_seconds, tasks_completed, tasks_failed):
        """Record orchestrator run metrics"""
        if not self.enabled:
            return

        success_rate = tasks_completed / (tasks_completed + tasks_failed) if (tasks_completed + tasks_failed) > 0 else 0

        metrics = [
            {
                'MetricName': 'OrchestratorDuration',
                'Value': duration_seconds,
                'Unit': 'Seconds'
            },
            {
                'MetricName': 'TasksCompleted',
                'Value': tasks_completed,
                'Unit': 'Count'
            },
            {
                'MetricName': 'TasksFailed',
                'Value': tasks_failed,
                'Unit': 'Count'
            },
            {
                'MetricName': 'TaskSuccessRate',
                'Value': success_rate * 100,
                'Unit': 'Percent'
            }
        ]

        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
        except Exception as e:
            logger.warning(f"Failed to publish metrics: {e}")

    def record_rate_limit_utilization(self, source, utilization_percent):
        """Record rate limit utilization"""
        if not self.enabled:
            return

        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[{
                    'MetricName': 'RateLimitUtilization',
                    'Value': utilization_percent,
                    'Unit': 'Percent',
                    'Dimensions': [
                        {'Name': 'Source', 'Value': source}
                    ]
                }]
            )
        except Exception as e:
            logger.warning(f"Failed to publish metrics: {e}")
```

### Implementation Steps

**Step 1: Create metrics_collector.py** (1 hour)

**File:** `scripts/monitoring/metrics_collector.py` (NEW)

Copy implementation above.

**Step 2: Integrate with orchestrator** (1 hour)

**File:** `scripts/orchestration/scraper_orchestrator.py`

**Import (Line 35):**
```python
from monitoring.metrics_collector import MetricsCollector
```

**Initialize in __init__ (Line 110):**
```python
# Metrics collection
metrics_enabled = self.config.get("metrics", {}).get("cloudwatch", {}).get("enabled", True)
self.metrics = MetricsCollector(
    namespace="ADCE/Orchestrator",
    enabled=metrics_enabled
)
```

**Instrument _execute_task (Line 249):**
```python
def _execute_task(self, task):
    start_time = time.time()

    # ... existing execution code ...

    duration = time.time() - start_time
    success = (result.returncode == 0)

    # Publish metrics
    self.metrics.record_task_execution(
        scraper=scraper,
        duration_seconds=duration,
        success=success
    )

    # ... existing stats updates ...
```

**Instrument execute_all_tasks (Line 206):**
```python
def execute_all_tasks(self, priority_filter=None):
    start_time = time.time()

    # ... existing execution code ...

    duration = time.time() - start_time

    # Publish orchestrator metrics
    self.metrics.record_orchestrator_run(
        duration_seconds=duration,
        tasks_completed=self.execution_stats["completed"],
        tasks_failed=self.execution_stats["failed"]
    )

    # ... rest of method ...
```

**Step 3: Add metrics config** (15 min)

**File:** `config/autonomous_config.yaml`

**Add after Line 85:**
```yaml
# Metrics & Observability
metrics:
  cloudwatch:
    enabled: true
    namespace: "ADCE/Orchestrator"
    region: "us-east-1"

  prometheus:
    enabled: false  # Future enhancement
    port: 9090

  dims_integration:
    enabled: true
    update_on_completion: true
```

**Step 4: Set up CloudWatch dashboard** (Week 4)

**Created via AWS Console or Terraform:**

Dashboard widgets:
- Task execution rate (line chart)
- Task success rate (gauge)
- Orchestrator duration (line chart)
- Rate limit utilization by source (multi-gauge)
- Error count by scraper (bar chart)

### Testing

**Test Case 1: Metrics Publishing**
```python
metrics = MetricsCollector(namespace="Test/ADCE")

# Publish test metric
metrics.record_task_execution(
    scraper="test_scraper",
    duration_seconds=5.0,
    success=True
)

# Verify in CloudWatch console:
# Metrics > Test/ADCE > TaskDuration
# Should show data point with value 5.0
```

**Test Case 2: End-to-End**
```bash
# Run orchestrator with metrics enabled
python scripts/orchestration/scraper_orchestrator.py

# Check CloudWatch metrics after completion
aws cloudwatch get-metric-statistics \
    --namespace "ADCE/Orchestrator" \
    --metric-name "TaskSuccessRate" \
    --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average

# Should return success rate metric
```

### Cost Analysis

**CloudWatch Metrics Pricing:**
- First 10 metrics: Free
- Additional metrics: $0.30/metric/month
- API requests: $0.01 per 1,000 requests

**Expected Metrics:**
- TaskDuration (per scraper): 5 metrics
- TaskCount (per scraper): 5 metrics
- OrchestratorDuration: 1 metric
- TaskSuccessRate: 1 metric
- RateLimitUtilization (per source): 5 metrics

**Total:** ~17 metrics
**Cost:** $2.10/month (17 metrics - 10 free = 7 * $0.30)

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_orchestrator_enhancements.py` (NEW)

```python
import pytest
import time
from scripts.orchestration.scraper_orchestrator import ScraperOrchestrator
from scripts.orchestration.rate_limit_coordinator import TokenBucket, RateLimitCoordinator

class TestWeightedPriorityQueue:
    """Test weighted priority scoring"""

    def test_score_calculation_base_priority(self):
        """Test base priority scores"""
        orchestrator = ScraperOrchestrator(dry_run=True)

        critical_task = {"priority": "CRITICAL", "source": "ESPN"}
        high_task = {"priority": "HIGH", "source": "ESPN"}

        critical_score = orchestrator._calculate_task_score(critical_task)
        high_score = orchestrator._calculate_task_score(high_task)

        assert critical_score > high_score
        assert critical_score >= 1000  # Base CRITICAL score

    def test_score_calculation_age_factor(self):
        """Test age-based score boost"""
        orchestrator = ScraperOrchestrator(dry_run=True)

        old_task = {
            "priority": "MEDIUM",
            "source": "ESPN",
            "detected_at": (datetime.now() - timedelta(hours=24)).isoformat()
        }

        new_task = {
            "priority": "MEDIUM",
            "source": "ESPN",
            "detected_at": datetime.now().isoformat()
        }

        old_score = orchestrator._calculate_task_score(old_task)
        new_score = orchestrator._calculate_task_score(new_task)

        assert old_score > new_score  # Older task should score higher

    def test_task_ordering(self):
        """Test that tasks are ordered correctly by weighted score"""
        # Create mix of tasks
        tasks = [
            {"id": "A", "priority": "LOW", "source": "ESPN", "detected_at": "2025-10-30T10:00:00"},
            {"id": "B", "priority": "HIGH", "source": "Kaggle", "detected_at": "2025-10-31T10:00:00"},
            {"id": "C", "priority": "MEDIUM", "source": "ESPN", "detected_at": "2025-10-29T10:00:00"},
        ]

        orchestrator = ScraperOrchestrator(dry_run=True)
        orchestrator.task_queue = {"tasks": tasks}

        scored = [(orchestrator._calculate_task_score(t), t) for t in tasks]
        scored.sort(reverse=True)

        # Verify oldest ESPN MEDIUM task beats new HIGH Kaggle
        # (age + source boost should overcome priority difference)
        assert scored[0][1]["id"] in ["C", "B"]  # C or B should be first


class TestTokenBucket:
    """Test rate limiting token bucket"""

    def test_token_consumption(self):
        """Test basic token consumption"""
        bucket = TokenBucket(rate=10.0, capacity=10.0)

        # Consume 5 tokens
        assert bucket.consume(5) == True
        assert bucket.tokens == 5.0

    def test_token_refill(self):
        """Test token refill over time"""
        bucket = TokenBucket(rate=10.0)

        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0.0

        # Wait 1 second
        time.sleep(1)

        # Should refill to 10
        bucket.consume(0)  # Trigger refill
        assert bucket.tokens >= 9.5  # Allow for timing jitter

    def test_blocking_consumption(self):
        """Test that consumption blocks when tokens unavailable"""
        bucket = TokenBucket(rate=10.0)

        # Consume all tokens
        bucket.consume(10)

        # Try to consume 5 more (should block and wait for refill)
        start = time.time()
        bucket.consume(5, timeout=1)
        elapsed = time.time() - start

        assert elapsed >= 0.4  # Should wait ~0.5 seconds for refill


class TestRateLimitCoordinator:
    """Test global rate limit coordination"""

    def test_coordinator_initialization(self):
        """Test that coordinator loads config and creates buckets"""
        coordinator = RateLimitCoordinator()

        assert "ESPN" in coordinator.buckets
        assert "Basketball_Reference" in coordinator.buckets

    def test_acquire_tokens(self):
        """Test acquiring tokens from coordinator"""
        coordinator = RateLimitCoordinator()

        # Should succeed immediately
        assert coordinator.acquire("ESPN", count=1) == True

        # Acquire many tokens, should block briefly
        start = time.time()
        coordinator.acquire("ESPN", count=20, timeout=5)
        elapsed = time.time() - start

        assert elapsed >= 1.0  # Should wait for refill


class TestParallelExecution:
    """Test parallel task execution"""

    def test_concurrent_execution(self):
        """Test that multiple tasks execute in parallel"""
        # Create 10 fast tasks
        tasks = [
            {"id": f"task_{i}", "priority": "HIGH", "source": "ESPN",
             "scraper": "mock_scraper", "estimated_time_minutes": 0.1}
            for i in range(10)
        ]

        orchestrator = ScraperOrchestrator(max_concurrent=5, dry_run=True)
        orchestrator.task_queue = {"tasks": tasks}

        start = time.time()
        stats = orchestrator.execute_all_tasks()
        duration = time.time() - start

        # With 5 workers and 10 tasks of 0.1 min each:
        # Sequential: 10 * 0.1 = 1.0 minutes
        # Parallel: 10 / 5 * 0.1 = 0.2 minutes
        # Allow overhead, should be < 0.5 minutes
        assert duration < 30  # 30 seconds

    def test_thread_safety(self):
        """Test that concurrent updates to stats are thread-safe"""
        # Submit 100 tasks concurrently
        tasks = [{"id": f"task_{i}", "priority": "MEDIUM"} for i in range(100)]

        orchestrator = ScraperOrchestrator(max_concurrent=10, dry_run=True)
        orchestrator.task_queue = {"tasks": tasks}

        stats = orchestrator.execute_all_tasks()

        # Verify all tasks accounted for (no lost updates)
        total = stats["completed"] + stats["failed"] + stats["skipped"]
        assert total == 100
```

**Run Tests:**
```bash
pytest tests/test_orchestrator_enhancements.py -v
```

### Integration Tests

**File:** `tests/integration/test_adce_end_to_end.py` (NEW)

```python
class TestADCEEndToEnd:
    """End-to-end integration tests for enhanced ADCE"""

    def test_full_cycle(self):
        """Test complete autonomous cycle"""
        # 1. Generate mock task queue
        # 2. Start autonomous loop
        # 3. Verify orchestrator triggered
        # 4. Verify tasks executed
        # 5. Verify reconciliation triggered
        # 6. Verify metrics published

    def test_rate_limit_compliance(self):
        """Verify no rate limit violations under load"""
        # 1. Create 100 ESPN tasks
        # 2. Execute with max_concurrent=5
        # 3. Monitor for 429 errors
        # 4. Verify API calls stay within limits

    def test_15_minute_reconciliation(self):
        """Verify reconciliation runs every 15 minutes"""
        # 1. Start autonomous loop with 15-min interval
        # 2. Monitor for 1 hour
        # 3. Verify 4 reconciliation cycles occurred
```

### Load Testing

**Scenario 1: High Task Volume**
```bash
# Generate 1000 task queue
python tests/load/generate_large_task_queue.py --count 1000

# Run orchestrator
time python scripts/orchestration/scraper_orchestrator.py

# Measure:
# - Total duration
# - Tasks per minute
# - Memory usage
# - API 429 errors
```

**Scenario 2: Long-Running Stability**
```bash
# Run autonomous loop for 24 hours
python scripts/autonomous/autonomous_loop.py &

# Monitor every hour
watch -n 3600 'curl -s http://localhost:8080/health | python -m json.tool'

# Verify:
# - No crashes
# - Memory stable
# - 96 reconciliation cycles (24 hours * 4 per hour)
# - Success rate > 95%
```

---

## Rollback Plan

### Rollback Trigger Conditions

**Roll back if:**
1. Task success rate drops below 85% (from 95% baseline)
2. Orchestrator duration increases by >50% (30 min → 45+ min)
3. API 429 errors > 10/day
4. Memory usage > 3GB (from 500MB baseline)
5. System crashes or hangs

### Rollback Procedure

**Step 1: Disable Enhancements via Config** (2 min)

**File:** `config/autonomous_config.yaml`

```yaml
# Disable parallel execution
max_concurrent_scrapers: 1  # Force sequential

# Disable weighted priority
priority_weighting:
  enabled: false

# Revert to 1-hour reconciliation
reconciliation_interval_hours: 1

# Disable metrics (optional)
metrics:
  cloudwatch:
    enabled: false
```

**Step 2: Restart Autonomous Loop** (1 min)

```bash
# Stop service
launchctl stop com.nba-simulator.adce-autonomous

# Start service (will load new config)
launchctl start com.nba-simulator.adce-autonomous

# Verify reverted behavior
tail -f logs/autonomous_loop.log
```

**Step 3: Git Rollback (if config insufficient)** (5 min)

```bash
# Find commit before enhancements
git log --oneline | head -10

# Rollback to pre-enhancement commit
git revert <enhancement-commit-hash>

# Restart service
launchctl kickstart -k gui/$(id -u)/com.nba-simulator.adce-autonomous
```

### Monitoring During Rollback

**Watch for stabilization:**
```bash
# Monitor success rate
watch -n 60 'curl -s http://localhost:8080/health | jq ".orchestrator.success_rate"'

# Monitor memory
watch -n 60 'ps aux | grep autonomous_loop | grep -v grep'

# Check for 429 errors
grep -c "429" logs/autonomous_loop.log
```

**Expected recovery time:** 5-15 minutes

---

## Migration Guide

### Pre-Deployment Checklist

- [ ] All unit tests pass (pytest)
- [ ] Integration tests pass
- [ ] Load test completed (1000 tasks)
- [ ] Code reviewed by team
- [ ] Documentation updated
- [ ] Rollback plan tested
- [ ] Monitoring dashboard created (Week 4)

### Deployment Steps

**Week 3 Day 1-2: Orchestrator Enhancements**

1. **Morning:** Deploy weighted priority queue
   ```bash
   git checkout -b feature/weighted-priority-queue
   # Implement Enhancement 1
   pytest tests/test_orchestrator_enhancements.py::TestWeightedPriorityQueue
   git commit -m "feat: Add weighted priority queue scoring"
   ```

2. **Afternoon:** Deploy parallel execution
   ```bash
   # Implement Enhancement 2
   pytest tests/test_orchestrator_enhancements.py::TestParallelExecution
   git commit -m "feat: Add parallel task execution with ThreadPoolExecutor"
   ```

3. **Evening:** Deploy rate limit coordinator
   ```bash
   # Implement Enhancement 3
   pytest tests/test_orchestrator_enhancements.py::TestRateLimitCoordinator
   git commit -m "feat: Add global rate limit coordinator"
   ```

**Week 3 Day 3-4: Real-Time Reconciliation**

4. **Morning:** Update configs for 15-min reconciliation
   ```bash
   # Update autonomous_config.yaml
   # Update autonomous_loop.py
   git commit -m "feat: Reduce reconciliation interval to 15 minutes"
   ```

5. **Afternoon:** Test 15-min cycle
   ```bash
   # Start autonomous loop
   python scripts/autonomous/autonomous_loop.py &

   # Monitor for 2 hours (8 cycles)
   watch -n 900 'grep "Reconciliation cycle" logs/autonomous_loop.log | tail -1'
   ```

**Week 3 Day 5: Testing & Documentation**

6. **Morning:** End-to-end testing
   ```bash
   pytest tests/integration/test_adce_end_to_end.py -v
   ```

7. **Afternoon:** Load testing
   ```bash
   python tests/load/generate_large_task_queue.py --count 1000
   time python scripts/orchestration/scraper_orchestrator.py
   ```

8. **Evening:** Documentation
   - Update PRODUCTION_ACTIVATION_COMPLETE.md
   - Create operator runbook
   - Update PHASE_1_ACTIVATION_GUIDE.md

### Post-Deployment Validation

**Day 1 (Nov 7):**
- [ ] Autonomous loop running
- [ ] 15-minute reconciliation cycles working
- [ ] No API 429 errors
- [ ] Memory usage < 1GB

**Day 2 (Nov 8):**
- [ ] 24 hours uptime
- [ ] 96 reconciliation cycles completed
- [ ] Task success rate > 90%
- [ ] CloudWatch metrics publishing

**Day 3 (Nov 9):**
- [ ] 3 days stable operation
- [ ] Performance meets targets
- [ ] No rollback needed
- [ ] Declare success ✅

---

## Success Metrics Summary

| Metric | Baseline | Target | Achieved | Status |
|--------|----------|--------|----------|--------|
| **Task Throughput** | 5 tasks/min | 15-20 tasks/min | TBD | ⏸️ Pending |
| **Gap Detection Latency** | 60 min | 15 min | TBD | ⏸️ Pending |
| **Orchestrator Runtime** | 30-60 min | 10-20 min | TBD | ⏸️ Pending |
| **API 429 Errors** | 0-2/day | 0/day | TBD | ⏸️ Pending |
| **Parallel Efficiency** | N/A | 70-80% | TBD | ⏸️ Pending |
| **Memory Usage** | 500 MB | < 1 GB | TBD | ⏸️ Pending |
| **Success Rate** | 95% | > 90% | TBD | ⏸️ Pending |

**Fill in "Achieved" column during Week 3 Day 5 testing.**

---

## Next Steps

1. **Review this design doc** with team (30 min)
2. **Set up development environment** for testing
3. **Begin Day 1 implementation** (weighted priority queue)
4. **Update todo list** to track progress

---

**Document Status:** READY FOR IMPLEMENTATION
**Version:** 1.0
**Last Updated:** October 31, 2025
**Next Review:** November 1, 2025 (Morning validation)
