#!/usr/bin/env python3
"""Verify and prepare one development-preview UTM pair. Does not start VMs.

Use the setup kit and image archives from the same GitHub prerelease. SHA-256
detects corruption; it is not independent publisher authentication.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import uuid

from harden_utm import hardened


def extract_bundle(archive, temporary, expected_bundle):
    """Copy two exact regular files; never apply archive paths or metadata."""
    seen = set()
    bundle = temporary / expected_bundle
    (bundle / 'Data').mkdir(parents=True, mode=0o700)
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != expected_bundle:
                raise ValueError('Unsafe or unexpected archive path')
            relative = PurePosixPath(*path.parts[1:]).as_posix()
            if member.isdir() and relative in ('.', 'Data'):
                continue
            if not member.isfile() or relative in seen:
                raise ValueError('Archive link, duplicate or special file rejected')
            if relative == 'config.plist':
                limit = 1024 * 1024
            elif relative == 'Data/system.qcow2':
                limit = 32 * 1024**3
            else:
                raise ValueError('Unexpected file in image bundle')
            if not 0 < member.size <= limit:
                raise ValueError('Invalid archived file size')
            seen.add(relative)
            source = tar.extractfile(member)
            if source is None:
                raise ValueError('Missing archive data')
            with source, (bundle / relative).open('xb') as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            os.chmod(bundle / relative, 0o600)
    if seen != {'config.plist', 'Data/system.qcow2'}:
        raise ValueError('Expected one configuration and one disk')
    with (bundle / 'Data/system.qcow2').open('rb') as disk:
        header = disk.read(72)
    if len(header) != 72 or header[:4] != b'QFI\xfb':
        raise ValueError('Invalid QCOW2 header')
    if struct.unpack('!I', header[4:8])[0] != 3:
        raise ValueError('Expected QCOW2 version 3')
    if any(header[8:20]) or any(header[32:36]) or any(header[60:72]):
        raise ValueError('Backing files, encryption or internal snapshots are not accepted')
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('PREVIEW-MANIFEST.json'))
    args = parser.parse_args()
    os.umask(0o077)
    if sys.platform != 'darwin' or os.geteuid() == 0:
        raise SystemExit('Run as your ordinary macOS user, without sudo')
    manifest = json.loads(args.manifest.read_text())
    entries = manifest['images']
    if len(entries) != 2 or {e['role'] for e in entries} != {'gateway', 'workstation'}:
        raise SystemExit('Expected a manifest for exactly one pair')
    downloads = args.downloads.resolve(strict=True)
    # Verify both archives before writing an installed bundle.
    for entry in entries:
        if Path(entry['archive']).name != entry['archive']:
            raise ValueError('Archive must be a local filename')
        archive = downloads / entry['archive']
        if archive.is_symlink() or not archive.is_file():
            raise ValueError('Missing local archive, or symlinked archive')
        with archive.open('rb') as data:
            digest = hashlib.file_digest(data, 'sha256').hexdigest()
        if digest != entry['sha256']:
            raise ValueError('Archive checksum mismatch: ' + entry['archive'])
    destination = args.destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise SystemExit('Destination must not exist; never overwrite an installed pair')
    if not destination.parent.is_dir():
        raise SystemExit('Create the destination parent directory first')
    socket_path = subprocess.check_output(
        [sys.executable, str(Path(__file__).with_name('private_socket_dir.py')),
         '--pair-id', uuid.uuid4().hex[:8]], text=True).strip()
    temporary = Path(tempfile.mkdtemp(prefix='.preview-setup-', dir=destination.parent))
    try:
        for entry in entries:
            name = entry['bundle']
            if Path(name).name != name or name != f"Whonix-{entry['role'].title()}-LXQt.utm":
                raise ValueError('Unexpected bundle name')
            bundle = extract_bundle(downloads / entry['archive'], temporary, name)
            config_path = bundle / 'config.plist'
            config = hardened(plistlib.loads(config_path.read_bytes()), entry['role'], socket_path)
            if config['Drive'][0]['ImageName'] != 'system.qcow2':
                raise ValueError('Configuration does not reference the packaged disk')
            with (bundle / 'Data/system.qcow2').open('rb') as data:
                if hashlib.file_digest(data, 'sha256').hexdigest() != entry['disk_sha256']:
                    raise ValueError('Extracted disk checksum mismatch')
            config_path.write_bytes(plistlib.dumps(config, sort_keys=False))
            os.chmod(bundle, 0o700)
            os.chmod(bundle / 'Data', 0o700)
            os.chmod(config_path, 0o600)
        temporary.rename(destination)
        print('Prepared DEVELOPMENT PREVIEW pair in ' + str(destination))
        print('Open both .utm bundles in UTM. Start Gateway first and wait for Tor.')
        print('Workstation includes ALPHA Tor Browser. Reboot powers off; manually Start again.')
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


if __name__ == '__main__':
    main()
