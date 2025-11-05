"""
DIMS (Data Inventory Management System) Module

Comprehensive data inventory tracking and verification system:
- Automated metric verification
- Historical tracking
- Drift detection
- Alert management
- Database backend integration

Components:
- DIMSCore: Core verification and metric management
- DIMSCache: Intelligent caching layer
- DIMSDatabase: PostgreSQL backend for historical data
- DIMSEvents: Event-driven metric updates
- DIMSApproval: Approval workflow for metric changes

Usage:
    from nba_simulator.monitoring.dims import DIMS
    
    dims = DIMS()
    
    # Verify all metrics
    results = dims.verify_all_metrics()
    
    # Update specific metric
    dims.update_metric('s3_storage', 'total_objects', 146115)
    
    # Get metric history
    history = dims.get_metric_history('s3_storage.total_objects', days=30)
"""

from .core import DIMSCore
from .cache import DIMSCache
from .database import DIMSDatabase
from .events import DIMSEvents
from .approval import DIMSApproval
from .outputs import DIMSOutputManager, MarkdownGenerator, JSONGenerator
from .workflows import WorkflowIntegration

# Convenience alias
DIMS = DIMSCore

__all__ = [
    'DIMS',
    'DIMSCore',
    'DIMSCache',
    'DIMSDatabase',
    'DIMSEvents',
    'DIMSApproval',
    'DIMSOutputManager',
    'MarkdownGenerator',
    'JSONGenerator',
    'WorkflowIntegration',
]
