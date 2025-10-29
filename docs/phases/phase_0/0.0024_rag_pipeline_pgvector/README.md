# 0.2: Implement RAG Pipeline with PostgreSQL + pgvector

**Status:** 🔵 **PLANNED** (Priority 3 - Weeks 5-6)
**Phase:** 0 (Data Collection)
**Priority:** Medium (AI Features)
**Implementation ID:** rec_034 (PostgreSQL pgvector replacement for Qdrant/Pinecone)

---

## Overview

Implement a Retrieval-Augmented Generation (RAG) feature pipeline using PostgreSQL's pgvector extension for vector embeddings, eliminating the need for separate vector databases like Qdrant or Pinecone.

### Why PostgreSQL + pgvector Instead of Qdrant/Pinecone?

**Technical Superiority:**
- ✅ **Native Vector Support:** pgvector extension adds vector data types
- ✅ **Fast Similarity Search:** HNSW and IVFFlat indexes for efficient retrieval
- ✅ **ACID Transactions:** Vectors and metadata stay consistent
- ✅ **Better Integration:** Join embeddings with game data in single query
- ✅ **Simpler Architecture:** One database for everything

**Cost Savings:**
- Qdrant Cloud: $10-20/month
- Pinecone: $10-50/month
- pgvector: **FREE** (PostgreSQL extension)
- **Savings: $10-50/month ($120-600/year)**

**Operational Benefits:**
- No separate vector database to manage
- Single backup and recovery strategy
- Unified monitoring and alerting
- Lower operational complexity
- Better query performance with joins

---

## Capabilities

### 1. Vector Embeddings Storage

Store document embeddings with metadata:

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Store game embeddings
CREATE TABLE game_embeddings (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    season VARCHAR(10),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,

    -- Vector embedding (OpenAI: 1536 dims, BGE: 768 dims)
    embedding vector(1536) NOT NULL,

    -- Metadata for filtering
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_game_chunk UNIQUE (game_id, chunk_index)
);
```

### 2. Fast Similarity Search

Query semantically similar content:

```sql
-- Create HNSW index for fast similarity search (recommended)
CREATE INDEX ON game_embeddings
USING hnsw (embedding vector_cosine_ops);

-- Query similar games (cosine similarity)
SELECT
    game_id,
    chunk_text,
    1 - (embedding <=> $1::vector) AS similarity
FROM game_embeddings
WHERE 1 - (embedding <=> $1::vector) > 0.7  -- 70% similarity threshold
ORDER BY embedding <=> $1::vector
LIMIT 10;

-- Alternative: IVFFlat index (faster build, slower search)
-- CREATE INDEX ON game_embeddings
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);
```

### 3. Filtered Vector Search

Combine semantic search with metadata filtering:

```sql
-- Find similar Lakers games in 2023-24 season
SELECT
    game_id,
    chunk_text,
    metadata,
    1 - (embedding <=> $1::vector) AS similarity
FROM game_embeddings
WHERE metadata->>'team' = 'Lakers'
  AND metadata->>'season' = '2023-24'
  AND 1 - (embedding <=> $1::vector) > 0.7
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

### 4. Join Embeddings with Raw Data

Retrieve full game context in single query:

```sql
-- Get similar games with full box score data
SELECT
    e.game_id,
    e.chunk_text,
    e.similarity,
    r.raw_data->>'final_score' as score,
    r.raw_data->'key_players' as key_players
FROM (
    SELECT
        game_id,
        chunk_text,
        1 - (embedding <=> $1::vector) AS similarity
    FROM game_embeddings
    WHERE 1 - (embedding <=> $1::vector) > 0.7
    ORDER BY embedding <=> $1::vector
    LIMIT 10
) e
JOIN nba_raw_data r ON e.game_id = r.game_id
WHERE r.source = 'basketball_reference';
```

---

## RAG Pipeline

### Step-by-Step Process

**1. Document Ingestion**
```python
# Load game data from PostgreSQL
games = db.execute("""
    SELECT game_id, raw_data
    FROM nba_raw_data
    WHERE season = '2023-24'
""")
```

**2. Document Cleaning**
```python
# Remove irrelevant information
def clean_document(raw_data: dict) -> str:
    # Extract key information only
    relevant_text = f"""
    Game: {raw_data['home_team']} vs {raw_data['away_team']}
    Date: {raw_data['game_date']}
    Final Score: {raw_data['final_score']}
    Key Players: {format_players(raw_data['players'])}
    Game Flow: {raw_data['quarter_scores']}
    """
    return relevant_text
```

**3. Document Chunking**
```python
# Split into manageable pieces (500 tokens each)
def chunk_document(text: str, chunk_size: int = 500) -> list[str]:
    chunks = []
    words = text.split()

    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i+chunk_size])
        chunks.append(chunk)

    return chunks
```

**4. Embedding Generation**
```python
from openai import OpenAI

client = OpenAI()

def generate_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",  # 1536 dimensions
        input=text
    )
    return response.data[0].embedding
```

**5. Storage in PostgreSQL**
```python
# Store embeddings with metadata
for chunk_idx, chunk in enumerate(chunks):
    embedding = generate_embedding(chunk)

    db.execute("""
        INSERT INTO game_embeddings
        (game_id, season, chunk_index, chunk_text, embedding, metadata)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, [
        game_id,
        season,
        chunk_idx,
        chunk,
        embedding,
        {'team': team, 'date': date, 'type': 'box_score'}
    ])
```

**6. Index Creation**
```sql
-- Create HNSW index for fast retrieval
CREATE INDEX ON game_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**7. Semantic Search**
```python
# Query similar games
def search_similar(query: str, limit: int = 10) -> list:
    query_embedding = generate_embedding(query)

    results = db.execute("""
        SELECT
            game_id,
            chunk_text,
            metadata,
            1 - (embedding <=> $1::vector) AS similarity
        FROM game_embeddings
        WHERE 1 - (embedding <=> $1::vector) > 0.7
        ORDER BY embedding <=> $1::vector
        LIMIT $2
    """, [query_embedding, limit])

    return results
```

---

## Implementation Plan

### Week 1: Setup & Pipeline (Days 32-35)

**Day 32: pgvector Setup**
- [ ] Install pgvector extension on RDS
- [ ] Create `game_embeddings` table
- [ ] Test vector operations
- [ ] Benchmark index performance

**Day 33-34: Embedding Pipeline**
- [ ] Build document cleaning module
- [ ] Implement chunking strategy
- [ ] Integrate OpenAI embeddings API
- [ ] Add batch processing
- [ ] Error handling and retries

**Day 35: Storage Integration**
- [ ] Implement embedding storage
- [ ] Add metadata extraction
- [ ] Create HNSW indexes
- [ ] Test insertion performance

### Week 2: Retrieval & Testing (Days 36-38)

**Day 36: Retrieval System**
- [ ] Build semantic search API
- [ ] Add filtered search capabilities
- [ ] Implement similarity thresholds
- [ ] Optimize query performance

**Day 37: Integration Testing**
- [ ] End-to-end RAG pipeline test
- [ ] Performance benchmarks
- [ ] Accuracy evaluation
- [ ] Scale testing (10K+ embeddings)

**Day 38: Documentation**
- [ ] API documentation
- [ ] Query examples
- [ ] Performance tuning guide
- [ ] Troubleshooting guide

---

## PostgreSQL Schema

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Game embeddings table
CREATE TABLE game_embeddings (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    season VARCHAR(10),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,

    -- Vector embedding (1536 dims for OpenAI text-embedding-3-small)
    embedding vector(1536) NOT NULL,

    -- Metadata for filtering and context
    metadata JSONB,

    -- Tracking
    created_at TIMESTAMP DEFAULT NOW(),
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small',

    CONSTRAINT unique_game_chunk UNIQUE (game_id, chunk_index)
);

-- Indexes for performance
CREATE INDEX idx_embeddings_game_id ON game_embeddings (game_id);
CREATE INDEX idx_embeddings_season ON game_embeddings (season);
CREATE INDEX idx_embeddings_metadata ON game_embeddings USING GIN (metadata);

-- HNSW index for fast vector similarity search
CREATE INDEX idx_embeddings_vector ON game_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Embedding statistics table
CREATE TABLE embedding_stats (
    id SERIAL PRIMARY KEY,
    total_embeddings INTEGER,
    total_games INTEGER,
    avg_chunks_per_game DECIMAL(5,2),
    total_dimensions INTEGER,
    index_size_mb DECIMAL(10,2),
    last_updated TIMESTAMP DEFAULT NOW()
);
```

---

## Integration Points

### ADCE Integration

```python
# Add to ADCE: generate embeddings after data collection
async def process_new_game(game_id: str):
    # 1. Scrape game data (existing ADCE)
    game_data = await scrape_game(game_id)

    # 2. Store in PostgreSQL JSONB (0.1)
    await store_raw_data(game_id, game_data)

    # 3. Generate embeddings (NEW)
    chunks = chunk_document(clean_document(game_data))
    for idx, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)
        await store_embedding(game_id, idx, chunk, embedding)
```

### DIMS Integration

Track RAG pipeline metrics:

```python
# Update DIMS with embedding metrics
dims_client.update_metric('total_embeddings', count)
dims_client.update_metric('embedding_generation_time_ms', avg_time)
dims_client.update_metric('vector_search_latency_ms', search_time)
```

---

## Performance Benchmarks

**Target Metrics:**
- Embedding Generation: < 500ms per chunk (OpenAI API)
- Storage: > 100 embeddings/second
- Vector Search: < 100ms for top-10 similar
- Index Build: < 5 minutes for 10K embeddings

**HNSW Index Parameters:**
- `m = 16`: Number of connections (higher = better recall, slower build)
- `ef_construction = 64`: Build time quality (higher = better index, slower build)
- `ef_search`: Query time quality (set at runtime, default 40)

---

## Example Usage

```python
# Initialize RAG system
from rag_pipeline import RAGSystem

rag = RAGSystem(db_connection)

# 1. Ingest games
await rag.ingest_season('2023-24')

# 2. Search similar games
results = rag.search("Lakers comeback wins in clutch situations")

# Results:
# [
#   {
#     "game_id": "LAL_MIA_20240215",
#     "similarity": 0.89,
#     "text": "Lakers mounted a dramatic 15-point comeback...",
#     "metadata": {"team": "Lakers", "season": "2023-24"}
#   },
#   ...
# ]

# 3. Get full context for LLM
context = rag.get_context_for_llm(results, max_tokens=2000)
```

---

## Documentation

### Query Patterns

```python
# Pattern 1: Simple similarity search
query_embedding = generate_embedding("LeBron triple-double performances")
results = db.execute("""
    SELECT game_id, chunk_text,
           1 - (embedding <=> $1::vector) AS similarity
    FROM game_embeddings
    ORDER BY embedding <=> $1::vector
    LIMIT 10
""", [query_embedding])

# Pattern 2: Filtered search
results = db.execute("""
    SELECT game_id, chunk_text, similarity
    FROM (
        SELECT *, 1 - (embedding <=> $1::vector) AS similarity
        FROM game_embeddings
        WHERE metadata->>'player' = 'LeBron James'
          AND metadata->>'season' = '2023-24'
    ) sub
    WHERE similarity > 0.75
    ORDER BY similarity DESC
    LIMIT 5
""", [query_embedding])

# Pattern 3: Multi-vector aggregation
results = db.execute("""
    SELECT game_id, AVG(similarity) as avg_similarity
    FROM (
        SELECT game_id, 1 - (embedding <=> $1::vector) AS similarity
        FROM game_embeddings
    ) sub
    WHERE similarity > 0.7
    GROUP BY game_id
    ORDER BY avg_similarity DESC
    LIMIT 10
""", [query_embedding])
```

---

## Related Sub-Phases

**Prerequisites:**
- ✅ 0.0023: PostgreSQL JSONB Storage (provides source data)
- ✅ 0.0018: Autonomous Data Collection (automation)

**Integrates With:**
- 🔄 0.0025: RAG + LLM Integration (uses these embeddings)
- 🔄 0.0014: Error Analysis (validates retrieval quality)

**Supersedes:**
- 🗄️ archive/mongodb_superseded/0.2_rag_mongodb_SUPERSEDED/

---

## Navigation

**Return to:** [Phase 0 Index](../PHASE_0_INDEX.md)
**Previous:** [0.0023 PostgreSQL JSONB Storage](../0.0023_postgresql_jsonb_storage/README.md)
**Next:** [0.0025 RAG + LLM Integration](../0.0025_rag_llm_integration/README.md)

---

**Implementation Status:** 🔵 PLANNED (Ready to implement - Priority 3, Weeks 5-6)

