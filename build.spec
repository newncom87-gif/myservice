# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 빌드 스펙. macOS/Windows 공용.

macOS: pyinstaller build.spec  (이 Mac에서 바로 .app 생성)
Windows: pyinstaller build.spec  (Windows 머신 또는 CI에서 실행해야 .exe 생성됨)
"""
import sys

APP_NAME = "성경말씀PPT생성기"
# macOS의 codesign이 "실행파일명(CFBundleExecutable)"에 한글이 있으면 번들을
# --deep 서명할 때 SIGBUS로 크래시하는 버그가 있다(이 환경 macOS 15.5에서 재현 확인).
# 앱 번들 폴더명(Finder에 보이는 이름)과 창 제목은 한글 그대로 두고, 실행파일 자체의
# 파일명만 ASCII로 바꿔서 우회한다. Windows는 이 문제가 없으므로 그대로 한글 사용.
EXE_NAME = "BiblePPTMaker" if sys.platform == "darwin" else APP_NAME

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("app/static", "app/static"), ("app/data", "app/data")],
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
    name=EXE_NAME,
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
    icon="icons/icon.icns" if sys.platform == "darwin" else ("icons/icon.ico" if sys.platform == "win32" else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=EXE_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon="icons/icon.icns",
        bundle_identifier="com.hgkim.biblepptmaker",
        info_plist={
            "NSHighResolutionCapable": "True",
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
        },
    )
