"""
DIMS Approval Module - Approval Workflow

Provides approval workflow for metric changes above thresholds.

Features:
- Approval requirement detection
- Multi-level approval workflows
- Approval tracking and auditing
- Notification integration

Based on: scripts/monitoring/dims/approval.py
"""

import logging
from typing import Dict, Any, Optional

from ...utils import setup_logging


class DIMSApproval:
    """
    Approval workflow for metric changes.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        database: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize DIMS approval workflow.
        
        Args:
            config: DIMS configuration
            database: Optional database backend
            logger: Optional logger instance
        """
        self.config = config
        self.database = database
        self.logger = logger or setup_logging('nba_simulator.monitoring.dims.approval')
        
        # Approval thresholds
        self.approval_thresholds = config.get('approval', {}).get('thresholds', {})
        
        self.logger.info("DIMS Approval initialized")
    
    def requires_approval(
        self,
        metric_category: str,
        metric_name: str,
        drift_pct: Optional[float],
        severity: str
    ) -> bool:
        """
        Check if metric change requires approval.
        
        Args:
            metric_category: Metric category
            metric_name: Metric name
            drift_pct: Drift percentage
            severity: Severity level
            
        Returns:
            True if approval required
        """
        # Check if approvals enabled
        if not self.config.get('features', {}).get('approval_workflow', False):
            return False
        
        # Check drift threshold
        min_drift_for_approval = self.approval_thresholds.get('min_drift_pct', 25)
        if drift_pct and drift_pct >= min_drift_for_approval:
            return True
        
        # Check severity
        if severity in ('high', 'critical'):
            return True
        
        # Check if metric is in critical list
        critical_metrics = self.config.get('approval', {}).get('critical_metrics', [])
        if f"{metric_category}.{metric_name}" in critical_metrics:
            return True
        
        return False
    
    def request_approval(
        self,
        metric_category: str,
        metric_name: str,
        old_value: Any,
        new_value: Any,
        drift_pct: Optional[float],
        severity: str,
        requester: str = 'dims'
    ) -> bool:
        """
        Request approval for metric change.
        
        Args:
            metric_category: Metric category
            metric_name: Metric name
            old_value: Old value
            new_value: New value
            drift_pct: Drift percentage
            severity: Severity level
            requester: Who is requesting approval
            
        Returns:
            True if approval request created
        """
        self.logger.info(
            f"Approval requested for {metric_category}.{metric_name}: "
            f"{old_value} → {new_value}"
        )
        
        if self.database:
            # Log approval request
            self.database.create_approval_request(
                metric_category=metric_category,
                metric_name=metric_name,
                old_value=old_value,
                new_value=new_value,
                drift_pct=drift_pct,
                severity=severity,
                requester=requester
            )
        
        return True
