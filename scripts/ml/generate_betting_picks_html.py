#!/usr/bin/env python3
"""
Generate HTML visualization of betting picks.

Usage:
    python scripts/ml/generate_betting_picks_html.py --picks /tmp/today_betting_picks.csv --output /tmp/betting_picks.html
"""

import argparse
import pandas as pd
import psycopg2
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from dotenv import load_dotenv
from pytz import timezone


def format_odds(odds: float) -> str:
    """Format odds in American format."""
    if pd.isna(odds):
        return "N/A"
    if odds > 0:
        return f"+{int(odds)}"
    else:
        return str(int(odds))


def format_percentage(value: float) -> str:
    """Format percentage with 1 decimal place."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def get_ev_color(ev: float) -> str:
    """Get color class based on expected value."""
    if pd.isna(ev):
        return "ev-neutral"
    if ev > 0.50:  # >50% EV
        return "ev-very-high"
    elif ev > 0.20:  # >20% EV
        return "ev-high"
    elif ev > 0.05:  # >5% EV
        return "ev-medium"
    elif ev > 0:  # Positive EV
        return "ev-low"
    else:
        return "ev-negative"


def fetch_player_props(conn, game_ids: list, game_date: date, date_range_days: int = 0) -> pd.DataFrame:
    """Fetch player props for given games."""
    player_prop_markets = [
        'player_points', 'player_assists', 'player_rebounds',
        'player_threes', 'player_points_rebounds', 'player_points_assists',
        'player_points_rebounds_assists', 'player_steals', 'player_blocks',
        'player_double_double', 'player_triple_double'
    ]

    market_str = "', '".join(player_prop_markets)

    if len(game_ids) > 0:
        query = f"""
        SELECT
            e.event_id,
            e.home_team,
            e.away_team,
            mt.market_key,
            mt.market_name,
            os.outcome_name as player_name,
            os.price as odds,
            os.point,
            b.bookmaker_title,
            b.bookmaker_key
        FROM odds.events e
        JOIN odds.odds_snapshots os ON e.event_id = os.event_id
        JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
        JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
        WHERE DATE(e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago') = %s
          AND os.is_latest = true
          AND mt.market_key IN ('{market_str}')
          AND e.event_id = ANY(%s)
        ORDER BY e.event_id, mt.market_key, os.outcome_name, b.bookmaker_title
        """
        params = (game_date, game_ids)
    else:
        # Get all player props for the date (and optionally date range)
        if date_range_days > 0:
            date_end = game_date + timedelta(days=date_range_days)
            query = f"""
            SELECT
                e.event_id,
                e.home_team,
                e.away_team,
                mt.market_key,
                mt.market_name,
                os.outcome_name as player_name,
                os.price as odds,
                os.point,
                b.bookmaker_title,
                b.bookmaker_key
            FROM odds.events e
            JOIN odds.odds_snapshots os ON e.event_id = os.event_id
            JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
            JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
            WHERE DATE(e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago') BETWEEN %s AND %s
              AND os.is_latest = true
              AND mt.market_key IN ('{market_str}')
            ORDER BY e.event_id, mt.market_key, os.outcome_name, b.bookmaker_title
            """
            params = (game_date, date_end)
        else:
            query = f"""
            SELECT
                e.event_id,
                e.home_team,
                e.away_team,
                mt.market_key,
                mt.market_name,
                os.outcome_name as player_name,
                os.price as odds,
                os.point,
                b.bookmaker_title,
                b.bookmaker_key
            FROM odds.events e
            JOIN odds.odds_snapshots os ON e.event_id = os.event_id
            JOIN odds.bookmakers b ON os.bookmaker_id = b.bookmaker_id
            JOIN odds.market_types mt ON os.market_type_id = mt.market_type_id
            WHERE DATE(e.commence_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago') = %s
              AND os.is_latest = true
              AND mt.market_key IN ('{market_str}')
            ORDER BY e.event_id, mt.market_key, os.outcome_name, b.bookmaker_title
            """
            params = (game_date,)

    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        print(f"Warning: Could not fetch player props: {e}")
        return pd.DataFrame()


def generate_html(picks_df: pd.DataFrame, output_path: Path, player_props_df: pd.DataFrame = None) -> str:
    """Generate HTML visualization of betting picks."""

    # Import fetch_game_state to check for in-progress games
    import sys
    from pathlib import Path as PathLib
    sys.path.insert(0, str(PathLib(__file__).parent.parent.parent))
    from scripts.ml.fetch_game_state import get_game_state
    from datetime import date

    # Sort by expected value
    picks_df = picks_df.sort_values('expected_value', ascending=False)

    # Check for in-progress games and get game state
    game_states = {}
    if 'game_id' in picks_df.columns:
        for game_id in picks_df['game_id'].unique():
            try:
                game_state = get_game_state(str(game_id))
                if game_state:
                    game_states[game_id] = game_state
            except Exception:
                pass  # Silently fail if game state not available

    # Calculate summary statistics
    total_bets = len(picks_df)
    positive_ev_bets = (picks_df['expected_value'] > 0).sum()
    strong_bets = (picks_df['expected_value'] > 0.05).sum()
    very_strong_bets = (picks_df['expected_value'] > 0.20).sum()
    games_covered = picks_df['game_id'].nunique()
    market_types = picks_df['market_type'].unique()

    # Group by market type
    by_market = {}
    for market_type in market_types:
        by_market[market_type] = picks_df[picks_df['market_type'] == market_type].copy()

    # Market type names
    market_names = {
        'h2h': 'Moneyline',
        'spreads': 'Point Spreads',
        'totals': 'Totals (Over/Under)'
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Betting Picks - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .date {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .section {{
            padding: 30px;
            border-top: 1px solid #e0e0e0;
        }}

        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .bets-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        .bets-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}

        .bets-table td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}

        .bets-table tr:hover {{
            background: #f5f5f5;
        }}

        .game-info {{
            font-weight: 600;
            color: #333;
        }}

        .pick {{
            font-weight: 600;
            color: #667eea;
        }}

        .ev-very-high {{
            background: #d4edda;
            color: #155724;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .ev-high {{
            background: #cce5ff;
            color: #004085;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .ev-medium {{
            background: #fff3cd;
            color: #856404;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .ev-low {{
            background: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .ev-negative {{
            background: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .odds {{
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }}

        .bookmaker {{
            color: #666;
            font-size: 0.9em;
        }}

        .top-bets {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .top-bet-card {{
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .top-bet-card .game {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}

        .top-bet-card .pick {{
            font-size: 1.1em;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .top-bet-card .metrics {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }}

        .top-bet-card .metric {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }}

        .top-bet-card .metric-label {{
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}

        .top-bet-card .metric-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }}

        @media (max-width: 768px) {{
            .bets-table {{
                font-size: 0.85em;
            }}

            .bets-table th,
            .bets-table td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏀 NBA Betting Picks</h1>
            <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
        </div>

        <div class="summary">
            <div class="stat-card">
                <div class="value">{total_bets}</div>
                <div class="label">Total Bets</div>
            </div>
            <div class="stat-card">
                <div class="value">{positive_ev_bets}</div>
                <div class="label">Positive EV</div>
            </div>
            <div class="stat-card">
                <div class="value">{strong_bets}</div>
                <div class="label">Strong (EV > 5%)</div>
            </div>
            <div class="stat-card">
                <div class="value">{very_strong_bets}</div>
                <div class="label">Very Strong (EV > 20%)</div>
            </div>
            <div class="stat-card">
                <div class="value">{games_covered}</div>
                <div class="label">Games Covered</div>
            </div>
        </div>
"""

    # Top 10 bets section
    top_10 = picks_df.head(10)
    html += """
        <div class="section">
            <h2 class="section-title">🎯 Top 10 Value Bets</h2>
            <div class="top-bets">
"""

    for idx, (_, bet) in enumerate(top_10.iterrows(), 1):
        point_str = f" ({bet['point']:+.1f})" if pd.notna(bet['point']) else ""
        bet_recommendation = bet['recommendation'] + point_str

        # Check if game is in-progress and has game state
        game_id = bet.get('game_id', '')
        game_state_info = ""
        if game_id in game_states:
            state = game_states[game_id]
            game_state_info = f" <span style='color: #e74c3c; font-weight: bold;'>(Q{state['quarter']} {state['current_score_home']}-{state['current_score_away']})</span>"

        html += f"""
                <div class="top-bet-card">
                    <div class="game">{bet['away_team']} @ {bet['home_team']}{game_state_info}</div>
                    <div class="pick">{bet_recommendation}</div>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-label">Win %</div>
                            <div class="metric-value">{format_percentage(bet['model_probability'])}</div>
                        </div>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>
"""

    # Market type sections
    for market_type in ['h2h', 'spreads', 'totals']:
        if market_type not in by_market or len(by_market[market_type]) == 0:
            continue

        market_df = by_market[market_type]
        market_name = market_names.get(market_type, market_type.upper())

        html += f"""
        <div class="section">
            <h2 class="section-title">{market_name} ({len(market_df)} bets)</h2>
            <table class="bets-table">
                <thead>
                    <tr>
                        <th>Game</th>
                        <th>Bet</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
"""

        for _, bet in market_df.iterrows():
            point_str = f" ({bet['point']:+.1f})" if pd.notna(bet['point']) else ""
            bet_recommendation = bet['recommendation'] + point_str

            # Check if game is in-progress and has game state
            game_id = bet.get('game_id', '')
            game_state_info = ""
            if game_id in game_states:
                state = game_states[game_id]
                game_state_info = f" <span style='color: #e74c3c; font-weight: bold;'>(Q{state['quarter']} {state['current_score_home']}-{state['current_score_away']})</span>"

            html += f"""
                    <tr>
                        <td class="game-info">{bet['away_team']} @ {bet['home_team']}{game_state_info}</td>
                        <td class="pick">{bet_recommendation}</td>
                        <td>{format_percentage(bet['model_probability'])}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
"""

    # Player Props section (always show, even if empty)
    html += """
        <div class="section">
            <h2 class="section-title">👤 Player Props</h2>
"""

    if player_props_df is not None and len(player_props_df) > 0:
        # Group player props by game
        games_with_props = player_props_df['event_id'].unique()

        html += """
        <div class="section">
            <h2 class="section-title">👤 Player Props</h2>
"""

        # Get unique games from picks (with event_id if available)
        if 'event_id' in picks_df.columns:
            picks_games = picks_df.groupby(['game_id', 'home_team', 'away_team', 'event_id']).first().reset_index()
        else:
            picks_games = picks_df.groupby(['game_id', 'home_team', 'away_team']).first().reset_index()
            picks_games['event_id'] = None

        for _, game_row in picks_games.iterrows():
            # Match by event_id if available, otherwise by teams
            if pd.notna(game_row.get('event_id')) and game_row.get('event_id'):
                game_props = player_props_df[player_props_df['event_id'] == game_row['event_id']]
            else:
                game_props = player_props_df[
                    (player_props_df['home_team'] == game_row['home_team']) &
                    (player_props_df['away_team'] == game_row['away_team'])
                ]

            if len(game_props) == 0:
                continue

            html += f"""
            <div style="margin-bottom: 40px;">
                <h3 style="font-size: 1.4em; color: #667eea; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #667eea;">
                    {game_row['away_team']} @ {game_row['home_team']}
                </h3>
"""

            # Group by market type
            props_by_market = {}
            for market_key in game_props['market_key'].unique():
                market_props_subset = game_props[game_props['market_key'] == market_key]
                market_name = market_props_subset.iloc[0]['market_name'] if len(market_props_subset) > 0 else market_key
                props_by_market[market_key] = (market_name, market_props_subset)

            # Display props by market
            for market_key, (market_name, market_props_subset) in sorted(props_by_market.items()):
                html += f"""
                <div style="margin-bottom: 25px;">
                    <h4 style="font-size: 1.1em; color: #555; margin-bottom: 10px;">{market_name}</h4>
                    <table class="bets-table" style="margin-bottom: 20px;">
                        <thead>
                            <tr>
                                <th>Player</th>
                                <th>Pick</th>
                                <th>Line</th>
                                <th>Odds</th>
                                <th>Bookmaker</th>
                            </tr>
                        </thead>
                        <tbody>
"""

                # Group by player to show all lines for each player
                for player_name in sorted(market_props_subset['player_name'].unique()):
                    player_lines = market_props_subset[market_props_subset['player_name'] == player_name]
                    for _, prop in player_lines.iterrows():
                        point_str = f"{prop['point']:.1f}" if pd.notna(prop['point']) else "N/A"
                        outcome_name = str(prop['player_name'])
                        # Extract Over/Under from outcome if present
                        if 'Over' in outcome_name or 'Under' in outcome_name:
                            # Split to get player name and Over/Under
                            parts = outcome_name.split()
                            if len(parts) >= 2:
                                player_display = ' '.join(parts[:-1])
                                over_under = parts[-1]
                                pick = f"{over_under} {point_str}"
                            else:
                                pick = outcome_name
                        else:
                            pick = f"Over/Under {point_str}"

                        html += f"""
                            <tr>
                                <td class="game-info">{player_name}</td>
                                <td class="pick">{pick}</td>
                                <td>{point_str}</td>
                                <td class="odds">{format_odds(prop['odds'])}</td>
                                <td class="bookmaker">{prop['bookmaker_title']}</td>
                            </tr>
"""

                html += """
                        </tbody>
                    </table>
                </div>
"""

            html += """
            </div>
"""

        # Show message for games without props
        games_without_props = []
        for _, game_row in picks_games.iterrows():
            # Check if this game has props
            if pd.notna(game_row.get('event_id')) and game_row.get('event_id'):
                has_props = len(player_props_df[player_props_df['event_id'] == game_row['event_id']]) > 0
            else:
                def normalize_name(name):
                    return name.lower().replace(' ', '').replace('.', '').replace('-', '')
                has_props = len(player_props_df[
                    (player_props_df['home_team'].apply(normalize_name) == normalize_name(game_row['home_team'])) &
                    (player_props_df['away_team'].apply(normalize_name) == normalize_name(game_row['away_team']))
                ]) > 0

            if not has_props:
                games_without_props.append(game_row)

        if len(games_without_props) > 0:
            html += """
            <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h4 style="color: #666; margin-bottom: 15px;">Games Without Player Props</h4>
                <ul style="list-style: none; padding: 0;">
"""
            for game_row in games_without_props:
                html += f"""
                    <li style="padding: 10px; margin-bottom: 5px; background: white; border-radius: 4px;">
                        {game_row['away_team']} @ {game_row['home_team']}
                    </li>
"""
            html += """
                </ul>
            </div>
"""

        html += """
        </div>
"""
    else:
        html += """
            <div style="padding: 40px; text-align: center; color: #666;">
                <p style="font-size: 1.2em; margin-bottom: 10px;">⚠️ No Player Props Available</p>
                <p>Player props are not currently available for today's games.</p>
                <p style="margin-top: 10px; font-size: 0.9em;">Player props may become available closer to game time or through different bookmakers.</p>
            </div>
"""

    html += """
        </div>
"""

    html += f"""
        <div class="section" style="text-align: center; color: #666; padding: 20px;">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 10px; font-size: 0.9em;">All odds and probabilities are estimates. Bet responsibly.</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML visualization of betting picks")
    parser.add_argument(
        "--picks",
        type=str,
        default="/tmp/today_betting_picks.csv",
        help="Path to betting picks CSV file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/betting_picks.html",
        help="Output HTML file path",
    )
    parser.add_argument(
        "--include-player-props",
        action="store_true",
        default=True,
        help="Include player props in HTML (default: True)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("GENERATING BETTING PICKS HTML")
    print("=" * 80)
    print()

    # Load picks
    print(f"Loading picks from: {args.picks}")
    try:
        picks_df = pd.read_csv(args.picks)
        print(f"✓ Loaded {len(picks_df)} betting picks")
    except Exception as e:
        print(f"❌ Error loading picks: {e}")
        return

    # Fetch player props if requested
    player_props_df = None
    if args.include_player_props:
        print(f"\nFetching player props from database...")
        try:
            # Load database credentials
            load_dotenv("/Users/ryanranft/nba-sim-credentials.env")
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT", 5432),
                sslmode="require",
            )

            # Get unique event IDs from picks CSV
            event_ids = []
            if 'event_id' in picks_df.columns:
                event_ids = picks_df['event_id'].dropna().unique().tolist()

            # Get all player props for today (and tomorrow, since games might be stored with UTC dates)
            today = date.today()
            tomorrow = today + timedelta(days=1)

            # Try fetching for today first
            player_props_df = fetch_player_props(conn, event_ids, today)

            # If no props found for today, try tomorrow (games might be stored with UTC dates)
            if len(player_props_df) == 0:
                player_props_df = fetch_player_props(conn, event_ids, tomorrow)

            # If still no props, try without event ID filter (get all props for today and tomorrow)
            if len(player_props_df) == 0:
                player_props_df = fetch_player_props(conn, [], today, date_range_days=1)

            # If still no props, try getting all recent player props (for reference, even if not for today)
            if len(player_props_df) == 0:
                # Get all player props from last 7 days
                recent_date = today - timedelta(days=7)
                player_props_df = fetch_player_props(conn, [], recent_date, date_range_days=7)

            if len(player_props_df) > 0:
                print(f"✓ Loaded {len(player_props_df)} player props")
                print(f"  Games with props: {player_props_df['event_id'].nunique()}")
            else:
                print("⚠ No player props found")

            conn.close()
        except Exception as e:
            print(f"⚠ Could not fetch player props: {e}")
            player_props_df = None

    # Generate HTML
    print(f"\nGenerating HTML...")
    html_content = generate_html(picks_df, Path(args.output), player_props_df)

    # Save HTML
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html_content)

    print(f"✓ Saved to: {output_path}")
    print(f"✓ Open in browser: file://{output_path.absolute()}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

