#!/usr/bin/env python3
"""Prepare a *trusted locally built* ARM64 raw image in the Debian builder.

Creates a separate copy, adds software-rendering settings, and converts it to
QCOW2. Never run on a downloaded/untrusted or running guest disk. sudo mount
operates inside the disposable Linux builder, never on the Mac host.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

RENDERER = """[Service]
Environment=WLR_RENDERER=pixman
Environment=LIBGL_ALWAYS_SOFTWARE=1
Environment=QT_QUICK_BACKEND=software
"""


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if os.uname().sysname != "Linux" or os.geteuid() == 0:
        raise SystemExit("Run as an ordinary user in the disposable Debian builder")
    source = args.raw.resolve(strict=True)
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        raise SystemExit("Refusing to overwrite an existing output")
    layout = json.loads(subprocess.check_output(["sfdisk", "--json", str(source)], text=True))["partitiontable"]
    roots = [p for p in layout["partitions"] if p["type"].upper() == "B921B045-1DF0-41C3-AF44-4C6F280D3FAE"]
    if layout.get("sectorsize") != 512 or len(roots) != 1:
        raise SystemExit("Expected exactly one ARM64 Linux root partition on a 512-byte-sector disk")
    root = roots[0]
    temporary = Path(tempfile.mkdtemp(prefix=".runtime-", dir=output.parent))
    mount = temporary / "mnt"
    mount.mkdir()
    mounted = False
    try:
        raw = temporary / "disk.raw"
        run("qemu-img", "convert", "-f", "raw", "-O", "raw", str(source), str(raw))
        options = f"loop,nodev,nosuid,noexec,offset={root['start'] * 512},sizelimit={root['size'] * 512}"
        run("sudo", "mount", "-t", "ext4", "-o", options, str(raw), str(mount))
        mounted = True
        relative = Path("etc/systemd/system/greetd.service.d")
        for parent in (Path("etc"), Path("etc/systemd"), Path("etc/systemd/system"), relative):
            if (mount / parent).is_symlink():
                raise ValueError("Refusing a symlink in the configuration path")
        directory = mount / relative
        run("sudo", "install", "-d", "-o", "0", "-g", "0", "-m", "755", str(directory))
        config = temporary / "renderer.conf"
        config.write_text(RENDERER)
        destination = directory / "80-utm-software-renderer.conf"
        if destination.is_symlink():
            raise ValueError("Refusing a symlinked renderer configuration")
        run("sudo", "install", "-o", "0", "-g", "0", "-m", "644", str(config), str(destination))
        run("sudo", "umount", str(mount))
        mounted = False
        qcow = temporary / "runtime.qcow2"
        run("qemu-img", "convert", "-f", "raw", "-O", "qcow2", "-o",
            "compat=1.1,lazy_refcounts=off", str(raw), str(qcow))
        run("qemu-img", "check", str(qcow))
        qcow.rename(output)
        with output.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        print(json.dumps({"output": str(output), "sha256": digest, "renderer": "pixman"}))
    finally:
        if mounted:
            # If unmount fails, retain the working directory; never delete a mount.
            run("sudo", "umount", str(mount))
        shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
