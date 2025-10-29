# 0.6: PostgreSQL RAG + LLM Integration

**Status:** 🔵 **PLANNED** (Priority 3 - Weeks 5-6)
**Phase:** 0 (Data Collection)
**Priority:** Medium (AI Features)
**Implementation ID:** rec_188 (PostgreSQL replacement for MongoDB/Qdrant RAG + LLM)

---

## Overview

Combine Retrieval-Augmented Generation (RAG) using PostgreSQL + pgvector with Large Language Models (Claude, GPT-4, DeepSeek) to create a natural language interface for NBA data insights.

### Why PostgreSQL for RAG + LLM?

**Technical Advantages:**
- ✅ **Unified Database:** Vectors, raw data, and cache in one place
- ✅ **Fast Retrieval:** pgvector HNSW indexes for sub-100ms queries
- ✅ **ACID Transactions:** Consistent state across cache and data
- ✅ **Complex Queries:** Join embeddings with temporal panel data
- ✅ **Cost Efficiency:** No separate vector DB or NoSQL needed

**Cost Savings:**
- MongoDB + Qdrant: $25-40/month
- PostgreSQL + pgvector: **Already paying for RDS**
- **Additional Cost: $0/month** (+ LLM API costs only)

**Operational Benefits:**
- Single connection pool
- Unified backup strategy
- Simplified monitoring
- Lower latency (no cross-service calls)

---

## Architecture

```
User Natural Language Query
    ↓
1. Query Embedding (OpenAI)
    ↓
2. Vector Similarity Search (PostgreSQL + pgvector)
    ↓
3. Retrieve Top 10 Similar Game Chunks
    ↓
4. Get Full Game Context (JSONB raw_data)
    ↓
5. Build Prompt with Context
    ↓
6. Send to LLM (Claude/GPT-4/DeepSeek)
    ↓
7. Return Natural Language Response
    ↓
8. Cache in PostgreSQL (avoid repeat API calls)
```

---

## Capabilities

### 1. Natural Language Queries

Ask questions in plain English:

```python
# User queries
queries = [
    "How did the Lakers perform in clutch situations this season?",
    "What are LeBron James' best triple-double performances?",
    "Compare Steph Curry's 3-point efficiency home vs away",
    "Find games where the trailing team won in the 4th quarter"
]

# System returns natural language insights
response = await rag_llm.query(queries[0])
# "The Lakers have won 68% of games decided by 5 or fewer points this season..."
```

### 2. Context-Aware Responses

Retrieve relevant game data automatically:

```python
async def query_with_context(query: str) -> str:
    # 1. Generate query embedding
    query_embedding = generate_embedding(query)

    # 2. Search similar game chunks (PostgreSQL + pgvector)
    similar_chunks = db.execute("""
        SELECT
            game_id,
            chunk_text,
            metadata,
            1 - (embedding <=> $1::vector) AS similarity
        FROM game_embeddings
        WHERE 1 - (embedding <=> $1::vector) > 0.7
        ORDER BY embedding <=> $1::vector
        LIMIT 10
    """, [query_embedding])

    # 3. Get full game context (JSONB)
    game_ids = [chunk['game_id'] for chunk in similar_chunks]
    full_context = db.execute("""
        SELECT
            game_id,
            raw_data->>'final_score' as score,
            raw_data->'key_players' as players,
            raw_data->'quarter_scores' as quarters
        FROM nba_raw_data
        WHERE game_id = ANY($1)
    """, [game_ids])

    # 4. Build prompt
    prompt = build_prompt(query, similar_chunks, full_context)

    # 5. Query LLM
    response = await llm_client.chat(prompt)

    # 6. Cache response
    await cache_response(query, query_embedding, game_ids, response)

    return response
```

### 3. Response Caching

Avoid expensive re-computation:

```sql
-- Cache LLM responses
CREATE TABLE llm_response_cache (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_embedding vector(1536),
    context_game_ids TEXT[],
    llm_model VARCHAR(50) NOT NULL,
    response_text TEXT NOT NULL,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Fast cache lookup using vector similarity
CREATE INDEX ON llm_response_cache
USING hnsw (query_embedding vector_cosine_ops);

-- Check cache before calling LLM
SELECT response_text, cost_usd
FROM llm_response_cache
WHERE 1 - (query_embedding <=> $1::vector) > 0.95  -- 95% similar = cache hit
ORDER BY created_at DESC
LIMIT 1;
```

### 4. Multi-Model Support

Use different LLMs for different tasks:

```python
# Claude for analysis and reasoning
claude_response = await claude_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1000
)

# GPT-4 for structured data extraction
gpt4_response = await openai_client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}
)

# DeepSeek for cost-effective queries
deepseek_response = await deepseek_client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}]
)
```

### 5. Cost Tracking

Monitor LLM spending:

```sql
-- Track LLM usage and costs
CREATE TABLE llm_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    query_text TEXT,
    model VARCHAR(50),
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    cost_usd DECIMAL(10,4),
    response_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Daily cost summary
SELECT
    DATE(created_at) as date,
    model,
    COUNT(*) as query_count,
    SUM(cost_usd) as total_cost,
    AVG(response_time_ms) as avg_response_time,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
FROM llm_usage
GROUP BY DATE(created_at), model
ORDER BY date DESC;
```

---

## Implementation Plan

### Week 1: LLM Integration (Days 39-41)

**Day 39: LLM Clients**
- [ ] Implement Claude client
- [ ] Implement GPT-4 client
- [ ] Implement DeepSeek client
- [ ] Add API key management
- [ ] Error handling and retries

**Day 40: RAG Context Builder**
- [ ] Build context from vector search
- [ ] Format for LLM prompts
- [ ] Add token counting
- [ ] Implement prompt templates

**Day 41: Caching System**
- [ ] Create cache tables
- [ ] Implement cache lookup
- [ ] Add cache invalidation
- [ ] Track cache hit rates

### Week 2: Testing & Optimization (Days 42-43)

**Day 42: Integration & Testing**
- [ ] End-to-end RAG + LLM tests
- [ ] Accuracy evaluation
- [ ] Response quality assessment
- [ ] Performance benchmarks

**Day 43: Documentation & Launch**
- [ ] API documentation
- [ ] Example queries
- [ ] Cost optimization guide
- [ ] User guide

---

## PostgreSQL Schema

```sql
-- LLM response cache
CREATE TABLE llm_response_cache (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_embedding vector(1536),
    context_game_ids TEXT[],
    llm_model VARCHAR(50) NOT NULL,
    response_text TEXT NOT NULL,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector index for cache lookup
CREATE INDEX idx_cache_embedding ON llm_response_cache
USING hnsw (query_embedding vector_cosine_ops);

-- Text index for keyword search
CREATE INDEX idx_cache_query ON llm_response_cache
USING GIN (to_tsvector('english', query_text));

-- LLM usage tracking
CREATE TABLE llm_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    query_text TEXT,
    model VARCHAR(50),
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    cost_usd DECIMAL(10,4),
    response_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX idx_usage_user ON llm_usage (user_id);
CREATE INDEX idx_usage_model ON llm_usage (model);
CREATE INDEX idx_usage_date ON llm_usage (created_at);

-- Prompt templates
CREATE TABLE prompt_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    template_text TEXT NOT NULL,
    use_case VARCHAR(100),
    model_optimized_for VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Integration Points

### Complete RAG + LLM Workflow

```python
from rag_llm_system import RAGLLMSystem

# Initialize system
rag_llm = RAGLLMSystem(
    db_connection=db,
    llm_model='claude-3-5-sonnet',
    cache_enabled=True
)

# User query
user_query = "How did the Lakers perform in close games this season?"

# System handles entire workflow
response = await rag_llm.query(
    query=user_query,
    max_context_tokens=2000,
    temperature=0.7,
    use_cache=True
)

print(response.text)
print(f"Cost: ${response.cost_usd:.4f}")
print(f"Cache hit: {response.cache_hit}")
print(f"Context games: {len(response.context_game_ids)}")
```

### DIMS Integration

```python
# Track RAG + LLM metrics
dims_client.update_metric('llm_queries_total', count)
dims_client.update_metric('llm_cache_hit_rate', hit_rate)
dims_client.update_metric('llm_avg_cost_usd', avg_cost)
dims_client.update_metric('llm_avg_response_time_ms', avg_time)
```

---

## Example Queries

### Query 1: Performance Analysis

**User Query:**
```python
"Analyze LeBron James' performance in clutch situations this season"
```

**System Workflow:**
1. Generate query embedding
2. Find similar games (pgvector search)
3. Retrieve full game context (JSONB)
4. Build prompt with statistics
5. Send to Claude

**LLM Response:**
```
Based on 18 games this season where LeBron played in clutch situations
(score within 5 points in final 5 minutes):

Performance:
- 12-6 record (67% win rate)
- 28.5 PPG in clutch minutes (league-leading)
- 58% FG, 42% 3PT (well above his season average)
- 5 game-winning shots

Key Insights:
- Exceptional efficiency under pressure
- Lakers' offense runs through him in close games
- Significantly better at home (9-2) vs away (3-4)
```

### Query 2: Comparative Analysis

**User Query:**
```python
"Compare Steph Curry vs Damian Lillard 3-point shooting this season"
```

**System Workflow:**
1. Vector search for both players
2. Get shooting stats from JSONB
3. Build comparative prompt
4. Query GPT-4 for structured analysis

**LLM Response:**
```json
{
  "comparison": {
    "steph_curry": {
      "3pt_percentage": 42.8,
      "attempts_per_game": 11.2,
      "makes_per_game": 4.8,
      "volume": "elite",
      "efficiency": "elite"
    },
    "damian_lillard": {
      "3pt_percentage": 38.9,
      "attempts_per_game": 10.5,
      "makes_per_game": 4.1,
      "volume": "elite",
      "efficiency": "above_average"
    },
    "winner": "steph_curry",
    "reasoning": "Higher efficiency on similar volume"
  }
}
```

### Query 3: Historical Context

**User Query:**
```python
"Find games similar to the 2016 Finals Game 7"
```

**System Workflow:**
1. Vector search with game description
2. Find similar high-stakes close games
3. Build historical context
4. DeepSeek generates narrative

**LLM Response:**
```
Top 5 games with similar drama and stakes:

1. 2013 Finals Game 6 - Heat vs Spurs
   - Ray Allen's clutch 3-pointer
   - Elimination game intensity
   - Historic comeback

2. 2010 Finals Game 7 - Lakers vs Celtics
   - Low-scoring defensive battle
   - Championship on the line
   - Kobe's legacy game

[... continues ...]
```

---

## Cost Optimization

### Strategies

1. **Aggressive Caching:**
   - Cache responses for 7 days
   - Use vector similarity for cache hits (95%+ similar)
   - Saves ~60-80% of LLM costs

2. **Model Selection:**
   - Claude for complex analysis: $0.003/1K tokens
   - GPT-4 Turbo for structured data: $0.01/1K tokens
   - DeepSeek for simple queries: $0.0001/1K tokens

3. **Context Optimization:**
   - Limit context to 2000 tokens (most relevant)
   - Compress game summaries
   - Remove redundant information

4. **Batch Processing:**
   - Group similar queries
   - Reuse embeddings
   - Parallel processing

**Estimated Monthly Costs:**
- 1,000 queries/month: $3-8
- 10,000 queries/month: $30-80
- 100,000 queries/month: $300-800

---

## Performance Benchmarks

**Target Metrics:**
- End-to-End Latency: < 2 seconds (90th percentile)
- Vector Search: < 100ms
- Context Building: < 200ms
- LLM Response: < 1.5 seconds
- Cache Hit Rate: > 60%

**Quality Metrics:**
- Relevance: > 85% (human evaluation)
- Accuracy: > 90% (factual correctness)
- Helpfulness: > 80% (user satisfaction)

---

## Related Sub-Phases

**Prerequisites:**
- ✅ 0.0023: PostgreSQL JSONB Storage (source data)
- ✅ 0.0024: RAG Pipeline with pgvector (embeddings)
- ✅ 0.0018: Autonomous Data Collection (data freshness)

**Integrates With:**
- 🔄 0.0014: Error Analysis (validates LLM outputs)
- 🔄 0.0016: Robust Architecture (fault tolerance)

**Supersedes:**
- 🗄️ archive/mongodb_superseded/0.6_rag_llm_mongodb_SUPERSEDED/

---

## Navigation

**Return to:** [Phase 0 Index](../PHASE_0_INDEX.md)  
**Previous:** [0.0024 RAG Pipeline with pgvector](../0.0024_rag_pipeline_pgvector/README.md)  
**Related:** [Phase 5: Machine Learning Models](../../phase_5/PHASE_5_INDEX.md)

---

**Implementation Status:** 🔵 PLANNED (Ready to implement - Priority 3, Weeks 5-6)

