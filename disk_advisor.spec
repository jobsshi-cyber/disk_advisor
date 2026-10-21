# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/disk_advisor/main.py'],  # 直接指向 main.py
    pathex=['src'],                # 告诉打包器去 src 目录下找包
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='磁盘瘦身',            # 生成的 exe 名字
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                      # 启用 upx 压缩（可选，体积更小）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                  # 保留黑框框，因为我们要交互
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)