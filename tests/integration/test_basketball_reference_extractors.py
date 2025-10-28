"""
Integration Tests for Basketball Reference Extractors

Tests Basketball Reference extractors.
Basketball Reference provides historical data.
"""

import unittest
from tests.integration.base_integration_test import BaseIntegrationTest
from nba_simulator.etl.extractors.basketball_reference import (
    BasketballReferencePlayByPlayExtractor,
    BasketballReferenceBoxScoresExtractor
)


class TestBasketballReferencePlayByPlayExtractor(BaseIntegrationTest):
    """
    Test BasketballReferencePlayByPlayExtractor.

    Basketball Reference provides historical data.
    """

    def setUp(self):
        """Set up test"""
        self.extractor = BasketballReferencePlayByPlayExtractor()

    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "basketball_reference_play_by_play")

    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()

        self.assertEqual(health['status'], 'operational')
        self.assertEqual(health.get('data_source'), 'Basketball Reference')
        self.assertEqual(health.get('purpose'), 'Historical data and comprehensive coverage')

        # Check rate limiting note
        self.assertIn('rate_limit_note', health)
        self.assertIn('3s', health['rate_limit_note'])

        # Check legacy scripts
        if 'legacy_scripts' in health:
            scripts = health['legacy_scripts']
            # Should have 6 modes
            self.assertGreaterEqual(len(scripts), 6, "BBRef should have multiple modes")

            available = [name for name, exists in scripts.items() if exists]
            print(f"\n  ✓ Basketball Reference PBP modes: {', '.join(available)}")

    def test_extractor_has_multiple_modes(self):
        """Test BBRef extractor has comprehensive mode support"""
        self.assertIsNotNone(self.extractor.legacy_scripts)

        # BBRef should have 6 modes
        expected_modes = ['async', 'incremental', 'comprehensive',
                         'daily', 'backfill', 'discovery']

        for mode in expected_modes:
            self.assertIn(mode, self.extractor.legacy_scripts)

    def test_rate_limiting_configured(self):
        """Test BBRef has slower rate limiting (3s)"""
        # BBRef should have 3s rate limit to respect their site
        self.assertEqual(self.extractor.rate_limit_delay, 3.0)


class TestBasketballReferenceBoxScoresExtractor(BaseIntegrationTest):
    """Test BasketballReferenceBoxScoresExtractor"""

    def setUp(self):
        """Set up test"""
        self.extractor = BasketballReferenceBoxScoresExtractor()

    def test_extractor_instantiation(self):
        """Test extractor can be instantiated"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.name, "basketball_reference_box_scores")

    def test_health_check(self):
        """Test extractor health check"""
        health = self.extractor.health_check()
        self.assertEqual(health['status'], 'operational')

    def test_rate_limiting_configured(self):
        """Test BBRef box scores has 3s rate limit"""
        self.assertEqual(self.extractor.rate_limit_delay, 3.0)


if __name__ == '__main__':
    unittest.main()

