#!/usr/bin/env python3
"""Build a conventional CPython Windows folder plus a native NSIS x64 installer.

No Windows executables are executed by this build. Windows launch validation must
be performed separately; static extraction checks are recorded honestly.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def app_version(project: Path) -> str:
    tree = ast.parse((project / 'app_store.py').read_text(encoding='utf-8'))
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in statement.targets):
            return ast.literal_eval(statement.value)
    raise RuntimeError('VERSION is not a literal in app_store.py.')


def unpack_wheel(wheel: Path, destination: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        for member in archive.namelist():
            if member.endswith('/'):
                continue
            path = destination / member
            if not path.resolve().is_relative_to(destination.resolve()):
                raise ValueError('Invalid wheel path.')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(member))


def windows_pe_identity(path: Path) -> dict:
    # Read PE identity directly so the builder needs no third-party host package.
    data = path.read_bytes()
    if data[:2] != b'MZ':
        raise RuntimeError(f'Not a Windows PE: {path}')
    offset = int.from_bytes(data[0x3c:0x40], 'little')
    if data[offset:offset + 4] != b'PE\0\0':
        raise RuntimeError(f'Invalid PE signature: {path}')
    machine = int.from_bytes(data[offset + 4:offset + 6], 'little')
    magic = int.from_bytes(data[offset + 24:offset + 26], 'little')
    subsystem = int.from_bytes(data[offset + 24 + 68:offset + 24 + 70], 'little')
    if machine != 0x8664 or magic != 0x20b:
        raise RuntimeError(f'Expected AMD64 PE32+: {path} (machine={machine:#x})')
    return {'machine': 'AMD64 (0x8664)', 'format': 'PE32+', 'subsystem': subsystem}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--comtypes-wheel', type=Path, required=True)
    parser.add_argument('--tzdata-wheel', type=Path, required=True)
    parser.add_argument('--websocket-wheel', type=Path, required=True)
    parser.add_argument('--makensis', type=Path, required=True)
    parser.add_argument('--nsisdir', type=Path)
    parser.add_argument('--sevenzip', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    project, runtime, output = args.project.resolve(), args.runtime.resolve(), args.output_dir.resolve()
    packaging = project / 'packaging'
    version = app_version(project)
    output.mkdir(parents=True, exist_ok=True)
    payload = output / 'JevWIN-portable'
    if payload.exists():
        shutil.rmtree(payload)
    payload.mkdir()
    runtime_out = payload / 'runtime'
    runtime_out.mkdir()
    for item in runtime.iterdir():
        if item.is_file() and item.suffix.lower() in {'.exe', '.dll', '.txt'}:
            shutil.copy2(item, runtime_out / item.name)
    for folder in ('DLLs', 'Lib', 'tcl'):
        shutil.copytree(runtime / folder, runtime_out / folder,
                        ignore=shutil.ignore_patterns('__pycache__', 'site-packages'))
    site = payload / 'runtime' / 'Lib' / 'site-packages'
    site.mkdir(exist_ok=True)
    unpack_wheel(args.comtypes_wheel, site)
    unpack_wheel(args.tzdata_wheel, site)
    unpack_wheel(args.websocket_wheel, site)
    app = payload / 'app'
    app.mkdir()
    for path in sorted(project.iterdir()):
        if path.is_file() and (path.suffix.lower() in {'.json', '.md'} or
                               (path.suffix == '.py' and not path.name.startswith(('test_', 'build_')))
                               or path.name == 'requirements-runtime.txt'):
            if path.suffix == '.py':
                compile(path.read_text(encoding='utf-8'), path.name, 'exec')
            shutil.copy2(path, app / path.name)
    for name in ('templates', 'helpers', 'licenses', 'multimarket'):
        if (project / name).exists():
            shutil.copytree(project / name, app / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('windows_launcher.py', 'JevWIN.cmd', 'Diagnosticar_JevWIN.cmd'):
        data = (packaging / name).read_bytes()
        if name.endswith('.cmd'):
            data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        (payload / name).write_bytes(data)
    (payload / 'LEIA-ME.txt').write_text(
        f'JevWIN {version} - Windows 10/11 x64\n\n'
        'PACOTE PORTATIL: extraia esta pasta inteira e abra JevWIN.exe.\n'
        'Alternativa com console: JevWIN.cmd. Se houver erro, a janela permanece aberta.\n'
        'DIAGNOSTICO: abra Diagnosticar_JevWIN.cmd e copie a mensagem mostrada.\n'
        'Registros: %LOCALAPPDATA%\\JevWIN\\logs\\startup.log\n\n'
        'O Python oficial e as bibliotecas estao incluidos. Nao instale Python separadamente.\n'
        'Nao mova apenas o pequeno JevWIN.exe: ele usa as pastas runtime e app.\n\n'
        'O instalador JevWIN_Instalador.exe instala a mesma pasta para o usuario atual\n'
        'em %LOCALAPPDATA%\\Programs\\JevWIN e cria atalhos.\n'
        'Os dados e registros ficam em %LOCALAPPDATA%\\JevWIN.\n\n'
        'Execucao Windows ainda nao testada neste ambiente. Consulte app/WINDOWS_BUILD.md.\n',
        encoding='utf-8')
    env = os.environ.copy()
    if args.nsisdir:
        env['NSISDIR'] = str(args.nsisdir.resolve())
    compile_launcher = [str(args.makensis), '-V3', f'-DOUTPUT={payload / "JevWIN.exe"}', str(packaging / 'launcher.nsi')]
    launcher_result = subprocess.run(compile_launcher, check=True, env=env, capture_output=True, text=True)
    (output / 'launcher-build.log').write_text(launcher_result.stdout + launcher_result.stderr, encoding='utf-8')
    identity = windows_pe_identity(payload / 'JevWIN.exe')
    for name in ('python.exe', 'pythonw.exe', 'python312.dll', 'DLLs/_tkinter.pyd', 'DLLs/_sqlite3.pyd'):
        windows_pe_identity(payload / 'runtime' / name)
    manifest = {}
    for path in sorted(payload.rglob('*')):
        if path.is_file():
            name = path.relative_to(payload).as_posix()
            manifest[name] = {'bytes': path.stat().st_size, 'sha256': digest(path)}
    metadata = {'app_version': version, 'build_method': 'native NSIS x64 compiler; conventional official Windows CPython runtime tree',
                'windows_launch_test': 'not performed by this assembler; installation and GUI require separate Windows validation',
                'build_platform': sys.platform,
                'runtime': 'CPython 3.12 x64 (official interpreter files copied unchanged)', 'comtypes': '1.4.17', 'manifest': manifest}
    (payload / 'package-manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    installer = output / 'JevWIN_Instalador.exe'
    total_bytes = sum(info['bytes'] for info in manifest.values())
    compile_installer = [str(args.makensis), '-V3', f'-DVERSION={version}', f'-DSIZE_KB={(total_bytes + 1023) // 1024}',
                         f'-DPAYLOAD={payload}', f'-DOUTPUT={installer}', str(packaging / 'installer.nsi')]
    installer_result = subprocess.run(compile_installer, check=True, env=env, capture_output=True, text=True)
    (output / 'installer-build.log').write_text(installer_result.stdout + installer_result.stderr, encoding='utf-8')
    installer_identity = windows_pe_identity(installer)
    portable = output / 'JevWIN_Portatil.zip'
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(payload.rglob('*')):
            if path.is_file():
                archive.write(path, 'JevWIN-portable/' + path.relative_to(payload).as_posix())
    with zipfile.ZipFile(portable) as archive:
        assert archive.testzip() is None
        for name, item in manifest.items():
            assert hashlib.sha256(archive.read('JevWIN-portable/' + name)).hexdigest() == item['sha256'], name
    installer_checked = False
    if args.sevenzip:
        extracted = output / 'installer-extracted'
        if extracted.exists():
            shutil.rmtree(extracted)
        subprocess.run([str(args.sevenzip), 'x', '-y', f'-o{extracted}', str(installer)], check=True, capture_output=True, text=True)
        for name, item in manifest.items():
            candidate = extracted / name
            if not candidate.is_file() or digest(candidate) != item['sha256']:
                raise RuntimeError(f'Installer payload extraction/hash mismatch: {name}')
        installer_checked = True
    report = {key: value for key, value in metadata.items() if key != 'manifest'}
    report.update(payload_files=len(manifest), payload_bytes=total_bytes,
                  portable_round_trip_hashes_passed=True, installer_round_trip_hashes_passed=installer_checked,
                  launcher_identity=identity, installer_identity=installer_identity,
                  installation_scope='current user', installation_directory=r'%LOCALAPPDATA%\Programs\JevWIN',
                  diagnostic_logs=r'%LOCALAPPDATA%\JevWIN\logs',
                  original_python_exe_unchanged=digest(runtime / 'python.exe') == digest(payload / 'runtime' / 'python.exe'),
                  original_pythonw_exe_unchanged=digest(runtime / 'pythonw.exe') == digest(payload / 'runtime' / 'pythonw.exe'),
                  original_tcl_tk_dlls_unchanged=all(digest(runtime / name) == digest(payload / 'runtime' / name)
                                                   for name in ('DLLs/_tkinter.pyd', 'DLLs/tcl86t.dll', 'DLLs/tk86t.dll')),
                  artifacts={path.name: {'bytes': path.stat().st_size, 'sha256': digest(path)} for path in (installer, portable)})
    (output / 'JevWIN_distribution_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
