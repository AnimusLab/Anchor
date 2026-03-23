import hashlib
import os
import yaml
from pathlib import Path

def generate_lock():
    root = Path('anchor/governance')
    files = {}
    for f in root.rglob('*.anchor'):
        if f.is_file():
            # Use forward slashes for cross-platform consistency in lockfile
            rel_path = f.relative_to(root).as_posix()
            content = f.read_bytes().replace(b'\r\n', b'\n')
            files[rel_path] = hashlib.sha256(content).hexdigest()
    
    lock_data = {
        'version': '4.0.0',
        'generated': '2026-03-23T00:00:00Z',
        'algorithm': 'sha256',
        'offline_behaviour': 'warn',
        'files': {k: v for k, v in sorted(files.items())}
    }
    
    with open('GOVERNANCE.lock', 'w', encoding='utf-8') as f:
        yaml.dump(lock_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated GOVERNANCE.lock with {len(files)} files.")

if __name__ == "__main__":
    generate_lock()
