#!/usr/bin/env python3
"""
Phase 0.0011: OpenAI Embedding Generator

Purpose: Generate embeddings using OpenAI API
Created: October 25, 2025
Implementation ID: rec_034_pgvector

Usage:
    embedder = OpenAIEmbedder()
    embedding = embedder.generate_embedding("LeBron James, Lakers power forward")
"""

import os
import time
from typing import List, Optional, Dict
import openai
from openai import OpenAI


class OpenAIEmbedder:
    """
    Generate embeddings using OpenAI's text-embedding models

    Supports rate limiting, retries, and cost tracking
    """

    def __init__(
        self,
        model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize OpenAI embedder

        Args:
            model: OpenAI embedding model to use
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )

        self.client = OpenAI(api_key=api_key)

        # Model specifications
        self.model_specs = {
            "text-embedding-ada-002": {
                "dimension": 1536,
                "cost_per_1k_tokens": 0.0001,  # $0.0001 per 1K tokens
                "max_tokens": 8191,
            },
            "text-embedding-3-small": {
                "dimension": 1536,
                "cost_per_1k_tokens": 0.00002,  # $0.00002 per 1K tokens
                "max_tokens": 8191,
            },
            "text-embedding-3-large": {
                "dimension": 3072,
                "cost_per_1k_tokens": 0.00013,  # $0.00013 per 1K tokens
                "max_tokens": 8191,
            },
        }

        if model not in self.model_specs:
            raise ValueError(
                f"Unknown model: {model}. Supported models: {list(self.model_specs.keys())}"
            )

        self.dimension = self.model_specs[model]["dimension"]
        self.cost_per_1k_tokens = self.model_specs[model]["cost_per_1k_tokens"]

        # Statistics
        self.stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "total_failures": 0,
        }

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not text or not text.strip():
            return None

        # Clean text
        text = text.strip()

        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(text) // 4

        for attempt in range(self.max_retries):
            try:
                # Call OpenAI API
                response = self.client.embeddings.create(model=self.model, input=text)

                # Extract embedding
                embedding = response.data[0].embedding

                # Update statistics
                tokens_used = response.usage.total_tokens
                cost = (tokens_used / 1000) * self.cost_per_1k_tokens

                self.stats["total_calls"] += 1
                self.stats["total_tokens"] += tokens_used
                self.stats["total_cost_usd"] += cost

                return embedding

            except openai.RateLimitError as e:
                # Rate limit hit, wait and retry
                wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                print(
                    f"⚠️  Rate limit hit. Waiting {wait_time:.1f}s before retry {attempt + 1}/{self.max_retries}"
                )
                time.sleep(wait_time)

            except openai.APIError as e:
                # API error, retry
                if attempt < self.max_retries - 1:
                    print(
                        f"⚠️  API error: {e}. Retrying {attempt + 1}/{self.max_retries}"
                    )
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ API error after {self.max_retries} attempts: {e}")
                    self.stats["total_failures"] += 1
                    return None

            except Exception as e:
                print(f"❌ Unexpected error generating embedding: {e}")
                self.stats["total_failures"] += 1
                return None

        # All retries exhausted
        print(f"❌ Failed to generate embedding after {self.max_retries} attempts")
        self.stats["total_failures"] += 1
        return None

    def generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts

        Note: This processes texts one at a time. For true batch processing,
        use OpenAI's batch API (not implemented here for simplicity).

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (same order as input)
        """
        embeddings = []

        for i, text in enumerate(texts):
            if (i + 1) % 10 == 0:
                print(f"  Processing {i + 1}/{len(texts)}...")

            embedding = self.generate_embedding(text)
            embeddings.append(embedding)

            # Rate limiting: sleep briefly between requests
            if i < len(texts) - 1:  # Don't sleep after last request
                time.sleep(0.05)  # 50ms delay = ~20 requests/second

        return embeddings

    def estimate_cost(self, text: str) -> float:
        """
        Estimate cost for embedding a text

        Args:
            text: Text to embed

        Returns:
            Estimated cost in USD
        """
        # Rough token estimate: 1 token ≈ 4 characters
        estimated_tokens = len(text) // 4
        estimated_cost = (estimated_tokens / 1000) * self.cost_per_1k_tokens
        return estimated_cost

    def estimate_batch_cost(self, texts: List[str]) -> Dict:
        """
        Estimate cost for embedding multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            Dictionary with cost estimates
        """
        total_chars = sum(len(t) for t in texts)
        total_tokens = total_chars // 4
        total_cost = (total_tokens / 1000) * self.cost_per_1k_tokens

        return {
            "total_texts": len(texts),
            "total_chars": total_chars,
            "estimated_tokens": total_tokens,
            "estimated_cost_usd": total_cost,
            "cost_per_text": total_cost / len(texts) if texts else 0,
        }

    def get_stats(self) -> Dict:
        """
        Get embedding generation statistics

        Returns:
            Dictionary with statistics
        """
        stats = self.stats.copy()

        # Add derived metrics
        if stats["total_calls"] > 0:
            stats["avg_tokens_per_call"] = stats["total_tokens"] / stats["total_calls"]
            stats["avg_cost_per_call"] = stats["total_cost_usd"] / stats["total_calls"]
        else:
            stats["avg_tokens_per_call"] = 0
            stats["avg_cost_per_call"] = 0

        stats["success_rate"] = (
            (stats["total_calls"] - stats["total_failures"]) / stats["total_calls"]
            if stats["total_calls"] > 0
            else 0
        )

        return stats

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "total_failures": 0,
        }

    def print_stats(self):
        """Print statistics summary"""
        stats = self.get_stats()

        print(f"\n{'='*50}")
        print("OpenAI Embedder Statistics")
        print(f"{'='*50}\n")

        print(f"Model:             {self.model}")
        print(f"Dimension:         {self.dimension}")
        print(f"Cost per 1K tokens: ${self.cost_per_1k_tokens:.6f}")
        print()

        print(f"Total API Calls:   {stats['total_calls']:,}")
        print(f"Total Tokens:      {stats['total_tokens']:,}")
        print(f"Total Cost (USD):  ${stats['total_cost_usd']:.6f}")
        print(f"Total Failures:    {stats['total_failures']:,}")
        print()

        if stats["total_calls"] > 0:
            print(f"Avg Tokens/Call:   {stats['avg_tokens_per_call']:.1f}")
            print(f"Avg Cost/Call:     ${stats['avg_cost_per_call']:.6f}")
            print(f"Success Rate:      {stats['success_rate']:.1%}")

        print()


# Example usage
if __name__ == "__main__":
    # Test the embedder
    embedder = OpenAIEmbedder()

    # Test single embedding
    print("Testing single embedding...")
    text = "LeBron James, Los Angeles Lakers power forward, 4-time NBA champion"
    embedding = embedder.generate_embedding(text)

    if embedding:
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")
    else:
        print("❌ Failed to generate embedding")

    # Test batch embedding
    print("\nTesting batch embeddings...")
    texts = [
        "Stephen Curry, Golden State Warriors point guard",
        "Kevin Durant, Phoenix Suns forward",
        "Giannis Antetokounmpo, Milwaukee Bucks forward",
    ]

    embeddings = embedder.generate_embeddings_batch(texts)
    successful = sum(1 for e in embeddings if e is not None)
    print(f"✅ Generated {successful}/{len(texts)} embeddings")

    # Print statistics
    embedder.print_stats()
