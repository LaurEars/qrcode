#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "qrcode[pil]>=7.4.2",
# ]
# ///

"""
Generate a QR code image from any URL.

Usage:
  uv run url_qr.py --url "https://example.com" --output url_qr.png
  uv run url_qr.py --url "https://example.com" --show
"""

from __future__ import annotations

import argparse
from pathlib import Path

import qrcode


def generate_qr(url: str, output_path: Path) -> None:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a QR code image from a URL.")
    p.add_argument("--url", required=True, help="URL to encode")
    p.add_argument("--output", default="url_qr.png", help="Output image path (default: url_qr.png)")
    p.add_argument("--show", action="store_true", help="Open the image after saving")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    output_path = Path(args.output)
    generate_qr(args.url, output_path)
    print(f"Saved QR code to: {output_path.resolve()}")

    if args.show:
        try:
            from PIL import Image

            Image.open(output_path).show()
        except Exception as exc:
            print(f"Could not open image viewer: {exc}")


if __name__ == "__main__":
    main()
