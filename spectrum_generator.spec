import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

spekpy_datas = collect_data_files('spekpy')

a = Analysis(
    [os.path.join('src', 'xrayspectrum', 'gui.py')],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join('src', 'xrayspectrum', 'spectrum_generator.ico'), 'xrayspectrum'),
        *spekpy_datas,
    ],
    hiddenimports=[
        'xrayspectrum.spectrum',
        'xrayspectrum.attenuation_coefficient',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='XRaySpectrumGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join('src', 'xrayspectrum', 'spectrum_generator.ico'),
)
