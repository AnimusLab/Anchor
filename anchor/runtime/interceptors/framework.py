"""
anchor/runtime/interceptors/framework.py

Layer 1: SDK-specific framework wrappers.

Uses `wrapt` for transparent, signature-preserving patches on the most
commonly used AI provider Python SDKs.

Each wrapper:
  1. Extracts the prompt from the kwargs
  2. Runs it through PromptScanner
  3. Either blocks (raises AnchorViolationError) or passes through
  4. Wraps the response for output scanning

Supported SDKs:
  openai, anthropic, google-generativeai, langchain (openai/anthropic/google),
  ollama, groq, cohere, mistralai, transformers (HuggingFace pipeline)

Graceful degradation: if a SDK is not installed, its patch is silently skipped.
"""

from __future__ import annotations

import logging
from typing import Optional

from anchor.runtime.interceptors.base import (
    AnchorViolationError, Finding, InterceptorMode,
    PromptScanResult, ResponseScanResult, SessionStats,
)
from anchor.runtime.interceptors.output_scanner import scan_response

logger = logging.getLogger("anchor.runtime.framework")

# Injected by runtime/__init__.py
_mode:  InterceptorMode = InterceptorMode.BLOCK
_stats: Optional[SessionStats]  = None
_active_patches: list[str]      = []   # list of provider names successfully patched


# ---------------------------------------------------------------------------
# Shared scan logic
# ---------------------------------------------------------------------------

def _scan_messages(messages: list, provider: str) -> PromptScanResult:
    """Build a combined text from a messages list and scan it."""
    parts = []
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "")
            role    = msg.get("role", "?")
        elif hasattr(msg, "content"):
            content = msg.content
            role    = getattr(msg, "role", "?")
        else:
            content = str(msg)
            role    = "?"
        if isinstance(content, str):
            parts.append(f"[{role}] {content}")
    return _scan_text("\n".join(parts), provider)


def _scan_text(text: str, provider: str) -> PromptScanResult:
    """Scan arbitrary text and return PromptScanResult."""
    from anchor.runtime.interceptors.output_scanner import _COMPILED

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

    is_flagged = bool(findings)
    is_blocked = (
        is_flagged
        and _mode == InterceptorMode.BLOCK
        and any(f.severity in ("blocker", "error") for f in findings)
    )

    return PromptScanResult(
        provider   = provider,
        is_blocked = is_blocked,
        is_flagged = is_flagged,
        findings   = findings,
        mode       = _mode,
    )


def _handle(result: PromptScanResult) -> None:
    """Apply mode semantics and update stats."""
    if _stats:
        _stats.record_prompt(result)

    if not result.is_flagged:
        return

    top = result.top_finding
    msg = (
        f"[Anchor] {result.provider}: {top.rule_id} — {top.message}"
        if top else f"[Anchor] {result.provider}: policy violation"
    )

    if result.is_blocked:
        logger.error(msg)
        raise AnchorViolationError(
            message  = top.message if top else "Policy violation",
            rule_id  = top.rule_id if top else "UNKNOWN",
            provider = result.provider,
            preview  = top.snippet if top else "",
        )
    elif _mode == InterceptorMode.WARN:
        logger.warning(msg)
    else:
        logger.info(msg)


def _handle_response(text: str, provider: str) -> None:
    result = scan_response(text, provider)
    if _stats:
        _stats.record_response(result)
    if result.is_flagged:
        top = result.findings[0]
        logger.warning(f"[Anchor] {provider} response: {top.rule_id} — {top.message}")


# ---------------------------------------------------------------------------
# SDK patches
# ---------------------------------------------------------------------------

def _patch_openai() -> bool:
    try:
        import wrapt
        import openai

        @wrapt.patch_function_wrapper(
            "openai.resources.chat.completions", "Completions.create"
        )
        def _openai_create(wrapped, instance, args, kwargs):
            messages = kwargs.get("messages", [])
            _handle(_scan_messages(messages, "openai"))
            response = wrapped(*args, **kwargs)
            # Extract text from ChatCompletion response
            try:
                text = response.choices[0].message.content or ""
                if text:
                    _handle_response(text, "openai")
            except Exception:
                pass
            return response

        logger.info("[Anchor] Patched: openai.chat.completions.create")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch openai: {e}")
        return False


def _patch_anthropic() -> bool:
    try:
        import wrapt
        import anthropic  # noqa: F401

        @wrapt.patch_function_wrapper(
            "anthropic.resources.messages", "Messages.create"
        )
        def _anthropic_create(wrapped, instance, args, kwargs):
            messages = kwargs.get("messages", [])
            system   = kwargs.get("system", "")
            text     = f"[system] {system}\n" if system else ""
            text    += "\n".join(
                f"[{m.get('role','?')}] {m.get('content','')}"
                for m in messages
            )
            _handle(_scan_text(text, "anthropic"))
            response = wrapped(*args, **kwargs)
            try:
                out = response.content[0].text if response.content else ""
                if out:
                    _handle_response(out, "anthropic")
            except Exception:
                pass
            return response

        logger.info("[Anchor] Patched: anthropic.messages.create")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch anthropic: {e}")
        return False


def _patch_google_genai() -> bool:
    try:
        import wrapt
        import google.generativeai  # noqa: F401

        @wrapt.patch_function_wrapper(
            "google.generativeai.generative_models", "GenerativeModel.generate_content"
        )
        def _genai_generate(wrapped, instance, args, kwargs):
            contents = args[0] if args else kwargs.get("contents", "")
            text     = contents if isinstance(contents, str) else str(contents)
            _handle(_scan_text(text, "google-gemini"))
            response = wrapped(*args, **kwargs)
            try:
                out = response.text or ""
                if out:
                    _handle_response(out, "google-gemini")
            except Exception:
                pass
            return response

        logger.info("[Anchor] Patched: google.generativeai.GenerativeModel.generate_content")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch google-generativeai: {e}")
        return False


def _patch_langchain() -> bool:
    """
    Patch LangChain's BaseChatModel.invoke — covers langchain_openai,
    langchain_anthropic, langchain_google_genai, etc. in one shot.
    """
    try:
        import wrapt
        import langchain.schema.language_model  # noqa: F401

        @wrapt.patch_function_wrapper(
            "langchain.schema.language_model", "BaseLanguageModel.invoke"
        )
        def _lc_invoke(wrapped, instance, args, kwargs):
            prompt = args[0] if args else kwargs.get("input", "")
            text   = prompt if isinstance(prompt, str) else str(prompt)
            _handle(_scan_text(text, "langchain"))
            response = wrapped(*args, **kwargs)
            try:
                out = response.content if hasattr(response, "content") else str(response)
                if out:
                    _handle_response(out, "langchain")
            except Exception:
                pass
            return response

        logger.info("[Anchor] Patched: langchain BaseLanguageModel.invoke")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch langchain: {e}")
        return False


def _patch_ollama() -> bool:
    try:
        import wrapt
        import ollama  # noqa: F401

        @wrapt.patch_function_wrapper("ollama", "chat")
        def _ollama_chat(wrapped, instance, args, kwargs):
            messages = kwargs.get("messages", [])
            _handle(_scan_messages(messages, "ollama"))
            response = wrapped(*args, **kwargs)
            try:
                out = response.get("message", {}).get("content", "")
                if out:
                    _handle_response(out, "ollama")
            except Exception:
                pass
            return response

        logger.info("[Anchor] Patched: ollama.chat")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch ollama: {e}")
        return False


def _patch_groq() -> bool:
    try:
        import wrapt
        import groq  # noqa: F401

        @wrapt.patch_function_wrapper(
            "groq.resources.chat.completions", "Completions.create"
        )
        def _groq_create(wrapped, instance, args, kwargs):
            messages = kwargs.get("messages", [])
            _handle(_scan_messages(messages, "groq"))
            response = wrapped(*args, **kwargs)
            try:
                out = response.choices[0].message.content or ""
                if out:
                    _handle_response(out, "groq")
            except Exception:
                pass
            return response

        logger.info("[Anchor] Patched: groq.chat.completions.create")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch groq: {e}")
        return False


def _patch_cohere() -> bool:
    try:
        import wrapt
        import cohere  # noqa: F401

        @wrapt.patch_function_wrapper("cohere.client", "Client.chat")
        def _cohere_chat(wrapped, instance, args, kwargs):
            message = kwargs.get("message", args[0] if args else "")
            if isinstance(message, str):
                _handle(_scan_text(message, "cohere"))
            response = wrapped(*args, **kwargs)
            try:
                out = response.text or ""
                if out:
                    _handle_response(out, "cohere")
            except Exception:
                pass
            return response

        logger.info("[Anchor] Patched: cohere.Client.chat")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch cohere: {e}")
        return False


def _patch_mistral() -> bool:
    try:
        import wrapt
        import mistralai  # noqa: F401

        @wrapt.patch_function_wrapper(
            "mistralai.client", "MistralClient.chat"
        )
        def _mistral_chat(wrapped, instance, args, kwargs):
            messages = kwargs.get("messages", [])
            _handle(_scan_messages(messages, "mistral"))
            return wrapped(*args, **kwargs)

        logger.info("[Anchor] Patched: mistralai.MistralClient.chat")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch mistralai: {e}")
        return False


def _patch_transformers() -> bool:
    """
    Patch HuggingFace transformers Pipeline.__call__ to scan the
    'text_inputs' / first positional argument.
    """
    try:
        import wrapt
        import transformers  # noqa: F401

        @wrapt.patch_function_wrapper("transformers.pipelines.base", "Pipeline.__call__")
        def _pipeline_call(wrapped, instance, args, kwargs):
            inputs = args[0] if args else kwargs.get("inputs", "")
            text   = inputs if isinstance(inputs, str) else " ".join(
                str(i) for i in inputs
            ) if isinstance(inputs, list) else str(inputs)
            _handle(_scan_text(text, "huggingface-transformers"))
            return wrapped(*args, **kwargs)

        logger.info("[Anchor] Patched: transformers.Pipeline.__call__")
        return True
    except ImportError:
        return False
    except Exception as e:
        logger.debug(f"[Anchor] Could not patch transformers: {e}")
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SDK_PATCHERS = [
    ("openai",       _patch_openai),
    ("anthropic",    _patch_anthropic),
    ("google-genai", _patch_google_genai),
    ("langchain",    _patch_langchain),
    ("ollama",       _patch_ollama),
    ("groq",         _patch_groq),
    ("cohere",       _patch_cohere),
    ("mistral",      _patch_mistral),
    ("transformers", _patch_transformers),
]


def activate_framework_patches(mode: InterceptorMode,
                                stats: SessionStats) -> list[str]:
    """
    Install SDK-specific patches for all installed AI libraries.

    Returns a list of provider names that were successfully patched.
    This function requires `wrapt` to be installed.
    """
    global _mode, _stats, _active_patches

    _mode  = mode
    _stats = stats

    try:
        import wrapt  # noqa: F401  — must be present, verified here
    except ImportError:
        logger.warning(
            "[Anchor] `wrapt` not installed. SDK-specific patches skipped. "
            "Install it with: pip install wrapt"
        )
        return []

    patched = []
    for name, patcher in _SDK_PATCHERS:
        if patcher():
            patched.append(name)

    _active_patches = patched
    return patched


def get_active_patches() -> list[str]:
    return list(_active_patches)
