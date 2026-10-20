import os
import shutil
import subprocess
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
        audio_mode = str(payload.get("audio_extract_mode", "MP3_320K")).upper()

        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        ffmpeg_exe = _get_ffmpeg()
        if not ffmpeg_exe:
            return {"status": "ERROR", "message": "FFmpeg engine not found. Install FFMPEG_CORE in Module Manager."}

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        log_event("[PROGRESS: 20]", path=input_path)

        if audio_mode == "MUTE_VIDEO":
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_path,
                "-c:v", "copy",
                "-an",
                output_path
            ]
        elif audio_mode == "WAV_PCM":
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "48000",
                "-ac", "2",
                output_path
            ]
        elif audio_mode == "FLAC_LOSSLESS":
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_path,
                "-vn",
                "-acodec", "flac",
                output_path
            ]
        else:
            # MP3_320K
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", input_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-b:a", "320k",
                output_path
            ]

        log_event("[PROGRESS: 55]", path=input_path)
        subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Completed {audio_mode} -> {os.path.basename(output_path)}."}
    except Exception as e:
        log_event(f"AUDIO_EXTRACTOR_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"AUDIO_EXTRACTOR_FAILURE: {str(e)}"}
