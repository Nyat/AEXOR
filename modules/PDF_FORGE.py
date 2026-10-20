import os
from PIL import Image
from utils import log_event


def handle(payload):
    try:
        import fitz  # PyMuPDF

        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        output_dir = payload.get("output_dir") or (os.path.dirname(output_path) if output_path else "./output")
        pdf_mode = str(payload.get("pdf_mode", "AUTO")).upper()
        dpi = int(payload.get("pdf_dpi", 200))
        batch_files = payload.get("batch_files") or ([input_path] if input_path else [])

        os.makedirs(output_dir, exist_ok=True)
        ext = os.path.splitext(input_path)[1].lower() if input_path else ""

        # Determine effective mode
        if pdf_mode == "AUTO":
            effective_mode = "PDF_TO_IMAGES" if ext == ".pdf" else "IMAGES_TO_PDF"
        else:
            effective_mode = pdf_mode

        log_event("[PROGRESS: 15]", path=input_path)

        if effective_mode == "PDF_TO_IMAGES":
            if ext != ".pdf":
                return {"status": "ERROR", "message": "Selected file is not a PDF document."}
            doc = fitz.open(input_path)
            total_pages = len(doc)
            if total_pages == 0:
                doc.close()
                return {"status": "ERROR", "message": "PDF contains 0 pages."}

            base_name = os.path.splitext(os.path.basename(input_path))[0]
            zoom = max(1.0, dpi / 72.0)
            mat = fitz.Matrix(zoom, zoom)

            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=mat, alpha=False)
                page_out = os.path.join(output_dir, f"{base_name}_page_{i + 1:03d}.png")
                pix.save(page_out)
                prog = 15 + int(((i + 1) / total_pages) * 80)
                log_event(f"[PROGRESS: {prog}]", path=input_path)

            doc.close()
            log_event("[PROGRESS: 100]", path=input_path)
            return {"status": "SUCCESS", "message": f"Exported {total_pages} PDF pages at {dpi} DPI."}

        elif effective_mode == "COMPRESS_PDF":
            if ext != ".pdf":
                return {"status": "ERROR", "message": "COMPRESS_PDF requires a .pdf input file."}
            orig_size = os.path.getsize(input_path)
            doc = fitz.open(input_path)
            log_event("[PROGRESS: 55]", path=input_path)
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            new_size = os.path.getsize(output_path)
            saved_pct = max(0.0, (1.0 - (new_size / float(max(1, orig_size)))) * 100.0)
            log_event("[PROGRESS: 100]", path=input_path)
            return {"status": "SUCCESS", "message": f"PDF optimized ({saved_pct:.1f}% size reduction)."}

        else:
            # IMAGES_TO_PDF: Convert single or batch images into a single PDF
            img_files = [f for f in batch_files if f and os.path.splitext(f)[1].lower() != ".pdf"]
            if not img_files:
                return {"status": "ERROR", "message": "No valid image files provided for IMAGES_TO_PDF."}

            doc = fitz.open()
            for idx, img_path in enumerate(img_files):
                pil_img = Image.open(img_path).convert("RGB")
                import io
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=92)
                img_bytes = buf.getvalue()

                page = doc.new_page(width=pil_img.width, height=pil_img.height)
                page.insert_image(fitz.Rect(0, 0, pil_img.width, pil_img.height), stream=img_bytes)
                prog = 15 + int(((idx + 1) / len(img_files)) * 75)
                log_event(f"[PROGRESS: {prog}]", path=input_path)

            doc.save(output_path, garbage=3, deflate=True)
            doc.close()
            log_event("[PROGRESS: 100]", path=input_path)
            return {"status": "SUCCESS", "message": f"Compiled {len(img_files)} image(s) into {os.path.basename(output_path)}."}

    except Exception as e:
        log_event(f"PDF_FORGE_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"PDF_FORGE_FAILURE: {str(e)}"}
