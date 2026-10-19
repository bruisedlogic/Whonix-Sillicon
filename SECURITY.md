# Security scope

This is an independent experimental integration. It is not an anonymity guarantee, an upstream-supported port, or a completed security audit.

The intended boundary protects the Workstation's network path through the Gateway and minimizes guest-to-host integration. It does not protect against a compromised macOS host, hypervisor escape, physical access to an unlocked Mac, or account-based identity disclosure. The host can observe guest memory and disks. Any internal transport accessible to the host remains within this trust boundary.

Do not weaken signature verification, enable host shares to fix build problems, add a Workstation NAT adapter, or disable the Whonix firewall to obtain connectivity. Failed security checks block release.

Images must never contain GitHub credentials, builder SSH keys, personal accounts, or the builder's filesystem. Tests must be run again after changes to networking, UTM, QEMU, guest kernels, or security packages.
