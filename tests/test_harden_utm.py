import importlib.util
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "harden", Path(__file__).resolve().parents[1] / "scripts/harden_utm.py")
harden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harden)


def fixture():
    return {"Backend": "QEMU", "ConfigurationVersion": 4,
            "System": {"Architecture": "aarch64"}, "Information": {},
            "Drive": [{"ImageName": "disk.raw", "ImageType": "Disk"}],
            "Display": [{"Hardware": "virtio-gpu-gl-pci"}],
            "Network": [{"Mode": "Shared"}],
            "QEMU": {"AdditionalArguments": ["-netdev user,id=bypass"]},
            "Sharing": {"ClipboardSharing": True, "DirectoryShareMode": "WebDAV"},
            "Input": {"UsbSharing": True}, "Sound": [{"Hardware": "intel-hda"}]}


class IsolationTests(unittest.TestCase):
    def test_workstation_has_no_external_or_alternate_network(self):
        c = harden.hardened(fixture(), "workstation", "/tmp/test-private/net.sock")
        args = c["QEMU"]["AdditionalArguments"]
        self.assertEqual(args.count("-device"), 1)
        self.assertEqual(args.count("-netdev"), 1)
        self.assertEqual(c["Network"], [])
        self.assertFalse(any("user," in a or "bypass" in a or "tap," in a for a in args))
        self.assertIn("stream,id=internal,addr.type=unix,addr.path=/tmp/test-private/net.sock,server=off,reconnect-ms=2000", args)

    def test_gateway_has_one_external_and_private_internal_transport(self):
        c = harden.hardened(fixture(), "gateway", "/tmp/test-private/net.sock")
        args = c["QEMU"]["AdditionalArguments"]
        self.assertEqual(args.count("-device"), 2)
        self.assertEqual(args.count("-netdev"), 2)
        self.assertIn("user,id=external,ipv6=off,net=10.0.2.0/24", args)
        self.assertIn("stream,id=internal,addr.type=unix,addr.path=/tmp/test-private/net.sock,server=on", args)
        self.assertFalse(any("listen=" in a or "hostfwd" in a for a in args))

    def test_host_integrations_removed_and_input_not_mutated(self):
        original = fixture()
        c = harden.hardened(original, "workstation", "/tmp/private/net.sock")
        self.assertFalse(c["Sharing"]["ClipboardSharing"])
        self.assertEqual(c["Sharing"]["DirectoryShareMode"], "None")
        self.assertFalse(c["Input"]["UsbSharing"])
        self.assertEqual(c["Sound"], [])
        self.assertEqual(c["Serial"], [])
        self.assertEqual(c["Display"][0]["Hardware"], "virtio-gpu-pci")
        self.assertTrue(original["Sharing"]["ClipboardSharing"])

    def test_guest_reboot_uses_clean_exit_in_both_roles(self):
        for role in ("gateway", "workstation"):
            c = harden.hardened(fixture(), role, "/tmp/private/net.sock")
            self.assertEqual(c["QEMU"]["AdditionalArguments"].count("-no-reboot"), 1)

    def test_rejects_qemu_separator_injection_and_relative_socket(self):
        for path in ("relative.sock", "/tmp/sock,server=on", "/tmp/a b.sock", "/" + "a" * 100):
            with self.assertRaises(ValueError):
                harden.hardened(fixture(), "gateway", path)

    def test_rejects_unknown_architecture_or_extra_disk(self):
        c = fixture()
        c["System"]["Architecture"] = "x86_64"
        with self.assertRaises(ValueError):
            harden.hardened(c, "gateway", "/tmp/net.sock")
        c = fixture()
        c["Drive"].append({"ImageName": "host.raw", "ImageType": "Disk"})
        with self.assertRaises(ValueError):
            harden.hardened(c, "gateway", "/tmp/net.sock")

    def test_write_rejects_public_socket_directory(self):
        with tempfile.TemporaryDirectory(dir="/tmp", prefix="whonix-test-") as temp:
            root = Path(temp)
            bundle = root / "test.utm"
            (bundle / "Data").mkdir(parents=True)
            (bundle / "Data/disk.raw").touch()
            original = plistlib.dumps(fixture())
            (bundle / "config.plist").write_bytes(original)
            socket_dir = root / "public"
            socket_dir.mkdir(mode=0o755)
            os.chmod(socket_dir, 0o755)
            result = subprocess.run([sys.executable, str(Path(harden.__file__)), str(bundle),
                                     "--role", "gateway", "--socket", str(socket_dir / "net.sock"),
                                     "--write"], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"mode 0700", result.stderr)
            self.assertEqual((bundle / "config.plist").read_bytes(), original)
            self.assertFalse((bundle / "config.before-hardening.plist").exists())

    def test_write_sets_private_modes_and_keeps_original_backup(self):
        with tempfile.TemporaryDirectory(dir="/tmp", prefix="whonix-test-") as temp:
            root = Path(temp)
            bundle = root / "test.utm"
            (bundle / "Data").mkdir(parents=True)
            (bundle / "Data/disk.raw").touch()
            config = fixture()
            config["Information"]["UUID"] = "2C279BF0-E968-4EF1-B93E-61BABD03A7B7"
            original = plistlib.dumps(config)
            (bundle / "config.plist").write_bytes(original)
            command = [sys.executable, str(Path(harden.__file__)), str(bundle),
                       "--role", "gateway", "--socket", str(root / "net.sock"), "--write"]
            subprocess.run(command, check=True, capture_output=True)
            first_identity = plistlib.loads((bundle / "config.plist").read_bytes())["Information"]["UUID"]
            self.assertNotEqual(first_identity, config["Information"]["UUID"])
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(plistlib.loads((bundle / "config.plist").read_bytes())["Information"]["UUID"], first_identity)
            self.assertEqual((bundle / "config.before-hardening.plist").read_bytes(), original)
            for path, mode in [(bundle, 0o700), (bundle / "Data", 0o700),
                               (bundle / "config.plist", 0o600), (bundle / "Data/disk.raw", 0o600)]:
                self.assertEqual(path.stat().st_mode & 0o777, mode)

    def test_drive_external_metadata_is_not_preserved(self):
        c = fixture()
        c["Drive"][0].update(IsExternal=True, Bookmark="untrusted external disk")
        result = harden.hardened(c, "gateway", "/tmp/private/net.sock")
        self.assertNotIn("Bookmark", result["Drive"][0])
        self.assertNotIn("IsExternal", result["Drive"][0])


if __name__ == "__main__":
    unittest.main()
