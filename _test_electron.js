const el = require('electron');
console.log('Type:', typeof el);
console.log('Is string?:', typeof el === 'string');
if (typeof el === 'string') {
  console.log('Electron returned path string:', el);
  console.log('This means electron binary is broken or not loading main process properly');
} else {
  console.log('app:', el.app);
}
process.exit(0);
