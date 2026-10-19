import importlib.util
import io
from pathlib import Path
import struct
import sys
import tarfile
import tempfile
import unittest

scripts = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location('setup_preview', scripts / 'setup_preview.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
sys.path.pop(0)


class PreviewArchiveTests(unittest.TestCase):
    def run_archive(self, entries):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'image.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                for name, data, kind in entries:
                    info = tarfile.TarInfo(name)
                    if kind == 'link':
                        info.type = tarfile.SYMTYPE
                        info.linkname = '/etc/passwd'
                        tar.addfile(info)
                    else:
                        info.size = len(data)
                        tar.addfile(info, io.BytesIO(data))
            return setup.extract_bundle(archive, root / 'output', 'Test.utm').name

    def test_accepts_exact_pair_of_regular_files(self):
        header = bytearray(72)
        header[:8] = b'QFI\xfb' + struct.pack('!I', 3)
        self.assertEqual(self.run_archive([
            ('Test.utm/config.plist', b'configuration', 'file'),
            ('Test.utm/Data/system.qcow2', bytes(header), 'file')]), 'Test.utm')

    def test_rejects_path_traversal(self):
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.run_archive([('Test.utm/../../escape', b'x', 'file')])

    def test_rejects_links(self):
        with self.assertRaisesRegex(ValueError, 'link'):
            self.run_archive([('Test.utm/config.plist', b'', 'link')])

    def test_rejects_duplicate_configuration(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.run_archive([('Test.utm/config.plist', b'x', 'file')] * 2)
