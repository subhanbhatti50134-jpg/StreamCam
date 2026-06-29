#!/usr/bin/env python3
"""
StreamCam Server - Local Network Webcam Streamer
Serves MJPEG stream over local Wi-Fi with HTTPS support for mobile browsers.

Requirements: pip install flask opencv-python pyopenssl
"""

import cv2
import socket
import threading
import ssl
import os
import sys
import subprocess
from flask import Flask, Response, render_template_string, request
from datetime import datetime

# ─── Configuration ──────────────────────────────────────────────────────────

CAMERA_INDEX   = 0          # 0 = default webcam; try 1, 2 if wrong camera
STREAM_WIDTH   = 1280
STREAM_HEIGHT  = 720
STREAM_FPS     = 30
JPEG_QUALITY   = 85         # 1-100; lower = faster, smaller
PORT_HTTP      = 8080       # plain HTTP fallback (Android Chrome works fine)
PORT_HTTPS     = 8443       # HTTPS for iOS Safari
USE_HTTPS      = False       # set False if you hit cert issues

# ─── HTML Frontend ──────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>StreamCam</title>
<style>
  :root {
    --bg:        #0a0a0f;
    --surface:   #13131a;
    --border:    #1e1e2e;
    --rec:       #ff2d55;
    --rec-glow:  rgba(255,45,85,.35);
    --green:     #30d158;
    --text:      #f0f0f5;
    --muted:     #6e6e80;
    --font:      'SF Pro Display', -apple-system, 'Segoe UI', sans-serif;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: env(safe-area-inset-top, 0) env(safe-area-inset-right, 0)
             env(safe-area-inset-bottom, 0) env(safe-area-inset-left, 0);
    overflow-x: hidden;
  }

  /* ── Header ── */
  header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0;
    background: var(--bg);
    z-index: 10;
  }
  .logo {
    display: flex; align-items: center; gap: 8px;
    font-size: 17px; font-weight: 700; letter-spacing: -.3px;
  }
  .logo-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 6px var(--green);
    animation: pulse-green 2s ease-in-out infinite;
  }
  @keyframes pulse-green {
    0%,100% { opacity:1; box-shadow: 0 0 6px var(--green); }
    50%      { opacity:.6; box-shadow: 0 0 12px var(--green); }
  }
  .live-badge {
    font-size: 11px; font-weight: 700; letter-spacing: .8px;
    padding: 3px 8px; border-radius: 4px;
    background: rgba(48,209,88,.12);
    color: var(--green);
    border: 1px solid rgba(48,209,88,.25);
  }
  #clock {
    font-size: 13px; color: var(--muted);
    font-variant-numeric: tabular-nums;
  }

  /* ── Video Area ── */
  .video-wrap {
    width: 100%;
    max-width: 900px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .video-shell {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    background: #000;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--border);
    box-shadow: 0 20px 60px rgba(0,0,0,.6);
  }
  #stream {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
  }
  .overlay-tl, .overlay-tr {
    position: absolute; top: 12px;
    padding: 4px 9px; border-radius: 5px;
    font-size: 11px; font-weight: 600; letter-spacing: .5px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
  .overlay-tl { left: 12px; background: rgba(0,0,0,.55); color: var(--muted); }
  .overlay-tr { right: 12px; }
  #rec-indicator {
    display: none;
    align-items: center; gap: 5px;
    background: rgba(255,45,85,.18);
    border: 1px solid rgba(255,45,85,.4);
    color: var(--rec);
  }
  #rec-indicator.active { display: flex; }
  .rec-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--rec);
    animation: blink 1s step-start infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }
  #rec-timer { font-variant-numeric: tabular-nums; }

  /* ── Controls ── */
  .controls {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  #rec-btn {
    flex: 1;
    display: flex; align-items: center; justify-content: center; gap: 10px;
    padding: 16px 24px;
    border: none; border-radius: 12px;
    font-family: var(--font);
    font-size: 16px; font-weight: 700;
    cursor: pointer;
    transition: transform .15s, box-shadow .15s, background .2s;
    -webkit-tap-highlight-color: transparent;
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
  }
  #rec-btn:active { transform: scale(.97); }
  #rec-btn.recording {
    background: var(--rec);
    border-color: var(--rec);
    box-shadow: 0 0 20px var(--rec-glow), 0 4px 12px rgba(255,45,85,.3);
  }
  #rec-btn .btn-icon {
    width: 16px; height: 16px;
    border-radius: 50%;
    background: currentColor;
    transition: border-radius .2s;
  }
  #rec-btn.recording .btn-icon {
    border-radius: 3px;
  }
  .info-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .info-row {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 13px;
  }
  .info-label { color: var(--muted); }
  .info-value { font-weight: 600; font-variant-numeric: tabular-nums; }
  .status-dot {
    display: inline-block;
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--green); margin-right: 5px;
    box-shadow: 0 0 5px var(--green);
  }
  #storage-status { color: var(--muted); font-size: 12px; }
  #log {
    font-size: 12px; color: var(--muted);
    padding: 2px 0;
    min-height: 18px;
  }
  .log-ok  { color: var(--green); }
  .log-err { color: var(--rec); }

  /* ── Formats legend ── */
  .format-note {
    font-size: 11px; color: var(--muted);
    text-align: center; padding-bottom: 20px;
  }
  .format-note span { color: var(--text); font-weight: 600; }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-dot"></div>
    StreamCam
  </div>
  <div class="live-badge">LIVE</div>
  <div id="clock">--:--:--</div>
</header>

<div class="video-wrap">

  <div class="video-shell">
    <img id="stream" src="/stream" alt="Live feed" />
    <div class="overlay-tl" id="res-tag">HD 720p</div>
    <div class="overlay-tr" id="rec-indicator">
      <div class="rec-dot"></div>
      REC <span id="rec-timer">00:00</span>
    </div>
  </div>

  <div class="controls">
    <button id="rec-btn" onclick="toggleRecording()">
      <div class="btn-icon"></div>
      <span id="btn-label">Start Recording</span>
    </button>
  </div>

  <div class="info-card">
    <div class="info-row">
      <span class="info-label">Stream source</span>
      <span class="info-value"><span class="status-dot"></span>Laptop webcam</span>
    </div>
    <div class="info-row">
      <span class="info-label">Codec (recording)</span>
      <span class="info-value" id="codec-info">Detecting…</span>
    </div>
    <div class="info-row">
      <span class="info-label">Chunks saved</span>
      <span class="info-value" id="chunk-count">0</span>
    </div>
    <div class="info-row">
      <span class="info-label">Recorded size</span>
      <span class="info-value" id="rec-size">0 KB</span>
    </div>
    <div id="log">Waiting to record…</div>
  </div>

  <p class="format-note">
    iOS Safari → <span>.mp4 (H.264)</span> &nbsp;·&nbsp; Android Chrome → <span>.webm (VP8)</span>
  </p>

</div>

<script>
// ─── Clock ───────────────────────────────────────────────────────────────────
const clockEl = document.getElementById('clock');
setInterval(() => {
  clockEl.textContent = new Date().toLocaleTimeString();
}, 1000);

// ─── Detect best supported codec ─────────────────────────────────────────────
function getSupportedMimeType() {
  const candidates = [
    { mime: 'video/mp4;codecs=avc1',      ext: 'mp4',  label: 'H.264 / MP4'  },
    { mime: 'video/mp4;codecs=h264',      ext: 'mp4',  label: 'H.264 / MP4'  },
    { mime: 'video/mp4',                  ext: 'mp4',  label: 'MP4'           },
    { mime: 'video/webm;codecs=vp9,opus', ext: 'webm', label: 'VP9 / WebM'    },
    { mime: 'video/webm;codecs=vp8,opus', ext: 'webm', label: 'VP8 / WebM'    },
    { mime: 'video/webm;codecs=vp9',      ext: 'webm', label: 'VP9 / WebM'    },
    { mime: 'video/webm;codecs=vp8',      ext: 'webm', label: 'VP8 / WebM'    },
    { mime: 'video/webm',                 ext: 'webm', label: 'WebM'          },
  ];
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c.mime)) return c;
  }
  return { mime: '', ext: 'webm', label: 'Browser default' };
}

const codecInfo = getSupportedMimeType();
document.getElementById('codec-info').textContent = codecInfo.label;

// ─── Recording state ─────────────────────────────────────────────────────────
let mediaRecorder  = null;
let recordedChunks = [];
let recInterval    = null;
let recSeconds     = 0;
let totalBytes     = 0;
let chunkCount     = 0;
let isRecording    = false;

const streamImg  = document.getElementById('stream');
const btn        = document.getElementById('rec-btn');
const btnLabel   = document.getElementById('btn-label');
const recInd     = document.getElementById('rec-indicator');
const recTimer   = document.getElementById('rec-timer');
const chunkEl    = document.getElementById('chunk-count');
const sizeEl     = document.getElementById('rec-size');
const logEl      = document.getElementById('log');

function log(msg, cls = '') {
  logEl.textContent = msg;
  logEl.className = cls;
}

function formatTime(s) {
  const m = Math.floor(s / 60).toString().padStart(2, '0');
  const sec = (s % 60).toString().padStart(2, '0');
  return `${m}:${sec}`;
}

function formatBytes(b) {
  if (b < 1024)       return b + ' B';
  if (b < 1048576)    return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(2) + ' MB';
}

// ─── Auto Reconnect Helper ───────────────────────────────────────────────────
function forceStreamReconnect() {
  console.log("Re-establishing live stream connection socket...");
  // Appending a timestamp query (?t=...) forces browsers to bypass cache and start a clean stream socket
  streamImg.src = "/stream?t=" + new Date().getTime();
}

// Automatically recover connection if the user leaves and returns to the browser app
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    forceStreamReconnect();
  }
});

// Recover if the browser native element catches an image socket failure
streamImg.onerror = () => {
  setTimeout(forceStreamReconnect, 1000);
};

// ─── Core: capture the MJPEG stream via canvas ───────────────────────────────
async function toggleRecording() {
  if (!isRecording) {
    await startRecording();
  } else {
    stopRecording();
  }
}

async function startRecording() {
  try {
    const imgEl = document.getElementById('stream');
    const canvas = document.createElement('canvas');
    canvas.width  = imgEl.naturalWidth  || 1280;
    canvas.height = imgEl.naturalHeight || 720;
    const ctx = canvas.getContext('2d');

    let rafId;
    function drawFrame() {
      try { ctx.drawImage(imgEl, 0, 0, canvas.width, canvas.height); }
      catch(e) {}
      rafId = requestAnimationFrame(drawFrame);
    }
    drawFrame();

    const canvasStream = canvas.captureStream(30);
    const opts = codecInfo.mime ? { mimeType: codecInfo.mime } : {};
    mediaRecorder = new MediaRecorder(canvasStream, opts);

    recordedChunks = [];
    totalBytes = 0;
    chunkCount = 0;

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        recordedChunks.push(e.data);
        totalBytes += e.data.size;
        chunkCount++;
        chunkEl.textContent = chunkCount;
        sizeEl.textContent  = formatBytes(totalBytes);
      }
    };

    mediaRecorder.onstop = () => {
      cancelAnimationFrame(rafId);
      saveRecording();
    };

    mediaRecorder.start(1000);
    isRecording = true;
    recSeconds  = 0;

    btn.classList.add('recording');
    btnLabel.textContent = 'Stop Recording';
    recInd.classList.add('active');

    recInterval = setInterval(() => {
      recSeconds++;
      recTimer.textContent = formatTime(recSeconds);
    }, 1000);

    log('Recording… frames captured via canvas', 'log-ok');
  } catch (err) {
    log('Error: ' + err.message, 'log-err');
    console.error(err);
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  clearInterval(recInterval);
  isRecording = false;

  btn.classList.remove('recording');
  btnLabel.textContent = 'Start Recording';
  recInd.classList.remove('active');
  log('Processing recording…');
}

function saveRecording() {
  if (!recordedChunks.length) {
    log('No data recorded.', 'log-err');
    forceStreamReconnect();
    return;
  }

  const blob = new Blob(recordedChunks, { type: codecInfo.mime || 'video/webm' });
  const ext  = codecInfo.ext;
  const ts   = new Date().toISOString().replace(/[:.]/g, '-').slice(0,19);
  const filename = `streamcam-${ts}.${ext}`;

  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();

  // Clean up resource link bindings
  setTimeout(() => {
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }, 3000);

  log(`✓ Saved as ${filename} (${formatBytes(blob.size)})`, 'log-ok');
  chunkEl.textContent = 0;
  sizeEl.textContent  = '0 KB';

  // FIX: Force a fresh stream socket reconnection after letting the file compilation pass
  setTimeout(forceStreamReconnect, 600);
}
</script>
</body>
</html>
"""

# ─── Camera Thread ───────────────────────────────────────────────────────────

class Camera:
    def __init__(self, index=0):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  STREAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, STREAM_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS,          STREAM_FPS)
        self._frame  = None
        self._lock   = threading.Lock()
        self._active = True
        threading.Thread(target=self._capture, daemon=True).start()

    def _capture(self):
        while self._active:
            ok, frame = self.cap.read()
            if ok:
                ok2, buf = cv2.imencode(
                    '.jpg', frame,
                    [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                )
                if ok2:
                    with self._lock:
                        self._frame = buf.tobytes()

    def get_frame(self):
        with self._lock:
            return self._frame

    def release(self):
        self._active = False
        self.cap.release()

camera = Camera(CAMERA_INDEX)

# ─── Flask App ───────────────────────────────────────────────────────────────

app = Flask(__name__)

def gen_frames():
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/stream')
def stream():
    return Response(
        gen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control':    'no-cache, no-store, must-revalidate',
            'Pragma':           'no-cache',
            'Expires':          '0',
            'Access-Control-Allow-Origin': '*',
        }
    )

@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}

# ─── SSL Self-Signed Cert (for iOS Safari) ───────────────────────────────────

def generate_self_signed_cert():
    """Generate a temporary self-signed cert using OpenSSL CLI."""
    cert_file = '/tmp/streamcam.crt'
    key_file  = '/tmp/streamcam.key'
    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        print("  Generating self-signed TLS certificate…")
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', key_file, '-out', cert_file,
            '-days', '1', '-nodes',
            '-subj', '/CN=streamcam.local'
        ], check=True, capture_output=True)
    return cert_file, key_file

# ─── Entry Point ─────────────────────────────────────────────────────────────

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

if __name__ == '__main__':
    local_ip = get_local_ip()

    print("\n" + "═"*55)
    print("  StreamCam Server")
    print("═"*55)
    print(f"  Local IP detected: {local_ip}")
    print()
    print(f"  HTTP  (Android/Desktop): http://{local_ip}:{PORT_HTTP}")
    if USE_HTTPS:
        print(f"  HTTPS (iOS Safari):    https://{local_ip}:{PORT_HTTPS}")
        print()
        print("  ⚠  iOS: you must trust the certificate once.")
        print("     Open the HTTPS URL → tap Advanced → Proceed anyway")
    print("═"*55 + "\n")

    if USE_HTTPS:
        try:
            cert, key = generate_self_signed_cert()
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(cert, key)

            import threading as _t
            def run_https():
                app.run(host='0.0.0.0', port=PORT_HTTPS, ssl_context=(cert, key),
                        debug=False, use_reloader=False)
            _t.Thread(target=run_https, daemon=True).start()
        except Exception as e:
            print(f"  HTTPS unavailable ({e}), HTTP only.\n")

    app.run(host='0.0.0.0', port=PORT_HTTP, debug=False, use_reloader=False)