import importlib.util
from pathlib import Path
import socket
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'pcap_summary', Path(__file__).parent / 'runtime/pcap_summary.py')
pcap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcap)


def capture(frame):
    header = struct.pack('<IHHIIII', 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    record = struct.pack('<IIII', 0, 0, len(frame), len(frame))
    return header + record + frame


class CaptureBoundaryTests(unittest.TestCase):
    def analyze_bytes(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.pcap'
            path.write_bytes(data)
            return pcap.analyze(path)

    def test_detects_canary_and_direct_dns_without_disclosing_addresses(self):
        udp = struct.pack('!HHHH', 40000, 53, 8 + len(pcap.MARKER), 0) + pcap.MARKER
        ip = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 20 + len(udp), 0, 0, 64, 17, 0,
                         socket.inet_aton('10.0.2.15'), socket.inet_aton('1.1.1.1'))
        result = self.analyze_bytes(capture(b'\0' * 12 + b'\x08\x00' + ip + udp))
        self.assertEqual(result['marker_packets'], 1)
        self.assertEqual(result['counts']['udp_frames'], 1)
        self.assertEqual(result['counts']['destination_port_53_frames'], 1)
        self.assertEqual(result['counts']['probe_destination_frames'], 1)
        self.assertNotIn('1.1.1.1', str(result))

    def test_rejects_truncation_instead_of_reporting_clean(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            self.analyze_bytes(capture(b'\0' * 14)[:-1])

    def test_rejects_unknown_capture(self):
        with self.assertRaises(ValueError):
            self.analyze_bytes(b'wrong format' * 3)
