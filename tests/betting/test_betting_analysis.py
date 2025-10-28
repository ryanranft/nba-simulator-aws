#!/usr/bin/env python3
"""
Tests for betting analysis functionality.

Run with: pytest tests/betting/test_betting_analysis.py -v
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts/betting"))

from calculate_betting_edges import (
    american_to_probability,
    probability_to_american,
    calculate_ev,
    kelly_criterion,
)


class TestOddsConversion:
    """Test odds conversion functions."""

    def test_american_to_probability_positive(self):
        """Test conversion of positive American odds."""
        # +150 should be 40%
        assert abs(american_to_probability(150) - 0.4) < 0.01

        # +200 should be 33.3%
        assert abs(american_to_probability(200) - 0.333) < 0.01

    def test_american_to_probability_negative(self):
        """Test conversion of negative American odds."""
        # -150 should be 60%
        assert abs(american_to_probability(-150) - 0.6) < 0.01

        # -200 should be 66.7%
        assert abs(american_to_probability(-200) - 0.667) < 0.01

    def test_american_to_probability_even(self):
        """Test conversion of even odds."""
        # +100 should be 50%
        assert abs(american_to_probability(100) - 0.5) < 0.01


class TestExpectedValue:
    """Test expected value calculations."""

    def test_positive_ev(self):
        """Test positive EV calculation."""
        # 60% win probability at +150 odds
        model_prob = 0.60
        market_odds = 150
        ev = calculate_ev(model_prob, market_odds)

        # Should have positive EV
        assert ev > 0

    def test_negative_ev(self):
        """Test negative EV calculation."""
        # 30% win probability at +150 odds
        model_prob = 0.30
        market_odds = 150
        ev = calculate_ev(model_prob, market_odds)

        # Should have negative EV
        assert ev < 0

    def test_fair_odds(self):
        """Test EV at fair odds."""
        # 40% win probability at +150 odds (fair)
        model_prob = 0.40
        market_odds = 150
        ev = calculate_ev(model_prob, market_odds)

        # Should be close to 0
        assert abs(ev) < 0.05


class TestKellyCriterion:
    """Test Kelly Criterion calculations."""

    def test_kelly_positive_edge(self):
        """Test Kelly with positive edge."""
        # 60% win probability at +150 odds
        model_prob = 0.60
        market_odds = 150
        kelly = kelly_criterion(model_prob, market_odds)

        # Should suggest betting
        assert kelly > 0

    def test_kelly_negative_edge(self):
        """Test Kelly with negative edge."""
        # 30% win probability at +150 odds
        model_prob = 0.30
        market_odds = 150
        kelly = kelly_criterion(model_prob, market_odds)

        # Should not suggest betting
        assert kelly == 0

    def test_kelly_cap(self):
        """Test Kelly is capped at 25%."""
        # Very favorable odds
        model_prob = 0.90
        market_odds = 200
        kelly = kelly_criterion(model_prob, market_odds)

        # Should be capped at 25%
        assert kelly <= 0.25


def test_import_all_modules():
    """Test that all betting modules can be imported."""
    import fetch_todays_odds
    import fetch_simulation_features
    import generate_ml_predictions
    import run_game_simulations
    import simulate_player_props
    import calculate_betting_edges
    import generate_betting_report

    assert True  # If we get here, imports worked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
