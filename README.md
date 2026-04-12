# AEXOR HUB // Neural Workstation — V0.18.9-GUARDIAN

> **Portable, modular, GPU-accelerated image processing workstation.** Download once, install only what you need.

---

## ⚡ Features

| Module | Description |
|--------|-------------|
| **AI_UPSCALER** | ESRGAN-based neural upscaling (2×/4×) up to 8K resolution |
| **BG_REMOVER** | AI-powered alpha mask extraction with pixel-perfect edges |
| **FORMAT_CONVERTER** | Batch transcoding: WebP ↔ PNG ↔ JPEG ↔ HEIC |
| **IMAGE_COMPRESSOR** | Adaptive lossy/lossless compression with size guard |
| **INSTA_DOWNLOADER** | Authenticated high-res Instagram media extraction |
| **PHOTO_RESIZER** | Dynamic FIT/FILL canvas resampling (HD → 4K) |

- **Real-time telemetry** — CPU / GPU / VRAM monitoring HUD
- **Granular dependency control** — Install CPU or GPU engines independently per module
- **Dynamic hardware detection** — Auto-selects CUDA when NVIDIA GPU is present

---

## 🚀 Quick Start (Portable)

1. Download the latest **Aexor_Hub_Portable.zip** from [Releases](https://github.com/Nyat/AEXOR/releases)
2. Extract → Run `AEXOR_HUB.exe`
3. Open **MODULE_MANAGER** → Install desired modules
4. Click dependency buttons (CPU_ENGINE / GPU_ACCEL / Libraries) to activate

> No installer needed. No admin privileges. Fully portable.

---

## 🛠️ Architecture

```
Frontend    →  Electron + React (Vite) + TailwindCSS
Backend     →  Python Neural Worker (stdin/stdout IPC)
Modules     →  Dynamic .py scripts downloaded on demand
Dependencies→  Managed per-module via pip (isolated)
Design      →  NIGHT_GLASS visual profile (cyan/fuchsia)
```

### Module Lifecycle

```
Install Module  →  Downloads .py script only (~5 KB)
Install Deps    →  User chooses CPU/GPU/Libraries independently
Execute         →  Module auto-detects available compute backend
Uninstall       →  Clean removal of scripts and dependencies
```

---

## 💻 Development

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- NVIDIA GPU + Drivers (optional, for CUDA acceleration)

### Setup
```bash
git clone https://github.com/Nyat/AEXOR.git
cd AEXOR
npm install
cd web && npm install && npm run build && cd ..
npm run dev
```

### Build Portable
```bash
cd web && npm run build && cd ..
npm run package
# Output: dist/win-unpacked/
```

---

## 🔒 Privacy

All processing happens locally. No images are uploaded anywhere. Session tokens and user data are stored only in your local `%APPDATA%`.

---

## 📝 License

MIT — Use freely.
