import io
from pathlib import Path
import struct
import tempfile
import unittest

from 核心.注入入口 import transmit
from 核心.设备查询 import inspect, query
from 核心.Pico通信 import Pico
from 核心.记录协议 import LOAD, UNLOCK, boot_records, decode, encode, verified_payload


class BootTests(unittest.TestCase):
    def test_record_layout_and_crc_reject_corruption(self):
        record = encode(1, LOAD, b'abc')
        self.assertEqual(struct.unpack('<IHI', record[:10]), (13, 1, LOAD))
        self.assertEqual(decode(record), [(1, LOAD, b'abc')])
        broken = bytearray(record)
        broken[10] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC'):
            decode(broken)
        for data in (record[:-1], b'\x00' * 14):
            with self.assertRaises(ValueError):
                decode(data)

    def test_record_order_fixed_window_and_chunking(self):
        payload = bytes(range(256)) * 82
        records = decode(b''.join(boot_records(payload)))
        self.assertEqual(len(records), 45)
        self.assertEqual(records[0], (0x123, 0, b''))
        self.assertEqual(b''.join(row[2] for row in records[1:-3]), payload)
        self.assertEqual(records[1][1], LOAD)
        self.assertEqual(records[-3:], [(0xffff, LOAD, b''), (0, UNLOCK, b''), (0x123, 0, b'')])
        for payload in (b'', b'x' * 65537):
            with self.assertRaises(ValueError):
                boot_records(payload)

    def test_unknown_payload_is_rejected_without_device_access(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'candidate.bin'
            path.write_bytes(b'x' * 20992)
            with self.assertRaisesRegex(ValueError, 'blocked'):
                verified_payload(path)


class FakePico:
    def __init__(self, senses, fail_record=False):
        self.senses = iter(senses)
        self.events = []
        self.fail_record = fail_record

    def ping(self): self.events.append('ping')
    def carrier(self, value): self.events.append(('carrier', value))
    def disable_pull(self): self.events.append('pull-off')
    def sense(self): return next(self.senses)
    def send_record(self, record):
        self.events.append(('record', record))
        if self.fail_record: raise IOError('lost ACK')


class TransportTests(unittest.TestCase):
    def run_transport(self, device, clock=lambda: 0):
        transmit(device, [b'first', b'last'], 1, clock=clock,
                 sleep=lambda seconds: None, say=lambda *args, **kwargs: None)

    def test_baseline_high_blocks_all_records_and_releases(self):
        device = FakePico([True])
        with self.assertRaisesRegex(RuntimeError, 'Baseline'):
            self.run_transport(device)
        self.assertFalse(any(isinstance(event, tuple) and event[0] == 'record' for event in device.events))
        self.assertEqual(device.events[-2:], [('carrier', False), 'pull-off'])

    def test_activation_timeout_releases_without_sending(self):
        device = FakePico([False, False])
        clock = iter([0, 2])
        with self.assertRaises(TimeoutError):
            self.run_transport(device, lambda: next(clock))
        self.assertNotIn(('record', b'first'), device.events)
        self.assertEqual(device.events[-2:], [('carrier', False), 'pull-off'])

    def test_ordered_stream_once_and_no_retry_on_lost_ack(self):
        device = FakePico([False, True])
        self.run_transport(device)
        self.assertEqual([event for event in device.events if isinstance(event, tuple) and event[0] == 'record'],
                         [('record', b'first'), ('record', b'last')])
        device = FakePico([False, True], fail_record=True)
        with self.assertRaises(IOError):
            self.run_transport(device)
        self.assertEqual(device.events.count(('record', b'first')), 1)
        self.assertNotIn(('record', b'last'), device.events)
        self.assertEqual(device.events[-2:], [('carrier', False), 'pull-off'])

    def test_packet_fragmentation_version_and_invalid_response(self):
        class Port:
            def __init__(self, reply): self.reply = io.BytesIO(reply); self.sent = []
            def read(self, count): return self.reply.read(min(count, 2))
            def write(self, value): self.sent.append(value); return len(value)
        version = b'a6700_pio_od 2'
        port = Port(b'\x81' + struct.pack('<H', len(version)) + version)
        Pico(port).ping()
        self.assertEqual(port.sent, [b'\x01\x00\x00'])
        for response in (b'', b'\x81\x01\x00x', b'\x82\x01\x00x', b'\x83\x00\x00'):
            with self.assertRaises((TimeoutError, ValueError, RuntimeError)):
                Pico(Port(response)).ping()


class FakeUSB:
    def __init__(self, responses): self.responses = iter(responses); self.sent = []
    def write(self, endpoint, data, timeout): self.sent.append(data); return len(data)
    def read(self, endpoint, size, timeout): return next(self.responses)


class USBTests(unittest.TestCase):
    def test_identity_mismatch_never_queries_partition(self):
        device = FakeUSB([b'OKAYother'])
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            inspect(device, table=True)
        self.assertEqual(device.sent, [b'getvar:product'])

    def test_identity_then_version_then_table(self):
        device = FakeUSB([b'OKAYA6700-AP-read-candidate', b'OKAY0.5', b'INFOtable', b'OKAY'])
        result = inspect(device, table=True)
        self.assertEqual(result['partitions']['info'], ['table'])
        self.assertEqual(device.sent, [b'getvar:product', b'getvar:version', b'oem partition'])

    def test_non_query_commands_and_unexpected_data_are_blocked(self):
        device = FakeUSB([b'DATA00000010'])
        with self.assertRaises(ValueError): query(device, 'flash:nflasha')
        self.assertEqual(device.sent, [])
        with self.assertRaises(ValueError): query(device, 'getvar:product')


if __name__ == '__main__':
    unittest.main()
