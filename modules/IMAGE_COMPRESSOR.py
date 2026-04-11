from PIL import Image
from utils import log_event, IO_POOL

def handle(payload):
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    quality = int(payload.get("quality", 80))
    format_req = payload.get("format", "WEBP").upper()
    if format_req == "JPG": format_req = "JPEG"
    
    log_event("[PROGRESS: 20]", path=input_path)
    img = Image.open(input_path)
    if format_req == "JPEG" and img.mode in ("RGBA", "P"): img = img.convert("RGB")
    log_event("[PROGRESS: 60]", path=input_path)
    
    def save_file(img, out_path, q, fmt):
        try: img.save(out_path, format=fmt, quality=q, optimize=True)
        except Exception as e: log_event(f"DISK_ERROR: {e}", level="error", path=input_path)

    IO_POOL.submit(save_file, img, output_path, quality, format_req)
    log_event("[PROGRESS: 100]", path=input_path)
    return {"status": "SUCCESS"}
