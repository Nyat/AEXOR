const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

const readline = require('readline');
let isDev = false;
let pythonProcess = null;
let taskQueue = [];
let isProcessing = false;
let currentPendingTask = null;

async function processQueue() {
  if (isProcessing || taskQueue.length === 0) return;
  isProcessing = true;
  const task = taskQueue.shift();
  currentPendingTask = task;

  try {
    const response = await new Promise((resolve) => {
      task.internalResolve = resolve;
      
      const timeout = setTimeout(() => {
        if (currentPendingTask === task) {
          currentPendingTask = null;
          resolve({ status: 'ERROR', message: 'IPC_TIMEOUT' });
        }
      }, 300000); 

      // Send to python
      pythonProcess.stdin.write(JSON.stringify(task.args) + '\n');
    });
    
    task.resolve(response);
  } catch (e) {
    task.resolve({ status: 'ERROR', message: String(e) });
  } finally {
    isProcessing = false;
    currentPendingTask = null;
    processQueue();
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false,
    transparent: true,
    webPreferences: {
      preload: path.join(app.getAppPath(), 'src/preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  if (isDev) {
    win.loadURL('http://localhost:3000');
  } else {
    win.loadFile(path.join(app.getAppPath(), 'web/dist/index.html'));
  }
}

function startPythonWorker() {
  const workerPath = path.join(app.getAppPath(), 'worker', 'main.py');
  
  const win = () => BrowserWindow.getAllWindows()[0];
  const sendLog = (text, level = 'info') => {
    const w = win();
    if (w) w.webContents.send('telemetry-data', { type: 'log', text, level });
  };

  function setupWorkerListeners(proc) {
    const rl = readline.createInterface({
      input: proc.stdout,
      terminal: false
    });

    rl.on('line', (line) => {
      if (!line) return;
      try {
        const json = JSON.parse(line);
        const w = win();
        if (json.type === 'telemetry' || json.type === 'log') {
          if (w) w.webContents.send('telemetry-data', json);
        } else if (currentPendingTask && (json.action === currentPendingTask.args.action || json.status)) {
          if (currentPendingTask.internalResolve) {
            currentPendingTask.internalResolve(json);
          }
        }
      } catch (e) {}
    });

    proc.stderr.on('data', (data) => {
      sendLog(data.toString(), 'error');
    });

    pythonProcess = proc;
    sendLog(`[NEURAL_WORKER]: ATTACHED_TO_STREAM`, 'info');
  }

  function attemptSpawn(commands) {
    if (commands.length === 0) {
      sendLog(`CRITICAL: External Neural Workstation (Python 3.10+) not detected. Operation suspended.`, 'error');
      return;
    }

    const cmd = commands.shift();
    const proc = spawn(cmd, ['-u', workerPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true,
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    proc.on('error', (err) => {
      if (err.code === 'ENOENT') {
        attemptSpawn(commands);
      } else {
        sendLog(`SPAWN_FATAL: ${err.message}`, 'error');
      }
    });

    // If starts successfully, stdout will usually have the first line (log or telemetry)
    // We bind listeners and hope it stays alive
    setupWorkerListeners(proc);
  }

  sendLog(`[MAIN]: INITIATING_NEURAL_UPLINK: ${workerPath}`, 'info');
  attemptSpawn(['python', 'python3', 'py']);
}

app.whenReady().then(() => {
  isDev = !app.isPackaged;

  // Register IPC Handlers
  ipcMain.handle('select-file', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections'],
      filters: [{ name: 'Images', extensions: ['jpg', 'png', 'webp', 'jpeg'] }]
    });
    return result.filePaths; // Return all selected paths
  });

  ipcMain.handle('select-directory', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory']
    });
    return result.filePaths[0];
  });

  ipcMain.handle('run-task', async (event, args) => {
    return new Promise((resolve, reject) => {
      if (!pythonProcess) return reject('Worker not running');
      taskQueue.push({ args, resolve, reject });
      processQueue();
    });
  });

  ipcMain.handle('get-thumbnail', async (event, targetPath) => {
    const { nativeImage } = require('electron');
    const fs = require('fs');
    if (!targetPath) return null;
    
    try {
      // 1. Try native async thumbnail generation (Performance optimized)
      try {
        const thumb = await nativeImage.createThumbnailFromPath(targetPath, { width: 120, height: 120 });
        if (thumb && !thumb.isEmpty()) {
          return thumb.toDataURL();
        }
      } catch (e) {
        console.error(`[MAIN]: Native thumbnail failed for: ${targetPath}`);
      }

      // 2. Fallback: Standard createFromPath
      const img = nativeImage.createFromPath(targetPath);
      if (!img.isEmpty()) {
        return img.resize({ width: 120 }).toDataURL();
      }

      // 3. Last Resort: Read directly from FS if it's a small enough image or to verify it exists
      if (fs.existsSync(targetPath)) {
        const stats = fs.statSync(targetPath);
        if (stats.size < 10 * 1024 * 1024) { // Only read if < 10MB to avoid hang
          const data = fs.readFileSync(targetPath);
          const ext = path.extname(targetPath).replace('.', '').toLowerCase();
          return `data:image/${ext === 'jpg' ? 'jpeg' : ext};base64,${data.toString('base64')}`;
        }
      }
      
      return null;
    } catch (e) {
      console.error(`[IPC CRITICAL]: Thumbnail generation error for ${targetPath}:`, e.message);
      return null;
    }
  });

  ipcMain.on('window-minimize', () => {
    const win = BrowserWindow.getFocusedWindow();
    if (win) win.minimize();
  });

  ipcMain.on('window-close', () => {
    const win = BrowserWindow.getFocusedWindow();
    if (win) win.close();
  });

  ipcMain.on('open-path', (event, path) => {
    const { shell } = require('electron');
    shell.openPath(path);
  });

  ipcMain.on('window-drag', () => {
    // This is a placeholder if we wanted to use native drag
  });

  ipcMain.on('window-move', (event, { x, y }) => {
    const { screen } = require('electron');
    const win = BrowserWindow.getFocusedWindow();
    if (win) {
      const { x: cursorX, y: cursorY } = screen.getCursorScreenPoint();
      win.setPosition(cursorX - x, cursorY - y);
    }
  });

  createWindow();
  startPythonWorker();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) pythonProcess.kill();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
