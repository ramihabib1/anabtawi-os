from mem0 import Memory
from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, SUPABASE_DB_URL

_memory: Memory | None = None
_mem0_unavailable = False


def get_memory() -> Memory | None:
    """Return Mem0 Memory instance, or None if connection unavailable."""
    global _memory, _mem0_unavailable
    if _mem0_unavailable:
        return None
    if _memory is None:
        try:
            _memory = _init_memory()
        except Exception as e:
            print(f"[mem0] WARNING: Could not connect to Mem0/pgvector: {e}")
            print("[mem0] Continuing without memory — agent will run with no prior knowledge.")
            _mem0_unavailable = True
            return None
    return _memory


def _init_memory() -> Memory:
    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
                "api_key": OPENAI_API_KEY,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "api_key": OPENAI_API_KEY,
            },
        },
        "vector_store": {
            "provider": "supabase",
            "config": {
                "connection_string": SUPABASE_DB_URL,
                "collection_name": "memories",
            },
        },
    }
    return Memory.from_config(config)
