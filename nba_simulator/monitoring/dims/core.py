"""
DIMS Core Module - Data Inventory Management System

Handles all metric CRUD operations, verification, and command execution.
Integrated with nba_simulator package infrastructure.

Features:
- Automated metric calculation via shell commands
- Drift detection with configurable thresholds
- Historical tracking and snapshots
- Database backend for persistence
- Event-driven updates
- Approval workflows

Based on: scripts/monitoring/dims/core.py
Enhanced with better integration and error handling.
"""

import os
import yaml
import subprocess
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ...database import get_db_connection, execute_query
from ...utils import setup_logging


class MetricStatus(Enum):
    """Metric verification status"""
    OK = "ok"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    ERROR = "error"
    NEW = "new"
    DIFFERENT = "different"


class MetricSeverity(Enum):
    """Metric drift severity"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricVerificationResult:
    """Result of a metric verification"""
    metric: str
    documented: Any
    actual: Any
    drift: Any
    drift_pct: Optional[float]
    status: MetricStatus
    severity: MetricSeverity
    message: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metric': self.metric,
            'documented': self.documented,
            'actual': self.actual,
            'drift': self.drift,
            'drift_pct': self.drift_pct,
            'status': self.status.value,
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }


class DIMSCore:
    """
    Core class for Data Inventory Management System operations.
    
    Manages metrics verification, calculation, and tracking.
    """
    
    def __init__(
        self,
        project_root: Optional[str] = None,
        config_path: Optional[str] = None,
        metrics_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize DIMS Core.
        
        Args:
            project_root: Path to project root. If None, auto-detects.
            config_path: Path to config.yaml. If None, uses default.
            metrics_path: Path to metrics.yaml. If None, uses default.
            logger: Optional logger instance.
        """
        # Setup logging
        if logger:
            self.logger = logger
        else:
            self.logger = setup_logging('nba_simulator.monitoring.dims')
        
        # Detect project root
        if project_root is None:
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / 'inventory').exists():
                    project_root = str(current)
                    break
                current = current.parent
        
        self.project_root = Path(project_root or os.getcwd())
        
        # Set paths
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self.project_root / 'inventory' / 'config.yaml'
        
        if metrics_path:
            self.metrics_path = Path(metrics_path)
        else:
            self.metrics_path = self.project_root / 'inventory' / 'metrics.yaml'
        
        # Load configuration and metrics
        self.config = self._load_config()
        self.metrics = self._load_metrics()
        
        # Initialize optional modules
        self.database = None
        self.cache = None
        self.events = None
        self.approval = None
        
        self._initialize_features()
        
        self.logger.info(f"DIMS Core initialized for {self.project_root}")
    
    def _initialize_features(self):
        """Initialize optional features based on configuration"""
        features = self.config.get('features', {})
        
        # Database backend
        if features.get('database_backend', False):
            try:
                from .database import DIMSDatabase
                self.database = DIMSDatabase()
                self.logger.info("Database backend enabled")
            except Exception as e:
                self.logger.warning(f"Database backend failed to initialize: {e}")
        
        # Cache layer
        if features.get('cache', {}).get('enabled', False):
            try:
                from .cache import DIMSCache
                cache_config = self.config.get('cache', {})
                self.cache = DIMSCache(cache_config)
                self.logger.info("Cache layer enabled")
            except Exception as e:
                self.logger.warning(f"Cache failed to initialize: {e}")
        
        # Event handler
        if features.get('event_driven', False):
            try:
                from .events import DIMSEvents
                self.events = DIMSEvents(self.config, self.database)
                self.logger.info("Event handler enabled")
            except Exception as e:
                self.logger.warning(f"Event handler failed to initialize: {e}")
        
        # Approval workflow
        if features.get('approval_workflow', False):
            try:
                from .approval import DIMSApproval
                self.approval = DIMSApproval(self.config, self.database)
                self.logger.info("Approval workflow enabled")
            except Exception as e:
                self.logger.warning(f"Approval workflow failed to initialize: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            raise
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from metrics.yaml"""
        if not self.metrics_path.exists():
            self.logger.warning(f"Metrics file not found: {self.metrics_path}")
            return {'metadata': {}}
        
        try:
            with open(self.metrics_path, 'r') as f:
                metrics = yaml.safe_load(f)
            
            self.logger.info(f"Loaded metrics from {self.metrics_path}")
            return metrics or {'metadata': {}}
        except Exception as e:
            self.logger.error(f"Failed to load metrics: {e}")
            return {'metadata': {}}
    
    def save_metrics(self, metrics: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save metrics to metrics.yaml.
        
        Args:
            metrics: Metrics dict to save. If None, saves current self.metrics.
            
        Returns:
            True if successful, False otherwise
        """
        if metrics is None:
            metrics = self.metrics
        
        try:
            # Update metadata
            if 'metadata' not in metrics:
                metrics['metadata'] = {}
            
            metrics['metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()
            metrics['metadata']['version'] = self.config.get('version', '1.0.0')
            
            # Create backup
            if self.metrics_path.exists():
                backup_path = self.metrics_path.with_suffix('.yaml.bak')
                import shutil
                shutil.copy2(self.metrics_path, backup_path)
            
            # Write to file
            with open(self.metrics_path, 'w') as f:
                yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)
            
            self.logger.info(f"Saved metrics to {self.metrics_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
            return False
    
    def execute_command(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Execute a shell command and return its output.
        
        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds
            cwd: Working directory (defaults to project_root)
            
        Returns:
            Tuple of (success: bool, output: Optional[str])
        """
        if cwd is None:
            cwd = str(self.project_root)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return (True, output)
            else:
                self.logger.error(f"Command failed: {command}")
                self.logger.error(f"Error: {result.stderr}")
                return (False, None)
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout}s: {command}")
            return (False, None)
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            return (False, None)
    
    def get_metric_value(
        self,
        metric_path: str,
        use_cache: bool = True
    ) -> Optional[Any]:
        """
        Get current value of a metric from metrics.yaml.
        
        Args:
            metric_path: Dot-separated path to metric (e.g., 's3_storage.total_objects')
            use_cache: Whether to use cached value
            
        Returns:
            Metric value or None if not found
        """
        # Check cache first if enabled
        if use_cache and self.cache:
            cached_value = self.cache.get(metric_path)
            if cached_value is not None:
                return cached_value
        
        # Navigate to metric in YAML
        parts = metric_path.split('.')
        current = self.metrics
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        # Extract value if it's in standard format
        if isinstance(current, dict) and 'value' in current:
            value = current['value']
        else:
            value = current
        
        # Cache if enabled
        if use_cache and self.cache:
            self.cache.set(metric_path, value)
        
        return value
    
    def calculate_metric(
        self,
        metric_category: str,
        metric_name: str
    ) -> Optional[Any]:
        """
        Calculate current value of a metric by executing its command.
        
        Args:
            metric_category: Metric category (e.g., 's3_storage')
            metric_name: Metric name (e.g., 'total_objects')
            
        Returns:
            Calculated value or None if calculation failed
        """
        # Get metric definition from config
        metric_def = self.config.get('metrics', {}).get(metric_category, {}).get(metric_name)
        
        if not metric_def:
            self.logger.error(f"Metric definition not found: {metric_category}.{metric_name}")
            return None
        
        # Check if metric is enabled
        if not metric_def.get('enabled', True):
            self.logger.debug(f"Metric disabled: {metric_category}.{metric_name}")
            return None
        
        # Get command
        command = metric_def.get('command')
        if not command:
            self.logger.error(f"No command defined for metric: {metric_category}.{metric_name}")
            return None
        
        # Execute command
        timeout = metric_def.get('timeout', 30)
        success, output = self.execute_command(command, timeout=timeout)
        
        if not success or output is None:
            return None
        
        # Parse output based on parse_type
        parse_type = metric_def.get('parse_type', 'string')
        
        try:
            if parse_type == 'integer':
                return int(output)
            elif parse_type == 'float':
                precision = metric_def.get('precision', 2)
                return round(float(output), precision)
            elif parse_type == 'string':
                return output
            elif parse_type == 'boolean':
                return output.lower() in ('true', 'yes', '1')
            else:
                return output
        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse output '{output}' as {parse_type}: {e}")
            return None
    
    def update_metric(
        self,
        metric_category: str,
        metric_name: str,
        new_value: Any,
        verification_method: str = 'automated',
        verified_by: str = 'dims_core'
    ) -> bool:
        """
        Update a metric value in metrics.yaml (and database if enabled).
        
        Args:
            metric_category: Metric category
            metric_name: Metric name
            new_value: New value to set
            verification_method: How the value was verified
            verified_by: Who/what verified the value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Navigate to metric location
            if metric_category not in self.metrics:
                self.metrics[metric_category] = {}
            
            if metric_name not in self.metrics[metric_category]:
                self.metrics[metric_category][metric_name] = {}
            
            metric = self.metrics[metric_category][metric_name]
            
            # Store old value for logging
            old_value = metric.get('value') if isinstance(metric, dict) else metric
            
            # Update metric in YAML
            if isinstance(metric, dict):
                metric['value'] = new_value
                metric['last_verified'] = datetime.now(timezone.utc).isoformat()
                metric['verification_method'] = verification_method
                metric['verified_by'] = verified_by
                metric['cached'] = False
                metric['cache_expires'] = None
            else:
                # Create new metric structure
                self.metrics[metric_category][metric_name] = {
                    'value': new_value,
                    'last_verified': datetime.now(timezone.utc).isoformat(),
                    'verification_method': verification_method,
                    'verified_by': verified_by,
                    'cached': False,
                    'cache_expires': None
                }
            
            self.logger.info(
                f"Updated metric {metric_category}.{metric_name}: "
                f"{old_value} → {new_value}"
            )
            
            # Save to YAML
            self.save_metrics()
            
            # Also save to database if enabled
            if self.database:
                # Determine value type
                value_type = 'string'
                if isinstance(new_value, bool):
                    value_type = 'boolean'
                elif isinstance(new_value, int):
                    value_type = 'integer'
                elif isinstance(new_value, float):
                    value_type = 'float'
                
                self.database.save_metric(
                    metric_category=metric_category,
                    metric_name=metric_name,
                    value=new_value,
                    value_type=value_type,
                    verification_method=verification_method,
                    verified_by=verified_by
                )
            
            # Clear cache if enabled
            if self.cache:
                self.cache.invalidate(f"{metric_category}.{metric_name}")
            
            # Emit event if enabled
            if self.events:
                self.events.emit('metric_updated', {
                    'category': metric_category,
                    'name': metric_name,
                    'old_value': old_value,
                    'new_value': new_value
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update metric: {e}")
            return False
    
    def verify_metric(
        self,
        metric_category: str,
        metric_name: str
    ) -> MetricVerificationResult:
        """
        Verify a single metric by comparing documented vs actual value.
        
        Args:
            metric_category: Metric category
            metric_name: Metric name
            
        Returns:
            MetricVerificationResult with comparison details
        """
        metric_path = f"{metric_category}.{metric_name}"
        
        # Get documented value
        documented = self.get_metric_value(metric_path)
        
        # Calculate actual value
        actual = self.calculate_metric(metric_category, metric_name)
        
        # Handle errors
        if actual is None:
            return MetricVerificationResult(
                metric=metric_path,
                documented=documented,
                actual=None,
                drift=None,
                drift_pct=None,
                status=MetricStatus.ERROR,
                severity=MetricSeverity.HIGH,
                message='Failed to calculate actual value'
            )
        
        if documented is None:
            return MetricVerificationResult(
                metric=metric_path,
                documented=None,
                actual=actual,
                drift=None,
                drift_pct=None,
                status=MetricStatus.NEW,
                severity=MetricSeverity.LOW,
                message='No documented value found (new metric)'
            )
        
        # Calculate drift for numeric values
        if isinstance(documented, (int, float)) and isinstance(actual, (int, float)):
            drift = actual - documented
            drift_pct = abs((drift / documented) * 100) if documented != 0 else (0 if drift == 0 else 100)
            
            # Get thresholds
            thresholds = self.config.get('verification', {}).get('thresholds', {})
            minor_threshold = thresholds.get('minor_drift_pct', 5)
            moderate_threshold = thresholds.get('moderate_drift_pct', 15)
            major_threshold = thresholds.get('major_drift_pct', 25)
            
            # Determine status and severity
            if drift == 0:
                status = MetricStatus.OK
                severity = MetricSeverity.NONE
                message = 'Values match exactly'
            elif drift_pct < minor_threshold:
                status = MetricStatus.MINOR
                severity = MetricSeverity.LOW
                message = f'Minor drift: {drift_pct:.1f}%'
            elif drift_pct < moderate_threshold:
                status = MetricStatus.MODERATE
                severity = MetricSeverity.MEDIUM
                message = f'Moderate drift: {drift_pct:.1f}%'
            else:
                status = MetricStatus.MAJOR
                severity = MetricSeverity.HIGH
                message = f'Major drift: {drift_pct:.1f}%'
            
            return MetricVerificationResult(
                metric=metric_path,
                documented=documented,
                actual=actual,
                drift=drift,
                drift_pct=round(drift_pct, 2),
                status=status,
                severity=severity,
                message=message
            )
        
        # Non-numeric comparison
        if documented == actual:
            status = MetricStatus.OK
            severity = MetricSeverity.NONE
            message = 'Values match'
        else:
            status = MetricStatus.DIFFERENT
            severity = MetricSeverity.MEDIUM
            message = 'Values differ'
        
        return MetricVerificationResult(
            metric=metric_path,
            documented=documented,
            actual=actual,
            drift=f"{documented} → {actual}",
            drift_pct=None,
            status=status,
            severity=severity,
            message=message
        )
    
    def verify_all_metrics(
        self,
        triggered_by: str = 'manual'
    ) -> Dict[str, Any]:
        """
        Verify all metrics defined in config.
        
        Args:
            triggered_by: What triggered this verification
            
        Returns:
            Dict with verification results
        """
        start_time = datetime.now(timezone.utc)
        
        results = {
            'timestamp': start_time.isoformat(),
            'total_metrics': 0,
            'verified': 0,
            'drift_detected': False,
            'discrepancies': [],
            'approvals_required': [],
            'summary': {status.value: 0 for status in MetricStatus}
        }
        
        metrics_config = self.config.get('metrics', {})
        
        for category, metrics in metrics_config.items():
            for metric_name, metric_def in metrics.items():
                results['total_metrics'] += 1
                
                # Skip if disabled
                if not metric_def.get('enabled', True):
                    continue
                
                self.logger.debug(f"Verifying {category}.{metric_name}...")
                
                verification = self.verify_metric(category, metric_name)
                results['verified'] += 1
                
                # Update summary
                results['summary'][verification.status.value] += 1
                
                # Add to discrepancies if not OK
                if verification.status != MetricStatus.OK:
                    results['discrepancies'].append(verification.to_dict())
                
                if verification.status in (MetricStatus.MINOR, MetricStatus.MODERATE, MetricStatus.MAJOR):
                    results['drift_detected'] = True
                    
                    # Check if approval required
                    if self.approval and self.approval.requires_approval(
                        category, metric_name,
                        verification.drift_pct,
                        verification.severity.value
                    ):
                        results['approvals_required'].append(verification.to_dict())
        
        execution_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        results['execution_time_ms'] = execution_time_ms
        
        self.logger.info(
            f"Verification complete: {results['verified']}/{results['total_metrics']} metrics "
            f"verified in {execution_time_ms}ms"
        )
        
        # Save to database if enabled
        if self.database:
            run_id = self.database.save_verification_run(
                results=results,
                triggered_by=triggered_by,
                execution_time_ms=execution_time_ms
            )
            results['verification_run_id'] = run_id
        
        return results
    
    def get_metric_history(
        self,
        metric_path: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical values of a metric.
        
        Args:
            metric_path: Dot-separated metric path
            days: Number of days to look back
            
        Returns:
            List of {date: str, value: Any} dicts
        """
        # Try database first if available
        if self.database:
            return self.database.get_metric_history(metric_path, days)
        
        # Fall back to file-based history
        history = []
        historical_dir = self.project_root / 'inventory' / 'historical'
        
        if not historical_dir.exists():
            return history
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for snapshot_file in sorted(historical_dir.glob('*.yaml')):
            try:
                date_str = snapshot_file.stem
                snapshot_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if snapshot_date < cutoff_date:
                    continue
                
                with open(snapshot_file, 'r') as f:
                    snapshot = yaml.safe_load(f)
                
                # Extract metric value
                parts = metric_path.split('.')
                current = snapshot
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break
                
                if current is not None:
                    if isinstance(current, dict) and 'value' in current:
                        value = current['value']
                    else:
                        value = current
                    
                    history.append({
                        'date': date_str,
                        'value': value
                    })
                    
            except Exception as e:
                self.logger.warning(f"Error reading snapshot {snapshot_file}: {e}")
                continue
        
        return history
    
    def create_snapshot(self) -> bool:
        """
        Create a snapshot of current metrics.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            historical_dir = self.project_root / 'inventory' / 'historical'
            historical_dir.mkdir(parents=True, exist_ok=True)
            
            today = datetime.now()
            snapshot_file = historical_dir / f"{today.strftime('%Y-%m-%d')}.yaml"
            
            # Write current metrics to file
            with open(snapshot_file, 'w') as f:
                yaml.dump(self.metrics, f, default_flow_style=False, sort_keys=False)
            
            self.logger.info(f"Created snapshot: {snapshot_file}")
            
            # Also save to database if enabled
            if self.database:
                self.database.save_snapshot(today, self.metrics)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create snapshot: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get DIMS system information.
        
        Returns:
            Dict with system info
        """
        return {
            'version': self.config.get('version', 'unknown'),
            'system_name': self.config.get('system_name', 'DIMS'),
            'project_root': str(self.project_root),
            'config_path': str(self.config_path),
            'metrics_path': str(self.metrics_path),
            'features': {
                'database_backend': self.database is not None,
                'cache': self.cache is not None,
                'events': self.events is not None,
                'approval': self.approval is not None
            },
            'total_metrics_defined': sum(
                len(metrics) for metrics in self.config.get('metrics', {}).values()
            ),
            'total_metrics_documented': len(self.metrics) - 1  # Exclude metadata
        }
