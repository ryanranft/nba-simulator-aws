"""
Master Agent - Main Orchestration Coordinator

Coordinates execution of all other agents in the NBA Simulator system.
Manages priorities, dependencies, scheduling, and overall system health.

Responsibilities:
- Agent lifecycle management
- Priority-based execution scheduling
- Dependency resolution
- Health monitoring
- Error recovery and retry logic
- System-wide reporting
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from enum import Enum
import json

from .base_agent import BaseAgent, AgentState, AgentPriority, AgentMetrics


class ExecutionPhase(Enum):
    """Execution phases for agent orchestration"""
    COLLECTION = "collection"      # Data collection agents
    VALIDATION = "validation"      # Data validation agents
    INTEGRATION = "integration"    # Cross-source integration
    QUALITY = "quality"            # Quality assurance
    DEDUPLICATION = "deduplication"  # Duplicate resolution
    HISTORICAL = "historical"      # Historical processing
    REPORTING = "reporting"        # Report generation
    COMPLETE = "complete"          # All phases complete


class MasterAgent(BaseAgent):
    """
    Master orchestration agent that coordinates all other agents.
    
    Manages 8 phases of execution:
    1. Collection - NBA Stats, hoopR, BBRef agents
    2. Validation - Initial data validation
    3. Integration - Cross-source matching
    4. Quality - Quality scoring and verification
    5. Deduplication - Duplicate detection and resolution
    6. Historical - Historical data processing
    7. Reporting - Generate execution reports
    8. Complete - Finalization
    
    Features:
    - Priority-based scheduling
    - Automatic retry on failures
    - Dependency management
    - Health monitoring
    - Comprehensive reporting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Master Agent.
        
        Args:
            config: Configuration dictionary with keys:
                - max_retries: Maximum retry attempts per agent (default: 3)
                - retry_delay: Delay between retries in seconds (default: 60)
                - parallel_execution: Enable parallel agent execution (default: False)
                - stop_on_failure: Stop all execution if critical agent fails (default: True)
        """
        super().__init__(
            agent_name="master_orchestrator",
            config=config,
            priority=AgentPriority.CRITICAL
        )
        
        # Configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 60)
        self.parallel_execution = self.config.get('parallel_execution', False)
        self.stop_on_failure = self.config.get('stop_on_failure', True)
        
        # Execution state
        self.current_phase = ExecutionPhase.COLLECTION
        self.registered_agents: Dict[str, BaseAgent] = {}
        self.agent_priorities: Dict[str, AgentPriority] = {}
        self.agent_dependencies: Dict[str, Set[str]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.failed_agents: Set[str] = set()
        self.completed_agents: Set[str] = set()
        
        # Phase mapping
        self.phase_agents: Dict[ExecutionPhase, List[str]] = {
            ExecutionPhase.COLLECTION: ['nba_stats', 'hoopr', 'bbref'],
            ExecutionPhase.VALIDATION: ['quality'],
            ExecutionPhase.INTEGRATION: ['integration'],
            ExecutionPhase.QUALITY: ['quality'],
            ExecutionPhase.DEDUPLICATION: ['deduplication'],
            ExecutionPhase.HISTORICAL: ['historical'],
            ExecutionPhase.REPORTING: [],
            ExecutionPhase.COMPLETE: []
        }
    
    def register_agent(
        self,
        agent: BaseAgent,
        dependencies: Optional[Set[str]] = None
    ) -> None:
        """
        Register an agent for orchestration.
        
        Args:
            agent: Agent instance to register
            dependencies: Set of agent names this agent depends on
        """
        agent_name = agent.agent_name
        self.registered_agents[agent_name] = agent
        self.agent_priorities[agent_name] = agent.priority
        self.agent_dependencies[agent_name] = dependencies or set()
        
        self.logger.info(
            f"Registered agent: {agent_name} "
            f"(priority: {agent.priority.name}, "
            f"dependencies: {dependencies or 'none'})"
        )
    
    def _validate_config(self) -> bool:
        """Validate master agent configuration"""
        try:
            # Check max_retries
            if not isinstance(self.max_retries, int) or self.max_retries < 0:
                self.log_error("max_retries must be non-negative integer")
                return False
            
            # Check retry_delay
            if not isinstance(self.retry_delay, (int, float)) or self.retry_delay < 0:
                self.log_error("retry_delay must be non-negative number")
                return False
            
            # Check boolean flags
            if not isinstance(self.parallel_execution, bool):
                self.log_error("parallel_execution must be boolean")
                return False
            
            if not isinstance(self.stop_on_failure, bool):
                self.log_error("stop_on_failure must be boolean")
                return False
            
            self.logger.info("Master agent configuration validated")
            return True
            
        except Exception as e:
            self.log_error(f"Configuration validation error: {e}")
            return False
    
    def _initialize_agent(self) -> bool:
        """Initialize master agent"""
        try:
            self.logger.info("Initializing master orchestrator...")
            
            # Initialize all registered agents
            for agent_name, agent in self.registered_agents.items():
                self.logger.info(f"Initializing agent: {agent_name}")
                if not agent.initialize():
                    self.log_error(f"Failed to initialize agent: {agent_name}")
                    return False
            
            self.logger.info(f"All {len(self.registered_agents)} agents initialized")
            return True
            
        except Exception as e:
            self.log_error(f"Master initialization error: {e}")
            return False
    
    def _execute_core(self) -> bool:
        """
        Execute orchestration of all registered agents.
        
        Executes agents phase by phase, respecting priorities and dependencies.
        
        Returns:
            bool: True if all agents executed successfully
        """
        try:
            self.logger.info("Starting agent orchestration...")
            self.metrics.start_time = datetime.now(timezone.utc)
            
            # Execute each phase
            for phase in ExecutionPhase:
                if phase == ExecutionPhase.COMPLETE:
                    continue
                
                self.current_phase = phase
                self.logger.info(f"Executing phase: {phase.value}")
                
                # Get agents for this phase
                phase_agent_names = self.phase_agents.get(phase, [])
                
                if not phase_agent_names:
                    self.logger.info(f"No agents for phase {phase.value}")
                    continue
                
                # Execute phase agents
                phase_success = self._execute_phase(phase, phase_agent_names)
                
                if not phase_success and self.stop_on_failure:
                    self.log_error(f"Phase {phase.value} failed, stopping execution")
                    return False
            
            # Final phase
            self.current_phase = ExecutionPhase.COMPLETE
            self.logger.info("All phases completed")
            
            # Calculate final metrics
            self._calculate_final_metrics()
            
            return len(self.failed_agents) == 0
            
        except Exception as e:
            self.log_error(f"Orchestration error: {e}")
            return False
    
    def _execute_phase(
        self,
        phase: ExecutionPhase,
        agent_names: List[str]
    ) -> bool:
        """
        Execute all agents in a phase.
        
        Args:
            phase: Current execution phase
            agent_names: List of agent names to execute
            
        Returns:
            bool: True if phase completed successfully
        """
        phase_success = True
        
        for agent_name in agent_names:
            if agent_name not in self.registered_agents:
                self.log_warning(f"Agent {agent_name} not registered, skipping")
                continue
            
            # Check dependencies
            if not self._check_dependencies(agent_name):
                self.log_error(f"Dependencies not met for agent: {agent_name}")
                self.failed_agents.add(agent_name)
                phase_success = False
                continue
            
            # Execute agent with retry logic
            success = self._execute_agent_with_retry(agent_name)
            
            if success:
                self.completed_agents.add(agent_name)
                self.metrics.items_successful += 1
            else:
                self.failed_agents.add(agent_name)
                self.metrics.items_failed += 1
                phase_success = False
            
            self.metrics.items_processed += 1
        
        return phase_success
    
    def _execute_agent_with_retry(self, agent_name: str) -> bool:
        """
        Execute an agent with automatic retry on failure.
        
        Args:
            agent_name: Name of agent to execute
            
        Returns:
            bool: True if agent executed successfully
        """
        agent = self.registered_agents[agent_name]
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(
                    f"Executing agent {agent_name} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                
                # Execute agent
                start_time = datetime.now(timezone.utc)
                success = agent.execute()
                end_time = datetime.now(timezone.utc)
                duration = (end_time - start_time).total_seconds()
                
                # Record execution
                execution_record = {
                    'agent_name': agent_name,
                    'attempt': attempt + 1,
                    'success': success,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'metrics': agent.get_metrics().to_dict()
                }
                self.execution_history.append(execution_record)
                
                if success:
                    self.logger.info(f"Agent {agent_name} completed successfully")
                    return True
                else:
                    self.logger.warning(
                        f"Agent {agent_name} failed "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    
                    # Retry if attempts remaining
                    if attempt < self.max_retries:
                        self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                        import time
                        time.sleep(self.retry_delay)
                
            except Exception as e:
                self.log_error(f"Error executing agent {agent_name}: {e}")
                if attempt >= self.max_retries:
                    return False
        
        self.log_error(f"Agent {agent_name} failed after {self.max_retries + 1} attempts")
        return False
    
    def _check_dependencies(self, agent_name: str) -> bool:
        """
        Check if all dependencies for an agent are satisfied.
        
        Args:
            agent_name: Name of agent to check
            
        Returns:
            bool: True if all dependencies satisfied
        """
        dependencies = self.agent_dependencies.get(agent_name, set())
        
        for dep_name in dependencies:
            if dep_name in self.failed_agents:
                self.log_error(
                    f"Dependency {dep_name} failed for agent {agent_name}"
                )
                return False
            
            if dep_name not in self.completed_agents:
                self.log_warning(
                    f"Dependency {dep_name} not completed for agent {agent_name}"
                )
                return False
        
        return True
    
    def _calculate_final_metrics(self) -> None:
        """Calculate final orchestration metrics"""
        try:
            total_agents = len(self.registered_agents)
            successful = len(self.completed_agents)
            failed = len(self.failed_agents)
            
            # Calculate quality score
            if total_agents > 0:
                self.metrics.quality_score = (successful / total_agents) * 100
            else:
                self.metrics.quality_score = 0.0
            
            self.logger.info(
                f"Final metrics: {successful}/{total_agents} agents successful "
                f"(quality score: {self.metrics.quality_score:.1f}%)"
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating final metrics: {e}")
    
    def _shutdown_agent(self) -> None:
        """Shutdown all registered agents"""
        try:
            self.logger.info("Shutting down all agents...")
            
            for agent_name, agent in self.registered_agents.items():
                try:
                    self.logger.info(f"Shutting down agent: {agent_name}")
                    agent.shutdown()
                except Exception as e:
                    self.log_error(f"Error shutting down {agent_name}: {e}")
            
            self.logger.info("All agents shutdown")
            
        except Exception as e:
            self.logger.error(f"Master shutdown error: {e}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get master agent information"""
        return {
            'name': 'Master Orchestrator',
            'version': '1.0.0',
            'description': 'Coordinates execution of all NBA Simulator agents',
            'capabilities': [
                'Agent lifecycle management',
                'Priority-based scheduling',
                'Dependency resolution',
                'Automatic retry logic',
                'Health monitoring',
                'System-wide reporting'
            ],
            'registered_agents': list(self.registered_agents.keys()),
            'execution_phases': [phase.value for phase in ExecutionPhase]
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get detailed execution summary.
        
        Returns:
            Dict with execution statistics and history
        """
        return {
            'current_phase': self.current_phase.value,
            'registered_agents': len(self.registered_agents),
            'completed_agents': list(self.completed_agents),
            'failed_agents': list(self.failed_agents),
            'success_rate': (
                len(self.completed_agents) / len(self.registered_agents) * 100
                if self.registered_agents else 0
            ),
            'execution_history': self.execution_history,
            'quality_score': self.metrics.quality_score
        }
