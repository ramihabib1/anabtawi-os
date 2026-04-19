-- Migration: 001_consolidation_log
-- Idempotent: safe to re-run via Supabase SQL editor
-- Created: Phase 01 / Plan 01

CREATE TABLE IF NOT EXISTS consolidation_log (
    job_type              TEXT PRIMARY KEY,
    last_processed_cutoff TIMESTAMPTZ,
    last_run_at           TIMESTAMPTZ,
    last_run_success      BOOLEAN NOT NULL DEFAULT FALSE,
    total_runs_count      INTEGER NOT NULL DEFAULT 0
);

INSERT INTO consolidation_log (job_type, last_processed_cutoff, last_run_at, last_run_success, total_runs_count)
VALUES
    ('weekly_patterns', NULL, NULL, FALSE, 0),
    ('monthly_review',  NULL, NULL, FALSE, 0)
ON CONFLICT (job_type) DO NOTHING;
