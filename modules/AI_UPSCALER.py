import os
import torch
import numpy as np
from PIL import Image
from utils import log_event, IO_POOL, ensure_cuda_dlls
import warnings

warnings.simplefilter('ignore', Image.DecompressionBombWarning)
import sys
try:
    import torchvision.transforms.functional
    sys.modules['torchvision.transforms.functional_tensor'] = torchvision.transforms.functional
except Exception:
    pass

warnings.filterwarnings("ignore", category=UserWarning, module="torchvision")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

UPSCALERS = {}

def get_weights_dir():
    appdata = os.environ.get('APPDATA')
    weights_dir = os.path.join(appdata, 'AEXOR HUB', 'weights') if appdata else os.path.join(os.path.expanduser('~'), '.aexor-hub', 'weights')
    os.makedirs(weights_dir, exist_ok=True)
    return weights_dir

def _resolve_gpu_device():
    ensure_cuda_dlls()
    if torch.cuda.is_available():
        return torch.device('cuda'), 'cuda', True
    try:
        import torch_directml
        return torch_directml.device(), 'dml', False
    except Exception:
        pass
    raise RuntimeError("GPU acceleration unavailable. Ensure GPU_ACCEL is installed in Module Manager.")

def get_upscaler():
    global UPSCALERS
    dev_obj, dev_key, use_half = _resolve_gpu_device()
    if dev_key not in UPSCALERS or UPSCALERS[dev_key] is None:
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet
        
        weights_dir = get_weights_dir()
        model_path = os.path.join(weights_dir, 'RealESRGAN_x4plus.pth')
        
        if not os.path.exists(model_path):
            log_event(f"ASSET_ERROR: Weights not found at {model_path}. Downloading...", level="info")
            import urllib.request
            urllib.request.urlretrieve("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth", model_path)
            log_event("Weight download complete.", level="info")

        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        
        UPSCALERS[dev_key] = RealESRGANer(
            scale=4, model_path=model_path, model=model, device=dev_obj,
            tile=768, tile_pad=32, pre_pad=0, half=use_half
        )
        log_event(f"NEURAL_LOAD: ESRGAN_X4PLUS on GPU ({dev_key.upper()})", path="SYSTEM")
    return UPSCALERS.get(dev_key)

def handle(payload):
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    scale = int(payload.get("upscale", 2))
    
    log_event("[PROGRESS: 5]", path=input_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img = Image.open(input_path).convert("RGB")
    orig_w, orig_h = img.size
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    upscaler = get_upscaler()
    if not upscaler: 
         return {"status": "ERROR", "message": "Upscaler GPU initialization failed."}
    
    MAX_SIDE = 16380
    effective_scale = float(scale)
    if max(orig_w, orig_h) * effective_scale > MAX_SIDE:
        effective_scale = MAX_SIDE / float(max(orig_w, orig_h))
        log_event(
            f"RESOLUTION_GUARD: Requested {scale}X ({orig_w * scale}x{orig_h * scale}) exceeds 16K limit; capping to {int(orig_w * effective_scale)}x{int(orig_h * effective_scale)} for memory stability.",
            level="info"
        )

    log_event("[PROGRESS: 30]", path=input_path)
    output, _ = upscaler.enhance(np.array(img), outscale=effective_scale)
    
    log_event("[PROGRESS: 90]", path=input_path)
    out_h, out_w = output.shape[:2]
    try:
        out_img = Image.fromarray(output)
        ext = os.path.splitext(output_path)[1].lower()
        if ext in ('.jpg', '.jpeg'):
            out_img.save(output_path, format='JPEG', quality=98, subsampling=0)
        elif ext == '.webp':
            out_img.save(output_path, format='WEBP', quality=98)
        else:
            out_img.save(output_path)
    except Exception as e:
        log_event(f"DISK_ERROR: {e}", level="error", path=input_path)
        return {"status": "ERROR", "message": f"DISK_WRITE_FAILURE: {e}"}

    log_event("[PROGRESS: 100]", path=input_path)
    return {
        "status": "SUCCESS",
        "message": f"NEURAL_UPSCALE_COMPLETE [{scale}X]: {orig_w}x{orig_h} -> {out_w}x{out_h}"
    }
