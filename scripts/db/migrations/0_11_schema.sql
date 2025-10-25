-- ============================================================================
-- Phase 0.11: RAG Pipeline with pgvector - Database Schema
-- ============================================================================
-- Purpose: Vector embeddings storage for semantic search over NBA data
-- Created: October 25, 2025
-- Implementation ID: rec_034_pgvector
--
-- Prerequisites:
--   - PostgreSQL 11+ with pgvector extension installed
--   - RDS PostgreSQL instance running
--
-- Usage:
--   psql -h $RDS_HOST -U $RDS_USER -d $RDS_DATABASE -f 0_11_schema.sql
-- ============================================================================

-- Enable pgvector extension
-- Note: Requires rds_superuser role on AWS RDS
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgvector installation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension is not installed. Please install it first.';
    END IF;
END $$;

-- Create schema for RAG components
CREATE SCHEMA IF NOT EXISTS rag;

-- Grant permissions
GRANT USAGE ON SCHEMA rag TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA rag TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA rag GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO PUBLIC;

-- ============================================================================
-- Table: nba_embeddings
-- Purpose: Store vector embeddings for NBA entities (players, teams, games)
-- ============================================================================

CREATE TABLE IF NOT EXISTS rag.nba_embeddings (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,  -- 'player', 'team', 'game', 'season'
    entity_id VARCHAR(100) NOT NULL,
    text_content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-ada-002 dimension
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_entity UNIQUE(entity_type, entity_id)
);

-- Indexes for entity lookups
CREATE INDEX IF NOT EXISTS idx_embeddings_entity_type ON rag.nba_embeddings(entity_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_entity_id ON rag.nba_embeddings(entity_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_created_at ON rag.nba_embeddings(created_at);

-- GIN index for JSONB metadata
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata ON rag.nba_embeddings USING GIN (metadata);

-- HNSW index for fast similarity search (cosine distance)
-- m = 16: number of connections per layer (higher = more accurate, slower build)
-- ef_construction = 64: size of dynamic candidate list (higher = better recall, slower build)
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_cosine ON rag.nba_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat index alternative (faster build, good for smaller datasets)
-- Uncomment if HNSW build is too slow or dataset is < 100K vectors
-- CREATE INDEX IF NOT EXISTS idx_embeddings_ivfflat_cosine ON rag.nba_embeddings
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- ============================================================================
-- Table: play_embeddings
-- Purpose: Store embeddings for individual plays (play-by-play events)
-- ============================================================================

CREATE TABLE IF NOT EXISTS rag.play_embeddings (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    play_id VARCHAR(100) NOT NULL,
    quarter INTEGER,
    time_remaining VARCHAR(20),
    game_clock_seconds NUMERIC(8, 2),
    play_description TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_play UNIQUE(game_id, play_id)
);

-- Indexes for play lookups
CREATE INDEX IF NOT EXISTS idx_play_embeddings_game_id ON rag.play_embeddings(game_id);
CREATE INDEX IF NOT EXISTS idx_play_embeddings_quarter ON rag.play_embeddings(quarter);
CREATE INDEX IF NOT EXISTS idx_play_embeddings_metadata ON rag.play_embeddings USING GIN (metadata);

-- HNSW index for play similarity search
CREATE INDEX IF NOT EXISTS idx_play_embeddings_hnsw_cosine ON rag.play_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- Table: document_embeddings
-- Purpose: Store embeddings for documentation, articles, analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS rag.document_embeddings (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL,  -- 'doc', 'article', 'analysis', 'report'
    document_id VARCHAR(100) NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_document UNIQUE(document_type, document_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_document_embeddings_type ON rag.document_embeddings(document_type);
CREATE INDEX IF NOT EXISTS idx_document_embeddings_metadata ON rag.document_embeddings USING GIN (metadata);

-- HNSW index for document similarity
CREATE INDEX IF NOT EXISTS idx_document_embeddings_hnsw_cosine ON rag.document_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- Table: embedding_generation_log
-- Purpose: Track embedding generation progress and costs
-- ============================================================================

CREATE TABLE IF NOT EXISTS rag.embedding_generation_log (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    total_records INTEGER NOT NULL,
    processed_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost_usd NUMERIC(10, 4) DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embedding_log_batch_id ON rag.embedding_generation_log(batch_id);
CREATE INDEX IF NOT EXISTS idx_embedding_log_status ON rag.embedding_generation_log(status);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: similarity_search
-- Purpose: Find most similar entities using cosine similarity
CREATE OR REPLACE FUNCTION rag.similarity_search(
    query_embedding vector(1536),
    entity_type_filter VARCHAR(50) DEFAULT NULL,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    entity_id VARCHAR(100),
    entity_type VARCHAR(50),
    text_content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.entity_id,
        e.entity_type,
        e.text_content,
        1 - (e.embedding <=> query_embedding) AS similarity,
        e.metadata
    FROM rag.nba_embeddings e
    WHERE
        entity_type_filter IS NULL OR e.entity_type = entity_type_filter
    ORDER BY e.embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function: hybrid_search
-- Purpose: Combine keyword search with vector similarity
CREATE OR REPLACE FUNCTION rag.hybrid_search(
    query_text TEXT,
    query_embedding vector(1536),
    entity_type_filter VARCHAR(50) DEFAULT NULL,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    entity_id VARCHAR(100),
    entity_type VARCHAR(50),
    text_content TEXT,
    vector_similarity FLOAT,
    text_rank FLOAT,
    combined_score FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.entity_id,
        e.entity_type,
        e.text_content,
        (1 - (e.embedding <=> query_embedding)) AS vector_similarity,
        ts_rank_cd(to_tsvector('english', e.text_content), plainto_tsquery('english', query_text)) AS text_rank,
        (
            (1 - (e.embedding <=> query_embedding)) * 0.7 +
            ts_rank_cd(to_tsvector('english', e.text_content), plainto_tsquery('english', query_text)) * 0.3
        ) AS combined_score,
        e.metadata
    FROM rag.nba_embeddings e
    WHERE
        (entity_type_filter IS NULL OR e.entity_type = entity_type_filter)
        AND (
            to_tsvector('english', e.text_content) @@ plainto_tsquery('english', query_text)
            OR e.embedding <=> query_embedding < 0.5
        )
    ORDER BY combined_score DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function: get_embedding_stats
-- Purpose: Get statistics about stored embeddings
CREATE OR REPLACE FUNCTION rag.get_embedding_stats()
RETURNS TABLE (
    entity_type VARCHAR(50),
    total_embeddings BIGINT,
    avg_text_length NUMERIC,
    earliest_created TIMESTAMP,
    latest_created TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.entity_type,
        COUNT(*) AS total_embeddings,
        AVG(LENGTH(e.text_content)) AS avg_text_length,
        MIN(e.created_at) AS earliest_created,
        MAX(e.created_at) AS latest_created
    FROM rag.nba_embeddings e
    GROUP BY e.entity_type
    ORDER BY total_embeddings DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================

-- View: player_embeddings_summary
CREATE MATERIALIZED VIEW IF NOT EXISTS rag.player_embeddings_summary AS
SELECT
    entity_id AS player_id,
    text_content,
    metadata->>'team' AS team,
    metadata->>'position' AS position,
    metadata->>'seasons_active' AS seasons_active,
    created_at
FROM rag.nba_embeddings
WHERE entity_type = 'player';

CREATE INDEX IF NOT EXISTS idx_player_embeddings_summary_player_id
ON rag.player_embeddings_summary(player_id);

-- View: game_embeddings_summary
CREATE MATERIALIZED VIEW IF NOT EXISTS rag.game_embeddings_summary AS
SELECT
    entity_id AS game_id,
    text_content,
    metadata->>'season' AS season,
    metadata->>'game_date' AS game_date,
    metadata->>'home_team' AS home_team,
    metadata->>'away_team' AS away_team,
    created_at
FROM rag.nba_embeddings
WHERE entity_type = 'game';

CREATE INDEX IF NOT EXISTS idx_game_embeddings_summary_game_id
ON rag.game_embeddings_summary(game_id);
CREATE INDEX IF NOT EXISTS idx_game_embeddings_summary_season
ON rag.game_embeddings_summary(season);

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION rag.refresh_embedding_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY rag.player_embeddings_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY rag.game_embeddings_summary;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers for updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION rag.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_nba_embeddings_updated_at
    BEFORE UPDATE ON rag.nba_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION rag.update_updated_at_column();

-- ============================================================================
-- Grants and Permissions
-- ============================================================================

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION rag.similarity_search(vector(1536), VARCHAR(50), INTEGER) TO PUBLIC;
GRANT EXECUTE ON FUNCTION rag.hybrid_search(TEXT, vector(1536), VARCHAR(50), INTEGER) TO PUBLIC;
GRANT EXECUTE ON FUNCTION rag.get_embedding_stats() TO PUBLIC;
GRANT EXECUTE ON FUNCTION rag.refresh_embedding_views() TO PUBLIC;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify pgvector version
DO $$
DECLARE
    version TEXT;
BEGIN
    SELECT extversion INTO version FROM pg_extension WHERE extname = 'vector';
    RAISE NOTICE 'pgvector version: %', version;
END $$;

-- Check table creation
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'rag' AND table_name = 'nba_embeddings') THEN
        RAISE NOTICE '✅ Table rag.nba_embeddings created successfully';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'rag' AND table_name = 'play_embeddings') THEN
        RAISE NOTICE '✅ Table rag.play_embeddings created successfully';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'rag' AND table_name = 'document_embeddings') THEN
        RAISE NOTICE '✅ Table rag.document_embeddings created successfully';
    END IF;
END $$;

-- Display embedding statistics (will be empty initially)
SELECT * FROM rag.get_embedding_stats();

-- ============================================================================
-- End of Schema
-- ============================================================================

COMMENT ON SCHEMA rag IS 'RAG (Retrieval-Augmented Generation) vector embeddings for NBA data';
COMMENT ON TABLE rag.nba_embeddings IS 'Vector embeddings for NBA entities (players, teams, games)';
COMMENT ON TABLE rag.play_embeddings IS 'Vector embeddings for individual play-by-play events';
COMMENT ON TABLE rag.document_embeddings IS 'Vector embeddings for documentation and analysis';
COMMENT ON TABLE rag.embedding_generation_log IS 'Track embedding generation progress and costs';
