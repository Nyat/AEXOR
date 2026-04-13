import json
import sys
from concurrent.futures import ThreadPoolExecutor

# Register HEIC/HEIF support globally before any PIL usage
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

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
