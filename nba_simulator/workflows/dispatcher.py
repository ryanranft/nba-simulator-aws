"""
Workflow Dispatcher - Unified Task Routing and Execution

Migrated from scripts/etl/data_dispatcher.py to nba_simulator package.
Provides centralized dispatcher pattern for routing workflow tasks to
appropriate handlers (scrapers, agents, transformers, loaders).

Design Patterns:
- Registry Pattern: Dynamic handler registration
- Factory Pattern: Handler instantiation
- Strategy Pattern: Pluggable execution strategies
- Observer Pattern: Event notifications

Key Features:
- Registry-based handler routing
- Priority-based task queuing
- Async/await support
- Error handling and retry logic
- Integration with ADCE autonomous system
- Comprehensive metrics and monitoring

Usage:
    from nba_simulator.workflows import WorkflowDispatcher, DispatchTask

    # Initialize dispatcher
    dispatcher = WorkflowDispatcher()

    # Create task
    task = DispatchTask(
        handler="espn_scraper",
        operation="scrape_date",
        params={"date": "20250101"},
        priority=TaskPriority.HIGH
    )

    # Dispatch task
    result = await dispatcher.dispatch(task)

Version: 2.0 (Refactored from 1.0)
Migrated: November 4, 2025
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

# NBA Simulator imports (new package structure)
from ..database import get_db_connection
from ..utils import setup_logging

# Import ETL components
from ..etl.extractors import (
    ESPNScraper,
    BasketballReferenceScraper,
    HoopRScraper,
    NBAAPIScraper,
)

# Import agents
from ..agents import (
    MasterAgent,
    QualityAgent,
    IntegrationAgent,
    NBAStatsAgent,
    DeduplicationAgent,
    HistoricalAgent,
    HooprAgent,
    BasketballReferenceAgent,
)


class TaskPriority(Enum):
    """Priority levels for dispatch tasks"""

    CRITICAL = 1  # Immediate execution (e.g., live games)
    HIGH = 2  # High priority (e.g., recent games, missing data)
    NORMAL = 3  # Normal priority (e.g., scheduled workflows)
    LOW = 4  # Low priority (e.g., historical backfill)
    BACKGROUND = 5  # Background processing


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class HandlerType(Enum):
    """Types of handlers that can be registered"""

    SCRAPER = "scraper"  # ETL extractors
    AGENT = "agent"  # Autonomous agents
    TRANSFORMER = "transformer"  # Data transformers
    LOADER = "loader"  # Data loaders
    VALIDATOR = "validator"  # Data validators
    WORKFLOW = "workflow"  # Other workflows


@dataclass
class DispatchTask:
    """
    Represents a task to be dispatched.

    Unlike WorkflowTask (which is internal to a workflow),
    DispatchTask represents external tasks routed to handlers.
    """

    handler: str  # Handler identifier (e.g., 'espn_scraper', 'quality_agent')
    operation: str  # Operation to perform (e.g., 'scrape', 'validate')
    params: Dict[str, Any] = field(default_factory=dict)  # Operation parameters
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    handler_type: Optional[HandlerType] = None

    # Execution tracking
    task_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results and errors
    result: Optional[Any] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate task after initialization"""
        if not self.handler:
            raise ValueError("Task handler cannot be empty")
        if not self.operation:
            raise ValueError("Task operation cannot be empty")

        # Generate task ID if not provided
        if not self.task_id:
            self.task_id = (
                f"{self.handler}_{self.operation}_{self.created_at.timestamp()}"
            )

    def mark_queued(self):
        """Mark task as queued"""
        self.status = TaskStatus.QUEUED

    def mark_running(self):
        """Mark task as running"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, result: Any = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def mark_failed(self, error: str, error_type: Optional[str] = None):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error
        self.error_type = error_type or "UnknownError"

    def mark_retrying(self):
        """Mark task as retrying"""
        self.status = TaskStatus.RETRYING
        self.retry_count += 1

    def mark_cancelled(self):
        """Mark task as cancelled"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
