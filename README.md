# Whonix-Sillicon

Independent work toward a hardened Whonix Gateway/Workstation pair for UTM on Apple Silicon.

**Status: experimental, not a release.** Upstream does not support Apple Silicon and describes its UTM target as unmaintained. This repository cannot change that support status. No security audit or production-readiness claim is made. Do not use an unvalidated image for sensitive activity.

There is an additional browser blocker: on 2026-10-19, Tor's stable Linux ARM64 download metadata returned HTTP 404, while the alpha channel offered `16.0a14`. This project does not silently substitute an alpha browser or ordinary Firefox for stable Tor Browser. A successful image build alone therefore does not establish a complete browsing environment.

The spelling of this repository name is intentional. This project is not affiliated with or endorsed by Whonix, Kicksecure, or UTM.

## Design

Build from the upstream `18.2.1.9-developers-only` tag, matching the stable release announcement. Verify its signature and exact commit before running build code. Build the Gateway and Workstation sequentially in a disposable Debian 13 ARM64 builder, without Mac directory mounts.

Retain Whonix/Kicksecure's guest firewall, AppArmor, kernel hardening, signed package updates, and privilege separation. Additional hardening should reduce host integration rather than replace upstream security mechanisms with an unreviewed collection of sysctl settings.

The intended runtime configuration disables clipboard and directory sharing, USB passthrough, audio, and accelerated graphics. The Workstation has one internal network interface and no NAT or bridged interface. Only the Gateway has an external interface. Internal transport and runtime isolation must be validated before a release.

## Build

See `scripts/build.sh`. Run inside a clean Debian 13 ARM64 VM as an ordinary user with sudo access. The builder must have at least 4 GiB RAM and approximately 65 GiB free disk capacity. Build dependencies and upstream scripts install software inside the builder. They must never run directly on macOS.

For a fresh builder on macOS with Lima already installed:

```sh
limactl start --name=whonix-builder --yes builder/debian-arm64.yaml
limactl shell whonix-builder -- bash -c 'cat > "$HOME/build-whonix.sh"' < scripts/build.sh
limactl shell whonix-builder -- bash -lc 'bash "$HOME/build-whonix.sh"'
```

The supplied Lima configuration has no host mounts, SSH agent forwarding, container runtime, or automatic guest-service port forwarding. Its dated Debian image and SHA-512 digest are pinned. The image URL may eventually be retired; update the URL and independently verified digest together. The builder has direct network access for downloads and is separate from the Whonix runtime VMs.

See [runtime preparation and startup](docs/runtime.md) for QCOW2 conversion, software rendering, importing, and signed guest updates. See [validation](docs/validation.md) for actual results and remaining blockers.

## Release gates

- Verify upstream signing fingerprint, tag signature, exact commit, and submodules.
- Build both images and record package versions and source revisions.
- Import and boot both images in UTM on Apple Silicon.
- Validate final UTM configuration and actual QEMU arguments.
- Confirm there are no unintended host shares or externally listening internal network ports.
- Update both guests successfully using signed repositories.
- Verify Tor bootstrap and Tor Browser availability on ARM64.
- Confirm Workstation connectivity uses Tor and fails closed when the Gateway or Tor stops.
- Test DNS and IPv6 failure paths, direct TCP/UDP egress, and reboot persistence.
- Remove build credentials, SSH access, temporary tooling, and machine-specific state before distributing an image.
- Publish hashes, provenance, limitations, and test results for each image.

Passing these gates establishes evidence for a particular configuration; it does not establish that the platform is audited or supported upstream.

## References

- [Whonix on macOS and Apple Silicon](https://www.whonix.org/wiki/MacOS#Apple_Silicon)
- [Upstream build documentation](https://www.whonix.org/wiki/Dev/Build_Documentation/images)
- [Whonix signing key](https://www.whonix.org/wiki/Main/Project_Signing_Key)
- [Whonix 18.2.1.9 announcement](https://forums.whonix.org/t/23402)
