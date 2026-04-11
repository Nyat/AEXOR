import os
from PIL import Image
from PIL import ImageOps
from utils import log_event

def handle_vizyon_resizer(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        
        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        log_event("[PROGRESS: 5]", path=input_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        img = Image.open(input_path).convert("RGBA")
        log_event("[PROGRESS: 15]", path=input_path)
        
        # 1000x1000 White Canvas (Optimized Resampler)
        canvas = Image.new("RGB", (1000, 1000), (255, 255, 255))
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        x = (1000 - img.width) // 2
        y = (1000 - img.height) // 2
        
        canvas.paste(img, (x, y), img)
        log_event("[PROGRESS: 90]", path=input_path)
        canvas.save(output_path, "WEBP", quality=100, lossless=True)
        
        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Resized to Vizyon standards (1000x1000)."}
    except Exception as e:
        log_event(f"VIZYON_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"VIZYON_RESIZER_FAILURE: {str(e)}"}
