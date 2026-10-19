# Security scope and reporting

## Support status

This repository is a development integration, not an upstream-supported Apple Silicon port, audited anonymity system or stable browsing image. No production-supported release exists. Do not use the development images for sensitive activity.

A stable Linux ARM64 Tor Browser was absent from Tor's official release table checked on 2026-10-20. No alpha or ordinary browser was installed as a substitute. A bounded network test cannot establish browser fingerprinting resistance, sandbox strength or browser update safety.

## Threat boundary

The intended boundary routes ordinary Workstation network traffic through Gateway and reduces guest-to-host integration. Upstream Whonix/Kicksecure supplies the guest firewall, AppArmor, kernel policy, package verification and privilege separation. This project preserves those mechanisms rather than replacing them with an independent firewall.

The Mac, UTM/QEMU, the current host user and root are trusted. The host can read guest memory, disks and the internal transport. This setup does not protect against a compromised host, hypervisor escape, an unlocked Mac, malicious firmware or identity disclosure through accounts and behavior. Mode-0700 socket and bundle directories restrict other local accounts; they do not restrict software running as the owner.

Gateway NAT has no host port forwarding and disables external IPv6 service, but does not itself prohibit every Gateway-to-host/LAN connection. Internal IPv6 exists and uses upstream guest policy. Disabling external IPv6 service is not evidence that every IPv6 path has been audited.

Guest full-disk encryption, verified Secure Boot and personal login credentials were not provisioned. Upstream passwordless local login/autologin remains until the operator changes it using SYSMAINT. Host FileVault protects storage at rest; it does not protect guest data from a logged-in host account.

## Validation limits

The [network report](docs/network-validation.md) documents ordinary-user probes and external virtual-NIC captures under three finite conditions. It is not an adversarial audit, privileged Workstation compromise test, browser/WebRTC test, timing/traffic-correlation study, malicious Gateway test or proof against all leaks. No tests run indefinitely.

Warm reset hung in the tested UTM/firmware environment. `-no-reboot` makes a guest reboot exit QEMU cleanly; the operator must then start the VM. This avoids the observed hang but does not repair firmware. The Workstation socket reconnects only to its configured local Gateway endpoint; reconnecting is not proof that Tor has bootstrapped.

## Non-negotiable configuration

Keep source/repository signature verification enabled. Do not add a Workstation NAT/bridged interface, host shares, SSH server or a persistent diagnostic agent to obtain connectivity. Do not disable the Whonix firewall or remove user/sysmaint separation. A failed security check blocks image release.

Diagnostic controllers, serial channels and packet-capture devices used on disposable test copies must be removed before any image is distributed. Never publish raw packet captures, Tor state, guest journals, host paths, personal accounts, GitHub tokens, builder SSH keys or used test disks as release assets. The sanitized report intentionally omits exit and relay addresses.

## Reporting a problem

For a public repository, use **Security → Advisories → Report a vulnerability** if private reporting is enabled. Otherwise contact the repository owner through GitHub to arrange a private channel. Do not post credentials, identifying traffic captures or exploitable guest data in a public issue. Report upstream defects to the responsible project through its own security process.

Include the integration commit, host/UTM/kernel versions, a minimal reproduction and sanitized observations. Recheck relevant behavior after networking, UTM/QEMU, guest kernel, firewall or security-package changes; retain the previously validated configuration until the new result is understood.
