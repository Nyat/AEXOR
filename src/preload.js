const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  runTask: (args) => ipcRenderer.invoke('run-task', args),
  onTelemetry: (callback) => ipcRenderer.on('telemetry-data', (_event, value) => callback(value)),
  selectFile: () => ipcRenderer.invoke('select-file'),
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  minimize: () => ipcRenderer.send('window-minimize'),
  close: () => ipcRenderer.send('window-close'),
  openPath: (path) => ipcRenderer.send('open-path', path),
  windowDrag: () => ipcRenderer.send('window-drag'),
  windowMove: (coords) => ipcRenderer.send('window-move', coords),
  getThumbnail: (path) => ipcRenderer.invoke('get-thumbnail', path)
});
