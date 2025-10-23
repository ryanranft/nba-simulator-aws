#!/usr/bin/env python3
"""
Pytest configuration for Phase 0.1 tests.
"""

import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--bucket",
        action="store",
        default="nba-sim-raw-data-lake",
        help="S3 bucket name to test",
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
