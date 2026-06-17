# CLI Command Reference

This page provides the syntax, parameters, flags, exit codes, and examples for all subcommands in the **`anchor`** Command Line Interface.

---

## 📌 Global Syntax

```bash
anchor [GLOBAL_OPTIONS] COMMAND [ARGS]...
```

*   **`--help`**: Output help information for any command or group.
*   **`--version`**: Display the installed Anchor core version (e.g. `5.0.8`).

---

## 🛠️ Commands

### 1. `anchor init`
Initialise Anchor compliance rulesets and pre-commit hooks in the target repository.

```bash
anchor init [OPTIONS]
```

#### Options:
*   **`--domains <list>`**: Comma-separated domains to load. Under V4, it always includes all core domains (`security`, `ethics`, `shared`, `privacy`, `alignment`, `legal`, `operational`, `supply_chain`, `agentic`).
*   **`--frameworks <list>`**: Comma-separated industry frameworks to activate. Options: `finos`, `owasp`, `nist`, `all`.
*   **`--regulators <list>`**: Comma-separated jurisdictional government regulations to load. Options: `rbi`, `eu`, `sebi`, `cfpb`, `fca`, `sec`, `all`.
*   **`--sandbox`**: Flag to automatically download and initialize the Diamond Cage WASM container.
*   **`--all`**: Initialise all domains, frameworks, and government regulations.
*   **`--force`**: Force-overwrite existing files in `.anchor/`.
*   **`--no-sign`**: Skip downloading and registering the authoritative remote `GOVERNANCE.lock` signature.
*   **`--policy-name <string>`**: Custom name for the local override policy file (default: `policy.anchor`).

#### Examples:
```bash
# Initialize only core domains and the local template
anchor init

# Load RBI, SEC, and EU compliance modules alongside OWASP rules
anchor init --regulators rbi,sec,eu --frameworks owasp --sandbox
```

---

### 2. `anchor check`
Universal static scanning command to audit code repositories, training files, or models against active policy files.

```bash
anchor check [PATHS]... [OPTIONS]
```

#### Options:
*   **`-p, --policy <path>`**: Explicit policy files to load. Can be specified multiple times.
*   **`-d, --dir <path>`**: Directory to run code scanning.
*   **`-m, --model <path>`**: Model weights file (`.safetensors`, `.gguf`) to audit.
*   **`-c, --context <path>`**: genAI Threat Model document (Markdown) to extract scoped Risk IDs from.
*   **`--severity <level>`**: Minimum violation severity to display. Options: `info`, `warning`, `error`, `blocker` (default: `info`).
*   **`--json-report`**: Generate a `governance_report.json` CI artifact inside `.anchor/telemetry/`.
*   **`--generate-report`**: Generate a styled `governance_report.html` audit report.
*   **`--llm`**: Format stdout as high-density, token-optimized text suitable for AI agent prompting context.
*   **`--exclude <pattern>`**: Paths to exclude from evaluation. Can be specified multiple times.

#### Exit Codes:
*   **`0`**: Scan completed. No violations of `error` or `blocker` severity.
*   **`1`**: Scanned successfully but found active compliance violations.
*   **`2`**: Executable exception or missing parameters.

---

### 3. `anchor check drift`
Audit a repository's git commit history to detect semantic or structural architectural drift of critical functions and classes.

```bash
anchor check drift [TARGET]
```

#### Target:
*   Can be a directory path or a single symbol path (e.g. `src/models.py`).

#### Examples:
```bash
# Evaluate drift on all symbols within the current repo
anchor check drift .
```

---

### 4. `anchor check verify-sync`
Verify that local `.anchor/` rules and modules match the authoritative signatures in `.anchor.lock`.

```bash
anchor check verify-sync
```

---

### 5. `anchor sync`
Synchronize local rulesets with the official, authoritative upstream repository.

```bash
anchor sync --restore
```

#### Options:
*   **`--restore`**: Required option. Overwrites modified local files inside `.anchor/` with the official remote versions if cryptographic hashes mismatch.

---

### 6. `anchor heal`
Review, display, and apply auto-fix suggestions mapping to AST-detected static violations.

```bash
anchor heal [PATHS]... [OPTIONS]
```

#### Options:
*   **`--apply`**: In-place modification flag. Applies all deterministic code patches directly to target files.
*   **`-v, --verbose`**: Verbose logging showing refactoring template diffs.

#### Examples:
```bash
# View diff-style recommendations for violations logged in the last scan
anchor heal

# Apply fixes to the main server module
anchor heal src/server.py --apply
```
