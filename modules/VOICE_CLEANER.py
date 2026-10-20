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
        import numpy as np
        import soundfile as sf
        import noisereduce as nr
        from scipy import signal

        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        strength = str(payload.get("voice_strength", "STUDIO")).upper()
        voice_boost = bool(payload.get("voice_boost", True))
        out_mode = str(payload.get("voice_output", "WAV")).upper()

        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        ffmpeg_exe = _get_ffmpeg()
        if not ffmpeg_exe:
            return {"status": "ERROR", "message": "FFmpeg engine missing. Install FFMPEG_CORE in Module Manager."}

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        log_event("[PROGRESS: 15]", path=input_path)

        prop_decrease = 0.65 if strength == "LIGHT" else (0.96 if strength == "AGGRESSIVE" else 0.85)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
            raw_wav = tmp_in.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out:
            clean_wav = tmp_out.name

        try:
            subprocess.run(
                [ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error", "-i", input_path, "-vn", "-acodec", "pcm_s16le", "-ar", "48000", raw_wav],
                check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            log_event("[PROGRESS: 35]", path=input_path)

            data, sr = sf.read(raw_wav, dtype="float32")
            # Spectral gating noise reduction
            if data.ndim > 1:
                cleaned = np.stack([
                    nr.reduce_noise(y=data[:, ch], sr=sr, prop_decrease=prop_decrease, stationary=False)
                    for ch in range(data.shape[1])
                ], axis=1)
            else:
                cleaned = nr.reduce_noise(y=data, sr=sr, prop_decrease=prop_decrease, stationary=False)

            log_event("[PROGRESS: 70]", path=input_path)

            if voice_boost:
                # 80Hz high-pass filter to remove mic rumble + peak normalization
                sos = signal.butter(4, 80.0 / (sr / 2.0), btype="highpass", output="sos")
                if cleaned.ndim > 1:
                    for ch in range(cleaned.shape[1]):
                        cleaned[:, ch] = signal.sosfilt(sos, cleaned[:, ch])
                else:
                    cleaned = signal.sosfilt(sos, cleaned)

                peak = float(np.max(np.abs(cleaned)))
                if peak > 1e-5:
                    cleaned = (cleaned / peak) * 0.92

            sf.write(clean_wav, cleaned, sr, subtype="PCM_16")
            log_event("[PROGRESS: 85]", path=input_path)

            in_ext = os.path.splitext(input_path)[1].lower()
            is_video = in_ext in (".mp4", ".mov", ".mkv", ".webm", ".avi")

            if out_mode == "VIDEO_REMUX" and is_video:
                subprocess.run(
                    [
                        ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", input_path, "-i", clean_wav,
                        "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
                        "-c:a", "aac", "-b:a", "192k", "-shortest",
                        output_path
                    ],
                    check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )
            elif out_mode == "MP3":
                subprocess.run(
                    [
                        ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", clean_wav, "-acodec", "libmp3lame", "-b:a", "320k",
                        output_path
                    ],
                    check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                )
            else:
                shutil.copy2(clean_wav, output_path)

            log_event("[PROGRESS: 100]", path=input_path)
            return {"status": "SUCCESS", "message": f"Voice denoised ({strength}{', EQ Boost' if voice_boost else ''})."}
        finally:
            for p in (raw_wav, clean_wav):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
    except Exception as e:
        log_event(f"VOICE_CLEANER_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"VOICE_CLEANER_FAILURE: {str(e)}"}
