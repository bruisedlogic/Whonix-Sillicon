# Whonix-Sillicon

Build and isolation tooling for a Whonix Gateway/Workstation pair in UTM on Apple Silicon. Builds use pinned, signature-verified upstream source and retain Whonix's firewall, AppArmor, signed updates and user/sysmaint separation.

**Development preview — not a supported Whonix port or a production browsing image.** Apple Silicon/UTM is unsupported upstream. Stable Linux ARM64 Tor Browser is still unavailable in the official download table checked on 2026-10-20. The project does not replace it with alpha Tor Browser or ordinary Firefox and call the result stable.

## Current results

| Area | Status |
|---|---|
| Gateway and Workstation | Built, updated and booted on M2 Pro / UTM 5.0.8 |
| Workstation HTTPS | Tor Project API reported `IsTor: true` using Python sockets and certificate-verified TLS |
| Network validation | One bounded 24-case matrix: IPv4/IPv6 TCP, DNS, UDP and HTTPS with Tor running, Tor stopped and Gateway off; see the [test report](docs/network-validation.md) |
| Gateway process restart | Workstation reconnects to the same private Unix socket; HTTPS recovered without restarting Workstation |
| Guest reboot | Uses a **manual cold-start workaround**, described below; the underlying warm-reset hang remains unresolved |
| Stable ARM64 Tor Browser | Blocked by official release availability; no browser installed |
| Security audit / release images | No audit; no distributable binary release |

See the [validation record](docs/validation.md) for exact scope, failures and limitations. Finite tests provide evidence for this setup, not proof of complete leak resistance.

## Isolation

Workstation has one internal interface and no NAT or bridged interface. Only Gateway has external NAT. The internal connection uses a Unix socket in UTM QEMUHelper's owner-only temporary directory, with a two-second reconnect interval on Workstation. It has no internal TCP listener.

Clipboard, host directory sharing, USB passthrough, audio and accelerated graphics are disabled. Bundle directories are mode 0700 and disks/configurations 0600. macOS, UTM, the current host account and root remain trusted. The configuration does not provision guest disk encryption or verified Secure Boot.

## Reboot behavior

A guest-initiated warm reboot reproduced a hang after firmware launched Debian. Changing the interrupt-controller configuration did not resolve it, and that trial configuration was discarded.

The hardener now adds QEMU's `-no-reboot`: selecting **Reboot** shuts the VM down cleanly instead of entering the failing warm-reset path. **Wait for it to stop, then click Start in UTM.** This is an intentional workaround, not seamless automatic reboot or a firmware repair. Gateway should start first; allow Tor to connect before using Workstation. Workstation's private link reconnects if Gateway is restarted.

## Build and prepare

Requirements: Apple Silicon Mac, current UTM, Python 3.11+, `qemu-img`, and a disposable Debian 13 ARM64 builder with at least 4 GiB RAM and approximately 65 GiB disk capacity. Upstream build code runs **inside the builder**, never directly on macOS.

```sh
limactl start --name=whonix-builder --yes builder/debian-arm64.yaml
limactl shell whonix-builder -- bash -c 'cat > "$HOME/build-whonix.sh"' < scripts/build.sh
limactl shell whonix-builder -- bash -lc 'bash "$HOME/build-whonix.sh"'
```

The supplied Lima definition has no host mounts, SSH agent forwarding, container runtime or automatic service port forwarding. Its dated Debian image and SHA-512 digest are pinned. The builder has direct download access and is separate from the runtime pair.

Builds pin `18.2.1.9-developers-only` and its exact commit, matching the upstream stable announcement. Signature and submodule checks stay enabled. See [runtime preparation](docs/runtime.md) for QCOW2 conversion, software rendering, local socket configuration, import and signed updates. Do not import the unchanged upstream UTM template.

## Publication

This repository publishes original integration source and documented development results. It does not redistribute or certify Whonix images. The local test disks contain machine-specific state and must not be uploaded as release assets.

The [release checklist](docs/release.md) distinguishes source publication from a usable image release. The stable browser and warm-reset limitations remain prominent release blockers. The project is independent of Whonix, Kicksecure, UTM and the Tor Project. The repository spelling is intentional.

## Documentation

- [Security scope and reporting](SECURITY.md)
- [UTM hardening design](docs/hardening.md)
- [Runtime preparation and maintenance](docs/runtime.md)
- [Bounded network test methodology and results](docs/network-validation.md)
- [Build provenance](docs/build-provenance.json)
- [Official Whonix Apple Silicon status](https://www.whonix.org/wiki/MacOS#Apple_Silicon)
- [Official Tor Browser platform/channel table](https://download.torproject.org/tor-browser-for-desktop/)
- [Upstream build documentation](https://www.whonix.org/wiki/Dev/Build_Documentation/images)
- [Whonix signing key](https://www.whonix.org/wiki/Main/Project_Signing_Key)
- [Whonix 18.2.1.9 announcement](https://forums.whonix.org/t/23402)
