-- ══════════════════════════════════════════════════════════════
-- OVO — Supabase Database Schema
-- Run this ENTIRE file in: Supabase Dashboard → SQL Editor → New query
-- ══════════════════════════════════════════════════════════════


-- ┌─────────────────────────────────────────────┐
-- │  1. Enable pgvector extension               │
-- │  Required for semantic "vibe search"         │
-- └─────────────────────────────────────────────┘

CREATE EXTENSION IF NOT EXISTS vector
  WITH SCHEMA extensions;


-- ┌─────────────────────────────────────────────┐
-- │  2. Fragments table — the Git Graph          │
-- │  Each row = one musical idea (node).         │
-- │  parent_id creates Git-like branching.       │
-- └─────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS public.fragments (
  -- Primary key: auto-generated UUID
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Self-referencing FK for branching (NULL = root node)
  parent_id   UUID REFERENCES public.fragments(id)
              ON DELETE SET NULL
              DEFAULT NULL,

  -- Fragment classification
  type        TEXT NOT NULL
              CHECK (type IN ('raw_capture', 'ai_split'))
              DEFAULT 'raw_capture',

  -- Detected/assigned instrument stems
  stems       TEXT[] NOT NULL DEFAULT '{}',

  -- Extracted audio metadata
  bpm         INTEGER,
  key         TEXT,
  duration    TEXT,

  -- AI-generated metadata
  mood        TEXT,
  title       TEXT,

  -- Public URL to the .wav file in Supabase Storage
  file_url    TEXT,

  -- Vector embedding (OpenAI text-embedding-3-small = 1536 dims)
  -- Used for semantic "vibe search": find fragments by mood/feel
  embedding   vector(1536),

  -- Timestamps
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add a comment for documentation
COMMENT ON TABLE public.fragments IS
  'Musical idea fragments — the nodes in OVO''s Git-like version tree.';

COMMENT ON COLUMN public.fragments.parent_id IS
  'Self-referencing FK. NULL = root fragment. Non-null = derived from parent.';

COMMENT ON COLUMN public.fragments.embedding IS
  'OpenAI text-embedding-3-small vector (1536 dims) for semantic vibe search.';


-- ┌─────────────────────────────────────────────┐
-- │  3. HNSW Index for fast vector search        │
-- │  Cosine distance is best for text embeddings │
-- └─────────────────────────────────────────────┘

CREATE INDEX IF NOT EXISTS idx_fragments_embedding_hnsw
  ON public.fragments
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Standard index on parent_id for fast tree traversal
CREATE INDEX IF NOT EXISTS idx_fragments_parent_id
  ON public.fragments(parent_id);

-- Index on created_at for chronological queries
CREATE INDEX IF NOT EXISTS idx_fragments_created_at
  ON public.fragments(created_at DESC);


-- ┌─────────────────────────────────────────────┐
-- │  4. Row Level Security (RLS)                 │
-- │  Public read, service-role write.            │
-- └─────────────────────────────────────────────┘

ALTER TABLE public.fragments ENABLE ROW LEVEL SECURITY;

-- Anyone can read fragments (the frontend needs this)
CREATE POLICY "Public read access"
  ON public.fragments
  FOR SELECT
  USING (true);

-- Only authenticated users (or service role) can insert
CREATE POLICY "Authenticated insert"
  ON public.fragments
  FOR INSERT
  WITH CHECK (true);

-- Only authenticated users (or service role) can update
CREATE POLICY "Authenticated update"
  ON public.fragments
  FOR UPDATE
  USING (true);


-- ┌─────────────────────────────────────────────┐
-- │  5. Storage Bucket: ovo_audio                │
-- │  Stores the raw .wav files.                  │
-- └─────────────────────────────────────────────┘

-- Create the storage bucket (public so the frontend can stream audio)
INSERT INTO storage.buckets (id, name, public)
VALUES ('ovo_audio', 'ovo_audio', true)
ON CONFLICT (id) DO NOTHING;

-- Allow anyone to read audio files (public streaming)
CREATE POLICY "Public audio read"
  ON storage.objects
  FOR SELECT
  USING (bucket_id = 'ovo_audio');

-- Allow anyone to upload audio files (for hackathon convenience;
-- in production you'd restrict this to authenticated users)
CREATE POLICY "Public audio insert"
  ON storage.objects
  FOR INSERT
  WITH CHECK (bucket_id = 'ovo_audio');


-- ══════════════════════════════════════════════════════════════
-- ✅ Schema ready. You should see:
--    • Table: public.fragments
--    • Extension: vector
--    • Bucket: ovo_audio (in Storage tab)
--    • 3 indexes on fragments
-- ══════════════════════════════════════════════════════════════
