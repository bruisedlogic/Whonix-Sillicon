# Preparing and starting the UTM pair

This is a development workflow for trusted, locally built images. It does not produce a supported Whonix release. Read the README and validation record before using it.

## Prepare the disks

The original UTM raw disk failed with an I/O error in the development environment. The runtime uses QCOW2 version 3 (`compat=1.1,lazy_refcounts=off`). Without accelerated graphics, the Wayland desktop also needed software rendering.

Inside the disposable Debian builder, after `build.sh` completes, run `scripts/prepare_runtime.py` as the ordinary build user for each original raw disk. Copy this script into the builder first. It needs sudo, util-linux, and qemu-utils. It creates a separate disk, mounts only that copy, adds a greetd service environment override for pixman/software rendering, unmounts, converts to QCOW2, checks integrity, and prints the resulting SHA-256. Keep the original image and archive unchanged.

```sh
python3 prepare_runtime.py /path/to/Whonix-Gateway-LXQt-18.2.1.9.arm64.raw /path/to/gateway-runtime.qcow2
python3 prepare_runtime.py /path/to/Whonix-Workstation-LXQt-18.2.1.9.arm64.raw /path/to/workstation-runtime.qcow2
```

Never mount an untrusted image on the Mac or run this helper against a running VM. The builder is a disposable trust boundary, not protection against every malicious filesystem exploit.

## Prepare the bundles on macOS

Use Python 3.11 or later and `qemu-img`. Copy the original `.utm.tar.gz` archives through Lima's control channel and compare their SHA-256 with the builder's output. `scripts/unpack_utm.py ARCHIVE OUTPUT_DIRECTORY --role gateway|workstation --sha256 EXPECTED_DIGEST` validates archive paths and file types, extracts a private bundle, converts its raw disk to QCOW2, and applies host-integration/network hardening. It refuses existing destinations. It does **not** add the guest software-rendering override itself.

Before importing the bundles, replace each unpacked QCOW2 disk with the corresponding `prepare_runtime.py` output, transferred through the builder control channel. Compare the transferred file's SHA-256 with that helper's output, preserve the configured filename, and set the disk mode to 0600. Keep bundle and Data directories at 0700. Re-run `harden_utm.py` for both roles using the same local socket path as described in `hardening.md`.

Do not import the unmodified upstream template: its internal network transport and host integration differ from this configuration. Do not reuse another Mac's hard-coded socket path.

## Start and maintain

1. Open each prepared `.utm` bundle using UTM's File > Open. The custom QEMU notice is expected because the private internal transport is configured explicitly.
2. Start Gateway first. Wait for Tor to connect. Start Workstation second.
3. For updates, select **PERSISTENT Mode | SYSMAINT Session** in each VM's boot menu. Use **Install Updates** in the System Maintenance Panel. Keep the Gateway running while updating Workstation. Do not disable repository signature checks.
4. Shut down normally from inside each guest. Stop Workstation before Gateway. If Gateway's QEMU process is restarted, cold-start Workstation afterward so its internal socket connection is recreated. Warm reboot reliability remains a validation item.
5. Use **PERSISTENT Mode | USER Session** for daily activities, keeping user/sysmaint separation enabled. Do not select the option that removes the split.

The upstream image enables passwordless local login and autologin. Root is locked and no SSH server was installed in the tested image. Set your own guest passwords using **Manage Passwords** and then consider disabling GUI autologin; no generated password is embedded in this repository. FileVault protects the Mac's disk at rest, but a logged-in host account can access these VMs.

A functioning desktop or successful command-line Tor check does not solve the stable ARM64 Tor Browser availability blocker. Do not substitute ordinary Firefox and treat it as equivalent.
