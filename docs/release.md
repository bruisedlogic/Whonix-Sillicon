# Development preview publication

The downloadable prerelease is an **unofficial development preview**, not a stable or upstream-supported port. Official ARM64 alpha Tor Browser is explicitly labeled alpha. Unavailable Kloak keystroke protection, manual cold reboot, passwordless local defaults and lack of audit must remain visible.

Release masters are copies of the original verified build, updated offline through signed repositories and sanitized before first boot. Testing uses separate disposable copies. Only config.plist and one self-contained QCOW2 disk belong in each image archive. Never publish used disks, NVRAM, diagnostics, packet captures, Tor state, journals, host paths or credentials.

Publish both image archives, strict setup kit, exact image/disk hashes, unsigned-checksum trust explanation, package/license inventories, corresponding-source directions, build provenance and a sanitized validation record. The setup script creates per-pair private sockets and new UTM UUIDs. No browser or firewall sandbox may be disabled to obtain a passing result.

Stable support would require a stable upstream ARM64 browser, resolution of ARM64 security-service failures, reliable reboot, independent review and broader adversarial testing. Finite test success does not satisfy those requirements.

See [setup](../releases/v0.1.0-preview.1/SETUP.md), [security scope](../SECURITY.md), and the prerelease's SOURCES.md and RELEASE-VALIDATION.md assets.
