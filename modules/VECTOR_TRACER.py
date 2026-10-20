import os
import tempfile
from PIL import Image
from utils import log_event


def handle(payload):
    try:
        import vtracer

        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        colormode = str(payload.get("vector_colormode", "color")).lower()
        preset = str(payload.get("vector_preset", "POSTER")).upper()

        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        log_event("[PROGRESS: 10]", path=input_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Convert source image (including HEIC/WEBP) to a temporary PNG for vtracer
        img = Image.open(input_path).convert("RGBA")
        if max(img.width, img.height) > 2500:
            img.thumbnail((2500, 2500), Image.Resampling.LANCZOS)

        log_event("[PROGRESS: 35]", path=input_path)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_png = tmp.name
        try:
            img.save(tmp_png, "PNG")
            log_event("[PROGRESS: 55]", path=input_path)

            if preset == "LOGO_SHARP":
                filter_speckle = 8
                color_precision = 8
                layer_difference = 24
                corner_threshold = 45
            elif preset == "PHOTO_DETAILED":
                filter_speckle = 2
                color_precision = 8
                layer_difference = 8
                corner_threshold = 60
            else:
                filter_speckle = 4
                color_precision = 6
                layer_difference = 16
                corner_threshold = 60

            vtracer.convert_image_to_svg_py(
                tmp_png,
                output_path,
                colormode="binary" if colormode == "binary" else "color",
                hierarchical="stacked",
                mode="spline",
                filter_speckle=filter_speckle,
                color_precision=color_precision,
                layer_difference=layer_difference,
                corner_threshold=corner_threshold,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3
            )
        finally:
            if os.path.exists(tmp_png):
                try:
                    os.remove(tmp_png)
                except Exception:
                    pass

        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Vectorized to SVG ({colormode.upper()} / {preset})."}
    except Exception as e:
        log_event(f"VECTOR_TRACER_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"VECTOR_TRACER_FAILURE: {str(e)}"}
