"""Build fixed-profile Linux ELF payloads locally; never access a camera."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from a6700_unlock.catalog import load_catalog
from a6700_unlock.device_profile import load_device_profile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang",default=shutil.which("clang"))
    parser.add_argument("--linker",default=shutil.which("aarch64-elf-ld") or shutil.which("ld.lld"))
    args=parser.parse_args()
    if not args.clang or not args.linker:
        parser.error("Need clang plus aarch64-elf-ld or ld.lld")
    profile=load_device_profile(load_catalog())
    source=ROOT/"src/a6700_unlock/native/transaction.c"
    destination=ROOT/"src/a6700_unlock/data/native"
    destination.mkdir(exist_ok=True)
    rows=[]
    for row,mask in zip(profile.entries,profile.masks(writable_only=True)):
        rows.append("{%dUL,%d,{%s}}"%(row["device_offset"],row["device"],",".join(str(v) for v in mask)))
    header=("struct Entry { unsigned long offset; unsigned char device; unsigned char mask[64]; };\n"
            f"#define ENTRY_COUNT {len(rows)}u\n"
            "static const unsigned char PROFILE_DIGEST[32]={"+",".join(str(v) for v in bytes.fromhex(profile.digest))+"};\n"
            "static const struct Entry ENTRIES[ENTRY_COUNT]={"+",\n".join(rows)+"};\n")
    manifest=dict(profile_sha256=profile.digest,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  hardware_validation="pending",syscalls={"fsync":82,"pread64":67,"pwrite64":68},payloads={})
    with tempfile.TemporaryDirectory(prefix="a6700-native-build-") as temp:
        work=Path(temp)
        (work/"profile.h").write_text(header)
        for name,mode in (("reader",0),("writer",1)):
            obj=work/(name+".o");binary=work/(name+".elf")
            subprocess.run([args.clang,"-target","aarch64-unknown-elf","-fPIC","-O2","-ffreestanding",
                            "-fno-builtin","-fno-stack-protector","-I",str(work),f"-DBUILD_WRITER={mode}",
                            "-c",str(source),"-o",str(obj)],check=True)
            subprocess.run([args.linker,"-shared","-Bsymbolic","-z","noexecstack","-o",str(binary),str(obj)],check=True)
            data=binary.read_bytes()
            if data[:4]!=b"\x7fELF": raise RuntimeError("Not ELF")
            (destination/(name+".elf")).write_bytes(data)
            manifest["payloads"][name]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    (destination/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":main()
