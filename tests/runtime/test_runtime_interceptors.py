"""Smoke test for anchor.runtime module."""
import sys
sys.path.insert(0, 'D:/Anchor')

# 1: base types
from anchor.runtime.interceptors.base import (
    AnchorViolationError, PromptScanResult, ResponseScanResult,
    InterceptorMode, SessionStats, Finding
)
print("1. base.py imports: OK")

# 2: provider registry
from anchor.runtime.interceptors.provider_registry import (
    identify_provider, extract_prompt_from_payload
)
assert identify_provider("https://api.openai.com/v1/chat/completions") == "openai"
assert identify_provider("https://api.anthropic.com/v1/messages") == "anthropic"
assert identify_provider("https://api.groq.com/openai/v1/chat/completions") == "groq"
assert identify_provider("https://google.com") is None
print("2. provider_registry.py domain lookups: OK")

# 3: output scanner
from anchor.runtime.interceptors.output_scanner import scan_response
dangerous = scan_response("rm -rf /", "test")
assert dangerous.is_flagged, "rm -rf / should be flagged"
safe = scan_response('print("hello world")', "test")
assert not safe.is_flagged, "harmless code should not be flagged"
print("3. output_scanner.py: OK")

# 4: http backstop imports + activate/deactivate
from anchor.runtime.interceptors.http_backstop import activate_backstop, deactivate_backstop
stats = SessionStats()
ok = activate_backstop(InterceptorMode.WARN, stats)
deactivate_backstop()
print(f"4. http_backstop.py: OK (patched={'yes' if ok else 'no — requests/httpx not installed'})")

# 5: framework imports
from anchor.runtime.interceptors.framework import activate_framework_patches, get_active_patches
print("5. framework.py imports: OK")

# 6: full runtime (auto-activated on import)
import anchor.runtime as rt
s = rt.get_session_stats()
print(f"6. runtime/__init__.py: OK (status={s['status']}, mode={s.get('mode', '?')})")

print("\nALL SMOKE TESTS PASSED")
