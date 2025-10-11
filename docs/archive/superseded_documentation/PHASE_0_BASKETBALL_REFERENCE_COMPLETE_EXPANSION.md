# Phase 0: Basketball Reference COMPLETE Data Expansion

**Phase:** 0 (Data Collection - Comprehensive Edition)
**Sub-Phase:** 0.X - ALL Basketball Data Collection
**Status:** ⏸️ PENDING
**Scope:** NBA + WNBA + G League + ABA + BAA + International + College (234+ data types)
**Priority:** Tiered (IMMEDIATE → OPTIONAL)
**Estimated Time:** 140-197 hours total (spread across 13 tiers)
**Cost Impact:** +$0.031-0.26/month S3 storage (negligible)
**Dependencies:** Comprehensive scraper created ✅

---

## 🎯 Executive Summary

**Discovery Results:**
- **Total Data Types Available:** 234+ across all basketball domains
- **Currently Documented:** 32 NBA types (14% of available data)
- **NEW Discoveries:** 202 additional data types

**Recommendation:**
- **Essential:** Collect all 119 NBA data types (Tiers 1-9)
- **Historical:** Add ABA & BAA for complete NBA lineage (Tiers 7-8)
- **Optional:** WNBA, G League, International, College (Tiers 10-13)

**For Your Panel Data Goals:**
- All 119 NBA types provide complete statistical coverage 1946-2025
- ABA/BAA extends history to true league origins (1946)
- Granular stats (salaries, contracts, shooting zones, PBP details) enhance ML features
- Other leagues optional but provide multi-league analysis capability

---

## 📊 Data Scope by Tier

| Tier | Domain | Data Types | Records | Time | Priority | Cost/Mo |
|------|--------|-----------|---------|------|----------|---------|
| **1** | NBA High Value | 5 | 150K | 15-20h | IMMEDIATE | $0.002 |
| **2** | NBA Strategic | 4 | 200K | 20-25h | IMMEDIATE | $0.003 |
| **3** | NBA Specialized | 4 | 5K | 5-7h | NEAR-TERM | <$0.001 |
| **4** | NBA Player Granular | 2 | 500K-10M | 50-100h | SELECTIVE | $0.12-0.23 |
| **5A** | NBA Salaries | 6 | 50K | 8-10h | HIGH | $0.001 |
| **5B** | NBA Shooting Detail | 5 | Incl. | 2-3h | HIGH | Incl. |
| **5C** | NBA PBP Detail | 6 | Incl. | 2-3h | HIGH | Incl. |
| **6** | NBA Awards Expanded | 11 | 20K | 5-6h | MEDIUM | <$0.001 |
| **7** | ABA Historical | 12 | 50K | 10-12h | MEDIUM | $0.001 |
| **8** | BAA Historical | 8 | 10K | 4-5h | MEDIUM | <$0.001 |
| **9** | NBA Misc Tools | 20 | Varies | 10-15h | LOW | <$0.001 |
| **10** | WNBA Complete | 16 | 100K | 15-20h | OPTIONAL | $0.002 |
| **11** | G League | 10 | 30K | 8-10h | OPTIONAL | $0.001 |
| **12** | International Select | 10 | 50K | 20-30h | OPTIONAL | $0.001 |
| **13** | College Select | 10 | 200K | 30-40h | OPTIONAL | $0.005 |
| **TOTAL** | **All Basketball** | **234** | **1.4M-11M** | **205-308h** | - | **$0.03-0.26** |

---

## 🗂️ Complete Data Type Index

### ✅ Already Collected (12 types)

See `PHASE_0_BASKETBALL_REFERENCE_EXPANSION.md` for details.

1. Season Totals (1947-2025)
2. Advanced Totals (1953-2025)
3. Team Standings (1971-2025)
4. Transactions (2001-2025)
5. Draft Data (2001-2025)
6. Per-Game Stats (2001-2025)
7. Shooting Stats (2001-2025)
8. Play-by-Play (2001-2025)
9. Team Ratings (2001-2025)
10. Playoff Stats (2001-2025)
11. Coach Records (2001-2025)
12. Awards (2024 tested)

---

### ⏸️ Already Planned (20 types) - TIERS 1-4

See `PHASE_0_BASKETBALL_REFERENCE_EXPANSION.md` for detailed implementation steps.

**TIER 1:**
13. Adjusted Shooting (2000-2025, 26 yrs, ~19K records)
14. Per 100 Possessions (1974-2025, 52 yrs, ~38K records)
15. Schedule/Game Results (1947-2025, 79 yrs, ~70K games)
16. Rookies Stats (1947-2025, 79 yrs, ~6K records)
17. All-Rookie Teams (1962-2025, 64 yrs, ~640 records)

**TIER 2:**
18. Team Starting Lineups (2000-2025, 750 team-seasons, ~60K records)
19. Team Game Logs (1947-2025, ~195K records)
20. Per Minute Stats (1952-2025, 74 yrs, ~55K records)
21. Season Leaders (1947-2025, 79 yrs, ~7,900 records)

**TIER 3:**
22. Hall of Fame (~400 inductees)
23. Executive Stats (GMs/Presidents)
24. Team Referee Stats (recent years)
25. Jersey Numbers (recent years)

**TIER 4:**
26. Player Game Logs (5M+ games, selective recommended)
27. Player Career Splits (5K players, selective recommended)

---

### 🆕 NEW NBA DISCOVERIES - TIERS 5-9 (76 types)

#### TIER 5A: Salaries & Contracts (6 types) - HIGH PRIORITY

**Time:** 8-10 hours | **Records:** ~50,000 | **Coverage:** 1990-2031

28. **Team Payroll by Season**
    - URL: `/contracts/`
    - Data: Team total salaries, cap space, 2025-2031 commitments
    - Value: Financial analysis, trade feasibility

29. **Player Contracts**
    - URL: `/contracts/players.html`
    - Data: Contract values, years, options, guarantees
    - Value: Player valuation, contract optimization

30. **Historical Player Salaries**
    - URL: Player pages → Salaries tab
    - Data: Year-by-year salaries (1990-2025)
    - Value: Era-adjusted value analysis

31. **Salary Cap History**
    - Data: Historical cap values
    - Value: Financial context

32. **Luxury Tax Data**
    - Data: Tax thresholds, penalties
    - Value: Team financial strategy

33. **Contracts Glossary**
    - Data: CBA terms, contract types
    - Value: Understanding financial structures

**Implementation:**
- Scrape `/contracts/` page for current payrolls
- Scrape `/contracts/players.html` for individual contracts
- Extract salary data from player pages (requires player iteration)
- Compile salary cap and tax history

---

#### TIER 5B: Granular Shooting Stats (5 types) - HIGH PRIORITY

**Time:** 2-3 hours (extends existing Shooting scraper) | **Records:** Included in existing

34. **Shooting by Distance Zones**
    - Data: FG% by zone (0-3ft, 3-10ft, 10-16ft, 16-3PT, 3PT)
    - Value: Shot selection optimization
    - Note: More granular than current "Shooting Stats"

35. **Dunk Tracking**
    - Data: Dunks made/attempted
    - Value: Rim pressure quantification

36. **Corner 3-Point Shooting**
    - Data: Corner 3PT attempts and %
    - Value: Shot location strategy

37. **Heave Shots**
    - Data: Long-distance heaves (filter noise)
    - Value: Clean shooting percentages

38. **Assisted FG Percentage**
    - Data: % of FG that were assisted
    - Value: Shot creation vs. catch-and-shoot

**Implementation:**
- Extend existing shooting scraper to capture all column headers
- Parse additional columns: dunks, corner 3s, heaves, assisted %
- Already available on shooting page, just need to capture more columns

---

#### TIER 5C: Granular Play-by-Play Stats (6 types) - HIGH PRIORITY

**Time:** 2-3 hours (extends existing PBP scraper) | **Records:** Included in existing

39. **Position Percentage Breakdown**
    - Data: % time at PG, SG, SF, PF, C
    - Value: Positional flexibility tracking

40. **OnCourt Plus/Minus**
    - Data: Team performance with player on court
    - Value: Impact measurement

41. **On-Off Differential**
    - Data: Team performance difference (on vs. off)
    - Value: Net impact quantification

42. **Turnover Type Breakdown**
    - Data: Bad pass vs. lost ball turnovers
    - Value: Turnover classification

43. **Fouls Drawn**
    - Data: Fouls player draws (not just commits)
    - Value: Drawing contact ability

44. **And1 Plays & Shots Blocked**
    - Data: And-one conversions, shots blocked on defense
    - Value: Contact finishing, rim protection

**Implementation:**
- Extend existing PBP scraper to capture all columns
- Already available on PBP page, just capture more columns

---

#### TIER 6: Awards Expanded (11 types) - MEDIUM PRIORITY

**Time:** 5-6 hours | **Records:** ~20,000 | **Coverage:** Varies by award

45. **Player of the Month** (Modern era)
46. **Rookie of the Month** (Modern era)
47. **Coach of the Month** (Modern era)
48. **Defensive Player of the Month** (Recent years)
49. **Player of the Week** (Modern era)
50. **Social Justice Champion** (2021-present)
51. **Sportsmanship Award** (1996-present)
52. **Clutch Player of the Year** (2023-present)
53. **In-Season Tournament MVP** (2023-present)
54. **Twyman-Stokes Teammate Award** (2013-present)
55. **J. Walter Kennedy Citizenship Award** (1975-present)

**All-Star Weekend Events (5 types):**
56. **Rising Stars Challenge** (1994-present)
57. **Skills Challenge** (2003-present)
58. **Three-Point Contest** (1986-present)
59. **Slam Dunk Contest** (1984-present)
60. **Legends Game** (1984-1993)

**Implementation:**
- Awards pages: Standard table scraping
- All-Star events: Event-specific parsers

---

#### TIER 7: ABA Historical (12 types) - MEDIUM PRIORITY

**Time:** 10-12 hours | **Records:** ~50,000 | **Coverage:** 1967-1976 (9 seasons)

61. ABA Season Totals
62. ABA Per-Game Stats
63. ABA Per 36 Minutes
64. ABA Per 100 Possessions
65. ABA Advanced Stats
66. ABA Adjusted Shooting
67. ABA Team Standings
68. ABA Team Stats (multiple tables)
69. ABA Playoff Stats
70. ABA All-Star Games (1968-1976)
71. ABA Awards (MVP, ROY, All-ABA)
72. ABA Coaches

**Implementation:**
- Same scraper as NBA, different league URLs
- URL pattern: `/leagues/ABA_{season}.html`
- Same table structures as NBA

---

#### TIER 8: BAA Historical (8 types) - MEDIUM PRIORITY

**Time:** 4-5 hours | **Records:** ~10,000 | **Coverage:** 1946-1949 (3 seasons)

73. BAA Season Totals
74. BAA Per-Game Stats
75. BAA Team Standings
76. BAA Team Stats
77. BAA Playoff Stats
78. BAA Champions
79. BAA Coaches
80. BAA Draft (if available)

**Implementation:**
- Same scraper as NBA, different league URLs
- URL pattern: `/leagues/BAA_{season}.html`

---

#### TIER 9: NBA Miscellaneous Tools (20 types) - LOW PRIORITY

**Time:** 10-15 hours | **Records:** Varies | **Coverage:** Complete history

**Frivolities & Tools:**
81. Injury Report (current season, dynamic)
82. Preseason Odds (championship, win totals)
83. Buzzer-Beaters Database
84. "Cups of Coffee" (one-game players)
85. Daily Leaders (historical)
86. Eastern vs. Western Conference Records
87. Historical Standings by Date
88. Milestones Watch
89. Franchise Milestones
90. MVP Award Tracker (current season)
91. Playoff Probabilities (current season)
92. Roster Continuity
93. Simple Projection System
94. Players by Birth Place
95. Players by Birth Year
96. Players by College
97. Teammates & Opponents Tracker
98. Trade Partners
99. Most Games Without Playoffs
100. "On This Date" Events
101. Last N Days Stats
102. Uniform Numbers (comprehensive)

**Player Page Enhancements:**
103. Player Similarity Scores
104. Player Projections (next season)
105. Player FAQs
106. Triple-Doubles Tracking (already in totals, just extract)
107. Player Game Highs
108. Player Playoff Series Stats
109. Player All-Star Game Stats
110. Player Leaderboards (career rankings)

**Team Page Enhancements:**
111. Team Depth Charts
112. Team Splits (home/away, vs. division, etc.)
113. Team On/Off Stats
114. Franchise History Pages
115. Team vs. Opponent Stats
116. Team Awards Summary

**Playoff Enhancements:**
117. Playoff Series Results (series-level)
118. Playoff Series Betting Odds
119. 7-Game Series Outcomes

**Implementation:**
- Most are single-page scrapes or enhancements to existing scrapers
- Some require special parsing (dynamic pages, frivolities tools)
- Player/team page enhancements require iterating entities

---

### 🆕 NON-NBA LEAGUES - TIERS 10-13 (115 types)

#### TIER 10: WNBA Complete (16 types) - OPTIONAL

**Time:** 15-20 hours | **Records:** ~100,000 | **Coverage:** 1997-2025 (29 seasons)

120. WNBA Season Totals
121. WNBA Per-Game Stats
122. WNBA Advanced Stats
123. WNBA Team Standings
124. WNBA Team Statistics
125. WNBA Player Game Logs
126. WNBA All-Star Games (1999-2025)
127. WNBA Draft
128. WNBA Supplemental Draft
129. WNBA Awards (MVP, ROY, COY, All-WNBA)
130. WNBA Playoff Statistics
131. WNBA Daily Scores
132. WNBA Career Leaderboards
133. WNBA Season Leaders
134. WNBA Rookie Records
135. WNBA Player Headshots

**Implementation:**
- URL pattern: `/wnba/` + year/data type
- Similar structure to NBA
- Complete women's professional basketball history

---

#### TIER 11: G League (10 types) - OPTIONAL

**Time:** 8-10 hours | **Records:** ~30,000 | **Coverage:** 2002-2025 (23 seasons)

136. G League Season Standings
137. G League Player Statistics
138. G League Team Rosters
139. G League Game Logs
140. G League Daily Scores
141. G League Awards (MVP, ROY, All-League)
142. G League Season Leaders
143. G League Career Leaders
144. G League Top Performers
145. G League Box Scores

**Implementation:**
- URL pattern: `/gleague/` + year/data type
- NBA developmental league
- Useful for prospect tracking

---

#### TIER 12: International Basketball (40 types) - OPTIONAL

**Time:** 20-30 hours (selective) | **Records:** ~50,000 | **Coverage:** 1936-2025

**Olympics (5 types):**
146. Men's Olympics Player Stats (1936-2024)
147. Women's Olympics Player Stats (1936-2024)
148. Men's Olympics Team Stats
149. Women's Olympics Team Stats
150. Olympics Medal Standings

**FIBA World Cup (3 types):**
151. FIBA Player Stats (2010-2023)
152. FIBA Team Stats
153. FIBA Standings

**European Leagues (32 types = 8 leagues × 4 data types each):**

**EuroLeague (2000-2025):**
154-157. Player/Team Stats, Standings, Playoffs

**EuroCup (2002-2025):**
158-160. Player/Team Stats, Standings

**Liga ACB - Spain (1983-2025):**
161-163. Player/Team Stats, Standings

**Lega Basket Serie A - Italy (1998-2025):**
164-166. Player/Team Stats, Standings

**Greek Basket League (2001-2025):**
167-169. Player/Team Stats, Standings

**LNB Pro A - France (2002-2025):**
170-172. Player/Team Stats, Standings

**CBA - China (2011-2025):**
173-175. Player/Team Stats, Standings

**NBL - Australia (2011-2025):**
176-178. Player/Team Stats, Standings

**Other Leagues (4 types):**
179. ABA League First Division Stats
180. Israeli Premier League Stats
181. Turkish Super League Stats
182. VTB United League Stats

**Implementation:**
- URL pattern: `/international/` + competition
- Selective collection recommended (Olympics, FIBA, EuroLeague priority)
- Useful for international player scouting

---

#### TIER 13: College Basketball (30 types) - OPTIONAL

**Time:** 30-40 hours (selective) | **Records:** ~200,000 | **Coverage:** 1891-2025

**Note:** Redirects to Sports-Reference.com/cbb/

183. NCAA D1 Player Stats (Season totals, per-game, advanced)
184. NCAA D1 Team Stats
185. NCAA D1 Conference Standings
186. NCAA D1 Schedule & Results
187. NCAA Tournament Results (Men's & Women's, complete history)
188. NIT Results
189. CBI Tournament Results
190. CIT Tournament Results
191. NCAA Bracket History
192. NCAA Conference Data (all conferences)
193. College Coach Records
194. College Player Game Logs
195. College Team Game Logs

**Awards (10 types):**
196. Player of the Year (AP, Wooden, Naismith, etc.)
197. All-America Teams
198. Conference Player of the Year
199. Conference awards
200. NCAA Tournament MOP

**Additional Data (11 types):**
201. College Polls (AP, Coaches)
202. College Statistical Leaders
203. College Career Leaders
204. College Player Season Finder
205. College Team Season Finder
206. College Player Biographical Data
207. College Recruiting Classes (if available)
208. College Transfer Portal (recent years)
209. Women's College Basketball (1981+)
210. College Buzzer-Beaters
211. College Milestones
212. College Conference Tournament Results
213. College Daily Leaders

**Implementation:**
- Different domain: sports-reference.com/cbb/
- Selective collection: Focus on NCAA Tournament, major conferences
- Useful for draft pipeline analysis

---

## 🎯 Implementation Roadmap

### Phase 1: Complete NBA Foundation (Tiers 1-5) - **67-97 HOURS**

**Weeks 1-2: Already Planned Tier 1** (15-20 hours)
- Adjusted Shooting, Per 100 Poss, Schedule, Rookies, All-Rookie Teams

**Weeks 3-4: Already Planned Tier 2** (20-25 hours)
- Team Lineups, Team Game Logs, Per Minute, Season Leaders

**Week 5: Already Planned Tier 3** (5-7 hours)
- Hall of Fame, Executives, Team Referees, Jersey Numbers

**Weeks 6-8: NEW Tier 5A-5C** (12-16 hours)
- Salaries & Contracts, Granular Shooting, Granular PBP

**Weeks 9-16: SELECTIVE Tier 4** (50-100 hours if collecting player granularity)
- Player Game Logs (selective: top 500 players only)
- Player Career Splits (selective: top 500 players only)

**Milestone:** Complete NBA statistical foundation

---

### Phase 2: NBA Awards & Historical Leagues (Tiers 6-8) - **19-23 HOURS**

**Week 17: Tier 6 - Awards Expanded** (5-6 hours)
- Monthly/weekly awards, All-Star events

**Weeks 18-19: Tier 7 - ABA Historical** (10-12 hours)
- ABA complete collection (1967-1976, 9 seasons)

**Week 20: Tier 8 - BAA Historical** (4-5 hours)
- BAA complete collection (1946-1949, 3 seasons)

**Milestone:** Complete NBA/ABA/BAA lineage 1946-2025

---

### Phase 3: NBA Miscellaneous (Tier 9) - **10-15 HOURS**

**Weeks 21-23: Tier 9 - Tools & Enhancements** (10-15 hours)
- Frivolities databases
- Player/team page enhancements
- Playoff series data

**Milestone:** Exhaustive NBA data collection complete (119 types)

---

### Phase 4: OPTIONAL - Other Leagues (Tiers 10-13) - **73-100 HOURS**

**Weeks 24-26: WNBA** (15-20 hours)
- Complete WNBA collection (1997-2025)

**Weeks 27-28: G League** (8-10 hours)
- Complete G League collection (2002-2025)

**Weeks 29-32: International (Selective)** (20-30 hours)
- Olympics, FIBA, EuroLeague priority

**Weeks 33-37: College (Selective)** (30-40 hours)
- NCAA Tournament, major conferences

**Milestone:** Complete multi-league basketball database

---

## 📋 Success Criteria

### NBA Complete (Tiers 1-9) ✅

**Foundation Stats:**
- [ ] 5 Tier 1 types: 150K records
- [ ] 4 Tier 2 types: 200K records
- [ ] 4 Tier 3 types: 5K records
- [ ] 2 Tier 4 types: 500K-10M records (selective)

**Enhanced Stats:**
- [ ] 6 Tier 5A types: 50K salary records
- [ ] 5 Tier 5B types: Granular shooting (extended)
- [ ] 6 Tier 5C types: Granular PBP (extended)

**Awards & History:**
- [ ] 16 Tier 6 types: 20K award records
- [ ] 12 Tier 7 types: 50K ABA records
- [ ] 8 Tier 8 types: 10K BAA records

**Miscellaneous:**
- [ ] 39 Tier 9 types: Varied records

**Total NBA: 119 data types, 485K-10.5M records**

---

### Multi-League (Tiers 10-13) ✅ (Optional)

**WNBA:**
- [ ] 16 types: 100K records (1997-2025)

**G League:**
- [ ] 10 types: 30K records (2002-2025)

**International:**
- [ ] 40 types: 50K records (selective)

**College:**
- [ ] 30 types: 200K records (selective)

**Total All Basketball: 234 types, 865K-10.88M records**

---

## 💰 Cost Summary

**Current Plan (Tiers 1-4):**
- Storage: 260 MB - 10 GB
- Cost: $0.006 - 0.23/month

**Full NBA (Tiers 1-9):**
- Storage: 560 MB - 10.3 GB
- Cost: $0.013 - 0.24/month
- **Increase: +$0.007 - 0.01/month**

**All Basketball (Tiers 1-13):**
- Storage: 1.36 GB - 11 GB
- Cost: $0.031 - 0.26/month
- **Increase: +$0.025 - 0.03/month vs. current plan**

**Conclusion:** Even ALL basketball data is negligible cost (<$0.30/month).

---

## ⏱️ Time Investment Summary

| Scope | Tiers | Hours | Weeks @ 10h/wk |
|-------|-------|-------|----------------|
| **Current Plan** | 1-4 | 40-60 | 4-6 |
| **Full NBA** | 1-9 | 67-97 | 7-10 |
| **All Basketball** | 1-13 | 140-197 | 14-20 |

---

## 🚀 Quick Start Recommendations

**For Panel Data System (Recommended):**
1. ✅ Execute Tiers 1-3 (already planned, high value)
2. ✅ Execute Tiers 5A-5C (salaries + granular stats)
3. ✅ Execute Tiers 7-8 (ABA/BAA for historical completeness)
4. ⚠️ Selective Tier 4 (top players only)
5. ⚠️ Optional Tier 6 (awards if desired)
6. ❌ Skip Tiers 10-13 unless multi-league analysis desired

**Time:** 52-64 hours (NBA foundation + historical)
**Cost:** ~$0.015/month

**For Complete Basketball Database:**
1. ✅ Execute all NBA tiers (1-9)
2. ✅ Execute WNBA (Tier 10)
3. ✅ Execute ABA/BAA (Tiers 7-8, already in NBA plan)
4. ⚠️ Selective International (Olympics, FIBA, EuroLeague only)
5. ⚠️ Selective College (NCAA Tournament only)

**Time:** 140-197 hours (all basketball)
**Cost:** ~$0.03-0.26/month

---

## 📖 Related Documentation

- **Complete Catalog:** `docs/data_sources/basketball_reference_COMPLETE_catalog_2025-10-11.md` (234 data types)
- **Original Plan:** `docs/phases/PHASE_0_BASKETBALL_REFERENCE_EXPANSION.md` (32 data types, detailed implementation)
- **Original Analysis:** `docs/data_sources/basketball_reference_additional_sources_2025-10-10.md`
- **Comprehensive Scraper:** `scripts/etl/scrape_basketball_reference_comprehensive.py`

---

## 🔧 Technical Implementation

**Extending the Comprehensive Scraper:**

1. **Add league parameter:**
   ```python
   def __init__(self, league='NBA'):  # 'NBA', 'WNBA', 'ABA', 'BAA', 'G-League'
       self.league = league
       self.BASE_URL = self._get_base_url()
   ```

2. **Add new data type configs:**
   ```python
   # Tier 5A: Salaries
   'salaries': {
       'url_pattern': '/contracts/players.html',
       's3_prefix': 'basketball_reference/salaries',
       'min_year': 1990
   },

   # Tier 6: Monthly awards
   'player_of_month': {
       'url_pattern': '/awards/pom.html',
       's3_prefix': 'basketball_reference/awards/pom',
       'special': 'single_page_multi_year'
   }
   ```

3. **Extend existing scrapers:**
   ```python
   # Tier 5B: Extend shooting scraper
   def scrape_shooting(self, season):
       # Current: Captures basic shooting columns
       # Enhanced: Capture ALL columns including dunks, corner 3s, heaves
       all_columns = ['Dunks', 'Corner3', 'Heaves', 'AssistedPct']
   ```

**Rate Limiting:**
- Maintain 12s between requests for Basketball-Reference.com
- Adjust for Sports-Reference.com/cbb/ (same domain, same rate limit)
- No rate limiting needed for single-page scrapes

**S3 Structure:**
```
s3://nba-sim-raw-data-lake/basketball_reference/
├── nba/           # Tiers 1-9
├── wnba/          # Tier 10
├── gleague/       # Tier 11
├── aba/           # Tier 7
├── baa/           # Tier 8
├── international/ # Tier 12
└── college/       # Tier 13
```

---

## 📞 Decision Required

**User, please confirm collection scope:**

**Option A: NBA Foundation (Recommended for Panel Data)**
- Tiers 1-5 (already planned + salaries + granular stats)
- Time: 52-64 hours
- Cost: +$0.015/month
- **Provides: Complete modern NBA statistical coverage**

**Option B: NBA Complete + Historical**
- Tiers 1-9 (all NBA + ABA + BAA)
- Time: 86-117 hours
- Cost: +$0.02/month
- **Provides: Complete NBA lineage 1946-2025**

**Option C: All Basketball**
- Tiers 1-13 (NBA + WNBA + G + ABA + BAA + Int'l + College)
- Time: 140-197 hours
- Cost: +$0.03-0.26/month
- **Provides: Complete basketball database, all leagues**

**Which scope should we implement?**

---

**Phase Owner:** Data Collection Team
**Last Updated:** October 11, 2025
**Status:** Ready for user confirmation of scope
**Next Action:** User selects Option A, B, or C → Begin implementation