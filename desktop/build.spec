# PyInstaller spec for StreamCam Tray App
# Build with:  pyinstaller build.spec
# Produces a single windowed executable with NO console window,
# so end users never need to open a terminal.

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['tray_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['cv2', 'pystray._win32', 'pystray._darwin', 'pystray._xorg'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StreamCam',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # <-- no terminal / console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
