#!/usr/bin/env python3
"""Create the owner-only directory for the proposed Unix internal link.

This does not launch VMs or remove a stale socket. The same socket path must
be embedded in both bundles before import into UTM.
"""
import os
from pathlib import Path
import stat


def main():
    os.umask(0o077)
    directory = Path(f"/private/tmp/whonix-sillicon-{os.getuid()}")
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise SystemExit("Socket directory must be a real directory owned by you with mode 0700")
    print(directory / "internal.sock")


if __name__ == "__main__":
    main()
