#!/usr/bin/env python3
"""
StreamCam Core - Local Network Webcam Streamer (importable module)

This is the original server.py logic, refactored so it can be started/stopped
programmatically by the tray app instead of being run as a standalone script.

Requirements: pip install flask opencv-python pyopenssl
"""

import cv2
import socket
import threading
import ssl
import os
import subprocess
from flask import Flask, Response, render_template_string
from datetime import datetime

# ─── Configuration ──────────────────────────────────────────────────────────

CAMERA_INDEX  = 0
STREAM_WIDTH  = 1280
STREAM_HEIGHT = 720
STREAM_FPS    = 30
JPEG_QUALITY  = 85
PORT_HTTP     = 8080
PORT_HTTPS    = 8443
USE_HTTPS     = False

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>StreamCam</title>
<style>
  :root { --bg:#0a0a0f; --surface:#13131a; --border:#1e1e2e; --rec:#ff2d55;
    --rec-glow:rgba(255,45,85,.35); --green:#30d158; --text:#f0f0f5; --muted:#6e6e80;
    --font:'SF Pro Display',-apple-system,'Segoe UI',sans-serif; }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100dvh;
    display:flex;flex-direction:column;align-items:center;overflow-x:hidden;}
  header{width:100%;display:flex;align-items:center;justify-content:space-between;
    padding:14px 20px;border-bottom:1px solid var(--border);position:sticky;top:0;
    background:var(--bg);z-index:10;}
  .logo{display:flex;align-items:center;gap:8px;font-size:17px;font-weight:700;}
  .logo-dot{width:10px;height:10px;border-radius:50%;background:var(--green);
    box-shadow:0 0 6px var(--green);}
  .live-badge{font-size:11px;font-weight:700;padding:3px 8px;border-radius:4px;
    background:rgba(48,209,88,.12);color:var(--green);border:1px solid rgba(48,209,88,.25);}
  .video-wrap{width:100%;max-width:900px;padding:16px;display:flex;flex-direction:column;gap:12px;}
  .video-shell{position:relative;width:100%;aspect-ratio:16/9;background:#000;
    border-radius:14px;overflow:hidden;border:1px solid var(--border);}
  #stream{width:100%;height:100%;object-fit:cover;display:block;}
  .info-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;
    padding:14px 16px;font-size:13px;color:var(--muted);}
</style>
</head>
<body>
<header>
  <div class="logo"><div class="logo-dot"></div>StreamCam</div>
  <div class="live-badge">LIVE</div>
</header>
<div class="video-wrap">
  <div class="video-shell"><img id="stream" src="/stream" alt="Live feed"></div>
  <div class="info-card">Served from the StreamCam tray app. Point the mobile app at this device's IP.</div>
</div>
<script>
  const img = document.getElementById('stream');
  function reconnect(){ img.src = "/stream?t=" + Date.now(); }
  document.addEventListener('visibilitychange', () => { if (!document.hidden) reconnect(); });
  img.onerror = () => setTimeout(reconnect, 1000);
</script>
</body>
</html>
"""

# ─── Camera Thread ───────────────────────────────────────────────────────────

class Camera:
    def __init__(self, index=0):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, STREAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, STREAM_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, STREAM_FPS)
        self._frame = None
        self._lock = threading.Lock()
        self._active = True
        threading.Thread(target=self._capture, daemon=True).start()

    def _capture(self):
        while self._active:
            ok, frame = self.cap.read()
            if ok:
                ok2, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if ok2:
                    with self._lock:
                        self._frame = buf.tobytes()

    def get_frame(self):
        with self._lock:
            return self._frame

    def release(self):
        self._active = False
        self.cap.release()


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def generate_self_signed_cert():
    cert_file = '/tmp/streamcam.crt'
    key_file = '/tmp/streamcam.key'
    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', key_file, '-out', cert_file,
            '-days', '1', '-nodes', '-subj', '/CN=streamcam.local'
        ], check=True, capture_output=True)
    return cert_file, key_file


class StreamCamServer:
    """Wraps the Flask app + camera so it can be started/stopped from the tray app."""

    def __init__(self):
        self.camera = None
        self.app = None
        self._http_thread = None
        self._https_thread = None
        self.running = False

    def _gen_frames(self):
        while self.running:
            frame = self.camera.get_frame()
            if frame:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def _build_app(self):
        app = Flask(__name__)

        @app.route('/')
        def index():
            return render_template_string(HTML)

        @app.route('/stream')
        def stream():
            return Response(
                self._gen_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame',
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Access-Control-Allow-Origin': '*',
                }
            )

        @app.route('/health')
        def health():
            return {'status': 'ok', 'timestamp': datetime.now().isoformat()}

        return app

    def start(self):
        if self.running:
            return
        self.camera = Camera(CAMERA_INDEX)
        self.app = self._build_app()
        self.running = True

        def run_http():
            self.app.run(host='0.0.0.0', port=PORT_HTTP, debug=False, use_reloader=False)

        self._http_thread = threading.Thread(target=run_http, daemon=True)
        self._http_thread.start()

        if USE_HTTPS:
            try:
                cert, key = generate_self_signed_cert()

                def run_https():
                    self.app.run(host='0.0.0.0', port=PORT_HTTPS, ssl_context=(cert, key),
                                  debug=False, use_reloader=False)

                self._https_thread = threading.Thread(target=run_https, daemon=True)
                self._https_thread.start()
            except Exception:
                pass

    def stop(self):
        self.running = False
        if self.camera:
            self.camera.release()
        # Flask's dev server threads are daemonized; they die with the process.
        # For a clean stop within the same process we just mark running=False
        # so the frame generator exits; the tray app fully tears down on Quit.

    def local_url(self):
        return f"http://{get_local_ip()}:{PORT_HTTP}"
