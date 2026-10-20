import os
from PIL import Image, ImageDraw, ImageFont
from utils import log_event


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def _luminance(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def handle(payload):
    try:
        input_path = payload.get("input_path")
        output_path = payload.get("output_path")
        swatch_count = int(payload.get("palette_count", 6))
        mode = str(payload.get("palette_mode", "STUDIO_CARD")).upper()

        if not input_path or not output_path:
            return {"status": "ERROR", "message": "Missing input or output path."}

        swatch_count = max(3, min(10, swatch_count))
        log_event("[PROGRESS: 10]", path=input_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        img = Image.open(input_path).convert("RGB")
        log_event("[PROGRESS: 30]", path=input_path)

        # Quantize image to extract dominant colors
        sample = img.copy()
        sample.thumbnail((300, 300), Image.Resampling.LANCZOS)
        quantized = sample.quantize(colors=swatch_count, method=Image.Quantize.MEDIANCUT)
        palette_raw = quantized.getpalette()
        color_counts = sorted(quantized.getcolors(), reverse=True)

        colors = []
        for _, idx in color_counts[:swatch_count]:
            r = palette_raw[idx * 3]
            g = palette_raw[idx * 3 + 1]
            b = palette_raw[idx * 3 + 2]
            colors.append((r, g, b))

        while len(colors) < swatch_count:
            colors.append((15, 15, 20))

        # Sort by luminance for a sleek studio gradient feel
        colors.sort(key=_luminance)
        hex_list = [_rgb_to_hex(c) for c in colors]
        log_event(f"PALETTE_EXTRACTED: {' '.join(hex_list)}", level="info", path=input_path)
        log_event("[PROGRESS: 65]", path=input_path)

        if mode == "SWATCH_GRID":
            card_w, card_h = 1600, 900
            canvas = Image.new("RGB", (card_w, card_h), (10, 10, 11))
            draw = ImageDraw.Draw(canvas)
            margin = 60
            gap = 20
            avail_w = card_w - (margin * 2) - (gap * (swatch_count - 1))
            sw_w = avail_w // swatch_count
            sw_h = card_h - (margin * 2) - 100

            for i, (rgb, hx) in enumerate(zip(colors, hex_list)):
                x1 = margin + i * (sw_w + gap)
                y1 = margin
                x2 = x1 + sw_w
                y2 = y1 + sw_h
                draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=rgb)
                draw.text((x1 + 12, y2 + 24), hx, fill=(255, 255, 255))
                draw.text((x1 + 12, y2 + 48), f"RGB({rgb[0]},{rgb[1]},{rgb[2]})", fill=(140, 140, 150))
            canvas.save(output_path, "PNG")
        else:
            # STUDIO_CARD or CARD_+_CSS: Original image + sleek palette footer
            target_w = max(1000, min(2400, img.width))
            scale = target_w / float(img.width)
            target_h = int(img.height * scale)
            resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

            footer_h = max(160, int(target_h * 0.22))
            pad = max(24, int(target_w * 0.025))
            canvas_w = target_w + pad * 2
            canvas_h = target_h + footer_h + pad * 3

            canvas = Image.new("RGB", (canvas_w, canvas_h), (10, 10, 11))
            canvas.paste(resized, (pad, pad))

            draw = ImageDraw.Draw(canvas)
            gap = max(10, int(target_w * 0.01))
            sw_w = (target_w - gap * (swatch_count - 1)) // swatch_count
            sw_y1 = pad * 2 + target_h
            sw_y2 = canvas_h - pad

            for i, (rgb, hx) in enumerate(zip(colors, hex_list)):
                x1 = pad + i * (sw_w + gap)
                x2 = x1 + sw_w if i < swatch_count - 1 else (pad + target_w)
                draw.rounded_rectangle([x1, sw_y1, x2, sw_y2], radius=10, fill=rgb)
                txt_color = (10, 10, 11) if _luminance(rgb) > 145 else (245, 245, 250)
                draw.text((x1 + 12, sw_y2 - 28), hx, fill=txt_color)

            canvas.save(output_path, "PNG")

            if mode == "CARD_+_CSS":
                css_path = os.path.splitext(output_path)[0] + ".css"
                css_lines = [":root {"]
                for idx, (rgb, hx) in enumerate(zip(colors, hex_list), 1):
                    css_lines.append(f"  --palette-color-{idx}: {hx}; /* rgb({rgb[0]}, {rgb[1]}, {rgb[2]}) */")
                css_lines.append("}\n")
                with open(css_path, "w", encoding="utf-8") as cf:
                    cf.write("\n".join(css_lines))

        log_event("[PROGRESS: 100]", path=input_path)
        return {"status": "SUCCESS", "message": f"Generated {swatch_count}-color palette ({', '.join(hex_list[:4])}...)."}
    except Exception as e:
        log_event(f"PALETTE_GEN_ERROR: {str(e)}", level="error", path=payload.get("input_path"))
        return {"status": "ERROR", "message": f"PALETTE_GENERATOR_FAILURE: {str(e)}"}
