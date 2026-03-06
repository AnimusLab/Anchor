"""
anchor/runtime/interceptors/provider_registry.py

Registry of known AI API domains and prompt extraction helpers.

The HTTP backstop uses this to determine whether an outgoing HTTP request
is going to an AI provider — without needing to know which SDK generated it.

Adding a new provider requires only a single line here.
"""

from __future__ import annotations
import json
from typing import Optional, List
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Known AI API domains
# Each entry: (domain_fragment, provider_name)
# Matched as: domain_fragment in request_host
# ---------------------------------------------------------------------------
AI_API_DOMAINS: list[tuple[str, str]] = [
    # ── Frontier labs ──────────────────────────────────────────────────
    ("api.openai.com",               "openai"),
    ("oaidalleapiprodscus",          "openai-dalle"),
    ("api.anthropic.com",            "anthropic"),
    ("generativelanguage.googleapis.com", "google-gemini"),
    ("aiplatform.googleapis.com",    "google-vertex-ai"),
    ("api.mistral.ai",               "mistral"),
    ("api.cohere.com",               "cohere"),
    ("api.cohere.ai",                "cohere"),

    # ── Inference providers ────────────────────────────────────────────
    ("api.groq.com",                 "groq"),
    ("api.together.xyz",             "together-ai"),
    ("api.together.ai",              "together-ai"),
    ("api.perplexity.ai",            "perplexity"),
    ("api.fireworks.ai",             "fireworks"),
    ("api.deepinfra.com",            "deep-infra"),
    ("api.replicate.com",            "replicate"),
    ("api.novita.ai",                "novita"),
    ("api.deepseek.com",             "deepseek"),
    ("api.cerebras.ai",              "cerebras"),

    # ── HuggingFace ───────────────────────────────────────────────────
    ("huggingface.co/api",           "huggingface"),
    ("api-inference.huggingface.co", "huggingface-inference"),

    # ── Cloud AI (Azure / AWS / GCP) ──────────────────────────────────
    ("openai.azure.com",             "azure-openai"),
    ("cognitiveservices.azure.com",  "azure-cognitive"),
    ("bedrock-runtime",              "aws-bedrock"),
    ("sagemaker.amazonaws.com",      "aws-sagemaker"),

    # ── Coding-specific in-process SDKs ───────────────────────────────
    ("api.codeium.com",              "codeium"),
    ("api.tabnine.com",              "tabnine"),

    # ── Local / self-hosted (catch Ollama's default listen address) ───
    ("localhost:11434",              "ollama-local"),
    ("127.0.0.1:11434",              "ollama-local"),
    ("localhost:1234",               "lm-studio"),
]

# ---------------------------------------------------------------------------
# Runtime-registered custom providers (populated via register_provider())
# ---------------------------------------------------------------------------
_CUSTOM_PROVIDERS: list[tuple[str, str]] = []


def register_provider(domain: str, name: str) -> None:
    """
    Register a custom or unknown AI provider so Anchor can intercept its calls.

    Call this BEFORE anchor.runtime.activate(). Example::

        import anchor.runtime
        anchor.runtime.register_provider("api.moonshot.cn", "kimi")
        anchor.runtime.register_provider("api.perplexity.ai", "perplexity")
        anchor.runtime.activate()

    Args:
        domain: The hostname (or fragment) of the provider's API endpoint.
                Matched as: ``domain in request_host``.
                Examples: "api.kimi.ai", "my-company.ai/v1/chat"
        name:   A short human-readable label (used in reports and logs).
    """
    entry = (domain.lower(), name)
    if entry not in _CUSTOM_PROVIDERS:
        _CUSTOM_PROVIDERS.append(entry)


def identify_provider(url: str) -> Optional[str]:
    """
    Return the provider name if the URL points to a known AI API.
    Returns None if the URL is not recognised as an AI API endpoint.

    Custom providers (registered via register_provider) are checked first.
    """
    try:
        host     = urlparse(url).netloc.lower()
        path     = urlparse(url).path.lower()
        combined = host + path
        # Custom providers take precedence
        for fragment, name in _CUSTOM_PROVIDERS:
            if fragment in combined:
                return name
        # Built-in registry
        for fragment, name in AI_API_DOMAINS:
            if fragment in combined:
                return name
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Prompt extraction helpers
# ---------------------------------------------------------------------------

def extract_prompt_from_payload(body_bytes: bytes) -> Optional[str]:
    """
    Try to extract a human-readable prompt string from a raw request body.

    Handles the common JSON schemas used by OpenAI, Anthropic, Cohere,
    HuggingFace, Ollama, and generic 'prompt' / 'inputs' fields.

    Returns the extracted text as a single string, or None if not parseable.
    """
    if not body_bytes:
        return None
    try:
        payload = json.loads(body_bytes.decode("utf-8", errors="ignore"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Binary or non-JSON body — not an LLM API call we recognise
        return None

    # ── OpenAI / Groq / Together / Mistral chat format ────────────────
    if "messages" in payload and isinstance(payload["messages"], list):
        parts: List[str] = []
        for msg in payload["messages"]:
            role    = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str):
                parts.append(f"[{role}] {content}")
            elif isinstance(content, list):
                # Multi-modal content blocks
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(f"[{role}] {block.get('text', '')}")
        return "\n".join(parts) if parts else None

    # ── Anthropic messages format ──────────────────────────────────────
    if "messages" in payload and "system" in payload:
        system = payload.get("system", "")
        msgs   = payload.get("messages", [])
        parts  = [f"[system] {system}"] if system else []
        for msg in msgs:
            parts.append(f"[{msg.get('role', '')}] {msg.get('content', '')}")
        return "\n".join(parts) if parts else None

    # ── Cohere / generic 'message' field ──────────────────────────────
    if "message" in payload and isinstance(payload["message"], str):
        return payload["message"]

    # ── HuggingFace / generic 'inputs' field ──────────────────────────
    if "inputs" in payload:
        inp = payload["inputs"]
        if isinstance(inp, str):
            return inp
        if isinstance(inp, list):
            return " ".join(str(x) for x in inp)

    # ── Raw completion 'prompt' field ─────────────────────────────────
    if "prompt" in payload and isinstance(payload["prompt"], str):
        return payload["prompt"]

    # ── Ollama format ─────────────────────────────────────────────────
    if "model" in payload and ("prompt" in payload or "messages" in payload):
        return payload.get("prompt") or str(payload.get("messages", ""))

    return None


def extract_response_text(body_bytes: bytes, provider: str) -> Optional[str]:
    """
    Extract the generated text from an LLM API response body.

    Handles OpenAI, Anthropic, Cohere, HuggingFace, and Ollama response shapes.
    Falls back to raw UTF-8 decoding for unknown providers.
    """
    if not body_bytes:
        return None
    try:
        payload = json.loads(body_bytes.decode("utf-8", errors="ignore"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body_bytes.decode("utf-8", errors="ignore")[:4096]

    # OpenAI / Groq / Together
    choices = payload.get("choices", [])
    if choices and isinstance(choices, list):
        first = choices[0]
        if "message" in first:
            return first["message"].get("content", "")
        if "text" in first:
            return first["text"]

    # Anthropic
    content = payload.get("content", [])
    if content and isinstance(content, list):
        texts = [b.get("text", "") for b in content if isinstance(b, dict)]
        return "\n".join(texts)

    # Cohere
    if "text" in payload:
        return payload["text"]

    # HuggingFace
    if isinstance(payload, list) and payload:
        first = payload[0]
        return first.get("generated_text") or first.get("text") or str(first)

    # Ollama
    if "response" in payload:
        return payload["response"]
    if "message" in payload and isinstance(payload["message"], dict):
        return payload["message"].get("content", "")

    return None
