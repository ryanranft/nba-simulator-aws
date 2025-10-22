#!/usr/bin/env python3
"""
Enhanced Phase 9.8: Betting Integration

Integrates betting odds and predictions with enhanced features:
- Real-time odds calculation with market data
- Quarter-by-quarter predictions with confidence intervals
- ROI tracking with advanced analytics
- Betting strategy optimization with Kelly Criterion
- Risk management and bankroll management
- Historical performance analysis

Created: October 13, 2025
Phase: 9.8 (Betting Integration) - Enhanced
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import math

logger = logging.getLogger(__name__)


class EnhancedBettingIntegrationSystem:
    """
    Enhanced betting integration system for quarter-by-quarter predictions and ROI tracking.

    Features:
    - Real-time odds calculation
    - Advanced betting strategies
    - Kelly Criterion optimization
    - Risk management
    - Performance analytics
    """

    def __init__(self):
        self.betting_history = []
        self.roi_tracker = {}
        self.strategy_performance = {}

        # Market data simulation (in production, would connect to real odds providers)
        self.market_data = {
            "vig": 0.05,  # 5% house edge
            "volatility_factor": 1.2,
            "liquidity_factor": 0.8,
        }

        # Risk management parameters
        self.risk_params = {
            "max_bet_percentage": 0.05,  # Max 5% of bankroll per bet
            "max_daily_loss": 0.20,  # Max 20% daily loss
            "kelly_factor": 0.25,  # Conservative Kelly factor
            "stop_loss_threshold": 0.10,  # Stop loss at 10% drawdown
        }

        # Performance tracking
        self.performance_metrics = {
            "total_bets": 0,
            "winning_bets": 0,
            "total_wagered": 0.0,
            "total_profit": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
        }

    def calculate_quarter_odds(
        self,
        home_score: int,
        away_score: int,
        quarter: int,
        time_remaining: int,
        market_context: Dict[str, Any] = None,
    ) -> Dict[str, float]:
        """Calculate betting odds with enhanced market factors"""

        if market_context is None:
            market_context = {}

        score_diff = home_score - away_score

        # Base probability calculation
        base_prob = 0.5 + (score_diff * 0.01)  # Each point = 1% advantage

        # Time factor (more time = more uncertainty)
        time_factor = time_remaining / 720.0
        time_adjustment = time_factor * 0.1

        # Quarter factor (later quarters = more certainty)
        quarter_factor = (quarter - 1) / 3.0
        quarter_adjustment = quarter_factor * 0.05

        # Market volatility adjustment
        volatility = market_context.get("volatility", 1.0)
        volatility_adjustment = (volatility - 1.0) * 0.02

        # Final probability
        home_prob = (
            base_prob + time_adjustment + quarter_adjustment + volatility_adjustment
        )

        # Apply house edge (vig)
        vig = self.market_data["vig"]
        home_prob_adjusted = home_prob * (1 - vig)
        away_prob_adjusted = (1 - home_prob) * (1 - vig)

        # Convert to odds
        home_odds = 1.0 / home_prob_adjusted if home_prob_adjusted > 0 else 10.0
        away_odds = 1.0 / away_prob_adjusted if away_prob_adjusted > 0 else 10.0

        # Add market spread
        spread = self._calculate_spread(score_diff, time_remaining, quarter)

        return {
            "home_odds": round(home_odds, 2),
            "away_odds": round(away_odds, 2),
            "home_probability": round(home_prob_adjusted, 3),
            "away_probability": round(away_prob_adjusted, 3),
            "spread": round(spread, 1),
            "total_line": self._calculate_total_line(
                home_score, away_score, time_remaining, quarter
            ),
            "confidence": self._calculate_odds_confidence(
                time_remaining, quarter, score_diff
            ),
        }

    def _calculate_spread(
        self, score_diff: int, time_remaining: int, quarter: int
    ) -> float:
        """Calculate point spread"""
        # Base spread from current score differential
        base_spread = score_diff

        # Adjust for time remaining (less time = more certain spread)
        time_factor = time_remaining / 720.0
        time_adjustment = (1.0 - time_factor) * 2.0

        # Adjust for quarter (later quarters = more certain spread)
        quarter_factor = (quarter - 1) / 3.0
        quarter_adjustment = quarter_factor * 1.0

        spread = base_spread + time_adjustment + quarter_adjustment

        return round(spread, 1)

    def _calculate_total_line(
        self, home_score: int, away_score: int, time_remaining: int, quarter: int
    ) -> float:
        """Calculate over/under total line"""
        current_total = home_score + away_score

        # Project remaining points based on pace
        minutes_remaining = time_remaining / 60.0
        avg_quarter_score = 25.0  # Historical average

        remaining_quarters = (4 - quarter) + (minutes_remaining / 12.0)
        projected_additional = remaining_quarters * avg_quarter_score

        total_line = current_total + projected_additional

        return round(total_line, 1)

    def _calculate_odds_confidence(
        self, time_remaining: int, quarter: int, score_diff: int
    ) -> float:
        """Calculate confidence in odds"""
        # More time = less confidence
        time_factor = time_remaining / 720.0

        # Later quarters = more confidence
        quarter_factor = (quarter - 1) / 3.0

        # Larger score differential = more confidence
        score_factor = min(abs(score_diff) / 20.0, 1.0)

        confidence = (
            (1.0 - time_factor) * 0.4 + quarter_factor * 0.3 + score_factor * 0.3
        )

        return round(confidence, 3)

    def calculate_kelly_bet_size(
        self, win_probability: float, odds: float, bankroll: float
    ) -> float:
        """Calculate optimal bet size using Kelly Criterion"""

        if win_probability <= 0 or win_probability >= 1 or odds <= 1:
            return 0.0

        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = win probability, q = 1 - p
        b = odds - 1
        p = win_probability
        q = 1 - p

        kelly_fraction = (b * p - q) / b

        # Apply conservative factor
        conservative_factor = self.risk_params["kelly_factor"]
        adjusted_fraction = kelly_fraction * conservative_factor

        # Ensure within risk limits
        max_fraction = self.risk_params["max_bet_percentage"]
        final_fraction = min(adjusted_fraction, max_fraction)

        bet_size = bankroll * final_fraction

        return max(0.0, bet_size)

    def calculate_spread_betting(
        self, home_score: int, away_score: int, spread: float, bet_amount: float = 100.0
    ) -> Dict[str, Any]:
        """Calculate spread betting with enhanced analysis"""

        current_diff = home_score - away_score

        # Determine if spread is covered
        home_covers = current_diff > spread
        away_covers = current_diff < -spread
        push = abs(current_diff - spread) < 0.5

        # Calculate potential outcomes
        if home_covers:
            home_payout = bet_amount * 1.91  # Standard -110 odds
            away_payout = 0
        elif away_covers:
            home_payout = 0
            away_payout = bet_amount * 1.91
        else:  # Push
            home_payout = bet_amount
            away_payout = bet_amount

        # Calculate edge
        spread_differential = abs(current_diff - spread)
        edge = max(
            0, 1.0 - spread_differential / 10.0
        )  # Edge decreases as spread gets closer

        return {
            "current_spread": current_diff,
            "betting_spread": spread,
            "home_covers": home_covers,
            "away_covers": away_covers,
            "push": push,
            "spread_differential": spread_differential,
            "home_payout": home_payout,
            "away_payout": away_payout,
            "edge": edge,
            "recommended_bet": (
                "home" if home_covers else "away" if away_covers else "pass"
            ),
        }

    def calculate_total_betting(
        self,
        home_score: int,
        away_score: int,
        total_line: float,
        bet_amount: float = 100.0,
    ) -> Dict[str, Any]:
        """Calculate total (over/under) betting with enhanced analysis"""

        current_total = home_score + away_score

        over_hit = current_total > total_line
        under_hit = current_total < total_line
        push = abs(current_total - total_line) < 0.5

        # Calculate potential outcomes
        if over_hit:
            over_payout = bet_amount * 1.91
            under_payout = 0
        elif under_hit:
            over_payout = 0
            under_payout = bet_amount * 1.91
        else:  # Push
            over_payout = bet_amount
            under_payout = bet_amount

        # Calculate edge
        total_differential = abs(current_total - total_line)
        edge = max(
            0, 1.0 - total_differential / 20.0
        )  # Edge decreases as total gets closer

        return {
            "current_total": current_total,
            "total_line": total_line,
            "over_hit": over_hit,
            "under_hit": under_hit,
            "push": push,
            "total_differential": total_differential,
            "over_payout": over_payout,
            "under_payout": under_payout,
            "edge": edge,
            "recommended_bet": "over" if over_hit else "under" if under_hit else "pass",
        }

    def track_bet(
        self,
        bet_type: str,
        amount: float,
        odds: float,
        prediction: str,
        game_id: str,
        strategy: str = "default",
    ) -> str:
        """Track a betting decision with enhanced metadata"""

        bet_id = f"{game_id}_{len(self.betting_history) + 1}"

        bet_record = {
            "bet_id": bet_id,
            "bet_type": bet_type,
            "amount": amount,
            "odds": odds,
            "prediction": prediction,
            "game_id": game_id,
            "strategy": strategy,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "expected_value": self._calculate_expected_value(odds, prediction),
            "kelly_fraction": self._calculate_kelly_fraction(odds, prediction),
        }

        self.betting_history.append(bet_record)

        # Update strategy tracking
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                "total_bets": 0,
                "winning_bets": 0,
                "total_wagered": 0.0,
                "total_profit": 0.0,
            }

        self.strategy_performance[strategy]["total_bets"] += 1
        self.strategy_performance[strategy]["total_wagered"] += amount

        logger.info(
            f"Tracked bet: {bet_id} - {bet_type} - ${amount} at {odds} ({strategy})"
        )

        return bet_id

    def _calculate_expected_value(self, odds: float, prediction: str) -> float:
        """Calculate expected value of bet"""
        # Simplified EV calculation
        win_prob = 0.5  # Would use actual model prediction in production
        payout = odds - 1

        ev = (win_prob * payout) - ((1 - win_prob) * 1)
        return ev

    def _calculate_kelly_fraction(self, odds: float, prediction: str) -> float:
        """Calculate Kelly fraction for bet"""
        win_prob = 0.5  # Would use actual model prediction in production

        if win_prob <= 0 or win_prob >= 1 or odds <= 1:
            return 0.0

        b = odds - 1
        p = win_prob
        q = 1 - p

        kelly_fraction = (b * p - q) / b
        return max(0.0, kelly_fraction)

    def resolve_bet(
        self, bet_id: str, outcome: str, actual_result: Any, actual_odds: float = None
    ) -> Dict[str, Any]:
        """Resolve a betting decision with enhanced analytics"""

        bet = next((b for b in self.betting_history if b["bet_id"] == bet_id), None)

        if not bet:
            return {"error": "Bet not found"}

        bet["status"] = "resolved"
        bet["outcome"] = outcome
        bet["actual_result"] = actual_result
        bet["actual_odds"] = actual_odds
        bet["resolved_at"] = datetime.now().isoformat()

        # Calculate payout
        if outcome == "win":
            payout = bet["amount"] * bet["odds"]
            profit = payout - bet["amount"]
        elif outcome == "push":
            payout = bet["amount"]
            profit = 0
        else:  # loss
            payout = 0
            profit = -bet["amount"]

        bet["payout"] = payout
        bet["profit"] = profit

        # Update ROI tracking
        if bet["game_id"] not in self.roi_tracker:
            self.roi_tracker[bet["game_id"]] = {"total_bet": 0, "total_profit": 0}

        self.roi_tracker[bet["game_id"]]["total_bet"] += bet["amount"]
        self.roi_tracker[bet["game_id"]]["total_profit"] += profit

        # Update strategy performance
        strategy = bet["strategy"]
        if outcome == "win":
            self.strategy_performance[strategy]["winning_bets"] += 1
        self.strategy_performance[strategy]["total_profit"] += profit

        # Update overall performance metrics
        self.performance_metrics["total_bets"] += 1
        if outcome == "win":
            self.performance_metrics["winning_bets"] += 1
        self.performance_metrics["total_wagered"] += bet["amount"]
        self.performance_metrics["total_profit"] += profit

        # Calculate win rate
        win_rate = (
            self.performance_metrics["winning_bets"]
            / self.performance_metrics["total_bets"]
        )

        return {
            "bet_id": bet_id,
            "outcome": outcome,
            "payout": payout,
            "profit": profit,
            "roi": profit / bet["amount"] if bet["amount"] > 0 else 0,
            "win_rate": win_rate,
            "strategy_performance": self.strategy_performance[strategy],
        }

    def calculate_roi(
        self, game_id: str = None, strategy: str = None
    ) -> Dict[str, float]:
        """Calculate Return on Investment with enhanced analytics"""

        if game_id:
            if game_id not in self.roi_tracker:
                return {"roi": 0.0, "total_bet": 0.0, "total_profit": 0.0}

            tracker = self.roi_tracker[game_id]
            roi = (
                tracker["total_profit"] / tracker["total_bet"]
                if tracker["total_bet"] > 0
                else 0.0
            )

            return {
                "roi": roi,
                "total_bet": tracker["total_bet"],
                "total_profit": tracker["total_profit"],
                "game_id": game_id,
            }

        elif strategy:
            if strategy not in self.strategy_performance:
                return {"roi": 0.0, "total_bet": 0.0, "total_profit": 0.0}

            perf = self.strategy_performance[strategy]
            roi = (
                perf["total_profit"] / perf["total_wagered"]
                if perf["total_wagered"] > 0
                else 0.0
            )

            return {
                "roi": roi,
                "total_bet": perf["total_wagered"],
                "total_profit": perf["total_profit"],
                "win_rate": (
                    perf["winning_bets"] / perf["total_bets"]
                    if perf["total_bets"] > 0
                    else 0.0
                ),
                "strategy": strategy,
            }

        else:
            # Overall ROI
            total_bet = sum(
                tracker["total_bet"] for tracker in self.roi_tracker.values()
            )
            total_profit = sum(
                tracker["total_profit"] for tracker in self.roi_tracker.values()
            )
            roi = total_profit / total_bet if total_bet > 0 else 0.0

            return {
                "roi": roi,
                "total_bet": total_bet,
                "total_profit": total_profit,
                "games_tracked": len(self.roi_tracker),
                "total_bets": self.performance_metrics["total_bets"],
                "win_rate": (
                    self.performance_metrics["winning_bets"]
                    / self.performance_metrics["total_bets"]
                    if self.performance_metrics["total_bets"] > 0
                    else 0.0
                ),
            }

    def get_betting_recommendations(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get betting recommendations based on current game state"""

        home_score = game_state.get("home_score", 0)
        away_score = game_state.get("away_score", 0)
        quarter = game_state.get("quarter", 1)
        time_remaining = game_state.get("time_remaining", 720)

        # Calculate odds
        odds = self.calculate_quarter_odds(
            home_score, away_score, quarter, time_remaining
        )

        # Calculate spread betting
        spread_betting = self.calculate_spread_betting(
            home_score, away_score, odds["spread"]
        )

        # Calculate total betting
        total_betting = self.calculate_total_betting(
            home_score, away_score, odds["total_line"]
        )

        # Generate recommendations
        recommendations = {
            "odds": odds,
            "spread_betting": spread_betting,
            "total_betting": total_betting,
            "recommendations": [],
        }

        # Add recommendations based on edge
        if spread_betting["edge"] > 0.6:
            recommendations["recommendations"].append(
                {
                    "type": "spread",
                    "bet": spread_betting["recommended_bet"],
                    "edge": spread_betting["edge"],
                    "confidence": "high",
                }
            )

        if total_betting["edge"] > 0.6:
            recommendations["recommendations"].append(
                {
                    "type": "total",
                    "bet": total_betting["recommended_bet"],
                    "edge": total_betting["edge"],
                    "confidence": "high",
                }
            )

        return recommendations

    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics"""

        analytics = {
            "overall_performance": self.performance_metrics.copy(),
            "strategy_performance": self.strategy_performance.copy(),
            "roi_by_game": {},
            "roi_by_strategy": {},
            "risk_metrics": self._calculate_risk_metrics(),
        }

        # Calculate ROI by game
        for game_id in self.roi_tracker:
            analytics["roi_by_game"][game_id] = self.calculate_roi(game_id=game_id)

        # Calculate ROI by strategy
        for strategy in self.strategy_performance:
            analytics["roi_by_strategy"][strategy] = self.calculate_roi(
                strategy=strategy
            )

        return analytics

    def _calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate risk management metrics"""

        if not self.betting_history:
            return {"max_drawdown": 0.0, "sharpe_ratio": 0.0, "var_95": 0.0}

        # Calculate daily P&L
        daily_pnl = {}
        for bet in self.betting_history:
            if bet["status"] == "resolved":
                date = bet["resolved_at"][:10]  # Extract date
                if date not in daily_pnl:
                    daily_pnl[date] = 0.0
                daily_pnl[date] += bet["profit"]

        pnl_values = list(daily_pnl.values())

        if len(pnl_values) < 2:
            return {"max_drawdown": 0.0, "sharpe_ratio": 0.0, "var_95": 0.0}

        # Calculate max drawdown
        cumulative_pnl = np.cumsum(pnl_values)
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdowns = running_max - cumulative_pnl
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0.0

        # Calculate Sharpe ratio (simplified)
        mean_return = np.mean(pnl_values)
        std_return = np.std(pnl_values)
        sharpe_ratio = mean_return / std_return if std_return > 0 else 0.0

        # Calculate Value at Risk (95%)
        var_95 = np.percentile(pnl_values, 5)  # 5th percentile

        return {
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "var_95": var_95,
            "daily_volatility": std_return,
        }


if __name__ == "__main__":
    betting_system = EnhancedBettingIntegrationSystem()
    print("✅ Enhanced Betting Integration System created successfully!")

    # Test with sample data
    try:
        # Test odds calculation
        odds = betting_system.calculate_quarter_odds(50, 45, 3, 300)
        print(f"\n🎯 Quarter Odds: {odds}")

        # Test spread betting
        spread = betting_system.calculate_spread_betting(50, 45, 3.5)
        print(f"\n📊 Spread Betting: {spread}")

        # Test total betting
        total = betting_system.calculate_total_betting(50, 45, 200.5)
        print(f"\n📈 Total Betting: {total}")

        # Test Kelly Criterion
        kelly_bet = betting_system.calculate_kelly_bet_size(0.6, 1.8, 1000.0)
        print(f"\n💰 Kelly Bet Size: ${kelly_bet:.2f}")

        # Test bet tracking
        bet_id = betting_system.track_bet(
            "moneyline", 100.0, 1.8, "home", "test_game_001", "kelly"
        )
        print(f"\n📝 Tracked Bet: {bet_id}")

        # Test bet resolution
        result = betting_system.resolve_bet(bet_id, "win", "home_wins")
        print(f"\n✅ Bet Resolution: {result}")

        # Test ROI calculation
        roi = betting_system.calculate_roi("test_game_001")
        print(f"\n📊 ROI: {roi}")

        # Test betting recommendations
        game_state = {
            "home_score": 50,
            "away_score": 45,
            "quarter": 3,
            "time_remaining": 300,
        }
        recommendations = betting_system.get_betting_recommendations(game_state)
        print(
            f"\n🎯 Betting Recommendations: {len(recommendations['recommendations'])} recommendations"
        )

        # Test performance analytics
        analytics = betting_system.get_performance_analytics()
        print(
            f"\n📈 Performance Analytics: {analytics['overall_performance']['total_bets']} total bets"
        )

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ Enhanced Betting Integration System test completed!")





