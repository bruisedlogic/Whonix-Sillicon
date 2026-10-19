#!/usr/bin/env python3
"""Offline UTM configuration hardening. Both VMs must be fully shut down.

Only generated ARM64 Whonix bundles with one local disk are accepted.
This changes virtual hardware configuration, not guest firewall policy.
"""
import argparse
import copy
import os
from pathlib import Path
import plistlib
import re
import tempfile
import uuid


def hardened(config, role, socket_path):
    c = copy.deepcopy(config)
    if role not in ("gateway", "workstation"):
        raise ValueError("Unknown role")
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", socket_path):
        raise ValueError("Socket path must be absolute and contain no QEMU separators")
    if len(socket_path.encode()) > 95:
        raise ValueError("Socket path is too long")
    if c.get("Backend") != "QEMU" or c.get("ConfigurationVersion") != 4:
        raise ValueError("Expected UTM QEMU configuration version 4")
    if c.get("System", {}).get("Architecture") != "aarch64":
        raise ValueError("Expected an ARM64 image")
    drives = c.get("Drive", [])
    if len(drives) != 1 or drives[0].get("ImageType") != "Disk":
        raise ValueError("Expected exactly one system disk and no attached media")
    name = drives[0].get("ImageName", "")
    if not name or Path(name).name != name or name in (".", ".."):
        raise ValueError("Disk must be local to the bundle's Data directory")
    c["Sharing"] = {"ClipboardSharing": False, "DirectoryShareMode": "None",
                    "DirectoryShareReadOnly": True}
    c["Input"] = {"MaximumUsbShare": 0, "UsbBusSupport": "3.0", "UsbSharing": False}
    c["Sound"] = []
    c["Serial"] = []
    c["Network"] = []  # All interfaces below; never an implicit NAT adapter.
    for display in c.get("Display", []):
        display["Hardware"] = "virtio-gpu-pci"
        display["DynamicResolution"] = False
    internal = f"stream,id=internal,addr.type=unix,addr.path={socket_path}"
    args = []
    if role == "gateway":
        args += ["-device", "virtio-net-pci,netdev=external,mac=02:00:00:00:01:01",
                 "-netdev", "user,id=external,ipv6=off,net=10.0.2.0/24",
                 "-device", "virtio-net-pci,netdev=internal,mac=02:00:00:00:01:02",
                 "-netdev", internal + ",server=on"]
    else:
        args += ["-device", "virtio-net-pci,netdev=internal,mac=02:00:00:00:02:01",
                 "-netdev", internal + ",server=off"]
    # Replace every custom argument; do not retain an old alternate network path.
    c["QEMU"] = {"AdditionalArguments": args, "BalloonDevice": False,
                 "DebugLog": False, "Hypervisor": True, "PS2Controller": False,
                 "RNGDevice": True, "RTCLocalTime": False, "TPMDevice": False,
                 "TSO": False, "UEFIBoot": True}
    c["System"].update(CPUCount=2 if role == "gateway" else 4,
                        MemorySize=2048 if role == "gateway" else 4096,
                        Target="virt", CPU="default")
    # Preserve image identity across repeated hardening runs.
    c["Information"].setdefault("UUID", str(uuid.uuid4()).upper())
    return c


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--role", required=True, choices=("gateway", "workstation"))
    parser.add_argument("--socket", required=True)
    parser.add_argument("--write", action="store_true", help="Apply; otherwise print proposed plist")
    args = parser.parse_args()
    bundle = args.bundle.resolve(strict=True)
    path = bundle / "config.plist"
    if path.is_symlink():
        raise SystemExit("Refusing symlinked configuration")
    # UTM keeps a suspended memory state under Data; never edit such a bundle.
    if any((bundle / "Data").glob("*.sav")) or any((bundle / "Data").glob("*.vmstate")):
        raise SystemExit("Discard suspended state and fully shut down the VM first")
    original = path.read_bytes()
    config = hardened(plistlib.loads(original), args.role, args.socket)
    disk = bundle / "Data" / config["Drive"][0]["ImageName"]
    if disk.is_symlink() or not disk.is_file():
        raise SystemExit("Missing local system disk, or disk is a symlink")
    result = plistlib.dumps(config, sort_keys=False)
    if not args.write:
        print(result.decode(), end="")
        return
    backup = bundle / "config.before-hardening.plist"
    if not backup.exists():
        with backup.open("xb") as f:
            os.chmod(backup, 0o600)
            f.write(original)
    fd, temporary = tempfile.mkstemp(dir=bundle, prefix=".config-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(result)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"Hardened {args.role}: {bundle.name}")


if __name__ == "__main__":
    main()
