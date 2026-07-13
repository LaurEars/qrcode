#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "qrcode[pil]>=7.4.2",
# ]
# ///

"""
Generate a Wi-Fi QR code image that guests can scan to join your network.

Usage:
  uv run wifi_qr.py --ssid "MyNetwork" --password "supersecret" --output wifi_q.png
  uv run wifi_qr.py --ssid "MyNetwork" --password "supersecret" --security WPA --show
  uv run wifi_qr.py --ssid "Guest WiFi" --password "" --security nopass

Notes:
- Supported security values: WPA, WEP, nopass
- Hidden networks are supported with --hidden
- Special characters in SSID/password are escaped correctly for Wi-Fi QR format
"""

from __future__ import annotations

import argparse
from pathlib import Path

import qrcode


def escape_wifi_value(value: str) -> str:
    """
    Escape characters required by the Wi-Fi QR code format.
    """
    for ch in ["\\", ";", ",", ":", '"']:
        value = value.replace(ch, "\\" + ch)
    return value


def build_wifi_payload(ssid: str, password: str, security: str, hidden: bool) -> str:
    """
    Build the Wi-Fi QR payload in the standard format:
    WIFI:T:WPA;S:MySSID;P:mypassword;H:false;;
    """
    sec = security.strip()

    if sec.lower() == "nopass":
        sec = "nopass"
    else:
        sec = sec.upper()

    escaped_ssid = escape_wifi_value(ssid)
    escaped_password = escape_wifi_value(password)

    parts = [f"WIFI:T:{sec};", f"S:{escaped_ssid};"]

    if sec != "nopass":
        parts.append(f"P:{escaped_password};")

    if hidden:
        parts.append("H:true;")

    parts.append(";")
    return "".join(parts)


def generate_qr(payload: str, output_path: Path) -> None:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Wi-Fi QR code image for guests."
    )
    parser.add_argument("--ssid", required=True, help="Wi-Fi network name")
    parser.add_argument(
        "--password",
        default="",
        help="Wi-Fi password. Leave empty for open networks.",
    )
    parser.add_argument(
        "--security",
        default="WPA",
        choices=["WPA", "WEP", "nopass", "wpa", "wep"],
        help="Wi-Fi security type (default: WPA)",
    )
    parser.add_argument(
        "--hidden",
        action="store_true",
        help="Mark the Wi-Fi network as hidden",
    )
    parser.add_argument(
        "--output",
        default="wifi_qr.png",
        help="Output image path (default: wifi_qr.png)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Open the generated QR code image after saving",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.security.lower() != "nopass" and not args.password:
        raise SystemExit(
            "Error: password is required unless --security nopass is used."
        )

    payload = build_wifi_payload(
        ssid=args.ssid,
        password=args.password,
        security=args.security,
        hidden=args.hidden,
    )

    output_path = Path(args.output)
    generate_qr(payload, output_path)

    print(f"Saved Wi-Fi QR code to: {output_path.resolve()}")
    print(f"QR payload: {payload}")

    if args.show:
        try:
            from PIL import Image

            Image.open(output_path).show()
        except Exception as exc:
            print(f"Could not open image viewer: {exc}")


if __name__ == "__main__":
    main()
