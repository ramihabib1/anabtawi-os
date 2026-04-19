-- Migration: 002_prediction_log
-- Idempotent: safe to re-run via Supabase SQL editor
-- Created: Phase 01 / Plan 01

CREATE TABLE IF NOT EXISTS prediction_log (
    id                UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
    product_id        UUID         NOT NULL REFERENCES products(id),
    agent             TEXT         NOT NULL,
    predicted_value   NUMERIC(8,2) NOT NULL,
    confidence        NUMERIC(4,3) NOT NULL,
    snapshot_date     DATE         NOT NULL,
    resolution_date   DATE         NOT NULL,
    resolution_status TEXT         NOT NULL DEFAULT 'pending'
                      CHECK (resolution_status IN ('pending', 'accurate', 'inaccurate')),
    actual_outcome   NUMERIC(8,2),
    resolved_at       TIMESTAMPTZ,
    run_id            TEXT,
    reasoning         TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prediction_log_resolution
    ON prediction_log (resolution_date, resolution_status);

CREATE INDEX IF NOT EXISTS idx_prediction_log_product
    ON prediction_log (product_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_prediction_log_run
    ON prediction_log (run_id);
