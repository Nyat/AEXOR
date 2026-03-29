const { app } = require('electron');
console.log('ELECTRON_APP_OBJECT:', typeof app);
if (app) {
  app.whenReady().then(() => {
    console.log('SUCCESS: Electron is running correctly.');
    app.quit();
  });
} else {
  console.log('FAILURE: app is undefined. Environment is likely Node.js');
  process.exit(1);
}
