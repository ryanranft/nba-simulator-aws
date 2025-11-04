"""
Workflows Module - Workflow Orchestration and Task Management

Provides base classes and utilities for building NBA Simulator workflows.
Workflows are composed of tasks that execute in sequence or parallel.

Key Components:
- BaseWorkflow: Abstract base class for all workflows
- WorkflowTask: Individual task representation
- WorkflowState: State machine for workflow lifecycle
- WorkflowMetrics: Standard metrics collection

Example Usage:
    from nba_simulator.workflows import BaseWorkflow, WorkflowTask, WorkflowPriority
    
    class MyWorkflow(BaseWorkflow):
        def _validate_config(self) -> bool:
            return True
        
        def _build_tasks(self) -> List[WorkflowTask]:
            return [
                WorkflowTask(task_id="task1", task_name="Scrape Data", task_type="scrape"),
                WorkflowTask(task_id="task2", task_name="Transform Data", task_type="transform",
                            dependencies=["task1"])
            ]
        
        def _execute_task(self, task: WorkflowTask) -> Any:
            # Task execution logic
            pass
        
        def get_workflow_info(self) -> Dict[str, Any]:
            return {
                "name": "My Workflow",
                "version": "1.0.0",
                "description": "Example workflow"
            }
    
    # Use workflow
    workflow = MyWorkflow("my_workflow", "etl")
    workflow.initialize()
    success = workflow.execute()
    report = workflow.generate_report()
"""

from .base_workflow import (
    BaseWorkflow,
    WorkflowState,
    WorkflowPriority,
    WorkflowTask,
    WorkflowMetrics,
)

__all__ = [
    # Base Classes
    'BaseWorkflow',
    
    # Enums
    'WorkflowState',
    'WorkflowPriority',
    
    # Data Classes
    'WorkflowTask',
    'WorkflowMetrics',
]

__version__ = '1.0.0'
