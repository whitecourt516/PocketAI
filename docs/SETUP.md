# Pocket Avatar — Setup Guide
## Getting the otter on your screen, step by step

**Written for:** The user | Windows | Ollama already running | Python installed  
**Time needed:** About 30–45 minutes  
**What you'll have at the end:** Pocket's avatar living on your desktop, expressions changing automatically as it responds

---

## Before You Start — Check These

Open **Command Prompt** (press `Win + R`, type `cmd`, press Enter) and run these checks:

```
python --version
```
Should show Python 3.10 or higher. ✓

```
ollama list
```
Should show `llama3.1:8b` in the list. ✓

```
ollama serve
```
If it says "already running" or shows a port — great, leave it. ✓

---

## Step 1 — Install Node.js

The avatar app runs on Electron, which needs Node.js.

1. Go to **https://nodejs.org**
2. Click the big **LTS** download button (not "Current")
3. Run the installer — click Next through everything, keep all defaults
4. When it finishes, **close and reopen** your Command Prompt

Verify it worked:
```
node --version
npm --version
```
Both should show version numbers. ✓

---

## Step 2 — Copy the Pocket Avatar Folder

1. Take the `pocket-avatar` folder (the one containing this guide)
2. Copy it somewhere permanent — a good spot is:
   ```
   C:\Users\YourName\pocket-avatar\
   ```
3. Don't put it on the Desktop or in Downloads — those are messy. Give it a real home.

---

## Step 3 — Install the Avatar App Dependencies

In Command Prompt, navigate to the app folder:

```
cd C:\Users\YourName\pocket-avatar\app
```
*(Replace YourName with your actual Windows username)*

Then install:
```
npm install
```

You'll see a lot of text scroll by — that's normal. Wait for it to finish (1–3 minutes). ✓

---

## Step 4 — Install the Python Dependencies

In Command Prompt, run:

```
pip install requests websockets --break-system-packages
```

Wait for it to finish. ✓

---

## Step 5 — Start the Avatar App

In Command Prompt (still in the `app` folder):

```
npm start
```

**What you should see:**
- A small otter appears on your screen
- It has a transparent background — just the otter, no box
- It sits there breathing gently
- The terminal shows: `[Pocket] WebSocket server listening on port 7845`

If you don't see the otter, check the terminal for error messages and see the Troubleshooting section at the bottom of this guide.

---

## Step 6 — Start the Expression Engine

Open a **second** Command Prompt window (keep the first one running the avatar).

Navigate to the expression engine folder:
```
cd C:\Users\YourName\pocket-avatar\expression-engine
```

Run it:
```
python pocket_avatar.py
```

**What you should see:**
```
==================================================
  Pocket Expression Engine
  Model: llama3.1:8b
  Avatar: ws://localhost:7845
==================================================

[Pocket] Connected to avatar ✓
Type your message and press Enter.
```

The otter's expression may flicker as it connects. ✓

---

## Step 7 — Talk to Pocket

Type anything in the expression engine window and press Enter:

```
You: Hey Pocket, how are you doing?
```

Watch the otter — it should:
1. Switch to the **thinking** expression (dots appear) while Ollama processes
2. Switch to a **happy** or **neutral** expression when the response arrives
3. Show the response as a **subtitle bubble** above the otter
4. Print the full response in the terminal

If the response is long (code, a detailed explanation), the **output panel** will slide open in the bottom-right corner of your screen.

---

## Step 8 — Test the Expressions

In the expression engine window, try these test commands:

```
/expr happy
/expr excited
/expr thinking
/expr concerned
/expr surprised
/expr sleepy
/expr smug
/expr neutral
```

Each one should immediately change the otter's appearance. ✓

Test the output panel:
```
/panel
```
The panel should open in the bottom-right corner with some test content. ✓

---

## Step 9 — Learn the Hotkeys

These work **anywhere** on your screen while the avatar is running:

| Hotkey | What it does |
|--------|-------------|
| `Alt + H` | Hide / show the otter |
| `Alt + P` | Toggle the output panel open/closed |

---

## You're Done — Basic Setup Complete ✓

Pocket is now:
- Living on your desktop as an animated otter
- Responding to your text with automatic expressions
- Showing short responses as subtitles, long responses in the panel
- Always on top of your other windows

---

## What's Next

### Connecting Your Push-to-Talk Voice Input
Since you already have push-to-talk set up, the next step is routing your voice transcriptions through the expression engine instead of typing. This happens in Stage 2 (Voice) of the roadmap — Whisper transcribes your speech and feeds it directly to `pocket_avatar.py` as if you typed it.

### Swapping In Your Real Otter Model
When your Live2D otter is rigged and exported:

1. Export from Live2D Cubism as `.moc3`
2. Copy these files into `pocket-avatar/model/`:
   ```
   Otter.moc3
   Otter.model3.json
   Otter.physics3.json
   textures/ (folder)
   expressions/ (folder)
   ```
3. Open `app/renderer/avatar.html`
4. Find the line that says `// TODO: initialize PIXI + Live2DSprite`
5. That section has instructions for enabling the Live2D canvas

The placeholder otter disappears and your real otter takes over. Nothing else changes.

### Letting Pocket Edit Its Own Appearance
Once Stage 4 (/read command) is working, Pocket can:
- Read its own `pocket_avatar.py` to understand the emotion rules
- Suggest new emotions or adjust which keywords trigger which expression
- Read and propose changes to its own config values (wander speed, subtitle timing, etc.)
- Write those changes back with your approval

The appearance config lives in two files Pocket will have full access to:
- `app/main.js` — wandering speed, panel position, window size
- `expression-engine/pocket_avatar.py` — emotion rules, subtitle length, personality

---

## Troubleshooting

**Otter doesn't appear:**
- Make sure you ran `npm install` before `npm start`
- Check the terminal for red error messages
- Try closing and rerunning `npm start`

**"Cannot connect to avatar" in the expression engine:**
- Make sure the avatar app (`npm start`) is running first
- Wait a few seconds after starting the avatar before starting the expression engine

**"Cannot connect to Ollama":**
- Run `ollama serve` in a separate terminal
- Make sure `ollama list` shows `llama3.1:8b`
- If your model has a different name, edit line 18 of `pocket_avatar.py`:
  ```python
  OLLAMA_MODEL = "your-model-name-here"
  ```

**Expression engine shows response but otter doesn't react:**
- Check that the WebSocket connected: look for `[Pocket] Connected to avatar ✓`
- Try restarting both the avatar and the expression engine

**Otter is behind other windows:**
- This shouldn't happen (it's set to always-on-top) but if it does, click the otter's terminal window and the otter should pop back to front

---

*Pocket Avatar v1.0 | Built for the user's Pocket companion project*
