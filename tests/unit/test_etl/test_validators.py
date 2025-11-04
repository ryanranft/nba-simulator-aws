"""
Tests for ETL Data Validators

Tests validation logic for game data, play-by-play, and box scores.
"""

import pytest
from datetime import datetime

from nba_simulator.etl.validation import (
    BaseValidator,
    GameValidator,
    PlayByPlayValidator,
    BoxScoreValidator,
    ValidationLevel,
    ValidationResult,
    ValidationReport,
    DataSource,
    validate_game,
    validate_play_by_play,
    validate_box_score,
    validate_batch
)


class TestValidationResult:
    """Test ValidationResult functionality"""
    
    def test_validation_result_str(self):
        """Test string representation"""
        result = ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            message="Test error",
            field="test_field",
            expected="value1",
            actual="value2"
        )
        
        result_str = str(result)
        assert "[ERROR]" in result_str
        assert "Test error" in result_str
        assert "test_field" in result_str
        assert "value1" in result_str
        assert "value2" in result_str


class TestValidationReport:
    """Test ValidationReport functionality"""
    
    def test_report_is_valid(self):
        """Test is_valid property"""
        report = ValidationReport()
        
        # Empty report is valid
        assert report.is_valid is True
        
        # Adding warning doesn't invalidate
        report.add_result(ValidationResult(
            is_valid=True,
            level=ValidationLevel.WARNING,
            message="Warning"
        ))
        assert report.is_valid is True
        
        # Adding error invalidates
        report.add_result(ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            message="Error"
        ))
        assert report.is_valid is False
    
    def test_report_counts(self):
        """Test error and warning counts"""
        report = ValidationReport()
        
        report.add_result(ValidationResult(
            is_valid=True,
            level=ValidationLevel.INFO,
            message="Info"
        ))
        report.add_result(ValidationResult(
            is_valid=True,
            level=ValidationLevel.WARNING,
            message="Warning 1"
        ))
        report.add_result(ValidationResult(
            is_valid=True,
            level=ValidationLevel.WARNING,
            message="Warning 2"
        ))
        report.add_result(ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            message="Error"
        ))
        
        assert report.error_count == 1
        assert report.warning_count == 2
        assert report.has_warnings is True


class TestGameValidator:
    """Test GameValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = GameValidator(source=DataSource.ESPN)
        self.valid_game = {
            'game_id': 'ESPN_401234567',
            'game_date': '2024-11-01',
            'home_team': 'LAL',
            'away_team': 'GSW',
            'season': 2024,
            'home_score': 110,
            'away_score': 105
        }
    
    def test_valid_game(self):
        """Test validation of valid game data"""
        report = self.validator.validate(self.valid_game)
        assert report.is_valid is True
        assert report.error_count == 0
    
    def test_missing_required_field(self):
        """Test missing required field"""
        invalid_game = self.valid_game.copy()
        del invalid_game['game_id']
        
        report = self.validator.validate(invalid_game)
        assert report.is_valid is False
        assert report.error_count > 0
    
    def test_invalid_game_id(self):
        """Test invalid game ID"""
        invalid_game = self.valid_game.copy()
        invalid_game['game_id'] = ''
        
        report = self.validator.validate(invalid_game)
        assert report.is_valid is False
    
    def test_invalid_season(self):
        """Test invalid season"""
        invalid_game = self.valid_game.copy()
        invalid_game['season'] = 1900  # Before NBA founded
        
        report = self.validator.validate(invalid_game)
        assert report.is_valid is False
        
        invalid_game['season'] = "2024"  # String instead of int
        report = self.validator.validate(invalid_game)
        assert report.is_valid is False
    
    def test_unusual_score(self):
        """Test unusual score generates warning"""
        invalid_game = self.valid_game.copy()
        invalid_game['home_score'] = 250  # Unrealistic score
        
        report = self.validator.validate(invalid_game)
        assert report.has_warnings is True
    
    def test_short_team_code(self):
        """Test team code validation"""
        invalid_game = self.valid_game.copy()
        invalid_game['home_team'] = 'L'  # Too short
        
        report = self.validator.validate(invalid_game)
        assert report.has_warnings is True


class TestPlayByPlayValidator:
    """Test PlayByPlayValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = PlayByPlayValidator(source=DataSource.ESPN)
        self.valid_play = {
            'game_id': 'ESPN_401234567',
            'period': 1,
            'time_remaining': '10:30',
            'description': 'LeBron James makes layup'
        }
    
    def test_valid_play(self):
        """Test validation of valid play data"""
        report = self.validator.validate(self.valid_play)
        assert report.is_valid is True
        assert report.error_count == 0
    
    def test_missing_required_field(self):
        """Test missing required field"""
        invalid_play = self.valid_play.copy()
        del invalid_play['description']
        
        report = self.validator.validate(invalid_play)
        assert report.is_valid is False
    
    def test_invalid_period(self):
        """Test invalid period number"""
        invalid_play = self.valid_play.copy()
        invalid_play['period'] = 25  # Unrealistic
        
        report = self.validator.validate(invalid_play)
        assert report.has_warnings is True
    
    def test_empty_description(self):
        """Test empty description"""
        invalid_play = self.valid_play.copy()
        invalid_play['description'] = ''
        
        report = self.validator.validate(invalid_play)
        assert report.has_warnings is True
    
    def test_time_remaining_formats(self):
        """Test various time remaining formats"""
        # String format - valid
        play1 = self.valid_play.copy()
        play1['time_remaining'] = '5:45'
        report = self.validator.validate(play1)
        assert report.is_valid is True
        
        # Integer seconds - valid
        play2 = self.valid_play.copy()
        play2['time_remaining'] = 345
        report = self.validator.validate(play2)
        assert report.is_valid is True
        
        # Invalid format
        play3 = self.valid_play.copy()
        play3['time_remaining'] = '10-30'  # Wrong separator
        report = self.validator.validate(play3)
        assert report.is_valid is False


class TestBoxScoreValidator:
    """Test BoxScoreValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = BoxScoreValidator(source=DataSource.NBA_API)
        self.valid_box_score = {
            'game_id': 'NBA_21234567',
            'player_id': '2544',
            'team': 'LAL',
            'points': 28,
            'rebounds': 8,
            'assists': 7,
            'steals': 2,
            'blocks': 1,
            'turnovers': 3,
            'minutes': 38,
            'fg_pct': 0.524,
            'fg3_pct': 0.400,
            'ft_pct': 0.875
        }
    
    def test_valid_box_score(self):
        """Test validation of valid box score"""
        report = self.validator.validate(self.valid_box_score)
        assert report.is_valid is True
        assert report.error_count == 0
    
    def test_missing_required_field(self):
        """Test missing required field"""
        invalid_box = self.valid_box_score.copy()
        del invalid_box['player_id']
        
        report = self.validator.validate(invalid_box)
        assert report.is_valid is False
    
    def test_stat_ranges(self):
        """Test statistical range validation"""
        # Unrealistic points
        invalid_box = self.valid_box_score.copy()
        invalid_box['points'] = 150
        report = self.validator.validate(invalid_box)
        assert report.is_valid is False
        
        # Unrealistic rebounds
        invalid_box = self.valid_box_score.copy()
        invalid_box['rebounds'] = 60
        report = self.validator.validate(invalid_box)
        assert report.is_valid is False
        
        # Unrealistic assists
        invalid_box = self.valid_box_score.copy()
        invalid_box['assists'] = 40
        report = self.validator.validate(invalid_box)
        assert report.is_valid is False
    
    def test_percentage_validation(self):
        """Test shooting percentage validation"""
        # Invalid FG%
        invalid_box = self.valid_box_score.copy()
        invalid_box['fg_pct'] = 1.5  # > 1.0
        report = self.validator.validate(invalid_box)
        assert report.is_valid is False
        
        # Invalid 3P%
        invalid_box = self.valid_box_score.copy()
        invalid_box['fg3_pct'] = -0.1  # < 0.0
        report = self.validator.validate(invalid_box)
        assert report.is_valid is False


class TestBaseValidator:
    """Test BaseValidator functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = BaseValidator(source=DataSource.ESPN)
    
    def test_validate_required_fields_pass(self):
        """Test required fields validation - passing"""
        data = {'field1': 'value1', 'field2': 'value2', 'field3': 'value3'}
        required = ['field1', 'field2']
        
        result = self.validator.validate_required_fields(data, required)
        assert result is True
        assert self.validator.report.is_valid is True
    
    def test_validate_required_fields_fail(self):
        """Test required fields validation - failing"""
        data = {'field1': 'value1'}
        required = ['field1', 'field2', 'field3']
        
        result = self.validator.validate_required_fields(data, required)
        assert result is False
        assert self.validator.report.is_valid is False
    
    def test_validate_field_type_pass(self):
        """Test field type validation - passing"""
        data = {'age': 25, 'name': 'John'}
        
        result = self.validator.validate_field_type(data, 'age', int)
        assert result is True
        
        result = self.validator.validate_field_type(data, 'name', str)
        assert result is True
    
    def test_validate_field_type_fail(self):
        """Test field type validation - failing"""
        data = {'age': '25'}  # String instead of int
        
        result = self.validator.validate_field_type(data, 'age', int)
        assert result is False
        assert self.validator.report.is_valid is False
    
    def test_validate_range_pass(self):
        """Test range validation - passing"""
        result = self.validator.validate_range(50, 'score', min_val=0, max_val=100)
        assert result is True
        
        result = self.validator.validate_range(0, 'score', min_val=0, max_val=100)
        assert result is True
        
        result = self.validator.validate_range(100, 'score', min_val=0, max_val=100)
        assert result is True
    
    def test_validate_range_fail(self):
        """Test range validation - failing"""
        result = self.validator.validate_range(-10, 'score', min_val=0, max_val=100)
        assert result is False
        
        result = self.validator.validate_range(150, 'score', min_val=0, max_val=100)
        assert result is False


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_validate_game_function(self):
        """Test validate_game convenience function"""
        game_data = {
            'game_id': 'TEST_123',
            'game_date': '2024-11-01',
            'home_team': 'LAL',
            'away_team': 'GSW',
            'season': 2024
        }
        
        report = validate_game(game_data, source=DataSource.ESPN)
        assert isinstance(report, ValidationReport)
        assert report.is_valid is True
    
    def test_validate_play_by_play_function(self):
        """Test validate_play_by_play convenience function"""
        play_data = {
            'game_id': 'TEST_123',
            'period': 1,
            'time_remaining': '10:00',
            'description': 'Test play'
        }
        
        report = validate_play_by_play(play_data, source=DataSource.ESPN)
        assert isinstance(report, ValidationReport)
        assert report.is_valid is True
    
    def test_validate_box_score_function(self):
        """Test validate_box_score convenience function"""
        box_score_data = {
            'game_id': 'TEST_123',
            'player_id': '123',
            'team': 'LAL',
            'points': 20
        }
        
        report = validate_box_score(box_score_data, source=DataSource.NBA_API)
        assert isinstance(report, ValidationReport)
        assert report.is_valid is True
    
    def test_validate_batch(self):
        """Test batch validation"""
        games = [
            {
                'game_id': 'TEST_1',
                'game_date': '2024-11-01',
                'home_team': 'LAL',
                'away_team': 'GSW',
                'season': 2024
            },
            {
                'game_id': 'TEST_2',
                'game_date': '2024-11-02',
                'home_team': 'BOS',
                'away_team': 'MIA',
                'season': 2024
            }
        ]
        
        reports = validate_batch(games, GameValidator, source=DataSource.ESPN)
        
        assert len(reports) == 2
        assert all(isinstance(r, ValidationReport) for r in reports)
        assert all(r.is_valid for r in reports)


class TestIntegration:
    """Integration tests for validation workflow"""
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow"""
        # Valid game
        valid_game = {
            'game_id': 'ESPN_401234567',
            'game_date': '2024-11-01',
            'home_team': 'LAL',
            'away_team': 'GSW',
            'season': 2024,
            'home_score': 110,
            'away_score': 105
        }
        
        report = validate_game(valid_game, source=DataSource.ESPN)
        
        # Should be valid
        assert report.is_valid is True
        assert report.error_count == 0
        assert report.source == DataSource.ESPN
        
        # Invalid game - missing required field
        invalid_game = valid_game.copy()
        del invalid_game['game_date']
        
        report = validate_game(invalid_game, source=DataSource.ESPN)
        
        # Should be invalid
        assert report.is_valid is False
        assert report.error_count > 0
    
    def test_multi_source_validation(self):
        """Test validation across multiple sources"""
        sources = [DataSource.ESPN, DataSource.NBA_API, DataSource.HOOPR]
        
        game_data = {
            'game_id': 'TEST_123',
            'game_date': '2024-11-01',
            'home_team': 'LAL',
            'away_team': 'GSW',
            'season': 2024
        }
        
        for source in sources:
            report = validate_game(game_data, source=source)
            assert report.is_valid is True
            assert report.source == source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
