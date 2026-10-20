import os
from PIL import Image
from utils import log_event

def handle(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        log_event("[PROGRESS: 5]", path=input_path)
        
        fmt = payload.get("format", "WEBP").lower()
        if fmt == "jpg": fmt = "jpeg"
        if fmt == "heic": fmt = "heif"
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.open(input_path)
        log_event("[PROGRESS: 15]", path=input_path)
        
        if img.mode in ("RGBA", "P") and fmt == "jpeg":
            img = img.convert("RGB")
            
        img.save(output_path, fmt.upper(), quality=100)
        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Converted to {fmt.upper()}"}
    except Exception as e:
        log_event(f"CONVERT_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"FORMAT_CONVERTER_FAILURE: {str(e)}"}
