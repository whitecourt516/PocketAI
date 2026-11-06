# Stage 3 — Interface & Avatar (UPDATED)
**Priority: Medium | Status: Files built, ready to install**  
**Replaces the VTube Studio plan in the master roadmap**

---

## What Changed and Why

The original plan listed VTube Studio for the avatar. VTube Studio is a streaming tool — it's designed to put an avatar in front of a camera for Twitch/YouTube. That's not what Pocket is. Pocket is a desktop companion that lives on your screen and expresses itself in response to what it's thinking and saying.

The new architecture is a **custom Electron app** — a small desktop application that renders Pocket's otter avatar directly on your screen with a transparent background, always on top of your other windows, wandering around freely.

This is better for Pocket because:
- Pocket can read and edit its own appearance files directly (critical for Stage 4 self-improvement)
- No third-party app in the loop — full control over every behavior
- The avatar responds to Pocket's actual output, not face tracking
- Expressions are driven by what Pocket is *saying*, not what your face is doing

---

## What's Built

All files are in the `pocket-avatar/` folder:

```
pocket-avatar/
├── app/                        ← Electron avatar application
│   ├── main.js                 ← Window management, wandering, WebSocket server
│   ├── preload.js              ← Secure bridge between app and renderer
│   ├── package.json            ← Node.js dependencies
│   └── renderer/
│       ├── avatar.html         ← The otter (placeholder + Live2D ready)
│       └── panel.html          ← Output panel for code/long responses
│
├── expression-engine/
│   └── pocket_avatar.py        ← Connects Ollama → emotion detection → avatar
│
└── docs/
    └── SETUP.md                ← Full install guide
```

---

## How It Works

```
You speak / type
      ↓
pocket_avatar.py receives input
      ↓
Sends to Ollama (llama3.1:8b) on port 11434
      ↓
Reads the response
      ↓
Detects emotion (keyword analysis → expression name)
      ↓
Sends WebSocket command to Electron app on port 7845
      ↓
Otter changes expression + shows subtitle
      ↓  (if response is long/code)
Output panel opens in bottom-right corner
```

---

## Avatar Behaviors

| Behavior | Detail |
|----------|--------|
| Wandering | Otter moves to a new random screen position every 8 seconds, smooth animation |
| Always on top | Sits above all other windows at all times |
| Expressions | neutral, happy, excited, thinking, surprised, concerned, sleepy, smug, sad |
| Thinking state | Dots appear while Ollama is processing, wandering pauses |
| Subtitles | Short responses appear as a bubble above the otter (auto-dismisses) |
| Output panel | Long text / code opens a dark panel in the bottom-right corner |
| Hotkeys | Alt+H hides/shows otter, Alt+P toggles panel |
| Self-modifiable | All appearance config is in plain files Pocket can read and edit |

---

## Current State — Placeholder Otter

The avatar currently shows a simple SVG otter — a brown otter shape with the right proportions, scarf, and eyes. It breathes, reacts to expressions, and tilts when wandering. It is enough to develop and test the full system.

**To swap in the real otter when it's rigged:**
1. Export from Live2D Cubism: `.moc3`, `.model3.json`, `.physics3.json`, textures, expressions
2. Drop files into `pocket-avatar/model/`
3. Uncomment the Live2D loader section in `avatar.html`
4. Real otter replaces placeholder — nothing else changes

---

## Self-Improvement Hook (Stage 4 Preview)

The files Pocket will be able to edit to change its own appearance/behavior:

| File | What Pocket can change |
|------|----------------------|
| `pocket_avatar.py` lines 30-45 | Emotion detection rules — which words trigger which expression |
| `pocket_avatar.py` line 18 | Which Ollama model it uses |
| `pocket_avatar.py` line 20 | Max subtitle length |
| `main.js` CONFIG block | Wander speed, interval, window size, panel corner |
| `pocket_avatar.py` POCKET_SYSTEM_PROMPT | Its own personality and instructions |

Once `/read` is working in Stage 4, Pocket can examine these files, propose changes, and (with the user's approval) write updates to them directly.

---

## Install

See `docs/SETUP.md` for the full step-by-step guide.

Short version:
```bash
# Install Node.js from nodejs.org first, then:
cd pocket-avatar/app
npm install
npm start

# In a second terminal:
cd pocket-avatar/expression-engine
pip install requests websockets
python pocket_avatar.py
```

---

## What's NOT in Stage 3

- Voice input/output — that's Stage 2 (Whisper + Piper), already documented in the roadmap. Once Stage 2 is wired up, voice flows through `pocket_avatar.py` automatically.
- Screen awareness — Stage 5
- The real otter model — depends on art/rigging timeline, completely independent of this code

---

*Stage 3 updated May 2026 | Original VTube Studio plan superseded*
