import os
import torch
import numpy as np
from PIL import Image
from ..utils import log_event, IO_POOL

# Global State for Neural Engines
UPSCALERS = {}
BG_SESSIONS = {}

def get_weights_dir():
    appdata = os.environ.get('APPDATA')
    possible_paths = []
    if appdata:
        possible_paths.append(os.path.join(appdata, 'AEXOR HUB', 'weights'))
        possible_paths.append(os.path.join(appdata, 'N-Tools', 'weights'))
    
    home = os.path.expanduser('~')
    possible_paths.append(os.path.join(home, '.aexor-hub', 'weights'))
    possible_paths.append(os.path.join(home, '.n-tools', 'weights'))
    
    for p in possible_paths:
        if os.path.exists(p): return p
        
    weights_dir = possible_paths[0] if appdata else possible_paths[2]
    if not os.path.exists(weights_dir):
        try: os.makedirs(weights_dir)
        except:
            weights_dir = os.path.join(os.path.dirname(__file__), 'weights')
            if not os.path.exists(weights_dir): os.makedirs(weights_dir)
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
                log_event(f"ASSET_ERROR: Weights not found at {model_path}", level="error")
                return None

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

def get_bg_session(model_name="birefnet-general"):
    global BG_SESSIONS
    if model_name not in BG_SESSIONS:
        from rembg import new_session
        BG_SESSIONS[model_name] = new_session(model_name)
        log_event(f"NEURAL_LOAD: {model_name.upper()} Evolution loaded.", path="SYSTEM")
    return BG_SESSIONS[model_name]

def handle_upscaler(payload):
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    scale = int(payload.get("upscale", 2))
    device_name = payload.get("device", "cuda")
    
    log_event("[PROGRESS: 5]", path=input_path)
    img = Image.open(input_path).convert("RGB")
    if device_name == 'cuda': torch.cuda.empty_cache()
    
    upscaler = get_upscaler(device_name)
    if not upscaler: 
         return {"status": "ERROR", "message": f"Upscaler initialization failed."}
    
    log_event("[PROGRESS: 30]", path=input_path)
    if device_name == 'cuda':
        with torch.amp.autocast('cuda'):
            output, _ = upscaler.enhance(np.array(img), outscale=scale)
    else:
        output, _ = upscaler.enhance(np.array(img), outscale=scale)
    
    log_event("[PROGRESS: 90]", path=input_path)
    
    def save_to_disk(arr, path):
        try: Image.fromarray(arr).save(path, quality=100, subsampling=0)
        except Exception as e: log_event(f"DISK_ERROR: {e}", level="error", path=input_path)

    IO_POOL.submit(save_to_disk, output, output_path)
    log_event("[PROGRESS: 100]", path=input_path)
    return {"status": "SUCCESS", "message": f"NEURAL_UPSCAL_COMPLETE"}

def handle_bg_remover(payload):
    from rembg import remove
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    
    log_event("[PROGRESS: 5]", path=input_path)
    input_img = Image.open(input_path).convert("RGBA")
    session = get_bg_session("birefnet-general")
    
    output_img = remove(
        input_img, session=session, alpha_matting=True,
        alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=10, alpha_matting_erode_size=1
    )
    
    log_event("[PROGRESS: 90]", path=input_path)
    output_img.save(output_path, "PNG")
    log_event("[PROGRESS: 100]", path=input_path)
    return {"status": "SUCCESS", "message": "High-precision background removed"}
