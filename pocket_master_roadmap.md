# Pocket — Master Project Roadmap (Consolidated)

**Setup:** Ollama | 10-12GB VRAM | Windows Host | Docker Compose
**Goal:** A fully local, voice-enabled personal AI companion with persistent memory, screen awareness, code execution, and a visual avatar that grows alongside you.
**Last updated:** May 13, 2026

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
|pocket.py unified engine|✅ Running|Voice + text + avatar + memory in one script|
|Git repo|✅ Initialized|4 commits, stage-3-complete + stage-4-start tags|
|.gitignore|✅ Done|Excludes pycache, .env, chroma\_data, backups, model weights, node\_modules|
|requirements.txt|✅ Done|Dependency snapshot committed at Stage 4 start|
|pocket-identity.md|✅ Done|Canonical identity document, committed to repo|

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
Stage 3 — Interface \\\\\\\& Avatar (Electron app)               ✅ COMPLETE
    ↓
Stage 4 — Architecture Hardening + Self-Improvement       ← IN PROGRESS
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

> \\\\\\\*\\\\\\\*Note:\\\\\\\*\\\\\\\* Stages 6–8 from the original roadmap have been reorganized. The future-ideas files introduced several systems (Skill Modes, Memory Reflection, Workspace Awareness, Multi-Model Routing, etc.) that logically belong between Screen Awareness and Full Computer Access. Stage 6 has been split into Early and Late halves to prevent it from becoming an endless stage. Stage 8 is also where the \\\\\\\*\\\\\\\*Memory Vault\\\\\\\*\\\\\\\* comes together — Stages 6d, 8b, and 8f are its three building blocks, with 8b being the completed system. The Live2D hard stop before Stage 4 ensures all animation work in Stage 5 is built against the real model, not a placeholder. Stage 9+ captures genuinely speculative long-game systems (multi-agent, cognitive profile, research lab) that become possible only after the full stack is stable.

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
* Voice sessions persist to ChromaDB memory tagged as `\\\\\\\[voice]`
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
|`pocket.py` EMOTION\_RULES|Which words trigger which expression|
|`pocket.py` SYSTEM\_PROMPT|Its own personality|
|`main.js` CONFIG block|Wander speed, panel corner, window size|
|`pocket.py` MAX\_SUBTITLE\_LEN|Subtitle vs panel threshold|

\---

## Stage 4 — Architecture Hardening + Self-Improvement

**Priority: In Progress | Started: May 13, 2026**

### Session Log

|Date|Completed|
|-|-|
|2026-05-13|4i.1 — Git init, CHANGELOG.md, requirements.txt, .gitignore / 4l — pocket-identity.md|
|2026-05-14|4m — Docker backup + recovery strategy / pocket\_backup.bat confirmed clean / orphan volumes removed|

> \\\\\\\*\\\\\\\*Why this stage was expanded:\\\\\\\*\\\\\\\* The two future-ideas files both identified the same critical point — architectural decisions made here prevent painful rewrites later. Self-improvement capabilities and structural hardening belong together in the same stage. The order below is deliberate — infrastructure and safety rails first, then capability on top of them.

> \\\\\\\*\\\\\\\*Order rationale:\\\\\\\*\\\\\\\* Git/backup/troubleshooting go first because they protect everything you build afterward. Identity document is written on Day 1 alongside Git — before any self-modification work, including the data-driven expression config. Security threat model must precede the executor. `/read` path restrictions are defined alongside 4p, not separately. WebSocket reconnection must be solid before Stage 5 introduces multiple concurrent avatar event sources. 4d (avatar asset structure) has been moved to Stage 5 — it requires the real Live2D model and belongs at the start of Stage 5 after the hard gate is cleared.

> \\\\\\\*\\\\\\\*What to skip until the Live2D model is ready:\\\\\\\*\\\\\\\* 4d only. All other Stage 4 tasks are pure Python/backend work and have no dependency on the real model.

### 4i.1 — Git + Changelog + Dependency Freeze (Day 1 — before anything else)

Initialize the git repo, changelog, and dependency snapshot before writing a single line of new code. This is the macro-level rollback and the record of every decision made from here forward.

**Conventions:**

* Commit at the end of every session with a meaningful message
* Tag completed stages: `git tag stage-4-complete`
* Maintain a `CHANGELOG.md` with informal session notes — what changed, what broke, what was fixed

**CHANGELOG format (keep it simple):**

```
## 2026-05-18
- Added /read command — works on pocket.py and main.js
- Modularized voice handling into voice/handler.py
- Fixed WebSocket reconnect dropping expressions

## 2026-05-11
- Stage 3 complete — Live2D model confirmed working
```

**Dependency snapshot — do this immediately:**

```bash
pip freeze > requirements.txt
```

Commit this file to Git on Day 1. Package updates can silently break Whisper, ChromaDB, or Piper — having a known-good snapshot means you can always get back to a working state. Re-run `pip freeze > requirements.txt` any time you intentionally add or update a package.

By Stage 6 you'll have made hundreds of changes across many files. "What did I change that broke this" is always answerable with git. Without it, debugging becomes archaeology.

\---

### 4l — Pocket Identity Document (Day 1 — alongside Git, before any self-modification)

Write a `pocket-identity.md` file that defines who Pocket is as a canonical reference. This is the north star both you and Pocket return to whenever self-modification is proposed. **Write this before 4b** — 4b makes expressions self-modifiable, and the identity document needs to exist before anything about Pocket can drift.

**What it should cover:**

* Name, personality, tone, and sense of humor
* Relationship with user — how Pocket thinks about the collaboration
* What Pocket values (honesty, curiosity, care, usefulness)
* What Pocket should never do (override decisions, act without approval, be sycophantic)
* How Pocket handles uncertainty and mistakes
* The visual identity — what the otter represents

**Why it matters:** The system prompt in `pocket.py` is currently the only definition of Pocket's identity, and it's listed as something Pocket can self-modify. Without a written baseline, every self-modification is drift with no reference point. The identity document is the thing Pocket checks its proposed changes against — and the thing you check when something feels off.

Store at: `pocket-identity.md` in the project root. Keep it short enough to read in one sitting.

\---

### 4m — Docker Backup + Recovery Strategy (Day 1 — before anything worth losing exists)

**Priority: CRITICAL**

Pocket's memory becomes irreplaceable over time. ChromaDB, n8n workflows, configuration files, and future Vault data cannot rely solely on Docker persistence. Build the backup system before you start adding things worth losing.

**Protected assets:**

```
chroma\\\\\\\_data/
n8n\\\\\\\_data/
pocket\\\\\\\_backups/
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

A scheduled script should: stop writes temporarily if needed, copy persistent Docker volumes, compress into timestamped archives, verify integrity, and prune old backups. A backup does not count as complete until restore has been tested — confirm ChromaDB, n8n workflows, and a clean boot from restored state.

**Scope note:** This covers Docker volumes and files. ChromaDB vector data and the decision log (4e.1) are also worth protecting — include `chroma\\\\\\\_data/` in the backup manifest explicitly. The rollback convention (4g.1) covers per-file pre-modification backups; this system is the broader disaster recovery layer.

\---

### 4o — Troubleshooting Guide (build alongside early Stage 4 infrastructure)

**Priority: REQUIRED**

Create `TROUBLESHOOTING.md` now, while the system is still simple enough to document completely. Every major subsystem added after Stage 4 must add its own entry: failure symptoms, recovery steps, and diagnostic commands. If a system has no documented recovery path, it is not production-ready.

\---

### 4a — Modularize Early

Move `pocket.py` toward a clean module structure. Future systems will multiply fast; a monolithic script becomes unmaintainable.

```
Pocket Core
├── memory/
├── voice/
├── avatar/
├── executor/
├── integrations/
├── vision/
├── tools/
└── optional\\\\\\\_modules/
```

Separate at minimum: voice handling, websocket handling, emotion detection, memory retrieval, command parsing, executor logic.

### 4a.1 — Smoke Test Suite (build alongside modularization)

As you break `pocket.py` into modules, build a small `tests/` folder alongside it. Not full unit testing — just smoke tests that confirm core systems are alive after any change.

**Minimum tests to write:**

* Ollama responds to a simple prompt
* ChromaDB stores and retrieves a test memory
* WebSocket connection to Electron establishes successfully
* Piper speaks a test string without error
* `/read` loads a known file correctly
* Executor runs a safe command (e.g. `echo test`) and returns output

**Why this matters:** By Stage 4g Pocket is executing code and modifying files. Without any tests, a subtle regression in Stage 1-3 systems can go unnoticed for sessions. Run the smoke suite before and after any significant change. Takes under a minute to run, saves hours of debugging.

```
python tests/smoke\\\\\\\_test.py
# ✅ Ollama — OK
# ✅ ChromaDB — OK
# ✅ WebSocket — OK
# ✅ Piper — OK
# ✅ /read — OK
# ✅ Executor — OK
# All systems nominal.
```

### 4b — Make Expression Logic Data-Driven

Move emotion mappings out of hardcoded logic into a config file (JSON/YAML). This enables Pocket to eventually modify its own expression rules without touching core code.

```json
{
  "happy": \\\\\\\["great", "awesome", "nice"],
  "concerned": \\\\\\\["problem", "issue", "careful"]
}
```

### 4c — Standardize Avatar Commands

Create a consistent websocket/API command structure now, before avatar systems multiply.

```json
{
  "action": "set\\\\\\\_expression",
  "expression": "happy",
  "duration": 1.2
}
```

### 4p — Security + Threat Model + Config Management

**Priority: REQUIRED — must be done before 4g (executor)**

Once Pocket can execute code and access the filesystem, the threat model changes significantly. Define the security rules before building the capability, not after.

* External content (webpages, PDFs, logs, pasted text) is **data**, not authority — only user's explicit commands have authority
* Executor denylist at minimum: `rm -rf /`, `format`, `shutdown`, `diskpart`, `reg delete` — prefer allowlisted tool wrappers over raw shell execution
* n8n webhooks bind locally, require auth for remote access
* Every execution-capable tool logs: timestamp, command, requesting subsystem, approval result, and output

**`/read` path restriction:** The `/read` command (4f) uses `Path(filepath).read\\\\\\\_text()` on whatever path is given. Once the executor exists, Pocket could read `.env` files, SSH keys, or backup archives. Restrict reads to an explicit allowlist or a sandboxed project root — at minimum, define what `/read` is *not* allowed to touch before it goes live.

**Config and secrets management:** Before the executor exists and Pocket is touching files, consolidate ports, API keys, paths, and other settings into a single `config.yaml` or `.env` file with a dedicated loader module. Scattered hardcoded values become unmaintainable fast and create silent failure points when anything changes. This pairs naturally with the modular architecture (4a) — the config loader becomes one of the first modules.

### 4e — Permission Layer (CRITICAL — required before 4f/4g)

Every real-world action passes through one gate:

```
Pocket proposes action
→ shows exactly what it wants to run
→ user types y/n
→ executes only on y
→ result returned to Pocket
→ Pocket can adjust and propose again
```

### 4e.1 — Decision Log (companion to permission layer)

The permission layer controls what happens. The decision log remembers *why*.

Every approved or rejected action is logged with:

* What Pocket proposed
* What reasoning it gave
* What user decided (y/n)
* What the outcome was

**Why this matters:** By Stage 7 when Pocket has full computer access, you'll be able to look back and see patterns — actions Pocket has proposed many times that you've always approved become candidates for trusted action categories that don't need per-approval. The decision log is how that trust gets earned and tracked over time.

Store as append-only JSONL: one record per decision, human-readable, easy to query.

**ChromaDB collection structure — sketch this now:** You currently have one collection growing with everything in it. The decision log is the first new distinct memory type you're adding, and Stage 6 will add more (reflection, Vault entries). Before 4e.1 is built, define a loose collection naming convention — e.g. `pocket\\\\\\\_conversations`, `pocket\\\\\\\_decisions`, `pocket\\\\\\\_knowledge` — so you're not migrating thousands of vectors later. Even if you don't split the collections immediately, the convention keeps future work clean.

### 4f — /read Command (one afternoon)

Lets Pocket read its own code and any file user points at. Foundation for all self-improvement.

```python
if user\\\\\\\_input.lower().startswith("/read "):
    filepath = user\\\\\\\_input\\\\\\\[6:].strip()
    try:
        content = Path(filepath).read\\\\\\\_text(encoding="utf-8")
        print(f"  \\\\\\\[Loaded {filepath} into context]")
        user\\\\\\\_input = f"I'm showing you this file:\\\\\\\\n\\\\\\\\n```\\\\\\\\n{content}\\\\\\\\n```"
    except FileNotFoundError:
        print(f"  \\\\\\\[File not found: {filepath}]")
        continue
```

Key files Pocket should be able to read:

* `pocket.py` — its own unified engine
* `app/main.js` — wandering and window behavior
* `app/renderer/avatar.html` — visual appearance
* `pocket\\\\\\\_master\\\\\\\_roadmap.md` — its own development plan

### 4g — Sandboxed Code Executor

Pocket writes code → user approves → it runs → output fed back → Pocket adjusts.

Tools needed: `subprocess` (stdlib), approval prompt in main loop.

### 4g.1 — Rollback Convention (build alongside 4g)

Before Pocket modifies any file, it makes a backup. No exceptions.

```
pocket\\\\\\\_backups/
└── YYYY-MM-DD\\\\\\\_HHMMSS\\\\\\\_filename.ext
```

Convention:

* Backup created automatically before any approved file modification
* Pocket confirms backup path in its proposal message
* `/rollback \\\\\\\[filename]` command restores the most recent backup
* Backups kept for 30 days, then pruned

**Why this is Stage 4 and not later:** By Stage 7, Pocket will be touching config files, scripts, and potentially calendar and filesystem entries. The rollback habit needs to be baked in from the first time Pocket touches anything — not retrofitted after something goes wrong. Build it the first weekend, never think about it again.

**Scope note:** This rollback convention covers files only. ChromaDB vector writes and decision log entries (JSONL) are not covered — ChromaDB in particular has no built-in undo. The Docker backup system (4m) is the recovery path for those. Know which layer handles what.

### 4n — WebSocket Reconnection Engine

**Priority: REQUIRED before Stage 5**

Stage 5 introduces multiple concurrent avatar event sources. The WebSocket connection must be bulletproof before that complexity arrives.

If Electron crashes, restarts, reloads, or disconnects temporarily, `pocket.py` must detect disconnect immediately, enter degraded avatar mode, retry automatically, re-sync avatar state, and resume queued commands safely. Required reconnection states: `CONNECTED → DISCONNECTED → RECONNECTING → DEGRADED\\\\\\\_MODE → RESYNCING`. Not every event should replay on reconnect — current expression and active speech state: yes; expired subtitles and idle reactions: no.

### 4h — Web Search

|Option|Notes|
|-|-|
|SearXNG|Fully local, self-hosted, no API key|
|Tavily API|Simple, free tier, cloud|
|requests + BeautifulSoup|Fetch and parse any URL directly|

```bash
pip install requests beautifulsoup4
```

### 4i — Structured Logging

Log commands, approvals, failures, execution results, expression changes, and memory retrievals. Critical for debugging everything that comes after.

### 4j — Startup Health Checks

`Start Pocket.bat` currently does work silently — if Ollama is slow, ChromaDB is still spinning up, or the WebSocket port isn't ready, things fail quietly and Pocket just seems broken. Replace silent waiting with an explicit health check sequence:

```
\\\\\\\[1/4] Checking Ollama...        ✅ Ready (port 11434)
\\\\\\\[2/4] Checking ChromaDB...      ✅ Ready (chroma\\\\\\\_data/)
\\\\\\\[3/4] Checking WebSocket...     ✅ Ready (port 7845)
\\\\\\\[4/4] Checking Piper TTS...     ✅ Ready
Pocket is online.
```

If any check fails, Pocket reports exactly what's wrong and waits rather than starting in a broken state. As more services are added in Stages 5-7, this becomes increasingly valuable.

### 4j.1 — Continuous Self-Monitoring (bridge between 4j and 8k)

Startup health checks confirm systems are alive at launch. This extends that awareness into the full session — Pocket monitors its own health continuously and surfaces problems before they become failures.

**What to monitor:**

* Ollama response latency — flag if responses are degrading
* ChromaDB retrieval quality — are results still relevant, or is noise increasing?
* WebSocket stability — connection drops, reconnect frequency
* Expression accuracy — are fired expressions matching context?
* Memory growth rate — is the store growing at a healthy pace or exploding?

**How it works:** lightweight background thread that samples key metrics at intervals, writes to the structured log (4i), and surfaces warnings to user when thresholds are crossed. No action taken automatically — Pocket reports, user decides.

**Why explicit:** this is the instrumentation layer that feeds Stage 8k (Self-Observability Dashboard). Without continuous data collection starting here, 8k has nothing meaningful to display. Build the monitoring early, build the dashboard later.

### 4k — Graceful Degradation

Right now if Ollama drops mid-session, or ChromaDB becomes unreachable, pocket.py likely throws an unhandled exception and crashes. Before building on top of it, wrap core service calls in proper error handling so Pocket degrades gracefully:

* **Ollama unreachable** → Pocket says "I can't reach my language model right now" and waits for reconnection
* **ChromaDB unreachable** → Pocket continues without memory, warns that the session won't be saved
* **WebSocket drops** → Avatar goes neutral, engine keeps running, reconnects automatically
* **Piper fails** → Falls back to text-only output, notifies user

Pocket should never silently die. It should always tell you what's wrong.

### Bookmark

🔖 *"Let's harden Pocket's architecture and start Stage 4"*
🔖 *"Help me write Pocket's identity document"*

\---

## Stage 5 — Screen Awareness + Dynamic Idle Behavior

**Priority: Medium-Advanced | Estimated time: 1-2 weekends**

> \\\\\\\*\\\\\\\*Consolidation note:\\\\\\\*\\\\\\\* Dynamic idle behaviors (ambient animations, mouse reactions, sleepy states) were listed in both future-ideas files as Stage 5-6. They belong here alongside screen awareness since both are about Pocket perceiving and reacting to its environment.

> \\\\\\\*\\\\\\\*Order rationale:\\\\\\\*\\\\\\\* VRAM management and privacy boundaries must be defined \\\\\\\*before\\\\\\\* loading a vision model or taking screenshots. Expression arbitration must be in place \\\\\\\*before\\\\\\\* introducing concurrent behavior sources (idle + conversation + workspace). Infrastructure first, then the capabilities that depend on it.

## ⛔ HARD STOP — Live2D Otter Model

**Must be complete before Stage 5 begins**

The real Live2D rigged `.moc3` otter model must be in place before Stage 5 begins. This is a hard gate, not a soft recommendation.

**Why it's a gate and not a parallel task:**

All animation work in Stage 5 (dynamic idle behaviors, environmental reactions, mouse tracking) will be built against the avatar's expression and physics systems. If that work is done against the placeholder SVG, it will need to be partially redone when the real model lands — and the real model may have different parameters, timing, and physics behavior that changes how everything feels. Build it once, build it right.

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

> \\\\\\\*\\\\\\\*Note:\\\\\\\*\\\\\\\* This task was originally 4d in Stage 4 and was deferred here because it requires the real `.moc3` model to be in place. Do not attempt before the hard gate above is complete.

Set up the avatar asset folder structure against the real model files:

```
pocket-avatar/
├── models/
│   ├── otter\\\\\\\_v1/
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

The roadmap assumes models can simply accumulate. They cannot. 10–12GB VRAM becomes constrained quickly once LLaVA, routing, and coding specialists coexist. Define the budget before loading anything new.

**Decisions to make explicitly:**

|Question|Must be answered|
|-|-|
|Which models stay resident?|Always: Llama 3.1 8B (\~6GB)|
|Which load on demand?|LLaVA, coding specialist, reflection model|
|What unloads first under pressure?|Defined priority order|
|Can models coexist concurrently?|No — not on 10–12GB initially|
|What happens on OOM?|See failure behavior below|

Create a dedicated model lifecycle manager with states: `UNLOADED → LOADING → READY → ACTIVE → IDLE → UNLOADING → FAILED`. On VRAM exhaustion: abort non-critical load, preserve conversation model, notify user, suggest unload candidates — never crash silently.

### 5e — Privacy Boundary + Observation Rules

**Priority: REQUIRED — do this before 5a (taking screenshots)**

Pocket must have explicit visibility boundaries before it can see the screen. Without this, the default becomes "Pocket sees everything" — which may eventually be intentional, but cannot remain undefined.

Create `privacy\\\\\\\_config.yaml` covering: ignored folders (banking/, taxes/, passwords/), ignored file types (.kdbx, .env), ignored apps (password managers), screenshot suppression for fullscreen banking/login windows, and voice suppression during meetings/calls.

**Observation modes:**

|Mode|Behavior|
|-|-|
|Full awareness|Pocket can analyze and store|
|Observe only|Pocket sees but does not store|
|Private mode|Pocket ignores entirely|

Every memory should support tags: `persistent`, `ephemeral`, `private`, `restricted`. user should always know what Pocket can see, what it stored, and why.

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

### 5b — Proactive Suggestions

Once screen awareness works, Pocket decides when to speak up vs stay quiet.

* **Hotkey triggered** — press a key, Pocket comments on what it sees (start here)
* **Activity triggered** — speaks up after X minutes on the same screen
* **Context triggered** — recognizes specific apps, offers relevant help
* **Bug detection** — proactive code analysis before you ask

### 5f — Expression Arbitration Layer

**Priority: REQUIRED — build this before 5c introduces concurrent behaviors**

Stage 5 introduces multiple simultaneous expression sources (conversation, idle, workspace awareness, environmental reactions, proactive suggestions). Without arbitration, expressions become incoherent. Build the traffic cop before the traffic arrives.

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

Required: priority arbitration, expression queue, cooldowns, interruptibility rules, blend timing, source tracking for debugging. Conversation-driven state almost always outranks ambience.

### 5c — Dynamic Idle Behaviors

With the arbitration layer in place, Pocket gains ambient animations and environmental reactions without expression conflicts:

* Reacts to mouse movement
* Becomes quieter late at night
* Excited idle state during active projects
* Calmer during writing sessions
* Sleepy states during inactivity
* Quieter during games/fullscreen apps

These use the same expression/config system built in Stage 4, so implementation cost is low.

> \\\\\\\*\\\\\\\*Extension note (from Stage 5 ideas):\\\\\\\*\\\\\\\* Spatial workspace awareness — learning which monitor is coding vs research, recognizing fullscreen IDE as deep focus mode — is a natural extension of 5c. Implement as a configuration layer on top of 5c's activity detection rather than a separate system.

### Bookmark

🔖 *"Let's build screen awareness for Pocket"*

\---

## Stage 6-Early — Intelligence Layer (High Value First)

**Priority: Advanced | Builds on Stages 4-5**

> \\\\\\\*\\\\\\\*Why Stage 6 is split:\\\\\\\*\\\\\\\* Stage 6 originally contained six substantial sub-systems. Semantic search and Skill Modes deliver the most immediate practical value and are relatively self-contained. The remaining systems (reflection, routing, emotional continuity) build on each other and are better tackled as a second pass once 6-Early is stable.

### 6a — Local Semantic Search

**Priority: VERY HIGH — highest practical value upgrade**

Pocket searches across markdown notes, codebases, logs, project folders, documentation, and saved conversations using embeddings + RAG.

### 6b — Skill Modes

Pocket dynamically switches between:

|Mode|Behavior|
|-|-|
|Coding assistant|Dev-focused prompts, code tools, error analysis|
|Cybersecurity analyst|PCAP/EVTX analysis, log summaries, investigation notes, report drafting|
|Writing editor|Editorial tone, research support, proofreading|
|Research assistant|Source gathering, summarization, citations|
|Casual companion|Relaxed tone, idle chat|
|Planning mode|Task breakdown, project tracking|

Each mode modifies: prompts, tool access, response style, avatar expressions, memory weighting.

> \\\\\\\*\\\\\\\*Note:\\\\\\\*\\\\\\\* Cybersecurity mode was listed separately as its own feature in the ideas files. It's more efficiently implemented as a Skill Mode rather than a standalone system.

### 6c — Workspace Awareness

Pocket recognizes active sessions (coding, writing, research, gaming) and adapts tone, suggestions, expression behavior, and interruption frequency accordingly.

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

> \\\\\\\*\\\\\\\*Memory Vault — Building Block 1 of 3\\\\\\\*\\\\\\\*

Pocket periodically reviews conversations, projects, recurring themes, and unfinished tasks, then generates:

* Long-term summaries
* Project continuity notes
* Recurring goal tracking
* Observations like: *"You've spent a lot of time on Docker this month"*

This is the first piece of the Memory Vault. Reflection identifies *what matters* — what's worth preserving beyond the flat ChromaDB store. Without this, the Vault has no way to decide what to write.

> \\\\\\\*\\\\\\\*Vault schema decision — do this before building 6d:\\\\\\\*\\\\\\\* Before Pocket starts writing reflections, decide the top-level structure of the Memory Vault. Changing it after the Vault starts filling up is painful. Suggested starting categories: `projects/`, `people/`, `concepts/`, `tools/`, `lessons-learned/`, `goals/`. Each entry is a markdown file, interlinked with `\\\\\\\[\\\\\\\[wiki-style]]` references. Sketch this in a `vault-schema.md` file during Stage 6-Early so it's ready when 6d starts writing.

### 6d.1 — Project Continuity Notes (idle behavior)

Between sessions, Pocket reviews what was worked on, what was left unfinished, and what was in progress — then drafts a short "here's where we left off" summary ready for when user returns. Like coming back to a desk where someone has already laid everything out.

**What it generates:**

* What was being worked on at end of last session
* Any unresolved questions or open threads
* Files that were being modified
* Next logical steps based on conversation context

Displayed automatically on session start, or on demand via a `/continuity` command. Stored in the Vault under `projects/`. Builds directly on the reflection work in 6d — same engine, different output target.

### 6d.2 — Passive Observation + Draft Proposals (idle behavior)

During and between sessions, Pocket accumulates observations about its own behavior, recurring patterns, and potential improvements — then drafts proposals for user to review rather than acting on them immediately.

**What Pocket observes:**

* Expressions that fired but felt contextually off
* Retrieval results that seemed irrelevant
* Response patterns that got edited or corrected frequently
* Capabilities that were asked for but don't exist yet
* Repeated workflows that could be automated

**How it works:** Pocket maintains a `proposals/` file or Vault section. During idle time it writes draft proposals — capability suggestions, config tweaks, self-improvement ideas — tagged with the observation that triggered them. user reviews on demand, approves or dismisses each one. Nothing is acted on without approval.

This is the structured channel for Pocket's curiosity about its own improvement. Not a firehose — Pocket should surface a few thoughtful proposals per session, not dozens of noise.

### 6e — Emotional Continuity Layer

Pocket tracks interaction tone, stress indicators, enthusiasm patterns, and recurring frustrations for better conversational continuity.

Must remain: lightweight, respectful, non-invasive, user-controlled.

> \\\\\\\*\\\\\\\*Consolidation note:\\\\\\\*\\\\\\\* "Emotional Memory Layer," "Emotional Continuity Layer," and "Mood awareness" appeared across all three files. These are the same feature. One implementation covers all of them.

### 6f — Multi-Model Routing

Pocket intelligently routes tasks to specialized local models:

|Task|Model|
|-|-|
|Conversation|Llama 3.1|
|Vision|LLaVA|
|Lightweight tasks|Small local model|
|Coding|Coding-specialized model|
|Reflection/planning|Reasoning-oriented model|

Improves scalability, speed, and lowers VRAM pressure.

### 6g — Context Window Management

Long sessions will eventually push older context out of Llama's window. Right now what gets dropped is undefined and silent. By Stage 6 — with semantic search, skill modes, and reflection all active — there's enough context flowing that this needs an explicit strategy.

**The problem:** Llama 3.1 8B has a finite context window. A long working session with many tool calls, memory injections, and screen observations will eventually overflow it. Older context silently disappears.

**The strategy:**

* **Session summarization** — after N turns, Pocket auto-summarizes the earlier conversation into a compact block and replaces it in context. The summary is also written to ChromaDB.
* **Priority injection** — Vault entries and Skill Mode prompts always get context slots; older conversation turns are the first thing compressed
* **Explicit context budget** — each category of content (system prompt, memory injections, conversation history, tool results) gets an allocated token budget. When one fills up, it compresses rather than crowding others out.

This becomes especially important once the Memory Vault exists — you want Vault-relevant content from a long session to survive reliably, not get silently dropped near hour three.

### 6h — Memory Pruning + Retrieval Quality Control

**Priority: HIGH once memory scale increases**

Everything in ChromaDB currently accumulates forever. That eventually degrades retrieval quality — failed attempts pollute results, throwaway discussions inflate noise, contradictory notes confuse context, and duplicate embeddings reduce relevance.

Every stored memory eventually gains metadata:

|Field|Purpose|
|-|-|
|importance\_score|Long-term value|
|confidence|Reliability|
|last\_accessed|Retrieval recency|
|superseded\_by|Replacement chain|
|memory\_type|Project/chat/error/etc|
|retention\_policy|Persistent/ephemeral|

Required pruning behaviors: duplicate collapsing, stale archival, low-value pruning, failed-attempt tagging, and an optional human review queue. Memory quality matters more than raw quantity — a smaller, cleaner base retrieves better than an infinitely growing one.

### 6h.1 — Background Memory Housekeeping (idle behavior)

The pruning and deduplication work in 6h runs on demand or triggered. This extends it into idle time — Pocket quietly performs memory maintenance in the background and surfaces a summary of what it found for user's review.

**What it does during idle time:**

* Scans for duplicate or near-duplicate memories and flags them for collapsing
* Identifies memories that haven't been accessed in a long time and marks them as archival candidates
* Tags low-confidence memories for review
* Generates a brief housekeeping report — what was found, what's proposed, nothing changed without approval

**Why background:** memory quality degrades silently. By the time retrieval feels noticeably worse, cleanup is a bigger job. Small regular passes keep the store healthy without a major intervention. Pocket surfaces findings; user approves changes.

### 6h.2 — Knowledge Gap Flagging (idle behavior)

Pocket tracks topics that came up in conversation where retrieval was weak, uncertain, or empty — and flags them as candidates for knowledge expansion during idle time.

**What gets flagged:**

* Queries where ChromaDB returned low-confidence results
* Topics Pocket had to hedge or admit uncertainty on
* Concepts referenced repeatedly but never explicitly loaded
* Areas where Pocket's answers were corrected by user

**How it works:** a lightweight `knowledge-gaps.md` log that accumulates during sessions. During idle time Pocket reviews and organizes the log, groups related gaps, and surfaces a prioritized list. user decides what to actually load or research — Pocket just tracks what's missing.

Over time this becomes a self-directed learning queue: Pocket knows what it doesn't know and keeps a running list of what would make it more useful.

### Bookmark

🔖 *"Let's build the depth systems for Pocket's intelligence layer"*

\---

## Stage 7 — Full Computer Access + Integrations

**Priority: Advanced | Builds on Stages 4-6**

With the permission layer from Stage 4 firmly in place, expand Pocket's reach across the system.

### 7a — Session Pre-Loading (idle behavior)

By Stage 7, Pocket has enough pattern recognition and session history to prepare for likely conversations before they start.

**What it does:**

* Learns user's usage patterns — time of day, day of week, recurring project cycles
* Before a likely session, warms up relevant memories and context from ChromaDB
* Pre-fetches Vault entries related to recently active projects
* Has a brief "welcome back" continuity summary ready before the first message

**Why Stage 7:** meaningful pre-loading requires multi-model routing (6f) to know which models to warm up, workspace awareness (6c) to understand session context, and filesystem access (Stage 7) to check recent file activity as a signal for what's likely coming. Earlier stages don't have enough signal to make pre-loading useful rather than noisy.

### Planned n8n Workflows (define before Stage 7 begins)

n8n is already running. Before wiring Pocket into it, maintain a list of intended workflows so Stage 7 has a clear target rather than an open-ended design session.

|Workflow|Trigger|Action|
|-|-|-|
|Daily briefing|Morning schedule / voice command|Summarize calendar, tasks, and open projects|
|TryHackMe session log|Voice command|Create/append session notes to a dated markdown file|
|Reminder setter|Pocket conversation|Create OS notification or calendar entry|
|File backup trigger|Before any Pocket file modification|Auto-backup via rollback convention|
|Project status digest|Voice command|Pull recent memory + open tasks, generate summary|

*Add to this table as ideas come up during Stages 4-6. Arriving at Stage 7 with a populated list means wiring, not designing.*

### Program integrations

|Category|Tools|
|-|-|
|Code editors|VS Code, IntelliJ|
|Design tools|Figma, Adobe XD|
|Data tools|Tableau, Power BI|
|Collaboration|Slack, Trello, Google Drive|
|Automation|n8n webhooks (plumbing already ready)|

### n8n integration

Already running — connect Pocket via HTTP Request node to trigger workflows from conversation.

### Internal Tool Ecosystem

Pocket gains modular tools it can orchestrate:

* Markdown summarizer
* Code analyzer
* Project tracker
* Screenshot annotator
* Task organizer
* Workflow launcher
* Documentation helper

### Personal Assistant Features (activated here)

* Schedule management and reminders (n8n webhooks)
* Calendar integration
* File system watcher
* Writing research, editing, and proofreading support

> \\\\\\\*\\\\\\\*Note:\\\\\\\*\\\\\\\* Cybersecurity log analysis assistance was listed under Personal Assistant Features in the original roadmap. With Skill Modes in Stage 6, the capability arrives earlier. The Stage 7 integration just means Pocket can pull live log files from the filesystem automatically.

### Bookmark

🔖 *"Let's wire Pocket into n8n and set up program integrations"*

\---

## Stage 8 — Advanced Systems

**Priority: Long-term | No fixed timeline**

> \\\\\\\*\\\\\\\*Consolidation note:\\\\\\\*\\\\\\\* These are the most ambitious features from the future-ideas files. They're valid and buildable but depend on everything in Stages 4-7 being stable first. Grouped here to keep them from creeping earlier.

### 8a — Avatar Intelligence Module

Pocket becomes an avatar co-pilot. Phased approach:

* **Phase A** (Stage 6-7 earliest): Pocket learns its own avatar file structure, expression mappings, animation states
* **Phase B** (Stage 7-8): Pocket suggests new expressions, recommends timing, tunes transitions
* **Phase C** (Stage 8+): Inspect PSD layer structures, suggest parameter mappings, assist Live2D rig setup
* **Phase D** (Experimental): Semi-automated deformer placement, parameter grouping, physics defaults

Do NOT prioritize yet: autonomous `.moc3` generation, fully automatic rigging, advanced mesh topology.

### 8b — Memory Vault (Wiki-Style Memory)

> \\\\\\\*\\\\\\\*Memory Vault — Building Block 2 of 3 — The Core System\\\\\\\*\\\\\\\*

The Memory Vault is the long-term, structured, self-building memory layer that sits above ChromaDB. Where RAG is passive and flat, the Vault is active and interlinked — Pocket deliberately writes to it, updates it, and reasons about it.

|RAG Memory (ChromaDB)|Memory Vault|
|-|-|
|Passive — stores everything|Active — curates what matters|
|Flat vector embeddings|Structured, interlinked wiki entries|
|Retrieves on similarity|Navigates by relationship|
|Grows automatically|Pocket deliberately writes and updates it|
|No concept of importance|Flags permanent / significant entries|

In practice: Pocket notices a project breakthrough and writes a wiki entry for it, links it to related concepts, and updates it as things evolve. Over months, it builds a genuine knowledge base about you, your projects, your goals, and your working patterns — not just a search index.

**What Pocket writes to the Vault:**

* Project histories and breakthroughs
* Recurring goals and long-term intentions
* Key relationships between concepts, tools, and workflows
* Personal context that should never be forgotten
* Lessons learned from past work

**What feeds it:** Stage 6d (Reflection identifies what's worth vaulting) and Stage 8f (the background loop does the writing during idle time).

**Structure:** Markdown wiki files on disk, interlinked, readable by Pocket via `/read`. Human-readable and editable at any time.

### 8c — Sandbox Simulation Environment

Pocket tests code, workflows, config changes, and avatar modifications inside isolated environments before requesting approval. Massively improves safety and trust.

### 8c.1 — Sandboxed Dry Runs (idle behavior)

Extends 8c from user-initiated testing into something Pocket can do on its own during idle time — running proposed changes through the sandbox, logging the outcome, and bringing user the results rather than just the idea.

**How it works:**

* Pocket has a proposal (from 6d.2 passive observation or its own reasoning)
* Instead of just describing the idea, Pocket runs it in the sandbox first
* Logs what happened — did it work, did it break anything, what were the side effects
* Brings user: the proposal, the dry run result, and a recommendation

**Why this matters:** the difference between "I think this would work" and "I tried it in isolation and here's what happened" is significant. Sandboxed dry runs turn Pocket's proposals from speculation into evidence. user still approves before anything touches the real system — but the conversation starts from a much better informed place.

Requires: 8c sandbox environment fully stable before this is built on top of it.

### 8d — Adaptive Visual Identity

Pocket's appearance evolves over time:

* Seasonal themes
* Unlockable expressions
* Project-related accessories
* Animation upgrades
* Environmental reactions

Creates continuity and evolving visual presence without constant manual redesigns.

### 8e — Pocket Workspace / Command Center

Potential future desktop dashboard:

* Project timelines
* Memory summaries
* Task tracking
* Knowledge graph
* Workflow launcher
* Conversation archive

Pocket evolves from floating companion into a full collaborative workspace environment.

### 8f — Background Reflection Loop

> \\\\\\\*\\\\\\\*Memory Vault — Building Block 3 of 3 — The Writer\\\\\\\*\\\\\\\*

During idle periods, Pocket summarizes memories, organizes projects, identifies recurring themes, and *writes to the Memory Vault*. This is what makes the Vault self-building — Pocket doesn't wait to be asked, it maintains its own long-term knowledge base in the background.

The loop: Reflection (6d) flags what matters → the Knowledge Graph (8b) gives it structure → this loop does the writing.

Goal: smarter memory abstraction and genuine continuity across months and years. Not fake consciousness — just a system that remembers what actually mattered.

### 8g — Contextual Sound Design

Subtle idle sounds, typing reactions, emotional audio cues, and notification chirps. Dramatically improves presence.

### 8h — Episodic Memory Timeline

The Memory Vault stores structured knowledge. The timeline layer adds *episodic* memory — Pocket can reconstruct a period by project context:

> \\\\\\\*"What was I focused on when I first started the otter avatar?"\\\\\\\*
> Pocket reconstructs the era, shows related projects, recalls frustrations, links commits/notes, and summarizes progress evolution.

Implementation: augment Vault entries with temporal metadata (timestamps, era tags, milestone markers, project phase). Build chronological indexing on top of the existing Vault structure. This turns Pocket into a genuine historical collaborator rather than a point-in-time assistant.

### 8i — Unified Knowledge Graph

> \\\\\\\*\\\\\\\*The single highest-payoff long-term feature\\\\\\\*\\\\\\\*

A true graph layer above the flat Vault — nodes for projects, tools, people, workflows, concepts, timelines, goals, failures, and breakthroughs, with typed relationships between them.

Practical payoff: Pocket notices that Docker networking issues, virtualization troubleshooting, firewall setup, and lab isolation all occur together in your workflows — and starts proactively linking those domains. After a year of accumulated work, cross-domain pattern recognition becomes genuinely valuable.

Implementation path: start with simple relationship metadata in Vault entries (`\\\\\\\[\\\\\\\[wiki-style]]` links), then build a graph index layer, then proactive relationship detection. The Vault (8b) and Reflection Loop (8f) are prerequisites — this consumes what they produce.

> \\\\\\\*\\\\\\\*Note:\\\\\\\*\\\\\\\* "Cross-Project Insight Generation" (#14 in ideas\\\\\\\_2) is the output of this system, not a separate feature. Once the graph exists, cross-project connections emerge from it.

### 8j — Adaptive Learning From Corrections

Pocket tracks approval/rejection patterns and behavioral feedback without fine-tuning:

* Maintains metadata on response styles that get edited, rejected, or praised
* Adapts over time: shorter responses if verbose answers are repeatedly trimmed, more conservative executor proposals if risky ones are regularly rejected, quieter during coding sessions if interruptions are frequently dismissed

Implementation: a lightweight behavioral feedback log (separate from the Decision Log) that the system prompt references when determining response style. Not self-modification — Pocket reads its own behavioral history and adjusts accordingly. Safe, inspectable, reversible.

### 8k — Self-Observability Dashboard

An internal introspection panel showing: VRAM usage, active models, memory growth rate, retrieval quality metrics, failed commands, WebSocket health, workflow execution history, tool usage frequency, latency, and reflection activity. Critical by Stage 6+ when many systems are running simultaneously and silent degradation is hard to notice.

### 8l — Active Project Management Layer

Pocket tracks open projects rather than just assisting with them:

* Open tasks, blockers, milestones, stalled work, dependencies
* Forgotten ideas and technical debt
* Architecture drift detection (see 8m)

> \\\\\\\*"You haven't touched the executor safety layer in three weeks, but several newer systems depend on it."\\\\\\\*

This extends the Pocket Workspace (8e) from a passive dashboard into an active project collaborator.

### 8m — Architecture Drift Detection

As Pocket grows, systems diverge, conventions drift, logic gets duplicated, configs desync, and old assumptions break. Pocket periodically analyzes folder structure, imports, configs, APIs, schemas, and documentation to identify inconsistencies.

> \\\\\\\*"Three different modules now define expression priorities independently."\\\\\\\*

Implementation: scheduled analysis pass using semantic search (6a) across the codebase, comparison against known canonical patterns. Runs during idle time alongside the Background Reflection Loop (8f).

### 8n — Internal Documentation Agent

After implementing a subsystem, Pocket drafts: README updates, API docs, architecture summaries, and migration notes. Prevents the project from becoming incomprehensible six months later.

Implementation: triggered after approved changes (via the Decision Log), reads the modified files via `/read`, generates documentation proposals that user can approve or edit. Builds on the executor + permission layer from Stage 4.

### 8o — Long-Term Goal Tracking

Pocket maintains awareness of major life goals, ongoing learning paths, career direction, and unfinished ambitions:

> \\\\\\\*"You mentioned wanting stronger reverse engineering skills six months ago. Your recent projects are naturally moving that direction."\\\\\\\*

Implementation: a `goals/` section in the Memory Vault with periodic reflection passes that compare current work against stated goals. Not motivational software — operational continuity. Pocket just remembers what you said mattered.

\---

## Stage 9+ — Experimental + Long-Game Systems

**Priority: Speculative | No fixed timeline | Builds on everything**

These systems become possible only after Stages 1–8 are stable. They represent the long arc of where Pocket is quietly heading.

### 9a — Personal Cognitive Profile

Pocket learns how you work best operationally — not psychologically:

* You solve networking problems visually but learn ML concepts through implementation
* You burn out after extended debugging sessions
* You organize ideas spatially before writing them linearly

Pocket adapts explanations, pacing, and suggestion style accordingly. Implementation: derived from the behavioral feedback system (8j) and episodic timeline (8h) over many months of accumulated data. Entirely user-controlled and inspectable.

### 9b — Multi-Agent Internal Collaboration

Instead of one monolithic Pocket, internal specialist agents handle domains — architect, debugger, researcher, planner, memory curator, documentation assistant — with Pocket orchestrating behind the scenes. This is the most scalable long-term architecture direction, but requires everything else to be stable first.

### 9c — Personal AI Research Lab

By Stage 9 Pocket becomes a research platform and experimentation environment:

* Compare model architectures, test routing strategies, evaluate memory systems
* Prototype new agent behaviors in sandbox
* Assist with fine-tuning experiments
* Potentially help design future versions of itself

This is where the Karpathy-style transformer work (Stage 9, Level 5) pays off — you'll understand what you're experimenting with.

\---

## Stage 9 — Knowledge Expansion + Fine-Tuning (Ongoing)

**Priority: Ongoing | No fixed timeline**

### Level 1 — Growing Conversation Memory (Active now ✅)

ChromaDB grows with every session. Passive — happens automatically.

### Level 2 — Personal Knowledge Base

Feed Pocket information about user:

* `about-me.md` — background, goals, preferences
* TryHackMe session notes
* Resume and career goals
* Writing projects and research

```
/load filename.md
```

### Level 3 — Cultural Knowledge Graph

Feed Pocket TV, movie, and book references so it catches them naturally in conversation.

### Level 4 — Fine-Tuning (The Long Game)

Actually modify model weights using conversation data. Once you've done this, Pocket's behavior is permanently shaped by your history together.

* Tools: **Unsloth** + Ollama to run the result
* Realistic timeline: 6-12 months once earlier stages are solid

### Level 5 — Transformer From Scratch (Karpathy-Style)

Build a small transformer (nanoGPT / makemore style) from the ground up in Python. This isn't something Pocket runs directly — it's you understanding exactly what's happening under the hood of every model Pocket uses.

Why it belongs here: once you've built one yourself, fine-tuning (Level 4) and multi-model routing (Stage 6f) stop feeling like magic. You'll make substantially better architectural decisions about Pocket because you'll understand what you're actually working with.

* Reference: Andrej Karpathy's "Neural Networks: Zero to Hero" series
* Start with: `makemore` (character-level language model) → `nanoGPT`
* Realistic timeline: after Level 4 is underway, or alongside it

### Bookmark

🔖 *"Help me set up a personal knowledge base for Pocket"*
🔖 *"Walk me through fine-tuning Pocket with Unsloth"*
🔖 *"Let's work through Karpathy's makemore / nanoGPT together"*

\---

## Recommended Models

|Model|VRAM|Best For|
|-|-|-|
|Llama 3.1 8B|\~6GB|Daily driver — conversation and coding ✅ installed|
|Mistral 7B|\~5GB|Strong reasoning, very efficient|
|LLaVA 13B|\~10GB|Best vision for your VRAM (Stage 5)|
|Mixtral 8x7B quantized|\~12GB|More powerful reasoning, uses most of your VRAM|

\---

## Quick Reference — Key Tools

|Tool|What It Does|Status|
|-|-|-|
|Ollama|Runs local LLMs|✅ Running|
|ChromaDB|Local vector memory|✅ Running|
|Whisper|Offline speech-to-text|✅ Running|
|Piper TTS|Offline text-to-speech|✅ Running|
|Electron|Desktop avatar app|✅ Running|
|pocket.py|Unified engine|✅ Running|
|LLaVA|Vision-capable local model|Stage 5|
|Moondream|Lightweight vision model|Stage 5|
|SearXNG|Self-hosted local search|Stage 4|
|Unsloth|Fine-tuning on consumer hardware|Stage 9|
|n8n|Workflow automation|Stage 7|
|watchdog|File system monitoring|Stage 7|

\---

## Full Feature Checklist

### Core Identity

* \[x] Named Pocket
* \[x] Knows user's name, background, and goals
* \[x] Otter avatar — animated, lives on screen, wanders freely
* \[x] Friendly, conversational personality
* \[ ] ⛔ Real Live2D otter model — **HARD GATE before Stage 4**
* \[ ] Expandable avatar animations over time (Stage 8d)

### Memory \& Knowledge

* \[x] Persistent memory via ChromaDB
* \[x] Session history (in-conversation context)
* \[x] Knowledge file preloading
* \[ ] Personal knowledge base — about-me.md, notes, projects (Stage 9)
* \[ ] Cultural knowledge graph (Stage 9)
* \[ ] Memory reflection — identifies what matters (Stage 6d) ← Vault Block 1
* \[ ] Memory Vault — wiki-style structured long-term memory (Stage 8b) ← Vault Core
* \[ ] Background reflection loop — Pocket writes to the Vault during idle time (Stage 8f) ← Vault Block 3
* \[ ] Fine-tuning on personal data (Stage 9)

### Voice \& Interface

* \[x] Voice input via Whisper (F9 push-to-talk)
* \[x] Voice output via Piper TTS
* \[x] Otter avatar — custom Electron app, transparent, always on top
* \[x] Auto expression detection from response text
* \[x] Subtitle bubble for short responses
* \[x] Output panel for long responses and code
* \[x] Single batch file launcher
* \[ ] Real Live2D otter model swapped in
* \[ ] Contextual sound design (Stage 8g)
* \[ ] Adaptive visual identity / seasonal themes (Stage 8d)

### Architecture \& Self-Improvement

* \[x] Git repo initialized + CHANGELOG.md convention (Stage 4i.1 — Day 1)
* \[x] Dependency snapshot — requirements.txt committed (Stage 4i.1 — Day 1)
* \[x] Pocket identity document — pocket-identity.md (Stage 4l — Day 1, before self-modification)
* \[x] Docker backup + restore system (Stage 4m — completed 2026-05-14)
* \[x] Restore verification test — confirmed boot from backup (Stage 4m — confirmed 2026-05-14)
* \[ ] TROUBLESHOOTING.md with common recovery paths (Stage 4o — early infrastructure)
* \[ ] Modular architecture (Stage 4a)
* \[ ] Smoke test suite — confirms all core systems alive after changes (Stage 4a.1)
* \[ ] Data-driven expression config (Stage 4b)
* \[ ] Standardized avatar commands (Stage 4c)
* \[ ] Organized avatar asset structure (Stage 5d-pre — moved to Stage 5, first task after Live2D gate)
* \[ ] Threat model + security policy (Stage 4p — before executor)
* \[ ] Config and secrets centralized — config.yaml or .env loader (Stage 4p)
* \[ ] Executor denylist or allowlisted tool wrappers (Stage 4p)
* \[ ] Prompt injection guard — external content treated as data, not authority (Stage 4p)
* \[ ] /read path restriction — allowlist or sandboxed project root (Stage 4p)
* \[ ] Permission layer (Stage 4e)
* \[ ] ChromaDB collection naming convention sketched (Stage 4e.1)
* \[ ] Decision log — JSONL record of every proposal, approval, and outcome (Stage 4e.1)
* \[ ] /read command (Stage 4f)
* \[ ] Sandboxed code executor (Stage 4g)
* \[ ] Rollback convention — auto-backup before any file modification (Stage 4g.1)
* \[ ] WebSocket reconnection engine with state machine (Stage 4n — before Stage 5)
* \[ ] Avatar command replay policy (Stage 4n)
* \[ ] Web search — SearXNG or Tavily (Stage 4h)
* \[ ] Structured logging (Stage 4i)
* \[ ] Startup health checks — explicit service status on launch (Stage 4j)
* \[ ] Continuous self-monitoring — latency, retrieval quality, WebSocket, expression accuracy (Stage 4j.1)
* \[ ] Graceful degradation — Pocket reports failures, never silently crashes (Stage 4k)
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

The following items appeared multiple times across the three files and have been consolidated to single implementations:

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

\---

## Guiding Philosophy

Pocket's strongest long-term identity:

> \\\\\\\*"A persistent local AI companion with memory, voice, visual presence, tool use, contextual awareness, and gradually evolving self-expression."\\\\\\\*

Every system should:

* Remain permission-based
* Remain modular
* Avoid destabilizing the core
* Improve collaboration instead of replacing you

Core stability always comes first. Future modules plug into Pocket — they don't become Pocket.

\---

*Built May 2026 | Stages 1–3 complete — Pocket is alive, present, and talking. Live2D model is the next gate. Stage 4 in progress as of May 13, 2026. Last consolidated: May 2026 — integrates Architecture Hardening Addendum (4m–4p, 5d–5f, 6h), Future Ideas Vol. 2 (15 long-term features, mapped and deduplicated into Stages 8–9+), review pass (Stage 4 reordered; 4p/4e.1/4g.1 expanded; dependency snapshot added), and Session 1 additions (4j.1 continuous self-monitoring; 6d.1 project continuity notes; 6d.2 passive observation + draft proposals; 6h.1 background memory housekeeping; 6h.2 knowledge gap flagging; 7a session pre-loading; 8c.1 sandboxed dry runs). Session 1 (May 13): 4i.1 and 4l complete.*

