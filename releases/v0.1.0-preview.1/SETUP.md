# UTM development preview — v0.1.0-preview.1

**UNOFFICIAL / UNSUPPORTED / NOT AUDITED. Do not use for sensitive activity.**
This Apple Silicon integration is independent of Whonix, Kicksecure, UTM and Tor.
The Workstation includes official **Tor Browser 16.0a14 ARM64 ALPHA**, not stable.
Kloak crashes under ARM64 seccomp: **keystroke timing protection is unavailable; input can drop keystrokes**.
Guest Reboot powers off; manually Start again. No guest disk encryption or verified Secure Boot is provisioned. Upstream passwordless local login/autologin remains; use SYSMAINT to configure your own credentials before personal use. A trusted, updated Mac and UTM are required.

## Download

Use assets from [this prerelease](https://github.com/bruisedlogic/Whonix-Sillicon/releases/tag/v0.1.0-preview.1):

- `Whonix-Sillicon-Gateway-arm64-v0.1.0-preview.1.utm.tar.gz`
- `Whonix-Sillicon-Workstation-arm64-v0.1.0-preview.1.utm.tar.gz`
- `Whonix-Sillicon-Setup-v0.1.0-preview.1.tar.gz`
- `PREVIEW-MANIFEST.json`, `SETUP.md`, `VM-SHA256SUMS`

Keep them together in a new download folder. Source/license assets are separate optional downloads; see SOURCES.md. Required host: Apple Silicon, UTM 5.0.8 (tested), Python 3.11+, at least 40 GiB free space and enough memory for 2 GiB Gateway plus 4 GiB Workstation. Close other VMs. Open UTM once to initialize its helper container.

SHA-256 detects corruption; these checksums are **unsigned**, and depend on trust in GitHub/HTTPS and this publisher. Upstream signing keys do not authenticate the modified images. Review the scripts before running them. Never run setup with sudo.

In Terminal, change into that folder and run:

```sh
shasum -a 256 -c VM-SHA256SUMS
tar -xzf Whonix-Sillicon-Setup-v0.1.0-preview.1.tar.gz
python3 Whonix-Sillicon-preview-setup/setup_preview.py --downloads "$PWD" --destination "$HOME/Documents/Whonix-Sillicon-preview.1"
```

Every checksum must say OK. The destination must not already exist. Setup verifies both archives and extracted disk hashes, rejects unsafe archive paths/links, sets owner-only file permissions, and allocates a distinct private socket and UTM UUIDs for your pair. It does not import or start VMs. Keep the extracted setup folder with its manifest. If the helper directory is missing, open UTM and initialize it, then retry. Do not change the socket to TCP or add a Workstation NAT interface.

## Start and applications

1. In UTM, File → Open each generated `.utm` bundle in the destination. Custom QEMU arguments are intentional and should be reviewed against the source; do not import the unchanged archive templates.
2. Start **Gateway first**, complete upstream connection/setup prompts and wait for Tor to connect.
3. Start Workstation. Select **PERSISTENT Mode | USER Session**, finish the first-run notices, then open Tor Browser from the application menu or run `torbrowser`.
4. The **SYSMAINT** session is for administration/updates. Its maintenance panel is not the normal application desktop. See [application inventory](https://github.com/bruisedlogic/Whonix-Sillicon/blob/main/docs/applications.md).

Keep unsupported-platform warnings visible. Use the Whonix browser launcher: it supplies Gateway proxy/stream-isolation settings. Do not start the bundled Tor daemon separately. Alpha updates remain alpha; keep browser signature verification and signed OS repositories enabled. Update OS packages through the upstream maintenance workflow; check browser updates before browsing.

For reboot, wait until UTM shows stopped, then Start manually. Start Gateway before Workstation. Shut down Workstation before Gateway. If Gateway is off or Tor unavailable, browsing should fail; do not add alternate connectivity to fix it.

## What is and is not tested

The source repository contains a bounded ordinary-user network report, not a full adversarial audit. Consult RELEASE-VALIDATION.md for this candidate's actual checks. No guarantee is made about all browser leaks, WebRTC/fingerprinting, privileged compromise, traffic correlation or future updates. macOS/UTM/the host account remain trusted. Clipboard, folders, USB passthrough, audio and accelerated graphics are disabled. These restrictions do not protect against a compromised host.
