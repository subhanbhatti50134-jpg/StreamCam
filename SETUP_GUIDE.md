# StreamCam — Deployment Guide

## What You're Building

```
Laptop (webcam) ──── Flask/MJPEG ──── Wi-Fi ──── iPhone / Android
                      port 8080 (HTTP)
                      port 8443 (HTTPS)
```

The laptop captures JPEG frames from the webcam via OpenCV and pushes them
as an MJPEG stream. The mobile browser draws each frame to a canvas, then
MediaRecorder encodes and saves the video locally on the device.

---

## 1 — Install Dependencies

```bash
pip install flask opencv-python pyopenssl
# Also needs the openssl CLI (pre-installed on macOS/Linux)
# Windows users: install OpenSSL from https://slproweb.com/products/Win32OpenSSL.html
```

---

## 2 — Run the Server

```bash
python server.py
```

You'll see output like:

```
═══════════════════════════════════════════════════════
  StreamCam Server
═══════════════════════════════════════════════════════
  Local IP detected: 192.168.1.42

  HTTP  (Android/Desktop): http://192.168.1.42:8080
  HTTPS (iOS Safari):      https://192.168.1.42:8443
═══════════════════════════════════════════════════════
```

---

## 3 — Find Your IP Manually (if needed)

**macOS:**
```bash
ipconfig getifaddr en0       # Wi-Fi
```

**Linux:**
```bash
hostname -I | awk '{print $1}'
```

**Windows:**
```powershell
ipconfig | findstr "IPv4"
```

Use the `192.168.x.x` or `10.x.x.x` address — **not** 127.0.0.1.

---

## 4 — Connect from Android (Chrome)

1. Open Chrome on Android
2. Navigate to: `http://192.168.1.42:8080`  ← use your actual IP
3. The live stream appears immediately
4. Tap **Start Recording** → tap **Stop Recording**
5. The `.webm` file downloads automatically to Downloads/

> **Codec used:** VP8 or VP9 / WebM — natively supported in Chrome

---

## 5 — Connect from iPhone (Safari)

iOS Safari **requires HTTPS** to allow file downloads via blobs.

**Step A — Trust the certificate (one time only):**
1. Open Safari on iPhone
2. Navigate to: `https://192.168.1.42:8443`
3. Safari shows a security warning → tap **Show Details** → **visit this website**
4. A system prompt appears — tap **Visit Website**, then go to:
   **Settings → General → VPN & Device Management → [the certificate] → Trust**

**Step B — Record:**
1. Return to Safari, reload the HTTPS URL
2. Stream is live — tap **Start Recording**
3. Tap **Stop Recording**
4. Safari's download manager saves the `.mp4` to Files → On My iPhone → Downloads

> **Codec used:** H.264 / MP4 — Safari's preferred format

---

## 6 — iOS Alternative: Use the HTTP URL

If you don't want to trust the cert, use HTTP on iOS **but** save via Share Sheet:

1. Open `http://192.168.1.42:8080` in Safari
2. Record as usual
3. When you tap Stop, if the download doesn't auto-save, Safari shows
   a "Download" prompt in the address bar area — tap it → Save to Files

---

## 7 — Troubleshooting

| Problem | Fix |
|---------|-----|
| Black/no video | Wrong camera index — edit `CAMERA_INDEX = 1` in server.py |
| Can't connect from phone | Ensure laptop and phone are on same Wi-Fi; check firewall allows ports 8080/8443 |
| Recording button does nothing | Open browser console (Android: chrome://inspect, iOS: Safari dev tools) |
| iOS download not working | Must use HTTPS; trust cert via Settings as described above |
| Stream is choppy | Lower `JPEG_QUALITY` to 60 or `STREAM_FPS` to 15 in server.py |
| `openssl` not found | Install OpenSSL or set `USE_HTTPS = False` in server.py |

---

## 8 — macOS Firewall Note

If on macOS and the phone can't connect:

```
System Settings → Network → Firewall → Options
→ Allow incoming connections for Python
```

Or temporarily disable the firewall for testing.

---

## Architecture Deep-Dive

### Why MJPEG instead of WebRTC or HLS?

| Method | Pros | Cons |
|--------|------|------|
| **MJPEG (this app)** | Zero setup, works everywhere, single file | Higher bandwidth than H.264 |
| WebRTC (aiortc) | Low latency, native codec | Complex signaling server needed |
| HLS (ffmpeg) | Great codec support | 2-10s latency, requires ffmpeg |

MJPEG is the sweet spot for local network streaming: it works in every browser
with no plugins, no codec negotiation, and a single Python file.

### Why canvas capture for recording?

MJPEG `<img>` tags can't be directly captured by `MediaRecorder`. The canvas
bridge pattern:

```
<img src="/stream"> → requestAnimationFrame → canvas.drawImage() 
→ canvas.captureStream(30fps) → MediaRecorder → Blob → download
```

This is fully local — no data leaves the device after the stream arrives.

### Codec selection logic

```
iOS Safari   → video/mp4;codecs=avc1  → saved as .mp4
Android Chrome → video/webm;codecs=vp9 → saved as .webm
Desktop Chrome → video/webm;codecs=vp9 → saved as .webm
Firefox       → video/webm;codecs=vp8 → saved as .webm
```

The JS auto-detects via `MediaRecorder.isTypeSupported()`, so it always
picks the best format for the current browser.
