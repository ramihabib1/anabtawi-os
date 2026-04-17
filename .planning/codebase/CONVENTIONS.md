# CONVENTIONS.md — Code Style & Patterns

## Language Style
- Python 3.12, no type: ignore comments, modern union syntax (`X | Y`)
- `from __future__ import annotations` used in async modules (sync layer)
- f-strings throughout; no `.format()` or `%` formatting
- `pydantic>=2.0.0` in deps but not currently used in implemented code — future use

## Module-Level Patterns

### Singletons (lazy, module-level)
```python
# core/supabase_client.py pattern
_client: Client | None = None

def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client
```
Same pattern in `core/mem0_client.py` and `core/anthropic_client.py`. Mem0 client adds a `_mem0_unavailable: bool` flag to suppress repeated connection attempts.

### Config as Module Constants
`core/config.py` loads `.env` via `dotenv.load_dotenv()` at import time and exposes everything as module-level constants. No dataclasses or Pydantic settings model — just `os.environ["KEY"]` for required, `os.environ.get("KEY", "")` for optional.

### Agent Pattern (Template Method)
```python
class MyAgent(BaseAgent):
    def __init__(self): super().__init__(agent_name="my_agent", domain="my_domain")
    def fetch_data(self) -> dict: ...      # required
    def analyze(self, data, memories) -> dict: ...  # required
    def process_response(self, response) -> str: ... # required
```
BaseAgent.run() calls them in order. No decorators, no dependency injection.

## Logging

### Sync Layer — structlog
```python
from sync.utils.logging import get_logger
logger = get_logger(__name__)
logger.info("event_name", key=value, count=N)  # structured k=v
logger.error("error_event", exc=str(e))
```
JSON in production (`ENVIRONMENT=production`), colored console in dev.

### Agent/Executor Layer — stdlib logging + print
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Executor started.")
# Agents also use print() for run-level progress:
print(f"[{self.run_id}] Fetching data...")
```
No structlog in agents — kept simple.

## Error Handling

### Agents: catch-all in BaseAgent.run()
```python
try:
    data = self.fetch_data()
    ...
except Exception as e:
    success = False
    error_message = str(e)
    self.send_failure_alert(e)  # → notifications table (Telegram picks it up)
finally:
    self.log_run(success, error_message, output_summary, duration_ms)
```
Individual step failures are caught at the base level. Subclass methods don't need try/except unless they want to handle partial failures.

### Mem0: graceful None fallback
```python
if self.memory is None:
    return []   # fetch_memories() silently skips
```
```python
if self.memory is None:
    print(f"Mem0 unavailable — skipping {len(obs)} observations")
    return     # write_observations() silently skips
```

### Sync Layer: tenacity retry on HTTP
```python
@retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=2, max=30),
)
async def _request(self, method, url, ...): ...
```

### DB writes: wrapped in try/except with print
```python
try:
    self.supabase.table("notifications").insert({...}).execute()
    alerts_written += 1
except Exception as e:
    print(f"[{self.run_id}] Failed to write alert: {e}")
```
DB write failures are non-fatal; agent continues and logs the partial failure.

## Claude Prompt Conventions

### JSON-only output instruction
Every agent system prompt ends with:
```
OUTPUT: You MUST respond with valid JSON only. No preamble, no markdown code blocks.
Just the raw JSON object matching this exact schema: {...}
```

### Defensive parsing (strip markdown fences)
```python
raw_text = response.content[0].text.strip()
if raw_text.startswith("```"):
    lines = raw_text.split("\n")
    raw_text = "\n".join(lines[1:-1])
result = json.loads(raw_text)
```

### L1 Rules injection
Every agent system prompt includes `L1_RULES` from `core/config.py` — a multiline string constant — to enforce business invariants regardless of memory context.

## Telegram Message Formatting
- HTML parse mode everywhere (`parse_mode="HTML"`)
- `<b>Bold</b>` for labels, no markdown
- Emoji-coded severity: 🔴 critical, 🟡 warning, 🔵 info, 🟢 healthy
- Inline keyboards use `callback_data="action:id"` pattern (e.g., `"approve:uuid"`)

## Supabase Query Patterns
```python
# Chained builder (sync client)
result = self.supabase.table("notifications").insert({...}).execute()
result = self.supabase.table("approval_requests").select("*").eq("status", "approved").is_("execution_result", "null").execute()

# Async client (sync layer)
result = await db.table("products").select("id, sku").eq("is_active", True).execute()
```
Always access `.data` on result. No ORM — raw dicts throughout.

## Naming Conventions Summary
| Context | Convention | Example |
|---------|------------|---------|
| Module files | snake_case | `inventory_agent.py` |
| Classes | PascalCase | `InventoryAgent`, `SPAPIClient` |
| Functions | snake_case | `fetch_data()`, `write_observations()` |
| Constants | UPPER_SNAKE | `L1_RULES`, `MODEL_DAILY` |
| DB table names | snake_case | `approval_requests`, `agent_runs` |
| Agent names in DB | snake_case string | `"inventory_agent"` |
| Memory types | lowercase | `"observation"`, `"pattern"`, `"playbook"` |
| Action types | snake_case | `"fba_replenishment"`, `"price_change"` |
