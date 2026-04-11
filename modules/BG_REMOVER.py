import os
from PIL import Image
from utils import log_event, IO_POOL

BG_SESSIONS = {}

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

def handle(payload):
    from rembg import remove
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    device_name = payload.get("device", "cuda")
    
    log_event("[PROGRESS: 5]", path=input_path)
    input_img = Image.open(input_path).convert("RGBA")
    session = get_bg_session("birefnet-general", device_name=device_name)
    
    log_event("[PROGRESS: 30]", path=input_path)
    # The new_session will handle downloading the ONNX weights to U2NET_HOME automatically.
    output_img = remove(input_img, session=session)
    log_event("[PROGRESS: 90]", path=input_path)
    
    def save_to_disk(img, path):
         try: img.save(path, format="PNG")
         except Exception as e: log_event(f"DISK_ERROR: {e}", level="error", path=input_path)
    
    IO_POOL.submit(save_to_disk, output_img, output_path)
    log_event("[PROGRESS: 100]", path=input_path)
    
    return {"status": "SUCCESS", "message": "BG_REMOVED_SUCCESSFULLY"}
