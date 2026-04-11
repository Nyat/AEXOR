import os
from PIL import Image
from utils import log_event

def handle_format_converter(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        log_event("[PROGRESS: 5]", path=input_path)
        
        fmt = payload.get("format", "WEBP").lower()
        if fmt == "jpg": fmt = "jpeg"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img = Image.open(input_path)
        log_event("[PROGRESS: 15]", path=input_path)
        
        if img.mode in ("RGBA", "P") and fmt == "jpeg":
            img = img.convert("RGB")
            
        img.save(output_path, fmt.upper())
        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Converted to {fmt.upper()}"}
    except Exception as e:
        log_event(f"CONVERT_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"FORMAT_CONVERTER_FAILURE: {str(e)}"}

def handle_image_compressor(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        quality = int(payload.get("quality", 80))
        
        log_event("[PROGRESS: 5]", path=input_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Calculate original size
        old_size = os.path.getsize(input_path)
        
        img = Image.open(input_path)
        log_event("[PROGRESS: 15]", path=input_path)
        
        # Adaptive Compression based on format
        fmt = img.format if img.format else output_path.split('.')[-1].upper()
        if fmt == 'JPG': fmt = 'JPEG'
        if fmt == 'HEIC': fmt = 'HEIF' # Pillow-HEIF uses 'HEIF' for saving
        
        save_args = {"optimize": True}
        
        if fmt == 'PNG':
            if quality < 95:
                # Map quality to color count (quantization)
                colors = max(8, int(256 * (quality / 100)))
                img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
            save_args["compress_level"] = 9
        elif fmt in ('JPEG', 'WEBP', 'HEIF'):
            adj_quality = int(quality * 0.85) if fmt == 'HEIF' else quality
            save_args["quality"] = adj_quality
            if fmt == 'JPEG':
                save_args["progressive"] = True
                save_args["subsampling"] = 0 if adj_quality > 90 else (1 if adj_quality > 60 else 2)
            
        img.save(output_path, fmt, **save_args)
        
        new_size = os.path.getsize(output_path)
        
        # SIZE_GUARD: Revert if larger
        if new_size >= old_size:
            import shutil
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

def handle_photo_resizer(payload):
    try:
        from PIL import ImageOps
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
            # ImageOps.fit crops to exactly fit the target bbox preserving aspect ratio
            canvas = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS, bleed=0.0, centering=(0.5, 0.5))
            # Drop alpha channel if present to save as WEBP elegantly or convert to RGB
            canvas = canvas.convert("RGB")
        else:
            # FIT mode: Scale down preserving aspect ratio, paste on canvas
            rgb_color = (0, 0, 0) if bg_color == "BLACK" else (255, 255, 255)
            canvas = Image.new("RGB", (target_w, target_h), rgb_color)
            
            # Calculate bounding box
            img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            
            x = (target_w - img.width) // 2
            y = (target_h - img.height) // 2
            
            # Merge Alpha properly
            temp = Image.new("RGBA", canvas.size, rgb_color + (255,))
            temp.paste(img, (x, y), img)
            canvas = temp.convert("RGB")
            
        log_event("[PROGRESS: 90]", path=input_path)
        canvas.save(output_path, "WEBP", quality=95, method=4)
        
        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Resized to {target_w}x{target_h} ({mode})"}
    except Exception as e:
        log_event(f"RESIZER_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"PHOTO_RESIZER_FAILURE: {str(e)}"}

