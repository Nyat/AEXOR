import os
import shutil
import subprocess
import tempfile
from utils import log_event, ensure_cuda_dlls

_DEMUCS_MODEL = None
_DEMUCS_DEVICE = None


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


def _save_stem_audio(wav_np, sr, out_path, fmt, ffmpeg_exe):
    import soundfile as sf
    if fmt == "WAV" or not ffmpeg_exe:
        sf.write(out_path, wav_np.T, sr, subtype="PCM_16")
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = tmp.name
        try:
            sf.write(tmp_wav, wav_np.T, sr, subtype="PCM_16")
            subprocess.run(
                [ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error", "-i", tmp_wav, "-acodec", "libmp3lame", "-b:a", "320k", out_path],
                check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
        finally:
            if os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass


def handle(payload):
    global _DEMUCS_MODEL, _DEMUCS_DEVICE
    try:
        ensure_cuda_dlls()
        import torch
        import soundfile as sf
        import numpy as np
        from demucs.pretrained import get_model
        from demucs.apply import apply_model

        input_path = payload.get("input_path")
        output_dir = payload.get("output_dir") or (os.path.dirname(payload.get("output_path", "")) or "./output")
        stem_mode = str(payload.get("stem_mode", "VOCALS_INSTRUMENTAL")).upper()
        audio_fmt = str(payload.get("stem_format", "MP3")).upper()

        if not input_path:
            return {"status": "ERROR", "message": "Missing input path."}

        os.makedirs(output_dir, exist_ok=True)
        ffmpeg_exe = _ensure_ffmpeg()
        if not ffmpeg_exe:
            return {"status": "ERROR", "message": "FFmpeg engine missing. Install DEMUCS_AI in Module Manager."}

        if torch.cuda.is_available():
            target_dev = torch.device("cuda")
            dev_label = "CUDA"
        else:
            try:
                import torch_directml
                target_dev = torch_directml.device()
                dev_label = "DIRECTML"
            except Exception:
                return {"status": "ERROR", "message": "GPU acceleration unavailable for Demucs. Install GPU_ACCEL in Module Manager."}

        log_event("[PROGRESS: 10]", path=input_path)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
            decoded_wav = tmp_in.name

        try:
            subprocess.run(
                [ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error", "-i", input_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", decoded_wav],
                check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            log_event("[PROGRESS: 25]", path=input_path)

            if _DEMUCS_MODEL is None or _DEMUCS_DEVICE != dev_label:
                log_event(f"NEURAL_LOAD: HTDEMUCS_4STEM on GPU ({dev_label})", level="info", path=input_path)
                _DEMUCS_MODEL = get_model("htdemucs")
                _DEMUCS_MODEL.to(target_dev)
                _DEMUCS_MODEL.eval()
                _DEMUCS_DEVICE = dev_label

            audio_data, sr = sf.read(decoded_wav, dtype="float32", always_2d=True)
            wav_tensor = torch.from_numpy(audio_data.T)
            if wav_tensor.shape[0] == 1:
                wav_tensor = wav_tensor.repeat(2, 1)
            elif wav_tensor.shape[0] > 2:
                wav_tensor = wav_tensor[:2, :]

            ref = wav_tensor.mean(0)
            wav_norm = (wav_tensor - ref.mean()) / (ref.std() + 1e-8)

            log_event("[PROGRESS: 45]", path=input_path)
            with torch.no_grad():
                sources = apply_model(
                    _DEMUCS_MODEL,
                    wav_norm[None],
                    device=target_dev,
                    shifts=1,
                    split=True,
                    overlap=0.25,
                    progress=False
                )[0]
                sources = sources * ref.std() + ref.mean()

            log_event("[PROGRESS: 85]", path=input_path)
            sources_np = sources.cpu().numpy()
            source_names = _DEMUCS_MODEL.sources
            stem_map = {name: sources_np[idx] for idx, name in enumerate(source_names)}

            base_name = os.path.splitext(os.path.basename(input_path))[0]
            ext_out = "wav" if audio_fmt == "WAV" else "mp3"
            saved_files = []

            if stem_mode == "4_STEMS":
                for s_name, s_arr in stem_map.items():
                    out_p = os.path.join(output_dir, f"{base_name}-{s_name}.{ext_out}")
                    _save_stem_audio(s_arr, sr, out_p, audio_fmt, ffmpeg_exe)
                    saved_files.append(os.path.basename(out_p))
            else:
                vocals_arr = stem_map.get("vocals")
                inst_arr = sum(arr for k, arr in stem_map.items() if k != "vocals")

                if stem_mode in ("VOCALS_INSTRUMENTAL", "VOCALS_ONLY") and vocals_arr is not None:
                    v_path = os.path.join(output_dir, f"{base_name}-vocals.{ext_out}")
                    _save_stem_audio(vocals_arr, sr, v_path, audio_fmt, ffmpeg_exe)
                    saved_files.append(os.path.basename(v_path))

                if stem_mode in ("VOCALS_INSTRUMENTAL", "INSTRUMENTAL_ONLY"):
                    i_path = os.path.join(output_dir, f"{base_name}-instrumental.{ext_out}")
                    _save_stem_audio(inst_arr, sr, i_path, audio_fmt, ffmpeg_exe)
                    saved_files.append(os.path.basename(i_path))

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            log_event("[PROGRESS: 100]", path=input_path)
            return {"status": "SUCCESS", "message": f"Separated stems: {', '.join(saved_files)}"}
        finally:
            if os.path.exists(decoded_wav):
                try:
                    os.remove(decoded_wav)
                except Exception:
                    pass
    except Exception as e:
        log_event(f"AUDIO_SEPARATOR_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"AUDIO_SEPARATOR_FAILURE: {str(e)}"}
