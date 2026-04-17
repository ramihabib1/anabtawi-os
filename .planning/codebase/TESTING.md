# TESTING.md — Testing Approach & Coverage

## Current State: No Automated Test Suite
There is no pytest or unittest infrastructure. No test files, no CI test step, no coverage tooling.

The `scripts/` directory contains manual verification scripts, not automated tests:
- `scripts/setup_mem0.py` — verifies Mem0 connection (write a memory, search for it)
- `scripts/test_approval.py` — creates a test approval request in Supabase
- `scripts/verify_approval.py` — checks if a specific approval request exists/resolved

## Manual Testing Approach
From `PROJECT_STATE.md`:
> Phase 1: "Test with real production data (read-only, no actions)" / "Validate output: do the stockout predictions make sense?"

The current testing methodology is:
1. Run the agent script directly against production Supabase
2. Inspect the JSON output and Supabase table writes visually
3. Verify business logic correctness by domain reasoning (do the days-of-supply numbers make sense?)

## Sync Layer: No Tests Either
`sync/jobs/*.py` are tested by running them manually and checking `sync_log` table entries in Supabase. No mock SP-API responses or fixture data.

## CI Pipeline
`.github/workflows/deploy.yml` deploys on push to `main` but runs **no tests**:
```yaml
script: |
  git pull origin main
  venv/bin/pip install -r requirements.txt -q
  sudo systemctl restart habib-tgbot habib-executor
```

## What Testability Exists

### Graceful degradation tested implicitly
`core/mem0_client.py`'s `_mem0_unavailable` flag and None-return pattern was validated by running the inventory agent on a dev machine where Mem0/pgvector isn't reachable — the agent completes without crashing.

### Executor action dispatch
`executor/executor.py:execute()` has an `else` branch that writes `{"error": "Unknown action type: ..."}` — this is the only defensive coding that approximates a test boundary.

### SP-API connection validation
`executor/sp_api_client.py:validate_connection()` calls `Sellers.get_marketplace_participations()` — a lightweight auth probe usable as a smoke test.

## Recommendations (When Tests Are Added)
Based on the codebase structure, the highest-value tests would be:

**Unit tests for agent data processing:**
- `InventoryAgent._build_inventory_table()` — pure function, takes dicts, returns sorted list
- Stockout flag logic (days_of_supply thresholds: critical ≤7, warning ≤14)
- `_build_inventory_table` edge cases: zero velocity (999 days), missing snapshot data

**Integration tests (with real Supabase, no mocks):**
- Agent write cycle: does `process_response()` create the right `notifications` rows?
- Approval expiry: does `expire_approvals.py` correctly mark pending → expired?

**Claude response parsing:**
- The markdown fence stripping logic in `analyze()` — test with/without fences
- `json.loads()` failure paths — what happens with malformed Claude output?

## Known Test Gaps
- No validation of SP-API write payloads before execution
- No rollback or idempotency checks on approval execution
- No tests for Telegram callback handler (approve/reject state transitions)
- No contract tests between agent output schema and what Executor expects
- Claude prompt regressions are caught manually by reviewing output quality
