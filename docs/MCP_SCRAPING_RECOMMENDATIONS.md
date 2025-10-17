# MCP Web Scraping Recommendations for Overnight Jobs

**Created:** October 12, 2025
**Context:** Basketball Reference overnight scraping (9 data types, 1947-2025)
**Note:** MCP book library currently empty - recommendations based on established best practices

---

## Critical Recommendations

### 1. Rate Limiting & Politeness ⭐⭐⭐

**Current Status:** ✅ 12s rate limit working (no 429 errors)

**Recommendations:**
- **Keep 12s minimum** - working well, don't reduce
- **Add random jitter:** 12s ± 2s (10-14s range) to appear more human
- **Implement exponential backoff:** On any error, increase delay (12s → 24s → 48s)
- **Respect robots.txt:** Check `basketball-reference.com/robots.txt` for guidelines
- **Monitor response times:** If server responses slow down, increase delay

**Implementation:**
```python
import random
import time

def rate_limited_request(url, base_delay=12):
    jitter = random.uniform(-2, 2)
    delay = max(base_delay + jitter, 10)  # Never less than 10s
    time.sleep(delay)
    return requests.get(url)
```

---

### 2. Error Recovery & Checkpointing ⭐⭐⭐

**Current Status:** ✅ Incremental scraper has checkpointing

**Recommendations:**
- **Atomic writes:** Write to temp file, then atomic rename
- **Progress markers:** Track completed seasons in `.complete` files
- **Error log:** Separate error log with stack traces
- **Resume logic:** Always check for existing data before scraping
- **Partial save:** Save immediately after each item (current approach is correct)

**Implementation:**
```python
def save_with_checkpoint(data, season, data_type):
    temp_file = f"/tmp/bbref_{data_type}_{season}.json.tmp"
    final_file = f"/tmp/bbref_{data_type}_{season}.json"
    complete_marker = f"/tmp/bbref_{data_type}_{season}.complete"

    # Write to temp
    with open(temp_file, 'w') as f:
        json.dump(data, f)

    # Atomic rename
    os.rename(temp_file, final_file)

    # Create completion marker
    Path(complete_marker).touch()
```

---

### 3. Anti-Blocking Strategies ⭐⭐⭐

**Current Status:** ⚠️ HTTP 403 blocking some scrapers

**Recommendations (Priority Order):**

#### A. User-Agent Rotation (Easy, High Impact)
```python
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
]

headers = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

#### B. Session Management (Medium, High Impact)
```python
session = requests.Session()
# Reuse same session for multiple requests
# Maintains cookies and connection pooling
```

#### C. Request Headers (Easy, Medium Impact)
Add realistic browser headers:
- `Referer`: Previous Basketball Reference page
- `Accept-Language`: en-US,en;q=0.9
- `Cache-Control`: max-age=0

#### D. IP Rotation (Hard, High Impact)
- **Residential proxies:** Rotate through proxy pool
- **Cost:** $50-200/month for proxy service
- **Services:** Bright Data, Oxylabs, SmartProxy
- **Note:** Only implement if user-agent rotation fails

---

### 4. Data Validation During Scraping ⭐⭐

**Recommendations:**
- **Response validation:** Check HTTP status, content-length, content-type
- **Structure validation:** Verify expected tables/divs exist
- **Data sanity:** Check record counts (e.g., draft should have ~60 picks)
- **Fail fast:** If 5 consecutive errors, stop and alert
- **Sample checking:** Log first record of each season for manual review

**Implementation:**
```python
def validate_response(response, season):
    if response.status_code != 200:
        log.error(f"HTTP {response.status_code} for {season}")
        return False

    if len(response.content) < 1000:
        log.error(f"Suspiciously small response for {season}")
        return False

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', id='draft_stats')
    if not table:
        log.error(f"No draft table found for {season}")
        return False

    rows = table.find_all('tr')
    if len(rows) < 10:
        log.error(f"Too few draft picks for {season}: {len(rows)}")
        return False

    return True
```

---

### 5. Graceful Degradation ⭐⭐

**Recommendations:**
- **Skip, don't fail:** If one season fails 3 times, skip and continue
- **Error budget:** Allow up to 10% failure rate, then stop
- **Data type priority:** If errors increase, stop lower-priority types
- **Alert on threshold:** If error rate > 5%, send alert (log prominently)

**Implementation:**
```python
class ScraperStats:
    def __init__(self):
        self.total_attempts = 0
        self.total_errors = 0
        self.consecutive_errors = 0

    def record_success(self):
        self.total_attempts += 1
        self.consecutive_errors = 0

    def record_error(self):
        self.total_attempts += 1
        self.total_errors += 1
        self.consecutive_errors += 1

    def should_continue(self):
        error_rate = self.total_errors / max(self.total_attempts, 1)
        if error_rate > 0.10:  # 10% error budget
            return False
        if self.consecutive_errors > 5:
            return False
        return True
```

---

### 6. Monitoring & Observability ⭐⭐

**Recommendations:**
- **Structured logging:** JSON logs with timestamp, season, data_type, duration
- **Progress indicators:** Log "Season X/Y complete" every season
- **ETA calculation:** Estimate completion time based on current rate
- **Heartbeat:** Log "Still alive" message every 10 minutes
- **Summary stats:** Log totals every 10 seasons (X completed, Y errors, ETA)

**Implementation:**
```python
import logging
import json
from datetime import datetime, timedelta

def log_progress(season, total_seasons, start_time):
    elapsed = (datetime.now() - start_time).total_seconds()
    rate = season / elapsed  # seasons per second
    remaining = total_seasons - season
    eta_seconds = remaining / rate
    eta = datetime.now() + timedelta(seconds=eta_seconds)

    log.info(json.dumps({
        'type': 'progress',
        'season': season,
        'total': total_seasons,
        'elapsed_seconds': elapsed,
        'eta': eta.isoformat(),
        'rate_per_hour': rate * 3600
    }))
```

---

### 7. Resource Management ⭐

**Recommendations:**
- **Memory limits:** Clear soup objects after each request
- **Disk space checks:** Verify 10GB available before starting
- **Connection pooling:** Reuse HTTP connections (use requests.Session)
- **Temp file cleanup:** Delete temp files after S3 upload
- **Process monitoring:** Log PID, memory usage every 30 minutes

---

### 8. S3 Upload Optimization ⭐

**Recommendations:**
- **Batch uploads:** Upload every 10 files, not one-by-one
- **Retry logic:** Retry S3 uploads 3 times with exponential backoff
- **Upload verification:** Verify file exists in S3 after upload
- **Local retention:** Keep local copy until S3 verified (current approach)

---

## Priority Implementation Order

### Immediate (Deploy Tonight):
1. ✅ User-Agent rotation
2. ✅ Request header improvements
3. ✅ Session management
4. ✅ Enhanced logging with ETA
5. ✅ Data validation checks

### Short-Term (Next 2-3 Days):
6. Error budget implementation
7. Structured JSON logging
8. Automated alerts on high error rates

### Medium-Term (If Still Blocked):
9. IP/proxy rotation (if HTTP 403 persists)
10. Headless browser (Selenium/Playwright) as last resort

---

## HTTP 403 Specific Strategies

If still seeing HTTP 403 with recommendations above:

### Option A: Gradual Ramp-Up
- Start with 20s delay
- After 10 successful requests, reduce to 15s
- After 50 successful requests, reduce to 12s
- If any 403, increase delay by 5s

### Option B: Time-Based Scraping
- Basketball Reference may have rate limits per time window
- Scrape 50 requests, then wait 10 minutes
- This mimics human browsing patterns

### Option C: Referer Chain
- Always include previous Basketball Reference URL as Referer
- Start from homepage, navigate to draft page, then to specific year
- Builds realistic browsing session

---

## Recommended Tools

### For Anti-Blocking:
- **cloudscraper:** `pip install cloudscraper` - Bypasses Cloudflare
- **playwright:** `pip install playwright` - Full browser automation
- **requests-html:** `pip install requests-html` - JavaScript rendering

### For Monitoring:
- **tqdm:** `pip install tqdm` - Progress bars
- **rich:** `pip install rich` - Beautiful console output

---

## Testing Strategy

Before overnight run:

1. **Dry run:** Test with 3 seasons, verify all saves working
2. **Error injection:** Simulate failures, verify resume works
3. **Rate limit test:** Verify delays are correct (log timestamps)
4. **S3 verification:** Confirm uploads work before starting
5. **Monitor first hour:** Stay online first 60 minutes, catch issues early

---

## Red Flags to Stop Scraper

Stop immediately if:
- ❌ Error rate > 10%
- ❌ 5 consecutive HTTP 403 errors
- ❌ No successful requests in 30 minutes
- ❌ Disk space < 5GB
- ❌ Memory usage > 2GB (indicates leak)

---

## Success Metrics

Target for overnight run:
- ✅ Error rate < 5%
- ✅ 95%+ seasons successfully scraped
- ✅ All data validated and uploaded to S3
- ✅ Resume from checkpoint works if interrupted
- ✅ No data loss on any failure

---

*Generated: October 12, 2025*
*Based on: Industry best practices, existing scraper analysis, Basketball Reference characteristics*


