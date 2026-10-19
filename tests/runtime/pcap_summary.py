#!/usr/bin/env python3
"""Summarize private Ethernet PCAPs without printing traffic addresses.

Counts are observations, not an automatic security verdict. IPv6 extension
headers and fragmented transport payloads require separate manual analysis.
"""
import argparse
from collections import Counter
import ipaddress
import json
from pathlib import Path
import struct

MARKER = b'WHONIX-UTM-BOUNDED-LEAK-CANARY-20261020'
PROBE_ADDRESSES = {'1.1.1.1', '2606:4700:4700::1111',
                   '198.51.100.42', '2001:db8::42'}
MAGIC = {b'\xd4\xc3\xb2\xa1': '<', b'\xa1\xb2\xc3\xd4': '>',
         b'\x4d\x3c\xb2\xa1': '<', b'\xa1\xb2\x3c\x4d': '>'}


def analyze(path):
    counts = Counter()
    packets = marker_packets = 0
    with Path(path).open('rb') as capture:
        header = capture.read(24)
        if len(header) != 24 or header[:4] not in MAGIC:
            raise ValueError('Not a supported PCAP file')
        endian = MAGIC[header[:4]]
        major, minor = struct.unpack(endian + 'HH', header[4:8])
        snaplen, link = struct.unpack(endian + 'II', header[16:24])
        if (major, minor) != (2, 4) or link != 1 or not 0 < snaplen <= 16 * 1024 * 1024:
            raise ValueError('Expected PCAP 2.4 with Ethernet link type')
        while True:
            record = capture.read(16)
            if not record:
                break
            if len(record) != 16:
                raise ValueError('Truncated packet header; stop capture before analysis')
            _, _, size, original_size = struct.unpack(endian + '4I', record)
            if size > snaplen or size != original_size:
                raise ValueError('Truncated or invalid packet capture')
            frame = capture.read(size)
            if len(frame) != size:
                raise ValueError('Truncated packet data')
            packets += 1
            marker_packets += MARKER in frame
            if len(frame) < 14:
                raise ValueError('Short Ethernet frame')
            ethertype = struct.unpack('!H', frame[12:14])[0]
            packet = frame[14:]
            if ethertype == 0x0800 and len(packet) >= 20:
                version, protocol = 4, packet[9]
                addresses = [ipaddress.ip_address(packet[12:16]),
                             ipaddress.ip_address(packet[16:20])]
                offset = (packet[0] & 15) * 4
                if offset < 20 or len(packet) < offset:
                    raise ValueError('Malformed IPv4 header')
                fragment = struct.unpack('!H', packet[6:8])[0] & 0x1FFF
                transport = packet[offset:] if not fragment else b''
                if fragment:
                    counts['ipv4_noninitial_fragment'] += 1
            elif ethertype == 0x86DD and len(packet) >= 40:
                version, protocol = 6, packet[6]
                addresses = [ipaddress.ip_address(packet[8:24]),
                             ipaddress.ip_address(packet[24:40])]
                transport = packet[40:]
                if any(a.is_global and not a.is_multicast for a in addresses):
                    counts['global_ipv6_frames'] += 1
            else:
                counts['other_ethernet_frames'] += 1
                continue
            counts[f'ipv{version}_frames'] += 1
            if str(addresses[1]) in PROBE_ADDRESSES:
                counts['probe_destination_frames'] += 1
            if protocol in (6, 17) and len(transport) >= 4:
                _, destination_port = struct.unpack('!HH', transport[:4])
                counts['tcp_frames' if protocol == 6 else 'udp_frames'] += 1
                if destination_port == 53:
                    counts['destination_port_53_frames'] += 1
            else:
                counts[f'ip_protocol_{protocol}_frames'] += 1
    return {'file': Path(path).name, 'packets': packets,
            'marker_packets': marker_packets, 'counts': dict(counts)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', nargs='+')
    args = parser.parse_args()
    for filename in args.capture:
        print(json.dumps(analyze(filename)))
