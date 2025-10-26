"""
Tests for 1.0004

Auto-generated test template.

Usage:
    pytest tests/phases/phase_1/test_1_4.py -v
"""

import pytest
import sys
from pathlib import Path

# Import validator
validators_path = (
    Path(__file__).parent.parent.parent.parent / "validators" / "phases" / f"phase_1"
)
sys.path.insert(0, str(validators_path))

from validate_1_4 import Phase14Validator


class TestPhase14Validation:
    """Tests for 1.0004 validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return Phase14Validator(verbose=False)

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


class TestPhase14Integration:
    """Integration tests for 1.0004."""

    def test_phase_complete_validation(self):
        """Comprehensive phase completion test."""
        validator = Phase14Validator(verbose=False)
        all_passed, results = validator.run_all_validations()

        assert all_passed == True, "1.0004 validation failed"
        assert results["feature_1_valid"] == True
        assert results["feature_2_valid"] == True
