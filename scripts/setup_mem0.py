"""
One-time Mem0 setup script.
Verifies Mem0 can connect to Supabase pgvector and write/read memories.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mem0_client import get_memory

def main():
    print("Initializing Mem0...")
    memory = get_memory()
    print("Mem0 initialized.")

    print("Writing test memory...")
    result = memory.add(
        messages=[{"role": "assistant", "content": "Habib Distribution setup test: system initialized successfully."}],
        user_id="habib_distribution",
        metadata={
            "agent": "setup",
            "memory_type": "observation",
            "domain": "system",
            "confidence": 1.0,
        }
    )
    print(f"Write result: {result}")

    print("Searching for test memory...")
    search_result = memory.search(
        query="system initialized setup test",
        user_id="habib_distribution",
        limit=5
    )
    print(f"Search result: {search_result}")
    print(f"Found {len(search_result.get('results', []))} memories.")
    print("Mem0 setup complete.")

if __name__ == "__main__":
    main()
