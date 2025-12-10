# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Archivos a incluir
added_files = [
    ('app', 'app'),
    ('config.py', '.'),
    ('requirements.txt', '.'),
    ('data', 'data'),
    ('backups', 'backups'),
    ('logs', 'logs'),
    ('uploads', 'uploads'),
    ('resources', 'resources'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_migrate',
        'pandas',
        'sqlalchemy',
        'werkzeug.security',
        'datetime',
        'json',
        'os',
        'sys',
        'threading',
        'webbrowser',
        'winshell',
        'win32com.client',
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

# Configuración del EXE
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HospitalSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Cambiar a False para ocultar consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/hospital.ico',
)

# Opcional: Crear instalador NSIS
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='HospitalSystem',
# )