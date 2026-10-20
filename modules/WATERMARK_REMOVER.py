import os
from PIL import Image
from utils import log_event


def handle(payload):
    try:
        import cv2
        import numpy as np

        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        zone = str(payload.get("wm_zone", "BOTTOM_RIGHT")).upper()
        algo = str(payload.get("wm_algo", "TELEA")).upper()

        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        log_event("[PROGRESS: 10]", path=input_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        pil_img = Image.open(input_path).convert("RGB")
        img_rgb = np.array(pil_img)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        h, w = img_bgr.shape[:2]
        log_event("[PROGRESS: 30]", path=input_path)

        mask = np.zeros((h, w), dtype=np.uint8)

        # Define target region ROI based on selected zone
        pad_x = max(16, int(w * 0.28))
        pad_y = max(16, int(h * 0.16))
        margin = max(4, int(min(w, h) * 0.01))

        if zone == "BOTTOM_RIGHT":
            roi_x1, roi_y1, roi_x2, roi_y2 = w - pad_x, h - pad_y, w - margin, h - margin
        elif zone == "BOTTOM_LEFT":
            roi_x1, roi_y1, roi_x2, roi_y2 = margin, h - pad_y, pad_x, h - margin
        elif zone == "TOP_RIGHT":
            roi_x1, roi_y1, roi_x2, roi_y2 = w - pad_x, margin, w - margin, pad_y
        elif zone == "TOP_LEFT":
            roi_x1, roi_y1, roi_x2, roi_y2 = margin, margin, pad_x, pad_y
        elif zone == "CENTER_STAMP":
            cw, ch = int(w * 0.45), int(h * 0.25)
            roi_x1, roi_y1 = (w - cw) // 2, (h - ch) // 2
            roi_x2, roi_y2 = roi_x1 + cw, roi_y1 + ch
        else:
            # AUTO_CORNERS: scan all 4 corners for high-frequency text/watermark edges
            roi_x1, roi_y1, roi_x2, roi_y2 = 0, 0, w, h

        log_event("[PROGRESS: 50]", path=input_path)

        if zone == "AUTO_DETECT":
            # Scan all 4 corner boxes for text/logo stroke contrast
            corners = [
                (w - pad_x, h - pad_y, w - margin, h - margin),
                (margin, h - pad_y, pad_x, h - margin),
                (w - pad_x, margin, w - margin, pad_y),
                (margin, margin, pad_x, pad_y),
            ]
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
            blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
            combined = cv2.add(tophat, blackhat)

            best_score = -1
            best_c = corners[0]
            for (cx1, cy1, cx2, cy2) in corners:
                sub = combined[cy1:cy2, cx1:cx2]
                score = float(np.percentile(sub, 95)) if sub.size > 0 else 0
                if score > best_score:
                    best_score = score
                    best_c = (cx1, cy1, cx2, cy2)
            roi_x1, roi_y1, roi_x2, roi_y2 = best_c

        roi = img_bgr[roi_y1:roi_y2, roi_x1:roi_x2]
        if roi.size > 0:
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            ksize = max(5, int(min(w, h) * 0.015) | 1)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
            tophat = cv2.morphologyEx(roi_gray, cv2.MORPH_TOPHAT, kernel)
            blackhat = cv2.morphologyEx(roi_gray, cv2.MORPH_BLACKHAT, kernel)
            stroke = cv2.add(tophat, blackhat)
            _, thresh = cv2.threshold(stroke, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            dilate_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            roi_mask = cv2.dilate(thresh, dilate_k, iterations=2)

            # If threshold found very few pixels, fallback to smooth box mask in the corner
            if np.count_nonzero(roi_mask) < (roi.shape[0] * roi.shape[1] * 0.01):
                roi_mask[:] = 255
            mask[roi_y1:roi_y2, roi_x1:roi_x2] = roi_mask

        log_event("[PROGRESS: 75]", path=input_path)
        inpaint_flag = cv2.INPAINT_NS if algo == "NS" else cv2.INPAINT_TELEA
        radius = max(5, int(min(w, h) * 0.008))
        cleaned_bgr = cv2.inpaint(img_bgr, mask, radius, inpaint_flag)

        log_event("[PROGRESS: 90]", path=input_path)
        cleaned_rgb = cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB)
        out_img = Image.fromarray(cleaned_rgb)
        out_img.save(output_path, "WEBP", quality=95)

        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Watermark region ({zone}) inpainted via {algo}."}
    except Exception as e:
        log_event(f"WATERMARK_REMOVER_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"WATERMARK_REMOVER_FAILURE: {str(e)}"}
