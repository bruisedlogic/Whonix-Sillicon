# Publication and image release

## Source publication

The repository can describe an experimental integration without claiming a supported port. Before making it public, review the complete tracked tree and history for secrets, personal data, local paths, logs, archives and VM disks. Keep provenance, the MIT scope for original wrapper code, upstream attribution and material limitations visible. Do not describe finite test success as a security audit or a breakthrough in platform support.

Do not attach the installed or instrumented development disks as release assets. Source publication is separate from distributing a usable, supported image.

## Image release blockers

- Official stable Linux ARM64 Tor Browser and a working authenticated update path are required. The current official platform table offers ARM64 only in alpha.
- Warm reset remains broken. The cold-start workaround requires an extra Start action and must be disclosed wherever reboot instructions appear.
- Independent review and broader adversarial testing have not occurred. The finite network matrix covers ordinary-user probes, not a compromised root Workstation or browser behavior.
- A clean image must be built from verified source, updated, sanitized and validated independently of used local disks. Remove diagnostics, test services, host-specific socket paths, personal state and credentials. Review upstream's own image generalization requirements; deleting a few logs is not sufficient.
- Publish exact source/package revisions, build instructions, transferred image hashes, licensing/redistribution notices, the tested host profile and reproducible validation evidence for any actual image release.

## Verification gates

1. Verify official signing identity, tag, commit and required submodules.
2. Build both images without host mounts; preserve original artifacts and hashes.
3. Prepare QCOW2/software-rendered runtime copies and local private sockets.
4. Verify imported configuration and actual QEMU arguments, isolation and permissions.
5. Complete signed guest updates without bypassing verification.
6. Test Tor HTTPS, TCP, DNS and UDP over IPv4/IPv6 with Tor running/stopped and Gateway off; inspect both internal and external captures.
7. Verify cold-reboot handling, recovery and update persistence in the exact candidate image.
8. Verify stable Tor Browser launch, Tor connectivity, browser leak behavior, sandboxing and authenticated updates.
9. Independently review, sanitize, hash and document the exact distribution candidate.

Passing a checklist does not confer upstream support or an anonymity guarantee. Any failed or unperformed gate stays visible in the release notes.
