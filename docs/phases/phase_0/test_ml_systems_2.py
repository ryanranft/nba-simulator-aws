#!/usr/bin/env python3
"""
Test Suite: Data Drift Detection

Recommendation ID: ml_systems_2
Generated: 2025-10-15T21:01:26.113762
Updated: 2025-10-15 (comprehensive tests added)

Tests the implementation of Data Drift Detection.

Test Coverage:
- Unit tests for initialization, setup, validation
- Statistical method tests (PSI, KS, Chi², Wasserstein, JS)
- Drift detection with various scenarios
- Error handling and edge cases
- Integration tests for end-to-end workflows
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from implement_ml_systems_2 import DataDriftDetection, SCIPY_AVAILABLE

# Skip all tests if scipy not available
if SCIPY_AVAILABLE:
    import numpy as np
    import pandas as pd


class TestDataDriftDetection(unittest.TestCase):
    """Test suite for DataDriftDetection."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'alert_threshold_psi': 0.2,
            'alert_threshold_ks': 0.1,
            'alert_threshold_chi2': 0.05,
        }
        self.implementation = DataDriftDetection(self.config)

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.implementation, 'cleanup'):
            self.implementation.cleanup()

    def test_initialization(self):
        """Test that DataDriftDetection initializes correctly."""
        self.assertIsNotNone(self.implementation)
        self.assertFalse(self.implementation.setup_complete)
        self.assertEqual(self.implementation.config, self.config)
        self.assertIsNone(self.implementation.reference_data)
        self.assertEqual(self.implementation.psi_threshold, 0.2)
        self.assertEqual(self.implementation.ks_threshold, 0.1)
        self.assertEqual(self.implementation.chi2_pvalue_threshold, 0.05)

    def test_initialization_with_defaults(self):
        """Test initialization with default configuration."""
        impl = DataDriftDetection()
        self.assertEqual(impl.psi_threshold, 0.2)  # Default
        self.assertEqual(impl.ks_threshold, 0.1)   # Default
        self.assertEqual(impl.chi2_pvalue_threshold, 0.05)  # Default

    def test_initialization_with_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        custom_config = {
            'alert_threshold_psi': 0.15,
            'alert_threshold_ks': 0.08,
            'alert_threshold_chi2': 0.01,
        }
        impl = DataDriftDetection(custom_config)
        self.assertEqual(impl.psi_threshold, 0.15)
        self.assertEqual(impl.ks_threshold, 0.08)
        self.assertEqual(impl.chi2_pvalue_threshold, 0.01)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_setup(self):
        """Test setup process."""
        result = self.implementation.setup()
        self.assertTrue(result)
        self.assertTrue(self.implementation.setup_complete)
        self.assertIsNotNone(self.implementation.reference_data)
        self.assertGreater(len(self.implementation.feature_stats), 0)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_setup_generates_demo_data(self):
        """Test that setup generates demo data when no reference provided."""
        self.implementation.setup()

        # Verify reference data was generated
        self.assertIsNotNone(self.implementation.reference_data)
        self.assertGreater(len(self.implementation.reference_data), 0)

        # Verify expected columns exist
        expected_columns = ['team_score', 'opponent_score', 'field_goal_pct',
                           'three_point_pct', 'rebounds', 'assists', 'home_away']
        for col in expected_columns:
            self.assertIn(col, self.implementation.reference_data.columns)

    def test_setup_without_scipy(self):
        """Test setup fails gracefully without scipy."""
        with patch('implement_ml_systems_2.SCIPY_AVAILABLE', False):
            impl = DataDriftDetection(self.config)
            result = impl.setup()
            self.assertFalse(result)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_validate_prerequisites(self):
        """Test prerequisite validation."""
        result = self.implementation.validate_prerequisites()
        self.assertTrue(result)

    def test_validate_prerequisites_without_scipy(self):
        """Test prerequisite validation fails without scipy."""
        with patch('implement_ml_systems_2.SCIPY_AVAILABLE', False):
            impl = DataDriftDetection(self.config)
            result = impl.validate_prerequisites()
            self.assertFalse(result)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_execute_without_setup(self):
        """Test that execute fails without setup."""
        with self.assertRaises(RuntimeError) as context:
            self.implementation.execute()

        self.assertIn('Setup must be completed', str(context.exception))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_execute_success(self):
        """Test successful execution."""
        self.implementation.setup()
        results = self.implementation.execute()

        # Verify results structure
        self.assertIsNotNone(results)
        self.assertIn('success', results)
        self.assertTrue(results['success'])
        self.assertIn('execution_time', results)
        self.assertGreater(results['execution_time'], 0)

        # Verify drift-specific results
        self.assertIn('drift_results', results)
        self.assertIn('reference_data_shape', results)
        self.assertIn('current_data_shape', results)
        self.assertIn('features_monitored', results)

        # Verify drift results structure
        drift_results = results['drift_results']
        self.assertIn('timestamp', drift_results)
        self.assertIn('features', drift_results)
        self.assertIn('alerts', drift_results)
        self.assertIn('summary', drift_results)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_generate_demo_data(self):
        """Test demo data generation."""
        n_samples = 100
        data = self.implementation._generate_demo_data(n_samples, seed=42)

        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), n_samples)
        self.assertGreater(len(data.columns), 0)

        # Check for expected columns
        expected_cols = ['team_score', 'field_goal_pct', 'home_away']
        for col in expected_cols:
            self.assertIn(col, data.columns)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_generate_demo_data_reproducibility(self):
        """Test that demo data generation is reproducible with same seed."""
        data1 = self.implementation._generate_demo_data(100, seed=42)
        data2 = self.implementation._generate_demo_data(100, seed=42)

        # Should be identical with same seed
        pd.testing.assert_frame_equal(data1, data2)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_psi_no_drift(self):
        """Test PSI calculation with no drift."""
        # Same distribution
        reference = np.random.normal(0, 1, 1000)
        current = np.random.normal(0, 1, 1000)

        psi = self.implementation.calculate_psi(reference, current)

        # PSI should be low (< 0.1 typically for same distribution)
        self.assertIsInstance(psi, float)
        self.assertGreaterEqual(psi, 0)
        self.assertLess(psi, 0.3)  # Allow some variance

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_psi_with_drift(self):
        """Test PSI calculation with drift."""
        # Different distributions
        reference = np.random.normal(0, 1, 1000)
        current = np.random.normal(5, 1, 1000)  # Mean shift

        psi = self.implementation.calculate_psi(reference, current)

        # PSI should be high (> 0.2 for significant drift)
        self.assertGreater(psi, 0.2)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_ks_test_no_drift(self):
        """Test KS test with no drift."""
        reference = np.random.normal(0, 1, 1000)
        current = np.random.normal(0, 1, 1000)

        ks_stat, pvalue = self.implementation.calculate_ks_test(reference, current)

        self.assertIsInstance(ks_stat, float)
        self.assertIsInstance(pvalue, float)
        self.assertGreaterEqual(ks_stat, 0)
        self.assertLessEqual(ks_stat, 1)
        # High p-value indicates same distribution
        self.assertGreater(pvalue, 0.05)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_ks_test_with_drift(self):
        """Test KS test with drift."""
        reference = np.random.normal(0, 1, 1000)
        current = np.random.normal(3, 1, 1000)  # Mean shift

        ks_stat, pvalue = self.implementation.calculate_ks_test(reference, current)

        # Should detect significant difference
        self.assertGreater(ks_stat, 0.1)
        self.assertLess(pvalue, 0.001)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_chi_squared_no_drift(self):
        """Test Chi-squared test with no drift."""
        # Same categorical distribution
        categories = ['A', 'B', 'C']
        reference = pd.Series(np.random.choice(categories, 1000))
        current = pd.Series(np.random.choice(categories, 1000))

        chi2, pvalue = self.implementation.calculate_chi_squared(reference, current)

        self.assertIsInstance(chi2, float)
        self.assertIsInstance(pvalue, float)
        self.assertGreaterEqual(chi2, 0)
        # High p-value indicates same distribution
        self.assertGreater(pvalue, 0.05)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_chi_squared_with_drift(self):
        """Test Chi-squared test with drift."""
        # Different categorical distributions
        reference = pd.Series(np.random.choice(['A', 'B', 'C'], 1000, p=[0.6, 0.3, 0.1]))
        current = pd.Series(np.random.choice(['A', 'B', 'C'], 1000, p=[0.1, 0.3, 0.6]))

        chi2, pvalue = self.implementation.calculate_chi_squared(reference, current)

        # Should detect significant difference
        self.assertGreater(chi2, 10)
        self.assertLess(pvalue, 0.001)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_wasserstein_distance(self):
        """Test Wasserstein distance calculation."""
        reference = np.random.normal(0, 1, 1000)
        current = np.random.normal(2, 1, 1000)

        distance = self.implementation.calculate_wasserstein_distance(reference, current)

        self.assertIsInstance(distance, float)
        self.assertGreaterEqual(distance, 0)
        # Should be non-zero for different distributions
        self.assertGreater(distance, 0.5)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_calculate_jensen_shannon_divergence(self):
        """Test Jensen-Shannon divergence calculation."""
        reference = np.random.normal(0, 1, 1000)
        current = np.random.normal(0, 1, 1000)

        js_div = self.implementation.calculate_jensen_shannon_divergence(reference, current)

        self.assertIsInstance(js_div, float)
        self.assertGreaterEqual(js_div, 0)
        self.assertLessEqual(js_div, 1)
        # Should be small for similar distributions
        self.assertLess(js_div, 0.5)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_detect_drift_without_setup(self):
        """Test drift detection fails without setup."""
        current_data = pd.DataFrame({'col1': [1, 2, 3]})

        with self.assertRaises(RuntimeError):
            self.implementation.detect_drift(current_data)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_detect_drift_no_drift(self):
        """Test drift detection with no drift."""
        self.implementation.setup()

        # Use same distribution as reference
        current_data = self.implementation._generate_demo_data(500, seed=42)

        results = self.implementation.detect_drift(current_data)

        self.assertIn('summary', results)
        self.assertEqual(results['summary']['overall_drift_detected'], False)
        self.assertEqual(results['summary']['features_with_drift'], 0)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_detect_drift_with_drift(self):
        """Test drift detection with intentional drift."""
        self.implementation.setup()

        # Create data with drift
        current_data = self.implementation._generate_demo_data(500, seed=99)
        current_data['team_score'] = current_data['team_score'] + 20  # Large shift

        results = self.implementation.detect_drift(current_data)

        self.assertIn('summary', results)
        self.assertTrue(results['summary']['overall_drift_detected'])
        self.assertGreater(results['summary']['features_with_drift'], 0)

        # Check that team_score shows drift
        self.assertIn('team_score', results['features'])
        self.assertTrue(results['features']['team_score']['drift_detected'])

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_cleanup(self):
        """Test cleanup process."""
        self.implementation.setup()

        # Store reference to check cleanup
        self.assertIsNotNone(self.implementation.reference_data)

        # Cleanup should not raise errors
        self.implementation.cleanup()

        # Reference data should be cleared
        self.assertIsNone(self.implementation.reference_data)


class TestDataDriftDetectionIntegration(unittest.TestCase):
    """Integration tests for DataDriftDetection."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.config = {
            'alert_threshold_psi': 0.15,  # More sensitive
            'alert_threshold_ks': 0.08,
        }
        self.implementation = DataDriftDetection(self.config)

    def tearDown(self):
        """Clean up after integration tests."""
        self.implementation.cleanup()

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # 1. Validate prerequisites
        prereqs = self.implementation.validate_prerequisites()
        self.assertTrue(prereqs, "Prerequisites should be valid")

        # 2. Setup
        setup_result = self.implementation.setup()
        self.assertTrue(setup_result, "Setup should succeed")
        self.assertTrue(self.implementation.setup_complete)

        # 3. Execute (creates reference, generates drift, detects)
        exec_result = self.implementation.execute()
        self.assertTrue(exec_result['success'], "Execution should succeed")

        # Verify execution results
        self.assertIn('drift_results', exec_result)
        drift_results = exec_result['drift_results']
        self.assertIn('summary', drift_results)

        # Should detect some drift (intentional in execute())
        self.assertTrue(drift_results['summary']['overall_drift_detected'])

        # 4. Cleanup
        self.implementation.cleanup()

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_multiple_drift_detections(self):
        """Test running drift detection multiple times."""
        self.implementation.setup()

        # Run detection multiple times
        results = []
        for i in range(3):
            current_data = self.implementation._generate_demo_data(200, seed=100+i)
            result = self.implementation.detect_drift(current_data)
            results.append(result)

        # All should succeed
        for result in results:
            self.assertIn('summary', result)
            self.assertIn('features', result)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_custom_thresholds_affect_detection(self):
        """Test that custom thresholds affect drift detection."""
        # Very lenient thresholds
        lenient_config = {
            'alert_threshold_psi': 0.5,
            'alert_threshold_ks': 0.5,
        }
        lenient_impl = DataDriftDetection(lenient_config)
        lenient_impl.setup()

        # Very strict thresholds
        strict_config = {
            'alert_threshold_psi': 0.05,
            'alert_threshold_ks': 0.02,
        }
        strict_impl = DataDriftDetection(strict_config)
        strict_impl.setup()

        # Same drift data
        drifted_data = lenient_impl._generate_demo_data(200, seed=99)
        drifted_data['team_score'] = drifted_data['team_score'] + 10

        lenient_results = lenient_impl.detect_drift(drifted_data)
        strict_results = strict_impl.detect_drift(drifted_data)

        # Strict should detect more drift
        self.assertGreaterEqual(
            strict_results['summary']['features_with_drift'],
            lenient_results['summary']['features_with_drift']
        )

        lenient_impl.cleanup()
        strict_impl.cleanup()

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_feature_specific_monitoring(self):
        """Test monitoring specific features only."""
        config = {
            'features_to_monitor': ['team_score', 'field_goal_pct']
        }
        impl = DataDriftDetection(config)
        impl.setup()

        # Only specified features should be monitored
        self.assertEqual(len(impl.features_to_monitor), 2)
        self.assertIn('team_score', impl.features_to_monitor)
        self.assertIn('field_goal_pct', impl.features_to_monitor)

        impl.cleanup()

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy/numpy/pandas not installed")
    def test_categorical_and_numerical_features(self):
        """Test that both categorical and numerical features are detected."""
        self.implementation.setup()

        # Create drift in both types
        current_data = self.implementation._generate_demo_data(500, seed=99)
        current_data['team_score'] = current_data['team_score'] + 20  # Numerical drift
        current_data['home_away'] = np.random.choice(['home', 'away'], 500, p=[0.9, 0.1])  # Categorical drift

        results = self.implementation.detect_drift(current_data)

        # Both should show drift
        self.assertTrue(results['features']['team_score']['drift_detected'])
        self.assertTrue(results['features']['home_away']['drift_detected'])

        # Check different metrics used
        self.assertIn('psi', results['features']['team_score'])
        self.assertIn('chi2_statistic', results['features']['home_away'])


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataDriftDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestDataDriftDetectionIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
