# Basketball Reference - Additional Data Sources

**Status:** Analysis Complete
**Date:** October 10, 2025
**Purpose:** Identify additional valuable data sources beyond what we've already collected

## Already Collected ✅

1. **Season Totals** - Basic counting stats (75 years, 1947-2025)
2. **Advanced Totals** - Advanced metrics (PER, WS, BPM, VORP) (67 years, 1953-2025)
3. **Team Standings** - Win/loss records (29 years, 1971-2025)
4. **Transactions** - Trades, signings, waivers (25 years, 2001-2025)

## High-Priority Additions 🎯

### 1. **Draft Data** (1947-present)
**URL Pattern:** `https://www.basketball-reference.com/draft/NBA_YYYY.html`

**Value:**
- Links players to draft position (1st pick vs. 2nd round impacts expectations)
- College/international origin (feature for ML models)
- Career performance vs. draft position (ROI analysis)
- Trade value context (draft picks in transactions)

**Data Fields:**
- Pick number (overall + round)
- Team (drafting team)
- Player name + slug
- College/country
- Career stats (games, points, assists, rebounds)
- Advanced metrics (WS, BPM, VORP)

**Coverage:** Complete from 1947-2025 (79 drafts)

**Use Cases:**
- Feature engineering: "draft_position", "years_since_draft"
- Validate roster data (rookie identification)
- Historical context for player expectations
- ML features: college pedigree, draft class strength

---

### 2. **Awards & All-NBA Selections** (1946-present)
**URL Patterns:**
- MVP: `/awards/mvp.html`
- All-NBA: `/awards/all_league.html`
- All-Star: `/awards/all_star.html`
- All-Defensive: `/awards/all_defense.html`
- Rookie of Year: `/awards/roy.html`
- DPOY: `/awards/dpoy.html`
- 6th Man: `/awards/smoy.html`
- MIP: `/awards/mip.html`
- Coach of Year: `/awards/coy.html`

**Value:**
- Player quality indicators (All-NBA 1st team vs. 2nd team vs. none)
- Historical context for performance evaluation
- Career trajectory markers (MIP, rookie awards)
- Coaching effectiveness (COY)
- ML features: "all_nba_selections", "all_star_appearances"

**Data Structure:**
- Season, player, award type, team selection (1st/2nd/3rd)
- Vote counts/shares
- Points/wins shares at time of award

**Use Cases:**
- Weight player contributions by accolades
- Identify breakout seasons (MIP correlation)
- Validate "star player" designation
- Historical player ranking

---

### 3. **Per-Game Stats** (1947-present)
**URL Pattern:** `https://www.basketball-reference.com/leagues/NBA_YYYY_per_game.html`

**Value:**
- Normalized stats (accounts for minutes played)
- Better for cross-era comparisons
- Identifies efficiency vs. volume scorers

**Data Fields:**
- All counting stats divided by games played
- PPG, RPG, APG, SPG, BPG, TOV/G
- FG%, 3P%, FT%

**Why Better Than Totals:**
- Fairer comparison (starter vs. bench player)
- Normalized for games played (injury seasons)
- Standard metric for player evaluation

---

### 4. **Shooting Stats** (2000-present)
**URL Pattern:** `https://www.basketball-reference.com/leagues/NBA_YYYY_shooting.html`

**Value:**
- Shot location data (0-3ft, 3-10ft, 10-16ft, 16-3P, 3P)
- Shooting percentages by distance
- Shot distribution (% of FGA from each zone)
- Assisted vs. unassisted FG

**Data Fields:**
- % FGA from 0-3 ft, 3-10 ft, 10-16 ft, 16ft-3P, 3P
- FG% from each distance
- % of 2P/3P assisted
- Dunks, corner 3s, heaves

**Use Cases:**
- Shooting profile analysis
- Position identification (big men vs. guards)
- Evolution of 3-point shooting
- Shot selection quality

---

### 5. **Play-by-Play Stats** (2001-present)
**URL Pattern:** `https://www.basketball-reference.com/leagues/NBA_YYYY_play-by-play.html`

**Value:**
- On-court/off-court differentials
- Plus-minus data
- Positional estimates
- Time played at each position

**Data Fields:**
- % time at PG, SG, SF, PF, C
- On-court +/-
- Bad passes, lost balls
- Shooting fouls drawn

**Use Cases:**
- Positional flexibility (positionless basketball)
- Impact metrics (on/off court splits)
- Turnover classification (bad pass vs. lost ball)

---

### 6. **Team Ratings** (1974-present)
**URL Pattern:** `https://www.basketball-reference.com/leagues/NBA_YYYY_ratings.html`

**Value:**
- Offensive/defensive efficiency ratings
- Strength of schedule
- Simple Rating System (SRS)
- Pace factor

**Data Fields:**
- Offensive Rating (points per 100 possessions)
- Defensive Rating (points allowed per 100 possessions)
- Net Rating (ORtg - DRtg)
- Pace (possessions per 48 minutes)
- SRS (point differential adjusted for schedule)

**Use Cases:**
- Team quality assessment
- Opponent strength adjustment
- Predict game outcomes
- Era-adjusted comparisons

---

### 7. **Injury/Illness Designations** (2020-present)
**URL Pattern:** Found in transactions data

**Value:**
- Explains player absences
- Data quality validation (missing game data)
- Load management tracking

**Currently:** Captured in transactions as "injury_designation" type ✅

---

### 8. **Playoff Stats** (1947-present)
**URL Patterns:**
- Season totals: `/playoffs/NBA_YYYY.html`
- Per game: `/playoffs/NBA_YYYY_per_game.html`
- Advanced: `/playoffs/NBA_YYYY_advanced.html`

**Value:**
- Separate playoff performance from regular season
- High-stakes performance indicators
- Star player validation (clutch performance)

**Data Fields:**
- Same as regular season stats but for playoffs only
- Series-level data
- Elimination game performance

**Use Cases:**
- Identify clutch performers
- Separate sample for ML models
- Historical playoff performance analysis

---

### 9. **Salaries** (1985-present)
**URL Pattern:** `https://www.basketball-reference.com/contracts/`

**Value:**
- Player value assessment (performance vs. salary)
- Cap space analysis
- Contract status (years remaining)
- Trade value context

**Data Fields:**
- Salary by season
- Contract length
- Guaranteed money
- Team options, player options

**Use Cases:**
- Value over replacement (VORP vs. salary)
- Trade feasibility
- Team-building strategy
- Underpaid/overpaid identification

**Note:** May require separate scraping approach (different page structure)

---

### 10. **Coach Records** (1947-present)
**URL Pattern:** `https://www.basketball-reference.com/leagues/NBA_YYYY_coaches.html`

**Value:**
- Coaching effectiveness
- Roster stability (coaching changes)
- Winning percentage by coach

**Data Fields:**
- Coach name
- Team
- Games, wins, losses
- Playoff record
- Years with team

**Use Cases:**
- Control variable for team performance
- Coaching change impact
- Historical coaching analysis

---

### 11. **Game-by-Game Results** (1947-present)
**URL Pattern:** `https://www.basketball-reference.com/leagues/NBA_YYYY_games.html`

**Value:**
- Complete season schedule
- Game outcomes (score, OT)
- Attendance data
- Arena information

**Data Fields:**
- Date, teams, score
- OT periods
- Attendance
- Arena, notes

**Use Cases:**
- Game-level analysis
- Schedule difficulty
- Home/away splits
- Temporal patterns (back-to-back games)

**Note:** Less detailed than ESPN/hoopR play-by-play but provides schedule context

---

### 12. **Standings by Date** (1947-present)
**URL Pattern:** `https://www.basketball-reference.com/leagues/NBA_YYYY_standings_by_date.html`

**Value:**
- Team performance over time
- Playoff race context
- Win streak/loss streak identification

**Data Fields:**
- Date, team, wins, losses, win%
- Games back
- Division/conference rank

**Use Cases:**
- Temporal analysis (team improvement/decline)
- Playoff race pressure
- Trade deadline context

---

## Medium-Priority Additions 📊

### 13. **Adjusted Shooting Stats** (2000-present)
- True shooting % adjustments
- Effective field goal %
- Shot quality metrics

### 14. **Rookies Stats** (1947-present)
- Filtered view of rookie performance
- First-year player identification

### 15. **Per 36 Minutes Stats** (1974-present)
- Normalized for playing time
- Bench player evaluation

### 16. **Per 100 Possessions Stats** (1974-present)
- Pace-adjusted stats
- Cross-era comparisons

---

## Lower-Priority / Specialized 📑

### 17. **Hall of Fame Inductees**
- Historical player importance
- Legacy indicators

### 18. **College Stats Links**
- Player development tracking
- Pre-NBA performance

### 19. **International Stats**
- Non-NBA career data
- Player background

### 20. **G-League Stats**
- Two-way player tracking
- Development league performance

---

## Recommended Implementation Priority

### Phase 1 - High Value (Immediate)
1. **Draft Data** - Critical for player context
2. **Awards/All-NBA** - Quality indicators
3. **Per-Game Stats** - Better normalization than totals

### Phase 2 - Analytical Depth (Near-term)
4. **Shooting Stats** - Shot profiles
5. **Play-by-Play Stats** - Positional data
6. **Team Ratings** - Opponent strength

### Phase 3 - Complete Picture (Long-term)
7. **Playoff Stats** - Separate dataset
8. **Salaries** - Value analysis
9. **Game-by-Game Results** - Schedule context
10. **Coach Records** - Control variable

### Phase 4 - Enhancement (Future)
11. **Standings by Date** - Temporal patterns
12. **Adjusted Shooting** - Advanced metrics
13. **Specialized Stats** - Per 36, Per 100

---

## Data Quality Benefits

**How These Help Our Multi-Source Integration:**

1. **Draft Data** → Validates rookie identification across ESPN/hoopR
2. **Awards** → Confirms "star player" designation
3. **Shooting Stats** → Cross-validates position assignments
4. **Team Ratings** → Explains opponent-adjusted performance gaps
5. **Salaries** → Identifies trade likelihood (contract situations)
6. **Playoffs** → Separates regular season from postseason data quality

---

## Next Steps

1. **Create draft scraper** (highest priority)
2. **Create awards scraper** (quality indicators)
3. **Extend season stats scraper** to include per-game, shooting, play-by-play
4. **Design unified schema** for all Basketball Reference data types
5. **Build validation layer** using awards/draft data to validate ESPN/hoopR

---

## Storage Impact

**Current S3 Usage:**
- Basketball Reference: ~200 MB (season totals, advanced, standings, transactions)

**Estimated Additional:**
- Draft: ~5 MB (79 drafts × ~60 players)
- Awards: ~2 MB (79 years × multiple awards)
- Per-Game: ~150 MB (same as totals)
- Shooting: ~100 MB (25 years × detailed breakdowns)
- Play-by-Play: ~100 MB (24 years × on/off court data)
- Team Ratings: ~5 MB (50 years × 30 teams)
- Playoffs: ~100 MB (separate from regular season)
- **Total New:** ~462 MB

**Total Basketball Reference:** ~662 MB (still very manageable)

---

## Conclusion

Basketball Reference contains a wealth of additional data beyond what we've collected. The **highest-value additions are:**

1. **Draft data** (player context)
2. **Awards/All-NBA** (quality indicators)
3. **Per-game stats** (better normalization)
4. **Shooting stats** (position validation)

These four alone would significantly enhance our data quality validation and provide rich features for ML models.
