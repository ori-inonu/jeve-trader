"""Copy installed dependency notices; no network, no invented license text."""
import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    inventory = []

    def copy_notices(kind, name, version, directory, declared=None):
        dest = output / kind / re.sub(r'[^A-Za-z0-9_.-]', '_', f'{name}-{version}')
        notices = []
        if directory and directory.is_dir():
            for source in directory.iterdir():
                if source.is_file() and source.name.lower().startswith(('license', 'copying', 'notice', 'copyright', 'licence')):
                    dest.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest / source.name)
                    notices.append(source.name)
            for sub in ('licenses', 'LICENSES'):
                if (directory/sub).is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(directory/sub, dest/sub, dirs_exist_ok=True)
                    notices.append(sub+'/')
        inventory.append(dict(ecosystem=kind, name=name, version=version, declared_license=declared,
                              notices=notices, notice_available=bool(notices)))

    base = Path(sys.base_prefix)
    copy_notices('python', 'CPython', sys.version.split()[0], base, 'PSF-2.0 and bundled notices')
    for name in ('pyinstaller', 'comtypes', 'tzdata'):
        dist = metadata.distribution(name)
        copy_notices('python', name, dist.version, Path(dist._path), dist.metadata.get('License-Expression') or dist.metadata.get('License'))
    packages = {}
    for file in (ROOT/'desktop/node_modules').rglob('package.json'):
        try:
            package = json.loads(file.read_text(encoding='utf-8'))
            name, version = package['name'], package['version']
        except (KeyError, ValueError, OSError):
            continue
        packages.setdefault((name, version), (file.parent, package.get('license')))
    for (name, version), (directory, license_) in sorted(packages.items()):
        copy_notices('npm', name, version, directory, license_)
    lock = tomllib.loads((ROOT/'desktop/src-tauri/Cargo.lock').read_text(encoding='utf-8'))
    registries = list((Path.home()/'.cargo/registry/src').glob('*'))
    for package in lock['package']:
        if package.get('source', '').startswith('registry+'):
            directory = next((x/f"{package['name']}-{package['version']}" for x in registries if (x/f"{package['name']}-{package['version']}").is_dir()), None)
            declared = None
            if directory:
                declared = tomllib.loads((directory/'Cargo.toml').read_text(encoding='utf-8')).get('package', {}).get('license')
            copy_notices('cargo', package['name'], package['version'], directory, declared)
    (output/'inventory.json').write_text(json.dumps(dict(scope='Installed build dependencies; some target-only crates may be absent. Commercial license review remains separate.', packages=inventory), indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Collected notices: {sum(x["notice_available"] for x in inventory)}/{len(inventory)} dependencies')


if __name__ == '__main__':
    main()
