import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "unpack", Path(__file__).resolve().parents[1] / "scripts/unpack_utm.py")
unpack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unpack)


class ArchiveBoundaryTests(unittest.TestCase):
    def archive(self, path, extra=None):
        prefix = "home/builder/result/Whonix-Gateway-LXQt.utm/"
        with tarfile.open(path, "w:gz") as tar:
            for name in ("config.plist", "Data/disk.raw"):
                member = tarfile.TarInfo(prefix + name)
                member.size = 1
                tar.addfile(member, io.BytesIO(b"x"))
            if extra:
                tar.addfile(extra)

    def test_accepts_single_regular_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "bundle.tar.gz"
            self.archive(archive)
            self.assertEqual(unpack.archive_layout(archive).name, "Whonix-Gateway-LXQt.utm")

    def test_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "bundle.tar.gz"
            link = tarfile.TarInfo("home/builder/result/Whonix-Gateway-LXQt.utm/escape")
            link.type = tarfile.SYMTYPE
            link.linkname = "/tmp/elsewhere"
            self.archive(archive, link)
            with self.assertRaises(ValueError):
                unpack.archive_layout(archive)

    def test_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "bundle.tar.gz"
            self.archive(archive, tarfile.TarInfo("../Whonix-Gateway-LXQt.utm/escape"))
            with self.assertRaises(ValueError):
                unpack.archive_layout(archive)


if __name__ == "__main__":
    unittest.main()
