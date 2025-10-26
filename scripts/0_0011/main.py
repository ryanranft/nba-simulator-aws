#!/usr/bin/env python3
"""
0.0011: RAG Pipeline Main Interface

Purpose: Unified CLI for RAG pipeline operations
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    # Initialize database
    python scripts/0_11/main.py init

    # Generate embeddings
    python scripts/0_11/main.py embed --entity-type player --limit 100

    # Search
    python scripts/0_11/main.py search "best Lakers players"

    # Get stats
    python scripts/0_11/main.py stats
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.db.0_0011_init import RAGDatabaseInitializer
from scripts.0_0011.embedding_pipeline import EmbeddingPipeline
from scripts.0_0011.vector_search import VectorSearch
from scripts.0_0011.rag_queries import RAGQueries


def cmd_init(args):
    """Initialize RAG database schema"""
    initializer = RAGDatabaseInitializer()
    success = initializer.initialize(verify_only=args.verify_only)
    sys.exit(0 if success else 1)


def cmd_embed(args):
    """Generate embeddings"""
    pipeline = EmbeddingPipeline(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    try:
        if args.entity_type in ['player', 'all']:
            pipeline.process_players(limit=args.limit)

        if args.entity_type in ['game', 'all']:
            pipeline.process_games(limit=args.limit)

        pipeline.print_summary()
        sys.exit(0)

    except Exception as e:
        print(f"❌ Embedding error: {e}")
        pipeline.print_summary()
        sys.exit(1)

    finally:
        pipeline.close()


def cmd_search(args):
    """Perform search"""
    with VectorSearch() as search:
        if args.hybrid:
            results = search.hybrid_search(
                args.query,
                entity_type=args.type,
                limit=args.limit
            )
        else:
            results = search.similarity_search(
                args.query,
                entity_type=args.type,
                limit=args.limit
            )

        search.print_results(results, show_metadata=args.metadata)


def cmd_stats(args):
    """Show RAG statistics"""
    with RAGQueries() as rag:
        stats = rag.get_stats()

        print(f"\n{'='*60}")
        print("RAG Pipeline Statistics")
        print(f"{'='*60}\n")

        print(f"Total Embeddings: {stats['total_embeddings']:,}\n")

        if stats['embeddings_by_type']:
            for entity_type, data in stats['embeddings_by_type'].items():
                print(f"{entity_type.upper()}:")
                print(f"  Count:           {data['count']:,}")
                print(f"  Avg Text Length: {data['avg_text_length']:.1f} chars")

                if data['earliest_created']:
                    print(f"  Earliest:        {data['earliest_created']}")
                if data['latest_created']:
                    print(f"  Latest:          {data['latest_created']}")

                print()
        else:
            print("No embeddings found. Run 'main.py embed' to generate embeddings.")
            print()


def cmd_compare(args):
    """Compare two players"""
    with RAGQueries() as rag:
        comparison = rag.player_comparison(args.player1, args.player2)

        if 'error' in comparison:
            print(f"❌ {comparison['error']}")
            sys.exit(1)

        print(f"\n{'='*60}")
        print("Player Comparison")
        print(f"{'='*60}\n")

        print(f"Player 1: {comparison['player1']['name']}")
        print(f"{comparison['player1']['description']}\n")

        print(f"Player 2: {comparison['player2']['name']}")
        print(f"{comparison['player2']['description']}\n")

        if comparison['similarity'] is not None:
            print(f"Similarity Score: {comparison['similarity']:.4f}")
            print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='0.0011: RAG Pipeline for NBA Data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database schema
  python scripts/0_11/main.py init

  # Generate player embeddings (first 100)
  python scripts/0_11/main.py embed --entity-type player --limit 100

  # Search for players
  python scripts/0_11/main.py search "best three-point shooters"

  # Compare two players
  python scripts/0_11/main.py compare "LeBron James" "Michael Jordan"

  # Show statistics
  python scripts/0_11/main.py stats
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Init command
    parser_init = subparsers.add_parser('init', help='Initialize RAG database schema')
    parser_init.add_argument('--verify-only', action='store_true', help='Verify without changes')
    parser_init.set_defaults(func=cmd_init)

    # Embed command
    parser_embed = subparsers.add_parser('embed', help='Generate embeddings')
    parser_embed.add_argument('--entity-type', choices=['player', 'game', 'all'], default='all')
    parser_embed.add_argument('--limit', type=int, help='Limit number of records')
    parser_embed.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser_embed.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser_embed.set_defaults(func=cmd_embed)

    # Search command
    parser_search = subparsers.add_parser('search', help='Search embeddings')
    parser_search.add_argument('query', help='Search query')
    parser_search.add_argument('--type', choices=['player', 'game'], help='Filter by type')
    parser_search.add_argument('--limit', type=int, default=10, help='Number of results')
    parser_search.add_argument('--hybrid', action='store_true', help='Use hybrid search')
    parser_search.add_argument('--metadata', action='store_true', help='Show metadata')
    parser_search.set_defaults(func=cmd_search)

    # Compare command
    parser_compare = subparsers.add_parser('compare', help='Compare two players')
    parser_compare.add_argument('player1', help='First player name')
    parser_compare.add_argument('player2', help='Second player name')
    parser_compare.set_defaults(func=cmd_compare)

    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show RAG statistics')
    parser_stats.set_defaults(func=cmd_stats)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
