# core/memory.py
# ChromaDB persistent memory — save, retrieve, and bootstrap knowledge.
#
# Stage 4s: MemoryModule implements PocketModule.
#   start()        — runs bootstrap_knowledge() (skips if already seeded)
#   stop()         — no-op; ChromaDB persists automatically
#   health_check() — pings the collection with a lightweight query
#   on_event()     — handles "memory.store" events from the bus (4q)

import os
import uuid
import time
import chromadb

from config.settings import COLLECTION_NAME, N_MEMORIES, KNOWLEDGE_FILES
from core.pocket_module import PocketModule
from core.logger import log

# ── ChromaDB client ───────────────────────────────────────────────────────────
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CHROMA_PATH  = os.path.join(project_root, "chroma_data")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
memory        = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


# ═════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def save_memory(role: str, content: str):
    if len(content.strip()) < 20:
        return
    memory.add(
        documents=[f"{role}: {content}"],
        ids=[str(uuid.uuid4())],
        metadatas=[{"role": role, "timestamp": str(time.time())}]
    )


def get_relevant_memories(query: str) -> str:
    try:
        results = memory.query(query_texts=[query], n_results=N_MEMORIES)
        if not results["documents"][0]:
            return ""
        mems = "\n".join(results["documents"][0])
        log.memory_retrieval(query, len(results["documents"][0]))
        return f"--- Relevant memories ---\n{mems}\n---"
    except Exception as e:
        log.error("memory", str(e))
        return ""


def load_knowledge_file(filepath: str):
    path = os.path.join(project_root, filepath) if not os.path.isabs(filepath) else filepath
    if not os.path.exists(path):
        print(f"  [Knowledge file not found: {path}]")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    chunk_size, overlap = 600, 80
    chunks, start = [], 0
    while start < len(content):
        chunks.append(content[start:start + chunk_size])
        start += chunk_size - overlap
    for chunk in chunks:
        if chunk.strip():
            save_memory("knowledge", chunk)
    print(f"  [Knowledge loaded: {os.path.basename(path)} ({len(chunks)} chunks)]")


def bootstrap_knowledge():
    try:
        existing = memory.get(where={"role": "knowledge"}, limit=1)
        if existing["ids"]:
            return
    except Exception:
        pass
    print("\n  [First run — loading knowledge files...]")
    for f in KNOWLEDGE_FILES:
        load_knowledge_file(f)
    print()


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class MemoryModule(PocketModule):
    """Lifecycle wrapper for ChromaDB memory.

    start()  — bootstraps knowledge files on first run (skips if already done).
    stop()   — no-op; ChromaDB's PersistentClient flushes to disk automatically.
    health_check() — stores and retrieves a canary document to verify the
                     collection is read/write. Cleans up after itself.
    on_event() — handles "memory.store" from the event bus so other modules
                 can save memories without importing this module directly.
    """

    def start(self) -> None:
        bootstrap_knowledge()

    def stop(self) -> None:
        # ChromaDB persists automatically — nothing to flush or close.
        pass

    def health_check(self) -> bool:
        try:
            canary_id = "__health_check__"
            memory.upsert(
                documents=["health check"],
                ids=[canary_id],
                metadatas=[{"role": "health", "timestamp": str(time.time())}],
            )
            result = memory.get(ids=[canary_id])
            memory.delete(ids=[canary_id])
            return bool(result["ids"])
        except Exception as e:
            print(f"  [MemoryModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Supported event: {"type": "memory.store", "role": "...", "content": "..."}
        if event.get("type") != "memory.store":
            return
        role    = event.get("role", "assistant")
        content = event.get("content", "")
        if content:
            save_memory(role, content)


memory_module = MemoryModule()
