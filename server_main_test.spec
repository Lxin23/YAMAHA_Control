# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server_main_test.py', 'share.py', 'connector_server_test.py'],
    pathex=[],
    binaries=[],
    datas=[('F:\\Greatway\\pythonProject\\pyqt\\test_01\\data', 'data'),
           ('F:\\Greatway\\pythonProject\\pyqt\\test_01\\images', 'images')],
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
    name='server_main_test',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='server_main_test',
)
