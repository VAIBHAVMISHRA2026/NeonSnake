# -*- mode: python ; coding: utf-8 -*-
"""
NeonSnake.spec - PyInstaller build configuration for Neon Snake Arena game.
Bundles all assets (images, sounds, music, data) into a single .exe file.
"""

import os

block_cipher = None

# Game source directory
game_dir = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[game_dir],
    binaries=[],
    datas=[
        ('assets/images/*', 'assets/images'),
        ('assets/sounds/*', 'assets/sounds'),
        ('assets/music/*', 'assets/music'),
        ('data/*', 'data'),
    ],
    hiddenimports=[
        'settings', 'utils', 'snake', 'food', 'powerups',
        'enemy', 'game', 'menu', 'ui', 'camera', 'effects',
        'particles', 'audio', 'save',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'email', 'html', 'http', 'xml', 'pydoc'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NeonSnakeArena',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window - game only!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/images/icon.ico',
)
