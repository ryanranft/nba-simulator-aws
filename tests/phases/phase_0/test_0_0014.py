"""
Tests for Phase 0.0014

Auto-generated test template.

Usage:
    pytest tests/phases/phase_0/test_0_0014.py -v
"""

import pytest
import sys
from pathlib import Path

# Import validator
validators_path = (
    Path(__file__).parent.parent.parent.parent / "validators" / "phases" / f"phase_0"
)
sys.path.insert(0, str(validators_path))

from validate_0_14 import Phase014Validator


class TestPhase014Validation:
    """Tests for Phase 0.0014 validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return Phase014Validator(verbose=False)

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


class TestPhase014Integration:
    """Integration tests for Phase 0.0014."""

    def test_phase_complete_validation(self):
        """Comprehensive phase completion test."""
        validator = Phase014Validator(verbose=False)
        all_passed, results = validator.run_all_validations()

        assert all_passed == True, "Phase 0.0014 validation failed"
        assert results["feature_1_valid"] == True
        assert results["feature_2_valid"] == True
