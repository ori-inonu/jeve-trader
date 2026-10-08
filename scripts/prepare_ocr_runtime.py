"""Build the pinned local OCR runtime; no Profit/JEV access or global install."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '2750401336fb7c95f6619657a46a7e798661341c'
TOOL_SHA256 = '13b8175e99a884c5ad34249218754b45541a1a63f216e92603aee57a285ac741'
MODEL_COMMIT = '87416418657359cb625c412a48b6e1d6d41c29bd'
MODEL_FILES = {
    'eng.traineddata': '7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2',
    'LICENSE': 'cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def prepare(vcpkg_root, tool):
    if any(os.environ.get(name) for name in ('VCPKG_OVERLAY_PORTS', 'VCPKG_OVERLAY_TRIPLETS')):
        raise RuntimeError('External vcpkg overlay configuration is not allowed for the pinned OCR build.')
    if os.name != 'nt':
        raise RuntimeError('The OCR delivery requires Windows x64.')
    vcpkg_root = vcpkg_root.resolve()
    if not vcpkg_root.exists():
        vcpkg_root.mkdir(parents=True)
        run(['git', 'init', vcpkg_root])
        run(['git', '-C', vcpkg_root, 'fetch', '--depth', '1', 'https://github.com/microsoft/vcpkg.git', BASELINE])
        run(['git', '-C', vcpkg_root, 'checkout', '--detach', 'FETCH_HEAD'])
    revision = run(['git', '-C', vcpkg_root, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if revision != BASELINE:
        raise RuntimeError('vcpkg checkout does not match the pinned baseline; it was left unchanged.')
    run(['git', '-C', vcpkg_root, 'diff', '--exit-code', 'HEAD', '--'])
    binary = vcpkg_root/'vcpkg.exe'
    if not binary.exists():
        if not tool.is_file() or digest(tool) != TOOL_SHA256:
            raise RuntimeError('Provide the pinned trusted Visual Studio vcpkg executable with --vcpkg-tool.')
        shutil.copy2(tool, binary)
    if digest(binary) != TOOL_SHA256:
        raise RuntimeError('vcpkg tool hash differs from the locked build tool.')
    # Request the pinned static build; existing installed packages may be reused.
    build_environment = dict(os.environ, VCPKG_BINARY_SOURCES='clear', VCPKG_DISABLE_METRICS='1')
    run([binary, 'install', 'tesseract:x64-windows-static', '--vcpkg-root='+str(vcpkg_root),
         '--binarysource=clear', '--disable-metrics', '--no-print-usage'], env=build_environment)
    installed = vcpkg_root/'installed'/'x64-windows-static'
    tesseract = installed/'tools'/'tesseract'/'tesseract.exe'
    if not tesseract.is_file():
        raise RuntimeError('Static Tesseract tool missing after source build.')
    version_output = run([tesseract, '--version'], capture_output=True, text=True).stdout
    if not version_output.startswith('tesseract 5.5.3'):
        raise RuntimeError('Unexpected OCR engine version.')
    compiler = Path(os.environ['WINDIR'])/'Microsoft.NET'/'Framework64'/'v4.0.30319'/'csc.exe'
    if not compiler.is_file():
        raise RuntimeError('The Windows .NET Framework x64 C# compiler is required.')
    app = ROOT/'app'
    target = app/'ocr_runtime'
    with tempfile.TemporaryDirectory(prefix='ocr-build-', dir=app) as directory:
        stage = Path(directory)/'runtime'
        (stage/'tessdata').mkdir(parents=True)
        (stage/'licenses').mkdir()
        run([compiler, '/nologo', '/target:exe', '/platform:x64', '/optimize+', '/r:System.Drawing.dll',
             '/out:'+str(stage/'profit-capture.exe'), app/'profit_capture.cs'])
        shutil.copy2(tesseract, stage/'tesseract.exe')
        for name, expected in MODEL_FILES.items():
            url = 'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/'+MODEL_COMMIT+'/'+name
            with urlopen(url, timeout=45) as response:
                data = response.read(8_000_001)
            if len(data) > 8_000_000 or hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError('Pinned OCR model download hash mismatch: '+name)
            destination = stage/'tessdata'/name if name.endswith('.traineddata') else stage/'licenses'/'tessdata_fast-LICENSE.txt'
            destination.write_bytes(data)
        notices = list((installed/'share').glob('*/copyright'))
        if not notices or not (installed/'share'/'tesseract'/'copyright').is_file():
            raise RuntimeError('vcpkg dependency notices are missing.')
        for notice in notices:
            shutil.copy2(notice, stage/'licenses'/(notice.parent.name+'-copyright.txt'))
        abi_files = list((installed/'share').glob('*/vcpkg_abi_info.txt'))
        if not abi_files or not (installed/'share'/'tesseract'/'vcpkg_abi_info.txt').is_file():
            raise RuntimeError('Installed package ABI provenance is missing.')
        for abi in abi_files:
            shutil.copy2(abi, stage/'licenses'/(abi.parent.name+'-vcpkg-abi-info.txt'))
        status = vcpkg_root/'installed'/'vcpkg'/'status'
        if not status.is_file():
            raise RuntimeError('vcpkg package inventory is missing.')
        shutil.copy2(status, stage/'licenses'/'vcpkg-package-status.txt')
        (stage/'licenses'/'BUILD-SOURCES.txt').write_text(
            'Tesseract 5.5.3, source-built x64-windows-static; no training tools.\n'
            'https://github.com/microsoft/vcpkg/tree/'+BASELINE+'\n'
            'Model eng: https://github.com/tesseract-ocr/tessdata_fast/tree/'+MODEL_COMMIT+'\n'
            'All installed dependency notices and package versions accompany this runtime.\n'
            'External overlays are rejected; binary cache retrieval is disabled during preparation.\n'
            'Existing local installed packages may be reused; ABI records accompany the inventory.\n'
            'Profit and B3 feeds are not included. No JEV calls are made by this runtime.\n', encoding='utf-8')
        files = {p.relative_to(stage).as_posix():digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}
        manifest = dict(schema_version=1, engine='tesseract', version='5.5.3', model='eng', files=files,
                        vcpkg_baseline=BASELINE, vcpkg_tool_sha256=TOOL_SHA256, model_commit=MODEL_COMMIT,
                        helper_source_sha256=digest(app/'profit_capture.cs'), compiler_sha256=digest(compiler),
                        triplet='x64-windows-static', external_overlays=False,
                        binary_cache_retrieval=False, installed_packages_may_be_reused=True, real_profit_tested=False)
        (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
        # Only this generated directory under app is replaced. Never erase an input checkout.
        if target.resolve() != app.resolve()/'ocr_runtime' or target.is_symlink():
            raise RuntimeError('Generated runtime target is outside the owned workspace.')
        if target.exists():
            backup = Path(directory)/'previous-runtime'
            target.rename(backup)
            try:
                stage.rename(target)
            except BaseException:
                backup.rename(target)
                raise
        else:
            stage.rename(target)
    sys.path.insert(0, str(app))
    from profit_ocr import diagnose_runtime
    result = diagnose_runtime()
    print(json.dumps(dict(runtime=str(target), diagnostic=result, manifest_sha256=digest(target/'manifest.json'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vcpkg-root', type=Path, default=ROOT/'.artifacts'/'ocr-dependencies'/'vcpkg')
    parser.add_argument('--vcpkg-tool', type=Path, default=Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)'))/'Microsoft Visual Studio'/'18'/'BuildTools'/'VC'/'vcpkg'/'vcpkg.exe')
    args = parser.parse_args()
    prepare(args.vcpkg_root, args.vcpkg_tool)
