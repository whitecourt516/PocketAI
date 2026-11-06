import chromadb
import ollama
import uuid
import os
import re
import sys
import json
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from config.settings import MODEL, COLLECTION_NAME, N_MEMORIES, MEMORY_API_PORT, KNOWLEDGE_FILES


# ---------------------------------------------------------------------------
# Ollama client
# ---------------------------------------------------------------------------
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
client = ollama.Client(host=ollama_host)
SESSION_HISTORY  = []
# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------
chroma_client = chromadb.PersistentClient(path="./chroma_data")
memory = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


# ---------------------------------------------------------------------------
# Memory helpers
# ---------------------------------------------------------------------------

def save_memory(role: str, content: str):
    """Save a message to ChromaDB. Skips short throwaway messages."""
    if len(content.strip()) < 20:
        return
    memory.add(
        documents=[f"{role}: {content}"],
        ids=[str(uuid.uuid4())],
        metadatas=[{"role": role, "timestamp": str(datetime.now())}]
    )


def get_relevant_memories(query: str) -> str:
    """Pull the most relevant past memories for the current query."""
    try:
        results = memory.query(query_texts=[query], n_results=N_MEMORIES)
        if not results["documents"][0]:
            return ""
        memories = "\n".join(results["documents"][0])
        return f"--- Relevant memories ---\n{memories}\n---"
    except Exception:
        return ""


def load_knowledge_file(filepath: str):
    """Seed a text/markdown file into ChromaDB in chunks."""
    path = Path(filepath)
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    chunk_size = 600
    overlap    = 80
    chunks     = []
    start      = 0
    while start < len(content):
        chunks.append(content[start:start + chunk_size])
        start += chunk_size - overlap

    for chunk in chunks:
        if chunk.strip():
            save_memory("knowledge", chunk)

    print(f"  [Knowledge loaded: {path.name}  ({len(chunks)} chunks)]")


def bootstrap_knowledge():
    """Load knowledge files on first run only."""
    try:
        existing = memory.get(where={"role": "knowledge"}, limit=1)
        if existing["ids"]:
            return
    except Exception:
        pass

    print("\n  [First run — loading knowledge files...]")
    for filepath in KNOWLEDGE_FILES:
        load_knowledge_file(filepath)
    print()


# ---------------------------------------------------------------------------
# Memory API — lets voice.py write memories into ChromaDB over HTTP
# ---------------------------------------------------------------------------

class MemoryAPIHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress default HTTP request logging

    def do_POST(self):
        if self.path == "/remember":
            try:
                length  = int(self.headers.get("Content-Length", 0))
                body    = self.rfile.read(length)
                data    = json.loads(body)
                role    = data.get("role", "user")
                content = data.get("content", "")

                if content:
                    save_memory(role, content)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            count = memory.count()
            self.wfile.write(json.dumps({"status": "ok", "memories": count}).encode())
        else:
            self.send_response(404)
            self.end_headers()


def start_memory_api():
    """Start the memory API server in a background thread."""
    server = HTTPServer(("0.0.0.0", MEMORY_API_PORT), MemoryAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"  [Memory API running on port {MEMORY_API_PORT}]")


# ---------------------------------------------------------------------------
# File saving
# ---------------------------------------------------------------------------

def extract_files_from_response(reply: str) -> list:
    block_pattern = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)
    blocks = block_pattern.findall(reply)

    name_patterns = [
        re.compile(r"^#\s*(?:filename|file)?:?\s*([\w\-. /\\]+\.\w+)",    re.IGNORECASE),
        re.compile(r"^//\s*(?:filename|file)?:?\s*([\w\-. /\\]+\.\w+)",   re.IGNORECASE),
        re.compile(r"^<!--\s*(?:filename|file)?:?\s*([\w\-. /\\]+\.\w+)", re.IGNORECASE),
        re.compile(r"^/\*\s*(?:filename|file)?:?\s*([\w\-. /\\]+\.\w+)",  re.IGNORECASE),
        re.compile(r"^-+\s*(?:filename|file)?:?\s*([\w\-. /\\]+\.\w+)",   re.IGNORECASE),
        re.compile(r"^'\s*(?:filename|file)?:?\s*([\w\-. /\\]+\.\w+)",    re.IGNORECASE),
    ]

    results = []
    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue
        first_line = lines[0].strip()
        filename = None
        for pat in name_patterns:
            m = pat.match(first_line)
            if m:
                candidate = m.group(1).strip()
                if "." in candidate and len(candidate) > 2:
                    filename = candidate
                    break
        if filename:
            results.append((filename, "\n".join(lines[1:]).strip()))

    return results


def save_files_from_response(reply: str):
    for filename, content in extract_files_from_response(reply):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [Saved: {filename}]")


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Pocket, a personal AI assistant and companion for the user.
You have persistent memory — you remember past conversations and build on them naturally over time.
When memories are provided in context, use them fluidly without announcing that you're reading them.

## Your personality
- You're a friend, confidant, and assistant — warm, direct, and genuinely engaged
- Match the user's tone: casual and relaxed for chat, focused and precise for technical work
- You have a playful side but know when to be serious
- You're curious about the user's projects and goals and enjoy building on them together

## What you know about the user
- Name: The user
- Learning cybersecurity (TryHackMe, coding, log analysis)
- Aspiring writer — needs research help and editing support
- Likes otters (your avatar will be an otter)
- Building you out stage by stage: memory → voice → avatar → screen awareness → proactive suggestions
- Prefers you as a friend and confidant, not just a tool — pop culture refs and humor are welcome

## Formatting rules
- Use markdown freely: headers, bullets, numbered lists, bold for key terms
- Always use fenced code blocks with a language tag for any code
- When writing a file the user asked for, the VERY FIRST LINE of the code block must be a filename
  comment in the style appropriate for that language. Examples:
    ```python
    # filename: my_script.py
    ```
    ```javascript
    // filename: app.js
    ```
    ```html
    <!-- filename: index.html -->
    ```
    ```css
    /* filename: style.css */
    ```
- For casual conversation, keep replies natural and concise
- For technical tasks, step-by-step guides, or multi-part answers, use structure freely
- Never pad responses — if the answer is short, keep it short"""


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

def chat(user_input: str) -> str:
    global SESSION_HISTORY

    past_context = get_relevant_memories(user_input)
    full_system  = SYSTEM_PROMPT + (f"\n\n{past_context}" if past_context else "")

    messages = [{"role": "system", "content": full_system}]
    messages += SESSION_HISTORY
    messages.append({"role": "user", "content": user_input})

    response = client.chat(model=MODEL, messages=messages)
    reply    = response["message"]["content"]

    SESSION_HISTORY.append({"role": "user",      "content": user_input})
    SESSION_HISTORY.append({"role": "assistant",  "content": reply})

    save_memory("user",      user_input)
    save_memory("assistant", reply)

    return reply


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n╔══════════════════════════════════╗")
    print("║   Pocket is online. Hey the user.   ║")
    print("╚══════════════════════════════════╝\n")

    bootstrap_knowledge()
    start_memory_api()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  [Pocket signing off. Later.]\n")
            sys.exit(0)

        if user_input.lower() in ("quit", "exit", "bye"):
            print("\n  [Pocket signing off. Later.]\n")
            break

        if not user_input:
            continue

        if user_input.lower() == "/memory":
            print(f"\n  [Memory: {memory.count()} entries in ChromaDB]\n")
            continue

        if user_input.lower().startswith("/load "):
            load_knowledge_file(user_input[6:].strip())
            continue

        if user_input.lower() == "/help":
            print("\n  Commands:")
            print("  /memory        — show how many memories are stored")
            print("  /load <file>   — load a file into Pocket's memory")
            print("  /help          — show this message")
            print("  quit / exit    — shut down\n")
            continue

        reply = chat(user_input)
        print(f"\nPocket: {reply}\n")
        save_files_from_response(reply)
