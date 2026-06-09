# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect ALL submodules so nothing gets missed
hidden = []
hidden += collect_submodules('pynput')
hidden += collect_submodules('mouse')
hidden += collect_submodules('plyer')
hidden += collect_submodules('sklearn')
hidden += collect_submodules('scipy')
hidden += collect_submodules('keyboard')
hidden += collect_submodules('pyperclip')
hidden += collect_submodules('pywin32')

datas_extra = []
datas_extra += collect_data_files('sklearn')
datas_extra += collect_data_files('scipy')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('layvix_ai.pkl', '.'),
        ('icon.ico', '.'),
        ('icon.svg', '.'),
        ('ar_words.txt', '.'),
        ('en_words.txt', '.'),
    ] + datas_extra,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Layvix',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Layvix',
)
