import sys
import json
import os
import threading
import psutil
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Unified Utilities and Asset Management
from utils import log_event, IO_POOL, ensure_cuda_dlls

# Engines are imported lazily within the neural dispatch map to ensure <1s startup time


# Pre-execution: Hardware Calibration & Platform Support
if sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass


def detect_gpu_vendor():
    """
    Detect dedicated GPU vendor ('nvidia' or 'amd'), ignoring integrated graphics
    whenever a discrete GPU is present.
    """
    # 1. Check NVIDIA first via nvidia-smi (NVIDIA GPUs in desktop/laptop systems are discrete)
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip().splitlines()
        if out and out[0].strip():
            return "nvidia", out[0].strip()
    except Exception:
        pass

    # 2. Enumerate Windows display adapters via Registry to distinguish discrete vs integrated
    if sys.platform == "win32":
        try:
            import winreg
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            adapters = []
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(k, i)
                    i += 1
                    if not sub.isdigit():
                        continue
                    sk = winreg.OpenKey(k, sub)
                    desc = str(winreg.QueryValueEx(sk, "DriverDesc")[0]).strip()
                    prov = ""
                    try:
                        prov = str(winreg.QueryValueEx(sk, "ProviderName")[0]).strip()
                    except Exception:
                        pass
                    adapters.append((desc, prov))
                except OSError:
                    break

            # Filter out virtual display drivers
            real_adapters = [
                (d, p) for d, p in adapters
                if not any(v in d.lower() for v in ("virtual", "basic", "remote", "indirect", "amyuni", "parsec"))
            ]

            # Pass 2A: Look for any NVIDIA adapter
            for d, p in real_adapters:
                if "nvidia" in d.lower() or "nvidia" in p.lower():
                    return "nvidia", d

            # Pass 2B: Look for discrete AMD Radeon (RX / PRO / XT / Vega / VII, excluding plain integrated 'AMD Radeon(TM) Graphics')
            for d, p in real_adapters:
                dl = d.lower()
                if ("amd" in dl or "radeon" in dl or "advanced micro" in p.lower()):
                    if any(tag in dl for tag in (" rx ", "radeon rx", "radeon pro", " xt", " xtx", "vega", "radeon vii", "w6", "w7")):
                        return "amd", d

            # Pass 2C: If no discrete GPU exists, allow AMD / DirectML-capable GPU
            for d, p in real_adapters:
                dl = d.lower()
                if "amd" in dl or "radeon" in dl or "advanced micro" in p.lower():
                    return "amd", d
        except Exception:
            pass

    return "amd", "DirectML GPU Core"


GPU_VENDOR, DETECTED_GPU_NAME = detect_gpu_vendor()


# Global Neural Telemetry
def send_telemetry():
    while True:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            ram_percent = mem.percent
            ram_mb = int(mem.used / (1024 * 1024))
            
            gpu = 0
            vram_mb = 0
            gpu_name = DETECTED_GPU_NAME or "Neural GPU Core"
            
            if GPU_VENDOR == "nvidia":
                try:
                    res_meta = subprocess.check_output(
                        ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,name", "--format=csv,noheader,nounits"],
                        encoding="utf-8", stderr=subprocess.DEVNULL
                    ).strip().split(",")
                    gpu = int(res_meta[0].strip())
                    vram_mb = int(res_meta[1].strip())
                    gpu_name = res_meta[2].strip()
                except Exception:
                    pass
            
            print(json.dumps({
                "type": "telemetry", "cpu": cpu, "ram": ram_percent, "ram_mb": ram_mb, 
                "gpu": gpu, "vram_mb": vram_mb, "gpu_name": gpu_name
            }), flush=True)
        except Exception:
            pass
        time.sleep(2)

# Start Telemetry
threading.Thread(target=send_telemetry, daemon=True).start()

import importlib.util

DYNAMIC_MODULES = {}

def load_dynamic_handler(action):
    if action == "AUDIO_SEPERATOR":
        action = "AUDIO_SEPARATOR"
    # Try dynamic load from APPDATA (synced with bundled modules)
    appdata = os.environ.get('APPDATA')
    bundled_mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules', f"{action}.py"))
    if appdata:
        mod_dir = os.path.join(appdata, 'AEXOR HUB', 'modules')
        mod_path = os.path.join(mod_dir, f"{action}.py")
        target_path = mod_path
        if os.path.exists(mod_path) and os.path.exists(bundled_mod):
            try:
                with open(bundled_mod, "rb") as fb, open(mod_path, "rb") as fm:
                    if fb.read() != fm.read():
                        try:
                            import shutil
                            shutil.copy2(bundled_mod, mod_path)
                        except Exception:
                            target_path = bundled_mod
            except Exception:
                pass
        elif not os.path.exists(mod_path) and os.path.exists(bundled_mod):
            target_path = bundled_mod

        if os.path.exists(target_path):
            try:
                mtime = os.path.getmtime(target_path)
                cached = DYNAMIC_MODULES.get(action)
                if cached and cached[0] == mtime and cached[1] == target_path:
                    return cached[2].handle
                spec = importlib.util.spec_from_file_location(action, target_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                DYNAMIC_MODULES[action] = (mtime, target_path, module)
                return module.handle
            except Exception as e:
                log_event(f"DYNAMIC_LOAD_FAIL [{action}]: {e}", level="error")
                
    # Fallback to local static modules
    try:
        if action == "AI_UPSCALER":
            from engines.neural_engine import handle_upscaler; return handle_upscaler
        elif action == "BG_REMOVER":
            from engines.neural_engine import handle_bg_remover; return handle_bg_remover
        elif action == "FORMAT_CONVERTER":
            from engines.image_engine import handle_format_converter; return handle_format_converter
        elif action == "IMAGE_COMPRESSOR":
            from engines.image_engine import handle_image_compressor; return handle_image_compressor
        elif action == "INSTA_DOWNLOADER":
            from engines.social_engine import handle_insta_downloader; return handle_insta_downloader
        elif action == "PHOTO_RESIZER":
            from engines.image_engine import handle_photo_resizer; return handle_photo_resizer
    except Exception as e:
        log_event(f"FALLBACK_LOAD_FAIL [{action}]: {e}", level="error")
    return None

import urllib.request

def _run_pip_streaming(cmd):
    """Run a pip command with real-time log streaming. Returns exit code."""
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    for line in iter(process.stdout.readline, ''):
        stripped = line.strip()
        if stripped:
            log_event(stripped, level="progress")
    process.stdout.close()
    return process.wait()


def _detect_best_cuda_config(default_index, include_audio=False):
    """Detect user's NVIDIA GPU compute capability & driver to pick the exact compatible PyTorch CUDA wheel index."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,compute_cap,driver_version", "--format=csv,noheader"],
            encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip().splitlines()[0]
        parts = [p.strip() for p in out.split(",")]
        gpu_name = parts[0] if len(parts) > 0 else "Unknown NVIDIA GPU"
        cc = float(parts[1]) if len(parts) > 1 else 8.6
        drv_str = parts[2].split(".")[0] if len(parts) > 2 else "570"
        drv_major = int(drv_str) if drv_str.isdigit() else 570

        if cc < 7.5:
            # GTX 10-series (Pascal sm_61) / Maxwell: requires cu121 and torch<2.5
            idx = "https://download.pytorch.org/whl/cu121"
            pkgs = ["torch==2.4.1+cu121", "torchvision==0.19.1+cu121"]
            if include_audio:
                pkgs.append("torchaudio==2.4.1+cu121")
            profile = "cu121 (Legacy Pascal/Maxwell)"
        elif cc >= 10.0 or drv_major >= 570:
            # RTX 50-series (Blackwell sm_120) or modern driver
            idx = "https://download.pytorch.org/whl/cu128"
            pkgs = ["torch", "torchvision"] + (["torchaudio"] if include_audio else [])
            profile = "cu128"
        elif drv_major >= 560:
            idx = "https://download.pytorch.org/whl/cu126"
            pkgs = ["torch", "torchvision"] + (["torchaudio"] if include_audio else [])
            profile = "cu126"
        elif drv_major >= 550:
            idx = "https://download.pytorch.org/whl/cu124"
            pkgs = ["torch", "torchvision"] + (["torchaudio"] if include_audio else [])
            profile = "cu124"
        else:
            idx = "https://download.pytorch.org/whl/cu121"
            pkgs = ["torch==2.5.1+cu121", "torchvision==0.20.1+cu121"]
            if include_audio:
                pkgs.append("torchaudio==2.5.1+cu121")
            profile = "cu121"

        log_event(f"[SYSTEM] NVIDIA GPU Detected: {gpu_name} (CC {cc}, Driver {drv_major}) -> Profile: {profile}", level="info")
        return idx, pkgs
    except Exception:
        base_pkgs = ["torch", "torchvision"] + (["torchaudio"] if include_audio else [])
        return default_index or "https://download.pytorch.org/whl/cu128", base_pkgs


def handle_ecosystem(action, payload):
    appdata = os.environ.get('APPDATA')
    mod_dir = os.path.join(appdata, 'AEXOR HUB', 'modules') if appdata else ""
    if not mod_dir:
        return {"status": "ERROR", "message": "APPDATA env missing"}
    os.makedirs(mod_dir, exist_ok=True)

    # ── INSTALL_MODULE: Copy from bundled modules first (offline/pre-push safe), fallback to URL ──
    if action == "INSTALL_MODULE":
        mod_id = payload.get("id")
        if mod_id == "AUDIO_SEPERATOR":
            mod_id = "AUDIO_SEPARATOR"
        url = payload.get("url")
        bundled_mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules', f"{mod_id}.py"))
        try:
            if os.path.exists(bundled_mod):
                import shutil
                shutil.copy2(bundled_mod, os.path.join(mod_dir, f"{mod_id}.py"))
                log_event(f"[SYSTEM] Module script {mod_id}.py synchronized from local bundle.", level="info")
                return {"status": "SUCCESS", "message": f"{mod_id} module file established"}
            elif url:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    content = response.read()
                with open(os.path.join(mod_dir, f"{mod_id}.py"), "wb") as f:
                    f.write(content)
                log_event(f"[SYSTEM] Module script {mod_id}.py downloaded.", level="info")
                return {"status": "SUCCESS", "message": f"{mod_id} module file established"}
            return {"status": "ERROR", "message": f"Module source not found for {mod_id}"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # ── UNINSTALL_MODULE: Delete .py file ONLY ──
    if action == "UNINSTALL_MODULE":
        mod_id = payload.get("id")
        py_path = os.path.join(mod_dir, f"{mod_id}.py")
        if os.path.exists(py_path):
            try:
                os.remove(py_path)
            except Exception:
                pass
        log_event(f"[SYSTEM] Module {mod_id} removed from workspace.", level="info")
        return {"status": "SUCCESS", "message": f"{mod_id} unlinked"}

    # ── INSTALL_DEP: Install a single dependency group with vendor-aware GPU resolution ──
    if action == "INSTALL_DEP":
        dep_id = payload.get("dep_id", "unknown")
        packages = list(payload.get("packages", []))
        extra_index = payload.get("extra_index", "")
        force_reinstall = payload.get("force_reinstall", False)

        if not packages:
            return {"status": "ERROR", "message": "No packages specified"}

        vendor, gpu_title = detect_gpu_vendor()

        def _is_pkg_installed(pkg_spec):
            import importlib.metadata
            base_pkg = pkg_spec.split("==")[0].split(">=")[0].split("<=")[0].strip()
            for candidate in (base_pkg, base_pkg.replace("-", "_"), base_pkg.replace("_", "-")):
                try:
                    importlib.metadata.version(candidate)
                    return True
                except importlib.metadata.PackageNotFoundError:
                    pass
            return False

        # ── Vendor-specific GPU acceleration resolution ──
        if dep_id == "gpu_engine":
            log_event(f"[SYSTEM] Dedicated GPU Target: {gpu_title} ({vendor.upper()})", level="info")

            # Case 1: ONNX Runtime GPU modules (BG_REMOVER, NEURAL_OCR)
            if any(p.startswith("onnxruntime") for p in packages):
                chk_ort = subprocess.run(
                    [sys.executable, "-c", "from utils import ensure_cuda_dlls; ensure_cuda_dlls(); import onnxruntime as ort; print(','.join(ort.get_available_providers()))"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                prov_out = chk_ort.stdout.strip() if chk_ort.returncode == 0 else ""

                if vendor == "nvidia":
                    if "CUDAExecutionProvider" in prov_out and _is_pkg_installed("nvidia-cublas-cu12") and _is_pkg_installed("nvidia-cudnn-cu12"):
                        log_event("[SYSTEM] NVIDIA CUDA ONNX Runtime already active — skipping download.", level="info")
                        return {"status": "SUCCESS", "message": f"{dep_id} installed"}

                    for conflict_pkg in ("onnxruntime", "onnxruntime-directml"):
                        if _is_pkg_installed(conflict_pkg):
                            subprocess.run(
                                [sys.executable, "-m", "pip", "uninstall", "-y", conflict_pkg],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                            )
                    packages = [p for p in ("onnxruntime-gpu", "nvidia-cublas-cu12", "nvidia-cudnn-cu12") if not _is_pkg_installed(p)]
                    if not packages or "CUDAExecutionProvider" not in prov_out:
                        packages = ["onnxruntime-gpu", "nvidia-cublas-cu12", "nvidia-cudnn-cu12"]
                    extra_index = ""
                    force_reinstall = False
                else:
                    if "DmlExecutionProvider" in prov_out and not _is_pkg_installed("onnxruntime") and not _is_pkg_installed("onnxruntime-gpu"):
                        log_event("[SYSTEM] AMD DirectML ONNX Runtime already active — skipping download.", level="info")
                        return {"status": "SUCCESS", "message": f"{dep_id} installed"}

                    for conflict_pkg in ("onnxruntime", "onnxruntime-gpu"):
                        if _is_pkg_installed(conflict_pkg):
                            subprocess.run(
                                [sys.executable, "-m", "pip", "uninstall", "-y", conflict_pkg],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                            )
                    packages = ["onnxruntime-directml"]
                    extra_index = ""
                    force_reinstall = False

            # Case 2: PyTorch GPU modules (AI_UPSCALER, AUDIO_SEPARATOR)
            elif "torch" in packages:
                include_audio = "torchaudio" in packages
                if vendor == "nvidia":
                    extra_index, cuda_pkgs = _detect_best_cuda_config(extra_index, include_audio=include_audio)
                    chk_installed = subprocess.run(
                        [sys.executable, "-c", "import torch; print(torch.__version__)"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    if chk_installed.returncode == 0:
                        ver = chk_installed.stdout.strip()
                        has_audio_ok = True
                        if include_audio:
                            chk_aud = subprocess.run([sys.executable, "-c", "import torchaudio"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            has_audio_ok = (chk_aud.returncode == 0)
                        if "+cu" in ver and has_audio_ok:
                            log_event(f"[SYSTEM] NVIDIA CUDA PyTorch ({ver}) already active — skipping download.", level="info")
                            return {"status": "SUCCESS", "message": f"{dep_id} installed"}
                        elif "+cu" in ver and include_audio and not has_audio_ok:
                            # Torch CUDA is already installed! Only install torchaudio without touching torch/torchvision!
                            audio_pkg = [p for p in cuda_pkgs if p.startswith("torchaudio")] or ["torchaudio"]
                            log_event(f"[SYSTEM] CUDA PyTorch ({ver}) found. Installing missing {audio_pkg[0]} only...", level="info")
                            cmd = [sys.executable, "-m", "pip", "install", "--default-timeout=1000"] + audio_pkg + ["--index-url", extra_index]
                            rc = _run_pip_streaming(cmd)
                            if rc != 0:
                                return {"status": "ERROR", "message": f"pip exited with code {rc}"}
                            ensure_cuda_dlls()
                            return {"status": "SUCCESS", "message": f"{dep_id} installed"}
                        else:
                            log_event(f"[SYSTEM] Upgrading CPU PyTorch ({ver}) to NVIDIA CUDA acceleration...", level="info")
                            cmd = [
                                sys.executable, "-m", "pip", "install", "--default-timeout=1000",
                                "--force-reinstall", "--no-deps"
                            ] + cuda_pkgs + ["--index-url", extra_index]
                            try:
                                rc = _run_pip_streaming(cmd)
                                if rc != 0:
                                    raise Exception(f"pip exited with code {rc}")
                                ensure_cuda_dlls()
                                log_event(f"[SYSTEM] Dependency {dep_id} established successfully.", level="info")
                                return {"status": "SUCCESS", "message": f"{dep_id} installed"}
                            except Exception as e:
                                return {"status": "ERROR", "message": str(e)}
                    else:
                        packages = cuda_pkgs
                        force_reinstall = False
                else:
                    # AMD GPU -> torch-directml
                    amd_pkgs = ["torch", "torchvision", "torch-directml"] + (["torchaudio"] if include_audio else [])
                    missing_amd = [p for p in amd_pkgs if not _is_pkg_installed(p)]
                    if not missing_amd:
                        log_event("[SYSTEM] AMD DirectML PyTorch already active — skipping download.", level="info")
                        return {"status": "SUCCESS", "message": f"{dep_id} installed"}
                    packages = missing_amd
                    extra_index = ""
                    force_reinstall = False

            # Case 3: CTranslate2 / Whisper GPU module (AUTO_SUBTITLER)
            elif any("nvidia-" in p or "ctranslate2" in p for p in packages):
                target_pkgs = ["ctranslate2", "nvidia-cublas-cu12", "nvidia-cudnn-cu12"] if vendor == "nvidia" else ["ctranslate2"]
                missing_ct2 = [p for p in target_pkgs if not _is_pkg_installed(p)]
                if not missing_ct2:
                    log_event(f"[SYSTEM] {dep_id} packages already active — skipping download.", level="info")
                    return {"status": "SUCCESS", "message": f"{dep_id} installed"}
                packages = missing_ct2
                extra_index = ""
                force_reinstall = False

        else:
            # ── Standard Library Dependency (LIBS): Skip any package already installed ──
            missing_pkgs = [p for p in packages if not _is_pkg_installed(p)]
            if not missing_pkgs:
                log_event(f"[SYSTEM] Dependency {dep_id} ({', '.join(packages)}) already satisfied — skipping download.", level="info")
                return {"status": "SUCCESS", "message": f"{dep_id} installed"}
            packages = missing_pkgs
            force_reinstall = False

        if any("rapidocr" in p for p in packages):
            # Prevent rapidocr-onnxruntime from pulling CPU 'onnxruntime' over our GPU onnxruntime-gpu / onnxruntime-directml!
            prereq_pkgs = ["pyclipper", "numpy", "six", "Shapely", "PyYAML", "Pillow", "opencv-python-headless"]
            missing_pre = [p for p in prereq_pkgs if not _is_pkg_installed(p)]
            if missing_pre:
                _run_pip_streaming([sys.executable, "-m", "pip", "install", "--default-timeout=1000"] + missing_pre)
            rc = _run_pip_streaming([sys.executable, "-m", "pip", "install", "--default-timeout=1000", "--no-deps", "rapidocr-onnxruntime"])
            if rc != 0:
                return {"status": "ERROR", "message": f"pip exited with code {rc}"}
            ensure_cuda_dlls()
            log_event(f"[SYSTEM] Dependency {dep_id} established successfully.", level="info")
            return {"status": "SUCCESS", "message": f"{dep_id} installed"}

        log_event(f"[SYSTEM] Installing missing packages for {dep_id}: {', '.join(packages)}...", level="info")
        cmd = [sys.executable, "-m", "pip", "install", "--default-timeout=1000"]
        if force_reinstall:
            cmd.append("--force-reinstall")
        cmd += packages
        if extra_index:
            cmd += ["--index-url", extra_index]

        try:
            rc = _run_pip_streaming(cmd)
            if rc != 0:
                raise Exception(f"pip exited with code {rc}")

            # Only if rapidocr-onnxruntime or rembg pulled CPU 'onnxruntime' over our GPU provider, remove ONLY the CPU 'onnxruntime' metadata/package if needed
            if any("rapidocr" in p or "rembg" in p for p in packages):
                chk_after = subprocess.run(
                    [sys.executable, "-c", "from utils import ensure_cuda_dlls; ensure_cuda_dlls(); import onnxruntime as ort; print(','.join(ort.get_available_providers()))"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                prov_after = chk_after.stdout.strip() if chk_after.returncode == 0 else ""
                if vendor == "nvidia" and _is_pkg_installed("onnxruntime-gpu") and "CUDAExecutionProvider" not in prov_after:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "uninstall", "-y", "onnxruntime", "onnxruntime-directml"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    _run_pip_streaming([sys.executable, "-m", "pip", "install", "--default-timeout=1000", "--force-reinstall", "--no-deps", "onnxruntime-gpu"])
                elif vendor == "amd" and _is_pkg_installed("onnxruntime-directml") and "DmlExecutionProvider" not in prov_after:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "uninstall", "-y", "onnxruntime", "onnxruntime-gpu"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    _run_pip_streaming([sys.executable, "-m", "pip", "install", "--default-timeout=1000", "--force-reinstall", "--no-deps", "onnxruntime-directml"])

            ensure_cuda_dlls()
            log_event(f"[SYSTEM] Dependency {dep_id} established successfully.", level="info")
            return {"status": "SUCCESS", "message": f"{dep_id} installed"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # ── UNINSTALL_DEP: Remove a single dependency group ──
    if action == "UNINSTALL_DEP":
        dep_id = payload.get("dep_id", "unknown")
        packages = list(payload.get("packages", []))

        if not packages:
            return {"status": "ERROR", "message": "No packages specified"}

        if dep_id == "gpu_engine" and any(p.startswith("onnxruntime") for p in packages):
            packages = ["onnxruntime", "onnxruntime-gpu", "onnxruntime-directml"]

        log_event(f"[SYSTEM] Removing dependency: {dep_id}...", level="info")
        cmd = [sys.executable, "-m", "pip", "uninstall", "-y"] + packages

        try:
            rc = _run_pip_streaming(cmd)
            log_event(f"[SYSTEM] Dependency {dep_id} removed.", level="info")
            return {"status": "SUCCESS", "message": f"{dep_id} uninstalled"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # ── CHECK_NVIDIA / GPU INFO: Probe dedicated GPU vendor ──
    if action == "CHECK_NVIDIA":
        vendor, gpu_title = detect_gpu_vendor()
        return {
            "status": "SUCCESS",
            "has_nvidia": (vendor == "nvidia"),
            "gpu_vendor": vendor,
            "gpu_name": gpu_title
        }

    return {"status": "ERROR", "message": "Unknown ecosystem command"}


def process_command(cmd_data):
    action = cmd_data.get("action")
    payload = cmd_data.get("payload", {})

    if action == "PING":
        return {"status": "SUCCESS", "message": "PONG", "version": "V0.18.9-GUARDIAN"}

    if action == "PURGE_MEMORY":
        import gc
        for _, _, mod in list(DYNAMIC_MODULES.values()):
            for attr_name in ("UPSCALERS", "BG_SESSIONS", "_OCR_ENGINE", "_DEMUCS_MODEL", "_WHISPER_MODEL"):
                if hasattr(mod, attr_name):
                    val = getattr(mod, attr_name)
                    if isinstance(val, dict):
                        val.clear()
                    else:
                        setattr(mod, attr_name, None)
        DYNAMIC_MODULES.clear()
        if "engines.neural_engine" in sys.modules:
            ne = sys.modules["engines.neural_engine"]
            if hasattr(ne, "UPSCALERS"): ne.UPSCALERS.clear()
            if hasattr(ne, "BG_SESSIONS"): ne.BG_SESSIONS.clear()
        gc.collect()
        if "torch" in sys.modules:
            try:
                sys.modules["torch"].cuda.empty_cache()
                sys.modules["torch"].cuda.ipc_collect()
            except Exception:
                pass
        return {"status": "SUCCESS", "action": "PURGE_MEMORY", "message": "NEURAL_MEMORY_PURGED: Aexor VRAM & RAM buffers released."}

    ecosystem_actions = [
        "INSTALL_MODULE", "UNINSTALL_MODULE",
        "INSTALL_DEP", "UNINSTALL_DEP",
        "CHECK_NVIDIA"
    ]
    if action in ecosystem_actions:
        res = handle_ecosystem(action, payload)
        res["action"] = action
        return res

    try:
        # Always enforce GPU mode
        payload["device"] = "cuda"
        payload["gpu_vendor"] = GPU_VENDOR
        ensure_cuda_dlls()

        if GPU_VENDOR == "nvidia" and action in ("AI_UPSCALER", "AUDIO_SEPARATOR", "AUDIO_SEPERATOR") and "torch" not in sys.modules:
            chk_cu = subprocess.run(
                [sys.executable, "-c", "import torch; print(torch.__version__)"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if chk_cu.returncode == 0 and "+cu" not in chk_cu.stdout.strip():
                ver = chk_cu.stdout.strip()
                log_event(f"[SYSTEM] CPU PyTorch ({ver}) detected. Upgrading to NVIDIA CUDA build...", level="info")
                idx, pkgs = _detect_best_cuda_config("", include_audio=(action != "AI_UPSCALER"))
                cmd = [
                    sys.executable, "-m", "pip", "install", "--default-timeout=1000",
                    "--force-reinstall", "--no-deps"
                ] + pkgs + ["--index-url", idx]
                _run_pip_streaming(cmd)

        if action in ("NEURAL_OCR", "BG_REMOVER"):
            chk_ort = subprocess.run(
                [sys.executable, "-c", "from utils import ensure_cuda_dlls; ensure_cuda_dlls(); import onnxruntime as ort; print(','.join(ort.get_available_providers()))"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            prov_out = chk_ort.stdout.strip() if chk_ort.returncode == 0 else ""
            if GPU_VENDOR == "nvidia" and "CUDAExecutionProvider" not in prov_out:
                log_event("[SYSTEM] Aligning ONNX Runtime with NVIDIA CUDAExecutionProvider...", level="info")
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", "onnxruntime", "onnxruntime-directml"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                _run_pip_streaming([
                    sys.executable, "-m", "pip", "install", "--default-timeout=1000",
                    "--force-reinstall", "onnxruntime-gpu", "nvidia-cublas-cu12", "nvidia-cudnn-cu12"
                ])
                ensure_cuda_dlls()
                for m_key in list(sys.modules.keys()):
                    if m_key.startswith("onnxruntime") or m_key.startswith("rapidocr") or m_key.startswith("rembg"):
                        del sys.modules[m_key]
            elif GPU_VENDOR == "amd" and "DmlExecutionProvider" not in prov_out:
                log_event("[SYSTEM] Aligning ONNX Runtime with AMD DirectML ExecutionProvider...", level="info")
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", "onnxruntime", "onnxruntime-gpu"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                _run_pip_streaming([
                    sys.executable, "-m", "pip", "install", "--default-timeout=1000",
                    "--force-reinstall", "onnxruntime-directml"
                ])
                for m_key in list(sys.modules.keys()):
                    if m_key.startswith("onnxruntime") or m_key.startswith("rapidocr") or m_key.startswith("rembg"):
                        del sys.modules[m_key]

        handler = load_dynamic_handler(action)
        if handler:
            result = handler(payload)
            result["action"] = action
            return result
        return {"status": "ERROR", "message": f"Unknown sequence: {action}"}
    except Exception as e:
        return {"status": "ERROR", "message": f"NEURAL_DISPATCH_FAILURE: {str(e)}"}

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
        
    while True:
        line = sys.stdin.readline()
        if not line: break
        try:
            cmd_data = json.loads(line)
            result = process_command(cmd_data)
            print(json.dumps(result), flush=True)
        except Exception as e:
            msg = {"status": "ERROR", "message": f"CRITICAL_LOOP_ERROR: {str(e)}"}
            print(json.dumps(msg), flush=True)

if __name__ == "__main__":
    log_event(f"NEURAL_WORKER_ONLINE // GPU_TARGET: {DETECTED_GPU_NAME} ({GPU_VENDOR.upper()})", path="SYSTEM")
    main()
