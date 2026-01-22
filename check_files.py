# check_files.py
import os

required_files = [
    'anchor/__init__.py',
    'anchor/symbols.py',
    'anchor/history.py',
    'anchor/contexts.py',
    'anchor/metrics.py',
    'anchor/verdicts.py',
    'anchor/report.py',
    'anchor/repo.py',
    'anchor/cli.py',
]

for file in required_files:
    exists = os.path.exists(file)
    size = os.path.getsize(file) if exists else 0
    status = "✓" if exists and size > 100 else "✗"
    print(f"{status} {file:<30} ({size} bytes)")
