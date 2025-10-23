"""
Tests for Phase 2.0

Auto-generated test template.

Usage:
    pytest tests/phases/phase_2/test_2_0.py -v
"""

import pytest
import sys
from pathlib import Path

# Import validator
validators_path = (
    Path(__file__).parent.parent.parent.parent / "validators" / "phases" / f"phase_2"
)
sys.path.insert(0, str(validators_path))

from validate_2_0 import Phase20Validator


class TestPhase20Validation:
    """Tests for Phase 2.0 validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return Phase20Validator(verbose=False)

    def test_feature_1_validation(self, validator):
        """Test feature 1 validation."""
        assert (
            validator.validate_feature_1() == True
        ), f"Feature 1 failed: {validator.failures}"

    def test_feature_2_validation(self, validator):
        """Test feature 2 validation."""
        assert (
            validator.validate_feature_2() == True
        ), f"Feature 2 failed: {validator.failures}"

    def test_all_validations(self, validator):
        """Test all validations pass."""
        all_passed, results = validator.run_all_validations()
        assert all_passed == True, f"Not all validations passed: {results}"


class TestPhase20Integration:
    """Integration tests for Phase 2.0."""

    def test_phase_complete_validation(self):
        """Comprehensive phase completion test."""
        validator = Phase20Validator(verbose=False)
        all_passed, results = validator.run_all_validations()

        assert all_passed == True, "Phase 2.0 validation failed"
        assert results["feature_1_valid"] == True
        assert results["feature_2_valid"] == True
