import hashlib
from pathlib import Path
import tempfile
import unittest

from 核心.扇区备份 import read_region, save_region
from test_引导 import FakeUSB

ROOT = Path(__file__).resolve().parents[1]


class BackupTests(unittest.TestCase):
    def test_raw_region_sequence_and_final_ack(self):
        data=bytes(range(256))*2
        device=FakeUSB([b'OKAY',b'OKAY',b'DATA00000200',data[:200],data[200:],b'OKAY'])
        self.assertEqual(read_region(device,'nflashaB0',0,1),data)
        self.assertEqual(device.sent,[b'oem partition',b'oem partition dump nflashaB0 0 1',b'upload'])

    def test_wrong_data_size_or_missing_final_ack_fails(self):
        for responses in ([b'OKAY',b'OKAY',b'DATA00000400'],
                          [b'OKAY',b'OKAY',b'DATA00000200',b'x'*512,b'FAILread failed']):
            with self.assertRaises((ValueError,RuntimeError)):
                read_region(FakeUSB(responses),'nflasha',0,1)

    def test_invalid_region_never_sends_and_output_never_overwrites(self):
        for target,offset,count in [('nflasha15',0,1),('nflasha',0,32769),('nflasha',0xffffffff,2)]:
            device=FakeUSB([])
            with self.assertRaises(ValueError):read_region(device,target,offset,count)
            self.assertEqual(device.sent,[])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'备份.raw'
            save_region(path,b'first')
            with self.assertRaises(FileExistsError):save_region(path,b'new')
            self.assertEqual(path.read_bytes(),b'first')

    def test_pico_source_is_complete_and_matches_historical_version(self):
        expected={'pico_boot.ino':'acc13bfc67e78534ffcb1ec5164a1e45b43ce572a51f71d89b9bb489cee2cfd7',
                  'serialboot.pio':'951422c52af2dd6f2431fc65cf0df9e9b2102f88b60924d6fb172ad2307c3d22',
                  'serialboot.pio.h':'20195e2bec487489df27dd9adb594ea1ce17f4f3d7dc2eac819d0fb7d9c25278'}
        for name,digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/'硬件/Pico注入/pico_boot'/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__':unittest.main()
