"""
NBA Data Inventory Management System (DIMS)
Version: 1.0.0

A comprehensive system for managing, verifying, and updating data inventory metrics.
"""

__version__ = "1.0.0"
__author__ = "NBA Simulator Project"

from . import core
from . import cache
from . import outputs

__all__ = ['core', 'cache', 'outputs']
