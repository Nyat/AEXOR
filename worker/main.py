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
from engines.image_engine import handle_format_converter, handle_image_compressor, handle_photo_resizer
from engines.neural_engine import handle_upscaler, handle_bg_remover
from engines.social_engine import handle_insta_downloader

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

# --- NEURAL DISPATCH MAP ---
NEURAL_HANDLERS = {
    "AI_UPSCALER": handle_upscaler,
    "BG_REMOVER": handle_bg_remover,
    "FORMAT_CONVERTER": handle_format_converter,
    "IMAGE_COMPRESSOR": handle_image_compressor,
    "INSTA_DOWNLOADER": handle_insta_downloader,
    "PHOTO_RESIZER": handle_photo_resizer,
    "PING": lambda _: {"status": "SUCCESS", "message": "PONG", "version": "V0.18.9-GUARDIAN"}
}

def process_command(cmd_data):
    action = cmd_data.get("action")
    payload = cmd_data.get("payload", {})
    
    try:
        handler = NEURAL_HANDLERS.get(action)
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
