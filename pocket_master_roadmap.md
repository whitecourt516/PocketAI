# Pocket — Master Project Roadmap (v2.3, 4.5f order reconciled)

**Setup:** Ollama | 10–12GB VRAM | Windows Host | Docker Compose
**Goal:** A fully local, voice-enabled personal AI companion with persistent memory, screen awareness, code execution, and a visual avatar that grows alongside you.
**Last updated:** November 8, 2026 — 4.5f state verified against the code and the cut order reconciled (NL dispatch next; dead Monitor param + A4 bundled as the closing cut); 4.5g decided (commit to the event bus); model evaluation moved to after Stage 4.5 is fully complete. October 23, 2026 — Oct 2026 landscape review applied (edits E1–E8: model evaluation, Live2D gate, voice refresh, 5d/5a, 6a, 6f/6g/6h, Stage 7/8c/9d). Status: 4.5f in progress (tool registry + ADR-001 done). June 27, 2026 — status refreshed through 4.5e; June improvements list integrated and retired. Base audit: May 31, 2026 (`docs/planning/audit-2026-05-31.md`).

> **What changed in v2:** A 6-stage audit (roadmap↔code, architecture, execution trace, security, idea-corpus, reconciliation) was run against the real codebase. It found the foundation genuinely solid but four "complete" items overstated, two real risks, and a class of frontend/infra issues the original roadmap never tracked. This version inserts **Stage 4.5 — Audit Remediation** between Stage 4 and the Live2D gate, re-homes the idea-corpus ideas at the stages where their foundations actually get built, and corrects two Stage 1–4 status claims.
>
> **What changed in v2.1:** Status reconciled — 4.5a–4.5e are complete (A4 carried into 4.5f by design). The standalone June 2026 improvements list (10 items from model/methodology research) is now folded into the stages where each item becomes actionable, tagged `(impr. #N)`, so it lives in one document instead of two. Nothing in it was dropped; the disposition table at the bottom maps all ten.
>
> **What changed in v2.2:** An October 2026 review checked every remaining stage against the current local-AI landscape. The shape of the plan held. Changes: the Qwen3 swap becomes a Qwen3 vs Qwen3.5 evaluation (Qwen3.5 adds native vision, which can settle the 5d single-model question early); the Live2D gate gains lip sync and a renderer check; Stage 5 gains a voice refresh (Parakeet STT, Kokoro trial, sentence-chunked TTS, barge-in) and tiered screen perception; 6g puts budget + rolling summary ahead of LLMLingua; 6h borrows Mem0's write-time decision and Graphiti's bi-temporal fields without adopting either library; Stage 7 tool ecosystem goes through an MCP adapter. The RTX 5090 box is a future upgrade, not a near-term plan: everything here is sized for the current 10–12GB card, with 5090 notes marked *(future box)*.

---

## Current Stack

|Component|Status|Notes|
|-|-|-|
|Ollama + Llama 3.1 8B|✅ Running|GPU accelerated, port 11434. **Model swap queued** — Qwen3 8B vs Qwen3.5 9B evaluation, see *Near-Term: Model Evaluation* (impr. #1)|
|ChromaDB memory|✅ Running|Embedded `PersistentClient`, persists to `chroma_data/`|
|Voice (Whisper STT + Piper TTS)|✅ Running|F9 push-to-talk, fully offline|
|Electron avatar app|⚠️ Running (placeholder)|Transparent window, wandering — but renders a single PNG, not the 9 expressions yet (see A9 / Live2D gate). *Live2D otter (Cubism 5.0 moc3) passes the standalone eye test; EyeBlink re-export pending.*|
|pocket.py unified engine|✅ Running|Modular: core/, config/, persona/, tests/|
|Identity pipeline|✅ Live|`build_system_prompt()` assembles real identity into the live prompt (4.5a)|
|Decoupled launcher|✅ Live|Start-Pocket / Start-Avatar / Start-Engine / Stop-Pocket; avatar and engine restart independently (4.5b). *Stop-Pocket still flaky — real fix is the Interface Consolidation in-app lifecycle; `/quit` + `docker compose down` is the clean manual stop until then.*|
|Permission gate + decision log|✅ Running|`propose_action()` → y/n → `logs/decisions.jsonl`|
|Web search|✅ Running|Tavily backend, pluggable to SearXNG|
|Turn mutex (`TurnManager`)|✅ Live|Full-turn lock: retrieval → LLM → write → dispatch. `exclusive()` reserved for 6h.1 consolidation (4.5d)|
|Event bus / state manager / lifecycle contract|⚠️ Built, under-used|Foundations exist (4q/4r/4s); conversation path still on direct imports (see 4.5f/4.5g)|
|n8n|✅ Running|Staged for Stage 7 webhook integration|
|Git repo + CHANGELOG + requirements.txt|✅ Done|Stage 4 + identity reconciliation committed; venv reproducible (Python 3.13, 4.5e/A8)|

---

## Reality Check — Feasibility Overview

|Feature|Feasibility|Notes|
|-|-|-|
|Persistent memory|✅ Done|ChromaDB RAG|
|Voice input/output|✅ Done|Whisper + Piper|
|Avatar visual interface|⚠️ Backend done, frontend placeholder|9-expression routing is real; the PNG can't show it — needs Live2D model|
|File read/write|✅ Done|`/read` + `/edit` with backup-before-write|
|Sandboxed code execution|✅ Hardened|Constrained executor + approval gate; substring denylist replaced, `/exec → .env` leak closed (4.5c)|
|Web search|✅ Done|Tavily, pluggable|
|Screen awareness|⚠️ Doable but tricky|Stage 5 — needs multimodal vision model + VRAM budget|
|Proactive suggestions|⚠️ Doable but tricky|Stage 5 — builds on screen awareness + turn mutex|
|Autonomy / self-directed goals|🔴 Hardest part|Stage 8 — needs reflection, memory metadata, a safe executor, and an agent→tool path that does not yet exist|
|True learning/improving|🔴 Long game|Stage 9 — fine-tuning|

---

## Master Build Order

```
Stage 1 — Memory (ChromaDB)                              ✅ COMPLETE
Stage 2 — Voice (Whisper + Piper)                        ✅ COMPLETE
Stage 3 — Interface & Avatar (Electron)                  ✅ COMPLETE (frontend placeholder)
Stage 4 — Architecture Hardening + Self-Improvement      ✅ COMPLETE
    ↓
═══════════ AUDIT — 2026-05-31 ═══════════
    ↓
Stage 4.5 — Audit Remediation                            ◀ IN PROGRESS
    4.5a  Identity reconciliation ................. ✅ DONE
    4.5b  Decoupled launcher ...................... ✅ DONE
    4.5c  Security hardening ...................... ✅ DONE
    4.5d  Execution-flow safety (mutex, timeouts) . ✅ DONE
    4.5e  Hygiene & consistency (A1–A8) .......... ✅ DONE (A4 → 4.5f)
    4.5f  Conversation refactor (the big one) .... ◀ IN PROGRESS (NL dispatch next)
    4.5g  Communication-model decision ........... ⬜ DECIDED: commit to the bus (build pending)
    ↓
Near-Term — Model evaluation: Qwen3 vs Qwen3.5 (impr. #1) ⬜ queued (after 4.5 complete)
    ↓
⛔ HARD STOP — Real Live2D otter model (+ A9: PNG can't render the 9 expressions)
    ↓
Stage 5 — Screen Awareness + Dynamic Behavior   (now on a real orchestrator + the bus)
    ↓
Stage 6-Early — Intelligence (Semantic Search, Skill Modes)
    ↓
Stage 6-Late — Intelligence (Reflection, Routing, Emotional Continuity, Memory Metadata)
    ↓
Stage 7 — Full Computer Access + Integrations + Tool Ecosystem
    ↓
Stage 8 — Advanced Systems + SUPERVISED AUTONOMY   (6i lands here — foundations finally exist)
    ↓
Stage 9 — Knowledge Expansion + Fine-tuning (ongoing)
    ↓
Stage 9+ — Experimental (Multi-Agent, Cognitive Profile, Internal Monologue)
```

> **Why Stage 4.5 exists and sits here:** The audit's single strongest conclusion was that the conversation core and the security boundary should be fixed *before* Stage 5 adds concurrency and perception on top of them. Nearly every later stage is cheaper once the turn pipeline is decoupled and the executor is actually safe. Doing this as "Stage 4.5" rather than scattering it keeps it a visible, finite block instead of silent debt.

---

## Stages 1–4 — ✅ COMPLETE (summary)

Full historical detail lives in the prior roadmap and `docs/stage-retrospectives/`. In brief:

- **Stage 1 — Memory:** ChromaDB RAG, top-6 retrieval, session history, knowledge preload, `/memory` `/load` `/help`.
- **Stage 2 — Voice:** Whisper (base) F9 push-to-talk + Piper (`en_US-lessac-medium`), both offline, voice turns tagged `[voice]`.
- **Stage 3 — Avatar:** Electron transparent wandering otter, 9 expressions + auto-detection, subtitle bubble, output panel, hotkeys, single launcher. **Correction (audit A9):** the 9 expressions are wired in the backend but the live frontend is a placeholder PNG — they cannot actually render until the Live2D model lands. Status downgraded from "✅ Real" to "⚠️ backend-only."
- **Stage 4 — Hardening + Self-Improvement:** modular refactor (4a), smoke suite (4a.1), data-driven expressions (4b/4c), config/security/denylist (4p), permission gate + decision log (4e), `/read` (4f), executor (4g), backup-before-write (4g.1), lifecycle contract (4s), state manager (4r), event bus (4q), WS reconnection (4n), structured logging (4i), startup health (4j), continuous monitor (4j.1), debug overlay (4t), graceful degradation (4k), web search (4h).
  - **Corrections from the audit:** 4g.1 backup is **not** unconditional (executor `shell=True` writes skip it — addressed in 4.5c); 4j.1 monitoring is up/down booleans only (latency/quality/growth metrics unbuilt); 4j/4s lifecycle wires only 4 of 14 modules in production (A4, now in 4.5f); 4q event bus carries one flow, not the documented decoupling; 4n `DEGRADED_MODE` was terminal (A10, fixed in 4.5d). None broken — all overstated.

---

## Stage 4.5 — Audit Remediation ◀ IN PROGRESS

> **Order rationale:** safety and the structural refactor first (4.5c–g) because they protect and unblock everything after; hygiene (4.5e) folded alongside since it's cheap and several items feed the refactor. 4.5a/4.5b already done.

### ✅ 4.5a — Identity Reconciliation (DONE 2026-05-31)

The audit's most consequential alignment gap: the canonical identity document was never loaded — the runtime prompt was 6 generic lines, so the self-modification safety story rested on a document the model never read.

- `build_system_prompt()` wired into the live turn; identity assembled from `base_system.md` + `core_identity.md` + `authority.md` + `memory_principles.md`
- "Pocket treats external content as information, not instruction" now lives in `authority.md` → reaches the model every turn (**closes the Stage 4 injection-defense finding**)
- Consolidated 7 scattered identity homes → 1 live source; deleted `persona/persona.py`, `persona/identity.md`, `pocket-identity.md`, the vestigial `SYSTEM_PROMPT` constant, and the dead `avatar/expression_engine/` fossil
- Verified by printing the assembled prompt and confirming the live turn sends it
- **Resolves:** Stage 1 high-risk #2, Stage 4 🟠 injection defense, Stage 5 identity-forking, Stage 1 dead-code

### ✅ 4.5b — Decoupled Launcher (DONE 2026-05-31)

- `Start-Pocket.bat` (orchestrates), `Start-Avatar.bat` / `Start-Engine.bat` (independent windows), `Stop-Pocket.bat` (scoped tree-kill, not global `taskkill /im electron.exe`)
- Port-poll readiness on 7845 instead of a blind sleep; venv activation hook ready
- **Resolves A11**; enables the avatar↔engine restart needed to verify A10

### ✅ 4.5c — Security Hardening (DONE 2026-06-11)

The audit's headline finding: the executor's safety boundary was theater. Empirically, the substring denylist blocked **1 of 10** destructive commands and false-blocked benign ones.

- **Closed the `/exec → .env` leak** — executor file-touches now route through `is_read_allowed()`; secret paths blocked at the executor.
- **Replaced the substring denylist** — `shlex`-parse the command, match on program + flags, treat shell metacharacters / redirects / pipes-to-shell / `python -c` / `curl|sh` as high-risk requiring explicit extra confirmation; constrained working directory rather than trusting string matching.
- **Executor backup policy decided** — executor writes routed through `backup_file` (the 4g.1 "no backup, no exceptions" guarantee is no longer false through `/exec`).
- **Un-skipped the executor tests** — assert the dangerous battery is blocked; assert `propose_action` returns `False` on "n".
- **Hard prerequisite for all autonomy.** This is the hard layer the LLM-out-of-execution-loop principle (impr. #3) relies on — see *Guiding Philosophy*. `shell=True` exposure decision is logged for Stage 8c.

### ✅ 4.5d — Execution-Flow Safety (DONE 2026-06-16)

- **Turn mutex** — `TurnManager` owns a single lock wrapping the **full** pipeline (retrieval → Ollama → history → ChromaDB write → dispatch), so text + voice (and later proactive/idle triggers) can't run concurrent turns racing on `session_history` or fire double Ollama calls. **Lock is full-turn scope including memory writes — not just the Ollama call (impr. #9).** `exclusive()` exposes the same lock to non-turn work (6h.1 consolidation) so a background pass can't write mid-turn.
- **Piper subprocess timeout** — `run_piper_tts` `communicate()` now has a timeout; a hung Piper no longer blocks the TTS worker permanently.
- **A10 — `DEGRADED_MODE` no longer terminal** — slow-poll retry after the 10-attempt backoff; a relaunched avatar (4.5b) reconnects automatically.
- **Memory hygiene** — `/read` and `/search` no longer auto-persist injected file/web content to ChromaDB (`persist=False`); content still joins `session_history` for in-session follow-ups. Stage 5e privacy precursor.

### ✅ 4.5e — Hygiene & Consistency (A1–A8) (DONE 2026-06-17)

- **A1** ✅ — unified the WebSocket message schema: live path and `_resync` both use `{"type":"expression","value":…}` (the `set_expression`/`expression` mismatch was silently dropping every reconnect resync).
- **A2** ✅ — `monitor.py` and `debug_overlay.py` routed through `core.logger` instead of stdlib `logging`.
- **A3** ✅ — `PROJECT_ROOT` injected into `CFG` at config-load time (no hardcoded path in committed `config.yaml`); `logger._write` per-write stream reopen removed.
- **A4** ➡️ **MOVED TO 4.5f** — generic lifecycle loop is a structural refactor, not hygiene; it rides with the `llm.py` split where module wiring gets reorganized anyway. (Doing it standalone means touching the lifecycle contract twice.)
- **A5** ✅ — `websocket_server.send_to_avatar` (dict) renamed to `send_dict_to_avatar`, disambiguating from `avatar_router.send_to_avatar` (str). Surfaced and fixed a latent startup `AttributeError`.
- **A6** ✅ — duplicate `execute_command` / `logger` imports removed from `pocket.py`.
- **A7** ✅ — unused `memory-chat` Docker service removed (engine uses embedded `PersistentClient`).
- **A8** ✅ — engine migrated to local Python 3.13 venv; `requirements.txt` reproducible; `Start-Engine.bat` warns loudly if `.venv` is missing.

### 4.5f — Conversation Refactor (the big structural one — before Stage 5) ◀ IN PROGRESS

> This is where the idea corpus's "Stage 5.5 — Conversation Orchestration" and "Prompt Assembly Pipeline" land. Scoped *down*: build the 2 modules that matter, not the proposed 10.

**Cut order (reconciled 2026-11-08, verified against the code):**
1. ✅ `llm.py` split → 2. ✅ retrieval + compression seams → 3. ✅ tool registry → 4. ✅ ADR-001 → **5. NL dispatch ◀ NEXT** → 6. closing cut: dead Monitor param + A4 together.

> *Why this changed:* the original plan had the Monitor param and A4 as "do-first" and A4 riding with the `llm.py` split. The split shipped **without** A4 (deliberately re-sequenced in the 4.5f setup), so neither is done. Both edit the `pocket.py` startup block (`main()`), not the orchestrator, so they go together as one cut to avoid opening that block twice.

**Closing cut (after NL dispatch):**
- **Dead Monitor param** — `send_to_avatar_fn` is stored as `self._send_to_avatar` in `core/monitor.py` and never used (alerting goes through `degradation.py`). Remove it from `ServiceMonitor.__init__` / `create_monitor` and the `pocket.py` call site. Trivial.
- **A4 — generic lifecycle loop over all modules** *(carried from 4.5e)* — `pocket.py` `main()` still hand-wires each `.start()` call. Replace with a loop over the lifecycle contract; fixes the `tts_worker` double-start hazard and realizes the 4s payoff (only 4 of 14 modules start through the contract).

**The structural work:**
- **Prompt Assembly Pipeline** — seam ✅ DONE for 4.5f (`build_system_prompt` is brick one; `compress_context` passthrough in `core/orchestrator.py`, commit `766f5f2`). The remaining sections are Stage 6 work, not 4.5f. Extend to add mode / memory / emotional sections as those systems arrive. This is the seam every Stage 6 feature plugs into.
  - **Leave a context-compression hook (impr. #5):** the assembly seam is `retrieved chunks → [compression step — identity/passthrough for now] → context injection`. Wire the actual LLMLingua-style compressor at 6g; leaving the seam now avoids retrofitting it into a finished pipeline.
-  ✅ **Split `llm.py`** (DONE) — extracted pure Ollama transport (`core/ollama_client.py`) and the conversation orchestrator (`core/orchestrator.py`, which now owns `run_turn` + `session_history`); `turn_manager` stayed (4.5d). `llm.py` is now the facade — mutex + public API + `LLMModule`. Two committed cuts; `stop()` rebind bug caught and fixed in cut 2.
  - ✅ **Retrieval as a separable, injectable step (impr. #4)** (DONE — `run_turn(text, persist, prefetched=None)`, commit `766f5f2`): the orchestrator must expose memory retrieval as a standalone unit whose result can be *passed into* the turn (e.g. `prefetched=None`, fall back to inline retrieval when absent), so Stage 5 speculative prefetch wires in without touching the turn lock. The lock stays full-turn scope (impr. #9); prefetch *feeds* the turn, it does not bypass the lock. **Do this here, not in 4.5d** (4.5d would have been the second touch).
- ✅ **Tool registry** (DONE) — the if/elif command chain in `cli_input_loop()` is replaced by the schema-first `ToolRegistry` (`core/tool_registry.py`); the startup `Commands:` line generates from it. Sets up Stage 7's tool ecosystem.
  - **Schema-first contract (impr. #2):** build the registry so every tool carries an explicit JSON schema validated *on receipt* before any execution attempt, with a re-request cycle on malformed output rather than a silent try/except. Reliability comes from the schema discipline, not the model — the schema is the hard boundary.
- ✅ **Decide the agent→tool path explicitly** (DONE — ADR-001, `docs/planning/adr-agent-tool-path.md`) — model-selected tool calls route uniformly through `propose_action()`; core invariant "model invocation ≠ approval." Slash commands typed by Eddie are themselves approval. The `risk` field stays metadata-only until 8p.
  - **LLM-out-of-execution-loop is the architecture, not a convention (impr. #3):** the LLM decides *what*, deterministic code handles *how*. The registry defines legal call shapes; the executor only accepts validated calls; nothing else gets through. The 4.5c constrained executor + `propose_action()` gate already implement this correctly — the rule here is *don't soften it*: no broad try/except, no fallback execution paths that route around the gate.
- **Natural-language tool dispatch** ◀ NEXT — thin layer on the registry: expose registered tools as model-callable schemas so plain-language requests map to a *proposed* tool call routed through `propose_action()` (still y/n; slash commands kept as the fast path). Rides after the registry + 4.5c. The actual fix for the "everything is a manual slash command" friction.
  - **Use Ollama's native tool API (Oct 2026 review):** pass the registry's schemas as the `tools` array on `/api/chat` and read structured `tool_calls` back. Ollama does **not** validate arguments against the schema, so validate-on-receipt (impr. #2) stays the hard boundary. Keep `params_schema` as plain JSON Schema so the Stage 7 MCP adapter is free.
  - **Thinking control via the API:** for Qwen-family models, pass `think: false` per request through `ollama_client.py` (reasoning comes back in a separate `message.thinking` field). Keep the `<think>` strip before TTS/avatar as a backstop.
  - **First cut (seam, no behavior change):** add `ToolRegistry.to_ollama_tools()` (registry → Ollama `tools` array) and `tools` / `think` passthrough params on the `ollama_client.py` chat call. Nothing sends them yet. Second cut wires `tool_calls` parsing → schema validation → `propose_action()` in the orchestrator.
  - **Structured output for non-tool JSON:** Ollama's `format` parameter accepts a JSON Schema and constrains decoding — use it for later JSON tasks (6h write-time memory decisions).

### 4.5g — Communication-Model Decision

- Commit the conversation/avatar/TTS path to the event bus (kills the real `tts ↔ degradation` cycle and the lazy-import dodges scattered through `llm`/`degradation`/`health_check` — e.g. the `from core.avatar_router import send_to_avatar` lazy import inside `_run_turn`), **or** formally retire the bus. Running both half-heartedly is the current worst case. Do this before Stage 5 multiplies event sources.

- **DECIDED (2026-11-08): commit to the bus** (Eddie approved the review's recommendation). Build pending, after 4.5f closes.
- **Recommendation (Oct 2026 review):** commit to the bus. Comparable companion projects (Open-LLM-VTuber, AIRI) run voice → expression → TTS as one streamed event pipeline; retiring the bus would leave Stage 5's new event sources (screen, idle, prefetch) on lazy imports.

### Bookmark
🔖 *"Let's do the conversation refactor (4.5f) before Stage 5"*

---

## Near-Term — Model Evaluation: Qwen3 vs Qwen3.5 (impr. #1)

> **Position:** queued after Stage 4.5 is fully complete (4.5f + 4.5g), per Eddie 2026-11-08; `qwen3.5:9b` is the expected pick, but still run the eval. NL dispatch gives it a real tool-call path to test against. Low-risk, ~afternoon of work. Independent of the Live2D gate. Llama 3.1 8B is still the running model — the Qwen3 swap was planned but has not happened yet.

- **Evaluate two candidates against Llama 3.1 8B, then swap to the winner:**
  - `qwen3:8b` — ~5.2GB Q4_K_M, strong native tool calling, thinking toggle. The original plan.
  - `qwen3.5:9b` — ~6.6GB download, 256K context, **native vision + tools + thinking in one model**, hybrid attention (less KV cache at long context than Qwen3). Reported BFCL-V4 66.1. Needs Ollama ≥ 0.17.4.
  - *Also considered:* `gemma4:e4b` (vision + audio input, tools, thinking, 128K) — weaker pick for tool use; note only.
- **Test set:** `smoke_test.py` + a ~20-prompt tool-call set run through NL dispatch (correct tool chosen, args pass schema validation, no call when none is wanted) + a few long `/read` injections.
- **If `qwen3.5:9b` wins:** it becomes the single resident model and the 5d vision-model question is settled early — no separate vision model on the 12GB card.
- **Gotchas:**
  - Thinking mode: pass `think: false` per request through the Ollama API (reasoning returns in `message.thinking`). Keep stripping `<think>...</think>` before anything reaches TTS or the avatar output panel as a backstop. Enable thinking selectively when the reflection use case (6d) arrives — thinking mode *is* the reflection layer, no separate model needed.
  - Set `num_ctx` explicitly — don't rely on Ollama's default, or large `/read` injections get silently truncated. Check native context with `ollama show <model>`.
  - Check the installed Ollama version first (`ollama -v`).
  - Run `smoke_test.py` against the new model before calling it done.

### Bookmark
🔖 *"Let's do the model evaluation"*

---

## ⛔ HARD STOP — Live2D Otter Model

Unchanged hard gate, now with an audit note attached.

- `.moc3` export into `pocket-avatar/model/`, Live2D loader uncommented in `avatar.html`
- All 9 expressions mapped and **actually rendering** — **this is the fix for audit A9** (today's PNG can't show them; the backend routing is already real)
- Wandering, subtitles, physics, breathing confirmed on the real model
- **Renderer compatibility check** ✅ — the otter export is Cubism 5.0 moc3 and renders correctly on `pixi-live2d-display` 0.4.0 (Cubism 4 framework) in the standalone eye test; eye sliders + mouse follow work. *Re-check on every new rig:* Cubism 5.3 features (blend modes, offscreen drawing) need the R5 SDK; if a future export uses them, move to Live2D's official Cubism 5 Web SDK or `untitled-pixi-live2d-engine` (PixiJS v8, Cubism 2–5), not a re-rig.
- **Blink** — EyeBlink group re-export requested from the artist (pending).
- **Lip sync (mouth follows TTS)** — waits on the mouth rig + LipSync group. Plan: Piper plays audio in Python, so the avatar never sees the waveform; compute an RMS envelope per TTS chunk (~30ms frames) and send it over the existing WebSocket with playback start; the avatar drives `ParamMouthOpenY`. Add `ParamMouthOpenY` to `check_model.py`'s required params when the mouth rig arrives.
- **Final export textures** — ask for 2048/4096 instead of 8192 for the shipped build (VRAM).
- **Do not start Stage 5 until complete.**

### 5d-pre — Organize Avatar Assets
First task after the gate clears: `pocket-avatar/{models,expressions,physics,animations,configs,exports}/`. (Originally 4d; deferred here because it needs the real model.)

### 🪟 Interface Consolidation — Single App Surface

> **Position:** after the Live2D gate, before Stage 5's perception work. **Type:** QoL / operator UX — not a functional prerequisite, but doing it _here_ pays off: it builds the surface every later stage renders _into_ instead of spawning new windows.

> **Why here:** the current model is a constellation — separate avatar window, output panel, debug panel, an engine terminal, and a launcher script per piece. Functional, but developer-hell to operate. The Live2D model reshapes the avatar window anyway, so consolidating _after_ the art avoids redoing frontend work — and consolidating _before_ Stage 5 gives the perception/idle features one home to dock into.

- **Single app surface** — collapse avatar + output panel + debug panel + the engine CLI into one Electron app (one primary window, docked/toggleable panels).
- **In-app conversation + text input** _(absorbs old QoL #4)_ — a text input field and scrollable conversation view inside the app. Voice (F9) stays; this adds typed input in the GUI. _Plumbing partly exists: the engine already drains an avatar→engine WS channel reserved "future use" in `_hold`. The 4.5d turn mutex already covers it as another concurrent input source (text / voice / GUI), and 4.5f's orchestrator split makes the input source pluggable instead of hard-wired to the CLI loop._
- **Launcher + lifecycle rework** _(absorbs old QoL #1 — Stop-Pocket)_ — one launch, one real in-app quit/stop, retiring the Start/Stop `.bat` constellation. This _is_ the Stop-Pocket fix. _Until this lands, `/quit` + `docker compose down` is the clean manual stop._
- **Terminal becomes dev-only** — normal operation runs through the app; the CLI stays as a debug entry point.

_Dependencies: Live2D gate · 4.5f orchestrator · 4.5d mutex. Enables: Stage 5+ features render into this surface instead of new windows._

#### Bookmark
🔖 _"Let's consolidate Pocket into a single app surface"_

---

## Stage 5 — Screen Awareness + Dynamic Idle Behavior

Now built on a real orchestrator (4.5f) and the event bus (4.5g), with the turn mutex (4.5d) already in place.

- **5d — VRAM Budget + Model Lifecycle** (before loading any vision model). **Target shape (Oct 2026 review): one resident multimodal primary + an optional small helper.** If the near-term evaluation picks `qwen3.5:9b`, vision is already in the primary and no separate vision model is needed on the 10–12GB card. Helper (`qwen3.5:2b`/`4b`, ~2.7–4GB) for background jobs only, loaded on demand. Lifecycle states + OOM behavior.
  - **Ollama settings to pin:** explicit `num_ctx`; `OLLAMA_FLASH_ATTENTION=1`; `OLLAMA_KV_CACHE_TYPE=q8_0` (roughly halves KV cache); `keep_alive` for the primary; `OLLAMA_MAX_LOADED_MODELS` to cap concurrent residents.
  - *(future box)* On a 32GB card the primary can move up a tier — `qwen3.6:35b` (MoE, ~3B active, ~24GB) or `qwen3.5:27b` dense (~17–20GB) — leaving room for STT/TTS/embeddings/reranker on GPU. Re-check the landscape when that box is actually being bought.
- **5e — Privacy Boundary** (before any screenshot/always-on input). `privacy_config.yaml`: ignored folders/types/apps, screenshot suppression, observation modes, memory tags (persistent/ephemeral/private/restricted). *The `/read`+`/search` ephemeral handling from 4.5d is the precursor.*
- **5a — Screen Awareness** — **tiered perception (Oct 2026 review):** (1) foreground window title + process — always on, near-free; (2) UI Automation text of the focused window (`uiautomation` / `pywinauto`) — exact text, no OCR, no VRAM; (3) screenshot → vision model → spoken/avatar response, only on request or hotkey. The 5e app ignore list blocks capture *before* it happens at each tier.
- **Speculative context pre-fetch during STT (impr. #4 — wire here)** — while Whisper transcribes, kick off memory retrieval against the partial transcript in parallel via the injectable retrieval step left in 4.5f. By the time the full query lands, results are waiting — reclaims 0.5–2s of transcription dead time, the biggest lever on perceived voice latency. *Resolution of the impr. #4 ↔ #9 tension:* prefetch starts **outside** the lock (cache warm); the turn **validates/consumes** the prefetched result **under** the lock, which still owns retrieval-through-write correctness. Not speculative decoding — just parallelising STT + retrieval.
- **5-voice — Voice Pipeline Refresh (Oct 2026 review)** — independent small cuts, each behind the existing module interface:
  - **STT: Whisper base → Parakeet TDT 0.6B** via `onnx-asr` or `sherpa-onnx` (no NeMo needed). More accurate than Whisper large-v3 on the open ASR leaderboard, much faster, and doesn't hallucinate text during silence. Contained change to `core/stt.py`. If speculative prefetch needs partial transcripts, NVIDIA's Nemotron streaming ASR produces them natively — evaluate it when building prefetch.
  - **TTS: trial Kokoro-82M** (Apache-2.0) — more natural than Piper medium at similar CPU cost. Keep Piper (now maintained by the Open Home Foundation, GPL-3.0) as fallback. *(future box)* Chatterbox (MIT, voice cloning) or Qwen3-TTS (Apache-2.0, streaming) for a custom otter voice.
  - **Sentence-chunked TTS** — start speaking at the first finished sentence instead of the full reply (if not already done). With prefetch, the biggest perceived-latency lever.
  - **Barge-in** — pressing F9 while Pocket is speaking stops TTS.
  - Wakeword stays dropped. If hands-free is ever revisited (with 5e + consent): Silero VAD + Smart Turn v3.2 (8MB, CPU, BSD-2) for end-of-turn detection.
- **5b — Proactive Suggestions** — hotkey → activity → context → bug detection. *Wires through the dormant `web.search` bus hook.*
- **5f — Expression Arbitration Layer** (before concurrent behaviors) — priority-ranked expression events (critical 100 → idle 10), cooldown, blending, source tracking.
- **5c — Dynamic Idle Behaviors** — mouse reactions, time-of-day calm, project-excited idle, sleepy states, quiet during fullscreen. *Extension: spatial workspace awareness.*

### Bookmark
🔖 *"Let's build screen awareness for Pocket"*

---

## Stage 6-Early — Intelligence Layer (High Value First)

- **6a — Local Semantic Search** (highest practical value) — embeddings + RAG across notes, code, logs, docs, saved conversations.
  - **Cross-encoder reranking (impr. #10):** after ChromaDB returns top-N, a cross-encoder rescores by jointly reading query + each candidate — meaningfully more accurate than vector similarity alone. Slots directly before context injection, no schema changes. Start point: `cross-encoder/ms-marco-MiniLM-L-6-v2` (tiny, CPU-only, no VRAM). **Make the reranker model name a config key (Oct 2026 review):** MiniLM is now considered legacy (~60 BEIR nDCG@10); `bge-reranker-v2-m3` (0.6B, MIT, ~71.5) or `Qwen3-Reranker-0.6B` (~71.4) are much stronger but ~20× bigger — benchmark CPU latency per turn before switching, or run on GPU if VRAM allows.
  - **Embedding model upgrade (Oct 2026 review):** if the Chroma collection uses the default embedding function, that's `all-MiniLM-L6-v2`. `qwen3-embedding:0.6b` or `embeddinggemma` via Ollama are much stronger. Switching means re-embedding every memory — **do it in the same cut as the 6h schema migration** so memory is touched once (A4 trap).
  - **Typed-memory retrieval routing (impr. #6 — design input):** retrieval strategy differs by memory type (see 6h) — episodic by recency+relevance, semantic by entity match, procedural keyword-heavy. 6a's retrieval layer should be able to route per type, not one-size-fits-all.
- **6b — Skill Modes** — coding / cybersecurity / writing / research / casual / planning. **⚠️ Resolve the taxonomy first:** task-mode (6b) vs mood-based "Interaction Style Profiles" vs numeric "Temperament Engine." Pick the axis (recommend task-mode primary, mood as a lightweight modifier) before building.
- **6c — Workspace Awareness** — recognize coding/writing/research/gaming sessions and adapt.
- **Vault schema** — sketch `vault-schema.md` before 6d.

### Bookmark
🔖 *"Let's build Pocket's intelligence layer — starting with semantic search"*

---

## Stage 6-Late — Intelligence Layer (Depth Systems)

- **6d — Memory Reflection** (Vault block 1) — periodic review → long-term summaries. *(Qwen3 thinking mode is the reflection engine — impr. #1; no separate model.)*
- **6d.1 — Project Continuity Notes** — between-session "here's where we left off" (`/continuity`).
- **6d.2 — Passive Observation + Draft Proposals** — Pocket drafts improvement ideas for review (`proposals/`).
- **6e — Emotional Continuity Layer** — tone/stress/enthusiasm tracking; lightweight, respectful, user-controlled. *Folds in the idea corpus's "Temperament Engine" + "Emotional Simulation Layer" as modifiers, not new systems.*
- **6f — Multi-Model Routing** — **re-scoped (Oct 2026 review): primary + helper.** With a multimodal primary, separate vision/coding/reflection models aren't needed at this scale. Routing = which jobs go to the small helper (memory extraction, consolidation, intent classification) so the primary isn't tied up. *Built on the 5d target shape.*
- **6g — Context Window Management** — *fixes the unbounded `session_history` re-sent every turn.* **Order (Oct 2026 review):** (1) explicit `num_ctx` + per-section token budgets; (2) rolling session summary; (3) priority injection.
  - **Compression hook (impr. #5) — now optional:** LLMLingua-style token pruning targets long retrieved chunks, not history growth; it adds a CPU model pass to every voice turn and is riskier with 8B readers. Keep the 4.5f passthrough seam; wire a compressor only if measurements show retrieved chunks crowding the budget.
- **6h — Memory Metadata + Pruning** — importance/confidence/recency/supersedes/type/retention; duplicate collapse, stale archival, low-value pruning.
  - **Typed memory (impr. #6):** episodic / semantic / procedural as a tagging + routing layer on top of ChromaDB (not three databases). The `type` tag is what lets 6a route a query to the right retrieval strategy.
  - **Temporal memory (impr. #7):** store a timestamp with every memory and maintain a lightweight temporal index; timestamps are **first-class retrieval keys**, not annotation fields. Enables "what were we working on last week" / "how has this changed" that pure similarity can't answer. **Design into the schema from the start** — retrofitting temporal indexing is painful. Pairs with typed memory (episodic needs temporal ordering). **Bi-temporal fields (borrowed from Graphiti, Oct 2026 review):** `valid_at` (when it became true), `invalid_at` (when it stopped being true), `ingested_at` (when Pocket learned it) — superseded facts get `invalid_at` set instead of being deleted.
  - **Pre-storage reasoning (impr. #8):** process at **write time**, not read time — on store, the model reasons about category, contradictions, ephemeral-vs-persistent, and what this *supersedes*. Conflict detection + dedup happen at write time so stale facts don't accumulate as retrieval noise. The `supersedes` field and dedup are write-time operations, not metadata left for retrieval to sort out. **Implementation (borrowed from Mem0, Oct 2026 review):** one structured-output call (Ollama `format` = JSON Schema) that compares the new memory with its nearest neighbours and returns `ADD` / `UPDATE` / `DELETE` (→ set `invalid_at`) / `NONE`, running under the turn lock. Can run on the 6f helper model.
  - **Borrow patterns, not libraries:** Mem0, Graphiti and cognee all run locally on Ollama, but adopting one would add a dependency (Graphiti needs Neo4j/FalkorDB and warns small models break its JSON schema) and move memory writes outside `TurnManager` and the data-not-authority rules.
- **6h.1 — Background Housekeeping** — idle dedup + archival proposals.
  - **Idle consolidation (impr. #9):** scheduled background passes (not inline mid-turn) that merge duplicates, archive stale entries, and promote clusters of episodic memories into single semantic facts. **Must acquire `turn_manager.exclusive()`** before touching memory records — the 4.5d lock already spans the full turn including writes, so a consolidation pass and a live turn cannot interleave. (This is why the lock was scoped full-turn in 4.5d rather than around the Ollama call.)
- **6h.2 — Knowledge Gap Flagging** — `knowledge-gaps.md`; self-directed learning queue.

### Bookmark
🔖 *"Let's build the depth systems for Pocket's intelligence layer"*

---

## Stage 7 — Full Computer Access + Integrations

- **7a — Session Pre-loading** — context warmed before likely sessions.
- Sandboxed program access with per-action approval *(builds on the hardened executor from 4.5c)*.
- VS Code / IDE integration; n8n webhook triggers; file system watcher; calendar/schedule.
- **Tool ecosystem** — built on the 4.5f tool registry + schema contract (impr. #2). *Home for the idea corpus's `tools/` + `integrations/` clusters.* **Via MCP (Oct 2026 review):** MCP is now the common interface for local tools (n8n, VS Code, filesystem servers expose it). Build one MCP client adapter that registers MCP tools into `ToolRegistry`; every call still goes through `propose_action()`. Treat MCP tool descriptions as untrusted data — they are a prompt-injection surface. IDE integration through MCP rather than a custom extension.

---

## Stage 8 — Advanced Systems + Supervised Autonomy

- **8a — Avatar Intelligence / Co-pilot** — takes initiative on suggestions, never acts autonomously. *Assumes the agent→tool path decided in 4.5f.*
- **8b — Memory Vault** — wiki-style self-building long-term memory (6d feeds it; 8f writes to it).
- **8c — Sandbox Simulation** — test proposals in isolation before presenting (8c.1 dry runs). *`shell=True` exposure decision lands here.* **Mechanism:** a throwaway Docker container with `--network none` and a copy of the target folder (Docker is already in the stack); Windows Sandbox as the heavier alternative.
- **8d — Adaptive Visual Identity** — seasonal/mood-adaptive appearance. *Home for the idea corpus's dynamic "Identity Engine" evolution beyond the static prompt pipeline.*
- **8e — Workspace Dashboard** · **8f — Background Reflection Loop** (Vault block 3) · **8g — Contextual Sound** · **8h — Episodic Memory Timeline** *(consumes the temporal index from impr. #7)* · **8i — Knowledge Graph** · **8j — Learning From Corrections** · **8k — Self-Observability Dashboard** (consumes 4j.1, once 4j.1 measures real metrics) · **8l — Active Project Management** · **8m — Architecture Drift Detection** · **8n — Internal Documentation Agent** · **8o — Long-Term Goal Tracking**.

### 🔴 8p — Supervised Autonomy Framework (the idea corpus's 6i, re-homed)

> The idea corpus's biggest cluster (goals/tasks/self-directed maintenance) was premature where first written — it depends on systems that didn't exist. **This is where its foundations finally converge.**

- **Dependencies, now satisfied:** reflection (6d) · memory metadata (6h) · hardened executor (4.5c) · agent→tool decision (4.5f) · co-pilot (8a) · sandbox (8c).
- **Harvest 6i's safety principles into the design now:** Pocket may NOT self-authorize, escalate its own scope, or bypass the permission gate; resource budgeting (6i.7) caps what a self-directed task may consume.
- **6i.8 — pre-approved maintenance without per-action approval** is the one idea that directly contradicts the "every action approved" model. Gate it hard: only after the executor is *provably* safe (4.5c done + tested), inside the sandbox (8c), with exhaustive logging, scoped to a tiny whitelist. Skepticism is the default.

---

## Stage 9 — Knowledge Expansion + Fine-tuning (ongoing)

Continuous knowledge loading, fine-tuning experiments, capability expansion as the stack matures.

- **First fine-tune target (Oct 2026 review):** Pocket's voice + tool-call format, using `logs/decisions.jsonl` and approved transcripts as data. Handle 8j "learning from corrections" through memory first; fine-tune only what memory can't fix. QLoRA on a 9B model is practical on a 24–32GB card *(future box)*; on the current card, keep to small adapters or defer.

---

## Stage 9+ — Experimental / Long-Game

- **9a — Personal Cognitive Profile** — learns how Eddie thinks; adaptive explanation style.
- **9b — Multi-Agent Internal Collaboration** — specialist agents orchestrated by Pocket.
- **9c — Personal AI Research Lab** — architecture comparison, fine-tune experiments.
- **9d — Thinking-Visibility Policy** *(was: Internal Monologue / Thought Layer)* — thinking models already reason privately before responding, and Ollama returns that reasoning separately, so the mechanism is solved. What remains is policy: what Pocket may think about, whether thoughts are logged, and whether Eddie can read them. No longer the most speculative item.

---

## Idea-Corpus Disposition (every idea accounted for)

|Idea (source)|Disposition|Foundation / where built|
|-|-|-|
|Identity consolidation|✅ **Done**|4.5a|
|Prompt Assembly Pipeline|Started → extend|4.5f (brick laid in 4.5a)|
|Conversation Orchestration (Stage 5.5)|Scheduled, scoped down|4.5f (turn_manager + scheduler; defer interruption/backchannel/topic-tracking)|
|Tool registry|Scheduled|4.5f → Stage 7|
|Model-roles table|Planning input|5d (VRAM) + 6f (routing)|
|Skill Modes / Interaction Style / Temperament|Merge into one axis|6b (resolve taxonomy) + 6e|
|Emotional Simulation Layer|Lightweight modifier|6e|
|Memory layering (episodic/semantic/scoring)|Scheduled|6a / 6h / 8h / 8i|
|Reflection engine|Scheduled|6d → 8f|
|Goals / Tasks / Planning (6i, 6m, 6o)|Re-homed|**8p**|
|6i.8 pre-approved maintenance|Deferred + hard-gated|8p, after 4.5c proven|
|Sandbox simulation|Scheduled|8c|
|Knowledge graph|Scheduled|8i|
|Workspace / perception|Scheduled|Stage 5 / 6c|
|Adaptive / dynamic identity|Largely satisfied + advanced part later|prompt pipeline (4.5a/4.5f) now; evolution at 8d|
|Multi-agent|Scheduled|9b|
|Cognitive profile|Scheduled|9a|
|Internal Monologue / Thought Layer|Mechanism solved by thinking models; policy remains|9d (reframed v2.2)|
|Wakeword / always-listening|🚫 **Deferred/dropped**|Privacy regression; F9 is safer. Revisit only with 5e privacy + explicit consent|
|Directory-framework reorg|🧭 **North star only**|Not a migration — a literal adoption is a rewrite|
|Architectural-questions doc|Adopt as practice|Standing ADR / design checklist|
|Work-session prompts|Dev-process doc|Already encodes the audit's principles|
|Hardware build (5090 / 96GB)|Future upgrade (not near-term)|Plan is sized for the current 10–12GB card; 5090 notes marked *(future box)*. Relaxes the VRAM ceiling for 5d/6f when it happens; does **not** change ordering|

---

## Improvements — Integrated (June 2026 research list, now retired)

Ten items from model/methodology research, folded into the stages above. This table is the provenance map; the standalone list is no longer needed.

|#|Item|Disposition|Where it now lives|
|-|-|-|-|
|1|Qwen3 8B swap|Scheduled near-term — now an evaluation|*Near-Term: Model Evaluation* (qwen3:8b vs qwen3.5:9b; winner may settle 5d)|
|2|Schema-driven tool-call reliability|Scheduled|4.5f — tool registry built around validated JSON schemas|
|3|LLM-out-of-execution-loop (hard boundary)|✅ Implemented, harden + don't soften|4.5c (gate exists) + 4.5f (registry defines legal shapes)|
|4|Speculative context pre-fetch during STT|Seam now, wire later|4.5f (retrieval made injectable) → Stage 5 (parallelise w/ STT)|
|5|Context compression hook (LLMLingua)|Seam placed; compressor now optional|4.5f (passthrough hook) → 6g (budget + summary first; compressor only if measured need)|
|6|Typed memory (episodic/semantic/procedural)|Scheduled|6h (tagging + routing) + 6a (per-type retrieval)|
|7|Temporal memory (timestamps first-class)|Scheduled — design into schema early|6h schema, bi-temporal fields (+ consumed by 8h timeline)|
|8|Pre-storage reasoning (write-time)|Scheduled|6h (ADD/UPDATE/DELETE/NONE structured-output call)|
|9|Idle consolidation (scheduled, locked)|✅ Lock ready (4.5d), pass scheduled later|6h.1 (acquires `turn_manager.exclusive()`)|
|10|Cross-encoder reranking|Scheduled|6a (MiniLM first; model name as config key, bge-reranker-v2-m3 upgrade path)|

> **Note on the impr. #4 ↔ #9 tension:** item 9 wants retrieval *inside* the locked critical section; item 4 wants it to *start outside* (during STT). Resolution (Stage 5): prefetch starts outside the lock as a cache warm; the turn consumes/validates the prefetched result under the lock, which still owns retrieval-through-write correctness. 4.5f's only job is to leave retrieval separable so this is possible without re-touching the lock.

---

## Master Checklist

### Done (this audit cycle)
* [x] Identity reconciliation — `build_system_prompt()` on the live path (4.5a)
* [x] Injection-defense stance in the runtime prompt via `authority.md` (4.5a)
* [x] Identity consolidated to one source; dead duplicates deleted (4.5a)
* [x] `avatar/expression_engine/` fossil + vestigial `SYSTEM_PROMPT` removed (4.5a)
* [x] Decoupled launcher set; scoped shutdown; port-poll readiness (4.5b)
* [x] Close `/exec → .env` leak (4.5c)
* [x] Replace substring denylist with parsed/constrained executor (4.5c)
* [x] Executor backup policy decided + tests un-skipped (4.5c)
* [x] Turn mutex around the full pipeline incl. memory writes (4.5d, impr. #9)
* [x] Piper subprocess timeout (4.5d)
* [x] A10 — `DEGRADED_MODE` non-terminal / auto-recovers (4.5d)
* [x] `/read`+`/search` stop auto-persisting to memory (4.5d)
* [x] A1 WS schema unified · A2 monitor logging · A3 config paths + logger · A5 name collision · A6 dup imports · A7 unused Docker svc · A8 venv (4.5e)

### Stage 4.5f — in progress
* [x] Prompt assembly seam + compression hook passthrough (4.5f, impr. #5); remaining sections are Stage 6
* [x] `llm.py` split: client / orchestrator / turn_manager
* [x] Retrieval made separable/injectable for prefetch (4.5f, impr. #4)
* [x] Tool registry replaces if/elif chain + schema-first validation (4.5f, impr. #2)
* [x] Agent→tool path decided + documented — ADR-001 (4.5f, impr. #3)
* [ ] **NEXT:** Natural-language tool dispatch over the registry, behind the permission gate (Ollama `tools` + `think: false`)
* [ ] Closing cut: dead Monitor param cleanup + A4 generic lifecycle loop (both in `pocket.py` startup)

### Stage 4.5g
* [x] Decision: commit to the event bus (2026-11-08)
* [ ] Conversation/avatar/TTS path committed to the event bus (kills lazy-import dodges)

### Near-term
* [ ] Model evaluation: qwen3:8b vs qwen3.5:9b vs Llama 3.1 baseline — smoke test + tool-call set; `think: false` via API; strip `<think>` backstop; explicit `num_ctx` (impr. #1)

### Live2D gate
* [x] Renderer compatibility — Cubism 5.0 otter renders on pixi-live2d-display 0.4.0 (eye test passed)
* [ ] EyeBlink group re-export (requested from artist)
* [ ] Real `.moc3` model rendering all 9 expressions (closes A9)
* [ ] Lip sync — mouth rig + LipSync group, TTS amplitude envelope over WS → `ParamMouthOpenY`
* [ ] Final export at 2048/4096 textures
* [ ] Avatar asset structure organized (5d-pre)

### Forward (high level)
* [ ] Stage 5 — VRAM budget (single multimodal primary + helper) · privacy boundary · tiered screen awareness · voice refresh (Parakeet, Kokoro trial, sentence-chunked TTS, barge-in) · STT prefetch (impr. #4) · arbitration · idle
* [ ] Stage 6-Early — semantic search + cross-encoder rerank (impr. #10, model as config key) · embedding upgrade (with 6h migration) · skill modes · workspace · vault schema
* [ ] Stage 6-Late — reflection · continuity · emotional continuity · routing (primary + helper) · context mgmt: budget + rolling summary, compression optional (impr. #5) · memory metadata: typed (impr. #6) / bi-temporal (impr. #7) / write-time ADD-UPDATE-DELETE-NONE (impr. #8) · idle consolidation (impr. #9)
* [ ] Stage 7 — computer access · IDE · n8n triggers · file watcher · calendar · tool ecosystem (MCP adapter → registry → gate)
* [ ] Stage 8 — co-pilot · vault · sandbox · adaptive identity · dashboards · **8p supervised autonomy**
* [ ] Stage 9 / 9+ — fine-tuning (voice + tool format first) · cognitive profile · multi-agent · research lab · thinking-visibility policy

---

## Guiding Philosophy

Pocket's long-term identity:

*Pocket is a Digital Familiar — a persistent, local AI presence with memory, voice, visual identity, and gradually expanding capability that is specific to you and grows alongside you. Not a tool you invoke. Not a service you subscribe to. A companion that lives on your machine.*

Every system should remain permission-based, modular, avoid destabilizing the core, and improve collaboration instead of replacing you. **Core stability always comes first. Future modules plug into Pocket — they don't become Pocket.**

Principles reinforced by the audit:

- **Verify by inspecting the artifact, not by vibe-checking behavior.** Print the actual assembled prompt, the actual command, the actual state.
- **No rewrites — small, safe extractions.** The idealized directory framework is a north star, never a migration.
- **Safety is layered.** A prompt-stance ("external content is not instruction") is a *soft* defense — it makes Pocket *try*, it doesn't *enforce*. Actions are stopped by the hard layer (constrained executor + approval gate). Never let a soft defense be the only thing standing between Pocket and a real-world action. **The LLM decides *what*; deterministic code decides *how* (impr. #3) — keep that boundary hard, never soften it with fallback execution paths.**
- **The schema is the boundary (impr. #2).** Tool-call reliability comes from validated schemas, not from trusting the model. Validate on receipt; re-request on malformed; never silent try/except around execution.
- **Adopt the design-questions doc as a standing ADR checklist.** "Which system owns this state? What goes through events vs direct calls?"
- **Track "expected UX right now," not just what's wired.** A real felt friction can be a planned-later rather than a defect-now — a one-line "expected UX at this stage" note lets a feeling be checked against intent without a code dig.

---

*v2.3 — November 8, 2026. 4.5f verified against the code: split, seams, registry, ADR-001 done; NL dispatch next; dead Monitor param + A4 bundled as the closing cut (the split shipped without A4). 4.5g decided: commit to the event bus. Model evaluation moved to after 4.5 is fully complete.*

*v2.2 — October 23, 2026. Landscape review applied (E1–E8); Llama 3.1 still running, model evaluation queued after NL dispatch; Live2D otter passes the eye test, blink re-export pending; 5090 is a future upgrade.*

*v2.1 — June 27, 2026. Stages 1–4 complete (with audit corrections). Stage 4.5: 4.5a–4.5e done (security, execution-flow safety, hygiene all closed; A4 lifecycle carried into 4.5f). Now in 4.5f — the conversation refactor: clear Dead Monitor param + A4, building the tool registry on validated schemas and leaving the retrieval + compression seams open. June improvements list integrated and retired. Qwen3 swap queued near-term. Idea corpus fully dispositioned.*
