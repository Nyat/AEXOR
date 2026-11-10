# AEXOR HUB // Neural Workstation — V0.19.1-GUARDIAN // BETA

> **Portable, modular, 100% GPU-accelerated AI image, document, audio, and video workstation.** Download once, install only the neural engines you need.

---

## ⚡ Studio Modules (16 Specialized Engines)

### 🎨 VISUAL_STUDIO — Image, Vector & Document Intelligence
| Module | Description | Compute / Output |
|--------|-------------|------------------|
| **AI_UPSCALER** | Real-ESRGAN neural super-resolution (`2×` / `4×`) up to 8K resolution | `CUDA` / `DirectML` • `PNG` / `WEBP` / `JPG` |
| **BG_REMOVER** | BiRefNet high-precision alpha-mask extraction for hair, fur & complex edges | `CUDA` / `DirectML` • Transparent `PNG` or `WEBP` |
| **FORMAT_CONVERTER** | Multi-threaded batch image transcoding across modern & mobile formats | `WEBP` ↔ `PNG` ↔ `JPEG` ↔ `HEIC` |
| **IMAGE_COMPRESSOR** | Smart lossy/lossless optimization with automatic size-inflation guard | `WEBP` / `JPEG` / `PNG` / `HEIC` |
| **NEURAL_OCR** | RapidOCR optical character recognition with heuristic cuDNN acceleration | `CUDA` / `DirectML` • `TXT`, `Markdown`, `JSON` |
| **PALETTE_GENERATOR** | Chromatic DNA extraction (`5`, `8`, or `10` dominant colors) | `Studio Card`, `Swatch Grid`, `Card + CSS` |
| **PDF_FORGE** | Document matrix engine: combine images to PDF, render high-DPI pages, or compress | `150` / `300 DPI` • `PDF` ↔ `PNG` |
| **PHOTO_RESIZER** | Dynamic `FIT` (letterbox with `BLACK`/`WHITE`/`TRANSPARENT` fill) & `FILL` resampling | `HD (720p)` → `FHD` → `QHD` → `4K` |
| **VECTOR_TRACER** | High-precision spline raster-to-vector path synthesis (`COLOR` & `BINARY`) | Scalable `.svg` vector geometry |

---

### 🌐 NETWORK_UPLINK — Direct Media Extraction
| Module | Description | Capabilities |
|--------|-------------|--------------|
| **INSTA_DOWNLOADER** | Direct uplink to retrieve uncompressed Instagram Reels, Videos, Photos & Carousels | Optional browser cookie `sessionid` support |
| **MEDIA_DOWNLOADER** | Universal stream harvester (`YouTube`, `X / Twitter`, `TikTok`, `SoundCloud`, `Twitch`, `Vimeo`) | `MP4` (`Best` / `4K` / `1080p` / `720p`), `320k MP3`, `WAV` |

---

### 🎬 MEDIA_STUDIO — GPU Video & Neural Audio Processing
| Module | Description | Compute / Output |
|--------|-------------|------------------|
| **VIDEO_OPTIMIZER** | Hardware-accelerated video compression, 2-pass adaptive `GIF Forge` & `Animated WebP` | `NVIDIA NVENC (h264_nvenc)` + `CUDA Decode` |
| **AUDIO_EXTRACTOR** | High-speed acoustic stream demuxer and lossless video muting | `320kbps MP3`, `16-bit WAV`, `FLAC`, `Mute Video` |
| **AUDIO_SEPARATOR** | Hybrid Transformer Demucs (`htdemucs`) stem isolation & vocal remover | `CUDA` / `DirectML` • `Vocal+Inst`, `Vocals`, `Karaoke`, `4 Stems` |
| **AUTO_SUBTITLER** | Faster-Whisper (`CUDA Float16`) speech & music-vocal transcriber with word-level DTW alignment | `Base` / `Small` / `Medium` • Frame-accurate `SRT` & `TXT` |
| **VOICE_CLEANER** | Spectral acoustic denoiser with studio vocal presence EQ (`Light` / `Studio` / `Aggressive`) | `CUDA` • `WAV`, `320kbps MP3`, or direct `Video Remux` |

---

## 🔥 Core Workstation Highlights

- **Strict GPU-First Architecture** — Neural inference (PyTorch CUDA, ONNX Runtime GPU / DirectML, CTranslate2 Float16) and video encoding (`NVIDIA NVENC`) run directly on your dedicated graphics card.
- **Modular On-Demand Ecosystem (`MODULE_MANAGER`)** — Keep your footprint minimal. Install or uninstall individual module scripts and their compute dependencies (`GPU_ACCEL`, `FASTER_WHISPER`, `DEMUCS_AI`, `RAPID_OCR`, `FFMPEG_CORE`, etc.) with a single click.
- **Real-Time Telemetry & VRAM Guard** — Live `CPU`, `RAM`, `GPU Load`, and `VRAM` allocation telemetry in the sidebar, plus a dedicated **`PURGE_MEMORY`** console trigger to flush cached neural weights and reclaim GPU VRAM on demand.
- **Isolated Self-Healing Runtime** — Automatically provisions an isolated Python virtual environment in `%APPDATA%\AEXOR HUB\venv` with automatic CUDA DLL path resolution.

---

## 🚀 Quick Start (Portable Release)

1. Download the latest **`AEXOR_HUB_V0.19.1_Portable.zip`** from [Releases](https://github.com/Nyat/AEXOR/releases).
2. Extract the archive to any folder and launch **`AEXOR_HUB.exe`**.
3. Open **`MODULE_MANAGER`** (at the bottom of the left sidebar) → Install the modules and GPU/library dependencies you want to use.
4. Drag & drop your files (or paste a link in `NETWORK_UPLINK` modules), configure your preset in the top bar, and click **`INITIALIZE_EXECUTION`**.

> **Zero system pollution:** No Windows installer required. No global Python packages modified. Everything runs inside an isolated portable environment.

---

## 🛠️ Architecture

```text
Frontend     →  Electron + React 19 (TypeScript / Vite) + TailwindCSS
Backend      →  Persistent Python Neural Worker (Asynchronous JSON IPC over stdin/stdout)
Modules      →  Hot-swappable .py modules in modules/ synced with %APPDATA%\AEXOR HUB\modules
Dependencies →  Per-module granular pip management inside isolated %APPDATA%\AEXOR HUB\venv
Visual Theme →  NIGHT_GLASS Cyberpunk HUD (#00F3FF Cyan / #F205FF Neon Pink / #00FF88 Matrix Green)
```

---

## 💻 Development Setup

### Prerequisites
- **Node.js** `v18+`
- **Python** `v3.10 – v3.12`
- **NVIDIA GPU** (CUDA 12.x drivers recommended) or **DirectML-compatible GPU**

### Run in Development Mode
```bash
git clone https://github.com/Nyat/AEXOR.git
cd AEXOR
npm install
cd web && npm install && npm run build && cd ..
npm run dev
```

### Build Portable Package
```bash
cd web && npm run build && cd ..
npm run package
# Unpacked portable build is generated at: dist/win-unpacked/
```

---

## 🔒 Privacy & Security

All AI inference, OCR, transcription, stem separation, and media transcoding execute **100% locally on your hardware**. No media files or telemetry are ever uploaded to external servers. Any optional user credentials (such as your own browser `sessionid` for `INSTA_DOWNLOADER`) are stored strictly in your local machine's `localStorage` and never leave your device.

---

## 📝 License

MIT — Free for personal and commercial use.
