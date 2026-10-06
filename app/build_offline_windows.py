#!/usr/bin/env python3
"""Assemble a Windows PE bundle from official Windows binaries without running them.

Requires host CPython 3.12 and PyInstaller 6.16.0. This is an explicit archive
assembly fallback, not PyInstaller's normal Analysis/build workflow. Supply a
Windows CPython 3.12 installation tree (including Lib, DLLs, and tcl) and the
PyInstaller 6.16.0 win_amd64 wheel. Static verification is not a Windows launch test.
The normal supported Windows build is build_windows.ps1 / JevWIN.spec.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--bootloader-wheel', type=Path, required=True)
    parser.add_argument('--tzdata-wheel', type=Path, required=True)
    parser.add_argument('--comtypes-wheel', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error('Host CPython 3.12 required to match the Windows runtime bytecode.')
    import PyInstaller
    if PyInstaller.__version__ != '6.16.0':
        parser.error('PyInstaller 6.16.0 archive writer required.')
    from PyInstaller.archive import writers
    from PyInstaller.archive.readers import CArchiveReader
    import pefile

    project = args.project.resolve()
    runtime = args.runtime.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / 'offline-build'
    staging.mkdir(exist_ok=True)
    for required in ('python312.dll', 'Lib/encodings/__init__.py', 'DLLs/_tkinter.pyd',
                     'DLLs/_sqlite3.pyd', 'tcl/tcl8.6/init.tcl', 'tcl/tk8.6/tk.tcl'):
        if not (runtime / required).is_file():
            raise RuntimeError(f'Missing Windows runtime file: {required}')
    runtime_pe = pefile.PE(str(runtime / 'python312.dll'))
    runtime_version = 'unknown'
    for block in getattr(runtime_pe, 'FileInfo', []):
        for info in block:
            if info.Key == b'StringFileInfo':
                for table in info.StringTable:
                    runtime_version = table.entries.get(b'ProductVersion', b'unknown').decode('utf-8')
    if not runtime_version.startswith('3.12.'):
        raise RuntimeError(f'Unexpected runtime version: {runtime_version}')
    entrypoint = project / 'desktop_app.py'
    if not entrypoint.is_file():
        raise RuntimeError('Missing desktop_app.py entrypoint.')

    # The bootloader initializes CPython with base_library.zip in its module path.
    # Store the complete official Windows stdlib without compression, so startup
    # encodings do not need an extension module before Python initializes.
    base_library = staging / 'base_library.zip'
    with zipfile.ZipFile(base_library, 'w', compression=zipfile.ZIP_STORED) as archive:
        for path in sorted((runtime / 'Lib').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and 'site-packages' not in path.parts:
                archive.write(path, path.relative_to(runtime / 'Lib').as_posix())
    with zipfile.ZipFile(args.bootloader_wheel) as archive:
        bootloader_bytes = archive.read('PyInstaller/bootloader/Windows-64bit-intel/runw.exe')
    bootloader = staging / 'runw.exe'
    bootloader.write_bytes(bootloader_bytes)
    pe = pefile.PE(str(bootloader))
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.Subsystem != 2:
        raise RuntimeError('Expected official Windows x64 GUI bootloader.')

    payload = staging / 'tzdata'
    with zipfile.ZipFile(args.tzdata_wheel) as archive:
        for name in archive.namelist():
            if name.startswith('tzdata/') and not name.endswith('/'):
                path = payload / Path(name).relative_to('tzdata')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))

    com_payload = staging / 'comtypes'
    with zipfile.ZipFile(args.comtypes_wheel) as archive:
        for name in archive.namelist():
            if name.startswith('comtypes/') and not name.startswith('comtypes/test/') and not name.endswith('/'):
                path = com_payload / Path(name).relative_to('comtypes')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(name))

    bootstrap = staging / 'jev_bootstrap.py'
    bootstrap.write_text('''import sys, os
sys.frozen = True
sys.prefix = sys._MEIPASS
sys.exec_prefix = sys._MEIPASS
sys.base_prefix = sys._MEIPASS
sys.base_exec_prefix = sys._MEIPASS
sys.path[:] = [sys._MEIPASS, os.path.join(sys._MEIPASS, 'base_library.zip')]
os.environ['TCL_LIBRARY'] = os.path.join(sys._MEIPASS, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(sys._MEIPASS, 'tcl', 'tk8.6')
''', encoding='utf-8')
    # The bootloader requires a PYZ TOC entry. Imports use the complete stdlib ZIP
    # and extracted app modules, so this valid PYZ intentionally contains no modules.
    pyz = staging / 'PYZ.pyz'
    writers.ZlibArchiveWriter(str(pyz), [])
    entries = [
        ('PYZ.pyz', str(pyz), False, 'z'),
        ('base_library.zip', str(base_library), True, 'Z'),
    ]
    manifest = {}
    seen = set()

    def add(name: str, path: Path, kind: str = 'x') -> None:
        key = name.replace('/', '\\').casefold()
        if key in seen:
            raise RuntimeError(f'Duplicate archive name: {name}')
        seen.add(key)
        entries.append((name.replace('/', '\\'), str(path), True, kind))
        manifest[name] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    # Flatten all interpreter DLLs/extensions beside python312.dll; Windows DLL
    # loading then resolves every private dependency from the extraction directory.
    for path in sorted(runtime.glob('*.dll')):
        add(path.name, path, 'b')
    for path in sorted((runtime / 'DLLs').glob('*')):
        if path.suffix.lower() in {'.dll', '.pyd'}:
            add(path.name, path, 'b')
    for path in sorted((runtime / 'tcl').rglob('*')):
        if path.is_file() and path.suffix not in {'.lib', '.sh'}:
            add(path.relative_to(runtime).as_posix(), path, 'b' if path.suffix == '.dll' else 'x')
    add('PYTHON_LICENSE.txt', runtime / 'LICENSE.txt')
    for path in sorted(payload.rglob('*')):
        if path.is_file():
            add('tzdata/' + path.relative_to(payload).as_posix(), path)
    for path in sorted(com_payload.rglob('*')):
        if path.is_file():
            add('comtypes/' + path.relative_to(com_payload).as_posix(), path)
    for path in sorted(project.glob('*.py')):
        if not path.name.startswith(('test_', 'build_')):
            compile(path.read_text(encoding='utf-8'), path.name, 'exec')
            add(path.name, path)
    for pattern in ('*.json', '*.md'):
        for path in sorted(project.glob(pattern)):
            add(path.name, path)
    for folder in ('helpers', 'licenses', 'templates'):
        resources = project / folder
        if resources.exists():
            for path in sorted(resources.rglob('*')):
                if path.is_file():
                    add(path.relative_to(project).as_posix(), path)
    entries.extend([
        ('jev_bootstrap', str(bootstrap), True, 's'),
        ('desktop_app', str(entrypoint), True, 's'),
    ])
    # CArchiveWriter is format-portable. Explicit Windows path separators are
    # required by the genuine Windows bootloader; all machine code is from the
    # official Windows installer/wheel, never from host Linux binaries.
    archive_path = staging / 'JevWIN.pkg'
    writers.CArchiveWriter(str(archive_path), entries, 'python312.dll')
    output.write_bytes(bootloader_bytes + archive_path.read_bytes())
    # Appending the overlay changes the PE checksum; update it as a normal build
    # does. No signing or fabricated certificate is applied.
    final_pe = pefile.PE(str(output))
    final_pe.OPTIONAL_HEADER.CheckSum = final_pe.generate_checksum()
    final_pe.write(str(output))

    reader = CArchiveReader(str(output))
    for name, expected in manifest.items():
        contents = reader.extract(name.replace('/', '\\'))
        if hashlib.sha256(contents).hexdigest() != expected['sha256']:
            raise RuntimeError(f'Archive round-trip failed: {name}')
    if reader.extract('PYZ.pyz')[:4] != b'PYZ\0':
        raise RuntimeError('Missing valid PYZ header.')
    import io
    with zipfile.ZipFile(io.BytesIO(reader.extract('base_library.zip'))) as lib:
        if lib.testzip() is not None:
            raise RuntimeError('Corrupt base_library.zip.')
        for module in ('encodings/__init__.py', 'tkinter/__init__.py', 'sqlite3/__init__.py', 'ctypes/__init__.py', 'urllib/request.py'):
            assert module in lib.namelist(), module
    # Verify every bundled DLL/extension really is x64 Windows PE and that its
    # private DLL imports are supplied. Remaining dependencies must be OS DLLs.
    private = {name.casefold() for name in manifest if '/' not in name}
    windows_dlls = {
        'kernel32.dll','user32.dll','gdi32.dll','advapi32.dll','shell32.dll',
        'ole32.dll','oleaut32.dll','ws2_32.dll','shlwapi.dll','comctl32.dll',
        'comdlg32.dll','version.dll','ntdll.dll','msvcrt.dll','bcrypt.dll',
        'crypt32.dll','secur32.dll','rpcrt4.dll','iphlpapi.dll','netapi32.dll',
        'userenv.dll','psapi.dll','winmm.dll','winspool.drv','normaliz.dll',
        'cabinet.dll','msi.dll','dhcpcsvc.dll','dxgi.dll','dwmapi.dll',
        'ucrtbase.dll','oleacc.dll','uxtheme.dll','authz.dll','wtsapi32.dll',
        'powrprof.dll','d3d11.dll','propsys.dll','wbemuuid.dll','wldap32.dll','imm32.dll',
    }
    dependencies = {}
    unresolved = set()
    for name in manifest:
        if name.lower().endswith(('.dll', '.pyd')):
            binary = pefile.PE(data=reader.extract(name.replace('/', '\\')))
            if binary.FILE_HEADER.Machine != 0x8664:
                raise RuntimeError(f'Non-x64 binary: {name}')
            deps = [item.dll.decode('ascii').lower() for item in getattr(binary, 'DIRECTORY_ENTRY_IMPORT', [])]
            dependencies[name] = deps
            for dep in deps:
                if dep not in private and dep not in windows_dlls and not dep.startswith(('api-ms-win-', 'ext-ms-win-')):
                    unresolved.add(dep)
    if unresolved:
        raise RuntimeError('Unclassified Windows DLL dependencies: ' + ', '.join(sorted(unresolved)))
    report = {
        'artifact': output.name, 'bytes': output.stat().st_size,
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'machine': 'AMD64 (0x8664)', 'subsystem': 'Windows GUI (2)',
        'python': runtime_version + ' x64',
        'build_inputs': {
            'python312.dll_sha256': hashlib.sha256((runtime / 'python312.dll').read_bytes()).hexdigest(),
            'bootloader_wheel_sha256': hashlib.sha256(args.bootloader_wheel.read_bytes()).hexdigest(),
            'tzdata_wheel_sha256': hashlib.sha256(args.tzdata_wheel.read_bytes()).hexdigest(),
            'comtypes_wheel_sha256': hashlib.sha256(args.comtypes_wheel.read_bytes()).hexdigest(),
            'python_bytecode_magic': importlib.util.MAGIC_NUMBER.hex(),
        }, 'pyinstaller_bootloader': '6.16.0 official Windows wheel',
        'comtypes': '1.4.17',
        'build_method': 'offline CArchive assembly from official Windows runtime',
        'archive_entries': len(reader.toc), 'all_payload_hashes_verified': True,
        'all_private_dll_dependencies_resolved': True,
        'windows_launch_test': 'not performed; execution environment denies Wine IPC sockets',
        'manifest': manifest, 'dll_dependencies': dependencies,
    }
    report_path = output.with_suffix('.build-report.json')
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in {'manifest', 'dll_dependencies'}}, indent=2))
    print('Report:', report_path)


if __name__ == '__main__':
    main()
