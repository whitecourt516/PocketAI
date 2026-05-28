// preload.js — secure bridge between main process and renderer
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('pocket', {
  // Listen for commands from main process
  onExpression: (cb) => ipcRenderer.on('set-expression', (_, val) => cb(val)),
  onSubtitle:   (cb) => ipcRenderer.on('show-subtitle',  (_, val) => cb(val)),
  onWander:     (cb) => ipcRenderer.on('wander',         (_, val) => cb(val)),
  onDebugState: (callback) => ipcRenderer.on('debug-state', (_event, data) => callback(data)),
  onContent:    (cb) => ipcRenderer.on('show-content',   (_, val) => cb(val)),

  // Send to main process
  closePanel: () => ipcRenderer.send('close-panel'),
});
