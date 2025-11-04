#!/usr/bin/env python3
"""
Filter betting picks to show only the best pick per unique bet type.

Groups picks by unique bet identifier and selects the pick with highest
expected value (EV) for each group.

Usage:
    python scripts/ml/filter_best_picks.py --picks /tmp/today_betting_picks.csv --output /tmp/today_betting_picks_best.csv
"""

import argparse
import pandas as pd
from pathlib import Path


def create_bet_identifier(row: pd.Series) -> str:
    """Create unique identifier for a bet."""
    game_id = row['game_id']
    market_type = row['market_type']
    recommendation = str(row['recommendation'])
    
    # For spreads and totals, include the point value in the identifier
    # This ensures "Milwaukee -11.5" and "Milwaukee -12.0" are treated as different bets
    if pd.notna(row.get('point')):
        point = f"{row['point']:.1f}"
        # For totals, the recommendation is "Over X.X" or "Under X.X"
        # For spreads, the recommendation includes the team and spread like "Milwaukee -11.5"
        # Include point in identifier to ensure uniqueness
        bet_id = f"{game_id}_{market_type}_{recommendation}_{point}"
    else:
        # For moneyline, just use game + market + recommendation
        bet_id = f"{game_id}_{market_type}_{recommendation}"
    
    return bet_id


def filter_best_picks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter picks to show only the best pick per unique bet type.
    
    Groups by unique bet identifier and selects the pick with highest EV.
    """
    # Create bet identifier
    df = df.copy()
    df['bet_id'] = df.apply(create_bet_identifier, axis=1)
    
    # Group by bet_id and select row with highest expected_value
    best_picks = df.loc[df.groupby('bet_id')['expected_value'].idxmax()]
    
    # Drop the bet_id column
    best_picks = best_picks.drop('bet_id', axis=1)
    
    # Sort by expected value (descending)
    best_picks = best_picks.sort_values('expected_value', ascending=False)
    
    return best_picks.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Filter betting picks to best pick per bet type")
    parser.add_argument(
        "--picks",
        type=str,
        default="/tmp/today_betting_picks.csv",
        help="Path to betting picks CSV file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/today_betting_picks_best.csv",
        help="Output CSV file path",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("FILTERING BEST PICKS PER BET TYPE")
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
    
    # Filter to best picks
    print(f"\nFiltering to best pick per unique bet type...")
    best_picks_df = filter_best_picks(picks_df)
    
    print(f"✓ Filtered to {len(best_picks_df)} unique bets (from {len(picks_df)} picks)")
    print(f"  Removed {len(picks_df) - len(best_picks_df)} duplicate picks")
    
    # Show breakdown by market type
    print(f"\nBreakdown by market type:")
    for market_type in best_picks_df['market_type'].unique():
        count = len(best_picks_df[best_picks_df['market_type'] == market_type])
        print(f"  {market_type}: {count} unique bets")
    
    # Save filtered picks
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    best_picks_df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved to: {output_path}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

