// ─────────────────────────────────────────────────────────────────────────────
// Pocket Avatar — main.js
// Electron main process
// Handles: transparent window, always-on-top, wandering, output panel,
//          WebSocket server for expression/speech commands from Python
// ─────────────────────────────────────────────────────────────────────────────

const { app, BrowserWindow, screen, ipcMain, globalShortcut } = require('electron');
const path = require('path');
const WebSocket = require('ws');

// ── Config ────────────────────────────────────────────────────────────────────
const CONFIG = {
  avatar: {
    width: 300,
    height: 400,
  },
  outputPanel: {
    width: 480,
    height: 600,
    corner: 'bottom-right',   // options: bottom-right, bottom-left, top-right, top-left
    margin: 20,
  },
  debugPanel: {
    width: 340,
    height: 520,
    corner: 'bottom-left',   // opposite side from output panel
    margin: 20,
  },
  wandering: {
    enabled: true,
    intervalMs: 8000,          // how often to pick a new spot (ms)
    speedMs: 4000,             // how long the move animation takes (ms)
    margin: 80,                // how close to screen edges otter can get (px)
  },
  websocket: {
    port: 7845,                // Python expression engine connects here
  },
  hotkeys: {
    hide: 'Alt+H',             // toggle avatar visibility
    panel: 'Alt+P',            // toggle output panel
  }
};

// ── State ─────────────────────────────────────────────────────────────────────
let avatarWindow = null;
let outputPanelWindow = null;
let debugPanelWindow = null;
let debugPanelVisible = false;
let wss = null;
let wanderTimer = null;
let avatarVisible = true;

// ── Avatar Window ─────────────────────────────────────────────────────────────
function createAvatarWindow() {
  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;

  // Start in center of screen
  const startX = Math.floor(sw / 2 - CONFIG.avatar.width / 2);
  const startY = Math.floor(sh / 2 - CONFIG.avatar.height / 2);

  avatarWindow = new BrowserWindow({
    width: CONFIG.avatar.width,
    height: CONFIG.avatar.height,
    x: startX,
    y: startY,

    // Transparent + frameless = just the otter, no chrome
    transparent: true,
    frame: false,
    hasShadow: false,

    // Always visible above other windows
    alwaysOnTop: true,
    skipTaskbar: true,         // don't show in taskbar
    resizable: false,

    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  avatarWindow.loadFile('renderer/avatar.html');

  // Debug: set POCKET_DEVTOOLS=1 before Start-Avatar.bat to open the renderer console
  if (process.env.POCKET_DEVTOOLS) {
    avatarWindow.webContents.openDevTools({ mode: 'detach' });
  }

  // Click-through when not interacting — mouse clicks pass to windows below
  // Hold Alt to drag the otter manually if needed
  avatarWindow.setIgnoreMouseEvents(true, { forward: true });

  // Allow dragging when mouse is over otter
  avatarWindow.webContents.on('did-finish-load', () => {
    startWandering();
  });

  // Re-assert always on top every 5 seconds (some apps fight for top position)
  setInterval(() => {
    if (avatarWindow && !avatarWindow.isDestroyed()) {
      avatarWindow.setAlwaysOnTop(true, 'screen-saver');
    }
  }, 5000);
}

// ── Output Panel Window ───────────────────────────────────────────────────────
function createOutputPanel() {
  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;
  const { width, height, corner, margin } = CONFIG.outputPanel;

  let x, y;
  switch (corner) {
    case 'bottom-right': x = sw - width - margin;  y = sh - height - margin; break;
    case 'bottom-left':  x = margin;                y = sh - height - margin; break;
    case 'top-right':    x = sw - width - margin;  y = margin;               break;
    case 'top-left':     x = margin;                y = margin;               break;
    default:             x = sw - width - margin;  y = sh - height - margin;
  }

  outputPanelWindow = new BrowserWindow({
    width,
    height,
    x,
    y,
    transparent: true,
    frame: false,
    hasShadow: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    show: false,               // hidden by default, shown when needed
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  outputPanelWindow.loadFile('renderer/panel.html');
}

// ── Debug Panel Window ────────────────────────────────────────────────────────
function createDebugPanel() {
  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;
  const { width, height, corner, margin } = CONFIG.debugPanel;

  let x, y;
  switch (corner) {
    case 'bottom-right': x = sw - width - margin;  y = sh - height - margin; break;
    case 'bottom-left':  x = margin;                y = sh - height - margin; break;
    case 'top-right':    x = sw - width - margin;  y = margin;               break;
    case 'top-left':     x = margin;                y = margin;               break;
    default:             x = margin;                y = sh - height - margin;
  }

  debugPanelWindow = new BrowserWindow({
    width,
    height,
    x,
    y,
    transparent: true,
    frame: false,
    hasShadow: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  debugPanelWindow.loadFile('renderer/debug.html');
}

// ── Wandering Logic ───────────────────────────────────────────────────────────
function startWandering() {
  if (!CONFIG.wandering.enabled) return;

  wanderTimer = setInterval(() => {
    if (!avatarWindow || avatarWindow.isDestroyed()) return;

    const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;
    const m = CONFIG.wandering.margin;

    const newX = Math.floor(Math.random() * (sw - CONFIG.avatar.width - m * 2) + m);
    const newY = Math.floor(Math.random() * (sh - CONFIG.avatar.height - m * 2) + m);

    // Tell the renderer to animate the move (CSS transition handles the smooth movement)
    avatarWindow.webContents.send('wander', { x: newX, y: newY, duration: CONFIG.wandering.speedMs });

    // Actually move the window after the animation completes
    setTimeout(() => {
      if (avatarWindow && !avatarWindow.isDestroyed()) {
        avatarWindow.setPosition(newX, newY, true);
      }
    }, CONFIG.wandering.speedMs);

  }, CONFIG.wandering.intervalMs);
}

function pauseWandering() {
  if (wanderTimer) {
    clearInterval(wanderTimer);
    wanderTimer = null;
  }
}

function resumeWandering() {
  if (!wanderTimer) startWandering();
}

// ── WebSocket Server ──────────────────────────────────────────────────────────
// Python expression engine connects here and sends commands like:
// { type: "expression", value: "happy" }
// { type: "speech", text: "Hello!", subtitle: true }
// { type: "panel", content: "...", contentType: "code" }
// { type: "panel_close" }
// { type: "wander_pause" }   -- while speaking, pause wandering
// { type: "wander_resume" }

function startWebSocketServer() {
  wss = new WebSocket.Server({ port: CONFIG.websocket.port });

  wss.on('listening', () => {
    console.log(`[Pocket] WebSocket server listening on port ${CONFIG.websocket.port}`);
  });

  wss.on('connection', (ws) => {
    console.log('[Pocket] Expression engine connected');

    ws.on('message', (raw) => {
      try {
        const msg = JSON.parse(raw.toString());
        handleCommand(msg);
      } catch (e) {
        console.error('[Pocket] Bad message from expression engine:', e.message);
      }
    });

    ws.on('close', () => {
      console.log('[Pocket] Expression engine disconnected');
    });
  });
}

function handleCommand(msg) {
  if (!avatarWindow || avatarWindow.isDestroyed()) return;

  const msgType = msg.type || msg.command;

  switch (msgType) {

    // Change the otter's expression
    case 'expression':
      avatarWindow.webContents.send('set-expression', msg.value);
      break;

    // Show subtitle text near the otter
    case 'speech':
      avatarWindow.webContents.send('show-subtitle', {
        text: msg.text,
        duration: msg.duration || 4000,
      });
      break;

    // Show content in the output panel
    case 'panel':
      if (outputPanelWindow && !outputPanelWindow.isDestroyed()) {
        outputPanelWindow.webContents.send('show-content', {
          content: msg.content,
          contentType: msg.contentType || 'text',
          title: msg.title || 'Pocket',
        });
        outputPanelWindow.show();
      }
      break;

    // Hide the output panel
    case 'panel_close':
      if (outputPanelWindow && !outputPanelWindow.isDestroyed()) {
        outputPanelWindow.hide();
      }
      break;

    // Pause wandering (e.g. while speaking)
    case 'wander_pause':
      pauseWandering();
      break;

    // Resume wandering
    case 'wander_resume':
      resumeWandering();
      break;

    // Show debug state in debug panel
    case 'debug':
      if (debugPanelWindow && !debugPanelWindow.isDestroyed()) {
        debugPanelWindow.webContents.send('debug-state', msg.state);
        if (!debugPanelVisible) {
          debugPanelWindow.show();
          debugPanelVisible = true;
        }
      }
      break;

    default:
      console.log('[Pocket] Unknown command type:', msg.type || msg.command);
  }
}

// ── Hotkeys ───────────────────────────────────────────────────────────────────
function registerHotkeys() {
  // Alt+H — toggle avatar visibility
  globalShortcut.register(CONFIG.hotkeys.hide, () => {
    if (!avatarWindow || avatarWindow.isDestroyed()) return;
    avatarVisible = !avatarVisible;
    if (avatarVisible) {
      avatarWindow.show();
      resumeWandering();
    } else {
      avatarWindow.hide();
      pauseWandering();
    }
  });

  // Alt+P — toggle output panel
  globalShortcut.register(CONFIG.hotkeys.panel, () => {
    if (!outputPanelWindow || outputPanelWindow.isDestroyed()) return;
    if (outputPanelWindow.isVisible()) {
      outputPanelWindow.hide();
    } else {
      outputPanelWindow.show();
    }
  });

  // Alt+D — toggle debug panel
  globalShortcut.register('Alt+D', () => {
    if (!debugPanelWindow || debugPanelWindow.isDestroyed()) return;
    debugPanelVisible = !debugPanelVisible;
    if (debugPanelVisible) {
      debugPanelWindow.show();
    } else {
      debugPanelWindow.hide();
    }
  });
}

// ── IPC from renderer ─────────────────────────────────────────────────────────
ipcMain.on('close-panel', () => {
  if (outputPanelWindow && !outputPanelWindow.isDestroyed()) {
    outputPanelWindow.hide();
  }
});

// ── App Lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  createAvatarWindow();
  createOutputPanel();
  createDebugPanel();
  startWebSocketServer();
  registerHotkeys();

  console.log('[Pocket] Avatar is running');
  console.log(`[Pocket] Hide/show: ${CONFIG.hotkeys.hide}`);
  console.log(`[Pocket] Panel toggle: ${CONFIG.hotkeys.panel}`);
  console.log(`[Pocket] WebSocket: ws://localhost:${CONFIG.websocket.port}`);
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (wss) wss.close();
});

// Don't quit when all windows are closed (keep running in background)
app.on('window-all-closed', (e) => {
  e.preventDefault();
});
