import os
import json
import logging
from PIL import Image
from utils import log_event, ensure_cuda_dlls

_OCR_ENGINE = None
_OCR_PROVIDER = None


def _get_ocr_engine(gpu_vendor="nvidia"):
    global _OCR_ENGINE, _OCR_PROVIDER
    ensure_cuda_dlls()

    import onnxruntime as ort
    avail = ort.get_available_providers()

    # Silence RapidOCR's internal warning logger so it never spams the console
    logging.getLogger("OrtInferSession").setLevel(logging.ERROR)

    from rapidocr_onnxruntime import RapidOCR

    if gpu_vendor == "nvidia" and "CUDAExecutionProvider" in avail:
        if _OCR_ENGINE is not None and _OCR_PROVIDER == "CUDAExecutionProvider":
            return _OCR_ENGINE
        _OCR_ENGINE = RapidOCR(
            det_use_cuda=True, cls_use_cuda=True, rec_use_cuda=True,
            det_use_dml=False, cls_use_dml=False, rec_use_dml=False
        )
        _OCR_PROVIDER = "CUDAExecutionProvider"
        log_event("NEURAL_LOAD: RAPID_OCR on NVIDIA CUDAExecutionProvider", level="info", path="SYSTEM")
        return _OCR_ENGINE

    if "DmlExecutionProvider" in avail:
        if _OCR_ENGINE is not None and _OCR_PROVIDER == "DmlExecutionProvider":
            return _OCR_ENGINE
        _OCR_ENGINE = RapidOCR(
            det_use_cuda=False, cls_use_cuda=False, rec_use_cuda=False,
            det_use_dml=True, cls_use_dml=True, rec_use_dml=True
        )
        _OCR_PROVIDER = "DmlExecutionProvider"
        log_event("NEURAL_LOAD: RAPID_OCR on DirectML GPU Provider", level="info", path="SYSTEM")
        return _OCR_ENGINE

    if "CUDAExecutionProvider" in avail:
        if _OCR_ENGINE is not None and _OCR_PROVIDER == "CUDAExecutionProvider":
            return _OCR_ENGINE
        _OCR_ENGINE = RapidOCR(
            det_use_cuda=True, cls_use_cuda=True, rec_use_cuda=True,
            det_use_dml=False, cls_use_dml=False, rec_use_dml=False
        )
        _OCR_PROVIDER = "CUDAExecutionProvider"
        log_event("NEURAL_LOAD: RAPID_OCR on CUDAExecutionProvider", level="info", path="SYSTEM")
        return _OCR_ENGINE

    raise RuntimeError(
        f"GPU ExecutionProvider not active (Available: {avail}). Re-install GPU_ACCEL in Module Manager."
    )


def handle(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        ocr_format = str(payload.get("ocr_format", "TXT")).upper()
        min_conf = float(payload.get("ocr_confidence", 0.5))
        gpu_vendor = payload.get("gpu_vendor", "nvidia")

        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        log_event("[PROGRESS: 10]", path=input_path)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        import numpy as np
        img = Image.open(input_path).convert("RGB")
        img_np = np.array(img)
        log_event("[PROGRESS: 30]", path=input_path)

        engine = _get_ocr_engine(gpu_vendor=gpu_vendor)
        log_event("[PROGRESS: 50]", path=input_path)

        result, _ = engine(img_np)
        log_event("[PROGRESS: 85]", path=input_path)

        lines = []
        structured = []
        if result:
            for item in result:
                box, text, score = item[0], str(item[1]), float(item[2])
                if score >= min_conf and text.strip():
                    lines.append(text.strip())
                    structured.append({
                        "text": text.strip(),
                        "confidence": round(score, 4),
                        "box": box
                    })

        if ocr_format == "JSON":
            content = json.dumps({
                "source": os.path.basename(input_path),
                "line_count": len(structured),
                "blocks": structured
            }, indent=2, ensure_ascii=False)
        elif ocr_format == "MD":
            header = f"# OCR Extraction: {os.path.basename(input_path)}\n\n"
            body = "\n\n".join(lines) if lines else "_No text detected._"
            content = header + body + "\n"
        else:
            content = "\n".join(lines) if lines else ""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        preview = " | ".join(lines[:3])
        if len(preview) > 90:
            preview = preview[:87] + "..."
        if preview:
            log_event(f"OCR_TEXT ({len(lines)} lines): {preview}", level="info", path=input_path)
        else:
            log_event("OCR_NOTICE: No readable text regions above confidence threshold.", level="info", path=input_path)

        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Extracted {len(lines)} text lines ({ocr_format}) via {_OCR_PROVIDER}."}
    except Exception as e:
        log_event(f"NEURAL_OCR_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"NEURAL_OCR_FAILURE: {str(e)}"}
