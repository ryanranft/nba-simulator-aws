#!/usr/bin/env python3
"""
Generate HTML Dashboard for Predictions

Purpose: Create an HTML dashboard displaying predictions with improved projections

Usage:
    python scripts/ml/generate_predictions_html_dashboard.py
    python scripts/ml/generate_predictions_html_dashboard.py --predictions /tmp/nba_predictions/predictions_latest.csv
"""

import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
import os

def generate_html_dashboard(predictions_file: str, output_file: str = None):
    """Generate HTML dashboard from predictions CSV"""

    # Load predictions
    df = pd.read_csv(predictions_file)

    # Calculate stats
    total_games = len(df)
    avg_confidence = df['confidence'].mean() * 100
    avg_predicted_total = (df['predicted_home_score'] + df['predicted_away_score']).mean()
    avg_predicted_margin = abs(df['predicted_home_score'] - df['predicted_away_score']).mean()

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Predictions Dashboard - {datetime.now().strftime('%B %d, %Y')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{ color: #333; font-size: 2.5em; margin-bottom: 10px; }}
        .header .subtitle {{ color: #666; font-size: 1.2em; }}
        .improvements {{
            background: #10b981;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 500;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card .label {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
        .stat-card .value {{ color: #333; font-size: 2em; font-weight: bold; }}
        .stat-card .value.high {{ color: #10b981; }}
        .predictions-section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}
        .section-title {{
            color: #333;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .game-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
        }}
        .game-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .game-title {{ font-size: 1.3em; font-weight: bold; color: #333; }}
        .confidence-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .confidence-badge.very-strong {{ background: #10b981; color: white; }}
        .confidence-badge.strong {{ background: #3b82f6; color: white; }}
        .confidence-badge.moderate {{ background: #f59e0b; color: white; }}
        .confidence-badge.weak {{ background: #ef4444; color: white; }}
        .prediction-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .detail-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }}
        .detail-label {{ color: #666; font-size: 0.85em; margin-bottom: 5px; }}
        .detail-value {{ color: #333; font-size: 1.1em; font-weight: 600; }}
        .score {{ font-size: 1.8em; font-weight: bold; color: #667eea; }}
        .model-breakdown {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
        }}
        .model-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 0.9em;
        }}
        .model-name {{ color: #666; }}
        .model-value {{ color: #333; font-weight: 500; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏀 NBA Predictions Dashboard</h1>
            <div class="subtitle">Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p %Z')}</div>
        </div>

        <div class="improvements">
            ✅ <strong>IMPROVED PROJECTIONS</strong> - Now includes defensive ratings, opponent adjustments, historical calibration, and variance modeling
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Games</div>
                <div class="value">{total_games}</div>
            </div>
            <div class="stat-card">
                <div class="label">Avg Confidence</div>
                <div class="value">{avg_confidence:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">Avg Predicted Total</div>
                <div class="value">{avg_predicted_total:.1f}</div>
            </div>
            <div class="stat-card">
                <div class="label">Avg Predicted Margin</div>
                <div class="value">{avg_predicted_margin:.1f}</div>
            </div>
        </div>

        <div class="predictions-section">
            <h2 class="section-title">Game Predictions</h2>
"""

    # Add game predictions
    for _, game in df.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        predicted_winner = game['predicted_winner']
        home_score = game['predicted_home_score']
        away_score = game['predicted_away_score']
        home_prob = game['home_win_probability'] * 100
        away_prob = game['away_win_probability'] * 100
        confidence = game['confidence'] * 100
        strength = game['prediction_strength']
        model_agreement = game.get('model_agreement', 0) * 100 if pd.notna(game.get('model_agreement')) else 0
        predicted_total = home_score + away_score
        predicted_margin = abs(home_score - away_score)

        # Confidence badge class
        strength_class = strength.lower().replace(' ', '-')

        # Individual model probabilities
        panel_prob = game.get('panel_home_win_prob', None)
        bayesian_prob = game.get('bayesian_home_win_prob', None)
        simultaneous_prob = game.get('simultaneous_home_win_prob', None)

        html += f"""
            <div class="game-card">
                <div class="game-header">
                    <div class="game-title">{away_team} @ {home_team}</div>
                    <span class="confidence-badge {strength_class}">{strength}</span>
                </div>
                <div class="prediction-details">
                    <div class="detail-item">
                        <div class="detail-label">Predicted Winner</div>
                        <div class="detail-value">{predicted_winner} ({max(home_prob, away_prob):.1f}%)</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Predicted Score</div>
                        <div class="score">{home_score:.1f} - {away_score:.1f}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Predicted Total</div>
                        <div class="detail-value">{predicted_total:.1f} points</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Predicted Margin</div>
                        <div class="detail-value">{predicted_margin:.1f} points</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Confidence</div>
                        <div class="detail-value">{confidence:.1f}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Model Agreement</div>
                        <div class="detail-value">{model_agreement:.1f}%</div>
                    </div>
                </div>"""

        # Model breakdown if available
        if panel_prob is not None or bayesian_prob is not None or simultaneous_prob is not None:
            html += """
                <div class="model-breakdown">
                    <div class="detail-label" style="margin-bottom: 10px;">Individual Model Probabilities:</div>"""

            if panel_prob is not None:
                html += f"""
                    <div class="model-row">
                        <span class="model-name">Panel Regression:</span>
                        <span class="model-value">{panel_prob*100:.1f}%</span>
                    </div>"""

            if bayesian_prob is not None:
                html += f"""
                    <div class="model-row">
                        <span class="model-name">Hierarchical Bayesian:</span>
                        <span class="model-value">{bayesian_prob*100:.1f}%</span>
                    </div>"""

            if simultaneous_prob is not None:
                html += f"""
                    <div class="model-row">
                        <span class="model-name">Simultaneous Equations:</span>
                        <span class="model-value">{simultaneous_prob*100:.1f}%</span>
                    </div>"""

            html += "</div>"

        html += """
            </div>"""

    html += """
        </div>
    </div>
</body>
</html>"""

    # Save HTML
    if output_file is None:
        output_dir = Path(predictions_file).parent
        output_file = output_dir / f"predictions_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    with open(output_file, 'w') as f:
        f.write(html)

    # Create symlink to latest
    latest_file = Path(output_file).parent / "predictions_dashboard_latest.html"
    if latest_file.exists() or latest_file.is_symlink():
        latest_file.unlink()
    latest_file.symlink_to(Path(output_file).name)

    print(f"✓ HTML dashboard generated: {output_file}")
    print(f"✓ Symlink created: {latest_file}")

    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML dashboard from predictions CSV"
    )
    parser.add_argument(
        '--predictions',
        type=str,
        default='/tmp/nba_predictions/predictions_latest.csv',
        help='Path to predictions CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output HTML file path (default: auto-generated)'
    )

    args = parser.parse_args()

    if not os.path.exists(args.predictions):
        print(f"Error: Predictions file not found: {args.predictions}")
        return

    print("="*80)
    print("GENERATING HTML DASHBOARD")
    print("="*80)
    print(f"\nPredictions file: {args.predictions}")

    output_file = generate_html_dashboard(args.predictions, args.output)

    print(f"\n✓ Dashboard ready: {output_file}")
    print("✓ Open in browser to view")


if __name__ == "__main__":
    main()


