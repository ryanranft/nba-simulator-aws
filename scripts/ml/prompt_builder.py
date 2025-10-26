"""
Prompt Builder Module with Token Optimization

Builds optimized prompts for LLM with context assembly and token management.
Implements intent-specific instructions and token-efficient formatting.

Part of 0.0012: RAG + LLM Integration (rec_188)
"""

import json
from typing import Dict, List, Optional

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Token counting will be approximate.")


class PromptBuilder:
    """Build optimized prompts for NBA RAG+LLM"""

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize prompt builder.

        Args:
            model: LLM model name for token encoding
        """
        self.model = model

        # Initialize tokenizer if available
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoder = tiktoken.encoding_for_model(model)
            except KeyError:
                print(f"Warning: Model {model} not found, using cl100k_base encoding")
                self.encoder = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoder = None

        # Intent-specific instructions
        self.intent_instructions = {
            "comparison": """You are comparing NBA players or teams.
Provide a balanced analysis highlighting strengths and weaknesses of each.
Use statistics to support your comparisons and provide historical context.
Consider multiple dimensions: offensive skills, defensive ability, leadership, clutch performance.""",
            "narrative": """You are describing NBA game events with vivid detail.
Provide engaging play-by-play narrative with context about game significance.
Explain momentum shifts, key moments, and strategic decisions.
Help the reader visualize the action as if watching live.""",
            "statistics": """You are analyzing NBA statistics with expert insight.
Present numbers clearly with context about league averages and historical significance.
Explain what the statistics reveal about performance, trends, and player/team quality.
Use advanced metrics when relevant (PER, TS%, Win Shares, etc.).""",
            "ranking": """You are ranking NBA entities (players, teams, performances).
Provide a clear ranked list with detailed justification for each ranking.
Consider multiple dimensions: stats, impact, context, longevity, peak performance.
Acknowledge legitimate debates and alternative viewpoints.""",
            "prediction": """You are making NBA predictions based on data and analysis.
Provide probabilistic forecasts with confidence levels and key assumptions.
Explain the reasoning behind predictions using historical patterns and current trends.
Acknowledge uncertainty and factors that could change the forecast.""",
            "general": """You are an expert NBA analyst with comprehensive historical knowledge.
Provide accurate, insightful analysis based on the data context provided.
When uncertain, acknowledge limitations and explain your reasoning.
Focus on temporal aspects when relevant (career progression, momentum, trends).""",
        }

    def build_prompt(
        self,
        question: str,
        contexts: List[Dict],
        query_analysis: Dict,
        max_tokens: int = 3000,
    ) -> str:
        """
        Build context-aware prompt for LLM.

        Args:
            question: User's question
            contexts: Retrieved context dictionaries
            query_analysis: Query analysis from QueryUnderstanding
            max_tokens: Maximum tokens for context (reserve 30% for response)

        Returns:
            Formatted prompt string
        """
        # Get intent-specific instructions
        intent = query_analysis.get("intent", "general")
        instructions = self.intent_instructions.get(
            intent, self.intent_instructions["general"]
        )

        # Assemble context with token limits
        context_text = self._assemble_context(
            contexts, max_tokens=int(max_tokens * 0.7)  # Reserve 30% for response
        )

        # Build final prompt
        prompt = f"""{instructions}

Context from NBA Database:
{context_text}

Question: {question}

Please provide a comprehensive answer based on the context above. Include specific statistics and details when relevant."""

        return prompt

    def get_system_prompt(self) -> str:
        """
        Get system prompt for NBA analyst persona.

        Returns:
            System prompt string
        """
        return """You are an expert NBA analyst with access to comprehensive historical and real-time NBA data.

Your knowledge includes:
- Player statistics, career trajectories, and biographical information
- Game-level data, play-by-play events, and momentum analysis
- Team performance, strategies, and dynamics
- Historical context, era comparisons, and league trends
- Advanced analytics (PER, TS%, Win Shares, BPM, VORP, etc.)
- Temporal patterns (career progression, seasonal trends, game flow)

Guidelines:
- Provide accurate, insightful answers based on the data context provided
- Use specific statistics to support claims
- When uncertain, acknowledge limitations and explain reasoning
- Focus on temporal aspects when relevant (how things change over time)
- Consider context: era adjustments, rule changes, competition level
- Be objective and balanced in comparisons
- Explain advanced concepts clearly for general audiences"""

    def _assemble_context(self, contexts: List[Dict], max_tokens: int) -> str:
        """
        Assemble context with token limits.

        Args:
            contexts: List of context dictionaries
            max_tokens: Maximum tokens allowed

        Returns:
            Formatted context string
        """
        context_parts = []
        token_count = 0

        for ctx in contexts:
            # Format context based on source type
            formatted = self._format_context(ctx)

            # Check token limit
            ctx_tokens = self._count_tokens(formatted)

            if token_count + ctx_tokens > max_tokens:
                # Stop adding contexts if limit reached
                break

            context_parts.append(formatted)
            token_count += ctx_tokens

        if not context_parts:
            return "No relevant context found in database."

        return "\n\n---\n\n".join(context_parts)

    def _format_context(self, ctx: Dict) -> str:
        """
        Format a single context based on its source type.

        Args:
            ctx: Context dictionary

        Returns:
            Formatted context string
        """
        source = ctx.get("source", "unknown")

        if source == "player" or source == "player_stats":
            return self._format_player_context(ctx)
        elif source == "game":
            return self._format_game_context(ctx)
        elif source == "play":
            return self._format_play_context(ctx)
        elif source == "team" or source == "team_stats":
            return self._format_team_context(ctx)
        else:
            return self._format_generic_context(ctx)

    def _format_player_context(self, ctx: Dict) -> str:
        """Format player context with stats"""
        player_name = ctx.get("metadata", {}).get("name", "Unknown Player")
        content = ctx.get("content", "")

        # Extract stats if available
        career_stats = ctx.get("career_stats", {})
        season_stats = ctx.get("season_stats", {})

        formatted = f"[PLAYER: {player_name}]\n"
        formatted += f"{content}\n"

        if career_stats:
            formatted += f"\nCareer Statistics:\n"
            formatted += self._format_stats_dict(career_stats)

        if season_stats:
            formatted += f"\nSeason Statistics:\n"
            formatted += self._format_stats_dict(season_stats)

        # Add similarity score if available
        if "similarity" in ctx:
            formatted += f"\n(Relevance: {ctx['similarity']:.2%})"

        return formatted

    def _format_game_context(self, ctx: Dict) -> str:
        """Format game context"""
        metadata = ctx.get("metadata", {})
        game_date = metadata.get("game_date", "Unknown date")
        teams = metadata.get("matchup", "Unknown matchup")

        formatted = f"[GAME: {teams} on {game_date}]\n"
        formatted += ctx.get("content", "")

        if "raw_data" in ctx:
            raw = ctx["raw_data"]
            if "final_score" in raw:
                formatted += f"\nFinal Score: {raw['final_score']}"

        if "similarity" in ctx:
            formatted += f"\n(Relevance: {ctx['similarity']:.2%})"

        return formatted

    def _format_play_context(self, ctx: Dict) -> str:
        """Format play-by-play context"""
        metadata = ctx.get("metadata", {})
        quarter = metadata.get("quarter", "?")
        time = metadata.get("time_remaining", "Unknown")

        formatted = f"[PLAY: Q{quarter} - {time}]\n"
        formatted += ctx.get("content", "")

        if "similarity" in ctx:
            formatted += f"\n(Relevance: {ctx['similarity']:.2%})"

        return formatted

    def _format_team_context(self, ctx: Dict) -> str:
        """Format team context with stats"""
        team_name = ctx.get("team_name", "Unknown Team")

        formatted = f"[TEAM: {team_name}]\n"
        formatted += ctx.get("content", "")

        if "team_stats" in ctx:
            formatted += f"\nTeam Statistics:\n"
            formatted += self._format_stats_dict(ctx["team_stats"])

        if "record" in ctx:
            record = ctx["record"]
            formatted += f"\nRecord: {record.get('wins', 0)}-{record.get('losses', 0)}"

        return formatted

    def _format_generic_context(self, ctx: Dict) -> str:
        """Format generic context"""
        source = ctx.get("source", "UNKNOWN").upper()
        content = ctx.get("content", str(ctx))

        formatted = f"[{source}]\n{content}"

        if "similarity" in ctx:
            formatted += f"\n(Relevance: {ctx['similarity']:.2%})"

        return formatted

    def _format_stats_dict(self, stats: Dict, indent: str = "  ") -> str:
        """
        Format statistics dictionary.

        Args:
            stats: Statistics dictionary
            indent: Indentation string

        Returns:
            Formatted stats string
        """
        if not stats:
            return f"{indent}No statistics available"

        lines = []
        for key, value in stats.items():
            # Format key (convert snake_case to Title Case)
            formatted_key = key.replace("_", " ").title()

            # Format value
            if isinstance(value, float):
                formatted_value = f"{value:.1f}"
            elif isinstance(value, dict):
                # Nested dict (skip for now)
                continue
            else:
                formatted_value = str(value)

            lines.append(f"{indent}{formatted_key}: {formatted_value}")

        return "\n".join(lines)

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Approximate: 1 token ≈ 4 characters
            return len(text) // 4

    def estimate_cost(
        self, prompt: str, response_tokens: int = 500
    ) -> Dict[str, float]:
        """
        Estimate API cost for prompt and response.

        Args:
            prompt: Prompt text
            response_tokens: Expected response tokens

        Returns:
            Dictionary with token counts and cost estimates
        """
        prompt_tokens = self._count_tokens(prompt)

        # Pricing (as of 2025, subject to change)
        pricing = {
            "gpt-4": {
                "input": 0.03 / 1000,  # $0.03 per 1K input tokens
                "output": 0.06 / 1000,  # $0.06 per 1K output tokens
            },
            "gpt-3.5-turbo": {
                "input": 0.0005 / 1000,  # $0.0005 per 1K input tokens
                "output": 0.0015 / 1000,  # $0.0015 per 1K output tokens
            },
        }

        # Get pricing for model
        model_pricing = pricing.get(self.model, pricing["gpt-4"])

        input_cost = prompt_tokens * model_pricing["input"]
        output_cost = response_tokens * model_pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": prompt_tokens + response_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }


# Standalone testing
if __name__ == "__main__":
    # Test prompt building
    builder = PromptBuilder(model="gpt-4")

    # Mock contexts
    test_contexts = [
        {
            "source": "player",
            "metadata": {"name": "LeBron James"},
            "content": "LeBron James is a professional basketball player known for his versatility and basketball IQ.",
            "career_stats": {
                "points": 38652,
                "rebounds": 10562,
                "assists": 10243,
                "games_played": 1421,
            },
            "similarity": 0.95,
        },
        {
            "source": "player",
            "metadata": {"name": "Michael Jordan"},
            "content": "Michael Jordan is widely considered the greatest basketball player of all time.",
            "career_stats": {
                "points": 32292,
                "rebounds": 6672,
                "assists": 5633,
                "games_played": 1072,
            },
            "similarity": 0.93,
        },
    ]

    test_query_analysis = {
        "intent": "comparison",
        "query_type": "player_comparison",
        "entities": {"players": ["LeBron James", "Michael Jordan"]},
        "temporal": {},
        "confidence": 0.95,
    }

    question = "Compare LeBron James and Michael Jordan"

    # Build prompt
    prompt = builder.build_prompt(question, test_contexts, test_query_analysis)
    system_prompt = builder.get_system_prompt()

    print("System Prompt:")
    print("=" * 80)
    print(system_prompt)
    print("\n")

    print("User Prompt:")
    print("=" * 80)
    print(prompt)
    print("\n")

    # Estimate cost
    cost = builder.estimate_cost(prompt, response_tokens=500)
    print("Cost Estimate:")
    print("=" * 80)
    print(f"Prompt tokens: {cost['prompt_tokens']}")
    print(f"Response tokens: {cost['response_tokens']}")
    print(f"Total tokens: {cost['total_tokens']}")
    print(f"Estimated cost: ${cost['total_cost']:.4f}")
