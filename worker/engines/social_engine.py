import os
import re
import time
import random
import requests
import instaloader
from ..utils import log_event

# Global Instaloader Instance
INSTA_LOADER = None

def get_instaloader():
    global INSTA_LOADER
    if INSTA_LOADER is None:
        INSTA_LOADER = instaloader.Instaloader()
        INSTA_LOADER.context.log = lambda *args, **kwargs: None
    return INSTA_LOADER

def handle_insta_downloader(payload):
    url = payload.get("url")
    output_dir = os.path.abspath(payload.get("output_dir", "."))
    session_id = payload.get("session_id")
    os.makedirs(output_dir, exist_ok=True)
    
    log_event(f"INITIATING_UPLINK: {url}", path="SYSTEM")
    
    try:
        L = get_instaloader()
        if session_id:
            log_event("SESSION_KEY_INJECTED", path="SYSTEM")
            L.context._session.cookies.set('sessionid', session_id, domain=".instagram.com")
        
        shortcode_match = re.search(r'/(?:p|reels|reel|tv)/([^/?#&]+)', url)
        if not shortcode_match: return {"status": "ERROR", "message": "Invalid URL"}
        
        shortcode = shortcode_match.group(1)
        time.sleep(random.uniform(1.0, 2.0)) # Bot-prevention jitter
        
        log_event(f"FETCHING_METADATA: {shortcode}", path="SYSTEM")
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        nodes = list(post.get_sidecar_nodes()) if post.typename == 'GraphSidecar' else [post]
        
        saved_count = 0
        session = requests.Session()
        if session_id: session.cookies.set('sessionid', session_id, domain=".instagram.com")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
        
        for i, node in enumerate(nodes):
            is_video = getattr(node, 'is_video', post.is_video if i==0 else False)
            media_url = getattr(node, 'video_url' if is_video else 'display_url', None)
            
            if not media_url: 
                try: 
                    m = node._full_metadata_dict
                    media_url = m.get('video_url' if is_video else 'display_url')
                except: pass

            if not media_url: continue
                
            ext = ".mp4" if is_video else ".jpg"
            filename = f"insta_{shortcode}_{i+1}{ext}" if len(nodes) > 1 else f"insta_{shortcode}{ext}"
            target_path = os.path.join(output_dir, filename)
            
            log_event(f"UPLINK_{i+1}: Fetching...", path="SYSTEM")
            res = requests.get(media_url, headers=headers, stream=True, timeout=30)
            
            if 'text/html' in res.headers.get('Content-Type', '').lower():
                log_event(f"NODE_ERROR: Login Required", level="error")
                continue
                
            if res.status_code == 200:
                with open(target_path, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=1024*1024):
                        if chunk: f.write(chunk)
                if os.path.exists(target_path): 
                    saved_count += 1
                    log_event(f"UPLINK_SUCCESS: {filename}", path="SYSTEM")
        
        if saved_count > 0:
            return {"status": "SUCCESS", "message": f"NEURAL_RECOVERY_COMPLETE: {saved_count} items."}
        return {"status": "ERROR", "message": "RECOVERY_FAILED: Uplink severed."}

    except Exception as e:
        log_event(f"UPLINK_FATAL: {str(e)}", level="error")
        return {"status": "ERROR", "message": str(e)}
