import os
import sys
import warnings
import torch
import numpy as np
from PIL import Image
from utils import log_event, IO_POOL

# Suppress PIL Warnings for very large files
warnings.simplefilter('ignore', Image.DecompressionBombWarning)

# Monkey-patch torchvision to suppress deprecated functional_tensor warning
try:
    import torchvision.transforms.functional
    sys.modules['torchvision.transforms.functional_tensor'] = torchvision.transforms.functional
except Exception:
    pass

warnings.filterwarnings("ignore", category=UserWarning, module="torchvision")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# Global State for Neural Engines
UPSCALERS = {}
BG_SESSIONS = {}

def get_weights_dir():
    appdata = os.environ.get('APPDATA')
    weights_dir = os.path.join(appdata, 'AEXOR HUB', 'weights') if appdata else os.path.join(os.path.expanduser('~'), '.aexor-hub', 'weights')
    os.makedirs(weights_dir, exist_ok=True)
    return weights_dir

def get_upscaler(device_name='cuda'):
    global UPSCALERS
    if device_name not in UPSCALERS or UPSCALERS[device_name] is None:
        try:
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet
            
            if device_name == 'cuda' and not torch.cuda.is_available():
                log_event("HARDWARE_ERROR: CUDA not available. Forcing CPU.", level="error")
                device_name = 'cpu'
                
            device = torch.device(device_name)
            weights_dir = get_weights_dir()
            model_path = os.path.join(weights_dir, 'RealESRGAN_x4plus.pth')
            
            if not os.path.exists(model_path):
                log_event(f"ASSET_ERROR: Weights not found at {model_path}. Downloading...", level="info")
                import urllib.request
                urllib.request.urlretrieve("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth", model_path)
                log_event("Weight download complete.", level="info")

            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            half_precision = True if (device_name == 'cuda' and "+cpu" not in torch.__version__) else False
            
            UPSCALERS[device_name] = RealESRGANer(
                scale=4, model_path=model_path, model=model, device=device,
                tile=768 if device_name == 'cuda' else 400, tile_pad=32, pre_pad=0, half=half_precision
            )
            log_event(f"NEURAL_LOAD: ESRGAN_X4PLUS on {device_name.upper()}", path="SYSTEM")
        except Exception as e:
            log_event(f"Upscaler Init Error: {e}", level="error")
    return UPSCALERS.get(device_name)

def get_bg_session(model_name="birefnet-general", device_name='cuda'):
    global BG_SESSIONS
    cache_key = f"{model_name}_{device_name}"
    if cache_key not in BG_SESSIONS:
        from rembg import new_session
        import onnxruntime as ort
        
        if device_name == 'cuda':
            avail = ort.get_available_providers()
            if 'CUDAExecutionProvider' in avail:
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            elif 'DmlExecutionProvider' in avail:
                providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
            else:
                providers = ['CPUExecutionProvider']
        else:
            providers = ['CPUExecutionProvider']
            
        BG_SESSIONS[cache_key] = new_session(model_name, providers=providers)
        log_event(f"NEURAL_LOAD: {model_name.upper()} on {device_name.upper()}", path="SYSTEM")
    return BG_SESSIONS[cache_key]

def handle_upscaler(payload):
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    scale = int(payload.get("upscale", 2))
    device_name = payload.get("device", "cuda")
    if device_name == 'cuda' and not torch.cuda.is_available():
        log_event("HARDWARE_ERROR: CUDA not available. Forcing CPU.", level="error")
        device_name = 'cpu'
    
    log_event("[PROGRESS: 5]", path=input_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img = Image.open(input_path).convert("RGB")
    orig_w, orig_h = img.size
    if device_name == 'cuda': torch.cuda.empty_cache()
    
    upscaler = get_upscaler(device_name)
    if not upscaler: 
         return {"status": "ERROR", "message": "Upscaler initialization failed."}
    
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

def handle_bg_remover(payload):
    from rembg import remove
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    device_name = payload.get("device", "cuda")
    
    log_event("[PROGRESS: 5]", path=input_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    input_img = Image.open(input_path).convert("RGBA")
    session = get_bg_session("birefnet-general", device_name=device_name)
    
    output_img = remove(
        input_img, session=session, alpha_matting=True,
        alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=10, alpha_matting_erode_size=1
    )
    
    log_event("[PROGRESS: 90]", path=input_path)
    output_img.save(output_path, "PNG")
    log_event("[PROGRESS: 100]", path=input_path)
    return {"status": "SUCCESS", "message": "High-precision background removed"}
