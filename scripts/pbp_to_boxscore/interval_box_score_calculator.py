#!/usr/bin/env python3
"""
Interval Box Score Calculator

Calculates box score statistics for custom time intervals:
- 6-minute intervals (8 per regulation game)
- 3-minute intervals (16 per regulation game)
- 1:30 intervals (32 per regulation game)
- 1-minute intervals (48 per regulation game)
- 1-second intervals (2,880 per regulation game)
- OT 2:30 halves (2 per OT period)
- OT 1-minute intervals (5 per OT period)
- Decisecond (0.1s) intervals for final minute

All intervals include complete advanced statistics.

Created: October 19, 2025
Updated: October 19, 2025 - Added second and decisecond intervals
"""

import sqlite3
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TimeInterval:
    """Represents a time interval in the game"""
    interval_number: int
    start_seconds: int
    end_seconds: int
    period: Optional[int] = None  # For OT intervals
    label: str = ""

    def __post_init__(self):
        if not self.label:
            start_min = self.start_seconds / 60.0
            end_min = self.end_seconds / 60.0
            if self.period and self.period > 4:
                ot_num = self.period - 4
                self.label = f"OT{ot_num} {start_min:.1f}-{end_min:.1f}min"
            else:
                self.label = f"{start_min:.1f}-{end_min:.1f}min"


class IntervalBoxScoreCalculator:
    """
    Calculate box score statistics for custom time intervals

    Supports regulation intervals (6min, 3min, 1:30, 1min) and
    special OT intervals (2:30 halves, 1min).
    """

    # NBA game constants
    REGULATION_MINUTES = 48
    REGULATION_SECONDS = 48 * 60  # 2880 seconds
    OT_MINUTES = 5
    OT_SECONDS = 5 * 60  # 300 seconds

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize calculator with database connection

        Args:
            conn: SQLite database connection with temporal box score snapshots
        """
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    # ========================================================================
    # REGULATION INTERVAL PARTITIONING
    # ========================================================================

    def get_6min_intervals(self) -> List[TimeInterval]:
        """
        Get 6-minute intervals for regulation (8 intervals)

        Returns:
            List of TimeInterval objects spanning 0-48 minutes
        """
        intervals = []
        for i in range(8):
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=i * 360,
                end_seconds=(i + 1) * 360
            ))
        return intervals

    def get_3min_intervals(self) -> List[TimeInterval]:
        """
        Get 3-minute intervals for regulation (16 intervals)

        Returns:
            List of TimeInterval objects spanning 0-48 minutes
        """
        intervals = []
        for i in range(16):
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=i * 180,
                end_seconds=(i + 1) * 180
            ))
        return intervals

    def get_90sec_intervals(self) -> List[TimeInterval]:
        """
        Get 1:30 (90-second) intervals for regulation (32 intervals)

        Returns:
            List of TimeInterval objects spanning 0-48 minutes
        """
        intervals = []
        for i in range(32):
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=i * 90,
                end_seconds=(i + 1) * 90
            ))
        return intervals

    def get_1min_intervals(self) -> List[TimeInterval]:
        """
        Get 1-minute intervals for regulation (48 intervals)

        Returns:
            List of TimeInterval objects spanning 0-48 minutes
        """
        intervals = []
        for i in range(48):
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=i * 60,
                end_seconds=(i + 1) * 60
            ))
        return intervals

    # ========================================================================
    # OVERTIME INTERVAL PARTITIONING
    # ========================================================================

    def get_ot_half_intervals(self, ot_period: int) -> List[TimeInterval]:
        """
        Get 2:30 (half) intervals for an OT period (2 intervals per OT)

        Args:
            ot_period: OT period number (5 for OT1, 6 for OT2, etc.)

        Returns:
            List of TimeInterval objects for this OT period
        """
        ot_number = ot_period - 4
        ot_start_seconds = self.REGULATION_SECONDS + (ot_number - 1) * self.OT_SECONDS

        intervals = []
        for i in range(2):
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=ot_start_seconds + i * 150,
                end_seconds=ot_start_seconds + (i + 1) * 150,
                period=ot_period,
                label=f"OT{ot_number} {i * 2.5:.1f}-{(i + 1) * 2.5:.1f}min"
            ))
        return intervals

    def get_ot_minute_intervals(self, ot_period: int) -> List[TimeInterval]:
        """
        Get 1-minute intervals for an OT period (5 intervals per OT)

        Args:
            ot_period: OT period number (5 for OT1, 6 for OT2, etc.)

        Returns:
            List of TimeInterval objects for this OT period
        """
        ot_number = ot_period - 4
        ot_start_seconds = self.REGULATION_SECONDS + (ot_number - 1) * self.OT_SECONDS

        intervals = []
        for i in range(5):
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=ot_start_seconds + i * 60,
                end_seconds=ot_start_seconds + (i + 1) * 60,
                period=ot_period,
                label=f"OT{ot_number} {i}-{i + 1}min"
            ))
        return intervals

    # ========================================================================
    # SECOND-LEVEL AND SUB-SECOND INTERVALS
    # ========================================================================

    def get_1sec_intervals_regulation(self) -> List[TimeInterval]:
        """
        Get 1-second intervals for entire regulation (2,880 intervals)

        Returns:
            List of 2,880 TimeInterval objects spanning 0-2880 seconds
        """
        intervals = []
        for i in range(self.REGULATION_SECONDS):
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=i,
                end_seconds=i + 1,
                label=f"{i}s-{i+1}s"
            ))
        return intervals

    def get_1sec_intervals_ot(self, ot_period: int) -> List[TimeInterval]:
        """
        Get 1-second intervals for an OT period (300 intervals per OT)

        Args:
            ot_period: OT period number (5 for OT1, 6 for OT2, etc.)

        Returns:
            List of 300 TimeInterval objects for this OT period
        """
        ot_number = ot_period - 4
        ot_start_seconds = self.REGULATION_SECONDS + (ot_number - 1) * self.OT_SECONDS

        intervals = []
        for i in range(self.OT_SECONDS):
            absolute_second = ot_start_seconds + i
            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=absolute_second,
                end_seconds=absolute_second + 1,
                period=ot_period,
                label=f"OT{ot_number} {i}s-{i+1}s"
            ))
        return intervals

    def get_1sec_intervals_range(self, start_second: int, end_second: int,
                                 period: Optional[int] = None) -> List[TimeInterval]:
        """
        Get 1-second intervals for a specific time range

        Args:
            start_second: Start time in seconds (absolute game time)
            end_second: End time in seconds (absolute game time)
            period: Optional period number for labeling

        Returns:
            List of TimeInterval objects for the specified range
        """
        intervals = []
        for i in range(start_second, end_second):
            intervals.append(TimeInterval(
                interval_number=i - start_second + 1,
                start_seconds=i,
                end_seconds=i + 1,
                period=period,
                label=f"{i}s-{i+1}s"
            ))
        return intervals

    def get_decisecond_intervals_final_minute(self, period: int) -> List[TimeInterval]:
        """
        Get 0.1-second (decisecond) intervals for final minute of a period

        Final minute of regulation (Q4): 2820-2880 seconds (60 seconds)
        Final minute of OT: Last 60 seconds of that OT period

        Returns 600 intervals with 0.1s precision.

        Args:
            period: Period number (4 for Q4, 5 for OT1, etc.)

        Returns:
            List of 600 TimeInterval objects with decisecond precision

        Note:
            This requires sub-second precision in source data.
            If only second-level data available, will have ~60 snapshots
            instead of 600.
        """
        if period <= 4:
            # Final minute of regulation Q4
            final_minute_start = self.REGULATION_SECONDS - 60  # 2820
            final_minute_end = self.REGULATION_SECONDS  # 2880
            label_prefix = "Q4"
        else:
            # Final minute of OT
            ot_number = period - 4
            ot_start = self.REGULATION_SECONDS + (ot_number - 1) * self.OT_SECONDS
            final_minute_start = ot_start + self.OT_SECONDS - 60  # Last 60 seconds
            final_minute_end = ot_start + self.OT_SECONDS
            label_prefix = f"OT{ot_number}"

        intervals = []
        # Create 600 intervals (60 seconds × 10 deciseconds per second)
        for i in range(600):
            # Time in deciseconds (0.1s increments)
            start_deciseconds = final_minute_start + (i * 0.1)
            end_deciseconds = final_minute_start + ((i + 1) * 0.1)

            # Calculate seconds remaining (countdown from 60.0 to 0.0)
            seconds_remaining = 60.0 - (i * 0.1)

            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=int(start_deciseconds),  # For integer second queries
                end_seconds=int(end_deciseconds),
                period=period,
                label=f"{label_prefix} {seconds_remaining:.1f}s"
            ))

        return intervals

    def get_decisecond_intervals_range(self, start_second: float, end_second: float,
                                      period: Optional[int] = None) -> List[TimeInterval]:
        """
        Get 0.1-second intervals for any time range

        Args:
            start_second: Start time in seconds (can be decimal)
            end_second: End time in seconds (can be decimal)
            period: Optional period number for labeling

        Returns:
            List of TimeInterval objects with 0.1s precision

        Example:
            # Last 5 seconds with decisecond precision
            intervals = calc.get_decisecond_intervals_range(2875.0, 2880.0, period=4)
            # Returns 50 intervals (5 seconds × 10 deciseconds)
        """
        intervals = []

        # Calculate number of decisecond intervals
        duration_deciseconds = int((end_second - start_second) * 10)

        for i in range(duration_deciseconds):
            start_decisec = start_second + (i * 0.1)
            end_decisec = start_second + ((i + 1) * 0.1)

            intervals.append(TimeInterval(
                interval_number=i + 1,
                start_seconds=int(start_decisec),
                end_seconds=int(end_decisec),
                period=period,
                label=f"{start_decisec:.1f}s-{end_decisec:.1f}s"
            ))

        return intervals

    # ========================================================================
    # SNAPSHOT QUERIES
    # ========================================================================

    def get_snapshot_at_time(self, game_id: str, player_id: str,
                            elapsed_seconds: int) -> Optional[sqlite3.Row]:
        """
        Get player snapshot at or just before a specific elapsed time

        Args:
            game_id: Game identifier
            player_id: Player identifier
            elapsed_seconds: Elapsed seconds since game start

        Returns:
            Snapshot row or None if no snapshot found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM player_box_score_snapshots
            WHERE game_id = ?
              AND player_id = ?
              AND time_elapsed_seconds <= ?
            ORDER BY time_elapsed_seconds DESC, event_number DESC
            LIMIT 1
        """, (game_id, player_id, elapsed_seconds))

        return cursor.fetchone()

    def get_team_snapshot_at_time(self, game_id: str, team_id: str,
                                  elapsed_seconds: int) -> Optional[sqlite3.Row]:
        """
        Get team snapshot at or just before a specific elapsed time

        Args:
            game_id: Game identifier
            team_id: Team identifier
            elapsed_seconds: Elapsed seconds since game start

        Returns:
            Snapshot row or None if no snapshot found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM team_box_score_snapshots
            WHERE game_id = ?
              AND team_id = ?
              AND time_elapsed_seconds <= ?
            ORDER BY time_elapsed_seconds DESC, event_number DESC
            LIMIT 1
        """, (game_id, team_id, elapsed_seconds))

        return cursor.fetchone()

    def get_opponent_team_id(self, game_id: str, team_id: str) -> Optional[str]:
        """
        Get the opponent team ID for a game

        Args:
            game_id: Game identifier
            team_id: Team identifier

        Returns:
            Opponent team ID or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT team_id
            FROM team_box_score_snapshots
            WHERE game_id = ?
              AND team_id != ?
            LIMIT 1
        """, (game_id, team_id))

        result = cursor.fetchone()
        return result['team_id'] if result else None

    # ========================================================================
    # INTERVAL STAT CALCULATION
    # ========================================================================

    def calculate_interval_stats(self, game_id: str, player_id: str,
                                interval: TimeInterval) -> Dict:
        """
        Calculate stats for a specific interval (delta between start and end)

        Args:
            game_id: Game identifier
            player_id: Player identifier
            interval: TimeInterval object

        Returns:
            Dictionary with interval-only stats and ALL 16 advanced statistics
        """
        # Get snapshots at interval boundaries
        start_snapshot = self.get_snapshot_at_time(game_id, player_id, interval.start_seconds)
        end_snapshot = self.get_snapshot_at_time(game_id, player_id, interval.end_seconds)

        # If no data for this interval, return zeros
        if not end_snapshot:
            return self._empty_interval_stats(interval)

        # If no start snapshot (interval starts at game start), use zeros
        if not start_snapshot:
            start_vals = {key: 0 for key in end_snapshot.keys()}
        else:
            start_vals = dict(start_snapshot)

        end_vals = dict(end_snapshot)

        # Calculate delta (interval-only stats)
        interval_stats = {
            'interval': interval.label,
            'interval_number': interval.interval_number,
            'start_seconds': interval.start_seconds,
            'end_seconds': interval.end_seconds,
            'period': interval.period,

            # Basic stats (delta)
            'points': end_vals['points'] - start_vals.get('points', 0),
            'fgm': end_vals['fgm'] - start_vals.get('fgm', 0),
            'fga': end_vals['fga'] - start_vals.get('fga', 0),
            'fg3m': end_vals['fg3m'] - start_vals.get('fg3m', 0),
            'fg3a': end_vals['fg3a'] - start_vals.get('fg3a', 0),
            'ftm': end_vals['ftm'] - start_vals.get('ftm', 0),
            'fta': end_vals['fta'] - start_vals.get('fta', 0),
            'oreb': end_vals['oreb'] - start_vals.get('oreb', 0),
            'dreb': end_vals['dreb'] - start_vals.get('dreb', 0),
            'reb': end_vals['reb'] - start_vals.get('reb', 0),
            'ast': end_vals['ast'] - start_vals.get('ast', 0),
            'stl': end_vals['stl'] - start_vals.get('stl', 0),
            'blk': end_vals['blk'] - start_vals.get('blk', 0),
            'tov': end_vals['tov'] - start_vals.get('tov', 0),
            'pf': end_vals['pf'] - start_vals.get('pf', 0),
            'minutes': end_vals['minutes'] - start_vals.get('minutes', 0),
        }

        # Get team and opponent interval stats for advanced calculations
        team_id = end_vals.get('team_id')
        team_interval_stats = None
        opponent_interval_stats = None

        if team_id:
            # Calculate team interval stats
            team_interval_stats = self.calculate_team_interval_stats(game_id, team_id, interval)

            # Get opponent team and calculate their interval stats
            opponent_team_id = self.get_opponent_team_id(game_id, team_id)
            if opponent_team_id:
                opponent_interval_stats = self.calculate_team_interval_stats(
                    game_id, opponent_team_id, interval
                )

        # Calculate ALL advanced stats (now with team/opponent context for complete coverage)
        interval_stats.update(
            self._calculate_advanced_stats(
                interval_stats,
                team_stats=team_interval_stats,
                opponent_stats=opponent_interval_stats
            )
        )

        return interval_stats

    def calculate_team_interval_stats(self, game_id: str, team_id: str,
                                     interval: TimeInterval) -> Dict:
        """
        Calculate team stats for a specific interval

        Args:
            game_id: Game identifier
            team_id: Team identifier
            interval: TimeInterval object

        Returns:
            Dictionary with interval-only team stats
        """
        start_snapshot = self.get_team_snapshot_at_time(game_id, team_id, interval.start_seconds)
        end_snapshot = self.get_team_snapshot_at_time(game_id, team_id, interval.end_seconds)

        if not end_snapshot:
            return self._empty_interval_stats(interval)

        if not start_snapshot:
            start_vals = {key: 0 for key in end_snapshot.keys()}
        else:
            start_vals = dict(start_snapshot)

        end_vals = dict(end_snapshot)

        # Calculate delta
        interval_stats = {
            'interval': interval.label,
            'interval_number': interval.interval_number,
            'team_id': team_id,

            'points': end_vals['points'] - start_vals.get('points', 0),
            'fgm': end_vals['fgm'] - start_vals.get('fgm', 0),
            'fga': end_vals['fga'] - start_vals.get('fga', 0),
            'fg3m': end_vals['fg3m'] - start_vals.get('fg3m', 0),
            'fg3a': end_vals['fg3a'] - start_vals.get('fg3a', 0),
            'ftm': end_vals['ftm'] - start_vals.get('ftm', 0),
            'fta': end_vals['fta'] - start_vals.get('fta', 0),
            'oreb': end_vals['oreb'] - start_vals.get('oreb', 0),
            'dreb': end_vals['dreb'] - start_vals.get('dreb', 0),
            'reb': end_vals['reb'] - start_vals.get('reb', 0),
            'ast': end_vals['ast'] - start_vals.get('ast', 0),
            'stl': end_vals['stl'] - start_vals.get('stl', 0),
            'blk': end_vals['blk'] - start_vals.get('blk', 0),
            'tov': end_vals['tov'] - start_vals.get('tov', 0),
            'pf': end_vals['pf'] - start_vals.get('pf', 0),
        }

        # Advanced stats
        interval_stats.update(self._calculate_team_advanced_stats(interval_stats))

        return interval_stats

    # ========================================================================
    # ADVANCED STATISTICS
    # ========================================================================

    def _calculate_advanced_stats(self, stats: Dict, team_stats: Optional[Dict] = None,
                                  opponent_stats: Optional[Dict] = None) -> Dict:
        """
        Calculate ALL 16 Basketball Reference advanced statistics for an interval

        Args:
            stats: Player interval statistics
            team_stats: Team interval statistics (optional, for context-dependent stats)
            opponent_stats: Opponent interval statistics (optional, for defensive stats)

        Returns:
            Dictionary with all advanced statistics
        """
        advanced = {}

        # ====================================================================
        # SHOOTING EFFICIENCY (5 stats)
        # ====================================================================

        # 1. FG%
        if stats['fga'] > 0:
            advanced['fg_pct'] = stats['fgm'] / stats['fga'] * 100
            advanced['efg_pct'] = (stats['fgm'] + 0.5 * stats['fg3m']) / stats['fga'] * 100
            advanced['3par'] = stats['fg3a'] / stats['fga'] * 100
            advanced['ft_rate'] = stats['fta'] / stats['fga']  # FTr (NEW)
        else:
            advanced['fg_pct'] = 0.0
            advanced['efg_pct'] = 0.0
            advanced['3par'] = 0.0
            advanced['ft_rate'] = 0.0

        # 2. 3P%
        if stats['fg3a'] > 0:
            advanced['fg3_pct'] = stats['fg3m'] / stats['fg3a'] * 100
        else:
            advanced['fg3_pct'] = 0.0

        # 3. FT%
        if stats['fta'] > 0:
            advanced['ft_pct'] = stats['ftm'] / stats['fta'] * 100
        else:
            advanced['ft_pct'] = 0.0

        # 4. TS% (True Shooting)
        ts_attempts = stats['fga'] + 0.44 * stats['fta']
        if ts_attempts > 0:
            advanced['ts_pct'] = stats['points'] / (2 * ts_attempts) * 100
        else:
            advanced['ts_pct'] = 0.0

        # ====================================================================
        # REBOUNDING PERCENTAGES (3 stats) - Require team/opponent data
        # ====================================================================

        if team_stats and opponent_stats:
            team_oreb = team_stats.get('oreb', 0)
            team_dreb = team_stats.get('dreb', 0)
            opp_oreb = opponent_stats.get('oreb', 0)
            opp_dreb = opponent_stats.get('dreb', 0)

            # 5. ORB% (Offensive Rebound Percentage)
            orb_opportunities = team_oreb + opp_dreb
            if orb_opportunities > 0:
                advanced['orb_pct'] = stats['oreb'] / orb_opportunities * 100
            else:
                advanced['orb_pct'] = 0.0

            # 6. DRB% (Defensive Rebound Percentage)
            drb_opportunities = team_dreb + opp_oreb
            if drb_opportunities > 0:
                advanced['drb_pct'] = stats['dreb'] / drb_opportunities * 100
            else:
                advanced['drb_pct'] = 0.0

            # 7. TRB% (Total Rebound Percentage)
            total_rebs = team_oreb + team_dreb + opp_oreb + opp_dreb
            if total_rebs > 0:
                advanced['trb_pct'] = stats['reb'] / total_rebs * 100
            else:
                advanced['trb_pct'] = 0.0
        else:
            advanced['orb_pct'] = 0.0
            advanced['drb_pct'] = 0.0
            advanced['trb_pct'] = 0.0

        # ====================================================================
        # PLAYMAKING & DEFENSE (4 stats) - Require team/opponent data
        # ====================================================================

        # 8. AST% (Assist Percentage)
        if team_stats and stats.get('minutes', 0) > 0:
            team_minutes = team_stats.get('minutes', 0)
            player_minutes = stats.get('minutes', 0)
            team_fgm = team_stats.get('fgm', 0)
            player_fgm = stats['fgm']

            if team_minutes > 0:
                teammate_fgm = team_fgm - player_fgm
                if teammate_fgm > 0:
                    advanced['ast_pct'] = (stats['ast'] * team_minutes) / (player_minutes * teammate_fgm) * 100
                else:
                    advanced['ast_pct'] = 0.0
            else:
                advanced['ast_pct'] = 0.0
        else:
            advanced['ast_pct'] = 0.0

        # 9. STL% (Steal Percentage)
        if opponent_stats and team_stats and stats.get('minutes', 0) > 0:
            team_minutes = team_stats.get('minutes', 0)
            player_minutes = stats.get('minutes', 0)
            opp_poss = self._calculate_possessions_from_stats(opponent_stats)

            if team_minutes > 0 and opp_poss > 0:
                advanced['stl_pct'] = (stats['stl'] * team_minutes) / (player_minutes * opp_poss) * 100
            else:
                advanced['stl_pct'] = 0.0
        else:
            advanced['stl_pct'] = 0.0

        # 10. BLK% (Block Percentage)
        if opponent_stats and team_stats and stats.get('minutes', 0) > 0:
            team_minutes = team_stats.get('minutes', 0)
            player_minutes = stats.get('minutes', 0)
            opp_2pt_fga = opponent_stats.get('fga', 0) - opponent_stats.get('fg3a', 0)

            if team_minutes > 0 and opp_2pt_fga > 0:
                advanced['blk_pct'] = (stats['blk'] * team_minutes) / (player_minutes * opp_2pt_fga) * 100
            else:
                advanced['blk_pct'] = 0.0
        else:
            advanced['blk_pct'] = 0.0

        # 11. TOV% (Turnover Percentage)
        tov_possessions = stats['fga'] + 0.44 * stats['fta'] + stats['tov']
        if tov_possessions > 0:
            advanced['tov_pct'] = stats['tov'] / tov_possessions * 100
        else:
            advanced['tov_pct'] = 0.0

        # ====================================================================
        # USAGE & EFFICIENCY (4 stats)
        # ====================================================================

        # 12. USG% (Usage Percentage)
        if team_stats and stats.get('minutes', 0) > 0:
            team_minutes = team_stats.get('minutes', 0)
            player_minutes = stats.get('minutes', 0)
            team_fga = team_stats.get('fga', 0)
            team_fta = team_stats.get('fta', 0)
            team_tov = team_stats.get('tov', 0)

            if team_minutes > 0:
                team_poss_events = team_fga + 0.44 * team_fta + team_tov
                player_poss_events = stats['fga'] + 0.44 * stats['fta'] + stats['tov']

                if team_poss_events > 0:
                    advanced['usg_pct'] = (player_poss_events * team_minutes) / (team_poss_events * player_minutes) * 100
                else:
                    advanced['usg_pct'] = 0.0
            else:
                advanced['usg_pct'] = 0.0
        else:
            advanced['usg_pct'] = 0.0

        # 13. ORtg (Offensive Rating)
        player_poss = self._calculate_possessions_from_stats(stats)
        if player_poss > 0:
            advanced['ortg'] = (stats['points'] / player_poss) * 100
        else:
            advanced['ortg'] = 0.0

        # 14. DRtg (Defensive Rating) - Estimate
        # Note: True DRtg requires on/off court tracking. This is simplified.
        if opponent_stats and stats.get('minutes', 0) > 0:
            opp_points = opponent_stats.get('points', 0)
            opp_poss = self._calculate_possessions_from_stats(opponent_stats)
            if opp_poss > 0:
                advanced['drtg'] = (opp_points / opp_poss) * 100
            else:
                advanced['drtg'] = 0.0
        else:
            advanced['drtg'] = 0.0

        # 15. BPM (Box Plus/Minus - Simplified)
        if player_poss > 0:
            pts_per_100 = (stats['points'] / player_poss) * 100
            reb_per_100 = (stats['reb'] / player_poss) * 100
            ast_per_100 = (stats['ast'] / player_poss) * 100
            stocks_per_100 = ((stats['stl'] + stats['blk']) / player_poss) * 100
            tov_per_100 = (stats['tov'] / player_poss) * 100

            advanced['bpm'] = (
                (pts_per_100 - 15) * 0.15 +
                (reb_per_100 - 10) * 0.35 +
                (ast_per_100 - 5) * 0.70 +
                (stocks_per_100 - 3) * 0.70 -
                (tov_per_100 - 3) * 0.30
            )
        else:
            advanced['bpm'] = 0.0

        # ====================================================================
        # ADDITIONAL METRICS
        # ====================================================================

        # Assist to turnover ratio
        if stats['tov'] > 0:
            advanced['ast_to_tov'] = stats['ast'] / stats['tov']
        else:
            advanced['ast_to_tov'] = stats['ast'] if stats['ast'] > 0 else 0.0

        return advanced

    def _calculate_possessions_from_stats(self, stats: Dict) -> float:
        """Helper to calculate possessions from stat dict"""
        return stats.get('fga', 0) - stats.get('oreb', 0) + stats.get('tov', 0) + 0.44 * stats.get('fta', 0)

    def _calculate_team_advanced_stats(self, stats: Dict) -> Dict:
        """Calculate advanced statistics for team interval"""
        advanced = self._calculate_advanced_stats(stats)

        # Possessions
        poss = stats['fga'] - stats['oreb'] + stats['tov'] + 0.44 * stats['fta']
        advanced['possessions'] = poss

        # Offensive rating (points per 100 possessions)
        if poss > 0:
            advanced['ortg'] = stats['points'] / poss * 100
        else:
            advanced['ortg'] = 0.0

        # Pace (possessions per 48 minutes)
        # Note: For intervals, this extrapolates to full game pace
        interval_duration_min = (stats.get('end_seconds', 0) - stats.get('start_seconds', 0)) / 60.0
        if interval_duration_min > 0 and poss > 0:
            advanced['pace'] = poss / interval_duration_min * 48.0
        else:
            advanced['pace'] = 0.0

        return advanced

    def _empty_interval_stats(self, interval: TimeInterval) -> Dict:
        """Return empty stats dictionary for interval with no data"""
        return {
            'interval': interval.label,
            'interval_number': interval.interval_number,
            'start_seconds': interval.start_seconds,
            'end_seconds': interval.end_seconds,
            'period': interval.period,
            'points': 0, 'fgm': 0, 'fga': 0, 'fg_pct': 0.0,
            'fg3m': 0, 'fg3a': 0, 'fg3_pct': 0.0,
            'ftm': 0, 'fta': 0, 'ft_pct': 0.0,
            'reb': 0, 'oreb': 0, 'dreb': 0,
            'ast': 0, 'stl': 0, 'blk': 0, 'tov': 0, 'pf': 0,
            'ts_pct': 0.0, 'efg_pct': 0.0, '3par': 0.0,
            'tov_pct': 0.0, 'ast_to_tov': 0.0,
            'minutes': 0.0
        }

    # ========================================================================
    # BATCH CALCULATIONS
    # ========================================================================

    def calculate_all_regulation_intervals(self, game_id: str, player_id: str,
                                          interval_type: str = '6min') -> List[Dict]:
        """
        Calculate stats for all regulation intervals of a specific type

        Args:
            game_id: Game identifier
            player_id: Player identifier
            interval_type: '6min', '3min', '90sec', '1min', or '1sec'

        Returns:
            List of interval stat dictionaries

        Note:
            For '1sec', returns 2,880 intervals. This may take longer to compute.
            Consider using calculate_seconds_range() for specific time ranges.
        """
        # Get intervals based on type
        if interval_type == '6min':
            intervals = self.get_6min_intervals()
        elif interval_type == '3min':
            intervals = self.get_3min_intervals()
        elif interval_type == '90sec':
            intervals = self.get_90sec_intervals()
        elif interval_type == '1min':
            intervals = self.get_1min_intervals()
        elif interval_type == '1sec':
            intervals = self.get_1sec_intervals_regulation()
        else:
            raise ValueError(f"Unknown interval type: {interval_type}")

        # Calculate stats for each interval
        results = []
        for interval in intervals:
            stats = self.calculate_interval_stats(game_id, player_id, interval)
            results.append(stats)

        return results

    def calculate_all_ot_intervals(self, game_id: str, player_id: str,
                                  ot_period: int, interval_type: str = 'half') -> List[Dict]:
        """
        Calculate stats for all OT intervals of a specific type

        Args:
            game_id: Game identifier
            player_id: Player identifier
            ot_period: OT period number (5 for OT1, 6 for OT2, etc.)
            interval_type: 'half' (2:30), 'minute' (1min), '1sec', or 'decisecond'

        Returns:
            List of interval stat dictionaries

        Note:
            - '1sec' returns 300 intervals per OT period
            - 'decisecond' returns 600 intervals for final minute only
        """
        if interval_type == 'half':
            intervals = self.get_ot_half_intervals(ot_period)
        elif interval_type == 'minute':
            intervals = self.get_ot_minute_intervals(ot_period)
        elif interval_type == '1sec':
            intervals = self.get_1sec_intervals_ot(ot_period)
        elif interval_type == 'decisecond':
            intervals = self.get_decisecond_intervals_final_minute(ot_period)
        else:
            raise ValueError(f"Unknown OT interval type: {interval_type}")

        results = []
        for interval in intervals:
            stats = self.calculate_interval_stats(game_id, player_id, interval)
            results.append(stats)

        return results

    def calculate_seconds_range(self, game_id: str, player_id: str,
                               start_second: int, end_second: int,
                               period: Optional[int] = None) -> List[Dict]:
        """
        Calculate stats for a range of one-second intervals

        Args:
            game_id: Game identifier
            player_id: Player identifier
            start_second: Start time in seconds
            end_second: End time in seconds
            period: Optional period number for labeling

        Returns:
            List of interval stat dictionaries for each second

        Example:
            # Get final 10 seconds of regulation
            final_10 = calc.calculate_seconds_range('game123', 'player456', 2870, 2880, period=4)
        """
        intervals = self.get_1sec_intervals_range(start_second, end_second, period)

        results = []
        for interval in intervals:
            stats = self.calculate_interval_stats(game_id, player_id, interval)
            results.append(stats)

        return results

    def calculate_deciseconds_range(self, game_id: str, player_id: str,
                                   start_second: float, end_second: float,
                                   period: Optional[int] = None) -> List[Dict]:
        """
        Calculate stats for a range of decisecond (0.1s) intervals

        Args:
            game_id: Game identifier
            player_id: Player identifier
            start_second: Start time in seconds (can be decimal)
            end_second: End time in seconds (can be decimal)
            period: Optional period number for labeling

        Returns:
            List of interval stat dictionaries for each 0.1s

        Example:
            # Get final 5 seconds with 0.1s precision
            final_5 = calc.calculate_deciseconds_range('game123', 'player456', 2875.0, 2880.0, period=4)
        """
        intervals = self.get_decisecond_intervals_range(start_second, end_second, period)

        results = []
        for interval in intervals:
            stats = self.calculate_interval_stats(game_id, player_id, interval)
            results.append(stats)

        return results

    # ========================================================================
    # PLAYER BIOGRAPHICAL DATA INTEGRATION
    # ========================================================================

    def get_player_biographical(self, player_id: str) -> Optional[Dict]:
        """
        Fetch all biographical data for a player

        Args:
            player_id: Player identifier

        Returns:
            Dictionary with all biographical fields, or None if not found

        Fields returned:
            - birth_date, birth_date_precision, birth_city, birth_state, birth_country
            - height_inches, weight_pounds, wingspan_inches
            - nba_debut_date, nba_retirement_date
            - draft_year, draft_round, draft_pick, draft_team_id
            - college, high_school
            - nationality, position, jersey_number
            - data_source
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                birth_date,
                birth_date_precision,
                birth_city,
                birth_state,
                birth_country,
                height_inches,
                weight_pounds,
                wingspan_inches,
                nba_debut_date,
                nba_retirement_date,
                draft_year,
                draft_round,
                draft_pick,
                draft_team_id,
                college,
                high_school,
                nationality,
                position,
                jersey_number,
                data_source
            FROM player_biographical
            WHERE player_id = ?
        """, (player_id,))

        result = cursor.fetchone()
        if not result:
            return None

        return dict(result)

    def calculate_age_at_timestamp(self, birth_date: str, timestamp: str) -> Dict:
        """
        Calculate player age at specific timestamp with all 7 formats

        Ages are calculated assuming birth time is midnight UTC (00:00:00).
        This creates a ±24 hour uncertainty window for exact age.

        Args:
            birth_date: Birth date as string (YYYY-MM-DD)
            timestamp: Event timestamp (game time)

        Returns:
            Dictionary with all 7 age formats:
                - age_years_decimal: DECIMAL(10,4) high precision (e.g., 27.6412)
                - age_days: Integer days since birth
                - age_seconds: Total seconds since birth (for time-series models)
                - age_uncertainty_hours: Always 24 (birth time unknown)
                - age_min_decimal: Minimum age (born at 23:59:59)
                - age_max_decimal: Maximum age (born at 00:00:00)
                - age_string: Human readable (e.g., "27y 234d ±24h")

        ML Use Cases:
            - age_years_decimal: Regression models, age-performance curves
            - age_days: Tree-based models, discrete binning
            - age_seconds: LSTM/RNN time-series models
            - age_min/max: Uncertainty-aware models, confidence intervals
            - age_uncertainty_hours: Model confidence scoring
        """
        if not birth_date or not timestamp:
            return {
                'age_years_decimal': None,
                'age_days': None,
                'age_seconds': None,
                'age_uncertainty_hours': None,
                'age_min_decimal': None,
                'age_max_decimal': None,
                'age_string': None
            }

        cursor = self.conn.cursor()

        # Use SQLite's julianday for precise date calculations
        # julianday returns the number of days since noon in Greenwich on November 24, 4714 B.C.
        cursor.execute("""
            SELECT
                -- Format 1: High-precision decimal years
                CAST(
                    (julianday(?) - julianday(?)) / 365.25
                    AS REAL
                ) AS age_years_decimal,

                -- Format 2: Age in days
                CAST(
                    julianday(?) - julianday(?)
                    AS INTEGER
                ) AS age_days,

                -- Format 3: Age in seconds
                CAST(
                    (julianday(?) - julianday(?)) * 86400
                    AS INTEGER
                ) AS age_seconds
        """, (timestamp, birth_date, timestamp, birth_date, timestamp, birth_date))

        result = cursor.fetchone()

        age_years_decimal = result['age_years_decimal']
        age_days = result['age_days']
        age_seconds = result['age_seconds']

        # Calculate min/max age (±24 hours = ±1/365.25 years)
        one_day_in_years = 1.0 / 365.25
        age_min_decimal = age_years_decimal - one_day_in_years if age_years_decimal else None
        age_max_decimal = age_years_decimal + one_day_in_years if age_years_decimal else None

        # Create human-readable string
        if age_years_decimal is not None:
            years = int(age_years_decimal)
            remaining_days = age_days - (years * 365)  # Approximate
            age_string = f"{years}y {remaining_days}d ±24h"
        else:
            age_string = None

        return {
            'age_years_decimal': round(age_years_decimal, 4) if age_years_decimal else None,
            'age_days': age_days,
            'age_seconds': age_seconds,
            'age_uncertainty_hours': 24,  # Always 24 hours (birth time unknown)
            'age_min_decimal': round(age_min_decimal, 4) if age_min_decimal else None,
            'age_max_decimal': round(age_max_decimal, 4) if age_max_decimal else None,
            'age_string': age_string
        }

    def calculate_nba_experience(self, nba_debut_date: str, timestamp: str) -> Dict:
        """
        Calculate NBA experience at specific timestamp

        Args:
            nba_debut_date: NBA debut date as string (YYYY-MM-DD)
            timestamp: Event timestamp

        Returns:
            Dictionary with experience metrics:
                - nba_experience_years: DECIMAL(10,4) years since debut
                - nba_experience_days: Integer days since debut
                - is_rookie: Boolean (< 1 year experience)
        """
        if not nba_debut_date or not timestamp:
            return {
                'nba_experience_years': None,
                'nba_experience_days': None,
                'is_rookie': None
            }

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                CAST(
                    (julianday(?) - julianday(?)) / 365.25
                    AS REAL
                ) AS nba_experience_years,

                CAST(
                    julianday(?) - julianday(?)
                    AS INTEGER
                ) AS nba_experience_days
        """, (timestamp, nba_debut_date, timestamp, nba_debut_date))

        result = cursor.fetchone()
        exp_years = result['nba_experience_years']
        exp_days = result['nba_experience_days']

        return {
            'nba_experience_years': round(exp_years, 4) if exp_years else None,
            'nba_experience_days': exp_days,
            'is_rookie': (exp_years < 1.0) if exp_years is not None else None
        }

    def add_biographical_to_interval(self, interval_stats: Dict, player_id: str,
                                     timestamp: str = None) -> Dict:
        """
        Add biographical data and age calculations to interval statistics

        Args:
            interval_stats: Existing interval statistics dictionary
            player_id: Player identifier
            timestamp: Optional timestamp for age calculation (uses interval end time if not provided)

        Returns:
            Enhanced dictionary with biographical data and all 7 age formats

        Example:
            interval_stats = calc.calculate_interval_stats(game_id, player_id, interval)
            interval_stats = calc.add_biographical_to_interval(interval_stats, player_id, timestamp)
            # Now interval_stats includes height, weight, age_years_decimal, etc.
        """
        # Get biographical data
        bio_data = self.get_player_biographical(player_id)

        if not bio_data:
            # Return original stats if no biographical data available
            interval_stats['biographical_data_available'] = False
            return interval_stats

        # Add all biographical fields
        interval_stats.update(bio_data)
        interval_stats['biographical_data_available'] = True

        # Calculate age at timestamp (or interval end if not provided)
        if not timestamp and 'timestamp' in interval_stats:
            timestamp = interval_stats['timestamp']

        if bio_data.get('birth_date') and timestamp:
            age_data = self.calculate_age_at_timestamp(bio_data['birth_date'], timestamp)
            interval_stats.update(age_data)

        # Calculate NBA experience
        if bio_data.get('nba_debut_date') and timestamp:
            experience_data = self.calculate_nba_experience(bio_data['nba_debut_date'], timestamp)
            interval_stats.update(experience_data)

        # Calculate derived physical metrics
        if bio_data.get('height_inches') and bio_data.get('weight_pounds'):
            # BMI
            height_m = bio_data['height_inches'] * 0.0254
            weight_kg = bio_data['weight_pounds'] * 0.453592
            interval_stats['bmi'] = round(weight_kg / (height_m ** 2), 2)

            # Height/weight in metric
            interval_stats['height_cm'] = round(bio_data['height_inches'] * 2.54, 1)
            interval_stats['weight_kg'] = round(weight_kg, 1)

        # Wingspan/height ratio
        if bio_data.get('wingspan_inches') and bio_data.get('height_inches'):
            interval_stats['wingspan_height_ratio'] = round(
                bio_data['wingspan_inches'] / bio_data['height_inches'], 3
            )

        return interval_stats
