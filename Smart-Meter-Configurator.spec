# -*- mode: python ; coding: utf-8 -*-
import runpy
from pathlib import Path

app_version = runpy.run_path(
    str(Path(SPECPATH) / "constants.py")
)["APP_VERSION"]

build_name = f"Smart-Meter-Configurator-v{app_version}"

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('app.ico', '.'), ('app.png', '.'), ('icons', 'icons'), ('images', 'images'), ('verification_template.xlsx', '.'), ('verification_template_single.xlsx', '.')],
    hiddenimports=[],
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=build_name,
)
