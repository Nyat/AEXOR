from PIL import Image
from utils import log_event, IO_POOL

def handle(payload):
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    
    log_event("[PROGRESS: 20]", path=input_path)
    img = Image.open(input_path)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    log_event("[PROGRESS: 60]", path=input_path)
    
    def save_file(img, out_path):
        try: img.save(out_path, quality=100)
        except Exception as e: log_event(f"DISK_ERROR: {e}", level="error", path=input_path)

    IO_POOL.submit(save_file, img, output_path)
    log_event("[PROGRESS: 100]", path=input_path)
    return {"status": "SUCCESS"}
