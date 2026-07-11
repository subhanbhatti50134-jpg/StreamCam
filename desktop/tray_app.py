#!/usr/bin/env python3
"""
StreamCam Tray App
Runs the StreamCam server silently in the background with a system tray icon.
No terminal window needed once packaged (see build.spec).

Requirements: pip install flask opencv-python pystray pillow
"""

import sys
import os
import platform
import webbrowser
import threading

from PIL import Image, ImageDraw
import pystray

from streamcam_core import StreamCamServer

APP_NAME = "StreamCam"
server = StreamCamServer()


# ─── Tray Icon Image ─────────────────────────────────────────────────────────

def make_icon_image(active=True):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 14, 60, 50], radius=10, fill=(19, 19, 26, 255))
    draw.ellipse([24, 22, 40, 38], fill=(48, 209, 88, 255) if active else (110, 110, 128, 255))
    draw.rectangle([44, 24, 58, 40], fill=(19, 19, 26, 255))
    return img


# ─── Autostart (no terminal required by the end user) ───────────────────────

def _get_exe_path():
    """Path to the running executable (works both as .py and as a PyInstaller bundle)."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(__file__)


def is_autostart_enabled():
    system = platform.system()
    try:
        if system == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  r"Software\Microsoft\Windows\CurrentVersion\Run",
                                  0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, APP_NAME)
                return True
            except FileNotFoundError:
                return False
        elif system == "Darwin":
            plist = os.path.expanduser("~/Library/LaunchAgents/com.streamcam.app.plist")
            return os.path.exists(plist)
        else:  # Linux
            desktop_file = os.path.expanduser("~/.config/autostart/streamcam.desktop")
            return os.path.exists(desktop_file)
    except Exception:
        return False


def enable_autostart():
    system = platform.system()
    exe = _get_exe_path()
    try:
        if system == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  r"Software\Microsoft\Windows\CurrentVersion\Run",
                                  0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe}"')
            winreg.CloseKey(key)

        elif system == "Darwin":
            plist_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(plist_dir, exist_ok=True)
            plist_path = os.path.join(plist_dir, "com.streamcam.app.plist")
            with open(plist_path, "w") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.streamcam.app</string>
    <key>ProgramArguments</key><array><string>{exe}</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><false/>
</dict>
</plist>""")
            os.system(f'launchctl load "{plist_path}" >/dev/null 2>&1')

        else:  # Linux
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            desktop_path = os.path.join(autostart_dir, "streamcam.desktop")
            with open(desktop_path, "w") as f:
                f.write(f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={exe}
X-GNOME-Autostart-enabled=true
NoDisplay=false
""")
        return True
    except Exception as e:
        print(f"Could not enable autostart: {e}")
        return False


def disable_autostart():
    system = platform.system()
    try:
        if system == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  r"Software\Microsoft\Windows\CurrentVersion\Run",
                                  0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)

        elif system == "Darwin":
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.streamcam.app.plist")
            if os.path.exists(plist_path):
                os.system(f'launchctl unload "{plist_path}" >/dev/null 2>&1')
                os.remove(plist_path)

        else:  # Linux
            desktop_path = os.path.expanduser("~/.config/autostart/streamcam.desktop")
            if os.path.exists(desktop_path):
                os.remove(desktop_path)
        return True
    except Exception as e:
        print(f"Could not disable autostart: {e}")
        return False


# ─── Tray Menu Actions ────────────────────────────────────────────────────────

def open_dashboard(icon, item):
    webbrowser.open(server.local_url())


def toggle_autostart(icon, item):
    if is_autostart_enabled():
        disable_autostart()
    else:
        enable_autostart()
    icon.update_menu()


def autostart_checked(item):
    return is_autostart_enabled()


def quit_app(icon, item):
    server.stop()
    icon.stop()


def build_menu():
    return pystray.Menu(
        pystray.MenuItem(lambda item: f"StreamCam — {server.local_url()}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Dashboard", open_dashboard, default=True),
        pystray.MenuItem("Start at Login", toggle_autostart, checked=autostart_checked),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit StreamCam", quit_app),
    )


def main():
    server.start()
    icon = pystray.Icon(APP_NAME, make_icon_image(True), APP_NAME, build_menu())
    icon.run()


if __name__ == "__main__":
    main()
