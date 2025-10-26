#!/usr/bin/env python3
"""
0.0012: RAG + LLM Integration - Main CLI

Natural language query interface for NBA temporal panel data.
Combines retrieval-augmented generation with LLM for intelligent responses.

Usage:
    python scripts/0_12/main.py query "Who were the best shooters in 2022?"
    python scripts/0_12/main.py interactive
    python scripts/0_12/main.py metrics

Part of 0.0012: RAG + LLM Integration (rec_188)
"""

import os
import sys
import argparse
import psycopg2
from pgvector.psycopg2 import register_vector

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))

from scripts.ml.query_understanding import QueryUnderstanding
from scripts.ml.rag_retrieval import TemporalRAGRetrieval
from scripts.ml.prompt_builder import PromptBuilder
from scripts.ml.llm_integration import LLMIntegration


class RAGLLM:
    """Complete RAG + LLM system for NBA queries"""

    def __init__(
        self,
        db_connection: psycopg2.extensions.connection,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_k: int = 10,
    ):
        """
        Initialize RAG+LLM system.

        Args:
            db_connection: PostgreSQL connection
            model: LLM model name
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            top_k: Number of contexts to retrieve
        """
        self.conn = db_connection

        # Initialize components
        self.query_parser = QueryUnderstanding(db_connection)
        self.retrieval = TemporalRAGRetrieval(db_connection)
        self.prompt_builder = PromptBuilder(model=model)
        self.llm = LLMIntegration(
            model=model, temperature=temperature, max_tokens=max_tokens
        )

        self.top_k = top_k
        self.verbose = False

    def query(self, question: str, stream: bool = True) -> str:
        """
        Answer a question using RAG + LLM.

        Args:
            question: User's natural language question
            stream: Whether to stream response

        Returns:
            Generated answer
        """
        if self.verbose:
            print("\n" + "=" * 80)
            print(f"Question: {question}")
            print("=" * 80)

        # 1. Understand query
        if self.verbose:
            print("\n[1/4] Analyzing query...")

        analysis = self.query_parser.analyze_query(question)

        if self.verbose:
            print(f"  Intent: {analysis['intent']}")
            print(f"  Type: {analysis['query_type']}")
            print(f"  Confidence: {analysis['confidence']:.2%}")
            if analysis["entities"]["players"]:
                print(f"  Players: {', '.join(analysis['entities']['players'])}")
            if analysis["temporal"]["season"]:
                print(f"  Season: {analysis['temporal']['season']}")

        # 2. Retrieve context
        if self.verbose:
            print("\n[2/4] Retrieving relevant context...")

        contexts = self.retrieval.retrieve_context(question, analysis, top_k=self.top_k)

        if self.verbose:
            print(f"  Retrieved {len(contexts)} context items")

        # Enrich with JSONB data
        contexts = self.retrieval.enrich_with_jsonb(contexts)

        # 3. Build prompt
        if self.verbose:
            print("\n[3/4] Building prompt...")

        prompt = self.prompt_builder.build_prompt(
            question, contexts, analysis, max_tokens=3000
        )
        system_prompt = self.prompt_builder.get_system_prompt()

        # Estimate cost
        cost_estimate = self.prompt_builder.estimate_cost(
            prompt, response_tokens=self.llm.max_tokens
        )

        if self.verbose:
            print(f"  Prompt tokens: {cost_estimate['prompt_tokens']}")
            print(f"  Estimated cost: ${cost_estimate['total_cost']:.4f}")

        # 4. Generate response
        if self.verbose:
            print("\n[4/4] Generating response...")

        response = self.llm.generate_response(prompt, system_prompt, stream=stream)

        if self.verbose:
            print("\n" + "=" * 80)
            print("Answer:")
            print("=" * 80)

        return response

    def interactive_mode(self):
        """Run interactive query loop"""
        print("\n" + "=" * 80)
        print("NBA RAG+LLM Interactive Mode")
        print("=" * 80)
        print("\nAsk questions about NBA players, games, and statistics.")
        print("Commands:")
        print("  /metrics  - Show usage metrics")
        print("  /verbose  - Toggle verbose output")
        print("  /quit     - Exit")
        print()

        while True:
            try:
                # Get question
                question = input("\n>>> ").strip()

                if not question:
                    continue

                # Handle commands
                if question.startswith("/"):
                    command = question[1:].lower()

                    if command == "quit":
                        print("\nExiting...")
                        break
                    elif command == "metrics":
                        self._show_metrics()
                        continue
                    elif command == "verbose":
                        self.verbose = not self.verbose
                        print(f"Verbose mode: {'ON' if self.verbose else 'OFF'}")
                        continue
                    else:
                        print(f"Unknown command: {question}")
                        continue

                # Answer question
                answer = self.query(question, stream=True)

                if not self.verbose:
                    print(f"\n{answer}")

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                import traceback

                traceback.print_exc()

    def _show_metrics(self):
        """Display usage metrics"""
        metrics = self.llm.get_metrics()

        print("\n" + "=" * 80)
        print("Usage Metrics")
        print("=" * 80)
        print(f"Total Requests: {metrics['request_count']}")
        print(f"Total Tokens: {metrics['total_tokens']:,}")
        print(f"  - Prompt: {metrics['total_prompt_tokens']:,}")
        print(f"  - Completion: {metrics['total_completion_tokens']:,}")
        print(f"Total Cost: ${metrics['total_cost']:.4f}")
        print(f"Average Cost/Request: ${metrics['average_cost_per_request']:.4f}")
        print(f"Cache Size: {metrics['cache_size']} entries")
        print("=" * 80)


def get_db_connection() -> psycopg2.extensions.connection:
    """
    Get PostgreSQL database connection.

    Returns:
        Database connection

    Raises:
        ConnectionError: If connection fails
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "nba_data"),
            user=os.getenv("POSTGRES_USER", "nba_admin"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )

        # Register pgvector
        register_vector(conn)

        return conn

    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NBA RAG+LLM - Natural language query interface"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a single question")
    query_parser.add_argument("question", type=str, help="Question to ask")
    query_parser.add_argument("--model", default="gpt-4", help="LLM model")
    query_parser.add_argument(
        "--temperature", type=float, default=0.7, help="Temperature"
    )
    query_parser.add_argument("--max-tokens", type=int, default=1000, help="Max tokens")
    query_parser.add_argument(
        "--top-k", type=int, default=10, help="Context items to retrieve"
    )
    query_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    query_parser.add_argument(
        "--no-stream", action="store_true", help="Disable streaming"
    )

    # Interactive mode
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode")
    interactive_parser.add_argument("--model", default="gpt-4", help="LLM model")
    interactive_parser.add_argument(
        "--temperature", type=float, default=0.7, help="Temperature"
    )
    interactive_parser.add_argument(
        "--max-tokens", type=int, default=1000, help="Max tokens"
    )
    interactive_parser.add_argument(
        "--top-k", type=int, default=10, help="Context items"
    )
    interactive_parser.add_argument(
        "--verbose", action="store_true", help="Verbose output"
    )

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Show metrics")

    args = parser.parse_args()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    # Connect to database
    try:
        conn = get_db_connection()
        print(f"✓ Connected to PostgreSQL database")
    except ConnectionError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        # Initialize RAG+LLM system
        rag = RAGLLM(
            conn,
            model=getattr(args, "model", "gpt-4"),
            temperature=getattr(args, "temperature", 0.7),
            max_tokens=getattr(args, "max_tokens", 1000),
            top_k=getattr(args, "top_k", 10),
        )

        rag.verbose = getattr(args, "verbose", False)

        # Execute command
        if args.command == "query":
            # Single query
            answer = rag.query(args.question, stream=not args.no_stream)

            if not rag.verbose:
                print(f"\n{answer}")

            # Show metrics
            print()
            rag._show_metrics()

        elif args.command == "interactive":
            # Interactive mode
            rag.interactive_mode()

            # Show final metrics
            print()
            rag._show_metrics()

        elif args.command == "metrics":
            # Just show metrics
            rag._show_metrics()

        else:
            parser.print_help()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
