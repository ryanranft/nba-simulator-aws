"""
Phase 2 Serialization Tests

Tests for model serialization and deserialization:
- to_dict() / from_dict()
- to_json() / from_json()
- Round-trip conversions
- from_db_row()
"""

import pytest
import json
from datetime import datetime, date
from nba_simulator.models import Game, Player, Team


class TestGameSerialization:
    """Tests for Game serialization"""

    def test_game_to_dict(self):
        """Test Game.to_dict()"""
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

        game_dict = game.to_dict()

        assert isinstance(game_dict, dict)
        assert game_dict["game_id"] == "401584893"
        assert game_dict["season"] == 2024
        assert game_dict["home_score"] == 110

    def test_game_to_json(self):
        """Test Game.to_json()"""
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

        game_json = game.to_json()

        assert isinstance(game_json, str)
        parsed = json.loads(game_json)
        assert parsed["game_id"] == "401584893"

    def test_game_from_dict(self):
        """Test Game.from_dict()"""
        game_data = {
            "game_id": "401584893",
            "season": 2024,
            "game_date": datetime(2024, 10, 29, 19, 0),
            "home_team_id": "LAL",
            "away_team_id": "DEN",
            "home_score": 110,
            "away_score": 105,
            "status": "final",
        }

        game = Game.from_dict(game_data)

        assert game.game_id == "401584893"
        assert game.season == 2024
        assert game.home_score == 110

    def test_game_round_trip_dict(self):
        """Test Game dict round-trip conversion"""
        original = Game(
            game_id="401584893",
            season=2024,
            game_date=datetime(2024, 10, 29, 19, 0),
            home_team_id="LAL",
            away_team_id="DEN",
            home_score=110,
            away_score=105,
            status="final",
        )

        # Convert to dict and back
        game_dict = original.to_dict()
        restored = Game.from_dict(game_dict)

        assert original == restored

    def test_game_equality(self):
        """Test Game equality comparison"""
        game1 = Game(
            game_id="401584893",
            season=2024,
            game_date=datetime(2024, 10, 29, 19, 0),
            home_team_id="LAL",
            away_team_id="DEN",
            home_score=110,
            away_score=105,
            status="final",
        )

        game2 = Game(
            game_id="401584893",
            season=2024,
            game_date=datetime(2024, 10, 29, 19, 0),
            home_team_id="LAL",
            away_team_id="DEN",
            home_score=110,
            away_score=105,
            status="final",
        )

        assert game1 == game2


class TestPlayerSerialization:
    """Tests for Player serialization"""

    def test_player_to_dict(self):
        """Test Player.to_dict()"""
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

        player_dict = player.to_dict()

        assert isinstance(player_dict, dict)
        assert player_dict["player_id"] == "2544"
        assert player_dict["first_name"] == "LeBron"
        assert player_dict["height_inches"] == 81

    def test_player_round_trip_dict(self):
        """Test Player dict round-trip conversion"""
        original = Player(
            player_id="2544",
            first_name="LeBron",
            last_name="James",
            birth_date=date(1984, 12, 30),
            height_inches=81,
            weight_pounds=250,
            position="SF",
            rookie_year=2003,
        )

        # Convert to dict and back
        player_dict = original.to_dict()
        restored = Player.from_dict(player_dict)

        assert original == restored

    def test_player_to_json_formatting(self):
        """Test Player.to_json() with formatting"""
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

        # Test formatted JSON
        formatted_json = player.to_json(indent=2)
        assert "\\n" in repr(formatted_json)  # Should have newlines

        # Test compact JSON
        compact_json = player.to_json()
        assert "\\n" not in repr(compact_json)  # Should not have newlines


class TestTeamSerialization:
    """Tests for Team serialization"""

    def test_team_to_dict(self):
        """Test Team.to_dict()"""
        team = Team(
            team_id="LAL",
            team_name="Los Angeles Lakers",
            team_city="Los Angeles",
            team_nickname="Lakers",
            conference="Western",
            division="Pacific",
            founded_year=1947,
        )

        team_dict = team.to_dict()

        assert isinstance(team_dict, dict)
        assert team_dict["team_id"] == "LAL"
        assert team_dict["conference"] == "Western"

    def test_team_round_trip_dict(self):
        """Test Team dict round-trip conversion"""
        original = Team(
            team_id="LAL",
            team_name="Los Angeles Lakers",
            team_city="Los Angeles",
            team_nickname="Lakers",
            conference="Western",
            division="Pacific",
            founded_year=1947,
        )

        # Convert to dict and back
        team_dict = original.to_dict()
        restored = Team.from_dict(team_dict)

        assert original == restored

    def test_team_hash_for_set(self):
        """Test Team can be used in sets (hashable)"""
        team1 = Team(
            team_id="LAL",
            team_name="Los Angeles Lakers",
            team_city="Los Angeles",
            team_nickname="Lakers",
            conference="Western",
            division="Pacific",
            founded_year=1947,
        )

        team2 = Team(
            team_id="BOS",
            team_name="Boston Celtics",
            team_city="Boston",
            team_nickname="Celtics",
            conference="Eastern",
            division="Atlantic",
            founded_year=1946,
        )

        # Should be able to create a set
        team_set = {team1, team2}
        assert len(team_set) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
