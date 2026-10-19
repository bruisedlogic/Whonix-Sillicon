# Validation record

Date: 2026-10-19. This is a development record, not a release certification.

Environment: Apple M2 Pro, 16 GiB RAM, macOS 27.0.1, UTM 5.0.8 (bundled QEMU 10.0), Lima 2.2.1, Debian 13 ARM64 build guest.

Source: upstream `18.2.1.9-developers-only`, commit `3c25009d615ffd37a3544ddc32b9b507b0650bb6`. The tag and commit verified with signing key fingerprint `916B8D99C38EAF5E8ADC7A2A8D66066A2EEACCDA` obtained from the official Whonix website and compared against its published fingerprint. This relies on the website/TLS trust path; no separate out-of-band identity ceremony was performed.

| Check | Result |
|---|---|
| Top-level upstream tag and commit signatures | Passed |
| Upstream source/submodule sanity check | Passed, with signature and tag policy enabled |
| Configuration regression tests | 8 passed |
| Archive path/link boundary tests | 3 passed |
| Disposable Gateway and Workstation bundles import into UTM | Passed |
| Both disposable ARM64 VMs start under UTM hardware virtualization | Passed; booted firmware only |
| QEMU stream Unix listener in QEMUHelper's private temporary directory | Passed |
| Workstation stream client connects to that listener | Passed; matched Unix socket endpoint pair in `lsof` |
| TCP/UDP sockets on those two QEMU processes during transport-only test | None, using `lsof -a -c QEMULauncher -iTCP -iUDP` |
| Whonix Gateway image build and archive SHA-256 | Passed |
| Whonix Workstation image build and archive SHA-256 | Passed |
| Gateway and Workstation graphical cold boot | Passed with a greetd software-rendering override; both normal and sysmaint desktops displayed |
| Raw runtime disk | Failed: UTM reported `drive0, #block500: Invalid argument` during first boot |
| QCOW2 replacements | Both `qemu-img check` passed; raw-disk error not reproduced on QCOW2 cold boots |
| Installed guest protections | Gateway reports AppArmor enabled; whonix-firewall and security-misc packages present; no OpenSSH server or QEMU guest agent installed |
| Signed package updates through Tor | Both normal updaters reached signed repositories; installation verification in progress |
| Gateway Tor connection | HTTPS check.torproject.org API returned `IsTor: true` |
| Warm reboot | One Gateway warm reboot did not recover the desktop or network; cold start reached sysmaint successfully. Unresolved reliability limitation |
| Stable Tor Browser on Linux ARM64 | Blocked: stable download metadata returned HTTP 404; alpha metadata offered 16.0a14 |
| Workstation networking | Correct internal-only eth0 address (10.152.152.11/18); signed repository downloads through Tor succeeded after cold-starting the pair. Full egress/failure tests pending |
| Independent security audit | Not performed |

The transport test used blank disposable disks, not Whonix. Starting firmware and establishing a host socket does not demonstrate guest anonymity, traffic forwarding, or a functioning Workstation. Test VMs were stopped and removed after the check.

## Findings resolved in the build wrapper

- Explicitly set `HOMEVAR` to the builder user's real home directory; upstream otherwise assumes `/home/<username>`, which differs from Lima's home directory.
- Install `sq`, `sqop`, and `sequoia-git` before the upstream initial sanity check.
- Fetch missing tags for the exact pinned submodule commits. Keep the upstream signature and tag checks enabled.

## Transport finding

The proposed Unix socket under `/private/tmp` did not appear while the UTM VM ran. The same backend created a socket using standalone Homebrew QEMU. Moving the socket into QEMUHelper's existing mode-0700 temporary directory worked in UTM, consistent with a sandbox path restriction. No sandbox entitlement or macOS protection was disabled.
