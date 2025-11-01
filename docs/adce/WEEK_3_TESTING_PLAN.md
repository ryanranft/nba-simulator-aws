# Week 3 Day 5: Comprehensive Testing & Validation Plan

**Created:** November 1, 2025
**Status:** Active
**Owner:** NBA Simulator Dev Team
**Purpose:** Validate all Week 3 ADCE enhancements in production

---

## Overview

This document outlines comprehensive testing procedures for validating the four Week 3 enhancements deployed to production on November 1, 2025 at 7:35 AM CDT.

**Enhancements Under Test:**
1. Weighted Priority Queue (Enhancement #1)
2. Parallel Execution with ThreadPoolExecutor (Enhancement #2)
3. Global Rate Limit Coordinator (Enhancement #3)
4. 15-Minute Real-Time Reconciliation (Enhancement #4)

**Testing Duration:** 24-48 hours
**Success Criteria:** All tests pass with ≥95% success rate

---

## Test Suite 1: Real-Time Reconciliation (15-Minute Cycles)

### Objective
Verify that reconciliation now runs every 15 minutes instead of 60 minutes, reducing gap detection latency by 4x.

### Test Cases

#### TC-1.1: Cycle Interval Validation
**Duration:** 2 hours
**Expected Cycles:** 8 cycles (every 15 minutes)

**Procedure:**
```bash
# Monitor reconciliation cycles
tail -f logs/autonomous_loop.log | grep -i "reconciliation\|cycle"
```

**Success Criteria:**
- ✅ Reconciliation cycles occur every 15 ± 1 minutes
- ✅ No missed cycles during 2-hour window
- ✅ Cycle duration < 5 minutes per cycle

**Data Collection:**
- Record timestamp of each cycle start
- Record cycle duration
- Count total cycles in 2-hour window

**Expected Results:**
```
Cycle 1: 07:50 AM (duration: ~30s)
Cycle 2: 08:05 AM (duration: ~30s)
Cycle 3: 08:20 AM (duration: ~30s)
...
Cycle 8: 09:35 AM (duration: ~30s)
```

---

#### TC-1.2: Task Queue Responsiveness
**Duration:** 30 minutes
**Purpose:** Verify orchestrator triggers within 10 seconds of task detection

**Procedure:**
```bash
# Watch for task queue updates
watch -n 1 'cat inventory/gaps.json | jq ".total_tasks"'
```

**Success Criteria:**
- ✅ Orchestrator triggers ≤ 10 seconds after tasks appear
- ✅ Previous behavior: 30 seconds → New: 10 seconds (3x improvement)

---

#### TC-1.3: Gap Detection Latency
**Purpose:** Measure total time from gap occurrence to data collection

**Test Scenario:**
1. Identify a live NBA game
2. Record game end time
3. Measure time until gap detected
4. Measure time until data collected

**Success Criteria:**
- ✅ Gap detection: < 15 minutes from game end
- ✅ Data collection: < 25 minutes total (was ~75-90 minutes)
- ✅ 3.6x improvement over previous system

---

## Test Suite 2: Weighted Priority Queue

### Objective
Verify intelligent task prioritization using multi-factor scoring.

### Test Cases

#### TC-2.1: Score Calculation Validation
**Purpose:** Verify weighted scoring algorithm works correctly

**Procedure:**
```bash
# Trigger reconciliation with known gaps
# Check orchestrator logs for task scores

tail -f logs/autonomous_loop.log | grep "score:"
```

**Test Data Setup:**
Create test gaps with known characteristics:
- Gap A: CRITICAL priority, ESPN source, 2 hours old, 1 missing file
- Gap B: HIGH priority, NBA_API source, 6 hours old, 5 missing files
- Gap C: MEDIUM priority, Basketball Reference, 24 hours old, 3 missing files

**Expected Scores:**
```
Gap A: ~1000 + (2 * 0.5) + (1000 * 1.5) + 0.1 = ~2501 points
Gap B: ~100 + (6 * 0.5) + (100 * 1.3) - 0.5 = ~232.5 points
Gap C: ~10 + (24 * 0.5) + (10 * 1.2) - 0.3 = ~33.7 points
```

**Success Criteria:**
- ✅ Scores calculated correctly (±5% tolerance)
- ✅ Tasks executed in score order (highest first)
- ✅ Age escalation working (older gaps score higher)

---

#### TC-2.2: Source Priority Validation
**Purpose:** Verify source multipliers affect execution order

**Procedure:**
1. Create equal-priority tasks from different sources
2. Observe execution order

**Expected Order:**
1. ESPN tasks (1.5x multiplier)
2. NBA_API tasks (1.3x multiplier)
3. Basketball Reference tasks (1.2x multiplier)
4. hoopR tasks (1.1x multiplier)

**Success Criteria:**
- ✅ Source multipliers applied correctly
- ✅ ESPN tasks prioritized when priorities equal

---

#### TC-2.3: Backward Compatibility
**Purpose:** Verify legacy priority-only mode still works

**Procedure:**
```yaml
# Temporarily disable weighted scoring
priority_weighting:
  enabled: false
```

**Success Criteria:**
- ✅ System falls back to simple priority groups
- ✅ CRITICAL → HIGH → MEDIUM → LOW order preserved
- ✅ No errors when weighted scoring disabled

---

## Test Suite 3: Parallel Execution

### Objective
Verify concurrent scraper execution with thread safety and performance improvement.

### Test Cases

#### TC-3.1: Concurrent Execution Validation
**Purpose:** Verify up to 5 scrapers run concurrently

**Procedure:**
1. Generate task queue with 10+ tasks
2. Monitor orchestrator execution
3. Count concurrent scrapers

**Monitoring:**
```bash
# Watch for concurrent execution
tail -f logs/autonomous_loop.log | grep "Executing:"

# Monitor process count
watch -n 1 'ps aux | grep scraper | wc -l'
```

**Success Criteria:**
- ✅ Up to 5 scrapers run concurrently (max_concurrent=5)
- ✅ Never exceeds 5 concurrent processes
- ✅ Task completion time 3-5x faster than sequential

**Performance Benchmark:**
- 10 tasks, 30 seconds each:
  - Sequential: 300 seconds (5 minutes)
  - Parallel (5 workers): 60 seconds (1 minute)
  - **Expected: 60-90 seconds**

---

#### TC-3.2: Thread Safety Validation
**Purpose:** Verify statistics updates are thread-safe (no race conditions)

**Procedure:**
1. Execute 20+ tasks concurrently
2. Check final statistics

**Success Criteria:**
- ✅ `completed + failed + skipped = total_tasks` (exact match)
- ✅ No lost updates (race condition would cause mismatch)
- ✅ By-priority and by-scraper stats accurate

**Validation:**
```bash
# After orchestrator completes
cat logs/autonomous_loop.log | grep "EXECUTION SUMMARY" -A 20
```

---

#### TC-3.3: Graceful Shutdown Validation
**Purpose:** Verify clean shutdown during parallel execution

**Procedure:**
1. Start orchestrator with 10+ tasks
2. Send SIGINT (Ctrl+C) during execution
3. Observe shutdown behavior

**Success Criteria:**
- ✅ Running tasks complete before shutdown
- ✅ Queued tasks not started
- ✅ No zombie processes
- ✅ Statistics saved correctly

---

## Test Suite 4: Global Rate Limit Coordinator

### Objective
Verify API rate limiting prevents violations across concurrent scrapers.

### Test Cases

#### TC-4.1: Rate Limit Enforcement
**Purpose:** Verify requests stay within configured limits

**Procedure:**
1. Configure strict rate limits (for testing):
```yaml
rate_limiting:
  source_limits:
    espn:
      requests_per_minute: 10  # Low limit for testing
```
2. Execute 20+ ESPN tasks concurrently
3. Monitor rate limiting stats

**Success Criteria:**
- ✅ Requests never exceed 10/minute for ESPN
- ✅ Rate limiter blocks requests when approaching limit
- ✅ No 429 (Too Many Requests) errors from APIs

**Validation:**
```bash
# Check rate limiting stats in execution summary
tail -200 logs/autonomous_loop.log | grep -A 10 "Rate Limiting:"
```

**Expected Output:**
```
Rate Limiting:
  Global: 45/100 req/min, 850/5000 req/hour
  By Source:
    espn: 9/10 req/min, tokens=1.2
    nba_api: 15/30 req/min, tokens=8.5
```

---

#### TC-4.2: Per-Source Limit Validation
**Purpose:** Verify different sources have independent limits

**Procedure:**
1. Execute tasks from multiple sources simultaneously
2. Monitor per-source request counts

**Success Criteria:**
- ✅ ESPN: ≤ 60 requests/minute
- ✅ NBA_API: ≤ 30 requests/minute
- ✅ Basketball Reference: ≤ 20 requests/minute, ≥3s between requests
- ✅ hoopR: ≤ 40 requests/minute

---

#### TC-4.3: Burst Handling
**Purpose:** Verify token bucket algorithm allows bursts

**Procedure:**
1. Let rate limiter idle (tokens accumulate)
2. Execute 10 ESPN tasks rapidly
3. Observe burst allowance

**Success Criteria:**
- ✅ First 10 tasks execute immediately (burst_size=10)
- ✅ 11th task waits for token refill
- ✅ Smooth execution after burst

---

#### TC-4.4: Exponential Backoff
**Purpose:** Verify backoff when approaching limits

**Procedure:**
1. Execute many tasks for single source
2. Monitor delays as limit approached

**Success Criteria:**
- ✅ Delays increase when > 80% of limit used
- ✅ Delays follow exponential pattern (1s → 2s → 4s → ...)
- ✅ Maximum delay capped at 30 seconds

---

## Test Suite 5: Integration Testing

### Objective
Verify all four enhancements work together correctly.

### Test Cases

#### TC-5.1: Full System Integration
**Duration:** 4 hours
**Purpose:** All enhancements active simultaneously

**Scenario:**
1. Generate 50+ tasks with mixed priorities and sources
2. Let system process autonomously
3. Monitor for 4 hours (16 reconciliation cycles)

**Success Criteria:**
- ✅ All 4 enhancements operational
- ✅ No conflicts or errors
- ✅ Task completion rate ≥ 95%
- ✅ Zero API rate limit violations
- ✅ All 16 reconciliation cycles complete on schedule

---

#### TC-5.2: Load Testing
**Purpose:** Verify system handles heavy load

**Test Setup:**
- 100+ tasks across all sources
- Mixed priorities
- Run during peak hours

**Success Criteria:**
- ✅ System remains stable
- ✅ Memory usage < 500 MB
- ✅ CPU usage < 80% average
- ✅ All tasks complete within 6 hours

---

#### TC-5.3: Edge Cases
**Purpose:** Test unusual scenarios

**Test Cases:**
- Empty task queue (no gaps)
- Single CRITICAL task
- All tasks from one source
- Tasks with duplicate game IDs
- Scraper failures during execution

**Success Criteria:**
- ✅ Graceful handling of all edge cases
- ✅ Appropriate error messages
- ✅ System recovers automatically

---

## Test Suite 6: Performance Benchmarks

### Objective
Measure actual performance improvements.

### Benchmarks

#### Benchmark 1: End-to-End Latency
**Metric:** Time from gap occurrence to data collected

**Test:**
- Monitor live game completion
- Measure total time to collection

**Baseline (Week 2):** 75-90 minutes
**Target (Week 3):** 25-35 minutes
**Improvement:** 3x faster

---

#### Benchmark 2: Task Processing Throughput
**Metric:** Tasks completed per hour

**Test:**
- 50 tasks, measure completion time

**Baseline:** ~6 tasks/hour (sequential, 10 min each)
**Target:** ~25-30 tasks/hour (5 parallel workers)
**Improvement:** 4-5x faster

---

#### Benchmark 3: Reconciliation Overhead
**Metric:** Reconciliation cycle duration

**Test:**
- Measure 10 reconciliation cycles
- Calculate average duration

**Target:** < 2 minutes per cycle (was 3-5 minutes)

---

## Test Execution Schedule

### Day 1 (November 1, 2025)

**Morning (7:00 AM - 12:00 PM):**
- ✅ Deploy Week 3 enhancements (COMPLETE)
- ✅ Monitor first 15-minute cycle (COMPLETE)
- Run TC-1.1: Cycle Interval Validation (2 hours)
- Run TC-1.2: Task Queue Responsiveness
- Run TC-4.1: Rate Limit Enforcement

**Afternoon (12:00 PM - 6:00 PM):**
- Run TC-2.1: Score Calculation Validation
- Run TC-2.2: Source Priority Validation
- Run TC-3.1: Concurrent Execution Validation
- Run TC-3.2: Thread Safety Validation

**Evening (6:00 PM - 11:00 PM):**
- Run TC-5.1: Full System Integration (start 4-hour test)
- Monitor live game data collection
- Benchmark 1: End-to-End Latency

### Day 2 (November 2, 2025)

**Morning (7:00 AM - 12:00 PM):**
- Review overnight integration test results
- Run TC-4.2: Per-Source Limit Validation
- Run TC-4.3: Burst Handling
- Run TC-5.2: Load Testing

**Afternoon (12:00 PM - 6:00 PM):**
- Run TC-5.3: Edge Cases
- Benchmark 2: Task Processing Throughput
- Benchmark 3: Reconciliation Overhead
- Run TC-2.3: Backward Compatibility

**Evening (6:00 PM - 11:00 PM):**
- Final validation checks
- Prepare test completion report
- Document any issues found

---

## Success Criteria Summary

### Must Pass (Critical)
- ✅ 15-minute reconciliation cycles (TC-1.1)
- ✅ Thread-safe parallel execution (TC-3.2)
- ✅ Rate limits enforced (TC-4.1)
- ✅ No API violations for 24 hours
- ✅ System stability ≥ 24 hours

### Should Pass (Important)
- Weighted scoring accuracy ±5% (TC-2.1)
- 3x latency improvement (Benchmark 1)
- 4x throughput improvement (Benchmark 2)
- Graceful error handling (TC-5.3)

### Nice to Have (Optimizations)
- Burst handling smooth (TC-4.3)
- Memory usage optimized
- CPU usage < 50% average

---

## Issue Tracking

### Issue Template

```markdown
**Issue ID:** WEEK3-XXX
**Test Case:** TC-X.X
**Severity:** Critical / High / Medium / Low
**Status:** Open / In Progress / Resolved

**Description:**
[What went wrong]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]

**Logs:**
```
[Relevant log excerpts]
```

**Resolution:**
[How it was fixed, or N/A if still open]
```

---

## Test Data Management

### Test Gap Generation Script

```bash
#!/bin/bash
# scripts/testing/generate_test_gaps.sh
# Create artificial gaps for testing

# Generate test gaps with different characteristics
python -c "
import json
from datetime import datetime, timedelta

gaps = []

# Gap A: CRITICAL, ESPN, 2 hours old, 1 file
gaps.append({
    'id': 'test-gap-001',
    'priority': 'CRITICAL',
    'source': 'espn',
    'detected_at': (datetime.now() - timedelta(hours=2)).isoformat(),
    'gap_size': 1,
    'scraper': 'espn_boxscore_scraper'
})

# Gap B: HIGH, NBA_API, 6 hours old, 5 files
gaps.append({
    'id': 'test-gap-002',
    'priority': 'HIGH',
    'source': 'nba_api',
    'detected_at': (datetime.now() - timedelta(hours=6)).isoformat(),
    'gap_size': 5,
    'scraper': 'nba_api_boxscore_scraper'
})

# Save to test gaps file
with open('inventory/test_gaps.json', 'w') as f:
    json.dump({
        'total_tasks': len(gaps),
        'tasks': gaps
    }, f, indent=2)

print(f'Generated {len(gaps)} test gaps')
"
```

---

## Test Environment

### Configuration Backup

Before testing, backup current configuration:
```bash
cp config/autonomous_config.yaml config/autonomous_config.yaml.backup
cp inventory/gaps.json inventory/gaps.json.backup
```

### Rollback Procedure

If critical issues found:
```bash
# Stop services
python scripts/autonomous/autonomous_cli.py stop

# Restore backup config
cp config/autonomous_config.yaml.backup config/autonomous_config.yaml

# Restart with original configuration
python scripts/autonomous/autonomous_cli.py start
```

---

## Monitoring Dashboard

### Key Metrics to Watch

```bash
# Real-time monitoring script
watch -n 10 '
echo "=== WEEK 3 ENHANCEMENTS MONITORING ==="
echo ""
echo "System Status:"
python scripts/autonomous/autonomous_cli.py status | grep -A 5 "Status:"
echo ""
echo "Recent Reconciliation:"
tail -5 logs/autonomous_loop.log | grep reconciliation
echo ""
echo "Task Queue:"
cat inventory/gaps.json | jq ".total_tasks"
echo ""
echo "Rate Limiting Stats:"
tail -100 logs/autonomous_loop.log | grep "Rate Limiting:" -A 10 | tail -10
'
```

---

## Reporting

### Daily Test Report Template

```markdown
# Week 3 Testing - Day X Report

**Date:** YYYY-MM-DD
**Testing Duration:** X hours
**Tests Executed:** X/Y
**Tests Passed:** X
**Tests Failed:** Y
**Issues Found:** Z

## Test Results

| Test ID | Name | Status | Notes |
|---------|------|--------|-------|
| TC-1.1 | Cycle Interval | PASS/FAIL | ... |
| TC-1.2 | Queue Response | PASS/FAIL | ... |
...

## Performance Metrics

- Reconciliation interval: X minutes
- Task throughput: X tasks/hour
- End-to-end latency: X minutes
- Error rate: X%

## Issues

[List any issues found]

## Next Steps

[What to test next]
```

---

## Completion Criteria

Week 3 Day 5 testing is **COMPLETE** when:

- [ ] All critical tests pass (100%)
- [ ] All important tests pass (≥95%)
- [ ] 24-hour stability test completed
- [ ] Performance benchmarks meet targets
- [ ] No critical or high-severity issues open
- [ ] Test completion report documented
- [ ] Deployment validated production-ready

**Estimated Completion:** November 2-3, 2025

---

**Document Version:** 1.0
**Last Updated:** November 1, 2025 07:40 AM CDT
**Next Review:** After test completion
