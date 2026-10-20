import os
from PIL import Image
from utils import log_event, IO_POOL, ensure_cuda_dlls

BG_SESSIONS = {}

def get_bg_session(model_name="birefnet-general", gpu_vendor='nvidia'):
    global BG_SESSIONS
    ensure_cuda_dlls()
    cache_key = f"{model_name}_{gpu_vendor}"
    if cache_key not in BG_SESSIONS:
        from rembg import new_session
        import onnxruntime as ort
        
        avail = ort.get_available_providers()
        if gpu_vendor == 'nvidia' and 'CUDAExecutionProvider' in avail:
            providers = ['CUDAExecutionProvider']
        elif 'DmlExecutionProvider' in avail:
            providers = ['DmlExecutionProvider']
        elif 'CUDAExecutionProvider' in avail:
            providers = ['CUDAExecutionProvider']
        else:
            raise RuntimeError(f"GPU ExecutionProvider not active (Available: {avail}). Re-install GPU_ACCEL in Module Manager.")
            
        BG_SESSIONS[cache_key] = new_session(model_name, providers=providers)
        log_event(f"NEURAL_LOAD: {model_name.upper()} on {providers[0]}", path="SYSTEM")
    return BG_SESSIONS[cache_key]

def handle(payload):
    from rembg import remove
    input_path = payload.get("input_path")
    output_path = payload.get("output_path")
    gpu_vendor = payload.get("gpu_vendor", "nvidia")
    
    log_event("[PROGRESS: 5]", path=input_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    input_img = Image.open(input_path).convert("RGBA")
    session = get_bg_session("birefnet-general", gpu_vendor=gpu_vendor)
    
    log_event("[PROGRESS: 30]", path=input_path)
    output_img = remove(input_img, session=session)
    log_event("[PROGRESS: 90]", path=input_path)
    
    def save_to_disk(img, path):
         try: img.save(path, format="PNG")
         except Exception as e: log_event(f"DISK_ERROR: {e}", level="error", path=input_path)
    
    IO_POOL.submit(save_to_disk, output_img, output_path)
    log_event("[PROGRESS: 100]", path=input_path)
    
    return {"status": "SUCCESS", "message": "BG_REMOVED_SUCCESSFULLY"}
