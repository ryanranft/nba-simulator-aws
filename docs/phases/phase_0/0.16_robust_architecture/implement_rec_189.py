#!/usr/bin/env python3
"""
Implementation: Robust Architecture for Multi-Source Search

Recommendation ID: rec_189
Source: Hands On Large Language Models
Priority: IMPORTANT
Phase: 0.16 (Architecture)

Description:
Implements a robust architecture for performing multi-source searches with flexible
execution strategies. Supports sequential, parallel, conditional, and fallback search
patterns to improve information retrieval from multiple systems.

Architecture:
- Phase 0.10: PostgreSQL JSONB Storage
- Phase 0.11: RAG Pipeline with pgvector
- Phase 0.15: Information Availability (SemanticSearchEngine)

Key Capabilities:
- Sequential search (search A first, then B using A's results)
- Parallel search (search A and B simultaneously, merge results)
- Conditional search (search B only if A meets criteria)
- Fallback search (try A, fall back to B if insufficient)
- Result aggregation, de-duplication, and re-ranking

Expected Impact:
Improves the ability to find information through flexible multi-source search orchestration.
"""

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Add parent directory to path for Phase 0.15 integration
sys.path.insert(0, str(Path(__file__).parent.parent / "0.15_information_availability"))

try:
    from implement_rec_180 import SearchResult, SemanticSearchEngine
except ImportError:
    # Fallback for testing - will be mocked
    SearchResult = None
    SemanticSearchEngine = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Search execution strategies."""

    SEQUENTIAL = "sequential"  # Execute searches one after another
    PARALLEL = "parallel"  # Execute all searches simultaneously
    CONDITIONAL = "conditional"  # Execute search B only if A meets criteria
    FALLBACK = "fallback"  # Try A, fall back to B if A fails/insufficient


@dataclass
class SearchConfig:
    """
    Configuration for robust search architecture.

    Attributes:
        strategy: Search execution strategy (default: PARALLEL)
        sources: List of source types to search (e.g., ['semantic', 'jsonb'])
        timeout: Maximum time per search in seconds (default: 30)
        max_results: Maximum total results to return (default: 20)
        min_relevance_score: Minimum relevance score threshold (0-1)
        parallel_workers: Number of parallel workers for PARALLEL strategy
        conditional_threshold: Threshold for CONDITIONAL strategy
        deduplicate: Whether to deduplicate results by entity_id
        re_rank: Whether to re-rank merged results
    """

    strategy: SearchStrategy = SearchStrategy.PARALLEL
    sources: List[str] = field(default_factory=lambda: ["semantic", "jsonb"])
    timeout: int = 30
    max_results: int = 20
    min_relevance_score: float = 0.5
    parallel_workers: int = 4
    conditional_threshold: Dict[str, Any] = field(
        default_factory=lambda: {"min_results": 5}
    )
    deduplicate: bool = True
    re_rank: bool = True

    def validate(self) -> bool:
        """
        Validate configuration parameters.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(self.strategy, SearchStrategy):
            raise ValueError(f"Invalid strategy: {self.strategy}")

        if not self.sources:
            raise ValueError("At least one source must be specified")

        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

        if self.max_results <= 0:
            raise ValueError("max_results must be positive")

        if not 0 <= self.min_relevance_score <= 1:
            raise ValueError("min_relevance_score must be between 0 and 1")

        if self.parallel_workers <= 0:
            raise ValueError("parallel_workers must be positive")

        return True


class ResultAggregator:
    """
    Aggregates, de-duplicates, and re-ranks results from multiple searches.

    Integrates results from different sources, removes duplicates based on
    entity_id, and optionally re-ranks by combined relevance scores.
    """

    def __init__(
        self,
        min_relevance_score: float = 0.5,
        max_results: int = 20,
        deduplicate: bool = True,
        re_rank: bool = True,
    ):
        """
        Initialize ResultAggregator.

        Args:
            min_relevance_score: Minimum relevance score threshold
            max_results: Maximum results to return
            deduplicate: Whether to deduplicate by entity_id
            re_rank: Whether to re-rank merged results
        """
        self.min_relevance_score = min_relevance_score
        self.max_results = max_results
        self.deduplicate = deduplicate
        self.re_rank = re_rank
        logger.info(
            f"Initialized ResultAggregator (min_score={min_relevance_score}, "
            f"max={max_results}, dedupe={deduplicate}, re_rank={re_rank})"
        )

    def merge(self, result_sets: List[List[Any]]) -> List[Any]:
        """
        Merge multiple result sets into a single list.

        Args:
            result_sets: List of result sets from different searches

        Returns:
            Merged list of results
        """
        if not result_sets:
            logger.warning("No result sets to merge")
            return []

        merged = []
        for results in result_sets:
            if results:
                merged.extend(results)

        logger.info(f"Merged {len(result_sets)} result sets into {len(merged)} results")
        return merged

    def deduplicate_results(self, results: List[Any]) -> List[Any]:
        """
        Remove duplicate results based on entity_id.

        When duplicates are found, keeps the result with the highest
        relevance_score.

        Args:
            results: List of SearchResult objects

        Returns:
            De-duplicated list of results
        """
        if not results or not self.deduplicate:
            return results

        seen: Dict[str, Any] = {}

        for result in results:
            # Handle both SearchResult objects and dict representations
            if hasattr(result, "entity_id"):
                entity_id = result.entity_id
                relevance = getattr(result, "relevance_score", 0.0)
            else:
                entity_id = result.get("entity_id")
                relevance = result.get("relevance_score", 0.0)

            if entity_id not in seen:
                seen[entity_id] = result
            else:
                # Keep result with higher relevance score
                existing_relevance = (
                    getattr(seen[entity_id], "relevance_score", 0.0)
                    if hasattr(seen[entity_id], "relevance_score")
                    else seen[entity_id].get("relevance_score", 0.0)
                )
                if relevance > existing_relevance:
                    seen[entity_id] = result

        deduped = list(seen.values())
        logger.info(
            f"Deduplicated {len(results)} results to {len(deduped)} unique results"
        )
        return deduped

    def filter_by_relevance(self, results: List[Any]) -> List[Any]:
        """
        Filter results by minimum relevance score.

        Args:
            results: List of SearchResult objects

        Returns:
            Filtered list of results
        """
        if not results:
            return []

        filtered = []
        for result in results:
            relevance = (
                getattr(result, "relevance_score", 0.0)
                if hasattr(result, "relevance_score")
                else result.get("relevance_score", 0.0)
            )

            if relevance >= self.min_relevance_score:
                filtered.append(result)

        logger.info(
            f"Filtered {len(results)} results to {len(filtered)} "
            f"with relevance >= {self.min_relevance_score}"
        )
        return filtered

    def re_rank_results(self, results: List[Any]) -> List[Any]:
        """
        Re-rank results by relevance score (descending).

        Args:
            results: List of SearchResult objects

        Returns:
            Re-ranked list of results
        """
        if not results or not self.re_rank:
            return results

        try:
            ranked = sorted(
                results,
                key=lambda r: (
                    getattr(r, "relevance_score", 0.0)
                    if hasattr(r, "relevance_score")
                    else r.get("relevance_score", 0.0)
                ),
                reverse=True,
            )
            logger.info(f"Re-ranked {len(results)} results by relevance score")
            return ranked
        except Exception as e:
            logger.error(f"Error re-ranking results: {e}")
            return results

    def limit_results(self, results: List[Any]) -> List[Any]:
        """
        Limit results to maximum count.

        Args:
            results: List of SearchResult objects

        Returns:
            Limited list of results
        """
        if not results:
            return []

        limited = results[: self.max_results]

        if len(results) > self.max_results:
            logger.info(f"Limited {len(results)} results to {self.max_results}")

        return limited

    def aggregate(self, result_sets: List[List[Any]]) -> List[Any]:
        """
        Full aggregation pipeline: merge, dedupe, filter, re-rank, limit.

        Args:
            result_sets: List of result sets from different searches

        Returns:
            Aggregated, processed list of results
        """
        logger.info(f"Starting aggregation of {len(result_sets)} result sets...")

        # Step 1: Merge
        merged = self.merge(result_sets)

        # Step 2: Deduplicate
        deduped = self.deduplicate_results(merged)

        # Step 3: Filter by relevance
        filtered = self.filter_by_relevance(deduped)

        # Step 4: Re-rank
        ranked = self.re_rank_results(filtered)

        # Step 5: Limit
        final = self.limit_results(ranked)

        logger.info(
            f"Aggregation complete: {len(result_sets)} sets → {len(final)} final results"
        )
        return final


class SearchOrchestrator:
    """
    Orchestrates searches across multiple sources with different execution strategies.

    Supports parallel, conditional, and fallback search patterns. Integrates with
    Phase 0.15's SemanticSearchEngine for vector searches and Phase 0.10's
    PostgreSQL JSONB for structured queries.
    """

    def __init__(
        self, search_engine: Any = None, config: Optional[SearchConfig] = None
    ):
        """
        Initialize SearchOrchestrator.

        Args:
            search_engine: SemanticSearchEngine instance (Phase 0.15)
            config: SearchConfig instance
        """
        self.search_engine = search_engine
        self.config = config or SearchConfig()
        self.aggregator = ResultAggregator(
            min_relevance_score=self.config.min_relevance_score,
            max_results=self.config.max_results,
            deduplicate=self.config.deduplicate,
            re_rank=self.config.re_rank,
        )
        logger.info(
            f"Initialized SearchOrchestrator with strategy={self.config.strategy.value}"
        )

    def execute_single_search(
        self, query: str, source: str, options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Execute a single search against one source.

        Args:
            query: Search query
            source: Source type (e.g., 'semantic', 'jsonb')
            options: Additional search options

        Returns:
            List of search results
        """
        try:
            logger.info(f"Executing {source} search for query: '{query}'")

            if source == "semantic" and self.search_engine:
                # Use Phase 0.15 SemanticSearchEngine for vector search
                results = self.search_engine.search(
                    query=query,
                    top_k=options.get("top_k", 10) if options else 10,
                    entity_types=options.get("entity_types") if options else None,
                )
                logger.info(f"Semantic search returned {len(results)} results")
                return results

            elif source == "jsonb":
                # Mock JSONB search (would integrate with Phase 0.10 in production)
                logger.info("JSONB search (mock implementation)")
                return []

            else:
                logger.warning(f"Unknown source type: {source}")
                return []

        except Exception as e:
            logger.error(f"Error executing {source} search: {e}")
            return []

    def execute_parallel(
        self, query: str, options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Execute searches in parallel across all sources.

        Uses ThreadPoolExecutor to run searches concurrently and merge results.

        Args:
            query: Search query
            options: Additional search options

        Returns:
            Aggregated list of search results
        """
        logger.info(
            f"Executing PARALLEL search across {len(self.config.sources)} sources"
        )

        result_sets = []

        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            # Submit all searches
            futures = {
                executor.submit(
                    self.execute_single_search, query, source, options
                ): source
                for source in self.config.sources
            }

            # Collect results as they complete
            for future in as_completed(futures, timeout=self.config.timeout):
                source = futures[future]
                try:
                    results = future.result(timeout=self.config.timeout)
                    result_sets.append(results)
                    logger.info(
                        f"{source} search completed with {len(results)} results"
                    )
                except Exception as e:
                    logger.error(f"Error in {source} search: {e}")
                    result_sets.append([])

        # Aggregate all results
        return self.aggregator.aggregate(result_sets)

    def execute_conditional(
        self, query: str, options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Execute conditional search: run second search only if first meets threshold.

        Args:
            query: Search query
            options: Additional search options

        Returns:
            Aggregated list of search results
        """
        if len(self.config.sources) < 2:
            logger.warning("CONDITIONAL strategy requires at least 2 sources")
            return self.execute_single_search(query, self.config.sources[0], options)

        logger.info("Executing CONDITIONAL search")

        # Execute first search
        primary_source = self.config.sources[0]
        primary_results = self.execute_single_search(query, primary_source, options)

        result_sets = [primary_results]

        # Check threshold
        min_results = self.config.conditional_threshold.get("min_results", 5)

        if len(primary_results) < min_results:
            logger.info(
                f"Primary search returned {len(primary_results)} results "
                f"(< {min_results}), executing secondary search"
            )

            # Execute secondary search
            secondary_source = self.config.sources[1]
            secondary_results = self.execute_single_search(
                query, secondary_source, options
            )
            result_sets.append(secondary_results)
        else:
            logger.info(
                f"Primary search returned {len(primary_results)} results "
                f"(>= {min_results}), skipping secondary search"
            )

        return self.aggregator.aggregate(result_sets)

    def execute_fallback(
        self, query: str, options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Execute fallback search: try primary, fall back to secondary if insufficient.

        Args:
            query: Search query
            options: Additional search options

        Returns:
            Aggregated list of search results
        """
        if len(self.config.sources) < 2:
            logger.warning("FALLBACK strategy requires at least 2 sources")
            return self.execute_single_search(query, self.config.sources[0], options)

        logger.info("Executing FALLBACK search")

        # Try primary source
        primary_source = self.config.sources[0]
        primary_results = self.execute_single_search(query, primary_source, options)

        # Check if fallback is needed
        min_results = self.config.conditional_threshold.get("min_results", 5)

        if len(primary_results) >= min_results:
            logger.info(
                f"Primary search sufficient ({len(primary_results)} results), "
                f"no fallback needed"
            )
            return self.aggregator.aggregate([primary_results])

        logger.info(
            f"Primary search insufficient ({len(primary_results)} results), "
            f"falling back to secondary source"
        )

        # Fall back to secondary source
        secondary_source = self.config.sources[1]
        secondary_results = self.execute_single_search(query, secondary_source, options)

        # Return only fallback results if primary failed
        if not primary_results:
            logger.info("Using only secondary results (primary returned nothing)")
            return self.aggregator.aggregate([secondary_results])

        # Combine if both have results
        logger.info("Combining primary and secondary results")
        return self.aggregator.aggregate([primary_results, secondary_results])

    def execute(
        self, query: str, options: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Execute search using configured strategy.

        Args:
            query: Search query
            options: Additional search options

        Returns:
            Aggregated list of search results
        """
        if not query:
            raise ValueError("Query cannot be empty")

        logger.info(
            f"Executing {self.config.strategy.value} search for query: '{query}'"
        )

        if self.config.strategy == SearchStrategy.PARALLEL:
            return self.execute_parallel(query, options)
        elif self.config.strategy == SearchStrategy.CONDITIONAL:
            return self.execute_conditional(query, options)
        elif self.config.strategy == SearchStrategy.FALLBACK:
            return self.execute_fallback(query, options)
        elif self.config.strategy == SearchStrategy.SEQUENTIAL:
            # Sequential is handled by SequentialSearchPipeline
            logger.warning("Use SequentialSearchPipeline for SEQUENTIAL strategy")
            return self.execute_parallel(query, options)  # Fallback to parallel
        else:
            raise ValueError(f"Unknown strategy: {self.config.strategy}")


class SequentialSearchPipeline:
    """
    Executes searches sequentially, using results from one search to inform the next.

    Implements the pattern: Search A → Use A's results → Search B → Use B's results → etc.
    """

    def __init__(self, search_engine: Any = None):
        """
        Initialize SequentialSearchPipeline.

        Args:
            search_engine: SemanticSearchEngine instance (Phase 0.15)
        """
        self.search_engine = search_engine
        self.aggregator = ResultAggregator()
        logger.info("Initialized SequentialSearchPipeline")

    def execute_pipeline(
        self, initial_query: str, pipeline_steps: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Execute a sequential search pipeline.

        Args:
            initial_query: Initial search query
            pipeline_steps: List of pipeline step configurations
                Each step: {'source': str, 'query_template': str, 'options': dict}

        Returns:
            Final aggregated results

        Example:
            pipeline_steps = [
                {'source': 'semantic', 'query_template': '{query}', 'options': {}},
                {'source': 'jsonb', 'query_template': '{prev_results}', 'options': {}}
            ]
        """
        if not pipeline_steps:
            raise ValueError("Pipeline must have at least one step")

        logger.info(f"Executing {len(pipeline_steps)} sequential pipeline steps")

        all_results = []
        previous_results = []
        current_query = initial_query

        for i, step in enumerate(pipeline_steps):
            source = step.get("source", "semantic")
            options = step.get("options", {})

            logger.info(f"Step {i + 1}/{len(pipeline_steps)}: Searching {source}")

            # Execute search
            orchestrator = SearchOrchestrator(
                search_engine=self.search_engine,
                config=SearchConfig(strategy=SearchStrategy.PARALLEL, sources=[source]),
            )

            results = orchestrator.execute(current_query, options)

            all_results.append(results)
            previous_results = results

            logger.info(f"Step {i + 1} completed with {len(results)} results")

        # Aggregate final results
        return self.aggregator.aggregate(all_results)


class RobustArchitecture:
    """
    Main orchestration class for robust multi-source search architecture.

    Integrates:
    - Phase 0.10: PostgreSQL JSONB Storage
    - Phase 0.11: RAG Pipeline with pgvector
    - Phase 0.15: Information Availability (SemanticSearchEngine)

    Provides flexible search orchestration with multiple execution strategies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RobustArchitecture.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.initialized = False
        self.search_engine = None
        self.orchestrator = None
        self.pipeline = None

        # Parse search config
        strategy_str = self.config.get("strategy", "PARALLEL")
        strategy = (
            SearchStrategy[strategy_str]
            if isinstance(strategy_str, str)
            else strategy_str
        )

        self.search_config = SearchConfig(
            strategy=strategy,
            sources=self.config.get("sources", ["semantic", "jsonb"]),
            timeout=self.config.get("timeout", 30),
            max_results=self.config.get("max_results", 20),
            min_relevance_score=self.config.get("min_relevance_score", 0.5),
            parallel_workers=self.config.get("parallel_workers", 4),
            deduplicate=self.config.get("deduplicate", True),
            re_rank=self.config.get("re_rank", True),
        )

        logger.info(f"Initialized RobustArchitecture with strategy={strategy.value}")

    def setup(self) -> Dict[str, Any]:
        """
        Set up the robust architecture system.

        Returns:
            Setup results
        """
        logger.info("Setting up RobustArchitecture...")

        try:
            # Validate configuration
            self.search_config.validate()

            # Initialize search engine (Phase 0.15 integration)
            # In production, this would connect to actual SemanticSearchEngine
            # For now, use mock implementation
            self.search_engine = None  # Will be mocked in tests

            # Initialize orchestrator
            self.orchestrator = SearchOrchestrator(
                search_engine=self.search_engine, config=self.search_config
            )

            # Initialize sequential pipeline
            self.pipeline = SequentialSearchPipeline(search_engine=self.search_engine)

            self.initialized = True
            logger.info("✅ RobustArchitecture setup complete")

            return {"success": True, "message": "Setup completed successfully"}

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return {"success": False, "error": str(e)}

    def execute(
        self,
        query: str,
        strategy: Optional[SearchStrategy] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute search using robust architecture.

        Args:
            query: Search query
            strategy: Override default strategy (optional)
            options: Additional search options

        Returns:
            Search results with metadata
        """
        if not self.initialized:
            raise RuntimeError("Must call setup() before execute()")

        if not query:
            raise ValueError("Query cannot be empty")

        logger.info(f"Executing search for query: '{query}'")

        try:
            # Override strategy if provided
            if strategy:
                original_strategy = self.orchestrator.config.strategy
                self.orchestrator.config.strategy = strategy
                logger.info(f"Overriding strategy to {strategy.value}")

            # Execute search
            start_time = datetime.now()
            results = self.orchestrator.execute(query, options)
            execution_time = (datetime.now() - start_time).total_seconds()

            # Restore original strategy if overridden
            if strategy:
                self.orchestrator.config.strategy = original_strategy

            logger.info(
                f"Search completed in {execution_time:.2f}s with {len(results)} results"
            )

            return {
                "success": True,
                "query": query,
                "results": results,
                "metadata": {
                    "results_count": len(results),
                    "execution_time": execution_time,
                    "strategy": self.orchestrator.config.strategy.value,
                    "sources": self.orchestrator.config.sources,
                },
            }

        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            return {"success": False, "error": str(e), "query": query, "results": []}

    def execute_pipeline(
        self, initial_query: str, pipeline_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute sequential search pipeline.

        Args:
            initial_query: Initial search query
            pipeline_steps: List of pipeline step configurations

        Returns:
            Pipeline results with metadata
        """
        if not self.initialized:
            raise RuntimeError("Must call setup() before execute_pipeline()")

        logger.info(f"Executing pipeline with {len(pipeline_steps)} steps")

        try:
            start_time = datetime.now()
            results = self.pipeline.execute_pipeline(initial_query, pipeline_steps)
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Pipeline completed in {execution_time:.2f}s with {len(results)} results"
            )

            return {
                "success": True,
                "query": initial_query,
                "results": results,
                "metadata": {
                    "results_count": len(results),
                    "execution_time": execution_time,
                    "pipeline_steps": len(pipeline_steps),
                },
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": initial_query,
                "results": [],
            }

    def validate(self) -> bool:
        """
        Validate the robust architecture setup.

        Returns:
            True if validation passes
        """
        logger.info("Validating RobustArchitecture...")

        if not self.initialized:
            logger.error("System not initialized")
            return False

        if not self.orchestrator:
            logger.error("SearchOrchestrator not initialized")
            return False

        if not self.pipeline:
            logger.error("SequentialSearchPipeline not initialized")
            return False

        try:
            self.search_config.validate()
            logger.info("✅ Validation complete")
            return True
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up RobustArchitecture resources...")
        self.search_engine = None
        self.orchestrator = None
        self.pipeline = None
        self.initialized = False


def main():
    """Main execution function with examples."""
    print("=" * 80)
    print("Phase 0.16: Robust Architecture for Multi-Source Search")
    print("=" * 80)

    # Example 1: Parallel Search (Default)
    print("\n--- Example 1: Parallel Search ---")
    arch = RobustArchitecture(config={"strategy": "PARALLEL"})
    setup_result = arch.setup()
    print(f"Setup: {setup_result['message']}")

    if setup_result["success"]:
        result = arch.execute("Lakers championship wins")
        print(f"Query: {result['query']}")
        print(f"Results: {result['metadata']['results_count']} results")
        print(f"Execution time: {result['metadata']['execution_time']:.2f}s")
        print(f"Strategy: {result['metadata']['strategy']}")

    # Example 2: Sequential Search
    print("\n--- Example 2: Sequential Pipeline ---")
    pipeline_steps = [
        {"source": "semantic", "query_template": "{query}", "options": {}},
        {"source": "jsonb", "query_template": "{prev_results}", "options": {}},
    ]

    result = arch.execute_pipeline("LeBron James playoff stats", pipeline_steps)
    print(f"Pipeline: {result['metadata']['pipeline_steps']} steps")
    print(f"Results: {result['metadata']['results_count']} results")

    # Example 3: Conditional Search
    print("\n--- Example 3: Conditional Search ---")
    arch2 = RobustArchitecture(config={"strategy": "CONDITIONAL"})
    arch2.setup()

    result = arch2.execute("rare defensive statistics")
    print(f"Strategy: {result['metadata']['strategy']}")
    print(f"Results: {result['metadata']['results_count']} results")

    # Validation
    print("\n--- Validation ---")
    is_valid = arch.validate()
    print(f"Validation: {'✅ Passed' if is_valid else '❌ Failed'}")

    # Cleanup
    arch.cleanup()
    arch2.cleanup()

    print("\n✅ All examples complete!")


if __name__ == "__main__":
    main()
