# Benchmark Results

This document presents empirical execution speeds, parsing overheads, and sandboxing penalties recorded during the validation of the Anchor compliance engine.

---

## 1. Static Scan Performance (Layer 1)

Static scanning performance is governed by the efficiency of AST compilation (via Tree-sitter) and policy execution.

### Processing Latency by Language
*   **AST Compilation Time**: $< 8\text{ms}$ per file (average across Python, TS, and Go).
*   **Total Scan Time (Django - 742 files)**: $2.4\text{s}$ to $3.1\text{s}$ (executed on a standard developer workstation).
*   **Memory Footprint**: $< 120\text{MB}$ RAM during high-concurrency static execution.

*Conclusion*: Anchor is fast enough to execute inside pre-commit hooks and CI/CD pipelines without introducing developer pipeline friction.

---

## 2. Runtime Interception Latency (Layer 2)

Layer 2 interceptors operate directly inside the critical path of outbound AI/LLM requests. Minimizing execution latency is crucial to avoid degrading application responsiveness.

### Interceptor Critical Path Overhead
*   **RAM-Cached Warm-Up Penalty**: $\sim 30\text{ms}$ (on initial SDK boot, caching Git context, loading constitution schemas, and compiling Aho-Corasick tries).
*   **Audit Path Execution (`DecisionAuditor.audit()`)**: $< 2.2\text{ms}$ (inclusive of prompt/response content hashing and cryptographic HMAC-SHA256 signature calculations).
*   **I/O Logging (Local appending to JSONL)**: $< 0.8\text{ms}$ (using non-blocking file system writes).

*Conclusion*: Once warmed up, the runtime compliance check introduces no noticeable latency overhead to network API roundtrips (which typically range from 200ms to 2000ms).

---

## 3. Sandbox Penalty (Diamond Cage)

When behavioral verification is active, scripts are executed inside the **Diamond Cage WASM sandbox** (using WasmEdge) to isolate execution.

| Execution Mode | Isolation Guarantees | Average Latency | Performance Overhead |
|---|---|---|---|
| **Native Python Subprocess** | None (full network/filesystem access) | $12\text{ms}$ | Baseline ($1\text{x}$) |
| **Diamond Cage WASM Container** | Full (blocked network, `/app` mount only) | $38\text{ms}$ | $\sim 3.1\text{x}$ slowdown |

### Overhead Analysis
The $26\text{ms}$ overhead introduced by the Diamond Cage is caused by:
1.  Stripping environment variables and mounting isolated directory structures.
2.  Booting the lightweight Python 3.11 WASM runtime inside WasmEdge.

*Conclusion*: While sandboxed execution is $3\text{x}$ slower than native execution, the absolute latency penalty remains under $30\text{ms}$, making it highly acceptable for developer pre-commit stages where security containment is required.
