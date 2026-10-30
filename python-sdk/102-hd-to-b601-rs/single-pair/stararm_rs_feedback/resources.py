"""Install pinned runtime assets in the local cache, outside the source tree."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

BUNDLE_URL = 'https://github.com/VincentHSS/stararm-b601-rs-feedback/releases/download/v0.6.1/stararm_rs_feedback-0.6.1-py3-none-any.whl'
BUNDLE_SHA256 = 'ecaf98c88e325d04f2097e7f4f51a778d8a2372e34fa32b465e402b920d4175a'
PREFIX = 'stararm_rs_feedback/'


def resource_root():
    override = os.environ.get('STARARM_RESOURCES_DIR')
    cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))
    return Path(override).expanduser().resolve() if override else cache/'stararm102'/'b601-rs'/'resources-v1'


def runtime_file(relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative:
        raise ValueError('Invalid runtime resource path')
    root = resource_root()
    result = (root/relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError('Resource path escapes the cache')
    return result


def ready(root=None):
    root = root or resource_root()
    try:
        manifest = json.loads((root/'installed.json').read_text(encoding='utf-8'))
        return (manifest['bundle_sha256'] == BUNDLE_SHA256
                and all(_selected(PREFIX+name) == name and (root/name).is_file()
                        and (root/name).resolve().is_relative_to(root.resolve())
                        and hashlib.sha256((root/name).read_bytes()).hexdigest() == digest
                        for name,digest in manifest['files'].items())
                and {'assets/b601_rs.urdf','web/model/robot.json','web/vendor/three.module.js','web/icons.svg'} <= set(manifest['files']))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def _selected(name):
    if not name.startswith(PREFIX):
        return None
    name = name[len(PREFIX):]
    if name.startswith(('assets/', 'web/model/', 'web/vendor/')) or name == 'web/icons.svg':
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Unsafe asset archive member')
        return name
    return None


def install(archive, root=None):
    archive, root = Path(archive), root or resource_root()
    if hashlib.sha256(archive.read_bytes()).hexdigest() != BUNDLE_SHA256:
        raise ValueError('Runtime asset checksum mismatch')
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='stararm-assets-',dir=root.parent) as temporary:
        stage = Path(temporary); files = {}
        with ZipFile(archive) as bundle:
            if sum(item.file_size for item in bundle.infolist()) > 160*1024*1024:
                raise ValueError('Runtime asset archive is too large')
            for item in bundle.infolist():
                name = _selected(item.filename)
                if not name or item.is_dir():
                    continue
                if name in files or (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Duplicate or symbolic-link resource')
                destination = stage/name
                if not destination.resolve().is_relative_to(stage.resolve()):
                    raise ValueError('Unsafe extraction destination')
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = bundle.read(item)
                destination.write_bytes(data)
                files[name] = hashlib.sha256(data).hexdigest()
        required = {'assets/b601_rs.urdf','assets/LICENSE-Seeed.txt','web/model/robot.json',
                    'web/model/LICENSE-Seeed.txt','web/vendor/three.module.js',
                    'web/vendor/LICENSE-three.txt','web/vendor/LICENSE-lucide.txt','web/icons.svg'}
        if not required <= files.keys():
            raise ValueError('Runtime asset bundle is incomplete')
        # Upstream licenses remain in the installed dependency cache, not this repository.
        root.mkdir(parents=True,exist_ok=True)
        (root/'installed.json').unlink(missing_ok=True)
        for name in files:
            destination=root/name
            if not destination.resolve().is_relative_to(root.resolve()):
                raise ValueError('Unsafe resource cache destination')
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(stage/name,destination)
        marker=root/'installed.json.tmp'
        marker.write_text(json.dumps(dict(bundle_sha256=BUNDLE_SHA256,files=files)),encoding='utf-8')
        marker.replace(root/'installed.json')
    return root


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,help='Use a previously downloaded asset wheel')
    parser.add_argument('--check',action='store_true',help='Check local assets without network access')
    args=parser.parse_args(argv)
    if args.check:
        if not ready():parser.error('Assets are missing. Run: python -m stararm_rs_feedback.resources')
        print(f'Runtime assets ready: {resource_root()}');return
    if args.archive:
        install(args.archive)
    elif not ready():
        resource_root().parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=resource_root().parent) as temporary:
            archive=Path(temporary)/'runtime.whl'
            with urlopen(BUNDLE_URL,timeout=60) as response, archive.open('wb') as output:
                shutil.copyfileobj(response,output)
            install(archive)
    print(f'Runtime assets ready: {resource_root()}')


if __name__ == '__main__':main()
