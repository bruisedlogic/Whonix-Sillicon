#!/usr/bin/env python3
"""Finite network probes; run as ordinary user in a disposable Workstation.

Packet capture at Gateway's external virtual NIC is required to interpret
results. A successful connect may be transparent Tor, and an unanswered UDP
probe alone does not prove filtering. No privileged controller is installed.
"""
import json, socket, ssl, struct, time

def probe(kind):
    start = time.monotonic()
    try:
        if kind == 'tor_https':
            ctx = ssl.create_default_context()
            with socket.create_connection(('check.torproject.org', 443), 25) as s:
                with ctx.wrap_socket(s, server_hostname='check.torproject.org') as tls:
                    tls.sendall(b'GET /api/ip HTTP/1.1\r\nHost: check.torproject.org\r\nConnection: close\r\n\r\n')
                    data = b''
                    while True:
                        block = tls.recv(8192)
                        if not block: break
                        data += block
                    return {'success': True, 'response': data.decode(errors='replace')[-1600:]}
        if kind in ('tcp4', 'tcp6'):
            address = '1.1.1.1' if kind == 'tcp4' else '2606:4700:4700::1111'
            with socket.create_connection((address, 443), 8):
                return {'success': True}
        if kind in ('dns4', 'dns6'):
            family = socket.AF_INET if kind == 'dns4' else socket.AF_INET6
            address = '1.1.1.1' if kind == 'dns4' else '2606:4700:4700::1111'
            request = struct.pack('!6H', 0x6243, 0x0100, 1, 0, 0, 0) + b'\x07example\x03com\0' + struct.pack('!2H', 1, 1)
            with socket.socket(family, socket.SOCK_DGRAM) as s:
                s.settimeout(6); s.sendto(request, (address, 53))
                data, source = s.recvfrom(4096)
                header = struct.unpack('!6H', data[:12])
                matches = data[:2] == request[:2]
                return {'success': matches and (header[1] & 15) == 0 and header[3] > 0,
                        'reply_bytes': len(data), 'rcode': header[1] & 15,
                        'answers': header[3], 'transaction_matches': matches}
        if kind in ('udp4', 'udp6'):
            family = socket.AF_INET if kind == 'udp4' else socket.AF_INET6
            address = '198.51.100.42' if kind == 'udp4' else '2001:db8::42'
            with socket.socket(family, socket.SOCK_DGRAM) as s:
                s.settimeout(3)
                s.sendto(b'WHONIX-UTM-BOUNDED-LEAK-CANARY-20261020', (address, 44444))
                try: data, source = s.recvfrom(4096)
                except socket.timeout: return {'sent': True, 'reply': False}
                return {'sent': True, 'reply': True, 'bytes': len(data)}
        if kind == 'system_dns':
            return {'success': True, 'answers': sorted({x[4][0] for x in socket.getaddrinfo('example.com', 443)})}
        raise ValueError('unknown probe')
    except Exception as exc:
        return {'success': False, 'error': type(exc).__name__ + ': ' + str(exc),
                'elapsed': round(time.monotonic() - start, 2)}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=('tor_https', 'tcp4', 'system_dns', 'dns4', 'udp4', 'tcp6', 'dns6', 'udp6'))
    args = parser.parse_args()
    result = probe(args.kind)
    # Avoid publishing the exit IP in the default machine-readable result.
    if 'response' in result:
        body = result.pop('response').split('\r\n\r\n', 1)[-1]
        try: result['is_tor'] = json.loads(body).get('IsTor')
        except ValueError: result['is_tor'] = None
    print(json.dumps({'probe': args.kind, 'result': result}))
