# Pocket — Master Project Roadmap (Consolidated)

**Setup:** Ollama | 10-12GB VRAM | Windows Host | Docker Compose
**Goal:** A fully local, voice-enabled personal AI companion with persistent memory, screen awareness, code execution, and a visual avatar that grows alongside you.
**Last updated:** May 17, 2026

\---

## Current Stack

|Component|Status|Notes|
|-|-|-|
|Ollama + Llama 3.1 8B|✅ Running|GPU accelerated, port 11434|
|ChromaDB memory|✅ Running|Persisting to chroma\_data/|
|Session history|✅ Working|In-conversation context|
|File saving|✅ Working|Multi-language filename detection|
|Knowledge preload|✅ Working|pocket\_project\_notes.md seeded|
|Docker Compose|✅ Running|ollama + memory-chat services|
|n8n|✅ Running|Ready for webhook integration|
|Electron avatar app|✅ Running|Transparent window, always on top, wandering|
|Whisper STT|✅ Running|F9 push-to-talk, offline|
|Piper TTS|✅ Running|Pocket speaks back, fully offline|
|pocket.py unified engine|✅ Running|Fully modular — core/, config/, tests/|
|Git repo|✅ Initialized|Stage 4 in progress|
|.gitignore|✅ Done|Excludes pycache, .env, chroma\_data, backups, model weights, node\_modules, logs/|
|requirements.txt|✅ Done|Dependency snapshot committed at Stage 4 start|
|pocket-identity.md|✅ Done|Canonical identity document, committed to repo|
|config/config.yaml|✅ Done|Single source of truth for all settings|
|core/config\_loader.py|✅ Done|Centralized config + .env loader|
|core/permissions.py|✅ Done|Permission gate + decision log (decisions.jsonl)|
|tests/smoke\_test.py|✅ Done|All 4 core systems green|

\---

## Reality Check — Feasibility Overview

|Feature|Feasibility|Notes|
|-|-|-|
|Persistent memory|✅ Done|ChromaDB RAG — working|
|Voice input/output|✅ Done|Whisper + Piper — working|
|Avatar / visual interface|✅ Done|Custom Electron app — working|
|File read/write|✅ Very doable|Write done, /read command next|
|Sandboxed code execution|✅ Doable|Subprocess + approval gate|
|Web search|✅ Doable|SearXNG local or Tavily API|
|Screen awareness|⚠️ Doable but tricky|Requires multimodal vision model|
|Proactive suggestions|⚠️ Doable but tricky|Builds on screen awareness|
|n8n workflow triggers|✅ Doable|Plumbing already in place|
|Avatar self-modification|✅ Doable|Config files are plain text Pocket can read/edit|
|True learning/improving|🔴 Hardest part|Fine-tuning — long game|

\---

## Master Build Order

```
Stage 1 — Memory (ChromaDB)                              ✅ COMPLETE
    ↓
Stage 2 — Voice (Whisper + Piper)                        ✅ COMPLETE
    ↓
Stage 3 — Interface \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\& Avatar (Electron app)               ✅ COMPLETE
    ↓
Stage 4 — Architecture Hardening + Self-Improvement       ← IN PROGRESS
    ↓
Stage 4 (cont.) — Event Bus, State Manager, Lifecycle Contract, Debug Overlay (4q–4t)
    ↓
⛔ HARD STOP — Real Live2D otter model must be in place
    ↓
Stage 5 — Screen Awareness + Dynamic Behavior
    ↓
Stage 6-Early — Intelligence Layer (Semantic Search, Skill Modes)
    ↓
Stage 6-Late — Intelligence Layer (Reflection, Routing, Emotional Continuity)
    ↓
Stage 7 — Full Computer Access + Integrations
    ↓
Stage 8 — Advanced Systems (Avatar Intelligence, Memory Vault, Knowledge Graph)
    ↓
Stage 9 — Knowledge Expansion + Fine-tuning (ongoing)
    ↓
Stage 9+ — Experimental Systems (Multi-Agent, Cognitive Profile, Research Lab)
```

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Note:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* Stages 6–8 from the original roadmap have been reorganized. The future-ideas files introduced several systems (Skill Modes, Memory Reflection, Workspace Awareness, Multi-Model Routing, etc.) that logically belong between Screen Awareness and Full Computer Access. Stage 6 has been split into Early and Late halves to prevent it from becoming an endless stage. Stage 8 is also where the \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Memory Vault\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* comes together — Stages 6d, 8b, and 8f are its three building blocks, with 8b being the completed system. The Live2D hard stop before Stage 4 ensures all animation work in Stage 5 is built against the real model, not a placeholder. Stage 9+ captures genuinely speculative long-game systems (multi-agent, cognitive profile, research lab) that become possible only after the full stack is stable.

\---

## Stage 1 — Memory ✅ COMPLETE

**Completed: May 2026**

Pocket has persistent memory via ChromaDB RAG. Every conversation is stored as vector embeddings and relevant memories are automatically injected into each new session.

### What's working

* ChromaDB persisting to disk across container restarts
* Relevant memory retrieval per query (top 6 results)
* Session history for in-conversation context
* Knowledge file preloading on first run
* Throwaway message filtering
* `/memory`, `/load`, `/help` commands
* File saving with flexible multi-language regex
* Pocket knows user's name, goals, projects, and preferences

\---

## Stage 2 — Voice ✅ COMPLETE

**Completed: May 2026**

Pocket can hear user and speak back. Both run fully offline.

### What's working

* **Whisper (base model)** — offline speech to text, F9 push-to-talk
* **Piper TTS** — offline text to speech, en\_US-lessac-medium voice
* Voice sessions persist to ChromaDB memory tagged as `\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\[voice]`
* Clean speech preprocessing strips markdown before speaking
* Integrated into unified `pocket.py` — no separate script needed

\---

## Stage 3 — Interface \& Avatar ✅ COMPLETE

**Completed: May 2026**

Pocket has a visual identity — an animated otter avatar that lives on user's desktop, reacts emotionally, and speaks with a subtitle bubble. A single batch file starts everything.

### What's working

* **Otter avatar** — wanders freely, always on top
* **Transparent window** — just the otter, no box or chrome
* **9 expressions** — neutral, happy, excited, thinking, surprised, concerned, sleepy, smug, sad
* **Auto expression detection** — keyword analysis drives expression changes automatically
* **Thinking state** — dots appear while Ollama processes
* **Subtitle bubble** — short responses appear above the otter, auto-dismiss
* **Output panel** — long responses and code open in a fixed bottom-right panel
* **Hotkeys** — Alt+H hides/shows otter, Alt+P toggles panel
* **Single launcher** — `Start Pocket.bat`
* **Clean shutdown** — `/quit` command

### Still pending for Stage 3

* **Real otter model** — Live2D rigged `.moc3` export replaces placeholder SVG. Drop files into `pocket-avatar/model/` and uncomment the Live2D loader in `avatar.html`.

### Self-modification hook (ready for Stage 4)

|File|What Pocket can change|
|-|-|
|`config/expressions.json`|Which words trigger which expression|
|`persona/prompts/base\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_system.md`|Its own personality|
|`app/main.js` CONFIG block|Wander speed, panel corner, window size|
|`config/config.yaml`|Subtitle threshold, ports, model settings|

\---

## Stage 4 — Architecture Hardening + Self-Improvement

**Priority: In Progress | Started: May 13, 2026**

### Session Log

|Date|Completed|
|-|-|
|2026-05-13|4i.1 — Git init, CHANGELOG.md, requirements.txt, .gitignore / 4l — pocket-identity.md|
|2026-05-14|4m — Docker backup + recovery strategy / pocket\_backup.bat confirmed clean / orphan volumes removed|
|2026-05-17|4a — Modular refactor complete (core/memory, tts, stt, websocket\_server, llm, avatar\_router) / 4a.1 — Smoke test suite, all systems green / 4b — Data-driven expression config (config/expressions.json) / 4c — Standardized avatar commands (core/avatar\_router.py) / 4o — TROUBLESHOOTING.md / 4p — config.yaml + .env loader + security denylist + is\_read\_allowed + is\_command\_allowed / 4e — Permission layer + decision log (logs/decisions.jsonl)|

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Why this stage was expanded:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* The two future-ideas files both identified the same critical point — architectural decisions made here prevent painful rewrites later. Self-improvement capabilities and structural hardening belong together in the same stage. The order below is deliberate — infrastructure and safety rails first, then capability on top of them.

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Order rationale:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* Git/backup/troubleshooting go first because they protect everything you build afterward. Identity document is written on Day 1 alongside Git — before any self-modification work, including the data-driven expression config. Security threat model must precede the executor. `/read` path restrictions are defined alongside 4p, not separately. WebSocket reconnection must be solid before Stage 5 introduces multiple concurrent avatar event sources. 4d (avatar asset structure) has been moved to Stage 5 — it requires the real Live2D model and belongs at the start of Stage 5 after the hard gate is cleared.

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*What to skip until the Live2D model is ready:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* 4d only. All other Stage 4 tasks are pure Python/backend work and have no dependency on the real model.

\---

### ✅ 4i.1 — Git + Changelog + Dependency Freeze (COMPLETE)

Initialize the git repo, changelog, and dependency snapshot before writing a single line of new code. This is the macro-level rollback and the record of every decision made from here forward.

**Conventions:**

* Commit at the end of every session with a meaningful message
* Tag completed stages: `git tag stage-4-complete`
* Maintain a `CHANGELOG.md` with informal session notes — what changed, what broke, what was fixed

**CHANGELOG format (keep it simple):**

```
## 2026-05-17
- Stage 4a complete — pocket.py fully modular
- Smoke tests all green
- config.yaml + permission layer in place

## 2026-05-13
- Stage 4 started — git init, identity doc, requirements.txt
```

**Dependency snapshot:**

```bash
pip freeze > requirements.txt
```

Re-run any time you intentionally add or update a package.

\---

### ✅ 4l — Pocket Identity Document (COMPLETE)

`pocket-identity.md` committed to project root. Canonical reference for all self-modification proposals.

\---

### ✅ 4m — Docker Backup + Recovery Strategy (COMPLETE)

**Completed: 2026-05-14**

Backup system in place. Restore verified from clean boot.

**Protected assets:**

```
chroma\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_data/
n8n\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_data/
pocket\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_backups/
Memory Vault/
configs/
logs/
```

**Minimum backup policy:**

|Type|Frequency|
|-|-|
|Incremental backup|Daily|
|Full archive|Weekly|
|Off-machine copy|Optional but recommended|

\---

### ✅ 4o — Troubleshooting Guide (COMPLETE)

`TROUBLESHOOTING.md` committed. Covers: Ollama, Docker, ChromaDB, Whisper, Piper, Electron avatar, expression engine, Git, import/module errors, emergency recovery, and verification checklist.

\---

### ✅ 4a — Modularize Early (COMPLETE)

**Completed: 2026-05-17**

pocket.py fully modular. Structure:

```
PocketAI/
├── pocket.py              — orchestrator only (imports + main loop)
├── config/
│   ├── config.yaml        — single source of truth
│   ├── settings.py        — backwards-compat shim
│   ├── persona.py         — system prompt stub
│   └── expressions.json   — emotion keyword mappings
├── core/
│   ├── config\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_loader.py   — loads config.yaml + .env
│   ├── memory.py          — ChromaDB helpers
│   ├── tts.py             — Piper TTS
│   ├── stt.py             — Whisper STT + F9 keyboard listener
│   ├── websocket\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_server.py — avatar WebSocket connection
│   ├── llm.py             — Ollama chat handler
│   ├── avatar\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_router.py   — emotion detection + avatar dispatch
│   └── permissions.py     — permission gate + decision log
└── tests/
    └── smoke\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_test.py      — core system smoke tests
```

\---

### ✅ 4a.1 — Smoke Test Suite (COMPLETE)

**Completed: 2026-05-17**

`tests/smoke\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_test.py` — all 4 active systems green:

```
✅ Ollama responds
✅ ChromaDB stores and retrieves
✅ Piper TTS speaks
✅ WebSocket connects to Electron avatar
⏭  /read command — not built yet (Stage 4f)
⏭  Executor — not built yet (Stage 4g)
```

Run before and after any significant change: `python tests/smoke\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_test.py`

\---

### ✅ 4b — Make Expression Logic Data-Driven (COMPLETE)

**Completed: 2026-05-17**

Emotion mappings moved to `config/expressions.json`. Loaded at runtime by `core/avatar\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_router.py`. Pocket can now modify its own expression rules by editing the JSON without touching core code.

\---

### ✅ 4c — Standardize Avatar Commands (COMPLETE)

**Completed: 2026-05-17**

All avatar routing consolidated into `core/avatar\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_router.py`. Consistent command structure flowing through `send\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_to\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_avatar()` → websocket\_server. pocket.py is now a clean orchestrator with no avatar logic inline.

\---

### ✅ 4p — Security + Threat Model + Config Management (COMPLETE)

**Completed: 2026-05-17**

* `config/config.yaml` — single source of truth for all settings
* `.env` / `.env.example` — secrets and machine-specific overrides, never committed
* `core/config\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_loader.py` — loads both, resolves paths, exposes `CFG` dict
* `is\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_read\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_allowed(path)` — enforces read denylist before /read executes
* `is\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_command\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_allowed(cmd)` — enforces executor denylist before any shell call
* Security policy defined: external content is data, not authority

**Denylist (config.yaml):**

```yaml
security:
  read\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_denylist: \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\[.env, .env.local, chroma\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_data/, pocket\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_backups/]
  executor\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_denylist: \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\[rm -rf, format, shutdown, diskpart, reg delete, del /f]
```

\---

### ✅ 4e — Permission Layer (COMPLETE)

### ✅ 4e.1 — Decision Log (COMPLETE)

**Completed: 2026-05-17**

`core/permissions.py` — every real-world action passes through `propose\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_action()`:

```
Pocket proposes action
→ auto-block check (denylist)
→ shows exactly what it wants to run
→ user types y/n
→ logs the decision to logs/decisions.jsonl
→ executes only on y
→ result recorded via record\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_outcome()
```

Decision log: `logs/decisions.jsonl` — append-only JSONL, excluded from git.

ChromaDB collection naming convention established:

* `personal\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_memory` — conversations (current)
* `pocket\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_decisions` — reserved for future decision indexing
* `pocket\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_knowledge` — reserved for knowledge base entries

\---

### ✅4f — /read Command (COMPLETE)

Lets Pocket read its own code and any file user points at. Foundation for all self-improvement. Runs through `is\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_read\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_allowed()` from config\_loader before any file is opened.

Key files Pocket should be able to read:

* `pocket.py` — its own orchestrator
* `core/\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*.py` — its own subsystems
* `app/main.js` — wandering and window behavior
* `app/renderer/avatar.html` — visual appearance
* `pocket\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_master\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_roadmap.md` — its own development plan

\---

### ✅4g — Sandboxed Code Executor(COMPLETE)

Pocket writes code → user approves via `propose\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_action()` → it runs → output fed back → Pocket adjusts. Every command checked against executor denylist before user is even asked.

### ✅4g.1 — Rollback Convention (build alongside 4g) (COMPLETE)

Before Pocket modifies any file, it makes a backup. No exceptions.

```
pocket\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_backups/
└── YYYY-MM-DD\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_HHMMSS\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_filename.ext
```

* Backup created automatically before any approved file modification
* Pocket confirms backup path in its proposal message
* `/rollback \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\[filename]` command restores the most recent backup
* Backups kept for 30 days, then pruned

**Scope note:** This rollback convention covers files only. ChromaDB vector writes and decision log entries (JSONL) are not covered — the Docker backup system (4m) is the recovery path for those.

\---

### 4s — Module Lifecycle Contract

**Priority: First — define the interface everything else plugs into**

As more modules are added, there's no standard way to start them, stop them, or check if they're healthy. A Module Lifecycle Contract defines that every core module implements the same interface. Build this first so that 4r, 4q, 4n, and 4j all speak the same language from the start.

**Contract:**

```python
class PocketModule:
    def start(self) -> None: ...       # called on launch
    def stop(self) -> None: ...        # called on clean shutdown
    def health\_check(self) -> bool: ...  # called by 4j startup checks
    def on\_event(self, event) -> None: ... # called by event bus (4q)
```

**Why first:** This is a two-hour task that makes every subsequent module cleaner. 4j startup health checks become generic instead of hard-coded per module. 4q event bus has a standard subscriber interface. Do it before you write any new module code.

\---

### 4r — Runtime State Manager

**Priority: Second — everything that follows reads from this**

Stage 5 introduces multiple systems that need to know what Pocket is currently doing: is it speaking? Is the avatar in an expression? Is it mid-reconnect? Right now there's no single source of truth.

A Runtime State Manager is a lightweight shared object that all modules read and write through. No module should infer Pocket's state from another module's internals.

**Tracked state:**

```python
state = {
    "avatar": {"expression": "thinking", "speaking": True},
    "connection": {"websocket": "CONNECTED"},
    "session": {"voice\_active": False, "current\_query": "..."},
    "health": {"ollama": True, "chroma": True, "piper": True}
}
```

**Why second:** Build this before 4q and 4n. The WebSocket reconnection state machine (4n) is just `state\["connection"]\["websocket"]` changing values — if 4r doesn't exist yet, 4n invents its own state object and you'll have two. The event bus (4q) can write to 4r on every emit. 4t (debug overlay) reads from 4r for free.

\---

### 4q — Event Bus

**Priority: Third — wire up after the contract and state exist**

Right now, modules call each other directly — avatar logic knows about TTS, the orchestrator knows about memory, etc. As Stage 5 introduces concurrent event sources (screen awareness, idle behaviors, conversation), direct coupling becomes a maintenance and debugging nightmare.

An internal event bus decouples every module. Nothing calls another module directly — it emits an event and subscribers handle it.

**Pattern:**

```python
# core/event\_bus.py
bus.emit("avatar.expression", {"name": "thinking", "source": "llm"})
bus.emit("tts.speak", {"text": "...", "priority": 1})
bus.emit("memory.store", {"content": "...", "tags": \["voice"]})
```

**Why third:** With 4s defining how modules subscribe and 4r holding shared state, the bus is straightforward to implement. Every new module added from here plugs into the bus cleanly. Retrofitting this after Stage 5 means rewriting all the new modules you just built.

\---

### 4n — WebSocket Reconnection Engine

**Priority: REQUIRED before Stage 5 — build on top of 4r**

Stage 5 introduces multiple concurrent avatar event sources. The WebSocket connection must be bulletproof before that complexity arrives.

If Electron crashes, restarts, reloads, or disconnects temporarily, `pocket.py` must detect disconnect immediately, enter degraded avatar mode, retry automatically, re-sync avatar state, and resume queued commands safely.

Required reconnection states: `CONNECTED → DISCONNECTED → RECONNECTING → DEGRADED\\\_MODE → RESYNCING`

These states live in `state\["connection"]\["websocket"]` (4r) — not in a local variable inside the WebSocket module. That way 4t can display them and 4j.1 can monitor them without coupling.

Not every event should replay on reconnect — current expression and active speech state: yes; expired subtitles and idle reactions: no.

\---

### 4i — Structured Logging

Log commands, approvals, failures, execution results, expression changes, and memory retrievals. Critical for debugging everything that comes after.

\---

### 4j — Startup Health Checks

Replace silent waiting with an explicit health check sequence. Calls `health\_check()` on each module (4s interface) rather than hard-coding per-service checks.

```
\[1/4] Checking Ollama...        ✅ Ready (port 11434)
\[2/4] Checking ChromaDB...      ✅ Ready (chroma\_data/)
\[3/4] Checking WebSocket...     ✅ Ready (port 7845)
\[4/4] Checking Piper TTS...     ✅ Ready
Pocket is online.
```

If any check fails, Pocket reports exactly what's wrong and waits rather than starting in a broken state.

\---

### 4j.1 — Continuous Self-Monitoring

Extends startup health checks into the full session. Lightweight background thread monitors:

* Ollama response latency
* ChromaDB retrieval quality
* WebSocket stability
* Expression accuracy
* Memory growth rate

Surfaces warnings to user when thresholds are crossed. No automatic action — Pocket reports, user decides. Writes health values into 4r state so 4t can display them live. Feeds Stage 8k (Self-Observability Dashboard).

\---

### 4t — Runtime Debug Overlay

**Priority: Build right after 4j.1 — 4r does all the work, this just displays it**

A lightweight developer overlay — either in the terminal or a small Electron panel — that shows Pocket's live internal state at a glance. Not a full dashboard (that's Stage 8k), just enough to debug Stage 5's moving parts without adding print statements everywhere.

**What it shows:**

```
\[STATE]  avatar=thinking | speaking=False | ws=CONNECTED
\[EVENTS] last 5 bus events with timestamps
\[HEALTH] ollama=✅ chroma=✅ piper=✅ ws=✅
\[EXPR]   current=thinking | source=llm | cooldown=0.8s
```

Toggle with a hotkey (e.g. Alt+D). Reads directly from the Runtime State Manager (4r) — no extra instrumentation needed. This is a small payoff task after the infrastructure work of 4s/4r/4q/4n.

\---

### 4k — Graceful Degradation

Wrap core service calls in proper error handling:

* **Ollama unreachable** → Pocket says "I can't reach my language model right now" and waits
* **ChromaDB unreachable** → Pocket continues without memory, warns session won't be saved
* **WebSocket drops** → Avatar goes neutral, engine keeps running, reconnects automatically (via 4n)
* **Piper fails** → Falls back to text-only output, notifies user

Pocket should never silently die. It should always tell you what's wrong.

\---

### 4h — Web Search

Lower priority — useful but not required before Stage 5. Do after the architecture work is solid.

|Option|Notes|
|-|-|
|SearXNG|Fully local, self-hosted, no API key|
|Tavily API \*|Simple, free tier, cloud|
|requests + BeautifulSoup|Fetch and parse any URL directly|

```bash
pip install requests beautifulsoup4
```

### Bookmark

🔖 *"Let's harden Pocket's architecture and start Stage 4"*
🔖 *"Help me write Pocket's identity document"*

\---

## Stage 5 — Screen Awareness + Dynamic Idle Behavior

**Priority: Medium-Advanced | Estimated time: 1-2 weekends**

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Consolidation note:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* Dynamic idle behaviors (ambient animations, mouse reactions, sleepy states) were listed in both future-ideas files as Stage 5-6. They belong here alongside screen awareness since both are about Pocket perceiving and reacting to its environment.

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Order rationale:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* VRAM management and privacy boundaries must be defined \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*before\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* loading a vision model or taking screenshots. Expression arbitration must be in place \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*before\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* introducing concurrent behavior sources (idle + conversation + workspace). Infrastructure first, then the capabilities that depend on it.

## ⛔ HARD STOP — Live2D Otter Model

**Must be complete before Stage 5 begins**

The real Live2D rigged `.moc3` otter model must be in place before Stage 5 begins. This is a hard gate, not a soft recommendation.

**What "in place" means:**

* `.moc3` export dropped into `pocket-avatar/model/`
* Live2D loader uncommented in `avatar.html`
* All 9 current expressions mapped and confirmed working
* Wandering and subtitle behavior confirmed on real model
* Physics and breathing confirmed stable

**Do not start Stage 5 until this checklist is complete.**

\---

### 5d-pre — Organize Avatar Assets

**First task of Stage 5 — do immediately after Live2D gate is cleared**

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Note:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* This task was originally 4d in Stage 4 and was deferred here because it requires the real `.moc3` model to be in place. Do not attempt before the hard gate above is complete.

```
pocket-avatar/
├── models/
│   ├── otter\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_v1/
│   └── experimental/
├── expressions/
├── physics/
├── animations/
├── configs/
└── exports/
```

\---

### 5d — VRAM Budget + Model Lifecycle Management

**Priority: REQUIRED — do this before 5a (loading LLaVA)**

|Question|Must be answered|
|-|-|
|Which models stay resident?|Always: Llama 3.1 8B (\~6GB)|
|Which load on demand?|LLaVA, coding specialist, reflection model|
|What unloads first under pressure?|Defined priority order|
|Can models coexist concurrently?|No — not on 10–12GB initially|
|What happens on OOM?|See failure behavior below|

Model lifecycle states: `UNLOADED → LOADING → READY → ACTIVE → IDLE → UNLOADING → FAILED`

On VRAM exhaustion: abort non-critical load, preserve conversation model, notify user, suggest unload candidates — never crash silently.

\---

### 5e — Privacy Boundary + Observation Rules

**Priority: REQUIRED — do this before 5a (taking screenshots)**

Create `privacy\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_config.yaml` covering: ignored folders (banking/, taxes/, passwords/), ignored file types (.kdbx, .env), ignored apps (password managers), screenshot suppression for fullscreen banking/login windows, and voice suppression during meetings/calls.

**Observation modes:**

|Mode|Behavior|
|-|-|
|Full awareness|Pocket can analyze and store|
|Observe only|Pocket sees but does not store|
|Private mode|Pocket ignores entirely|

Memory tags: `persistent`, `ephemeral`, `private`, `restricted`.

\---

### 5a — Screen Awareness

With VRAM budget defined and privacy rules in place, Pocket can now safely see what's on user's screen.

1. Python script takes a screenshot (hotkey or timer triggered)
2. Screenshot sent to a vision-capable local model
3. Pocket responds with observations or suggestions
4. Response spoken via Piper and shown on avatar

|Model|VRAM|Notes|
|-|-|-|
|LLaVA 13B|\~10GB|Best capability for your VRAM|
|LLaVA 7B|\~6GB|Good balance|
|Moondream 2|\~4GB|Lightweight, surprisingly capable|

\---

### 5b — Proactive Suggestions

* **Hotkey triggered** — press a key, Pocket comments on what it sees (start here)
* **Activity triggered** — speaks up after X minutes on the same screen
* **Context triggered** — recognizes specific apps, offers relevant help
* **Bug detection** — proactive code analysis before you ask

\---

### 5f — Expression Arbitration Layer

**Priority: REQUIRED — build this before 5c introduces concurrent behaviors**

Expression requests become structured events:

```json
{
  "source": "conversation",
  "expression": "concerned",
  "priority": 90,
  "duration": 2.5,
  "interruptible": false
}
```

**Priority order:**

|Source|Priority|
|-|-|
|Critical warnings/errors|100|
|Active conversation emotion|90|
|Speech-linked reactions|80|
|Workspace awareness|60|
|Environmental reactions|50|
|Idle animations|10|

\---

### 5c — Dynamic Idle Behaviors

With the arbitration layer in place, Pocket gains ambient animations and environmental reactions:

* Reacts to mouse movement
* Becomes quieter late at night
* Excited idle state during active projects
* Calmer during writing sessions
* Sleepy states during inactivity
* Quieter during games/fullscreen apps

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Extension note:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* Spatial workspace awareness — learning which monitor is coding vs research, recognizing fullscreen IDE as deep focus mode — is a natural extension of 5c.

### Bookmark

🔖 *"Let's build screen awareness for Pocket"*

\---

## Stage 6-Early — Intelligence Layer (High Value First)

**Priority: Advanced | Builds on Stages 4-5**

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Why Stage 6 is split:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* Stage 6 originally contained six substantial sub-systems. Semantic search and Skill Modes deliver the most immediate practical value and are relatively self-contained. The remaining systems (reflection, routing, emotional continuity) build on each other and are better tackled as a second pass once 6-Early is stable.

### 6a — Local Semantic Search

**Priority: VERY HIGH — highest practical value upgrade**

Pocket searches across markdown notes, codebases, logs, project folders, documentation, and saved conversations using embeddings + RAG.

\---

### 6b — Skill Modes

|Mode|Behavior|
|-|-|
|Coding assistant|Dev-focused prompts, code tools, error analysis|
|Cybersecurity analyst|PCAP/EVTX analysis, log summaries, investigation notes, report drafting|
|Writing editor|Editorial tone, research support, proofreading|
|Research assistant|Source gathering, summarization, citations|
|Casual companion|Relaxed tone, idle chat|
|Planning mode|Task breakdown, project tracking|

Each mode modifies: prompts, tool access, response style, avatar expressions, memory weighting.

\---

### 6c — Workspace Awareness

Pocket recognizes active sessions (coding, writing, research, gaming) and adapts:

* Quieter during focus sessions
* Coding-oriented help while IDEs are active
* Relaxed idle behavior during media viewing
* Different expression sets per activity type

### Bookmark

🔖 *"Let's build Pocket's intelligence layer — starting with semantic search"*

\---

## Stage 6-Late — Intelligence Layer (Depth Systems)

**Priority: Advanced | Builds on 6-Early**

### 6d — Memory Reflection System

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Memory Vault — Building Block 1 of 3\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*

Pocket periodically reviews conversations, projects, recurring themes, and unfinished tasks, then generates long-term summaries, project continuity notes, recurring goal tracking, and observations.

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*Vault schema decision — do this before building 6d:\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\* Decide the top-level structure of the Memory Vault before Pocket starts writing reflections. Suggested categories: `projects/`, `people/`, `concepts/`, `tools/`, `lessons-learned/`, `goals/`. Each entry is a markdown file, interlinked with `\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\[\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\[wiki-style]]` references. Sketch this in a `vault-schema.md` file during Stage 6-Early.

\---

### 6d.1 — Project Continuity Notes

Between sessions, Pocket reviews what was worked on, what was left unfinished, and drafts a "here's where we left off" summary. Displayed on session start or via `/continuity`. Stored in the Vault under `projects/`.

\---

### 6d.2 — Passive Observation + Draft Proposals

Pocket accumulates observations about its own behavior and drafts proposals for user to review. Maintained in a `proposals/` Vault section. Nothing acted on without approval.

\---

### 6e — Emotional Continuity Layer

Pocket tracks interaction tone, stress indicators, enthusiasm patterns, and recurring frustrations for better conversational continuity. Must remain: lightweight, respectful, non-invasive, user-controlled.

\---

### 6f — Multi-Model Routing

|Task|Model|
|-|-|
|Conversation|Llama 3.1|
|Vision|LLaVA|
|Lightweight tasks|Small local model|
|Coding|Coding-specialized model|
|Reflection/planning|Reasoning-oriented model|

\---

### 6g — Context Window Management

* **Session summarization** — after N turns, Pocket auto-summarizes earlier conversation into a compact block
* **Priority injection** — Vault entries and Skill Mode prompts always get context slots
* **Explicit context budget** — each category gets an allocated token budget

\---

### 6h — Memory Pruning + Retrieval Quality Control

Every stored memory gains metadata:

|Field|Purpose|
|-|-|
|importance\_score|Long-term value|
|confidence|Reliability|
|last\_accessed|Retrieval recency|
|superseded\_by|Replacement chain|
|memory\_type|Project/chat/error/etc|
|retention\_policy|Persistent/ephemeral|

Required: duplicate collapsing, stale archival, low-value pruning, failed-attempt tagging, optional human review queue.

\---

### 6h.1 — Background Memory Housekeeping

Extends 6h into idle time. Pocket quietly scans for duplicates, stale memories, and low-confidence entries, then generates a housekeeping report for user's review. Nothing changed without approval.

\---

### 6h.2 — Knowledge Gap Flagging

Pocket tracks topics where retrieval was weak or uncertain, maintains a `knowledge-gaps.md` log, and surfaces a prioritized list during idle time. Self-directed learning queue — Pocket knows what it doesn't know.

### Bookmark

🔖 *"Let's build the depth systems for Pocket's intelligence layer"*

\---

## Stage 7 — Full Computer Access + Integrations

**Priority: High-Advanced | Builds on Stages 4-6**

* Session pre-loading — context warmed up before likely sessions (7a)
* Sandboxed program access with per-action approval
* VS Code / IDE integration
* n8n webhook triggers
* File system watcher
* Calendar and schedule management
* Internal tool ecosystem

\---

## Stage 8 — Advanced Systems

### 8a — Avatar Intelligence Module

Co-pilot mode — Pocket takes initiative on suggestions but never acts autonomously.

### 8b — Memory Vault

Wiki-style self-building long-term memory. Building Block 2 of 3 (6d reflection feeds this; 8f writes to it in background).

### 8c — Sandbox Simulation Environment

Pocket tests proposals in isolation before presenting results. Sandboxed dry runs (8c.1).

### 8d — Adaptive Visual Identity

Seasonal themes, mood-adaptive appearance, long-term visual evolution.

### 8e — Pocket Workspace Dashboard

Unified view of active projects, memory health, tool usage, and system status.

### 8f — Background Reflection Loop

Building Block 3 of 3 — Pocket writes to the Vault autonomously during idle time. Feeds 8b.

### 8g — Contextual Sound Design

Ambient audio, reaction sounds, environmental feedback.

### 8h — Episodic Memory Timeline

Reconstruct project eras and periods. "What was I working on in April?"

### 8i — Unified Knowledge Graph

Typed relationships across projects, tools, concepts, and people.

### 8j — Adaptive Learning From Corrections

Behavioral feedback metadata — Pocket learns from being corrected.

### 8k — Self-Observability Dashboard

VRAM, retrieval quality, tool usage, expression accuracy — feeds from 4j.1 monitoring.

### 8l — Active Project Management

Open tasks, blockers, stalled work — Pocket tracks progress across sessions.

### 8m — Architecture Drift Detection

Periodic codebase consistency analysis — flags when implementation diverges from intent.

### 8n — Internal Documentation Agent

Auto-draft docs after approved changes.

### 8o — Long-Term Goal Tracking

Compare current work against stated goals over time.

\---

## Stage 9 — Knowledge Expansion + Fine-tuning (ongoing)

Continuous knowledge loading, model fine-tuning experiments, and capability expansion as the system matures.

\---

## Stage 9+ — Experimental / Long-Game

### 9a — Personal Cognitive Profile

Operationally adaptive explanation style — Pocket learns how user thinks.

### 9b — Multi-Agent Internal Collaboration

Specialist agents orchestrated by Pocket for complex tasks.

### 9c — Personal AI Research Lab

Architecture comparison, fine-tune experiments, model evaluation.

\---

## Master Checklist

### Core Systems

* \[x] Persistent memory — ChromaDB RAG (Stage 1)
* \[x] Voice input — Whisper STT, F9 push-to-talk (Stage 2)
* \[x] Voice output — Piper TTS, offline (Stage 2)
* \[x] Otter avatar — custom Electron app, transparent, always on top (Stage 3)
* \[x] Auto expression detection from response text (Stage 3)
* \[x] Subtitle bubble for short responses (Stage 3)
* \[x] Output panel for long responses and code (Stage 3)
* \[x] Single batch file launcher (Stage 3)
* \[ ] Real Live2D otter model swapped in
* \[ ] Contextual sound design (Stage 8g)
* \[ ] Adaptive visual identity / seasonal themes (Stage 8d)

### Architecture \& Self-Improvement

* \[x] Git repo initialized + CHANGELOG.md convention (Stage 4i.1)
* \[x] Dependency snapshot — requirements.txt committed (Stage 4i.1)
* \[x] Pocket identity document — pocket-identity.md (Stage 4l)
* \[x] Docker backup + restore system (Stage 4m — 2026-05-14)
* \[x] Restore verification test — confirmed boot from backup (Stage 4m)
* \[x] TROUBLESHOOTING.md with common recovery paths (Stage 4o)
* \[x] Modular architecture — core/, config/, tests/ (Stage 4a)
* \[x] Smoke test suite — all 4 systems green (Stage 4a.1)
* \[x] Data-driven expression config — config/expressions.json (Stage 4b)
* \[x] Standardized avatar commands — core/avatar\_router.py (Stage 4c)
* \[ ] Organized avatar asset structure (Stage 5d-pre — after Live2D gate)
* \[x] Threat model + security policy (Stage 4p)
* \[x] Config and secrets centralized — config.yaml + .env loader (Stage 4p)
* \[x] Executor denylist — is\_command\_allowed() (Stage 4p)
* \[x] Prompt injection guard — external content is data, not authority (Stage 4p)
* \[x] /read path restriction — is\_read\_allowed() (Stage 4p)
* \[x] Permission layer — propose\_action() gate (Stage 4e)
* \[x] ChromaDB collection naming convention sketched (Stage 4e.1)
* \[x] Decision log — logs/decisions.jsonl (Stage 4e.1)
* \[ ] /read command (Stage 4f) ← NEXT
* \[ ] Sandboxed code executor (Stage 4g)
* \[ ] Rollback convention — auto-backup before any file modification (Stage 4g.1)
* \[ ] Module Lifecycle Contract — start/stop/health interface for all modules (Stage 4s)
* \[ ] Runtime State Manager — single source of truth for live state (Stage 4r)
* \[ ] Event Bus — decoupled inter-module messaging (Stage 4q)
* \[ ] WebSocket reconnection engine with state machine (Stage 4n — builds on 4r)
* \[ ] Avatar command replay policy (Stage 4n)
* \[ ] Structured logging (Stage 4i)
* \[ ] Startup health checks — explicit service status on launch (Stage 4j — uses 4s interface)
* \[ ] Continuous self-monitoring — latency, retrieval quality, WebSocket, expression accuracy (Stage 4j.1 — feeds into 4r)
* \[ ] Runtime Debug Overlay — live state/event/health view, Alt+D toggle (Stage 4t — reads from 4r)
* \[ ] Graceful degradation — Pocket reports failures, never silently crashes (Stage 4k)
* \[ ] Web search — SearXNG or Tavily (Stage 4h)
* \[ ] Avatar self-modification (expressions, wander config, personality)

### Screen \& Context Awareness

* \[ ] VRAM budget document + model lifecycle manager (Stage 5d — before loading LLaVA)
* \[ ] OOM recovery handling + dynamic model loading/unloading (Stage 5d)
* \[ ] privacy\_config.yaml — ignored folders, apps, file types (Stage 5e — before screenshots)
* \[ ] Semantic indexing exclusions + screenshot suppression rules (Stage 5e)
* \[ ] Observation modes — full / observe-only / private (Stage 5e)
* \[ ] Memory tagging system — persistent / ephemeral / private / restricted (Stage 5e)
* \[ ] Screenshot capture and vision model analysis (Stage 5a)
* \[ ] Proactive suggestions (Stage 5b)
* \[ ] Expression arbitration layer with priority system (Stage 5f — before concurrent behaviors)
* \[ ] Expression cooldown + blending + source tracking (Stage 5f)
* \[ ] Dynamic idle behaviors + environmental reactions (Stage 5c)
* \[ ] Spatial workspace awareness — monitor layout / focus mode detection (Stage 5c extension)

### Intelligence Layer — Early (6-Early)

* \[ ] Local semantic search across files (Stage 6a)
* \[ ] Skill modes — coding, cybersecurity, writing, research, casual (Stage 6b)
* \[ ] Workspace awareness — coding/writing/gaming modes (Stage 6c)
* \[ ] Vault schema defined — top-level categories sketched before 6d begins

### Intelligence Layer — Late (6-Late)

* \[ ] Memory reflection — identifies what matters (Stage 6d) ← Vault Block 1
* \[ ] Project continuity notes — between-session summaries ready on return (Stage 6d.1)
* \[ ] Passive observation + draft proposals — Pocket surfaces improvement ideas for review (Stage 6d.2)
* \[ ] Emotional continuity / mood awareness (Stage 6e)
* \[ ] Multi-model routing (Stage 6f)
* \[ ] Context window management — session summarization + priority injection (Stage 6g)
* \[ ] Memory metadata scoring system (Stage 6h)
* \[ ] Duplicate memory collapsing + stale archival/pruning (Stage 6h)
* \[ ] Retrieval quality controls (Stage 6h)
* \[ ] Background memory housekeeping — idle dedup + archival proposals (Stage 6h.1)
* \[ ] Knowledge gap flagging — tracks what Pocket doesn't know, surfaces learning candidates (Stage 6h.2)

### Computer \& Program Access

* \[ ] n8n workflow inventory maintained during Stages 4-6 (ready for Stage 7)
* \[ ] Session pre-loading — context warmed up before likely sessions (Stage 7a)
* \[ ] Sandboxed program access with per-action approval (Stage 7)
* \[ ] VS Code / IDE integration (Stage 7)
* \[ ] n8n webhook triggers (Stage 7)
* \[ ] File system watcher (Stage 7)
* \[ ] Calendar and schedule management (Stage 7)
* \[ ] Internal tool ecosystem (Stage 7)

### Advanced Systems

* \[ ] Avatar intelligence module — co-pilot, not autonomous (Stage 8a)
* \[ ] Memory Vault — wiki-style self-building long-term memory (Stage 8b)
* \[ ] Sandbox simulation environment (Stage 8c)
* \[ ] Sandboxed dry runs — Pocket tests proposals in isolation before presenting results (Stage 8c.1)
* \[ ] Background reflection loop — writes to the Vault (Stage 8f)
* \[ ] Pocket Workspace dashboard (Stage 8e)
* \[ ] Episodic Memory Timeline — reconstruct project eras and periods (Stage 8h)
* \[ ] Unified Knowledge Graph — typed relationships across projects, tools, concepts (Stage 8i)
* \[ ] Adaptive Learning From Corrections — behavioral feedback metadata (Stage 8j)
* \[ ] Self-Observability Dashboard — VRAM, retrieval quality, tool usage (Stage 8k)
* \[ ] Active Project Management — open tasks, blockers, stalled work (Stage 8l)
* \[ ] Architecture Drift Detection — periodic codebase consistency analysis (Stage 8m)
* \[ ] Internal Documentation Agent — auto-draft docs after approved changes (Stage 8n)
* \[ ] Long-Term Goal Tracking — compare current work against stated goals (Stage 8o)

### Experimental / Long-Game (Stage 9+)

* \[ ] Personal Cognitive Profile — operationally adaptive explanation style (Stage 9a)
* \[ ] Multi-Agent Internal Collaboration — specialist agents orchestrated by Pocket (Stage 9b)
* \[ ] Personal AI Research Lab — architecture comparison, fine-tune experiments (Stage 9c)

\---

## Redundancies Resolved

|Redundancy|Where it appeared|Resolution|
|-|-|-|
|Emotional memory / mood awareness / emotional continuity|All 3 files|Single feature: Stage 6e Emotional Continuity Layer|
|Memory reflection / dreaming / project continuity|Future ideas + Avatar notes|All three are Memory Vault building blocks: 6d (reflection), 8b (vault core), 8f (background writer)|
|Dynamic idle behaviors|Both future files|Consolidated into Stage 5c|
|Workspace awareness|Both future files|Single feature: Stage 6c|
|Skill modes|Both future files|Single feature: Stage 6b|
|Multi-model routing|Both future files|Single feature: Stage 6f|
|Local semantic search|Both future files|Single feature: Stage 6a|
|Sandbox simulation|Both future files|Single feature: Stage 8c|
|Cybersecurity assistant|Roadmap + Future ideas|Implemented as a Skill Mode (6b) rather than standalone system|
|Permission layer emphasis|All 3 files|Already in Stage 4e; noted as CRITICAL throughout|
|Modular architecture emphasis|All 3 files|Stage 4a — do first|
|Long-term avatar evolution|Both future files|Stage 8d Adaptive Visual Identity|
|Simulation / Planning Mode (ideas\_2 #8)|ideas\_2|Same as Stage 8c Sandbox Simulation — merged|
|Autonomous quiet maintenance (ideas\_2 #11)|ideas\_2|Housekeeping behaviors folded into Stage 8f Background Reflection Loop|
|Cross-project insight generation (ideas\_2 #14)|ideas\_2|Output of Stage 8i Knowledge Graph — not a separate system|
|Spatial workspace awareness (ideas\_2 #12)|ideas\_2|Extension of Stage 5c dynamic idle behaviors — noted there rather than duplicated|
|Personal AI Research Lab (ideas\_2 #15)|ideas\_2|Stage 9c — valid but depends on full stack being stable first|
|Event Bus (4q) vs. 4j.1 Continuous Self-Monitoring|New stages review|Not redundant — 4j.1 monitors and reports health; 4q decouples how modules communicate. Both needed.|
|Runtime State Manager (4r) vs. 4j.1 health dict|New stages review|Not redundant — 4j.1 tracks service health booleans; 4r tracks live runtime state (expression, speech, connection phase). 4j.1 feeds into 4r as one of its fields.|
|Runtime Debug Overlay (4t) vs. Stage 8k Self-Observability Dashboard|New stages review|Not redundant — 4t is a lightweight dev tool (terminal/hotkey, reads 4r directly); 8k is a full persistent dashboard with historical data and charts. 4t is scaffolding; 8k is the product.|
|Module Lifecycle Contract (4s) vs. 4j Startup Health Checks|New stages review|Not redundant — 4j runs startup checks; 4s defines the interface those checks call. 4s makes 4j generic instead of hard-coded per module.|

\---

## Guiding Philosophy

Pocket's strongest long-term identity:

> \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*"A persistent local AI companion with memory, voice, visual presence, tool use, contextual awareness, and gradually evolving self-expression."\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\*

Every system should:

* Remain permission-based
* Remain modular
* Avoid destabilizing the core
* Improve collaboration instead of replacing you

Core stability always comes first. Future modules plug into Pocket — they don't become Pocket.

\---

*Built May 2026 | Stages 1–3 complete. Stage 4 in progress as of May 19, 2026. Completed this session: 4a, 4a.1, 4b, 4c, 4o, 4p, 4e, 4e.1. Added: 4q (Event Bus), 4r (Runtime State Manager), 4s (Module Lifecycle Contract), 4t (Runtime Debug Overlay). Next: 4f (/read command) → 4n (WebSocket reconnection) → 4q–4t → Live2D gate → Stage 5.*

