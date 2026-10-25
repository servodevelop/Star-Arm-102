"""Prevent non-README translations from falling outside the sync check."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import check_readme_sync as sync


class BilingualDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, content='# Guide\n'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def run_check(self):
        output = io.StringIO()
        with patch.object(sync, 'ROOT', self.root), contextlib.redirect_stdout(output):
            failed = sync.main()
        return failed, output.getvalue()

    def test_non_readme_command_drift_is_reported(self):
        self.write('python-sdk/single-arm/PYTHON_SDK_GUIDE.md', '# Guide\n\n```bash\nrun --window=1\n```\n')
        zh = self.write('python-sdk/single-arm/PYTHON_SDK_GUIDE.zh.md', '# 指南\n\n```bash\nrun --window=30\n```\n')
        failed, output = self.run_check()
        self.assertTrue(failed)
        self.assertIn('PYTHON_SDK_GUIDE.zh.md: mismatched code', output)
        zh.write_text('# 指南\n\n```bash\nrun --window=1\n```\n')
        self.assertFalse(self.run_check()[0])

    def test_legacy_filename_pair_and_language_links(self):
        en = self.write('lerobot/stararm102_en.md', '# Guide\n\n[中文](stararm102.md)\n')
        zh = self.write('lerobot/stararm102.md', '# 指南\n\n[English](stararm102_en.md)\n')
        self.assertIn((en, zh), sync.document_pairs(self.root))
        self.assertFalse(self.run_check()[0])

    def test_current_pairs_exclude_hidden_and_unpaired_history(self):
        en = self.write('docs/getting-started.md')
        zh = self.write('docs/getting-started.zh.md')
        self.write('ros2-humble/legacy-guide.zh.md')
        self.write('.preview/README.zh.md')
        self.assertEqual(sync.document_pairs(self.root), [(en, zh)])
        self.write('hardware/README.zh.md')
        failed, output = self.run_check()
        self.assertTrue(failed)
        self.assertIn('hardware/README.zh.md: missing bilingual counterpart', output)

    def test_translation_links_preserve_directory_vs_document(self):
        self.assertEqual(sync.canonical('../docs/getting-started.zh.md'),
                         sync.canonical('../docs/getting-started.md'))
        self.assertEqual(sync.canonical('PYTHON_SDK_GUIDE.zh.md'),
                         sync.canonical('PYTHON_SDK_GUIDE.md'))
        self.assertNotEqual(sync.canonical('../hardware/'),
                            sync.canonical('../hardware/README.zh.md'))


if __name__ == '__main__':
    unittest.main()
