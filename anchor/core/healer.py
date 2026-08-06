"""
anchor/core/healer.py

Hybrid Healer — Anchor's fix suggestion engine.

For each detected violation, the Healer reads the flagged source line and
proposes a concrete, diff-style fix that the developer can apply.

Suggestions are written into governance_violations.txt under each violation.
They can be applied via:

    anchor heal <path>            # show diffs interactively
    anchor heal <path> --apply    # apply all fixes

Design principles:
  - SUGGEST, never silently mutate. Developers are always in control.
  - Rule-specific fixers for common violations.
  - Graceful fallback to mitigation text when no auto-fix is available.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class HealSuggestion:
    """A suggested fix for a single violation."""
    rule_id:     str
    file:        str
    line:        int
    original:    str          # the flagged line (stripped)
    suggested:   str          # the proposed replacement (stripped), or "" if manual only
    explanation: str          # human-readable explanation of the change
    auto_fixable: bool = False  # True if suggested can be applied programmatically


# ---------------------------------------------------------------------------
# Rule-specific fixers
# ---------------------------------------------------------------------------

def _fix_anc_001(line: str):
    """ANC-001: Public LLM API call → route through PII-scrubbing proxy."""
    # Suggest wrapping with a proxy or using an internal client
    return (
        "# Route through your PII-scrubbing proxy instead of calling the public API directly.",
        "Direct calls to public LLM APIs (OpenAI, Anthropic, Cohere) may leak sensitive data. "
        "Route all LLM traffic through a proxy that strips PII before forwarding.",
        False
    )


def _fix_anc_002(line: str):
    """ANC-002: Vector store upsert without encryption."""
    return (
        "",
        "Encrypt embeddings before upserting to vector stores. Unencrypted embeddings can be "
        "inverted to recover sensitive source text. Use client-side encryption or an encrypted index.",
        False
    )


def _fix_anc_010(line: str):
    """ANC-010: Missing system prompt guardrail."""
    if "messages" in line:
        suggested = line.rstrip() + '\n    {"role": "system", "content": "You are a helpful assistant. Do not discuss [PROHIBITED_TOPICS]."}'
        return (
            suggested,
            "Add a system prompt as the first message to define alignment and behavioral constraints.",
            False
        )
    return None


def _fix_anc_011(line: str):
    """ANC-011: Sensitive attribute as model feature."""
    return (
        "",
        "Remove or proxy sensitive demographic attributes (gender, race, etc.) from model features. "
        "Use fairness-aware feature engineering or add bias detection tests to your ML pipeline.",
        False
    )


def _fix_anc_015(line: str):
    """ANC-015: LLM output displayed without moderation."""
    m = re.search(r'(print|render|display|return)\s*\(\s*(\w+)', line)
    if m:
        var = m.group(2)
        suggested = re.sub(
            r'(print|render|display|return)\s*\(\s*(\w+)',
            f'{m.group(1)}(moderation_filter({var})',
            line, count=1
        )
        return (
            suggested.rstrip(),
            "Wrap LLM output in a content moderation filter before displaying to users. "
            "This prevents reputational damage from harmful model outputs.",
            False
        )
    return None


def _fix_anc_022(line: str):
    """ANC-022: Unverified cross-agent message consumption."""
    return (
        "",
        "Verify the integrity and origin of messages between agents. "
        "Use signed messages or a trust broker to prevent a compromised agent from poisoning the swarm.",
        False
    )


def _fix_anc_023(line: str):
    """ANC-023: Bulk env access  os.environ → targeted os.environ.get()"""
    m = re.search(r'(\w+)\s*=\s*os\.environ(?!\s*\.get)', line)
    if m:
        var = m.group(1)
        suggested = re.sub(
            r'os\.environ(?!\s*\.get)',
            f'os.environ.get("YOUR_KEY_NAME", "")',
            line,
            count=1
        )
        return (
            suggested.rstrip(),
            "Replace broad os.environ access with targeted os.environ.get('KEY', default). "
            "This prevents agents from bulk-harvesting all environment variables.",
            True
        )
    suggested = re.sub(r'\bos\.environ\b(?!\s*\.get)', 'os.environ.get("YOUR_KEY_NAME", "")', line, count=1)
    return (
        suggested.rstrip(),
        "Use os.environ.get('SPECIFIC_KEY', '') to fetch only the variable your code needs.",
        True
    )


def _fix_subprocess_shell(line: str):
    """ANC-018: subprocess without Diamond Cage sandboxing."""
    if "shell=True" in line:
        suggested = line.replace("shell=True", "shell=False")
        return (
            suggested.rstrip(),
            "Set shell=False and pass arguments as a list: subprocess.run(['cmd', 'arg1']) "
            "to prevent shell injection attacks.",
            True
        )
    # No shell=True, but still unsandboxed — suggest Diamond Cage
    return (
        "",
        "Native subprocess calls bypass the Diamond Cage sandbox. "
        "Use anchor.core.sandbox.DiamondCage.run_safe() for agent-initiated subprocess execution.",
        False
    )


def _fix_eval(line: str):
    """Eval/exec of user input → raise NotImplementedError or use ast.literal_eval"""
    m = re.search(r'\beval\s*\(', line)
    if m:
        suggested = line[:m.start()] + "# UNSAFE: " + line[m.start():].rstrip() + "  # Use ast.literal_eval() for safe literal parsing"
        return (
            suggested.rstrip(),
            "eval() on user input allows arbitrary code execution. "
            "Use ast.literal_eval() for safe parsing of literals, or redesign to avoid eval entirely.",
            False
        )
    return None


def _fix_open_file(line: str):
    """RI-08: Raw file open → add suppression comment if intentional"""
    if "# anchor: ignore" not in line:
        suggested = line.rstrip() + "  # anchor: ignore RI-08"
        return (
            suggested,
            "If this file access is intentional and safe, add '# anchor: ignore RI-08' "
            "to suppress this finding and create an audit trail.",
            True
        )
    return None


def _fix_hardcoded_secret(line: str):
    """Hardcoded credential → replace with env var lookup"""
    m = re.search(r'(api[_\-]?key|password|secret|token)\s*=\s*["\'"]([^"\']{6,})["\']', line, re.IGNORECASE)
    if m:
        var_name = m.group(1).upper().replace("-", "_")
        suggested = re.sub(
            r'(api[_\-]?key|password|secret|token)\s*=\s*["\'"][^"\']+["\']',
            f'{m.group(1)} = os.environ.get("{var_name}", "")',
            line, count=1, flags=re.IGNORECASE
        )
        return (
            suggested.rstrip(),
            f"Never hardcode credentials. Load from environment: "
            f'os.environ.get("{var_name}", ""). '
            f"Add {var_name} to your .env file and ensure it's in .gitignore.",
            True
        )
    return None


def _fix_pickle(line: str):
    """Pickle/marshal of untrusted data → use json"""
    if "pickle" in line.lower():
        suggested = line.rstrip() + "  # RISK: Use json.loads() for untrusted data; pickle can execute code"
        return (
            suggested,
            "pickle.loads() on untrusted data allows arbitrary code execution. "
            "Use json.loads() for safe deserialization, or validate the source before unpickling.",
            False
        )
    return None


# ---------------------------------------------------------------------------
# Fixer registry: maps rule_id prefix → fixer function
# ---------------------------------------------------------------------------
_FIXERS: list[tuple[str, callable]] = [
    ("ANC-001",  _fix_anc_001),
    ("ANC-002",  _fix_anc_002),
    ("ANC-010",  _fix_anc_010),
    ("ANC-011",  _fix_anc_011),
    ("ANC-015",  _fix_anc_015),
    ("ANC-018",  _fix_subprocess_shell),
    ("ANC-022",  _fix_anc_022),
    ("ANC-023",  _fix_anc_023),
    ("RI-12",    _fix_subprocess_shell),
    ("ANC-030",  _fix_eval),
    ("ANC-031",  _fix_eval),
    ("RI-08",    _fix_open_file),
    ("ANC-010",  _fix_hardcoded_secret),
    ("ANC-011",  _fix_hardcoded_secret),
    ("ANC-012",  _fix_hardcoded_secret),
    ("ANC-PKL",  _fix_pickle),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def suggest_fix(violation: dict) -> Optional[HealSuggestion]:
    """
    Generate a fix suggestion for a violation dict.

    Args:
        violation: A violation dict from the engine, with keys:
                   id, name, file, line, message, mitigation, severity.

    Returns:
        HealSuggestion if a suggestion could be generated, else None.
    """
    rule_id   = violation.get("id", "")
    file_path = violation.get("file", "")
    line_no   = violation.get("line", 0)
    mitigation = violation.get("mitigation", "")

    # Read the flagged line from the source file
    original_line = _read_line(file_path, line_no)
    if original_line is None:
        return HealSuggestion(
            rule_id     = rule_id,
            file        = file_path,
            line        = line_no,
            original    = "",
            suggested   = "",
            explanation = mitigation or "See Anchor documentation for remediation guidance.",
            auto_fixable = False,
        )

    # Try rule-specific fixers
    for prefix, fixer in _FIXERS:
        if rule_id.startswith(prefix):
            result = fixer(original_line)
            if result:
                suggested, explanation, auto_fixable = result
                return HealSuggestion(
                    rule_id      = rule_id,
                    file         = file_path,
                    line         = line_no,
                    original     = original_line.strip(),
                    suggested    = suggested.strip(),
                    explanation  = explanation,
                    auto_fixable = auto_fixable,
                )

    # Generic fallback
    if original_line.strip():
        return HealSuggestion(
            rule_id      = rule_id,
            file         = file_path,
            line         = line_no,
            original     = original_line.strip(),
            suggested    = "",
            explanation  = mitigation or "Manual review required. See mitigation guidance in the Anchor catalog.",
            auto_fixable = False,
        )

    return None


def format_suggestion_for_report(suggestion: HealSuggestion) -> str:
    """
    Format a HealSuggestion as a diff-style block for the .txt report.
    """
    lines = []
    lines.append("    --- Suggested Fix " + "-" * 41)
    lines.append(f"    {suggestion.explanation}")
    if suggestion.original:
        lines.append(f"    [✗] {suggestion.original}")
    if suggestion.suggested and suggestion.suggested != suggestion.original:
        lines.append(f"    [✔] {suggestion.suggested}")
    if not suggestion.auto_fixable:
        lines.append("    Manual review required — apply with care.")
    else:
        lines.append("    Auto-fixable via: anchor heal " + suggestion.file)
    lines.append("    " + "-" * 59)
    return "\n".join(lines)


def apply_fix(suggestion: HealSuggestion) -> bool:
    """
    Apply an auto-fixable suggestion to the source file in-place.

    Returns True if the fix was applied, False otherwise.
    Only runs when auto_fixable=True and suggested is non-empty.
    """
    if not suggestion.auto_fixable or not suggestion.suggested:
        return False

    file_path = suggestion.file
    line_no   = suggestion.line

    try:
        with open(file_path, "r", encoding="utf-8") as f:  # anchor: ignore RI-08
            source_lines = f.readlines()

        if line_no < 1 or line_no > len(source_lines):
            return False

        orig = source_lines[line_no - 1]
        leading = len(orig) - len(orig.lstrip())
        fixed = " " * leading + suggestion.suggested + "\n"
        source_lines[line_no - 1] = fixed

        with open(file_path, "w", encoding="utf-8") as f:  # anchor: ignore RI-08
            f.writelines(source_lines)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_line(file_path: str, line_no: int) -> Optional[str]:
    """Read a specific 1-indexed line from a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:  # anchor: ignore RI-08
            for i, line in enumerate(f, start=1):
                if i == line_no:
                    return line.rstrip()
    except Exception:
        pass
    return None
