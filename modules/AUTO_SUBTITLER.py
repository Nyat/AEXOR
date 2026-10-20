import os
import shutil
import subprocess
import tempfile
from utils import log_event, ensure_cuda_dlls

_WHISPER_MODEL = None
_WHISPER_KEY = None


def _get_ffmpeg():
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which("ffmpeg")


def _format_srt_timestamp(seconds):
    ms = int(round((seconds - int(seconds)) * 1000))
    total_sec = int(seconds)
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def handle(payload):
    global _WHISPER_MODEL, _WHISPER_KEY
    try:
        ensure_cuda_dlls()
        from faster_whisper import WhisperModel

        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        output_dir = payload.get("output_dir") or (os.path.dirname(output_path) if output_path else "./output")
        model_tier = str(payload.get("model_size") or payload.get("whisper_model", "base")).lower()
        sub_format = str(payload.get("sub_format") or payload.get("whisper_format", "SRT")).upper()
        lang = str(payload.get("language") or payload.get("whisper_lang", "AUTO")).upper()

        if not input_path:
            return {"status": "ERROR", "message": "Missing input path."}

        os.makedirs(output_dir, exist_ok=True)
        ffmpeg_exe = _get_ffmpeg()
        if not ffmpeg_exe:
            return {"status": "ERROR", "message": "FFmpeg engine missing. Install FASTER_WHISPER in Module Manager."}

        log_event("[PROGRESS: 10]", path=input_path)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_16k = tmp.name

        try:
            subprocess.run(
                [ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error", "-i", input_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_16k],
                check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            log_event("[PROGRESS: 25]", path=input_path)

            key = f"{model_tier}_cuda"
            if _WHISPER_MODEL is None or _WHISPER_KEY != key:
                log_event(f"NEURAL_LOAD: WHISPER_{model_tier.upper()} on GPU (CUDA_FLOAT16)", level="info", path=input_path)
                _WHISPER_MODEL = WhisperModel(model_tier, device="cuda", compute_type="float16")
                _WHISPER_KEY = key

            log_event("[PROGRESS: 45]", path=input_path)
            lang_arg = None if lang == "AUTO" else lang.lower()
            segments_gen, info = _WHISPER_MODEL.transcribe(wav_16k, language=lang_arg, beam_size=5, vad_filter=True)

            srt_blocks = []
            txt_lines = []
            duration = getattr(info, "duration", 0) or 1.0

            for idx, seg in enumerate(segments_gen, 1):
                start_ts = _format_srt_timestamp(seg.start)
                end_ts = _format_srt_timestamp(seg.end)
                text = seg.text.strip()
                if text:
                    srt_blocks.append(f"{idx}\n{start_ts} --> {end_ts}\n{text}")
                    txt_lines.append(text)
                prog = min(92, 45 + int((seg.end / float(duration)) * 47))
                log_event(f"[PROGRESS: {prog}]", path=input_path)

            base_name = os.path.splitext(os.path.basename(input_path))[0]
            saved = []

            if sub_format in ("SRT", "BOTH"):
                srt_path = os.path.join(output_dir, f"{base_name}.srt")
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(srt_blocks) + "\n")
                saved.append(os.path.basename(srt_path))

            if sub_format in ("TXT", "BOTH"):
                txt_path = os.path.join(output_dir, f"{base_name}-transcript.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(txt_lines) + "\n")
                saved.append(os.path.basename(txt_path))

            log_event("[PROGRESS: 100]", path=input_path)
            det_lang = getattr(info, "language", "auto").upper()
            return {"status": "SUCCESS", "message": f"Transcribed {len(srt_blocks)} segments [{det_lang}] -> {', '.join(saved)}"}
        finally:
            if os.path.exists(wav_16k):
                try:
                    os.remove(wav_16k)
                except Exception:
                    pass
    except Exception as e:
        log_event(f"AUTO_SUBTITLER_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"AUTO_SUBTITLER_FAILURE: {str(e)}"}
