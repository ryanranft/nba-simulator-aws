"""
NBA Simulator Agents Package

Autonomous agents for orchestration, validation, and data management.

Available Agents:
- BaseAgent: Abstract base class for all agents
- MasterAgent: Main orchestration coordinator
- QualityAgent: Data quality validation
- IntegrationAgent: Cross-source validation
- NBAStatsAgent: NBA API coordination
- DeduplicationAgent: Duplicate detection and resolution
- HistoricalAgent: Historical data management
- HooprAgent: hoopR data integration
- BasketballReferenceAgent: Basketball-Reference.com 13-tier collection

Usage:
    from nba_simulator.agents import MasterAgent, QualityAgent

    # Create agents
    master = MasterAgent(config={'max_retries': 3})
    quality = QualityAgent(config={'min_quality_score': 85.0})

    # Register with master
    master.register_agent(quality)

    # Initialize and execute
    master.initialize()
    master.execute()

    # Get report
    report = master.generate_report()
"""

from .base_agent import BaseAgent, AgentState, AgentPriority, AgentMetrics

from .master import MasterAgent, ExecutionPhase
from .quality import QualityAgent, QualityCheck
from .integration import IntegrationAgent, IntegrationMatch, ConflictResolution
from .nba_stats import NBAStatsAgent
from .deduplication import DeduplicationAgent
from .historical import HistoricalAgent
from .hoopr import HooprAgent
from .bbref import BasketballReferenceAgent, BBRefTier

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentState",
    "AgentPriority",
    "AgentMetrics",
    # Concrete agents
    "MasterAgent",
    "QualityAgent",
    "IntegrationAgent",
    "NBAStatsAgent",
    "DeduplicationAgent",
    "HistoricalAgent",
    "HooprAgent",
    "BasketballReferenceAgent",
    # Additional exports
    "ExecutionPhase",
    "QualityCheck",
    "IntegrationMatch",
    "ConflictResolution",
    "BBRefTier",
]

__version__ = "1.0.0"
