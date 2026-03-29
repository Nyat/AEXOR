const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const electronPath = path.join(__dirname, 'node_modules/electron/dist/electron.exe');

if (!fs.existsSync(electronPath)) {
  console.error('ERROR: Electron binary not found at', electronPath);
  process.exit(1);
}

console.log('Launching AEXOR HUB via Electron...');
const child = spawn(electronPath, ['.'], {
  cwd: __dirname,
  stdio: 'inherit',
  detached: true,
  windowsHide: false
});

child.on('error', (err) => {
  console.error('Failed to start Electron:', err);
});

child.unref();
console.log('Electron process spawned. The window should appear shortly.');
process.exit(0);
