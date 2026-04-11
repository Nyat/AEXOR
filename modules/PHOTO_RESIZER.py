import os
from PIL import Image, ImageOps
from utils import log_event, IO_POOL

def handle(payload):
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    
    # New Options
    target_w = int(payload.get("width", 1920))
    target_h = int(payload.get("height", 1080))
    mode = payload.get("resize_mode", "FIT").upper()
    bg_color = payload.get("bg_color", "BLACK").upper()
    
    log_event("[PROGRESS: 5]", path=input_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    img = Image.open(input_path).convert("RGBA")
    log_event("[PROGRESS: 15]", path=input_path)
    
    if mode == "FILL":
        canvas = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS, bleed=0.0, centering=(0.5, 0.5))
        canvas = canvas.convert("RGB")
    else:
        rgb_color = (0, 0, 0) if bg_color == "BLACK" else (255, 255, 255)
        canvas = Image.new("RGB", (target_w, target_h), rgb_color)
        
        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        
        x = (target_w - img.width) // 2
        y = (target_h - img.height) // 2
        
        temp = Image.new("RGBA", canvas.size, rgb_color + (255,))
        temp.paste(img, (x, y), img)
        canvas = temp.convert("RGB")
        
    log_event("[PROGRESS: 90]", path=input_path)
    
    def save_file(canvas, out_path):
        try: canvas.save(out_path, "WEBP", quality=95, method=4)
        except Exception as e: log_event(f"DISK_ERROR: {e}", level="error", path=input_path)

    IO_POOL.submit(save_file, canvas, output_path)
    log_event("[PROGRESS: 100]", path=input_path)
    return {"status": "SUCCESS", "message": f"Resized to {target_w}x{target_h} ({mode})"}
