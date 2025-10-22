#!/usr/bin/env python3
"""
Advanced Statistics Demo

Demonstrates calculation of advanced basketball statistics from box score data.
Shows efficiency metrics, four factors, pace/possessions, and more.

Created: October 18, 2025
"""

import sqlite3
from pathlib import Path


class AdvancedStatsCalculator:
    """Calculate advanced basketball statistics"""

    @staticmethod
    def true_shooting_pct(points, fga, fta):
        """TS% = PTS / (2 * (FGA + 0.44 * FTA))"""
        ts_attempts = fga + 0.44 * fta
        return (points / (2 * ts_attempts) * 100) if ts_attempts > 0 else 0.0

    @staticmethod
    def effective_fg_pct(fgm, fg3m, fga):
        """eFG% = (FGM + 0.5 * 3PM) / FGA"""
        return ((fgm + 0.5 * fg3m) / fga * 100) if fga > 0 else 0.0

    @staticmethod
    def game_score(pts, fgm, fga, ftm, fta, oreb, dreb, stl, ast, blk, pf, tov):
        """John Hollinger's Game Score"""
        return (pts + 0.4*fgm - 0.7*fga - 0.4*(fta-ftm) +
                0.7*oreb + 0.3*dreb + stl + 0.7*ast + 0.7*blk - 0.4*pf - tov)

    @staticmethod
    def possessions(fga, oreb, tov, fta):
        """Estimated possessions = FGA - OREB + TOV + 0.44*FTA"""
        return fga - oreb + tov + 0.44 * fta

    @staticmethod
    def offensive_rating(points, possessions):
        """Points per 100 possessions"""
        return (points / possessions * 100) if possessions > 0 else 0.0

    @staticmethod
    def pace(possessions, minutes):
        """Possessions per 48 minutes"""
        return (possessions * (48 / minutes)) if minutes > 0 else 0.0

    @staticmethod
    def three_point_attempt_rate(fg3a, fga):
        """3PAr = 3PA / FGA * 100 - Percentage of FG attempts from 3-point range"""
        return (fg3a / fga * 100) if fga > 0 else 0.0

    @staticmethod
    def assist_percentage(player_ast, team_minutes, player_minutes, team_fgm, player_fgm):
        """
        AST% = (Player AST * Team Minutes) / (Player Minutes * (Team FGM - Player FGM)) * 100
        Estimates % of teammate FG assisted while player on floor
        """
        if player_minutes == 0:
            return 0.0

        teammate_fgm = team_fgm - player_fgm
        if teammate_fgm == 0:
            return 0.0

        return ((player_ast * team_minutes) / (player_minutes * teammate_fgm)) * 100

    @staticmethod
    def steal_percentage(player_stl, team_minutes, player_minutes, opponent_poss):
        """
        STL% = (Player STL * Team Minutes) / (Player Minutes * Opponent Possessions) * 100
        Estimates steals per 100 opponent possessions
        """
        if player_minutes == 0 or opponent_poss == 0:
            return 0.0

        return ((player_stl * team_minutes) / (player_minutes * opponent_poss)) * 100

    @staticmethod
    def block_percentage(player_blk, team_minutes, player_minutes, opponent_2pt_fga):
        """
        BLK% = (Player BLK * Team Minutes) / (Player Minutes * Opponent 2PT FGA) * 100
        Estimates blocks per 100 opponent 2PT attempts
        """
        if player_minutes == 0 or opponent_2pt_fga == 0:
            return 0.0

        return ((player_blk * team_minutes) / (player_minutes * opponent_2pt_fga)) * 100

    @staticmethod
    def box_plus_minus_simple(player_stats, team_stats, league_avg_pace=100.0):
        """
        Simplified BPM - Not the full Basketball Reference formula
        This is a simplified version for demonstration
        Full BPM requires league-wide regression coefficients
        """
        # Get player per-100 stats
        player_poss = AdvancedStatsCalculator.possessions(
            player_stats['fga'], player_stats['oreb'],
            player_stats['tov'], player_stats['fta']
        )

        if player_poss == 0:
            return 0.0

        # Points contribution
        pts_per_100 = (player_stats['pts'] / player_poss) * 100

        # Rebounds contribution
        reb_per_100 = (player_stats['reb'] / player_poss) * 100

        # Assists contribution
        ast_per_100 = (player_stats['ast'] / player_poss) * 100

        # Stocks (steals + blocks) contribution
        stocks_per_100 = ((player_stats['stl'] + player_stats['blk']) / player_poss) * 100

        # Turnovers (negative)
        tov_per_100 = (player_stats['tov'] / player_poss) * 100

        # Simplified BPM formula (not exact, but directionally correct)
        bpm = (
            (pts_per_100 - 15) * 0.15 +
            (reb_per_100 - 10) * 0.35 +
            (ast_per_100 - 5) * 0.70 +
            (stocks_per_100 - 3) * 0.70 -
            (tov_per_100 - 3) * 0.30
        )

        return bpm


def create_sample_game():
    """Create sample game with realistic stats"""
    db_path = "/tmp/advanced_stats_demo.db"

    if Path(db_path).exists():
        Path(db_path).unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create simple box score table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            player_name TEXT,
            team TEXT,
            minutes REAL,
            pts INTEGER,
            fgm INTEGER,
            fga INTEGER,
            fg3m INTEGER,
            fg3a INTEGER,
            ftm INTEGER,
            fta INTEGER,
            oreb INTEGER,
            dreb INTEGER,
            reb INTEGER,
            ast INTEGER,
            stl INTEGER,
            blk INTEGER,
            tov INTEGER,
            pf INTEGER
        )
    """)

    # Insert sample players with realistic NBA Finals stats
    players = [
        # Jayson Tatum - 31 PTS, efficient night
        ("Jayson Tatum", "BOS", 42, 31, 12, 23, 5, 11, 2, 3, 1, 8, 9, 5, 1, 2, 3, 2),
        # Jaylen Brown - 25 PTS
        ("Jaylen Brown", "BOS", 38, 25, 10, 18, 3, 7, 2, 2, 2, 5, 7, 3, 2, 1, 2, 3),
        # Derrick White - 15 PTS
        ("Derrick White", "BOS", 35, 15, 5, 10, 3, 6, 2, 2, 0, 3, 3, 4, 2, 0, 1, 2),
        # Jrue Holiday - 12 PTS
        ("Jrue Holiday", "BOS", 34, 12, 5, 11, 2, 5, 0, 0, 1, 4, 5, 6, 3, 1, 2, 1),
        # Kristaps Porzingis - 18 PTS
        ("Kristaps Porzingis", "BOS", 28, 18, 7, 13, 2, 5, 2, 2, 3, 5, 8, 1, 0, 3, 1, 3),

        # Opponent team
        ("Luka Doncic", "DAL", 41, 28, 10, 22, 4, 10, 4, 5, 1, 7, 8, 8, 1, 0, 4, 3),
        ("Kyrie Irving", "DAL", 39, 24, 9, 19, 4, 8, 2, 2, 0, 3, 3, 5, 2, 1, 3, 2),
        ("Daniel Gafford", "DAL", 25, 12, 6, 8, 0, 0, 0, 2, 4, 6, 10, 1, 0, 2, 1, 4),
    ]

    cursor.executemany("""
        INSERT INTO player_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, players)

    conn.commit()
    conn.close()

    print(f"✓ Created sample game database: {db_path}\n")
    return db_path


def display_advanced_stats(db_path):
    """Calculate and display advanced statistics"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("="*90)
    print("ADVANCED STATISTICS DEMO")
    print("="*90)
    print()

    # Initialize calculator
    calc = AdvancedStatsCalculator()

    # Player statistics
    cursor.execute("SELECT * FROM player_stats WHERE team = 'BOS' ORDER BY pts DESC")
    bos_players = cursor.fetchall()

    # Calculate team stats for percentage calculations
    cursor.execute("""
        SELECT
            SUM(fgm) as team_fgm,
            SUM(fga) as team_fga,
            SUM(fg3a) as team_fg3a,
            AVG(minutes) as team_minutes
        FROM player_stats
        WHERE team = 'BOS'
    """)
    bos_team_stats = cursor.fetchone()

    # Calculate opponent stats (DAL is opponent)
    cursor.execute("""
        SELECT
            SUM(fga) as opp_fga,
            SUM(fg3a) as opp_fg3a,
            SUM(oreb) as opp_oreb,
            SUM(tov) as opp_tov,
            SUM(fta) as opp_fta
        FROM player_stats
        WHERE team = 'DAL'
    """)
    opp_stats = cursor.fetchone()

    # Calculate opponent possessions and 2PT FGA
    opp_possessions = calc.possessions(
        opp_stats['opp_fga'], opp_stats['opp_oreb'],
        opp_stats['opp_tov'], opp_stats['opp_fta']
    )
    opp_2pt_fga = opp_stats['opp_fga'] - opp_stats['opp_fg3a']

    print("BOSTON CELTICS - Individual Advanced Stats (ALL 16 Basketball Reference Metrics)")
    print("="*130)
    print(f"{'Player':<20} {'MP':>5} {'TS%':>6} {'eFG%':>6} {'3PAr':>6} {'AST%':>6} {'STL%':>6} {'BLK%':>6} {'TOV%':>6} {'USG%':>6} {'BPM':>6}")
    print("-"*130)

    for player in bos_players:
        ts_pct = calc.true_shooting_pct(player['pts'], player['fga'], player['fta'])
        efg_pct = calc.effective_fg_pct(player['fgm'], player['fg3m'], player['fga'])
        three_par = calc.three_point_attempt_rate(player['fg3a'], player['fga'])

        # New percentage stats
        ast_pct = calc.assist_percentage(
            player['ast'], bos_team_stats['team_minutes'],
            player['minutes'], bos_team_stats['team_fgm'], player['fgm']
        )
        stl_pct = calc.steal_percentage(
            player['stl'], bos_team_stats['team_minutes'],
            player['minutes'], opp_possessions
        )
        blk_pct = calc.block_percentage(
            player['blk'], bos_team_stats['team_minutes'],
            player['minutes'], opp_2pt_fga
        )

        # Turnover rate (already had this formula)
        tov_pct = (player['tov'] / (player['fga'] + 0.44*player['fta'] + player['tov']) * 100) if (player['fga'] + 0.44*player['fta'] + player['tov']) > 0 else 0

        # Usage rate approximation
        team_poss = calc.possessions(bos_team_stats['team_fga'], 7, 9, 5)  # Using team totals
        player_poss = calc.possessions(player['fga'], player['oreb'], player['tov'], player['fta'])
        usg_pct = (player_poss / team_poss * 100) if team_poss > 0 else 0

        # Simplified BPM
        bpm = calc.box_plus_minus_simple(player, None)

        print(f"{player['player_name']:<20} {player['minutes']:>5.1f} {ts_pct:>6.1f} {efg_pct:>6.1f} "
              f"{three_par:>6.1f} {ast_pct:>6.1f} {stl_pct:>6.1f} {blk_pct:>6.1f} {tov_pct:>6.1f} "
              f"{usg_pct:>6.1f} {bpm:>6.1f}")

    print()

    # Team statistics
    print("TEAM STATISTICS - Advanced Metrics")
    print("-"*90)

    for team in ['BOS', 'DAL']:
        cursor.execute("""
            SELECT
                SUM(pts) as pts,
                SUM(fgm) as fgm,
                SUM(fga) as fga,
                SUM(fg3m) as fg3m,
                SUM(fg3a) as fg3a,
                SUM(ftm) as ftm,
                SUM(fta) as fta,
                SUM(oreb) as oreb,
                SUM(dreb) as dreb,
                SUM(reb) as reb,
                SUM(ast) as ast,
                SUM(tov) as tov,
                AVG(minutes) as avg_min
            FROM player_stats
            WHERE team = ?
        """, (team,))

        team_stats = cursor.fetchone()

        # Calculate team advanced stats
        ts_pct = calc.true_shooting_pct(team_stats['pts'], team_stats['fga'], team_stats['fta'])
        efg_pct = calc.effective_fg_pct(team_stats['fgm'], team_stats['fg3m'], team_stats['fga'])
        three_par = calc.three_point_attempt_rate(team_stats['fg3a'], team_stats['fga'])
        poss = calc.possessions(team_stats['fga'], team_stats['oreb'], team_stats['tov'], team_stats['fta'])
        ortg = calc.offensive_rating(team_stats['pts'], poss)
        pace_val = calc.pace(poss, team_stats['avg_min'])
        ast_pct = (team_stats['ast'] / team_stats['fgm'] * 100) if team_stats['fgm'] > 0 else 0
        tov_rate = (team_stats['tov'] / (team_stats['fga'] + 0.44*team_stats['fta'] + team_stats['tov']) * 100)

        print(f"\n{team} Team Totals:")
        print(f"  Points: {team_stats['pts']}")
        print(f"  FG: {team_stats['fgm']}/{team_stats['fga']} ({team_stats['fgm']/team_stats['fga']*100:.1f}%)")
        print(f"  3PT: {team_stats['fg3m']}")
        print(f"  Rebounds: {team_stats['reb']} (OREB: {team_stats['oreb']}, DREB: {team_stats['dreb']})")
        print(f"  Assists: {team_stats['ast']}")
        print(f"  Turnovers: {team_stats['tov']}")

        print(f"\n  Advanced Metrics:")
        print(f"    True Shooting %: {ts_pct:.1f}%")
        print(f"    Effective FG %: {efg_pct:.1f}%")
        print(f"    3-Point Attempt Rate: {three_par:.1f}% (3PA / FGA)")
        print(f"    Possessions: {poss:.1f}")
        print(f"    Offensive Rating: {ortg:.1f} (pts per 100 poss)")
        print(f"    Pace: {pace_val:.1f} (poss per 48 min)")
        print(f"    Assist %: {ast_pct:.1f}% (assists on made FG)")
        print(f"    Turnover Rate: {tov_rate:.1f}%")

    print()
    print("="*90)
    print("✓ DEMO COMPLETE")
    print("="*90)
    print()

    print("ALL 16 BASKETBALL REFERENCE ADVANCED STATS - Key Metrics Explained:")
    print("="*90)
    print("• TS% (True Shooting): Shooting efficiency accounting for 2PT, 3PT, and FT")
    print("• eFG% (Effective FG): FG% adjusted for 3PT being worth more (adds 0.5 per 3PM)")
    print("• 3PAr (3-Point Attempt Rate): Percentage of FG attempts from 3-point range")
    print("• AST% (Assist %): Percentage of teammate FG assisted while player on floor")
    print("• STL% (Steal %): Steals per 100 opponent possessions")
    print("• BLK% (Block %): Blocks per 100 opponent 2PT attempts")
    print("• TOV% (Turnover %): Turnovers per 100 plays")
    print("• USG% (Usage %): Percentage of team plays used while on floor")
    print("• ORB%, DRB%, TRB%: Rebounding percentages (in full game data)")
    print("• ORtg, DRtg: Offensive/Defensive ratings (in full game data)")
    print("• BPM (Box Plus/Minus): Simplified estimate of points above average per 100 poss")
    print("• FTr (Free Throw Rate): FTA / FGA (in full game data)")
    print()
    print("NOTE: This demo shows simplified calculations. Full implementation tracks")
    print("      on-floor statistics for more accurate AST%, STL%, and BLK%.")
    print("      BPM shown is a simplified version - full BPM requires league-wide data.")
    print()

    conn.close()


def main():
    """Run advanced statistics demo"""
    db_path = create_sample_game()
    display_advanced_stats(db_path)


if __name__ == "__main__":
    main()
