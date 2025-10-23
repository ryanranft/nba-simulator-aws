# 0.8: RAG Pipeline with pgvector

**Sub-Phase:** 0.8 (RAG Infrastructure)
**Parent Phase:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Status:** 🔵 PLANNED
**Priority:** ⭐ HIGH
**Implementation ID:** rec_034_pgvector

---

## Overview

Implement a Retrieval-Augmented Generation (RAG) feature pipeline using PostgreSQL's pgvector extension for vector embeddings and similarity search. This provides enterprise-grade vector search capabilities within our existing database infrastructure.

**Supersedes:** [0.2 Qdrant RAG Pipeline](../archive/mongodb_superseded/0.2_rag_mongodb_SUPERSEDED/README.md) (archived October 22, 2025)

**Key Capabilities:**
- Vector embeddings storage with pgvector extension
- Similarity search using HNSW or IVFFlat indexes
- Semantic search over NBA data and documentation
- Integration with OpenAI embeddings or local models
- Native joins with temporal and JSONB data
- Zero additional database infrastructure

**Impact:**
Unified vector search, simplified architecture, enhanced player/game discovery, $120-240/year cost savings vs Qdrant.

---

## Quick Start

```python
import psycopg2
from pgvector.psycopg2 import register_vector
import openai
import numpy as np

# Connect to PostgreSQL with pgvector
conn = psycopg2.connect(
    host=os.getenv('RDS_HOST'),
    database=os.getenv('RDS_DATABASE'),
    user=os.getenv('RDS_USER'),
    password=os.getenv('RDS_PASSWORD')
)
register_vector(conn)

# Create table with vector column
cur = conn.cursor()
cur.execute("""
    -- Enable pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Create embeddings table
    CREATE TABLE IF NOT EXISTS nba_embeddings (
        id SERIAL PRIMARY KEY,
        entity_type VARCHAR(50) NOT NULL,  -- 'player', 'game', 'play'
        entity_id VARCHAR(100) NOT NULL,
        text_content TEXT NOT NULL,
        embedding vector(1536),  -- OpenAI ada-002 dimension
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Create HNSW index for fast similarity search
    CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
    ON nba_embeddings
    USING hnsw (embedding vector_cosine_ops);
""")

# Generate embedding for text
def get_embedding(text: str) -> list:
    """Get OpenAI embedding for text"""
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

# Insert embedded content
player_description = "LeBron James, power forward, Lakers, 4-time NBA champion"
embedding = get_embedding(player_description)

cur.execute("""
    INSERT INTO nba_embeddings (entity_type, entity_id, text_content, embedding, metadata)
    VALUES (%s, %s, %s, %s, %s);
""", (
    'player',
    'jamesle01',
    player_description,
    embedding,
    {'team': 'LAL', 'position': 'PF'}
))

# Semantic search
query = "Who are the best power forwards in Lakers history?"
query_embedding = get_embedding(query)

cur.execute("""
    SELECT
        entity_id,
        text_content,
        metadata,
        1 - (embedding <=> %s::vector) as similarity
    FROM nba_embeddings
    WHERE entity_type = 'player'
    ORDER BY embedding <=> %s::vector
    LIMIT 5;
""", (query_embedding, query_embedding))

results = cur.fetchall()
for entity_id, content, metadata, similarity in results:
    print(f"{entity_id}: {content} (similarity: {similarity:.4f})")
```

---

## Architecture

### pgvector Benefits

**vs Qdrant/Pinecone:**
- ✅ **Unified database** - Single connection pool
- ✅ **ACID transactions** - Consistent updates
- ✅ **Native joins** - Combine with temporal data
- ✅ **HNSW indexing** - Fast approximate nearest neighbor
- ✅ **Zero infrastructure cost** - Using existing RDS
- ✅ **Mature ecosystem** - PostgreSQL reliability

### Vector Storage Schema

```sql
-- Main embeddings table
CREATE TABLE nba_embeddings (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    text_content TEXT NOT NULL,
    embedding vector(1536),  -- Adjust based on model
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_id)
);

-- Entity-specific indexes
CREATE INDEX idx_embeddings_entity ON nba_embeddings(entity_type, entity_id);
CREATE INDEX idx_embeddings_metadata ON nba_embeddings USING GIN (metadata);

-- Vector similarity indexes (choose based on use case)
-- HNSW: Better for high-dimensional, large datasets
CREATE INDEX idx_embeddings_hnsw ON nba_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat: Faster build time, good for smaller datasets
-- CREATE INDEX idx_embeddings_ivfflat ON nba_embeddings
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- Play-by-play embeddings for detailed search
CREATE TABLE play_embeddings (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    play_id VARCHAR(100) NOT NULL,
    quarter INTEGER,
    time_remaining VARCHAR(10),
    play_description TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    UNIQUE(game_id, play_id)
);

CREATE INDEX idx_play_embeddings_game ON play_embeddings(game_id);
CREATE INDEX idx_play_embeddings_hnsw ON play_embeddings
USING hnsw (embedding vector_cosine_ops);
```

### Integration with JSONB Storage

```python
# Join embeddings with JSONB raw data
query = """
    SELECT
        e.entity_id,
        e.text_content,
        1 - (e.embedding <=> %s::vector) as similarity,
        r.data->>'player_name' as name,
        r.data->'career_stats' as stats
    FROM nba_embeddings e
    JOIN raw_data.nba_players r ON
        e.entity_id = r.player_id
    WHERE e.entity_type = 'player'
    ORDER BY e.embedding <=> %s::vector
    LIMIT 10;
"""
```

---

## Implementation Steps

### 1. Install pgvector Extension (30 minutes)

```sql
-- Connect to RDS PostgreSQL
-- Requires PostgreSQL 11+

-- Install extension (requires superuser or rds_superuser)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check version
SELECT vector_version();
```

### 2. Embedding Generation Pipeline (4-6 hours)

```python
# scripts/ml/generate_embeddings.py
import psycopg2
from pgvector.psycopg2 import register_vector
import openai
from typing import List, Dict
import time

class EmbeddingPipeline:
    """Generate and store embeddings for NBA data"""

    def __init__(self, conn, model="text-embedding-ada-002"):
        self.conn = conn
        self.model = model
        register_vector(conn)
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def generate_player_embeddings(self):
        """Generate embeddings for all players"""
        cur = self.conn.cursor()

        # Get players from JSONB storage
        cur.execute("""
            SELECT DISTINCT
                player_id,
                data->>'player_name' as name,
                data->>'position' as position,
                data->>'team' as team,
                data->'career_stats' as stats
            FROM raw_data.nba_players;
        """)

        players = cur.fetchall()

        for player_id, name, position, team, stats in players:
            # Create descriptive text
            text = self._create_player_description(
                name, position, team, stats
            )

            # Generate embedding
            embedding = self._get_embedding(text)

            # Store in database
            cur.execute("""
                INSERT INTO nba_embeddings
                (entity_type, entity_id, text_content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (entity_type, entity_id)
                DO UPDATE SET
                    text_content = EXCLUDED.text_content,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW();
            """, (
                'player',
                player_id,
                text,
                embedding,
                {'name': name, 'position': position, 'team': team}
            ))

            # Rate limiting
            time.sleep(0.1)

        self.conn.commit()

    def generate_play_embeddings(self, game_id: str):
        """Generate embeddings for play-by-play data"""
        cur = self.conn.cursor()

        # Get plays from JSONB
        cur.execute("""
            SELECT
                game_id,
                play_data->>'play_id' as play_id,
                play_data->>'quarter' as quarter,
                play_data->>'time_remaining' as time,
                play_data->>'description' as description
            FROM raw_data.nba_games,
            LATERAL jsonb_array_elements(data->'plays') as play_data
            WHERE game_id = %s;
        """, (game_id,))

        plays = cur.fetchall()

        batch = []
        for game_id, play_id, quarter, time, description in plays:
            text = f"Q{quarter} {time}: {description}"
            batch.append((game_id, play_id, quarter, time, text))

            # Process in batches of 100
            if len(batch) >= 100:
                self._process_play_batch(batch)
                batch = []

        if batch:
            self._process_play_batch(batch)

        self.conn.commit()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI"""
        try:
            response = openai.Embedding.create(
                input=text,
                model=self.model
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def _create_player_description(self, name, position, team, stats):
        """Create rich text description for player"""
        desc = f"{name}, {position}"
        if team:
            desc += f", {team}"
        if stats:
            desc += f". Career stats: {stats}"
        return desc
```

### 3. Semantic Search Functions (2-3 hours)

```python
# scripts/ml/semantic_search.py
class SemanticSearch:
    """Semantic search using pgvector"""

    def __init__(self, conn):
        self.conn = conn
        register_vector(conn)

    def search_players(self, query: str, limit: int = 10) -> List[Dict]:
        """Search players by semantic similarity"""
        query_embedding = self._get_embedding(query)

        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                e.entity_id,
                e.text_content,
                e.metadata,
                1 - (e.embedding <=> %s::vector) as similarity,
                r.data->'career_stats' as stats
            FROM nba_embeddings e
            LEFT JOIN raw_data.nba_players r ON
                e.entity_id = r.player_id
            WHERE e.entity_type = 'player'
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s;
        """, (query_embedding, query_embedding, limit))

        results = []
        for row in cur.fetchall():
            results.append({
                'player_id': row[0],
                'description': row[1],
                'metadata': row[2],
                'similarity': float(row[3]),
                'stats': row[4]
            })

        return results

    def search_similar_plays(self, play_description: str,
                            limit: int = 20) -> List[Dict]:
        """Find similar plays across all games"""
        query_embedding = self._get_embedding(play_description)

        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                game_id,
                play_id,
                quarter,
                time_remaining,
                play_description,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM play_embeddings
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, (query_embedding, query_embedding, limit))

        return [dict(zip([
            'game_id', 'play_id', 'quarter', 'time',
            'description', 'metadata', 'similarity'
        ], row)) for row in cur.fetchall()]

    def hybrid_search(self, query: str, filters: Dict = None,
                     limit: int = 10) -> List[Dict]:
        """Combine semantic search with metadata filtering"""
        query_embedding = self._get_embedding(query)

        where_clauses = ["entity_type = 'player'"]
        params = [query_embedding, query_embedding]

        if filters:
            for key, value in filters.items():
                where_clauses.append(f"metadata->>'{key}' = %s")
                params.append(value)

        params.append(limit)

        where_sql = " AND ".join(where_clauses)

        cur = self.conn.cursor()
        cur.execute(f"""
            SELECT
                entity_id,
                text_content,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM nba_embeddings
            WHERE {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, params)

        return cur.fetchall()
```

### 4. Performance Optimization (2-3 hours)

```sql
-- Index tuning for pgvector
-- HNSW parameters:
-- m: number of connections (higher = better recall, more memory)
-- ef_construction: construction time quality (higher = better index)

-- Rebuild with optimal parameters
DROP INDEX IF EXISTS idx_embeddings_hnsw;
CREATE INDEX idx_embeddings_hnsw ON nba_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 24, ef_construction = 100);

-- Query-time tuning
SET hnsw.ef_search = 100;  -- Higher = better recall, slower

-- Analyze performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT entity_id, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM nba_embeddings
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

---

## Configuration

```yaml
# config/pgvector_config.yaml
pgvector:
  extension_version: "0.5.0"

  embeddings:
    model: "text-embedding-ada-002"
    dimensions: 1536
    batch_size: 100
    rate_limit_delay: 0.1  # seconds

  indexes:
    hnsw:
      m: 24
      ef_construction: 100
      ef_search: 100

    # Alternative: IVFFlat
    # ivfflat:
    #   lists: 100
    #   probes: 10

  entity_types:
    - player
    - team
    - game
    - play
    - season_summary

  storage:
    partition_by_entity: true
    enable_compression: true
```

---

## Performance Characteristics

**Estimated Time:** 1 week
- Extension setup: 30 minutes
- Schema design: 2-3 hours
- Embedding pipeline: 4-6 hours
- Search functions: 2-3 hours
- Index optimization: 2-3 hours
- Testing: 6-8 hours
- Documentation: 2-3 hours

**Embedding Generation:**
- Players (~5,000): ~10 minutes (with OpenAI)
- Games (~30,000): ~60 minutes
- Plays (~500,000): ~12 hours

**Query Performance:**
- Top-10 similarity search: 1-10ms (with HNSW)
- Top-100 similarity search: 5-20ms
- Hybrid search with filters: 10-50ms

**Cost:**
- OpenAI embeddings: $0.0001 per 1K tokens
  - 5K players × 100 tokens = 500K tokens = $0.05
  - 30K games × 50 tokens = 1.5M tokens = $0.15
  - Total one-time: ~$0.20-0.50
- Storage: 1536 dimensions × 4 bytes × 500K entities = ~3 GB
- Monthly: $0 (using existing RDS)

---

## Dependencies

**Prerequisites:**
- [0.7: PostgreSQL JSONB Storage](../0.7_postgresql_jsonb_storage/README.md)
- PostgreSQL 11+ with pgvector extension
- OpenAI API key (or local embedding model)

**Enables:**
- [0.9: RAG + LLM Integration](../0.9_rag_llm_integration/README.md)
- Enhanced semantic search across all NBA data
- Intelligent player/game discovery

---

## Testing

```python
# tests/test_pgvector_rag.py
import pytest
from scripts.ml.semantic_search import SemanticSearch

def test_vector_similarity():
    """Test vector similarity search"""
    search = SemanticSearch(conn)
    results = search.search_players("best three point shooters")

    assert len(results) > 0
    assert results[0]['similarity'] > 0.7
    assert 'Curry' in results[0]['description']

def test_hybrid_search():
    """Test semantic search with filters"""
    results = search.hybrid_search(
        "elite defenders",
        filters={'position': 'SF'},
        limit=5
    )

    assert len(results) == 5
    assert all(r['metadata']['position'] == 'SF' for r in results)

def test_index_performance():
    """Test HNSW index performance"""
    import time
    start = time.time()
    results = search.search_players("clutch performers", limit=100)
    duration = time.time() - start

    assert duration < 0.1  # Should be under 100ms
```

---

## Troubleshooting

### Common Issues

**1. Extension not available**
```
ERROR: could not open extension control file
```
Solution: Install pgvector on RDS (requires AWS support for custom extensions)

**2. Index build timeout**
```
CREATE INDEX takes too long
```
Solution: Use lower `ef_construction` or create with `CONCURRENTLY`

**3. Poor recall**
```sql
-- Increase search quality
SET hnsw.ef_search = 200;

-- Or rebuild index with higher m
CREATE INDEX ... WITH (m = 32, ef_construction = 200);
```

---

## Related Documentation

- **[PHASE_0_INDEX.md](../../PHASE_0_INDEX.md)** - Phase 0 overview
- **[0.7: PostgreSQL JSONB](../0.7_postgresql_jsonb_storage/README.md)** - JSONB storage prerequisite
- **[0.9: RAG + LLM](../0.9_rag_llm_integration/README.md)** - Next step: LLM integration
- **[pgvector GitHub](https://github.com/pgvector/pgvector)** - Official pgvector docs

---

## Navigation

**Return to:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Prerequisites:** [0.7: PostgreSQL JSONB Storage](../0.7_postgresql_jsonb_storage/README.md)
**Next Steps:** [0.9: RAG + LLM Integration](../0.9_rag_llm_integration/README.md)

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Source:** LLM Engineers Handbook (rec_034, adapted for pgvector)

