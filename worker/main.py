import sys
import json
import os
import threading
import psutil
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Unified Utilities and Asset Management
from utils import log_event, IO_POOL

# Engines are imported lazily within the neural dispatch map to ensure <1s startup time


# Pre-execution: Hardware Calibration & Platform Support
if sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

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
            gpu_name = "Nvidia Neural Core"
            
            try:
                res_meta = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,name", "--format=csv,noheader,nounits"],
                    encoding="utf-8"
                ).strip().split(",")
                gpu = int(res_meta[0].strip())
                vram_mb = int(res_meta[1].strip())
                gpu_name = res_meta[2].strip()
            except: pass
            
            print(json.dumps({
                "type": "telemetry", "cpu": cpu, "ram": ram_percent, "ram_mb": ram_mb, 
                "gpu": gpu, "vram_mb": vram_mb, "gpu_name": gpu_name
            }), flush=True)
        except: pass
        time.sleep(2)

# Start Telemetry
threading.Thread(target=send_telemetry, daemon=True).start()

import importlib.util

def load_dynamic_handler(action):
    # Try dynamic load from APPDATA
    appdata = os.environ.get('APPDATA')
    if appdata:
        mod_dir = os.path.join(appdata, 'AEXOR HUB', 'modules')
        mod_path = os.path.join(mod_dir, f"{action}.py")
        if os.path.exists(mod_path):
            try:
                spec = importlib.util.spec_from_file_location(action, mod_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
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
        elif action == "VIZYON_RESIZER":
            from engines.vizyon_engine import handle_vizyon_resizer; return handle_vizyon_resizer
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


def handle_ecosystem(action, payload):
    appdata = os.environ.get('APPDATA')
    mod_dir = os.path.join(appdata, 'AEXOR HUB', 'modules') if appdata else ""
    if not mod_dir:
        return {"status": "ERROR", "message": "APPDATA env missing"}
    os.makedirs(mod_dir, exist_ok=True)

    # ── INSTALL_MODULE: Download .py file ONLY (no pip) ──
    if action == "INSTALL_MODULE":
        mod_id = payload.get("id")
        url = payload.get("url")
        try:
            if url:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    content = response.read()
                with open(os.path.join(mod_dir, f"{mod_id}.py"), "wb") as f:
                    f.write(content)
                log_event(f"[SYSTEM] Module script {mod_id}.py downloaded.", level="info")
            return {"status": "SUCCESS", "message": f"{mod_id} module file established"}
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

    # ── INSTALL_DEP: Install a single dependency group ──
    if action == "INSTALL_DEP":
        dep_id = payload.get("dep_id", "unknown")
        packages = payload.get("packages", [])
        extra_index = payload.get("extra_index", "")
        force_reinstall = payload.get("force_reinstall", False)

        if not packages:
            return {"status": "ERROR", "message": "No packages specified"}

        log_event(f"[SYSTEM] Installing dependency: {dep_id}...", level="info")
        cmd = [sys.executable, "-m", "pip", "install", "--default-timeout=1000"]
        if force_reinstall:
            cmd.append("--force-reinstall")
        cmd += packages
        if extra_index:
            cmd += ["--extra-index-url", extra_index]

        try:
            rc = _run_pip_streaming(cmd)
            if rc != 0:
                raise Exception(f"pip exited with code {rc}")
            log_event(f"[SYSTEM] Dependency {dep_id} established successfully.", level="info")
            return {"status": "SUCCESS", "message": f"{dep_id} installed"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # ── UNINSTALL_DEP: Remove a single dependency group ──
    if action == "UNINSTALL_DEP":
        dep_id = payload.get("dep_id", "unknown")
        packages = payload.get("packages", [])

        if not packages:
            return {"status": "ERROR", "message": "No packages specified"}

        log_event(f"[SYSTEM] Removing dependency: {dep_id}...", level="info")
        cmd = [sys.executable, "-m", "pip", "uninstall", "-y"] + packages

        try:
            rc = _run_pip_streaming(cmd)
            log_event(f"[SYSTEM] Dependency {dep_id} removed.", level="info")
            return {"status": "SUCCESS", "message": f"{dep_id} uninstalled"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    # ── CHECK_NVIDIA: Probe for NVIDIA GPU presence ──
    if action == "CHECK_NVIDIA":
        try:
            result = subprocess.run(
                ["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            has_nvidia = result.returncode == 0
        except Exception:
            has_nvidia = False
        return {"status": "SUCCESS", "has_nvidia": has_nvidia}

    return {"status": "ERROR", "message": "Unknown ecosystem command"}


def process_command(cmd_data):
    action = cmd_data.get("action")
    payload = cmd_data.get("payload", {})

    if action == "PING":
        return {"status": "SUCCESS", "message": "PONG", "version": "V0.18.9-GUARDIAN"}

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
    log_event("NEURAL_WORKER_ONLINE // AEXOR_HUB_V0.18.9-GUARDIAN", path="SYSTEM")
    main()
