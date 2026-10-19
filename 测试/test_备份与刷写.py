import ast
import hashlib
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from 核心.扇区备份 import read_region, save_region
from 核心.记录协议 import verified_payload
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

    def test_raw_write_mode_rejects_an_unlisted_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'相机引导.bin';path.write_bytes(b'x'*27736)
            with self.assertRaisesRegex(ValueError,'blocked'):verified_payload(path,'原始读写')


class DispatchTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'), '本机没有C编译器，无法执行生成的命令分发器')
    def test_actual_generated_c_dispatch_allows_only_raw_flash_targets(self):
        spec=importlib.util.spec_from_file_location('raw_adapter',ROOT/'脚本/原始读写适配.py')
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        tree=ast.parse((ROOT/'脚本/构建相机引导.py').read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='replace_fn')
        namespace={'re':re}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'构建函数','exec'),namespace)
        base='''static void cmd_help(void)
{}
static void cmd_oem(const char *args)
{}
static void cmd_flash(const char *name)
{
    if (!mmc_ready)
        mmc_init();
}
static void fastboot_command(const char *cmd)
{}
'''
        generated=adapter.adapt(base,namespace['replace_fn'])
        dispatch=generated[generated.index('static void fastboot_command('):]
        header='''#include <stdio.h>
#include <string.h>
static int str_eq(const char*a,const char*b){return !strcmp(a,b);}
static const char*str_after(const char*a,const char*b){return !strncmp(a,b,strlen(b))?a+strlen(b):0;}
static void cmd_getvar(const char*a){puts("getvar");}
static void cmd_oem(const char*a){puts("oem");}
static void cmd_upload(void){puts("upload");}
static void cmd_download(const char*a){puts("download");}
static void cmd_flash(const char*a){puts(a);}
static void fb_fail(const char*a){puts("blocked");}
'''
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'dispatch.c';binary=Path(folder)/'dispatch'
            source.write_text(header+dispatch+'\nint main(int n,char**v){fastboot_command(v[1]);return 0;}\n')
            subprocess.run([shutil.which('cc'),str(source),'-o',str(binary)],check=True,capture_output=True)
            for command,expected in [('flash:nflasha','nflasha'),('flash:nflashaB0','nflashaB0'),
                                     ('flash:nflashaB1','nflashaB1'),('flash:nflasha15','blocked'),
                                     ('flash:nflashaB0 extra','blocked'),('erase:nflasha','blocked'),
                                     ('reboot','blocked'),('download:00000200','download')]:
                self.assertEqual(subprocess.check_output([str(binary),command],text=True).strip(),expected)


if __name__=='__main__':unittest.main()
