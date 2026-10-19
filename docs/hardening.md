# UTM hardening design

Apply configuration changes only to freshly generated bundles before importing them into UTM, with both VMs fully stopped. Never edit a running or suspended VM. `harden_utm.py` is a configuration transformer, not a running-VM safety monitor.

Applying the transformer requires ownership of the bundle, Data directory, disk, and configuration. It sets bundle and Data directory permissions to 0700, and disk/configuration permissions to 0600. This limits other local accounts' access; the current macOS user and root remain trusted.

The two fixed VM UUIDs from upstream's templates are replaced on first hardening, so separate imports do not share those prototype identities. Reapplying hardening preserves the new UUID. The default socket filename supports one pair at a time per macOS user; give each additional pair a distinct socket filename in the same private directory, using the identical path for that pair's Gateway and Workstation.

The transformer replaces all custom QEMU arguments and removes all UTM network adapters, then defines exactly two Gateway interfaces and one Workstation interface. Workstation has only the internal link. Gateway's external interface uses user-mode NAT with IPv6 disabled and no host port forwarding. This does not hide the Mac's external address from the Gateway or Tor entry guard, and does not block every possible Gateway-to-host/LAN connection. Guest firewall behavior still requires runtime testing.

The internal link uses a QEMU `stream` backend with a Unix socket in UTM QEMUHelper's owner-only temporary directory, instead of the upstream template's TCP listener on all interfaces. This removes the internal TCP port and restricts other local users through filesystem permissions. Processes running as your own macOS user or root remain trusted. A transport-only test first established the socket connection; subsequent guest tests verified Tor HTTPS and failure behavior. See [network validation](network-validation.md) for scope. Workstation uses `reconnect-ms=2000`, which retries only this same private endpoint after Gateway exits. This does not create a fallback Internet path or bypass guest firewall/Tor policy. A socket under `/private/tmp` did not appear in the sandboxed UTM test, so that location is not used.

Generate the local path:

```sh
python3 scripts/private_socket_dir.py
```

Use its output for the same `--socket` argument in both offline bundles:

```sh
socket_path=$(python3 scripts/private_socket_dir.py)
python3 scripts/harden_utm.py /path/to/Gateway.utm --role gateway --socket "$socket_path"
python3 scripts/harden_utm.py /path/to/Workstation.utm --role workstation --socket "$socket_path"
```

These commands print proposed plists. Add `--write` to apply after review. The first original configuration is retained locally as `config.before-hardening.plist`. Always use the generated path for your account. Start Gateway before Workstation. Do not distribute a bundle with a hard-coded path for someone else's home directory or UID. The temporary directory must already exist and be owned by the current user with mode 0700. The helper refuses other permissions. Long paths or QEMU argument separator characters are rejected.

Clipboard, directory shares, serial ports, USB sharing, and sound devices are disabled. The display uses `virtio-gpu-pci` without OpenGL acceleration. Hardware virtualization and the RNG remain enabled. Host TPM emulation is not enabled because adding an emulated TPM alone does not establish verified boot or disk protection.

QEMU's `-no-reboot` avoids the reproduced warm-reset hang by exiting cleanly on a guest reboot request. The operator must start the VM again. This is a manual cold-start workaround; no claim is made that firmware warm reboot is fixed. The unsuccessful GICv2/userspace-interrupt-controller trial was discarded; standard UTM hardware virtualization and interrupt-controller selection remain in use.

Guest-side security must come from verified Whonix/Kicksecure packages and successful updates. Do not replace their firewall, remove required services indiscriminately, or claim full-disk encryption or Secure Boot without provisioning and validating those features separately.
