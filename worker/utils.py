import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Unified IO Pool for non-blocking disk operations
IO_POOL = ThreadPoolExecutor(max_workers=4)

def log_event(text, level='info', path=None):
    """Unified JSON logging for Electron IPC stability"""
    msg = {"type": "log", "text": str(text), "level": level}
    if path: msg["path"] = path
    # Ensure UTF-8 output
    try:
        print(json.dumps(msg), flush=True)
    except UnicodeEncodeError:
        # Fallback for complex characters
        print(json.dumps(msg, ensure_ascii=True), flush=True)

_ADDED_DLL_DIRS = []

def ensure_cuda_dlls():
    """Register NVIDIA pip wheel and PyTorch bin directories in Windows DLL search path and PATH."""
    if sys.platform != "win32":
        return
    try:
        site_pkgs = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "Lib", "site-packages")
        if not os.path.isdir(site_pkgs):
            import site
            sps = site.getsitepackages()
            site_pkgs = next((p for p in sps if "site-packages" in p), "")
        if not site_pkgs or not os.path.isdir(site_pkgs):
            return

        candidate_dirs = []
        torch_lib = os.path.join(site_pkgs, "torch", "lib")
        if os.path.isdir(torch_lib):
            candidate_dirs.append(torch_lib)

        nvidia_root = os.path.join(site_pkgs, "nvidia")
        if os.path.isdir(nvidia_root):
            for sub in os.listdir(nvidia_root):
                bin_dir = os.path.join(nvidia_root, sub, "bin")
                if os.path.isdir(bin_dir):
                    candidate_dirs.append(bin_dir)

        current_path = os.environ.get("PATH", "")
        new_paths = []
        for d in candidate_dirs:
            if d not in current_path:
                new_paths.append(d)
            if hasattr(os, "add_dll_directory"):
                try:
                    handle = os.add_dll_directory(d)
                    _ADDED_DLL_DIRS.append(handle)
                except Exception:
                    pass
        if new_paths:
            os.environ["PATH"] = os.pathsep.join(new_paths) + os.pathsep + current_path
    except Exception:
        pass

ensure_cuda_dlls()

# Register HEIC/HEIF support globally before any PIL usage
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    log_event("[SYSTEM]: HEIC_KERNEL_LOADED", level='info')
except ImportError:
    log_event("[SYSTEM_WARNING]: HEIC_KERNEL_MISSING - Install manually via Module Manager", level='warning')
except Exception as e:
    log_event(f"[SYSTEM_ERROR]: HEIC_INIT_FAILED: {str(e)}", level='error')
