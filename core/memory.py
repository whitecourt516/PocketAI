# core/memory.py

import os
import uuid
import time
import chromadb

from config.settings import COLLECTION_NAME, N_MEMORIES, KNOWLEDGE_FILES

# ── ChromaDB client ───────────────────────────────────────────────────────────
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CHROMA_PATH  = os.path.join(project_root, "chroma_data")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
memory        = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


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
        return f"--- Relevant memories ---\n{mems}\n---"
    except Exception:
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