"""
DIMS (Data Inventory Management System) Module

Comprehensive data inventory tracking and verification system.

Features:
- Metric tracking and verification
- PostgreSQL backend for history
- TTL-based caching
- Event-driven updates
- Approval workflows
- Output generation

Created: November 5, 2025
Migrated from: scripts/monitoring/dims/
"""

from .core import DIMSCore

__all__ = ["DIMSCore"]

# Additional imports available when database is enabled
try:
    from .database import DatabaseBackend

    __all__.append("DatabaseBackend")
except ImportError:
    pass

try:
    from .cache import DIMSCache

    __all__.append("DIMSCache")
except ImportError:
    pass

try:
    from .events import EventHandler

    __all__.append("EventHandler")
except ImportError:
    pass
