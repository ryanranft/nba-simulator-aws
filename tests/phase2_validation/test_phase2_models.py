"""
Phase 2 Model Tests

Comprehensive tests for Game, Player, and Team models including:
- Valid creation
- Validation edge cases
- Helper methods
- Equality and hashing
"""

import pytest
from datetime import datetime, date
from nba_simulator.models import Game, Player, Team, ValidationError


class TestGameModel:
    """Tests for Game model"""

    def test_game_creation_valid(self):
        """Test creating a valid game"""
        game = Game(
            game_id="401584893",
            season=2024,
            game_date=datetime(2024, 10, 29, 19, 0),
            home_team_id="LAL",
            away_team_id="DEN",
            home_score=110,
            away_score=105,
            status="final",
        )
        assert game.game_id == "401584893"
        assert game.season == 2024
        assert game.home_team_id == "LAL"

    def test_game_same_teams_invalid(self):
        """Test that same home/away team is invalid"""
        with pytest.raises(
            ValidationError, match="Home and away teams must be different"
        ):
            Game(
                game_id="401584893",
                season=2024,
                game_date=datetime(2024, 10, 29),
                home_team_id="LAL",
                away_team_id="LAL",  # Same as home
                status="scheduled",
            )

    def test_game_negative_score_invalid(self):
        """Test that negative scores are invalid"""
        with pytest.raises(ValidationError, match="score cannot be negative"):
            Game(
                game_id="401584893",
                season=2024,
                game_date=datetime(2024, 10, 29),
                home_team_id="LAL",
                away_team_id="DEN",
                home_score=-10,
                away_score=100,
                status="final",
            )

    def test_game_final_without_scores_invalid(self):
        """Test that final games must have scores"""
        with pytest.raises(ValidationError, match="Final games must have scores"):
            Game(
                game_id="401584893",
                season=2024,
                game_date=datetime(2024, 10, 29),
                home_team_id="LAL",
                away_team_id="DEN",
                status="final",  # Final but no scores
            )

    def test_game_invalid_season(self):
        """Test that invalid seasons are rejected"""
        with pytest.raises(ValidationError, match="Season must be 1946 or later"):
            Game(
                game_id="401584893",
                season=1945,  # Before NBA founded
                game_date=datetime(2024, 10, 29),
                home_team_id="LAL",
                away_team_id="DEN",
            )

    def test_game_winner_method(self):
        """Test winner() helper method"""
        game = Game(
            game_id="401584893",
            season=2024,
            game_date=datetime(2024, 10, 29),
            home_team_id="LAL",
            away_team_id="DEN",
            home_score=110,
            away_score=105,
            status="final",
        )
        assert game.winner() == "LAL"

    def test_game_margin_method(self):
        """Test margin() helper method"""
        game = Game(
            game_id="401584893",
            season=2024,
            game_date=datetime(2024, 10, 29),
            home_team_id="LAL",
            away_team_id="DEN",
            home_score=110,
            away_score=105,
            status="final",
        )
        assert game.margin() == 5

    def test_game_total_points_method(self):
        """Test total_points() helper method"""
        game = Game(
            game_id="401584893",
            season=2024,
            game_date=datetime(2024, 10, 29),
            home_team_id="LAL",
            away_team_id="DEN",
            home_score=110,
            away_score=105,
            status="final",
        )
        assert game.total_points() == 215


class TestPlayerModel:
    """Tests for Player model"""

    def test_player_creation_valid(self):
        """Test creating a valid player"""
        player = Player(
            player_id="2544",
            first_name="LeBron",
            last_name="James",
            birth_date=date(1984, 12, 30),
            height_inches=81,
            weight_pounds=250,
            position="SF",
            rookie_year=2003,
        )
        assert player.player_id == "2544"
        assert player.first_name == "LeBron"
        assert player.position == "SF"

    def test_player_invalid_position(self):
        """Test that invalid positions are rejected"""
        with pytest.raises(ValidationError, match="Position must be one of"):
            Player(
                player_id="2544",
                first_name="LeBron",
                last_name="James",
                birth_date=date(1984, 12, 30),
                height_inches=81,
                weight_pounds=250,
                position="XX",  # Invalid position
                rookie_year=2003,
            )

    def test_player_height_too_short_invalid(self):
        """Test that unrealistic height is rejected"""
        with pytest.raises(ValidationError, match="Height must be between"):
            Player(
                player_id="2544",
                first_name="Test",
                last_name="Player",
                birth_date=date(1990, 1, 1),
                height_inches=50,  # Too short
                weight_pounds=200,
                position="PG",
                rookie_year=2010,
            )

    def test_player_invalid_jersey_number(self):
        """Test that invalid jersey numbers are rejected"""
        with pytest.raises(ValidationError, match="Jersey number must be between"):
            Player(
                player_id="2544",
                first_name="Test",
                last_name="Player",
                birth_date=date(1990, 1, 1),
                height_inches=75,
                weight_pounds=200,
                position="PG",
                jersey_number=100,  # Invalid (>99)
                rookie_year=2010,
            )

    def test_player_full_name_method(self):
        """Test full_name() helper method"""
        player = Player(
            player_id="2544",
            first_name="LeBron",
            last_name="James",
            birth_date=date(1984, 12, 30),
            height_inches=81,
            weight_pounds=250,
            position="SF",
            rookie_year=2003,
        )
        assert player.full_name() == "LeBron James"

    def test_player_age_method(self):
        """Test age() calculation"""
        player = Player(
            player_id="2544",
            first_name="LeBron",
            last_name="James",
            birth_date=date(1984, 12, 30),
            height_inches=81,
            weight_pounds=250,
            position="SF",
            rookie_year=2003,
        )
        # Age should be 39 or 40 depending on current date
        age = player.age()
        assert 39 <= age <= 41

    def test_player_height_formatting(self):
        """Test height_feet_inches() formatting"""
        player = Player(
            player_id="2544",
            first_name="LeBron",
            last_name="James",
            birth_date=date(1984, 12, 30),
            height_inches=81,
            weight_pounds=250,
            position="SF",
            rookie_year=2003,
        )
        assert player.height_feet_inches() == "6'9\""


class TestTeamModel:
    """Tests for Team model"""

    def test_team_creation_valid(self):
        """Test creating a valid team"""
        team = Team(
            team_id="LAL",
            team_name="Los Angeles Lakers",
            team_city="Los Angeles",
            team_nickname="Lakers",
            conference="Western",
            division="Pacific",
            founded_year=1947,
        )
        assert team.team_id == "LAL"
        assert team.conference == "Western"
        assert team.division == "Pacific"

    def test_team_invalid_conference(self):
        """Test that invalid conferences are rejected"""
        with pytest.raises(ValidationError, match="Conference must be one of"):
            Team(
                team_id="LAL",
                team_name="Los Angeles Lakers",
                team_city="Los Angeles",
                team_nickname="Lakers",
                conference="Central",  # Invalid
                division="Pacific",
                founded_year=1947,
            )

    def test_team_mismatched_conference_division(self):
        """Test that division must match conference"""
        with pytest.raises(
            ValidationError, match="Western conference teams must be in"
        ):
            Team(
                team_id="LAL",
                team_name="Los Angeles Lakers",
                team_city="Los Angeles",
                team_nickname="Lakers",
                conference="Western",
                division="Atlantic",  # Eastern division
                founded_year=1947,
            )

    def test_team_invalid_id_format(self):
        """Test that team ID must be uppercase"""
        with pytest.raises(ValidationError, match="Team ID must be uppercase"):
            Team(
                team_id="lal",  # Lowercase
                team_name="Los Angeles Lakers",
                team_city="Los Angeles",
                team_nickname="Lakers",
                conference="Western",
                division="Pacific",
                founded_year=1947,
            )

    def test_team_full_name_method(self):
        """Test full_name() method"""
        team = Team(
            team_id="LAL",
            team_name="Los Angeles Lakers",
            team_city="Los Angeles",
            team_nickname="Lakers",
            conference="Western",
            division="Pacific",
            founded_year=1947,
        )
        assert team.full_name() == "Los Angeles Lakers"

    def test_team_years_since_founded(self):
        """Test years_since_founded() calculation"""
        team = Team(
            team_id="LAL",
            team_name="Los Angeles Lakers",
            team_city="Los Angeles",
            team_nickname="Lakers",
            conference="Western",
            division="Pacific",
            founded_year=2020,
        )
        years = team.years_since_founded()
        assert years >= 4  # At least 4 years (2020-2024)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
