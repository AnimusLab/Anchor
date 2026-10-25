# 🛡️ Anchor Core (`anchor-audit`)

### The Deterministic Runtime Governance & Compliance Kernel for Autonomous AI Systems.

[![PyPI Version](https://img.shields.io/pypi/v/anchor-audit.svg)](https://pypi.org/project/anchor-audit/)
[![License](https://img.shields.io/github/license/AnimusLab/Anchor.svg)](https://github.com/AnimusLab/Anchor)

**Current release: 6.0.6** · Python 3.10–3.13

Anchor is a high-performance, dual-language (Rust/Python) infrastructure library designed to enforce strict regulatory invariants, architectural boundaries, and safety safeguards around autonomous AI agents and LLM application pipelines in real-time. 

By executing compiled Abstract Syntax Tree (AST) query matchers and single-pass Deterministic Finite Automaton (DFA) regex sets, Anchor operates with zero-copy memory boundaries—designed to keep per-call overhead low. See `benchmarks/bench_guard.py` to measure it on your hardware.

---

## 🏎️ Core Architectural Horsepower

- **Fast static scanning**: Rust backend engine utilizing parallel directory walking via `rayon` and memory-mapped files (`memmap2`).
- **Zero-Copy Memory Boundaries**: Leverages PyO3 zero-copy buffer bridges to consume incoming network data frames straight from host ASGI server pools (like FastAPI) with zero heap allocation overhead.
- **Asymmetric Cryptographic Identity**: Every compiled audit log is bundled into an tamper-evident Decision Audit Chain (DAC) block, sealed locally using Ed25519 asymmetric keys and verified via constant-time hashing (`subtle::ConstantTimeEq`).
- **Active Self-Healing Interception**: Moves beyond passive post-mortem dashboards. If an active consumer agent drifts into an invariant violation, Anchor's runtime layer intercepts the thread, halts execution, and injects dynamic, domain-agnostic rerouting directives on the fly.

---

## 🏛️ Comprehensive Regulatory Scope

Anchor maps rules to the provisions they relate to (a pattern match is not a legal finding). Coverage includes:

1. **EU Artificial Intelligence Act (Regulation EU 2024/1689)**: Complete mapping from Chapter II Article 5 Prohibited Practices (subliminal manipulation, facial scraping safeguards) to Chapter III Articles 6–27 High-Risk System obligations (6-month log retention tracking under Art 12/19, Article 14 human override levers), stretching up to Article 99 turnover penalty metrics.
2. **U.S. Securities and Exchange Commission (SEC / FINRA)**: Hard automated boundaries protecting algorithmic trading setups under SEC Regulation SCI (System capacity loop circuit breakers), Exchange Act Rule 15c3-5 (Pre-trade credit and risk limit validation), and Cybersecurity Form 8-K outbound data exfiltration gates.
3. **Industry Frameworks**: Built-in support for FINOS OSERA AI supply-chain resiliency blueprints, OWASP Top 10 LLM security controls, NIST AI RMF, and ISO/IEC 42001 standards.

---

## 📦 High-Velocity Installation

Deploy the compiled binary kernel straight into your production cluster workspace:

```bash
pip install anchor-audit
```

Anchor pulls in its runtime dependencies automatically (Click, HTTPX, PyYAML,
cryptography, wrapt, GitPython and the tree-sitter grammars), so the `anchor`
command is usable straight after install.

Optional extras:

```bash
pip install "anchor-audit[providers]"   # OpenAI, Anthropic, Groq, Cohere, Ollama, ...
pip install "anchor-audit[server]"      # FastAPI/ASGI gateway (anchor.app) + uvicorn
pip install "anchor-audit[dev]"         # pytest, black, mypy
```

The CLI, the `@guard` decorator and the static scanner need none of these extras.

### 6.0.3 release highlights

- Telemetry remains explicitly opt-in and performs no network dispatch by default.
- Governance signatures are line-ending independent across Windows, macOS, and Linux.
- The package metadata, wheel smoke test, secret scanning, and developer extras are
  aligned with the `pyproject.toml` build.
- The committed governance public key is rotated; the private signing key is
  generated and retained outside the repository.

Initialize your local asymmetric cryptographic repository identity:

```bash
anchor init
```

Run a parallel static code safety audit across your local workspace:

```bash
anchor check .
```

`anchor check` exits `0` when no findings meet the threshold, `1` when there are
findings, and `2` on usage errors or when `ANCHOR_REQUIRE_VERIFIED_GOVERNANCE=1`
is set and the bundled rules cannot be verified, so it can gate CI directly.

```bash
anchor --version
anchor check . --severity blocker      # blocker | error (default) | warning | info
anchor check . --format json           # machine-readable report on stdout (or: markdown)
```

`anchor init` prompts interactively in a terminal; with no terminal (CI, Docker)
or with `--no-prompt` it runs non-interactively.

### Building from source

Prebuilt wheels need no toolchain. Installing from source (`pip install .` or an
sdist on a platform without a wheel) compiles the Rust kernel and needs Rust
**1.78 or newer** (the committed `Cargo.lock` is lockfile v4) and a C toolchain.

---

## 🔌 Runtime Integration

Wrap a high-privilege agent routine or LLM invocation with a decorator. `@guard` only protects functions you wrap; unwrapped code is not covered.

```python
from anchor import guard

@guard(domain="finance")
def execute_algorithmic_trade(order_payload):
    # If the autonomous agent tries to route an un-vetted market order,
    # Anchor audits the call payload before the function body runs and returns a BLOCKED_BY_ANCHOR directive on a match.
    return route_order_to_exchange(order_payload)
```

`from anchor.guard import guard` is the equivalent spelling if you prefer to
import the decorator directly. Both are exercised by
[`tests/test_readme_example.py`](tests/test_readme_example.py).

---

## 🌐 The AnimusLab Institution Network

Anchor Core acts as the local spoke auditing engine that feeds seamlessly into the wider, unified decentralized coordination hub ecosystem:

- **Central Portal Hub**: [animuslab.dev](https://animuslab.dev)
- **Enterprise Fleet Cockpit**: [hub.animuslab.dev](https://hub.animuslab.dev)
- **Statutory Rules Documentation**: [animuslab.dev/rules](https://animuslab.dev/rules)
- **Authoritative Engineering Profile**: [tan.animuslab.dev](https://tan.animuslab.dev)

*Maintained by AnimusLab.*

---

## ⚠️ Limitations

- `@guard` (Layer 2) covers only the functions you decorate. Keyword/pattern checks can be rephrased around; treat Anchor as one deterministic layer in defense-in-depth.
- Telemetry is **off by default**. Set `ANCHOR_TELEMETRY=on` to opt in; see [docs/telemetry.md](docs/telemetry.md) for exactly what is sent.
- Static rules are pattern/AST based. Known detection gaps are tracked as `xfail` tests in `tests/unit/test_detection_gaps.py`.

---

## Security and legal notes

- **Gateway.** `anchor.app` fails closed: set `ANCHOR_GATEWAY_TOKEN` and send `Authorization: Bearer <token>`. Request bodies are limited to 1 MiB (`ANCHOR_GATEWAY_MAX_BODY_BYTES`). Bind to `127.0.0.1` unless it runs behind a trusted proxy. For local development only, `ANCHOR_GATEWAY_ALLOW_UNAUTHENTICATED=1` disables the check.
- **Remote policies.** `extends:` accepts `https://` URLs only, refuses private and local addresses, and can be restricted with `ANCHOR_POLICY_URL_ALLOWLIST`.
- **Sandbox runtime.** Downloaded runtime files are verified against pinned SHA-256 hashes before use.
- **Not legal advice.** Anchor reports automated pattern and AST findings mapped to the provisions they relate to. A finding is not a legal determination, and a clean scan is not a compliance certification. References to OWASP, NIST, FINOS, OECD and regulators identify sources only and do not imply endorsement.
- **Reporting vulnerabilities:** see [SECURITY.md](SECURITY.md). Third-party licenses: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
