# Pocket Changelog

## 2026-05-13

* Git repo initialized — Stage 4 begins
* requirements.txt snapshot committed
* Stages 1–3 complete: ChromaDB memory, Whisper STT, Piper TTS, Electron avatar, unified pocket.py


2026-05-20

\- Stage 4s complete — Module Lifecycle Contract

\- pocket\_module.py — PocketModule ABC, all 4 methods enforced at instantiation

\- All 9 core modules retrofitted with start/stop/health\_check/on\_event

\- Smoke test updated with full contract test block


## 2026-05-24
- 4q complete — EventBus + EventBusModule, synchronous pub/sub
- Failing subscribers log and recover, don't crash the bus
- Smoke tests green including bad_handler isolation test


## 2026-05-24
- 4q complete — EventBus + EventBusModule, synchronous pub/sub
- 4n complete — WebSocket reconnection engine, exponential backoff (cap 60s, max 10 attempts)
- 4i complete — structured JSONL logging, daily rotation, wired into executor/avatar/memory/websocket/pocket
- 18 passed · 0 failed · 1 skipped


## 2026-05-27
- Stage 4j complete — startup health checks, critical/non-critical gates
- Stage 4j.1 complete — continuous self-monitoring background thread
- Stage 4t complete — runtime debug overlay (Electron debug panel)
  - Dark floating panel shows STATE / CONN / SESSION / HEALTH / EVENTS live
  - Alt+D toggles panel visibility and starts/stops the Python live feed
  - Reads directly from StateManager (4r) and EventBus (4q)

### Bugs fixed this session
- 4t: DebugOverlay instantiated with send_to_avatar (string processor) instead of
  websocket_module.send (raw dict sender) — panel was receiving garbage
- 4t: overlay.snapshot() renamed to push() in new version but pocket.py still
  called snapshot() — AttributeError on Alt+D
- 4t: handleCommand in main.js routes on msg.type but overlay sends msg.command —
  debug messages were silently dropped by the default case
- 4t: overlay.start_live() called unconditionally on startup — panel opened
  automatically with no way to dismiss it; fixed by lazy-starting on Alt+D

## 2026-05-29
- Stage 4k complete — graceful degradation for Ollama, Chroma, Piper, WebSocket
- Added core/degradation.py — notify() + mark_degraded/mark_recovered, deduped,
  routed through state (4r), logging (4i), event bus (4q)
- Fixed unhandled save_memory crash on ChromaDB failure (could take down a turn)
- Routed 4j.1 monitor's degraded/recovered transitions through the shared helper;
  removed its old avatar-alert path
- Added tests/degradation_test.py — fault-injection suite, 31/31 green
- Manual pass: confirmed Pocket survives + reports Ollama/Chroma/Piper/WebSocket
  failures. WebSocket auto-reconnect not yet re-verified — the avatar server
  didn't relaunch during the test (operational, not a code issue; see audit A11)
- Logged audit findings A1–A11 for the upcoming project audit

## 2026-05-30
- Stage 4h started — web search via core/web_search.py, Tavily backend
- Pluggable backend design (SearXNG stubbed for Stage 6/7)
- /search command + .env key