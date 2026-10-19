# UTM hardening design

Apply configuration changes only to freshly generated bundles before importing them into UTM, with both VMs fully stopped. Never edit a running or suspended VM. `harden_utm.py` is a configuration transformer, not a running-VM safety monitor.

The transformer replaces all custom QEMU arguments and removes all UTM network adapters, then defines exactly two Gateway interfaces and one Workstation interface. Workstation has only the internal link. Gateway's external interface uses user-mode NAT with IPv6 disabled and no host port forwarding. This does not hide the Mac's external address from the Gateway or Tor entry guard, and does not block every possible Gateway-to-host/LAN connection. Guest firewall behavior still requires runtime testing.

The proposed internal link uses a QEMU `stream` backend with a Unix socket in an owner-only directory, instead of the upstream template's TCP listener on all interfaces. This removes the internal TCP port and restricts other local users through filesystem permissions. Processes running as your own macOS user or root remain trusted. UTM sandbox compatibility must be demonstrated before release; do not substitute an all-interface TCP listener if it fails.

Generate the local path:

```sh
python3 scripts/private_socket_dir.py
```

Use its output for the same `--socket` argument in both offline bundles:

```sh
python3 scripts/harden_utm.py /path/to/Gateway.utm --role gateway --socket /private/tmp/whonix-sillicon-501/internal.sock
python3 scripts/harden_utm.py /path/to/Workstation.utm --role workstation --socket /private/tmp/whonix-sillicon-501/internal.sock
```

These commands print proposed plists. Add `--write` to apply after review. The first original configuration is retained locally as `config.before-hardening.plist`. The UID above is an example; always use the generated path for your account. Start Gateway before Workstation. Do not distribute a bundle with a hard-coded path for someone else's UID.

Clipboard, directory shares, serial ports, USB sharing, and sound devices are disabled. The display uses `virtio-gpu-pci` without OpenGL acceleration. Hardware virtualization and the RNG remain enabled. Host TPM emulation is not enabled because adding an emulated TPM alone does not establish verified boot or disk protection.

Guest-side security must come from verified Whonix/Kicksecure packages and successful updates. Do not replace their firewall, remove required services indiscriminately, or claim full-disk encryption or Secure Boot without provisioning and validating those features separately.
