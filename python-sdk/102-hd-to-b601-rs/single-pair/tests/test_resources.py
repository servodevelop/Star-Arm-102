import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo
from stararm_rs_feedback import resources


class ResourceTests(unittest.TestCase):
    def make_bundle(self, directory, extra=None):
        path=directory/'bundle.whl'
        required=['assets/b601_rs.urdf','assets/LICENSE-Seeed.txt','web/model/robot.json',
                  'web/model/LICENSE-Seeed.txt','web/vendor/three.module.js',
                  'web/vendor/LICENSE-three.txt','web/vendor/LICENSE-lucide.txt','web/icons.svg']
        with ZipFile(path,'w') as archive:
            for name in required: archive.writestr(resources.PREFIX+name,'fixture')
            archive.writestr(resources.PREFIX+'dashboard.py','not a runtime asset')
            if extra: archive.writestr(*extra)
        return path,hashlib.sha256(path.read_bytes()).hexdigest()

    def test_install_keeps_dependency_notices_in_cache_and_checks_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);archive,digest=self.make_bundle(directory)
            cache=directory/'cache'
            with patch.object(resources,'BUNDLE_SHA256',digest):
                resources.install(archive,cache)
                self.assertTrue(resources.ready(cache))
                self.assertTrue((cache/'web/vendor/LICENSE-three.txt').is_file())
                self.assertFalse((cache/'dashboard.py').exists())
                (cache/'web/vendor/three.module.js').write_text('damaged')
                self.assertFalse(resources.ready(cache))
                resources.install(archive,cache)
                self.assertTrue(resources.ready(cache))
                (cache/'assets/LICENSE-Seeed.txt').unlink()
                self.assertFalse(resources.ready(cache))

    def test_checksum_mismatch_never_creates_ready_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);archive,_=self.make_bundle(directory)
            with self.assertRaisesRegex(ValueError,'checksum'):resources.install(archive,directory/'cache')
            self.assertFalse((directory/'cache/installed.json').exists())

    def test_archive_traversal_is_rejected_before_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory)
            archive,digest=self.make_bundle(directory,(resources.PREFIX+'assets/../../escape','bad'))
            with patch.object(resources,'BUNDLE_SHA256',digest):
                with self.assertRaisesRegex(ValueError,'Unsafe'):resources.install(archive,directory/'cache')
            self.assertFalse((directory/'escape').exists())
            self.assertFalse((directory/'cache/installed.json').exists())

    def test_symlink_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);entry=ZipInfo(resources.PREFIX+'assets/link')
            entry.create_system=3;entry.external_attr=0o120777<<16
            archive,digest=self.make_bundle(directory,(entry,'../../outside'))
            with patch.object(resources,'BUNDLE_SHA256',digest):
                with self.assertRaisesRegex(ValueError,'symbolic'):resources.install(archive,directory/'cache')

    def test_static_paths_cannot_escape_runtime_cache(self):
        for path in ['../secret','web/model/../../../../secret','/secret','C:/secret',r'web\..\secret']:
            with self.subTest(path=path),self.assertRaises(ValueError):resources.runtime_file(path)


if __name__ == '__main__':unittest.main()
