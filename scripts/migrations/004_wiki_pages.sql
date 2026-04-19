-- Migration: 004_wiki_pages
-- Idempotent: safe to re-run via Supabase SQL editor
-- Created: Phase 01 / Plan 01

CREATE TABLE IF NOT EXISTS wiki_pages (
    id             UUID    DEFAULT gen_random_uuid() PRIMARY KEY,
    slug           TEXT    UNIQUE NOT NULL,
    title          TEXT    NOT NULL,
    category       TEXT    NOT NULL
                   CHECK (category IN ('product', 'competitor', 'playbook', 'brief')),
    content        TEXT    NOT NULL,
    generated_from JSONB,
    generated_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wiki_pages_category
    ON wiki_pages (category);

CREATE INDEX IF NOT EXISTS idx_wiki_pages_slug
    ON wiki_pages (slug);
