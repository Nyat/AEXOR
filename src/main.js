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

let lastValidPosition = null;
let savePositionTimer = null;

function getWindowStatePath() {
  const fs = require('fs');
  const appDataStr = process.env.APPDATA || (process.platform === 'darwin' ? process.env.HOME + '/Library/Preferences' : process.env.HOME + '/.local/share');
  const aexorDir = path.join(appDataStr, 'AEXOR HUB');
  if (!fs.existsSync(aexorDir)) {
    fs.mkdirSync(aexorDir, { recursive: true });
  }
  return path.join(aexorDir, 'window-state.json');
}

function isValidWindowPosition(x, y, width = 1200, height = 800) {
  if (typeof x !== 'number' || typeof y !== 'number' || !Number.isFinite(x) || !Number.isFinite(y)) {
    return false;
  }
  if (x <= -10000 || y <= -10000) {
    return false;
  }
  try {
    const { screen } = require('electron');
    const displays = screen.getAllDisplays();
    return displays.some((d) => {
      const wa = d.workArea;
      const overlapX = Math.min(x + width, wa.x + wa.width) - Math.max(x, wa.x);
      const titleBarVisible = y >= wa.y - 10 && y + 40 <= wa.y + wa.height;
      return overlapX >= 120 && titleBarVisible;
    });
  } catch (e) {
    return false;
  }
}

function loadWindowPosition(width = 1200, height = 800) {
  try {
    const fs = require('fs');
    const statePath = getWindowStatePath();
    if (!fs.existsSync(statePath)) return null;
    const raw = fs.readFileSync(statePath, 'utf-8');
    const data = JSON.parse(raw);
    if (data && isValidWindowPosition(data.x, data.y, width, height)) {
      const pos = { x: Math.round(data.x), y: Math.round(data.y) };
      lastValidPosition = pos;
      return pos;
    }
  } catch (e) {}
  return null;
}

function flushWindowPosition(win) {
  try {
    if (savePositionTimer) {
      clearTimeout(savePositionTimer);
      savePositionTimer = null;
    }
    if (win && !win.isDestroyed() && !win.isMinimized() && !win.isMaximized()) {
      const [curX, curY] = win.getPosition();
      if (isValidWindowPosition(curX, curY)) {
        lastValidPosition = { x: Math.round(curX), y: Math.round(curY) };
      }
    }
    if (lastValidPosition && isValidWindowPosition(lastValidPosition.x, lastValidPosition.y)) {
      const fs = require('fs');
      fs.writeFileSync(getWindowStatePath(), JSON.stringify(lastValidPosition), 'utf-8');
    }
  } catch (e) {}
}

function scheduleSaveWindowPosition(win) {
  if (win && !win.isDestroyed() && !win.isMinimized() && !win.isMaximized()) {
    const [curX, curY] = win.getPosition();
    if (isValidWindowPosition(curX, curY)) {
      lastValidPosition = { x: Math.round(curX), y: Math.round(curY) };
    }
  }
  if (savePositionTimer) clearTimeout(savePositionTimer);
  savePositionTimer = setTimeout(() => {
    flushWindowPosition(win);
  }, 400);
}

function createWindow() {
  const WIN_WIDTH = 1200;
  const WIN_HEIGHT = 800;
  const savedPos = loadWindowPosition(WIN_WIDTH, WIN_HEIGHT);

  const winOptions = {
    width: WIN_WIDTH,
    height: WIN_HEIGHT,
    frame: false,
    transparent: true,
    webPreferences: {
      preload: path.join(app.getAppPath(), 'src/preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  };

  if (savedPos) {
    winOptions.x = savedPos.x;
    winOptions.y = savedPos.y;
  }

  const win = new BrowserWindow(winOptions);

  if (!lastValidPosition && !win.isMinimized()) {
    const [initX, initY] = win.getPosition();
    if (isValidWindowPosition(initX, initY, WIN_WIDTH, WIN_HEIGHT)) {
      lastValidPosition = { x: Math.round(initX), y: Math.round(initY) };
    }
  }

  win.on('moved', () => scheduleSaveWindowPosition(win));
  win.on('close', () => flushWindowPosition(win));

  if (isDev) {
    win.loadURL('http://localhost:3000');
  } else {
    win.loadFile(path.join(app.getAppPath(), 'web/dist/index.html'));
  }
}

function startPythonWorker(isPurgeRestart = false) {
  const fs = require('fs');
  const appDataStr = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Preferences' : process.env.HOME + "/.local/share");
  const aexorDir = path.join(appDataStr, 'AEXOR HUB');
  const venvDir = path.join(aexorDir, 'venv');
  const venvPython = process.platform === 'win32' 
      ? path.join(venvDir, 'Scripts', 'python.exe')
      : path.join(venvDir, 'bin', 'python');

  if (!fs.existsSync(aexorDir)) {
      fs.mkdirSync(aexorDir, { recursive: true });
  }

  let workerPath = path.join(app.getAppPath(), 'worker', 'main.py');
  if (app.isPackaged) {
    workerPath = workerPath.replace('app.asar', 'app.asar.unpacked');
  }
  
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
          if (isPurgeRestart && json.type === 'log' && (json.text.includes('NEURAL_WORKER_ONLINE') || json.text.includes('HEIC_KERNEL_LOADED'))) {
            return;
          }
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
    if (!isPurgeRestart) {
      sendLog(`[NEURAL_WORKER]: ATTACHED_TO_STREAM (Isolated Venv)`, 'info');
    }
  }

  function runTargetPython() {
      if (!isPurgeRestart) {
        sendLog(`[MAIN]: INITIATING_NEURAL_UPLINK: ${workerPath}`, 'info');
      }
      const proc = spawn(venvPython, ['-u', workerPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
        env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' }
      });
      proc.on('error', (err) => {
          sendLog(`SPAWN_FATAL: Isolated Python engine failed to launch. ${err.message}`, 'error');
      });
      setupWorkerListeners(proc);
  }

  // 1. Check if Venv exists
  if (!fs.existsSync(venvPython)) {
      sendLog(`[SYSTEM]: INITIALIZING NEURAL KERNEL (VENV CREATION)... PLEASE WAIT.`, 'info');
      
      const { exec } = require('child_process');
      // Find a system python to create the venv
      exec(`python -m venv "${venvDir}"`, (error, stdout, stderr) => {
           if (error) {
               sendLog(`[SYSTEM_CRITICAL]: Failed to create VENV! ${stderr}`, 'error');
           } else {
               sendLog(`[SYSTEM]: VENV Created. Installing core kernel packages...`, 'info');
               const pipExe = process.platform === 'win32' ? path.join(venvDir, 'Scripts', 'pip.exe') : path.join(venvDir, 'bin', 'pip');
               exec(`"${pipExe}" install psutil requests`, (err3) => {
                  if (err3) {
                      sendLog(`[SYSTEM_CRITICAL]: Failed to install core packages!`, 'error');
                  } else {
                      sendLog(`[SYSTEM]: KERNEL INITIALIZED SUCCESSFULLY.`, 'info');
                      runTargetPython();
                  }
               });
           }
      });
  } else {
      runTargetPython();
  }
}

app.whenReady().then(() => {
  isDev = !app.isPackaged;

  // Register IPC Handlers
  ipcMain.handle('select-file', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'All Supported Assets', extensions: ['jpg', 'png', 'webp', 'jpeg', 'heic', 'heif', 'bmp', 'tiff', 'pdf', 'mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v', 'mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac'] },
        { name: 'Images & Documents', extensions: ['jpg', 'png', 'webp', 'jpeg', 'heic', 'heif', 'bmp', 'tiff', 'pdf'] },
        { name: 'Video & Audio', extensions: ['mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v', 'mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac'] }
      ]
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
    if (args && args.action === 'PURGE_MEMORY') {
      if (isProcessing || taskQueue.length > 0) {
        return { status: 'ERROR', message: 'Cannot purge memory while a task is active.' };
      }
      try {
        if (pythonProcess) {
          const oldProc = pythonProcess;
          pythonProcess = null;
          oldProc.removeAllListeners();
          if (oldProc.stdout) oldProc.stdout.removeAllListeners();
          if (oldProc.stderr) oldProc.stderr.removeAllListeners();
          oldProc.kill();
        }
        startPythonWorker(true);
        const w = BrowserWindow.getAllWindows()[0];
        if (w && w.webContents) {
          w.webContents.session.clearCache().catch(() => {});
        }
        return { status: 'SUCCESS', message: 'NEURAL_MEMORY_PURGED: Aexor VRAM & RAM buffers released.' };
      } catch (e) {
        return { status: 'ERROR', message: `MEMORY_PURGE_FAILED: ${e.message}` };
      }
    }

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
      scheduleSaveWindowPosition(win);
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
