"""
ADCE - Autonomous Data Collection Ecosystem

Migrated from scripts/autonomous/ and scripts/reconciliation/ during Phase 6 refactoring.

The ADCE system provides 24/7 self-healing data collection with:
- Autonomous loop controller for orchestration
- Gap detection engine for identifying missing data
- Reconciliation daemon for continuous monitoring
- Health monitoring and status reporting

Components:
- AutonomousLoop: Master controller for 24/7 operation
- GapDetector: Identifies and prioritizes data gaps
- ReconciliationDaemon: Automated reconciliation scheduler

Usage:
    from nba_simulator.adce import AutonomousLoop, GapDetector, ReconciliationDaemon
    
    # Start autonomous loop
    loop = AutonomousLoop(config_file="config/autonomous_config.yaml")
    loop.start()
    
    # Or use components individually
    detector = GapDetector(coverage_analysis_file="inventory/cache/coverage_analysis.json")
    gaps = detector.detect_gaps()
"""

from .autonomous_loop import AutonomousLoop
from .gap_detector import GapDetector, Priority
from .reconciliation import ReconciliationDaemon

__all__ = [
    'AutonomousLoop',
    'GapDetector',
    'Priority',
    'ReconciliationDaemon',
]
