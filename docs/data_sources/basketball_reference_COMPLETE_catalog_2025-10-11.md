# Basketball Reference - COMPLETE Data Catalog

**Date:** October 11, 2025
**Purpose:** Exhaustive catalog of ALL basketball data available on Basketball-Reference.com and Sports-Reference.com
**Status:** Comprehensive audit complete
**Scope:** NBA, WNBA, G League, ABA, BAA, International, College Basketball, and all specialized data

---

## Executive Summary

**Total Data Categories Found:** 200+ distinct data types across 8 major basketball domains

**Already Documented:** 32 NBA data types (12 collected + 20 planned)
**NEW Discoveries:** 170+ additional data types across:
- 45+ additional NBA data types
- WNBA (complete league, 1997-2025)
- G League (2002-2025)
- ABA (1967-1976)
- BAA (1946-1949)
- International (15+ leagues/competitions)
- College Basketball (complete NCAA coverage)
- 30+ specialized tools and databases

---

## SECTION 1: NBA DATA

### A. ALREADY COLLECTED ✅ (12 types)

1. Season Totals (Basic counting stats, 1947-2025)
2. Advanced Totals (PER, WS, BPM, VORP, 1953-2025)
3. Team Standings (Win/loss records, 1971-2025)
4. Transactions (Trades, signings, waivers, 2001-2025)
5. Draft Data (Pick position, college, career stats, 2001-2025)
6. Per-Game Stats (Normalized by games, 2001-2025)
7. Shooting Stats (Shot location/distribution, 2001-2025)
8. Play-by-Play (On/off court, positional, 2001-2025)
9. Team Ratings (Offensive/defensive efficiency, 2001-2025)
10. Playoff Stats (Postseason performance, 2001-2025)
11. Coach Records (Coaching records, 2001-2025)
12. Awards (MVP, All-NBA, All-Star, 2024 tested, ready for full)

---

### B. ALREADY PLANNED FOR COLLECTION ⏸️ (20 types)

**TIER 1 (5 types):**
13. Adjusted Shooting Stats (2000-2025)
14. Per 100 Possessions Stats (1974-2025)
15. Game-by-Game Results/Schedule (1947-2025, ~70,000 games)
16. Rookies Stats (1947-2025)
17. All-Rookie Teams (1962-2025)

**TIER 2 (4 types):**
18. Team Starting Lineups (2000-2025)
19. Team Game Logs (1947-2025, all teams)
20. Per Minute Stats (1952-2025)
21. Season Leaders (1947-2025, top 10 per category)

**TIER 3 (4 types):**
22. Hall of Fame Inductees (~400 inductees)
23. Executive Stats (GMs/Presidents records)
24. Team Referee Stats (Recent years)
25. Jersey Numbers (Recent years)

**TIER 4 (2 types):**
26. Player Game Logs (5M+ individual games, selective recommended)
27. Player Career Splits (Home/away, clutch, opponent, ~5K players)

---

### C. NEW NBA DATA TYPES DISCOVERED 🆕 (45+ types)

**Salaries & Contracts (6 types):**
28. **Team Payroll by Season** (2025-2031 future commitments)
    - URL: `/contracts/`
    - Data: Total team salaries, salary cap info, year-by-year
    - Coverage: Current + 5 years future
    - Value: Financial analysis, cap space, contract structure

29. **Player Contracts** (Individual contracts)
    - URL: `/contracts/players.html`
    - Data: Contract values, years, guarantees, options
    - Coverage: All active players
    - Value: Player valuation, trade analysis

30. **Historical Salaries** (Past player salaries)
    - URL: Player pages, `/players/{X}/{slug}.html` → Salaries tab
    - Data: Year-by-year player salaries
    - Coverage: 1990s-present (varies by player)
    - Value: Historical contract analysis

31. **Salary Cap History**
    - Data: Historical salary cap values by year
    - Value: Era-adjusted salary analysis

32. **Luxury Tax Data**
    - Data: Tax thresholds, team tax payments
    - Value: Financial strategy analysis

33. **Contracts Glossary**
    - Data: Contract terms, CBA rules
    - Value: Understanding contract structures

---

**Team-Specific Data (8 types):**
34. **Team Depth Charts** (Positional depth)
    - URL: `/teams/{TEAM}/{season}_depth.html`
    - Data: Starter/backup designation, position groupings
    - Coverage: Recent years
    - Value: Roster construction, positional needs

35. **Team Splits** (Performance by various splits)
    - URL: `/teams/{TEAM}/{season}_splits.html`
    - Data: Home/away, vs. division, vs. conference, by month
    - Coverage: All teams, all seasons
    - Value: Situational performance patterns

36. **Team On/Off Stats** (Lineup impact)
    - URL: `/teams/{TEAM}/{season}_on-off.html`
    - Data: Team performance with/without each player
    - Coverage: Modern era
    - Value: Player impact quantification

37. **Franchise History Pages** (Complete team history)
    - URL: `/teams/{TEAM}/`
    - Data: Year-by-year records, playoff history, coaching changes
    - Coverage: All franchises, all years
    - Value: Historical team analysis

38. **Team Shooting Detailed** (Shot charts and zones)
    - URL: `/teams/{TEAM}/{season}_shooting.html`
    - Data: Shot distance, shot location, zone percentages
    - Coverage: Modern era (2000+)
    - Value: Shot selection analysis

39. **Team Transactions by Team** (Team-specific)
    - URL: `/teams/{TEAM}/{season}_transactions.html`
    - Data: Filtered view of transactions for one team
    - Coverage: 2001-2025
    - Value: Roster management tracking
    - Note: Filtered view of already-collected data

40. **Team vs. Opponent Stats** (Head-to-head)
    - Data: Performance vs. specific opponents
    - Value: Matchup analysis

41. **Team Awards Summary**
    - Data: Team championships, All-Stars, award winners by franchise
    - Value: Franchise legacy tracking

---

**Player-Specific Data (12 types):**
42. **Player Similarity Scores** (Career comparisons)
    - URL: Player pages → Similarity Scores section
    - Data: Most similar players by career stats
    - Coverage: All historical players
    - Value: Player comparisons, archetype identification

43. **Player Projections** (Next season projections)
    - URL: Player pages → "202X-XX Projection" tab
    - Data: Projected stats for upcoming season
    - Coverage: Active players
    - Value: Fantasy, betting, expectations

44. **Player FAQs** (Common questions)
    - URL: Player pages → FAQ section
    - Data: Milestones, achievements, notable games
    - Coverage: Major players
    - Value: Quick facts, trivia

45. **Triple-Doubles Tracking**
    - Column in season totals: "Trp-Dbl"
    - Data: Count of triple-doubles per season
    - Coverage: All seasons
    - Value: Milestone tracking

46. **Player News & Updates**
    - URL: Player pages → News section
    - Data: Recent player news articles
    - Coverage: Active players
    - Value: Current events tracking

47. **Player Game Highs**
    - URL: Player pages → Game Highs section
    - Data: Career high in each stat category, date of occurrence
    - Coverage: All players
    - Value: Peak performance tracking

48. **Player Playoff Series Stats** (Series-by-series)
    - URL: Player pages → Playoff Series tab
    - Data: Player stats for each playoff series
    - Coverage: All playoff players
    - Value: Postseason performance by series

49. **Player All-Star Game Stats** (All-Star appearances)
    - URL: Player pages → All-Star Games tab
    - Data: Performance in each All-Star Game
    - Coverage: All All-Stars
    - Value: All-Star legacy tracking

50. **Player Leaderboards** (Career rankings)
    - URL: Player pages → Leaderboards section
    - Data: Where player ranks all-time in each category
    - Coverage: All players
    - Value: Historical context

51. **Player by Birth Place** (Geographic tracking)
    - URL: `/friv/birthplaces.cgi`
    - Data: Players grouped by birth country/city
    - Coverage: All players
    - Value: Geographic analysis, scouting origins

52. **Player by Birth Year** (Age cohorts)
    - URL: `/friv/birthyears.cgi`
    - Data: Players born in each year
    - Coverage: All players
    - Value: Age cohort analysis

53. **Player by College** (College-to-NBA tracking)
    - URL: `/friv/colleges.fcgi`
    - Data: All NBA players from each college
    - Coverage: All players with college
    - Value: College pipeline analysis

---

**Awards & Honors (15+ types - greatly expanded):**
54. **Player of the Month** (Monthly awards)
    - URL: `/awards/pom.html`
    - Data: Winner, runner-ups, stats
    - Coverage: Modern era
    - Value: Short-term performance recognition

55. **Rookie of the Month**
    - URL: `/awards/rom.html`
    - Data: Monthly rookie awards
    - Coverage: Modern era
    - Value: Rookie development tracking

56. **Coach of the Month**
    - URL: `/awards/com.html`
    - Data: Monthly coaching awards
    - Coverage: Modern era
    - Value: Coaching effectiveness

57. **Defensive Player of the Month**
    - URL: `/awards/dpom.html`
    - Data: Monthly defensive awards
    - Coverage: Recent years
    - Value: Defensive excellence tracking

58. **Player of the Week** (Weekly awards)
    - URL: `/awards/pow.html`
    - Data: Weekly top performers
    - Coverage: Modern era
    - Value: Week-to-week excellence

59. **Social Justice Champion** (Kareem Abdul-Jabbar Trophy)
    - URL: `/awards/social-justice.html`
    - Coverage: 2021-present
    - Value: Off-court impact recognition

60. **Sportsmanship Award** (Joe Dumars Trophy)
    - URL: `/awards/sportsmanship.html`
    - Coverage: 1996-present
    - Value: Character recognition

61. **Clutch Player of the Year** (Jerry West Trophy)
    - URL: `/awards/clutch.html`
    - Coverage: 2023-present
    - Value: Clutch performance recognition

62. **In-Season Tournament MVP**
    - URL: `/awards/in-season-tournament-mvp.html`
    - Coverage: 2023-present
    - Value: Mid-season tournament recognition

63. **NBA 75th Anniversary Team**
    - URL: `/awards/nba-75th-anniversary-team.html`
    - Data: 75 greatest players selection
    - Value: Historical legacy

64. **All-Defensive Teams** (1st and 2nd team)
    - URL: `/awards/all-defense.html`
    - Coverage: 1969-present
    - Value: Defensive excellence tracking

65. **All-NBA Teams** (1st, 2nd, 3rd teams)
    - URL: `/awards/all-league.html`
    - Coverage: 1947-present
    - Value: Season excellence tracking

66. **Twyman-Stokes Teammate of the Year**
    - URL: `/awards/teammate.html`
    - Coverage: 2013-present
    - Value: Team chemistry recognition

67. **J. Walter Kennedy Citizenship Award**
    - URL: `/awards/citizenship.html`
    - Coverage: 1975-present
    - Value: Community impact recognition

68. **Executive of the Year**
    - URL: `/awards/executive.html`
    - Coverage: 1973-present
    - Value: Front office excellence

---

**All-Star Weekend Events (5 types):**
69. **Rising Stars Challenge** (Rookie/Sophomore game)
    - URL: `/allstar/rising_stars.html`
    - Data: Rosters, scores, MVP
    - Coverage: 1994-present
    - Value: Young player showcase

70. **All-Star Skills Challenge**
    - URL: `/allstar/skills.html`
    - Data: Participants, results, times
    - Coverage: 2003-present
    - Value: Guard skills showcase

71. **Three-Point Contest**
    - URL: `/allstar/three_point.html`
    - Data: Participants, scores, winners
    - Coverage: 1986-present
    - Value: Shooting excellence

72. **Slam Dunk Contest**
    - URL: `/allstar/slam_dunk.html`
    - Data: Participants, judges' scores, winners
    - Coverage: 1984-present
    - Value: Athleticism showcase

73. **Legends Game** (Retired players game)
    - URL: `/allstar/legends.html`
    - Data: Rosters, scores
    - Coverage: 1984-1993
    - Value: Historical player performance

---

**Playoff-Specific Data (3 types):**
74. **Playoff Series Results** (Series-level data)
    - URL: `/playoffs/series.html`
    - Data: All playoff series, winner/loser, dates, series length
    - Coverage: 1947-present (NBA & ABA)
    - Value: Postseason matchup analysis

75. **Playoff Series Betting Odds**
    - Data: Historical betting lines for playoff series
    - Coverage: Recent years
    - Value: Market expectations analysis

76. **7-Game Series Outcomes** (Game-by-game)
    - URL: `/friv/playoff-series.html`
    - Data: All 7-game series, game-by-game results
    - Coverage: Complete history
    - Value: Comeback analysis, series momentum

---

**Advanced Stats & Ratings (8 types):**
77. **SRS (Simple Rating System)**
    - URL: `/leagues/NBA_{season}_ratings.html`
    - Data: Team strength rating
    - Coverage: All seasons
    - Value: Team quality measure (already partially in Team Ratings)

78. **SOS (Strength of Schedule)**
    - Data: Opponent strength rating
    - Coverage: All seasons
    - Value: Schedule difficulty

79. **Adjusted Offensive Rating (ORtg/A)**
    - Data: Schedule-adjusted offensive efficiency
    - Coverage: All seasons
    - Value: Context-adjusted offense

80. **Adjusted Defensive Rating (DRtg/A)**
    - Data: Schedule-adjusted defensive efficiency
    - Coverage: All seasons
    - Value: Context-adjusted defense

81. **Adjusted Net Rating (NRtg/A)**
    - Data: Schedule-adjusted point differential
    - Coverage: All seasons
    - Value: Overall team strength

82. **Adjusted MOV (Margin of Victory)**
    - Data: Schedule-adjusted point differential
    - Coverage: All seasons
    - Value: Contextualized dominance

83. **Four Factors (Detailed)**
    - Data: eFG%, TOV%, ORB%, FTr (offensive & defensive)
    - Coverage: Modern era
    - Value: Dean Oliver's four factors
    - Note: More detailed than currently collected

84. **Pace (Possessions per 48)**
    - Data: Game tempo
    - Coverage: Modern era
    - Value: Game speed analysis

---

**Shooting Statistics (Granular) (5 types):**
85. **Shooting by Distance Zones**
    - Data: FG% by distance (0-3ft, 3-10ft, 10-16ft, 16-3PT, 3PT)
    - Coverage: Modern era (2000+)
    - Value: Shot selection optimization
    - Note: More granular than currently collected

86. **Dunk Tracking** (Dunks made and attempted)
    - Column: "Dunks"
    - Coverage: Modern era
    - Value: Rim pressure tracking

87. **Corner 3-Point Shooting** (Specific corner 3s)
    - Data: Corner 3-point attempts and %
    - Coverage: Modern era
    - Value: Shot location optimization

88. **Heave Shots** (Long-distance heaves)
    - Data: Half-court+ shots at end of quarters
    - Coverage: Modern era
    - Value: Filtering noise from shooting %

89. **Percentage of FG Assisted**
    - Data: % of made shots that were assisted
    - Coverage: Modern era
    - Value: Shot creation vs. catch-and-shoot

---

**Play-by-Play Derived Stats (Granular) (6 types):**
90. **Position Percentage Breakdown**
    - Data: % of time at PG, SG, SF, PF, C
    - Coverage: Modern era
    - Value: Positional flexibility tracking

91. **OnCourt Plus/Minus**
    - Data: Team performance when player is on court
    - Coverage: Modern era
    - Value: Impact measurement

92. **On-Off Differential**
    - Data: Team performance difference with player on vs. off
    - Coverage: Modern era
    - Value: Net impact quantification

93. **Bad Pass Turnovers** (Specific TO type)
    - Column: "BadPass"
    - Coverage: Modern era
    - Value: Turnover classification

94. **Lost Ball Turnovers** (Specific TO type)
    - Column: "LostBall"
    - Coverage: Modern era
    - Value: Turnover classification

95. **Fouls Drawn** (Not just committed)
    - Column: "Fouls Drawn"
    - Coverage: Modern era
    - Value: Drawing contact ability

96. **And1 Plays** (Fouls drawn on made shots)
    - Column: "And1"
    - Coverage: Modern era
    - Value: Contact finishing ability

97. **Shots Blocked** (On defense)
    - Column: "Blkd"
    - Coverage: Modern era
    - Value: Rim protection

---

**Miscellaneous Tools & Databases (20+ types):**
98. **Injury Report** (Current injuries)
    - URL: `/friv/injuries.fcgi`
    - Data: Current injured players, injury type, status
    - Coverage: Current season only (rolling ~30 days)
    - Value: Roster availability
    - Limitation: Historical data not retained

99. **Preseason Odds** (Betting markets)
    - URL: `/leagues/NBA_{season}_preseason_odds.html`
    - Data: Championship odds, win totals, division/conference odds
    - Coverage: Recent years
    - Value: Market expectations baseline

100. **Buzzer-Beaters Database**
    - URL: `/friv/buzzer-beaters.html`
    - Data: All game-winning shots at buzzer
    - Coverage: Complete history
    - Value: Clutch moments tracking

101. **"Cups of Coffee"** (One-game players)
    - URL: `/friv/one-game.html`
    - Data: Players with exactly 1 NBA game
    - Coverage: Complete history
    - Value: Career brevity analysis

102. **Daily Leaders** (Historical)
    - URL: `/friv/dailyleaders.cgi`
    - Data: Top performers each day in NBA history
    - Coverage: Complete history
    - Value: Historical context, "on this date"

103. **Eastern vs. Western Conference Records**
    - URL: `/friv/conf-vs-conf.html`
    - Data: Head-to-head conference performance
    - Coverage: Complete history
    - Value: Conference strength analysis

104. **Historical Standings by Date** (Standings evolution)
    - URL: `/friv/standings.fcgi`
    - Data: Standings on any given date in history
    - Coverage: Complete history
    - Value: Season progression tracking

105. **Milestones Watch** (Approaching milestones)
    - URL: `/friv/milestones.cgi`
    - Data: Players/teams close to career/franchise milestones
    - Coverage: Active players/teams
    - Value: Milestone prediction

106. **Franchise Milestones** (Team records)
    - Data: Franchise wins, playoff appearances, championships
    - Coverage: All franchises
    - Value: Franchise history

107. **MVP Award Tracker** (Season-long tracker)
    - URL: `/friv/mvp.html`
    - Data: MVP race odds throughout season
    - Coverage: Current season
    - Value: Award prediction

108. **Playoff Probabilities** (Playoff odds)
    - URL: `/friv/playoff_prob.html`
    - Data: Real-time playoff probability calculations
    - Coverage: Current season
    - Value: Playoff race tracking

109. **Roster Continuity** (Team roster turnover)
    - URL: `/friv/continuity.html`
    - Data: % of minutes returning from prior season
    - Coverage: All seasons
    - Value: Roster stability measurement

110. **Simple Projection System** (Team projections)
    - URL: `/friv/playoff_prob.html` (includes SRS projections)
    - Data: Projected win totals, playoff odds
    - Coverage: Current season
    - Value: Season forecasting

111. **Players Who Played for Multiple Teams** (Career team tracking)
    - URL: `/friv/frivolities.html`
    - Data: Players grouped by number of teams
    - Coverage: All players
    - Value: Journeyman analysis

112. **Teammates & Opponents** (Shared time tracking)
    - URL: `/friv/teammates_opponents.html`
    - Data: Who played with/against whom
    - Coverage: All players
    - Value: Connection analysis

113. **Trade Partners** (Trade history)
    - URL: `/friv/trades.html`
    - Data: Which teams have traded with each other
    - Coverage: Complete history
    - Value: Trade pattern analysis

114. **Most Games Without Playoffs** (Playoff droughts)
    - URL: `/friv/playoff-droughts.html`
    - Data: Longest active playoff droughts
    - Coverage: Current
    - Value: Franchise struggles tracking

115. **"On This Date" Historical Events**
    - URL: `/friv/on-this-date.cgi`
    - Data: Notable events/performances on specific calendar dates
    - Coverage: Complete history
    - Value: Historical trivia

116. **Last N Days Stats** (Rolling performance)
    - URL: `/friv/last_n_days_leaders.html`
    - Data: Top performers over recent stretch (7, 14, 30 days)
    - Coverage: Current season
    - Value: Hot/cold streak identification

117. **Uniform Numbers** (Jersey tracking)
    - URL: `/friv/numbers.cgi`
    - Data: Which players wore which numbers
    - Coverage: Complete history
    - Value: Jersey history, retirement candidates
    - Note: More comprehensive than documented

118. **Random Page** (Site exploration tool)
    - URL: `/friv/random.html`
    - Value: Site discovery, entertainment

119. **Linkify Tool** (Name detection)
    - Tool: Converts player names in text to links
    - Value: Content enhancement

---

## SECTION 2: WNBA DATA 🆕

**Coverage:** 1997-2025 (complete WNBA history)
**Status:** NOT in current plan at all
**Total Types:** 15+ distinct data types

120. **WNBA Season Totals**
    - URL: `/wnba/years/WNBA_{season}.html`
    - Coverage: 1997-2025
    - Data: Player season statistics

121. **WNBA Per-Game Stats**
    - Data: Per-game averages
    - Coverage: 1997-2025

122. **WNBA Advanced Stats**
    - Data: PER, WS, BPM, etc.
    - Coverage: 1997-2025

123. **WNBA Team Standings**
    - Data: Win/loss records, playoff seeds
    - Coverage: 1997-2025

124. **WNBA Team Statistics**
    - Data: Team-level performance
    - Coverage: 1997-2025

125. **WNBA Player Game Logs**
    - Data: Game-by-game stats
    - Coverage: All players

126. **WNBA All-Star Games**
    - URL: `/wnba/allstar/`
    - Coverage: 1999-2025
    - Data: Rosters, scores, MVP

127. **WNBA Draft**
    - URL: `/wnba/draft/`
    - Coverage: 1997-2025
    - Data: Draft picks, colleges

128. **WNBA Supplemental Draft**
    - URL: `/wnba/draft/WNBA_supplemental_draft.html`
    - Data: Special draft events

129. **WNBA Awards**
    - MVP, Rookie of the Year, Coach of the Year
    - All-WNBA Teams
    - Coverage: 1997-2025

130. **WNBA Playoff Statistics**
    - Data: Postseason performance
    - Coverage: 1997-2025

131. **WNBA Daily Scores**
    - Data: Historical game results
    - Coverage: 1997-2025

132. **WNBA Career Leaderboards**
    - Data: All-time leaders in each category
    - Coverage: Complete history

133. **WNBA Season Leaders**
    - Data: Single-season leaders
    - Coverage: 1997-2025

134. **WNBA Rookie Records**
    - Data: Rookie performance milestones
    - Coverage: 1997-2025

135. **WNBA Player Headshots**
    - Data: Player photos
    - Coverage: Modern era

---

## SECTION 3: G LEAGUE DATA 🆕

**Coverage:** 2002-2025 (23 seasons)
**Status:** NOT in current plan
**Total Types:** 10+ distinct data types

136. **G League Season Standings**
    - URL: `/gleague/years/NBA-D-League_{season}.html`
    - Coverage: 2002-2025
    - Data: Team records

137. **G League Player Statistics**
    - Data: Season stats (per-game, totals, advanced)
    - Coverage: 2002-2025

138. **G League Team Rosters**
    - Data: Team roster by season
    - Coverage: 2002-2025

139. **G League Game Logs**
    - Data: Player game-by-game stats
    - Coverage: 2002-2025

140. **G League Daily Scores**
    - Data: Game results
    - Coverage: 2002-2025

141. **G League Awards**
    - MVP, Rookie of the Year, All-League Teams
    - Coverage: 2002-2025

142. **G League Season Leaders**
    - Data: Top performers in each category
    - Coverage: 2002-2025

143. **G League Career Leaders**
    - Data: All-time G League statistics
    - Coverage: 2002-2025

144. **G League Top Performers**
    - Data: Recent standout performances
    - Coverage: Current season

145. **G League Box Scores**
    - Data: Game-level statistics
    - Coverage: 2002-2025

---

## SECTION 4: ABA DATA 🆕

**Coverage:** 1967-1976 (9 ABA seasons)
**Status:** NOT in current plan
**Total Types:** 12+ distinct data types

146. **ABA Season Totals**
    - URL: `/leagues/ABA_{season}.html`
    - Coverage: 1967-1976
    - Data: Player statistics

147. **ABA Per-Game Stats**
    - Data: Per-game averages
    - Coverage: 1967-1976

148. **ABA Per 36 Minutes**
    - Data: Normalized per 36 min
    - Coverage: 1967-1976

149. **ABA Per 100 Possessions**
    - Data: Pace-adjusted stats
    - Coverage: 1967-1976

150. **ABA Advanced Stats**
    - Data: Advanced metrics
    - Coverage: 1967-1976

151. **ABA Adjusted Shooting**
    - Data: League-adjusted shooting
    - Coverage: 1967-1976

152. **ABA Team Standings**
    - Data: Win/loss, playoff seeds
    - Coverage: 1967-1976

153. **ABA Team Stats** (Per game, totals, per 100 poss, advanced)
    - Coverage: 1967-1976

154. **ABA Playoff Stats**
    - Data: Postseason performance
    - Coverage: 1967-1976

155. **ABA All-Star Games**
    - URL: `/allstar/` (includes ABA)
    - Coverage: 1968-1976
    - Data: Rosters, MVP, scores

156. **ABA Awards**
    - MVP, Rookie of the Year, All-ABA Teams
    - Coverage: 1967-1976

157. **ABA Coaches**
    - Data: Coaching records
    - Coverage: 1967-1976

---

## SECTION 5: BAA DATA 🆕

**Coverage:** 1946-1949 (3 BAA seasons, pre-NBA)
**Status:** NOT in current plan
**Total Types:** 8+ distinct data types

158. **BAA Season Totals**
    - URL: `/leagues/BAA_{season}.html`
    - Coverage: 1946-1949
    - Data: Player statistics

159. **BAA Per-Game Stats**
    - Coverage: 1946-1949

160. **BAA Team Standings**
    - Coverage: 1946-1949

161. **BAA Team Stats**
    - Coverage: 1946-1949

162. **BAA Playoff Stats**
    - Coverage: 1946-1949

163. **BAA Champions**
    - Data: Championship results
    - Coverage: 1946-1949

164. **BAA Coaches**
    - Data: Coaching records
    - Coverage: 1946-1949

165. **BAA Draft** (if available)
    - Coverage: 1946-1949

---

## SECTION 6: INTERNATIONAL BASKETBALL 🆕

**Coverage:** Varies by competition (1936-2025)
**Status:** NOT in current plan
**Total Types:** 40+ competitions × multiple data types = 100+ distinct datasets

### Olympics
166. **Men's Olympics Player Stats** (1936-2024)
167. **Women's Olympics Player Stats** (1936-2024)
168. **Men's Olympics Team Stats** (1936-2024)
169. **Women's Olympics Team Stats** (1936-2024)
170. **Olympics Medal Standings** (Historical)

### FIBA World Cup
171. **FIBA World Cup Player Stats** (2010-2023)
172. **FIBA World Cup Team Stats** (2010-2023)
173. **FIBA World Cup Standings** (2010-2023)

### European Leagues

**EuroLeague (2000-2025):**
174. EuroLeague Player Stats
175. EuroLeague Team Stats
176. EuroLeague Standings
177. EuroLeague Playoff Stats
178. EuroLeague Finals Results

**EuroCup (2002-2025):**
179. EuroCup Player Stats
180. EuroCup Team Stats
181. EuroCup Standings

**Liga ACB - Spain (1983-2025):**
182. Liga ACB Player Stats
183. Liga ACB Team Stats
184. Liga ACB Standings

**Lega Basket Serie A - Italy (1998-2025):**
185. Serie A Player Stats
186. Serie A Team Stats
187. Serie A Standings

**Greek Basket League (2001-2025):**
188. Greek League Player Stats
189. Greek League Team Stats
190. Greek League Standings

**LNB Pro A - France (2002-2025):**
191. Pro A Player Stats
192. Pro A Team Stats
193. Pro A Standings

**Chinese Basketball Association (2011-2025):**
194. CBA Player Stats
195. CBA Team Stats
196. CBA Standings

**NBL - Australia (2011-2025):**
197. NBL Player Stats
198. NBL Team Stats
199. NBL Standings

**ABA League First Division:**
200. ABA League Player Stats
201. ABA League Team Stats

**Israeli Basketball Premier League:**
202. Israeli League Stats

**Turkish Basketball Super League:**
203. Turkish League Stats

**VTB United League:**
204. VTB League Stats

---

## SECTION 7: COLLEGE BASKETBALL 🆕

**Coverage:** Complete NCAA history (1891-present for men's, 1981-present for women's)
**Status:** NOT in current plan (redirects to Sports-Reference.com/cbb/)
**Total Types:** 30+ distinct data types

**NOTE:** College data redirects to Sports-Reference.com (separate site)

205. **NCAA Division I Player Stats** (Season-by-season)
206. **NCAA Division I Team Stats**
207. **NCAA Division I Standings** (Conference standings)
208. **NCAA Division I Schedule & Results**
209. **NCAA Tournament Results** (Men's & Women's, complete history)
210. **NIT Results** (Complete history)
211. **CBI Tournament Results**
212. **CIT Tournament Results**
213. **NCAA Tournament Bracket History**
214. **NCAA Conference Data** (All conferences, historical)
215. **College Coach Records**
216. **College Player Game Logs**
217. **College Team Game Logs**
218. **College Awards:**
    - Player of the Year (AP, Wooden, Naismith, etc.)
    - All-America Teams
    - Conference Player of the Year
    - Conference awards
219. **College Polls** (AP Poll, Coaches Poll, historical)
220. **College Statistical Leaders** (Season leaders by category)
221. **College Career Leaders** (All-time college leaders)
222. **NCAA Tournament Most Outstanding Player**
223. **College Player Season Finder** (Query tool)
224. **College Team Season Finder** (Query tool)
225. **College Player Biographical Data**
226. **College Recruiting Classes** (If available)
227. **College Transfer Portal Data** (Recent years)
228. **Women's College Basketball** (Complete datasets, 1981+)
229. **Division II & III Data** (If available)
230. **College Buzzer-Beaters**
231. **College Milestones**
232. **College Conference Tournament Results**
233. **College Daily Leaders**
234. **College "One Shining Moment" Database** (Tournament highlights)

---

## CROSS-REFERENCE SUMMARY

### Data Coverage by Domain

| Domain | Years Covered | Data Types | In Current Plan? | Priority |
|--------|---------------|-----------|------------------|----------|
| **NBA** | 1946-2025 | 119 types | 32 types (27%) | ✅ HIGH |
| **WNBA** | 1997-2025 | 16 types | 0 types (0%) | 🆕 NEW |
| **G League** | 2002-2025 | 10 types | 0 types (0%) | 🆕 NEW |
| **ABA** | 1967-1976 | 12 types | 0 types (0%) | 🆕 NEW |
| **BAA** | 1946-1949 | 8 types | 0 types (0%) | 🆕 NEW |
| **International** | 1936-2025 | 40 types | 0 types (0%) | 🆕 NEW |
| **College** | 1891-2025 | 30 types | 0 types (0%) | 🆕 NEW |
| **TOTAL** | - | **234+ types** | **32 types (14%)** | - |

---

### NBA Data Coverage Breakdown

| Category | Already Collected | Already Planned | NEW Discoveries | Total |
|----------|-------------------|-----------------|-----------------|-------|
| **Player Stats** | 7 types | 6 types | 12 types | 25 |
| **Team Stats** | 4 types | 4 types | 8 types | 16 |
| **Advanced Metrics** | 2 types | 2 types | 8 types | 12 |
| **Awards/Honors** | 1 type | 1 type | 15 types | 17 |
| **Shooting** | 1 type | 1 type | 5 types | 7 |
| **Play-by-Play** | 1 type | 0 types | 6 types | 7 |
| **Salaries/Contracts** | 0 types | 0 types | 6 types | 6 |
| **All-Star Events** | 0 types | 0 types | 5 types | 5 |
| **Playoff-Specific** | 1 type | 0 types | 3 types | 4 |
| **Tools/Misc** | 0 types | 0 types | 20 types | 20 |
| **TOTAL NBA** | **17** | **14** | **88** | **119** |

---

## GAPS IDENTIFIED

### Critical Gaps in Current Plan

**1. Entire Leagues Missing:**
- ❌ WNBA (1997-2025) - 16 data types
- ❌ G League (2002-2025) - 10 data types
- ❌ ABA (1967-1976) - 12 data types
- ❌ BAA (1946-1949) - 8 data types
- ❌ International (15+ leagues) - 40 data types
- ❌ College (NCAA complete) - 30 data types
- **Total: 116 data types from non-NBA leagues**

**2. NBA Data Categories Missing:**
- ❌ Salaries & Contracts (6 types)
- ❌ Awards - Most monthly/weekly awards (11 types)
- ❌ All-Star Weekend Events (5 types)
- ❌ Playoff Series Data (3 types)
- ❌ Granular Shooting Stats (5 types)
- ❌ Granular PBP Stats (6 types)
- ❌ Miscellaneous Tools/Databases (20 types)
- ❌ Player-Specific (9 types not planned)
- ❌ Team-Specific (5 types not planned)
- ❌ Advanced Ratings (6 types not fully covered)
- **Total: 76 NBA data types not in plan**

**3. Data Granularity Gaps:**
- Current plan: "Shooting Stats" (1 type)
- Available: 7 shooting stat types with distance zones, dunks, corners, heaves
- Current plan: "Play-by-Play" (1 type)
- Available: 7 PBP-derived stat types (on/off, position %, turnover types, fouls drawn, etc.)

---

## RECOMMENDATIONS

### Immediate Actions

**1. Update Basketball Reference Expansion Plan to include:**
- TIER 5: WNBA Complete Collection (16 types, 1997-2025)
- TIER 6: ABA Historical Data (12 types, 1967-1976)
- TIER 7: G League Data (10 types, 2002-2025)
- TIER 8: BAA Historical Data (8 types, 1946-1949)
- TIER 9: International Basketball (40 types, select competitions)
- TIER 10: College Basketball (30 types, select years/tournaments)

**2. Expand NBA Tiers to include missing categories:**
- Add to TIER 1: Salaries & Contracts (high value for analysis)
- Add to TIER 2: All-Star Weekend Events, Playoff Series Data
- Add to TIER 3: Monthly/weekly awards, Misc tools
- Update existing tiers with granular shooting and PBP stats

**3. Prioritization by Use Case:**

**For Panel Data System:**
- ✅ Priority 1: All granular player/team stats by season
- ✅ Priority 2: Game-level and series-level data
- ⚠️ Priority 3: Awards and honors (useful but not critical)
- ⚠️ Priority 4: Tools and databases (nice-to-have)

**For Historical Completeness:**
- ✅ Include ABA (1967-1976) - extends history to pre-merger
- ✅ Include BAA (1946-1949) - true league origins
- ⚠️ G League - developmental context
- ⚠️ WNBA - complete women's basketball

**For Multi-Sport Expansion:**
- ⚠️ College - scouting and draft pipeline
- ⚠️ International - global basketball context

---

### Implementation Priority Matrix

| Tier | Data Types | Estimated Records | Time | Priority | Rationale |
|------|-----------|-------------------|------|----------|-----------|
| **1** | NBA High Value (5) | 150K | 15-20h | **IMMEDIATE** | Already planned |
| **2** | NBA Strategic (4) | 200K | 20-25h | **IMMEDIATE** | Already planned |
| **3** | NBA Specialized (4) | 5K | 5-7h | **NEAR-TERM** | Already planned |
| **4** | NBA Player Granular (2) | 500K-10M | 50-100h | **SELECTIVE** | Already planned |
| **5A** | NBA Salaries (6) | 50K | 8-10h | **HIGH** | Financial analysis |
| **5B** | NBA Shooting Granular (5) | Included | 2-3h | **HIGH** | Extend existing |
| **5C** | NBA PBP Granular (6) | Included | 2-3h | **HIGH** | Extend existing |
| **6** | NBA Awards Expanded (11) | 20K | 5-6h | **MEDIUM** | Recognition tracking |
| **7** | ABA Historical (12) | 50K | 10-12h | **MEDIUM** | Pre-merger era |
| **8** | BAA Historical (8) | 10K | 4-5h | **MEDIUM** | League origins |
| **9** | NBA Misc Tools (20) | Varies | 10-15h | **LOW** | Nice-to-have |
| **10** | WNBA Complete (16) | 100K | 15-20h | **OPTIONAL** | Separate league |
| **11** | G League (10) | 30K | 8-10h | **OPTIONAL** | Developmental |
| **12** | International Select (10) | 50K | 20-30h | **OPTIONAL** | Global context |
| **13** | College Select (10) | 200K | 30-40h | **OPTIONAL** | Scouting pipeline |

---

### Storage Impact

**Current Plan (Tiers 1-4):**
- Records: 350K-10M (depending on Tier 4 selection)
- Storage: 260 MB - 10 GB
- Cost: $0.006 - 0.23/month

**With All New NBA Data (Tiers 5A-9):**
- Additional Records: +140K
- Additional Storage: +300 MB
- Additional Cost: +$0.007/month
- **Total: 490K-10M records, 560 MB - 10 GB, $0.013 - 0.24/month**

**With Non-NBA Leagues (Tiers 10-13):**
- Additional Records: +380K
- Additional Storage: +800 MB
- Additional Cost: +$0.018/month
- **Grand Total: 870K-10M records, 1.36 GB - 11 GB, $0.031 - 0.26/month**

**Conclusion:** Even collecting ALL basketball data from Sports Reference is negligible cost (<$0.30/month).

---

### Time Investment

**Current Plan:** 40-60 hours (Tiers 1-4, selective Tier 4)

**Full NBA Collection:**
- Tiers 1-4: 40-60 hours
- Tiers 5-9: 27-37 hours
- **Total NBA: 67-97 hours**

**All Basketball Data:**
- Tiers 1-9 (NBA): 67-97 hours
- Tiers 10-13 (Other leagues): 73-100 hours
- **Grand Total: 140-197 hours**

**Spread over:**
- 10 weeks @ 14-20 hours/week = Comprehensive collection
- 20 weeks @ 7-10 hours/week = Leisurely pace

---

## NEXT STEPS

1. **Update PHASE_0_BASKETBALL_REFERENCE_EXPANSION.md** with:
   - 76 new NBA data types (Tiers 5A-9)
   - 6 new league sections (Tiers 10-13)
   - Updated implementation timeline
   - Storage and cost projections
   - Prioritization matrix

2. **Create sub-phase files:**
   - PHASE_0_WNBA_COLLECTION.md (if pursuing Tier 10)
   - PHASE_0_ABA_BAA_COLLECTION.md (if pursuing Tiers 7-8)
   - PHASE_0_INTERNATIONAL_COLLECTION.md (if pursuing Tier 12)
   - PHASE_0_COLLEGE_COLLECTION.md (if pursuing Tier 13)

3. **Confirm with user:**
   - Which tiers to pursue?
   - NBA-only or all basketball?
   - Selective vs. comprehensive approach?

4. **Update comprehensive scraper:**
   - Extend to support new data types
   - Add league-specific scraping modes
   - Update rate limiting for multiple domains

---

## CONCLUSION

**Basketball-Reference.com contains 234+ distinct basketball data types across 7 leagues/domains.**

**Current plan captures 32 NBA data types (14% of available data).**

**To achieve COMPLETE basketball data coverage:**
- ✅ Collect all 119 NBA data types (Tiers 1-9)
- ✅ Collect ABA & BAA for historical completeness (Tiers 7-8)
- ⚠️ Optionally collect WNBA, G League, International, College (Tiers 10-13)

**For panel data purposes, priority recommendation:**
1. **Tiers 1-4** (already planned) - Essential foundation
2. **Tiers 5A-5C** (NBA salaries + granular stats) - High analytical value
3. **Tiers 7-8** (ABA & BAA) - Historical completeness to 1946
4. **Tier 6** (Expanded awards) - Recognition tracking
5. **Tiers 10-13** (Other leagues) - Only if multi-league analysis desired

**Estimated total time for comprehensive NBA collection (Tiers 1-9): 67-97 hours**

**User decision required:** Scope of collection (NBA-only vs. all basketball)?

---

**Document Status:** Complete and ready for user review
**Next Action:** User confirmation of collection scope
**Last Updated:** October 11, 2025