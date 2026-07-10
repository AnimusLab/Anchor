"""
bench_anchor.py -- Anchor Runtime Latency Benchmark
=====================================================

Measures the four core runtime primitives under N-iteration load.

  Suite 1 -- Policy Evaluation
      PolicyEngine.scan_file() against a realistic Python file with
      active governance rules (the same 118-rule production set).

  Suite 2 -- Hash Generation
      DecisionAuditor._hash_payload() -- raw SHA-256 throughput,
      isolated from I/O so we can report the primitive cost alone.

  Suite 3 -- Receipt Generation (Decision Audit Chain)
      DecisionAuditor.audit() -- the full critical DAC write path:
        ETH compliance check (Aho-Corasick) + SHA-256 hash chain
        + HMAC-SHA256 signature + JSONL append to disk.

  Suite 4 -- Replay Verification
      verify_chain_hash() -- HMAC-SHA256 verification as used by
      `anchor verify --block` in the forensic audit replay path.

Each suite reports:
  - Average latency
  - Median latency
  - P95 latency
  - P99 latency
  - Throughput (evaluations/second)

Usage:
  conda run -n anchor_dev python benchmarks/bench_anchor.py
  conda run -n anchor_dev python benchmarks/bench_anchor.py --iterations 50000
  conda run -n anchor_dev python benchmarks/bench_anchor.py --suite policy
  conda run -n anchor_dev python benchmarks/bench_anchor.py --json
  conda run -n anchor_dev python benchmarks/bench_anchor.py --output results.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Callable, List, Optional

# ---------------------------------------------------------------------------
# Bootstrap: add repo root to sys.path and change into it
# ---------------------------------------------------------------------------
_ANCHOR_ROOT = Path(__file__).resolve().parent.parent
if str(_ANCHOR_ROOT) not in sys.path:
    sys.path.insert(0, str(_ANCHOR_ROOT))
os.chdir(_ANCHOR_ROOT)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Realistic Python file that triggers multiple Anchor rules.
# Written as a concatenation of byte strings so no non-ASCII chars appear.
_FIXTURE_PY: bytes = (
    b"import os\n"
    b"import subprocess\n"
    b"import pickle\n"
    b"import requests\n"
    b"\n"
    b"SECRET_KEY = 'super-secret-key-123'\n"
    b"API_TOKEN  = 'ghp_abc123def456ghi789jkl012'\n"
    b"\n"
    b"def load_model(path: str):\n"
    b"    with open(path, 'rb') as f:\n"
    b"        return pickle.load(f)\n"
    b"\n"
    b"def run_eval(prompt: str):\n"
    b"    result = subprocess.run(\n"
    b"        ['python', 'eval.py', prompt],\n"
    b"        shell=True,\n"
    b"        capture_output=True,\n"
    b"    )\n"
    b"    return result.stdout\n"
    b"\n"
    b"def export_data(data: dict, url: str):\n"
    b"    requests.post(url, json=data)\n"
    b"    eval(data.get('code', ''))\n"
    b"\n"
    b"class LoanDecisionEngine:\n"
    b"    def decide(self, applicant: dict) -> dict:\n"
    b"        if applicant.get('zip_code') in BAD_ZIPS:\n"
    b"            return {'decision': 'DENY'}\n"
    b"        return {'decision': 'APPROVE'}\n"
)

# Realistic conversational fixture for ETH compliance scan
_BENCH_PROMPT = (
    "Please evaluate the loan application for this applicant."
)
_BENCH_RESPONSE = (
    "Based on the applicant financial profile and credit history, "
    "we recommend APPROVAL with a 6.5 percent APR. The primary "
    "factors are debt-to-income ratio and employment stability."
)


# ---------------------------------------------------------------------------
# Statistics container
# ---------------------------------------------------------------------------

class BenchResult:
    def __init__(
        self,
        suite_name: str,
        iterations: int,
        timings_us: List[float],
        errors: int = 0,
        notes: str = "",
    ) -> None:
        self.suite_name = suite_name
        self.iterations = iterations
        self.timings_us = timings_us
        self.errors     = errors
        self.notes      = notes

    @property
    def avg_us(self) -> float:
        return statistics.mean(self.timings_us)

    @property
    def median_us(self) -> float:
        return statistics.median(self.timings_us)

    @property
    def p95_us(self) -> float:
        s = sorted(self.timings_us)
        return s[min(int(len(s) * 0.95), len(s) - 1)]

    @property
    def p99_us(self) -> float:
        s = sorted(self.timings_us)
        return s[min(int(len(s) * 0.99), len(s) - 1)]

    @property
    def throughput(self) -> float:
        total_s = sum(self.timings_us) / 1_000_000
        return self.iterations / total_s if total_s > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "suite":          self.suite_name,
            "iterations":     self.iterations,
            "errors":         self.errors,
            "avg_ms":         round(self.avg_us / 1000, 4),
            "median_ms":      round(self.median_us / 1000, 4),
            "p95_ms":         round(self.p95_us / 1000, 4),
            "p99_ms":         round(self.p99_us / 1000, 4),
            "throughput_eps": round(self.throughput, 1),
            "notes":          self.notes,
        }


def _run_suite(
    name:       str,
    fn:         Callable,
    iterations: int,
    warmup:     int = 200,
) -> BenchResult:
    """Execute fn() for `iterations` timed iterations, preceded by `warmup` un-timed calls."""
    print(f"  Warming up ({warmup} iters)...", end="", flush=True)
    for _ in range(warmup):
        try:
            fn()
        except Exception:
            pass
    print(" done")

    timings: List[float] = []
    errors = 0
    print(f"  Running {iterations:,} iterations...", end="", flush=True)
    for _ in range(iterations):
        t0 = perf_counter()
        try:
            fn()
        except Exception:
            errors += 1
        timings.append((perf_counter() - t0) * 1_000_000)

    print(f" done  ({errors} errors)")
    return BenchResult(name, iterations, timings, errors)


# ---------------------------------------------------------------------------
# Suite 1 -- Policy Evaluation
# ---------------------------------------------------------------------------

def build_policy_suite(n: int) -> BenchResult:
    """
    Measures PolicyEngine.scan_file() -- the hot path for `anchor check`.
    Uses the real production rule set loaded from the project .anchor dir.
    """
    print("\n[Suite 1] Policy Evaluation -- PolicyEngine.scan_file()")

    from anchor.core.engine import PolicyEngine
    from anchor.core.loader import load_constitution
    from anchor.core.registry import LanguageRegistry

    anchor_dir = Path(".anchor")
    gov_root   = Path("anchor") / "governance"
    constitution = load_constitution(gov_root, anchor_dir=anchor_dir)
    rules_list   = [asdict(r) for r in constitution.rules.values()]

    engine  = PolicyEngine({"rules": rules_list})
    adapter = LanguageRegistry.get_adapter_for_file("target.py")
    if adapter is None:
        raise RuntimeError("No Python adapter found. Is tree-sitter-python installed?")

    r = _run_suite(
        "Policy Evaluation (scan_file)",
        lambda: engine.scan_file(_FIXTURE_PY, "bench/fixture.py", adapter),
        n,
    )
    r.notes = f"{len(rules_list)} active rules, {len(_FIXTURE_PY)} byte fixture"
    return r


# ---------------------------------------------------------------------------
# Suite 2 -- Hash Generation
# ---------------------------------------------------------------------------

def build_hash_suite(n: int) -> BenchResult:
    """
    Measures the raw SHA-256 hashing primitive used in DAC block formation.
    Isolated from disk I/O so we can quote the pure compute cost.
    """
    print("\n[Suite 2] Hash Generation -- SHA-256 (_hash_payload)")

    from anchor.runtime.decision_auditor import DecisionAuditor

    # Warm up singleton (absorbs the 30 ms subprocess penalty once)
    auditor = DecisionAuditor()
    payload = json.dumps(["ETH-001", "SEC-003", "SEC-007"])

    r = _run_suite(
        "Hash Generation (SHA-256)",
        lambda: auditor._hash_payload(payload),
        n,
    )
    r.notes = f"payload={len(payload)} bytes"
    return r


# ---------------------------------------------------------------------------
# Suite 3 -- Receipt Generation (full DAC audit path)
# ---------------------------------------------------------------------------

def build_receipt_suite(n: int) -> BenchResult:
    """
    Measures DecisionAuditor.audit() -- the full critical path:
      1. ETH compliance check (Aho-Corasick trie scan)
      2. SHA-256 hash chain computation
      3. HMAC-SHA256 signature (if ANCHOR_MAT env is set)
      4. JSONL append to .anchor/runtime_chain.jsonl

    This includes real disk I/O so the number reflects production latency.
    """
    print("\n[Suite 3] Receipt Generation -- DecisionAuditor.audit() [full DAC path]")

    from anchor.runtime.decision_auditor import DecisionAuditor

    auditor  = DecisionAuditor()
    findings = [
        {"rule_id": "SEC-003", "severity": "ERROR", "message": "Hardcoded secret"},
    ]

    r = _run_suite(
        "Receipt Generation (audit + JSONL write)",
        lambda: auditor.audit(
            provider="benchmark",
            prompt=_BENCH_PROMPT,
            response=_BENCH_RESPONSE,
            findings=findings,
            jurisdiction="GLOBAL",
            latency_ms=0.0,
            mode="conversational",
        ),
        n,
    )
    r.notes = "ETH scan + chain hash + JSONL disk write"
    return r


# ---------------------------------------------------------------------------
# Suite 4 -- Replay Verification (HMAC-SHA256)
# ---------------------------------------------------------------------------

def build_verify_suite(n: int) -> BenchResult:
    """
    Measures verify_chain_hash() -- the cryptographic verification step
    used in `anchor verify --block` and forensic audit replay.
    Sets a test key in ANCHOR_MAT so we benchmark the real HMAC path.
    """
    print("\n[Suite 4] Replay Verification -- verify_chain_hash() [HMAC-SHA256]")

    _orig_key = os.environ.get("ANCHOR_MAT", "")
    os.environ["ANCHOR_MAT"] = "bench-test-secret-key-do-not-use-in-production"

    from anchor.core.crypto import sign_chain_hash, verify_chain_hash

    test_hash = hashlib.sha256(b"benchmark_chain_data").hexdigest()
    test_sig  = sign_chain_hash(test_hash)
    if test_sig is None:
        raise RuntimeError("sign_chain_hash returned None -- ANCHOR_MAT not set correctly")

    r = _run_suite(
        "Replay Verification (HMAC-SHA256)",
        lambda: verify_chain_hash(test_hash, test_sig),
        n,
    )
    r.notes = "HMAC-SHA256 with pre-computed chain_hash + signature"

    if _orig_key:
        os.environ["ANCHOR_MAT"] = _orig_key
    elif "ANCHOR_MAT" in os.environ:
        del os.environ["ANCHOR_MAT"]

    return r


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

DIV = "-" * 80


def _fmt(us: float) -> str:
    """Format microseconds: show us for sub-ms values, ms for larger."""
    if us < 1000:
        return f"{us:>8.2f} us"
    return f"{us / 1000:>8.3f} ms"


def print_result(r: BenchResult) -> None:
    print(f"\n  Suite:       {r.suite_name}")
    print(f"  Iterations:  {r.iterations:>10,}  |  Errors: {r.errors}")
    print(f"  Notes:       {r.notes}")
    print(f"  {'-'*52}")
    print(f"  Average:     {_fmt(r.avg_us)}")
    print(f"  Median:      {_fmt(r.median_us)}")
    print(f"  P95:         {_fmt(r.p95_us)}")
    print(f"  P99:         {_fmt(r.p99_us)}")
    print(f"  {'-'*52}")
    print(f"  Throughput:  {r.throughput:>12,.0f}  eval/sec")


def print_summary_table(results: List[BenchResult]) -> None:
    w = 44
    print(f"\n  {'Suite':<{w}} {'Avg':>10} {'P95':>10} {'P99':>10} {'Eval/s':>12}")
    print(f"  {'-'*w} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")
    for r in results:
        print(
            f"  {r.suite_name:<{w}} "
            f"{_fmt(r.avg_us):>10} "
            f"{_fmt(r.p95_us):>10} "
            f"{_fmt(r.p99_us):>10} "
            f"{r.throughput:>12,.0f}"
        )


def print_paper_block(results: List[BenchResult]) -> None:
    """Ready-to-paste paragraph for a research paper Methods/Performance section."""
    print(f"\n{DIV}")
    print("  PAPER CITATION BLOCK")
    print(DIV)
    for r in results:
        print(f"\n  [{r.suite_name}]")
        print(
            f"  Average policy evaluation latency: {r.avg_us/1000:.3f} ms "
            f"(median {r.median_us/1000:.3f} ms, "
            f"P95 {r.p95_us/1000:.3f} ms, "
            f"P99 {r.p99_us/1000:.3f} ms). "
            f"Throughput: {r.throughput:,.0f} evaluations/sec "
            f"(n={r.iterations:,} iterations, "
            f"{r.notes})."
        )
    print(f"\n{DIV}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

SUITES = {
    "policy":  build_policy_suite,
    "hash":    build_hash_suite,
    "receipt": build_receipt_suite,
    "verify":  build_verify_suite,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Anchor Runtime Latency Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int, default=10_000,
        help="Iterations per suite (default: 10,000)",
    )
    parser.add_argument(
        "--suite", "-s",
        choices=list(SUITES.keys()) + ["all"],
        default="all",
        help="Which suite to run (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output (for CI / appendix ingestion)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str, default=None,
        help="Write JSON results to this file path",
    )
    args = parser.parse_args()

    # Disable remote Ledger and Relay URLs to avoid blocking HTTP/socket timeouts in benchmarks
    os.environ.pop("ANCHOR_LEDGER_URL", None)
    os.environ.pop("ANCHOR_RELAY_URL", None)

    if not args.json:
        print(DIV)
        print("  Anchor Runtime Benchmark")
        print(f"  Python:               {sys.version.split()[0]}")
        print(f"  Iterations per suite: {args.iterations:,}")
        anchor_dir = Path(".anchor")
        if anchor_dir.exists():
            print(f"  .anchor dir:          {anchor_dir.resolve()}")
        print(DIV)

    selected = list(SUITES.keys()) if args.suite == "all" else [args.suite]
    results: List[BenchResult] = []

    for key in selected:
        try:
            r = SUITES[key](args.iterations)
            results.append(r)
            if not args.json:
                print_result(r)
        except Exception as exc:
            import traceback
            print(f"\n[ERROR] Suite {key!r} failed: {exc}", file=sys.stderr)
            traceback.print_exc()

    if not results:
        sys.exit(1)

    if args.json:
        payload = json.dumps([r.to_dict() for r in results], indent=2)
        print(payload)
        if args.output:
            Path(args.output).write_text(payload, encoding="utf-8")
        return

    if len(results) > 1:
        print(f"\n{DIV}\n  SUMMARY TABLE\n{DIV}")
        print_summary_table(results)

    print_paper_block(results)

    if args.output:
        Path(args.output).write_text(
            json.dumps([r.to_dict() for r in results], indent=2),
            encoding="utf-8",
        )
        print(f"\n  Results written to: {args.output}")


if __name__ == "__main__":
    main()
