# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — работает на Windows и macOS

import sys
import os

block_cipher = None

# Библиотеки с динамическими импортами и файлами-ресурсами (шаблон docx,
# CMap-ресурсы pdfminer и т.п.) — собираем целиком, иначе .exe упадёт при импорте.
from PyInstaller.utils.hooks import collect_all
_extra_datas, _extra_binaries, _extra_hidden = [], [], []
for _pkg in ('docx', 'pdfplumber', 'pdfminer', 'PIL'):
    _d, _b, _h = collect_all(_pkg)
    _extra_datas += _d
    _extra_binaries += _b
    _extra_hidden += _h

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=_extra_binaries,
    datas=_extra_datas,
    hiddenimports=[
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.reader.excel',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ] + _extra_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
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
    name='AnalyzDebitCredit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # не показывать консоль
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',      # раскомментировать если добавишь иконку
)

# macOS: создаём .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='AnalyzDebitCredit.app',
        # icon='icon.icns',  # раскомментировать если добавишь иконку
        bundle_identifier='com.gzhi.analyzdebitcredit',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': 'Анализ дебита и кредита',
        },
    )
