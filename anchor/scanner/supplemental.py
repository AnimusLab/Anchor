"""
anchor/scanner/supplemental.py

Static rules that complement the native engine's built-in set.

The native engine only recognises hard-coded secrets assigned to api_key-style
variables or written as bearer tokens, and has no rule for provider tokens,
private-key blocks, unsafe deserialisation, disabled TLS verification or DOM
write sinks. Those are checked here, line by line, and flow through the same
pragma, ``.anchorignore`` and severity handling as engine findings.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from anchor.scanner.pragmas import iter_text_files, read_text


@dataclass(frozen=True)
class SupplementalRule:
    rule_id: str
    name: str
    severity: str
    statutes: str
    pattern: "re.Pattern[str]"
    extensions: Optional[FrozenSet[str]] = None      # None = every text file
    skip_if_engine_reported: FrozenSet[str] = frozenset()


_PY = frozenset({".py", ".pyi", ".ipynb"})
_JS = frozenset({".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".html", ".htm", ".vue", ".svelte"})

RULES: Tuple[SupplementalRule, ...] = (
    SupplementalRule(
        "SEC-020", "Hardcoded AWS Access Key ID", "blocker", "OWASP-LLM06",
        re.compile(r"\b(?:AKIA|ASIA)(?![0-9A-Z]*EXAMPLE)[0-9A-Z]{16}\b"),
        skip_if_engine_reported=frozenset({"SEC-002"}),
    ),
    SupplementalRule(
        "SEC-021", "Hardcoded Provider or VCS Token", "blocker", "OWASP-LLM06",
        re.compile(
            r"\bgh[pousr]_[A-Za-z0-9]{36,}"
            r"|\bgithub_pat_[A-Za-z0-9_]{22,}"
            r"|\bxox[abprs]-[A-Za-z0-9-]{10,}"
            r"|\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}"
        ),
        skip_if_engine_reported=frozenset({"SEC-002"}),
    ),
    SupplementalRule(
        "SEC-022", "Private Key Material in Source", "blocker", "OWASP-LLM06",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----"),
    ),
    SupplementalRule(
        "SEC-023", "Unsafe Deserialization (pickle/marshal/yaml.load/torch.load)", "error", "OWASP-LLM05",
        re.compile(
            r"\b(?:pickle|cPickle|_pickle|dill|marshal|shelve)\.loads?\s*\("
            r"|\byaml\.load\s*\((?![^)\n]*(?:SafeLoader|CSafeLoader))"
            r"|\btorch\.load\s*\((?![^)\n]*weights_only\s*=\s*True)"
        ),
        extensions=_PY,
    ),
    SupplementalRule(
        "SEC-024", "TLS Certificate Verification Disabled", "error", "CWE-295",
        re.compile(
            r"\bverify\s*=\s*False\b"
            r"|\bssl\._create_unverified_context\b"
            r"|\bCERT_NONE\b"
            r"|\brejectUnauthorized\s*:\s*false\b"
            r"|\bInsecureSkipVerify\s*:\s*true\b"
            r"|\bNODE_TLS_REJECT_UNAUTHORIZED\s*=\s*[\"']?0"
        ),
    ),
    SupplementalRule(
        "SEC-025", "DOM Write Sink (document.write)", "error", "CWE-79",
        re.compile(r"\bdocument\.write(?:ln)?\s*\("),
        extensions=_JS,
    ),
    SupplementalRule(
        "SEC-026", "Social Security Number Literal", "warning", "GLBA / GDPR-Art5",
        re.compile(r"(?<![\d-])(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}(?![\d-])"),
    ),
)

_SKIP_SUFFIXES = (".min.js", ".map", ".lock", ".svg")
_SKIP_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock"}
MAX_LINE_LENGTH = 2000  # minified bundles: not worth regex-scanning


def scan_supplemental(target: str, engine_violations: Iterable[dict] = ()) -> List[dict]:
    """Run the supplemental rules over ``target`` (a file or directory)."""
    engine_rules: Dict[Tuple[str, int], Set[str]] = {}
    for v in engine_violations:
        key = (os.path.realpath(v.get("file", "")), int(v.get("line", 0) or 0))
        engine_rules.setdefault(key, set()).update(
            r.strip().upper() for r in str(v.get("aggregated_rule_ids", "")).split(",") if r.strip()
        )

    findings: List[dict] = []
    for full, _rel in iter_text_files(target):
        name = os.path.basename(full)
        if name in _SKIP_NAMES or name.endswith(_SKIP_SUFFIXES):
            continue
        ext = os.path.splitext(name)[1].lower()
        rules = [r for r in RULES if r.extensions is None or ext in r.extensions]
        if not rules:
            continue
        text = read_text(full)
        if not text:
            continue
        real = os.path.realpath(full)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if len(line) > MAX_LINE_LENGTH:
                continue
            already = engine_rules.get((real, line_no), set())
            for rule in rules:
                if rule.skip_if_engine_reported & already:
                    continue
                if rule.pattern.search(line):
                    findings.append({
                        "file": full,
                        "line": line_no,
                        "line_content": line.strip()[:200],
                        "name": rule.name,
                        "aggregated_rule_ids": rule.rule_id,
                        "statutory_references": rule.statutes,
                        "severity": rule.severity,
                    })
    return findings
