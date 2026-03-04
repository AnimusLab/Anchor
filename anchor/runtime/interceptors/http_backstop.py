"""
anchor/runtime/interceptors/http_backstop.py

Layer 2: Universal HTTP-level interceptor.

Patches `requests.Session.request` and `httpx.Client.send` so that ANY
outgoing HTTP request to a known AI API domain is scanned — regardless of
which Python SDK made the call.

This is the safety net that catches:
  - Providers whose SDK we haven't explicitly wrapped in framework.py
  - Calls made via raw requests/httpx (e.g., direct REST clients)
  - New providers that launched after Anchor shipped

Architecture:
  - Prompt → identify_provider() → extract_prompt_from_payload()
             → PromptScanner → block / warn / audit
  - Response ← extract_response_text() → OutputScanner → log findings
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from anchor.runtime.interceptors.base import (
    AnchorViolationError, Finding, InterceptorMode,
    PromptScanResult, ResponseScanResult, SessionStats,
)
from anchor.runtime.interceptors.provider_registry import (
    identify_provider, extract_prompt_from_payload, extract_response_text,
)
from anchor.runtime.interceptors.output_scanner import scan_response

logger = logging.getLogger("anchor.runtime.http")

# Thread-local flag to prevent re-entrant interception
# (our own HTTP calls inside the interceptor must not trigger another scan)
_in_anchor_call = threading.local()

# Shared state — injected by runtime/__init__.py
_mode:  InterceptorMode = InterceptorMode.BLOCK
_stats: Optional[SessionStats]  = None

_requests_original_send = None
_httpx_original_send    = None

_patches_active = False


# ---------------------------------------------------------------------------
# Internal prompt scan (thin wrapper; full engine scan in framework.py)
# ---------------------------------------------------------------------------

def _scan_prompt_text(text: str, provider: str) -> PromptScanResult:
    """Quick regex-based scan of a prompt via the output_scanner patterns."""
    # Import here to avoid circular import at module level
    from anchor.runtime.interceptors.output_scanner import _COMPILED
    from anchor.runtime.interceptors.base import Finding

    findings = []
    for compiled, rule_id, severity, message in _COMPILED:
        m = compiled.search(text)
        if m:
            findings.append(Finding(
                rule_id  = rule_id,
                severity = severity,
                message  = message.replace("response", "prompt"),
                snippet  = m.group(0)[:120],
            ))

    is_flagged  = bool(findings)
    is_blocked  = is_flagged and _mode == InterceptorMode.BLOCK and any(
        f.severity in ("blocker", "error") for f in findings
    )

    return PromptScanResult(
        provider   = provider,
        is_blocked = is_blocked,
        is_flagged = is_flagged,
        findings   = findings,
        mode       = _mode,
    )


def _handle_prompt_result(result: PromptScanResult) -> None:
    """Apply mode semantics and update stats."""
    if _stats:
        _stats.record_prompt(result)

    if not result.is_flagged:
        return

    top = result.top_finding
    log_msg = (
        f"[Anchor] {result.provider} prompt flagged — "
        f"{top.rule_id}: {top.message}" if top else
        f"[Anchor] {result.provider} prompt flagged"
    )

    if result.is_blocked:
        logger.error(log_msg)
        raise AnchorViolationError(
            message  = top.message if top else "Policy violation",
            rule_id  = top.rule_id if top else "UNKNOWN",
            provider = result.provider,
            preview  = top.snippet if top else "",
        )
    elif _mode == InterceptorMode.WARN:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)


def _handle_response_result(result: ResponseScanResult) -> None:
    if _stats:
        _stats.record_response(result)
    if result.is_flagged:
        top = result.findings[0]
        logger.warning(
            f"[Anchor] {result.provider} response flagged — "
            f"{top.rule_id}: {top.message}"
        )


# ---------------------------------------------------------------------------
# requests patch
# ---------------------------------------------------------------------------

def _patched_requests_send(self, request, **kwargs):
    """Replacement for requests.Session.send."""
    if getattr(_in_anchor_call, "active", False):
        return _requests_original_send(self, request, **kwargs)

    url      = request.url or ""
    provider = identify_provider(url)

    if provider:
        _in_anchor_call.active = True
        try:
            # Scan outgoing prompt
            body = request.body if request.body else b""
            if isinstance(body, str):
                body = body.encode("utf-8")
            prompt_text = extract_prompt_from_payload(body)
            if prompt_text:
                result = _scan_prompt_text(prompt_text, provider)
                _handle_prompt_result(result)

            # Make the actual call
            response = _requests_original_send(self, request, **kwargs)

            # Scan response
            resp_body = response.content or b""
            resp_text = extract_response_text(resp_body, provider)
            if resp_text:
                resp_result = scan_response(resp_text, provider)
                _handle_response_result(resp_result)

            return response
        finally:
            _in_anchor_call.active = False
    else:
        return _requests_original_send(self, request, **kwargs)


# ---------------------------------------------------------------------------
# httpx patch
# ---------------------------------------------------------------------------

def _patched_httpx_send(self, request, **kwargs):
    """Replacement for httpx.Client.send."""
    if getattr(_in_anchor_call, "active", False):
        return _httpx_original_send(self, request, **kwargs)

    url      = str(request.url)
    provider = identify_provider(url)

    if provider:
        _in_anchor_call.active = True
        try:
            body = request.content or b""
            prompt_text = extract_prompt_from_payload(body)
            if prompt_text:
                result = _scan_prompt_text(prompt_text, provider)
                _handle_prompt_result(result)

            response = _httpx_original_send(self, request, **kwargs)

            resp_text = extract_response_text(response.content or b"", provider)
            if resp_text:
                resp_result = scan_response(resp_text, provider)
                _handle_response_result(resp_result)

            return response
        finally:
            _in_anchor_call.active = False
    else:
        return _httpx_original_send(self, request, **kwargs)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def activate_backstop(mode: InterceptorMode, stats: SessionStats) -> bool:
    """
    Install the HTTP-level patches.

    Returns True if at least one HTTP library was successfully patched.
    """
    global _requests_original_send, _httpx_original_send
    global _mode, _stats, _patches_active

    _mode  = mode
    _stats = stats

    if _patches_active:
        return True

    patched_any = False

    # Patch requests
    try:
        import requests
        _requests_original_send = requests.Session.send
        requests.Session.send   = _patched_requests_send
        logger.debug("[Anchor] HTTP backstop: requests.Session.send patched")
        patched_any = True
    except ImportError:
        logger.debug("[Anchor] HTTP backstop: requests not installed, skipping")

    # Patch httpx
    try:
        import httpx
        _httpx_original_send = httpx.Client.send
        httpx.Client.send    = _patched_httpx_send
        logger.debug("[Anchor] HTTP backstop: httpx.Client.send patched")
        patched_any = True
    except ImportError:
        logger.debug("[Anchor] HTTP backstop: httpx not installed, skipping")

    _patches_active = patched_any
    return patched_any


def deactivate_backstop() -> None:
    """Remove the HTTP-level patches and restore originals."""
    global _patches_active

    if not _patches_active:
        return

    try:
        import requests
        if _requests_original_send:
            requests.Session.send = _requests_original_send
    except ImportError:
        pass

    try:
        import httpx
        if _httpx_original_send:
            httpx.Client.send = _httpx_original_send
    except ImportError:
        pass

    _patches_active = False
