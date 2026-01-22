# diagnose.py
import sys
import traceback

tests = [
    ("symbols", "from anchor import symbols"),
    ("Symbol", "from anchor.symbols import Symbol, Role, Metrics"),
    ("RoleClusterer", "from anchor.contexts import RoleClusterer"),
    ("MetricsCalculator", "from anchor.metrics import MetricsCalculator"),
]

for name, code in tests:
    try:
        exec(code)
        print(f"✓ {name}")
    except Exception as e:
        print(f"✗ {name}: {e}")
        traceback.print_exc()
        break
