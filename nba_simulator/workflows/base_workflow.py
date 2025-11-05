"""
Base Workflow - Abstract Base Class for All Workflows

Provides standard lifecycle, state management, and task execution for all NBA Simulator workflows.
All workflows must inherit from this class and implement required abstract methods.

Design Patterns:
- Template Method: Standard lifecycle with customizable hooks
- State Machine: Workflow state transitions with validation
- Strategy: Pluggable task execution strategies
- Memento: State persistence and recovery

Combines patterns from:
- BaseAgent: Lifecycle and state management
- DataDispatcher: Task execution and async support
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import json
import logging
import asyncio
from dataclasses import dataclass, asdict, field


from ..database import get_db_connection
from ..utils import setup_logging


class WorkflowState(Enum):
    """Workflow lifecycle states with transition validation"""

    CREATED = "created"  # Initial state
    INITIALIZED = "initialized"  # Configuration validated
    READY = "ready"  # Pre-execution checks passed
    RUNNING = "running"  # Actively executing
    PAUSED = "paused"  # Temporarily suspended
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"  # Execution failed
    CANCELLED = "cancelled"  # User cancelled
    SHUTDOWN = "shutdown"  # Cleanly shut down

    def can_transition_to(self, target_state: "WorkflowState") -> bool:
        """Validate if transition to target state is allowed"""
        valid_transitions = {
            WorkflowState.CREATED: [WorkflowState.INITIALIZED, WorkflowState.FAILED],
            WorkflowState.INITIALIZED: [WorkflowState.READY, WorkflowState.FAILED],
            WorkflowState.READY: [
                WorkflowState.RUNNING,
                WorkflowState.FAILED,
                WorkflowState.CANCELLED,
            ],
            WorkflowState.RUNNING: [
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
                WorkflowState.PAUSED,
                WorkflowState.CANCELLED,
            ],
            WorkflowState.PAUSED: [
                WorkflowState.RUNNING,
                WorkflowState.CANCELLED,
                WorkflowState.FAILED,
            ],
            WorkflowState.COMPLETED: [WorkflowState.SHUTDOWN],
            WorkflowState.FAILED: [WorkflowState.SHUTDOWN],
            WorkflowState.CANCELLED: [WorkflowState.SHUTDOWN],
        }
        return target_state in valid_transitions.get(self, [])


class WorkflowPriority(Enum):
    """Workflow execution priority levels"""

    CRITICAL = 1  # Immediate execution (e.g., live data collection)
    HIGH = 2  # High priority (e.g., daily updates)
    NORMAL = 3  # Normal priority (e.g., scheduled workflows)
    LOW = 4  # Low priority (e.g., backfill operations)
    BACKGROUND = 5  # Background processing


@dataclass
class WorkflowTask:
    """
    Represents a single task within a workflow.

    Workflows are composed of multiple tasks that execute in sequence or parallel.
    """

    task_id: str
    task_name: str
    task_type: str  # e.g., 'scrape', 'transform', 'load', 'validate'
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(
        default_factory=list
    )  # Task IDs that must complete first
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay_seconds: int = 60  # Delay between retries
    is_critical: bool = True  # If False, workflow continues on failure

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries

    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds"""
        if not self.start_time:
            return None
        end_time = self.end_time or datetime.now(timezone.utc)
        return (end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


@dataclass
class WorkflowMetrics:
    """Standard metrics collected by all workflows"""

    workflow_name: str
    workflow_type: str
    state: str
    priority: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Task metrics
    total_tasks: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_skipped: int = 0

    # Item metrics (workflow-specific items processed)
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0

    # Error tracking
    errors_encountered: int = 0
    warnings_issued: int = 0
    retries_attempted: int = 0

    # Quality metrics
    quality_score: float = 0.0
    data_completeness: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_tasks == 0:
            return 0.0
        return (self.tasks_completed / self.total_tasks) * 100

    @property
    def item_success_rate(self) -> float:
        """Calculate item-level success rate"""
        if self.items_processed == 0:
            return 0.0
        return (self.items_successful / self.items_processed) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        # Add computed properties
        data["success_rate"] = self.success_rate
        data["item_success_rate"] = self.item_success_rate
        return data


class BaseWorkflow(ABC):
    """
    Abstract base class for all workflows.

    Provides:
    - Standard lifecycle (initialize, execute, shutdown)
    - State machine with validated transitions
    - Task management and execution (sync and async)
    - Metrics collection and reporting
    - Error handling and recovery
    - State persistence
    - Logging infrastructure

    Subclasses must implement:
    - _validate_config(): Validate workflow-specific configuration
    - _build_tasks(): Define the workflow tasks
    - _execute_task(): Execute a single task
    - get_workflow_info(): Workflow metadata

    Optional hooks:
    - _initialize_workflow(): Custom initialization
    - _pre_execution(): Before workflow execution
    - _post_execution(): After workflow execution
    - _shutdown_workflow(): Custom cleanup
    """

    def __init__(
        self,
        workflow_name: str,
        workflow_type: str,
        config: Optional[Dict[str, Any]] = None,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
        state_dir: Optional[Path] = None,
        enable_persistence: bool = True,
    ):
        """
        Initialize base workflow.

        Args:
            workflow_name: Unique identifier for this workflow
            workflow_type: Type of workflow (e.g., 'etl', 'validation', 'autonomous')
            config: Workflow-specific configuration
            priority: Execution priority level
            state_dir: Directory for state persistence
            enable_persistence: Whether to persist state to disk
        """
        self.workflow_name = workflow_name
        self.workflow_type = workflow_type
        self.config = config or {}
        self.priority = priority
        self.enable_persistence = enable_persistence
        self.state = WorkflowState.CREATED

        # Set up state directory
        if state_dir is None:
            project_root = Path(__file__).parent.parent.parent
            state_dir = project_root / "data" / "workflow_state"
        self.state_dir = Path(state_dir)
        if self.enable_persistence:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.state_file = self.state_dir / f"{workflow_name}_state.json"

        # Initialize logging
        self.logger = setup_logging(
            name=f"workflow.{workflow_name}", level=config.get("log_level", "INFO")
        )

        # Initialize metrics
        self.metrics = WorkflowMetrics(
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            state=self.state.value,
            priority=priority.value,
            start_time=datetime.now(timezone.utc),
        )

        # Task management
        self.tasks: List[WorkflowTask] = []
        self.task_results: Dict[str, Any] = {}

        # Database connection (lazy loaded)
        self._db = None

        # State variables
        self.is_initialized = False
        self.is_cancelled = False
        self.errors: List[str] = []
        self.warnings: List[str] = []

        # Execution control
        self._execution_future: Optional[asyncio.Future] = None

        self.logger.info(
            f"Workflow {workflow_name} (type={workflow_type}) created with priority {priority.name}"
        )

    @property
    def db(self):
        """Lazy-load database connection"""
        if self._db is None:
            self._db = get_db_connection()
        return self._db

    # ===== STATE MANAGEMENT =====

    def transition_state(self, new_state: WorkflowState) -> bool:
        """
        Transition workflow to new state with validation.

        Args:
            new_state: Target state

        Returns:
            bool: True if transition successful
        """
        if not self.state.can_transition_to(new_state):
            self.logger.error(
                f"Invalid state transition: {self.state.value} -> {new_state.value}"
            )
            return False

        old_state = self.state
        self.state = new_state
        self.metrics.state = new_state.value

        self.logger.info(f"State transition: {old_state.value} -> {new_state.value}")

        if self.enable_persistence:
            self._save_state()

        return True

    def _load_state(self) -> None:
        """Load workflow state from disk"""
        if not self.enable_persistence or not self.state_file.exists():
            return

        try:
            with open(self.state_file, "r") as f:
                state_data = json.load(f)

            # Restore state
            self.state = WorkflowState(state_data.get("state", "created"))
            self.errors = state_data.get("errors", [])
            self.warnings = state_data.get("warnings", [])

            # Restore tasks
            if "tasks" in state_data:
                self.tasks = []
                for task_data in state_data["tasks"]:
                    # Convert ISO strings back to datetime
                    if "start_time" in task_data and task_data["start_time"]:
                        task_data["start_time"] = datetime.fromisoformat(
                            task_data["start_time"]
                        )
                    if "end_time" in task_data and task_data["end_time"]:
                        task_data["end_time"] = datetime.fromisoformat(
                            task_data["end_time"]
                        )
                    self.tasks.append(WorkflowTask(**task_data))

            # Restore metrics
            if "metrics" in state_data:
                metrics_data = state_data["metrics"]
                if "start_time" in metrics_data:
                    metrics_data["start_time"] = datetime.fromisoformat(
                        metrics_data["start_time"]
                    )
                if "end_time" in metrics_data and metrics_data["end_time"]:
                    metrics_data["end_time"] = datetime.fromisoformat(
                        metrics_data["end_time"]
                    )
                self.metrics = WorkflowMetrics(**metrics_data)

            self.logger.debug(f"State loaded from {self.state_file}")

        except Exception as e:
            self.logger.warning(f"Could not load state: {e}")

    def _save_state(self) -> None:
        """Save workflow state to disk"""
        if not self.enable_persistence:
            return

        try:
            state_data = {
                "workflow_name": self.workflow_name,
                "workflow_type": self.workflow_type,
                "state": self.state.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "errors": self.errors,
                "warnings": self.warnings,
                "tasks": [task.to_dict() for task in self.tasks],
                "metrics": self.metrics.to_dict(),
            }

            with open(self.state_file, "w") as f:
                json.dump(state_data, f, indent=2)

            self.logger.debug(f"State saved to {self.state_file}")

        except Exception as e:
            self.logger.error(f"Could not save state: {e}")

    # ===== LIFECYCLE METHODS =====

    def initialize(self) -> bool:
        """
        Initialize workflow and validate configuration.

        Template method that:
        1. Loads previous state if exists
        2. Validates configuration
        3. Builds workflow tasks
        4. Performs workflow-specific initialization
        5. Transitions to INITIALIZED state

        Returns:
            bool: True if initialization successful
        """
        try:
            self.logger.info(f"Initializing workflow {self.workflow_name}...")

            # Load previous state if exists
            if self.enable_persistence and self.state_file.exists():
                self._load_state()
                self.logger.info("Previous state loaded successfully")

            # Validate configuration
            if not self._validate_config():
                self.logger.error("Configuration validation failed")
                self.transition_state(WorkflowState.FAILED)
                return False

            # Build workflow tasks
            try:
                self.tasks = self._build_tasks()
                self.metrics.total_tasks = len(self.tasks)
                self.logger.info(f"Built {len(self.tasks)} workflow tasks")
            except Exception as e:
                self.logger.error(f"Failed to build tasks: {e}", exc_info=True)
                self.transition_state(WorkflowState.FAILED)
                return False

            # Workflow-specific initialization
            if not self._initialize_workflow():
                self.logger.error("Workflow initialization failed")
                self.transition_state(WorkflowState.FAILED)
                return False

            self.is_initialized = True
            self.transition_state(WorkflowState.INITIALIZED)
            self.logger.info(f"Workflow {self.workflow_name} initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Initialization error: {e}", exc_info=True)
            self.errors.append(f"Initialization: {str(e)}")
            self.transition_state(WorkflowState.FAILED)
            return False

    def execute(self, async_mode: bool = False) -> bool:
        """
        Execute workflow's tasks.

        Template method that:
        1. Checks initialization
        2. Performs pre-execution checks
        3. Transitions to RUNNING state
        4. Executes all tasks (sync or async)
        5. Performs post-execution cleanup
        6. Updates metrics and state

        Args:
            async_mode: Whether to run in async mode

        Returns:
            bool: True if execution successful
        """
        if not self.is_initialized:
            self.logger.error("Workflow not initialized. Call initialize() first.")
            return False

        if (
            self.state != WorkflowState.INITIALIZED
            and self.state != WorkflowState.READY
        ):
            self.logger.error(f"Cannot execute from state: {self.state.value}")
            return False

        try:
            # Transition to READY
            if not self.transition_state(WorkflowState.READY):
                return False

            # Pre-execution hook
            if not self._pre_execution():
                self.logger.error("Pre-execution checks failed")
                self.transition_state(WorkflowState.FAILED)
                return False

            # Transition to RUNNING
            if not self.transition_state(WorkflowState.RUNNING):
                return False

            self.metrics.start_time = datetime.now(timezone.utc)
            self.logger.info(f"Executing workflow {self.workflow_name}...")

            # Execute tasks (sync or async)
            if async_mode:
                success = asyncio.run(self._execute_tasks_async())
            else:
                success = self._execute_tasks_sync()

            # Post-execution hook
            self._post_execution(success)

            # Update final metrics
            self.metrics.end_time = datetime.now(timezone.utc)
            self.metrics.duration_seconds = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds()
            self.metrics.errors_encountered = len(self.errors)
            self.metrics.warnings_issued = len(self.warnings)

            # Calculate quality score
            self._calculate_quality_score()

            # Transition to final state
            if self.is_cancelled:
                self.transition_state(WorkflowState.CANCELLED)
            elif success:
                self.transition_state(WorkflowState.COMPLETED)
                self.logger.info(
                    f"Workflow {self.workflow_name} completed successfully "
                    f"(duration={self.metrics.duration_seconds:.2f}s, "
                    f"quality={self.metrics.quality_score:.1f}%)"
                )
            else:
                self.transition_state(WorkflowState.FAILED)
                self.logger.error(f"Workflow {self.workflow_name} failed")

            return success

        except Exception as e:
            self.logger.error(f"Execution error: {e}", exc_info=True)
            self.errors.append(f"Execution: {str(e)}")
            self.metrics.end_time = datetime.now(timezone.utc)
            self.transition_state(WorkflowState.FAILED)
            return False

    def _execute_tasks_sync(self) -> bool:
        """Execute tasks synchronously"""
        for task in self.tasks:
            if self.is_cancelled:
                task.status = "skipped"
                self.metrics.tasks_skipped += 1
                continue

            # Check dependencies
            if not self._check_task_dependencies(task):
                task.status = "skipped"
                self.metrics.tasks_skipped += 1
                self.logger.warning(f"Task {task.task_id} skipped due to dependencies")
                continue

            # Execute task with retry logic
            success = self._execute_task_with_retry(task)

            if success:
                self.metrics.tasks_completed += 1
            else:
                self.metrics.tasks_failed += 1
                # Check if workflow should continue on task failure
                if not self.config.get("continue_on_error", False):
                    return False

        return self.metrics.tasks_failed == 0

    async def _execute_tasks_async(self) -> bool:
        """Execute tasks asynchronously"""
        # Group tasks by dependency level
        task_groups = self._group_tasks_by_dependencies()

        for group in task_groups:
            if self.is_cancelled:
                for task in group:
                    task.status = "skipped"
                    self.metrics.tasks_skipped += 1
                break

            # Execute tasks in group concurrently
            results = await asyncio.gather(
                *[self._execute_task_async(task) for task in group],
                return_exceptions=True,
            )

            # Process results
            for task, result in zip(group, results):
                if isinstance(result, Exception):
                    task.status = "failed"
                    task.error = str(result)
                    self.metrics.tasks_failed += 1
                elif result:
                    self.metrics.tasks_completed += 1
                else:
                    self.metrics.tasks_failed += 1

            # Check if workflow should continue
            if self.metrics.tasks_failed > 0 and not self.config.get(
                "continue_on_error", False
            ):
                return False

        return self.metrics.tasks_failed == 0

    def _execute_task_with_retry(self, task: WorkflowTask) -> bool:
        """Execute a single task with retry logic"""
        task.status = "running"
        task.start_time = datetime.now(timezone.utc)

        while True:
            try:
                self.logger.info(f"Executing task: {task.task_id} ({task.task_name})")
                result = self._execute_task(task)

                task.status = "completed"
                task.result = result
                task.end_time = datetime.now(timezone.utc)
                self.task_results[task.task_id] = result

                self.logger.info(
                    f"Task {task.task_id} completed (duration={task.duration:.2f}s)"
                )
                return True

            except Exception as e:
                error_msg = f"Task {task.task_id} failed: {str(e)}"
                self.logger.error(error_msg)

                if task.can_retry:
                    task.retry_count += 1
                    self.metrics.retries_attempted += 1
                    self.logger.info(
                        f"Retrying task {task.task_id} ({task.retry_count}/{task.max_retries})"
                    )
                    continue
                else:
                    task.status = "failed"
                    task.error = str(e)
                    task.end_time = datetime.now(timezone.utc)
                    self.errors.append(error_msg)
                    return False

    async def _execute_task_async(self, task: WorkflowTask) -> bool:
        """Execute a single task asynchronously"""
        task.status = "running"
        task.start_time = datetime.now(timezone.utc)

        try:
            self.logger.info(
                f"Executing task (async): {task.task_id} ({task.task_name})"
            )

            # Check if _execute_task is async
            result = self._execute_task(task)
            if asyncio.iscoroutine(result):
                result = await result

            task.status = "completed"
            task.result = result
            task.end_time = datetime.now(timezone.utc)
            self.task_results[task.task_id] = result

            self.logger.info(
                f"Task {task.task_id} completed (async, duration={task.duration:.2f}s)"
            )
            return True

        except Exception as e:
            error_msg = f"Task {task.task_id} failed: {str(e)}"
            self.logger.error(error_msg)
            task.status = "failed"
            task.error = str(e)
            task.end_time = datetime.now(timezone.utc)
            self.errors.append(error_msg)
            return False

    def _check_task_dependencies(self, task: WorkflowTask) -> bool:
        """Check if all task dependencies are satisfied"""
        for dep_id in task.dependencies:
            dep_task = next((t for t in self.tasks if t.task_id == dep_id), None)
            if not dep_task or dep_task.status != "completed":
                return False
        return True

    def _group_tasks_by_dependencies(self) -> List[List[WorkflowTask]]:
        """Group tasks by dependency level for parallel execution"""
        groups = []
        remaining_tasks = self.tasks.copy()
        completed_task_ids = set()

        while remaining_tasks:
            # Find tasks with no incomplete dependencies
            ready_tasks = [
                task
                for task in remaining_tasks
                if all(dep in completed_task_ids for dep in task.dependencies)
            ]

            if not ready_tasks:
                # Circular dependency or invalid task graph
                self.logger.error("Cannot resolve task dependencies")
                break

            groups.append(ready_tasks)
            completed_task_ids.update(task.task_id for task in ready_tasks)
            remaining_tasks = [
                task for task in remaining_tasks if task not in ready_tasks
            ]

        return groups

    def _calculate_quality_score(self) -> None:
        """Calculate overall workflow quality score"""
        if self.metrics.total_tasks == 0:
            self.metrics.quality_score = 0.0
            return

        # Base score on task success rate
        base_score = self.metrics.success_rate

        # Penalize for retries
        retry_penalty = (self.metrics.retries_attempted / self.metrics.total_tasks) * 10

        # Penalize for errors
        error_penalty = (
            self.metrics.errors_encountered / self.metrics.total_tasks
        ) * 15

        self.metrics.quality_score = max(0, base_score - retry_penalty - error_penalty)

    def pause(self) -> bool:
        """Pause workflow execution"""
        if self.state != WorkflowState.RUNNING:
            self.logger.error("Can only pause running workflow")
            return False

        self.logger.info(f"Pausing workflow {self.workflow_name}")
        return self.transition_state(WorkflowState.PAUSED)

    def resume(self) -> bool:
        """Resume paused workflow"""
        if self.state != WorkflowState.PAUSED:
            self.logger.error("Can only resume paused workflow")
            return False

        self.logger.info(f"Resuming workflow {self.workflow_name}")
        return self.transition_state(WorkflowState.RUNNING)

    def cancel(self) -> bool:
        """Cancel workflow execution"""
        if self.state not in [
            WorkflowState.READY,
            WorkflowState.RUNNING,
            WorkflowState.PAUSED,
        ]:
            self.logger.error("Cannot cancel workflow in current state")
            return False

        self.logger.warning(f"Cancelling workflow {self.workflow_name}")
        self.is_cancelled = True
        return True

    def shutdown(self) -> bool:
        """
        Gracefully shutdown workflow.

        Performs cleanup and saves final state.

        Returns:
            bool: True if shutdown successful
        """
        try:
            self.logger.info(f"Shutting down workflow {self.workflow_name}...")

            # Workflow-specific cleanup
            self._shutdown_workflow()

            # Close database connection
            if self._db is not None:
                self._db.close()
                self._db = None

            # Save final state
            self.transition_state(WorkflowState.SHUTDOWN)

            self.logger.info(f"Workflow {self.workflow_name} shutdown complete")
            return True

        except Exception as e:
            self.logger.error(f"Shutdown error: {e}", exc_info=True)
            return False

    # ===== STATUS AND REPORTING =====

    def get_status(self) -> Dict[str, Any]:
        """
        Get current workflow status.

        Returns:
            Dict containing state, metrics, tasks, and errors
        """
        return {
            "workflow_name": self.workflow_name,
            "workflow_type": self.workflow_type,
            "state": self.state.value,
            "priority": self.priority.value,
            "is_initialized": self.is_initialized,
            "is_cancelled": self.is_cancelled,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                    "status": task.status,
                    "duration": task.duration,
                }
                for task in self.tasks
            ],
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics.to_dict(),
        }

    def get_metrics(self) -> WorkflowMetrics:
        """Get workflow metrics"""
        return self.metrics

    def generate_report(self, format: str = "dict") -> Any:
        """
        Generate workflow execution report.

        Args:
            format: Output format ('dict', 'json', 'markdown')

        Returns:
            Report in requested format
        """
        report_data = {
            "workflow_name": self.workflow_name,
            "workflow_type": self.workflow_type,
            "workflow_info": self.get_workflow_info(),
            "execution_summary": {
                "state": self.state.value,
                "priority": self.priority.name,
                "duration_seconds": self.metrics.duration_seconds,
                "total_tasks": self.metrics.total_tasks,
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": self.metrics.success_rate,
                "quality_score": self.metrics.quality_score,
            },
            "task_details": [task.to_dict() for task in self.tasks],
            "errors": self.errors,
            "warnings": self.warnings,
            "full_metrics": self.metrics.to_dict(),
        }

        if format == "json":
            return json.dumps(report_data, indent=2)
        elif format == "markdown":
            return self._format_markdown_report(report_data)
        else:
            return report_data

    def _format_markdown_report(self, data: Dict[str, Any]) -> str:
        """Format report as markdown"""
        md = f"# Workflow Report: {data['workflow_name']}\n\n"
        md += f"**Type:** {data['workflow_type']}\n"
        md += f"**State:** {data['execution_summary']['state']}\n"
        md += f"**Priority:** {data['execution_summary']['priority']}\n"
        md += f"**Duration:** {data['execution_summary']['duration_seconds']:.2f}s\n"
        md += f"**Tasks:** {data['execution_summary']['tasks_completed']}/{data['execution_summary']['total_tasks']} completed\n"
        md += f"**Success Rate:** {data['execution_summary']['success_rate']:.1f}%\n"
        md += (
            f"**Quality Score:** {data['execution_summary']['quality_score']:.1f}%\n\n"
        )

        if data["errors"]:
            md += "## Errors\n"
            for error in data["errors"]:
                md += f"- {error}\n"
            md += "\n"

        if data["warnings"]:
            md += "## Warnings\n"
            for warning in data["warnings"]:
                md += f"- {warning}\n"
            md += "\n"

        md += "## Task Summary\n"
        for task in data["task_details"]:
            md += f"- **{task['task_id']}**: {task['status']}"
            if task.get("duration"):
                md += f" ({task['duration']:.2f}s)"
            md += "\n"

        return md

    # ===== ABSTRACT METHODS (must be implemented by subclasses) =====

    @abstractmethod
    def _validate_config(self) -> bool:
        """
        Validate workflow-specific configuration.

        Returns:
            bool: True if configuration is valid
        """
        pass

    @abstractmethod
    def _build_tasks(self) -> List[WorkflowTask]:
        """
        Build the list of tasks for this workflow.

        Returns:
            List of WorkflowTask objects defining the workflow
        """
        pass

    @abstractmethod
    def _execute_task(self, task: WorkflowTask) -> Any:
        """
        Execute a single workflow task.

        This method can be sync or async (return coroutine).

        Args:
            task: The task to execute

        Returns:
            Task result (any type)
        """
        pass

    @abstractmethod
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get workflow metadata and information.

        Returns:
            Dict containing workflow description, version, capabilities, etc.
        """
        pass

    # ===== OPTIONAL HOOKS (can be overridden by subclasses) =====

    def _initialize_workflow(self) -> bool:
        """
        Optional workflow-specific initialization logic.

        Override this method for custom initialization.
        Default implementation returns True.

        Returns:
            bool: True if initialization successful
        """
        return True

    def _pre_execution(self) -> bool:
        """
        Optional pre-execution checks.

        Override this method for custom pre-execution logic.
        Default implementation returns True.

        Returns:
            bool: True if checks passed
        """
        return True

    def _post_execution(self, success: bool) -> None:
        """
        Optional post-execution cleanup.

        Override this method for custom post-execution logic.
        Default implementation does nothing.

        Args:
            success: Whether execution was successful
        """
        pass

    def _shutdown_workflow(self) -> None:
        """
        Optional workflow-specific shutdown logic.

        Override this method for custom cleanup.
        Default implementation does nothing.
        """
        pass

    # ===== UTILITY METHODS =====

    def log_error(self, message: str) -> None:
        """Log and track an error"""
        self.logger.error(message)
        self.errors.append(message)

    def log_warning(self, message: str) -> None:
        """Log and track a warning"""
        self.logger.warning(message)
        self.warnings.append(message)

    def update_metric(self, key: str, value: Any) -> None:
        """Update a specific metric"""
        if hasattr(self.metrics, key):
            setattr(self.metrics, key, value)
            self.logger.debug(f"Metric updated: {key} = {value}")
        else:
            self.logger.warning(f"Unknown metric: {key}")

    def get_task(self, task_id: str) -> Optional[WorkflowTask]:
        """Get a task by ID"""
        return next((task for task in self.tasks if task.task_id == task_id), None)

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get result from a completed task"""
        return self.task_results.get(task_id)
