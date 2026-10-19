#!/usr/bin/env python3
"""Locate UTM QEMUHelper's owner-only directory for the Unix internal link.

This does not launch VMs or remove a stale socket. The same socket path must
be embedded in both bundles before import into UTM.
"""
import os
from pathlib import Path
import stat


def main():
    os.umask(0o077)
    directory = Path.home() / "Library/Containers/com.utmapp.QEMUHelper/Data/tmp"
    if not directory.exists():
        raise SystemExit("Run UTM once to initialize its QEMUHelper container first")
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise SystemExit("Socket directory must be a real directory owned by you with mode 0700")
    print(directory / f"whonix-{os.getuid()}.sock")


if __name__ == "__main__":
    main()
