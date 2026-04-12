# AEXOR HUB // Neural Workstation - V0.18.9-GUARDIAN

> **AEXOR HUB // GUARDIAN** is a high-performance neural workstation designed for professional-grade image processing, media acquisition, and hardware-aware task execution. 

---

## 🛰️ Neural Infrastructure Features

- **🛡️ Neural Image Compression (GUARDIAN Engine)**: Lossless and lossy optimization with built-in `Size Guard`. Automatically prevents file bloat and handles adaptive palette quantization for PNG/HEIC/JPEG/WebP.
- **⚡ Neural Upscaling (X2/X4)**: Deep-learning based resolution enhancement with hardware-aware predictive progress bars (TFLOPS calibrated).
- **🔳 Alpha Extraction (BG Remover)**: High-fidelity background removal with neural edge detection.
- **📥 Insta Media Uplink**: Authenticated, robust Instagram media downloader for high-resolution asset acquisition.
- **⚙️ Dynamic Format Transcoder**: Batch format conversion across all industry-standard image extensions including `HEIC` and `WebP`.
- **📊 Real-time Telemetry**: Integrated CPU/GPU/VRAM monitoring with a sleek, minimalist HUD design.

---

## 🛠️ Technical Architecture

- **Frontend**: Electron + React (Vite) + TailwindCSS.
- **Backend**: Python-based Neural Worker (Torch, PIL, Rembg).
- **Communication**: Asynchronous IPC Bridge for non-blocking task execution.
- **Design Aesthetic**: `NIGHT_GLASS` visual profile with high-contrast cyan/fuchsia accent lines.

---

## 🚀 Installation & Local Execution

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- NVIDIA GPU (Optional, but recommended for CUDA acceleration)

### Setup
1. **Clone the Repo**:
   ```bash
   git clone https://github.com/nyat/Aexor-Hub.git
   cd Aexor-Hub
   ```
2. **Install Node Dependencies**:
   ```bash
   npm install
   ```
3. **Setup Python Worker**:
   ```bash
   pip install -r worker/requirements.txt
   ```
4. **Launch Workstation**:
   ```bash
   npm run dev
   ```

## 🔒 Security & Privacy (GUARDIAN)
- **Local Execution**: All neural processing happens on your local machine. No images are ever uploaded to a central server.
- **Size Guard**: Integrated logic to prevent data loss or inefficient storage usage.

---

## 📝 License
This project is currently **Private** and is purely for personal high-fidelity workstation use. 
