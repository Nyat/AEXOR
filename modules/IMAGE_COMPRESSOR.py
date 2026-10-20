import os
import shutil
from PIL import Image
from utils import log_event

def handle(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        quality = int(payload.get("quality", 80))
        
        log_event("[PROGRESS: 5]", path=input_path)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        old_size = os.path.getsize(input_path)
        img = Image.open(input_path)
        log_event("[PROGRESS: 15]", path=input_path)
        
        fmt = img.format if img.format else output_path.split('.')[-1].upper()
        if fmt == 'JPG': fmt = 'JPEG'
        if fmt == 'HEIC': fmt = 'HEIF'
        
        save_args = {"optimize": True}
        
        if fmt == 'PNG':
            if quality < 95:
                colors = max(8, int(256 * (quality / 100)))
                img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
            save_args["compress_level"] = 9
        elif fmt in ('JPEG', 'WEBP', 'HEIF'):
            if fmt == 'JPEG' and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            adj_quality = int(quality * 0.85) if fmt == 'HEIF' else quality
            save_args["quality"] = adj_quality
            if fmt == 'JPEG':
                save_args["progressive"] = True
                save_args["subsampling"] = 0 if adj_quality > 90 else (1 if adj_quality > 60 else 2)
            
        img.save(output_path, fmt, **save_args)
        
        new_size = os.path.getsize(output_path)
        
        if new_size >= old_size:
            shutil.copy2(input_path, output_path)
            new_size = old_size
            msg_status = "ORIGINAL_KEPT"
        else:
            savings = 100 - (100 * new_size / old_size) if old_size > 0 else 0
            msg_status = f"{savings:.1f}% SAVED"
        
        log_event("[PROGRESS: 100]", path=input_path)
        return {
            "status": "SUCCESS", 
            "message": f"COMPRESS: {msg_status} ({new_size / (1024*1024):.2f}MB) // Q: {quality}%"
        }
    except Exception as e:
        log_event(f"COMPRESS_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"IMAGE_COMPRESSOR_FAILURE: {str(e)}"}
