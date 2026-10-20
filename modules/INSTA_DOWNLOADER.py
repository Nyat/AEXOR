import os
import re
import json
import html
import time
import random
import urllib.parse
import requests
from utils import log_event

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
IG_APP_ID = "936619743392459"


def _shortcode_to_media_id(shortcode: str) -> int:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    media_id = 0
    for char in shortcode:
        if char in alphabet:
            media_id = (media_id * 64) + alphabet.index(char)
    return media_id


def _extract_from_v1_item(item: dict) -> list:
    """Extract [(media_url, is_video)] from v1 API item dict."""
    results = []
    carousel = item.get("carousel_media")
    nodes = carousel if carousel else [item]
    for node in nodes:
        video_versions = node.get("video_versions")
        if video_versions and isinstance(video_versions, list):
            best_vid = video_versions[0].get("url")
            if best_vid:
                results.append((best_vid, True))
                continue
        img_versions = node.get("image_versions2", {}).get("candidates", [])
        if img_versions and isinstance(img_versions, list):
            best_img = img_versions[0].get("url")
            if best_img:
                results.append((best_img, False))
    return results


def _extract_from_gql_media(media: dict) -> list:
    """Extract [(media_url, is_video)] from GraphQL shortcode_media / xdt_shortcode_media."""
    results = []
    sidecar = media.get("edge_sidecar_to_children", {}).get("edges", [])
    nodes = [edge.get("node", {}) for edge in sidecar] if sidecar else [media]
    for node in nodes:
        is_vid = bool(node.get("is_video"))
        if is_vid and node.get("video_url"):
            results.append((node["video_url"], True))
        elif node.get("video_versions") and isinstance(node.get("video_versions"), list):
            results.append((node["video_versions"][0].get("url"), True))
        elif node.get("display_url"):
            results.append((node["display_url"], False))
        elif node.get("image_versions2", {}).get("candidates"):
            results.append((node["image_versions2"]["candidates"][0].get("url"), False))
        elif node.get("display_resources"):
            res_list = node["display_resources"]
            if res_list:
                results.append((res_list[-1].get("src"), False))
    return [(u, v) for (u, v) in results if u]


def _walk_json_for_media(obj) -> list:
    if isinstance(obj, dict):
        for key in ("xdt_shortcode_media", "shortcode_media"):
            if key in obj and isinstance(obj[key], dict):
                res = _extract_from_gql_media(obj[key])
                if res:
                    return res
        if "items" in obj and isinstance(obj["items"], list) and obj["items"]:
            first = obj["items"][0]
            if isinstance(first, dict) and ("image_versions2" in first or "carousel_media" in first or "video_versions" in first):
                res = _extract_from_v1_item(first)
                if res:
                    return res
        for v in obj.values():
            found = _walk_json_for_media(v)
            if found:
                return found
    elif isinstance(obj, list):
        for elem in obj:
            found = _walk_json_for_media(elem)
            if found:
                return found
    return []


def _prepare_session(session_id: str = None, shortcode: str = ""):
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    if session_id:
        clean_sid = session_id.strip().strip('"').strip("'")
        unquoted_sid = urllib.parse.unquote(clean_sid)
        encoded_sid = urllib.parse.quote(unquoted_sid, safe="")
        s.cookies.set("sessionid", encoded_sid, domain=".instagram.com")
        if ":" in unquoted_sid:
            ds_user_id = unquoted_sid.split(":", 1)[0]
            if ds_user_id.isdigit():
                s.cookies.set("ds_user_id", ds_user_id, domain=".instagram.com")

    lsd = "AVqbxe3J_YA"
    page_media = []
    try:
        target_url = f"https://www.instagram.com/p/{shortcode}/" if shortcode else "https://www.instagram.com/"
        r0 = s.get(target_url, timeout=15)
        if r0.status_code == 200:
            m_lsd = re.search(r'"LSD"\s*,\s*\[\]\s*,\s*\{\s*"token"\s*:\s*"([^"]+)"', r0.text)
            if m_lsd:
                lsd = m_lsd.group(1)
            for script_body in re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', r0.text, re.DOTALL):
                if "xdt_shortcode_media" in script_body or "image_versions2" in script_body or "video_versions" in script_body:
                    try:
                        blob = json.loads(script_body)
                        found = _walk_json_for_media(blob)
                        if found:
                            page_media = found
                            break
                    except Exception:
                        pass
    except Exception:
        pass

    csrf = s.cookies.get("csrftoken")
    if not csrf:
        csrf = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=32))
        s.cookies.set("csrftoken", csrf, domain=".instagram.com")

    s.headers.update({
        "Accept": "*/*",
        "X-IG-App-ID": IG_APP_ID,
        "X-ASBD-ID": "129477",
        "X-IG-WWW-Claim": "0",
        "X-FB-LSD": lsd,
        "X-CSRFToken": csrf,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.instagram.com",
        "Referer": f"https://www.instagram.com/p/{shortcode}/" if shortcode else "https://www.instagram.com/",
    })
    return s, lsd, page_media


def _fetch_media_list(shortcode: str, session_id: str = None) -> list:
    s, lsd, page_media = _prepare_session(session_id=session_id, shortcode=shortcode)

    # 1. If Relay SSR page HTML already contained the media JSON, return immediately
    if page_media:
        return page_media

    # 2. Authenticated v1 REST API (/api/v1/media/{media_id}/info/)
    if session_id:
        try:
            media_id = _shortcode_to_media_id(shortcode)
            for host in ("www.instagram.com", "i.instagram.com"):
                r_v1 = s.get(f"https://{host}/api/v1/media/{media_id}/info/", timeout=15)
                if r_v1.status_code == 200 and "application/json" in r_v1.headers.get("Content-Type", "").lower():
                    data = r_v1.json()
                    items = data.get("items", [])
                    if items:
                        extracted = _extract_from_v1_item(items[0])
                        if extracted:
                            return extracted
        except Exception as e:
            log_event(f"V1_API_FALLBACK: {e}", level="info")

    # 3. GraphQL doc_id POST with real LSD + CSRF + App-ID headers
    for doc_id in ("8845758582119845", "10015901848480474"):
        try:
            r_gql = s.post(
                "https://www.instagram.com/graphql/query",
                data={
                    "av": "0",
                    "__d": "www",
                    "__user": "0",
                    "__a": "1",
                    "__req": "1",
                    "lsd": lsd,
                    "fb_api_caller_class": "RelayModern",
                    "fb_api_req_friendly_name": "PolarisPostActionLoadPostQueryQuery",
                    "variables": json.dumps({"shortcode": shortcode}),
                    "server_timestamps": "true",
                    "doc_id": doc_id,
                },
                timeout=15,
            )
            if r_gql.status_code == 200:
                text = r_gql.text
                if text.startswith("for (;;);"):
                    text = text[len("for (;;);"):]
                gql_json = json.loads(text)
                found = _walk_json_for_media(gql_json)
                if found:
                    return found
        except Exception:
            pass

    # 4. Server-Side Embed Page Fallback (uses minimal User-Agent to force static SSR HTML)
    try:
        r_emb = requests.get(
            f"https://www.instagram.com/p/{shortcode}/embed/captioned/",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        if r_emb.status_code == 200:
            ctx_match = re.search(r'"contextJSON"\s*:\s*"((?:\\.|[^"\\])*)"', r_emb.text)
            if ctx_match:
                try:
                    ctx_raw = json.loads(f'"{ctx_match.group(1)}"')
                    ctx_data = json.loads(ctx_raw)
                    found = _walk_json_for_media(ctx_data)
                    if found:
                        return found
                except Exception:
                    pass

            vid_matches = re.findall(r'"video_url"\s*:\s*"([^"]+)"', r_emb.text)
            if vid_matches:
                results = []
                for v_url in dict.fromkeys(vid_matches):
                    clean_u = html.unescape(v_url.encode("utf-8").decode("unicode_escape"))
                    results.append((clean_u, True))
                if results:
                    return results

            img_tags = re.findall(r'<img[^>]+class="EmbeddedMediaImage"[^>]*>', r_emb.text)
            if img_tags:
                results = []
                for tag in img_tags:
                    src_m = re.search(r'src="([^"]+)"', tag)
                    if src_m:
                        results.append((html.unescape(src_m.group(1)), False))
                if results:
                    return list(dict.fromkeys(results))
    except Exception:
        pass

    return []


def handle(payload):
    url = payload.get("url", "")
    output_dir = os.path.abspath(payload.get("output_dir", "./output"))
    session_id = payload.get("session_id", "")
    os.makedirs(output_dir, exist_ok=True)

    log_event(f"INITIATING_UPLINK: {url}", path="SYSTEM")

    try:
        if session_id:
            log_event("SESSION_KEY_INJECTED", path="SYSTEM")

        shortcode_match = re.search(r"/(?:p|reels|reel|tv)/([^/?#&]+)", url)
        if not shortcode_match:
            return {"status": "ERROR", "message": "Invalid Instagram URL"}

        shortcode = shortcode_match.group(1)
        time.sleep(random.uniform(0.3, 0.8))

        log_event(f"FETCHING_METADATA: {shortcode}", path="SYSTEM")
        media_items = _fetch_media_list(shortcode, session_id=session_id)

        if not media_items:
            return {
                "status": "ERROR",
                "message": "RECOVERY_FAILED: Instagram blocked access or invalid/expired sessionid.",
            }

        saved_count = 0
        dl_headers = {"User-Agent": USER_AGENT, "Referer": "https://www.instagram.com/"}

        for i, (media_url, is_video) in enumerate(media_items):
            ext = ".mp4" if is_video else ".jpg"
            filename = f"insta_{shortcode}_{i+1}{ext}" if len(media_items) > 1 else f"insta_{shortcode}{ext}"
            target_path = os.path.join(output_dir, filename)

            log_event(f"UPLINK_{i+1}: Fetching...", path="SYSTEM")
            res = requests.get(media_url, headers=dl_headers, stream=True, timeout=30)

            if "text/html" in res.headers.get("Content-Type", "").lower():
                log_event("NODE_ERROR: Login Required", level="error")
                continue

            if res.status_code == 200:
                with open(target_path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(target_path):
                    saved_count += 1
                    log_event(f"UPLINK_SUCCESS: {filename}", path="SYSTEM")

        if saved_count > 0:
            return {"status": "SUCCESS", "message": f"NEURAL_RECOVERY_COMPLETE: {saved_count} items."}
        return {"status": "ERROR", "message": "RECOVERY_FAILED: Uplink severed."}

    except Exception as e:
        log_event(f"UPLINK_FATAL: {str(e)}", level="error")
        return {"status": "ERROR", "message": str(e)}
