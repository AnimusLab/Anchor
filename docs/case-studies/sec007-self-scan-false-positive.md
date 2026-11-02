# Case study: SEC-007 false positives in Anchor's self-scan

**Project:** Anchor
**Rule:** `SEC-007` — Potential Shell Invocation
**Observed version:** `6.1.0`
**Status:** Remediation applied; targeted regression, Rust, Python, build, and self-scan verification passed
**Verification date:** 1 November 2026

## Summary

Anchor scanned its own repository and reported six `SEC-007` findings as blockers. Inspection showed that these were not six demonstrated shell-execution vulnerabilities. They were matches in two detector-definition lines and four Rust regression-test assertions that intentionally contained shell-related examples.

The incident exposed a limitation in line-oriented pattern scanning: a regular expression can match its own source representation and the illustrative strings used to test it. The scanner did not have a semantic basis for treating those lines as executable shell invocations.

The remediation uses existing, rule-scoped inline suppression directives on the exact detector-definition and test-fixture lines. It does **not** disable `SEC-007`, lower its severity, or exclude `src/lib.rs` from scanning. An end-to-end regression test checks that the annotated examples are suppressed while an unannotated shell invocation in the same scanned file remains reportable.

The maintainer then rebuilt the native extension, ran the targeted regression test, Rust tests, and full Python suite, and repeated the repository self-scan. The resulting self-scan reported zero findings.

## Reproduction and baseline

Run the self-scan from the Anchor repository root:

```powershell
anchor check . --severity info --format json
```

The pre-remediation report contained:

| Metric | Baseline result |
|---|---:|
| Rule version | `6.1.0` |
| Files scanned | 121 |
| Lines scanned | 13,555 |
| Scan latency | 83,650 µs (83.65 ms) |
| Total findings | 6 |
| Reported risk score | 10.0 |
| Reported risk level | `CRITICAL` |

All six findings were attributed to `SEC-007` in `src/lib.rs`:

| Source line | Matched content | Why it was not a vulnerability finding |
|---:|---|---|
| 92 | Runtime regular-expression definition | Detector configuration, not a shell invocation |
| 95 | Static regular-expression definition | Detector configuration, not a shell invocation |
| 541 | `os.system(cmd)` inside an assertion string | Synthetic positive test input |
| 542 | `os.system(cmd)` inside an assertion string | Synthetic negative test input |
| 543 | `rm -rf /` inside an assertion string | Synthetic dangerous-command test input |
| 544 | `subprocess.run(cmd, shell=True)` inside an assertion string | Synthetic dangerous-call test input |

The output therefore measured pattern matches, not six independently established vulnerabilities. The `CRITICAL` aggregate was a consequence of the rule's configured severity and should not be interpreted as proof that the repository executed these commands.

## Root cause

`SEC-007` is implemented in the native scanner as a line-oriented regular-expression rule. It searches supported source files for shell-related patterns. This is a fast heuristic, but it does not by itself distinguish executable code from a detector's own pattern string or a test assertion containing an example.

There was also a pragma-placement issue. The static pattern had a comment-only `anchor: ignore SEC-007` directive followed by another explanatory comment. Comment-only directives apply to the next physical line, so the directive targeted the intervening comment rather than the pattern declaration. The runtime-pattern declaration had no preceding directive, and the four assertion lines had no rule-scoped directives.

## Remediation

The correction is deliberately narrow:

1. Add trailing `anchor: ignore SEC-007` directives to the two detector-definition lines.
2. Add the same rule-scoped directive to each of the four regression assertion lines that contains a synthetic shell example.
3. Add an end-to-end scanner test using a Rust source fixture. The test asserts that the annotated examples do not produce findings, while a `Command::new("sh").arg("-c")` invocation on an unannotated line still produces `SEC-007`.
4. Keep the existing `SEC-007` static and runtime patterns active. No file-wide or directory-wide exclusion is introduced.

The directives target only `SEC-007` on the annotated lines. In this incident, each of the six reported findings carried `SEC-007` as its only rule ID. Multi-rule findings that aggregate several IDs on one source line are a separate suppression-semantics concern and are not changed by this remediation. An actual invocation elsewhere in the file remains reportable by the regression test.

This is a targeted, documented suppression for known detector-definition and fixture lines. It is **not** a general-purpose semantic or taint-analysis upgrade to `SEC-007`.

## Verification

The maintainer ran the following commands in the Windows `anchor_dev` Conda environment after applying the patch.

### Targeted regression test

```powershell
pytest -q tests/unit/test_ignore_pragmas.py -k rust_sec007
```

Result:

```text
1 passed, 13 deselected
```

### Rust tests

```powershell
cargo test
```

Result: one Rust unit test passed:

```text
runtime_rule_tests::sec007_static_and_runtime_patterns_have_distinct_scopes ... ok

1 passed; 0 failed
```

Rust doc-tests contained zero tests. The build emitted the existing PyO3 `non_local_definitions` warning around `#[pymethods]`; it did not prevent compilation or test execution.

### Native extension rebuild

```powershell
maturin develop --release
```

Result: successful release build and editable installation of `anchor-audit 6.1.0`.

### Full Python suite

```powershell
pytest -q
```

Result:

```text
348 passed, 2 skipped in 29.27s
```

### Post-remediation self-scan

```powershell
anchor check . --severity info --format json
```

Result:

| Metric | Baseline | Post-remediation |
|---|---:|---:|
| Files scanned | 121 | 121 |
| Lines scanned | 13,555 | 13,570 |
| Scan latency | 83,650 µs | 85,257 µs |
| Total findings | 6 | 0 |
| Risk score | 10.0 | 0.0 |
| Risk level | `CRITICAL` | `LOW` |
| `is_compliant` | `false` | `true` |

The final report returned:

```json
{
  "is_compliant": true,
  "rule_version": "6.1.0",
  "scan_latency_us": 85257,
  "files_scanned": 121,
  "lines_scanned": 13570,
  "risk_score": 0.0,
  "risk_level": "LOW",
  "total_violations": 0,
  "violations": []
}
```

## Interpretation and limitations

This verification establishes that the six observed SEC-007 self-scan findings were eliminated in the tested Anchor 6.1.0 working tree, that the focused regression test preserved detection of an unannotated shell invocation in its fixture, and that the reported repository self-scan returned zero findings after the change.

It does **not** establish general SEC-007 precision or recall, prove the absence of shell vulnerabilities, or demonstrate that every shell-related pattern is exploitable. The rule remains a heuristic indicator, not a data-flow or taint-analysis engine. A clean self-scan is one repository-specific regression result, not a security certification or proof of production safety.

A future enhancement may use language-aware syntax and call-context analysis to distinguish process creation, shell selection, and the flow of untrusted input to command arguments. Such analysis will need its own labelled tests and precision/recall measurements.

## What this demonstrates

A scanner should be tested against its own source, including the rules and fixtures that implement its detection logic. A trustworthy self-scan must distinguish a detector describing a dangerous pattern from application code that actually invokes it. Narrow, reviewable suppressions and regression tests are preferable to excluding an entire source file or weakening a rule globally. The remediation and its limits should be published together so readers can see both what was fixed and what remains unproven.
