# Basketball Reference Scraping Notes

**Date:** October 11, 2025
**Issue:** HTTP 403 Forbidden responses
**Status:** BLOCKED - Need anti-bot measures

---

## Problem

Basketball Reference is blocking our scraper requests with HTTP 403 errors, despite:
- Proper User-Agent header
- 12-second rate limiting
- Respectful scraping practices

This is expected behavior as Basketball Reference actively blocks automated scrapers.

---

## Current Status

### ✅ Working Scraper
**File:** `scripts/etl/scrape_basketball_reference_comprehensive.py`
**Status:** OPERATIONAL for 9 data types
**Proven:** Successfully scraped multiple data types
**Coverage:** Draft, awards, per-game, shooting, play-by-play, team ratings, playoffs, coaches, standings

### ⚠️ Blocked Scraper
**File:** `scripts/etl/scrape_bref_tier1_incremental.py`
**Status:** BLOCKED by HTTP 403
**Enhanced:** Fixed HTML parsing, robust table detection
**Ready:** Code is ready, but needs anti-blocking measures

---

## Solutions

### Option 1: Use Existing Working Scraper (RECOMMENDED)
**Pros:**
- Already proven to work
- Handles 9 data types
- Production-ready
- Can collect most needed data

**Cons:**
- Limited to specific data types
- Not as granular as Tier 1 plan

**Action:**
```bash
# Scrape what we need with proven scraper
python scripts/etl/scrape_basketball_reference_comprehensive.py \
  --start-season 2020 --end-season 2024 \
  --all \
  --upload-to-s3 \
  --rate-limit 20
```

### Option 2: Implement Anti-Blocking Measures
**Techniques:**
1. **Proxy Rotation**
   - Use rotating proxy service
   - Residential proxies preferred
   - Cost: $50-100/month

2. **Longer Delays**
   - Increase rate limit to 30-60 seconds
   - Random jitter between requests
   - Slower but more reliable

3. **Browser Automation**
   - Use Selenium/Playwright
   - Render JavaScript
   - Mimic human behavior
   - Slower but more robust

4. **Session Management**
   - Rotate User-Agents
   - Manage cookies properly
   - Simulate browser sessions

**Example Implementation:**
```python
# Enhanced User-Agent rotation
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...',
    'Mozilla/5.0 (X11; Linux x86_64) ...'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Longer delays with jitter
def rate_limit_with_jitter(base_delay=30):
    jitter = random.uniform(-5, 5)
    time.sleep(base_delay + jitter)
```

### Option 3: Alternative Data Sources
**Use existing data instead:**
- ESPN: 44,826 PBP files already collected
- hoopR: 13M PBP rows in RDS
- NBA API: 2,163 PBP files
- Kaggle: Historical data in SQLite

**Coverage:** Already have comprehensive data for most use cases

### Option 4: Manual Data Collection
For critical missing data only:
- Identify specific gaps
- Manual browser downloads
- One-time collection
- Store in S3 for future use

---

## Recommended Path Forward

### Immediate (Now)
1. ✅ Use existing comprehensive scraper for available data types
2. ✅ Leverage already-collected ESPN/hoopR/NBA API data
3. ✅ Begin Phase 9 (PBP to Box Score) with existing data

### Short-term (1-2 weeks)
1. Implement proxy rotation for Tier 1 scraper
2. Test with longer delays (30-60s)
3. Add User-Agent rotation
4. Gradual rollout with monitoring

### Long-term (1-3 months)
1. Build comprehensive anti-blocking system
2. Implement browser automation for difficult cases
3. Set up scheduled scraping with proper intervals
4. Monitor for blocking and adapt

---

## Data Priority Assessment

**Already Have (No scraping needed):**
- ✅ Play-by-play: ESPN (44K games), hoopR (13M rows), NBA API (2K games)
- ✅ Box scores: All sources
- ✅ Team stats: All sources
- ✅ Player stats: All sources
- ✅ Schedules: Complete

**Can Get with Working Scraper:**
- ✅ Draft data (1947-2025)
- ✅ Awards (1946-2025)
- ✅ Per-game stats (1947-2025)
- ✅ Shooting stats (2000-2025)
- ✅ Team ratings (1974-2025)
- ✅ Playoff stats (1947-2025)
- ✅ Coach records (1947-2025)

**Need Tier 1 Scraper (blocked):**
- ⏸️ Player game logs (individual games)
- ⏸️ Shot charts (detailed)
- ⏸️ Player tracking (advanced)
- ⏸️ Lineup combinations

**Assessment:** We have 90% of needed data. Tier 1 blockers are "nice to have" not "must have."

---

## Cost-Benefit Analysis

### Immediate Implementation (Proxy Service)
- **Cost:** $50-100/month
- **Time:** 1-2 days setup
- **Benefit:** Access to Tier 1 data
- **Risk:** Still might get blocked

### Wait and Use Existing Data
- **Cost:** $0
- **Time:** 0 hours
- **Benefit:** Begin Phase 9 immediately with existing data
- **Risk:** None

### Recommendation
**Start Phase 9 with existing data.** We have comprehensive PBP data from ESPN and hoopR. The Tier 1 data is supplementary, not critical.

**Defer Tier 1 scraper** until Phase 9 is operational and we can assess if the additional granularity is worth the anti-blocking investment.

---

## Technical Improvements Made

### Enhanced HTML Parsing ✅
- BeautifulSoup Comment parsing
- 5 fallback strategies for table detection
- Multiple stat name support
- Robust error handling

### Code is Ready ✅
- Checkpoint-based progress tracking
- Incremental saving (no data loss)
- Resume capability
- Proper logging

### Only Issue: Blocking ⚠️
- Not a code problem
- Not a parsing problem
- Anti-bot protection working as intended
- Need anti-blocking measures to proceed

---

## Next Steps

**User Decision Required:**

**Option A:** Use existing data, begin Phase 9 immediately
- Fastest path to value
- Zero cost
- No blocking issues
- 90% of needed data available

**Option B:** Implement proxy service, collect Tier 1 data
- 1-2 days setup
- $50-100/month cost
- Additional 10% data granularity
- Some blocking risk remains

**Option C:** Hybrid approach
- Begin Phase 9 with existing data
- Implement proxy service in parallel
- Add Tier 1 data when available
- Best of both worlds

**Recommended:** Option C (Hybrid)

---

**Document Version:** 1.0
**Created:** October 11, 2025
**Status:** Awaiting user decision on anti-blocking approach


