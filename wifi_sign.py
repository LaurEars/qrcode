#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "qrcode[pil]>=7.4.2",
#   "pillow>=10.0.0",
# ]
# ///

from __future__ import annotations

import argparse
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont


def escape_wifi_value(value: str) -> str:
    for ch in ["\\", ";", ",", ":", '"']:
        value = value.replace(ch, "\\" + ch)
    return value


def build_wifi_payload(ssid: str, password: str, security: str, hidden: bool) -> str:
    sec = "nopass" if security.lower() == "nopass" else security.upper()

    parts = [f"WIFI:T:{sec};", f"S:{escape_wifi_value(ssid)};"]
    if sec != "nopass":
        parts.append(f"P:{escape_wifi_value(password)};")
    if hidden:
        parts.append("H:true;")
    parts.append(";")
    return "".join(parts)


def make_qr(payload: str, size: int = 720) -> Image.Image:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    # Whole pixels per module; resampling leaves modules uneven and hurts scanning.
    modules = qr.modules_count + 2 * qr.border
    qr.box_size = max(1, round(size / modules))
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def center_text(draw, text, y, font, width, fill):
    _, h = text_size(draw, text, font)
    x = (width - text_size(draw, text, font)[0]) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return h


def draw_contactless(draw, cx, cy, radius, color):
    """Draw the ')))' contactless / tap symbol, opening to the right."""
    stroke = max(3, int(radius * 0.22))
    for frac in (0.42, 0.72, 1.0):
        r = radius * frac
        draw.arc(
            (cx - r, cy - r, cx + r, cy + r),
            start=-52, end=52, fill=color, width=stroke,
        )


def draw_tap_line(draw, cy, width, font, text, text_color, icon_color):
    """Contactless glyph + tap text, centered as one unit. Returns its height."""
    tw, th = text_size(draw, text, font)
    icon_r = th * 0.5
    icon_w = icon_r * 1.15
    gap = th * 0.9
    total = icon_w + gap + tw
    x0 = (width - total) / 2
    draw_contactless(draw, x0 + icon_r * 0.55, cy + th / 2, icon_r, icon_color)
    draw.text((x0 + icon_w + gap, cy), text, font=font, fill=text_color)
    return th


def create_sign(ssid, password, security, hidden, output_path: Path,
                tap=False, tap_text="Scan or tap to connect", dpi=600):
    # 4 x 6 inches (portrait) so it prints to fit the frame exactly.
    # The layout is authored at 300 DPI; px() scales every dimension to the
    # requested DPI so higher-resolution renders keep the same proportions.
    s = dpi / 300
    px = lambda v: int(round(v * s))
    width, height = 4 * dpi, 6 * dpi

    bg = (245, 242, 235)
    panel = (255, 255, 255)
    ink = (30, 30, 30)
    soft = (120, 120, 120)
    border = (210, 205, 195)
    accent = (176, 108, 46)  # warm tone for the tap glyph

    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)

    margin = px(70)
    draw.rounded_rectangle(
        (margin, margin, width - margin, height - margin),
        radius=px(30),
        fill=panel,
        outline=border,
        width=max(1, px(4)),
    )

    label_font = load_font(px(30), bold=True)
    value_font = load_font(px(46))
    tap_font = load_font(px(40), bold=True)

    payload = build_wifi_payload(ssid, password, security, hidden)
    qr = make_qr(payload, size=px(720))

    pw_display = "No password" if security.lower() == "nopass" else password

    # Build the text block as (kind, ...) steps, measure its height, then draw it
    # vertically centered in the space beneath the QR so nothing floats.
    steps = [
        ("text", "Network", label_font, soft),
        ("gap", px(12)),
        ("text", ssid, value_font, ink),
        ("gap", px(46)),
        ("text", "Password", label_font, soft),
        ("gap", px(12)),
        ("text", pw_display, value_font, ink),
    ]
    if tap:
        steps += [
            ("gap", px(92)),
            ("tap", tap_text),
        ]

    def step_height(step):
        kind = step[0]
        if kind == "gap":
            return step[1]
        if kind == "text":
            return text_size(draw, step[1], step[2])[1]
        if kind == "tap":
            return text_size(draw, step[1], tap_font)[1]
        return 0

    # Center the QR + text as one group so it sits evenly in the frame.
    gap_qr_text = px(90)
    block_h = sum(step_height(s) for s in steps)
    group_h = qr.height + gap_qr_text + block_h
    qr_y = margin + (height - 2 * margin - group_h) // 2

    image.paste(qr, ((width - qr.width) // 2, qr_y))
    y = qr_y + qr.height + gap_qr_text

    for step in steps:
        kind = step[0]
        if kind == "gap":
            y += step[1]
        elif kind == "text":
            y += center_text(draw, step[1], y, step[2], width, step[3])
        elif kind == "tap":
            y += draw_tap_line(draw, y, width, tap_font, step[1], ink, accent)

    image.save(output_path, dpi=(dpi, dpi))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--ssid", required=True)
    p.add_argument("--password", default="")
    p.add_argument("--security", default="WPA")
    p.add_argument("--hidden", action="store_true")
    p.add_argument("--tap", action="store_true",
                   help="Show a 'tap to connect' line for the NFC chip in the frame")
    p.add_argument("--tap-text", default=None,
                   help="Custom wording for the tap line (implies --tap)")
    p.add_argument("--dpi", type=int, default=600,
                   help="Print resolution (default: 600)")
    p.add_argument("--output", default="wifi_sign.png")
    return p.parse_args()


def main():
    args = parse_args()

    if args.security.lower() != "nopass" and not args.password:
        raise SystemExit("Password required unless using nopass")

    # --tap-text on its own is enough to opt in; otherwise use the default wording.
    show_tap = args.tap or args.tap_text is not None
    tap_text = args.tap_text or "Scan or tap to connect"

    create_sign(
        args.ssid,
        args.password,
        args.security,
        args.hidden,
        Path(args.output),
        tap=show_tap,
        tap_text=tap_text,
        dpi=args.dpi,
    )

    print(f"Saved: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
