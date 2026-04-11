import os
import torch
import numpy as np
from PIL import Image
from utils import log_event, IO_POOL
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

def handle(payload):
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
