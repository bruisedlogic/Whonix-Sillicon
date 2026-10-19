# Release validation — v0.1.0-preview.1

**Unofficial development preview; no security audit or anonymity guarantee.** Checked 2026-10-20 on M2 Pro, macOS 27.0.1, UTM 5.0.8 (bundled QEMU 10.0). Tor Browser 16.0a14 is ALPHA.

Release masters were prepared offline from the original never-booted, signature-verified upstream build. Gateway received 7 signed package upgrades; Workstation received 6. The official ARM64 browser archive and its source archive passed Tor Browser Developers signature verification. Testing used independent disposable disk copies; the release masters were never booted. Final image/disk hashes are in PREVIEW-MANIFEST.json.

| Check | Observation |
|---|---|
| Final archives | Host SHA-256 matched builder for both archives; extracted disk hashes matched manifest |
| Setup | Actual setup script accepted final archives, extracted exact files and prepared private configurations; both extracted QCOW2 disks passed qemu-img check |
| Source tests | 19 tests passed, including unsafe archive/link/duplicate rejection and Workstation network configuration boundaries |
| Desktop | Both roles booted; Whonix USER desktop and first-run notices appeared |
| Browser launch | Official alpha launched as ordinary user through upstream `torbrowser`; Whonix welcome page rendered |
| Browser HTTPS | Tor Project API displayed `IsTor: true` over HTTPS |
| Tor stopped | Fresh browser request failed with Secure Connection Failed; ordinary-user Python HTTPS probe failed resolving the destination; no warning was bypassed |
| Recovery | Initial immediate probe failed during restart; subsequent Python HTTPS and normal browser reload returned `IsTor: true` |
| Ordinary-user probes, Tor available | IPv4 and IPv6 TCP calls connected through the transparent routing policy. IPv4 DNS and UDP were rejected locally. IPv6 DNS returned an answer and IPv6 UDP send returned without reply; these socket results alone do not establish external egress |
| External virtual-NIC capture | 2,303 frames in the final QA Gateway run: 2,292 IPv4/TCP, 9 IPv6/ICMPv6, 2 other Ethernet. No observed direct DNS, UDP, known direct probe destination or canary marker. Capture is finite and does not cover all traffic or earlier boots |
| Browser process snapshot | Ten observed helper/content-process command lines, all UID 1000 and AppArmor enforce. Nine showed Seccomp 2 / NoNewPrivs 1; one showed 0 / 0. Process roles and sandbox parity were not independently established; this is not a complete sandbox pass |
| Keystroke service | **FAIL:** upstream Kloak repeatedly died under ARM64 seccomp (syscall 48). Timing camouflage unavailable; dropped input observed. Its sandbox was not weakened |

A new alpha-channel configuration initially had mode 0600 and blocked the ordinary-user launcher; final masters and build script use 0644 for public configuration files. The vendor browser cache is readable/executable by users and remains root-owned. No browser sandbox, AppArmor, firewall, privilege split or signature verification was disabled.

The earlier [24-case network matrix](https://github.com/bruisedlogic/Whonix-Sillicon/blob/main/docs/network-validation.md) covered Tor running/stopped and Gateway off on the earlier local pair. It is historical evidence, not a complete repeat on these exact release bytes. This candidate received the bounded smoke checks above. No claim is made that “all leak tests” passed: browser WebRTC/fingerprinting, privileged compromise, host/LAN attacks, timing correlation and update behavior remain unaudited.

Guest warm reset remains unresolved: `-no-reboot` intentionally powers off; manually Start in UTM. The local delivered preview pair was restored from verified pristine masters after testing. Diagnostic services, serial channels, capture arguments, guest journals/browser history and generated NVRAM are absent from distributed masters. The original local pair was left unchanged.
