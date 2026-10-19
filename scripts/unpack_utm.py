#!/usr/bin/env python3
"""Verify a locally built archive, unpack its one bundle, and apply hardening.

Obtain the expected SHA-256 from your trusted builder over its SSH control
channel. A checksum copied from an untrusted download is not authentication.
Requires macOS's tar for sparse disk extraction. Does not import or start UTM.
"""
import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


def archive_layout(archive):
    root = None
    files = []
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isdir() or member.isfile()):
                raise ValueError("Archive contains an unsafe path, link, or special file")
            bundles = [i for i, part in enumerate(path.parts) if part.endswith(".utm")]
            if len(bundles) != 1:
                raise ValueError("Expected one UTM bundle prefix")
            candidate = PurePosixPath(*path.parts[:bundles[0] + 1])
            if root is None:
                root = candidate
            if root != candidate:
                raise ValueError("Archive contains multiple bundles")
            relative = path.relative_to(root).as_posix()
            if member.isdir():
                if relative not in (".", "Data"):
                    raise ValueError("Unexpected directory")
            else:
                if relative == "config.plist":
                    if member.size > 1024 * 1024:
                        raise ValueError("Oversized configuration")
                elif not re.fullmatch(r"Data/[A-Za-z0-9_.-]+\.raw", relative):
                    raise ValueError("Unexpected file in bundle")
                elif not 0 < member.size <= 64 * 1024**3:
                    raise ValueError("Disk size is outside the allowed range")
                files.append(relative)
    if root is None or len(files) != 2 or files.count("config.plist") != 1 or len(set(files)) != 2:
        raise ValueError("Expected exactly one configuration and one raw disk")
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--role", required=True, choices=("gateway", "workstation"))
    args = parser.parse_args()
    os.umask(0o077)
    archive = args.archive.resolve(strict=True)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.sha256):
        raise SystemExit("Expected a complete SHA-256 digest")
    with archive.open("rb") as f:
        actual = hashlib.file_digest(f, "sha256").hexdigest()
    if actual != args.sha256.lower():
        raise SystemExit("Archive checksum mismatch")
    root = archive_layout(archive)
    if root.name != f"Whonix-{args.role.title()}-LXQt.utm":
        raise SystemExit("Bundle name does not match the selected role")
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    output = args.output.resolve(strict=True)
    destination = output / root.name
    if destination.exists() or destination.is_symlink():
        raise SystemExit("Destination bundle already exists; refusing to overwrite it")
    qemu_img = shutil.which("qemu-img")
    if qemu_img is None:
        raise SystemExit("qemu-img is required for the UTM runtime disk conversion")
    scripts = Path(__file__).resolve().parent
    socket_path = subprocess.check_output([sys.executable, str(scripts / "private_socket_dir.py")], text=True).strip()
    temporary = Path(tempfile.mkdtemp(prefix=".unpack-", dir=output))
    try:
        subprocess.run(["/usr/bin/tar", "--no-same-owner", "--no-same-permissions",
                        "--no-acls", "--no-xattrs", "--no-fflags",
                        f"--strip-components={len(root.parts) - 1}", "-xzf", str(archive),
                        "-C", str(temporary)], check=True)
        bundle = temporary / root.name
        config_path = bundle / "config.plist"
        config = plistlib.loads(config_path.read_bytes())
        disks = list((bundle / "Data").glob("*.raw"))
        drives = config.get("Drive", [])
        if len(disks) != 1 or len(drives) != 1 or drives[0].get("ImageName") != disks[0].name:
            raise ValueError("Configuration does not reference the one archived local disk")
        raw = disks[0]
        # Use a version-3 QCOW2 runtime disk with no optional new-format features.
        # Keep the original archive untouched for recovery and provenance.
        qcow = raw.with_suffix(".qcow2")
        subprocess.run([qemu_img, "convert", "-f", "raw", "-O", "qcow2", "-o",
                        "compat=1.1,lazy_refcounts=off", str(raw), str(qcow)], check=True)
        subprocess.run([qemu_img, "check", str(qcow)], check=True)
        config["Drive"][0]["ImageName"] = qcow.name
        raw.unlink()
        config["Information"]["Name"] = f"Whonix {args.role.title()} — ARM64 experimental"
        config_path.write_bytes(plistlib.dumps(config, sort_keys=False))
        subprocess.run([sys.executable, str(scripts / "harden_utm.py"), str(bundle),
                        "--role", args.role, "--socket", socket_path, "--write"], check=True)
        bundle.rename(destination)
        print(destination)
    finally:
        shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
