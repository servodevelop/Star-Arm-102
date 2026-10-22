#!/usr/bin/env python3
"""Regenerate the customer URDF ZIPs from their source packages."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1] / 'hardware'


def main():
    for model in ('102-ld', '102-hd', '102-fl'):
        variant = 'fl' if model == '102-fl' else 'ld-hd'
        if model == '102-ld':
            directory = ROOT / model / 'urdf'
            source = directory / 'stararm102-ld-hd-description'
            output = directory / 'downloads' / 'star-arm-102-ld-hd-urdf-2026-10-21.zip'
        else:
            directory = ROOT / model / 'robot-description'
            source = directory / ('stararm102_' + variant.replace('-', '_') + '_description')
            output = directory / ('star-arm-102-' + variant + '-urdf.zip')
        if not (source / 'package.xml').is_file():
            raise FileNotFoundError(f'Missing ROS source package: {source}')
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
            for path in sorted(source.rglob('*')):
                if not path.is_file() or any(part.startswith('.') or part == '__pycache__' for part in path.relative_to(source).parts):
                    continue
                info = ZipInfo(path.relative_to(source.parent).as_posix(), date_time=(2026, 10, 9, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
        print(output)


if __name__ == '__main__':
    main()
