# 0.12: RAG + LLM Integration

**Sub-Phase:** 0.12 (RAG + LLM)
**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
**Status:** ✅ COMPLETE
**Priority:** 🟡 MEDIUM
**Implementation ID:** rec_188_postgresql

---

## Overview

Combine Retrieval-Augmented Generation (RAG) pipeline with Large Language Models (LLMs) using unified PostgreSQL architecture. This enables natural language querying over NBA temporal data with context-aware responses.

**Supersedes:** MongoDB+Qdrant RAG+LLM (see `../archive/mongodb_superseded/0.6_rag_llm_mongodb_SUPERSEDED/`) - archived October 22, 2025

**Key Capabilities:**
- Natural language queries over NBA data
- Context retrieval using pgvector semantic search
- LLM-powered response generation with temporal awareness
- Unified data access across JSONB, vectors, and temporal tables
- Token-efficient context assembly
- Cost-optimized LLM API usage

**Impact:**
Intelligent NBA data access, reduced query complexity, enhanced user experience, simplified architecture with single database.

---

## Quick Start

```python
import psycopg2
from pgvector.psycopg2 import register_vector
import openai
from typing import List, Dict

class RAGLLM:
    """RAG + LLM system for NBA data"""

    def __init__(self, conn):
        self.conn = conn
        register_vector(conn)
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def query(self, user_question: str, max_tokens: int = 500) -> str:
        """Answer question using RAG + LLM"""

        # 1. Retrieve relevant context
        context = self._retrieve_context(user_question, top_k=5)

        # 2. Assemble prompt
        prompt = self._build_prompt(user_question, context)

        # 3. Generate response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )

        return response.choices[0].message.content

    def _retrieve_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant context using pgvector"""
        # Get query embedding
        embedding = self._get_embedding(query)

        cur = self.conn.cursor()

        # Semantic search across multiple entity types
        cur.execute("""
            WITH ranked_results AS (
                -- Search players
                SELECT
                    'player' as source,
                    e.entity_id,
                    e.text_content,
                    e.metadata,
                    1 - (e.embedding <=> %s::vector) as similarity
                FROM nba_embeddings e
                WHERE e.entity_type = 'player'
                ORDER BY e.embedding <=> %s::vector
                LIMIT 3

                UNION ALL

                -- Search games
                SELECT
                    'game' as source,
                    e.entity_id,
                    e.text_content,
                    e.metadata,
                    1 - (e.embedding <=> %s::vector) as similarity
                FROM nba_embeddings e
                WHERE e.entity_type = 'game'
                ORDER BY e.embedding <=> %s::vector
                LIMIT 2
            )
            SELECT * FROM ranked_results
            ORDER BY similarity DESC
            LIMIT %s;
        """, (embedding, embedding, embedding, embedding, top_k))

        results = []
        for source, entity_id, content, metadata, similarity in cur.fetchall():
            results.append({
                'source': source,
                'entity_id': entity_id,
                'content': content,
                'metadata': metadata,
                'similarity': float(similarity)
            })

        return results

    def _build_prompt(self, question: str, context: List[Dict]) -> str:
        """Build prompt with retrieved context"""
        context_text = "\n\n".join([
            f"[{ctx['source'].upper()}] {ctx['content']}"
            for ctx in context
        ])

        prompt = f"""Based on the following NBA data context, please answer the question.

Context:
{context_text}

Question: {question}

Please provide a detailed answer based on the context provided."""

        return prompt

    def _get_system_prompt(self) -> str:
        """System prompt for NBA temporal data"""
        return """You are an expert NBA analyst with access to comprehensive historical and real-time NBA data.
Your knowledge includes:
- Player statistics and career trajectories
- Game-level and play-by-play data
- Team performance and dynamics
- Historical context and comparisons

Provide accurate, insightful answers based on the data context provided.
When uncertain, acknowledge limitations.
Focus on temporal aspects when relevant (career progression, game momentum, season trends)."""

# Usage
conn = psycopg2.connect(...)
rag = RAGLLM(conn)

# Ask natural language questions
answer = rag.query("Who were the best three-point shooters in the 2022 season?")
print(answer)

answer = rag.query("What happened in the final moments of the Lakers vs Warriors game on June 15, 2022?")
print(answer)
```

---

## Architecture

### RAG + LLM Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     User Question                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              1. Query Understanding                          │
│  - Extract entities (players, teams, dates)                 │
│  - Determine query type (stats, comparison, narrative)      │
│  - Generate embedding                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           2. Context Retrieval (pgvector)                    │
│  ┌─────────────────┬─────────────────┬──────────────────┐   │
│  │  Player Search  │   Game Search   │   Play Search    │   │
│  │   (Top 3)       │    (Top 2)      │    (Top 5)       │   │
│  └─────────────────┴─────────────────┴──────────────────┘   │
│                                                              │
│  Join with JSONB data for enrichment                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         3. Temporal Context Enhancement                      │
│  - Query temporal snapshots if date mentioned               │
│  - Add career progression context                           │
│  - Include game momentum data                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            4. Prompt Assembly                                │
│  - System prompt (NBA analyst persona)                      │
│  - Context (retrieved + temporal)                           │
│  - User question                                            │
│  - Token optimization (summarize if needed)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              5. LLM Generation                               │
│  - Send to OpenAI GPT-4 / Claude / Local LLM               │
│  - Stream response for better UX                            │
│  - Extract citations                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           6. Response Post-Processing                        │
│  - Add source citations                                     │
│  - Format statistics                                        │
│  - Include confidence scores                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  Enhanced Answer
```

### PostgreSQL Unified Access

```sql
-- Single query retrieving context from multiple sources
WITH semantic_results AS (
    -- Vector similarity search
    SELECT
        entity_id,
        text_content,
        metadata,
        1 - (embedding <=> %s::vector) as similarity
    FROM nba_embeddings
    WHERE entity_type = 'player'
    ORDER BY embedding <=> %s::vector
    LIMIT 5
),
jsonb_enrichment AS (
    -- Enrich with JSONB raw data
    SELECT
        s.entity_id,
        s.text_content,
        s.similarity,
        r.data->'career_stats' as stats,
        r.data->'biographical' as bio
    FROM semantic_results s
    JOIN raw_data.nba_players r ON s.entity_id = r.player_id
),
temporal_context AS (
    -- Add temporal progression
    SELECT
        j.entity_id,
        j.text_content,
        j.stats,
        j.bio,
        json_agg(
            json_build_object(
                'season', t.season,
                'points', t.cumulative_points,
                'games', t.games_played
            )
        ) as career_progression
    FROM jsonb_enrichment j
    LEFT JOIN player_snapshots t ON
        j.entity_id = t.player_id
    GROUP BY j.entity_id, j.text_content, j.stats, j.bio
)
SELECT * FROM temporal_context;
```

---

## Implementation Steps

### 1. Query Understanding (2-3 hours)

```python
# scripts/ml/query_understanding.py
import re
from datetime import datetime
from typing import Dict, List

class QueryUnderstanding:
    """Parse and understand user queries"""

    def analyze_query(self, query: str) -> Dict:
        """Extract query intent and entities"""
        return {
            'intent': self._classify_intent(query),
            'entities': self._extract_entities(query),
            'temporal': self._extract_temporal(query),
            'query_type': self._determine_query_type(query)
        }

    def _classify_intent(self, query: str) -> str:
        """Classify query intent"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['compare', 'vs', 'versus', 'better']):
            return 'comparison'
        elif any(word in query_lower for word in ['what happened', 'describe', 'tell me about']):
            return 'narrative'
        elif any(word in query_lower for word in ['stats', 'statistics', 'averages', 'totals']):
            return 'statistics'
        elif any(word in query_lower for word in ['best', 'top', 'greatest', 'who']):
            return 'ranking'
        else:
            return 'general'

    def _extract_entities(self, query: str) -> Dict:
        """Extract player names, teams, etc."""
        entities = {
            'players': [],
            'teams': [],
            'seasons': []
        }

        # Use database to match entity names
        conn = self._get_connection()
        cur = conn.cursor()

        # Find player mentions
        cur.execute("""
            SELECT DISTINCT data->>'player_name' as name
            FROM raw_data.nba_players
            WHERE %s ILIKE '%%' || (data->>'player_name') || '%%';
        """, (query,))

        entities['players'] = [row[0] for row in cur.fetchall()]

        return entities

    def _extract_temporal(self, query: str) -> Dict:
        """Extract temporal references"""
        temporal = {
            'season': None,
            'date': None,
            'date_range': None
        }

        # Season pattern (e.g., "2022 season", "2021-22")
        season_match = re.search(r'(\d{4})(?:-(\d{2}))?\s*season', query)
        if season_match:
            temporal['season'] = int(season_match.group(1))

        # Date pattern (e.g., "June 15, 2022")
        date_patterns = [
            r'(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, query)
            if date_match:
                try:
                    temporal['date'] = datetime.strptime(
                        date_match.group(1),
                        '%B %d, %Y'
                    )
                except:
                    pass

        return temporal
```

### 2. Context Retrieval with Temporal Awareness (3-4 hours)

```python
# scripts/ml/rag_retrieval.py
class TemporalRAGRetrieval:
    """Context retrieval with temporal awareness"""

    def retrieve_context(self, query: str,
                        query_analysis: Dict,
                        top_k: int = 10) -> List[Dict]:
        """Retrieve relevant context based on query analysis"""

        intent = query_analysis['intent']
        entities = query_analysis['entities']
        temporal = query_analysis['temporal']

        # Adaptive retrieval based on intent
        if intent == 'comparison':
            return self._retrieve_comparison_context(entities, temporal, top_k)
        elif intent == 'narrative':
            return self._retrieve_narrative_context(query, temporal, top_k)
        elif intent == 'statistics':
            return self._retrieve_statistical_context(entities, temporal, top_k)
        else:
            return self._retrieve_general_context(query, top_k)

    def _retrieve_comparison_context(self, entities: Dict,
                                     temporal: Dict,
                                     top_k: int) -> List[Dict]:
        """Retrieve context for player/team comparisons"""
        players = entities.get('players', [])
        season = temporal.get('season')

        cur = self.conn.cursor()

        # Get player embeddings and stats
        cur.execute("""
            SELECT
                e.entity_id,
                e.text_content,
                e.metadata,
                r.data->'career_stats' as career_stats,
                r.data->'season_stats' as season_stats
            FROM nba_embeddings e
            JOIN raw_data.nba_players r ON e.entity_id = r.player_id
            WHERE e.entity_type = 'player'
              AND e.metadata->>'name' = ANY(%s)
              AND (%s IS NULL OR r.season = %s);
        """, (players, season, season))

        results = []
        for row in cur.fetchall():
            results.append({
                'player_id': row[0],
                'description': row[1],
                'metadata': row[2],
                'career_stats': row[3],
                'season_stats': row[4]
            })

        return results

    def _retrieve_narrative_context(self, query: str,
                                    temporal: Dict,
                                    top_k: int) -> List[Dict]:
        """Retrieve play-by-play narrative context"""
        query_embedding = self._get_embedding(query)
        game_date = temporal.get('date')

        cur = self.conn.cursor()

        # Search play embeddings with temporal filter
        cur.execute("""
            SELECT
                p.game_id,
                p.play_description,
                p.quarter,
                p.time_remaining,
                p.metadata,
                1 - (p.embedding <=> %s::vector) as similarity
            FROM play_embeddings p
            WHERE (%s IS NULL OR
                   (p.metadata->>'game_date')::date = %s)
            ORDER BY p.embedding <=> %s::vector
            LIMIT %s;
        """, (query_embedding, game_date, game_date,
              query_embedding, top_k))

        return [dict(zip([
            'game_id', 'description', 'quarter',
            'time', 'metadata', 'similarity'
        ], row)) for row in cur.fetchall()]
```

### 3. Prompt Engineering (2-3 hours)

```python
# scripts/ml/prompt_builder.py
class PromptBuilder:
    """Build optimized prompts for LLM"""

    def build_prompt(self, question: str,
                    context: List[Dict],
                    query_analysis: Dict,
                    max_tokens: int = 3000) -> str:
        """Build context-aware prompt"""

        # Token-efficient context assembly
        context_text = self._assemble_context(
            context,
            max_tokens=max_tokens * 0.7  # Reserve 30% for response
        )

        # Intent-specific instructions
        instructions = self._get_intent_instructions(
            query_analysis['intent']
        )

        prompt = f"""{instructions}

Context:
{context_text}

Question: {question}

Please provide a comprehensive answer based on the context above."""

        return prompt

    def _assemble_context(self, context: List[Dict],
                         max_tokens: int) -> str:
        """Assemble context with token limits"""
        import tiktoken

        enc = tiktoken.encoding_for_model("gpt-4")
        context_parts = []
        token_count = 0

        for ctx in context:
            # Format context based on type
            if ctx.get('source') == 'player':
                text = self._format_player_context(ctx)
            elif ctx.get('source') == 'game':
                text = self._format_game_context(ctx)
            else:
                text = ctx.get('description', str(ctx))

            # Check token limit
            ctx_tokens = len(enc.encode(text))
            if token_count + ctx_tokens > max_tokens:
                break

            context_parts.append(text)
            token_count += ctx_tokens

        return "\n\n".join(context_parts)

    def _get_intent_instructions(self, intent: str) -> str:
        """Get intent-specific instructions"""
        instructions = {
            'comparison': """You are comparing NBA players or teams.
Provide a balanced analysis highlighting strengths and weaknesses.
Use statistics to support your comparisons.""",

            'narrative': """You are describing NBA game events.
Provide vivid play-by-play narrative with context about game significance.
Explain momentum shifts and key moments.""",

            'statistics': """You are analyzing NBA statistics.
Present numbers clearly with context about league averages and historical significance.
Explain what the statistics reveal about performance.""",

            'ranking': """You are ranking NBA entities.
Provide a clear ranked list with justification for each ranking.
Consider multiple dimensions (stats, impact, context)."""
        }

        return instructions.get(intent,
            "You are an expert NBA analyst. Provide accurate, insightful analysis.")
```

### 4. LLM Integration with Streaming (2-3 hours)

```python
# scripts/ml/llm_integration.py
class LLMIntegration:
    """LLM integration with streaming support"""

    def __init__(self, model="gpt-4"):
        self.model = model
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def generate_response(self, prompt: str,
                         system_prompt: str,
                         stream: bool = True) -> str:
        """Generate LLM response"""

        if stream:
            return self._generate_streaming(prompt, system_prompt)
        else:
            return self._generate_standard(prompt, system_prompt)

    def _generate_streaming(self, prompt: str, system_prompt: str):
        """Generate with streaming for better UX"""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.get('content'):
                content = chunk.choices[0].delta.content
                full_response += content
                yield content

        return full_response

    def _generate_standard(self, prompt: str, system_prompt: str) -> str:
        """Standard non-streaming generation"""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content
```

---

## Configuration

```yaml
# config/rag_llm_config.yaml
rag_llm:
  retrieval:
    top_k: 10
    similarity_threshold: 0.7
    entity_distribution:
      players: 5
      games: 3
      plays: 2

  llm:
    provider: "openai"  # or "anthropic", "local"
    model: "gpt-4"
    max_tokens: 1000
    temperature: 0.7
    stream: true

  prompt:
    max_context_tokens: 3000
    system_prompt_template: "templates/nba_analyst_system.txt"
    intent_instructions: "templates/intent_instructions.yaml"

  cost_optimization:
    cache_responses: true
    cache_ttl: 3600  # seconds
    use_gpt35_for_simple: true
    token_budget_per_day: 100000
```

---

## Performance Characteristics

**Estimated Time:** 4-5 days
- Query understanding: 2-3 hours
- Context retrieval: 3-4 hours
- Prompt engineering: 2-3 hours
- LLM integration: 2-3 hours
- Response processing: 2-3 hours
- Testing: 1-2 days
- Documentation: 4-6 hours

**Query Latency:**
- Context retrieval: 10-50ms
- LLM generation: 2-10 seconds (GPT-4)
- Total: 2-11 seconds

**Cost per Query:**
- GPT-4 (1K tokens context + 500 tokens response): $0.03-0.05
- GPT-3.5-turbo: $0.002-0.003
- Embeddings (100 tokens): $0.00001
- Total: $0.002-0.05 per query

**Daily Budget Examples:**
- 1,000 queries/day × $0.003 (GPT-3.5) = $3/day = $90/month
- 100 queries/day × $0.03 (GPT-4) = $3/day = $90/month

---

## Dependencies

**Prerequisites:**
- [0.7: PostgreSQL JSONB Storage](../0.7_postgresql_jsonb_storage/README.md)
- [0.8: RAG Pipeline with pgvector](../0.8_rag_pipeline_pgvector/README.md)
- OpenAI API key or local LLM setup

**Enables:**
- Natural language interface to NBA data
- Intelligent query understanding
- Context-aware responses

---

## Testing

```python
# tests/test_rag_llm.py
import pytest

def test_simple_query():
    """Test simple player query"""
    rag = RAGLLM(conn)
    answer = rag.query("Who is LeBron James?")

    assert len(answer) > 100
    assert "LeBron" in answer
    assert "Lakers" in answer or "Cavaliers" in answer

def test_comparison_query():
    """Test player comparison"""
    answer = rag.query("Compare LeBron James and Michael Jordan")

    assert "LeBron" in answer
    assert "Jordan" in answer
    assert any(word in answer for word in ['points', 'championships', 'career'])

def test_temporal_query():
    """Test query with temporal context"""
    answer = rag.query("What were LeBron's stats in the 2016 Finals?")

    assert "2016" in answer
    assert "Finals" in answer

def test_cost_tracking():
    """Test cost tracking"""
    initial_cost = rag.get_total_cost()
    rag.query("Test question")
    final_cost = rag.get_total_cost()

    assert final_cost > initial_cost
    assert (final_cost - initial_cost) < 0.10  # Under 10 cents
```

---



---

## How This Phase Enables the Simulation Vision

This phase provides critical infrastructure that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference Foundation

ML/AI infrastructure augments econometric causal inference:

**Causal ML integration:**
- **Double machine learning:** ML for nuisance parameter estimation in causal models
- **Causal forests:** Heterogeneous treatment effect estimation using random forests
- **Targeted learning:** Data-adaptive causal inference combining ML with econometrics

**Instrumental variables enhancement:**
- **Deep IV:** Neural networks for flexible IV estimation with high-dimensional instruments
- **Weak instrument detection:** ML-based tests for instrument relevance
- **Optimal instrument selection:** Automated IV selection from candidate set

**Propensity score refinement:**
- **ML for propensity scores:** Gradient boosting, random forests for treatment assignment modeling
- **Overlap diagnostics:** Automated detection of common support violations
- **Doubly robust estimation:** Combines outcome regression with propensity scores

### 2. Nonparametric Event Modeling (Distribution-Free)

ML/AI enhances nonparametric modeling:

**Flexible function approximation:**
- **Neural networks:** Universal approximators without functional form assumptions
- **Random forests:** Nonparametric regression trees for conditional distributions
- **Gaussian processes:** Nonparametric Bayesian approach with uncertainty quantification

**Density estimation:**
- **Normalizing flows:** Deep generative models for complex empirical distributions
- **Mixture density networks:** Neural networks outputting full conditional distributions
- **Variational autoencoders:** Learn latent representations of irregular events

**Distribution-free prediction:**
- **Conformal prediction:** Distribution-free prediction intervals with coverage guarantees
- **Quantile regression forests:** Estimate conditional quantiles without distributional assumptions
- **Kernel methods:** Nonparametric classification and regression

### 3. Context-Adaptive Simulations

Using ML/AI, simulations adapt intelligently:

**Real-time predictions:**
- Neural networks for instant win probability updates
- Reinforcement learning for adaptive strategy selection
- Transfer learning from historical to current game context

**Context-aware embeddings:**
- Vector representations capture game situation nuances
- Attention mechanisms focus on relevant historical context
- Contextual bandits for dynamic decision-making

**Personalized modeling:**
- Player-specific models learned from individual history
- Team-specific strategy models
- Matchup-specific performance predictions

### 4. Integration with Main README Methodology

**Panel data regression (Main README: Lines 81-87):**
- ML models trained on panel data structure with cross-sectional and time series dimensions

**Nonparametric validation (Main README: Line 116):**
- ML predictions validated using conformal prediction with distribution-free guarantees

**Monte Carlo simulation (Main README: Line 119):**
- ML models provide parameter distributions for Monte Carlo uncertainty quantification

**See [main README](../../../README.md) for complete methodology.**

---

## Related Documentation

- **[PHASE_0_INDEX.md](../../PHASE_0_INDEX.md)** - Phase 0 overview
- **[0.10: PostgreSQL JSONB](../0.10_postgresql_jsonb_storage/README.md)** - JSONB storage
- **[0.11: pgvector RAG](../0.11_rag_pipeline_pgvector/README.md)** - Vector search
- **[OpenAI API Docs](https://platform.openai.com/docs)** - LLM API reference

---

## Navigation

**Return to:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Prerequisites:**
- [0.7: PostgreSQL JSONB Storage](../0.7_postgresql_jsonb_storage/README.md)
- [0.8: RAG Pipeline with pgvector](../0.8_rag_pipeline_pgvector/README.md)

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Source:** LLM Engineers Handbook (rec_188, adapted for PostgreSQL)

