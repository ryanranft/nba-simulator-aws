"""
LLM Integration Module with Streaming Support

Integrates with OpenAI GPT-4/3.5 and other LLMs.
Supports streaming responses, cost tracking, and response caching.

Part of Phase 0.0012: RAG + LLM Integration (rec_188)
"""

import os
import json
import time
from typing import Dict, List, Optional, Generator
from datetime import datetime
import openai


class LLMIntegration:
    """LLM integration with streaming and cost tracking"""

    def __init__(
        self, model: str = "gpt-4", temperature: float = 0.7, max_tokens: int = 1000
    ):
        """
        Initialize LLM integration.

        Args:
            model: LLM model name
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum response tokens
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize OpenAI API
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Cost tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0

        # Response cache (simple in-memory cache)
        self.cache = {}
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hour

    def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        stream: bool = True,
        use_cache: bool = True,
    ) -> str:
        """
        Generate LLM response.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            stream: Whether to stream response
            use_cache: Whether to use cached responses

        Returns:
            Generated response text
        """
        # Check cache
        if use_cache and self.cache_enabled:
            cached_response = self._get_cached_response(prompt, system_prompt)
            if cached_response:
                print("  [Using cached response]")
                return cached_response

        # Generate response
        if stream:
            response_text = self._generate_streaming(prompt, system_prompt)
        else:
            response_text = self._generate_standard(prompt, system_prompt)

        # Cache response
        if use_cache and self.cache_enabled:
            self._cache_response(prompt, system_prompt, response_text)

        return response_text

    def _generate_streaming(self, prompt: str, system_prompt: str) -> str:
        """
        Generate response with streaming for better UX.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Complete response text
        """
        try:
            start_time = time.time()

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

            full_response = ""
            print("\n  [Streaming response...]")

            for chunk in response:
                if chunk.choices[0].delta.get("content"):
                    content = chunk.choices[0].delta.content
                    full_response += content
                    print(content, end="", flush=True)

            print()  # New line after streaming

            # Track metrics (approximate for streaming)
            elapsed = time.time() - start_time
            self._update_metrics(prompt, full_response, elapsed)

            return full_response

        except Exception as e:
            print(f"\n  [Error generating streaming response: {e}]")
            raise

    def _generate_standard(self, prompt: str, system_prompt: str) -> str:
        """
        Standard non-streaming generation.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Response text
        """
        try:
            start_time = time.time()

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            response_text = response.choices[0].message.content

            # Track metrics
            elapsed = time.time() - start_time
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            self._update_metrics(
                prompt, response_text, elapsed, prompt_tokens, completion_tokens
            )

            return response_text

        except Exception as e:
            print(f"\n  [Error generating response: {e}]")
            raise

    def _update_metrics(
        self,
        prompt: str,
        response: str,
        elapsed: float,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ):
        """
        Update usage metrics and cost tracking.

        Args:
            prompt: Prompt text
            response: Response text
            elapsed: Time elapsed (seconds)
            prompt_tokens: Number of prompt tokens (or None to estimate)
            completion_tokens: Number of completion tokens (or None to estimate)
        """
        # Estimate tokens if not provided
        if prompt_tokens is None:
            prompt_tokens = len(prompt) // 4  # Rough estimate
        if completion_tokens is None:
            completion_tokens = len(response) // 4

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.request_count += 1

        # Calculate cost
        cost = self._calculate_cost(prompt_tokens, completion_tokens)
        self.total_cost += cost

        # Log metrics
        print(
            f"\n  [Metrics: {prompt_tokens} + {completion_tokens} tokens, "
            f"${cost:.4f}, {elapsed:.2f}s]"
        )

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost based on token usage.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Total cost in USD
        """
        # Pricing as of 2025 (subject to change)
        pricing = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
            "gpt-4-turbo": {"input": 0.01 / 1000, "output": 0.03 / 1000},
        }

        model_pricing = pricing.get(self.model, pricing["gpt-4"])

        input_cost = prompt_tokens * model_pricing["input"]
        output_cost = completion_tokens * model_pricing["output"]

        return input_cost + output_cost

    def _get_cached_response(self, prompt: str, system_prompt: str) -> Optional[str]:
        """
        Get cached response if available and not expired.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Cached response or None
        """
        cache_key = self._make_cache_key(prompt, system_prompt)

        if cache_key in self.cache:
            cached = self.cache[cache_key]

            # Check expiration
            if time.time() - cached["timestamp"] < self.cache_ttl:
                return cached["response"]
            else:
                # Expired, remove from cache
                del self.cache[cache_key]

        return None

    def _cache_response(self, prompt: str, system_prompt: str, response: str):
        """
        Cache response.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            response: Response to cache
        """
        cache_key = self._make_cache_key(prompt, system_prompt)

        self.cache[cache_key] = {"response": response, "timestamp": time.time()}

    def _make_cache_key(self, prompt: str, system_prompt: str) -> str:
        """
        Create cache key from prompts.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Cache key string
        """
        import hashlib

        combined = f"{system_prompt}|||{prompt}|||{self.model}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_metrics(self) -> Dict:
        """
        Get usage metrics.

        Returns:
            Dictionary with metrics
        """
        return {
            "request_count": self.request_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost": self.total_cost,
            "average_cost_per_request": self.total_cost / max(self.request_count, 1),
            "cache_size": len(self.cache),
        }

    def reset_metrics(self):
        """Reset usage metrics"""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0

    def clear_cache(self):
        """Clear response cache"""
        self.cache = {}

    def save_metrics(self, filepath: str):
        """
        Save metrics to file.

        Args:
            filepath: Path to save metrics JSON
        """
        metrics = self.get_metrics()
        metrics["timestamp"] = datetime.now().isoformat()
        metrics["model"] = self.model

        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"  [Metrics saved to {filepath}]")


# Standalone testing
if __name__ == "__main__":
    import sys

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Test LLM integration
    llm = LLMIntegration(model="gpt-3.5-turbo", max_tokens=200)

    system_prompt = """You are an expert NBA analyst.
Provide accurate, insightful analysis based on facts."""

    test_prompts = [
        "Who is LeBron James?",
        "Compare LeBron James and Michael Jordan in 50 words.",
    ]

    print("Testing LLM Integration")
    print("=" * 80)

    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        print("-" * 80)

        response = llm.generate_response(prompt, system_prompt, stream=True)

        print()

    # Show metrics
    print("\n" + "=" * 80)
    print("Final Metrics:")
    metrics = llm.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
