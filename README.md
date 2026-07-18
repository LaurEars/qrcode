# qrcode

<img src="repo_qr.png" alt="QR code linking to this repo" width="140" align="right">

Small scripts for generating QR codes as PNGs — plain URL codes, Wi-Fi join codes, and a printable Wi-Fi sign.

The scripts run via [uv](https://docs.astral.sh/uv/) (dependencies are declared inline, so there's nothing to install first).

## Scripts

| Script | What it makes |
| --- | --- |
| `url_qr.py` | A QR code from any URL |
| `wifi_qr.py` | A Wi-Fi QR code guests scan to join your network |
| `wifi_sign.py` | A printable 4×6" Wi-Fi sign (QR + network/password + optional "tap to connect") |

## URL QR code

```bash
uv run url_qr.py --url "https://example.com" --output url_qr.png
```

## Wi-Fi QR code

```bash
uv run wifi_qr.py --ssid "MyNetwork" --password "supersecret" --output wifi_qr.png
```

Open network (no password):

```bash
uv run wifi_qr.py --ssid "Guest WiFi" --security nopass --output wifi_qr.png
```

Useful flags: `--security {WPA,WEP,nopass}`, `--hidden`, `--show` (open the image after saving).

## Wi-Fi sign

A framed sign with the QR code, network name, and password. Sized to 4×6" so it prints to fill a standard photo frame.

```bash
uv run wifi_sign.py --ssid "MyNetwork" --password "supersecret" --output wifi_sign.png
```

Add a "tap to connect" line for an NFC chip in the frame:

```bash
uv run wifi_sign.py --ssid "MyNetwork" --password "supersecret" --tap --output wifi_sign.png
```

Customize the tap wording (implies `--tap`):

```bash
uv run wifi_sign.py --ssid "MyNetwork" --password "supersecret" \
  --tap-text "Tap phone to connect" --output wifi_sign.png
```

Renders at 600 DPI by default; use `--dpi` to change it.
