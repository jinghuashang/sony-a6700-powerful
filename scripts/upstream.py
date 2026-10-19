"""Check exact upstream inputs without vendoring their source or binaries."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def checked_upstream(path):
    path = path.resolve()
    pin = json.loads((ROOT / 'upstream.lock.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != pin['commit']:
        raise ValueError('Upstream HEAD differs from the pinned commit')
    for name, expected in pin['files'].items():
        source = path / name
        if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError('Upstream file changed: ' + name)
    return path
