/* StreamCam mobile app logic */

const STORAGE_KEY = 'streamcam_server_address';

const settingsScreen = document.getElementById('settings-screen');
const streamScreen   = document.getElementById('stream-screen');
const ipInput         = document.getElementById('ip-input');
const connectBtn      = document.getElementById('connect-btn');
const settingsError   = document.getElementById('settings-error');
const settingsBtn     = document.getElementById('settings-btn');
const streamImg       = document.getElementById('stream');
const connDot         = document.getElementById('conn-dot');
const connLabel       = document.getElementById('conn-label');
const serverAddrEl    = document.getElementById('server-addr');
const recBtn          = document.getElementById('rec-btn');
const btnLabel        = document.getElementById('btn-label');
const recInd           = document.getElementById('rec-indicator');
const recTimer         = document.getElementById('rec-timer');
const chunkEl          = document.getElementById('chunk-count');
const sizeEl            = document.getElementById('rec-size');
const logEl             = document.getElementById('log');

let currentAddress = null;
let isRecording = false;
let mediaRecorder = null;
let recordedChunks = [];
let totalBytes = 0;
let chunkCount = 0;
let recSeconds = 0;
let recInterval = null;

// ─── Cross-platform storage (Capacitor Preferences when available, else localStorage) ──

function isNative() {
  return typeof Capacitor !== 'undefined' && Capacitor.Plugins && Capacitor.Plugins.Preferences;
}

async function saveAddress(addr) {
  if (isNative()) {
    await Capacitor.Plugins.Preferences.set({ key: STORAGE_KEY, value: addr });
  } else {
    localStorage.setItem(STORAGE_KEY, addr);
  }
}

async function loadAddress() {
  if (isNative()) {
    const { value } = await Capacitor.Plugins.Preferences.get({ key: STORAGE_KEY });
    return value;
  }
  return localStorage.getItem(STORAGE_KEY);
}

async function clearAddress() {
  if (isNative()) {
    await Capacitor.Plugins.Preferences.remove({ key: STORAGE_KEY });
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

// ─── Screen management ────────────────────────────────────────────────────────

function showSettings(prefill) {
  streamScreen.classList.add('hidden');
  settingsScreen.classList.remove('hidden');
  settingsError.textContent = '';
  if (prefill) ipInput.value = prefill;
  ipInput.focus();
}

function showStream(addr) {
  settingsScreen.classList.add('hidden');
  streamScreen.classList.remove('hidden');
  serverAddrEl.textContent = addr;
  connectStream(addr);
}

function log(msg, cls) {
  logEl.textContent = msg;
  logEl.className = cls || '';
}

// ─── Connecting to the stream ─────────────────────────────────────────────────

function normalizeAddress(raw) {
  let addr = raw.trim();
  addr = addr.replace(/^https?:\/\//, '');
  addr = addr.replace(/\/$/, '');
  if (!addr.includes(':')) addr += ':8080';
  return addr;
}

function connectStream(addr) {
  currentAddress = addr;
  connLabel.textContent = 'Connecting…';
  connDot.style.background = '#6e6e80';
  reconnectStream();
}

function reconnectStream() {
  if (!currentAddress) return;
  streamImg.src = `http://${currentAddress}/stream?t=${Date.now()}`;
}

streamImg.onload = () => {
  connLabel.textContent = 'Live';
  connDot.style.background = '#30d158';
  connDot.style.boxShadow = '0 0 6px #30d158';
};
streamImg.onerror = () => {
  connLabel.textContent = 'Reconnecting…';
  connDot.style.background = '#ff2d55';
  setTimeout(reconnectStream, 1500);
};

document.addEventListener('visibilitychange', () => {
  if (!document.hidden) reconnectStream();
});

// ─── Settings screen actions ───────────────────────────────────────────────────

connectBtn.addEventListener('click', async () => {
  const raw = ipInput.value;
  if (!raw || raw.trim().length < 3) {
    settingsError.textContent = 'Enter your laptop\u2019s IP address.';
    return;
  }
  const addr = normalizeAddress(raw);
  await saveAddress(addr);
  showStream(addr);
});

settingsBtn.addEventListener('click', () => {
  showSettings(currentAddress);
});

// ─── Recording (canvas capture -> MediaRecorder -> native save) ──────────────

function pickCodec() {
  const candidates = [
    { mime: 'video/mp4;codecs=avc1', ext: 'mp4' },
    { mime: 'video/webm;codecs=vp9', ext: 'webm' },
    { mime: 'video/webm;codecs=vp8', ext: 'webm' },
    { mime: 'video/webm', ext: 'webm' },
  ];
  for (const c of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(c.mime)) return c;
  }
  return { mime: '', ext: 'webm' };
}

function formatTime(s) {
  const m = Math.floor(s / 60).toString().padStart(2, '0');
  const sec = (s % 60).toString().padStart(2, '0');
  return `${m}:${sec}`;
}

function formatBytes(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
  return (b / 1048576).toFixed(2) + ' MB';
}

recBtn.addEventListener('click', () => {
  if (!isRecording) startRecording(); else stopRecording();
});

let rafId = null;

async function startRecording() {
  try {
    const canvas = document.createElement('canvas');
    canvas.width = streamImg.naturalWidth || 1280;
    canvas.height = streamImg.naturalHeight || 720;
    const ctx = canvas.getContext('2d');

    function drawFrame() {
      try { ctx.drawImage(streamImg, 0, 0, canvas.width, canvas.height); } catch (e) {}
      rafId = requestAnimationFrame(drawFrame);
    }
    drawFrame();

    const codecInfo = pickCodec();
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
        sizeEl.textContent = formatBytes(totalBytes);
      }
    };

    mediaRecorder.onstop = () => {
      cancelAnimationFrame(rafId);
      saveRecording(codecInfo);
    };

    mediaRecorder.start(1000);
    isRecording = true;
    recSeconds = 0;

    recBtn.classList.add('recording');
    btnLabel.textContent = 'Stop Recording';
    recInd.classList.add('active');

    recInterval = setInterval(() => {
      recSeconds++;
      recTimer.textContent = formatTime(recSeconds);
    }, 1000);

    log('Recording… frames captured via canvas', 'log-ok');
  } catch (err) {
    log('Error: ' + err.message, 'log-err');
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
  clearInterval(recInterval);
  isRecording = false;
  recBtn.classList.remove('recording');
  btnLabel.textContent = 'Start Recording';
  recInd.classList.remove('active');
  log('Processing recording…');
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function saveRecording(codecInfo) {
  if (!recordedChunks.length) {
    log('No data recorded.', 'log-err');
    reconnectStream();
    return;
  }

  const blob = new Blob(recordedChunks, { type: codecInfo.mime || 'video/webm' });
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const filename = `streamcam-${ts}.${codecInfo.ext}`;

  try {
    if (isNative() && Capacitor.Plugins.Filesystem) {
      const base64 = await blobToBase64(blob);
      const { Filesystem, Share } = Capacitor.Plugins;
      const written = await Filesystem.writeFile({
        path: filename,
        data: base64,
        directory: 'CACHE',
      });
      log(`\u2713 Saved ${filename} (${formatBytes(blob.size)}) \u2014 opening share sheet\u2026`, 'log-ok');
      if (Share) {
        await Share.share({
          title: 'StreamCam recording',
          url: written.uri,
        });
      }
    } else {
      // Plain-browser fallback (e.g. testing in desktop Chrome before packaging)
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(url); document.body.removeChild(a); }, 3000);
      log(`\u2713 Saved as ${filename} (${formatBytes(blob.size)})`, 'log-ok');
    }
  } catch (err) {
    log('Save error: ' + err.message, 'log-err');
  }

  chunkEl.textContent = 0;
  sizeEl.textContent = '0 KB';
  setTimeout(reconnectStream, 600);
}

// ─── Boot ──────────────────────────────────────────────────────────────────────

(async function init() {
  const saved = await loadAddress();
  if (saved) {
    showStream(saved);
  } else {
    showSettings();
  }
})();
