# StreamCam Desktop — Background Tray App

Runs your webcam server silently in the background with a system tray icon.
No terminal, no visible console window, and it can start automatically when
you log in.

## One-time setup (you do this once, on your own machine)

```bash
cd desktop
pip install -r requirements.txt
```

## Try it first (still from a terminal, just to confirm it works)

```bash
python tray_app.py
```

You should see a small camera icon appear in your system tray / menu bar.
Right-click (or click, on macOS) it:

- **Open Dashboard** — opens the live stream in your default browser
- **Start at Login** — toggle on; from then on StreamCam launches itself
  automatically every time you log in, with no terminal involved
- **Quit StreamCam** — stops the server and exits

## Package it into a real double-click app (removes the terminal step above)

This step needs to be run once per operating system you want to support —
PyInstaller can't cross-compile, so build on Windows for the `.exe`, on
macOS for the `.app`, on Linux for the standalone binary.

```bash
pyinstaller build.spec
```

The finished app appears in `dist/`:

- **Windows:** `dist/StreamCam.exe` — double-click to launch, no console window
- **macOS:** `dist/StreamCam.app` — double-click, or drag to Applications
- **Linux:** `dist/StreamCam` — mark executable (`chmod +x`) and double-click
  from your file manager, or add it to your app launcher

From here on, your day-to-day flow is: double-click once, or just log in
(if "Start at Login" is on) — the tray icon appears and the phone app can
connect immediately.

## Notes

- macOS will ask for **Camera** and possibly **Local Network** permission the
  first time — allow both.
- If Windows Defender / Gatekeeper flags the unsigned executable, that's
  normal for a self-built app; you can allow it or sign it with your own
  certificate later.
- `streamcam_core.py` still has the same `CAMERA_INDEX`, `JPEG_QUALITY`, etc.
  settings as the original `server.py` — edit them there if needed.
