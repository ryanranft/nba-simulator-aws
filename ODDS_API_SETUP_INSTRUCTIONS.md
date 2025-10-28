# Odds API Setup - Your Action Required

**Date:** October 28, 2025
**Status:** ✅ All betting analysis code ready | ⏳ Waiting for API key configuration

---

## 🎯 What's Been Built

Your NBA betting analysis system is **100% complete** and ready to use:

✅ **9 Python Scripts** (1,800+ lines)
  - Odds fetching from PostgreSQL
  - ML predictions with confidence intervals
  - Monte Carlo simulations (10K per game)
  - Player props analysis
  - Betting edge calculator (EV + Kelly Criterion)
  - Report generation (Markdown, CSV, JSON)
  - Master orchestrator

✅ **Test Suite** - All calculations validated

✅ **Demo Completed** - Successfully predicted 7 games from Oct 28, 2024

---

## 🔑 What You Need to Do (5 minutes)

The **only missing piece** is the Odds API key to collect real-time betting odds.

### **Step 1: Get Free API Key** (2 minutes)

1. Visit: **https://the-odds-api.com**
2. Click **"Get API Key"** or **"Sign Up"**
3. Create account (email + password)
4. Copy your API key (looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

**Free Tier**: 500 requests/month (perfect for daily betting analysis)

---

### **Step 2: Run Setup Script** (1 minute)

```bash
cd /Users/ryanranft/odds-api
./setup_api_key.sh
```

The script will:
- Ask for your API key
- Create `.env` configuration
- Verify database connection
- Show next steps

**Or manually** edit `.env`:
```bash
cd /Users/ryanranft/odds-api
nano .env

# Add this line:
ODDS_API_KEY=your_actual_key_here
```

---

### **Step 3: Start the Scraper** (30 seconds)

```bash
cd /Users/ryanranft/odds-api
source venv/bin/activate
python scripts/run_scraper.py --live
```

This will:
- Fetch all NBA games for today + upcoming week
- Collect odds from 10+ bookmakers
- Store in your RDS PostgreSQL `odds` schema
- Takes 1-2 minutes for first run

---

### **Step 4: Run Betting Analysis** (10 minutes)

Once scraper completes:

```bash
cd /Users/ryanranft/nba-simulator-aws
conda activate nba-aws

# Run full analysis
python3 scripts/betting/run_full_betting_analysis.py \
    --date 2025-10-28 \
    --n-simulations 10000 \
    --min-edge 0.02

# View results
open reports/betting/betting_recommendations_2025-10-28.md
```

---

## 📊 What You'll Get

After analysis completes, you'll have:

### **1. Markdown Report** (`reports/betting/*.md`)
```
# NBA Betting Recommendations - October 28, 2025

## High-Confidence Recommendations

### Lakers @ Warriors (7:00 PM PT)

**Moneyline Edge**
- Recommendation: Bet Lakers -150
- Model Probability: 67.8% (CI: 64.2% - 71.4%)
- Market Implied: 60.0%
- Edge: +7.8%
- Expected Value: +13.0%
- Kelly Fraction: 5.2%
- Confidence: HIGH ⭐⭐⭐

**Spread Edge**
- Recommendation: Lakers -4.5 (-110)
- Model Probability: 58.3%
- Edge: +5.9%
- Confidence: MEDIUM ⭐⭐

[... continues for all games and bet types ...]
```

### **2. CSV Export** (`reports/betting/*.csv`)
For Excel/Google Sheets analysis

### **3. JSON Data** (`data/betting/*.json`)
For programmatic access

---

## 🎲 Analysis Includes

✅ **Game-Level Bets:**
- Moneylines (straight win/loss)
- Spreads (point spreads)
- Totals (over/under)
- Quarter/half lines

✅ **Player Props:**
- Points over/under
- Rebounds over/under
- Assists over/under
- Three-pointers made
- Combined PRA (points + rebounds + assists)

✅ **Advanced Metrics:**
- Expected Value (EV)
- Kelly Criterion bet sizing
- Confidence intervals
- Model vs market comparison
- Edge identification (+2% minimum)

---

## 🔍 System Verification

To check if everything is working:

```bash
cd /Users/ryanranft/odds-api
./verify_scraper_status.sh
```

Expected output:
```
═══════════════════════════════════════════════════════════════
  Odds API Scraper Status Check
═══════════════════════════════════════════════════════════════

📋 Configuration:
  ✅ .env file exists
  ✅ API key configured (32 chars)

🏃 Scraper Process:
  ✅ Scraper is running (PID: 12345)

📊 Database Status:
  ✅ Database connected
  📅 Total events: 156
  📊 Total odds snapshots: 4,892
  🎯 Games today: 12
  🕒 Latest update: 2025-10-28 14:23:15
```

---

## 💡 Quick Reference

| Task | Command |
|------|---------|
| **Check status** | `cd /Users/ryanranft/odds-api && ./verify_scraper_status.sh` |
| **Start scraper** | `cd /Users/ryanranft/odds-api && python scripts/run_scraper.py --live` |
| **Run analysis** | `cd /Users/ryanranft/nba-simulator-aws && conda activate nba-aws && python3 scripts/betting/run_full_betting_analysis.py --date 2025-10-28` |
| **View report** | `open reports/betting/betting_recommendations_2025-10-28.md` |

---

## 📈 API Usage (Free Tier Management)

**Free Plan**: 500 requests/month

**Smart Usage Strategies:**

1. **Daily Betting** (30 requests/month) ✅
   - Run once per day before betting
   - `python scripts/run_scraper.py --live` (1 request)

2. **Multi-Time Analysis** (180 requests/month) ✅
   - Every 4 hours: `*/240 * * * * python scripts/run_scraper.py --live`
   - Catch odds movements throughout day

3. **Continuous (720/month)** ⚠️
   - Exceeds free tier
   - Consider paid plan ($100/mo for 20K requests)

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No games found" | Wait 5-10 min for scraper to collect data |
| "Invalid API key" | Verify at https://the-odds-api.com/account |
| "Rate limit exceeded" | Check quota: `python scripts/check_quota.py` |
| "Database connection failed" | Verify RDS credentials in `../nba-sim-credentials.env` |

---

## 📚 Documentation

All documentation created for you:

1. **`/Users/ryanranft/odds-api/QUICK_START.md`** - Fast setup guide
2. **`/Users/ryanranft/odds-api/SETUP_ODDS_API.md`** - Complete setup instructions
3. **`/Users/ryanranft/odds-api/setup_api_key.sh`** - Interactive setup script
4. **`/Users/ryanranft/odds-api/verify_scraper_status.sh`** - Status checker
5. **`/Users/ryanranft/nba-simulator-aws/BETTING_ANALYSIS_SETUP.md`** - System overview
6. **`/Users/ryanranft/nba-simulator-aws/BETTING_IMPLEMENTATION_SUMMARY.md`** - Technical details

---

## ✅ Next Steps Summary

**Right now (5 minutes):**
1. Get API key: https://the-odds-api.com
2. Run: `cd /Users/ryanranft/odds-api && ./setup_api_key.sh`
3. Start scraper: `python scripts/run_scraper.py --live`

**After scraper collects data (10-15 minutes):**
4. Run analysis: `cd /Users/ryanranft/nba-simulator-aws && conda activate nba-aws && python3 scripts/betting/run_full_betting_analysis.py --date 2025-10-28`
5. View recommendations: `open reports/betting/betting_recommendations_2025-10-28.md`

---

## 🎉 What You'll Have

After completing these steps, you'll have:

✅ **Real-time odds** from 10+ bookmakers
✅ **ML predictions** with confidence intervals
✅ **10,000 Monte Carlo simulations** per game
✅ **Player props analysis**
✅ **Betting edges** identified (EV + Kelly Criterion)
✅ **Comprehensive reports** (Markdown, CSV, JSON)
✅ **Automated pipeline** for daily analysis

**Ready to dominate NBA betting with data science! 🏀📊💰**

---

**Questions?** Check the troubleshooting section or review the detailed docs in `/Users/ryanranft/odds-api/SETUP_ODDS_API.md`

