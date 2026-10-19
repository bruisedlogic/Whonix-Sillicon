# Bounded network validation — 2026-10-20

One finite matrix covered eight probes in each of three conditions, for **24 ordinary-user cases**. Separate targeted checks covered Gateway process recovery and the cold-reboot workaround. No stress loop or prolonged browsing was run. [Sanitized machine-readable results](test-results-2026-10-20.json) accompany this report.

## Environment and method

Apple M2 Pro, 16 GiB RAM, macOS 27.0.1, UTM 5.0.8 / bundled QEMU 10.0, updated Whonix 18.2.1.9 ARM64 guests and Debian kernel 6.12.113+deb13-arm64. The base guests had completed signed updates on 2026-10-19. Tests used disposable copies of those disks.

A temporary root diagnostic controller, reachable only through a local QEMU virtio-serial Unix socket in QEMUHelper's private directory, coordinated operations. It dropped all supplementary groups, GID and UID to the ordinary `user` account (UID 1000) in fresh processes for network probes. No SSH server, host directory share, guest NAT bypass or guest firewall exception was added. Capture devices observed Gateway's external/internal virtual NICs and Workstation's internal NIC. The controller and capture devices were removed by restoring the clean base disks and applying the final hardener after testing.

The matrix ran after a reboot investigation with Gateway using a GICv2/userspace-interrupt-controller trial. That trial did not fix warm reboot and was discarded. Networking, guest firewall and probe code were unchanged by that trial. The final standard-controller configuration received separate reboot-policy and cold-recovery checks; this is not an assertion that the complete matrix was repeated under every hardware variation.

HTTPS used Python's socket and TLS libraries with certificate verification and no explicit SOCKS proxy or curl wrapper. TCP probes targeted `1.1.1.1:443` and `[2606:4700:4700::1111]:443`. Explicit DNS probes sent a single A query for `example.com` to the corresponding public resolver on UDP port 53. UDP canaries used documentation-only addresses `198.51.100.42` / `2001:db8::42`, port 44444, with a distinctive payload. A send without a reply is not by itself evidence of filtering; packet captures were checked too.

## Results

| Probe | Tor running | Tor stopped | Gateway off |
|---|---|---|---|
| Certificate-verified Tor HTTPS API | `IsTor: true` | DNS failure | DNS failure |
| Direct-address IPv4 TCP | Connected through guest transparent-proxy path; no direct external probe destination | Connection refused | No route to host |
| System DNS | Resolved | Resolution failed | Resolution failed |
| Explicit public IPv4 DNS | Operation not permitted | Operation not permitted | Operation not permitted |
| IPv4 UDP canary | Operation not permitted | Operation not permitted | Operation not permitted |
| Direct-address IPv6 TCP | Socket connected; no external global IPv6/probe destination | Connection refused | No route to host |
| Explicit public IPv6 DNS | Reply, matching transaction; capture confirmed NOERROR and one answer | Timed out | Timed out |
| IPv6 UDP canary | Send accepted, no reply; internal capture observed canary, external capture did not | Send accepted, no reply; no external canary | Send accepted, no reply; Gateway process absent |

Before Tor-stopped probes, `systemctl stop tor.service tor@default.service` returned success and `pgrep -x tor` found no process. Before Gateway-off probes, `utmctl status` confirmed Gateway was stopped. No QEMU TCP/UDP host sockets were listed by `lsof` while Tor was stopped.

## Capture observations

The completed Gateway external capture contained **1,283 Ethernet frames**: 1,274 IPv4 TCP frames, seven IPv6 ICMP control frames, and two other Ethernet frames. It contained **zero UDP frames, zero port-53 destination frames, zero probe-destination frames and zero canary payloads**. The IPv6 frames were control traffic, not global IPv6 probe traffic. The IPv4 connections were to other destinations used during Tor operation; this observation alone does not authenticate every remote endpoint as a Tor relay.

The Workstation internal capture contained 788 frames, including 18 frames addressed to probe destinations, 39 UDP frames and four frames containing the canary marker (including returned control/error traffic). These observations distinguish attempted internal traffic from an entirely idle network. The captured normal IPv6 DNS reply was checked separately: transaction matched, RCODE 0, one answer. IPv6 TCP success establishes a socket-level test, not a complete IPv6 TLS browsing test.

The simple published PCAP summarizer rejects invalid/truncated captures and suppresses traffic addresses. It counts IP protocols directly; IPv6 extension-header and fragmented-transport analysis require separate review. Raw captures, Tor exit addresses, relay addresses and guest journals remain private and are not release assets.

## Reboot and recovery

The original warm reboot hung after firmware started Debian's shim. A GICv2/userspace-interrupt-controller trial reached the desktop but hung again on warm reboot. No firmware repair is claimed.

The final hardener uses `-no-reboot`. One guest reboot request per role resulted in a stopped VM without forced termination. Both were started again, using the standard controller configuration, and Workstation's certificate-verified HTTPS check returned `IsTor: true`. This verifies a **manual cold-start workaround**, not automatic reboot or endurance reliability.

With `reconnect-ms=2000`, the existing Workstation recovered its private link after Gateway's QEMU process was stopped and started; HTTPS later succeeded without restarting Workstation. An initial request during Gateway startup failed before recovery, as expected. Operators must still wait for Tor to become usable.

## Reproducing a bounded check

Use disposable, private test copies. Record the exact candidate configuration and revisions. Add QEMU `filter-dump` capture objects only to those copies, with files in their private Data directories. Observe both the external Gateway link and internal Workstation link. Capture complete packets and stop the VMs before parsing the final captures.

Copy [the probe](../tests/runtime/probe.py) into the test Workstation using a reviewed lab-only transfer method. Run it as the ordinary user, once per named probe and condition:

```sh
python3 probe.py tor_https
python3 probe.py tcp4
python3 probe.py system_dns
python3 probe.py dns4
python3 probe.py udp4
python3 probe.py tcp6
python3 probe.py dns6
python3 probe.py udp6
```

Use a Gateway administrator session to stop Tor for the second condition and confirm the processes are gone; do not disable the firewall. Shut Gateway down and confirm its host process is stopped for the third. Keep the Workstation configuration unchanged. Analyze the private captures locally:

```sh
python3 tests/runtime/pcap_summary.py gateway-external.pcap workstation-internal.pcap
```

Remove all lab services, transfer media, channels and capture devices before distribution. Prefer fresh build outputs for a release candidate rather than attempting to clean used lab images.

## Limits

These results found no direct egress in this matrix. They do not prove absence of all leaks. Privileged/root Workstation compromise, ICMP/raw-socket attacks, IPv6 extension/fragment attacks, malicious gateways, host/LAN exploitation, browser/WebRTC behavior, sandbox escapes, timing correlation, sustained failures and independent audit remain untested. Stable ARM64 Tor Browser remains unavailable, so there is no completed browser test or production browsing release.
