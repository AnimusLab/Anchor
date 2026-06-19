# CLI Command Reference

This page documents the full syntax, options, and examples for every command in the **`anchor`** CLI (v5.0.8).

---

## Global Syntax

```bash
anchor [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|---|---|
| `--version` | Display the installed Anchor version. |
| `--help` | Show help for any command or subcommand. |

---

## Command Tree

```
anchor
├── init                  ← Set up governance in a repository
├── sync                  ← Pull latest authoritative governance files
├── check                 ← Layer 1: compliance scan (default)
│   ├── drift             ← Architectural drift analysis
│   └── verify-sync       ← Internal mitigation.anchor integrity check
└── heal                  ← Show and optionally apply fix suggestions
```

---

## Commands

### `anchor init`

Initialise Anchor V5 governance in a repository. Creates `.anchor/` with the requested domain, framework, and regulator files. Always loads all core domains: `security`, `ethics`, `shared`, `privacy`, `alignment`, `legal`, `operational`, `supply-chain`, `agentic`.

```bash
anchor init [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--domains <list>` | — | Comma-separated domains to load. Options: `all` (core domains always included). |
| `--frameworks <list>` | — | Comma-separated frameworks. Options: `finos`, `owasp`, `nist`, `all`. |
| `--regulators <list>` | — | Comma-separated regulators. Options: `rbi`, `eu`, `sebi`, `cfpb`, `fca`, `sec`, `all`. |
| `--sandbox` | off | Install Diamond Cage (WASM sandbox) for secure execution. |
| `--all` | off | Initialise ALL available domains, frameworks, and regulators. |
| `--force` | off | Overwrite existing `.anchor/` files. |
| `--no-sign` | off | Skip directory signing. |
| `--policy-name <name>` | `policy.anchor` | Name for the local project policy file. |

**Examples:**

```bash
# Minimal init — core domains only
anchor init

# Load RBI + EU regulators alongside OWASP rules, with sandbox
anchor init --regulators rbi,eu --frameworks owasp --sandbox

# Load everything
anchor init --all
```

---

### `anchor sync`

Sync governance files with the authoritative remote repository.

```bash
anchor sync [OPTIONS]
```

| Option | Description |
|---|---|
| `--restore` | Overwrite locally modified files with authoritative remote versions. |

**Examples:**

```bash
# Check sync status
anchor sync

# Restore any locally modified governance files
anchor sync --restore
```

---

### `anchor check`

Universal Layer 1 enforcement command for code, AI models, and architectural drift. When invoked without a subcommand, runs a compliance scan against source code or model weights.

```bash
anchor check [PATHS]... [OPTIONS] [SUBCOMMAND]
```

| Option | Default | Description |
|---|---|---|
| `-p, --policy <path>` | — | Policy file(s) to apply. Can be specified multiple times. |
| `-d, --dir <path>` | — | Directory to scan. |
| `-m, --model <path>` | — | Model weights file to validate (`.safetensors`, `.gguf`). |
| `--metadata <path>` | — | Path to training metadata JSON. |
| `-c, --context <path>` | — | GenAI Threat Model (Markdown) to enforce. |
| `--server-mode` | off | Run in server mode (includes local company policy). |
| `--generate-report` | off | Generate a human-readable audit report. |
| `-j, --json-report` | off | Generate `anchor-report.json` for CI pipelines. |
| `--json` | off | Output canonical JSON schema for BYODB pipelines. |
| `--llm` | off | Output high-density, token-optimized text for LLM contexts. |
| `-v, --verbose` | off | Show detailed loading info. |
| `--no-sandbox` | off | Disable Diamond Cage WASM sandbox. |
| `-s, --severity <level>` | `info` | Minimum severity to display. Options: `info`, `warning`, `error`, `blocker`. |
| `--hook` | off | Indicate if running as a Git hook (customizes output format). |
| `--exclude <pattern>` | — | Paths to exclude from scanning. Can be specified multiple times. |
| `--github-summary` | off | Generate `anchor-summary.md` for GitHub Step Summary (CI only). |

**Exit Codes:**

| Code | Meaning |
|---|---|
| `0` | Scan passed. No violations at or above the severity threshold. |
| `1` | Violations found at or above the severity threshold. |

**Examples:**

```bash
# Scan current directory
anchor check .

# Scan with RBI regulator policy, blocking on error severity
anchor check . --regulators rbi --severity error

# Validate a model weights file
anchor check --model model.safetensors --metadata meta.json

# Output JSON for a CI pipeline
anchor check . --json-report

# Exclude test directories
anchor check . --exclude tests --exclude benchmarks
```

---

### `anchor check drift`

Scan a codebase for architectural drift. For each symbol, the engine traces its introducing commit, anchors the original intent, extracts current call contexts, and issues a verdict.

```bash
anchor check drift [TARGET] [OPTIONS]
```

| Argument / Option | Default | Description |
|---|---|---|
| `TARGET` | `.` | File or directory to scan. |
| `-r, --repo <path>` | `.` | Path to the git repository root. |
| `-l, --limit <n>` | `30` | Max symbols to analyse (safeguard for large codebases). |
| `--only-violations` | off | Only show symbols with non-ALIGNED verdicts. |
| `--json` | off | Output results as JSON. |
| `-v, --verbose` | off | Show debug output. |
| `--report` | off | Generate persistent audit reports in `.anchor/`. |
| `--no-sandbox` | off | Disable Diamond Cage WASM sandbox. |

**Verdicts:**

| Verdict | Meaning |
|---|---|
| `ALIGNED` | Current usage is consistent with the original anchored intent. |
| `INTENT_VIOLATION` | Dominant usage directly contradicts the original purpose. |
| `SEMANTIC_OVERLOAD` | Symbol serves too many distinct caller domains (identity crisis). |
| `DEPENDENCY_INERTIA` | Symbol is barely used but still carries interface weight (dead weight). |
| `COMPLEXITY_DRIFT` | Usage has grown far beyond the original scope (scope creep). |
| `CONFIDENCE_TOO_LOW` | Insufficient history or docstrings to issue a verdict. |

**Reports written to `.anchor/`:**

| File | Contents |
|---|---|
| `.anchor/violations/drift_violations.txt` | Plain-text summary of all verdicts. |
| `.anchor/reports/drift_audit.md` | Markdown audit report with evidence tables. |
| `.anchor/telemetry/drift_report.json` | JSON report (written when `--json` or CI detected). |

**Examples:**

```bash
# Analyse the current directory (default limit: 30 symbols)
anchor check drift .

# Analyse a specific file
anchor check drift src/agent.py

# Analyse up to 200 symbols, show only violations
anchor check drift . --limit 200 --only-violations

# Output JSON for downstream tooling
anchor check drift . --json > drift.json
```

---

### `anchor check verify-sync`

Verify that all three copies of `mitigation.anchor` are identical (canonical source, root copy, and local cache). Detects tampering or out-of-sync states.

```bash
anchor check verify-sync [OPTIONS]
```

| Option | Description |
|---|---|
| `--fix` | Auto-sync all copies from the canonical package source. |
| `-v, --verbose` | Show SHA-256 hash details for each copy. |

**Examples:**

```bash
# Check sync status
anchor check verify-sync

# Show hashes and auto-fix any drift
anchor check verify-sync --verbose --fix
```

---

### `anchor heal`

Read violations from the last `anchor check` run and display diff-style fix suggestions. Auto-fixable issues can be patched in-place.

```bash
anchor heal [PATHS]... [OPTIONS]
```

| Option | Description |
|---|---|
| `--apply` | Apply all auto-fixable suggestions in-place. |
| `-v, --verbose` | Show details for every violation. |

**Examples:**

```bash
# Show all fix suggestions from the last scan
anchor heal

# Show suggestions for a single file
anchor heal src/agent.py

# Apply all auto-fixable patches
anchor heal . --apply
```
