# -*- mode: python ; coding: utf-8 -*-
"""Build with Windows CPython 3.12 x64: python -m PyInstaller JevWIN.spec."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

project = Path(SPECPATH)
data = []
for pattern in ('*.json', '*.md'):
    data.extend((str(path), '.') for path in sorted(project.glob(pattern)))
for folder in ('helpers', 'licenses', 'templates'):
    resources = project / folder
    if resources.exists():
        data.extend((str(path), str(path.parent.relative_to(project)))
                    for path in sorted(resources.rglob('*')) if path.is_file())
data.extend(collect_data_files('tzdata'))
data.extend(collect_data_files('comtypes', excludes=['**/test/**']))
com_imports = collect_submodules('comtypes', filter=lambda name: not name.startswith('comtypes.test'))

analysis = Analysis(
    [str(project / 'desktop_app.py')],
    pathex=[str(project)], binaries=[], datas=data,
    hiddenimports=['tkinter', 'tkinter.ttk', 'sqlite3', 'tzdata'] + com_imports,
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    noarchive=False, optimize=0,
)
archive = PYZ(analysis.pure)
exe = EXE(
    archive, analysis.scripts, analysis.binaries, analysis.datas, [],
    name='JevWIN', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, runtime_tmpdir=None, console=False,
    disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)
