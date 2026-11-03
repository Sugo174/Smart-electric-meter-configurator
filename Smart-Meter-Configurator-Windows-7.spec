# -*- mode: python ; coding: utf-8 -*-
import runpy
from pathlib import Path

app_version = runpy.run_path(
    str(Path(SPECPATH) / "constants.py")
)["APP_VERSION"]

build_name = f"Smart-Meter-Configurator-v{app_version}-Windows-7"
from PyInstaller.utils.hooks import collect_all

datas = [('app.ico', '.'), ('app.png', '.'), ('icons', 'icons'), ('images', 'images')]
binaries = []
hiddenimports = ['babel.numbers']
tmp_ret = collect_all('sv_ttk')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


block_cipher = None


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=build_name,
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
    icon=['app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=build_name,
)
