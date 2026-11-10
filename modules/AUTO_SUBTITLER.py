import os
import shutil
import subprocess
import tempfile
import warnings
import wave

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*symlinks.*")

from utils import log_event, ensure_cuda_dlls

_WHISPER_MODEL = None
_WHISPER_KEY = None


def _patch_av_open():
    """Patch PyAV av.open so faster-whisper works seamlessly with PyAV >= 14 where metadata_errors was removed."""
    try:
        import av
        orig_open = av.open
        if not getattr(orig_open, "_aexor_patched", False):
            def _safe_av_open(*args, **kwargs):
                try:
                    return orig_open(*args, **kwargs)
                except TypeError:
                    kwargs.pop("metadata_errors", None)
                    return orig_open(*args, **kwargs)
            _safe_av_open._aexor_patched = True
            av.open = _safe_av_open
    except Exception:
        pass


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
    if ms >= 1000:
        ms -= 1000
        total_sec += 1
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def _split_segment_words(seg, max_words=10, max_duration=5.5, pause_thresh=0.6):
    """Split a Whisper segment into natural, readable subtitle phrases using word-level timestamps."""
    words = getattr(seg, "words", None)
    if not words:
        text = seg.text.strip()
        return [(seg.start, seg.end, text)] if text else []

    refined = []
    cur_words = []
    total_w = len(words)

    for idx, w in enumerate(words):
        if not cur_words:
            cur_words.append(w)
            continue

        prev_w = cur_words[-1]
        gap = w.start - prev_w.end
        dur = w.end - cur_words[0].start
        remaining = total_w - idx
        prev_txt = prev_w.word.strip()
        has_punct = prev_txt.endswith((".", ",", "!", "?", ";", ":"))

        should_split = (
            (gap >= 1.0) or
            (remaining >= 2 and (
                (gap >= pause_thresh) or
                (len(cur_words) >= max_words) or
                (dur >= max_duration and len(cur_words) >= 4) or
                (has_punct and len(cur_words) >= 4)
            ))
        )

        if should_split:
            line_txt = "".join(x.word for x in cur_words).strip()
            if line_txt:
                refined.append((cur_words[0].start, prev_w.end, line_txt))
            cur_words = [w]
        else:
            cur_words.append(w)

    if cur_words:
        line_txt = "".join(x.word for x in cur_words).strip()
        if line_txt:
            refined.append((cur_words[0].start, cur_words[-1].end, line_txt))

    return refined


def handle(payload):
    global _WHISPER_MODEL, _WHISPER_KEY
    try:
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        warnings.filterwarnings("ignore", message=".*symlinks.*")
        ensure_cuda_dlls()
        _patch_av_open()

        import numpy as np
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

            # Read 16kHz mono PCM directly into float32 numpy array
            with wave.open(wav_16k, "rb") as wf:
                raw_pcm = wf.readframes(wf.getnframes())
                audio_np = np.frombuffer(raw_pcm, dtype=np.int16).astype(np.float32) / 32768.0

            key = f"{model_tier}_cuda"
            if _WHISPER_MODEL is None or _WHISPER_KEY != key:
                log_event(f"NEURAL_LOAD: WHISPER_{model_tier.upper()} on GPU (CUDA_FLOAT16)", level="info", path=input_path)
                _WHISPER_MODEL = WhisperModel(model_tier, device="cuda", compute_type="float16")
                _WHISPER_KEY = key

            log_event("[PROGRESS: 45]", path=input_path)
            lang_arg = None if lang == "AUTO" else lang.lower()

            # Disable aggressive speech-only Silero VAD so music/vocals/background audio aren't stripped,
            # and use word_timestamps + hallucination_silence_threshold for frame-accurate subtitle lines.
            segments_gen, info = _WHISPER_MODEL.transcribe(
                audio_np,
                language=lang_arg,
                beam_size=5,
                vad_filter=False,
                word_timestamps=True,
                condition_on_previous_text=False,
                no_speech_threshold=0.9,
                log_prob_threshold=None,
                hallucination_silence_threshold=2.0
            )

            srt_blocks = []
            txt_lines = []
            duration = getattr(info, "duration", 0) or (len(audio_np) / 16000.0) or 1.0
            sub_idx = 0

            for seg in segments_gen:
                sub_items = _split_segment_words(seg)
                for st, en, text in sub_items:
                    if text:
                        sub_idx += 1
                        start_ts = _format_srt_timestamp(st)
                        end_ts = _format_srt_timestamp(en)
                        srt_blocks.append(f"{sub_idx}\n{start_ts} --> {end_ts}\n{text}")
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
