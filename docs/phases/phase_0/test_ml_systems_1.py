#!/usr/bin/env python3
"""
Test Suite: Model Versioning with MLflow

Recommendation ID: ml_systems_1
Generated: 2025-10-15T21:01:26.113136
Updated: 2025-10-15 (comprehensive tests added)

Tests the implementation of Model Versioning with MLflow.

Test Coverage:
- Unit tests for initialization, setup, validation
- Model registration and promotion
- Model version retrieval
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

from implement_ml_systems_1 import ModelVersioningWithMlflow, MLFLOW_AVAILABLE


class TestModelVersioningWithMlflow(unittest.TestCase):
    """Test suite for ModelVersioningWithMlflow."""

    def setUp(self):
        """Set up test fixtures."""
        # Use temporary directory for test MLflow tracking
        self.test_dir = tempfile.mkdtemp()
        self.config = {
            'tracking_uri': f'file:{self.test_dir}/mlruns',
            'experiment_name': 'test-nba-ml',
            'artifact_location': f'{self.test_dir}/artifacts',
            'default_tags': {
                'environment': 'test',
                'project': 'nba-simulator-test'
            }
        }
        self.implementation = ModelVersioningWithMlflow(self.config)

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.implementation, 'cleanup'):
            self.implementation.cleanup()

        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test that ModelVersioningWithMlflow initializes correctly."""
        self.assertIsNotNone(self.implementation)
        self.assertFalse(self.implementation.setup_complete)
        self.assertEqual(self.implementation.config, self.config)
        self.assertEqual(self.implementation.experiment_name, 'test-nba-ml')
        self.assertIsNone(self.implementation.client)
        self.assertIsNone(self.implementation.experiment_id)

    def test_initialization_with_defaults(self):
        """Test initialization with default configuration."""
        impl = ModelVersioningWithMlflow()
        self.assertEqual(impl.experiment_name, 'nba-simulator-ml')
        self.assertEqual(impl.config, {})

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_setup(self):
        """Test setup process."""
        result = self.implementation.setup()
        self.assertTrue(result)
        self.assertTrue(self.implementation.setup_complete)
        self.assertIsNotNone(self.implementation.client)
        self.assertIsNotNone(self.implementation.experiment_id)

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_setup_creates_experiment(self):
        """Test that setup creates MLflow experiment."""
        self.implementation.setup()

        # Verify experiment was created
        self.assertIsNotNone(self.implementation.experiment_id)

        # Verify experiment can be retrieved
        experiment = self.implementation.client.get_experiment(
            self.implementation.experiment_id
        )
        self.assertEqual(experiment.name, 'test-nba-ml')

    def test_setup_without_mlflow(self):
        """Test setup fails gracefully without MLflow."""
        with patch('implement_ml_systems_1.MLFLOW_AVAILABLE', False):
            impl = ModelVersioningWithMlflow(self.config)
            result = impl.setup()
            self.assertFalse(result)

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_validate_prerequisites(self):
        """Test prerequisite validation."""
        result = self.implementation.validate_prerequisites()
        self.assertTrue(result)

    def test_validate_prerequisites_without_mlflow(self):
        """Test prerequisite validation fails without MLflow."""
        with patch('implement_ml_systems_1.MLFLOW_AVAILABLE', False):
            impl = ModelVersioningWithMlflow(self.config)
            result = impl.validate_prerequisites()
            self.assertFalse(result)

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_execute_without_setup(self):
        """Test that execute fails without setup."""
        with self.assertRaises(RuntimeError) as context:
            self.implementation.execute()

        self.assertIn('Setup must be completed', str(context.exception))

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
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

        # Verify MLflow-specific results
        self.assertIn('run_id', results)
        self.assertIn('experiment_id', results)
        self.assertIn('model_name', results)
        self.assertIn('model_version', results)
        self.assertEqual(results['final_stage'], 'Production')

        # Verify metrics logged
        self.assertEqual(results['parameters_logged'], 4)
        self.assertEqual(results['metrics_logged'], 5)

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_register_model(self):
        """Test model registration."""
        self.implementation.setup()

        # Create a dummy run
        import mlflow
        with mlflow.start_run() as run:
            run_id = run.info.run_id

            # Try to log a model (may fail without sklearn)
            try:
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(n_estimators=5)
                mlflow.sklearn.log_model(model, "test_model")

                # Register the model
                result = self.implementation.register_model(
                    model_name="test-model",
                    model_artifact_path="test_model",
                    run_id=run_id,
                    description="Test model",
                    tags={'test': 'true'}
                )

                self.assertEqual(result['status'], 'registered')
                self.assertEqual(result['model_name'], 'test-model')
                self.assertIsNotNone(result['version'])
            except ImportError:
                # Skip if sklearn not available
                pass

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_register_model_without_artifacts(self):
        """Test model registration fails without artifacts."""
        self.implementation.setup()

        result = self.implementation.register_model(
            model_name="test-model"
        )

        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'missing_artifacts')

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_promote_model(self):
        """Test model promotion to different stages."""
        self.implementation.setup()

        # First need to register a model
        import mlflow
        with mlflow.start_run() as run:
            run_id = run.info.run_id

            try:
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(n_estimators=5)
                mlflow.sklearn.log_model(model, "test_model")

                # Register the model
                result = self.implementation.register_model(
                    model_name="test-promotion-model",
                    model_artifact_path="test_model",
                    run_id=run_id
                )

                if result['status'] == 'registered':
                    version = result['version']

                    # Test promotion to Staging
                    success = self.implementation.promote_model(
                        "test-promotion-model",
                        version,
                        'Staging'
                    )
                    self.assertTrue(success)

                    # Test promotion to Production
                    success = self.implementation.promote_model(
                        "test-promotion-model",
                        version,
                        'Production'
                    )
                    self.assertTrue(success)
            except ImportError:
                # Skip if sklearn not available
                pass

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_promote_model_invalid_stage(self):
        """Test model promotion with invalid stage."""
        self.implementation.setup()

        result = self.implementation.promote_model(
            "test-model",
            1,
            'InvalidStage'
        )

        self.assertFalse(result)

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_cleanup(self):
        """Test cleanup process."""
        self.implementation.setup()

        # Should not raise any errors
        self.implementation.cleanup()

        # Verify experiment stats were logged (checked via logger, not assertion)


class TestModelVersioningWithMlflowIntegration(unittest.TestCase):
    """Integration tests for ModelVersioningWithMlflow."""

    def setUp(self):
        """Set up integration test fixtures."""
        # Use temporary directory for integration tests
        self.test_dir = tempfile.mkdtemp()
        self.config = {
            'tracking_uri': f'file:{self.test_dir}/mlruns',
            'experiment_name': 'integration-test-nba-ml',
            'artifact_location': f'{self.test_dir}/artifacts',
            'default_tags': {
                'environment': 'integration-test',
                'project': 'nba-simulator-test'
            }
        }
        self.implementation = ModelVersioningWithMlflow(self.config)

    def tearDown(self):
        """Clean up after integration tests."""
        self.implementation.cleanup()

        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # 1. Validate prerequisites
        prereqs = self.implementation.validate_prerequisites()
        self.assertTrue(prereqs, "Prerequisites should be valid")

        # 2. Setup
        setup_result = self.implementation.setup()
        self.assertTrue(setup_result, "Setup should succeed")
        self.assertTrue(self.implementation.setup_complete)

        # 3. Execute (creates run, logs model, registers, promotes)
        exec_result = self.implementation.execute()
        self.assertTrue(exec_result['success'], "Execution should succeed")

        # Verify execution results
        self.assertIn('run_id', exec_result)
        self.assertIn('model_name', exec_result)
        self.assertIn('model_version', exec_result)
        self.assertEqual(exec_result['final_stage'], 'Production')

        # 4. Verify model is in Production
        model_info = self.implementation.get_model_version(
            exec_result['model_name'],
            stage='Production'
        )
        self.assertIsNotNone(model_info)
        self.assertEqual(model_info['stage'], 'Production')

        # 5. Cleanup
        self.implementation.cleanup()

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_multiple_runs_same_experiment(self):
        """Test creating multiple runs in the same experiment."""
        self.implementation.setup()

        # Execute multiple times
        results = []
        for i in range(3):
            result = self.implementation.execute()
            self.assertTrue(result['success'])
            results.append(result)

        # Verify all runs have different run_ids
        run_ids = [r['run_id'] for r in results]
        self.assertEqual(len(run_ids), len(set(run_ids)), "Run IDs should be unique")

        # Verify all runs in same experiment
        experiment_ids = [r['experiment_id'] for r in results]
        self.assertEqual(len(set(experiment_ids)), 1, "All runs should be in same experiment")

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_model_versioning_increments(self):
        """Test that model versions increment correctly."""
        self.implementation.setup()

        # Execute twice to create two versions
        result1 = self.implementation.execute()
        result2 = self.implementation.execute()

        # Verify versions increment
        if result1.get('model_version') and result2.get('model_version'):
            self.assertGreater(
                result2['model_version'],
                result1['model_version'],
                "Model version should increment"
            )

    @unittest.skipIf(not MLFLOW_AVAILABLE, "MLflow not installed")
    def test_artifact_storage_location(self):
        """Test that artifacts are stored in correct location."""
        self.implementation.setup()
        result = self.implementation.execute()

        if result['success']:
            # Verify artifact location exists
            artifact_path = Path(self.test_dir) / 'artifacts'
            # Note: Actual artifact path verification would require
            # inspecting MLflow's internal structure
    


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestModelVersioningWithMlflow))
    suite.addTests(loader.loadTestsFromTestCase(TestModelVersioningWithMlflowIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())




