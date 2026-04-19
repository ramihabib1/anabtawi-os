-- Migration: 003_recommendation_outcomes
-- Idempotent: safe to re-run via Supabase SQL editor
-- Created: Phase 01 / Plan 01

CREATE TABLE IF NOT EXISTS recommendation_outcomes (
    id                      UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
    approval_id             UUID         NOT NULL REFERENCES approval_requests(id),
    action_type             TEXT         NOT NULL,
    agent                   TEXT         NOT NULL,
    product_id              UUID         REFERENCES products(id),
    baseline_metrics        JSONB        NOT NULL DEFAULT '{}'::jsonb,
    measurement_window_days INTEGER      NOT NULL,
    actual_outcome          JSONB,
    revenue_delta           NUMERIC(10,2),
    outcome_status          TEXT         NOT NULL DEFAULT 'pending'
                            CHECK (outcome_status IN ('pending', 'measured', 'inconclusive')),
    measured_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recommendation_outcomes_approval
    ON recommendation_outcomes (approval_id);

CREATE INDEX IF NOT EXISTS idx_recommendation_outcomes_created
    ON recommendation_outcomes (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_recommendation_outcomes_action_type
    ON recommendation_outcomes (action_type, created_at DESC);
