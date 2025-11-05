"""
Base Agent - Abstract Base Class for All Autonomous Agents

Provides standard lifecycle, state management, and reporting for all NBA Simulator agents.
All agents must inherit from this class and implement required abstract methods.

Design Patterns:
- Template Method: Standard lifecycle with customizable hooks
- Strategy: Pluggable validation and execution strategies
- Memento: State persistence and recovery
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
from dataclasses import dataclass, asdict

from ..database import get_db_connection
from ..utils import setup_logging


class AgentState(Enum):
    """Agent lifecycle states"""

    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


class AgentPriority(Enum):
    """Agent execution priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class AgentMetrics:
    """Standard metrics collected by all agents"""

    agent_name: str
    state: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    errors_encountered: int = 0
    warnings_issued: int = 0
    quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


class BaseAgent(ABC):
    """
    Abstract base class for all autonomous agents.

    Provides:
    - Standard lifecycle (initialize, execute, shutdown)
    - State management and persistence
    - Metrics collection and reporting
    - Error handling and recovery
    - Configuration management
    - Logging infrastructure

    Subclasses must implement:
    - _validate_config(): Validate agent-specific configuration
    - _execute_core(): Core agent logic
    - get_agent_info(): Agent metadata
    """

    def __init__(
        self,
        agent_name: str,
        config: Optional[Dict[str, Any]] = None,
        priority: AgentPriority = AgentPriority.NORMAL,
        state_dir: Optional[Path] = None,
    ):
        """
        Initialize base agent.

        Args:
            agent_name: Unique identifier for this agent
            config: Agent-specific configuration
            priority: Execution priority level
            state_dir: Directory for state persistence (default: project_root/data/agent_state)
        """
        self.agent_name = agent_name
        self.config = config or {}
        self.priority = priority
        self.state = AgentState.INITIALIZED

        # Set up state directory
        if state_dir is None:
            project_root = Path(__file__).parent.parent.parent
            state_dir = project_root / "data" / "agent_state"
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / f"{agent_name}_state.json"

        # Initialize logging
        self.logger = setup_logging(
            name=f"agent.{agent_name}", level=config.get("log_level", "INFO")
        )

        # Initialize metrics
        self.metrics = AgentMetrics(
            agent_name=agent_name,
            state=self.state.value,
            start_time=datetime.now(timezone.utc),
        )

        # Database connection (lazy loaded)
        self._db = None

        # State variables
        self.is_initialized = False
        self.errors: List[str] = []
        self.warnings: List[str] = []

        self.logger.info(f"Agent {agent_name} created with priority {priority.name}")

    @property
    def db(self):
        """Lazy-load database connection"""
        if self._db is None:
            self._db = get_db_connection()
        return self._db

    # ===== LIFECYCLE METHODS =====

    def initialize(self) -> bool:
        """
        Initialize agent and validate configuration.

        Template method that:
        1. Loads previous state if exists
        2. Validates configuration
        3. Performs agent-specific initialization

        Returns:
            bool: True if initialization successful
        """
        try:
            self.logger.info(f"Initializing agent {self.agent_name}...")

            # Load previous state if exists
            if self.state_file.exists():
                self._load_state()
                self.logger.info("Previous state loaded successfully")

            # Validate configuration
            if not self._validate_config():
                self.logger.error("Configuration validation failed")
                self.state = AgentState.FAILED
                return False

            # Agent-specific initialization
            if not self._initialize_agent():
                self.logger.error("Agent initialization failed")
                self.state = AgentState.FAILED
                return False

            self.is_initialized = True
            self.state = AgentState.INITIALIZED
            self.logger.info(f"Agent {self.agent_name} initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Initialization error: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.errors.append(f"Initialization: {str(e)}")
            return False

    def execute(self) -> bool:
        """
        Execute agent's core logic.

        Template method that:
        1. Checks initialization
        2. Updates state to RUNNING
        3. Executes core logic
        4. Updates metrics
        5. Persists state

        Returns:
            bool: True if execution successful
        """
        if not self.is_initialized:
            self.logger.error("Agent not initialized. Call initialize() first.")
            return False

        try:
            self.logger.info(f"Executing agent {self.agent_name}...")
            self.state = AgentState.RUNNING
            self.metrics.start_time = datetime.now(timezone.utc)

            # Execute core logic (implemented by subclass)
            success = self._execute_core()

            # Update final metrics
            self.metrics.end_time = datetime.now(timezone.utc)
            self.metrics.duration_seconds = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds()
            self.metrics.errors_encountered = len(self.errors)
            self.metrics.warnings_issued = len(self.warnings)

            # Update state
            if success:
                self.state = AgentState.COMPLETED
                self.logger.info(f"Agent {self.agent_name} completed successfully")
            else:
                self.state = AgentState.FAILED
                self.logger.error(f"Agent {self.agent_name} failed")

            # Persist state
            self._save_state()

            return success

        except Exception as e:
            self.logger.error(f"Execution error: {e}", exc_info=True)
            self.state = AgentState.FAILED
            self.errors.append(f"Execution: {str(e)}")
            self.metrics.end_time = datetime.now(timezone.utc)
            self._save_state()
            return False

    def shutdown(self) -> bool:
        """
        Gracefully shutdown agent.

        Performs cleanup and saves final state.

        Returns:
            bool: True if shutdown successful
        """
        try:
            self.logger.info(f"Shutting down agent {self.agent_name}...")

            # Agent-specific cleanup
            self._shutdown_agent()

            # Close database connection
            if self._db is not None:
                self._db.close()
                self._db = None

            # Save final state
            self.state = AgentState.SHUTDOWN
            self._save_state()

            self.logger.info(f"Agent {self.agent_name} shutdown complete")
            return True

        except Exception as e:
            self.logger.error(f"Shutdown error: {e}", exc_info=True)
            return False

    # ===== STATE MANAGEMENT =====

    def _load_state(self) -> None:
        """Load agent state from disk"""
        try:
            with open(self.state_file, "r") as f:
                state_data = json.load(f)

            # Restore state variables
            self.state = AgentState(state_data.get("state", "initialized"))
            self.errors = state_data.get("errors", [])
            self.warnings = state_data.get("warnings", [])

            # Restore metrics if available
            if "metrics" in state_data:
                metrics_data = state_data["metrics"]
                # Convert ISO strings back to datetime
                if "start_time" in metrics_data:
                    metrics_data["start_time"] = datetime.fromisoformat(
                        metrics_data["start_time"]
                    )
                if "end_time" in metrics_data and metrics_data["end_time"]:
                    metrics_data["end_time"] = datetime.fromisoformat(
                        metrics_data["end_time"]
                    )
                self.metrics = AgentMetrics(**metrics_data)

            self.logger.debug(f"State loaded from {self.state_file}")

        except Exception as e:
            self.logger.warning(f"Could not load state: {e}")

    def _save_state(self) -> None:
        """Save agent state to disk"""
        try:
            state_data = {
                "agent_name": self.agent_name,
                "state": self.state.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "errors": self.errors,
                "warnings": self.warnings,
                "metrics": self.metrics.to_dict(),
            }

            with open(self.state_file, "w") as f:
                json.dump(state_data, f, indent=2)

            self.logger.debug(f"State saved to {self.state_file}")

        except Exception as e:
            self.logger.error(f"Could not save state: {e}")

    # ===== STATUS AND REPORTING =====

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.

        Returns:
            Dict containing state, metrics, and errors
        """
        return {
            "agent_name": self.agent_name,
            "state": self.state.value,
            "priority": self.priority.value,
            "is_initialized": self.is_initialized,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics.to_dict(),
        }

    def get_metrics(self) -> AgentMetrics:
        """Get agent metrics"""
        return self.metrics

    def generate_report(self, format: str = "dict") -> Any:
        """
        Generate agent execution report.

        Args:
            format: Output format ('dict', 'json', 'markdown')

        Returns:
            Report in requested format
        """
        report_data = {
            "agent_name": self.agent_name,
            "agent_info": self.get_agent_info(),
            "execution_summary": {
                "state": self.state.value,
                "duration_seconds": self.metrics.duration_seconds,
                "items_processed": self.metrics.items_processed,
                "success_rate": (
                    self.metrics.items_successful / self.metrics.items_processed * 100
                    if self.metrics.items_processed > 0
                    else 0
                ),
                "quality_score": self.metrics.quality_score,
            },
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
        md = f"# Agent Report: {data['agent_name']}\n\n"
        md += f"**State:** {data['execution_summary']['state']}\n"
        md += f"**Duration:** {data['execution_summary']['duration_seconds']:.2f}s\n"
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

        return md

    # ===== ABSTRACT METHODS (must be implemented by subclasses) =====

    @abstractmethod
    def _validate_config(self) -> bool:
        """
        Validate agent-specific configuration.

        Returns:
            bool: True if configuration is valid
        """
        pass

    @abstractmethod
    def _execute_core(self) -> bool:
        """
        Execute core agent logic.

        Returns:
            bool: True if execution successful
        """
        pass

    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent metadata and information.

        Returns:
            Dict containing agent description, version, capabilities, etc.
        """
        pass

    # ===== OPTIONAL HOOKS (can be overridden by subclasses) =====

    def _initialize_agent(self) -> bool:
        """
        Optional agent-specific initialization logic.

        Override this method for custom initialization.
        Default implementation returns True.

        Returns:
            bool: True if initialization successful
        """
        return True

    def _shutdown_agent(self) -> None:
        """
        Optional agent-specific shutdown logic.

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
