import os
import shutil
from utils import log_event


def _ensure_ffmpeg():
    try:
        import imageio_ffmpeg
        src_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if src_exe and os.path.exists(src_exe):
            appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
            bin_dir = os.path.join(appdata, "AEXOR HUB", "bin")
            os.makedirs(bin_dir, exist_ok=True)
            dst_exe = os.path.join(bin_dir, "ffmpeg.exe")
            if not os.path.exists(dst_exe):
                try:
                    shutil.copy2(src_exe, dst_exe)
                except Exception:
                    dst_exe = src_exe
            if bin_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            return dst_exe
    except Exception:
        pass
    return shutil.which("ffmpeg")


def handle(payload):
    try:
        import yt_dlp

        url = str(payload.get("media_url") or payload.get("url") or "").strip()
        output_dir = payload.get("output_dir") or "./output"
        media_format = str(payload.get("media_format", "VIDEO_MP4")).upper()
        media_quality = str(payload.get("media_quality", "BEST")).upper()

        if not url:
            return {"status": "ERROR", "message": "No target URL provided."}

        os.makedirs(output_dir, exist_ok=True)
        ffmpeg_exe = _ensure_ffmpeg()
        log_event(f"MEDIA_UPLINK: Connecting to stream [{url[:60]}]...", level="info")
        log_event("[PROGRESS: 10]")

        last_pct = [10]

        def _progress_hook(d):
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                if total > 0:
                    pct = min(90, max(12, int((downloaded / float(total)) * 85)))
                    if pct >= last_pct[0] + 4:
                        last_pct[0] = pct
                        log_event(f"[PROGRESS: {pct}]")
            elif d.get("status") == "finished":
                log_event("[PROGRESS: 92]")

        ydl_opts = {
            "outtmpl": os.path.join(output_dir, "%(title).80s [%(id)s].%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [_progress_hook],
            "windowsfilenames": True,
        }
        if ffmpeg_exe:
            ydl_opts["ffmpeg_location"] = ffmpeg_exe

        if media_format == "AUDIO_MP3":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]
        elif media_format == "AUDIO_WAV":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }]
        else:
            # VIDEO_MP4
            if media_quality == "720P":
                ydl_opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            elif media_quality == "1080P":
                ydl_opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
            else:
                ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            ydl_opts["merge_output_format"] = "mp4"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Media_Asset") if isinstance(info, dict) else "Media_Asset"

        log_event("[PROGRESS: 100]")
        return {"status": "SUCCESS", "message": f"Downloaded '{title[:48]}' ({media_format})."}
    except Exception as e:
        log_event(f"MEDIA_DOWNLOADER_ERROR: {str(e)}", level="error")
        return {"status": "ERROR", "message": f"MEDIA_DOWNLOADER_FAILURE: {str(e)}"}
