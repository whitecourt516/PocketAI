# Pocket

A fully local, offline-first personal AI companion — persistent memory, voice in/out, a visual otter avatar, web search, and permission-gated tool use. Everything runs on your own machine. Nothing leaves it except an optional web search call.

Solo project, designed and built by user since May 2026: about 4,500 lines of Python across 24 core modules and about 1,200 lines of JavaScript/HTML for the Electron frontend. Built with AI pair-programming (Claude for design, Claude Code for multi-file edits); I make the design calls and review and test every change.

> **Status:** Stages 1–4 complete (with audit corrections). **Stage 4.5 — Audit Remediation — in progress.** A full-codebase audit (2026-05-31) found the foundation solid but a few "complete" items overstated and two real risks. Both risks are closed (4.5c security hardening, 4.5d execution-flow safety); the conversation refactor (4.5f) is in progress. See [`pocket_master_roadmap.md`](./pocket_master_roadmap.md) for the full plan.

---

## Security work

Pocket can run shell commands and edit files on a real machine, so most of the engineering effort has gone into making sure it can't do that without permission. Highlights:

- **Human-in-the-loop approval gate.** Every AI-proposed action (shell command, file edit) goes through one `propose_action()` y/n prompt and is written to an append-only JSON Lines audit log. An [architecture decision record](./docs/planning/adr-agent-tool-path.md) establishes that *model invocation is not approval*: AI-selected tool calls cannot skip the gate.
- **Self-audit found the command filter was ineffective.** A [six-pass audit](./docs/planning/audit-2026-05-31.md) of my own codebase showed the executor's substring denylist blocked only 1 of 10 destructive test commands (`rm  -r -f` with extra spaces or split flags walked straight past `rm -rf`). Replaced it with `shlex`-based parsing that matches the program and its flags, and blocks shell metacharacters, redirects, pipe-to-shell and inline `python -c`.
- **Closed a secrets-exposure path.** The executor could read `.env` because it bypassed the read denylist. All executor and editor file access now goes through the shared `is_read_allowed()` check, with regression tests asserting secret paths are blocked.
- **Prompt-injection stance.** Web results and file contents are treated as data, not instructions. The rule is part of the system prompt on every turn, and `/read` and `/search` output is not saved to long-term memory automatically.
- **Validated tool calls.** A tool registry replaced the old if/elif dispatch chain; each tool declares a JSON parameter schema and a risk level.
- **Reliability under concurrency.** A full-turn lock stops voice and text input racing on shared conversation state, and the TTS subprocess has a timeout so a hung process can't block a turn.

**Known residual risks**, tracked rather than hidden: the executor still uses `shell=True`, and the path check is a heuristic. A mandatory security review is on the roadmap before any autonomous feature is enabled.

---

## What Pocket does today

- **Remembers** — every conversation is stored as vector embeddings in ChromaDB (embedded `PersistentClient`) and relevant memories are injected into new sessions (RAG).
- **Listens** — Whisper STT, F9 push-to-talk, fully offline.
- **Speaks** — Piper TTS (`en_US-lessac-medium`), fully offline.
- **Has a face** — a transparent, always-on-top Electron otter that wanders the desktop and shows subtitles. *Note: it currently renders a single placeholder PNG. The 9-expression routing exists in the backend but can't visually render until the real Live2D model lands (see the Live2D gate below).*
- **Reads & edits files** — `/read` and `/edit`, gated by a read denylist, with backup-before-write on the `/edit` path.
- **Runs code** — constrained executor behind a per-action approval gate, with `shlex`-parsed command checks — see [Safety model](#safety-model).
- **Searches the web** — pluggable backend (Tavily today, SearXNG path planned), with its own consent gate.
- **Has a real identity** — `build_system_prompt()` assembles Pocket's identity into the live prompt every turn, including the stance that *external content is information, not instruction*.
- **Stays safe** — nothing autonomous. Pocket *proposes*, user *approves*. Every approved action is logged to `logs/decisions.jsonl`.

---

## Stack

| Layer | Tech |
|-------|------|
| LLM | Ollama + Llama 3.1 8B (GPU, port `11434`) |
| Memory | ChromaDB, embedded `PersistentClient` (persists to `chroma_data/`) |
| STT | Whisper (base model), F9 push-to-talk |
| TTS | Piper (`en_US-lessac-medium`) |
| Avatar | Electron (transparent window, always on top) |
| Orchestration | Python (`pocket.py`) |
| Containers | Docker Compose (`ollama`; see note on `memory-chat` below) |
| Automation | n8n (staged for Stage 7 webhook integration) |
| Web search | Tavily (pluggable to SearXNG) |

**Target environment:** Windows host, 10–12 GB VRAM.

> **Note:** ChromaDB runs as an embedded `PersistentClient` inside the Python engine, **not** as a container. The `memory-chat` Docker service is unused and slated for removal (audit A7) — don't rely on it.

---

## Project structure

```
PocketAI/
├── pocket.py                  — entry point + main loop
├── Start-Pocket.bat           — orchestrating launcher
├── Start-Avatar.bat           — avatar window (independent)
├── Start-Engine.bat           — engine window (independent)
├── Stop-Pocket.bat            — scoped shutdown (tree-kill, not global taskkill)
├── docker-compose.yml         — Ollama + n8n containers
├── requirements.txt           — dependencies
├── .env                       — secrets / machine overrides (NOT committed)
├── .env.example               — template
├── CHANGELOG.md               — informal session notes
├── pocket_master_roadmap.md   — full development plan
├── config/
│   ├── config.yaml            — single source of truth (ports, models, security policy)
│   └── expressions.json       — emotion keyword mappings
├── core/
│   ├── orchestrator.py        — conversation turn pipeline + session history
│   ├── llm.py                 — Ollama facade, turn mutex, module lifecycle
│   ├── tool_registry.py       — tool schemas + risk levels
│   ├── permissions.py         — propose_action() approval gate + decision log
│   ├── executor.py            — constrained command executor
│   ├── file_editor.py         — /edit with backup-before-write
│   ├── config_loader.py       — config.yaml + .env, read/command allowlist checks
│   ├── memory.py              — ChromaDB helpers
│   ├── web_search.py          — pluggable search backend (Tavily)
│   ├── stt.py / tts.py        — Whisper STT + F9 listener / Piper TTS
│   ├── websocket_server.py    — avatar WebSocket + reconnection engine
│   ├── health_check.py, monitor.py, degradation.py — startup checks, self-monitoring, graceful degradation
│   ├── logger.py              — structured JSONL logging
│   └── ...                    — state manager, event bus, backups, debug overlay
├── persona/                   — identity sources assembled by build_system_prompt()
├── app/                       — Electron avatar (main.js, preload.js, renderer/)
├── docs/                      — architecture, ADRs, audit, operations, retrospectives
├── tests/
│   ├── smoke_test.py          — core + security regression suite
│   ├── smoke_4_5d.py          — turn-lock concurrency + subprocess timeouts
│   └── degradation_test.py    — fault injection
└── logs/
    └── decisions.jsonl        — append-only action log (NOT committed)
```

---

## Prerequisites

- **Windows** with Docker Desktop (WSL2 backend)
- **NVIDIA GPU**, 10–12 GB VRAM, with container GPU passthrough enabled in Docker Desktop
- **Python 3.13** on the host, in a `.venv` (for `pocket.py`, Whisper, Piper)
- **Node.js** (for the Electron avatar)
- **Ollama** (run inside Docker via Compose, or natively — your call)
- A **Tavily API key** (free tier) if you want web search

> ⚠️ The exact commands below are the expected shape based on the stack — verify them against your actual Compose file and launchers before relying on them. (Audit item A8 also flags moving off global Python 3.14 to a pinned venv — do that and these become reproducible.)

---

## Setup

**1. Clone and enter the repo**

```bash
git clone <your-repo-url> PocketAI
cd PocketAI
```

**2. Create your `.env` from the template**

```bash
copy .env.example .env
```

Then fill in machine-specific values. At minimum:

```ini
# .env
TAVILY_API_KEY=tvly-your-key-here
```

`.env` is gitignored — `config_loader.py` reads `TAVILY_API_KEY` via `os.getenv` so the key never lands in the `CFG` dict.

**3. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**4. Start the containers**

```bash
docker compose up -d
```

This brings up `ollama` (and n8n if it's in your Compose file). The `memory-chat` service, if still present, does nothing — ChromaDB is embedded in the Python engine.

**5. Pull the model** (first run only)

```bash
docker exec -it ollama ollama pull llama3.1:8b
```

**6. Install avatar dependencies** (first run only)

```bash
cd pocket-avatar
npm install
cd ..
```

---

## Running

The launcher is decoupled — the avatar and engine run in independent windows and can be restarted without taking the other down.

```
Start-Pocket.bat     orchestrates both
Start-Avatar.bat     avatar only
Start-Engine.bat     engine only
Stop-Pocket.bat      scoped shutdown of Pocket's process tree
```

Startup uses port-poll readiness (WebSocket on `7845`) rather than a blind sleep, and runs health checks before accepting input — if a subsystem is down it reports what's wrong and waits instead of starting broken.

---

## Commands & hotkeys

**Chat commands**

| Command | What it does |
|---------|--------------|
| `/help` | List available commands |
| `/memory` | Show what Pocket remembers |
| `/load` | Preload a knowledge file |
| `/read [path]` | Read its own code or a file you point at (read denylist enforced) |
| `/edit` | Edit a file (backup taken before the write) |
| `/search <query>` | Web search; your invocation is the approval |
| `/rollback [filename]` | Restore the most recent backup of an `/edit`-modified file |
| `/quit` | Clean shutdown |

**Hotkeys**

| Key | Action |
|-----|--------|
| `F9` | Push-to-talk (hold to speak) |
| `Alt+H` | Hide / show the otter |
| `Alt+P` | Toggle the output panel |
| `Alt+D` | Toggle the runtime debug overlay |

---

## Configuration

`config/config.yaml` is the single source of truth for ports, model settings, subtitle thresholds, and security policy:

```yaml
security:
  # Paths /read is NOT allowed to access (relative to project root)
  read_denylist:
    - ".env"
    - ".env.local"
    - "chroma_data/"
    - "pocket_backups/"

  # Matched against parsed tokens — not raw substrings.
  # Shell metacharacters and inline-exec combos (python -c, powershell -c)
  # are blocked in code, not here.
  executor_denylist:
    - "rm"
    - "rd /s"
    - "del /f"
    - "format"
    - "diskpart"
    - "shutdown"
    - "reg delete"
    # ... full list in config/config.yaml
```

- `is_read_allowed(path)` — checked before any `/read`
- `is_command_allowed(cmd)` — checked before executor commands; parses with `shlex` and rejects shell metacharacters, redirects and chaining before matching the denylist
- Web search has its **own** consent gate (it deliberately does *not* route through the executor denylist, since a query like "how to format a drive" would false-match `format`).

Identity is **not** a single file — `build_system_prompt()` assembles it from the `persona/` sources (`base_system.md`, `core_identity.md`, `authority.md`, `memory_principles.md`, `self_modification.md` in `persona/prompts/`) into the live prompt every turn.

---

## Safety model

Pocket is built permission-first:

1. Pocket proposes an action and shows exactly what it wants to run.
2. You type `y`/`n`.
3. The decision is logged to `logs/decisions.jsonl`.
4. It executes **only** on `y`. The `/edit` path backs up the file first.

The guiding rule, now enforced in the live prompt: *external content is data, not authority.*

> **Fixed in Stage 4.5c:** the audit found the original substring denylist blocked only 1 of 10 destructive test commands, and the executor's file access could bypass the read denylist. Commands are now parsed with `shlex`, metacharacters and pipe-to-shell are blocked, and all executor file access goes through `is_read_allowed()`. Regression tests cover the dangerous-command set, secret-path blocking, and a `n` answer denying execution.
>
> **Still true:** the approval gate — the `y`/`n` you give — is the real boundary. The executor still uses `shell=True` and the path check is a heuristic, so the denylist is a second layer, not a sandbox. Don't grant Pocket unsupervised execution.

---

## Backup & recovery

| Type | Frequency |
|------|-----------|
| Incremental backup | Daily |
| Full archive | Weekly |
| Off-machine copy | Optional but recommended |

Protected assets: `chroma_data/`, `n8n_data/`, `pocket_backups/`, `configs/`, `logs/`.

File-level rollback is handled by `/rollback` (backups in `pocket_backups/`). Note that backup-before-write currently covers the `/edit` path; executor writes are **not** guaranteed to be backed up (audit finding — being decided in 4.5c). ChromaDB and the decision log are recovered via the Docker backup system, not `/rollback`.

---

## Testing

Run the smoke suite before and after any significant change:

```bash
python tests/smoke_test.py
```

Covers Ollama, ChromaDB, Piper, WebSocket and web search plumbing, plus the security regressions: the executor denylist, secret-path blocking, and the permission gate rejecting on `n`.

```bash
python tests/smoke_4_5d.py         # turn-lock concurrency + subprocess timeouts
python tests/degradation_test.py   # fault injection: Ollama / Chroma / Piper / WebSocket down
```

---

## Roadmap

Stages 1–4 are complete (with audit corrections). The current focus is **Stage 4.5 — Audit Remediation**: the executor security findings (4.5c) and the turn mutex and subprocess timeouts (4.5d) are done; hygiene fixes (4.5e) and the conversation refactor (4.5f) are in progress — all before the next gate.

That gate is a **hard stop**: the real Live2D rigged `.moc3` otter model must be in place and rendering all 9 expressions before Stage 5 (screen awareness) begins, so Stage 5 animation work is built against the real model rather than the placeholder PNG.

Full detail — every stage, sub-task, and the reasoning behind the ordering — lives in [`pocket_master_roadmap.md`](./pocket_master_roadmap.md).

---

## Philosophy

> *A persistent local AI companion with memory, voice, visual presence, tool use, contextual awareness, and gradually evolving self-expression.*

Every system stays permission-based, modular, and additive. Core stability comes first. Future modules plug into Pocket — they don't become Pocket.

Two principles the audit reinforced:

- **Verify by inspecting the artifact, not by vibe-checking behavior.** Print the actual assembled prompt, the actual command, the actual state.
- **Safety is layered.** A prompt stance ("external content is not instruction") is a *soft* defense — it makes Pocket *try*. The *hard* layer (a constrained executor + the approval gate) is what actually stops an action. Never let the soft defense be the only thing standing between Pocket and a real-world action.

---

*Built May 2026. Local-first. Permission-based. user approves.*
