"""
Tests for ETL Transformers

Tests transformation layer components.
"""

import unittest
from datetime import datetime
from nba_simulator.etl.transformers import DataNormalizer, SchemaValidator
from nba_simulator.etl.transformers.schema_validator import UNIFIED_PLAY_BY_PLAY_SCHEMA


class TestDataNormalizer(unittest.TestCase):
    """Test DataNormalizer"""

    def test_hoopr_normalizer_instantiation(self):
        """Test hoopR normalizer can be instantiated"""
        normalizer = DataNormalizer(source="hoopr")
        self.assertIsNotNone(normalizer)
        self.assertEqual(normalizer.source, "hoopr")

    def test_espn_normalizer_instantiation(self):
        """Test ESPN normalizer can be instantiated"""
        normalizer = DataNormalizer(source="espn")
        self.assertIsNotNone(normalizer)
        self.assertEqual(normalizer.source, "espn")

    def test_hoopr_data_transformation(self):
        """Test hoopR data transformation"""
        normalizer = DataNormalizer(source="hoopr")

        # Sample hoopR data
        hoopr_data = {
            'game_id': '401234567',
            'id': '12345',
            'wallclock': '2024-01-15T19:30:00',
            'type_text': 'Made Shot',
            'athlete_id_1': '2544',
            'team_id': '17',
            'text': 'LeBron James makes 3-pt jump shot'
        }

        result = normalizer.transform(hoopr_data)

        # Check unified fields present
        self.assertIn('game_id', result)
        self.assertIn('event_id', result)
        self.assertIn('data_source', result)
        self.assertEqual(result['data_source'], 'hoopr')
        self.assertEqual(result['game_id'], '401234567')
        self.assertEqual(result['event_id'], '12345')

    def test_schema_validation(self):
        """Test schema validation"""
        normalizer = DataNormalizer(source="hoopr")

        hoopr_data = {
            'game_id': '401234567',
            'id': '12345',
            'wallclock': '2024-01-15T19:30:00',
            'type_text': 'Made Shot',
        }

        result = normalizer.transform(hoopr_data)
        is_valid = normalizer.validate_schema(result)

        self.assertTrue(is_valid)


class TestSchemaValidator(unittest.TestCase):
    """Test SchemaValidator"""

    def test_validator_instantiation(self):
        """Test validator can be instantiated"""
        validator = SchemaValidator(UNIFIED_PLAY_BY_PLAY_SCHEMA)
        self.assertIsNotNone(validator)

    def test_valid_data_passes(self):
        """Test valid data passes validation"""
        validator = SchemaValidator(UNIFIED_PLAY_BY_PLAY_SCHEMA)

        valid_data = {
            'game_id': '401234567',
            'event_id': '12345',
            'timestamp': datetime.utcnow(),
            'event_type': 'Made Shot',
            'player_id': '2544',
            'team_id': '17',
            'event_data': {},
            'data_source': 'hoopr',
            'created_at': datetime.utcnow()
        }

        is_valid, errors = validator.validate(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_missing_required_field_fails(self):
        """Test missing required field fails validation"""
        validator = SchemaValidator(UNIFIED_PLAY_BY_PLAY_SCHEMA)

        invalid_data = {
            # Missing 'game_id' (required)
            'event_id': '12345',
            'timestamp': datetime.utcnow(),
            'data_source': 'hoopr',
            'created_at': datetime.utcnow()
        }

        is_valid, errors = validator.validate(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()

