import os
import shutil
import subprocess
import tempfile
from utils import log_event


def _get_ffmpeg():
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which("ffmpeg")


def handle(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        video_mode = str(payload.get("video_mode", "COMPRESS_MP4")).upper()
        video_preset = str(payload.get("video_preset", "BALANCED")).upper()
        video_scale = str(payload.get("video_scale", "ORIGINAL")).upper()

        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        ffmpeg_exe = _get_ffmpeg()
        if not ffmpeg_exe:
            return {"status": "ERROR", "message": "FFmpeg engine not found. Install FFMPEG_CORE in Module Manager."}

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        log_event("[PROGRESS: 15]", path=input_path)

        scale_filter = ""
        if video_scale == "1080P":
            scale_filter = "scale='min(1920,iw)':-2:flags=lanczos"
        elif video_scale == "720P":
            scale_filter = "scale='min(1280,iw)':-2:flags=lanczos"
        elif video_scale == "480P":
            scale_filter = "scale='min(854,iw)':-2:flags=lanczos"

        if video_mode == "GIF_FORGE":
            fps = 18 if video_preset == "ULTRA" else (15 if video_preset == "BALANCED" else 12)
            width_cap = 800 if video_scale == "ORIGINAL" else (1080 if video_scale == "1080P" else (720 if video_scale == "720P" else 480))
            vf_palette = f"fps={fps},scale='min({width_cap},iw)':-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_path,
                "-vf", vf_palette,
                "-loop", "0",
                output_path
            ]
            log_event("[PROGRESS: 45]", path=input_path)
            subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        elif video_mode == "ANIMATED_WEBP":
            fps = 20 if video_preset == "ULTRA" else (15 if video_preset == "BALANCED" else 12)
            q_val = "85" if video_preset == "ULTRA" else ("75" if video_preset == "BALANCED" else "60")
            width_cap = 960 if video_scale == "ORIGINAL" else (1080 if video_scale == "1080P" else (720 if video_scale == "720P" else 480))
            vf = f"fps={fps},scale='min({width_cap},iw)':-1:flags=lanczos"
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_path,
                "-vf", vf,
                "-vcodec", "libwebp",
                "-lossless", "0",
                "-compression_level", "4",
                "-q:v", q_val,
                "-loop", "0",
                "-an",
                output_path
            ]
            log_event("[PROGRESS: 45]", path=input_path)
            subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        else:
            # COMPRESS_MP4 (H.264 + AAC)
            crf = "20" if video_preset == "ULTRA" else ("25" if video_preset == "BALANCED" else "30")
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_path,
            ]
            if scale_filter:
                cmd += ["-vf", scale_filter]
            cmd += [
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", crf,
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "160k",
                "-movflags", "+faststart",
                output_path
            ]
            log_event("[PROGRESS: 45]", path=input_path)
            subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Video processed ({video_mode} / {video_preset})."}
    except Exception as e:
        log_event(f"VIDEO_OPTIMIZER_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"VIDEO_OPTIMIZER_FAILURE: {str(e)}"}
